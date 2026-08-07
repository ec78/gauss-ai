"""Tests for the Repair Session Summary module.

Run with:

    python scripts/test_gauss_repair_session_summary.py

No test launches GAUSS, executes anything, mutates any approval store, edits
source code, reads or writes a file, or accesses the network. The summary
module consumes only already-constructed objects, built here via each
object's own real, existing construction path (never hand-faked shapes).
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_code_assistant_workflow as mvp  # noqa: E402
import gauss_execution_diagnostics as diag_mod  # noqa: E402
import gauss_execution_interpreter as interp_mod  # noqa: E402
import gauss_repair_application as application_mod  # noqa: E402
import gauss_repair_application_approval as application_approval_mod  # noqa: E402
import gauss_repair_approval as repair_approval_mod  # noqa: E402
import gauss_repair_draft as repair_draft_mod  # noqa: E402
import gauss_repair_draft_approval as draft_approval_mod  # noqa: E402
import gauss_repair_planner as repair_planner_mod  # noqa: E402
import gauss_repair_session_summary as summary_mod  # noqa: E402
import gauss_verification_execution as verification_mod  # noqa: E402
import gauss_verification_review as review_mod  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


# ---------------------------------------------------------------------------
# Fixture builders -- each object built via its own real construction path
# ---------------------------------------------------------------------------


def _evidence(**overrides: object) -> "interp_mod.ExecutionEvidence":
    values = {
        "runner": "FAKE", "gauss_ran": False, "executed": True, "execution_status": "failed",
        "exit_code": 0, "stdout_chars": 0, "stderr_chars": 0, "timed_out": False,
        "workspace_state": "failed", "provenance": None,
        "stdout_text": "Program execute failed\n", "stderr_text": "error G0105 : Undefined symbol\n",
        "metadata_error": None,
    }
    values.update(overrides)
    return interp_mod.ExecutionEvidence(**values)


def _workflow_result(**overrides: object) -> "mvp.WorkflowResult":
    values = {
        "request_summary": "Run x = 2 + 2;", "workspace_id": "ws-1", "execution_status": "failed",
        "execution_session_reference": None, "files_produced": (), "files_read": (),
        "provenance": None, "analysis_status": "completed", "user_facing_summary": "Execution failed.",
    }
    values.update(overrides)
    return mvp.WorkflowResult(**values)


def _interpretation(**overrides: object) -> "interp_mod.ExecutionInterpretation":
    return interp_mod.interpret_execution(_evidence(**overrides))


def _diagnosis(**overrides: object) -> "diag_mod.DiagnosticAssessment":
    return diag_mod.diagnose_execution(_evidence(**overrides))


def _plan(**overrides: object) -> "repair_planner_mod.RepairPlan":
    return repair_planner_mod.plan_repair(_evidence(**overrides))


def _artifact(**overrides: object) -> "repair_draft_mod.SourceArtifact":
    values = {"workspace_id": "ws-1", "relative_path": "model.gss", "file_type": ".gss"}
    values.update(overrides)
    return repair_draft_mod.SourceArtifact(**values)


def _identity(**overrides: object) -> "repair_draft_mod.SourceIdentity":
    values = {"artifact": _artifact(), "content_hash": "a" * 64, "size": 128, "encoding": "utf-8"}
    values.update(overrides)
    return repair_draft_mod.SourceIdentity(**values)


def _scope(**overrides: object) -> "repair_draft_mod.EditScope":
    values = {"line_start": 3, "line_end": 3, "intended_operation": "insert missing statement terminator"}
    values.update(overrides)
    return repair_draft_mod.EditScope(**values)


def _draft(plan: "repair_planner_mod.RepairPlan", **overrides: object) -> "repair_draft_mod.RepairDraft":
    values = {
        "repair_draft_id": "draft-1",
        "repair_plan_digest": repair_planner_mod.repair_plan_digest(plan),
        "source_identity": _identity(),
        "edit_scope": _scope(),
        "proposed_change_description": "Insert a missing statement terminator at the reported line.",
        "generated_at": "1000.0",
    }
    values.update(overrides)
    return repair_draft_mod.build_repair_draft(**values)


def _application_result(**overrides: object) -> "application_mod.ApplicationResult":
    values = {
        "application_id": "app-1", "draft_digest": "d" * 64, "workspace_id": "ws-1",
        "relative_path": "model.gss", "pre_application_content_hash": "a" * 64,
        "post_application_content_hash": "b" * 64, "backup": None, "outcome": "applied",
        "reason": None, "checks": (), "applied_at": "1002.0",
        "application_boundary": application_mod.APPLIED_BOUNDARY_STATEMENT,
    }
    values.update(overrides)
    return application_mod.ApplicationResult(**values)


def _verification_request(**overrides: object) -> "verification_mod.VerificationExecutionRequest":
    values = {
        "verification_execution_id": "ve-1", "repair_application_id": "app-1",
        "application_result_id": "app-1", "workspace_id": "ws-1", "relative_path": "model.gss",
        "expected_post_repair_hash": "b" * 64, "reason": "Verify the repair.", "created_at": "1003.0",
    }
    values.update(overrides)
    return verification_mod.VerificationExecutionRequest(**values)


def _comparison(**overrides: object) -> "verification_mod.ComparisonSummary":
    values = {
        "original_outcome": "Runtime error G0105", "verification_outcome": "Execution successful",
        "same_outcome": False, "comparison": verification_mod.ComparisonOutcome.SUCCEEDED_AFTER_FAILURE.value,
        "observation": "The repaired code executed successfully whereas the original execution failed with G0105.",
    }
    values.update(overrides)
    return verification_mod.ComparisonSummary(**values)


def _review(**overrides: object) -> "review_mod.VerificationReview":
    values = {
        "review_id": "rev-1", "verification_execution_id": "ve-1",
        "comparison_summary_digest": review_mod.comparison_summary_digest(_comparison()),
        "decision": "accepted", "notes": "", "reviewed_at": "1004.0", "reviewed_by": "tester",
        "boundary": review_mod.VERIFICATION_REVIEW_BOUNDARY,
    }
    values.update(overrides)
    return review_mod.VerificationReview(**values)


# ---------------------------------------------------------------------------
# Summary reflects existing objects (identity, not equality)
# ---------------------------------------------------------------------------


def test_01_full_session_holds_the_exact_same_objects() -> None:
    execution = _workflow_result()
    interpretation = _interpretation()
    diagnosis = _diagnosis()
    plan = _plan()
    strategy_store = repair_approval_mod.RepairApprovalStore()
    strategy_approval = strategy_store.approve(plan, recorded_at="1000.0")
    draft = _draft(plan)
    draft_store = draft_approval_mod.DraftApprovalStore()
    draft_approval = draft_store.approve(draft, recorded_at="1001.0")
    application_approval_store = application_approval_mod.ApplicationApprovalStore()
    application_approval = application_approval_store.approve(draft, recorded_at="1002.0")
    application_result = _application_result()
    verification_request = _verification_request()
    comparison = _comparison()
    review = _review()

    summary = summary_mod.build_repair_session_summary(
        original_execution=execution, interpretation=interpretation, diagnosis=diagnosis,
        repair_plan=plan, strategy_approval=strategy_approval, repair_draft=draft,
        draft_approval=draft_approval, application_approval=application_approval,
        application_result=application_result, verification_request=verification_request,
        comparison_summary=comparison, verification_review=review, generated_at="2000.0",
    )

    check("original_execution is the same object", summary.original_execution is execution)
    check("interpretation is the same object", summary.interpretation is interpretation)
    check("diagnosis is the same object", summary.diagnosis is diagnosis)
    check("repair_plan is the same object", summary.repair_plan is plan)
    check("strategy_approval is the same object", summary.strategy_approval is strategy_approval)
    check("repair_draft is the same object", summary.repair_draft is draft)
    check("draft_approval is the same object", summary.draft_approval is draft_approval)
    check("application_approval is the same object", summary.application_approval is application_approval)
    check("application_result is the same object", summary.application_result is application_result)
    check("verification_request is the same object", summary.verification_request is verification_request)
    check("comparison_summary is the same object", summary.comparison_summary is comparison)
    check("verification_review is the same object", summary.verification_review is review)
    check("generated_at carried through", summary.generated_at == "2000.0")


def test_02_empty_session_all_domain_fields_none() -> None:
    summary = summary_mod.build_repair_session_summary(generated_at="t0")
    for field in (
        "original_execution", "interpretation", "diagnosis", "repair_plan", "strategy_approval",
        "repair_draft", "draft_approval", "application_approval", "application_result",
        "verification_request", "comparison_summary", "verification_review",
    ):
        check(f"{field} is None in an empty session", getattr(summary, field) is None)
    check("timeline is empty", summary.timeline == ())
    check("current_status is no_execution", summary.current_status == "no_execution")


# ---------------------------------------------------------------------------
# current_status -- one test per furthest-stage-reached case
# ---------------------------------------------------------------------------


def test_03_status_executed_only() -> None:
    summary = summary_mod.build_repair_session_summary(original_execution=_workflow_result(), generated_at="t0")
    check("status is executed", summary.current_status == "executed")


def test_04_status_interpreted_only() -> None:
    summary = summary_mod.build_repair_session_summary(interpretation=_interpretation(), generated_at="t0")
    check("status is interpreted", summary.current_status == "interpreted")


def test_05_status_diagnosed_only() -> None:
    summary = summary_mod.build_repair_session_summary(diagnosis=_diagnosis(), generated_at="t0")
    check("status is diagnosed", summary.current_status == "diagnosed")


def test_06_status_planned_only() -> None:
    summary = summary_mod.build_repair_session_summary(repair_plan=_plan(), generated_at="t0")
    check("status is planned", summary.current_status == "planned")


def test_07_status_strategy_approved_and_declined() -> None:
    plan = _plan()
    store = repair_approval_mod.RepairApprovalStore()
    approved = summary_mod.build_repair_session_summary(
        strategy_approval=store.approve(plan, recorded_at="t0"), generated_at="t1"
    )
    check("status is strategy_approved", approved.current_status == "strategy_approved")
    store2 = repair_approval_mod.RepairApprovalStore()
    declined = summary_mod.build_repair_session_summary(
        strategy_approval=store2.decline(plan, recorded_at="t0"), generated_at="t1"
    )
    check("status is strategy_declined", declined.current_status == "strategy_declined")


def test_08_status_draft_created_only() -> None:
    plan = _plan()
    summary = summary_mod.build_repair_session_summary(repair_draft=_draft(plan), generated_at="t0")
    check("status is draft_created", summary.current_status == "draft_created")


def test_09_status_draft_approved_and_declined() -> None:
    plan = _plan()
    draft = _draft(plan)
    store = draft_approval_mod.DraftApprovalStore()
    approved = summary_mod.build_repair_session_summary(
        draft_approval=store.approve(draft, recorded_at="t0"), generated_at="t1"
    )
    check("status is draft_approved", approved.current_status == "draft_approved")
    store2 = draft_approval_mod.DraftApprovalStore()
    declined = summary_mod.build_repair_session_summary(
        draft_approval=store2.decline(draft, recorded_at="t0"), generated_at="t1"
    )
    check("status is draft_declined", declined.current_status == "draft_declined")


def test_10_status_application_approved_and_declined() -> None:
    plan = _plan()
    draft = _draft(plan)
    store = application_approval_mod.ApplicationApprovalStore()
    approved = summary_mod.build_repair_session_summary(
        application_approval=store.approve(draft, recorded_at="t0"), generated_at="t1"
    )
    check("status is application_approved", approved.current_status == "application_approved")
    store2 = application_approval_mod.ApplicationApprovalStore()
    declined = summary_mod.build_repair_session_summary(
        application_approval=store2.decline(draft, recorded_at="t0"), generated_at="t1"
    )
    check("status is application_declined", declined.current_status == "application_declined")


def test_11_status_applied_blocked_failed() -> None:
    applied = summary_mod.build_repair_session_summary(application_result=_application_result(outcome="applied"), generated_at="t0")
    check("status is application_applied", applied.current_status == "application_applied")
    blocked = summary_mod.build_repair_session_summary(application_result=_application_result(outcome="blocked"), generated_at="t0")
    check("status is application_blocked", blocked.current_status == "application_blocked")
    failed = summary_mod.build_repair_session_summary(application_result=_application_result(outcome="failed"), generated_at="t0")
    check("status is application_failed", failed.current_status == "application_failed")


def test_12_status_verification_requested() -> None:
    summary = summary_mod.build_repair_session_summary(verification_request=_verification_request(), generated_at="t0")
    check("status is verification_requested", summary.current_status == "verification_requested")


def test_13_status_verification_completed() -> None:
    summary = summary_mod.build_repair_session_summary(comparison_summary=_comparison(), generated_at="t0")
    check("status is verification_completed", summary.current_status == "verification_completed")


def test_14_status_verification_reviewed_each_decision() -> None:
    for decision in ("accepted", "rejected", "inconclusive"):
        summary = summary_mod.build_repair_session_summary(verification_review=_review(decision=decision), generated_at="t0")
        check(f"status is verification_reviewed:{decision}", summary.current_status == f"verification_reviewed:{decision}")


def test_15_status_reflects_furthest_stage_even_with_all_earlier_stages_present() -> None:
    """A comprehensive session with every stage populated must still report
    the furthest stage, never an earlier one, regardless of how many earlier
    stages were also supplied."""
    plan = _plan()
    draft = _draft(plan)
    summary = summary_mod.build_repair_session_summary(
        original_execution=_workflow_result(), interpretation=_interpretation(), diagnosis=_diagnosis(),
        repair_plan=plan, strategy_approval=repair_approval_mod.RepairApprovalStore().approve(plan, recorded_at="t0"),
        repair_draft=draft, draft_approval=draft_approval_mod.DraftApprovalStore().approve(draft, recorded_at="t0"),
        application_approval=application_approval_mod.ApplicationApprovalStore().approve(draft, recorded_at="t0"),
        application_result=_application_result(), verification_request=_verification_request(),
        comparison_summary=_comparison(), verification_review=_review(decision="rejected"),
        generated_at="t1",
    )
    check("status reflects the furthest stage (review), not an earlier one", summary.current_status == "verification_reviewed:rejected")


# ---------------------------------------------------------------------------
# Missing stages handled honestly
# ---------------------------------------------------------------------------


def test_16_missing_stage_no_field_inferred_from_a_later_one() -> None:
    """Passing only application_result (no plan, no draft, no approvals)
    must NOT synthesize any of the missing intermediate objects."""
    summary = summary_mod.build_repair_session_summary(application_result=_application_result(), generated_at="t0")
    check("repair_plan still None", summary.repair_plan is None)
    check("repair_draft still None", summary.repair_draft is None)
    check("strategy_approval still None", summary.strategy_approval is None)
    check("draft_approval still None", summary.draft_approval is None)
    check("application_approval still None", summary.application_approval is None)
    check("status is application_applied", summary.current_status == "application_applied")


def test_17_partial_session_strategy_approved_no_draft() -> None:
    plan = _plan()
    strategy_approval = repair_approval_mod.RepairApprovalStore().approve(plan, recorded_at="t0")
    summary = summary_mod.build_repair_session_summary(repair_plan=plan, strategy_approval=strategy_approval, generated_at="t1")
    check("repair_draft is honestly None", summary.repair_draft is None)
    check("status is strategy_approved", summary.current_status == "strategy_approved")
    check("timeline has exactly one entry", len(summary.timeline) == 1)


# ---------------------------------------------------------------------------
# Timeline: ordering, contents, correctness
# ---------------------------------------------------------------------------


def test_18_timeline_empty_when_no_timestamped_stage_present() -> None:
    """interpretation/diagnosis/repair_plan carry no timestamp anywhere in
    this architecture -- a session with only those populated has an empty
    timeline, not a fabricated one."""
    summary = summary_mod.build_repair_session_summary(
        original_execution=_workflow_result(), interpretation=_interpretation(), diagnosis=_diagnosis(),
        repair_plan=_plan(), generated_at="t0",
    )
    check("timeline is empty despite four populated fields", summary.timeline == ())


def test_19_timeline_fixed_pipeline_order_regardless_of_kwarg_order() -> None:
    plan = _plan()
    draft = _draft(plan)
    review = _review()
    verification_request = _verification_request()
    application_result = _application_result()
    application_approval = application_approval_mod.ApplicationApprovalStore().approve(draft, recorded_at="t0")
    draft_approval = draft_approval_mod.DraftApprovalStore().approve(draft, recorded_at="t0")
    strategy_approval = repair_approval_mod.RepairApprovalStore().approve(plan, recorded_at="t0")

    # Passed in REVERSE pipeline order as keyword arguments -- Python
    # dataclasses/kwargs have no inherent ordering, so this proves the
    # timeline's own order comes from the module's fixed logic, not from
    # call-site argument order.
    summary = summary_mod.build_repair_session_summary(
        verification_review=review, verification_request=verification_request,
        application_result=application_result, application_approval=application_approval,
        draft_approval=draft_approval, repair_draft=draft, strategy_approval=strategy_approval,
        generated_at="t9",
    )
    stages = [entry.stage for entry in summary.timeline]
    check(
        "timeline stages are in fixed pipeline order regardless of kwarg order",
        stages == [
            "strategy_approval", "repair_draft", "draft_approval", "application_approval",
            "application_result", "verification_request", "verification_review",
        ],
    )


def test_20_timeline_only_includes_present_timestamped_stages() -> None:
    plan = _plan()
    draft = _draft(plan)
    summary = summary_mod.build_repair_session_summary(
        repair_draft=draft, verification_review=_review(), generated_at="t0",
    )
    stages = [entry.stage for entry in summary.timeline]
    check("timeline has exactly two entries", len(stages) == 2)
    check("timeline entries are repair_draft then verification_review", stages == ["repair_draft", "verification_review"])


def test_21_timeline_entry_timestamps_and_descriptions_correct() -> None:
    plan = _plan()
    strategy_approval = repair_approval_mod.RepairApprovalStore().decline(plan, recorded_at="t-strategy")
    summary = summary_mod.build_repair_session_summary(strategy_approval=strategy_approval, generated_at="t9")
    entry = summary.timeline[0]
    check("timestamp matches the record's own recorded_at", entry.timestamp == "t-strategy")
    check("description reflects the actual decision", entry.description == "Strategy declined")


def test_22_timeline_covers_all_seven_timestamped_stages_in_a_full_session() -> None:
    plan = _plan()
    draft = _draft(plan)
    summary = summary_mod.build_repair_session_summary(
        strategy_approval=repair_approval_mod.RepairApprovalStore().approve(plan, recorded_at="t1"),
        repair_draft=draft,
        draft_approval=draft_approval_mod.DraftApprovalStore().approve(draft, recorded_at="t2"),
        application_approval=application_approval_mod.ApplicationApprovalStore().approve(draft, recorded_at="t3"),
        application_result=_application_result(applied_at="t4"),
        verification_request=_verification_request(created_at="t5"),
        verification_review=_review(reviewed_at="t6"),
        generated_at="t9",
    )
    check("timeline has exactly seven entries", len(summary.timeline) == 7)
    check("timestamps appear in the order supplied by each record", [e.timestamp for e in summary.timeline] == ["t1", "1000.0", "t2", "t3", "t4", "t5", "t6"])


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_23_summary_is_frozen() -> None:
    summary = summary_mod.build_repair_session_summary(generated_at="t0")
    raised = False
    try:
        summary.current_status = "tampered"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        raised = True
    check("mutating current_status raises FrozenInstanceError", raised)


def test_24_timeline_entry_is_frozen() -> None:
    plan = _plan()
    strategy_approval = repair_approval_mod.RepairApprovalStore().approve(plan, recorded_at="t0")
    summary = summary_mod.build_repair_session_summary(strategy_approval=strategy_approval, generated_at="t1")
    entry = summary.timeline[0]
    raised = False
    try:
        entry.stage = "tampered"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        raised = True
    check("mutating a TimelineEntry raises FrozenInstanceError", raised)


def test_25_timeline_itself_is_an_immutable_tuple() -> None:
    summary = summary_mod.build_repair_session_summary(generated_at="t0")
    check("timeline is a tuple, not a list", isinstance(summary.timeline, tuple))


# ---------------------------------------------------------------------------
# Boundary
# ---------------------------------------------------------------------------


def test_26_boundary_fixed_and_present() -> None:
    a = summary_mod.build_repair_session_summary(generated_at="t0")
    b = summary_mod.build_repair_session_summary(original_execution=_workflow_result(), generated_at="t1")
    check("boundary identical regardless of session state", a.boundary == b.boundary)
    check("boundary discloses read-only framing", "read-only summary" in a.boundary)
    check("boundary discloses no new approval/execution/plan/repair/mutation", "creates no new approval, executes nothing, plans nothing, repairs nothing, and mutates no prior state" in a.boundary)


# ---------------------------------------------------------------------------
# Architectural / structural proofs
# ---------------------------------------------------------------------------


def test_27_module_performs_no_io() -> None:
    source = Path(summary_mod.__file__).read_text(encoding="utf-8")
    forbidden = ("open(", "os.path", "Path(", "os.replace", "subprocess", "socket")
    for token in forbidden:
        check(f"module source does not contain {token!r}", token not in source)


def test_28_module_defines_no_mutation_execution_or_approval_callables() -> None:
    source = Path(summary_mod.__file__).read_text(encoding="utf-8")
    forbidden = (
        "def execute(", "def apply_repair(", "def propose_", "def confirm(", "def approve(",
        "def decline(", "def revoke(", "def rollback(", "def retry(",
    )
    for token in forbidden:
        check(f"module defines no {token!r}", token not in source)


def test_29_generated_at_is_never_computed_internally() -> None:
    source = Path(summary_mod.__file__).read_text(encoding="utf-8")
    check("module never calls time.time() or similar", "time.time()" not in source and "import time" not in source)
    check("generated_at is a required, caller-supplied parameter (no default)", "generated_at: str,\n) -> RepairSessionSummary" in source)


def test_30_no_module_other_than_the_cli_imports_this_module() -> None:
    scripts_dir = Path(summary_mod.__file__).resolve().parent
    importers = []
    for f in sorted(scripts_dir.glob("*.py")):
        if f.name.startswith("test_") or f.name == "gauss_repair_session_summary.py":
            continue
        text = f.read_text(encoding="utf-8")
        if "import gauss_repair_session_summary" in text:
            importers.append(f.name)
    check("only the CLI imports this module (or nothing yet does)", importers in ([], ["gauss_code_assistant_cli.py"]))


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
