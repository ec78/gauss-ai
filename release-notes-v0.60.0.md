# v0.60.0 - Repair Draft Review and Approval

This release implements Phase 3 of `planning/v0.58.0-repair-application-safety-design.md`: a draft-review and approval workflow. It authorizes a specific, immutable `RepairDraft` — nothing more. It does not authorize editing files, patch application, rerunning GAUSS, or repair application.

## Evaluated

- A new `50.x` Repair Draft Approval benchmark category was added (ten prompts, matching coverage rows) and deliberately left `Not Run`. No evaluation results were fabricated for this milestone.

## Added

- `scripts/gauss_repair_draft_approval.py`: `DraftApprovalStore` records an explicit accept/decline/revoke decision for a specific `RepairDraft`, hash-bound to `repair_draft_digest(...)` — and to that alone, never to `repair_plan_digest`, workspace, path, or execution request, per this milestone's own explicit design constraint.
- `DraftApprovalDecision` (`approved`/`declined`/`revoked`), `DraftApprovalRecord`, `DraftApprovalConflictError`.
- CLI `approve-repair-draft`/`decline-repair-draft`/`show-repair-draft-approval` commands, requiring the caller to supply the exact current `draft_digest`; a stale or incorrect digest is rejected with the correct current digest shown for guidance.
- `docs/gauss-repair-draft-approval.md` — purpose, architecture, the binding rule, approval lifecycle, relationships to `RepairPlan`/`RepairDraft`/future application, limitations.

## Critical Invariants (Unchanged, Extended One Layer)

`safe_to_apply` and `safe_to_prepare_draft` remain structurally `False` on every `DraftApprovalRecord`, across approved/declined/revoked states alike, with no code path capable of changing either — the same invariant `RepairPlan`, `ApprovalRecord`, and `RepairDraft` already enforce.

## A Deliberate Evolution: Revoke Transitions, It Doesn't Delete

Strategy-level `RepairApprovalStore.revoke(...)` (`v0.57.0`) deletes a record outright. This milestone's own instructions named `revoked` as a first-class decision value, so `DraftApprovalStore.revoke(...)` instead transitions an active record to a preserved `REVOKED` state in place — a decision history stays visible, while the digest is freed for a fresh `approve`/`decline` call exactly as before. Duplicate recording and conflicting recording (declining an already-approved draft, or vice versa) both raise `DraftApprovalConflictError` — a decision is never silently overwritten either way.

## The Binding Rule

A draft-approval decision binds to `repair_draft_digest(draft)` and to that alone. `DraftApprovalRecord` deliberately carries no `repair_plan_digest`, `workspace_id`, or `relative_path` field — only the draft's own opaque `repair_draft_id`, informational only, never used for lookup. This is already the strictest possible binding: the digest is computed over the draft's entire content, so any change to any embedded field already changes the digest a decision is keyed on. Verified directly: two drafts differing only in `repair_plan_digest`, or only in workspace/path, are correctly treated as unrelated, never found under each other's approval.

## Not Implemented

Apply-repair, rollback, patch generation, diff generation, file writes, filesystem mutation, backup, rerun, draft persistence, durable sessions, repair application. `scripts/gauss_repair_planner.py`, `scripts/gauss_repair_approval.py`, and `scripts/gauss_repair_draft.py` have zero diff.

## Documentation Updates

`README.md`, `ROADMAP.md` (new `v0.60.0` section; the "Repair Application" future candidate updated to note Phases 1-3 are now implemented), `KNOWN_LIMITATIONS.md`, `CHANGELOG.md`, and `docs/gauss-repair-draft.md` were all updated.

## Remaining Limitations

- Draft approval is process-local only — not durable, not shared across processes, cleared by `reset`.
- No CLI-level revoke command (module/API level only, matching `v0.57.0`'s own precedent for its first milestone).
- No application-approval layer, application transaction, backup, or rollback mechanism exists.
- No approval expiry/TTL, no batch approval.

## Next Recommended Milestone

With Phases 1-3 now implemented, the design's own Phase 4 (a local single-file application prototype) is the literal next phase — but it is also the first phase capable of writing to a file. A safety-first intermediate step worth considering first: implement and test the fourth approval layer (application approval) and the application-gate check itself (re-verifying every precondition from the design's §13, including a fresh source-hash comparison) as pure logic, deliberately deferring the actual file-write transaction one milestone further, so the highest-risk single change in this repository's history can be authorized and reviewed in complete isolation from everything that gates it.
