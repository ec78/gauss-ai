# v0.57.0 - Repair Approval Mechanism (Design Phase)

This release adds a new Approval stage to the project's staged reasoning pipeline (Execution → Evidence Collection → Interpretation → Verified Knowledge → Diagnosis → Repair Planning → **Approval** → Repair Application), strictly separate from the not-yet-implemented Repair Application stage. Approval never enables application.

## Evaluated

- All ten `48.x` Repair Approval Mechanism prompts: 10/10 Pass at 4.0, zero Critical/Major/Minor defects.
- No real GAUSS invocation was required or performed — this milestone reasons over already-computed `RepairPlan` objects and a pure, in-memory approval store.

## Added

- `scripts/gauss_repair_approval.py`: a new, pure (except for one small piece of in-memory state), process-local approval-recording module. `RepairApprovalStore.approve(plan, recorded_at)`/`.decline(plan, recorded_at)` record an explicit human decision hash-bound to `gauss_repair_planner.repair_plan_digest(plan)`.
- `gauss_repair_planner.repair_plan_digest(plan) -> str`: a SHA-256 fingerprint over a `RepairPlan`'s full identifying content, mirroring `gauss_runtime_orchestration.compute_request_hash`'s existing hashing convention rather than inventing a new one.
- `ApprovalDecision` (`approved`/`declined`), `ApprovalRecord`, `ApprovalConflictError`.
- CLI `approve-repair <plan_digest>` / `decline-repair <plan_digest>` commands, plus a `plan_digest` line (and, when relevant, a `next_step` line) added to `repair-plan`'s own output.
- `docs/gauss-repair-approval.md` — what approval is and is not, architecture, model, hash-binding, single-use/non-overwriting/revocable rules, CLI usage, safety boundaries, limitations.
- `docs/gauss-repair-planning.md` updated to reference the new downstream layer without changing repair planning's own responsibilities.

## Critical Invariant

`ApprovalRecord.safe_to_apply` and `.safe_to_prepare_draft` are **structurally always `False`** — checked directly across every reachable plan status, including after a decision is recorded. Approving a plan does not mutate the plan itself, does not enable draft preparation, and does not enable application. No code path anywhere in this module sets either flag to `True`.

## Hash-Binding and Non-Overwriting

Any change to a plan's content — different evidence, different source context, a different strategy — produces a different `repair_plan_digest`. A decision recorded against one digest is simply not found when looked up against a different one; there is no separate invalidation step. Recording a second decision for a digest that already has one raises `ApprovalConflictError` rather than silently overwriting it; `revoke(plan)` is the only sanctioned way to replace a decision.

## CLI Behavior

`approve-repair`/`decline-repair` operate against the adapter's own `last_repair_plan` — the exact plan `repair-plan` most recently computed, not a freshly recomputed one (source-context flags aren't remembered between calls). Supplying any digest other than the current plan's own is rejected with `ERROR stale_or_incorrect_digest` and the correct digest for guidance. Neither command calls `execute`/`plan`/`confirm`, reads or writes a file, or mutates workspace state. `reset` clears both `last_repair_plan` and the entire approval store.

## Safety Boundaries (unchanged, re-verified)

Execution, confirmation, provenance, output-reading, workspace-recovery, interpretation, diagnostic, and repair-planning contracts are all unchanged by this release. `scripts/gauss_execution_interpreter.py`, `scripts/gauss_execution_diagnostics.py`, `scripts/gauss_code_execution.py`, `scripts/gauss_workspace.py`, and `scripts/gauss_execution_workflow.py` have zero diff in this release.

## Remaining Limitations

- Approval is strategy-level, same as the plan it records a decision about — no application mechanism exists anywhere in this repository to consume an approval decision.
- No durable or cross-process persistence; approval state is in-memory and process-local, cleared by `reset`.
- No CLI `revoke` command yet (available at the module/API level, tested there).
- No approval expiry/TTL, no approval history beyond the current decision per digest.
- No automatic source-context collection was added or changed.
- No statistical or methodological validity assessment, same as every prior stage.

## Next Recommended Milestone

Durable execution sessions remain a real, previously-scoped candidate (`planning/v0.47.0-session-integration-readiness.md`), now closer to relevant since a future repair-application workflow would need to correlate an approval decision with the exact execution/plan it was derived from across turns — but no such workflow is authorized yet. The more evidence-grounded next step is either (a) a genuinely scoped, explicitly-authorized Repair Application *design* (not implementation) that defines how an `ApprovalRecord` would gate a future patch-construction step, or (b) durable sessions, specifically once Repair Application's own design determines it needs them.
