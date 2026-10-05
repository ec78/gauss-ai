"""Local MCP (Model Context Protocol) server for gauss-ai (v0.79.0) -- exposes
the existing conversational assistant and guided repair pipeline as MCP
tools for other local MCP clients (Claude Code, Claude Desktop) to call over
stdio.

This module is orchestration/transport glue ONLY, exactly the same
convention `gauss_ai_chat.py` and `gauss_ai_guided_repair.py` already
established for their own front-ends. It implements no grounding logic, no
model-request logic, no readiness/eligibility computation, no digest/
approval logic, and no repair-pipeline logic of its own -- every real
decision is delegated to the EXISTING, unmodified modules:
`gauss_conversation_engine.ConversationEngine` (conversational QA/codegen),
`gauss_execution_handoff` (the v0.78.0 controlled execution bridge), and
`gauss_code_assistant_cli.InteractiveMvpAdapter` (the guided repair REPL).

Hard boundaries (structurally enforced and tested, see
test_gauss_mcp_server.py):

- This module never recomputes a `HandoffReadiness` verdict, never
  reimplements digest/approval logic, and never redefines
  `InteractiveMvpAdapter` -- it only reads fields already computed by the
  modules above and forwards calls to them, exactly as
  `gauss_ai_chat._execution_offer_eligible` already does (imported and
  reused here directly rather than duplicated, despite the leading
  underscore -- a deliberate choice to single-source this safety gate
  rather than risk two copies silently drifting apart).
- A chat session's pending execution-handoff code/readiness state is read
  ONLY from the session's own last `ConversationEngine.ask(...)` result --
  never accepted as a caller-supplied tool argument. An MCP client cannot
  assert its own readiness state or inject arbitrary code into the
  execution-handoff flow.
- Real GAUSS execution (`runner="gauss"`) additionally requires the server
  OPERATOR to have set `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1` in the server
  process's own environment at startup -- an extra, server-side-only gate on
  top of the existing per-request digest/approval flow, since an MCP client
  is one step further removed from the human at the keyboard than a
  terminal user typing `--runner gauss` directly.
- Every session (`ChatSession`, `RepairSession`) is process-local, in-memory
  only, exactly like `gauss_execution_handoff.ExecutionHandoffApprovalStore`
  and `gauss_repair_application_approval.ApplicationApprovalStore` -- no
  persistence, nothing shared across server processes.

The `mcp` package (https://pypi.org/project/mcp/) is an OPTIONAL runtime
dependency (`pip install -e ".[mcp]"`) -- importing this module without it
installed raises a clear `ImportError` naming the extra to install, instead
of the SDK's own bare `ModuleNotFoundError`. The base `gauss-ai` CLI itself
(`gauss_ai_cli.py`) only imports this module lazily, inside its `mcp`
subcommand, so it remains fully usable with zero third-party dependencies
regardless of whether this extra is installed.
"""

from __future__ import annotations

import atexit
import dataclasses
import os
import uuid
from dataclasses import dataclass
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

__version__ = "0.79.0"

#: Set by the server OPERATOR in the process's own environment before
#: launch -- never read from a tool-call argument, and never anything an
#: MCP client can set remotely. See module docstring.
ENV_ALLOW_REAL_GAUSS = "GAUSS_AI_MCP_ALLOW_REAL_GAUSS"


def _real_gauss_allowed(env: dict[str, str] | None = None) -> bool:
    env = env if env is not None else os.environ
    return env.get(ENV_ALLOW_REAL_GAUSS, "").strip() == "1"


def _new_session_id() -> str:
    return uuid.uuid4().hex


def _default_id_fn() -> str:
    return str(uuid.uuid4())


def _default_clock_fn() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Session state -- process-local, in-memory only (see module docstring)
# ---------------------------------------------------------------------------


@dataclass
class ChatSession:
    engine: "engine_mod.ConversationEngine"
    approval_store: "handoff_mod.ExecutionHandoffApprovalStore"
    runner: str
    executable_path: str | None
    workspace_parent: str | None
    timeout_seconds: float
    #: The single generated code block and readiness state from the most
    #: recent `ask(...)` call that reached `_execution_offer_eligible(...)`,
    #: or `None`. Reset on every `ask(...)` call, mirroring
    #: `gauss_ai_chat.run_chat`'s own `pending_handoff` loop variable exactly
    #: -- a stale offer from an earlier turn can never be silently executed.
    pending_code: str | None = None
    pending_readiness_state: str | None = None
    #: The in-flight `ExecutionHandoffRequest` awaiting a yes/no decision via
    #: `gauss_execution_decide`, or `None`.
    pending_request: "handoff_mod.ExecutionHandoffRequest | None" = None


