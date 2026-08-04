"""Tests for the pure Repair Application Gate precondition re-verification.

Run with:

    python scripts/test_gauss_repair_application_gate.py

No test launches GAUSS, calls an execution helper, mutates workspace state,
edits source code, reads or writes files, accesses the network, or retries.
`evaluate_application_gate(...)` consumes already-constructed plan/draft/
approval-record/identity values only.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_repair_application_approval as aa  # noqa: E402
import gauss_repair_application_gate as gate  # noqa: E402
import gauss_repair_approval as ra  # noqa: E402
import gauss_repair_draft as rd  # noqa: E402
import gauss_repair_draft_approval as da  # noqa: E402
import gauss_repair_planner as rp  # noqa: E402
import gauss_execution_interpreter as interp  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _evidence(**overrides: object) -> "interp.ExecutionEvidence":
    values = {
        "runner": "FAKE",
        "gauss_ran": False,
        "executed": True,
        "execution_status": "failed",
        "exit_code": 0,
        "stdout_chars": 0,
        "stderr_chars": 0,
        "timed_out": False,
        "workspace_state": "failed",
        "provenance": None,
        "stdout_text": "Program execute failed\n",
        "stderr_text": "error G0105 : Undefined symbol\n",
        "metadata_error": None,
    }
    values.update(overrides)
    return interp.ExecutionEvidence(**values)


def _plan() -> "rp.RepairPlan":
    return rp.plan_repair(_evidence())


def _artifact(**overrides: object) -> rd.SourceArtifact:
    values = {"workspace_id": "ws-1", "relative_path": "model.gss", "file_type": ".gss"}
    values.update(overrides)
    return rd.SourceArtifact(**values)


def _identity(**overrides: object) -> rd.SourceIdentity:
    values = {"artifact": _artifact(), "content_hash": "a" * 64, "size": 128, "encoding": "utf-8"}
    values.update(overrides)
    return rd.SourceIdentity(**values)


def _scope(**overrides: object) -> rd.EditScope:
    values = {"line_start": 3, "line_end": 3, "intended_operation": "insert missing statement terminator"}
    values.update(overrides)
    return rd.EditScope(**values)


def _draft(plan: "rp.RepairPlan", **overrides: object) -> rd.RepairDraft:
    values = {
        "repair_draft_id": "draft-1",
        "repair_plan_digest": rp.repair_plan_digest(plan),
        "source_identity": _identity(),
        "edit_scope": _scope(),
        "proposed_change_description": "Insert a missing statement terminator at the reported line.",
        "generated_at": "1000.0",
    }
    values.update(overrides)
    return rd.build_repair_draft(**values)


@dataclass(frozen=True)
class _FullyApprovedFixture:
    plan: "rp.RepairPlan"
    plan_record: "ra.ApprovalRecord"
    draft: "rd.RepairDraft"
    draft_record: "da.DraftApprovalRecord"
    application_record: "aa.ApplicationApprovalRecord"
    current_identity: "rd.SourceIdentity"


def _fully_approved() -> _FullyApprovedFixture:
    plan = _plan()
    plan_record = ra.RepairApprovalStore().approve(plan, recorded_at="t0")
    draft = _draft(plan)
    draft_record = da.DraftApprovalStore().approve(draft, recorded_at="t0")
    application_record = aa.ApplicationApprovalStore().approve(draft, recorded_at="t0")
    return _FullyApprovedFixture(
        plan=plan, plan_record=plan_record, draft=draft, draft_record=draft_record,
        application_record=application_record, current_identity=_identity(),
    )


def _evaluate(f: _FullyApprovedFixture, **overrides: object) -> "gate.ApplicationGateResult":
    kwargs: dict[str, object] = {
        "repair_plan": f.plan,
        "repair_approval_record": f.plan_record,
        "repair_draft": f.draft,
        "draft_approval_record": f.draft_record,
        "application_approval_record": f.application_record,
        "current_source_identity": f.current_identity,
        "workspace_status": "ready",
    }
    kwargs.update(overrides)
    return gate.evaluate_application_gate(**kwargs)


def _check_result(result: "gate.ApplicationGateResult", check_name: str) -> "gate.ApplicationGateCheckResult":
    matches = [c for c in result.checks if c.check == check_name]
    assert matches, f"no check named {check_name!r} in result"
    return matches[0]


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_01_fully_approved_and_fresh_passes_every_check() -> None:
    f = _fully_approved()
    result = _evaluate(f)
    check("all_passed is True", result.all_passed is True)
    check("no failed checks", result.failed_checks == ())
    check("exactly ten checks reported", len(result.checks) == 10)
    check("draft_digest matches", result.draft_digest == rd.repair_draft_digest(f.draft))


def test_02_gate_boundary_present_and_states_no_authorization() -> None:
    f = _fully_approved()
    result = _evaluate(f)
    check("gate_boundary is the fixed statement", result.gate_boundary == gate.GATE_BOUNDARY_STATEMENT)
    check("gate boundary denies authorization", "does not authorize applying anything" in result.gate_boundary)


def test_03_not_applicable_checks_disclosed() -> None:
    f = _fully_approved()
    result = _evaluate(f)
    check("not_applicable_checks matches the module constant", result.not_applicable_checks == gate.NOT_APPLICABLE_GATE_ITEMS)
    check("backup_prepared is named as not applicable", "backup_prepared" in result.not_applicable_checks)
    check("audit_record_initialized is named as not applicable", "audit_record_initialized" in result.not_applicable_checks)


# ---------------------------------------------------------------------------
# Each check's failure path
# ---------------------------------------------------------------------------


def test_04_missing_strategy_approval_fails_gate() -> None:
    f = _fully_approved()
    result = _evaluate(f, repair_approval_record=None)
    c = _check_result(result, "strategy_approval_exists")
    check("strategy_approval_exists fails when no record supplied", c.passed is False)
    check("all_passed is False", result.all_passed is False)
    check("failed_checks names strategy_approval_exists", "strategy_approval_exists" in result.failed_checks)


def test_05_declined_strategy_approval_fails_gate() -> None:
    f = _fully_approved()
    declined_plan_record = ra.RepairApprovalStore().decline(_plan(), recorded_at="t0")
    result = _evaluate(f, repair_approval_record=declined_plan_record)
    check("strategy_approval_exists fails on a declined decision", _check_result(result, "strategy_approval_exists").passed is False)


def test_06_missing_draft_approval_fails_gate() -> None:
    f = _fully_approved()
    result = _evaluate(f, draft_approval_record=None)
    check("draft_approval_exists fails when no record supplied", _check_result(result, "draft_approval_exists").passed is False)
    check("all_passed is False", result.all_passed is False)


def test_07_missing_application_approval_fails_gate() -> None:
    f = _fully_approved()
    result = _evaluate(f, application_approval_record=None)
    check("application_approval_exists fails when no record supplied", _check_result(result, "application_approval_exists").passed is False)
    check("draft_digest_matches_approved also fails when no record supplied", _check_result(result, "draft_digest_matches_approved").passed is False)


def test_08_missing_current_source_identity_fails_closed() -> None:
    f = _fully_approved()
    result = _evaluate(f, current_source_identity=None)
    check("source_hash_matches fails closed when no current identity supplied", _check_result(result, "source_hash_matches").passed is False)
    check("path_unchanged fails closed when no current identity supplied", _check_result(result, "path_unchanged").passed is False)
    check("all_passed is False", result.all_passed is False)


def test_09_stale_source_hash_fails_gate() -> None:
    f = _fully_approved()
    stale_identity = _identity(content_hash="b" * 64)
    result = _evaluate(f, current_source_identity=stale_identity)
    check("source_hash_matches fails on a changed hash", _check_result(result, "source_hash_matches").passed is False)
    check("all_passed is False", result.all_passed is False)


def test_10_changed_path_fails_gate() -> None:
    f = _fully_approved()
    moved_identity = _identity(artifact=_artifact(relative_path="other.gss"))
    result = _evaluate(f, current_source_identity=moved_identity)
    check("path_unchanged fails when relative_path differs", _check_result(result, "path_unchanged").passed is False)


def test_11_changed_workspace_fails_gate() -> None:
    f = _fully_approved()
    moved_identity = _identity(artifact=_artifact(workspace_id="ws-other"))
    result = _evaluate(f, current_source_identity=moved_identity)
    check("path_unchanged fails when workspace_id differs", _check_result(result, "path_unchanged").passed is False)


def test_12_missing_workspace_status_fails_closed() -> None:
    f = _fully_approved()
    result = _evaluate(f, workspace_status=None)
    check("workspace_eligible fails closed when no status supplied", _check_result(result, "workspace_eligible").passed is False)
    check("all_passed is False", result.all_passed is False)


def test_13_deleted_workspace_fails_gate() -> None:
    f = _fully_approved()
    result = _evaluate(f, workspace_status="deleted")
    check("workspace_eligible fails for a deleted workspace", _check_result(result, "workspace_eligible").passed is False)


def test_14_revoked_strategy_approval_fails_gate() -> None:
    f = _fully_approved()
    strategy_store = ra.RepairApprovalStore()
    strategy_store.approve(f.plan, recorded_at="t0")
    strategy_store.revoke(f.plan)
    revoked_record = strategy_store.get_decision(f.plan)
    check("precondition: revoke actually deletes strategy-level records (not found afterward)", revoked_record is None)
    # Strategy-level revoke deletes the record entirely (v0.57.0 precedent) --
    # so the realistic "revoked" case at the gate is a supplied None, already
    # covered by test_04. This test instead proves NO_REVOCATION correctly
    # reports a revoked draft- or application-layer record.
    draft_store = da.DraftApprovalStore()
    draft_store.approve(f.draft, recorded_at="t0")
    draft_store.revoke(f.draft, recorded_at="t1")
    revoked_draft_record = draft_store.get_decision(f.draft)
    result = _evaluate(f, draft_approval_record=revoked_draft_record)
    check("no_revocation fails when the draft-approval record is revoked", _check_result(result, "no_revocation").passed is False)
    check("draft_approval_exists also fails on a revoked record", _check_result(result, "draft_approval_exists").passed is False)


def test_15_revoked_application_approval_fails_gate() -> None:
    f = _fully_approved()
    app_store = aa.ApplicationApprovalStore()
    app_store.approve(f.draft, recorded_at="t0")
    app_store.revoke(f.draft, recorded_at="t1")
    revoked_application_record = app_store.get_decision(f.draft)
    result = _evaluate(f, application_approval_record=revoked_application_record)
    check("no_revocation fails when the application-approval record is revoked", _check_result(result, "no_revocation").passed is False)
    check("application_approval_exists also fails on a revoked record", _check_result(result, "application_approval_exists").passed is False)


def test_16_mismatched_application_approval_draft_digest_fails_gate() -> None:
    f = _fully_approved()
    other_draft = _draft(f.plan, edit_scope=_scope(line_start=10, line_end=10))
    stale_application_record = aa.ApplicationApprovalStore().approve(other_draft, recorded_at="t0")
    result = _evaluate(f, application_approval_record=stale_application_record)
    check("application_approval_exists fails when the record's draft_digest doesn't match", _check_result(result, "application_approval_exists").passed is False)
    check("draft_digest_matches_approved fails when the record's draft_digest doesn't match", _check_result(result, "draft_digest_matches_approved").passed is False)


def test_17_mismatched_plan_digest_on_strategy_record_fails_gate() -> None:
    f = _fully_approved()
    other_evidence = _evidence(stderr_text="error G0036 : Matrices are not conformable\n")
    other_plan_record = ra.RepairApprovalStore().approve(rp.plan_repair(other_evidence), recorded_at="t0")
    result = _evaluate(f, repair_approval_record=other_plan_record)
    check("strategy_approval_exists fails when the record's plan_digest doesn't match the current plan", _check_result(result, "strategy_approval_exists").passed is False)


def test_18_edit_scope_unchanged_always_passes_structurally() -> None:
    f = _fully_approved()
    result = _evaluate(f)
    c = _check_result(result, "edit_scope_unchanged")
    check("edit_scope_unchanged always passes (structural guarantee)", c.passed is True)
    check("edit_scope_unchanged detail explains the structural guarantee", "digest" in c.detail)


def test_19_validation_failure_propagates_to_gate() -> None:
    f = _fully_approved()
    bad_identity = _identity(encoding="latin-1")
    bad_draft = _draft(f.plan, source_identity=bad_identity)
    draft_record = da.DraftApprovalStore().approve(bad_draft, recorded_at="t0")
    application_record = aa.ApplicationApprovalStore().approve(bad_draft, recorded_at="t0")
    result = gate.evaluate_application_gate(
        repair_plan=f.plan, repair_approval_record=f.plan_record, repair_draft=bad_draft,
        draft_approval_record=draft_record, application_approval_record=application_record,
        current_source_identity=bad_identity, workspace_status="ready",
    )
    check("validation_passed fails for a non-UTF-8-declared draft", _check_result(result, "validation_passed").passed is False)
    check("all_passed is False", result.all_passed is False)


# ---------------------------------------------------------------------------
# Determinism, purity, structural safety
# ---------------------------------------------------------------------------


def test_20_determinism() -> None:
    f = _fully_approved()
    result1 = _evaluate(f)
    result2 = _evaluate(f)
    check("repeated evaluation of the same inputs is deterministic", result1 == result2)


def test_21_no_safe_to_apply_field_anywhere() -> None:
    f = _fully_approved()
    result = _evaluate(f)
    check("ApplicationGateResult has no safe_to_apply field", not hasattr(result, "safe_to_apply"))
    for c in result.checks:
        check(f"check result {c.check!r} has no safe_to_apply field", not hasattr(c, "safe_to_apply"))


def test_22_no_io_in_module_source() -> None:
    source = Path(gate.__file__).read_text(encoding="utf-8")
    forbidden = ("open(", "write_text(", "read_text(", "os.remove", "os.replace", "shutil.", "hashlib.")
    for token in forbidden:
        check(f"module source contains no {token!r}", token not in source)


def test_23_no_forbidden_imports() -> None:
    source = Path(gate.__file__).read_text(encoding="utf-8")
    forbidden = (
        "gauss_code_execution",
        "gauss_workspace",
        "gauss_runtime_orchestration",
        "gauss_execution_adapter",
        "gauss_execution_workflow",
        "gauss_execution_session",
        "gauss_orchestration_state_store",
        "subprocess",
        "socket",
        "urllib",
    )
    for name in forbidden:
        check(f"module does not import {name!r}", f"import {name}" not in source)


def test_24_result_is_immutable_dataclass() -> None:
    f = _fully_approved()
    result = _evaluate(f)
    raised = False
    try:
        result.all_passed = False  # type: ignore[misc]
    except Exception:  # noqa: BLE001
        raised = True
    check("ApplicationGateResult is frozen (assignment raises)", raised)


def run_tests() -> int:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        before = len(_failures)
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _failures.append(f"{name} raised an unexpected exception: {type(exc).__name__}: {exc}")
        if len(_failures) == before:
            print(f"PASS  {name}")
        else:
            for failure in _failures[before:]:
                print(f"FAIL  {name}: {failure}")
    print()
    print(f"{len(tests)} test function(s) run, {len(_failures)} check failure(s).")
    if _failures:
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
