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
import gauss_execution_handoff as handoff_mod  # noqa: E402
import gauss_pre_execution_validation as validation_mod  # noqa: E402


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


_INV_RST = """inv, invpd
==========

.. function:: xi = inv(x)
              xi = invpd(x)

Purpose
-------
inv returns the inverse of an invertible matrix. invpd returns the inverse of a symmetric, positive definite matrix.
"""


def _fixture_docs_root(tmp: str) -> Path:
    root = Path(tmp) / "docs"
    root.mkdir()
    (root / "reshape.rst").write_text(_RESHAPE_RST, encoding="utf-8")
    (root / "meanc.rst").write_text(_MEANC_RST, encoding="utf-8")
    (root / "invinvpd.rst").write_text(_INV_RST, encoding="utf-8")
    return root


#: v0.78.0: `_INV_RST` above deliberately has no `Input`/`:type:` section
#: (existing tests 33/34 only need eligibility wording, not a resolved
#: parameter-role check), so it always leaves `parameter_role_check`
#: UNKNOWN and never reaches HANDOFF_CANDIDATE. The controlled-execution-
#: handoff tests need a real, reproducible HANDOFF_CANDIDATE turn, so this
#: is a separate, disposable fixture with a typed `x` parameter -- the
#: exact same shape `test_gauss_conversation_engine.py`'s own `_INV_RST` /
#: `test_105_correctly_formatted_matrix_literal_equivalent_is_syntax_
#: validated` already uses to reach real broad-evidence handoff candidacy.
_TYPED_INV_RST = """inv, invpd
==========

.. function:: xi = inv(x)
              xi = invpd(x)

Purpose
-------
inv returns the inverse of an invertible matrix. invpd returns the inverse of a symmetric, positive definite matrix.

Input
-----
    :param x: data
    :type x: NxN matrix
"""


def _fixture_docs_root_handoff_candidate(tmp: str) -> Path:
    root = Path(tmp) / "docs"
    root.mkdir()
    (root / "invinvpd.rst").write_text(_TYPED_INV_RST, encoding="utf-8")
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


def test_28_ungrounded_code_generation_request_is_blocked_not_fabricated() -> None:
    """v0.73.0: an ungrounded GAUSS-specific code-generation request is now
    deterministically BLOCKed before the model is ever consulted, rather
    than reaching the model and getting an honest-but-still-model-generated
    answer as in v0.72.0 -- see gauss_conversation_engine.GenerationPolicy.BLOCK."""
    messages: list[str] = []
    chat_mod.run_chat(
        prompt_fn=_scripted(["Write GAUSS code to estimate an OLS regression.", "exit"]),
        print_fn=messages.append, engine=_fake_engine(),
    )
    joined = "\n".join(messages)
    check(
        "generation is honestly blocked, not fabricated by the model",
        "I don't have enough authoritative GAUSS documentation" in joined,
    )


def test_29_help_text_mentions_code_generation_and_its_limits() -> None:
    messages: list[str] = []
    chat_mod.run_chat(prompt_fn=_scripted(["help", "exit"]), print_fn=messages.append, engine=_fake_engine())
    joined = "\n".join(messages)
    check("help mentions asking for GAUSS code", "GAUSS code" in joined)
    # v0.78.0: superseded the old blanket "does not execute" wording -- this
    # chat now DOES support one narrow, explicit, per-request controlled
    # execution path (gauss_execution_handoff.py) for HANDOFF_CANDIDATE
    # code, so help text must describe that boundary precisely rather than
    # claim a no-execution guarantee that is no longer literally true.
    check(
        "help states code never executes on its own initiative",
        "does not execute code on its own initiative" in joined,
    )
    check(
        "help states the controlled-execution approval boundary",
        "explicit, per-request controlled-execution approval" in joined,
    )


# ---------------------------------------------------------------------------
# v0.73.0: grounding-gated generation rendering
# ---------------------------------------------------------------------------


