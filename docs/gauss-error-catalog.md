# GAUSS Error Catalog

This is the human-readable companion to `scripts/gauss_error_catalog.py`, the deterministic, code-driven source of truth. If this document and the module ever disagree, the module is correct — regenerate this page from it rather than editing this file to match a claim the code doesn't actually make.

An entry appears here only if it satisfies at least one of:

1. Reproduced against a real GAUSS runtime (this repository's own execution evidence).
2. Already present in this repository's execution evidence (even from an unrelated experiment).
3. Verified against official GAUSS/Aptech documentation.

Nothing here is a guess. An uncataloged `G####` code is not a gap in this document — it means this repository has not yet verified that code by any of the three routes above, and the interpreter reports it honestly as `unknown` rather than inventing a meaning.

## Verified Entries

### G0105 — Bad expression or missing arguments

- **Category:** Parse/Syntax
- **Execution phase:** Parsing
- **Verification:** Real Runtime + Official Documentation
- **Generic interpretation:** Execution stopped during parsing because GAUSS reported invalid syntax or a missing expression.
- **Recommended inspection step:** Inspect the reported syntax near the parser diagnostic.
- **Source:** Reproduced repeatedly via `tgauss.exe -b` (`planning/v0.28.0-real-gauss-invocation-research.md`; real evaluations in `v0.50.0`/`v0.52.0`) using `x = ;`. Official Aptech documentation confirms the same title and describes the same general causes (missing semicolons, unloaded library statements, locale-related parsing issues).

### G0036 — Matrix dimensions are incompatible

- **Category:** Matrix Dimensions
- **Execution phase:** Runtime
- **Verification:** Real Runtime + Official Documentation (with a documented wording discrepancy — see below)
- **Generic interpretation:** Execution reached runtime before GAUSS reported an operation using incompatible matrix dimensions.
- **Recommended inspection step:** Inspect stderr and verify matrix dimensions before the reported operation.
- **Source:** Reproduced via `tgauss.exe -b` (`planning/v0.29.0-runtime-error-output-file-verification.md`; real evaluations in `v0.50.0`/`v0.52.0`) using `x = ones(2,2); y = ones(3,1); z = x + y; print z;`.
- **Documentation discrepancy:** Official Aptech documentation titles this error "Matrices are not conformable," while every real runtime observation recorded in this repository shows the literal stderr text "Matrix dimensions are incompatible." This catalog uses the runtime-observed text for its title/explanation, per its own verification policy of preferring runtime evidence when the two disagree — the documentation wording is most likely a paraphrased page title rather than a literal runtime string, but that is not independently confirmed.

### G0025 — Undefined symbol

- **Category:** Runtime Computation
- **Execution phase:** Runtime
- **Verification:** Real Runtime + Official Documentation
- **Generic interpretation:** Execution reached runtime before GAUSS reported an undefined symbol.
- **Recommended inspection step:** Inspect stderr and the generated GAUSS script for the referenced symbol.
- **Source:** Reproduced via `tgauss.exe -b` (`planning/v0.29.0-runtime-error-output-file-verification.md`) using `print undefinedvar;`, producing `error G0025 : Undefined symbol: 'undefinedvar'` with file/line info. Official Aptech documentation confirms an identical title and message format (example shown there: `G0025 : Undefined symbol: 'nobs' [estimate.gss, line 6]`) and documents the same underlying causes (a symbol referenced before definition, an unloaded library, or a procedure GAUSS hasn't been told about).

### G0014 — File not found

- **Category:** File I/O
- **Execution phase:** Runtime
- **Verification:** Real Runtime + Official Documentation
- **Generic interpretation:** GAUSS could not locate a file referenced by the script — for example a data file, an included source file, or a script path argument.
- **Recommended inspection step:** Confirm the referenced file exists and is reachable from GAUSS's current working directory or `SRC_PATH`, or supply an explicit full path.
- **Source:** Observed via `tgauss.exe -b` during `v0.28.0`'s non-interactive-invocation research (`planning/v0.28.0-real-gauss-invocation-research.md`). The specific test that produced it was an inconclusive `-e`-flag argument-parsing experiment, not an intentional file-not-found reproduction — but the resulting error text (`error G0014 : File not found '1+1;', line 1`) is genuine, unmodified GAUSS output. Official Aptech documentation independently confirms G0014 as "File not found," triggered when GAUSS cannot locate a referenced file in its current working directory or any directory in `SRC_PATH`.

### G0290 — Library not found

- **Category:** Package or Library
- **Execution phase:** Startup
- **Verification:** Official Documentation only — not yet reproduced against a real GAUSS runtime in this repository.
- **Generic interpretation:** GAUSS could not find a required application/library file (an `.lcg` library), typically because the corresponding GAUSS application module is not installed, or is not present under the active `GAUSSHOME` directory.
- **Recommended inspection step:** Confirm the required GAUSS application/library is installed under `GAUSSHOME` for the active GAUSS version before rerunning.
- **Source:** Aptech support content documents G0290 as "Library not found," occurring when a required application `.lcg` library file is missing from the active `GAUSSHOME` installation (e.g. an uninstalled application module such as `optmum`, `comt`, or `tsmt`).

## Future Placeholders (Not Yet Cataloged)

These categories exist in `gauss_error_catalog.GaussErrorCategory` because the interpreter's classification model anticipates them, but **no code is cataloged under them yet** — they are not documented here as if they were:

- **Numerical** — no verified error code yet.
- **Startup or Licensing** — GAUSS License Manager errors are documented by Aptech, but without a confirmed `G####` code format comparable to the entries above; not added speculatively.
- **User Interruption** — no verified error code yet (e.g. a user-initiated `Ctrl+C`/break during a run).
- **Timeout** — not a GAUSS error code at all; it is an interpreter-level classification applied when execution evidence reports `execution_status: timed_out`, whether from a real, observed runtime timeout or from simulated/injected evidence. The interpreter's own wording always distinguishes which kind of timeout evidence it is describing (see `gauss_execution_interpreter.interpret_execution`'s timeout branch) rather than implying a live GAUSS timeout occurred when it did not.
- **Unknown** — the deliberate fallback for any `G####` code not in this catalog. It is not a placeholder to be "filled in" by guessing; it is preserved permanently as the honest answer for genuinely unverified codes.

## Adding a New Entry

1. Establish verification via one of the three accepted routes (real runtime reproduction, existing repository evidence, or official documentation) — never from memory or inference alone.
2. Add a `GaussErrorCatalogEntry` to `scripts/gauss_error_catalog.py`'s `_ENTRIES` tuple, including a `verification_status` tuple and a `verification_source` citation.
3. If official documentation and observed runtime evidence disagree, keep runtime evidence as authoritative for `title`/`generic_explanation` and record the disagreement in `documentation_discrepancy` — never silently pick one without saying so.
4. Add or extend a test in `scripts/test_gauss_execution_interpreter.py` proving the new entry is looked up and classified correctly.
5. Update this document to match — by hand, since this file is not auto-generated.

No interpreter code should need to change to add a new entry; `gauss_execution_interpreter.interpret_execution(...)` only looks codes up in the catalog.
