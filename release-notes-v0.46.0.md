# v0.46.0 - Safe File Reading and MVP Workflow Evaluation

Summary: Evaluated all 20 previously-`Not Run` `39.x`/`40.x` benchmark prompts against real, currently-composed repository behavior. 20/20 Passed, 0 Critical, 0 Major, 1 Minor. No implementation code was modified. Produced a planning-only session-integration readiness assessment for a future `v0.47.0`.

## Evaluated

- `39.x` Safe Workspace File Reading (`39.1`-`39.10`): 10/10 Passed, all scored 4.0.
- `40.x` GAUSS Code Assistant MVP Workflow (`40.1`-`40.10`): 10/10 Passed. `40.6` scored 3.8 (Explanation Quality: 3) on a documented Minor finding — a decline message's wording was somewhat redundant; the underlying safety contract (decline, specific reason, no silent workspace creation) held exactly as designed.
- A dedicated verification harness (fake runners, disposable temp-directory-backed `WorkspaceRegistry`/`OrchestrationStateStore` instances, controlled fixture files) exercised `gauss_workspace.py`, `gauss_workspace_file_reader.py`, `gauss_execution_workflow.py`, and `gauss_code_assistant_workflow.py` for real, evidence-grounded results — never inferred from the existing unit test suites' pass/fail status.

## Found

- A genuine architectural fact, not a defect: a workspace's own seven-state lifecycle supports exactly one execution attempt. Re-executing against an already-`completed` workspace correctly raises `InvalidWorkspaceTransitionError`, confirmed directly by re-execution during evaluation. This is relevant evidence for the `v0.47.0` readiness question of whether a session can span multiple execution instances.

## Added

- `planning/v0.46.0-safe-file-reading-mvp-evaluation.md`: the evaluation plan (method, rubric, defect classification, evidence requirements).
- 20 evaluation run files (`evaluations/runs/2026-07-23-code-assistant-safe-file-reading-run-001.md` through `-010.md`; `evaluations/runs/2026-07-23-code-assistant-mvp-workflow-run-001.md` through `-010.md`).
- `planning/v0.47.0-session-integration-readiness.md`: a planning-only assessment of wiring `gauss_execution_session.ExecutionSession` into `gauss_execution_workflow.py`/`gauss_code_assistant_workflow.py` — documents the current `execution_session_reference`-means-`orchestration_instance_id` mismatch, the desired request→session→instance relationship, and a narrowly bounded recommended `v0.47.0` implementation scope. **No durable session integration is implemented.**

## Safety

- No implementation code was modified — the single Minor finding did not meet this milestone's own bar for a code change (documented safety-contract violation, localized fix, no redesign, full test coverage, disclosed in the final report), since the safety contract itself held throughout.
- Every evaluation used only fake runners, disposable temp directories, and controlled fixtures — no real GAUSS was run, no network access occurred.

## Testing

Full regression suite unchanged and passing: `gauss_workspace` (24/24), `test_workspace_execution_integration` (18/18), `gauss_workspace_file_reader` (25/25), `test_workspace_file_read_integration` (6/6), `test_code_assistant_mvp_workflow` (15/15), `gauss_execution_session` (26/26), `gauss_execution_workflow` (60/60), `gauss_runtime_orchestration` (95/95), `gauss_orchestration_state_store` (52/52), `gauss_execution_adapter` (31/31).

`python scripts/check_evaluation_tracking.py --json` → 364 prompt IDs, 364 coverage rows, 351 run files referenced, 356 index entries, 0 errors, `overall_pass: true` (2 known historical warnings unchanged). `python scripts/check_release_readiness.py --json` → `default_pass: true`, `overall_pass: true`.

## Limitations

- `execution_session_reference` still means `orchestration_instance_id`, not a real `gauss_execution_session.ExecutionSession` — unchanged since `v0.40.0`.
- A workspace supports exactly one execution attempt today — confirmed, not yet addressed.
- No uploads, persistent storage, cloud execution, multi-user support, binary file readers, PDF/image parsing, autonomous execution, or autonomous file reading.
- `v0.47.0` durable session integration is planned but not authorized for implementation.
