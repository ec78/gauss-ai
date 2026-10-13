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


_INV_RST = """inv, invpd
==========

.. function:: xi = inv(x)
              xi = invpd(x)

Purpose
-------
inv returns the inverse of an invertible matrix.

Input
-----
    :param x: data
    :type x: NxN matrix
"""

_TSCSFIT_RST = """tscsFit
=======

.. function:: tso = tscsFit(y, x, grp[, tsc])

Purpose
-------
Estimates the parameters of the pooled time-series cross-section regression model. See :func:`tscsmtControlCreate` to build the optional tsc control structure.
"""

#: v0.74.0: a doc-derivable concept NOT present in the hand-curated
#: `_CONCEPT_ALIAS_INDEX` at all -- used to prove the new documentation-
#: derived concept index (`gauss_doc_concept_index.py`) can resolve a
#: natural-language phrase to a real symbol on its own, without relying on
#: any curated alias.
_CORRX_RST = """corrx
=====

.. function:: y = corrx(x)

Purpose
-------
Computes the correlation matrix of the columns of a dataset.
"""


def _fixture_docs_root(tmp: str) -> Path:
    root = Path(tmp) / "docs"
    root.mkdir()
    (root / "reshape.rst").write_text(_RESHAPE_RST, encoding="utf-8")
    (root / "vec.rst").write_text(_VEC_RST, encoding="utf-8")
    (root / "meanc.rst").write_text(_MEANC_RST, encoding="utf-8")
    (root / "stdc.rst").write_text(_STDC_RST, encoding="utf-8")
    (root / "invinvpd.rst").write_text(_INV_RST, encoding="utf-8")
    (root / "tscsfit.rst").write_text(_TSCSFIT_RST, encoding="utf-8")
    (root / "corrx.rst").write_text(_CORRX_RST, encoding="utf-8")
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
        # v0.77.0: exact ORDER is no longer asserted here -- `_candidate_tokens`'s
        # Phase 12 reprioritization deliberately promotes a token that is
        # itself a curated concept-alias symbol (`meanc`) ahead of a plain
        # exact-documented-symbol-stem match (`reshape`) that merely appears
        # earlier in the sentence. Both are still matched; only WHICH order
        # they're discovered in changed, which is the whole point of the fix.
        check("both topics matched, order-independent", set(bundle.matched_topics) == {"reshape", "meanc"})
        check("two distinct sources", len(bundle.sources) == 2)
        check("no unmatched topics", bundle.unmatched_topics == ())


def test_30_three_command_request_grounds_all_three() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("Show me reshape, meanc, and stdc.", docs_root_str=str(docs_root))
        check("status is GROUNDED", bundle.status == engine_mod.GroundingStatus.GROUNDED)
        # v0.77.0: order-independent for the same reason as test_29 above.
        check("all three topics matched, order-independent", set(bundle.matched_topics) == {"reshape", "meanc", "stdc"})
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
    """v0.73.0: an ungrounded code-generation request is now correctly
    BLOCKed (see test_51_ungrounded_code_generation_request_is_blocked...),
    so this test configures a real docs_root, exactly like a genuinely
    GROUNDED request would need, to exercise the generated_code
    extraction path end to end."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="Here you go:\n\n```gauss\nx = reshape(5, 3);\n```\n")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Write GAUSS code to reshape a scalar into a vector.")
        check("intent recorded as code_generation", result.intent == engine_mod.Intent.CODE_GENERATION.value)
        check("generated_code is populated", result.generated_code == ("x = reshape(5, 3);",))
        check("executed is always False", result.executed is False)
        check("methodologically_validated is always False", result.methodologically_validated is False)
        check(
            "generation was permitted (reshape is grounded, even if other stray words like 'scalar'/'vector' are not)",
            result.generation_policy in (engine_mod.GenerationPolicy.FULL.value, engine_mod.GenerationPolicy.SUPPORTED_ONLY.value),
        )


def test_40_qa_intent_can_still_populate_generated_code_when_the_answer_is_code_shaped() -> None:
    """v0.73.0: broadened from the v0.72.0 behavior (QA never populated
    `generated_code`) after live Ollama evaluation found a real question
    ("Use reshape and colmean on my data.") that did not match any
    code-generation trigger phrase, classified as QA, yet still produced a
    code-shaped answer containing a hallucinated symbol -- the post-
    generation symbol check needs to see that code regardless of intent,
    since a hallucination is exactly as real in a QA answer that happens
    to include example code."""
    provider = provider_mod.FakeModelProvider(canned_answer="```gauss\nx = 1;\n```")
    engine = engine_mod.ConversationEngine(provider=provider)
    result = engine.ask("What does reshape do?")
    check("intent recorded as qa", result.intent == engine_mod.Intent.QA.value)
    check("generated_code is populated because the answer is code-shaped", result.generated_code == ("x = 1;",))


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
    check("generation is blocked, not left to the model", result.generation_policy == engine_mod.GenerationPolicy.BLOCK.value)
    check("no code was fabricated", result.generated_code == ())


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


# ---------------------------------------------------------------------------
# v0.73.0 Phase 2/3/4: function/concept resolution
# ---------------------------------------------------------------------------


def test_51_resolve_concepts_exact_symbol() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        resolutions = engine_mod.resolve_concepts("What does reshape do?", docs_root_str=str(docs_root))
        hits = [r for r in resolutions if r.status == engine_mod.ResolutionStatus.RESOLVED.value]
        check("reshape resolves as an exact symbol", any(r.resolved_symbol == "reshape" for r in hits))
        check(
            "match_type is EXACT_SYMBOL for the literal token",
            any(r.resolved_symbol == "reshape" and r.match_type == engine_mod.MatchType.EXACT_SYMBOL.value for r in hits),
        )


def test_52_resolve_concepts_description_to_symbol() -> None:
    """The exact v0.72.0 regression: a natural-language description, not
    the literal function name, must still resolve to the real symbol."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        resolutions = engine_mod.resolve_concepts("Calculate the column means.", docs_root_str=str(docs_root))
        hits = [r for r in resolutions if r.status == engine_mod.ResolutionStatus.RESOLVED.value]
        check("resolves to meanc", any(r.resolved_symbol == "meanc" for r in hits))
        check(
            "match_type is ALIAS_OR_DESCRIPTION, not EXACT_SYMBOL",
            any(r.resolved_symbol == "meanc" and r.match_type == engine_mod.MatchType.ALIAS_OR_DESCRIPTION.value for r in hits),
        )
        check("citation names the real file", any(r.resolved_symbol == "meanc" and r.citation == "meanc.rst" for r in hits))


def test_53_resolve_concepts_multiple_resolved_functions() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        resolutions = engine_mod.resolve_concepts("Show me reshape and meanc.", docs_root_str=str(docs_root))
        resolved_symbols = {r.resolved_symbol for r in resolutions if r.status == engine_mod.ResolutionStatus.RESOLVED.value}
        check("both reshape and meanc resolved", resolved_symbols == {"reshape", "meanc"})


def test_54_resolve_concepts_ambiguous_resolution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Two files that both score identically for the token "alphafunc"
        # (same heading, same "command_in_file_name" bonus) -- a real,
        # reproducible ambiguous case from command_doc_lookup's own scoring.
        (root / "alphafuncx.rst").write_text("alphafunc\n=========\n\nPurpose\n-------\nDoes alpha thing one.\n", encoding="utf-8")
        (root / "alphafuncy.rst").write_text("alphafunc\n=========\n\nPurpose\n-------\nDoes alpha thing two.\n", encoding="utf-8")
        resolutions = engine_mod.resolve_concepts("Use alphafunc on my data.", docs_root_str=str(root))
        ambiguous = [r for r in resolutions if r.status == engine_mod.ResolutionStatus.AMBIGUOUS.value]
        check("alphafunc is reported as ambiguous, not silently resolved to one guess", len(ambiguous) == 1)
        check("candidates name both real files", set(ambiguous[0].candidates) == {"alphafuncx", "alphafuncy"})


def test_55_resolve_concepts_unresolved_phrase() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        resolutions = engine_mod.resolve_concepts("Use somefuncxyz for this.", docs_root_str=str(docs_root))
        unresolved = [r for r in resolutions if r.status == engine_mod.ResolutionStatus.UNRESOLVED.value]
        check("somefuncxyz is honestly reported as unresolved", any(r.user_phrase == "somefuncxyz" for r in unresolved))
        check("no resolved_symbol is fabricated for it", all(r.resolved_symbol is None for r in unresolved))


def test_56_resolve_concepts_deduplicates_alias_and_literal() -> None:
    """If the user's own literal token already resolves a symbol directly,
    a redundant alias-phrase match for the SAME symbol must not also
    appear as a second, duplicate resolution."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        # "meanc" (literal) and "column means" (alias) both resolve to
        # meanc -- must appear exactly once in the resolutions.
        resolutions = engine_mod.resolve_concepts(
            "Use meanc to calculate the column means.", docs_root_str=str(docs_root),
        )
        meanc_resolutions = [r for r in resolutions if r.resolved_symbol == "meanc"]
        check("meanc appears exactly once, not duplicated by the alias", len(meanc_resolutions) == 1)
        check("the literal exact match won, not the alias", meanc_resolutions[0].match_type == engine_mod.MatchType.EXACT_SYMBOL.value)


def test_57_resolve_concepts_returns_empty_without_docs_root() -> None:
    check("no docs_root -> no resolutions", engine_mod.resolve_concepts("Calculate the column means.", docs_root_str=None) == ())
    check(
        "nonexistent docs_root -> no resolutions",
        engine_mod.resolve_concepts("Calculate the column means.", docs_root_str="/does/not/exist") == (),
    )


# ---------------------------------------------------------------------------
# v0.73.0 Phase 5: grounding integration (resolution + ground_multi)
# ---------------------------------------------------------------------------


def test_58_ground_multi_merges_literal_and_resolved_symbol() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("Use reshape, then calculate the column means.", docs_root_str=str(docs_root))
        check("status is GROUNDED", bundle.status == engine_mod.GroundingStatus.GROUNDED)
        check("both the literal and the resolved symbol are present", set(bundle.matched_topics) == {"reshape", "meanc"})
        origins = {s.topic: s.origin for s in bundle.sources}
        check("reshape's origin is literal", origins["reshape"] == "literal")
        check("meanc's origin is resolved_concept", origins["meanc"] == "resolved_concept")


def test_59_ground_multi_resolved_symbol_plus_recent_topic() -> None:
    """Prior-topic retention (v0.72.0) plus a new natural-language
    resolution (v0.73.0) working together across two turns."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider(), docs_root=str(docs_root))
        r1 = engine.ask("Show me reshape.")
        check("first turn grounds on reshape", r1.grounding_topic == "reshape")
        r2 = engine.ask("Now calculate the column means.")
        check("second turn resolves meanc via the concept index", "meanc" in [s.topic for s in r2.grounding_sources])
        check("recent_topics retains both", set(engine.state.recent_topics) == {"reshape", "meanc"})


def test_60_ground_multi_dedup_when_alias_and_literal_both_match() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("Use meanc to calculate the column means.", docs_root_str=str(docs_root))
        check("meanc appears exactly once as a source", [s.topic for s in bundle.sources].count("meanc") == 1)


def test_61_ground_multi_source_bound_respected_with_resolutions() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi(
            "Use reshape, vec, meanc, stdc, and the matrix inverse.", docs_root_str=str(docs_root),
        )
        check(
            f"total sources never exceed MAX_GROUNDING_SOURCES ({engine_mod.MAX_GROUNDING_SOURCES})",
            len(bundle.sources) <= engine_mod.MAX_GROUNDING_SOURCES,
        )


def test_62_grounding_source_provenance_tracked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider(), docs_root=str(docs_root))
        engine.ask("Show me reshape.")
        r2 = engine.ask("Give me a short example.")  # pure pronoun follow-up -> recent_topic fallback
        check("follow-up source origin is recent_topic", any(s.origin == "recent_topic" for s in r2.grounding_sources))


