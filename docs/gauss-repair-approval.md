# GAUSS Repair Approval

## What Approval Is

`scripts/gauss_repair_approval.py` (`v0.57.0`) records **one thing**: whether a human explicitly accepted or declined a specific, unmodified repair plan. That's the entire scope. It answers *did a human make a decision about this plan*, and nothing else.

## What Approval Is Not

**Approval is not application.** Recording an "approved" decision does not modify a file, does not prepare a draft, does not construct a patch, and does not rerun GAUSS. No mechanism in this repository consumes an approval decision toward any change — there is nothing downstream of this module yet. `safe_to_apply` and `safe_to_prepare_draft` are `False` on every `ApprovalRecord`, including approved ones, exactly as they are `False` on every `RepairPlan` — approval does not, and structurally cannot, flip either flag.

Read that twice if you take one thing from this document: **an "approved" repair plan is exactly as unapplied as a plan nobody has looked at.** The only difference is that a human decision now exists on record.

## Position in the Reasoning Pipeline

```
Execution
  -> Evidence Collection      (gauss_execution_workflow.py / gauss_code_execution.py)
  -> Interpretation           (gauss_execution_interpreter.py, v0.51.0)
  -> Verified Knowledge       (gauss_error_catalog.py, v0.51.0-v0.56.0)
  -> Diagnosis                (gauss_execution_diagnostics.py, v0.54.0-v0.55.0)
  -> Repair Planning          (gauss_repair_planner.py, v0.56.0)
  -> Approval                 (gauss_repair_approval.py, v0.57.0 -- this layer)
  -> Repair Application       (future, not implemented)
```

| Stage | Answers | Does not answer |
|---|---|---|
| Interpretation | What happened? | Why did it happen? |
| Diagnosis | What verified causes may explain it? What evidence is missing? | What exact code fixes it? |
| Repair Planning | What bounded strategy should be considered? | What exact code should be applied? |
| Approval | Did a human accept or decline this specific plan? | Should this plan be applied, or how? |
| Repair Application (future) | What specific, approved change was applied? | — |

## Deterministic Architecture

`RepairApprovalStore` is the only stateful piece, and its state is a single in-memory `dict[str, ApprovalRecord]` keyed by plan digest — nothing else. It is **not** durable: contrast `gauss_orchestration_state_store.OrchestrationStateStore`, which is SQLite-backed and survives a process restart. A `RepairApprovalStore` is exactly as durable as `InteractiveMvpAdapter.last_result` already is today — created fresh per adapter process, cleared by `reset`, gone when the process exits. This is a deliberate, structural choice, not a temporary gap: durable sessions are a separate, still-fully-deferred milestone (see `planning/v0.47.0-session-integration-readiness.md`), and this milestone does not depend on them.

