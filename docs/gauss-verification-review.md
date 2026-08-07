# GAUSS Verification Review

## Purpose

`scripts/gauss_verification_review.py` (`v0.65.0`) is a human review layer over Verification Execution. It records what a human concluded after inspecting a completed verification's own evidence (its `ComparisonSummary`). It answers exactly one question: *what did a human decide about this evidence?* It never answers *is the repair correct* — there is no code path anywhere in this module capable of computing `decision` from the evidence itself.

## What This Module Is Not

**Not automatic repair validation or acceptance.** `decision` is always a caller-supplied value. Nothing in this module inspects `ComparisonSummary.comparison`/`observation` and derives `accepted`/`rejected`/`inconclusive` from it.

**Not autonomous retry, repair, planning, or rollback.** This module has no import of `gauss_repair_application.py`, no import of `gauss_repair_planner.py`/`gauss_repair_draft.py`/any approval-store module, and no code path capable of starting an execution, building a repair plan, constructing a draft, or writing to a file.

**Not a mutation of any prior approval or repair state.** Recording a review never touches `RepairApprovalStore`, `DraftApprovalStore`, `ApplicationApprovalStore`, a `RepairDraft`, a `RepairPlan`, or an `ApplicationResult`.

## The Architectural Requirement

**A review references only a completed Verification Execution — never the execution machinery, the repair machinery, or an in-progress verification.**

- `scripts/gauss_verification_execution.py` has zero diff from this milestone.
- `scripts/gauss_repair_application.py` has zero diff from this milestone.
- `scripts/gauss_verification_review.py` imports `gauss_verification_execution` only for the `ComparisonSummary` type (an `isinstance` check, and to compute a content digest over its fields) — never the reverse. Dependency flows strictly one way: review depends on verification, verification never knows review exists.

## Position in the Reasoning Pipeline

```
... -> Repair Application Transaction (gauss_repair_application.py, v0.62.0)
    -> Verification Execution (gauss_verification_execution.py, v0.64.0)
    -> Verification Review    (this module, v0.65.0)
    -> (future, not implemented: anything that reads a review's own decision)
```

## VerificationReview

Immutable. Fields: `review_id`, `verification_execution_id`, `comparison_summary_digest`, `decision`, `notes`, `reviewed_at`, `reviewed_by`, `boundary`.

**Holds no field capable of referencing the underlying objects.** There is nowhere on `VerificationReview` for a `RepairDraft`, `RepairPlan`, `ApplicationResult`, `VerificationExecutionRequest`, or `ComparisonSummary` object to live — only two opaque strings, `verification_execution_id` and `comparison_summary_digest`. This is what makes "references only a completed Verification Execution" structurally true: a verification that has not finished executing has no `ComparisonSummary` to digest, so there is nothing for `build`-time validation to accept.

### `comparison_summary_digest`

`comparison_summary_digest(summary) -> str` is a deterministic SHA-256 fingerprint over all five of `ComparisonSummary`'s own fields (`original_outcome`, `verification_outcome`, `same_outcome`, `comparison`, `observation`), using the repository's standard canonical-JSON pattern. `ComparisonSummary` has no identity field of its own, so — unlike `repair_draft_digest` — nothing is excluded from the hash.

### Decision values

```python
class ReviewDecision(enum.Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"
```

Exposed as three explicit `VerificationReviewStore` methods — `accept(...)`, `reject(...)`, `mark_inconclusive(...)` — mirroring `ApplicationApprovalStore.approve(...)`/`.decline(...)`. An invalid decision value is a parsing error at the CLI boundary, never a value this module's own API can accept.

### No revoke

Unlike every prior approval-store layer in this repository (`RepairApprovalStore`, `DraftApprovalStore`, `ApplicationApprovalStore`), `VerificationReviewStore` has **no revoke operation**. A `VerificationReview` is write-once per `verification_execution_id`: a second review attempt for the same ID always raises `DuplicateVerificationReviewError`, regardless of whether the decision differs. This is a deliberate scope decision — see `planning/v0.65.0-verification-review.md` for the full reasoning.

### Boundary statement

A single, fixed, decision-invariant string, present on every record:

```
This review records a human conclusion about the verification evidence. The system is not
determining whether the repair is correct. No execution, planning, repair, rollback, or
approval mutation has occurred as a result of this review.
```

## Errors

- `InvalidVerificationReferenceError` — an empty or non-string `verification_execution_id`.
- `ComparisonNotAvailableError` — `comparison_summary` is not a genuine `ComparisonSummary` instance (i.e. the referenced verification has not completed).
- `DuplicateVerificationReviewError` — a review already exists for the supplied `verification_execution_id`.

## CLI Usage

```
gauss-mvp> review-verification --decision accepted --notes "Repair confirmed working" --reviewed-by alice
This review records a human conclusion.
The system is not determining whether the repair is correct.
review_id: ...
verification_execution_id: ...
comparison_summary_digest: ...
decision: accepted
notes: Repair confirmed working
reviewed_by: alice
reviewed_at: ...
boundary: This review records a human conclusion about the verification evidence. ...

gauss-mvp> show-verification-review
This review records a human conclusion.
The system is not determining whether the repair is correct.
review_id: ...
...
```

`review-verification` requires a completed verification execution — the same `confirm`/`execute` sequence `verify-repair` already requires, exactly as `show-verification-request`'s own comparison output does. Attempting to review before `verify-repair`, or before `confirm`/`execute` have completed, is refused with a clear error rather than inferred or silently skipped. `reset` clears the review store along with the rest of the verification-layer state.

## Limitations

- No revoke — a mis-recorded review cannot be corrected within this module; a fresh `gauss-mvp> reset` (which clears the entire session, not just the review) is the only way to record a different decision.
- Process-local only — cleared by `reset`, not durable, not shared across processes.
- No consumer reads a recorded review's `decision` anywhere in this repository yet — that is future, unauthorized work.
- `notes`/`reviewed_by` are free-text, caller-supplied, and never validated against any identity system.