def test_30_column_means_resolves_to_meanc_through_the_full_chat_loop() -> None:
    """The exact v0.72.0 regression, exercised through the full CLI loop."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        messages: list[str] = []
        chat_mod.run_chat(
            prompt_fn=_scripted(["Calculate the column means.", "exit"]), print_fn=messages.append,
            engine=_fake_engine(docs_root=str(docs_root)),
        )
        joined = "\n".join(messages)
        check("resolves to the real meanc function, not colmean", "meanc" in joined)
        check("colmean never appears", "colmean" not in joined)


def test_31_unknown_generated_symbol_is_disclosed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ncol_means = colmean(y);\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        messages: list[str] = []
        chat_mod.run_chat(
            prompt_fn=_scripted(["Calculate the column means.", "exit"]), print_fn=messages.append, engine=engine,
        )
        joined = "\n".join(messages)
        check("the unknown symbol is disclosed as a warning", "colmean" in joined and "Warning" in joined)


def test_32_panel_regression_without_support_is_blocked_through_the_full_chat_loop() -> None:
    messages: list[str] = []
    chat_mod.run_chat(
        prompt_fn=_scripted(["Write GAUSS code for a panel regression.", "exit"]),
        print_fn=messages.append, engine=_fake_engine(),  # no docs_root -> no authoritative support
    )
    joined = "\n".join(messages)
    check("generation is blocked, not fabricated", "I don't have enough authoritative GAUSS documentation" in joined)


def test_33_invpd_valid_spd_literal_shows_eligible_for_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = invpd({2 1, 1 2});\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        messages: list[str] = []
        chat_mod.run_chat(prompt_fn=_scripted(["Invert this matrix.", "exit"]), print_fn=messages.append, engine=engine)
        joined = "\n".join(messages)
        check("eligibility line shown", "eligible_for_validation" in joined)
        check("precondition satisfaction shown", "satisfied" in joined)
        check("never claims real execution occurred", "executed successfully" not in joined.lower())


def test_34_invpd_non_symmetric_literal_shows_ineligible_and_the_reason() -> None:
    """The exact v0.73.0 Finding 3 regression, rendered through the full
    chat loop: a documented function used with a real, existing symbol
    must still be marked ineligible when its own documented precondition
    is violated by a literal input."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = invpd({2 1, 3 2});\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        messages: list[str] = []
        chat_mod.run_chat(prompt_fn=_scripted(["Invert this matrix.", "exit"]), print_fn=messages.append, engine=engine)
        joined = "\n".join(messages)
        check("eligibility is ineligible", "ineligible" in joined)
        check("the violated precondition is named", "symmetric" in joined)


def test_35_module_still_never_imports_execution_repair_or_filesystem_modules() -> None:
    forbidden_modules = (
        "gauss_execution_workflow", "gauss_repair_application", "gauss_repair_draft",
        "gauss_repair_planner", "gauss_repair_approval", "gauss_verification_execution",
        "gauss_verification_review", "gauss_code_execution", "gauss_workspace", "subprocess",
    )
    for line in Path(chat_mod.__file__).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            for token in forbidden_modules:
                check(f"import line {stripped!r} does not reference {token!r}", token not in stripped)


def test_36_qa_intent_code_answer_is_rendered_with_validation_evidence() -> None:
    """v0.75.0: through the full chat loop, a `QA`-classified question
    ("What does invpd do?" -- matches no code-generation trigger phrase and
    no concept-alias phrase) whose answer happens to include real GAUSS
    code must now show the SAME validation section a `CODE_GENERATION`
    request already shows -- closing the QA-intent eligibility gap
    end-to-end, not merely inside `ConversationEngine.ask(...)`."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(
            canned_answer="invpd inverts a symmetric positive definite matrix, for example:\n\n```gauss\ny = invpd({2 1, 1 2});\n```",
        )
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        messages: list[str] = []
        chat_mod.run_chat(prompt_fn=_scripted(["What does invpd do?", "exit"]), print_fn=messages.append, engine=engine)
        joined = "\n".join(messages)
        check("validation section rendered for a QA-route answer", "Validation:" in joined)
        check("eligibility shown", "eligible_for_validation" in joined)


def test_37_predicted_output_mismatch_is_rendered_through_the_full_chat_loop() -> None:
    """Reconstructs the exact v0.74.0 wrong-model-prediction finding
    (evaluations/runs/2026-09-12-code-assistant-pre-execution-validation-
    run-004.md) end to end: the code itself is eligible, but the model's
    own claimed numeric inverse is wrong and must be disclosed as a
    MISMATCH, never silently accepted."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(
            canned_answer="```gauss\nxi = invpd({2 1, 1 2});\n```\nExpected output:\n0.5 -0.5\n-0.5 0.5",
        )
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        messages: list[str] = []
        chat_mod.run_chat(prompt_fn=_scripted(["Invert this matrix.", "exit"]), print_fn=messages.append, engine=engine)
        joined = "\n".join(messages)
        check("predicted output mismatch disclosed", "Predicted output: mismatch" in joined)
        check("code itself still eligible independent of the wrong prediction", "eligible_for_validation" in joined)


# ---------------------------------------------------------------------------
# v0.76.0: syntax validation / execution-handoff readiness rendering
# ---------------------------------------------------------------------------


