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

_MEANC_RST = """meanc
=====

.. function:: y = meanc(x)

Purpose
-------
Computes the mean of every column of a matrix.
"""

_STDC_RST = """stdc
====

.. function:: y = stdc(x)

Purpose
-------
Computes the standard deviation of every column of a matrix.
"""


def _fixture_docs_root(tmp: str) -> Path:
    root = Path(tmp) / "docs"
    root.mkdir()
    (root / "reshape.rst").write_text(_RESHAPE_RST, encoding="utf-8")
    (root / "vec.rst").write_text(_VEC_RST, encoding="utf-8")
    (root / "meanc.rst").write_text(_MEANC_RST, encoding="utf-8")
    (root / "stdc.rst").write_text(_STDC_RST, encoding="utf-8")
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


def test_16b_repair_intent_phrasing_found_during_v0_71_0_live_validation_is_redirected() -> None:
    """v0.71.0 Phase 11 live Ollama validation surfaced a real user phrasing
    ('Please fix my broken.gss file and apply the change automatically.')
    that the original, narrower execution-keyword list did not catch --
    reached the model instead of the boundary redirect. This proves the fix."""
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())
    for phrase in (
        "Please fix my broken.gss file and apply the change automatically.",
        "Can you repair this file for me?",
        "Just apply the fix already.",
    ):
        result = engine.ask(phrase)
        check(f"{phrase!r} is redirected honestly", result.text == engine_mod.EXECUTION_BOUNDARY_MESSAGE)


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


# ---------------------------------------------------------------------------
# v0.72.0 Phase 3: deterministic intent classification
# ---------------------------------------------------------------------------


def test_23_run_keywords_classify_as_execution_request() -> None:
    for phrase in ("Run this.", "Please execute that example.", "Can you run the code?"):
        check(f"{phrase!r} classifies as EXECUTION_REQUEST", engine_mod.classify_intent(phrase) == engine_mod.Intent.EXECUTION_REQUEST)


def test_24_repair_keywords_classify_as_repair_or_application_request() -> None:
    for phrase in (
        "Please fix my broken.gss file and apply the change automatically.",
        "Can you repair this file for me?",
        "Just apply the fix already.",
    ):
        check(
            f"{phrase!r} classifies as REPAIR_OR_APPLICATION_REQUEST",
            engine_mod.classify_intent(phrase) == engine_mod.Intent.REPAIR_OR_APPLICATION_REQUEST,
        )


def test_25_code_generation_phrasing_classifies_correctly() -> None:
    for phrase in (
        "Show me how to reshape this matrix to 4 columns.",
        "How would I calculate column means after reshaping a matrix?",
        "Write GAUSS code to estimate an OLS regression.",
        "Can you give me an example using reshape and meanc?",
        "Write an example using meanc.",
        "How would I loop over columns in GAUSS?",
        "Can you write GAUSS code for this?",
    ):
        check(f"{phrase!r} classifies as CODE_GENERATION", engine_mod.classify_intent(phrase) == engine_mod.Intent.CODE_GENERATION)


def test_26_plain_questions_classify_as_qa() -> None:
    for phrase in ("What does reshape do?", "What does error G0036 mean?", "What is a matrix?"):
        check(f"{phrase!r} classifies as QA", engine_mod.classify_intent(phrase) == engine_mod.Intent.QA)


def test_27_execution_and_repair_keywords_take_priority_over_code_generation_wording() -> None:
    """A phrase that could superficially look code-generation-shaped (it
    mentions 'code'/'this') must still classify as the safety-relevant
    intent when it matches an execution/repair phrase -- checked first."""
    check(
        "'run this code' is EXECUTION_REQUEST, not CODE_GENERATION",
        engine_mod.classify_intent("Can you run this code for me: print 1+1;") == engine_mod.Intent.EXECUTION_REQUEST,
    )
    check(
        "'fix this file' is REPAIR_OR_APPLICATION_REQUEST, not CODE_GENERATION",
        engine_mod.classify_intent("Can you fix this file for me?") == engine_mod.Intent.REPAIR_OR_APPLICATION_REQUEST,
    )


# ---------------------------------------------------------------------------
# v0.72.0 Phase 4/5/17: multi-source grounding and grounding status
# ---------------------------------------------------------------------------


def test_28_one_command_request_is_fully_grounded() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("What does reshape do?", docs_root_str=str(docs_root))
        check("status is GROUNDED", bundle.status == engine_mod.GroundingStatus.GROUNDED)
        check("exactly one source", len(bundle.sources) == 1)
        check("matched topic is reshape", bundle.matched_topics == ("reshape",))
        check("no unmatched topics", bundle.unmatched_topics == ())


