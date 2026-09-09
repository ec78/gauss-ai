"""Tests for `gauss_ai_chat.py` (v0.70.0).

Run with:

    python scripts/test_gauss_ai_chat.py

Every test drives `run_chat(...)` with a scripted `prompt_fn` and a captured
`print_fn` -- no test reads real stdin, and no test constructs a real
`AnthropicMessagesProvider` against the real network.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_ai_chat as chat_mod  # noqa: E402
import gauss_ai_config as config_mod  # noqa: E402
import gauss_chat_provider as provider_mod  # noqa: E402
import gauss_conversation_engine as engine_mod  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _scripted(answers: list[str]):
    queue = list(answers)

    def _prompt(_question: str) -> str:
        if not queue:
            raise AssertionError("prompt_fn called more times than answers were scripted")
        return queue.pop(0)

    return _prompt


_RESHAPE_RST = """reshape
=======

.. function:: y = reshape(x, r [, c])

Input
-----
:param x: data to reshape
:type x: NxK matrix

Examples
--------
.. code-block:: none

    x = reshape(5, 3);
"""


_MEANC_RST = """meanc
=====

.. function:: y = meanc(x)

Purpose
-------
Computes the mean of every column of a matrix.
"""


def _fixture_docs_root(tmp: str) -> Path:
    root = Path(tmp) / "docs"
    root.mkdir()
    (root / "reshape.rst").write_text(_RESHAPE_RST, encoding="utf-8")
    (root / "meanc.rst").write_text(_MEANC_RST, encoding="utf-8")
    return root


def _fake_engine(docs_root: str | None = None) -> "engine_mod.ConversationEngine":
    return engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider(), docs_root=docs_root)


# ---------------------------------------------------------------------------
# Launching, banner, exit
# ---------------------------------------------------------------------------


def test_01_launch_and_immediate_exit() -> None:
    messages: list[str] = []
    result = chat_mod.run_chat(prompt_fn=_scripted(["exit"]), print_fn=messages.append, engine=_fake_engine())
    check("returns the engine, not None", result is not None)
    check("banner is printed", any(chat_mod.BANNER in m for m in messages))


def test_02_quit_also_leaves() -> None:
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["quit"]), print_fn=messages.append, engine=_fake_engine())
    check("banner printed and loop exited cleanly", any(chat_mod.BANNER in m for m in messages))


def test_03_eof_leaves_cleanly_never_raises() -> None:
    def raising_prompt(_q: str) -> str:
        raise EOFError()

    result = chat_mod.run_chat(prompt_fn=raising_prompt, print_fn=lambda *_: None, engine=_fake_engine())
    check("EOF is handled cleanly, engine still returned", result is not None)


def test_04_blank_lines_are_ignored_not_treated_as_questions() -> None:
    messages: list[str] = []
    engine = _fake_engine()
    chat_mod.run_chat(prompt_fn=_scripted(["", "   ", "exit"]), print_fn=messages.append, engine=engine)
    check("no question was recorded in conversation history", len(engine.state.turns) == 0)


# ---------------------------------------------------------------------------
# Basic Q&A
# ---------------------------------------------------------------------------


def test_05_basic_question_produces_an_answer() -> None:
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["What is a matrix?", "exit"]), print_fn=messages.append, engine=_fake_engine())
    check("some answer text was printed", any("fake/test provider" in m for m in messages))


def test_06_grounded_answer_shows_the_grounding_disclosure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        messages: list[str] = []
        chat_mod.run_chat(
            prompt_fn=_scripted(["What does reshape do?", "exit"]), print_fn=messages.append,
            engine=_fake_engine(docs_root=str(docs_root)),
        )
        check("grounding disclosure is shown", any("Grounded in local official GAUSS documentation" in m for m in messages))


def test_07_ungrounded_answer_is_honestly_labeled() -> None:
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["What is the meaning of life?", "exit"]), print_fn=messages.append, engine=_fake_engine())
    check(
        "ungrounded disclosure is shown",
        any("Not grounded in official documentation or the verified error catalog" in m for m in messages),
    )


def test_08_error_catalog_question_shows_catalog_grounding() -> None:
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["What does error G0036 mean?", "exit"]), print_fn=messages.append, engine=_fake_engine())
    check("catalog grounding disclosure shown", any("verified error catalog: G0036" in m for m in messages))


# ---------------------------------------------------------------------------
# Multi-turn follow-up
# ---------------------------------------------------------------------------


def test_09_multi_turn_follow_up_via_the_full_loop() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        engine = _fake_engine(docs_root=str(docs_root))
        chat_mod.run_chat(
            prompt_fn=_scripted(["What does reshape do?", "Show me a simple example.", "exit"]),
            print_fn=lambda *_: None, engine=engine,
        )
        check("four turns recorded (two exchanges)", len(engine.state.turns) == 4)
        check("last_topic still reshape after the follow-up", engine.state.last_topic == "reshape")


# ---------------------------------------------------------------------------
# help / reset
# ---------------------------------------------------------------------------


def test_10_help_prints_help_text_without_treating_it_as_a_question() -> None:
    engine = _fake_engine()
    chat_mod.run_chat(prompt_fn=_scripted(["help", "exit"]), print_fn=lambda *_: None, engine=engine)
    check("'help' was not recorded as a conversation turn", len(engine.state.turns) == 0)


def test_11_help_output_mentions_reset_and_exit_and_the_repair_boundary() -> None:
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["help", "exit"]), print_fn=messages.append, engine=_fake_engine())
    joined = "\n".join(messages)
    check("mentions reset", "reset" in joined)
    check("mentions exit", "exit" in joined)
    check("points to the real repair command", "gauss-ai repair" in joined)


def test_12_reset_clears_conversation_and_is_not_treated_as_a_question() -> None:
    engine = _fake_engine()
    messages: list[str] = []
    chat_mod.run_chat(
        prompt_fn=_scripted(["What is a matrix?", "reset", "exit"]), print_fn=messages.append, engine=engine,
    )
    check("history is empty after reset (the one question was cleared)", len(engine.state.turns) == 0)
    check("a reset confirmation was printed", any("reset" in m.lower() for m in messages))


def test_13_new_is_a_synonym_for_reset() -> None:
    engine = _fake_engine()
    chat_mod.run_chat(prompt_fn=_scripted(["What is a matrix?", "new", "exit"]), print_fn=lambda *_: None, engine=engine)
    check("'new' also clears history", len(engine.state.turns) == 0)


# ---------------------------------------------------------------------------
# Execution boundary through the full loop
# ---------------------------------------------------------------------------


def test_14_execution_request_through_the_full_loop_is_redirected() -> None:
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["Run this.", "exit"]), print_fn=messages.append, engine=_fake_engine())
    check("the fixed boundary message was printed", any(engine_mod.EXECUTION_BOUNDARY_MESSAGE in m for m in messages))
    check("no grounding-disclosure line precedes it (it's a redirect, not an answer)", not any(m.startswith("[Grounded") for m in messages))


# ---------------------------------------------------------------------------
# Configuration precedence and unknown-provider handling
# ---------------------------------------------------------------------------


def test_15_unknown_configured_provider_returns_none_never_raises() -> None:
    result = chat_mod.run_chat(
        prompt_fn=_scripted([]), print_fn=lambda *_: None,
        cli_provider="not-a-real-vendor", config=config_mod.GaussAiConfig(), env={},
    )
    check("returns None on a configuration error", result is None)


def test_16_cli_provider_argument_is_used_to_construct_the_engine() -> None:
    messages: list[str] = []
    result = chat_mod.run_chat(
        prompt_fn=_scripted(["exit"]), print_fn=messages.append,
        cli_provider="fake", config=config_mod.GaussAiConfig(), env={},
    )
    check("a real engine was constructed", result is not None)
    check("the fake-provider notice was shown", any("Provider: fake/test" in m for m in messages))


def test_17_default_provider_is_fake_when_nothing_configured() -> None:
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["exit"]), print_fn=messages.append, config=config_mod.GaussAiConfig(), env={})
    check("defaults to the fake provider", any("Provider: fake/test" in m for m in messages))


# ---------------------------------------------------------------------------
# Never bypasses execution/application; secrets never surfaced
# ---------------------------------------------------------------------------


def test_18_module_never_imports_execution_or_repair_pipeline() -> None:
    forbidden_modules = (
        "gauss_execution_workflow", "gauss_repair_application", "gauss_repair_draft",
        "gauss_repair_planner", "gauss_repair_approval", "gauss_verification_execution",
        "gauss_verification_review", "gauss_code_execution", "gauss_workspace",
    )
    for line in Path(chat_mod.__file__).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            for token in forbidden_modules:
                check(f"import line {stripped!r} does not reference {token!r}", token not in stripped)


def test_19_no_output_line_ever_contains_a_secret_shaped_value() -> None:
    """Even when a real-shaped API key is present in the provider's own
    resolved environment and a call succeeds, nothing resembling it is ever
    printed -- checked through the full render pipeline. Uses an injected
    fake transport, so this test makes no real network call."""
    def fake_transport(_request):
        return 200, b'{"content": [{"type": "text", "text": "ok"}]}'

    provider = provider_mod.AnthropicMessagesProvider(
        env={"ANTHROPIC_API_KEY": "sk-should-never-be-printed"}, transport=fake_transport,
    )
    engine = engine_mod.ConversationEngine(provider=provider)
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["What does reshape do?", "exit"]), print_fn=messages.append, engine=engine)
    joined = "\n".join(messages)
    check("the real API key value never appears in any printed line", "sk-should-never-be-printed" not in joined)


# ---------------------------------------------------------------------------
# v0.71.0 Phase 6: generic startup status for any provider
# ---------------------------------------------------------------------------


def test_20_ollama_provider_startup_status_shows_provider_model_and_endpoint() -> None:
    provider = provider_mod.OllamaProvider(model="qwen2.5-coder:7b", endpoint="http://localhost:11434")
    engine = engine_mod.ConversationEngine(provider=provider)
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["exit"]), print_fn=messages.append, engine=engine)
    check("provider and model are shown", any("Provider: ollama" in m and "qwen2.5-coder:7b" in m for m in messages))
    check("endpoint is shown", any("http://localhost:11434" in m for m in messages))
    check("the fake-provider notice is not shown for a real provider", not any("Provider: fake/test" in m for m in messages))


def test_21_anthropic_provider_startup_status_shows_provider_and_model() -> None:
    provider = provider_mod.AnthropicMessagesProvider(model="claude-sonnet-5")
    engine = engine_mod.ConversationEngine(provider=provider)
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["exit"]), print_fn=messages.append, engine=engine)
    check("provider and model are shown", any("Provider: anthropic" in m and "claude-sonnet-5" in m for m in messages))


def test_22_startup_status_never_claims_grounding_without_a_configured_docs_root() -> None:
    engine = _fake_engine(docs_root=None)
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["exit"]), print_fn=messages.append, engine=engine)
    check("docs status says not configured", any("GAUSS documentation: not configured" in m for m in messages))
    check("docs status never claims configured", not any("GAUSS documentation: configured" in m for m in messages))


def test_23_startup_status_reports_a_configured_docs_root() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = _fake_engine(docs_root=tmp)
        messages: list[str] = []
        chat_mod.run_chat(prompt_fn=_scripted(["exit"]), print_fn=messages.append, engine=engine)
        check("docs status says configured", any("GAUSS documentation: configured" in m and tmp in m for m in messages))


# ---------------------------------------------------------------------------
# v0.71.0 Phase 7: gauss-ai CLI commands typed into chat are intercepted
# ---------------------------------------------------------------------------


def test_24_cli_shaped_input_is_intercepted_and_never_reaches_the_provider() -> None:
    engine = _fake_engine()
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["gauss-ai doctor", "exit"]), print_fn=messages.append, engine=engine)
    check("the interception message is shown", any("cannot run it" in m for m in messages))
    check("nothing was recorded as a conversation turn", len(engine.state.turns) == 0)


def test_25_a_normal_question_that_merely_mentions_gauss_ai_still_reaches_the_provider() -> None:
    engine = _fake_engine()
    chat_mod.run_chat(
        prompt_fn=_scripted(["How do I install gauss-ai?", "exit"]), print_fn=lambda *_: None, engine=engine,
    )
    check("the question and its answer were recorded (two turns)", len(engine.state.turns) == 2)


# ---------------------------------------------------------------------------
# v0.72.0: conversational GAUSS code generation rendering
# ---------------------------------------------------------------------------


def test_26_multi_source_grounded_code_generation_shows_both_topics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        messages: list[str] = []
        chat_mod.run_chat(
            prompt_fn=_scripted(["Can you give me an example using reshape and meanc?", "exit"]),
            print_fn=messages.append, engine=_fake_engine(docs_root=str(docs_root)),
        )
        joined = "\n".join(messages)
        check("disclosure names reshape", "reshape" in joined)
        check("disclosure names meanc", "meanc" in joined)
        check("disclosure says Grounded", "Grounded in" in joined)
        check("a fenced GAUSS code block is shown", "```gauss" in joined)
        check("the not-executed footer is shown", "has not been executed in this conversation" in joined)


def test_27_partially_grounded_code_generation_discloses_the_unsupported_function() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        messages: list[str] = []
        chat_mod.run_chat(
            prompt_fn=_scripted(["Show me reshape and somefuncxyz.", "exit"]),
            print_fn=messages.append, engine=_fake_engine(docs_root=str(docs_root)),
        )
        joined = "\n".join(messages)
        check("disclosure says Partially grounded", "Partially grounded" in joined)
        check("the unsupported function is named", "somefuncxyz" in joined)
        check("the grounded function is named", "reshape" in joined)


def test_28_ungrounded_code_generation_request_is_honestly_labeled() -> None:
    messages: list[str] = []
    chat_mod.run_chat(
        prompt_fn=_scripted(["Write GAUSS code to estimate an OLS regression.", "exit"]),
        print_fn=messages.append, engine=_fake_engine(),
    )
    joined = "\n".join(messages)
    check(
        "ungrounded disclosure is shown, not a fabricated grounding claim",
        "Not grounded in official documentation or the verified error catalog" in joined,
    )


def test_29_help_text_mentions_code_generation_and_its_limits() -> None:
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["help", "exit"]), print_fn=messages.append, engine=_fake_engine())
    joined = "\n".join(messages)
    check("help mentions asking for GAUSS code", "GAUSS code" in joined)
    check("help still states the no-execution/no-file-edit boundary", "does not execute" in joined)


def run_tests() -> int:
    tests = [
        (name, fn)
        for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    for name, fn in tests:
        before = len(_failures)
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _failures.append(f"{name} raised {type(exc).__name__}: {exc}")
        if len(_failures) == before:
            print(f"PASS  {name}")
        else:
            for failure in _failures[before:]:
                print(f"FAIL  {name}: {failure}")
    print(f"\n{len(tests)} test function(s) run, {len(_failures)} check failure(s).")
    if _failures:
        print("SOME CHECKS FAILED.")
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
