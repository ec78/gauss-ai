# Alpha Demo

A minimal, two-file scenario for exercising the guided repair workflow (`gauss-ai repair`) end to end, in fake mode, with no GAUSS installation required.

## Files

- **`working.gss`** — a valid, minimal GAUSS script (`x = 2 + 2; print x;`). Included as a baseline: running the guided workflow against it demonstrates the "nothing to repair" path (`repair-plan` reports `successful_execution_no_repair_needed`, and the guided command stops immediately after showing the session summary).
- **`broken.gss`** — the same script with its statement terminator removed from the first line (`x = 2 + 2` instead of `x = 2 + 2;`). This is the exact fault class this repository's verified error catalog documents for `G0105` ("Bad expression or missing arguments") — a missing semicolon on the reported line or the line before it.

Both files use only GAUSS syntax already verified by this repository's own evidence (`scripts/gauss_error_catalog.py`'s `G0105` entry, reproduced via real `tgauss.exe -b` invocation per `planning/v0.28.0-real-gauss-invocation-research.md`). Neither file contains any destructive operation, file I/O, network access, or package/license activation.

## Expected workflow (fake mode)

```
gauss-ai repair examples/alpha-demo/broken.gss --fake-result failure
```

Fake mode cannot infer success or failure from the file's real content (there is no real GAUSS parser behind it), so `--fake-result failure` tells the deterministic fake runner to report the same class of failure a real run of this file would produce. Omit the flag (or pass `--fake-result success`) to see the "nothing to repair" path instead.

The guided command will:

1. Create a workspace and copy `broken.gss` into it (the original file is never modified).
2. Propose an execution plan from the file's real content and ask you to confirm it.
3. Execute (fake), interpret, and diagnose the result.
4. Propose a repair strategy and ask you to approve it.
5. Ask you to describe the replacement: line `1`, replacement text `x = 2 + 2;`.
6. Ask you to approve the resulting draft, then approve applying it.
7. Re-verify the application gate's checkable preconditions and apply the repair inside the workspace copy.
8. Ask whether to verify the repair by executing the repaired file, then ask you to confirm that execution.
9. Ask for your review decision (`accepted` / `rejected` / `inconclusive`) on the resulting evidence.
10. Show the complete repair-session summary.

## Expected error category

`G0105` — Bad expression or missing arguments (parse/syntax category, `high` classification confidence). See `docs/gauss-error-catalog.md` for the full, evidence-sourced entry.

## Expected repair stages reached

Every stage in the pipeline: execution → interpretation → diagnosis → repair planning → strategy approval → repair draft → draft approval → application approval → application gate → repair application → verification execution → comparison → human verification review → repair session summary. Nothing is skipped for `broken.gss`, since a real (fake-simulated) failure genuinely occurred.

## Real-mode variant

With a configured terminal GAUSS executable (`gauss-ai config set gauss-executable <path>` or `gauss-ai init`), the same command without `--fake-result` runs the real file through a real GAUSS invocation:

```
gauss-ai repair examples/alpha-demo/broken.gss --runner gauss
```

This requires `--runner gauss` (or a configured default runner of `gauss`) and a valid, configured terminal (`tgauss`/`tgauss.exe`) executable — see `docs/alpha-installation.md`.
