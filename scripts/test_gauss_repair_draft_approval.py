"""Tests for deterministic, process-local repair-draft approval recording.

Run with:

    python scripts/test_gauss_repair_draft_approval.py

No test launches GAUSS, calls an execution helper, mutates workspace state,
edits source code, reads or writes files, accesses the network, or retries.
The draft-approval module consumes already-constructed `RepairDraft` objects
only.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_repair_draft as rd  # noqa: E402
import gauss_repair_draft_approval as da  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


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


def _draft(**overrides: object) -> rd.RepairDraft:
    values = {
        "repair_draft_id": "draft-1",
        "repair_plan_digest": "d" * 64,
        "source_identity": _identity(),
        "edit_scope": _scope(),
        "proposed_change_description": "Insert a missing statement terminator at the reported line.",
        "generated_at": "1000.0",
    }
    values.update(overrides)
    return rd.build_repair_draft(**values)


# ---------------------------------------------------------------------------
# Approve / decline / revoke
# ---------------------------------------------------------------------------


def test_01_approve_records_matching_digest() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    record = store.approve(draft, recorded_at="t0")
    check("decision is approved", record.decision == da.DraftApprovalDecision.APPROVED.value)
    check("draft_digest matches the draft's own digest", record.draft_digest == rd.repair_draft_digest(draft))
    check("repair_draft_id carried through for reference", record.repair_draft_id == draft.repair_draft_id)


def test_02_decline_records_matching_digest() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    record = store.decline(draft, recorded_at="t0")
    check("decision is declined", record.decision == da.DraftApprovalDecision.DECLINED.value)
    check("decline boundary text is distinct from approval boundary text", record.approval_boundary == da.DRAFT_DECLINE_BOUNDARY_STATEMENT)
    check("decline boundary does not falsely claim approval", "has been approved" not in record.approval_boundary)


def test_03_revoke_transitions_in_place() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    store.approve(draft, recorded_at="t0")
    revoked = store.revoke(draft, recorded_at="t1")
    check("revoke reports True for an active record", revoked is True)
    record = store.get_decision(draft)
    check("record still exists after revoke (preserved, not deleted)", record is not None)
    check("record's decision is now revoked", record.decision == da.DraftApprovalDecision.REVOKED.value)
    check("store still reports exactly one record", len(store) == 1)


def test_04_revoke_nonexistent_returns_false() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    check("revoking a digest with no record returns False", store.revoke(draft, recorded_at="t0") is False)


def test_05_revoke_already_revoked_returns_false() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    store.approve(draft, recorded_at="t0")
    store.revoke(draft, recorded_at="t1")
    check("revoking an already-revoked record returns False", store.revoke(draft, recorded_at="t2") is False)


def test_06_approve_after_revoke_succeeds() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    store.decline(draft, recorded_at="t0")
    store.revoke(draft, recorded_at="t1")
    record = store.approve(draft, recorded_at="t2")
    check("approval after revoke succeeds", record.decision == da.DraftApprovalDecision.APPROVED.value)
    check("store still reports exactly one record (overwritten, not appended)", len(store) == 1)


# ---------------------------------------------------------------------------
# Duplicate / conflict handling
# ---------------------------------------------------------------------------


def test_07_duplicate_approval_raises_conflict() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    store.approve(draft, recorded_at="t0")
    raised = False
    try:
        store.approve(draft, recorded_at="t1")
    except da.DraftApprovalConflictError:
        raised = True
    check("recording the identical decision twice raises DraftApprovalConflictError", raised)


def test_08_conflicting_decision_raises_conflict() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    store.approve(draft, recorded_at="t0")
    raised = False
    try:
        store.decline(draft, recorded_at="t1")
    except da.DraftApprovalConflictError:
        raised = True
    check("declining an already-approved draft without revoke raises DraftApprovalConflictError", raised)


def test_09_conflict_error_names_the_existing_decision() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    store.approve(draft, recorded_at="t0")
    message = ""
    try:
        store.approve(draft, recorded_at="t1")
    except da.DraftApprovalConflictError as exc:
        message = str(exc)
    check("conflict message names the existing decision", "approved" in message)
    check("conflict message names revoke as the remediation", "revoke" in message)


def test_10_conflict_does_not_mutate_the_existing_record() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    original = store.approve(draft, recorded_at="t0")
    try:
        store.approve(draft, recorded_at="t1")
    except da.DraftApprovalConflictError:
        pass
    check("the original record is unchanged after a rejected duplicate attempt", store.get_decision(draft) == original)


# ---------------------------------------------------------------------------
# Digest mismatch / binding
# ---------------------------------------------------------------------------


def test_11_digest_mismatch_produces_no_lookup_hit() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    store.approve(draft, recorded_at="t0")
    changed = _draft(edit_scope=_scope(line_start=10, line_end=10))
    check("a draft with a different digest has no recorded decision", store.get_decision(changed) is None)
    check("the original draft's decision is unaffected", store.get_decision(draft) is not None)


def test_12_binding_is_draft_digest_only_not_plan_digest() -> None:
    draft = _draft(repair_plan_digest="1" * 64)
    other_plan_same_everything_else = _draft(repair_plan_digest="1" * 64)
    store = da.DraftApprovalStore()
    store.approve(draft, recorded_at="t0")
    check(
        "an identically-shaped draft with the same plan digest is found (digest equality, not plan-digest binding)",
        store.get_decision(other_plan_same_everything_else) is not None,
    )
    different_plan = _draft(repair_plan_digest="2" * 64)
    check(
        "a draft differing only in repair_plan_digest is a genuinely different draft_digest and is not found",
        store.get_decision(different_plan) is None,
    )


def test_13_binding_is_draft_digest_only_not_workspace_or_path() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    store.approve(draft, recorded_at="t0")
    different_workspace = _draft(source_identity=_identity(artifact=_artifact(workspace_id="ws-other")))
    check("a draft differing only in workspace_id is a different draft_digest and is not found", store.get_decision(different_workspace) is None)
    different_path = _draft(source_identity=_identity(artifact=_artifact(relative_path="other.gss")))
    check("a draft differing only in relative_path is a different draft_digest and is not found", store.get_decision(different_path) is None)


def test_14_get_decision_for_digest_matches_get_decision() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    record = store.approve(draft, recorded_at="t0")
    check(
        "get_decision_for_digest returns the same record as get_decision",
        store.get_decision_for_digest(rd.repair_draft_digest(draft)) == store.get_decision(draft),
    )
    check("get_decision_for_digest returns None for an unknown digest", store.get_decision_for_digest("0" * 64) is None)


# ---------------------------------------------------------------------------
# Determinism, safety invariants, purity
# ---------------------------------------------------------------------------


def test_15_approval_determinism() -> None:
    draft1 = _draft()
    draft2 = _draft()
    store1 = da.DraftApprovalStore()
    store2 = da.DraftApprovalStore()
    record1 = store1.approve(draft1, recorded_at="t0")
    record2 = store2.approve(draft2, recorded_at="t0")
    check("identical drafts approved identically produce identical records", record1 == record2)


def test_16_safe_to_apply_always_false() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    approved = store.approve(draft, recorded_at="t0")
    check("approved record has safe_to_apply false", approved.safe_to_apply is False)
    store.revoke(draft, recorded_at="t1")
    declined = store.decline(draft, recorded_at="t2")
    check("declined record has safe_to_apply false", declined.safe_to_apply is False)
    revoked_record = store.get_decision(draft)
    store.revoke(draft, recorded_at="t3")
    revoked_record = store.get_decision(draft)
    check("revoked record has safe_to_apply false", revoked_record.safe_to_apply is False)
    check("approving does not mutate the underlying RepairDraft's own safe_to_apply", draft.safe_to_apply is False)


def test_17_safe_to_prepare_draft_always_false() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    approved = store.approve(draft, recorded_at="t0")
    check("approved record has safe_to_prepare_draft false", approved.safe_to_prepare_draft is False)
    check("approving does not mutate the underlying RepairDraft's own safe_to_prepare_draft", draft.safe_to_prepare_draft is False)


def test_18_no_io_in_module_source() -> None:
    source = Path(da.__file__).read_text(encoding="utf-8")
    forbidden = ("open(", "write_text(", "read_text(", "os.remove", "os.replace", "shutil.")
    for token in forbidden:
        check(f"module source contains no {token!r}", token not in source)


def test_19_no_forbidden_imports() -> None:
    source = Path(da.__file__).read_text(encoding="utf-8")
    forbidden = (
        "gauss_code_execution",
        "gauss_workspace",
        "gauss_runtime_orchestration",
        "gauss_execution_adapter",
        "gauss_execution_workflow",
        "gauss_execution_session",
        "gauss_orchestration_state_store",
        "gauss_repair_planner",
        "gauss_repair_approval",
        "subprocess",
        "socket",
        "urllib",
    )
    for name in forbidden:
        check(f"module does not import {name!r}", f"import {name}" not in source)


def test_20_approval_boundary_statement_fixed_and_present() -> None:
    draft = _draft()
    store = da.DraftApprovalStore()
    record = store.approve(draft, recorded_at="t0")
    check("approval_boundary is the fixed approved statement", record.approval_boundary == da.DRAFT_APPROVAL_BOUNDARY_STATEMENT)
    check("approval boundary discloses no files modified", "no files have been modified" in record.approval_boundary.lower())
    check("approval boundary discloses no execution occurred", "no execution has occurred" in record.approval_boundary.lower())
    check("approval boundary discloses application remains unavailable", "repair application remains unavailable" in record.approval_boundary.lower())


def test_21_multiple_independent_drafts_do_not_collide() -> None:
    draft_a = _draft(repair_draft_id="draft-a")
    draft_b = _draft(repair_draft_id="draft-b", edit_scope=_scope(line_start=20, line_end=20))
    store = da.DraftApprovalStore()
    store.approve(draft_a, recorded_at="t0")
    store.decline(draft_b, recorded_at="t1")
    check("draft A decision is approved", store.get_decision(draft_a).decision == "approved")
    check("draft B decision is declined", store.get_decision(draft_b).decision == "declined")
    check("store holds exactly two records", len(store) == 2)


def test_22_store_is_process_local_only() -> None:
    draft = _draft()
    store_a = da.DraftApprovalStore()
    store_b = da.DraftApprovalStore()
    store_a.approve(draft, recorded_at="t0")
    check("a fresh store instance has no knowledge of another store's records", store_b.get_decision(draft) is None)


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
