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
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

try:
    from mcp.server.mcpserver import MCPServer
except ImportError as exc:  # pragma: no cover - exercised only without the optional extra installed
    raise ImportError(
        "The 'mcp' package is required to run the gauss-ai MCP server. Install it with: "
        'pip install -e ".[mcp]"'
    ) from exc

import gauss_ai_chat as chat_mod
import gauss_ai_config as config_mod
import gauss_chat_provider as provider_mod
import gauss_code_assistant_cli as cli_mod
import gauss_conversation_engine as engine_mod
import gauss_execution_handoff as handoff_mod

__version__ = "0.82.0"

#: Set by the server OPERATOR in the process's own environment before
#: launch -- never read from a tool-call argument. See module docstring.
ENV_ALLOW_REAL_GAUSS = "GAUSS_AI_MCP_ALLOW_REAL_GAUSS"

#: Per-session cap on outstanding validation_ids (oldest evicted first).
MAX_VALIDATIONS_PER_SESSION = 8

DOCS_FETCH_HINT = "Run 'gauss-ai docs fetch' once to download the official GAUSS documentation."


def _real_gauss_allowed(env: dict[str, str] | None = None) -> bool:
    env = env if env is not None else os.environ
    return env.get(ENV_ALLOW_REAL_GAUSS, "").strip() == "1"


def _new_id() -> str:
    return uuid.uuid4().hex


def _clock() -> str:
    return datetime.now(timezone.utc).isoformat()


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


@dataclass
class RepairSession:
    adapter: "cli_mod.InteractiveMvpAdapter"


_sessions: dict[str, Session] = {}
_repair_sessions: dict[str, RepairSession] = {}
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
    }


# ---------------------------------------------------------------------------
# MCP server + always-registered tools
# ---------------------------------------------------------------------------

server = MCPServer(
    name="gauss-ai",
    version=__version__,
    instructions=(
        "GAUSS programming assistant backed by the official GAUSS documentation and deterministic checks. "
        "Recommended flow: gauss_session_start -> gauss_search_docs to look up the functions you need -> write "
        "the GAUSS code yourself -> gauss_validate_code to get a deterministic verdict (signatures, documented "
        "preconditions, syntax, unknown functions, and system-touching statements). Only code that reaches "
        "handoff_candidate gets a validation_id; to run it, call gauss_execution_prepare(validation_id), show the "
        "user the exact prompt it returns, and pass the user's own yes/no to gauss_execution_decide. Never answer "
        "yes on the user's behalf. gauss_repair_* tools drive the guided repair pipeline for real files, one REPL "
        "command per call. gauss_chat_ask exists only when the server is configured with its own model."
    ),
)