# ---------------------------------------------------------------------------
# v0.73.0 Phase 6/7: the deterministic generation gate
# ---------------------------------------------------------------------------


def test_63_gate_grounded_is_full() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("What does reshape do?", docs_root_str=str(docs_root))
        gate = engine_mod.compute_generation_gate(bundle)
        check("policy is FULL", gate.policy == engine_mod.GenerationPolicy.FULL.value)
        check("allowed is True", gate.allowed)


def test_64_gate_partially_grounded_is_supported_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        bundle = engine_mod.ground_multi("Show me reshape and somefuncxyz.", docs_root_str=str(docs_root))
        gate = engine_mod.compute_generation_gate(bundle)
        check("policy is SUPPORTED_ONLY", gate.policy == engine_mod.GenerationPolicy.SUPPORTED_ONLY.value)
        check("allowed is True (the supported portion can still be generated)", gate.allowed)


def test_65_gate_ungrounded_is_block() -> None:
    bundle = engine_mod.ground_multi("Write GAUSS code for fooPanelEstimator.", docs_root_str=None)
    gate = engine_mod.compute_generation_gate(bundle)
    check("policy is BLOCK", gate.policy == engine_mod.GenerationPolicy.BLOCK.value)
    check("allowed is False", not gate.allowed)


def test_66_gate_ambiguous_is_clarify_regardless_of_grounded_status() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "alphafuncx.rst").write_text("alphafunc\n=========\n\nPurpose\n-------\nOne.\n", encoding="utf-8")
        (root / "alphafuncy.rst").write_text("alphafunc\n=========\n\nPurpose\n-------\nTwo.\n", encoding="utf-8")
        bundle = engine_mod.ground_multi("Use alphafunc and reshape.", docs_root_str=str(root))
        gate = engine_mod.compute_generation_gate(bundle)
        check("policy is CLARIFY even though reshape alone would be GROUNDED", gate.policy == engine_mod.GenerationPolicy.CLARIFY.value)
        check("allowed is False", not gate.allowed)


def test_67_provider_not_called_on_block() -> None:
    class ExplodingProvider:
        def complete(self, messages, *, max_tokens=1024):
            raise AssertionError("the provider must never be called when generation is BLOCKed")

    engine = engine_mod.ConversationEngine(provider=ExplodingProvider())  # no docs_root -> always UNGROUNDED
    result = engine.ask("Write GAUSS code for fooPanelEstimator.")  # must not raise
    check("returns the fixed BLOCK message without calling the provider", result.text == engine_mod.GENERATION_BLOCKED_MESSAGE)
    check("generation_policy recorded as BLOCK", result.generation_policy == engine_mod.GenerationPolicy.BLOCK.value)


def test_68_provider_not_called_on_clarify() -> None:
    class ExplodingProvider:
        def complete(self, messages, *, max_tokens=1024):
            raise AssertionError("the provider must never be called when generation requires CLARIFY")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "alphafuncx.rst").write_text("alphafunc\n=========\n\nPurpose\n-------\nOne.\n", encoding="utf-8")
        (root / "alphafuncy.rst").write_text("alphafunc\n=========\n\nPurpose\n-------\nTwo.\n", encoding="utf-8")
        engine = engine_mod.ConversationEngine(provider=ExplodingProvider(), docs_root=str(root))
        result = engine.ask("Write GAUSS code using alphafunc.")  # must not raise
        check("generation_policy recorded as CLARIFY", result.generation_policy == engine_mod.GenerationPolicy.CLARIFY.value)
        check("the clarify message names the ambiguous candidates", "alphafuncx" in result.text and "alphafuncy" in result.text)


# ---------------------------------------------------------------------------
# v0.73.0 Phase 8: post-generation symbol support checking
# ---------------------------------------------------------------------------


def test_69_documented_function_accepted_by_the_symbol_checker() -> None:
    check_result = engine_mod.check_generated_symbols("y = reshape(x, 2, -1);\nprint y;", supported_symbols=("reshape",))
    check("reshape recognized as supported", "reshape" in check_result.supported_symbols)
    check("nothing flagged as unknown", check_result.unknown_call_symbols == ())


def test_70_colmean_flagged_as_unknown() -> None:
    code = "y = reshape(x, 2, -1);\ncol_means = colmean(y);\nprint col_means;"
    check_result = engine_mod.check_generated_symbols(code, supported_symbols=("reshape",))
    check("colmean is flagged as unknown", "colmean" in check_result.unknown_call_symbols)
    check("reshape is not flagged", "reshape" not in check_result.unknown_call_symbols)


def test_71_variable_names_not_flagged() -> None:
    code = "x = 5;\ny = x + 1;\nz = y * 2;\nprint z;"
    check_result = engine_mod.check_generated_symbols(code, supported_symbols=())
    check("no call-shaped tokens exist here at all", check_result.unknown_call_symbols == ())


def test_72_user_defined_proc_not_flagged() -> None:
    code = "proc (1) = myproc(a, b);\n    retp(a+b);\nendp;\nz = myproc(1, 2);\nprint z;"
    check_result = engine_mod.check_generated_symbols(code, supported_symbols=())
    check("myproc is classified as user-defined/ambiguous, not unknown", "myproc" in check_result.user_defined_or_ambiguous_symbols)
    check("myproc is never flagged as an unknown hallucination", "myproc" not in check_result.unknown_call_symbols)


def test_73_known_language_syntax_accepted() -> None:
    code = "for j (1, 3, 1);\n    print j;\nendfor;\nif j == 2;\n    print \"two\";\nendif;"
    check_result = engine_mod.check_generated_symbols(code, supported_symbols=())
    check("the loop variable j is never flagged as an unknown call", "j" not in check_result.unknown_call_symbols)
    check("no language keyword is flagged either", not set(check_result.unknown_call_symbols) & {"for", "if", "endfor", "endif"})


def test_74_unknown_call_shaped_symbol_flagged() -> None:
    code = "z = gaussmagicsortxyz(y);\nprint z;"
    check_result = engine_mod.check_generated_symbols(code, supported_symbols=("reshape",))
    check("the invented function is flagged", "gaussmagicsortxyz" in check_result.unknown_call_symbols)


def test_75_multiple_code_blocks_handled_conservatively() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        canned = (
            "First block:\n\n```gauss\ny = reshape(x, 2, -1);\n```\n\n"
            "Second block:\n\n```gauss\ncol_means = colmean(y);\n```\n"
        )
        provider = provider_mod.FakeModelProvider(canned_answer=canned)
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Show me reshape and then compute the column means.")
        check("both code blocks were extracted", len(result.generated_code) == 2)
        check("the hallucinated symbol in the second block is still caught", "colmean" in result.unknown_symbols)


# ---------------------------------------------------------------------------
# v0.73.0 Phase 9/10: hard regressions for the exact v0.72.0 failures
# ---------------------------------------------------------------------------


def test_76_column_means_regression_resolves_to_meanc_and_flags_colmean_if_fabricated() -> None:
    """The exact v0.72.0 failure, made permanent. Even if the underlying
    model still fabricates `colmean` (a real model-quality issue this
    architecture cannot force a model to stop doing), the product's own
    grounding correctly resolves the real `meanc` function, generation is
    permitted (FULL, since meanc is genuinely documented), and the
    post-generation check still catches the fabrication if it happens."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(
            canned_answer="```gauss\ncol_means = colmean(y);\nprint col_means;\n```",
        )
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Calculate the column means.")
        check("resolves to the real meanc function", "meanc" in result.grounding_topic or "meanc" in [s.topic for s in result.grounding_sources])
        check("grounding status is GROUNDED", result.grounding_status == engine_mod.GroundingStatus.GROUNDED.value)
        check("generation policy is FULL", result.generation_policy == engine_mod.GenerationPolicy.FULL.value)
        check("colmean is flagged as an unknown symbol, never silently accepted", "colmean" in result.unknown_symbols)


def test_76b_column_means_variants_all_resolve_to_meanc() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        for phrase in ("average each column", "get the mean of every column", "compute column averages"):
            bundle = engine_mod.ground_multi(phrase, docs_root_str=str(docs_root))
            check(f"{phrase!r} resolves to meanc", "meanc" in bundle.matched_topics)


def test_77_panel_regression_without_authoritative_support_is_blocked() -> None:
    """The exact v0.72.0 panel-regression failure, made permanent: with NO
    panel-estimation documentation available, generation must be BLOCKed,
    never left to the model to fabricate a syntax pattern."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "docs"
        root.mkdir()
        (root / "reshape.rst").write_text(_RESHAPE_RST, encoding="utf-8")  # no panel-estimation docs at all
        engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider(), docs_root=str(root))
        result = engine.ask("Write GAUSS code for a panel regression.")
        check("generation is BLOCKed", result.generation_policy == engine_mod.GenerationPolicy.BLOCK.value)
        check("no code was generated", result.generated_code == ())
        check("the fixed honest message is shown", result.text == engine_mod.GENERATION_BLOCKED_MESSAGE)


def test_77b_panel_regression_with_authoritative_support_resolves_and_generates() -> None:
    """When the configured documentation DOES cover a real panel-estimation
    command (tscsFit), the request should resolve and be permitted --
    BLOCK is for missing evidence, not a blanket ban on this topic."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)  # includes tscsfit.rst
        bundle = engine_mod.ground_multi("Write GAUSS code for a panel regression.", docs_root_str=str(docs_root))
        gate = engine_mod.compute_generation_gate(bundle)
        check("resolves to tscsfit", "tscsfit" in bundle.matched_topics)
        check("generation policy is FULL", gate.policy == engine_mod.GenerationPolicy.FULL.value)


def test_78_run_this_still_blocked_after_resolution_changes() -> None:
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())
    result = engine.ask("Run this code for me.")
    check("still redirected", result.text == engine_mod.EXECUTION_BOUNDARY_MESSAGE)


def test_79_apply_this_code_still_blocked_after_resolution_changes() -> None:
    engine = engine_mod.ConversationEngine(provider=provider_mod.FakeModelProvider())
    result = engine.ask("Apply that code to my file.")
    check("still redirected", result.text == engine_mod.EXECUTION_BOUNDARY_MESSAGE)


# ---------------------------------------------------------------------------
# v0.73.0 safety: no execution/file/process authority anywhere in the new code
# ---------------------------------------------------------------------------


def test_80_new_v0_73_0_functions_have_no_execution_or_file_write_capability() -> None:
    import inspect

    for func in (
        engine_mod.resolve_concepts, engine_mod.compute_generation_gate, engine_mod.check_generated_symbols,
        engine_mod._render_clarify_message,
    ):
        source = inspect.getsource(func)
        for token in ("open(", "write_text", "write_bytes", "os.system", "subprocess.", "eval(", "exec("):
            check(f"{func.__name__} source does not contain {token!r}", token not in source)


def test_81_module_still_never_imports_execution_repair_or_filesystem_modules() -> None:
    """Re-confirms the same structural guarantee test_17/test_49 already
    cover, now that v0.73.0 added resolution/gating/symbol-checking code."""
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


def test_82_qa_classified_request_naming_an_unsupported_symbol_still_flags_it() -> None:
    """The exact real gap found during this milestone's own Phase 21 live
    evaluation: 'Use reshape and colmean on my data.' does not match any
    code-generation trigger phrase (it is not phrased as an explicit
    request to write code), so it classifies as QA, not CODE_GENERATION --
    but the model can still legitimately return code-shaped prose in a QA
    answer, and if it uses a hallucinated symbol there, the post-generation
    check must still catch it."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(
            canned_answer="```gauss\ny = reshape(x, 2, -1);\ncolumnMeans = colmean(y);\nprint columnMeans;\n```",
        )
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Use reshape and colmean on my data.")
        check("intent is QA (no explicit code-generation trigger phrase)", result.intent == engine_mod.Intent.QA.value)
        check("colmean is still flagged as an unknown symbol", "colmean" in result.unknown_symbols)


