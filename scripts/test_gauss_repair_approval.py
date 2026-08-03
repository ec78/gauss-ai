"""Tests for deterministic, process-local repair-plan approval recording.

Run with:

    python scripts/test_gauss_repair_approval.py

No test launches GAUSS, calls an execution helper, mutates workspace state,
edits source code, reads or writes files, accesses the network, or retries.
The approval module consumes already-computed `RepairPlan` objects only.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_execution_interpreter as interp  # noqa: E402
import gauss_repair_approval as approval  # noqa: E402
import gauss_repair_planner as rp  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _failed(stderr_text: str, **overrides: object) -> interp.ExecutionEvidence:
    values = {
        "runner": "REAL_GAUSS",
        "gauss_ran": True,
        "executed": True,
        "execution_status": "failed",
        "exit_code": 0,
        "stdout_chars": len("Program execute failed\n"),
        "stderr_chars": len(stderr_text),
        "timed_out": False,
        "stdout_text": "Program execute failed\n",
        "stderr_text": stderr_text,
    }
    values.update(overrides)
    return interp.ExecutionEvidence(**values)


def _g0036_plan(source_context: "rp.SourceContext | None" = None) -> "rp.RepairPlan":
    return rp.plan_repair(_failed("error G0036 : Matrix dimensions are incompatible\n"), source_context=source_context)


# ---------------------------------------------------------------------------
# Digest tests (repair_plan_digest lives in gauss_repair_planner.py, but its
# only consumer is this milestone's approval module, so its correctness is
# exercised thoroughly here too, alongside the dedicated tests added to
# scripts/test_gauss_repair_planner.py).
# ---------------------------------------------------------------------------


def test_01_deterministic_digest_generation() -> None:
    plan = _g0036_plan()
    d1 = rp.repair_plan_digest(plan)
    d2 = rp.repair_plan_digest(plan)
    check("digest is deterministic for the same plan object", d1 == d2)
    check("digest looks like a sha256 hex string", len(d1) == 64 and all(c in "0123456789abcdef" for c in d1))


def test_02_identical_plans_produce_identical_digests() -> None:
    plan_a = _g0036_plan()
    plan_b = _g0036_plan()
    check("two independently computed identical plans share a digest", rp.repair_plan_digest(plan_a) == rp.repair_plan_digest(plan_b))


def test_03_meaningful_plan_changes_produce_different_digests() -> None:
    no_context = _g0036_plan()
    with_context = _g0036_plan(rp.SourceContext(matrix_shapes=("A=2x3", "B=4x5")))
    other_code = rp.plan_repair(_failed("error G0025 : Undefined symbol: 'x'\n"))
    d_no_context = rp.repair_plan_digest(no_context)
    d_with_context = rp.repair_plan_digest(with_context)
    d_other_code = rp.repair_plan_digest(other_code)
    check("source-context-narrowed plan has a different digest", d_no_context != d_with_context)
    check("a different error code produces a different digest", d_no_context != d_other_code)


# ---------------------------------------------------------------------------
# Core approval-store scenarios
# ---------------------------------------------------------------------------


def test_04_approval_accepted_for_matching_digest() -> None:
    plan = _g0036_plan()
    store = approval.RepairApprovalStore()
    record = store.approve(plan, recorded_at="t0")
    check("decision is approved", record.decision == approval.ApprovalDecision.APPROVED.value)
    check("digest matches the plan's own digest", record.plan_digest == rp.repair_plan_digest(plan))
    looked_up = store.get_decision(plan)
    check("get_decision finds the record for the same plan", looked_up == record)


def test_05_stale_approval_rejected_against_changed_plan() -> None:
    original = _g0036_plan()
    changed = _g0036_plan(rp.SourceContext(matrix_shapes=("A=2x3", "B=4x5")))
    store = approval.RepairApprovalStore()
    store.approve(original, recorded_at="t0")
    check("no decision found for the changed plan (different digest)", store.get_decision(changed) is None)
    check("the original plan's decision is unaffected", store.get_decision(original) is not None)


def test_06_decline_path() -> None:
    plan = _g0036_plan()
    store = approval.RepairApprovalStore()
    record = store.decline(plan, recorded_at="t0")
    check("decision is declined", record.decision == approval.ApprovalDecision.DECLINED.value)
    check("declined record still has safe_to_apply false", record.safe_to_apply is False)
    check("declined record still has safe_to_prepare_draft false", record.safe_to_prepare_draft is False)


def test_07_re_approval_or_overwrite_behavior() -> None:
    plan = _g0036_plan()
    store = approval.RepairApprovalStore()
    store.approve(plan, recorded_at="t0")
    raised = False
    try:
        store.approve(plan, recorded_at="t1")
    except approval.ApprovalConflictError:
        raised = True
    check("re-approving the same plan without revoke raises ApprovalConflictError", raised)

    raised_on_decline_too = False
    try:
        store.decline(plan, recorded_at="t2")
    except approval.ApprovalConflictError:
        raised_on_decline_too = True
    check("declining an already-approved plan without revoke also raises", raised_on_decline_too)

    check("revoke returns True when a record existed", store.revoke(plan) is True)
    check("revoke returns False when no record exists", store.revoke(plan) is False)
    new_record = store.decline(plan, recorded_at="t3")
    check("after revoke, a new decision can be recorded", new_record.decision == approval.ApprovalDecision.DECLINED.value)
    check("the store still reports exactly one record", len(store) == 1)


def test_08_approval_never_sets_safe_flags_true() -> None:
    for status_maker in (
        lambda: _g0036_plan(),
        lambda: rp.plan_repair(_failed("error G0290 : Library not found\n")),
        lambda: rp.plan_repair(interp.ExecutionEvidence(
            runner="REAL_GAUSS", gauss_ran=True, executed=True, execution_status="completed",
            exit_code=0, stdout_chars=5, stderr_chars=0, timed_out=False, stdout_text="ok\n", stderr_text="",
        )),
    ):
        plan = status_maker()
        store = approval.RepairApprovalStore()
        approved = store.approve(plan, recorded_at="t0")
        check(f"approved record for status={plan.repair_status} has safe_to_apply false", approved.safe_to_apply is False)
        check(f"approved record for status={plan.repair_status} has safe_to_prepare_draft false", approved.safe_to_prepare_draft is False)
        check(f"approving does not mutate the underlying RepairPlan's own safe_to_apply", plan.safe_to_apply is False)
        check(f"approving does not mutate the underlying RepairPlan's own safe_to_prepare_draft", plan.safe_to_prepare_draft is False)


def test_09_approval_module_has_no_forbidden_imports() -> None:
    source = Path(approval.__file__).read_text(encoding="utf-8")
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
        "requests",
        "http.client",
    )
    for name in forbidden:
        check(f"approval module does not import {name!r}", f"import {name}" not in source)
    check("approval module does not read files", "open(" not in source and "read_text(" not in source and "write_text(" not in source)


def test_10_approval_boundary_statement_present() -> None:
    plan = _g0036_plan()
    store = approval.RepairApprovalStore()
    record = store.approve(plan, recorded_at="t0")
    check("approval_boundary is the fixed statement", record.approval_boundary == approval.APPROVAL_BOUNDARY_STATEMENT)
    check("boundary text states application did not occur", "not apply" in record.approval_boundary.lower() or "does not apply" in record.approval_boundary.lower())


def test_11_get_decision_for_digest_matches_get_decision() -> None:
    plan = _g0036_plan()
    store = approval.RepairApprovalStore()
    record = store.approve(plan, recorded_at="t0")
    check(
        "get_decision_for_digest returns the same record as get_decision",
        store.get_decision_for_digest(rp.repair_plan_digest(plan)) == store.get_decision(plan),
    )
    check("get_decision_for_digest returns None for an unknown digest", store.get_decision_for_digest("0" * 64) is None)


def test_12_multiple_independent_plans_do_not_collide() -> None:
    plan_a = _g0036_plan()
    plan_b = rp.plan_repair(_failed("error G0025 : Undefined symbol: 'x'\n"))
    store = approval.RepairApprovalStore()
    store.approve(plan_a, recorded_at="t0")
    store.decline(plan_b, recorded_at="t1")
    check("plan A decision is approved", store.get_decision(plan_a).decision == "approved")
    check("plan B decision is declined", store.get_decision(plan_b).decision == "declined")
    check("store holds exactly two records", len(store) == 2)


def test_13_unknown_error_plan_can_still_be_declined() -> None:
    plan = rp.plan_repair(_failed("error G9999 : Never cataloged\n"))
    store = approval.RepairApprovalStore()
    record = store.decline(plan, recorded_at="t0")
    check("decline works even for an unknown-error plan with no proposed actions", record.decision == "declined")
    check("source_error_code preserved on the record", record.source_error_code == "G9999")


def test_14_store_is_process_local_only() -> None:
    store_a = approval.RepairApprovalStore()
    store_b = approval.RepairApprovalStore()
    plan = _g0036_plan()
    store_a.approve(plan, recorded_at="t0")
    check("a fresh store instance has no knowledge of another store's records", store_b.get_decision(plan) is None)


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
