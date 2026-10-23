"""Local MCP (Model Context Protocol) server for gauss-ai -- exposes the
conversational assistant, deterministic code validation, the controlled
execution handoff, and the guided repair pipeline as MCP tools for other
local MCP clients (Claude Code, Claude Desktop) over stdio. v0.79.0 added
the server; v0.80.0 added the "hybrid" path.

Two ways to get from a question to code (v0.80.0):

- **Hybrid (always available).** The calling model searches the docs
  (`gauss_search_docs`), writes GAUSS code itself, and submits it to
  `gauss_validate_code`, which computes the readiness verdict here,
  deterministically. No second model is involved -- the calling client IS
  the model. The code may come from the caller; the verdict never does.
- **Strict (opt-in).** `gauss_chat_ask`/`gauss_chat_reset` wrap
  `ConversationEngine.ask()` whole, including its own provider call, so the
  generation gate can block ungrounded code before any is written. These
  two tools are registered only when the configured `chat-provider` is a
  real model (`ollama`/`anthropic`) -- an explicit choice, never
  auto-detected.

This module is orchestration/transport glue ONLY, the same convention
`gauss_ai_chat.py` and `gauss_ai_guided_repair.py` established for their own
front-ends. It implements no grounding, readiness, digest, approval, or
repair logic of its own -- every real decision is delegated to the
existing modules: `gauss_conversation_engine` (`ConversationEngine`,
`validate_code`, `ground_multi`), `gauss_execution_handoff` (the v0.78.0
controlled execution bridge), and `gauss_code_assistant_cli.
InteractiveMvpAdapter` (the guided repair REPL).

Hard boundaries (structurally enforced and tested, see
test_gauss_mcp_server.py):

- This module never recomputes a readiness verdict and never reimplements
  digest/approval logic or `InteractiveMvpAdapter`. Whether execution may
  even be offered is read through `gauss_ai_chat._execution_offer_eligible`
  (imported and reused rather than duplicated, despite the underscore, so
  the two front-ends can never drift on this gate).
- Execution can only ever be prepared for code this server itself
  validated or generated: either the session's own last `gauss_chat_ask`
  answer, or a server-issued, single-use `validation_id` from
  `gauss_validate_code`, re-validated at prepare time.
- Real GAUSS execution (`runner="gauss"`) additionally requires the server
  OPERATOR to have set `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1` in the server
  process's own environment at startup -- an extra gate on top of the
  per-request digest/approval flow, since an MCP client is one step further
  removed from the human at the keyboard than a terminal user.
- v0.87.0 (live finding 77.x f2): `gauss_execution_decide` acts only on the
  pending request whose `request_id` the client names -- the prompt the
  user's reply answers. A prepare that replaces a pending request says so,
  and a reply aimed at the replaced prompt is refused without creating an
  approval. The server cannot prove the user saw a prompt (the client
  relays both prompt and reply); it can refuse to run a request other than
  the one the client says the reply answers.
- Sessions are process-local and in-memory only, like every other approval
  store in this repository.

The `mcp` package is an OPTIONAL runtime dependency
(`pip install -e ".[mcp]"`); importing this module without it raises a
clear `ImportError`. `gauss_ai_cli.py` imports this module lazily, so the
base CLI stays stdlib-only.
"""

from __future__ import annotations

import atexit
import dataclasses
import hashlib
import os
import time
import uuid
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

try:
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations
except ImportError as exc:  # pragma: no cover - exercised only without the optional extra installed
    raise ImportError(
        "The 'mcp' package is required to run the gauss-ai MCP server. Install it with: "
        'pip install "gauss-ai[mcp]"'
    ) from exc

import gauss_ai_chat as chat_mod
import gauss_ai_config as config_mod
import gauss_chat_provider as provider_mod
import gauss_code_assistant_cli as cli_mod
import gauss_conversation_engine as engine_mod
import gauss_doc_reader as doc_reader_mod
import gauss_execution_handoff as handoff_mod

__version__ = "0.89.3"

#: Set by the server OPERATOR in the process's own environment before
#: launch -- never read from a tool-call argument. See module docstring.
ENV_ALLOW_REAL_GAUSS = "GAUSS_AI_MCP_ALLOW_REAL_GAUSS"

#: Per-session cap on outstanding validation_ids (oldest evicted first).
MAX_VALIDATIONS_PER_SESSION = 8

#: v0.89.0 (planning v0.89 §3.8): a long-running server (one per Claude
#: Code window) kept every session until close or exit. A session idle
#: longer than this is closed by the sweep at the start of the next tool
#: call; 8 hours lets a prompt left open over a working day survive. An
#: evicted session's pending request and validation_ids die with it and
#: never approve anything.
SESSION_IDLE_SECONDS = 8 * 3600

#: v0.89.0: at most this many sessions of each kind; past it, the least
#: recently used is closed.
MAX_SESSIONS = 64

DOCS_FETCH_HINT = "Run 'gauss-ai docs fetch' once to download the official GAUSS documentation."

#: v0.89.0 (live finding 79.x-1; planning v0.89 §3.6): shown on every
#: documentation source, since the excerpt is cut and extraction drops some
#: value lists (`sqpSolveMT`'s return codes).
READ_DOC_HINT = (
    "The content is an excerpt. Call gauss_read_doc with this citation to see the page's sections, "
    "then read any section in full."
)

