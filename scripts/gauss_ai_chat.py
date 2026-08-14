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

BANNER = "GAUSS AI Assistant"

HELP_TEXT: tuple[str, ...] = (
    "Ask a GAUSS question in plain language, for example:",
    "  How do I read a CSV file in GAUSS?",
    "  What does reshape do?",
    "  What does error G0036 mean?",
    "",
    "Commands:",
    "  help           Show this message",
    "  reset / new    Start a new conversation (clears history)",
    "  exit / quit    Leave the assistant",
    "",
    "This chat does not execute GAUSS code or apply repairs. For that, use:",
    "  gauss-ai repair <file.gss>",
)


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

    if result.grounding_source == "error_catalog":
        print_fn(f"[Grounded in this repository's verified error catalog: {result.grounding_topic}]")
    elif result.grounding_source == "official_docs":
        print_fn(f"[Grounded in local official GAUSS documentation: {result.grounding_topic}]")
    elif result.grounding_source == "uncataloged_error_code":
        print_fn(
            f"[{result.grounding_topic} is not yet in this repository's verified error catalog -- the answer "
            "below is not documentation-grounded]"
        )
    else:
        print_fn("[Not grounded in official documentation or the verified error catalog -- from the model's own general knowledge]")
    print_fn("")
    print_fn(result.text)
    print_fn("")


def run_chat(
    *,
    prompt_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
    cli_provider: str | None = None,
    cli_model: str | None = None,
    cli_docs_root: str | None = None,
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
        try:
            provider = provider_mod.build_provider(provider_name, model=model)
        except ValueError as exc:
            print_fn(f"Configuration error: {exc}")
            print_fn("Run 'gauss-ai config set chat-provider fake' or 'gauss-ai config set chat-provider anthropic'.")
            return None
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=docs_root)

    print_fn(BANNER)
    print_fn("")
    if isinstance(engine.provider, provider_mod.FakeModelProvider):
        print_fn(
            "Using the deterministic fake/test provider -- no real model is configured, so answers are limited "
            "to raw retrieved documentation/catalog text, never synthesized prose. See "
            "docs/conversational-qa.md to configure a real provider."
        )
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
        result = engine.ask(stripped)
        _render_answer(print_fn, result)

    return engine
