# GAUSS Repair Application Approval and Gate Validation

## Purpose

Two related, but distinct, pieces of new logic, both `v0.61.0`:

- `scripts/gauss_repair_application_approval.py` records **one thing**: whether a human explicitly accepted, declined, or later revoked a decision about *applying* a specific, unmodified `RepairDraft` to its exact, freshly-reverified source state. This is Phase 4.C (Application Approval) of `planning/v0.58.0-repair-application-safety-design.md`.
- `scripts/gauss_repair_application_gate.py` answers a second, related question: *if an application transaction existed, would every checkable precondition for applying this exact draft currently hold?* This is a pure re-verification of `planning/v0.58.0-repair-application-safety-design.md` Section 13 (the Application Gate) — as far as it can be checked without a backup, rollback, application consumer, or audit mechanism, none of which exist yet.

Neither module applies anything. Neither writes a file. Neither generates a patch.

## What Application Approval and the Gate Are Not

**Application approval is not application.** Recording an "approved" decision does not modify a file, does not construct a patch, does not rerun GAUSS, and does not make an actual repair-application transaction available — nothing in this repository consumes an application-approval decision toward any change. `safe_to_apply` and `safe_to_prepare_draft` are `False` on every `ApplicationApprovalRecord`, exactly as they are `False` on every `RepairDraft` and `DraftApprovalRecord`.

**A passing gate result is not authorization to apply anything.** `ApplicationGateResult` has no `safe_to_apply` field at all — not `False`, absent entirely — a deliberate structural choice so no code path anywhere can even superficially resemble flipping the invariant every upstream layer already enforces. `evaluate_application_gate(...)` only reports whether every *checkable* precondition currently holds; it never claims application is now safe, and it explicitly discloses (`not_applicable_checks`) the preconditions it cannot check at all because no supporting mechanism exists.

**Application approval is not draft approval, and the gate is not a fourth approval layer.** Approving a `RepairDraft` (`gauss_repair_draft_approval.py`, `v0.60.0`) says the human accepted the *edit itself*; approving its application says the human separately authorizes *applying that exact edit to the exact, currently-verified file*. These are two independent decisions, per `planning/v0.58.0-repair-application-safety-design.md` §4's explicit prohibition on ever collapsing any two of the four approval layers into one confirmation. The gate is not an approval at all — it is a read-only check that several already-recorded approvals (and a freshly-supplied source state) are consistent with each other.

## Position in the Reasoning Pipeline

```
Execution
  -> Evidence Collection      (gauss_execution_workflow.py / gauss_code_execution.py)
  -> Interpretation           (gauss_execution_interpreter.py, v0.51.0)
  -> Verified Knowledge       (gauss_error_catalog.py, v0.51.0-v0.56.0)
  -> Diagnosis                (gauss_execution_diagnostics.py, v0.54.0-v0.55.0)
  -> Repair Planning          (gauss_repair_planner.py, v0.56.0)
  -> Approval (strategy)      (gauss_repair_approval.py, v0.57.0)
  -> Repair Draft              (gauss_repair_draft.py, v0.59.0)
  -> Repair Draft Approval    (gauss_repair_draft_approval.py, v0.60.0)
  -> Repair Application Approval  (gauss_repair_application_approval.py, v0.61.0 -- this layer)
  -> Repair Application Gate       (gauss_repair_application_gate.py, v0.61.0 -- this layer)
  -> Repair Application       (designed in v0.58.0, not implemented)
```

| Stage | Answers | Does not answer |
|---|---|---|
| Repair Draft Approval | Did a human accept, decline, or revoke a decision about this specific, unmodified draft? | Should this draft be applied? |
| Repair Application Approval | Did a human accept, decline, or revoke a decision about *applying* this specific draft? | Is it currently safe to apply it? |
| Repair Application Gate | Do every checkable precondition (approvals, source freshness, workspace eligibility, structural validation) currently hold? | Was anything applied? Is application now authorized? |
| Repair Application (future) | What specific, approved change was applied? | — |

