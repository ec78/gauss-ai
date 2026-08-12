# Alpha Demo

A minimal, two-file scenario for exercising the guided repair workflow (`gauss-ai repair`) end to end, in fake mode, with no GAUSS installation required.

## Files

- **`working.gss`** — a valid, minimal GAUSS script (`x = 2 + 2; print x;`). Included as a baseline: running the guided workflow against it demonstrates the "nothing to repair" path (`repair-plan` reports `successful_execution_no_repair_needed`, and the guided command stops immediately after showing the session summary).
- **`broken.gss`** — an incomplete assignment (`x = ;` instead of `x = 2 + 2;`). This is the **exact** fault class this repository's verified error catalog documents for `G0105` ("Bad expression or missing arguments") — reproduced directly against real GAUSS 26.1.1 as part of `v0.68.0`'s own real-GAUSS alpha validation, not merely inherited from the catalog's own separate verification.

Both files use only GAUSS syntax already verified by this repository's own evidence (`scripts/gauss_error_catalog.py`'s `G0105` entry). Neither file contains any destructive operation, file I/O, network access, or package/license activation.

**`v0.68.0` correction**: an earlier version of `broken.gss` used `x = 2 + 2` (a valid expression missing only its trailing semicolon) rather than the catalog's own exact verified trigger (`x = ;`, an incomplete right-hand side). Real-GAUSS validation in `v0.68.0` found that the earlier content actually produced a *different*, uncataloged real error (`G0008`, "Syntax error 'print'") rather than `G0105` — the system correctly and safely disclosed this as an uncataloged error with no fabricated cause or repair strategy, but the example itself no longer matched its own documented, real-verified fault class. `broken.gss` was corrected to the catalog's exact verified trigger, and re-confirmed end to end (real execution → diagnosis → repair → real verification → review) against real GAUSS 26.1.1.

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
5. Show an AI-generated repair-draft candidate (`v0.69.0`) for review -- `broken.gss` matches this repository's own verified `G0105` empty-assignment pattern exactly, so a candidate proposing `x = 0;` on line `1` is generated automatically. Accept it, edit its replacement text, or reject it and describe the replacement by hand instead.
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
