"""Deterministic, process-local repair-draft approval recording.

Position in the reasoning pipeline:

    ... -> Repair Planning (gauss_repair_planner.py, v0.56.0)
        -> Approval (gauss_repair_approval.py, v0.57.0 -- strategy-level)
        -> Repair Draft (gauss_repair_draft.py, v0.59.0)
        -> Repair Draft Approval (this module, v0.60.0)
        -> (Repair Application, future, not implemented)

This module answers exactly one question, one layer below where
`gauss_repair_approval.py` answers it: *did a human explicitly accept,
decline, or later revoke a decision about a specific, unmodified
`RepairDraft`?* It never answers "should this draft be applied" and it
never performs any application itself -- there is no code path in this
module capable of editing a file, generating a patch, or invoking a repair.

A draft-approval decision is bound to `gauss_repair_draft.repair_draft_digest(...)`
-- and to that alone. Per this milestone's own explicit design constraint,
the binding is never widened to `repair_plan_digest`, a workspace ID, a
relative path, or an execution request ID -- even though a `RepairDraft`
carries all of those, none of them is a lookup or matching key here. This is
already the strictest possible binding: `repair_draft_digest` is computed
over the draft's *entire* content (including its own embedded
`repair_plan_digest` and source identity), so any change to any of those
fields already changes the digest a decision is keyed on.

Pure and deterministic except for the one piece of state this module's own
job requires: which digests have a recorded decision, and what that decision
currently is. `DraftApprovalStore` is an ordinary in-memory dict wrapped in a
small class -- it is NOT a durable store, exactly as `RepairApprovalStore`
(`v0.57.0`) is not: created fresh per process, never written to disk,
discarded when the process exits or when the caller explicitly clears it.

This module never launches GAUSS, calls an execution helper, mutates
workspace state, edits source code, reads or writes files, accesses the
network, or calls an LLM -- it has no import, and no code path, capable of
any of those things. It consumes only a `gauss_repair_draft.RepairDraft`
object and `gauss_repair_draft.repair_draft_digest(...)` -- nothing else. It
does not import `gauss_repair_planner.py` or `gauss_repair_approval.py`.

Unlike `gauss_repair_approval.py`'s `RepairApprovalStore.revoke(...)` (which
deletes a record outright), `revoke(...)` here transitions an existing
APPROVED/DECLINED record *in place* to REVOKED, preserving it rather than
erasing it -- a small, deliberate evolution for this one layer, chosen so a
revoked decision remains visible as history rather than disappearing without
a trace. A REVOKED record does not block a fresh `approve`/`decline` call
for the same digest; only an active (APPROVED or DECLINED) record does.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import gauss_repair_draft as repair_draft_mod


class DraftApprovalDecision(enum.Enum):
    APPROVED = "approved"
    DECLINED = "declined"
    REVOKED = "revoked"


class DraftApprovalConflictError(Exception):
    """Raised when attempting to record a decision for a draft digest that
    already has an *active* (approved or declined) decision. A decision is
    never silently overwritten -- the caller must explicitly call
    `DraftApprovalStore.revoke(...)` first. Also covers the duplicate case
    (recording the exact same decision twice)."""


#: A fixed, always-present disclosure -- never conditional, never reworded
#: per decision, so it cannot be accidentally omitted from any record.
DRAFT_APPROVAL_BOUNDARY_STATEMENT = (
    "The repair draft has been approved. No files have been modified. No repair has been applied. No "
    "execution has occurred. Repair Application remains unavailable."
)

#: The disclosure shown for a declined or revoked decision -- distinct
#: wording since "has been approved" would be false for either.
DRAFT_DECLINE_BOUNDARY_STATEMENT = (
    "This repair draft has not been approved. No files have been modified. No repair has been applied. No "
    "execution has occurred. Repair Application remains unavailable."
)


@dataclass(frozen=True)
class DraftApprovalRecord:
    #: One of `DraftApprovalDecision`'s values.
    decision: str
    #: The exact `repair_draft_digest(...)` this decision is bound to -- the
    #: sole binding between a decision and a specific draft. Never
    #: `repair_plan_digest`, a workspace ID, a relative path, or an
    #: execution request ID (see module docstring).
    draft_digest: str
    #: Caller-supplied clock value (e.g. the adapter's own injectable
    #: `clock()`), never computed internally -- mirrors
    #: `gauss_repair_approval.ApprovalRecord.recorded_at`.
    recorded_at: str
    #: The draft's own opaque instance identifier -- informational only,
    #: never used for lookup or matching (that is `draft_digest` alone).
    repair_draft_id: str
    #: Always `False` -- an approval never implies safe application. Fixed
    #: on the record itself (not just documented) so a caller can never
    #: mistake a recorded decision for an application capability.
    safe_to_apply: bool
    #: Always `False` -- an approval never implies draft *preparation*
    #: either (there is no further, derived-draft-generation capability).
    safe_to_prepare_draft: bool
    approval_boundary: str


class DraftApprovalStore:
    """In-memory only -- see module docstring. Not thread-safe (matches this
    repository's existing single-threaded adapter convention); not shared
    across processes; never persisted."""

    def __init__(self) -> None:
        self._records: dict[str, DraftApprovalRecord] = {}

    def _boundary_for(self, decision: DraftApprovalDecision) -> str:
        return DRAFT_APPROVAL_BOUNDARY_STATEMENT if decision == DraftApprovalDecision.APPROVED else DRAFT_DECLINE_BOUNDARY_STATEMENT

    def _record_decision(
        self, draft: "repair_draft_mod.RepairDraft", decision: DraftApprovalDecision, *, recorded_at: str
    ) -> DraftApprovalRecord:
        digest = repair_draft_mod.repair_draft_digest(draft)
        existing = self._records.get(digest)
        if existing is not None and existing.decision != DraftApprovalDecision.REVOKED.value:
            raise DraftApprovalConflictError(
                f"an active decision ({existing.decision!r}) is already recorded for draft_digest {digest!r}; "
                "call revoke(draft) first if you intend to replace it."
            )
        record = DraftApprovalRecord(
            decision=decision.value,
            draft_digest=digest,
            recorded_at=recorded_at,
            repair_draft_id=draft.repair_draft_id,
            safe_to_apply=False,
            safe_to_prepare_draft=False,
            approval_boundary=self._boundary_for(decision),
        )
        self._records[digest] = record
        return record

    def approve(self, draft: "repair_draft_mod.RepairDraft", *, recorded_at: str) -> DraftApprovalRecord:
        return self._record_decision(draft, DraftApprovalDecision.APPROVED, recorded_at=recorded_at)

    def decline(self, draft: "repair_draft_mod.RepairDraft", *, recorded_at: str) -> DraftApprovalRecord:
        return self._record_decision(draft, DraftApprovalDecision.DECLINED, recorded_at=recorded_at)

    def get_decision(self, draft: "repair_draft_mod.RepairDraft") -> DraftApprovalRecord | None:
        """Looks up by the draft's *current* digest -- a draft that has
        changed since a decision was recorded will simply not be found,
        which is how staleness is enforced (mirrors
        `gauss_repair_approval.RepairApprovalStore.get_decision`)."""
        return self._records.get(repair_draft_mod.repair_draft_digest(draft))

    def get_decision_for_digest(self, draft_digest: str) -> DraftApprovalRecord | None:
        return self._records.get(draft_digest)

    def revoke(self, draft: "repair_draft_mod.RepairDraft", *, recorded_at: str) -> bool:
        """Transitions an existing *active* (approved or declined) record
        for this draft's current digest to REVOKED, in place -- the record
        is preserved as history, not deleted. Returns `True` if an active
        record was revoked, `False` if none existed or it was already
        revoked. The only sanctioned way to free a digest for a fresh
        `approve`/`decline` call."""
        digest = repair_draft_mod.repair_draft_digest(draft)
        existing = self._records.get(digest)
        if existing is None or existing.decision == DraftApprovalDecision.REVOKED.value:
            return False
        self._records[digest] = DraftApprovalRecord(
            decision=DraftApprovalDecision.REVOKED.value,
            draft_digest=digest,
            recorded_at=recorded_at,
            repair_draft_id=draft.repair_draft_id,
            safe_to_apply=False,
            safe_to_prepare_draft=False,
            approval_boundary=self._boundary_for(DraftApprovalDecision.REVOKED),
        )
        return True

    def __len__(self) -> int:
        return len(self._records)