_SESSION_EXPIRED_DETAIL = (
    f"This session was closed after {SESSION_IDLE_SECONDS // 3600} idle hours (or to stay under "
    f"{MAX_SESSIONS} open sessions). Nothing it held was approved or run. Start a new session."
)

#: v0.88.0 (planning v0.88 §3.10): shown with `omitted_topics`.
OMITTED_TOPICS_NOTE = "Resolved but not included (at most 4 per search); search these names separately."

#: v0.88.0 (live finding 78.x f2; planning v0.88 §3.11, v0.87 plan §11.8): 78.x's client suggested
#: labelled replies ("A: yes") that the reply parser rejects, and with prompts open in several sessions
#: only the client maps a bare reply to a prompt. Text only: the parser and the binding are unchanged.
REPLY_GUIDANCE = (
    "If several prompts are open, the user names the prompt in a separate message and replies with a bare yes "
    "or no; never ask the user to label a reply."
)

_REAL_GAUSS_NOT_ALLOWED_DETAIL = (
    "This session is configured for runner 'gauss', but the gauss-ai-mcp server process was not "
    f"started with {ENV_ALLOW_REAL_GAUSS}=1. Real GAUSS execution via MCP requires this explicit "
    "server-operator opt-in, in addition to the per-request approval."
)


def _real_gauss_allowed(env: dict[str, str] | None = None) -> bool:
    env = env if env is not None else os.environ
    return env.get(ENV_ALLOW_REAL_GAUSS, "").strip() == "1"


def _new_id() -> str:
    return uuid.uuid4().hex


def _clock() -> str:
    return datetime.now(timezone.utc).isoformat()


def _monotonic() -> float:
    """v0.89.0: the idle clock for session eviction, a module-level function
    so tests can replace it. Monotonic, so a wall-clock change never evicts
    or keeps a session."""
    return time.monotonic()


# ---------------------------------------------------------------------------
# Session state -- process-local, in-memory only
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidatedCode:
    code: str
    readiness_state: str
    docs_root: str | None


@dataclass
class Session:
    approval_store: "handoff_mod.ExecutionHandoffApprovalStore"
    runner: str
    executable_path: str | None
    workspace_parent: str | None
    timeout_seconds: float
    docs_root: str | None
    #: Built lazily by the first `gauss_chat_ask` (strict mode only).
    engine: "engine_mod.ConversationEngine | None" = None
    #: The last chat answer's single code block and readiness state, if it
    #: was offer-eligible. Reset on every `gauss_chat_ask`, mirroring
    #: `gauss_ai_chat.run_chat`'s own `pending_handoff`.
    pending_code: str | None = None
    pending_readiness_state: str | None = None
    #: Server-issued validation_ids for HANDOFF_CANDIDATE code from
    #: `gauss_validate_code`; single-use, popped by `gauss_execution_prepare`.
    validated: "OrderedDict[str, ValidatedCode]" = field(default_factory=OrderedDict)
    #: The prepared request awaiting `gauss_execution_decide`, and which path
    #: produced it ("chat" or "validated"), so deciding on a validated
    #: request never clears an unrelated pending chat offer.
    pending_request: "handoff_mod.ExecutionHandoffRequest | None" = None
    pending_source: str | None = None
    #: v0.87.0 (live finding 77.x f2): request_ids a later prepare replaced
    #: while they were still pending, newest last and capped like
    #: `validated`. Kept only so `gauss_execution_decide` can say
    #: `request_superseded` (name the prompt that replaced it) instead of a
    #: bare `request_not_pending`; a superseded request can never be approved.
    superseded_request_ids: "deque[str]" = field(default_factory=lambda: deque(maxlen=MAX_VALIDATIONS_PER_SESSION))
    #: v0.89.0: `_monotonic()` at the last tool call that used this session.
    last_used: float = field(default_factory=lambda: _monotonic())


@dataclass
class RepairSession:
    adapter: "cli_mod.InteractiveMvpAdapter"
    last_used: float = field(default_factory=lambda: _monotonic())


_sessions: dict[str, Session] = {}
_repair_sessions: dict[str, RepairSession] = {}
#: v0.89.0: ids the sweep closed, newest last, so a later call can say
#: `session_expired` instead of a bare `unknown_session`.
_expired_session_ids: "deque[str]" = deque(maxlen=4 * MAX_SESSIONS)
_config: "config_mod.GaussAiConfig | None" = None


def _get_config() -> "config_mod.GaussAiConfig":
    """Loaded once per server process, not once per tool call."""
    global _config
    if _config is None:
        _config = config_mod.load_config()
    return _config


def _close_all_sessions() -> None:
    """Registered with `atexit` so an abrupt stdio disconnect still cleans
    up every live repair session's real temporary workspace -- there is no
    terminal EOF here to trigger the REPL's own cleanup."""
    for repair_session in list(_repair_sessions.values()):
        try:
            repair_session.adapter.close()
        except Exception:  # noqa: BLE001 - best-effort cleanup only, never raises during shutdown
            pass
    _repair_sessions.clear()
    _sessions.clear()


atexit.register(_close_all_sessions)