def test_38_semicolon_matrix_literal_shows_invalid_syntax_and_not_ready_through_the_full_chat_loop() -> None:
    """The exact v0.75.0 live regression (evaluation 65.8b), rendered
    through the full chat loop this time: the user must actually SEE that
    the generated code has an invalid matrix literal and is not a handoff
    candidate, not just get a silent UNVERIFIED precondition."""
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = invpd({2 1; 1 2});\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        messages: list[str] = []
        chat_mod.run_chat(prompt_fn=_scripted(["Invert this matrix.", "exit"]), print_fn=messages.append, engine=engine)
        joined = "\n".join(messages)
        check("syntax invalid shown", "Syntax: invalid" in joined)
        check("row separator problem named", "row separator" in joined)
        check("readiness not ready", "Execution handoff readiness: not_ready" in joined)
        check("never claims real execution occurred", "executed successfully" not in joined.lower())


def test_39_fully_supported_example_shows_handoff_candidate_through_the_full_chat_loop() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs_root = _fixture_docs_root(tmp)
        provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = invpd({2 1, 1 2});\n```")
        engine = engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))
        messages: list[str] = []
        chat_mod.run_chat(
            prompt_fn=_scripted(["Use invpd to invert this matrix.", "exit"]), print_fn=messages.append, engine=engine,
        )
        joined = "\n".join(messages)
        check("syntax validated shown", "Syntax: validated" in joined)
        check("still discloses this was never executed", "This code has not been executed." in joined)


# ---------------------------------------------------------------------------
# v0.78.0: Controlled Execution Handoff -- conversational wiring
# ---------------------------------------------------------------------------


def _counting_id_fn():
    counter = {"n": 0}

    def _fn() -> str:
        counter["n"] += 1
        return f"id-{counter['n']}"

    return _fn


def _fixed_clock_fn() -> str:
    return "2026-09-19T00:00:00Z"


def _handoff_engine(tmp: str) -> "engine_mod.ConversationEngine":
    """The exact fixture shape `test_gauss_conversation_engine.py`'s own
    `test_105_correctly_formatted_matrix_literal_equivalent_is_syntax_
    validated` uses to reach real, broad-evidence `HANDOFF_CANDIDATE` --
    a literal (not runtime-variable) SPD argument plus a typed `x`
    parameter, so every coverage dimension is COMPLETE."""
    docs_root = _fixture_docs_root_handoff_candidate(tmp)
    provider = provider_mod.FakeModelProvider(canned_answer="```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```")
    return engine_mod.ConversationEngine(provider=provider, docs_root=str(docs_root))


def _minimal_answer_result(**overrides) -> "engine_mod.AnswerResult":
    defaults = dict(
        text="some answer", grounded=True, grounding_source="official_docs", grounding_topic="invpd",
        provider_name="fake", provider_model=None, provider_success=True, provider_error=None,
    )
    defaults.update(overrides)
    return engine_mod.AnswerResult(**defaults)


def test_40_execution_offer_appears_only_for_handoff_candidate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = _handoff_engine(tmp)
        messages: list[str] = []
        chat_mod.run_chat(
            prompt_fn=_scripted(["Use invpd to invert this matrix.", "exit"]), print_fn=messages.append,
            engine=engine, config=config_mod.GaussAiConfig(), env={},
        )
        joined = "\n".join(messages)
        check("execution offer is printed for a HANDOFF_CANDIDATE answer", "HANDOFF_CANDIDATE readiness" in joined)
        check("offer mentions the trigger phrase", "run this" in joined)


def test_41_no_offer_for_non_candidate_answer() -> None:
    messages: list[str] = []
    chat_mod.run_chat(
        prompt_fn=_scripted(["What does reshape do?", "exit"]), print_fn=messages.append,
        engine=_fake_engine(), config=config_mod.GaussAiConfig(), env={},
    )
    joined = "\n".join(messages)
    check("no execution offer for a plain QA answer", "HANDOFF_CANDIDATE readiness" not in joined)


def test_42_eligibility_gate_rejects_not_ready_and_review_required_and_multi_block() -> None:
    not_ready = _minimal_answer_result(
        generated_code=("print 1+1;",),
        handoff_readiness=validation_mod.ReadinessResult(state=validation_mod.HandoffReadiness.NOT_READY.value, reasons=()),
    )
    review_required = _minimal_answer_result(
        generated_code=("print 1+1;",),
        handoff_readiness=validation_mod.ReadinessResult(state=validation_mod.HandoffReadiness.REVIEW_REQUIRED.value, reasons=()),
    )
    candidate = _minimal_answer_result(
        generated_code=("print 1+1;",),
        handoff_readiness=validation_mod.ReadinessResult(state=validation_mod.HandoffReadiness.HANDOFF_CANDIDATE.value, reasons=()),
    )
    multi_block_candidate = _minimal_answer_result(
        generated_code=("print 1+1;", "print 2+2;"),
        handoff_readiness=validation_mod.ReadinessResult(state=validation_mod.HandoffReadiness.HANDOFF_CANDIDATE.value, reasons=()),
    )
    no_code = _minimal_answer_result(generated_code=(), handoff_readiness=None)

    check("NOT_READY never offers execution", not chat_mod._execution_offer_eligible(not_ready))
    check("REVIEW_REQUIRED never offers execution", not chat_mod._execution_offer_eligible(review_required))
    check("HANDOFF_CANDIDATE with exactly one code block offers execution", chat_mod._execution_offer_eligible(candidate))
    check("HANDOFF_CANDIDATE with multiple code blocks does NOT offer execution (v0.78.0 scope)", not chat_mod._execution_offer_eligible(multi_block_candidate))
    check("no generated code never offers execution", not chat_mod._execution_offer_eligible(no_code))


def test_43_run_this_with_no_pending_candidate_gives_a_clear_message() -> None:
    messages: list[str] = []
    chat_mod.run_chat(
        prompt_fn=_scripted(["run this", "exit"]), print_fn=messages.append,
        engine=_fake_engine(), config=config_mod.GaussAiConfig(), env={},
    )
    joined = "\n".join(messages)
    check("clear no-pending-candidate message shown", "no HANDOFF_CANDIDATE code available" in joined)


def test_44_approve_and_execute_fake_success_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = _handoff_engine(tmp)
        messages: list[str] = []
        chat_mod.run_chat(
            prompt_fn=_scripted(["Use invpd to invert this matrix.", "run this", "yes", "exit"]),
            print_fn=messages.append, engine=engine, config=config_mod.GaussAiConfig(), env={},
            id_fn=_counting_id_fn(), clock_fn=_fixed_clock_fn,
        )
        joined = "\n".join(messages)
        check("exact code shown before approval", "y = invpd({2 1, 1 2});\nprint y;" in joined)
        check("approval question shown", "Approve this exact execution" in joined)
        check("execution completed rendered", "Execution completed." in joined)
        check(
            "methodological caveat shown after success",
            "does not establish methodological correctness" in joined,
        )


def test_45_decline_blocks_execution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = _handoff_engine(tmp)
        messages: list[str] = []
        chat_mod.run_chat(
            prompt_fn=_scripted(["Use invpd to invert this matrix.", "run this", "no", "exit"]),
            print_fn=messages.append, engine=engine, config=config_mod.GaussAiConfig(), env={},
        )
        joined = "\n".join(messages)
        check("decline statement shown", "This request was declined" in joined)
        check("no execution occurred", "Execution completed." not in joined)


def test_46_unrecognized_response_reprompts_then_cancels_safely() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = _handoff_engine(tmp)
        messages: list[str] = []
        chat_mod.run_chat(
            prompt_fn=_scripted(["Use invpd to invert this matrix.", "run this", "sure", "looks good", "exit"]),
            print_fn=messages.append, engine=engine, config=config_mod.GaussAiConfig(), env={},
        )
        joined = "\n".join(messages)
        check("re-prompt shown for an unrecognized response", "Please answer exactly 'yes' or 'no'." in joined)
        check("cancels safely after a second unrecognized response", "cancelling. No code was executed." in joined)
        check("no execution occurred", "Execution completed." not in joined)


def test_47_second_run_this_is_a_brand_new_request_not_a_replay() -> None:
    # Approving once, executing, then asking to "run this" AGAIN re-enters
    # the flow from scratch -- a brand new request/approval, never a replay
    # of the consumed one. No consent is inherited: the second "run this"
    # must show the prompt and ask for approval again, and must execute
    # again (a fresh, explicit consent for identical code is not a replay).
    with tempfile.TemporaryDirectory() as tmp:
        engine = _handoff_engine(tmp)
        messages: list[str] = []
        chat_mod.run_chat(
            prompt_fn=_scripted([
                "Use invpd to invert this matrix.", "run this", "yes", "run this", "yes", "exit",
            ]),
            print_fn=messages.append, engine=engine, config=config_mod.GaussAiConfig(), env={},
            id_fn=_counting_id_fn(), clock_fn=_fixed_clock_fn,
        )
        joined_count = "\n".join(messages).count("Execution completed.")
        approval_count = "\n".join(messages).count("Approve this exact execution")
        check("execution completed twice (two fresh approvals, not a replay)", joined_count == 2)
        check("approval was explicitly asked for twice", approval_count == 2)


def test_48_chat_module_never_imports_subprocess_or_the_real_helper_directly() -> None:
    forbidden = ("subprocess", "gauss_code_execution")
    for line in Path(chat_mod.__file__).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            for token in forbidden:
                check(f"import line {stripped!r} does not reference {token!r}", token not in stripped)


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
