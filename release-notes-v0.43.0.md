# v0.43.0 - Workspace Integration with Execution Workflow

Summary: Connected the workspace abstraction with the GAUSS execution workflow.

## Added

- Workspace-aware execution requests: `ExecutionWorkflow.propose_execution(...)` accepts an optional `workspace_id`; `ExecutionProposal` gained a `workspace_id` reference field.
- Workspace validation: a missing, deleted, or archived workspace blocks a proposal; a `working_directory`/`output_directory` that escapes the workspace root is rejected the same way.
- Workspace-bound execution context: `execute(...)` drives the workspace's own `ready → executing → completed` lifecycle around invocation, and re-validates the workspace immediately before invoking (never touching the runner if the workspace no longer permits execution).
- Output provenance tracking: a new `WorkspaceProvenance` type (`workspace_id`, `execution_session_id`, `execution_instance_id`, metadata-only `artifacts`) is attached to every workspace-bound `ResponseReadyResult` and registered into the workspace's own manifest automatically.

## Safety

- Bounded execution paths — every workspace-derived `working_directory`/`output_directory` is validated to resolve inside the workspace's own root via `WorkspaceRegistry.resolve_within_workspace(...)`; no path traversal or outside-workspace write is possible through this integration.
- Workspace isolation — two workspaces registered in the same registry remain fully independent through proposal, confirmation, and execution; advancing or executing against one never affects another.
- Metadata/content separation — `WorkspaceProvenance.artifacts` carries only `ManifestFileEntry` metadata (name, relative path, size, source, creation state); no field anywhere in this integration can hold file content.
- Fail-closed workspace guard — if a workspace is deleted or archived between confirmation and execution, `execute(...)` raises `WorkspaceExecutionGuardError`/`InvalidWorkspaceTransitionError` before the runner is ever called.
- Fully additive and backward compatible — every existing `ExecutionWorkflow` caller that never supplies `workspace_registry`/`workspace_id` keeps its exact prior behavior; supplying `workspace_id` without a configured `workspace_registry` raises immediately rather than silently ignoring it.

## Testing

Actual results from this milestone's own validation run:

```
$ python scripts/test_workspace_execution_integration.py
...
18 test function(s) run, 0 check failure(s).
ALL CHECKS PASSED.

$ python scripts/check_release_readiness.py --json
{
  "default_checks": [
    {"script": "validate_all_evidence.py", "passed": true, "returncode": 0},
    {"script": "check_evaluation_tracking.py", "passed": true, "returncode": 0}
  ],
  "default_pass": true,
  "overall_pass": true
}
```

No regressions in existing suites: `scripts/test_gauss_workspace.py` (24/24), `scripts/test_gauss_execution_session.py` (26/26), `scripts/test_gauss_execution_workflow.py` (60/60), `scripts/test_gauss_runtime_orchestration.py` (95/95), `scripts/test_gauss_orchestration_state_store.py` (52/52) all still pass unchanged.

## Limitations

- No file uploads — there is still no transport for a user to place a file into a workspace.
- No artifact persistence — `workspace_id`-to-instance association and computed provenance are process-local and in-memory-only; nothing is durably stored.
- No cloud storage.
- No multi-user permissions — workspace ownership remains an unvalidated, opaque reference only.
- No automatic execution changes — nothing about how or when GAUSS itself runs is affected; this milestone only bounds *where* an already-confirmed execution may write.
- `workspace_id` is not part of `request_hash` — a disclosed, deliberate design choice; folding it in would require modifying the underlying controller's hash-included field list, out of scope here.
- `gauss_execution_session.py`'s `ExecutionSession` remains unwired to this integration.

This milestone does not claim functionality beyond what is described above.
