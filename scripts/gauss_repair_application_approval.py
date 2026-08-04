"""Deterministic, process-local repair-application approval recording.

Position in the reasoning pipeline:

    ... -> Repair Planning (gauss_repair_planner.py, v0.56.0)
        -> Approval (gauss_repair_approval.py, v0.57.0 -- strategy-level)
        -> Repair Draft (gauss_repair_draft.py, v0.59.0)
        -> Repair Draft Approval (gauss_repair_draft_approval.py, v0.60.0)
        -> Repair Application Approval (this module, v0.61.0)
        -> (Repair Application Gate check, gauss_repair_application_gate.py, v0.61.0)
        -> (Repair Application transaction, future, not implemented)

This module answers exactly one question, one layer below where
`gauss_repair_draft_approval.py` answers it: *did a human explicitly accept,
decline, or later revoke a decision about applying a specific, unmodified
`RepairDraft` to its exact, freshly-reverified source state?* It never
answers "is it now safe to apply" (that is `gauss_repair_application_gate.py`'s
job, and even that module never claims a passing gate authorizes an actual
write) and it never performs any application itself -- there is no code path
in this module capable of editing a file, generating a patch, or invoking a
repair.

An application-approval decision is bound to
`gauss_repair_draft.repair_draft_digest(...)` -- the same digest draft
approval itself binds to, not a new, independently-computed "application
digest." Per `planning/v0.58.0-repair-application-safety-design.md` Section
5, there is no separate "application content" to fingerprint independently
of the draft being applied; a future `repair_application_id` (an opaque
per-attempt identifier, assigned only once an actual application transaction
exists) is out of scope here.

Pure and deterministic except for the one piece of state this module's own
job requires: which digests have a recorded decision, and what that decision
currently is. `ApplicationApprovalStore` is an ordinary in-memory dict
wrapped in a small class -- it is NOT a durable store, exactly as
`RepairApprovalStore` (`v0.57.0`) and `DraftApprovalStore` (`v0.60.0`) are
not: created fresh per process, never written to disk, discarded when the
process exits or when the caller explicitly clears it.

This module never launches GAUSS, calls an execution helper, mutates
workspace state, edits source code, reads or writes files, accesses the
network, or calls an LLM -- it has no import, and no code path, capable of
any of those things. It consumes only a `gauss_repair_draft.RepairDraft`
object and `gauss_repair_draft.repair_draft_digest(...)` -- nothing else. It
does not import `gauss_repair_planner.py`, `gauss_repair_approval.py`, or
`gauss_repair_draft_approval.py`.

`revoke(...)` transitions an existing APPROVED/DECLINED record *in place* to
REVOKED, preserving it rather than erasing it -- the same discipline
`DraftApprovalStore.revoke(...)` (`v0.60.0`) already established, chosen
again here because this milestone's own task specification lists `revoked`
as a first-class decision value. A REVOKED record does not block a fresh
`approve`/`decline` call for the same digest; only an active (APPROVED or
DECLINED) record does.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import gauss_repair_draft as repair_draft_mod


class ApplicationApprovalDecision(enum.Enum):
    APPROVED = "approved"
    DECLINED = "declined"
    REVOKED = "revoked"


class ApplicationApprovalConflictError(Exception):
    """Raised when attempting to record a decision for a draft digest that
    already has an *active* (approved or declined) application-approval
    decision. A decision is never silently overwritten -- the caller must
    explicitly call `ApplicationApprovalStore.revoke(...)` first. Also
    covers the duplicate case (recording the exact same decision twice)."""


#: A fixed, always-present disclosure -- never conditional, never reworded
#: per decision, so it cannot be accidentally omitted from any record.
APPLICATION_APPROVAL_BOUNDARY_STATEMENT = (
    "The repair application has been approved. No files have been modified. No repair has been applied. No "
    "execution has occurred. The application transaction itself remains unimplemented -- approving this "
    "authorization records a decision only."
)

#: The disclosure shown for a declined or revoked decision -- distinct
#: wording since "has been approved" would be false for either.
APPLICATION_DECLINE_BOUNDARY_STATEMENT = (
    "This repair application has not been approved. No files have been modified. No repair has been applied. "
    "No execution has occurred. The application transaction itself remains unimplemented."
)


@dataclass(frozen=True)
class ApplicationApprovalRecord:
    #: One of `ApplicationApprovalDecision`'s values.
    decision: str
    #: The exact `repair_draft_digest(...)` this decision is bound to -- the
    #: sole binding between a decision and a specific draft. Never a
    #: separately-computed "application digest" (see module docstring).
    draft_digest: str
    #: Caller-supplied clock value (e.g. the adapter's own injectable
    #: `clock()`), never computed internally -- mirrors
    #: `gauss_repair_draft_approval.DraftApprovalRecord.recorded_at`.
    recorded_at: str
    #: The draft's own opaque instance identifier -- informational only,
    #: never used for lookup or matching (that is `draft_digest` alone).
    repair_draft_id: str
    #: Always `False` -- an application approval never implies a safe or
    #: performed application. Fixed on the record itself (not just
    #: documented) so a caller can never mistake a recorded decision for an
    #: application capability.
    safe_to_apply: bool
    #: Always `False` -- an application approval never implies draft
    #: preparation either.
    safe_to_prepare_draft: bool
    approval_boundary: str


class ApplicationApprovalStore:
    """In-memory only -- see module docstring. Not thread-safe (matches this
    repository's existing single-threaded adapter convention); not shared
    across processes; never persisted."""

    def __init__(self) -> None:
        self._records: dict[str, ApplicationApprovalRecord] = {}

    def _boundary_for(self, decision: ApplicationApprovalDecision) -> str:
        return (
            APPLICATION_APPROVAL_BOUNDARY_STATEMENT
            if decision == ApplicationApprovalDecision.APPROVED
            else APPLICATION_DECLINE_BOUNDARY_STATEMENT
        )

    def _record_decision(
        self, draft: "repair_draft_mod.RepairDraft", decision: ApplicationApprovalDecision, *, recorded_at: str
    ) -> ApplicationApprovalRecord:
        digest = repair_draft_mod.repair_draft_digest(draft)
        existing = self._records.get(digest)
        if existing is not None and existing.decision != ApplicationApprovalDecision.REVOKED.value:
            raise ApplicationApprovalConflictError(
                f"an active decision ({existing.decision!r}) is already recorded for draft_digest {digest!r}; "
                "call revoke(draft) first if you intend to replace it."
            )
        record = ApplicationApprovalRecord(
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

    def approve(self, draft: "repair_draft_mod.RepairDraft", *, recorded_at: str) -> ApplicationApprovalRecord:
        return self._record_decision(draft, ApplicationApprovalDecision.APPROVED, recorded_at=recorded_at)

    def decline(self, draft: "repair_draft_mod.RepairDraft", *, recorded_at: str) -> ApplicationApprovalRecord:
        return self._record_decision(draft, ApplicationApprovalDecision.DECLINED, recorded_at=recorded_at)

    def get_decision(self, draft: "repair_draft_mod.RepairDraft") -> ApplicationApprovalRecord | None:
        """Looks up by the draft's *current* digest -- a draft that has
        changed since a decision was recorded will simply not be found,
        which is how staleness is enforced (mirrors
        `gauss_repair_draft_approval.DraftApprovalStore.get_decision`)."""
        return self._records.get(repair_draft_mod.repair_draft_digest(draft))

    def get_decision_for_digest(self, draft_digest: str) -> ApplicationApprovalRecord | None:
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
        if existing is None or existing.decision == ApplicationApprovalDecision.REVOKED.value:
            return False
        self._records[digest] = ApplicationApprovalRecord(
            decision=ApplicationApprovalDecision.REVOKED.value,
            draft_digest=digest,
            recorded_at=recorded_at,
            repair_draft_id=draft.repair_draft_id,
            safe_to_apply=False,
            safe_to_prepare_draft=False,
            approval_boundary=self._boundary_for(ApplicationApprovalDecision.REVOKED),
        )
        return True

    def __len__(self) -> int:
        return len(self._records)
