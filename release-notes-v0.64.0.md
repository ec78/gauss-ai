# v0.64.0 - Verification Execution Workflow

This milestone adds a Verification Execution workflow: `scripts/gauss_verification_execution.py` executes an already-applied repair's resulting source through the **existing, unmodified execution pipeline** and collects evidence. It is explicitly **not** automatic repair validation, automatic repair acceptance, autonomous retry, autonomous repair, or autonomous planning — it produces evidence for a human to read, nothing more.

## Architecture: Repair Knows Nothing About Execution, Execution Knows Nothing About Repair

`scripts/gauss_execution_workflow.py` and `scripts/gauss_repair_application.py` both have **zero diff** from this milestone. `scripts/gauss_verification_execution.py` is the only dedicated logic module that imports both — purely as a translation adapter, never re-implementing execution or repair logic of its own. No repair-specific execution engine, runner, proposal, confirmation, or session type was created. `54.10`'s own evaluation run documents one honest clarification: `scripts/gauss_code_assistant_cli.py`, as this repository's single top-level orchestrator, has always imported every layer it wires together as commands — it dispatches to real entry points, it does not contain repair-aware execution logic or execution-aware repair logic of its own.

## VerificationExecutionRequest

`build_verification_execution_request(application_result, *, reason, ...)` produces an immutable `VerificationExecutionRequest` that references only an already-successful `ApplicationResult` — never a `RepairDraft` directly, confirmed structurally (`test_04`). Any `ApplicationResult` whose `outcome` is not `"applied"` raises `RepairNotAppliedError` — verification cannot be requested for a blocked or failed application.

## Execution Reuse

`propose_verification_execution(...)` re-reads and re-hashes the repaired file (via the same `read_workspace_file(...)` path every prior layer uses), fails closed if the source is unreadable or its hash no longer matches the application's own recorded post-application hash, and otherwise calls `ExecutionWorkflow.propose_execution(...)` — the exact same method an ordinary execution request uses, returning the exact same `wf.ProposalOutcome`/`wf.ExecutionProposal` types (`test_06`, `isinstance`-verified). The proposal deliberately omits `workspace_id=`, using `working_directory=<the workspace's own real root_path>` instead, since the workspace already completed its one-shot lifecycle during the original failing execution — this reuses an already-supported, pre-`v0.43.0` code path rather than adding new capability (`test_24` proves a completed workspace does not block the verification proposal). Everything after proposal generation — `confirm`, `execute` — is the pre-existing, completely unmodified execution workflow.

## Comparison: Evidence, Not a Verdict

`compare_execution_outcomes(original, verification) -> ComparisonSummary` is a pure function consuming two already-computed `ExecutionInterpretation` objects and selecting one of five named outcomes (`SUCCEEDED_AFTER_FAILURE`, `DIFFERENT_ERROR`, `SAME_ERROR`, `FAILED_AFTER_SUCCESS`, `BOTH_SUCCEEDED`), each with a fixed observation string. All three of the task's own worked examples are matched verbatim and covered by tests and by `54.6`/`54.7`/`54.8` evaluation evidence. `ComparisonSummary` has no `repair_correct`, `success_probability`, `confidence_score`, `verdict`, or `is_fixed` field anywhere — confirmed structurally via `hasattr` checks (`test_16`, `54.9`). A fixed `VERIFICATION_DISCLOSURE` is shown unconditionally, regardless of which comparison case occurred.

## CLI

Exactly two new commands: `verify-repair` and `show-verification-request`. `verify-repair` builds the request, proposes the verification execution, and mirrors the small amount of session bookkeeping `GaussCodeAssistantWorkflow.propose()` itself would have done — so the CLI's pre-existing, unmodified `confirm`/`execute` commands drive the run with zero new confirmation or execution code. `show-verification-request` displays the request and, once execution completes, the comparison. `reset` now also clears the verification request and the snapshotted original-execution interpretation (captured before verification overwrites the adapter's shared execution-result fields).

## Testing

`scripts/test_gauss_verification_execution.py` (new, 24 tests): request construction and rejection, structural proof the request never references a `RepairDraft`, genuine proposal-type reuse via `isinstance`, stale-hash and unreadable-source blocking, real `confirm`/`execute` reuse, all five comparison cases, the no-verdict-field structural check, determinism, disclosure content, and `git diff`/import-based proof of the architectural separation. `scripts/test_gauss_code_assistant_cli.py` grew by 10 tests (124-133, all three worked comparison examples exercised through the real CLI). Full existing regression suite (30 test files) re-run and passing unchanged.

## Evaluated

A new `54.x` category (ten prompts) was fully evaluated against real, on-disk, temp-directory-backed workspaces, real `ExecutionWorkflow` proposals, and the real CLI path. **10/10 Passed at 4.0. No defects found.**

## Not Implemented

Automatic retries, automatic repair acceptance, automatic rollback, automatic planning, automatic code editing, repair scoring, LLM repair loops, repair ranking, and autonomous execution — none were added, per this milestone's own explicit scope. `scripts/gauss_repair_planner.py`, `scripts/gauss_repair_approval.py`, `scripts/gauss_repair_draft.py`, `scripts/gauss_repair_draft_approval.py`, `scripts/gauss_repair_application_approval.py`, and `scripts/gauss_repair_application_gate.py` have zero diff.

## Documentation Updates

`README.md`, `ROADMAP.md` (new `v0.64.0` section), `KNOWN_LIMITATIONS.md`, `CHANGELOG.md`, and the new `docs/gauss-verification-execution.md`.

## Recommendation for the Next Milestone

With verification execution now producing real, evidence-only comparisons against the unmodified execution pipeline, the next natural step is a human-facing decision layer that records what a person concluded from that evidence — an ordinary approval/decision record analogous to every prior approval layer in this pipeline, not an automated verdict. This milestone deliberately does not request or imply that authorization. Do not implement functionality beyond this milestone.