def test_29_two_command_request_grounds_both() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("Show me reshape and meanc.", docs_root_str=str(docs_root))
        check("status is GROUNDED", bundle.status == engine_mod.GroundingStatus.GROUNDED)
        check("both topics matched", bundle.matched_topics == ("reshape", "meanc"))
        check("two distinct sources", len(bundle.sources) == 2)
        check("no unmatched topics", bundle.unmatched_topics == ())


def test_30_three_command_request_grounds_all_three() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("Show me reshape, meanc, and stdc.", docs_root_str=str(docs_root))
        check("status is GROUNDED", bundle.status == engine_mod.GroundingStatus.GROUNDED)
        check("all three topics matched", bundle.matched_topics == ("reshape", "meanc", "stdc"))
        check("three distinct sources", len(bundle.sources) == 3)


def test_31_one_documented_and_one_nonexistent_command_is_partially_grounded() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("Show me reshape and somefuncxyz.", docs_root_str=str(docs_root))
        check("status is PARTIALLY_GROUNDED", bundle.status == engine_mod.GroundingStatus.PARTIALLY_GROUNDED)
        check("reshape is matched", bundle.matched_topics == ("reshape",))
        check("somefuncxyz is unmatched, not silently dropped", "somefuncxyz" in bundle.unmatched_topics)
        check("the unmatched topic is never fabricated a source", len(bundle.sources) == 1)


def test_32_conceptual_comparison_of_two_documented_topics_is_fully_grounded() -> None:
    """The exact real limitation this milestone's own Finding 4 named: the
    legacy single-source `ground(...)` could only ever surface ONE of two
    real, documented topics in a comparison question. `ground_multi(...)`
    fixes this directly."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("What's the difference between reshape and vec?", docs_root_str=str(docs_root))
        check("status is GROUNDED", bundle.status == engine_mod.GroundingStatus.GROUNDED)
        check("both real topics matched, not just the last one", set(bundle.matched_topics) == {"reshape", "vec"})


def test_33_follow_up_requiring_previous_topic_plus_a_new_one() -> None:
    """v0.72.0 Phase 11: multi-turn context must not rely on only the
    single most recent topic -- a bounded `recent_topics` list is tried."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider(), docs_root=str(docs_root))
        r1 = engine.ask("Show me reshape.")
        check("first turn grounds on reshape", r1.grounding_topic == "reshape")
        r2 = engine.ask("Now show me meanc too.")
        check("second turn grounds on the newly named topic", "meanc" in [s.topic for s in r2.grounding_sources])
        check("recent_topics retains both", set(engine.state.recent_topics) == {"reshape", "meanc"})
        r3 = engine.ask("Give me a short example.")
        check("a pure pronoun follow-up resolves via the most recently remembered topic", r3.grounded)
        check("resolves to the most recently discussed topic (meanc)", r3.grounding_topic == "meanc")