The module has no import of `gauss_code_execution`, `gauss_workspace`, `gauss_runtime_orchestration`, `gauss_execution_adapter`, `gauss_execution_workflow`, `gauss_execution_session`, or `gauss_orchestration_state_store` — verified structurally (`test_09_approval_module_has_no_forbidden_imports` inspects the module's own source), not merely by convention. It never launches GAUSS, calls an execution helper, mutates workspace state, edits source code, reads or writes files, or accesses the network.

## Approval Model

```
ApprovalDecision (enum): approved | declined

ApprovalRecord (frozen dataclass)
  decision                    one of ApprovalDecision's values
  plan_digest                 the exact digest this decision was recorded against
  recorded_at                 caller-supplied clock value (never computed internally)
  source_error_code
  source_error_category
  repair_status
  safe_to_apply               always False
  safe_to_prepare_draft       always False
  approval_boundary           fixed disclosure, always present

RepairApprovalStore
  approve(plan, recorded_at) -> ApprovalRecord
  decline(plan, recorded_at) -> ApprovalRecord
  get_decision(plan) -> ApprovalRecord | None
  get_decision_for_digest(plan_digest) -> ApprovalRecord | None
  revoke(plan) -> bool
```

## Digest / Hash-Binding Model

`gauss_repair_planner.repair_plan_digest(plan) -> str` (added `v0.56.0`'s own module in `v0.57.0`, since it's the plan's own identity, not the approval layer's business to compute) is a SHA-256 fingerprint over a `RepairPlan`'s full identifying content — every field, including nested `RepairAction` entries — serialized in fixed order via `json.dumps(..., sort_keys=False)`, mirroring `gauss_runtime_orchestration.compute_request_hash`'s own established convention rather than inventing a second hashing scheme for this repository.

**Any change to any field produces a different digest.** A plan re-planned with different source context, or derived from different evidence, is a *different plan* with a *different digest* — a decision recorded against the old digest simply is not found when looked up against the new one. There is no separate "invalidation" step; staleness is a direct, structural consequence of hash-binding, the same way a stale `request_hash` already fails to match a changed execution proposal elsewhere in this repository.

## Single-Use, Non-Overwriting, Revocable

- `approve(plan, ...)` / `decline(plan, ...)` raise `ApprovalConflictError` if a decision already exists for that plan's digest. **A decision is never silently overwritten** — this is a hard requirement, not a convenience default.
- `revoke(plan)` explicitly removes an existing decision, returning `True`/`False` depending on whether one existed. This is the *only* sanctioned way to replace a decision — revoke, then record a new one.
- The store is process-local. It is not shared across adapter instances (`test_14_store_is_process_local_only`), and it is discarded on `reset`, alongside `last_repair_plan`.

## CLI Usage

```
gauss-mvp> repair-plan
...
plan_digest: 3e46512677036c268e0f5605238e974415d721a7875025963e0a6af3f6b1ad7c
...
next_step: run 'approve-repair 3e4651...' or 'decline-repair 3e4651...' to record an explicit decision (this records a decision only -- it does not apply anything).

gauss-mvp> approve-repair 3e46512677036c268e0f5605238e974415d721a7875025963e0a6af3f6b1ad7c
REAL_WORKFLOW: Repair-plan approval recorded from the current repair plan only.
APPROVAL_BOUNDARY: No code was modified. No file was written. No patch was applied. No draft was prepared. GAUSS was not rerun.
decision: approved
plan_digest: 3e46512677036c268e0f5605238e974415d721a7875025963e0a6af3f6b1ad7c
recorded_at: ...
safe_to_apply: false
safe_to_prepare_draft: false
approval_boundary: This records an explicit human decision about a specific repair plan. It does not apply, patch, or prepare a draft of any change. No code was modified. No file was written. GAUSS was not rerun.
```

`approve-repair`/`decline-repair` operate against `last_repair_plan` — the exact `RepairPlan` object the adapter's most recent `repair-plan` call produced, not a freshly recomputed one (source-context flags are not remembered between calls, so recomputation could silently diverge). Supplying any digest other than the current plan's own digest is rejected with `ERROR stale_or_incorrect_digest` and the correct current digest for guidance. `reset` clears both `last_repair_plan` and the entire approval store, consistent with how it already clears `interpret`/`diagnose`/`repair-plan` availability.

## Safety Boundaries

- `safe_to_apply` and `safe_to_prepare_draft` are `False` on every `ApprovalRecord`, approved or declined, with no code path that ever sets either to `True`.
- The approval module never reads or writes a file, never launches GAUSS, never mutates workspace state, never creates a new execution proposal.
- `approval_boundary` is a fixed, always-present disclosure string, identical on every record.
- Approval is always explicit — there is no default-accept, no inference from plan confidence, and no LLM-based reasoning anywhere in this module.

## Limitations

- Approval is strategy-level, same as the plan it records a decision about — no application mechanism exists anywhere in this repository to consume an approval decision.
- No durable or cross-process persistence: an approval recorded in one adapter process is invisible to another, and is gone when the process exits or `reset` runs.
- No revocation UI in the CLI yet (`revoke` exists at the module/API level, tested there, but is not wired to a CLI command this milestone — kept out of scope per "smallest coherent change").
- No batch approval, no approval expiry/TTL, no approval history beyond the single current decision per digest.
- No statistical or methodological validity assessment — unchanged from every prior stage.
