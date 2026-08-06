# GAUSS Verification Execution Workflow

## Purpose

`scripts/gauss_verification_execution.py` (`v0.64.0`) executes an already-applied repair's resulting source through the **existing, unmodified** execution pipeline and collects evidence. It answers exactly one question: *what happened when the repaired code ran, compared to what happened originally?* It never answers *is the repair correct*.

## What This Module Is Not

**Not automatic repair validation or acceptance.** Nothing in this repository treats a successful verification execution as proof the repair is correct, and no code path marks a repair "accepted" as a result of one.

**Not autonomous retry, repair, or planning.** Verification executes exactly once per `verify-repair` call, using exactly the caller-supplied fake-result mode (or, in real mode, whatever GAUSS actually reports) — it never loops, never retries, never constructs a new repair plan or draft on its own.

**Not a repair-specific execution engine.** There is no `RepairExecutionEngine`, `RepairRunner`, repair-specific proposal type, repair-specific confirmation type, or repair-specific session type anywhere in this repository. Verification produces a genuine `gauss_execution_workflow.ExecutionProposal`/`ProposalOutcome`, confirmed and executed through the exact same `ExecutionWorkflow.confirm_execution(...)`/`execute(...)` methods (or the MVP facade's own `confirm(...)`/`execute(...)`) any ordinary execution already uses — unmodified, zero diff.

## The Architectural Requirement

**Repair knows nothing about execution. Execution knows nothing about repair. Verification is only an adapter between them.**

- `scripts/gauss_execution_workflow.py` has zero diff from this milestone.
- `scripts/gauss_repair_application.py` has zero diff from this milestone.
- `scripts/gauss_verification_execution.py` is the *only* module that imports both `gauss_repair_application` (for the `ApplicationResult` type) and `gauss_execution_workflow` (for `ExecutionWorkflow`/`ExecutionProposal`/etc.) — and it does so only to translate one into inputs for the other. It contains no execution logic of its own and no repair logic of its own.

## Position in the Reasoning Pipeline

```
Execution
  -> ... (Interpretation, Verified Knowledge, Diagnosis, Repair Planning, all prior layers)
  -> Repair Application Transaction (gauss_repair_application.py, v0.62.0)
  -> Verification Execution           (this module, v0.64.0)
  -> (Separate rerun / ordinary execution confirmation -- already exists,
      unmodified: request/plan/confirm/execute)
```

## VerificationExecutionRequest

Immutable. Fields: `verification_execution_id`, `repair_application_id`, `application_result_id`, `workspace_id`, `relative_path`, `expected_post_repair_hash`, `reason`, `created_at`. `repair_application_id` and `application_result_id` are deliberately the same value — this repository has no separate, independently-identified "RepairApplication" record distinct from the transaction's own `ApplicationResult`.

**References only an `ApplicationResult` — never a `RepairDraft`.** `build_verification_execution_request(application_result, ...)` reads every field directly off `application_result`; there is no field anywhere on `VerificationExecutionRequest`, and no parameter anywhere on the constructor, capable of holding a `RepairDraft`. `application_result.outcome` must be `"applied"`; anything else raises `RepairNotAppliedError` immediately.

## Workflow: Reuse, Not Reimplementation

```
ApplicationResult (already exists, real, on disk)
    -> build_verification_execution_request(...)   [this module]
    -> VerificationExecutionRequest
    -> propose_verification_execution(...)         [this module -- one function]
        1. execution_workflow.read_workspace_file(...)   <- reused, unmodified
        2. compare checksum to expected_post_repair_hash <- fail closed if stale
        3. execution_workflow.propose_execution(...)      <- THE SAME METHOD
                                                              ordinary execution uses
    -> ProposalOutcome                              <- THE SAME TYPE ordinary execution returns
    -> (caller uses the ALREADY-EXISTING confirm_execution(...)/execute(...) -- untouched)
    -> ResponseReadyResult                          <- THE SAME TYPE ordinary execution returns
    -> compare_execution_outcomes(original, verification)  [this module -- pure, no I/O]
    -> ComparisonSummary
```

### Why the proposal is not workspace-lifecycle-bound

The workspace containing the repaired file already completed its one-shot lifecycle during the *original* failing execution — `propose_execution`'s own existing workspace-completed check (`v0.52.0`) would unconditionally block a second workspace-bound proposal against it. Verification's proposal therefore omits `workspace_id=` and passes `working_directory=<the workspace's own real root_path>` directly — an already-supported, pre-`v0.43.0` code path (workspace-unaware execution), not a new capability. The real repaired file is still executed at its real location; only the workspace's own single-shot bookkeeping is not re-entered for this second, independent attempt.

## Comparison Summary

`compare_execution_outcomes(original, verification) -> ComparisonSummary` is pure — no I/O, no re-execution — and consumes two already-computed `gauss_execution_interpreter.ExecutionInterpretation` objects, reusing that module's own classification rather than re-deriving it. It reports one of five evidence-only observations:

| Original | Verification | Observation |
|---|---|---|
| Failed | Succeeded | "The repaired code executed successfully whereas the original execution failed with {code}." |
| Failed | Failed, different code | "The repair changed execution behavior, but a different runtime error occurred." |
| Failed | Failed, same code | "The repair did not change the observed execution outcome." |
| Succeeded | Failed | "The verification execution failed with {code} even though the original execution succeeded." |
| Succeeded | Succeeded | "Both the original and verification executions completed successfully." |

**`ComparisonSummary` has no `repair_correct`, `success_probability`, or `confidence_score` field — structurally, not merely by convention.** It reports `original_outcome`, `verification_outcome`, `same_outcome: bool`, `comparison` (a named category), and `observation: str` only.

## CLI Usage

```
gauss-mvp> verify-repair --fake-success
This is an ordinary execution. It follows the standard execution workflow.
The repaired file is simply the execution target.
Repair success is NOT inferred from this proposal.
Verification evidence will be collected once execution completes.
...
request_hash: ...
next_step: run 'confirm <request_hash>' to proceed with this exact verification execution plan.

gauss-mvp> confirm <request_hash>
gauss-mvp> execute
gauss-mvp> show-verification-request
...
comparison_available: true
observation: The repaired code executed successfully whereas the original execution failed with G0105.
disclosure: This comparison reports evidence only. It does not conclude the repair is correct, assign a
success probability, or infer statistical correctness.
```

`confirm` and `execute` above are the exact same commands used for any ordinary execution — `verify-repair` populates the adapter's own `mvp_session`/`pending_request` fields so those pre-existing commands require zero modification. `show-verification-request` shows the request always, and the comparison once the verification execution has actually completed. `reset` clears the verification request and the snapshot of the original execution's own interpretation.

## Limitations

- The original execution's interpretation must be captured before `verify-repair` runs (it is snapshotted from the adapter's own current state); if no execution had occurred yet, no comparison is possible.
- Verification is not workspace-lifecycle-tracked — no provenance/manifest registration occurs for its own output files, since it deliberately does not bind to `workspace_id`.
- No automatic retry, rollback, repair acceptance, repair scoring, or LLM repair loop exists anywhere in this module.
- Process-local only — cleared by `reset`, not durable, not shared across processes.
- No statistical or methodological validity assessment — a completed verification execution proves only that a specific run occurred with a specific outcome, exactly as every prior execution-evidence boundary in this repository already states.
