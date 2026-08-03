"""Tests for immutable source-identity and repair-draft foundation models.

Run with:

    python scripts/test_gauss_repair_draft.py

No test performs any file I/O, launches GAUSS, calls an execution helper, or
mutates workspace state. This module constructs and validates data only.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_repair_draft as rd  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _artifact(**overrides: object) -> rd.SourceArtifact:
    values = {"workspace_id": "ws-1", "relative_path": "model.gss", "file_type": ".gss"}
    values.update(overrides)
    return rd.SourceArtifact(**values)


def _identity(**overrides: object) -> rd.SourceIdentity:
    values = {
        "artifact": _artifact(),
        "content_hash": "a" * 64,
        "size": 128,
        "encoding": "utf-8",
        "line_range": None,
        "observed_at": "1000.0",
    }
    values.update(overrides)
    return rd.SourceIdentity(**values)


def _scope(**overrides: object) -> rd.EditScope:
    values = {
        "line_start": 3,
        "line_end": 3,
        "intended_operation": "insert missing statement terminator",
        "target_procedure": None,
        "target_symbol": None,
    }
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
# Identity equality and digests
# ---------------------------------------------------------------------------


def test_01_source_artifact_equality_deterministic() -> None:
    a1 = _artifact()
    a2 = _artifact()
    check("two identically-constructed SourceArtifact instances are equal", a1 == a2)
    check("SourceArtifact is hashable", hash(a1) == hash(a2))


def test_02_source_identity_equality_deterministic() -> None:
    i1 = _identity()
    i2 = _identity()
    check("two identically-constructed SourceIdentity instances are equal", i1 == i2)
    check("SourceIdentity is hashable", hash(i1) == hash(i2))


def test_03_source_identity_inequality_on_hash_change() -> None:
    i1 = _identity()
    i2 = _identity(content_hash="b" * 64)
    check("different content_hash produces inequality", i1 != i2)


def test_04_source_identity_inequality_on_workspace_change() -> None:
    i1 = _identity()
    i2 = _identity(artifact=_artifact(workspace_id="ws-2"))
    check("different workspace_id produces inequality", i1 != i2)


def test_05_source_identity_digest_deterministic() -> None:
    i1 = _identity()
    i2 = _identity()
    check("identical SourceIdentity instances share a digest", rd.source_identity_digest(i1) == rd.source_identity_digest(i2))


def test_06_source_identity_digest_changes_with_content_hash() -> None:
    i1 = _identity()
    i2 = _identity(content_hash="c" * 64)
    check("different content_hash changes the identity digest", rd.source_identity_digest(i1) != rd.source_identity_digest(i2))


def test_07_repair_draft_digest_deterministic() -> None:
    d1 = _draft()
    d2 = _draft()
    check("identically-constructed drafts share a digest", rd.repair_draft_digest(d1) == rd.repair_draft_digest(d2))


def test_08_repair_draft_digest_is_sha256_hex() -> None:
    digest = rd.repair_draft_digest(_draft())
    check("digest is 64 hex characters", len(digest) == 64)
    check("digest contains only lowercase hex characters", all(c in "0123456789abcdef" for c in digest))


def test_09_repeated_construction_produces_identical_digests() -> None:
    digests = {rd.repair_draft_digest(_draft()) for _ in range(5)}
    check("five independently constructed, identical drafts share exactly one digest", len(digests) == 1)


def test_10_repair_draft_digest_changes_with_source_identity() -> None:
    base = _draft()
    changed = _draft(source_identity=_identity(content_hash="f" * 64))
    check("changing the bound source identity changes the draft digest", rd.repair_draft_digest(base) != rd.repair_draft_digest(changed))


def test_11_draft_id_excluded_from_digest() -> None:
    d1 = _draft(repair_draft_id="draft-alpha")
    d2 = _draft(repair_draft_id="draft-beta")
    check("different repair_draft_id, otherwise identical content, share a digest", rd.repair_draft_digest(d1) == rd.repair_draft_digest(d2))
    check("the two drafts are still distinguishable by their own id field", d1.repair_draft_id != d2.repair_draft_id)


def test_12_repair_draft_digest_changes_with_edit_scope() -> None:
    base = _draft()
    changed = _draft(edit_scope=_scope(line_start=10, line_end=10))
    check("changing the edit scope changes the draft digest", rd.repair_draft_digest(base) != rd.repair_draft_digest(changed))


def test_13_repair_draft_digest_changes_with_plan_digest() -> None:
    base = _draft()
    changed = _draft(repair_plan_digest="e" * 64)
    check("changing the bound repair_plan_digest changes the draft digest", rd.repair_draft_digest(base) != rd.repair_draft_digest(changed))


# ---------------------------------------------------------------------------
# Validation: matching / mismatch scenarios
# ---------------------------------------------------------------------------


def test_14_validation_passes_with_no_current_identity_supplied() -> None:
    result = rd.validate_repair_draft(_draft())
    check("all checks pass when no current source identity is supplied", result.all_passed)
    check("no failed checks", result.failed_checks == ())


def test_15_validation_passes_with_matching_current_identity() -> None:
    draft = _draft()
    result = rd.validate_repair_draft(draft, current_source_identity=draft.source_identity)
    check("validation passes when the current identity exactly matches the bound identity", result.all_passed)


def test_16_hash_mismatch_fails_validation() -> None:
    draft = _draft()
    stale = _identity(content_hash="9" * 64)
    result = rd.validate_repair_draft(draft, current_source_identity=stale)
    check("hash mismatch is reported", "hash_match" in result.failed_checks)
    check("overall validation fails on hash mismatch", result.all_passed is False)
    check("workspace_match is unaffected by a pure hash change", "workspace_match" not in result.failed_checks)


def test_17_workspace_mismatch_fails_validation() -> None:
    draft = _draft()
    swapped = _identity(artifact=_artifact(workspace_id="ws-other"))
    result = rd.validate_repair_draft(draft, current_source_identity=swapped)
    check("workspace mismatch is reported", "workspace_match" in result.failed_checks)
    check("overall validation fails on workspace mismatch", result.all_passed is False)


def test_18_path_mismatch_fails_validation() -> None:
    draft = _draft()
    swapped_path = _identity(artifact=_artifact(relative_path="other.gss"))
    result = rd.validate_repair_draft(draft, current_source_identity=swapped_path)
    check("path mismatch is reported under workspace_match", "workspace_match" in result.failed_checks)


# ---------------------------------------------------------------------------
# Validation: structural checks
# ---------------------------------------------------------------------------


def test_19_valid_utf8_encoding_required() -> None:
    bad = _draft(source_identity=_identity(encoding="latin-1"))
    result = rd.validate_repair_draft(bad)
    check("non-utf-8 declared encoding fails validation", "valid_utf8_encoding" in result.failed_checks)


def test_20_valid_range_rejects_inverted_range() -> None:
    bad = _draft(edit_scope=_scope(line_start=10, line_end=3))
    result = rd.validate_repair_draft(bad)
    check("an inverted range (end before start) fails valid_range", "valid_range" in result.failed_checks)
    check("bounded_scope also fails when the range itself is invalid", "bounded_scope" in result.failed_checks)


def test_21_valid_range_rejects_zero_or_negative_lines() -> None:
    bad = _draft(edit_scope=_scope(line_start=0, line_end=0))
    result = rd.validate_repair_draft(bad)
    check("line_start of 0 fails valid_range (1-based lines)", "valid_range" in result.failed_checks)


def test_22_bounded_scope_rejects_oversized_range() -> None:
    bad = _draft(edit_scope=_scope(line_start=1, line_end=rd.MAX_EDIT_RANGE_LINES + 50))
    result = rd.validate_repair_draft(bad)
    check("a range exceeding MAX_EDIT_RANGE_LINES fails bounded_scope", "bounded_scope" in result.failed_checks)
    check("valid_range itself still passes for an oversized-but-well-formed range", "valid_range" not in result.failed_checks)


def test_23_bounded_scope_accepts_range_at_exact_limit() -> None:
    ok = _draft(edit_scope=_scope(line_start=1, line_end=rd.MAX_EDIT_RANGE_LINES))
    result = rd.validate_repair_draft(ok)
    check("a range exactly at the MAX_EDIT_RANGE_LINES bound passes", "bounded_scope" not in result.failed_checks)


def test_24_single_file_structurally_guaranteed() -> None:
    result = rd.validate_repair_draft(_draft())
    single_file_check = next(c for c in result.checks if c.check == "single_file")
    check("single_file check always passes (structural guarantee)", single_file_check.passed)


def test_25_immutable_identity_check_passes_for_frozen_dataclass() -> None:
    result = rd.validate_repair_draft(_draft())
    immutable_check = next(c for c in result.checks if c.check == "immutable_identity")
    check("immutable_identity check passes for a real frozen SourceIdentity", immutable_check.passed)


def test_26_deterministic_digest_check_present_and_passing() -> None:
    result = rd.validate_repair_draft(_draft())
    digest_check = next(c for c in result.checks if c.check == "deterministic_digest")
    check("deterministic_digest check passes", digest_check.passed)
    check("validation result's own draft_digest matches repair_draft_digest(draft)", result.draft_digest == rd.repair_draft_digest(_draft()))


def test_27_reversible_representation_requires_description() -> None:
    empty_description = rd.RepairDraft(
        repair_draft_id="draft-empty",
        repair_plan_digest="a" * 64,
        source_identity=_identity(),
        edit_scope=_scope(),
        proposed_change_description="   ",
        assumptions=(),
        risks=(),
        verification_steps=(),
        generated_at="1000.0",
        generated_by="test",
        approval_required=True,
        safe_to_prepare_draft=False,
        safe_to_apply=False,
        draft_boundary=rd.DRAFT_BOUNDARY_STATEMENT,
    )
    result = rd.validate_repair_draft(empty_description)
    check("a blank description fails reversible_representation", "reversible_representation" in result.failed_checks)


def test_28_no_generated_code_rejects_semicolon() -> None:
    bad = _draft(edit_scope=_scope(intended_operation="x = 2 + 2;"))
    result = rd.validate_repair_draft(bad)
    check("a semicolon in intended_operation fails no_generated_code", "no_generated_code" in result.failed_checks)


def test_29_no_generated_code_rejects_assignment() -> None:
    bad = _draft(proposed_change_description="Set x = ones(2,2) to fix the dimension issue.")
    result = rd.validate_repair_draft(bad)
    check("an assignment-shaped description fails no_generated_code", "no_generated_code" in result.failed_checks)


def test_30_no_generated_code_passes_for_bounded_prose() -> None:
    result = rd.validate_repair_draft(_draft())
    check("ordinary bounded prose passes no_generated_code", "no_generated_code" not in result.failed_checks)


# ---------------------------------------------------------------------------
# Immutability and safety invariants
# ---------------------------------------------------------------------------


def test_31_source_artifact_is_frozen() -> None:
    artifact = _artifact()
    raised = False
    try:
        artifact.workspace_id = "changed"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        raised = True
    check("SourceArtifact raises FrozenInstanceError on mutation attempt", raised)


def test_32_source_identity_is_frozen() -> None:
    identity = _identity()
    raised = False
    try:
        identity.content_hash = "changed"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        raised = True
    check("SourceIdentity raises FrozenInstanceError on mutation attempt", raised)


def test_33_edit_scope_is_frozen() -> None:
    scope = _scope()
    raised = False
    try:
        scope.line_start = 99  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        raised = True
    check("EditScope raises FrozenInstanceError on mutation attempt", raised)


def test_34_repair_draft_is_frozen() -> None:
    draft = _draft()
    raised = False
    try:
        draft.proposed_change_description = "changed"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        raised = True
    check("RepairDraft raises FrozenInstanceError on mutation attempt", raised)


def test_35_safe_to_apply_always_false() -> None:
    scenarios = [
        _draft(),
        _draft(edit_scope=_scope(line_start=1, line_end=50)),
        _draft(source_identity=_identity(content_hash="1" * 64)),
        _draft(repair_plan_digest="2" * 64),
    ]
    for draft in scenarios:
        check(f"safe_to_apply is False for draft {draft.repair_draft_id}", draft.safe_to_apply is False)


def test_36_safe_to_prepare_draft_always_false() -> None:
    scenarios = [
        _draft(),
        _draft(edit_scope=_scope(line_start=1, line_end=50)),
        _draft(source_identity=_identity(content_hash="1" * 64)),
    ]
    for draft in scenarios:
        check(f"safe_to_prepare_draft is False for draft {draft.repair_draft_id}", draft.safe_to_prepare_draft is False)


def test_37_approval_required_always_true_via_builder() -> None:
    check("build_repair_draft always sets approval_required True", _draft().approval_required is True)


def test_38_draft_boundary_statement_fixed_and_present() -> None:
    check("draft_boundary is the fixed statement", _draft().draft_boundary == rd.DRAFT_BOUNDARY_STATEMENT)
    check("draft boundary discloses no file was modified", "no file" in _draft().draft_boundary.lower() or "no code was generated" in _draft().draft_boundary.lower())


def test_39_no_filesystem_mutation_in_module_source() -> None:
    source = Path(rd.__file__).read_text(encoding="utf-8")
    forbidden = ("open(", "write_text(", "read_text(", "os.remove", "os.replace", "shutil.")
    for token in forbidden:
        check(f"module source contains no {token!r}", token not in source)


def test_40_no_forbidden_imports() -> None:
    source = Path(rd.__file__).read_text(encoding="utf-8")
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


def test_41_generic_assumptions_risks_verification_steps_present() -> None:
    draft = _draft()
    check("assumptions is non-empty", len(draft.assumptions) > 0)
    check("risks is non-empty", len(draft.risks) > 0)
    check("verification_steps is non-empty", len(draft.verification_steps) > 0)


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
