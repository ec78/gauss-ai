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

from typing import Callable

import gauss_ai_config as config_mod
import gauss_chat_provider as provider_mod
import gauss_conversation_engine as engine_mod
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
    "never executed, verified, or written to a file -- see docs/conversational-code-generation.md.",
    "",
    "Commands:",
    "  help           Show this message",
    "  reset / new    Start a new conversation (clears history)",
    "  exit / quit    Leave the assistant",
    "",
    "This chat does not execute GAUSS code, edit files, or apply repairs. For that, use:",
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
            companion_hints=result.companion_hints,
        ))
    print_fn("")
    print_fn(result.text)
    print_fn("")


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


def run_chat(
    *,
    prompt_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
    cli_provider: str | None = None,
    cli_model: str | None = None,
    cli_docs_root: str | None = None,
    cli_ollama_endpoint: str | None = None,
    config: "config_mod.GaussAiConfig | None" = None,
    env: dict[str, str] | None = None,
    engine: "engine_mod.ConversationEngine | None" = None,
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
        result = engine.ask(stripped)
        _render_answer(print_fn, result)

    return engine
