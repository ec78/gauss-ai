# Real GAUSS Alpha Testing Guide

This guide is for manual testers who want to exercise the interactive adapter with real local GAUSS execution.

Fake execution remains the default alpha path. Use real mode only when you intentionally want a local `tgauss` process to run after confirmation.

## Prerequisites

- A local terminal GAUSS executable named `tgauss` or `tgauss.exe`.
- A workspace parent directory where temporary alpha workspaces may be created.
- Comfort running a terminal command.

The currently verified invocation evidence in this repository is Windows-oriented and based on `tgauss.exe -b <script>`.

## Start Real Mode

```text
python scripts/gauss_code_assistant_cli.py --runner gauss --gauss-executable C:\gauss26\tgauss.exe
```

You may also set:

```text
GAUSS_EXECUTABLE=C:\gauss26\tgauss.exe
python scripts/gauss_code_assistant_cli.py --runner gauss
```

If both are present, `--gauss-executable` wins.

Startup should show:

```text
Execution backend: REAL_GAUSS
GAUSS executable: ...
```

If the executable is missing, not a file, or named like the GUI executable `gauss.exe`, startup blocks with `ERROR runner_configuration`.

## Minimal Smoke Flow

```text
workspace create
request x = 2 + 2; print x;
plan
confirm <request_hash shown by plan>
execute
outputs
provenance
exit
```

Before confirmation, inspect the plan for:

- `execution_backend: REAL_GAUSS`
- `real_gauss_will_run_after_confirm_execute: true`
- `workspace_id`
- `working_directory`
- `executable_path`
- `timeout_seconds`
- `request_hash`
- `script_path: inline code; ... generated ... at execution time`

The exact generated `.gss` script path is reported after execution because the existing helper creates it at execution time inside the workspace.

## Expected Boundaries

- `execute` before `confirm` must fail.
- A stale or wrong hash must fail.
- Real mode must not fall back to fake mode.
- Successful execution may still not prove statistical or methodological validity.
- `outputs` must show metadata only.
- File contents require `read <relative-path>`.
- Stdout/stderr contents are not printed automatically; the adapter reports lengths and process metadata.
- Use `stdout` and `stderr` when you explicitly want to inspect captured process text after execution.

## Feedback

Use `docs/alpha-feedback-template.md` for structured feedback. For real-mode testing, include:

- OS and GAUSS version.
- Exact startup command.
- Whether `Execution backend: REAL_GAUSS` appeared.
- Whether `gauss_ran` was `true`, `false`, or surprising.
- Exit code, timeout state, and generated script path.
- Any confusing confirmation, output, or provenance text.