def _close_repair_session(session_id: str) -> bool:
    """The one path that closes a repair session and frees its workspace,
    shared by `gauss_repair_close` and the eviction sweep."""
    repair_session = _repair_sessions.pop(session_id, None)
    if repair_session is None:
        return False
    repair_session.adapter.close()
    return True


def _sweep_sessions() -> None:
    """v0.89.0 (planning v0.89 §3.8): run at the start of every tool call.
    Closes each session idle longer than `SESSION_IDLE_SECONDS`, then, while
    either kind still exceeds `MAX_SESSIONS`, the least recently used.
    Deterministic given `_monotonic()`."""
    now = _monotonic()
    for sid, session in list(_sessions.items()):
        if now - session.last_used > SESSION_IDLE_SECONDS:
            del _sessions[sid]
            _expired_session_ids.append(sid)
    for sid, repair_session in list(_repair_sessions.items()):
        if now - repair_session.last_used > SESSION_IDLE_SECONDS:
            _close_repair_session(sid)
            _expired_session_ids.append(sid)
    while len(_sessions) > MAX_SESSIONS:
        sid = min(_sessions, key=lambda k: _sessions[k].last_used)
        del _sessions[sid]
        _expired_session_ids.append(sid)
    while len(_repair_sessions) > MAX_SESSIONS:
        sid = min(_repair_sessions, key=lambda k: _repair_sessions[k].last_used)
        _close_repair_session(sid)
        _expired_session_ids.append(sid)


def _missing_session_error(session_id: str) -> dict[str, Any]:
    if session_id in _expired_session_ids:
        return {"error": "session_expired", "detail": _SESSION_EXPIRED_DETAIL}
    return {"error": "unknown_session"}


def _use_session(session_id: str) -> "tuple[Session | None, dict[str, Any] | None]":
    """Sweeps, then returns `(session, None)` with its idle clock reset, or
    `(None, error)`."""
    _sweep_sessions()
    session = _sessions.get(session_id)
    if session is None:
        return None, _missing_session_error(session_id)
    session.last_used = _monotonic()
    return session, None


def _use_repair_session(session_id: str) -> "tuple[RepairSession | None, dict[str, Any] | None]":
    _sweep_sessions()
    repair_session = _repair_sessions.get(session_id)
    if repair_session is None:
        return None, _missing_session_error(session_id)
    repair_session.last_used = _monotonic()
    return repair_session, None


def _resolve_docs_root(docs_root: str | None, session_id: str | None) -> "tuple[str | None, dict[str, Any] | None]":
    """v0.89.0 (planning v0.89 §2.6, §3.9): the docs root for the read-only
    doc tools. An explicit `docs_root` wins; otherwise a given session's own
    root (a client that set `docs_root` in `gauss_session_start` used to get
    grounded validation but ungrounded search); otherwise the usual
    environment-then-config resolution. Only which root is passed in
    changes; grounding itself is untouched."""
    if docs_root is None and session_id is not None:
        session, error = _use_session(session_id)
        if session is None:
            return None, error
        if session.docs_root is not None:
            return session.docs_root, None
    else:
        _sweep_sessions()
    return config_mod.resolve_docs_root(cli_value=docs_root, config=_get_config(), env=os.environ).value, None


# v0.89.0 (planning v0.89 §2.7, §3.9): MCP tool annotations, fixed here and
# pinned by a test. A client may use them to decide what to auto-approve, so
# a wrong hint is worse than none: `gauss_execution_decide` runs GAUSS and
# the repair tools write in a workspace, so neither is read-only.
_READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
_RUNS_CODE = ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=False, open_world_hint=False)
_MANAGES_WORKSPACE = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False)
_WRITES_WORKSPACE = ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=False, open_world_hint=False)
#: Strict-mode chat may call a cloud model provider the user enabled.
_ASKS_MODEL = ToolAnnotations(read_only_hint=True, open_world_hint=True)


# ---------------------------------------------------------------------------
# Serialization -- JSON-safe views, never raw objects by reference
# ---------------------------------------------------------------------------


def _readiness_dict(readiness: Any) -> dict[str, Any] | None:
    if readiness is None:
        return None
    return {"state": readiness.state, "reasons": list(readiness.reasons)}


def _answer_result_to_dict(result: "engine_mod.AnswerResult", *, execution_offer_eligible: bool) -> dict[str, Any]:
    return {
        "text": result.text,
        "intent": result.intent,
        "grounded": result.grounded,
        "grounding_status": result.grounding_status,
        "grounding_source": result.grounding_source,
        "grounding_topic": result.grounding_topic,
        "grounding_sources": [{"source": s.source, "topic": s.topic} for s in result.grounding_sources],
        "unsupported_topics": list(result.unsupported_topics),
        "omitted_topics": list(result.omitted_topics),
        "provider_name": result.provider_name,
        "provider_model": result.provider_model,
        "provider_success": result.provider_success,
        "provider_error": result.provider_error,
        "generated_code": list(result.generated_code),
        "unknown_symbols": list(result.unknown_symbols),
        "generation_policy": result.generation_policy,
        "ambiguous_topics": list(result.ambiguous_topics),
        "pre_execution_eligibility": result.pre_execution_eligibility,
        "pre_execution_issues": list(result.pre_execution_issues),
        "system_statements": [dataclasses.asdict(f) for f in result.system_statements],
        "handoff_readiness": _readiness_dict(result.handoff_readiness),
        "execution_offer_eligible": execution_offer_eligible,
    }


