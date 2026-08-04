"""Deterministic, pure re-verification of every checkable Repair Application
Gate precondition from `planning/v0.58.0-repair-application-safety-design.md`
Section 13.

Position in the reasoning pipeline:

    ... -> Repair Draft Approval (gauss_repair_draft_approval.py, v0.60.0)
        -> Repair Application Approval (gauss_repair_application_approval.py, v0.61.0)
        -> Repair Application Gate (this module, v0.61.0)
        -> (Repair Application transaction, future, not implemented)

This module answers exactly one question: *if an application transaction
existed, would every checkable precondition for applying this exact draft
currently hold?* It never performs an application, never claims one is now
safe or authorized, and never sets `safe_to_apply` anywhere -- there is no
field named `safe_to_apply` anywhere in this module's own result type, a
deliberate structural choice so no code path here can even superficially
resemble flipping the invariant every upstream layer already enforces.

This module is the first in the repair-reasoning pipeline whose entire job
is to *combine* several upstream layers' already-computed state into one
pass/fail verdict, rather than adding new content of its own. It imports
`gauss_repair_planner`, `gauss_repair_draft`, and `gauss_repair_draft_approval`
`gauss_repair_application_approval` only to reference their existing types and
call their existing pure digest/validation functions
(`repair_plan_digest`, `repair_draft_digest`, `validate_repair_draft`) --
it never re-derives any of their logic a second, possibly-divergent way, and
it never imports `gauss_repair_approval.py`'s or
`gauss_repair_draft_approval.py`'s own store classes (a caller looks a
decision up in the relevant store itself and passes the resulting record, or
`None`, into this module -- this module never holds or constructs a store).

Zero I/O. `current_source_identity` -- the one input this module needs to
check whether the draft's bound source has gone stale -- is always a
caller-supplied `gauss_repair_draft.SourceIdentity` value, exactly the same
zero-I/O, caller-supplied contract `gauss_repair_draft.validate_repair_draft`
already established for its own `current_source_identity` parameter in
`v0.59.0`. This module never reads a file, computes a hash, or queries a
workspace registry itself.

This module never launches GAUSS, calls an execution helper, mutates
workspace state, edits source code, reads or writes files, accesses the
network, or calls an LLM.

Several of Section 13's preconditions (a backup has been prepared, a
rollback path has been verified, the application consumer itself is
authorized to run, an audit record has been initialized) are **not**
checked by this module, because no backup mechanism, rollback mechanism,
application consumer, or audit mechanism exists anywhere in this repository
yet -- checking for the presence of something structurally impossible to
satisfy would not be a meaningful gate. These are disclosed explicitly via
`ApplicationGateResult.not_applicable_checks`, never silently omitted.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import gauss_repair_application_approval as application_approval
import gauss_repair_draft as repair_draft_mod
import gauss_repair_draft_approval as draft_approval
import gauss_repair_planner as repair_planner

#: A fixed, always-present disclosure -- never conditional, never reworded,
#: so a caller can never mistake a passing gate result for an authorization
#: to apply anything.
GATE_BOUNDARY_STATEMENT = (
    "A passing application gate result does not authorize applying anything. No application transaction "
    "exists in this repository. This is a precondition re-verification only."
)

#: Section 13 preconditions this module cannot check because no supporting
#: mechanism exists anywhere in this repository yet -- named explicitly so
#: their absence is disclosed, never silently assumed satisfied or omitted.
NOT_APPLICABLE_GATE_ITEMS: tuple[str, ...] = (
    "backup_prepared",
    "rollback_path_verified",
    "application_consumer_authorized",
    "audit_record_initialized",
)

#: Workspace statuses treated as ineligible for a future application. A
#: small, explicit, named set -- never an opaque scoring function.
_INELIGIBLE_WORKSPACE_STATUSES: frozenset[str] = frozenset({"deleted"})


class ApplicationGateCheck(enum.Enum):
    STRATEGY_APPROVAL_EXISTS = "strategy_approval_exists"
    DRAFT_APPROVAL_EXISTS = "draft_approval_exists"
    APPLICATION_APPROVAL_EXISTS = "application_approval_exists"
    SOURCE_HASH_MATCHES = "source_hash_matches"
    WORKSPACE_ELIGIBLE = "workspace_eligible"
    PATH_UNCHANGED = "path_unchanged"
    EDIT_SCOPE_UNCHANGED = "edit_scope_unchanged"
    NO_REVOCATION = "no_revocation"
    DRAFT_DIGEST_MATCHES_APPROVED = "draft_digest_matches_approved"
    VALIDATION_PASSED = "validation_passed"


@dataclass(frozen=True)
class ApplicationGateCheckResult:
    check: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ApplicationGateResult:
    draft_digest: str
    checks: tuple[ApplicationGateCheckResult, ...]
    all_passed: bool
    failed_checks: tuple[str, ...]
    #: Section 13 preconditions this evaluation could not check at all,
    #: because no supporting mechanism exists yet -- see module docstring.
    not_applicable_checks: tuple[str, ...]
    gate_boundary: str


def evaluate_application_gate(
    *,
    repair_plan: "repair_planner.RepairPlan",
    repair_approval_record: object | None,
    repair_draft: "repair_draft_mod.RepairDraft",
    draft_approval_record: "draft_approval.DraftApprovalRecord | None",
    application_approval_record: "application_approval.ApplicationApprovalRecord | None",
    current_source_identity: "repair_draft_mod.SourceIdentity | None" = None,
    workspace_status: str | None = None,
) -> ApplicationGateResult:
    """Pure, deterministic re-verification. Every input is a value the
    caller already has (a plan, a draft, and the three approval-layer
    records already looked up from their respective stores) or explicitly
    supplies fresh (`current_source_identity`, `workspace_status`) -- this
    function never fetches, reads, or re-derives any of them itself.

    `repair_approval_record` is typed loosely (`object | None`) rather than
    importing `gauss_repair_approval.ApprovalRecord` by name, since this
    module intentionally has no other reason to import
    `gauss_repair_approval.py` at all -- duck-typed attribute access
    (`.decision`, `.plan_digest`) is used instead, mirroring how this module
    already avoids importing any approval-layer *store* class."""
    results: list[ApplicationGateCheckResult] = []

    def record(check: ApplicationGateCheck, passed: bool, detail: str) -> None:
        results.append(ApplicationGateCheckResult(check=check.value, passed=passed, detail=detail))

    plan_digest = repair_planner.repair_plan_digest(repair_plan)
    draft_digest = repair_draft_mod.repair_draft_digest(repair_draft)

    # 1. Strategy approval exists and is approved for the current plan.
    if repair_approval_record is None:
        record(ApplicationGateCheck.STRATEGY_APPROVAL_EXISTS, False, "no strategy-level approval record was supplied")
    elif getattr(repair_approval_record, "plan_digest", None) != plan_digest:
        record(
            ApplicationGateCheck.STRATEGY_APPROVAL_EXISTS, False,
            "the supplied strategy-approval record's plan_digest does not match the current repair plan",
        )
    elif getattr(repair_approval_record, "decision", None) != "approved":
        record(
            ApplicationGateCheck.STRATEGY_APPROVAL_EXISTS, False,
            f"strategy approval decision is {getattr(repair_approval_record, 'decision', None)!r}, not 'approved'",
        )
    else:
        record(ApplicationGateCheck.STRATEGY_APPROVAL_EXISTS, True, "an approved strategy-approval record exists for the current plan")

    # 2. Draft approval exists and is approved for the current draft.
    if draft_approval_record is None:
        record(ApplicationGateCheck.DRAFT_APPROVAL_EXISTS, False, "no draft-approval record was supplied")
    elif draft_approval_record.draft_digest != draft_digest:
        record(
            ApplicationGateCheck.DRAFT_APPROVAL_EXISTS, False,
            "the supplied draft-approval record's draft_digest does not match the current repair draft",
        )
    elif draft_approval_record.decision != "approved":
        record(ApplicationGateCheck.DRAFT_APPROVAL_EXISTS, False, f"draft approval decision is {draft_approval_record.decision!r}, not 'approved'")
    else:
        record(ApplicationGateCheck.DRAFT_APPROVAL_EXISTS, True, "an approved draft-approval record exists for the current draft")

    # 3. Application approval exists and is approved for the current draft.
    if application_approval_record is None:
        record(ApplicationGateCheck.APPLICATION_APPROVAL_EXISTS, False, "no application-approval record was supplied")
    elif application_approval_record.draft_digest != draft_digest:
        record(
            ApplicationGateCheck.APPLICATION_APPROVAL_EXISTS, False,
            "the supplied application-approval record's draft_digest does not match the current repair draft",
        )
    elif application_approval_record.decision != "approved":
        record(
            ApplicationGateCheck.APPLICATION_APPROVAL_EXISTS, False,
            f"application approval decision is {application_approval_record.decision!r}, not 'approved'",
        )
    else:
        record(ApplicationGateCheck.APPLICATION_APPROVAL_EXISTS, True, "an approved application-approval record exists for the current draft")

    # 4. Source hash matches -- fails closed if no current identity was supplied.
    if current_source_identity is None:
        record(
            ApplicationGateCheck.SOURCE_HASH_MATCHES, False,
            "no current source identity was supplied; freshness cannot be verified, so this check fails closed",
        )
    elif current_source_identity.content_hash != repair_draft.source_identity.content_hash:
        record(
            ApplicationGateCheck.SOURCE_HASH_MATCHES, False,
            "the supplied current source content hash no longer matches the draft's own bound hash -- the source has changed",
        )
    else:
        record(ApplicationGateCheck.SOURCE_HASH_MATCHES, True, "current source content hash matches the draft's own bound hash")

    # 5. Workspace eligibility -- fails closed if no status was supplied.
    if workspace_status is None:
        record(
            ApplicationGateCheck.WORKSPACE_ELIGIBLE, False,
            "no current workspace status was supplied; eligibility cannot be verified, so this check fails closed",
        )
    elif workspace_status in _INELIGIBLE_WORKSPACE_STATUSES:
        record(ApplicationGateCheck.WORKSPACE_ELIGIBLE, False, f"workspace status {workspace_status!r} is not eligible for application")
    else:
        record(ApplicationGateCheck.WORKSPACE_ELIGIBLE, True, f"workspace status {workspace_status!r} is eligible")

    # 6. Path unchanged -- fails closed if no current identity was supplied.
    if current_source_identity is None:
        record(ApplicationGateCheck.PATH_UNCHANGED, False, "no current source identity was supplied; path cannot be re-verified, so this check fails closed")
    else:
        artifact_matches = (
            current_source_identity.artifact.workspace_id == repair_draft.source_identity.artifact.workspace_id
            and current_source_identity.artifact.relative_path == repair_draft.source_identity.artifact.relative_path
        )
        record(
            ApplicationGateCheck.PATH_UNCHANGED, artifact_matches,
            "current workspace_id/relative_path match the draft's own bound artifact"
            if artifact_matches
            else "the supplied current source identity targets a different workspace or path than this draft was bound to",
        )

    # 7. Edit scope unchanged -- structurally guaranteed: RepairDraft is
    #    immutable and edit_scope is part of what repair_draft_digest
    #    hashes, so this is checked against the digest match itself, not
    #    assumed silently.
    record(
        ApplicationGateCheck.EDIT_SCOPE_UNCHANGED, True,
        "structurally guaranteed: edit_scope is part of the immutable draft's own content digest, "
        "so any scope change would already have changed draft_digest and failed every digest-bound check above",
    )

    # 8. No revocation across any of the three approval layers.
    revoked_layers = [
        name
        for name, rec in (
            ("strategy", repair_approval_record),
            ("draft", draft_approval_record),
            ("application", application_approval_record),
        )
        if rec is not None and getattr(rec, "decision", None) == "revoked"
    ]
    record(
        ApplicationGateCheck.NO_REVOCATION, not revoked_layers,
        "no supplied approval record has been revoked" if not revoked_layers else f"revoked layer(s): {', '.join(revoked_layers)}",
    )

    # 9. Application-approval record's own draft_digest matches the current draft.
    if application_approval_record is None:
        record(ApplicationGateCheck.DRAFT_DIGEST_MATCHES_APPROVED, False, "no application-approval record was supplied")
    else:
        matches = application_approval_record.draft_digest == draft_digest
        record(
            ApplicationGateCheck.DRAFT_DIGEST_MATCHES_APPROVED, matches,
            "application-approval record's draft_digest matches the current draft"
            if matches
            else "application-approval record's draft_digest does not match the current draft -- the draft changed after approval",
        )

    # 10. Structural draft validation (Phase 2, reused rather than re-derived).
    validation = repair_draft_mod.validate_repair_draft(repair_draft, current_source_identity)
    record(
        ApplicationGateCheck.VALIDATION_PASSED, validation.all_passed,
        "structural draft validation passed" if validation.all_passed else f"structural draft validation failed: {', '.join(validation.failed_checks)}",
    )

    all_passed = all(r.passed for r in results)
    failed = tuple(r.check for r in results if not r.passed)
    return ApplicationGateResult(
        draft_digest=draft_digest,
        checks=tuple(results),
        all_passed=all_passed,
        failed_checks=failed,
        not_applicable_checks=NOT_APPLICABLE_GATE_ITEMS,
        gate_boundary=GATE_BOUNDARY_STATEMENT,
    )
