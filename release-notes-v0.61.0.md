# v0.61.0 - Repair Application Approval and Gate Validation

This release implements the fourth and final approval layer from `planning/v0.58.0-repair-application-safety-design.md` (§4.C, Application Approval) plus a pure re-verification of §13 (the Application Gate) — as far as it can be checked without a backup, rollback, application consumer, or audit mechanism, none of which exist yet. It authorizes checking whether an application would be allowed to proceed and recording a human decision about that exact authorization. It does not write a file, construct a patch, or perform any repair application.

## Evaluated

- A new `51.x` Repair Application Approval and Gate Validation benchmark category was added (ten prompts, matching coverage rows) and **fully evaluated**: 10/10 Passed at 4.0, 0 Critical/Major/Minor defects. Unlike `v0.59.0`'s `49.x` and `v0.60.0`'s `50.x` (both deliberately left `Not Run` as foundation-only milestones), this milestone's own task specification called for real evaluation, since the application-approval and gate logic is fully implemented, testable, real behavior.

## Added

- `scripts/gauss_repair_application_approval.py`: `ApplicationApprovalStore` records an explicit accept/decline/revoke decision about *applying* a specific `RepairDraft`, hash-bound to `repair_draft_digest(...)` — the same digest draft approval itself binds to, never a new, independently-computed "application digest" (per the design's own §5 identity model).
- `ApplicationApprovalDecision` (`approved`/`declined`/`revoked`), `ApplicationApprovalRecord`, `ApplicationApprovalConflictError`.
- `scripts/gauss_repair_application_gate.py`: `evaluate_application_gate(...)`, a pure function combining a plan, a draft, all three approval-layer records, a freshly-supplied current source identity, and a freshly-supplied workspace status into ten independently-reported checks (`ApplicationGateCheck`, `ApplicationGateCheckResult`, `ApplicationGateResult`).
- CLI `approve-repair-application`/`decline-repair-application`/`show-repair-application-approval` commands, mirroring `approve-repair-draft`'s own established digest-binding/stale-rejection behavior exactly.
- CLI `check-repair-application-gate [--current-content-hash SHA256]` command, deriving workspace eligibility from the adapter's own real, already-known `WorkspaceStatus` and never fabricating a "current" file observation.
- `docs/gauss-repair-application-approval.md` — purpose, architecture, the binding rule, the ten gate checks, relationships to every upstream layer, limitations.

## Critical Invariants (Unchanged, Extended One Layer — And Structurally Strengthened)

`safe_to_apply` and `safe_to_prepare_draft` remain structurally `False` on every `ApplicationApprovalRecord`, across approved/declined/revoked states alike, with no code path capable of changing either — the same invariant `RepairPlan`, `ApprovalRecord`, `RepairDraft`, and `DraftApprovalRecord` already enforce. `ApplicationGateResult` goes one step further: it has **no `safe_to_apply` field at all**, not even one fixed to `False` — a deliberate structural choice so no code path anywhere can even superficially resemble authorizing an application.

## The Application Gate Fails Closed, Not Skipped

`source_hash_matches` and `path_unchanged` report `FAIL` — not a silent pass — whenever the caller doesn't supply a freshly-observed current source identity, since the gate's entire purpose is to prove freshness, not merely check it when convenient. `workspace_eligible` is the one exception: the CLI derives it from the adapter's own real, already-known `WorkspaceStatus`, which is genuinely known (not fabricated) without any additional file read, so it is not required to fail closed the same way. Four Section-13 preconditions this repository cannot check at all — a backup has been prepared, a rollback path has been verified, the application consumer is authorized, an audit record has been initialized — are disclosed explicitly via `not_applicable_checks` on every result, passing or failing alike, rather than silently assumed satisfied.

## Revoke: Consistent With the v0.60.0 Precedent

`ApplicationApprovalStore.revoke(...)` transitions an active record to a preserved `REVOKED` state in place, exactly as `DraftApprovalStore.revoke(...)` (`v0.60.0`) already does — the same reasoning applies here: this milestone's own instructions list `revoked` as a first-class decision value, not merely an action. Duplicate and conflicting decisions both raise `ApplicationApprovalConflictError` rather than ever silently overwriting an active record.

## The Binding Rule

An application-approval decision binds to `repair_draft_digest(draft)` — the same digest draft approval itself binds to. There is no separate "application content" to fingerprint independently of the draft being applied; a future `repair_application_id` (an opaque per-attempt identifier, assigned only once an actual application transaction exists) is out of scope for this milestone.

## Not Implemented

The application transaction itself (§14), backup, rollback, audit, rerun, an `apply-repair` command, patch generation, file editing, filesystem mutation. `scripts/gauss_repair_planner.py`, `scripts/gauss_repair_approval.py`, `scripts/gauss_repair_draft.py`, and `scripts/gauss_repair_draft_approval.py` have zero diff.

## Documentation Updates

`README.md`, `ROADMAP.md` (new `v0.61.0` section; the "Repair Application" future candidate updated to note all four approval layers and the gate check are now implemented), `KNOWN_LIMITATIONS.md`, `CHANGELOG.md`, `docs/gauss-repair-application-safety.md` (updated to reflect what's implemented vs. what §14 still requires), and `docs/gauss-repair-draft-approval.md` were all updated.

## Remaining Limitations

- Application approval is process-local only — not durable, not shared across processes, cleared by `reset`.
- No CLI-level revoke command (module/API level only, matching every prior layer's own first-implementation precedent).
- No application transaction, backup, rollback, or audit mechanism exists — the gate's four `not_applicable_checks` items name this explicitly.
- The gate never reads a file itself; `source_hash_matches`/`path_unchanged` are only as trustworthy as the caller's own freshly-supplied current source identity.
- No approval expiry/TTL, no batch approval.

## Next Recommended Milestone

With all four approval layers now implemented (strategy, draft, application, and — separately, already existing — rerun via the ordinary execution-confirmation path) plus a pure gate check re-verifying every checkable precondition, the pipeline has everything the design's own Phase 4 (a local single-file application prototype) depends on except the transaction itself. That transaction is also the first code in this repository's history capable of writing to a user's file, so it needs its own explicit, separately-scoped authorization — this milestone deliberately does not request or imply that authorization.