@dataclass
class RepairSession:
    adapter: "cli_mod.InteractiveMvpAdapter"


_chat_sessions: dict[str, ChatSession] = {}
_repair_sessions: dict[str, RepairSession] = {}
_config: "config_mod.GaussAiConfig | None" = None


def _get_config() -> "config_mod.GaussAiConfig":
    """Loaded once per server process, not once per tool call -- avoids
    redundant disk reads on every chat/repair turn."""
    global _config
    if _config is None:
        _config = config_mod.load_config()
    return _config


def _close_all_sessions() -> None:
    """Registered with `atexit` so an abrupt stdio disconnect still cleans
    up every live repair session's real `tempfile.TemporaryDirectory`/SQLite
    state -- there is no terminal EOF here to trigger the REPL's own
    `finally: adapter.close()` (see `gauss_code_assistant_cli.run_repl`)."""
    for session in list(_repair_sessions.values()):
        try:
            session.adapter.close()
        except Exception:  # noqa: BLE001 - best-effort cleanup only, never raises during shutdown
            pass
    _repair_sessions.clear()
    _chat_sessions.clear()


atexit.register(_close_all_sessions)


def _answer_result_to_dict(result: "engine_mod.AnswerResult", *, execution_offer_eligible: bool) -> dict[str, Any]:
    """Flattens the fields of `AnswerResult` a client actually needs into a
    JSON-serializable dict -- never returns a raw dataclass/object by
    reference. Deliberately curated, not a blanket `dataclasses.asdict`,
    since several fields (`call_validations`, `precondition_checks`, etc.)
    are internal validation evidence already summarized by
    `pre_execution_eligibility`/`pre_execution_issues` for a tool caller's
    purposes."""
    handoff_readiness = None
    if result.handoff_readiness is not None:
        handoff_readiness = {
            "state": result.handoff_readiness.state,
            "reasons": list(result.handoff_readiness.reasons),
        }
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
        "handoff_readiness": handoff_readiness,
        "execution_offer_eligible": execution_offer_eligible,
    }


# ---------------------------------------------------------------------------
# MCP server + tools
# ---------------------------------------------------------------------------

server = MCPServer(
    name="gauss-ai",
    version=__version__,
    instructions=(
        "Conversational GAUSS assistant and guided repair pipeline. Chat tools answer GAUSS questions and "
        "generate code grounded in local official documentation, never executing anything on their own "
        "initiative. When a chat answer reaches HANDOFF_CANDIDATE readiness, gauss_execution_prepare / "
        "gauss_execution_decide offer a single, explicitly-approved, digest-bound execution of that exact "
        "code -- the same controlled bridge the gauss-ai CLI chat already uses. gauss_repair_* tools drive "
        "the full guided execute-diagnose-repair-verify-review pipeline for one file, one REPL command per "
        "call, so a human can approve or decline at every step."
    ),
)


