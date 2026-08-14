"""Tests for `gauss_conversation_engine.py` (v0.70.0).

Run with:

    python scripts/test_gauss_conversation_engine.py

Documentation-grounding tests use a small, disposable, synthetic `.rst`
fixture tree (never this machine's own real local GAUSS documentation
checkout, which is gitignored and does not exist on other machines) so
these tests are fully reproducible anywhere.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_chat_provider as provider_mod  # noqa: E402
import gauss_conversation_engine as engine_mod  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


_RESHAPE_RST = """reshape
=======

.. function:: y = reshape(x, r [, c])

Input
-----
:param x: data to reshape
:type x: NxK matrix

Output
------
:return y: reshaped matrix
:rtype y: RxC matrix

Examples
--------
.. code-block:: none

    x = reshape(5, 3);
"""

_VEC_RST = """vec
===

.. function:: y = vec(x)

Purpose
-------
Stacks the columns of a matrix into one column vector.
"""


def _fixture_docs_root(tmp: str) -> Path:
    root = Path(tmp) / "docs"
    root.mkdir()
    (root / "reshape.rst").write_text(_RESHAPE_RST, encoding="utf-8")
    (root / "vec.rst").write_text(_VEC_RST, encoding="utf-8")
    return root


# ---------------------------------------------------------------------------
# Grounding: error catalog
# ---------------------------------------------------------------------------


def test_01_grounds_on_a_known_error_code() -> None:
    result = engine_mod.ground("What does G0036 mean?", docs_root_str=None)
    check("hit", result.hit)
    check("source is error_catalog", result.source == "error_catalog")
    check("topic is the normalized code", result.topic == "G0036")
    check("content mentions the real catalog title", "Matrix dimensions are incompatible" in result.content)


def test_02_error_code_case_insensitive_and_embedded_in_a_sentence() -> None:
    result = engine_mod.ground("i keep seeing g0105 what does that mean", docs_root_str=None)
    check("hit", result.hit)
    check("topic normalized to uppercase", result.topic == "G0105")


def test_03_uncataloged_error_code_is_honestly_disclosed_not_fabricated() -> None:
    result = engine_mod.ground("What does G9999 mean?", docs_root_str=None)
    check("not a hit", not result.hit)
    check("source names it as uncataloged", result.source == "uncataloged_error_code")
    check("topic is still surfaced", result.topic == "G9999")
    check("no fabricated content", result.content == "")


# ---------------------------------------------------------------------------
# Grounding: documentation lookup
# ---------------------------------------------------------------------------


def test_04_grounds_on_a_real_local_doc_match() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        result = engine_mod.ground("What does reshape do?", docs_root_str=str(docs_root))
        check("hit", result.hit)
        check("source is official_docs", result.source == "official_docs")
        check("topic is the matched command", result.topic == "reshape")
        check("content includes the real extracted syntax", "reshape(x, r [, c])" in result.content)
        check("content includes the real extracted inputs section", "data to reshape" in result.content)
        check("content includes the real extracted outputs section", "reshaped matrix" in result.content)
        check("citation names the real file", result.citation == "reshape.rst")


def test_05_no_docs_root_configured_never_grounds_on_documentation() -> None:
    result = engine_mod.ground("What does reshape do?", docs_root_str=None)
    check("not a hit", not result.hit)
    check("source is none", result.source == "none")


def test_06_nonexistent_docs_root_path_is_handled_gracefully() -> None:
    result = engine_mod.ground("What does reshape do?", docs_root_str="/this/path/does/not/exist/anywhere")
    check("not a hit", not result.hit)
    check("source is none", result.source == "none")


def test_07_unrelated_question_with_docs_root_configured_does_not_fabricate_a_match() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        result = engine_mod.ground("What is the meaning of life?", docs_root_str=str(docs_root))
        check("not a hit -- no fabricated match", not result.hit)
        check("source is none", result.source == "none")


def test_08_follow_up_falls_back_to_last_topic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        result = engine_mod.ground("Show me a simple example.", docs_root_str=str(docs_root), last_topic="reshape")
        check("hit via last_topic fallback", result.hit)
        check("topic is the carried-over last_topic", result.topic == "reshape")


def test_09_a_new_topic_in_the_question_wins_over_last_topic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        result = engine_mod.ground("What's the difference between that and vec?", docs_root_str=str(docs_root), last_topic="reshape")
        check("hit", result.hit)
        check("topic is the newly mentioned command, not the stale last_topic", result.topic == "vec")


# ---------------------------------------------------------------------------
# ConversationEngine: multi-turn, reset, bounded history
# ---------------------------------------------------------------------------


def test_10_basic_question_returns_an_answer() -> None:
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())
    result = engine.ask("What does reshape do?")
    check("provider_success", result.provider_success)
    check("text is non-empty", bool(result.text))


def test_11_multi_turn_follow_up_context_is_retained() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider(), docs_root=str(docs_root))
        r1 = engine.ask("What does reshape do?")
        check("first question grounds on reshape", r1.grounding_topic == "reshape")
        r2 = engine.ask("Show me a simple example.")
        check("follow-up with no new topic still grounds, via last_topic", r2.grounded)
        check("follow-up resolves to the same prior topic", r2.grounding_topic == "reshape")


def test_12_reset_clears_history_and_last_topic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider(), docs_root=str(docs_root))
        engine.ask("What does reshape do?")
        check("history is non-empty before reset", len(engine.state.turns) > 0)
        check("last_topic is set before reset", engine.state.last_topic == "reshape")
        engine.reset()
        check("history is empty after reset", len(engine.state.turns) == 0)
        check("last_topic is cleared after reset", engine.state.last_topic is None)
        r = engine.ask("Show me a simple example.")
        check("after reset, a pure pronoun follow-up has nothing to resolve against", not r.grounded)


def test_13_conversation_history_is_bounded() -> None:
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())
    for i in range(engine_mod.MAX_HISTORY_TURNS):
        engine.ask(f"question number {i}")
    check(
        f"history never exceeds {engine_mod.MAX_HISTORY_TURNS} turns",
        len(engine.state.turns) <= engine_mod.MAX_HISTORY_TURNS,
    )


def test_14_oldest_turns_drop_first_when_bounded() -> None:
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())
    for i in range(engine_mod.MAX_HISTORY_TURNS):
        engine.ask(f"question number {i}")
    oldest_still_present = any("question number 0" in t.content for t in engine.state.turns)
    check("the very first question has been dropped from bounded history", not oldest_still_present)
    newest_present = any(f"question number {engine_mod.MAX_HISTORY_TURNS - 1}" in t.content for t in engine.state.turns)
    check("the most recent question is still present", newest_present)


# ---------------------------------------------------------------------------
# Execution boundary
# ---------------------------------------------------------------------------


def test_15_execution_intent_is_redirected_never_silently_bypassed() -> None:
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())
    for phrase in ("Run this.", "Please execute that example.", "Can you run the code?"):
        result = engine.ask(phrase)
        check(f"{phrase!r} is redirected honestly", result.text == engine_mod.EXECUTION_BOUNDARY_MESSAGE)
        check(f"{phrase!r} points to the real guided command", "gauss-ai repair" in result.text)


def test_16_execution_intent_never_calls_the_provider() -> None:
    class ExplodingProvider:
        def complete(self, messages, *, max_tokens=1024):
            raise AssertionError("the provider must never be called for an execution-intent question")

    engine = engine_mod.ConversationEngine(provider=ExplodingProvider())
    result = engine.ask("Run this.")  # must not raise
    check("returns the fixed boundary message without calling the provider", result.text == engine_mod.EXECUTION_BOUNDARY_MESSAGE)


def test_17_module_never_imports_execution_or_repair_pipeline() -> None:
    forbidden_modules = (
        "gauss_execution_workflow", "gauss_repair_application", "gauss_repair_draft",
        "gauss_repair_planner", "gauss_repair_approval", "gauss_verification_execution",
        "gauss_verification_review", "gauss_code_execution", "gauss_workspace",
    )
    for line in Path(engine_mod.__file__).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            for token in forbidden_modules:
                check(f"import line {stripped!r} does not reference {token!r}", token not in stripped)


# ---------------------------------------------------------------------------
# Code-shown / not-executed disclosure
# ---------------------------------------------------------------------------


def test_18_code_shaped_answer_gets_the_not_executed_footer() -> None:
    provider = provider_mod.FakeModelProvider(canned_answer="Try this:\n\nx = reshape(5, 3);\nprint x;")
    engine = engine_mod.ConversationEngine(provider=provider)
    result = engine.ask("How do I use reshape?")
    check("footer is appended", engine_mod.NOT_EXECUTED_FOOTER in result.text)


def test_19_plain_prose_answer_with_no_code_gets_no_footer() -> None:
    provider = provider_mod.FakeModelProvider(canned_answer="A matrix is a two-dimensional array of numbers.")
    engine = engine_mod.ConversationEngine(provider=provider)
    result = engine.ask("What is a matrix?")
    check("no footer appended to plain prose", engine_mod.NOT_EXECUTED_FOOTER not in result.text)


# ---------------------------------------------------------------------------
# Provider failure surfaced honestly
# ---------------------------------------------------------------------------


def test_20_provider_failure_is_surfaced_honestly_not_hidden() -> None:
    provider = provider_mod.AnthropicMessagesProvider(env={})  # missing API key
    engine = engine_mod.ConversationEngine(provider=provider)
    result = engine.ask("What does reshape do?")
    check("provider_success is False", not result.provider_success)
    check("error is surfaced in the text", "could not answer" in result.text)
    check("provider_error is populated", result.provider_error is not None)


def test_21_provider_failure_is_still_recorded_in_history() -> None:
    provider = provider_mod.AnthropicMessagesProvider(env={})
    engine = engine_mod.ConversationEngine(provider=provider)
    engine.ask("hello")
    check("the failed exchange is still recorded", len(engine.state.turns) == 2)


# ---------------------------------------------------------------------------
# Grounding never claimed without a real hit
# ---------------------------------------------------------------------------


def test_22_answer_result_never_claims_grounded_without_a_real_hit() -> None:
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())  # no docs_root configured
    result = engine.ask("What is the difference between a matrix and an array?")
    check("not grounded", not result.grounded)
    check("grounding_source is none", result.grounding_source == "none")


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