def test_83_companion_function_in_the_same_retrieved_source_is_not_a_false_positive() -> None:
    """v0.73.0 Phase 21 live evaluation found a real false positive:
    `invinvpd.rst` (grounded topic `inv`) legitimately documents `invpd`
    too, in the same real retrieved content, and the real model correctly
    used `invpd` -- the checker must not flag it as unknown merely because
    the RESOLVED topic name was `inv`, not `invpd`."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)  # invinvpd.rst documents both inv and invpd
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\nxi = invpd(x);\nprint xi;\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Invert this matrix.")
        check("resolved to inv", "inv" in [s.topic for s in result.grounding_sources])
        check("invpd is not flagged as unknown -- it's real, documented content from the same source", "invpd" not in result.unknown_symbols)


# ---------------------------------------------------------------------------
# v0.74.0: documentation-derived concept index (Phase 2/3)
# ---------------------------------------------------------------------------


def test_84_documentation_derived_index_resolves_a_phrase_not_in_curated_aliases() -> None:
    """`corrx` is NOT in `_CONCEPT_ALIAS_INDEX` at all -- this proves the new
    documentation-DERIVED index (built from the fixture doc's own heading +
    Purpose text) can resolve a natural-language phrase on its own."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = corrx(x);\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Write GAUSS code for the correlation between the columns of my dataset.")
        check("resolved to corrx via the derived index", "corrx" in [s.topic for s in result.grounding_sources])
        origins = {s.topic: s.origin for s in result.grounding_sources}
        check("provenance is derived_from_docs, not a curated alias", origins.get("corrx") == "derived_from_docs")
        # "dataset" is itself also attempted as a literal candidate token and
        # honestly reported unmatched (it is not a real symbol) -- this
        # makes the bundle PARTIALLY_GROUNDED, not GROUNDED, which is
        # correct: only that generation was still permitted at all is
        # actually being asserted here.
        check(
            "generation was permitted (FULL or SUPPORTED_ONLY)",
            result.generation_policy in (engine_mod.GenerationPolicy.FULL.value, engine_mod.GenerationPolicy.SUPPORTED_ONLY.value),
        )


def test_85_documentation_derived_candidate_not_in_this_docs_root_produces_no_resolution() -> None:
    """The re-verification discipline: a docs_root that does NOT contain
    `corrx.rst` at all must never resolve it, even if some other unrelated
    text happened to look similar -- there is no fixture describing
    correlation anywhere in this smaller root."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "docs"
        root.mkdir()
        (root / "meanc.rst").write_text(_MEANC_RST, encoding="utf-8")
        provider = provider_mod.FakeModelProvider(canned_answer="I don't have documentation for that.")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(root))
        result = engine.ask("What is the correlation between the columns of my dataset?")
        check("no fabricated resolution to corrx", "corrx" not in [s.topic for s in result.grounding_sources])


# ---------------------------------------------------------------------------
# v0.74.0: pre-execution validation (Phases 4-13)
# ---------------------------------------------------------------------------


def test_86_pre_execution_eligibility_populated_for_a_clean_full_gated_example() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = meanc(x);\nprint y;\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Calculate the column means.")
        check("policy is FULL", result.generation_policy == engine_mod.GenerationPolicy.FULL.value)
        check(
            "eligibility is ELIGIBLE_FOR_VALIDATION",
            result.pre_execution_eligibility == "eligible_for_validation",
        )
        check("no unresolved issues", result.pre_execution_issues == ())
        check("meanc call validated as compatible", any(
            v.symbol == "meanc" and v.argument_count_status == "compatible" for v in result.call_validations
        ))


def test_87_invpd_valid_symmetric_positive_definite_literal_is_eligible() -> None:
    """The exact v0.73.0 Finding 3 regression, valid side: a literal
    symmetric positive-definite matrix must be recognized as satisfying
    invpd's own documented precondition."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Invert this matrix.")
        satisfied = [c for c in result.precondition_checks if c.status == "satisfied"]
        check("invpd precondition reported satisfied", len(satisfied) == 1 and satisfied[0].precondition.symbol == "invpd")
        check("eligibility is ELIGIBLE_FOR_VALIDATION", result.pre_execution_eligibility == "eligible_for_validation")


def test_88_invpd_non_symmetric_literal_precondition_violated_is_ineligible() -> None:
    """The exact v0.73.0 Finding 3 regression, invalid side: a literal
    non-symmetric matrix must be flagged VIOLATED, and this must block
    eligibility even though nothing here claims GAUSS itself was run."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = invpd({2 1, 3 2});\nprint y;\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Invert this matrix.")
        violated = [c for c in result.precondition_checks if c.status == "violated"]
        check("invpd precondition reported violated", len(violated) == 1)
        check("eligibility is INELIGIBLE", result.pre_execution_eligibility == "ineligible")
        check("the violation is named in unresolved_issues", any("invpd" in issue for issue in result.pre_execution_issues))


def test_89_invpd_runtime_variable_argument_is_unverified_never_fabricated_satisfied() -> None:
    """A matrix that is a runtime value (not a literal, not traceable to a
    literal assignment in the same code) must be reported UNVERIFIED --
    this module must never claim SATISFIED without deterministic evidence,
    exactly mirroring the real documented invpd(x'x) OLS example, where x
    is real input data, not a literal this module could ever legitimately
    evaluate."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(
            canned_answer="```gauss\nx = loadd(\"mydata.csv\");\ny = invpd(x);\nprint y;\n```",
        )
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Invert this matrix.")
        unverified = [c for c in result.precondition_checks if c.precondition.symbol == "invpd"]
        check("invpd precondition present", len(unverified) == 1)
        check("status is unverified, not satisfied", unverified[0].status == "unverified")
        check("no fabricated SATISFIED anywhere", all(c.status != "satisfied" for c in result.precondition_checks))


def test_90_tscsmtcontrol_hallucination_surfaces_companion_hint_and_stays_ineligible() -> None:
    """The exact v0.73.0 `tscsmtControl` regression (live scenario 63.5):
    a FULL-gated request that correctly uses the real tscsFit signature can
    still hallucinate a secondary symbol. This must (a) still be flagged
    unknown, (b) surface the real documented companion
    (tscsmtControlCreate) as a hint without silently rewriting anything,
    and (c) never become eligible for validation."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(
            canned_answer=(
                "```gauss\ntsc = tscsmtControl();\ntso = tscsFit(y, x, grp);\nprint tso;\n```"
            ),
        )
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Write GAUSS code for a panel regression.")
        check("tscsmtControl still flagged unknown", "tscsmtControl" in result.unknown_symbols)
        hints = dict(result.companion_hints)
        check("companion hint names the real constructor", hints.get("tscsmtControl") == "tscsmtControlCreate")
        check("eligibility is INELIGIBLE -- no silent correction, no eligibility", result.pre_execution_eligibility == "ineligible")


def test_91_incompatible_argument_count_marks_call_incompatible_and_ineligible() -> None:
    """tscsFit's own fixture documents `tscsFit(y, x, grp[, tsc])` -- 3 or 4
    arguments. A generated call with only 2 must be flagged INCOMPATIBLE."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ntso = tscsFit(y, x);\nprint tso;\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Write GAUSS code for a panel regression.")
        incompatible = [v for v in result.call_validations if v.symbol == "tscsFit"]
        check("tscsFit call present", len(incompatible) == 1)
        check("flagged incompatible", incompatible[0].argument_count_status == "incompatible")
        check("eligibility is INELIGIBLE", result.pre_execution_eligibility == "ineligible")


def test_92_pre_execution_validation_only_runs_when_generation_actually_happened() -> None:
    """`BLOCK`/`CLARIFY` return before the provider is ever called, and a
    plain QA answer with no code never reaches the validation pass either --
    in both cases `pre_execution_eligibility` must stay `None`, distinct
    from an empty-but-checked result."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="not used")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))

        blocked = engine.ask("Write GAUSS code for a nonexistent completely unsupported topic xyzzy.")
        check("BLOCK leaves eligibility unset", blocked.pre_execution_eligibility is None)

        engine.reset()
        qa_provider = provider_mod.FakeModelProvider(canned_answer="reshape changes a matrix's dimensions.")
        qa_engine = engine_mod.ConversationEngine(provider=qa_provider, docs_root=str(docs_root))
        qa_result = qa_engine.ask("What does reshape do?")
        check("plain-prose QA answer leaves eligibility unset", qa_result.pre_execution_eligibility is None)


def test_93_new_v0_74_0_modules_have_no_execution_or_file_write_capability() -> None:
    import gauss_doc_concept_index as concept_index_mod
    import gauss_pre_execution_validation as validation_mod

    for module in (concept_index_mod, validation_mod):
        source = Path(module.__file__).read_text(encoding="utf-8")
        for token in ("open(", "write_text", "write_bytes", "os.system", "subprocess.", "eval(", "exec("):
            check(f"{module.__name__} source does not contain {token!r}", token not in source)


def test_94_new_v0_74_0_modules_never_import_execution_repair_or_filesystem_modules() -> None:
    import gauss_doc_concept_index as concept_index_mod
    import gauss_pre_execution_validation as validation_mod

    forbidden_modules = (
        "gauss_execution_workflow", "gauss_repair_application", "gauss_repair_draft",
        "gauss_repair_planner", "gauss_repair_approval", "gauss_verification_execution",
        "gauss_verification_review", "gauss_code_execution", "gauss_workspace", "subprocess",
    )
    for module in (concept_index_mod, validation_mod):
        for line in Path(module.__file__).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                for token in forbidden_modules:
                    check(f"{module.__name__} import line {stripped!r} does not reference {token!r}", token not in stripped)


def test_95_parenthetical_line_comment_is_not_mistaken_for_a_call() -> None:
    """The exact v0.74.0 live evaluation finding (category 64.x, scenario
    64.7): a real model wrote "// Set the method (optional, default is 0)"
    -- a plain GAUSS line comment containing a parenthetical remark --
    which must never be flagged as an unknown call to a function named
    `method`."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(
            canned_answer=(
                "```gauss\n"
                "// Set the method (optional, default is 0)\n"
                "y = meanc(x);\n"
                "```"
            ),
        )
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Calculate the column means.")
        check("comment parenthetical not flagged as an unknown symbol", "method" not in result.unknown_symbols)
        check("no fabricated call-validation entry for 'method'", not any(v.symbol == "method" for v in result.call_validations))


def test_96_block_comment_parenthetical_is_not_mistaken_for_a_call() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(
            canned_answer="```gauss\n/* uses helper(x) internally, see docs */\ny = meanc(x);\n```",
        )
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Calculate the column means.")
        check("block-comment parenthetical not flagged", "helper" not in result.unknown_symbols)


def test_97_common_builtin_is_not_mislabeled_not_documented_in_call_validation() -> None:
    """The exact v0.74.0 live evaluation finding (category 64.x, scenario
    64.7): `rows` (a real, common GAUSS builtin, already allowlisted for
    the post-generation unknown-symbol check) must also be recognized as
    documented by the pre-execution call-validation pass, not just by the
    older checker."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\nn = rows(x);\ny = meanc(x);\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Calculate the column means.")
        rows_validation = next(v for v in result.call_validations if v.symbol == "rows")
        check("rows is recognized as documented (a common builtin)", rows_validation.documented is True)


def test_98_multi_turn_reuse_of_an_earlier_grounded_function_is_not_flagged_unknown() -> None:
    """The exact v0.74.0 live evaluation finding (category 64.x, scenario
    64.10): a follow-up turn that legitimately reuses a function grounded
    in an EARLIER turn (without re-mentioning its name/description) must
    not have that function flagged as an unknown symbol merely because it
    is not part of THIS turn's own grounding bundle."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = meanc(x);\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        engine.ask("Calculate the column means.")  # grounds and remembers meanc

        provider.canned_answer = "```gauss\nz = invpd(y);\n```"
        result = engine.ask("Now invert that result.")
        check("meanc is not re-flagged as unknown in the follow-up turn", "meanc" not in result.unknown_symbols)


