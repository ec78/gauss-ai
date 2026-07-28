# v0.48.0 - Interactive Adapter Evaluation and Alpha Readiness

Summary: Evaluates the `v0.47.0` Interactive MVP Adapter against the `41.x` benchmark category and prepares structured manual alpha testing materials.

## Added

- `planning/v0.48.0-interactive-adapter-evaluation.md`: evaluation method, transcript coverage, benchmark result summary, alpha-readiness decision, and next-step recommendation.
- `docs/manual-alpha-testing-guide.md`: launch command, walkthroughs, supported commands, pass/fail criteria, expected disclosures, and limitations.
- `docs/alpha-feedback-template.md`: standard observation template for manual alpha testers.
- Ten `41.x` evaluation run files for the Interactive MVP Adapter category.

## Updated

- `evaluations/benchmark-coverage.md`: `41.1`-`41.10` moved from `Not Run` to `Passed`.
- `evaluations/runs/INDEX.md`: added the ten `41.x` run files.
- `evaluations/EVALUATION_DASHBOARD.md`: updated current milestone, guard counts, category summary, and current-warning notes for `v0.48.0`.
- README, roadmap, known limitations, changelog, and manual testing template updated for alpha-readiness status.

## Evaluation Result

- `41.x` Interactive MVP Adapter benchmarks: 10/10 Passed.
- Overall score: 10 at 4.0.
- Critical defects: 0.
- Major defects: 0.
- Minor defects: 0.
- Implementation fixes: none.
- GAUSS invocations: 0.

## Alpha-Readiness Classification

**Ready for structured manual alpha testing.**

The adapter supports a complete terminal alpha workflow through the real MVP facade: workspace bootstrap, request capture, planning, hash-bound confirmation, fake execution, output metadata inspection, explicit file reading, provenance, status, reset, and exit.

## Remaining Limitations

- Fake-runner-only execution.
- Process-local CLI state.
- Limited adapter-driven request interpretation.
- `WorkflowResult.execution_session_reference` still refers to an orchestration instance ID, not a durable `ExecutionSession`.
- A completed workspace remains single-shot for execution.
- No real GAUSS execution, durable session integration, chat adapter, uploads, persistence, cloud execution, multi-user ACLs, or binary/PDF/image/spreadsheet readers.

## Validation

Release validation should include:

```text
python -B scripts/test_gauss_code_assistant_cli.py
python -B scripts/test_code_assistant_mvp_workflow.py
python -B scripts/test_gauss_execution_workflow.py
python -B scripts/test_gauss_execution_session.py
python -B scripts/test_gauss_workspace.py
python -B scripts/test_workspace_execution_integration.py
python -B scripts/test_gauss_workspace_file_reader.py
python -B scripts/test_workspace_file_read_integration.py
python -B scripts/test_gauss_runtime_orchestration.py
python -B scripts/check_evaluation_tracking.py --json
python -B scripts/check_release_readiness.py --json
```

No validation command should run GAUSS.