## Architecture

`gauss_repair_application_approval.py` follows the exact discipline `gauss_repair_draft_approval.py` established one layer up: `ApplicationApprovalStore` is an ordinary in-memory `dict[str, ApplicationApprovalRecord]` wrapped in a small class — not durable, created fresh per process, discarded on `reset` or process exit. The module imports only `gauss_repair_draft` (for `RepairDraft` and `repair_draft_digest`); it never imports `gauss_repair_planner.py`, `gauss_repair_approval.py`, or `gauss_repair_draft_approval.py`, and performs zero I/O.

`gauss_repair_application_gate.py` is the first module in this pipeline whose entire purpose is to *combine* several upstream layers' already-computed state into one pass/fail verdict, rather than adding new content of its own. `evaluate_application_gate(...)` is a pure function: every input — the plan, the draft, all three approval-layer records (or `None`), a freshly-supplied `current_source_identity`, and a freshly-supplied `workspace_status` — is a value the caller already has or explicitly asserts. The function never fetches, reads, hashes, or re-derives any of them itself.

## The Binding Rule

An application-approval decision is bound to `repair_draft_digest(draft)` — the same digest draft approval itself binds to, **not** a new, independently-computed "application digest." Per the design document's Section 5, there is no separate "application content" to fingerprint independently of the draft being applied; a future `repair_application_id` (an opaque per-attempt identifier, assigned only once an actual application transaction exists) is out of scope for this milestone.

## Approval Lifecycle

```
ApplicationApprovalDecision: approved | declined | revoked

approve(draft, recorded_at)  -> ApplicationApprovalRecord   (raises ApplicationApprovalConflictError if an ACTIVE record exists)
decline(draft, recorded_at) -> ApplicationApprovalRecord    (same conflict rule)
revoke(draft, recorded_at)  -> bool                          (transitions an active record to REVOKED in place; True if one existed)
get_decision(draft)          -> ApplicationApprovalRecord | None
get_decision_for_digest(digest) -> ApplicationApprovalRecord | None
```

Identical lifecycle discipline to `DraftApprovalStore` (`v0.60.0`): revoke transitions in place rather than deleting, so a revoked decision remains visible as history while freeing the digest for a fresh `approve`/`decline`; duplicate and conflicting decisions both raise `ApplicationApprovalConflictError` rather than ever silently overwriting an active record.

## The Application Gate's Ten Checks

`evaluate_application_gate(...)` reports one `ApplicationGateCheckResult` per named check:

| Check | What it verifies | Fails closed if unsupplied? |
|---|---|---|
| `strategy_approval_exists` | An approved `ApprovalRecord` exists whose `plan_digest` matches the current plan | Yes (`None` fails) |
| `draft_approval_exists` | An approved `DraftApprovalRecord` exists whose `draft_digest` matches the current draft | Yes |
| `application_approval_exists` | An approved `ApplicationApprovalRecord` exists whose `draft_digest` matches the current draft | Yes |
| `source_hash_matches` | The caller's freshly-supplied `current_source_identity.content_hash` equals the draft's own bound hash | Yes — absence is treated as a failure to re-verify, not skipped |
| `workspace_eligible` | The caller's freshly-supplied `workspace_status` is not `deleted` | Yes |
| `path_unchanged` | The caller's freshly-supplied identity's `workspace_id`/`relative_path` match the draft's own bound artifact | Yes |
| `edit_scope_unchanged` | Structurally guaranteed — `edit_scope` is part of what `repair_draft_digest` hashes | Always passes |
| `no_revocation` | None of the three supplied approval records has decision `revoked` | N/A (absence is not itself a revocation) |
| `draft_digest_matches_approved` | The application-approval record's own `draft_digest` equals the current draft's digest | Yes |
| `validation_passed` | `gauss_repair_draft.validate_repair_draft(draft, current_source_identity)` reports `all_passed=True` | Reuses Phase 2 validation, not re-derived |