# ---------------------------------------------------------------------------
# v0.75.0: universal code-shaped-response validation -- the QA-intent
# eligibility gap this milestone's own objective is to close.
# ---------------------------------------------------------------------------


def test_99_qa_classified_turn_with_code_shaped_answer_now_gets_eligibility() -> None:
    """THE core v0.75.0 regression: v0.74.0 disclosed (but did not fix) a
    gap where a `QA`-classified turn producing code-shaped output never ran
    the pre-execution validation pass at all -- `pre_execution_eligibility`
    stayed `None` regardless of what the code actually contained. "What
    does meanc do?" classifies as `QA` (it matches no `_CODE_GENERATION_
    KEYWORDS` phrase), yet the model's own answer legitimately includes a
    real, well-formed `meanc` example -- this must now be validated and
    receive a real eligibility verdict, exactly as a `CODE_GENERATION`-
    classified turn already would."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        canned = (
            "meanc computes the mean of every column of a matrix. For example:\n\n"
            "```gauss\n"
            "x = meanc(y);\n"
            "```\n"
        )
        provider = provider_mod.FakeModelProvider(canned_answer=canned)
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("What does meanc do?")
        check("classified as QA, not CODE_GENERATION", result.intent == engine_mod.Intent.QA.value)
        check("code was actually extracted", result.generated_code != ())
        check("eligibility is no longer left unset for a QA-route code answer", result.pre_execution_eligibility is not None)
        check(
            "eligible for validation -- meanc is a real, correctly-used documented function",
            result.pre_execution_eligibility == "eligible_for_validation",
        )
        check("validation coverage was also computed", result.validation_coverage is not None)


def test_100_qa_classified_turn_with_hallucinated_symbol_is_now_ineligible_not_unvalidated() -> None:
    """Same gap, opposite outcome: a QA-route hallucination (`colmean`, the
    exact v0.72.0/v0.73.0 canonical fabricated-symbol example) must now be
    caught with a real `INELIGIBLE` verdict, not silently left unvalidated
    just because the turn was never classified `CODE_GENERATION`."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        canned = (
            "You can compute column averages like this:\n\n"
            "```gauss\n"
            "x = colmean(y);\n"
            "```\n"
        )
        provider = provider_mod.FakeModelProvider(canned_answer=canned)
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("What does reshape do?")
        check("classified as QA", result.intent == engine_mod.Intent.QA.value)
        check("hallucinated symbol still flagged", "colmean" in result.unknown_symbols)
        check("eligibility is computed, not left unset", result.pre_execution_eligibility is not None)
        check("ineligible", result.pre_execution_eligibility == "ineligible")
        check("issue names colmean", any("colmean" in issue for issue in result.pre_execution_issues))


def test_101_prose_only_qa_still_has_no_eligibility_verdict() -> None:
    """Phase 16 guardrail: universal validation must trigger ONLY on actual
    code-shaped content -- an ordinary prose QA answer must behave exactly
    as before (`pre_execution_eligibility` stays `None`, i.e. not
    applicable), never turned into a spurious validation failure."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="reshape changes the dimensions of a matrix without changing its data.")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("What does reshape do?")
        check("no code extracted", result.generated_code == ())
        check("eligibility not applicable (None)", result.pre_execution_eligibility is None)
        check("validation coverage also not computed", result.validation_coverage is None)


def test_102_code_generation_intent_still_validated_exactly_as_before_no_double_validation() -> None:
    """Non-regression: an explicit `CODE_GENERATION` request must still be
    validated exactly once (not twice merely because the universal routing
    fix runs for every intent now)."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        canned = "```gauss\nx = meanc(y);\n```\n"
        provider = provider_mod.FakeModelProvider(canned_answer=canned)
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Show me an example using meanc.")
        check("classified as CODE_GENERATION", result.intent == engine_mod.Intent.CODE_GENERATION.value)
        check("eligible", result.pre_execution_eligibility == "eligible_for_validation")
        check("exactly one call validation recorded for meanc, not duplicated", len(result.call_validations) == 1)


def test_103_follow_up_qa_turn_with_code_is_also_universally_validated() -> None:
    """A multi-turn conversation where turn 2 is a plain follow-up question
    (not itself CODE_GENERATION-phrased) that nonetheless produces code
    reusing an earlier turn's grounded topic -- validation must still run."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        engine = engine_mod.ConversationEngine(
            provider=provider_mod.FakeModelProvider(canned_answer="unused"), docs_root=str(docs_root),
        )
        engine.provider = provider_mod.FakeModelProvider(canned_answer="meanc computes the mean of every column.")
        first = engine.ask("What does meanc do?")
        check("first turn is prose-only, no eligibility", first.pre_execution_eligibility is None)

        engine.provider = provider_mod.FakeModelProvider(canned_answer="Sure:\n\n```gauss\nx = meanc(y);\n```\n")
        second = engine.ask("Now use meanc on my data.")
        check("second turn is a follow-up, not CODE_GENERATION-phrased", second.intent == engine_mod.Intent.QA.value)
        check("follow-up code is validated too", second.pre_execution_eligibility is not None)


# ---------------------------------------------------------------------------
# v0.76.0: syntax validation / coverage-hardening / handoff-readiness
# wiring, and the milestone's own hard regressions.
# ---------------------------------------------------------------------------


def test_104_semicolon_row_separator_matrix_literal_is_syntax_invalid_end_to_end() -> None:
    """The exact v0.75.0 live regression (evaluation 65.8b), reproduced
    through the full engine: a generated `invpd` example whose matrix
    literal used `;` as a row separator must now be caught by syntax
    validation and kept off the handoff-candidate path, even though the
    precondition checker itself can only, correctly, report UNVERIFIED for
    an unparseable literal."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\nx = {2 1; 1 2};\ny = invpd(x);\nprint y;\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Invert this matrix.")
        check("syntax validation ran", result.syntax_validation is not None)
        check("syntax invalid", result.syntax_validation.status == "invalid")
        check(
            "names the row separator problem",
            any("row separator" in issue.message for issue in result.syntax_validation.issues),
        )
        check("readiness computed", result.handoff_readiness is not None)
        check("not a handoff candidate", result.handoff_readiness.state == "not_ready")


def test_105_correctly_formatted_matrix_literal_equivalent_is_syntax_validated() -> None:
    """Phase 12's paired case: the correctly formatted GAUSS equivalent of
    the semicolon regression must NOT be penalized by syntax validation, and
    -- with a literal argument at the call site (so the parameter-role
    checker has real evidence, not a runtime-variable UNKNOWN) -- reaches
    real broad-evidence handoff candidacy."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Use invpd to invert this matrix.")
        check("syntax validated", result.syntax_validation.status == "validated")
        check("eligible", result.pre_execution_eligibility == "eligible_for_validation")
        check("handoff candidate", result.handoff_readiness.state == "handoff_candidate")


def test_106_dangling_assignment_is_syntax_invalid_end_to_end() -> None:
    """The exact `x = ;` regression, reproduced through the full engine."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\nx = ;\nprint x;\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Show me an example using meanc.")
        check("syntax invalid", result.syntax_validation.status == "invalid")
        check("names the dangling assignment", any("empty right-hand side" in i.message for i in result.syntax_validation.issues))
        check("not a handoff candidate", result.handoff_readiness.state == "not_ready")


def test_107_nested_reshape_and_meanc_call_parses_and_validates_through_the_full_engine() -> None:
    """Phase 14's exact example, `meanc(reshape(x, 2, 3))`, through the full
    engine: both real documented functions must be extracted, validated
    independently, and the code must be syntax-VALIDATED with no false
    unknown symbol."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = meanc(reshape(x, 2, 3));\nprint y;\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Reshape my data and take the column means.")
        check("no unknown symbols", result.unknown_symbols == ())
        check("both calls validated", {v.symbol for v in result.call_validations} == {"meanc", "reshape"})
        check("syntax validated", result.syntax_validation.status == "validated")
        check("eligible", result.pre_execution_eligibility == "eligible_for_validation")


def test_108_tscsmtcontrol_hallucination_still_prevented_from_handoff_readiness() -> None:
    """v0.76.0 re-confirmation of the exact v0.73.0 `tscsmtControl`
    regression (test_90 above): adding syntax validation/handoff readiness
    must not weaken this existing guarantee."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(
            canned_answer="```gauss\ntsc = tscsmtControl();\ntso = tscsFit(y, x, grp);\nprint tso;\n```",
        )
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Write GAUSS code for a panel regression.")
        check("still ineligible", result.pre_execution_eligibility == "ineligible")
        check("readiness computed", result.handoff_readiness is not None)
        check("not ready", result.handoff_readiness.state == "not_ready")


def test_109_invalid_invpd_precondition_still_prevented_from_handoff_readiness() -> None:
    """v0.76.0 re-confirmation of test_88 above: a violated documented
    precondition must still block handoff readiness, not just eligibility."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = invpd({2 1, 3 2});\nprint y;\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Invert this matrix.")
        check("still ineligible", result.pre_execution_eligibility == "ineligible")
        check("not ready", result.handoff_readiness.state == "not_ready")


def test_110_syntax_and_readiness_are_none_when_no_code_is_generated() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="reshape changes a matrix's dimensions.")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("What does reshape do?")
        check("syntax not applicable", result.syntax_validation is None)
        check("readiness not applicable", result.handoff_readiness is None)


def test_111_v0_76_0_module_still_never_imports_execution_repair_or_filesystem_modules() -> None:
    """Re-confirms the same structural safety guarantee test_49/test_94
    already cover, now that v0.76.0 added syntax validation and a
    handoff-readiness verdict -- neither adds any execution capability."""
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


def test_112_no_automatic_execution_handoff_is_ever_triggered() -> None:
    """Structural proof that reaching HANDOFF_CANDIDATE triggers nothing:
    `ConversationEngine.ask(...)`'s own source contains no call to any
    execution/repair-shaped function, regardless of what readiness state a
    turn computes."""
    import inspect

    source = inspect.getsource(engine_mod.ConversationEngine.ask)
    for token in ("execute(", "run_gauss", "apply_repair", "subprocess", "os.system"):
        check(f"ask(...) source does not contain {token!r}", token not in source)


def test_112b_grounding_token_cap_regression_reaches_both_late_function_names() -> None:
    """v0.77.0 (Phase 12): the EXACT real, disclosed v0.76.0 finding --
    `evaluations/runs/2026-09-14-code-assistant-gauss-syntax-validation-run-
    002.md`'s own note -- reproduced verbatim. The original `66.2` benchmark
    wording placed `meanc`/`reshape` at the very end of a long sentence;
    `_candidate_tokens`'s pre-existing left-to-right-only MAX_TOKEN_LOOKUPS=6
    cap consumed its budget on `computes`/`means`/`reshaped`/`version`/
    `element`/`vector` first, so NEITHER function was ever attempted as a
    grounding candidate. This test proves the reprioritized
    `_candidate_tokens`/`resolve_concepts` now reaches both."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        question = (
            "Write GAUSS code that computes the column means of a reshaped 2x3 version of a "
            "6-element vector x, using meanc and reshape."
        )
        candidates = engine_mod._candidate_tokens(question, docs_root=docs_root)
        check("meanc reachable within the cap", "meanc" in candidates)
        check("reshape reachable within the cap", "reshape" in candidates)
        check("cap itself is unchanged", len(candidates) <= engine_mod.MAX_TOKEN_LOOKUPS)

        resolutions = engine_mod.resolve_concepts(question, docs_root_str=str(docs_root))
        resolved_symbols = {r.resolved_symbol for r in resolutions if r.status == engine_mod.ResolutionStatus.RESOLVED.value}
        check("meanc actually resolved", "meanc" in resolved_symbols)
        check("reshape actually resolved", "reshape" in resolved_symbols)


