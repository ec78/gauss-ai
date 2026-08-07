"""Verification Review -- a human review layer over Verification Execution.

Position in the reasoning pipeline:

    ... -> Repair Application Transaction (gauss_repair_application.py, v0.62.0)
        -> Verification Execution (gauss_verification_execution.py, v0.64.0)
        -> Verification Review (this module, v0.65.0)
        -> (future, not implemented: anything that reads a review's own decision)

The review records what a human concluded after inspecting the evidence a
completed verification execution produced. It never infers that conclusion
automatically -- there is no code path anywhere in this module capable of
computing `decision` from a `ComparisonSummary`'s own fields. `decision` is
always a caller-supplied value, exactly as `recorded_at`/`reviewed_by`/
`notes` are.

This is not automatic repair validation, automatic repair acceptance,
automatic rollback, automatic planning, or a scoring/ranking system. It does
not call `gauss_repair_application.py` at all, and does not call
`gauss_verification_execution.py`'s own `propose_verification_execution(...)`/
`compare_execution_outcomes(...)` -- the caller supplies an already-computed
`ComparisonSummary`; this module never computes one itself. It does not
mutate any approval store, does not mutate `RepairDraft`/`RepairPlan` state,
and never triggers execution, planning, or repair of any kind.

`gauss_verification_execution.py` and `gauss_repair_application.py` both
have zero diff from this milestone. This module imports
`gauss_verification_execution` (for the `ComparisonSummary` type, used only
in an `isinstance` check and to compute a content digest over its fields) --
never the reverse. This preserves the same one-way layering this repository
has used at every prior approval boundary: a layer may depend on the thing
it reviews, but the reviewed thing never knows the reviewing layer exists.

`VerificationReview` deliberately holds no field capable of referencing a
`RepairDraft`, `RepairPlan`, `ApplicationResult`,
`VerificationExecutionRequest`, or `ComparisonSummary` object directly --
only two opaque strings (`verification_execution_id`,
`comparison_summary_digest`). This is what makes "the review references
only a completed Verification Execution" structurally true rather than
merely conventionally true: a verification that has not finished executing
has no `ComparisonSummary` to pass in at all, so there is nowhere on this
type for an in-progress or unverified reference to live.

Unlike `RepairApprovalStore` (v0.57.0), `DraftApprovalStore` (v0.60.0), and
`ApplicationApprovalStore` (v0.61.0), `VerificationReviewStore` supports NO
revoke operation. This is a deliberate scope decision: this milestone's own
task specification lists exactly three decision values (accepted/rejected/
inconclusive), never "revoked", and never mentions revocation. A
`VerificationReview` is therefore write-once per `verification_execution_id`
-- a second review attempt for the same ID always raises
`DuplicateVerificationReviewError`. See
`planning/v0.65.0-verification-review.md` for the full reasoning.

Never implements: automatic decision inference, revocation, execution,
planning, repair, rollback, approval mutation, or durable/cross-process
storage.
"""

from __future__ import annotations

import enum
import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Callable

import gauss_verification_execution as verification_mod


class InvalidVerificationReferenceError(Exception):
    """Raised when `verification_execution_id` is not a non-empty string."""


class ComparisonNotAvailableError(Exception):
    """Raised when `comparison_summary` is not a genuine
    `verification_mod.ComparisonSummary` instance -- structurally, this is
    how "only a completed Verification Execution can be reviewed" is
    enforced: a verification that has not finished executing has no
    `ComparisonSummary` to supply at all."""


class DuplicateVerificationReviewError(Exception):
    """Raised when a review already exists for the supplied
    `verification_execution_id`. There is no revoke operation in this
    module (see module docstring) -- a recorded review can never be
    replaced from within this module."""


