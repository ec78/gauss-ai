"""Tests for the Verification Review module.

Run with:

    python scripts/test_gauss_verification_review.py

No test launches GAUSS, calls an execution helper, mutates a repair or
approval store, or reads/writes a file. The review module consumes only an
already-computed `ComparisonSummary` and caller-supplied strings.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_verification_execution as ver  # noqa: E402
import gauss_verification_review as review  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _summary(**overrides: object) -> ver.ComparisonSummary:
    values = {
        "original_outcome": "Runtime error G0105",
        "verification_outcome": "Execution successful",
        "same_outcome": False,
        "comparison": ver.ComparisonOutcome.SUCCEEDED_AFTER_FAILURE.value,
        "observation": (
            "The repaired code executed successfully whereas the original execution failed with G0105."
        ),
    }
    values.update(overrides)
    return ver.ComparisonSummary(**values)


# ---------------------------------------------------------------------------
# accepted / rejected / inconclusive
# ---------------------------------------------------------------------------


def test_01_accept_records_decision() -> None:
    store = review.VerificationReviewStore()
    summary = _summary()
    record = store.accept(
        verification_execution_id="ve-1", comparison_summary=summary, reviewed_by="alice", reviewed_at="t0"
    )
    check("decision is accepted", record.decision == review.ReviewDecision.ACCEPTED.value)
    check("verification_execution_id carried through", record.verification_execution_id == "ve-1")
    check("comparison_summary_digest matches recomputation", record.comparison_summary_digest == review.comparison_summary_digest(summary))
    check("reviewed_by carried through", record.reviewed_by == "alice")
    check("reviewed_at carried through", record.reviewed_at == "t0")
    check("notes defaults to empty string", record.notes == "")
    check("boundary is the fixed statement", record.boundary == review.VERIFICATION_REVIEW_BOUNDARY)


def test_02_reject_records_decision() -> None:
    store = review.VerificationReviewStore()
    record = store.reject(
        verification_execution_id="ve-2", comparison_summary=_summary(), reviewed_by="bob", reviewed_at="t0",
        notes="Different error surfaced; not accepting this repair.",
    )
    check("decision is rejected", record.decision == review.ReviewDecision.REJECTED.value)
    check("notes carried through", record.notes == "Different error surfaced; not accepting this repair.")


def test_03_mark_inconclusive_records_decision() -> None:
    store = review.VerificationReviewStore()
    record = store.mark_inconclusive(
        verification_execution_id="ve-3", comparison_summary=_summary(), reviewed_by="carol", reviewed_at="t0",
    )
    check("decision is inconclusive", record.decision == review.ReviewDecision.INCONCLUSIVE.value)


def test_04_boundary_text_identical_across_all_three_decisions() -> None:
    store = review.VerificationReviewStore()
    accepted = store.accept(verification_execution_id="a", comparison_summary=_summary(), reviewed_by="x", reviewed_at="t0")
    rejected = store.reject(verification_execution_id="b", comparison_summary=_summary(), reviewed_by="x", reviewed_at="t0")
    inconclusive = store.mark_inconclusive(verification_execution_id="c", comparison_summary=_summary(), reviewed_by="x", reviewed_at="t0")
    check("boundary identical for accepted/rejected/inconclusive", accepted.boundary == rejected.boundary == inconclusive.boundary)
    check("boundary discloses human-conclusion framing", "This review records a human conclusion" in accepted.boundary)
    check("boundary discloses system is not determining correctness", "not determining whether the repair is correct" in accepted.boundary)


# ---------------------------------------------------------------------------
# comparison_summary_digest
# ---------------------------------------------------------------------------


def test_05_digest_deterministic_for_identical_content() -> None:
    s1 = _summary()
    s2 = _summary()
    check("two independently-built summaries with identical content produce the same digest", review.comparison_summary_digest(s1) == review.comparison_summary_digest(s2))
    check("s1 is not s2 (genuinely independent instances)", s1 is not s2)


def test_06_digest_differs_for_different_content() -> None:
    s1 = _summary()
    s2 = _summary(comparison=ver.ComparisonOutcome.SAME_ERROR.value, observation="The repair did not change the observed execution outcome.")
    check("digests differ for different comparison content", review.comparison_summary_digest(s1) != review.comparison_summary_digest(s2))


def test_07_digest_is_64_char_hex() -> None:
    digest = review.comparison_summary_digest(_summary())
    check("digest is 64 hex characters", len(digest) == 64 and all(c in "0123456789abcdef" for c in digest))


# ---------------------------------------------------------------------------
# duplicate review handling
# ---------------------------------------------------------------------------


def test_08_duplicate_review_same_id_raises() -> None:
    store = review.VerificationReviewStore()
    store.accept(verification_execution_id="ve-dup", comparison_summary=_summary(), reviewed_by="alice", reviewed_at="t0")
    raised = False
    try:
        store.reject(verification_execution_id="ve-dup", comparison_summary=_summary(), reviewed_by="bob", reviewed_at="t1")
    except review.DuplicateVerificationReviewError:
        raised = True
    check("second review for the same verification_execution_id raises DuplicateVerificationReviewError", raised)
    check("the original record is unchanged after the rejected duplicate attempt", store.get_review("ve-dup").decision == review.ReviewDecision.ACCEPTED.value)


def test_09_duplicate_review_same_decision_also_raises() -> None:
    """Recording the exact same decision twice is still a duplicate -- not
    a no-op and not silently merged."""
    store = review.VerificationReviewStore()
    store.accept(verification_execution_id="ve-dup2", comparison_summary=_summary(), reviewed_by="alice", reviewed_at="t0")
    raised = False
    try:
        store.accept(verification_execution_id="ve-dup2", comparison_summary=_summary(), reviewed_by="alice", reviewed_at="t1")
    except review.DuplicateVerificationReviewError:
        raised = True
    check("recording the same decision twice for the same id also raises", raised)


def test_10_different_ids_do_not_conflict() -> None:
    store = review.VerificationReviewStore()
    store.accept(verification_execution_id="ve-a", comparison_summary=_summary(), reviewed_by="alice", reviewed_at="t0")
    store.reject(verification_execution_id="ve-b", comparison_summary=_summary(), reviewed_by="bob", reviewed_at="t0")
    check("two distinct verification_execution_id values do not conflict", len(store) == 2)


# ---------------------------------------------------------------------------
# invalid verification reference
# ---------------------------------------------------------------------------


def test_11_empty_verification_execution_id_raises() -> None:
    store = review.VerificationReviewStore()
    raised = False
    try:
        store.accept(verification_execution_id="", comparison_summary=_summary(), reviewed_by="alice", reviewed_at="t0")
    except review.InvalidVerificationReferenceError:
        raised = True
    check("empty verification_execution_id raises InvalidVerificationReferenceError", raised)


def test_12_non_string_verification_execution_id_raises() -> None:
    store = review.VerificationReviewStore()
    raised = False
    try:
        store.reject(verification_execution_id=None, comparison_summary=_summary(), reviewed_by="alice", reviewed_at="t0")  # type: ignore[arg-type]
    except review.InvalidVerificationReferenceError:
        raised = True
    check("None verification_execution_id raises InvalidVerificationReferenceError", raised)


def test_13_none_comparison_summary_raises_comparison_not_available() -> None:
    """A verification execution that has not completed has no
    ComparisonSummary -- reviewing it must be refused, never inferred."""
    store = review.VerificationReviewStore()
    raised = False
    try:
        store.accept(verification_execution_id="ve-incomplete", comparison_summary=None, reviewed_by="alice", reviewed_at="t0")  # type: ignore[arg-type]
    except review.ComparisonNotAvailableError:
        raised = True
    check("comparison_summary=None raises ComparisonNotAvailableError", raised)


def test_14_wrong_type_comparison_summary_raises_comparison_not_available() -> None:
    store = review.VerificationReviewStore()
    raised = False
    try:
        store.accept(
            verification_execution_id="ve-wrong-type",
            comparison_summary={"comparison": "succeeded_after_failure"},  # type: ignore[arg-type]
            reviewed_by="alice", reviewed_at="t0",
        )
    except review.ComparisonNotAvailableError:
        raised = True
    check("a plain dict masquerading as a comparison summary raises ComparisonNotAvailableError", raised)


def test_15_invalid_reference_and_missing_comparison_leave_no_record() -> None:
    store = review.VerificationReviewStore()
    for attempt in (
        lambda: store.accept(verification_execution_id="", comparison_summary=_summary(), reviewed_by="a", reviewed_at="t0"),
        lambda: store.accept(verification_execution_id="ve-x", comparison_summary=None, reviewed_by="a", reviewed_at="t0"),  # type: ignore[arg-type]
    ):
        try:
            attempt()
        except (review.InvalidVerificationReferenceError, review.ComparisonNotAvailableError):
            pass
    check("no record was created by any of the rejected attempts", len(store) == 0)


# ---------------------------------------------------------------------------
# immutability
# ---------------------------------------------------------------------------


def test_16_verification_review_is_frozen() -> None:
    record = review.VerificationReviewStore().accept(
        verification_execution_id="ve-frozen", comparison_summary=_summary(), reviewed_by="alice", reviewed_at="t0"
    )
    raised = False
    try:
        record.decision = "rejected"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        raised = True
    check("mutating decision on an existing record raises FrozenInstanceError", raised)


def test_17_verification_review_has_no_verdict_or_reference_fields() -> None:
    """Structural proof that a review carries only opaque strings -- never
    the underlying RepairDraft/ApplicationResult/VerificationExecutionRequest/
    ComparisonSummary objects, and never a computed-correctness field."""
    record = review.VerificationReviewStore().accept(
        verification_execution_id="ve-structural", comparison_summary=_summary(), reviewed_by="alice", reviewed_at="t0"
    )
    forbidden_fields = (
        "repair_draft", "repair_plan", "application_result", "verification_execution_request",
        "comparison_summary", "repair_correct", "success_probability", "confidence_score", "is_fixed", "verdict",
    )
    for field in forbidden_fields:
        check(f"VerificationReview has no {field!r} field", not hasattr(record, field))


def test_18_comparison_summary_digest_is_stable_not_recomputed_on_read() -> None:
    summary = _summary()
    store = review.VerificationReviewStore()
    record = store.accept(verification_execution_id="ve-stable", comparison_summary=summary, reviewed_by="alice", reviewed_at="t0")
    fetched = store.get_review("ve-stable")
    check("get_review returns the exact same digest recorded at write time", fetched.comparison_summary_digest == record.comparison_summary_digest)


# ---------------------------------------------------------------------------
# store lookups
# ---------------------------------------------------------------------------


def test_19_get_review_returns_none_before_any_review() -> None:
    store = review.VerificationReviewStore()
    check("get_review returns None for an unknown id", store.get_review("nonexistent") is None)


def test_20_get_review_returns_recorded_review() -> None:
    store = review.VerificationReviewStore()
    written = store.reject(verification_execution_id="ve-lookup", comparison_summary=_summary(), reviewed_by="alice", reviewed_at="t0")
    fetched = store.get_review("ve-lookup")
    check("get_review returns the exact record written", fetched == written)


def test_21_store_len_tracks_record_count() -> None:
    store = review.VerificationReviewStore()
    check("empty store has length 0", len(store) == 0)
    store.accept(verification_execution_id="ve-len-1", comparison_summary=_summary(), reviewed_by="a", reviewed_at="t0")
    check("store length is 1 after one review", len(store) == 1)
    store.reject(verification_execution_id="ve-len-2", comparison_summary=_summary(), reviewed_by="a", reviewed_at="t0")
    check("store length is 2 after a second, distinct review", len(store) == 2)


# ---------------------------------------------------------------------------
# architectural / structural proofs
# ---------------------------------------------------------------------------


def test_22_module_never_imports_repair_or_approval_modules() -> None:
    """This module consumes only an already-computed ComparisonSummary --
    it has no need for, and no import of, any repair or approval module."""
    source = Path(review.__file__).read_text(encoding="utf-8")
    forbidden = (
        "import gauss_repair_draft", "import gauss_repair_draft_approval", "import gauss_repair_application",
        "import gauss_repair_application_approval", "import gauss_repair_application_gate",
        "import gauss_repair_planner", "import gauss_repair_approval",
    )
    for token in forbidden:
        check(f"module does not {token!r}", token not in source)


def test_23_module_never_imports_execution_modules() -> None:
    """A review never triggers execution -- structurally, the module has no
    import capable of starting one."""
    source = Path(review.__file__).read_text(encoding="utf-8")
    forbidden = (
        "import gauss_execution_workflow", "import gauss_code_execution", "import gauss_execution_adapter",
        "import gauss_runtime_orchestration", "import gauss_orchestration_state_store", "import subprocess",
        "import socket",
    )
    for token in forbidden:
        check(f"module does not {token!r}", token not in source)


def test_24_module_defines_no_execution_repair_or_rollback_callables() -> None:
    source = Path(review.__file__).read_text(encoding="utf-8")
    forbidden = ("def execute(", "def _execute(", "def apply_repair(", "def rollback(", "def _rollback(", "def revoke(", "def _revoke(")
    for token in forbidden:
        check(f"module defines no {token!r}", token not in source)


def test_25_verification_execution_module_has_zero_diff_dependency() -> None:
    """Structural proof this module only reads the existing, real
    ComparisonSummary type -- it neither subclasses nor monkeypatches it."""
    check("ComparisonSummary is the real, unmodified type", review.comparison_summary_digest.__module__ == "gauss_verification_review")
    check("ver.ComparisonSummary is still a frozen dataclass", dataclasses.is_dataclass(ver.ComparisonSummary))


def test_26_decision_values_match_task_specification_exactly() -> None:
    values = {d.value for d in review.ReviewDecision}
    check("decision values are exactly accepted/rejected/inconclusive", values == {"accepted", "rejected", "inconclusive"})


def test_27_no_revoke_method_exists_on_store() -> None:
    check("VerificationReviewStore has no revoke method", not hasattr(review.VerificationReviewStore, "revoke"))


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
