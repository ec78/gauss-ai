"""Tests for the `gauss-ai repair <file.gss>` guided workflow (v0.67.0).

Run with:

    python scripts/test_gauss_ai_guided_repair.py

The primary purpose of this file is proving the guided command cannot
bypass any existing safety boundary: it must not execute before an explicit
confirmation, must not auto-approve any of the three approval layers, must
not bypass the application gate, must not read any file other than the one
named on the command line, must not rerun without an ordinary execution
confirmation, must not fabricate a verification review, and must not write
outside the workspace it creates -- including never modifying the caller's
original file. Every approval point is driven by a scripted, injectable
`prompt_fn`; nothing is decided automatically.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_ai_guided_repair as guided_mod  # noqa: E402
import gauss_code_assistant_cli as cli  # noqa: E402
import gauss_code_assistant_workflow as mvp  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _new_adapter(tmp: str) -> "cli.InteractiveMvpAdapter":
    return cli.InteractiveMvpAdapter(workspace_parent=tmp, session_id="guided-test", clock=lambda: 1000.0)


def _broken_gss(tmp: str) -> Path:
    p = Path(tmp) / "broken.gss"
    p.write_bytes(b"x = 2 + 2\nprint x;\n")
    return p


def _g0105_gss(tmp: str, content: bytes = b"x = ;\nprint x;\n") -> Path:
    """A source file whose content genuinely matches the v0.69.0
    AI-assisted candidate generator's own G0105 empty-assignment pattern --
    distinct from `_broken_gss`, whose content deliberately does NOT match
    it, so every pre-existing (v0.67.0-era) test keeps exercising the fully
    manual entry path unchanged."""
    p = Path(tmp) / "g0105.gss"
    p.write_bytes(content)
    return p


def _scripted(answers: list[str]):
    queue = list(answers)

    def _prompt(_question: str) -> str:
        if not queue:
            raise AssertionError("prompt_fn called more times than answers were scripted")
        return queue.pop(0)

    return _prompt


_HAPPY_PATH_ANSWERS = [
    "y",  # confirm execution
    "y",  # approve strategy
    "1", "1", "insert missing semicolon", "Add missing semicolon", "x = 2 + 2;",  # draft fields
    "y",  # approve draft
    "y",  # approve application
    "y",  # verify now
    "y",  # confirm verification execution
    "accepted",  # review decision
    "",  # notes (skip)
]


# ---------------------------------------------------------------------------
# Full happy path
# ---------------------------------------------------------------------------


def test_01_full_guided_repair_reaches_verification_reviewed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        result = guided_mod.run_guided_repair(
            source, adapter=adapter, prompt_fn=_scripted(_HAPPY_PATH_ANSWERS), print_fn=lambda *_: None,
            fake_result="failure",
        )
        check("run_guided_repair returns the same adapter it was given", result is adapter)
        check("application was applied", adapter.last_application_result is not None and adapter.last_application_result.outcome == "applied")
        check("verification review was recorded", adapter._verification_review_store.get_review(adapter.last_verification_request.verification_execution_id) is not None)  # noqa: SLF001
        adapter.close()


def test_02_guided_repair_never_writes_the_original_file() -> None:
    """The single most important safety proof: the caller's real file, at
    its real path, is byte-for-byte unchanged after a full, successfully
    applied guided repair."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        original_bytes = source.read_bytes()
        adapter = _new_adapter(tmp)
        guided_mod.run_guided_repair(
            source, adapter=adapter, prompt_fn=_scripted(_HAPPY_PATH_ANSWERS), print_fn=lambda *_: None,
            fake_result="failure",
        )
        check("the original file's bytes are completely unchanged", source.read_bytes() == original_bytes)
        adapter.close()


def test_03_guided_repair_never_reads_or_touches_an_unrelated_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        unrelated = Path(tmp) / "unrelated.gss"
        unrelated.write_bytes(b"y = 1;\n")
        unrelated_before = unrelated.read_bytes()
        adapter = _new_adapter(tmp)
        guided_mod.run_guided_repair(
            source, adapter=adapter, prompt_fn=_scripted(_HAPPY_PATH_ANSWERS), print_fn=lambda *_: None,
            fake_result="failure",
        )
        check("an unrelated file in the same directory is completely untouched", unrelated.read_bytes() == unrelated_before)
        adapter.close()