def test_112c_candidate_tokens_without_docs_root_keeps_original_order_for_ties() -> None:
    """Backward compatibility: when `docs_root`/`recent_topics` are omitted
    (as every pre-v0.77.0 call site implicitly did), tokens with no tier-0/
    tier-1/tier-2 signal keep their original left-to-right order -- the
    reprioritization changes WHICH tokens are chosen, never the tie-break
    order among equally-unprioritized ones."""
    tokens = engine_mod._candidate_tokens("alpha beta gamma delta epsilon zeta eta theta")
    check("still exactly the first six in original order", tokens == ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"])


def test_112d_call_shaped_token_in_question_gets_top_priority() -> None:
    """Tier 0: a token immediately followed by `(` in the raw question text
    outranks a tier-1 concept-alias match and ordinary lexical tokens."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        question = (
            "I was reading about averaging and statistics summaries and general numeric data "
            "handling techniques when I noticed stdc(x) mentioned somewhere."
        )
        tokens = engine_mod._candidate_tokens(question, docs_root=docs_root)
        check("call-shaped stdc reaches the front", tokens[0] == "stdc")


def test_112e_concept_alias_symbol_outranks_plain_lexical_tokens() -> None:
    """Tier 1: a bare token that IS itself a curated concept-alias symbol
    (e.g. 'meanc') is promoted ahead of ordinary lexical tokens, even with
    no docs_root/recent_topics supplied at all."""
    tokens = engine_mod._candidate_tokens(
        "computing something about averaging summarizing numbers involving meanc directly"
    )
    check("meanc promoted ahead of earlier lexical tokens", tokens.index("meanc") < tokens.index("computing"))


def test_113_v0_77_0_module_never_imports_differential_harness_tooling() -> None:
    """v0.77.0 adds a real-GAUSS-invoking differential syntax-validation
    harness (gauss_differential_harness.py) plus its corpus builder
    (build_differential_corpus.py) -- both are evaluation infrastructure
    only. Re-confirms the same structural guarantee test_49/test_94/test_111
    already cover, extended with the new module names, plus the execution
    adapter those tools route real GAUSS invocation through."""
    forbidden_modules = (
        "gauss_execution_workflow", "gauss_repair_application", "gauss_repair_draft",
        "gauss_repair_planner", "gauss_repair_approval", "gauss_verification_execution",
        "gauss_verification_review", "gauss_code_execution", "gauss_workspace", "subprocess",
        "gauss_differential_harness", "build_differential_corpus", "gauss_execution_adapter",
    )
    for line in Path(engine_mod.__file__).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            for token in forbidden_modules:
                check(f"import line {stripped!r} does not reference {token!r}", token not in stripped)


# ---------------------------------------------------------------------------
# v0.80.0: the unknown-symbol checker and the call extractor share
# gauss_pre_execution_validation.call_scan_text(...) -- the bare-`print`
# gap reproduced live in evaluation 69.1.
# ---------------------------------------------------------------------------


def test_114_print_wrapped_hallucinated_call_is_flagged_unknown() -> None:
    result = engine_mod.check_generated_symbols("print colmean(x);", supported_symbols=())
    check("colmean flagged unknown", result.unknown_call_symbols == ("colmean",))


def test_115_checker_and_extractor_see_the_same_call_symbols() -> None:
    """Drift guard: the two scanners must never disagree about which
    symbols are calls, or a call could be validated but not symbol-checked
    (or vice versa)."""
    import gauss_pre_execution_validation as validation_mod

    snippets = (
        "print colmean(x);", "printfm(x, 1, mask);", "forecast = arima(y, 1);", "retp(f(x));",
        "if f(x) > 0;", "for i (1, rows(x), 1);", "proc (1) = myf(x);", "local a, b;",
        'print "Inverse (2x2):";', "do while i <= rows(x);", "y = invpd({2 1, 1 2});\nprint y;",
    )
    for code in snippets:
        extracted = {c.symbol.lower() for c in validation_mod.extract_generated_calls(code)}
        checked = engine_mod.check_generated_symbols(code, supported_symbols=())
        seen = {s.lower() for s in checked.supported_symbols + checked.unknown_call_symbols + checked.user_defined_or_ambiguous_symbols}
        check(f"same call symbols for {code!r}", extracted == seen)


def test_116_print_wrapped_precondition_violation_reaches_not_ready_through_ask() -> None:
    """End to end: previously this answer's `invpd` call was never extracted,
    so its non-symmetric literal escaped the documented-precondition check."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\nprint invpd({2 1, 3 2});\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        result = engine.ask("Use invpd to invert this matrix.")
        check("precondition evaluated", len(result.precondition_checks) > 0)
        check("violation detected", any(pc.status == "violated" for pc in result.precondition_checks))
        check("readiness is not_ready", result.handoff_readiness is not None and result.handoff_readiness.state == "not_ready")


def test_117_system_statement_in_otherwise_candidate_code_is_not_ready_through_ask() -> None:
    """v0.80.0: code that would otherwise reach HANDOFF_CANDIDATE (the typed
    invpd fixture shape) becomes NOT_READY once it also shells out."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "docs"
        root.mkdir()
        (root / "invinvpd.rst").write_text(_INV_RST.replace(
            "    :param x: data", "    :param x: data\n    :type x: NxN matrix",
        ), encoding="utf-8")
        provider = provider_mod.FakeModelProvider(canned_answer='```gauss\ny = invpd({2 1, 1 2});\nprint y;\ndos "dir";\n```')
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(root))
        result = engine.ask("Use invpd to invert this matrix.")
        check("dos found", [(f.name, f.category) for f in result.system_statements] == [("dos", "os_command")])
        check("not_ready", result.handoff_readiness is not None and result.handoff_readiness.state == "not_ready")


# ---------------------------------------------------------------------------
# v0.80.0: validate_code(...) -- client-authored code, server-computed verdict
# ---------------------------------------------------------------------------


def _typed_docs_root(tmp: str) -> str:
    root = Path(tmp) / "docs"
    root.mkdir()
    (root / "invinvpd.rst").write_text(_INV_RST.replace(
        "    :param x: data", "    :param x: data\n    :type x: NxN matrix",
    ), encoding="utf-8")
    return str(root)


def test_118_validate_code_reaches_candidate_for_documented_literal_code() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = engine_mod.validate_code("y = invpd({2 1, 1 2});\nprint y;", docs_root=_typed_docs_root(tmp))
        check("called invpd", result.called_symbols == ("invpd",))
        check("y is user-defined, not looked up", "y" in result.user_defined_symbols)
        check("handoff_candidate", result.handoff_readiness.state == "handoff_candidate")
        check("generated_code is exactly the input", result.generated_code == ("y = invpd({2 1, 1 2});\nprint y;",))


def test_119_validate_code_rejects_hallucinated_violating_and_system_code() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_docs_root(tmp)
        hallucinated = engine_mod.validate_code("print colmean(x);", docs_root=root)
        check("colmean not_ready", hallucinated.handoff_readiness.state == "not_ready")
        check("colmean unsupported", "colmean" in hallucinated.unsupported_topics)
        violating = engine_mod.validate_code("print invpd({2 1, 3 2});", docs_root=root)
        check("non-symmetric literal not_ready", violating.handoff_readiness.state == "not_ready")
        system = engine_mod.validate_code('y = invpd({2 1, 1 2});\nprint y;\ndos "dir";', docs_root=root)
        check("dos not_ready", system.handoff_readiness.state == "not_ready")


def test_120_validate_code_no_documented_calls_is_not_ready_with_a_note() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = engine_mod.validate_code("x = {1 2, 3 4};\nprint x;", docs_root=_typed_docs_root(tmp))
        check("not_ready", result.handoff_readiness.state == "not_ready")
        check("explains why", result.notes == (engine_mod.NO_DOCUMENTED_CALLS_NOTE,))


def test_121_validate_code_structural_rejections_never_raise() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_docs_root(tmp)
        cases = {
            "": "empty_code",
            "```gauss\nprint 1;\n```": "fenced_code",
            "x" * (engine_mod.MAX_VALIDATE_CODE_CHARS + 1): "code_too_large",
            "\n".join(f"y{i} = f{i}(1);" for i in range(engine_mod.MAX_VALIDATE_CODE_SYMBOLS + 1)): "too_many_symbols",
        }
        for code, reason in cases.items():
            result = engine_mod.validate_code(code, docs_root=root)
            check(f"{reason} rejected", result.rejected_reason == reason and result.handoff_readiness.state == "not_ready")
    check("no docs root rejected", engine_mod.validate_code("y = meanc(x);", docs_root=None).rejected_reason == "docs_root_not_configured")


# ---------------------------------------------------------------------------
# v0.81.0: idiomatic (assign-then-call) code reaches HANDOFF_CANDIDATE through
# real traced evidence; every NOT_READY protection still holds
# ---------------------------------------------------------------------------

#: Synthetic, typed fixtures modelled on the real `.. function::` blocks
#: (`:type`/`:rtype` lines), never a real docs checkout.
_TYPED_V081_RST = {
    "meanc.rst": "meanc\n=====\n\n.. function:: y = meanc(x)\n\n    :param x: data\n    :type x: NxK matrix\n\n"
                 "    :return y: column means\n    :rtype y: Kx1 matrix\n",
    "stdc.rst": "stdc\n====\n\n.. function:: y = stdc(x)\n\n    :param x: data\n    :type x: NxK matrix\n\n"
                "    :return y: column standard deviations\n    :rtype y: Kx1 matrix\n",
    "rndu.rst": "rndu\n====\n\n.. function:: y = rndu(r, c)\n\n    :param r: row dimension.\n    :type r: scalar\n\n"
                "    :param c: column dimension.\n    :type c: scalar\n\n    :return y: uniform random numbers.\n"
                "    :rtype y: RxC matrix\n",
    "zeros.rst": "zeros\n=====\n\n.. function:: y = zeros(r, c)\n\n    :param r: rows\n    :type r: scalar\n\n"
                 "    :param c: columns\n    :type c: scalar\n\n    :return y: zeros\n    :rtype y: RxC matrix\n",
    "invinvpd.rst": _INV_RST.replace("    :param x: data", "    :param x: data\n    :type x: NxN matrix"),
}


def _typed_v081_docs_root(tmp: str) -> str:
    root = Path(tmp) / "docs"
    root.mkdir()
    for name, text in _TYPED_V081_RST.items():
        (root / name).write_text(text, encoding="utf-8")
    return str(root)


def test_123_v081_idiomatic_assign_then_call_code_reaches_candidate() -> None:
    """Every snippet here was `review_required` (or, for the vector/scalar
    literal rows, falsely `not_ready`) before v0.81.0 -- see
    `planning/v0.81-idiomatic-handoff-candidacy.md`."""
    snippets = (
        "x = {1 2, 3 4};\ny = meanc(x);",
        "x = rndu(100, 4);\ny = meanc(x);",
        "x = rndu(1e5, 4);\ny = meanc(x);",
        "n = 5;\nx = zeros(n, 1);",
        "y = meanc({1,2,3});",
        "y = meanc(5);",
        "x = {1,2,3}; m = meanc(x); s = stdc(x); print m s;",
        "a = {2 1, 1 2};\nai = invpd(a);\nprint ai;",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v081_docs_root(tmp)
        for code in snippets:
            result = engine_mod.validate_code(code, docs_root=root)
            check(f"candidate: {code!r}", result.handoff_readiness.state == "handoff_candidate")


def test_124_v081_protections_still_not_ready_through_traced_variables() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v081_docs_root(tmp)
        cases = (
            "x = {1 2, 2 1};\ny = invpd(x);",                  # not positive definite, via a variable
            "x = {2 1, 1 2};\nx = {-1 0, 0 -1};\ny = invpd(x);",  # the governing (latest) assignment violates
            "y = meanc(\"abc\");",                             # string where a matrix is documented
            "y = zeros({1 2}, 3);",                            # vector where a scalar is documented
            "y = meanc(1, 2);",                                # argument count
            "x = colmean({1,2});",                             # hallucinated symbol
            "x = {2 1, 1 2};\ny = invpd(x);\ndos \"dir\";",    # system statement
        )
        for code in cases:
            result = engine_mod.validate_code(code, docs_root=root)
            check(f"not_ready: {code!r}", result.handoff_readiness.state == "not_ready")


def test_125_v081_untraceable_variables_stay_review_required() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v081_docs_root(tmp)
        cases = (
            "x = rndu(100, 3);\nb = invpd(x'x);",           # an expression is never evaluated
            # v0.82.0 (option B, user-approved): the v0.81.0 case
            # `x = {1,2,3}; x[1] = 9; y = meanc(x);` is superseded -- an indexed
            # write cannot change a numeric variable's shape (real G0058
            # evidence), so meanc's role check now traces `x` and the snippet
            # is a candidate (test_128). Its precondition tracing still refuses.
            "x = {1,2,3};\nx.a = 9;\ny = meanc(x);",        # member write
            "x = {1,2,3};\nfor i(1, 3, 1);\n  x = x + 1;\nendfor;\ny = meanc(x);",  # write inside a block
        )
        for code in cases:
            result = engine_mod.validate_code(code, docs_root=root)
            check(f"review_required: {code!r}", result.handoff_readiness.state == "review_required")


def test_126_v081_ask_path_extracts_signature_for_called_ungrounded_builtin() -> None:
    """Run 2026-09-12 (pre-execution validation run-002): on the `ask()`
    path, `rndu` -- a `_COMMON_BUILTIN_SYMBOLS` entry, not the grounded
    topic -- got "signature: unknown". It now gets its documented one."""
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v081_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\nx = rndu(100, 4);\ny = meanc(x);\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=root)
        result = engine.ask("Use meanc to compute the column means of a matrix.")
        rndu = [cv for cv in result.call_validations if cv.symbol == "rndu"]
        check("rndu validated", len(rndu) == 1)
        check("rndu signature now known", bool(rndu) and rndu[0].signature_known)
        check("meanc(x) traced to rndu's documented return", any(
            c.symbol == "meanc" and c.origin == "documented_return" and c.status == "match"
            for c in result.parameter_role_checks
        ))
        check("candidate", result.handoff_readiness is not None and result.handoff_readiness.state == "handoff_candidate")


_VCMVCX_RST = """vcm, vcx
========

Purpose
-------
Computes a variance-covariance matrix.

.. function:: vc = vcm(m [, ddof])
              vc = vcx(x [, ddof])

    :param x: data
    :type x: NxK matrix

    :return vc: variance-covariance matrix
    :rtype vc: KxK matrix
"""

_VCMSVCXS_RST = """vcms, vcxs
==========

Purpose
-------
Computes the observed variance-covariance matrix. :func:`vcxs` is kept for backwards compatibility.

.. function:: vc = vcms(m)
              vc = vcxs(x)

    :param x: data
    :type x: NxK matrix

.. seealso:: Functions :func:`vcx`, :func:`vcm`
"""


def test_127_v081_ambiguous_lookup_resolved_when_exactly_one_page_defines_the_call() -> None:
    """v0.81.0 re-baseline finding: `vcx` (on combined page `vcmvcx.rst`)
    scored ambiguous against `vcmsvcxs.rst`, which defines only `vcxs`."""
    import command_doc_lookup as doc_lookup_mod

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(_typed_v081_docs_root(tmp))
        (root / "vcmvcx.rst").write_text(_VCMVCX_RST, encoding="utf-8")
        (root / "vcmsvcxs.rst").write_text(_VCMSVCXS_RST, encoding="utf-8")
        raw = doc_lookup_mod.lookup("vcx", root, max_results=3)
        check("fixture reproduces the ambiguity", raw["status"] == "ambiguous")
        result = engine_mod.validate_code("x = rndu(5, 2);\nv = vcx(x);", docs_root=str(root))
        check("vcx grounded", "vcx" in result.pre_execution.call_validations[1].symbol and not result.ambiguous_topics)
        check("cites the defining page", any(s.citation and s.citation.endswith("vcmvcx.rst") for s in result.grounding_sources))
        check("candidate", result.handoff_readiness.state == "handoff_candidate")

        # Both pages defining `vcx(` -> still ambiguous, still not_ready.
        (root / "vcmsvcxs.rst").write_text(_VCMSVCXS_RST.replace("vc = vcxs(x)", "vc = vcx(x)"), encoding="utf-8")
        both = engine_mod.validate_code("x = rndu(5, 2);\nv = vcx(x);", docs_root=str(root))
        check("two defining pages stay ambiguous", both.ambiguous_topics == ("vcx",))
        check("two defining pages stay not_ready", both.handoff_readiness.state == "not_ready")


def test_122_validation_functions_contain_no_execution_or_write_primitives() -> None:
    import inspect

    for fn in (engine_mod.validate_code, engine_mod.validate_generated_code):
        source = inspect.getsource(fn)
        for forbidden in ("open(", "write_", "subprocess.", "eval(", "exec("):
            check(f"{fn.__name__} has no {forbidden!r}", forbidden not in source)
        params = inspect.signature(fn).parameters
        check(f"{fn.__name__} takes no model/provider argument", not any(
            "model" in p or "provider" in p for p in params
        ))


# ---------------------------------------------------------------------------
# v0.82.0: simple `for` loops reach HANDOFF_CANDIDATE through the bounded
# `for_block` syntax rule; every NOT_READY protection still holds inside a
# validated loop body. Readiness policy unchanged.
# ---------------------------------------------------------------------------

_TYPED_V082_RST = dict(_TYPED_V081_RST, **{
    "rows.rst": "rows\n====\n\n.. function:: y = rows(x)\n\n    :param x: any valid matrix\n    :type x: NxK matrix\n\n"
                "    :return y: number of rows\n    :rtype y: scalar\n",
    "cols.rst": "cols\n====\n\n.. function:: y = cols(x)\n\n    :param x: any valid matrix\n    :type x: NxK matrix\n\n"
                "    :return y: number of columns\n    :rtype y: scalar\n",
})


def _typed_v082_docs_root(tmp: str) -> str:
    root = Path(tmp) / "docs"
    root.mkdir()
    for name, text in _TYPED_V082_RST.items():
        (root / name).write_text(text, encoding="utf-8")
    return str(root)


def test_128_v082_simple_for_loops_reach_candidate() -> None:
    """Live finding 71.3: the first snippet was `review_required` in v0.81.0
    only because any `for` block capped syntax coverage at partial."""
    snippets = (
        "v = zeros(5, 1);\nfor i(1, 5, 1);\n    v[i] = i^2;\nendfor;\nprint v;",
        "v = zeros(5, 1); for i(1, 5, 1); v[i] = i^2; endfor; print v;",
        "x = zeros(3, 4);\nfor i (1, rows(x), 1);\n    for j (1, cols(x), 1);\n        x[i,j] = i * j;\n    endfor;\nendfor;\nprint x;",
        # option B: fill, then a statistic -- the role check looks through the indexed writes
        "v = zeros(5, 1);\nfor i (1, 5, 1);\n    v[i] = i^2;\nendfor;\nm = meanc(v);\nprint m;",
        # pre-v0.82.0 this read the indexed write as untraceable (test_125's superseded case)
        "x = {1,2,3};\nx[1] = 9;\ny = meanc(x);",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v082_docs_root(tmp)
        for code in snippets:
            result = engine_mod.validate_code(code, docs_root=root)
            check(f"candidate: {code!r}", result.handoff_readiness.state == "handoff_candidate")
            check(f"syntax validated: {code!r}", result.pre_execution.syntax.status == "validated")


def test_129_v082_protections_inside_a_validated_loop_stay_not_ready() -> None:
    loop = "v = zeros(5, 1);\nfor i (1, 5, 1);\n    {body}\nendfor;\nprint v;"
    cases = {
        "hallucinated symbol": loop.format(body="v[i] = colmean(i);"),
        "system statement": loop.format(body='dos "dir";\n    v[i] = i;'),
        "SPD violation through a variable": "x = {1 2, 2 1};\nfor i (1, 2, 1);\n    y = invpd(x);\nendfor;",
        "SPD violation on a literal": loop.format(body="y = invpd({-1 0, 0 -1});"),
        "argument count": loop.format(body="v[i] = meanc(i, 2);"),
        "string where a matrix is documented": loop.format(body='y = meanc("abc");'),
        "let misuse in the body": loop.format(body="v[i] = {1};"),
        "assignment to the loop counter": loop.format(body="i = 2;"),
        "unclosed loop": "v = zeros(5, 1);\nfor i (1, 5, 1);\n    v[i] = i;\nprint v;",
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v082_docs_root(tmp)
        for name, code in cases.items():
            result = engine_mod.validate_code(code, docs_root=root)
            check(f"not_ready: {name}", result.handoff_readiness.state == "not_ready")
            check(f"no validation_id-bearing verdict: {name}", result.handoff_readiness.state != "handoff_candidate")


def test_130_v082_unmodelled_loops_and_value_tracing_stay_review_required() -> None:
    cases = {
        "if inside the loop": "v = zeros(5, 1);\nfor i (1, 5, 1);\n    if i > 2;\n        v[i] = i;\n    endif;\nendfor;\nprint v;",
        "break inside the loop": "v = zeros(5, 1);\nfor i (1, 5, 1);\n    v[i] = i;\n    break;\nendfor;\nprint v;",
        "fractional step": "v = zeros(5, 1);\nfor i (1, 3, 0.5);\n    v[i] = i;\nendfor;\nprint v;",
        "threadfor": "v = zeros(5, 1);\nthreadfor i(1, 5, 1);\n    v[i] = i;\nthreadendfor;\nprint v;",
        "indexed write before invpd (value no longer traceable)": "x = {2 1, 1 2};\nx[1, 1] = -5;\ny = invpd(x);",
        "plain write inside the loop": "x = {1,2,3};\nfor i(1, 3, 1);\n  x = x + 1;\nendfor;\ny = meanc(x);",
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v082_docs_root(tmp)
        for name, code in cases.items():
            result = engine_mod.validate_code(code, docs_root=root)
            check(f"review_required: {name}", result.handoff_readiness.state == "review_required")


def test_131_v082_one_line_loop_counter_is_never_a_hallucinated_symbol() -> None:
    """Pre-v0.82.0, `call_scan_text` blanked a `for` counter only at the start
    of a line, so the one-line form read `i(` as a call to `i`."""
    code = "v = zeros(5, 1); for i(1, 5, 1); v[i] = i; endfor; print v;"
    symbol_check = engine_mod.check_generated_symbols(code, supported_symbols=("zeros",))
    check("no unknown symbols", symbol_check.unknown_call_symbols == ())
    check("no ambiguous symbols", symbol_check.user_defined_or_ambiguous_symbols == ())


def test_132_v082_io_network_and_database_calls_are_not_ready_through_validate_code() -> None:
    """Pre-v0.82.0, `x = fred_load("GNPCA");` (a web API call) reached
    HANDOFF_CANDIDATE against the real docs; v0.82.0's own signature fix
    briefly made `plotSave(...)` (a file write) one too. Synthetic, fully
    typed fixtures here, so only the registry can stop them."""
    pages = {
        "fred_load.rst": "fred_load\n=========\n\n.. function:: data = fred_load(series_id)\n\n"
                         "    :param series_id: FRED series id\n    :type series_id: string\n\n"
                         "    :return data: observations\n    :rtype data: dataframe\n",
        "plotsave.rst": "plotSave\n========\n\n.. function:: plotSave(filename[, size[, units[, dpi]]])\n\n"
                        "    :param filename: name of the file\n    :type filename: string\n\n"
                        "    :param size: dimensions\n    :type size: 2x1 vector\n",
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(_typed_v082_docs_root(tmp))
        for name, text in pages.items():
            (root / name).write_text(text, encoding="utf-8")
        for code, name in (('x = fred_load("GNPCA");', "fred_load"), ('plotSave("f.png", {800, 600});', "plotsave")):
            result = engine_mod.validate_code(code, docs_root=str(root))
            check(f"{name}: not_ready", result.handoff_readiness.state == "not_ready")
            check(f"{name}: named as a system statement",
                  any(f.name == name for f in result.pre_execution.system_statements))


def test_133_v082_param_continuation_lines_are_never_syntax() -> None:
    """Live finding 71.5: `vcmvcx.rst`'s ddof description was spliced into the
    extracted Syntax line, because an indented `(...)` line inside a
    `:param` block was also collected as an alternate call form."""
    import command_doc_lookup as doc_lookup_mod

    lines = [
        ".. function:: vc = vcm(m [, ddof])",
        "              vc = vcx(x [, ddof])",
        "",
        "    :param ddof: Optional input,  delta degrees of freedom. The divisor",
        "          will be :math:`(N - ddof)`. Default = 1 (sample covariance matrix).",
        "    :type ddof: Scalar",
    ]
    syntax = doc_lookup_mod.extract_function_directive_details(lines)["syntax"]
    check("both call forms kept", syntax == [".. function:: vc = vcm(m [, ddof])", "vc = vcx(x [, ddof])"])
    check("description not spliced in", not any("N - ddof" in s for s in syntax))



# ---------------------------------------------------------------------------
# v0.83.0: verdict explanations and search recall
# ---------------------------------------------------------------------------

_SPRINTF_RST = (
    "sprintf\n=======\n\n.. function:: s = sprintf(fmt, ...)\n\n"
    "    :param fmt: A sprintf style format string.\n    :type fmt: string\n\n"
    "    :param ....: One or more matrices or string arrays to add to the formatted string output.\n"
    "    :type ....: NxK numeric or string vectors\n\n"
    "    :return s: contains the formatted version of the input vectors.\n\n    :rtype s: Nx1 string array\n"
)


def test_134_v083_no_documented_call_reason_names_the_real_cause() -> None:
    """Live findings 72.6/72.8: not_ready was explained as "generation policy
    does not permit code generation (block)" although nothing was generated."""
    cases = (
        "s = 0;\nfor i(1, 20, 1);\n    s = s + i;\nendfor;\nprint s;",
        "s = 0;\nfor i(1, 100, 1);\n    s = s + i;\n    if s > 50;\n        break;\n    endif;\nendfor;\nprint s;",
        "x = colmedian({1, 2, 3});",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v082_docs_root(tmp)
        for code in cases:
            result = engine_mod.validate_code(code, docs_root=root)
            reasons = result.handoff_readiness.reasons
            check(f"still not_ready: {code[:20]!r}", result.handoff_readiness.state == "not_ready")
            check(f"real cause first: {code[:20]!r}", reasons[0] == engine_mod.NO_DOCUMENTED_CALLS_ISSUE)
            check(f"no generation wording: {code[:20]!r}", not any("generation policy" in r for r in reasons))
            check(f"note kept: {code[:20]!r}", result.notes == (engine_mod.NO_DOCUMENTED_CALLS_NOTE,))
        hallucinated = engine_mod.validate_code(cases[2], docs_root=root).handoff_readiness.reasons
        check("an unknown call is still named too", any("colmedian" in r for r in hallucinated))


def test_135_v083_partial_verdicts_name_their_cause() -> None:
    """Live findings 72.3/72.15: the client guessed the cause of "validation
    coverage is partial" wrong twice."""
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v082_docs_root(tmp)
        result = engine_mod.validate_code("v = 1 ./ rndu(10, 1);\nmu = meanc(v);", docs_root=root)
        reasons = result.handoff_readiness.reasons
        check("72.3 shape still review_required", result.handoff_readiness.state == "review_required")
        check("names the dimension", any("(incomplete: parameter roles partial)" in r for r in reasons))
        check("names symbol, argument, parameter and cause", any(
            "`meanc` argument 1 (parameter `x`): `v` is assigned from an expression (`1 ./ rndu(10, 1)`)" in r
            for r in reasons
        ))
        gaps = result.pre_execution.coverage_gaps
        check("structured gap", [(g.check, g.symbol, g.argument, g.parameter, g.cause) for g in gaps]
              == [("parameter_role", "meanc", 1, "x", "argument_assigned_from_expression")])

        looped = engine_mod.validate_code(
            "x = rndu(10, 1);\nfor i(1, 10, 1);\n    if i > 5;\n        break;\n    endif;\nendfor;\nm = meanc(x);",
            docs_root=root,
        )
        check("if/break with a documented call: review_required", looped.handoff_readiness.state == "review_required")
        check("syntax reason names the construct",
              any("unmodelled construct(s): control_flow_block" in r for r in looped.handoff_readiness.reasons))
        check("syntax gap listed", any(g.check == "syntax" for g in looped.pre_execution.coverage_gaps))

        clean = engine_mod.validate_code("x = rndu(10, 1);\nm = meanc(x);", docs_root=root)
        check("a candidate has no gaps", clean.handoff_readiness.state == "handoff_candidate"
              and clean.pre_execution.coverage_gaps == ())


def test_136_v083_sprintf_variadic_arguments_are_typed() -> None:
    """Live finding 72.15. `sprintf.rst` spells its variadic `:param ....:`,
    so its type never attached; real tgauss.exe -b runs every shape below."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(_typed_v082_docs_root(tmp))
        (root / "sprintf.rst").write_text(_SPRINTF_RST, encoding="utf-8")
        candidates = (
            's = sprintf("%d and %d", 3, 4);\nprint s;',
            's = sprintf("%d %d", {1, 2}, {3, 4});',
            's = sprintf("%d", {1 2 3});',
            's = sprintf("%d", {1 2, 3 4});',
            's = sprintf("%s", "hello");',
            'x = rndu(3, 1);\ns = sprintf("%f", x);',
        )
        for code in candidates:
            result = engine_mod.validate_code(code, docs_root=str(root))
            check(f"candidate: {code!r}", result.handoff_readiness.state == "handoff_candidate")
        expression = engine_mod.validate_code('s = sprintf("%s=%d", "a" $| "b", {1, 2});', docs_root=str(root))
        check("an expression argument stays review_required", expression.handoff_readiness.state == "review_required")
        check("...and says why", any(g.cause == "argument_expression" and g.parameter == "..."
                                     for g in expression.pre_execution.coverage_gaps))


def _page(title: str, purpose: str, function: str, returns: str) -> str:
    return (f"{title}\n{'=' * len(title)}\n\nPurpose\n-------\n\n{purpose}\n\nFormat\n------\n"
            f".. function:: {function}\n\n    :param x: data\n    :type x: NxK matrix\n\n    {returns}\n")


_SEARCH_PAGES = {
    "vcmvcx.rst": _page("vcm, vcx", "Computes an estimate of a variance-covariance matrix.", "vc = vcx(x)",
                        ":return vc: KxK variance-covariance matrix."),
    "varcovmvarcovx.rst": _page("varCovM, varCovX", "Computes the population variance-covariance matrix.",
                                "vc = varCovX(x)", ":return vc: KxK variance-covariance matrix."),
    "rndmvn.rst": _page("rndMVn", "Computes multivariate normal random numbers given a covariance matrix.",
                        "y = rndMVn(r, mu, x)", ":return y: random draws."),
    "tsmt/nwmt.rst": _page("nwmt", "Finds the Newey-West covariance matrix.", "vc = nwmt(x)",
                           ":return vc: Newey-West covariance matrix."),
    "user-guide/estimation-guide.rst": (
        "Estimation guide\n================\n\nPurpose\n-------\n\nHow covariance estimates are used in estimation.\n"
    ),
    "chol.rst": _page("chol", "Computes the Cholesky decomposition of a symmetric, positive definite matrix.",
                      "y = chol(x)", ":return y: upper triangular factor."),
    "bandchol.rst": _page("bandchol", "Computes the Cholesky decomposition of a positive definite banded matrix.",
                          "y = bandchol(x)", ":return y: banded factor."),
    "meanc.rst": _page("meanc", "Computes the mean of every column of a matrix.", "y = meanc(x)",
                       ":return y: column means."),
}


def _search_docs_root(tmp: str) -> str:
    root = Path(tmp) / "docs"
    for name, text in _SEARCH_PAGES.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8")
    return str(root)


def test_137_v083_search_candidates_are_labeled_and_ranked() -> None:
    """Live finding 72.16: a plain question returned nothing."""
    with tempfile.TemporaryDirectory() as tmp:
        root = _search_docs_root(tmp)

        bundle = engine_mod.ground_multi("covariance", docs_root_str=root)
        found = engine_mod.search_candidates("covariance", bundle, docs_root_str=root)
        check("mode B: still ungrounded", bundle.status.value == "ungrounded" and bundle.sources == ())
        check("mode B ranking: produces the concept, core before package; then input-only; then guides",
              [c.citation for c in found.candidates] == [
                  "varcovmvarcovx.rst", "vcmvcx.rst", "tsmt/nwmt.rst", "rndmvn.rst", "user-guide/estimation-guide.rst",
              ])
        check("every entry labeled a candidate", all(c.status == "candidate" for c in found.candidates))
        check("keyword origin", all(c.origin == "keyword_match" and c.keywords == ("covariance",) for c in found.candidates))
        check("purpose sentence, not page content",
              found.candidates[1].purpose == "Computes an estimate of a variance-covariance matrix.")
        check("not truncated", (found.matched_pages, found.truncated) == (5, False))

        saved = engine_mod.MAX_SEARCH_CANDIDATES
        engine_mod.MAX_SEARCH_CANDIDATES = 2
        try:
            capped = engine_mod.search_candidates("covariance", bundle, docs_root_str=root)
        finally:
            engine_mod.MAX_SEARCH_CANDIDATES = saved
        check("cap respected and disclosed", len(capped.candidates) == 2 and capped.truncated)

        ambiguous = engine_mod.ground_multi("cholesky decomposition", docs_root_str=root)
        found = engine_mod.search_candidates("cholesky decomposition", ambiguous, docs_root_str=root)
        check("mode A: the ambiguous resolution's pages",
              sorted(c.citation for c in found.candidates) == ["bandchol.rst", "chol.rst"])
        check("mode A origin", all(c.origin == "ambiguous_resolution" for c in found.candidates))

        grounded = engine_mod.ground_multi("meanc", docs_root_str=root)
        check("no candidates once grounded", engine_mod.search_candidates("meanc", grounded, docs_root_str=root).candidates == ())
        nothing = engine_mod.ground_multi("zzz", docs_root_str=root)
        check("no candidates for no keyword", engine_mod.search_candidates("zzz", nothing, docs_root_str=root).candidates == ())
        check("no docs root, no candidates",
              engine_mod.search_candidates("covariance", bundle, docs_root_str=None).candidates == ())
        check("verification rejects a page the symbol's lookup does not return",
              not engine_mod._candidate_verified(Path(root), "chol", "vcmvcx.rst"))


#: Computed with HEAD's (v0.82.0) `ground_multi`/`compute_generation_gate`
#: on `_SEARCH_PAGES` BEFORE the v0.83.0 changes, and identical after them:
#: (status, policy, matched, unmatched, ambiguous).
_PINNED_GATE = {
    "covariance": ("ungrounded", "block", (), ("covariance",), ()),
    "covariance estimates": ("ungrounded", "clarify", (), ("covariance", "estimates"), ("covariance estimates",)),
    "how is covariance computed": ("grounded", "full", ("estimation-guide",), (), ()),
    "cholesky decomposition": ("ungrounded", "clarify", (), ("cholesky", "decomposition"), ("cholesky decomposition",)),
    "meanc": ("grounded", "full", ("meanc",), (), ()),
    "column means": ("grounded", "full", ("meanc",), (), ()),
    "write code for the column means": ("grounded", "full", ("meanc",), (), ()),
    "zzz": ("ungrounded", "block", (), ("zzz",), ()),
    "what does G0025 mean": ("grounded", "full", ("G0025",), (), ()),
    "positive definite banded matrix": ("grounded", "full", ("bandchol",), (), ()),
}


def test_138_v083_search_candidates_never_reach_the_generation_gate() -> None:
    """The ask() generation gate is safety-relevant: candidates must not
    change it. Three guards: structural, pinned behavior, provider-raises."""
    import inspect

    check("ask() never calls search_candidates",
          "search_candidates" not in inspect.getsource(engine_mod.ConversationEngine.ask))
    for fn in (engine_mod.ground_multi, engine_mod.resolve_concepts, engine_mod.compute_generation_gate):
        source = inspect.getsource(fn)
        check(f"{fn.__name__} never reads search candidates",
              "search_candidates" not in source and "SearchCandidate" not in source)
    check("GroundingBundle carries no candidates field",
          not any("candidate" in f for f in engine_mod.GroundingBundle.__dataclass_fields__))

    with tempfile.TemporaryDirectory() as tmp:
        root = _search_docs_root(tmp)
        for question, pinned in _PINNED_GATE.items():
            bundle = engine_mod.ground_multi(question, docs_root_str=root)
            gate = engine_mod.compute_generation_gate(bundle)
            actual = (bundle.status.value, gate.policy, bundle.matched_topics, bundle.unmatched_topics,
                      bundle.ambiguous_topics)
            check(f"gate unchanged: {question!r}", actual == pinned)

        class ExplodingProvider:
            def complete(self, messages, *, max_tokens=1024):
                raise AssertionError("the provider must never be called when generation is blocked")

        engine = engine_mod.ConversationEngine(provider=ExplodingProvider(), docs_root=root)
        result = engine.ask("Write GAUSS code to compute the covariance of my data.")
        check("a candidate-only question is still blocked", result.generation_policy in ("block", "clarify"))
        check("no code generated", result.generated_code == ())


# ---------------------------------------------------------------------------
# v0.84.0: one lexer and statement stream -- every 73.10/73.14 probe and the
# planning doc's §2.2 rows, through validate_code on synthetic typed pages
# ---------------------------------------------------------------------------

_TYPED_V084_RST = dict(_TYPED_V082_RST, **{
    "det.rst": "det\n===\n\n.. function:: y = det(x)\n\n    :param x: square matrix\n    :type x: NxN matrix\n\n"
               "    :return y: the determinant\n    :rtype y: scalar\n",
    "eigh.rst": "eigh\n====\n\n.. function:: va = eigh(x)\n\n    :param x: symmetric matrix\n"
                "    :type x: NxN matrix\n\n    :return va: eigenvalues\n    :rtype va: Nx1 vector\n",
    "sprintf.rst": _SPRINTF_RST,
})


def _typed_v084_docs_root(tmp: str) -> str:
    root = Path(tmp) / "docs"
    root.mkdir()
    for name, text in _TYPED_V084_RST.items():
        (root / name).write_text(text, encoding="utf-8")
    return str(root)


def _state(code: str, root: str) -> str:
    return engine_mod.validate_code(code, docs_root=root).handoff_readiness.state


def test_139_v084_string_labels_never_define_names() -> None:
    """Live finding 73.14 (run-014): `_ASSIGNMENT_TARGET_RE` read `det =`
    inside a `print` label as an assignment."""
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v084_docs_root(tmp)
        det = engine_mod.validate_code('x = { 3 2 1, 0 1 -2, 1 3 4 };\nd = det(x);\nprint "det = " d;', docs_root=root)
        check("det label: handoff_candidate (was a false not_ready)", det.handoff_readiness.state == "handoff_candidate")
        check("det is called, not user-defined", det.called_symbols == ("det",) and "det" not in det.user_defined_symbols)

        fake = engine_mod.validate_code(
            'x = { 3 2 1, 0 1 -2, 1 3 4 };\nd = det(x);\nf = fakeinverse(x);\nprint "fakeinverse = " f;',
            docs_root=root,
        )
        check("fakeinverse label: not_ready (was review_required)", fake.handoff_readiness.state == "not_ready")
        check("fakeinverse is unknown", fake.pre_execution.unknown_symbols == ("fakeinverse",))
        check("and named as a gap", ("signature", "fakeinverse", "call_undocumented") in [
            (g.check, g.symbol, g.cause) for g in fake.pre_execution.coverage_gaps])

        sole = engine_mod.validate_code('f = fakeinverse(x); print "fakeinverse = " f;', docs_root=root)
        check("sole fakeinverse: not_ready naming it", sole.handoff_readiness.state == "not_ready"
              and any("fakeinverse" in r for r in sole.handoff_readiness.reasons))

        violated = engine_mod.validate_code('x = {1 2, 2 1}; y = invpd(x); print "invpd = " y;', docs_root=root)
        check("invpd label: the violation is the first reason",
              violated.handoff_readiness.state == "not_ready" and violated.handoff_readiness.reasons[0].startswith("invpd:"))

        system = engine_mod.validate_code('dos dir;\nprint "dos = " d;', docs_root=root)
        check("dos label: not_ready, dos not user-defined",
              system.handoff_readiness.state == "not_ready" and "dos" not in system.user_defined_symbols)

        for code in (
            'x = {1 2, 3 4};\nprint "proc fakefn(x)";\ny = fakefn(x);\nm = meanc(x);',
            "x = {4 1, 1 3};\nm = meanc(x);\ns.fakefn = 1;\ny = fakefn(x);",
            "proc (1) = f(x);\n  local a; a = fakefn(x);\n  retp(a);\nendp;\nm = meanc({1 2, 3 4});",
            "@ fakefn = 1; @\nx = {1 2, 3 4};\nm = meanc(x);\ny = fakefn(x);",
        ):
            result = engine_mod.validate_code(code, docs_root=root)
            check(f"hidden hallucination found: {code[:24]!r}", result.handoff_readiness.state == "not_ready"
                  and "fakefn" in result.pre_execution.unknown_symbols)


def test_140_v084_multi_line_statements_are_traced() -> None:
    """Live finding 73.10 (run-010): `_masked_statements` split per line, so a
    multi-line literal was never traced. Every two-line form must reach its
    one-line twin's verdict."""
    pairs = (
        ("x = { 2 1 0,\n      1 2 1,\n      0 1 2 };\nva = eigh(x);", "handoff_candidate"),
        ("x = {1 2,\n3 4}; m = meanc(x);", "handoff_candidate"),
        ("x = {1 2,\n2 1}; y = invpd(x);", "not_ready"),
        ("x = {2 1,\n1 2};\ny = invpd(x);", "handoff_candidate"),
        ("x = {1 2,\n2 4};\ny = inv(x);", "not_ready"),
        ("x = {1 2, 3 4};\nm = meanc(\n  x);", "handoff_candidate"),
        ("x = {2 1, 1 2};\ny = invpd(\n  x);", "handoff_candidate"),
        ("v = zeros(5,\n          1);\nfor i(1, 5, 1);\n    v[i] = i^2;\nendfor;\nprint v;", "handoff_candidate"),
        ('s = sprintf("%d", {1 2,\n3 4});', "handoff_candidate"),
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v084_docs_root(tmp)
        for code, expected in pairs:
            one_line = code.replace(",\n", ", ").replace("(\n  ", "(").replace("\n          ", " ")
            check(f"{expected}: {code[:22]!r}", _state(code, root) == expected)
            check(f"same as its one-line twin: {code[:22]!r}", _state(one_line, root) == expected)
        result = engine_mod.validate_code("x = {1 2,\n2 1}; y = invpd(x);", docs_root=root)
        check("the violation is the reason", result.handoff_readiness.reasons[0].startswith("invpd:"))


def test_141_v084_strings_and_comments_never_hide_code() -> None:
    """Planning v0.84 §2.2: string-embedded `/*`...`*/` and `\\"` escapes hid
    `dos dir;` and a hallucinated call, and both reached handoff_candidate."""
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v084_docs_root(tmp)
        unsafe = (
            'print "/*"; dos dir; print "*/";\nm = meanc({1 2, 3 4});',
            'print "a\\"b"; dos dir; print "c\\"d";\nm = meanc({1 2, 3 4});',
        )
        for code in unsafe:
            result = engine_mod.validate_code(code, docs_root=root)
            check(f"dos found: {code[:20]!r}", result.handoff_readiness.state == "not_ready"
                  and [f.name for f in result.pre_execution.system_statements] == ["dos"])
            hidden = engine_mod.validate_code(code.replace("dos dir;", "y = fakefn(1);"), docs_root=root)
            check(f"fakefn found: {code[:20]!r}", hidden.handoff_readiness.state == "not_ready"
                  and "fakefn" in hidden.pre_execution.unknown_symbols)
        candidates = (
            'x = {1 2, 3 4};\nm = meanc(x);\nprint "see https://docs.aptech.com";',
            's = { "a;b" };\nm = meanc({1 2, 3 4});',
            's = sprintf("a\\",%d", 3);',
            'print "say \\"hi\\"";\nm = meanc({1 2, 3 4});',
            "/* dos dir; */\nm = meanc({1 2, 3 4});",
        )
        for code in candidates:
            check(f"handoff_candidate: {code[:24]!r}", _state(code, root) == "handoff_candidate")
        for code in ("@ note @ m = meanc({1 2, 3 4});", "/* a /* b */ dos dir; */\nm = meanc({1 2, 3 4});",
                     'm = meanc({1 2, 3 4});\nprint "a\nb";'):
            check(f"undocumented lexical form: review_required: {code[:20]!r}", _state(code, root) == "review_required")
        for code in ("x = {1 2, 3 4};\nb = {1, 1};\ny = x @ b;\nm = meanc(y);",
                     "m = meanc({1 2, 3 4});\n/* never closed\ndos dir;"):
            check(f"unterminated comment: not_ready: {code[:20]!r}", _state(code, root) == "not_ready")
        shifted = engine_mod.validate_code("/* one\ntwo\nthree */\nm = meanc({1 2, 3 4});\ndos dir;", docs_root=root)
        check("line numbers survive a multi-line comment", shifted.pre_execution.system_statements[0].line_number == 5)


def test_142_v084_ask_path_shares_the_fix() -> None:
    """The `ask()` path's `check_generated_symbols(...)` had the same 73.14
    defect: a label made `fakeinverse` "user-defined or ambiguous"."""
    labelled = 'x = { 3 2 1, 0 1 -2, 1 3 4 };\nd = det(x);\nf = fakeinverse(x);\nprint "fakeinverse = " f;'
    check_result = engine_mod.check_generated_symbols(labelled, supported_symbols=("det",))
    check("unknown behind a label", check_result.unknown_call_symbols == ("fakeinverse",))
    with tempfile.TemporaryDirectory() as tmp:
        root = _typed_v084_docs_root(tmp)
        outcomes = []
        for code in (labelled, labelled.replace('print "fakeinverse = " f;', "print f;")):
            engine = engine_mod.ConversationEngine(
                provider=provider_mod.FakeModelProvider(canned_answer=f"```gauss\n{code}\n```"), docs_root=root,
            )
            result = engine.ask("Write GAUSS code that uses det on a 3x3 matrix.")
            outcomes.append((result.unknown_symbols, result.pre_execution_eligibility))
        check("ask(): the label changes nothing", outcomes[0] == outcomes[1])
        check("ask(): fakeinverse unknown", "fakeinverse" in outcomes[0][0])


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
