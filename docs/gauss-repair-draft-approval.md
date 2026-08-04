# GAUSS Repair Draft Approval

## Purpose

`scripts/gauss_repair_draft_approval.py` (`v0.60.0`) records **one thing**: whether a human explicitly accepted, declined, or later revoked a decision about a specific, unmodified `RepairDraft`. That's the entire scope. It is Phase 3 of `planning/v0.58.0-repair-application-safety-design.md`.

## What Draft Approval Is Not

**Draft approval is not application.** Recording an "approved" decision does not modify a file, does not construct a patch, does not rerun GAUSS, and does not make Repair Application available — nothing in this repository consumes a draft-approval decision toward any change. `safe_to_apply` and `safe_to_prepare_draft` are `False` on every `DraftApprovalRecord`, exactly as they are `False` on every `RepairDraft`.

**Draft approval is not strategy approval.** Approving a `RepairPlan` (`gauss_repair_approval.py`, `v0.57.0`) says nothing about any draft; approving a `RepairDraft` says nothing about the plan it was derived from. Each layer's approval is recorded, displayed, and revoked entirely independently — a tester who approved the strategy and then approves the draft has made two separate, explicit decisions, not one decision applied twice.

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
  -> Repair Draft Approval    (gauss_repair_draft_approval.py, v0.60.0 -- this layer)
  -> Repair Application Approval  (gauss_repair_application_approval.py, v0.61.0)
  -> Repair Application Gate       (gauss_repair_application_gate.py, v0.61.0)
  -> Repair Application       (application transaction itself, still not implemented)
```

| Stage | Answers | Does not answer |
|---|---|---|
| Repair Planning | What bounded strategy should be considered? | What exact code should be applied? |
| Approval (strategy) | Did a human accept or decline this specific plan? | Should a draft be prepared? |
| Repair Draft | What bounded, immutable, structurally-validated edit is proposed against an exact source state? | Is this edit approved? Should it be applied? |
| Repair Draft Approval | Did a human accept, decline, or revoke a decision about this specific, unmodified draft? | Should this draft be applied? |
| Repair Application Approval | Did a human authorize applying this specific draft? | Is it currently safe to apply it? |
| Repair Application (future) | What specific, approved change was applied? | — |

## Architecture

Follows the exact discipline `gauss_repair_approval.py` established: `DraftApprovalStore` is an ordinary in-memory `dict[str, DraftApprovalRecord]` wrapped in a small class — not durable, created fresh per process, discarded on `reset` or process exit. The module imports only `gauss_repair_draft` (for `RepairDraft` and `repair_draft_digest`); it never imports `gauss_repair_planner.py`, `gauss_repair_approval.py`, or any execution/workspace module, and performs zero I/O.

## The Binding Rule

A draft-approval decision is bound to `repair_draft_digest(draft)` **and to that alone** — never to `repair_plan_digest`, a workspace ID, a relative path, or an execution request ID, even though the bound `RepairDraft` carries all of those. This is already the strictest possible binding: `repair_draft_digest` is computed over the draft's entire content, including its own embedded `repair_plan_digest` and `source_identity` — so any change to any of those fields already changes the digest a decision is keyed on. Two independently-supplied `RepairDraft` objects that happen to be byte-for-byte identical in content (including sharing the same `repair_plan_digest`) are found as the *same* draft; a draft differing in even one field — workspace, path, plan digest, edit range — is a genuinely different digest and is never found (`test_12_binding_is_draft_digest_only_not_plan_digest`, `test_13_binding_is_draft_digest_only_not_workspace_or_path`).

## Approval Lifecycle

```
DraftApprovalDecision: approved | declined | revoked