Four Section-13 preconditions are **not checked** — `backup_prepared`, `rollback_path_verified`, `application_consumer_authorized`, `audit_record_initialized` — because no backup, rollback, application-consumer, or audit mechanism exists anywhere in this repository. These are named explicitly in `ApplicationGateResult.not_applicable_checks`, never silently omitted or assumed satisfied.

## Relationship to RepairPlan, RepairDraft, and the Two Approval Stores

`gauss_repair_application_approval.py` relates to `RepairDraft` exactly as `gauss_repair_draft_approval.py` does: every operation reduces a `RepairDraft` to `repair_draft_digest(draft)` for storage and lookup, nothing else about the draft is inspected. `gauss_repair_application_gate.py` relates to all four upstream modules by calling only their already-exported pure functions (`repair_plan_digest`, `repair_draft_digest`, `validate_repair_draft`) — it never imports either approval-layer *store* class, and never re-derives digest or validation logic a second way.

## Relationship to Future Repair Application

None yet. No application transaction exists anywhere in this repository. `safe_to_apply`/`safe_to_prepare_draft` remain `False` on every `ApplicationApprovalRecord`, and `ApplicationGateResult` has no `safe_to_apply` field at all — approving an application, or seeing a passing gate result, is exactly as inert, in terms of actual application, as never doing either. See `planning/v0.58.0-repair-application-safety-design.md` §14 for what a future implementation would still need: the application transaction itself, backup/rollback, and audit — each requiring its own explicit, separately-scoped authorization.

## CLI Usage

```
gauss-mvp> approve-repair-application 890ad04741a1c9...
REAL_WORKFLOW: Repair-application approval recorded from the current repair draft only.
APPLICATION_APPROVAL_BOUNDARY: No code was modified. No file was written. No patch was applied. No execution occurred. The application transaction itself remains unimplemented.
decision: approved
draft_digest: 890ad04741a1c9...
safe_to_apply: false
safe_to_prepare_draft: false
approval_boundary: The repair application has been approved. No files have been modified. No repair has been applied. No execution has occurred. The application transaction itself remains unimplemented -- approving this authorization records a decision only.

gauss-mvp> show-repair-application-approval

gauss-mvp> check-repair-application-gate --current-content-hash <sha256>
REAL_WORKFLOW: Application-gate precondition re-verification only.
gate_boundary: A passing application gate result does not authorize applying anything. No application transaction exists in this repository. This is a precondition re-verification only.
all_passed: true
  check[strategy_approval_exists]: pass -- ...
  ...
not_applicable_checks: backup_prepared, rollback_path_verified, application_consumer_authorized, audit_record_initialized
```

`approve-repair-application`/`decline-repair-application` operate against `last_repair_draft` and require the caller to supply its exact current `draft_digest`, mirroring `approve-repair-draft`'s own established behavior. `check-repair-application-gate` takes an optional `--current-content-hash` flag; without it, `source_hash_matches` and `path_unchanged` correctly fail closed rather than assuming freshness — the CLI never fabricates a "current" observation on the tester's behalf. Workspace eligibility is derived from the adapter's own real, already-known `WorkspaceStatus`, since that value is genuinely known (not fabricated) without any additional file read. `reset` clears `last_repair_draft`'s associated application-approval state via a fresh `ApplicationApprovalStore`, exactly as it already clears strategy- and draft-approval state. No `revoke-repair-application` CLI command exists yet — `revoke` remains available at the module/API level only, consistent with every prior layer's own first-implementation precedent.

## Limitations

- Application approval is process-local only — not durable, not shared across processes, cleared by `reset`.
- No CLI-level revoke command (module/API level only).
- No approval expiry/TTL, no batch approval.
- No application transaction, backup, rollback, or audit mechanism exists anywhere in this repository — the gate's four `not_applicable_checks` items name this explicitly.
- The gate never reads a file itself; `source_hash_matches`/`path_unchanged` are only as trustworthy as the caller's own freshly-supplied `current_source_identity`.
- No statistical or methodological validity assessment — unchanged from every prior stage.
