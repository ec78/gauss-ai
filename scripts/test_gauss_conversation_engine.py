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