@server.tool()
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
    a `session_id` for the other gauss_* tools."""
    config = _get_config()
    env = os.environ
    sid = session_id or _new_id()
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
        "runner": _sessions[sid].runner,
        "docs_root_configured": resolved_docs_root is not None,
    }
    if resolved_docs_root is None:
        response["hint"] = DOCS_FETCH_HINT
    return response


@server.tool()
def gauss_session_close(session_id: str) -> dict[str, Any]:
    """End a session and free its state."""
    existed = _sessions.pop(session_id, None) is not None
    return {"session_id": session_id, "closed": existed}


@server.tool()
def gauss_search_docs(query: str, docs_root: str | None = None) -> dict[str, Any]:
    """Search the official GAUSS documentation (and the verified GAUSS error
    catalog, for codes like G0025) for a natural-language question or
    function names. Returns the matching documentation excerpts to read
    before writing code. Purely local and read-only."""
    resolved = config_mod.resolve_docs_root(cli_value=docs_root, config=_get_config(), env=os.environ).value
    bundle = engine_mod.ground_multi(query, docs_root_str=resolved)
    response: dict[str, Any] = {
        "grounding_status": bundle.status.value,
        "sources": [
            {"source": s.source, "topic": s.topic, "citation": s.citation, "content": s.content}
            for s in bundle.sources
        ],
        "unmatched_topics": list(bundle.unmatched_topics),
        "ambiguous_topics": list(bundle.ambiguous_topics),
        "docs_root_configured": resolved is not None,
    }
    if resolved is None:
        response["hint"] = DOCS_FETCH_HINT + " Until then only error-code lookups can be grounded."
    return response


@server.tool()
def gauss_validate_code(session_id: str, code: str) -> dict[str, Any]:
    """Deterministically validate GAUSS code you wrote: documented
    signatures, documented preconditions, syntax, unknown (possibly
    hallucinated) functions, and system-touching statements. Pass raw GAUSS
    code, not a Markdown block. Nothing is executed. If the result reaches
    handoff_candidate, the response includes a single-use `validation_id`
    for `gauss_execution_prepare`."""
    session = _sessions.get(session_id)
    if session is None:
        return {"error": "unknown_session"}
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


@server.tool()
def gauss_execution_prepare(session_id: str, validation_id: str | None = None) -> dict[str, Any]:
    """Step 1 of 2 in the controlled execution handoff. Prepares exactly
    the code the server itself validated (`validation_id` from
    `gauss_validate_code`, single-use) or, without a validation_id, the
    session's last offer-eligible `gauss_chat_ask` answer. Code is never
    accepted directly here. Returns the exact code, runner, timeout and a
    digest for the human to review; nothing is executed by this call. Real
    GAUSS (`runner="gauss"`) also requires the server to have been started
    with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1."""
    session = _sessions.get(session_id)
    if session is None:
        return {"error": "unknown_session"}

    if validation_id is not None:
        entry = session.validated.pop(validation_id, None)
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

    if session.runner == "gauss" and not _real_gauss_allowed():
        return {
            "error": "real_gauss_not_allowed",
            "detail": (
                "This session is configured for runner 'gauss', but the gauss-ai-mcp server process was not "
                f"started with {ENV_ALLOW_REAL_GAUSS}=1. Real GAUSS execution via MCP requires this explicit "
                "server-operator opt-in, in addition to the per-request approval."
            ),
        }
    try:
        request = handoff_mod.create_execution_handoff_request(
            code=code, readiness_state=readiness_state, request_id=str(uuid.uuid4()), created_at=_clock(),
            runner=session.runner, executable_path=session.executable_path,
            timeout_seconds=session.timeout_seconds, workspace_parent=session.workspace_parent,
        )
    except (handoff_mod.HandoffNotEligibleError, handoff_mod.HandoffRequestValidationError) as exc:
        return {"error": "request_rejected", "detail": str(exc)}
    session.pending_request = request
    session.pending_source = source
    return {
        "request_id": request.request_id,
        "digest": request.digest,
        "rendered_prompt": handoff_mod.render_execution_handoff_prompt(request),
    }


@server.tool()
def gauss_execution_decide(session_id: str, response_text: str) -> dict[str, Any]:
    """Step 2 of 2. `response_text` must be the human's own raw answer to
    the prompt `gauss_execution_prepare` returned -- parsed server-side by
    the same narrow parser `gauss-ai chat` uses (only "yes"/"approve" or
    "no"/"decline"; anything else returns `outcome: "unrecognized"` and
    creates no approval). On approval, records it and invokes the existing
    GAUSS execution adapter exactly once, in this same call."""
    session = _sessions.get(session_id)
    if session is None:
        return {"error": "unknown_session"}
    request = session.pending_request
    if request is None:
        return {"error": "no_pending_request"}
    parsed = handoff_mod.parse_execution_approval_response(response_text)
    if parsed == "unrecognized":
        return {"outcome": "unrecognized", "message": "Please answer exactly 'yes' or 'no'."}

    try:
        approval = handoff_mod.create_execution_handoff_approval(
            request, decision=parsed, approval_id=str(uuid.uuid4()), decided_at=_clock(),
        )
        session.approval_store.record(approval)
    except handoff_mod.ExecutionApprovalValidationError as exc:
        return {"error": "approval_rejected", "detail": str(exc)}

    if session.pending_source == "chat":
        session.pending_code = None
        session.pending_readiness_state = None
    session.pending_request = None
    session.pending_source = None

    if parsed == "declined":
        return {"outcome": "declined", "consent_statement": approval.consent_statement}

    helper = handoff_mod.select_helper(request.runner)
    result = handoff_mod.execute_execution_handoff(request, approval, store=session.approval_store, helper=helper)
    return {
        "outcome": result.outcome,
        "launched": result.launched,
        "blocked_reason": result.blocked_reason,
        "result_digest": result.result_digest,
        "rendered": handoff_mod.render_conversational_execution_result(result),
        "evidence": dataclasses.asdict(result.evidence) if result.evidence is not None else None,
    }


@server.tool()
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


@server.tool()
def gauss_repair_command(session_id: str, command: str) -> dict[str, Any]:
    """Send one REPL command line to a guided-repair session -- the same
    dispatcher `gauss-ai repl` uses, so every command and decline path
    behaves identically. Errors come back as output lines, never a raised
    exception. "exit" or "quit" closes the session."""
    repair_session = _repair_sessions.get(session_id)
    if repair_session is None:
        return {"error": "unknown_session"}
    keep_going, output_lines = repair_session.adapter.handle_line(command)
    if not keep_going:
        repair_session.adapter.close()
        del _repair_sessions[session_id]
    return {"output": output_lines, "session_closed": not keep_going}


@server.tool()
def gauss_repair_close(session_id: str) -> dict[str, Any]:
    """End a guided-repair session and free its workspace, for a client
    that disconnects without sending "exit"."""
    repair_session = _repair_sessions.pop(session_id, None)
    if repair_session is None:
        return {"session_id": session_id, "closed": False}
    repair_session.adapter.close()
    return {"session_id": session_id, "closed": True}


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
    session = _sessions.get(session_id)
    if session is None:
        return {"error": "unknown_session"}
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
    session = _sessions.get(session_id)
    if session is None:
        return {"error": "unknown_session"}
    if session.engine is not None:
        session.engine.reset()
    session.pending_code = None
    session.pending_readiness_state = None
    return {"session_id": session_id, "reset": True}


def _register_chat_tools(target_server: "MCPServer") -> None:
    target_server.add_tool(gauss_chat_ask)
    target_server.add_tool(gauss_chat_reset)


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