def test_34_ambiguous_word_that_also_happens_to_match_a_documentation_filename() -> None:
    """'vec' is both a real command name and a short, ordinary-looking
    token -- confirms it is treated as a genuine match, not excluded for
    looking too generic, and is not confused with an unrelated topic."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("What does vec do?", docs_root_str=str(docs_root))
        check("status is GROUNDED", bundle.status == engine_mod.GroundingStatus.GROUNDED)
        check("matched exactly vec", bundle.matched_topics == ("vec",))


def test_35_off_topic_request_is_ungrounded_with_no_fabricated_source() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("What is the capital of France?", docs_root_str=str(docs_root))
        check("status is UNGROUNDED", bundle.status == engine_mod.GroundingStatus.UNGROUNDED)
        check("no sources fabricated", bundle.sources == ())


def test_36_error_code_and_command_question_grounds_both() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi(
            "What does error G0036 mean, and what does reshape do?", docs_root_str=str(docs_root)
        )
        check("status is GROUNDED", bundle.status == engine_mod.GroundingStatus.GROUNDED)
        check("both the error code and the command are matched", set(bundle.matched_topics) == {"G0036", "reshape"})
        catalog_sources = [s for s in bundle.sources if s.source == "error_catalog"]
        doc_sources = [s for s in bundle.sources if s.source == "official_docs"]
        check("the error-code source is correctly labeled error_catalog", len(catalog_sources) == 1)
        check("the command source is correctly labeled official_docs", len(doc_sources) == 1)


def test_37_code_generation_request_with_no_supported_documentation_is_ungrounded() -> None:
    bundle = engine_mod.ground_multi("Write GAUSS code to estimate an OLS regression.", docs_root_str=None)
    check("status is UNGROUNDED with no docs_root configured", bundle.status == engine_mod.GroundingStatus.UNGROUNDED)


def test_38_grounding_sources_are_bounded_and_deduplicated() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi(
            "Show me reshape, reshape, meanc, stdc, and vec.", docs_root_str=str(docs_root)
        )
        check(
            f"total sources never exceed MAX_GROUNDING_SOURCES ({engine_mod.MAX_GROUNDING_SOURCES})",
            len(bundle.sources) <= engine_mod.MAX_GROUNDING_SOURCES,
        )
        check("no duplicate topic appears twice", len(bundle.matched_topics) == len(set(bundle.matched_topics)))


# ---------------------------------------------------------------------------
# v0.72.0 Phase 6/7/9/10/18: conversational code generation
# ---------------------------------------------------------------------------


def test_39_code_generation_intent_extracts_generated_code_blocks() -> None:
    provider = provider_mod.FakeModelProvider(canned_answer="Here you go:\n\n```gauss\nx = reshape(5, 3);\n```\n")
    engine = engine_mod.ConversationEngine(provider=provider)
    result = engine.ask("Write GAUSS code to reshape a scalar into a vector.")
    check("intent recorded as code_generation", result.intent == engine_mod.Intent.CODE_GENERATION.value)
    check("generated_code is populated", result.generated_code == ("x = reshape(5, 3);",))
    check("executed is always False", result.executed is False)
    check("methodologically_validated is always False", result.methodologically_validated is False)


def test_40_plain_qa_intent_never_populates_generated_code() -> None:
    provider = provider_mod.FakeModelProvider(canned_answer="```gauss\nx = 1;\n```")
    engine = engine_mod.ConversationEngine(provider=provider)
    result = engine.ask("What does reshape do?")
    check("intent recorded as qa", result.intent == engine_mod.Intent.QA.value)
    check("generated_code is empty for a plain QA turn, even if the text happens to contain a fence", result.generated_code == ())


def test_41_extract_code_blocks_ignores_prose_and_handles_multiple_blocks() -> None:
    text = "Some prose.\n\n```gauss\nx = 1;\n```\n\nMore prose.\n\n```\ny = 2;\n```\n"
    blocks = engine_mod.extract_code_blocks(text)
    check("two blocks extracted", blocks == ("x = 1;", "y = 2;"))
    check("prose text alone yields no blocks", engine_mod.extract_code_blocks("Just plain prose, no code.") == ())


def test_42_documented_multi_command_code_generation_via_fake_provider() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider(), docs_root=str(docs_root))
        result = engine.ask("Can you give me an example using reshape and meanc?")
        check("intent is code_generation", result.intent == engine_mod.Intent.CODE_GENERATION.value)
        check("grounding_status is grounded", result.grounding_status == engine_mod.GroundingStatus.GROUNDED.value)
        check("both topics grounded", {s.topic for s in result.grounding_sources} == {"reshape", "meanc"})
        check("the deterministic template produced an extractable code block", len(result.generated_code) >= 1)
        check("the not-executed footer is present", engine_mod.NOT_EXECUTED_FOOTER in result.text)


def test_43_partial_grounding_never_silently_asserts_the_unsupported_function_as_documented() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider(), docs_root=str(docs_root))
        result = engine.ask("Show me reshape and somefuncxyz.")
        check("grounding_status is partially_grounded", result.grounding_status == engine_mod.GroundingStatus.PARTIALLY_GROUNDED.value)
        check("somefuncxyz is recorded as unsupported", "somefuncxyz" in result.unsupported_topics)
        check("only the real function appears as a grounded source", [s.topic for s in result.grounding_sources] == ["reshape"])


def test_44_ungrounded_code_generation_discloses_honestly_no_fabricated_source() -> None:
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())  # no docs_root
    result = engine.ask("Write GAUSS code to estimate an OLS regression.")
    check("intent is code_generation", result.intent == engine_mod.Intent.CODE_GENERATION.value)
    check("grounding_status is ungrounded", result.grounding_status == engine_mod.GroundingStatus.UNGROUNDED.value)
    check("no fabricated grounding sources", result.grounding_sources == ())


def test_45_code_generation_system_prompt_addendum_instructs_against_fabricated_execution_claims() -> None:
    """A soft, prompt-level guard (Phase 9) -- not deterministically
    enforceable against a real model's own prose, but this at least proves
    the instruction text exists and is not accidentally removed later."""
    addendum = engine_mod.CODE_GENERATION_SYSTEM_PROMPT_ADDENDUM.lower()
    check("addendum warns against inventing GAUSS functions", "never invent a gauss function" in addendum)
    check("addendum distinguishes prediction from execution evidence", "not observed execution evidence" in addendum)
    check("addendum warns against claiming execution/verification", "the code has been executed, tested, or verified" in addendum)
    check(
        "addendum separates syntax correctness from methodological correctness",
        "does not make a statistical or methodological choice correct" in addendum,
    )


# ---------------------------------------------------------------------------
# v0.72.0 Phase 14/15/18: execution/repair boundary still holds for
# code-generation turns and after code has been generated
# ---------------------------------------------------------------------------


def test_46_run_request_after_a_code_generation_turn_is_still_redirected() -> None:
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())
    engine.ask("Write GAUSS code to reshape a matrix.")
    result = engine.ask("Great, now run it.")
    check("still redirected, never executed", result.text == engine_mod.EXECUTION_BOUNDARY_MESSAGE)
    check("intent recorded as execution_request", result.intent == engine_mod.Intent.EXECUTION_REQUEST.value)


def test_47_apply_request_after_a_code_generation_turn_is_still_redirected() -> None:
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())
    engine.ask("Write GAUSS code to reshape a matrix.")
    result = engine.ask("Apply that fix to my file.")
    check("still redirected, never applied", result.text == engine_mod.EXECUTION_BOUNDARY_MESSAGE)
    check("intent recorded as repair_or_application_request", result.intent == engine_mod.Intent.REPAIR_OR_APPLICATION_REQUEST.value)


def test_47b_apply_code_to_a_named_file_phrasing_found_during_v0_72_0_live_validation_is_redirected() -> None:
    """v0.72.0 Phase 19 live Ollama validation surfaced a real gap the same
    way v0.71.0's Phase 11 did: 'Please apply that code to my myfile.gss
    file.' named 'code' (not 'repair'/'change'/'fix') as the thing to
    apply, to a named file, and reached the model instead of the boundary
    redirect. The model's own reply was still safe (no file-write
    capability exists regardless of routing), but the interception itself
    was fixed and is proven here."""
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())
    engine.ask("Write GAUSS code to reshape a matrix.")
    for phrase in (
        "Please apply that code to my myfile.gss file.",
        "Can you add this code to my script.gss?",
        "Write this code to output.gss for me.",
    ):
        result = engine.ask(phrase)
        check(f"{phrase!r} is redirected honestly", result.text == engine_mod.EXECUTION_BOUNDARY_MESSAGE)


def test_48_code_generation_never_calls_the_provider_for_a_run_request() -> None:
    class ExplodingProvider:
        def complete(self, messages, *, max_tokens=1024):
            raise AssertionError("the provider must never be called for an execution-intent question")

    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())
    engine.ask("Write GAUSS code to reshape a matrix.")  # a real, legitimate provider call
    engine.provider = ExplodingProvider()  # would raise immediately if "Run it." reached the provider
    result = engine.ask("Run it.")  # must not raise
    check("returns the fixed boundary message without calling the provider", result.text == engine_mod.EXECUTION_BOUNDARY_MESSAGE)


def test_49_module_still_never_imports_execution_repair_or_filesystem_modules() -> None:
    """Re-confirms the same structural safety guarantee `test_17` already
    covers, now that v0.72.0 added conversational code generation --
    generated code must remain exactly as advisory-only as v0.70.0's plain
    prose answers were."""
    forbidden_modules = (
        "gauss_execution_workflow", "gauss_repair_application", "gauss_repair_draft",
        "gauss_repair_planner", "gauss_repair_approval", "gauss_verification_execution",
        "gauss_verification_review", "gauss_code_execution", "gauss_workspace", "subprocess",
    )
    for line in Path(engine_mod.__file__).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            for token in forbidden_modules:
                check(f"import line {stripped!r} does not reference {token!r}", token not in stripped)


def test_50_extract_code_blocks_never_writes_anything_to_disk() -> None:
    """Structural proof that code-block extraction is pure text processing:
    no `open(`, no `Path(...).write_text(...)`-shaped call anywhere in its
    own source."""
    import inspect

    source = inspect.getsource(engine_mod.extract_code_blocks)
    for token in ("open(", "write_text", "write_bytes", "os.system", "subprocess."):
        check(f"extract_code_blocks source does not contain {token!r}", token not in source)


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
