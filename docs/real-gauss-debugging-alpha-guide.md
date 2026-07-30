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

- Blocked before launch: `gauss_ran: false`; examples include missing executable, invalid executable, execute-before-confirmation, and stale confirmation.
- Blocked before a new plan even exists (`v0.52.0`): attempting `request`/`plan` again against a workspace that already completed its one execution attempt is now rejected at `plan` itself, with `workspace_single_shot_exhausted: true` and explicit `workspace create` guidance — no confirmable plan is ever built for it, and the workspace's own completed status and manifest are left untouched.
- Launched and completed: `gauss_ran: true`, `execution_status: completed`.
- Launched and failed: `gauss_ran: true`, `execution_status: failed`; inspect `stdout` and `stderr`.
- Timed out: `execution_status: timed_out`; real-process timeout coverage is not yet verified by this milestone.

## Recovery After Failure

Use a new request and fresh confirmation for any corrected code. If the retained workspace has already completed or failed, run:

```text
workspace create
```

before the next execution attempt. As of `v0.52.0`, attempting `request`/`plan` again against a completed workspace is rejected immediately at `plan` (before any confirmable plan exists), with an explicit message telling you to run `workspace create`.

`reset` and `workspace create` are not the same thing: `reset` only clears the current request/plan/confirmation/result state on the adapter — it does not change the underlying workspace's own completed status. If the active workspace has already completed its one execution attempt, `reset` alone will not let you plan again; you need `workspace create` for a fresh, single-shot-eligible workspace. Before you `reset`, you can still freely re-inspect `interpret`, `stdout`, `stderr`, and `provenance` for the just-finished execution as many times as you like — none of those commands are destructive; `reset` (or starting a new `request`) is what clears that adapter-local view.

## Testing Recovery and Interpretation Without Real GAUSS

`InteractiveMvpAdapter`'s fake runner (the default backend) supports four deterministic `request` modes for exercising `interpret` and recovery behavior without a GAUSS installation:

```text
request --fake-success x = 2 + 2; print x;
request --fake-failure x = ;
request --fake-timeout x = 2 + 2; print x;
request --fake-unknown-error x = 2 + 2; print x;
```

`--fake-timeout` returns a controlled `execution_status: timed_out` result without launching any process. `--fake-unknown-error` returns a fixed, deliberately uncataloged `error G9999 : ...` result, useful for confirming that `interpret` reports an error code it doesn't recognize as `unknown` rather than guessing. Neither mode is real GAUSS evidence, and `interpret`'s own output makes that distinction explicit via `launch_status`.

## Current Limitations

- No automatic correction.
- No automatic retry.
- No durable `ExecutionSession` integration.
- No Claude Code/Codex chat adapter.
- Timeout behavior has not been verified with a real bounded GAUSS timeout fixture; `--fake-timeout` remains a controlled/injected result, not live evidence.
- Execution success does not establish statistical or methodological correctness.
- Interpretation is deterministic and evidence-bound; it explains, but does not repair, GAUSS code, and unknown GAUSS error codes remain generic (`unknown`) until verified and added to `scripts/gauss_error_catalog.py`.

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
