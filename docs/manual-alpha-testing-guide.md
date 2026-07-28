# Manual Alpha Testing Guide

This guide tests the `v0.47.0`/`v0.48.0` interactive adapter path. It does not run GAUSS.

## Prerequisites

- Python available as `python`.
- Repository checkout available locally.
- Run commands from the repository root.
- No GAUSS installation is required for this alpha harness.

## Launch

```text
python scripts/gauss_code_assistant_cli.py
```

Optional workspace parent:

```text
python scripts/gauss_code_assistant_cli.py --workspace-parent .gauss-ai-alpha-workspaces
```

## Supported Commands

- `help`
- `workspace create`
- `workspace status`
- `request [--fake-success|--fake-failure] <GAUSS code or short request>`
- `plan`
- `confirm <request_hash>`
- `decline`
- `execute`
- `outputs`
- `read <relative-path>`
- `provenance`
- `status`
- `reset`
- `exit`

## First-Run Walkthrough

```text
help
workspace create
workspace status
```

Pass criteria:

- Help lists the commands.
- Workspace creation reports `REAL_WORKFLOW`.
- Workspace status is `ready`.
- No output claims that GAUSS has run.

## Successful Workflow

```text
workspace create
request --fake-success x = 2 + 2; print x;
plan
confirm <request_hash shown by plan>
execute
outputs
read fake-output.txt
provenance
status
exit
```

Pass criteria:

- `plan` shows `request_hash`, `plan_digest`, `code_digest`, `workspace_id`, `orchestration_instance_id`, and the confirmation command.
- `execute` is accepted only after confirmation.
- `execute` says `FAKE_RUNNER` and `GAUSS was not run`.
- `outputs` reports metadata only.
- `read fake-output.txt` returns content between `content_begin` and `content_end`.
- `provenance` shows workspace and execution identifiers and the durable-session caveat.
- `status` includes `gauss_ran: false`.

## Confirmation Test

```text
workspace create
request --fake-success x = 2 + 2; print x;
plan
execute
```

Pass criteria:

- Execution is rejected before confirmation.
- No fake runner output appears.

Then confirm with the displayed hash:

```text
confirm <request_hash shown by plan>
execute
```

Pass criteria:

- Confirmation is accepted.
- Execution proceeds with the fake runner.

## Decline Test

```text
workspace create
request --fake-success x = 2 + 2; print x;
plan
decline
execute
```

Pass criteria:

- `decline` reports an unaccepted/cancelled confirmation path.
- `execute` after decline is rejected.

Recovery:

```text
request --fake-success z = 9; print z;
plan
confirm <new request_hash>
execute
```

Pass criteria:

- A fresh request/proposal can proceed.
- The prior declined confirmation is not reused.

## Stale Confirmation Test

```text
workspace create
request --fake-success x = 2 + 2; print x;
plan
```

Save the displayed hash, then change the request:

```text
request --fake-success y = 5; print y;
plan
confirm <old request_hash>
```

Pass criteria:

- The old hash is rejected.
- No execution occurs.

## Fake-Failure Recovery Test

```text
workspace create
request --fake-failure x = bad;
plan
confirm <request_hash>
execute
status
provenance
reset
workspace create
request --fake-success x = 2 + 2; print x;
plan
confirm <request_hash>
execute
outputs
```

Pass criteria:

- Fake failure reports `execution_status: failed` and `runtime_error_detected: True`.
- Provenance remains available and does not fabricate artifacts.
- A fresh workspace can complete a later success flow.

## Output Metadata Versus Explicit Reading

After a successful fake execution:

```text
outputs
read fake-output.txt
```

Pass criteria:

- `outputs` lists metadata only and does not print file content.
- `read fake-output.txt` is the first command that prints file content.

## Path-Boundary Test

After a successful fake execution:

```text
read ../outside.txt
read C:/outside.txt
read fake-output.txt
```

Pass criteria:

- Traversal is rejected with `path_escapes_workspace`.
- Absolute path is rejected with `path_not_relative`.
- Valid relative file read succeeds.

## Provenance Test

```text
provenance
```

Pass criteria:

- Provenance reports workspace, execution-session alias, execution instance, and artifact count.
- It states that `execution_session_reference` is not a durable `ExecutionSession` ID yet.

## Reset And Fresh Workspace Behavior

Use `reset` to clear the active request/proposal/result while retaining the workspace reference. If the retained workspace has completed an execution, use `workspace create` before another execution.

## Expected Disclosures

The adapter should consistently disclose:

- it is using a deterministic fake runner;
- GAUSS is not run;
- execution requires explicit confirmation;
- output metadata is not file content;
- file content requires explicit `read`;
- successful execution is not methodology validation;
- `execution_session_reference` is not a durable `ExecutionSession` ID yet.

## Recording Issues

Use `docs/alpha-feedback-template.md` for every observation. Include the exact command sequence, expected behavior, observed behavior, and severity.

## Current Limitations

- Fake-runner-only execution.
- Local process-scoped state.
- Limited adapter-driven request interpretation.
- No real GAUSS execution.
- No durable `ExecutionSession` integration.
- No Claude Code/Codex chat adapter.
- No uploads, cloud execution, persistence, multi-user ACLs, or binary/PDF/image/spreadsheet readers.