@server.tool()
def gauss_chat_start(
    provider: str | None = None,
    model: str | None = None,
    docs_root: str | None = None,
    ollama_endpoint: str | None = None,
    runner: str | None = None,
    gauss_executable: str | None = None,
    workspace_parent: str | None = None,
    timeout_seconds: float | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Start a new gauss-ai conversational session (GAUSS Q&A and code
    generation). Resolves provider/model/docs-root/runner/executable exactly
    as `gauss-ai chat` does on the command line (CLI argument > environment
    variable > config file > default), so a session with no arguments picks
    up whatever this machine's `gauss-ai config` already has set. Returns a
    `session_id` to pass to every other `gauss_chat_*`/`gauss_execution_*`
    tool."""
    config = _get_config()
    env = os.environ
    provider_name = config_mod.resolve_chat_provider(cli_value=provider, config=config, env=env).value
    resolved_model = config_mod.resolve_chat_model(cli_value=model, config=config, env=env).value
    resolved_docs_root = config_mod.resolve_docs_root(cli_value=docs_root, config=config, env=env).value
    endpoint = config_mod.resolve_ollama_endpoint(cli_value=ollama_endpoint, config=config, env=env).value
    try:
        build_kwargs: dict[str, Any] = {"model": resolved_model}
        if endpoint is not None:
            build_kwargs["endpoint"] = endpoint
        provider_obj = provider_mod.build_provider(provider_name, **build_kwargs)
    except ValueError as exc:
        return {"error": "configuration_error", "detail": str(exc)}

    resolved_runner = config_mod.resolve_default_runner(cli_value=runner, config=config, env=env).value
    resolved_executable = config_mod.resolve_gauss_executable(cli_value=gauss_executable, config=config, env=env).value
    resolved_workspace_parent = config_mod.resolve_workspace_parent(
        cli_value=workspace_parent, config=config, env=env
    ).value
    resolved_timeout = config_mod.resolve_default_timeout_seconds(
        cli_value=timeout_seconds, config=config, env=env
    ).value

    engine = engine_mod.ConversationEngine(provider=provider_obj, docs_root=resolved_docs_root)
    sid = session_id or _new_session_id()
    _chat_sessions[sid] = ChatSession(
        engine=engine,
        approval_store=handoff_mod.ExecutionHandoffApprovalStore(),
        runner=resolved_runner,
        executable_path=resolved_executable,
        workspace_parent=resolved_workspace_parent,
        timeout_seconds=resolved_timeout,
    )
    return {
        "session_id": sid,
        "provider": provider_name,
        "model": resolved_model,
        "docs_root_configured": resolved_docs_root is not None,
    }


@server.tool()
def gauss_chat_ask(session_id: str, question: str) -> dict[str, Any]:
    """Ask one GAUSS question or request GAUSS code in a session started by
    `gauss_chat_start`. Returns the grounding status, any generated code,
    deterministic pre-execution validation evidence, and whether this answer
    is eligible for a controlled-execution offer (`execution_offer_eligible`
    -- read `gauss_execution_prepare`'s docstring next if so). Generated
    code is never executed, verified, or written to a file by this tool."""
    session = _chat_sessions.get(session_id)
    if session is None:
        return {"error": "unknown_session"}
    result = session.engine.ask(question)
    session.pending_code = None
    session.pending_readiness_state = None
    session.pending_request = None
    eligible = chat_mod._execution_offer_eligible(result)
    if eligible:
        session.pending_code = result.generated_code[0]
        session.pending_readiness_state = result.handoff_readiness.state
    return _answer_result_to_dict(result, execution_offer_eligible=eligible)


@server.tool()
def gauss_chat_reset(session_id: str) -> dict[str, Any]:
    """Clear a chat session's conversation history and any pending
    execution offer -- equivalent to the `reset`/`new` command in
    `gauss-ai chat`."""
    session = _chat_sessions.get(session_id)
    if session is None:
        return {"error": "unknown_session"}
    session.engine.reset()
    session.pending_code = None
    session.pending_readiness_state = None
    session.pending_request = None
    return {"session_id": session_id, "reset": True}


@server.tool()
def gauss_chat_close(session_id: str) -> dict[str, Any]:
    """End a chat session and free its state."""
    existed = _chat_sessions.pop(session_id, None) is not None
    return {"session_id": session_id, "closed": existed}


@server.tool()
def gauss_execution_prepare(session_id: str) -> dict[str, Any]:
    """Step 1 of 2 in the controlled execution handoff. Only usable
    immediately after a `gauss_chat_ask` reply with
    `execution_offer_eligible: true` -- the code and readiness state come
    ONLY from that session's own last answer, never from a caller-supplied
    argument, so a client cannot assert its own readiness verdict. Returns
    the exact code, runner, executable, timeout, and a request digest for a
    human to review before deciding; nothing is executed by this call.
    Real GAUSS execution (`runner="gauss"`) additionally requires this
    server process to have been started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1."""
    session = _chat_sessions.get(session_id)
    if session is None:
        return {"error": "unknown_session"}
    if session.pending_code is None or session.pending_readiness_state is None:
        return {"error": "no_pending_handoff_candidate"}
    if session.runner == "gauss" and not _real_gauss_allowed():
        return {
            "error": "real_gauss_not_allowed",
            "detail": (
                "This session is configured for runner 'gauss', but the gauss-ai-mcp server process was not "
                f"started with {ENV_ALLOW_REAL_GAUSS}=1. Real GAUSS execution via MCP requires this explicit "
                "server-operator opt-in, in addition to the per-request approval below."
            ),
        }
    try:
        request = handoff_mod.create_execution_handoff_request(
            code=session.pending_code,
            readiness_state=session.pending_readiness_state,
            request_id=_default_id_fn(),
            created_at=_default_clock_fn(),
            runner=session.runner,
            executable_path=session.executable_path,
            timeout_seconds=session.timeout_seconds,
            workspace_parent=session.workspace_parent,
        )
    except (handoff_mod.HandoffNotEligibleError, handoff_mod.HandoffRequestValidationError) as exc:
        return {"error": "request_rejected", "detail": str(exc)}
    session.pending_request = request
    return {
        "request_id": request.request_id,
        "digest": request.digest,
        "rendered_prompt": handoff_mod.render_execution_handoff_prompt(request),
    }


@server.tool()
def gauss_execution_decide(session_id: str, response_text: str) -> dict[str, Any]:
    """Step 2 of 2 in the controlled execution handoff. `response_text` is
    the human's raw yes/no answer to the prompt `gauss_execution_prepare`
    returned -- parsed server-side via the same narrow, deterministic parser
    `gauss-ai chat` uses (only exactly "yes"/"approve" or "no"/"decline";
    anything else comes back as `outcome: "unrecognized"` and creates no
    approval). On an approved decision, this immediately records the
    approval and, in the same call, invokes the existing GAUSS execution
    adapter exactly once -- this is the real execution bridge; it is not
    advisory-only."""
    session = _chat_sessions.get(session_id)
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
            request, decision=parsed, approval_id=_default_id_fn(), decided_at=_default_clock_fn()
        )
        session.approval_store.record(approval)
    except handoff_mod.ExecutionApprovalValidationError as exc:
        return {"error": "approval_rejected", "detail": str(exc)}

    session.pending_request = None
    session.pending_code = None
    session.pending_readiness_state = None

    if parsed == "declined":
        return {"outcome": "declined", "consent_statement": approval.consent_statement}

    helper = handoff_mod.select_helper(request.runner)
    result = handoff_mod.execute_execution_handoff(request, approval, store=session.approval_store, helper=helper)
    evidence = dataclasses.asdict(result.evidence) if result.evidence is not None else None
    return {
        "outcome": result.outcome,
        "launched": result.launched,
        "blocked_reason": result.blocked_reason,
        "result_digest": result.result_digest,
        "rendered": handoff_mod.render_conversational_execution_result(result),
        "evidence": evidence,
    }


@server.tool()
def gauss_repair_start(
    runner: str | None = None,
    gauss_executable: str | None = None,
    workspace_parent: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Start a new guided-repair session for one file, resolving
    runner/executable/workspace-parent exactly as `gauss-ai repair` does.
    Returns a `session_id` to drive with `gauss_repair_command`, one REPL
    command at a time (e.g. "workspace create", "request", "plan",
    "confirm <hash>", "execute", "diagnose", "repair-plan",
    "approve-repair <digest>", ... -- the full command set `gauss-ai repl`'s
    own `help` command lists is available here unchanged)."""
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
    """Send one REPL command line to a guided-repair session started by
    `gauss_repair_start` -- the exact same dispatcher `gauss-ai repl` uses,
    so every command (and every decline path -- `decline-repair`,
    `decline-repair-draft`, `decline-repair-application`) behaves
    identically. Errors come back as ordinary output lines, never a raised
    exception. `command: "exit"` or `"quit"` closes and frees the session."""
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
    """Explicitly end a guided-repair session and free its workspace/state,
    for a client that disconnects without sending "exit"."""
    repair_session = _repair_sessions.pop(session_id, None)
    if repair_session is None:
        return {"session_id": session_id, "closed": False}
    repair_session.adapter.close()
    return {"session_id": session_id, "closed": True}


def main(argv: list[str] | None = None) -> int:
    """Runs the gauss-ai MCP server over stdio -- the standard transport for
    a locally-spawned MCP server, with no network/port/TLS surface to
    operate. Takes no CLI flags: every tool already resolves its own
    provider/runner/docs/executable configuration via the same
    CLI-argument > environment-variable > config-file > default precedence
    `gauss-ai chat`/`gauss-ai repair` use, per-call, so there is nothing new
    to configure at process startup beyond the existing `gauss-ai config`
    file and environment variables (plus GAUSS_AI_MCP_ALLOW_REAL_GAUSS, see
    module docstring)."""
    del argv
    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