approve(draft, recorded_at)  -> DraftApprovalRecord   (raises DraftApprovalConflictError if an ACTIVE record exists)
decline(draft, recorded_at) -> DraftApprovalRecord    (same conflict rule)
revoke(draft, recorded_at)  -> bool                     (transitions an active record to REVOKED in place; True if one existed)
get_decision(draft)          -> DraftApprovalRecord | None
get_decision_for_digest(digest) -> DraftApprovalRecord | None
```

**Revoke transitions in place rather than deleting** — a deliberate, small evolution beyond `gauss_repair_approval.RepairApprovalStore.revoke(...)` (which deletes outright). A revoked decision remains visible as history (`decision: "revoked"`) rather than disappearing without a trace, while a REVOKED record does not block a fresh `approve`/`decline` call for the same digest — only an *active* (approved or declined) record does. This means the sequence *decline → revoke → approve* is fully supported and produces exactly one current record, with the earlier decline's occurrence no longer blocking anything, but the fact that a decision happened at all remains recoverable via `get_decision(...)` at each step along the way (tests exercise this directly, e.g. `test_06_approve_after_revoke_succeeds`).

**Conflict detection** (`DraftApprovalConflictError`) covers both duplicate recording (approving the same draft twice) and conflicting recording (declining an already-approved draft, or vice versa) — a decision is never silently overwritten in either case; the error message names the existing decision and the required remediation (`revoke(draft)`).

## Relationship to RepairPlan

None. This module never imports `gauss_repair_planner.py` and never inspects a `RepairPlan` object — it consumes a `RepairDraft`'s own `repair_plan_digest` field only as inert data already embedded in the draft's content (and therefore already folded into `repair_draft_digest`).

## Relationship to RepairDraft

Direct and exclusive: every operation in this module takes a `RepairDraft` object and immediately reduces it to `repair_draft_digest(draft)` for storage and lookup. Nothing about a draft's own fields — `edit_scope`, `source_identity`, `assumptions`, `risks` — is inspected or duplicated here.

## Relationship to Repair Application Approval and the Gate

As of `v0.61.0`, `gauss_repair_application_gate.py` reads a `DraftApprovalRecord` (already looked up by the caller) as one of ten preconditions in its pure `evaluate_application_gate(...)` check — but only to confirm it exists and is `approved` for the current draft digest; nothing here is re-derived or duplicated. No code anywhere applies a repair as a result. `safe_to_apply`/`safe_to_prepare_draft` remain `False` on every `DraftApprovalRecord` with no code path capable of changing either — approving a draft is exactly as inert, in terms of actual application, as never approving one at all. See `docs/gauss-repair-application-approval.md` for the fourth approval layer (application approval, `v0.61.0`) and the gate check, and `planning/v0.58.0-repair-application-safety-design.md` for what a future implementation would still need beyond that: the application transaction itself, backup/rollback, and audit.

## CLI Usage

```
gauss-mvp> repair-draft --path model.gss --content-hash <sha256> --size 200 \
    --line-start 5 --line-end 5 --operation "insert missing semicolon" \
    --description "Insert a missing statement terminator at the reported line."
...
draft_digest: 890ad04741a1c9...

gauss-mvp> approve-repair-draft 890ad04741a1c9...
REAL_WORKFLOW: Repair-draft approval recorded from the current repair draft only.
DRAFT_APPROVAL_BOUNDARY: No code was modified. No file was written. No patch was applied. No execution occurred. Repair Application remains unavailable.
decision: approved
draft_digest: 890ad04741a1c9...
safe_to_apply: false
safe_to_prepare_draft: false
approval_boundary: The repair draft has been approved. No files have been modified. No repair has been applied. No execution has occurred. Repair Application remains unavailable.

gauss-mvp> show-repair-draft-approval
```

`approve-repair-draft`/`decline-repair-draft` operate against `last_repair_draft` — the adapter's own most recently constructed draft — and require the caller to supply its exact current `draft_digest`; a stale or incorrect digest is rejected with the correct current digest for guidance, mirroring `approve-repair`'s own established behavior. `reset` clears `last_repair_draft` and creates a fresh `DraftApprovalStore`, exactly as it already clears `last_repair_plan` and the strategy-level approval store. No `revoke-repair-draft` CLI command exists yet — `revoke` remains available at the module/API level only, tested there, consistent with `v0.57.0`'s own "smallest coherent change" precedent for its own unwired `revoke`.

## Limitations

- Draft approval is process-local only — not durable, not shared across processes, cleared by `reset`.
- No CLI-level revoke command (module/API level only).
- No approval expiry/TTL, no batch approval.
- No application consumer exists anywhere in this repository.
- No statistical or methodological validity assessment — unchanged from every prior stage.
