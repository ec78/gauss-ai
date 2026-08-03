"""Deterministic, process-local repair-plan approval recording.

Position in the reasoning pipeline:

    Execution evidence -> Interpretation -> Verified error knowledge
        -> Diagnosis -> Repair Planning (gauss_repair_planner.py)
        -> Approval (this module)
        -> (Repair Application, future, not implemented)

This module answers exactly one question: *did a human explicitly accept or
decline a specific, unmodified repair plan?* It never answers "should this
plan be applied" (no such judgment is made here) and it never performs any
application itself -- there is no code path in this module capable of
editing a file, preparing a draft, or invoking a repair.

An approval decision is bound to `gauss_repair_planner.repair_plan_digest(...)`
-- a SHA-256 fingerprint over a `RepairPlan`'s full identifying content. If a
plan changes in any way (different evidence, different source context,
different strategy text), its digest changes, and any prior decision recorded
under the old digest simply does not match the new one -- there is no
separate "invalidation" step; staleness falls directly out of the hash-bound
design, the same way a stale `request_hash` already fails to match a changed
execution proposal elsewhere in this repository.

Pure and deterministic except for the one piece of state this module's own
job requires: which digests have a recorded decision. `RepairApprovalStore`
is an ordinary in-memory dict wrapped in a small class -- it is NOT a durable
store (contrast `gauss_orchestration_state_store.OrchestrationStateStore`,
which is SQLite-backed and persists across process restarts). A
`RepairApprovalStore` is exactly as durable as every other piece of adapter
session state today (e.g. `InteractiveMvpAdapter.last_result`): created
fresh per process, never written to disk, discarded when the process exits
or when the caller explicitly clears it.

This module never launches GAUSS, calls an execution helper, mutates
workspace state, edits source code, reads or writes files, accesses the
network, or calls an LLM -- it has no import, and no code path, capable of
any of those things. It consumes only a `gauss_repair_planner.RepairPlan`
object; it does not duplicate repair-planning logic (it calls
`gauss_repair_planner.repair_plan_digest(...)`, the same function
`gauss_repair_planner.py` itself defines, rather than re-deriving a digest a
second way).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import gauss_repair_planner as repair_planner


class ApprovalDecision(enum.Enum):
    APPROVED = "approved"
    DECLINED = "declined"


class ApprovalConflictError(Exception):
    """Raised when attempting to record a decision for a plan digest that
    already has one. A decision is never silently overwritten -- the caller
    must explicitly call `RepairApprovalStore.revoke(...)` first."""


#: A fixed, always-present disclosure -- never conditional, never reworded
#: per decision, so it cannot be accidentally omitted from any record.
APPROVAL_BOUNDARY_STATEMENT = (
    "This records an explicit human decision about a specific repair plan. It does not apply, patch, or "
    "prepare a draft of any change. No code was modified. No file was written. GAUSS was not rerun."
)


@dataclass(frozen=True)
class ApprovalRecord:
    #: One of `ApprovalDecision`'s values.
    decision: str
    #: The exact `repair_plan_digest(...)` this decision was recorded
    #: against -- the sole binding between a decision and a specific plan.
    plan_digest: str
    #: Caller-supplied clock value (e.g. the adapter's own injectable
    #: `clock()`), never computed internally -- keeps this module pure and
    #: deterministic rather than silently depending on wall-clock time.
    recorded_at: str
    source_error_code: str | None
    source_error_category: str | None
    repair_status: str
    #: Always `False` -- an approval never implies safe application. Fixed
    #: on the record itself (not just documented) so a caller can never
    #: mistake a recorded decision for an application capability.
    safe_to_apply: bool
    #: Always `False` -- an approval never implies draft preparation either;
    #: no draft-generation capability exists anywhere in this repository.
    safe_to_prepare_draft: bool
    approval_boundary: str


class RepairApprovalStore:
    """In-memory only -- see module docstring. Not thread-safe (matches this
    repository's existing single-threaded adapter convention); not shared
    across processes; never persisted."""

    def __init__(self) -> None:
        self._records: dict[str, ApprovalRecord] = {}

    def _record_decision(self, plan: "repair_planner.RepairPlan", decision: ApprovalDecision, *, recorded_at: str) -> ApprovalRecord:
        digest = repair_planner.repair_plan_digest(plan)
        if digest in self._records:
            raise ApprovalConflictError(
                f"a decision ({self._records[digest].decision!r}) is already recorded for plan_digest "
                f"{digest!r}; call revoke(plan) first if you intend to replace it."
            )
        record = ApprovalRecord(
            decision=decision.value,
            plan_digest=digest,
            recorded_at=recorded_at,
            source_error_code=plan.source_error_code,
            source_error_category=plan.source_error_category,
            repair_status=plan.repair_status,
            safe_to_apply=False,
            safe_to_prepare_draft=False,
            approval_boundary=APPROVAL_BOUNDARY_STATEMENT,
        )
        self._records[digest] = record
        return record

    def approve(self, plan: "repair_planner.RepairPlan", *, recorded_at: str) -> ApprovalRecord:
        return self._record_decision(plan, ApprovalDecision.APPROVED, recorded_at=recorded_at)

    def decline(self, plan: "repair_planner.RepairPlan", *, recorded_at: str) -> ApprovalRecord:
        return self._record_decision(plan, ApprovalDecision.DECLINED, recorded_at=recorded_at)

    def get_decision(self, plan: "repair_planner.RepairPlan") -> ApprovalRecord | None:
        """Looks up by the plan's *current* digest -- a plan that has
        changed since a decision was recorded will simply not be found,
        which is how staleness is enforced (see module docstring)."""
        return self._records.get(repair_planner.repair_plan_digest(plan))

    def get_decision_for_digest(self, plan_digest: str) -> ApprovalRecord | None:
        return self._records.get(plan_digest)

    def revoke(self, plan: "repair_planner.RepairPlan") -> bool:
        """Removes any recorded decision for this plan's current digest.
        Returns `True` if a record was removed, `False` if none existed.
        The only sanctioned way to replace an existing decision."""
        return self._records.pop(repair_planner.repair_plan_digest(plan), None) is not None

    def __len__(self) -> int:
        return len(self._records)