def _validation_to_dict(result: "engine_mod.CodeValidationResult") -> dict[str, Any]:
    pre = result.pre_execution
    return {
        "handoff_readiness": _readiness_dict(result.handoff_readiness),
        "called_symbols": list(result.called_symbols),
        "user_defined_symbols": list(result.user_defined_symbols),
        "grounding_status": result.grounding_status,
        "grounding_sources": [{"topic": s.topic, "citation": s.citation} for s in result.grounding_sources],
        "unsupported_topics": list(result.unsupported_topics),
        "ambiguous_topics": list(result.ambiguous_topics),
        "unknown_symbols": list(pre.unknown_symbols) if pre else [],
        "eligibility": pre.eligibility if pre else None,
        "issues": list(pre.unresolved_issues) if pre else [],
        "syntax": pre.syntax.status if pre and pre.syntax else None,
        "preconditions": [
            {"symbol": c.precondition.symbol, "status": c.status, "explanation": c.explanation}
            for c in (pre.preconditions if pre else ())
        ],
        "system_statements": [dataclasses.asdict(f) for f in (pre.system_statements if pre else ())],
        "companion_hints": [list(pair) for pair in (pre.companion_hints if pre else ())],
        "notes": list(result.notes),
        # v0.83.0: what evidence was obtained, and every gap that kept it
        # short -- before this a client saw only "validation coverage is
        # partial" and guessed the cause (live findings 72.3, 72.15).
        "coverage": dataclasses.asdict(pre.coverage) if pre and pre.coverage else None,
        "coverage_gaps": [dataclasses.asdict(gap) for gap in (pre.coverage_gaps if pre else ())],
    }


# ---------------------------------------------------------------------------
# MCP server + always-registered tools
# ---------------------------------------------------------------------------

server = MCPServer(
    name="gauss-ai",
    version=__version__,
    instructions=(
        "GAUSS programming assistant backed by the official GAUSS documentation and deterministic checks. "
        "Recommended flow: gauss_session_start -> gauss_search_docs to look up the functions you need (its "
        "excerpts are cut; gauss_read_doc reads any section of a cited page in full, such as Remarks or return "
        "codes) -> write the GAUSS code yourself -> gauss_validate_code to get a deterministic verdict (signatures, documented "
        "preconditions, syntax, unknown functions, and system-touching statements). Only code that reaches "
        "handoff_candidate gets a validation_id; to run it, call gauss_execution_prepare(validation_id), show the "
        "user the exact prompt it returns, and pass the user's own yes/no to gauss_execution_decide together with "
        "that prompt's request_id. Never answer yes on the user's behalf. " + REPLY_GUIDANCE + " gauss_repair_* tools drive the guided "
        "repair pipeline for real files, one REPL command per call. gauss_chat_ask exists only when the server is configured with its own model."
    ),
)