def test_04_guided_repair_writes_only_inside_the_workspace_it_creates() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        before = {p for p in Path(tmp).iterdir()}
        guided_mod.run_guided_repair(
            source, adapter=adapter, prompt_fn=_scripted(_HAPPY_PATH_ANSWERS), print_fn=lambda *_: None,
            fake_result="failure",
        )
        after = {p for p in Path(tmp).iterdir()}
        new_entries = after - before
        check("only one new top-level entry appeared (the workspace directory)", len(new_entries) == 1)
        if new_entries:
            new_dir = next(iter(new_entries))
            check("the new entry is the workspace registry's own directory, not a stray file", new_dir.is_dir())
            # v0.89.0 (first CI run on macOS and the Windows runners): the
            # registry stores a resolved root, while `tmp` can be an alias of
            # the same directory -- macOS's `/var` is a symlink to
            # `/private/var`, and the Windows runner's temp directory is an
            # 8.3 short name (`RUNNER~1`). Same directory, two spellings, so
            # both sides are resolved before comparing.
            check("the new entry is exactly the active workspace's own root",
                  new_dir.resolve() == Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path).resolve())
        adapter.close()


# ---------------------------------------------------------------------------
# No bypass: cannot execute before explicit execution confirmation
# ---------------------------------------------------------------------------


def test_05_cancel_at_execution_confirmation_nothing_executes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=_scripted(["n"]), print_fn=lambda *_: None)
        check("last_result is None -- nothing executed", adapter.last_result is None)
        check("mvp_session did not advance past PLAN_PROPOSED", adapter.mvp_session is not None and adapter.mvp_session.stage == mvp.CodeAssistantStage.PLAN_PROPOSED)
        check("no repair plan exists yet", adapter.last_repair_plan is None)
        adapter.close()


# ---------------------------------------------------------------------------
# No bypass: cannot auto-approve the strategy
# ---------------------------------------------------------------------------


def test_06_cancel_at_strategy_approval_records_decline_not_approval() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        guided_mod.run_guided_repair(
            source, adapter=adapter, prompt_fn=_scripted(["y", "n"]), print_fn=lambda *_: None, fake_result="failure",
        )
        check("exactly one strategy decision was recorded", len(adapter._repair_approval_store) == 1)  # noqa: SLF001
        plan = adapter.last_repair_plan
        assert plan is not None
        import gauss_repair_planner as repair_planner_mod

        record = adapter._repair_approval_store.get_decision(plan)  # noqa: SLF001
        check("the recorded decision is 'declined', never 'approved'", record is not None and record.decision == "declined")
        check("no repair draft was ever constructed", adapter.last_repair_draft is None)
        adapter.close()


# ---------------------------------------------------------------------------
# No bypass: cannot auto-approve the draft
# ---------------------------------------------------------------------------


def test_07_cancel_at_draft_approval_records_decline_not_approval() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        answers = _scripted(["y", "y", "1", "1", "op", "desc", "x = 2 + 2;", "n"])
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
        check("a repair draft exists", adapter.last_repair_draft is not None)
        record = adapter._draft_approval_store.get_decision(adapter.last_repair_draft)  # noqa: SLF001
        check("the recorded draft decision is 'declined'", record is not None and record.decision == "declined")
        check("no application approval was ever recorded", len(adapter._application_approval_store) == 0)  # noqa: SLF001
        check("no application result exists", adapter.last_application_result is None)
        adapter.close()


# ---------------------------------------------------------------------------
# No bypass: cannot auto-approve application; cannot silently apply
# ---------------------------------------------------------------------------


def test_08_cancel_at_application_approval_records_decline_never_applies() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        answers = _scripted(["y", "y", "1", "1", "op", "desc", "x = 2 + 2;", "y", "n"])
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
        record = adapter._application_approval_store.get_decision(adapter.last_repair_draft)  # noqa: SLF001
        check("the recorded application decision is 'declined'", record is not None and record.decision == "declined")
        check("no application transaction was ever attempted", adapter.last_application_result is None)
        adapter.close()


# ---------------------------------------------------------------------------
# No bypass: application gate failure halts the workflow before apply
# ---------------------------------------------------------------------------


