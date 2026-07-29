# Real GAUSS Debugging Alpha Guide

Use this guide to test failed real GAUSS runs through the interactive adapter.

## Prerequisites

- A local terminal GAUSS executable, usually `tgauss.exe` on Windows.
- A workspace parent directory for disposable alpha workspaces.
- The repository checked out locally.

Example local launch:

```text
python scripts/gauss_code_assistant_cli.py --runner gauss --gauss-executable C:\gauss26\tgauss.exe --workspace-parent .gauss-ai-alpha-workspaces
```

`C:\gauss26\tgauss.exe` is an example from local evaluation evidence, not a universal path.

## Safe Success Test

```text
workspace create
request x = 2 + 2; print x;
plan
confirm <request_hash>
execute
interpret
stdout
stderr
provenance
```

Expected:

- `execution_backend: REAL_GAUSS`
- `gauss_ran: true`
- `execution_status: completed`
- `exit_code: 0`
- `stdout` shows `4.0000000`

## Syntax-Error Test

```text
workspace create
request x = ;
plan
confirm <request_hash>
execute
interpret
stdout
stderr
read <generated-script-relative-path>
```

Expected:

- `gauss_ran: true`
- `execution_status: failed`
- `stdout` may show `Program execute failed`
- `stderr` should show the GAUSS error text, such as `G0105`
- No retry occurs automatically
- A fix requires a new request, plan, confirmation, and usually a fresh workspace

## Runtime-Error Test

```text
workspace create
request x = ones(2,2); y = ones(3,1); z = x + y; print z;
plan
confirm <request_hash>
execute
interpret
stderr
read <generated-script-relative-path>
```

Expected:

- `gauss_ran: true`
- `execution_status: failed`
- `stderr` should show a runtime error such as `G0036 : Matrix dimensions are incompatible`
- The error is execution evidence, not proof that a statistical method is invalid

## Output-File Test

```text
workspace create
request output file = gauss_output.txt reset; x = 12345; print x; output off;
plan
confirm <request_hash>
execute
interpret
outputs
read gauss_output.txt
```

Expected:

- `outputs` lists metadata only
- `read gauss_output.txt` is required to see content
- The artifact remains inside the active workspace

## Inspecting Evidence

- `stdout`: displays captured stdout after explicit request.
- `stderr`: displays captured stderr after explicit request.
- `interpret`: explains the current execution result from already-captured evidence. It never reruns GAUSS, retries, edits code, or reads output files automatically.
- `outputs`: lists produced file metadata only.
- `read <relative-path>`: reads supported text files inside the workspace, including generated `.gss` scripts and output `.txt` files.
- `provenance`: reports backend, `gauss_ran`, process exit code, timeout state, workspace ID, execution reference, and artifact metadata.

## State Meanings

- Blocked before launch: `gauss_ran: false`; examples include missing executable, invalid executable, execute-before-confirmation, stale confirmation, and completed-workspace reuse.
- Launched and completed: `gauss_ran: true`, `execution_status: completed`.
- Launched and failed: `gauss_ran: true`, `execution_status: failed`; inspect `stdout` and `stderr`.
- Timed out: `execution_status: timed_out`; real-process timeout coverage is not yet verified by this milestone.

## Recovery After Failure

Use a new request and fresh confirmation for any corrected code. If the retained workspace has already completed or failed, run:

```text
workspace create
```

before the next execution attempt.

## Current Limitations

- No automatic correction.
- No automatic retry.
- No durable `ExecutionSession` integration.
- No Claude Code/Codex chat adapter.
- Timeout behavior has not been verified with a real bounded GAUSS timeout fixture.
- Execution success does not establish statistical or methodological correctness.

## Issue Reporting

Record:

- Backend and launch command.
- Workspace ID.
- Request hash.
- `gauss_ran`.
- Execution status, exit code, timeout state, duration.
- Stdout/stderr lengths and relevant explicit output.
- Generated script path.
- Output metadata and whether explicit `read` was used.
- Whether the next recovery step was obvious.