@server.tool(annotations=_READ_ONLY)
def gauss_session_start(
    runner: str | None = None,
    gauss_executable: str | None = None,
    workspace_parent: str | None = None,
    timeout_seconds: float | None = None,
    docs_root: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Start a session for validating and (optionally) executing GAUSS
    code. Settings left out resolve exactly as the gauss-ai CLI resolves
    them (argument > environment variable > config file > default). Returns
    a `session_id` for the other gauss_* tools, and `real_gauss_allowed`:
    whether the server operator started this server with
    GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1. It reflects that opt-in only; whether
    the GAUSS executable actually launches is known only from a run. Also
    returns `server_version`: if it is not the version you installed, or a
    tool asks for an argument its description does not mention, restart
    the MCP client and start a new conversation. Sessions idle for 8 hours
    are closed."""
    _sweep_sessions()
    config = _get_config()
    env = os.environ
    sid = session_id or _new_id()
    if sid in _expired_session_ids:
        _expired_session_ids.remove(sid)
    resolved_docs_root = config_mod.resolve_docs_root(cli_value=docs_root, config=config, env=env).value
    _sessions[sid] = Session(
        approval_store=handoff_mod.ExecutionHandoffApprovalStore(),
        runner=config_mod.resolve_default_runner(cli_value=runner, config=config, env=env).value,
        executable_path=config_mod.resolve_gauss_executable(cli_value=gauss_executable, config=config, env=env).value,
        workspace_parent=config_mod.resolve_workspace_parent(cli_value=workspace_parent, config=config, env=env).value,
        timeout_seconds=config_mod.resolve_default_timeout_seconds(cli_value=timeout_seconds, config=config, env=env).value,
        docs_root=resolved_docs_root,
    )
    response: dict[str, Any] = {
        "session_id": sid,
        # v0.89.0 (planning v0.89 §2.7, §3.9): some clients keep a tool's old
        # description across an upgrade, and since v0.87.0 a stale
        # `gauss_execution_decide` description omits `request_id`. The
        # version makes the mismatch visible to the user and in bug reports.
        "server_version": __version__,
        "runner": _sessions[sid].runner,
        "docs_root_configured": resolved_docs_root is not None,
        # v0.87.0 (live finding 76.x f2): in 76.1 a client could not tell
        # that a run was impossible until a prepare failed, guessed from a
        # config file, and told the user real execution was on. The flag is
        # the same categorical value prepare already checks -- it adds no
        # capability, and it says nothing about whether the executable runs.
        "real_gauss_allowed": _real_gauss_allowed(),
    }
    if _sessions[sid].runner == "gauss" and not response["real_gauss_allowed"]:
        response["execution_hint"] = _REAL_GAUSS_NOT_ALLOWED_DETAIL
    if resolved_docs_root is None:
        response["hint"] = DOCS_FETCH_HINT
    return response


@server.tool(annotations=_READ_ONLY)
def gauss_session_close(session_id: str) -> dict[str, Any]:
    """End a session and free its state."""
    _sweep_sessions()
    existed = _sessions.pop(session_id, None) is not None
    return {"session_id": session_id, "closed": existed}


def _source_dict(source: Any) -> dict[str, Any]:
    entry = {"source": source.source, "topic": source.topic, "citation": source.citation, "content": source.content}
    # v0.89.0: only a documentation page can be read further; an error-catalog
    # entry is already whole.
    if isinstance(source.citation, str) and source.citation.endswith(".rst"):
        entry["read_hint"] = READ_DOC_HINT
        # v0.89.0 (planning v0.89 §9.3): Aptech asked for a link back to the
        # page with each result. Built from the citation; no network.
        entry["docs_url"] = doc_reader_mod.docs_url(source.citation)
    return entry


@server.tool(annotations=_READ_ONLY)
def gauss_search_docs(query: str, docs_root: str | None = None, session_id: str | None = None) -> dict[str, Any]:
    """Search the official GAUSS documentation (and the verified GAUSS error
    catalog, for codes like G0025) for a natural-language question or
    function names. Returns the matching documentation excerpts to read
    before writing code. Excerpts are cut at about 1,500 characters, and
    some value lists (return codes, option codes) are not in them: call
    gauss_read_doc with a source's citation to read any section in full.
    When nothing is grounded but pages look relevant, `candidates` lists
    them (name, citation, purpose) -- candidates are not grounded answers;
    search a candidate's name to read its page. A documented name cut by
    the 4-source bound is listed in `omitted_topics`; search it separately.
    Each documentation source carries `docs_url`, its page on
    docs.aptech.com, to cite. Pass `session_id` to use that session's docs root. Purely local and
    read-only."""
    resolved, error = _resolve_docs_root(docs_root, session_id)
    if error is not None:
        return error
    bundle = engine_mod.ground_multi(query, docs_root_str=resolved)
    response: dict[str, Any] = {
        "grounding_status": bundle.status.value,
        "sources": [_source_dict(s) for s in bundle.sources],
        "unmatched_topics": list(bundle.unmatched_topics),
        "ambiguous_topics": list(bundle.ambiguous_topics),
        "docs_root_configured": resolved is not None,
    }
    # v0.88.0 (live findings 76.5, 77.5, 78.11; planning v0.88 §3.10): a
    # fifth named function was cut at `MAX_GROUNDING_SOURCES` and nothing said
    # so. It is now named, with what to do about it.
    if bundle.omitted_topics:
        response["omitted_topics"] = list(bundle.omitted_topics)
        response["omitted_note"] = OMITTED_TOPICS_NOTE
    # v0.83.0 (live finding 72.16): labeled candidate pages when the query
    # was ambiguous or matched only weakly. Computed from the finished
    # bundle; the grounding fields above are exactly what they were.
    found = engine_mod.search_candidates(query, bundle, docs_root_str=resolved)
    if found.candidates:
        response["candidates"] = [dataclasses.asdict(c) for c in found.candidates]
        response["candidates_truncated"] = found.truncated
        response["candidate_note"] = engine_mod.SEARCH_CANDIDATE_NOTE
    if resolved is None:
        response["hint"] = DOCS_FETCH_HINT + " Until then only error-code lookups can be grounded."
    return response


@server.tool(annotations=_READ_ONLY)
def gauss_read_doc(
    page: str,
    section: str | None = None,
    offset: int = 0,
    docs_root: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Read one official GAUSS documentation page in full, verbatim, as its
    RST source. `page` is a citation exactly as gauss_search_docs returns it
    (e.g. "sqpsolvemt.rst"). Without `section`, returns the page's outline:
    each heading, its level and its size. With `section` (a heading such as
    "Remarks" or "Format", matched case-insensitively; or "*" for the whole
    page), returns up to 8,000 characters of that section from `offset`,
    and `next_offset` when more remains -- call again with it to continue.
    Use this for content the search excerpt cuts or leaves out, such as an
    optimizer's return codes or a function's Remarks. Purely local and
    read-only; reading a page never changes a grounding status or a
    validation verdict. Each result carries `docs_url`, the page on
    docs.aptech.com, to cite. Pass `session_id` to use that session's docs
    root."""
    resolved, error = _resolve_docs_root(docs_root, session_id)
    if error is not None:
        return error
    if resolved is None:
        return {"error": "docs_root_not_configured", "hint": DOCS_FETCH_HINT}
    return doc_reader_mod.read_doc(resolved, page, section=section, offset=offset)


@server.tool(annotations=_READ_ONLY)
def gauss_validate_code(session_id: str, code: str) -> dict[str, Any]:
    """Deterministically validate GAUSS code you wrote: documented
    signatures, documented preconditions, syntax, unknown (possibly
    hallucinated) functions, and system-touching statements. Pass raw GAUSS
    code, not a Markdown block. Nothing is executed. If the result reaches
    handoff_candidate, the response includes a single-use `validation_id`
    for `gauss_execution_prepare`."""
    session, error = _use_session(session_id)
    if session is None:
        return error
    result = engine_mod.validate_code(code, docs_root=session.docs_root)
    if result.rejected_reason is not None:
        response: dict[str, Any] = {
            "error": result.rejected_reason,
            "detail": result.handoff_readiness.reasons[0] if result.handoff_readiness.reasons else "",
        }
        if result.rejected_reason == "docs_root_not_configured":
            response["hint"] = DOCS_FETCH_HINT
        return response
    response = _validation_to_dict(result)
    eligible = chat_mod._execution_offer_eligible(result)
    response["execution_offer_eligible"] = eligible
    if eligible:
        validation_id = _new_id()
        session.validated[validation_id] = ValidatedCode(
            code=code, readiness_state=result.handoff_readiness.state, docs_root=session.docs_root,
        )
        while len(session.validated) > MAX_VALIDATIONS_PER_SESSION:
            session.validated.popitem(last=False)
        response["validation_id"] = validation_id
        response["code_sha256"] = hashlib.sha256(code.encode("utf-8")).hexdigest()
    return response


@server.tool(annotations=_READ_ONLY)
def gauss_execution_prepare(session_id: str, validation_id: str | None = None) -> dict[str, Any]:
    """Step 1 of 2 in the controlled execution handoff. Prepares exactly
    the code the server itself validated (`validation_id` from
    `gauss_validate_code`, single-use) or, without a validation_id, the
    session's last offer-eligible `gauss_chat_ask` answer. Code is never
    accepted directly here. Returns the exact code, runner, timeout and a
    digest for the human to review, plus the `request_id` to pass to
    `gauss_execution_decide` with the human's answer; nothing is executed by
    this call. Preparing again replaces a still-pending request and says so
    (`replaced_request_id`): only the newest prompt can then be answered. A
    validation_id is spent only by a prepare that returns a prompt; a
    refusal leaves it usable. Real GAUSS (`runner="gauss"`) also requires
    the server to have been started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1."""
    session, error = _use_session(session_id)
    if session is None:
        return error

    # v0.87.0 (live finding 76.x f3): every refusal below happens BEFORE the
    # validation_id is spent. Before this the id was popped first, so a
    # `real_gauss_not_allowed` or `validation_stale` refusal consumed it and
    # a resubmission was told `unknown_or_used_validation_id` -- false, the
    # id had never been used (76.10's client re-validated to recover). The
    # rule is now: an id is spent only by a prepare that returns a prompt
    # (v0.87 plan decision 4), and a refused id gets the same refusal again.
    # The opt-in gate comes first, since it applies to both paths and no id
    # could ever get past it in this server process.
    if session.runner == "gauss" and not _real_gauss_allowed():
        return {"error": "real_gauss_not_allowed", "detail": _REAL_GAUSS_NOT_ALLOWED_DETAIL}

    if validation_id is not None:
        entry = session.validated.get(validation_id)
        if entry is None:
            return {"error": "unknown_or_used_validation_id"}
        # The docs may have changed since validation (e.g. a `gauss-ai docs
        # fetch` in between) -- re-validate rather than trust a stale verdict.
        recheck = engine_mod.validate_code(entry.code, docs_root=entry.docs_root)
        if not chat_mod._execution_offer_eligible(recheck):
            return {"error": "validation_stale", "handoff_readiness": _readiness_dict(recheck.handoff_readiness)}
        code, readiness_state, source = entry.code, recheck.handoff_readiness.state, "validated"
    else:
        if session.pending_code is None or session.pending_readiness_state is None:
            return {"error": "no_pending_handoff_candidate"}
        code, readiness_state, source = session.pending_code, session.pending_readiness_state, "chat"

    try:
        # v0.87.0 (live finding 77.x f3): no `workspace_parent`. The handoff
        # always runs in a fresh temporary directory (v0.78 plan; see
        # `execute_execution_handoff`), so the configured workspace parent
        # was shown in the prompt and bound into the digest without ever
        # being used. Leaving it out keeps the digest to what the prompt
        # shows and the run uses. Guided repair resolves its own.
        request = handoff_mod.create_execution_handoff_request(
            code=code, readiness_state=readiness_state, request_id=str(uuid.uuid4()), created_at=_clock(),
            runner=session.runner, executable_path=session.executable_path,
            timeout_seconds=session.timeout_seconds,
        )
    except (handoff_mod.HandoffNotEligibleError, handoff_mod.HandoffRequestValidationError) as exc:
        return {"error": "request_rejected", "detail": str(exc)}
    if validation_id is not None:
        session.validated.pop(validation_id, None)

    response: dict[str, Any] = {
        "request_id": request.request_id,
        "digest": request.digest,
        "rendered_prompt": handoff_mod.render_execution_handoff_prompt(request),
    }
    # v0.87.0 (live finding 77.x f2): before this a prepare silently
    # replaced a pending request, so a "yes" given to the earlier prompt
    # approved this one (77.1's request was replaced by 77.9's; probe P5).
    # The single slot stays (plan decision 3); the replacement is reported,
    # and the replaced id is remembered only so decide can say why it is
    # refused.
    replaced = session.pending_request
    if replaced is not None:
        session.superseded_request_ids.append(replaced.request_id)
        response["replaced_request_id"] = replaced.request_id
        response["notice"] = (
            f"An earlier prompt (request {replaced.request_id}) was pending and is no longer valid. "
            "Show the user this prompt instead."
        )
    session.pending_request = request
    session.pending_source = source
    return response


@server.tool(annotations=_RUNS_CODE)
def gauss_execution_decide(session_id: str, response_text: str, request_id: str | None = None) -> dict[str, Any]:
    """Step 2 of 2. `response_text` must be the human's own raw answer to
    the prompt `gauss_execution_prepare` returned, and `request_id` must be
    the request_id that prepare returned WITH THAT PROMPT. A missing
    request_id, or one that is not the pending request (for example a
    prompt a later prepare replaced), is refused and creates no approval.
    The answer is parsed server-side by the same narrow parser `gauss-ai
    chat` uses (only "yes"/"approve" or "no"/"decline"; anything else
    returns `outcome: "unrecognized"`, creates no approval, and keeps the
    request pending). On approval, records it and invokes the existing GAUSS
    execution adapter exactly once, in this same call. Every outcome echoes
    the `request_id` and `request_digest` it acted on. If several prompts
    are open, the user names the prompt in a separate message and replies
    with a bare yes or no; never ask the user to label a reply."""
    session, error = _use_session(session_id)
    if session is None:
        return error
    request = session.pending_request
    if request is None:
        return {"error": "no_pending_request"}
    # v0.87.0 (live finding 77.x f2): the reply is bound to the prompt the
    # client says it answers, checked before the reply is parsed or any
    # approval exists. `request_id` is optional in the schema but required
    # in effect (plan decision 2): a client still holding a stale tool
    # description (KL v0.80.0, 70.x) gets this explanation instead of a
    # generic schema error.
    if request_id is None:
        return {
            "error": "request_id_required",
            "detail": (
                "Pass request_id: the request_id gauss_execution_prepare returned with the prompt the user "
                "answered. Nothing was approved; the request is still pending."
            ),
        }
    if request_id != request.request_id:
        if request_id in session.superseded_request_ids:
            return {
                "error": "request_superseded",
                "detail": (
                    "That prompt was replaced by a later gauss_execution_prepare and can no longer be approved. "
                    "Nothing was approved or run. Show the user the pending prompt, or prepare again."
                ),
                "pending_request_id": request.request_id,
            }
        return {
            "error": "request_not_pending",
            "detail": (
                "That request_id is not pending in this session (unknown, or already decided). "
                "Nothing was approved or run."
            ),
        }
    echo = {"request_id": request.request_id, "request_digest": request.digest}

    parsed = handoff_mod.parse_execution_approval_response(response_text)
    if parsed == "unrecognized":
        return {"outcome": "unrecognized", "message": "Please answer exactly 'yes' or 'no'.", **echo}

    try:
        approval = handoff_mod.create_execution_handoff_approval(
            request, decision=parsed, approval_id=str(uuid.uuid4()), decided_at=_clock(),
        )
        session.approval_store.record(approval)
    except handoff_mod.ExecutionApprovalValidationError as exc:
        return {"error": "approval_rejected", "detail": str(exc), **echo}

    if session.pending_source == "chat":
        session.pending_code = None
        session.pending_readiness_state = None
    session.pending_request = None
    session.pending_source = None

    if parsed == "declined":
        return {"outcome": "declined", "consent_statement": approval.consent_statement, **echo}

    helper = handoff_mod.select_helper(request.runner)
    result = handoff_mod.execute_execution_handoff(request, approval, store=session.approval_store, helper=helper)
    return {
        "outcome": result.outcome,
        "launched": result.launched,
        "blocked_reason": result.blocked_reason,
        "result_digest": result.result_digest,
        "rendered": handoff_mod.render_conversational_execution_result(result),
        "evidence": dataclasses.asdict(result.evidence) if result.evidence is not None else None,
        **echo,
    }


@server.tool(annotations=_MANAGES_WORKSPACE)
def gauss_repair_start(
    runner: str | None = None,
    gauss_executable: str | None = None,
    workspace_parent: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Start a guided-repair session, resolving runner/executable/workspace
    exactly as `gauss-ai repair` does. Drive it with `gauss_repair_command`,
    one REPL command at a time (e.g. "workspace create", "request", "plan",
    "confirm <hash>", "execute", "diagnose", "repair-plan",
    "approve-repair <digest>", ... -- the full `gauss-ai repl` command set)."""
    _sweep_sessions()
    config = _get_config()
    env = os.environ
    resolved_runner = config_mod.resolve_default_runner(cli_value=runner, config=config, env=env).value
    resolved_executable = config_mod.resolve_gauss_executable(cli_value=gauss_executable, config=config, env=env).value
    resolved_workspace_parent = config_mod.resolve_workspace_parent(
        cli_value=workspace_parent, config=config, env=env
    ).value

    if resolved_runner == "gauss" and not _real_gauss_allowed():
        return {
            "error": "real_gauss_not_allowed",
            "detail": (
                "Real GAUSS execution via MCP requires the gauss-ai-mcp server process to be started with "
                f"{ENV_ALLOW_REAL_GAUSS}=1."
            ),
        }

    try:
        adapter = cli_mod.InteractiveMvpAdapter(
            workspace_parent=resolved_workspace_parent,
            runner_backend=resolved_runner,
            gauss_executable=resolved_executable,
            session_id=session_id,
        )
    except ValueError as exc:
        return {"error": "configuration_error", "detail": str(exc)}

    sid = adapter.adapter_session_id
    _repair_sessions[sid] = RepairSession(adapter=adapter)
    return {"session_id": sid, "backend": adapter.backend_label}


@server.tool(annotations=_WRITES_WORKSPACE)
def gauss_repair_command(session_id: str, command: str) -> dict[str, Any]:
    """Send one REPL command line to a guided-repair session -- the same
    dispatcher `gauss-ai repl` uses, so every command and decline path
    behaves identically. Errors come back as output lines, never a raised
    exception. "exit" or "quit" closes the session."""
    repair_session, error = _use_repair_session(session_id)
    if repair_session is None:
        return error
    keep_going, output_lines = repair_session.adapter.handle_line(command)
    if not keep_going:
        _close_repair_session(session_id)
    return {"output": output_lines, "session_closed": not keep_going}


@server.tool(annotations=_MANAGES_WORKSPACE)
def gauss_repair_close(session_id: str) -> dict[str, Any]:
    """End a guided-repair session and free its workspace, for a client
    that disconnects without sending "exit"."""
    _sweep_sessions()
    return {"session_id": session_id, "closed": _close_repair_session(session_id)}


# ---------------------------------------------------------------------------
# Opt-in strict-mode chat tools -- registered by `main()` only when the
# configured chat provider is a real model (see module docstring)
# ---------------------------------------------------------------------------


def gauss_chat_ask(session_id: str, question: str) -> dict[str, Any]:
    """Strict mode: ask gauss-ai's own configured model a GAUSS question or
    for GAUSS code. Unlike writing code yourself and validating it, this
    path can refuse to generate code at all for ungrounded topics. Returns
    grounding status, generated code, deterministic validation evidence,
    and whether the answer may be offered for controlled execution
    (`execution_offer_eligible` -- then call `gauss_execution_prepare`
    without a validation_id). Nothing is executed or written."""
    session, error = _use_session(session_id)
    if session is None:
        return error
    if session.engine is None:
        config = _get_config()
        env = os.environ
        provider_name = config_mod.resolve_chat_provider(config=config, env=env).value
        model = config_mod.resolve_chat_model(config=config, env=env).value
        endpoint = config_mod.resolve_ollama_endpoint(config=config, env=env).value
        try:
            build_kwargs: dict[str, Any] = {"model": model}
            if endpoint is not None:
                build_kwargs["endpoint"] = endpoint
            provider = provider_mod.build_provider(provider_name, **build_kwargs)
        except ValueError as exc:
            return {"error": "configuration_error", "detail": str(exc)}
        session.engine = engine_mod.ConversationEngine(provider=provider, docs_root=session.docs_root)
    result = session.engine.ask(question)
    session.pending_code = None
    session.pending_readiness_state = None
    eligible = chat_mod._execution_offer_eligible(result)
    if eligible:
        session.pending_code = result.generated_code[0]
        session.pending_readiness_state = result.handoff_readiness.state
    return _answer_result_to_dict(result, execution_offer_eligible=eligible)


def gauss_chat_reset(session_id: str) -> dict[str, Any]:
    """Strict mode: clear the session's conversation history and any
    pending chat execution offer -- equivalent to `reset` in `gauss-ai chat`."""
    session, error = _use_session(session_id)
    if session is None:
        return error
    if session.engine is not None:
        session.engine.reset()
    session.pending_code = None
    session.pending_readiness_state = None
    return {"session_id": session_id, "reset": True}


def _register_chat_tools(target_server: "MCPServer") -> None:
    target_server.add_tool(gauss_chat_ask, annotations=_ASKS_MODEL)
    target_server.add_tool(gauss_chat_reset, annotations=_READ_ONLY)


def chat_tools_enabled(config: "config_mod.GaussAiConfig", env: dict[str, str]) -> bool:
    """Strict-mode chat is an explicit opt-in: the configured chat provider
    must be a real model. `fake` (the default) never enables it, and a
    running Ollama service is never auto-detected."""
    return config_mod.resolve_chat_provider(config=config, env=env).value != provider_mod.FAKE_PROVIDER


def main(argv: list[str] | None = None) -> int:
    """Runs the gauss-ai MCP server over stdio -- the standard transport for
    a locally-spawned MCP server, with no network/port/TLS surface. Takes
    no CLI flags: configuration comes from `gauss-ai config` and environment
    variables, exactly as for the CLI (plus GAUSS_AI_MCP_ALLOW_REAL_GAUSS)."""
    del argv
    if chat_tools_enabled(_get_config(), dict(os.environ)):
        _register_chat_tools(server)
    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