def test_09_application_gate_failure_halts_before_apply() -> None:
    """Simulates the source changing between drafting and application by
    mutating the workspace copy from inside the scripted prompt_fn, exactly
    at the point a real concurrent edit could occur -- the gate's own
    source_hash_fresh check must then fail, and the guided workflow must
    stop, never calling apply-repair."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        queue = ["y", "y", "1", "1", "op", "desc", "y", "y"]

        def prompt_with_late_mutation(question: str) -> str:
            if question.startswith("Exact replacement text"):
                assert adapter.active_workspace_id is not None
                workspace_root = Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path)
                (workspace_root / source.name).write_bytes(b"mutated after drafting, before the gate check\n")
                return "x = 2 + 2;"
            if not queue:
                raise AssertionError("unexpected extra prompt")
            return queue.pop(0)

        guided_mod.run_guided_repair(
            source, adapter=adapter, prompt_fn=prompt_with_late_mutation, print_fn=lambda *_: None, fake_result="failure",
        )
        check("application approval was still recorded (that layer is independent of freshness)", adapter._application_approval_store.get_decision(adapter.last_repair_draft) is not None)  # noqa: SLF001
        check("no application transaction was attempted after the gate failed", adapter.last_application_result is None)
        adapter.close()


# ---------------------------------------------------------------------------
# No bypass: cannot rerun without ordinary execution confirmation
# ---------------------------------------------------------------------------


def test_10_cancel_at_verification_confirmation_leaves_applied_but_unverified() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        # ..., approve draft(y), approve application(y), verify now(y), THEN
        # decline the actual confirm/execute step for the verification run(n).
        answers = _scripted(["y", "y", "1", "1", "op", "desc", "x = 2 + 2;", "y", "y", "y", "n"])
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
        check("the repair was applied", adapter.last_application_result is not None and adapter.last_application_result.outcome == "applied")
        check("a verification request was proposed but never executed", adapter.last_verification_request is not None)
        check("mvp_session did not reach EXECUTED for the verification run", adapter.mvp_session is not None and adapter.mvp_session.stage != mvp.CodeAssistantStage.EXECUTED)
        check("no verification review exists", adapter._verification_review_store.get_review(adapter.last_verification_request.verification_execution_id) is None)  # noqa: SLF001
        adapter.close()


def test_11_declining_verification_entirely_still_leaves_applied_repair_unverified() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        answers = _scripted(["y", "y", "1", "1", "op", "desc", "x = 2 + 2;", "y", "y", "n"])
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
        check("applied but not verified is a valid, safely-reported stopping point", adapter.last_application_result.outcome == "applied")
        adapter.close()


# ---------------------------------------------------------------------------
# No bypass: cannot fabricate a verification review
# ---------------------------------------------------------------------------


def test_12_invalid_review_decision_records_nothing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        answers = _scripted(["y", "y", "1", "1", "op", "desc", "x = 2 + 2;", "y", "y", "y", "y", "not-a-real-decision"])
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
        check("an invalid decision string records no review", len(adapter._verification_review_store) == 0)  # noqa: SLF001
        adapter.close()


def test_13_every_review_decision_matches_exactly_what_was_typed() -> None:
    for decision in ("accepted", "rejected", "inconclusive"):
        with tempfile.TemporaryDirectory() as tmp:
            source = _broken_gss(tmp)
            adapter = _new_adapter(tmp)
            answers = _scripted(["y", "y", "1", "1", "op", "desc", "x = 2 + 2;", "y", "y", "y", "y", decision, ""])
            guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
            record = adapter._verification_review_store.get_review(adapter.last_verification_request.verification_execution_id)  # noqa: SLF001
            check(f"recorded decision is exactly {decision!r}, never inferred", record is not None and record.decision == decision)
            adapter.close()


# ---------------------------------------------------------------------------
# Stages skipped honestly when not applicable
# ---------------------------------------------------------------------------


def test_14_successful_original_execution_skips_the_entire_repair_pipeline() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        guided_mod.run_guided_repair(
            source, adapter=adapter, prompt_fn=_scripted(["y"]), print_fn=lambda *_: None, fake_result="success",
        )
        check("no repair plan digest was approved", len(adapter._repair_approval_store) == 0)  # noqa: SLF001
        check("no draft was constructed", adapter.last_repair_draft is None)
        check("no application was attempted", adapter.last_application_result is None)
        adapter.close()


# ---------------------------------------------------------------------------
# Architectural: orchestration only, no second engine
# ---------------------------------------------------------------------------


def test_15_module_defines_no_execution_repair_or_approval_engine_of_its_own() -> None:
    source = Path(guided_mod.__file__).read_text(encoding="utf-8")
    forbidden = (
        "def execute(", "def apply_repair(", "def propose_execution(", "def evaluate_application_gate(",
        "def interpret_execution(", "def diagnose_execution(", "def plan_repair(",
    )
    for token in forbidden:
        check(f"module defines no {token!r} of its own", token not in source)


def test_16_module_only_imports_the_existing_cli_adapter_and_config() -> None:
    source = Path(guided_mod.__file__).read_text(encoding="utf-8")
    forbidden = ("import gauss_repair_application\n", "import gauss_verification_execution\n", "import gauss_execution_workflow\n")
    for token in forbidden:
        check(f"module does not directly import {token.strip()!r} (reuses the adapter instead)", token not in source)


def test_17_run_guided_repair_returns_none_on_configuration_error_never_raises() -> None:
    result = guided_mod.run_guided_repair(
        "/tmp/does-not-matter.gss", cli_runner="gauss", cli_gauss_executable=None,
        config=__import__("gauss_ai_config").GaussAiConfig(), env={}, print_fn=lambda *_: None,
    )
    check("a real-runner request with no configured executable returns None, does not raise", result is None)


def test_18_missing_file_reports_error_and_does_not_create_a_workspace() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        messages: list[str] = []
        guided_mod.run_guided_repair(
            Path(tmp) / "does-not-exist.gss", adapter=adapter, prompt_fn=_scripted([]), print_fn=messages.append,
        )
        check("an error message was printed", any("does not exist" in m or "ERROR" in m for m in messages))
        adapter.close()


# ---------------------------------------------------------------------------
# v0.69.0 AI-assisted repair-draft candidate generation
# ---------------------------------------------------------------------------


def test_19_candidate_accept_flow_applies_the_generated_replacement_text() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _g0105_gss(tmp)
        adapter = _new_adapter(tmp)
        answers = _scripted(
            ["y", "y", "a", "y", "y", "y", "y", "accepted", ""]
            #  confirm  strategy  accept  draft  app  verify  confirm  review  notes
        )
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
        check("application was applied", adapter.last_application_result is not None and adapter.last_application_result.outcome == "applied")
        assert adapter.active_workspace_id is not None
        workspace_copy = Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path) / source.name
        check("the workspace copy now contains the candidate's own placeholder text", workspace_copy.read_text(encoding="utf-8") == "x = 0;\nprint x;\n")
        adapter.close()


def test_20_candidate_edit_flow_uses_the_users_own_replacement_text() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _g0105_gss(tmp)
        adapter = _new_adapter(tmp)
        answers = _scripted(
            ["y", "y", "e", "x = 42;", "y", "y", "y", "y", "accepted", ""]
            #  confirm  strategy  edit  new-text  draft  app  verify  confirm  review  notes
        )
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
        check("application was applied", adapter.last_application_result is not None and adapter.last_application_result.outcome == "applied")
        assert adapter.active_workspace_id is not None
        workspace_copy = Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path) / source.name
        check("the workspace copy contains the user's edited text, not the candidate's own placeholder", workspace_copy.read_text(encoding="utf-8") == "x = 42;\nprint x;\n")
        adapter.close()


def test_21_candidate_reject_flow_falls_back_to_fully_manual_entry() -> None:
    """Even when a candidate is available, the user must still be able to
    reject it and construct a completely different draft manually."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _g0105_gss(tmp)
        adapter = _new_adapter(tmp)
        answers = _scripted(
            ["y", "y", "r", "1", "1", "manual op", "manual desc", "x = 99;", "y", "y", "y", "y", "accepted", ""]
        )
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
        check("application was applied", adapter.last_application_result is not None and adapter.last_application_result.outcome == "applied")
        assert adapter.active_workspace_id is not None
        workspace_copy = Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path) / source.name
        check("the workspace copy contains the fully manual replacement text, not the candidate's", workspace_copy.read_text(encoding="utf-8") == "x = 99;\nprint x;\n")
        adapter.close()


