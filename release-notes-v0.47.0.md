# v0.47.0 - Interactive MVP Adapter

Summary: Adds the first local terminal entry point for manually testing the real GAUSS Code Assistant MVP workflow without writing Python glue.

## Added

- `scripts/gauss_code_assistant_cli.py`: an interactive terminal adapter around `GaussCodeAssistantWorkflow`.
- `scripts/test_gauss_code_assistant_cli.py`: 18 deterministic command-handler and transcript-style tests.
- `planning/v0.47.0-interactive-mvp-adapter.md`: implementation scope, architecture, safety model, and acceptance criteria.
- `41.x` Interactive MVP Adapter benchmark prompts and `Not Run` coverage rows.

## Adapter Capabilities

- Create and ready a local workspace beneath an approved parent directory.
- Accept a request and propose an execution plan through the existing MVP facade.
- Require `confirm <request_hash>` before execution.
- Reject stale or mismatched confirmation through the existing workflow validation path.
- Execute with a deterministic fake runner by default.
- List output metadata without reading file contents.
- Read a workspace file only through an explicit `read <relative-path>` command.
- Display trace identifiers and provenance.

## Explicit Non-Goals

- No durable `ExecutionSession` integration.
- No `begin_analysis()` wiring.
- No real GAUSS execution from the adapter.
- No uploads, cloud services, persistent sessions, multi-user ACLs, binary/PDF/image/spreadsheet readers, autonomous execution, autonomous file reading, or natural-language agent framework.

## Validation

Default adapter execution is fake-runner only and does not run GAUSS.

Release validation for this tag should include:

```text
python scripts/test_gauss_code_assistant_cli.py
python scripts/test_code_assistant_mvp_workflow.py
python scripts/test_gauss_execution_workflow.py
python scripts/test_gauss_execution_session.py
python scripts/test_gauss_workspace.py
python scripts/test_workspace_execution_integration.py
python scripts/test_gauss_workspace_file_reader.py
python scripts/test_workspace_file_read_integration.py
python scripts/test_gauss_runtime_orchestration.py
python scripts/check_evaluation_tracking.py --json
python scripts/check_release_readiness.py --json
```

## Remaining Limitations

- Fake runner is the default and the only adapter execution mode in this milestone.
- CLI state is process-local and not persistent across sessions.
- Request interpretation is limited and adapter-driven.
- `execution_session_reference` still means `orchestration_instance_id`, not a durable `ExecutionSession` ID.
- A completed workspace is single-shot for execution; create a fresh workspace for another run.
