# GAUSS AI v0.49.0 - Opt-In Real GAUSS Execution

This release connects the Interactive MVP Adapter to real local GAUSS execution as an explicit alpha-testing option.

## Highlights

- Added `--runner fake|gauss` to `scripts/gauss_code_assistant_cli.py`.
- Kept the deterministic fake runner as the default.
- Added real-runner startup validation for `--gauss-executable` or `GAUSS_EXECUTABLE`.
- Restricted real mode to terminal `tgauss`/`tgauss.exe` executables.
- Routed real execution through the existing `gauss_code_execution.execute_gauss_code(...)` helper.
- Preserved hash-bound confirmation before execution.
- Added backend, process, timeout, exit-code, stdout/stderr length, generated-script, output, and provenance disclosures.
- Added `scripts/test_gauss_code_assistant_real_runner.py` with no-GAUSS default tests and an explicit optional local smoke gate.
- Added `docs/real-gauss-alpha-testing-guide.md`.

## What This Enables

Manual alpha testers can now run:

```text
python scripts/gauss_code_assistant_cli.py --runner gauss --gauss-executable C:\gauss26\tgauss.exe
```

Then use the same workflow:

```text
workspace create
request x = 2 + 2; print x;
plan
confirm <request_hash>
execute
outputs
read <relative-path>
provenance
```

## Safety Notes

- No silent fallback from real GAUSS mode to fake mode.
- No automatic execution before confirmation.
- No automatic retry or repair.
- No automatic file reading.
- No stdout/stderr content display by default.
- Output-file contents still require explicit `read`.
- `gauss_ran=true` is reported only when the helper reports that execution actually occurred.
- Successful GAUSS execution is not treated as methodology validation.

## Still Not Included

- Durable execution-session integration.
- Claude Code/Codex chat adapter.
- Uploads.
- Cloud execution.
- Autonomous execution or file reading.
- GUI GAUSS executable support.
- Production-grade cross-platform execution guarantees.

## Validation

- Default no-GAUSS real-runner adapter tests passed.
- Existing MVP/workflow/workspace/file-reader/orchestration tests passed.
- Release-readiness default checks passed.
- Optional local real smoke passed against `C:\gauss26\tgauss.exe`.
- Formal `42.x` benchmark evaluations are not yet recorded; their coverage rows remain `Not Run` intentionally.