class ReviewDecision(enum.Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


#: Fixed, decision-invariant -- never reworded per decision, so it cannot be
#: accidentally omitted or softened for any particular outcome.
VERIFICATION_REVIEW_BOUNDARY = (
    "This review records a human conclusion about the verification evidence. "
    "The system is not determining whether the repair is correct. No execution, "
    "planning, repair, rollback, or approval mutation has occurred as a result "
    "of this review."
)


def comparison_summary_digest(summary: "verification_mod.ComparisonSummary") -> str:
    """Deterministic SHA-256 fingerprint over a `ComparisonSummary`'s full
    content, in fixed field order. Unlike `repair_draft_digest`, there is no
    instance-identity field to exclude -- `ComparisonSummary` has none."""
    canonical = {
        "original_outcome": summary.original_outcome,
        "verification_outcome": summary.verification_outcome,
        "same_outcome": summary.same_outcome,
        "comparison": summary.comparison,
        "observation": summary.observation,
    }
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VerificationReview:
    """Immutable. References only an already-completed Verification
    Execution -- via two opaque strings, never the underlying objects
    themselves. There is no field here capable of holding a `RepairDraft`,
    `RepairPlan`, `ApplicationResult`, `VerificationExecutionRequest`, or
    `ComparisonSummary`."""

    review_id: str
    verification_execution_id: str
    comparison_summary_digest: str
    #: One of `ReviewDecision`'s values.
    decision: str
    notes: str
    #: Caller-supplied clock value, never computed internally -- mirrors
    #: every other layer's `recorded_at`/`created_at` convention.
    reviewed_at: str
    reviewed_by: str
    boundary: str


class VerificationReviewStore:
    """In-memory only, process-local, not thread-safe, never persisted --
    the same discipline `ApplicationApprovalStore` and its predecessors
    already established. One record per `verification_execution_id`; there
    is no revoke, so a digest cannot become "stale" the way a draft's own
    digest can -- the evidence a review was written against never changes
    underneath it."""

    def __init__(self) -> None:
        self._records: dict[str, VerificationReview] = {}

    def _record(
        self,
        *,
        verification_execution_id: str,
        comparison_summary: "verification_mod.ComparisonSummary",
        decision: ReviewDecision,
        notes: str,
        reviewed_by: str,
        reviewed_at: str,
        id_factory: Callable[[], str],
    ) -> VerificationReview:
        if not isinstance(verification_execution_id, str) or not verification_execution_id:
            raise InvalidVerificationReferenceError(
                "verification_execution_id must be a non-empty string identifying a completed "
                "Verification Execution."
            )
        if not isinstance(comparison_summary, verification_mod.ComparisonSummary):
            raise ComparisonNotAvailableError(
                f"a real ComparisonSummary is required to review verification_execution_id "
                f"{verification_execution_id!r} -- the Verification Execution has not completed "
                "(no comparison evidence exists yet)."
            )
        existing = self._records.get(verification_execution_id)
        if existing is not None:
            raise DuplicateVerificationReviewError(
                f"a review (decision={existing.decision!r}) already exists for "
                f"verification_execution_id {verification_execution_id!r}; this module supports no "
                "revoke or replace operation."
            )
        record = VerificationReview(
            review_id=id_factory(),
            verification_execution_id=verification_execution_id,
            comparison_summary_digest=comparison_summary_digest(comparison_summary),
            decision=decision.value,
            notes=notes,
            reviewed_at=reviewed_at,
            reviewed_by=reviewed_by,
            boundary=VERIFICATION_REVIEW_BOUNDARY,
        )
        self._records[verification_execution_id] = record
        return record

    def accept(
        self,
        *,
        verification_execution_id: str,
        comparison_summary: "verification_mod.ComparisonSummary",
        reviewed_by: str,
        reviewed_at: str,
        notes: str = "",
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> VerificationReview:
        return self._record(
            verification_execution_id=verification_execution_id,
            comparison_summary=comparison_summary,
            decision=ReviewDecision.ACCEPTED,
            notes=notes,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
            id_factory=id_factory,
        )

    def reject(
        self,
        *,
        verification_execution_id: str,
        comparison_summary: "verification_mod.ComparisonSummary",
        reviewed_by: str,
        reviewed_at: str,
        notes: str = "",
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> VerificationReview:
        return self._record(
            verification_execution_id=verification_execution_id,
            comparison_summary=comparison_summary,
            decision=ReviewDecision.REJECTED,
            notes=notes,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
            id_factory=id_factory,
        )

    def mark_inconclusive(
        self,
        *,
        verification_execution_id: str,
        comparison_summary: "verification_mod.ComparisonSummary",
        reviewed_by: str,
        reviewed_at: str,
        notes: str = "",
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> VerificationReview:
        return self._record(
            verification_execution_id=verification_execution_id,
            comparison_summary=comparison_summary,
            decision=ReviewDecision.INCONCLUSIVE,
            notes=notes,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
            id_factory=id_factory,
        )

    def get_review(self, verification_execution_id: str) -> VerificationReview | None:
        return self._records.get(verification_execution_id)

    def __len__(self) -> int:
        return len(self._records)
