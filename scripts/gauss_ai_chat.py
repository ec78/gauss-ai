"""Interactive conversational GAUSS Q&A loop (v0.70.0), exposed as the
default `gauss-ai` invocation (no subcommand).

This module is orchestration/UI only -- exactly the same convention
`gauss_ai_guided_repair.py` already established. It implements no
grounding logic, no model-request logic, and no conversation-state logic of
its own; every real decision is delegated to `gauss_conversation_engine.
ConversationEngine`, which in turn delegates to `gauss_error_catalog.py`,
`command_doc_lookup.py`, and a `gauss_chat_provider.ModelProvider`. This
file's own job is: resolve configuration precedence (mirroring
`gauss_ai_guided_repair.run_guided_repair`'s own resolution block exactly),
print a banner and prompts, and format an `AnswerResult` for a human to
read -- nothing more.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Callable

import gauss_ai_config as config_mod
import gauss_chat_provider as provider_mod
import gauss_conversation_engine as engine_mod
import gauss_execution_handoff as handoff_mod
import gauss_pre_execution_validation as validation_mod

BANNER = "GAUSS AI Assistant"

HELP_TEXT: tuple[str, ...] = (
    "Ask a GAUSS question in plain language, for example:",
    "  What does reshape do?",
    "  What does error G0036 mean?",
    "",
    "Or ask for GAUSS code, for example:",
    "  Show me how to reshape a matrix to 4 columns.",
    "  Write GAUSS code to estimate an OLS regression.",
    "  Can you give me an example using reshape and meanc?",
    "Generated code is always labeled with whether it's grounded in official documentation, and is",
    "never verified or written to a file -- see docs/conversational-code-generation.md. This chat",
    "does not execute code on its own initiative under any circumstances.",
    "",
    "When generated code reaches HANDOFF_CANDIDATE readiness (the strongest deterministic evidence",
    "level), you may type 'run this' or 'execute this' to review the exact code and execution details",
    "and explicitly approve a single controlled execution -- see docs/controlled-execution-handoff.md.",
    "Nothing is ever executed without that explicit, per-request approval; a decline, a changed",
    "answer, or a prior execution never carries approval forward to a new request.",
    "",
    "Commands:",
    "  help           Show this message",
    "  reset / new    Start a new conversation (clears history)",
    "  exit / quit    Leave the assistant",
    "",
    "This chat does not edit files or apply repairs, and does not execute code except through the",
    "explicit, per-request controlled-execution approval described above. For file-based repair, use:",
    "  gauss-ai repair <file.gss>",
)


def _render_grounding_disclosure(result: "engine_mod.AnswerResult") -> str:
    """v0.72.0: handles single-source (unchanged legacy wording, still
    exactly what every pre-v0.72.0 test/evaluation transcript expects),
    multi-source, and partial-grounding disclosure lines. The status and
    source list are read directly off `result` -- computed by the grounding
    layer, never guessed from the rendered text."""
    sources = result.grounding_sources
    if result.grounding_status == "grounded" and len(sources) == 1:
        src = sources[0]
        if src.source == "error_catalog":
            return f"[Grounded in this repository's verified error catalog: {src.topic}]"
        return f"[Grounded in local official GAUSS documentation: {src.topic}]"
    if result.grounding_status == "grounded" and len(sources) > 1:
        catalog_topics = [s.topic for s in sources if s.source == "error_catalog"]
        doc_topics = [s.topic for s in sources if s.source == "official_docs"]
        parts = []
        if catalog_topics:
            parts.append(f"this repository's verified error catalog ({', '.join(catalog_topics)})")
        if doc_topics:
            parts.append(f"local official GAUSS documentation ({', '.join(doc_topics)})")
        return f"[Grounded in {' and '.join(parts)}]"
    if result.grounding_status == "partially_grounded":
        grounded_names = ", ".join(s.topic for s in sources) if sources else "none"
        unsupported_names = ", ".join(f"`{t}`" for t in result.unsupported_topics)
        return (
            f"[Partially grounded: {grounded_names} documented; {unsupported_names} not found in the "
            "configured GAUSS documentation or verified error catalog]"
        )
    if result.grounding_source == "uncataloged_error_code":
        return (
            f"[{result.grounding_topic} is not yet in this repository's verified error catalog -- the answer "
            "below is not documentation-grounded]"
        )
    return "[Not grounded in official documentation or the verified error catalog -- from the model's own general knowledge]"


def _render_answer(print_fn: Callable[[str], None], result: "engine_mod.AnswerResult") -> None:
    if result.provider_name == "none":
        # The fixed execution-boundary redirect -- not an answer from any
        # knowledge source, so no grounding disclosure applies.
        print_fn(result.text)
        print_fn("")
        return

    if not result.provider_success:
        print_fn(result.text)
        print_fn("")
        return

    print_fn(_render_grounding_disclosure(result))
    if result.unknown_symbols:
        # v0.73.0 Phase 8/19: the post-generation symbol check found a
        # call-shaped symbol in the generated code that is not a grounded/
        # resolved topic, a known language construct, or plausibly user-
        # defined -- disclosed regardless of the pre-generation grounding
        # status, since that status describes retrieval evidence, not
        # whether the model actually stayed within it.
        unknown_list = ", ".join(f"`{s}`" for s in result.unknown_symbols)
        print_fn(
            f"[Warning: the generated code also calls {unknown_list}, which is not a documented function this "
            "session could verify -- treat it as unverified, not authoritative GAUSS syntax.]"
        )
    if result.pre_execution_eligibility is not None:
        # v0.74.0 Phase 20: deterministic pre-execution validation evidence
        # -- signature compatibility, documented preconditions, and an
        # explicit eligibility verdict. Never implies real GAUSS execution
        # occurred; the fixed "not executed" footer above/below this still
        # applies regardless of what this reports.
        print_fn(validation_mod.render_validation_report(
            eligibility=result.pre_execution_eligibility, unresolved_issues=result.pre_execution_issues,
            call_validations=result.call_validations, preconditions=result.precondition_checks,
            companion_hints=result.companion_hints, parameter_role_checks=result.parameter_role_checks,
            predicted_output=result.predicted_output, coverage=result.validation_coverage,
            syntax=result.syntax_validation, readiness=result.handoff_readiness,
            system_statements=result.system_statements,
        ))
    print_fn("")
    print_fn(result.text)
    print_fn("")
    if _execution_offer_eligible(result):
        print_fn(
            "This code has reached HANDOFF_CANDIDATE readiness -- the strongest deterministic evidence level. "
            "Type 'run this' or 'execute this' to review the exact code and execution details and explicitly "
            "approve a single controlled execution."
        )
        print_fn("")


def _execution_offer_eligible(result: "engine_mod.AnswerResult") -> bool:
    """Deterministic gate for OFFERING a controlled-execution handoff --
    never a decision to execute anything. Requires exactly one generated
    code block (v0.78.0's deliberate single-snippet scope narrowing, see
    planning/v0.78-controlled-execution-handoff.md Section 7) and a current
    `HandoffReadiness.HANDOFF_CANDIDATE` verdict, computed entirely upstream
    by `gauss_pre_execution_validation.compute_handoff_readiness(...)` --
    this function reads that verdict, it never computes or overrides it."""
    return (
        result.handoff_readiness is not None
        and result.handoff_readiness.state == validation_mod.HandoffReadiness.HANDOFF_CANDIDATE.value
        and len(result.generated_code) == 1
    )


def _startup_status_lines(engine: "engine_mod.ConversationEngine") -> tuple[str, ...]:
    """Reports the resolved provider/model/grounding status for whichever
    provider is actually in use -- generalizes the v0.70.0 fake-provider-only
    notice (v0.71.0 Phase 6) so a real provider's user gets the same clarity
    a fake-provider user always had, and grounding is never claimed unless
    `docs_root` is actually configured."""
    provider = engine.provider
    lines: list[str] = []
    if isinstance(provider, provider_mod.FakeModelProvider):
        lines.append(
            "Provider: fake/test (deterministic, no network, no API key) -- answers are limited to raw "
            "retrieved documentation/catalog text, never synthesized prose."
        )
        lines.append("To use a real model: gauss-ai config set chat-provider ollama   (local, no API key)")
        lines.append("                  or: gauss-ai config set chat-provider anthropic  (cloud, needs an API key)")
    elif isinstance(provider, provider_mod.OllamaProvider):
        model = provider.model or provider_mod.DEFAULT_OLLAMA_MODEL
        endpoint = provider.endpoint or provider_mod.DEFAULT_OLLAMA_ENDPOINT
        lines.append(f"Provider: ollama (local)  Model: {model}")
        lines.append(f"Endpoint: {endpoint} -- run 'gauss-ai doctor' if this provider is unreachable.")
    elif isinstance(provider, provider_mod.AnthropicMessagesProvider):
        model = provider.model or "(provider default)"
        lines.append(f"Provider: anthropic (cloud)  Model: {model}")
    else:
        lines.append(f"Provider: {type(provider).__name__}")
    if engine.docs_root:
        lines.append(f"GAUSS documentation: configured ({engine.docs_root})")
    else:
        lines.append(
            "GAUSS documentation: not configured -- answers about specific commands will not be grounded in "
            "official docs. See docs/gauss-documentation-setup.md, or run: gauss-ai config set docs-root <path>"
        )
    return tuple(lines)


def _default_id_fn() -> str:
    return str(uuid.uuid4())


def _default_clock_fn() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_execution_handoff_settings(
    *,
    cli_runner: str | None,
    cli_gauss_executable: str | None,
    cli_workspace_parent: str | None,
    cli_timeout_seconds: float | None,
    config: "config_mod.GaussAiConfig",
    env: dict[str, str] | None,
) -> tuple[str, str | None, str | None, float]:
    """Mirrors `gauss_ai_guided_repair.run_guided_repair`'s own resolution
    block exactly, reusing the same config primitives -- no new resolution
    logic, no new config field. Returns (runner, executable_path,
    workspace_parent, timeout_seconds)."""
    runner = config_mod.resolve_default_runner(cli_value=cli_runner, config=config, env=env).value
    executable_path = config_mod.resolve_gauss_executable(cli_value=cli_gauss_executable, config=config, env=env).value
    workspace_parent = config_mod.resolve_workspace_parent(cli_value=cli_workspace_parent, config=config, env=env).value
    timeout_seconds = config_mod.resolve_default_timeout_seconds(
        cli_value=cli_timeout_seconds, config=config, env=env
    ).value
    return runner, executable_path, workspace_parent, timeout_seconds


def _run_execution_handoff_flow(
    *,
    code: str,
    readiness_state: str,
    prompt_fn: Callable[[str], str],
    print_fn: Callable[[str], None],
    store: "handoff_mod.ExecutionHandoffApprovalStore",
    runner: str,
    executable_path: str | None,
    workspace_parent: str | None,
    timeout_seconds: float,
    id_fn: Callable[[], str],
    clock_fn: Callable[[], str],
) -> None:
    """Phases 4-13 of the milestone brief, in one linear, non-looping flow:
    build the request, display it, parse an explicit approval response
    (bounded retries, never coerced), and only on an actual `\"approved\"`
    parse result, build the approval and execute exactly once through the
    existing `gauss_execution_adapter.GaussExecutionAdapter` (via
    `gauss_execution_handoff.execute_execution_handoff`). Never retries,
    never repairs, never constructs a second request or approval."""
    try:
        request = handoff_mod.create_execution_handoff_request(
            code=code, readiness_state=readiness_state, request_id=id_fn(), created_at=clock_fn(),
            runner=runner, executable_path=executable_path, timeout_seconds=timeout_seconds,
            workspace_parent=workspace_parent,
        )
    except (handoff_mod.HandoffNotEligibleError, handoff_mod.HandoffRequestValidationError) as exc:
        print_fn(f"Cannot prepare this execution: {exc}")
        if runner == "gauss" and not executable_path:
            print_fn("Run 'gauss-ai config set gauss-executable <path>' or 'gauss-ai doctor' to fix this.")
        print_fn("")
        return

    print_fn(handoff_mod.render_execution_handoff_prompt(request))

    decision: str | None = None
    for attempt in range(2):
        response = prompt_fn("approve execution [yes/no]> ")
        parsed = handoff_mod.parse_execution_approval_response(response)
        if parsed in ("approved", "declined"):
            decision = parsed
            break
        if attempt == 0:
            print_fn("Please answer exactly 'yes' or 'no'.")
    if decision is None:
        print_fn("Execution not approved -- cancelling. No code was executed.")
        print_fn("")
        return

    approval = handoff_mod.create_execution_handoff_approval(
        request, decision=decision, approval_id=id_fn(), decided_at=clock_fn(),
    )
    store.record(approval)

    if decision == "declined":
        print_fn(approval.consent_statement)
        print_fn("")
        return

    helper = handoff_mod.select_helper(request.runner)
    result = handoff_mod.execute_execution_handoff(request, approval, store=store, helper=helper)
    print_fn(handoff_mod.render_conversational_execution_result(result))
    print_fn("")


def run_chat(
    *,
    prompt_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
    cli_provider: str | None = None,
    cli_model: str | None = None,
    cli_docs_root: str | None = None,
    cli_ollama_endpoint: str | None = None,
    cli_runner: str | None = None,
    cli_gauss_executable: str | None = None,
    cli_workspace_parent: str | None = None,
    cli_timeout_seconds: float | None = None,
    config: "config_mod.GaussAiConfig | None" = None,
    env: dict[str, str] | None = None,
    engine: "engine_mod.ConversationEngine | None" = None,
    approval_store: "handoff_mod.ExecutionHandoffApprovalStore | None" = None,
    id_fn: Callable[[], str] = _default_id_fn,
    clock_fn: Callable[[], str] = _default_clock_fn,
) -> "engine_mod.ConversationEngine | None":
    """Runs the interactive chat loop against `engine` if supplied (tests
    always supply their own, so they can inspect its state afterward and so
    no real provider is ever constructed in a test), otherwise resolves
    configuration precedence and constructs one. Returns `None` only on a
    configuration error (an unrecognized `chat_provider` value) -- never
    raises, mirroring `gauss_ai_guided_repair.run_guided_repair`'s own
    error-handling convention exactly."""
    resolved_config = config if config is not None else config_mod.load_config()
    if engine is None:
        provider_name = config_mod.resolve_chat_provider(cli_value=cli_provider, config=resolved_config, env=env).value
        model = config_mod.resolve_chat_model(cli_value=cli_model, config=resolved_config, env=env).value
        docs_root = config_mod.resolve_docs_root(cli_value=cli_docs_root, config=resolved_config, env=env).value
        endpoint = config_mod.resolve_ollama_endpoint(cli_value=cli_ollama_endpoint, config=resolved_config, env=env).value
        try:
            build_kwargs = {"model": model}
            if endpoint is not None:
                build_kwargs["endpoint"] = endpoint
            provider = provider_mod.build_provider(provider_name, **build_kwargs)
        except ValueError as exc:
            print_fn(f"Configuration error: {exc}")
            print_fn(
                "Run 'gauss-ai config set chat-provider fake', 'gauss-ai config set chat-provider ollama', or "
                "'gauss-ai config set chat-provider anthropic'."
            )
            return None
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=docs_root)

    print_fn(BANNER)
    print_fn("")
    for line in _startup_status_lines(engine):
        print_fn(line)
    print_fn("")
    print_fn("Type a GAUSS question, or 'help' for more, 'exit' to leave.")
    print_fn("")

    store = approval_store if approval_store is not None else handoff_mod.ExecutionHandoffApprovalStore()
    #: The most recently answered HANDOFF_CANDIDATE single-code-block turn,
    #: or `None`. Deliberately re-derived from the LATEST answer only (reset
    #: on every `engine.ask(...)` call, including a non-code-shaped one) --
    #: this is what guarantees "the exact code should already be visible
    #: immediately above" (Phase 23): a stale offer from several turns ago
    #: can never be silently executed. This is plain local UI-loop state,
    #: not conversation-engine state -- gauss_conversation_engine.py is not
    #: modified by this milestone and knows nothing about execution.
    pending_handoff: tuple[str, str] | None = None

    while True:
        try:
            line = prompt_fn("> ")
        except EOFError:
            print_fn("")
            break
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if lowered in {"exit", "quit"}:
            break
        if lowered == "help":
            for text in HELP_TEXT:
                print_fn(text)
            continue
        if lowered in {"reset", "new"}:
            engine.reset()
            pending_handoff = None
            print_fn("Conversation reset -- starting fresh.")
            print_fn("")
            continue
        if config_mod.looks_like_cli_invocation(stripped):
            print_fn(
                f"'{stripped}' looks like a gauss-ai command, not a question -- this chat cannot run it. "
                "Exit this chat (type 'exit') and run it in your terminal instead."
            )
            print_fn("")
            continue
        if handoff_mod.looks_like_execution_request(stripped):
            # v0.78.0: this deliberately takes priority over
            # gauss_conversation_engine.py's own, broader, pre-existing
            # "execution-imperative question" detector (which matches e.g.
            # exactly "run this"/"execute this" among other phrases and
            # returns the fixed EXECUTION_BOUNDARY_MESSAGE). That detector
            # is unmodified and still applies to every OTHER phrasing it
            # recognizes (e.g. "run this script", "execute that") and to
            # these same exact phrases whenever no HANDOFF_CANDIDATE is
            # pending would also be handled here (see the message below) --
            # never silently falling through to a stale/incorrect "cannot
            # execute" claim once a controlled path genuinely exists.
            if pending_handoff is None:
                print_fn(
                    "There is no HANDOFF_CANDIDATE code available to execute right now -- ask for GAUSS code "
                    "first, and this offer will appear once it reaches that readiness level."
                )
                print_fn("")
                continue
            runner, executable_path, workspace_parent, timeout_seconds = _resolve_execution_handoff_settings(
                cli_runner=cli_runner, cli_gauss_executable=cli_gauss_executable,
                cli_workspace_parent=cli_workspace_parent, cli_timeout_seconds=cli_timeout_seconds,
                config=resolved_config, env=env,
            )
            code, readiness_state = pending_handoff
            _run_execution_handoff_flow(
                code=code, readiness_state=readiness_state, prompt_fn=prompt_fn, print_fn=print_fn, store=store,
                runner=runner, executable_path=executable_path, workspace_parent=workspace_parent,
                timeout_seconds=timeout_seconds, id_fn=id_fn, clock_fn=clock_fn,
            )
            continue
        result = engine.ask(stripped)
        _render_answer(print_fn, result)
        pending_handoff = (
            (result.generated_code[0], result.handoff_readiness.state)
            if _execution_offer_eligible(result)
            else None
        )

    return engine
