# v0.52.0 - Interpretation Evaluation and Recovery UX

This release formally evaluates all ten `43.x` Execution Interpretation benchmarks (added but `Not Run` in `v0.51.0`) through the real CLI/interpreter path, and fixes the completed-workspace planning issue carried since `v0.50.0`.

## Evaluated

- All ten `43.x` Execution Interpretation prompts: 10/10 Pass, average score 3.96, zero Critical/Major defects, one Minor (documentation-wording) finding.
- Three real GAUSS invocations (`x = 2 + 2; print x;`; `x = ;` → `G0105`; the repository's own verified matrix-dimension fixture → `G0036`), each on Windows/GAUSS 26.1.1 via `tgauss.exe -b <script>`.
- Timeout evidence: explicitly disclosed as a controlled, injected result (`--fake-timeout`), not a live GAUSS timeout — no unbounded real GAUSS loop was run.
- Unknown-error evidence: a deterministic, out-of-catalog `G9999` fixture (`--fake-unknown-error`).
- Interpreter boundaries (no execute, no retry, no code edit, no automatic file read, no auto-displayed streams, no workspace mutation, deterministic repeated interpretation) proven through the integrated CLI, not only direct unit tests.

## Fixed

- **Completed-workspace planning rejection.** A workspace that already completed its one allowed execution attempt now rejects a new `plan` immediately, with explicit guidance to run `workspace create`. Previously, a second `request`/`plan`/`confirm` cycle would silently succeed and only fail at `execute`, with a raw `InvalidWorkspaceTransitionError`. Enforced at the authoritative workflow layer (`ExecutionWorkflow.propose_execution`), not just in CLI text — no `ExecutionProposal` is ever built for the blocked case, and the workspace's own status/manifest are left untouched. The pre-existing `execute`-time guard remains as defense in depth.
- **`fake_runner_mode` no longer echoed under the real GAUSS backend**, where the field was previously always shown but meaningless.

## Added

- `InteractiveMvpAdapter` `request` modes `--fake-timeout` and `--fake-unknown-error`, for exercising timeout/uncataloged-error interpretation without a real GAUSS installation.
- Ten evaluation run files: `evaluations/runs/2026-07-30-code-assistant-execution-interpretation-run-001.md` through `-010.md`.
- `planning/v0.52.0-interpretation-evaluation-and-recovery-ux.md`.

## User-Facing Command Sequence

Recommended order after `execute`:

```text
interpret
stdout            (or stderr, when needed)
outputs
read <path>       (only when you need a specific file's contents)
provenance
reset             (before starting a new single-shot attempt)
```

`interpret` never reruns GAUSS, never edits code, and never reads files automatically. `reset` clears the adapter's current request/plan/result state but does not change a completed workspace's own status — a workspace that already completed its execution attempt needs `workspace create`, not `reset`, before another plan can succeed.

## Safety Boundaries (unchanged, re-verified)

Execution remains advisory-first and confirmation-gated. Interpretation remains deterministic, evidence-only, and never: launches GAUSS, retries, edits code, reads files automatically, or claims methodological/statistical validity from a successful run. Unknown GAUSS error codes remain generic and unspeculated. Fake-runner results are never presented as real GAUSS execution.

## Remaining Limitations

- Fake runner remains the default backend.
- Real execution verified on Windows/GAUSS 26.1.1 only.
- One workspace still supports exactly one completed execution attempt (by design — this release makes that boundary legible earlier, it does not remove it).
- No durable `ExecutionSession` integration.
- No automatic retry or autonomous correction; no code repair.
- Interpretation quality depends on captured evidence; unknown GAUSS error codes remain generic until verified and cataloged.
- Timeout evidence remains controlled/injected, not live-verified.

## Next Recommended Milestone

An expanded, evidence-backed GAUSS error catalog (additional real-verified error codes beyond `G0105`/`G0036`/`G0025`), rather than assisted debugging — this evaluation found no unresolved interpretation or recovery defects that would specifically motivate assisted debugging next.