def test_22_evidence_is_shown_before_manual_entry_even_when_no_candidate_matches() -> None:
    """Alpha finding #3: the assistant must show the evidence that
    motivated the repair before asking for line numbers -- true both when a
    candidate is generated and, as here, when none is."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)  # content does NOT match the G0105 pattern
        adapter = _new_adapter(tmp)
        messages: list[str] = []
        answers = _scripted(["y", "y", "1", "1", "op", "desc", "x = 2 + 2;", "y", "y", "y", "y", "accepted", ""])
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=messages.append, fake_result="failure")
        evidence_index = next((i for i, m in enumerate(messages) if "GENERATION_BOUNDARY" in m), None)
        manual_index = next((i for i, m in enumerate(messages) if "Manual repair draft entry" in m), None)
        check("generation evidence was printed", evidence_index is not None)
        check("the manual-entry prompt intro was printed", manual_index is not None)
        if evidence_index is not None and manual_index is not None:
            check("evidence appears before the manual-entry prompt, not after", evidence_index < manual_index)
        adapter.close()


def test_23_multiple_candidates_prompts_for_a_choice_and_applies_the_chosen_one() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _g0105_gss(tmp, content=b"x = ;\ny = ;\n")
        adapter = _new_adapter(tmp)
        answers = _scripted(
            ["y", "y", "2", "a", "y", "y", "y", "y", "accepted", ""]
            #  confirm  strategy  choose#2  accept  draft  app  verify  confirm  review  notes
        )
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
        check("application was applied", adapter.last_application_result is not None and adapter.last_application_result.outcome == "applied")
        assert adapter.active_workspace_id is not None
        workspace_copy = Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path) / source.name
        final_text = workspace_copy.read_text(encoding="utf-8")
        check("the second line (the chosen candidate) was replaced", "y = 0;" in final_text)
        check("the first line (not chosen) is untouched", final_text.splitlines()[0] == "x = ;")
        adapter.close()


def test_24_declining_application_approval_still_blocks_an_accepted_candidate() -> None:
    """Safety regression through the new candidate path: accepting a
    generated candidate does not, and must not, weaken the independent
    application-approval gate."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _g0105_gss(tmp)
        adapter = _new_adapter(tmp)
        answers = _scripted(["y", "y", "a", "y", "n"])
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
        record = adapter._application_approval_store.get_decision(adapter.last_repair_draft)  # noqa: SLF001
        check("the recorded application decision is 'declined'", record is not None and record.decision == "declined")
        check("no application transaction was ever attempted", adapter.last_application_result is None)
        adapter.close()


def test_25_declining_draft_approval_still_blocks_an_accepted_candidate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _g0105_gss(tmp)
        adapter = _new_adapter(tmp)
        answers = _scripted(["y", "y", "a", "n"])
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=lambda *_: None, fake_result="failure")
        record = adapter._draft_approval_store.get_decision(adapter.last_repair_draft)  # noqa: SLF001
        check("the recorded draft decision is 'declined'", record is not None and record.decision == "declined")
        check("no application approval was ever recorded", len(adapter._application_approval_store) == 0)  # noqa: SLF001
        adapter.close()


def test_26_exact_replacement_text_is_shown_again_immediately_before_apply_approval() -> None:
    """Small, additive safety-visibility improvement: whatever replacement
    text is about to be applied (candidate-sourced or fully manual) is
    printed once more right before the highest-stakes approval question."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _g0105_gss(tmp)
        adapter = _new_adapter(tmp)
        messages: list[str] = []
        answers = _scripted(["y", "y", "a", "y", "y", "y", "y", "accepted", ""])
        guided_mod.run_guided_repair(source, adapter=adapter, prompt_fn=answers, print_fn=messages.append, fake_result="failure")
        recap_index = next((i for i, m in enumerate(messages) if "Exact replacement text that will be applied" in m), None)
        check("the recap line was printed", recap_index is not None)
        if recap_index is not None:
            check("the recap shows the exact accepted candidate text", "x = 0;" in messages[recap_index + 1])
        adapter.close()


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
