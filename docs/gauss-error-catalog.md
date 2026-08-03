# GAUSS Error Catalog

This is the human-readable companion to `scripts/gauss_error_catalog.py`, the deterministic, code-driven source of truth. If this document and the module ever disagree, the module is correct — regenerate this page from it rather than editing this file to match a claim the code doesn't actually make.

An entry appears here only if it satisfies at least one of:

1. Reproduced against a real GAUSS runtime (this repository's own execution evidence).
2. Already present in this repository's execution evidence (even from an unrelated experiment).
3. Verified against official GAUSS/Aptech documentation.

Nothing here is a guess. An uncataloged `G####` code is not a gap in this document — it means this repository has not yet verified that code by any of the three routes above, and the interpreter reports it honestly as `unknown` rather than inventing a meaning.

**Since `v0.54.0`, each entry below distinguishes three different kinds of claim — never conflate them:**

1. **Verified error meaning** (`Category`/`Generic interpretation`/`Source`) — what this error code *is*, established by the routes above.
2. **Possible diagnostic cause** (`Known triggers`/`Diagnostic questions`) — a *plausible* situation known to trigger this code, never a confirmed diagnosis for any specific run. See `docs/gauss-diagnostic-reasoning.md` for how `scripts/gauss_execution_diagnostics.py` turns these into a bounded, low-confidence `DiagnosticCause` list.
3. **Repair advice** — out of scope for this catalog and for the diagnostic layer entirely. Nothing here proposes a code change; `recommended inspection step` and `Diagnostic questions` are both phrased as things to look at or ask, never as edits to make.

**As of `v0.55.0`, the catalog has 11 entries.** Six of these (`G0058`, `G0159`, `G0104`, `G0071`, `G0048`, `G0047`) are new this release, and `G0290` was upgraded from documentation-only to dual-sourced — all seven changes are backed by real GAUSS 26.1.1 runtime reproduction performed during `v0.55.0` (`planning/v0.55.0-verified-diagnostic-coverage-expansion.md`). The six new codes are real-runtime-verified only; none has yet been independently cross-checked against official Aptech documentation in this repository, which is disclosed explicitly in each entry's own **Verification** line rather than implied otherwise.

## Verified Entries

### G0105 — Bad expression or missing arguments

- **Category:** Parse/Syntax
- **Execution phase:** Parsing
- **Verification:** Real Runtime + Official Documentation
- **Generic interpretation:** Execution stopped during parsing because GAUSS reported invalid syntax or a missing expression.
- **Recommended inspection step:** Inspect the reported syntax near the parser diagnostic.
- **Source:** Reproduced repeatedly via `tgauss.exe -b` (`planning/v0.28.0-real-gauss-invocation-research.md`; real evaluations in `v0.50.0`/`v0.52.0`) using `x = ;`. Official Aptech documentation confirms the same title and describes the same general causes (missing semicolons, unloaded library statements, locale-related parsing issues).
- **Known triggers (possible causes, not confirmed):** a missing statement terminator (semicolon) on the reported line or the line before it; a required `library` statement not included before a package procedure call; an incomplete or malformed expression.
- **Diagnostic questions:** Does the reported line, or the line immediately before it, end with a semicolon? If this line calls a package procedure, is the corresponding `library` statement present earlier in the file?

### G0036 — Matrix dimensions are incompatible

- **Category:** Matrix Dimensions
- **Execution phase:** Runtime
- **Verification:** Real Runtime + Official Documentation (with a documented wording discrepancy — see below)
- **Generic interpretation:** Execution reached runtime before GAUSS reported an operation using incompatible matrix dimensions.
- **Recommended inspection step:** Inspect stderr and verify matrix dimensions before the reported operation.
- **Source:** Reproduced via `tgauss.exe -b` (`planning/v0.29.0-runtime-error-output-file-verification.md`; real evaluations in `v0.50.0`/`v0.52.0`) using `x = ones(2,2); y = ones(3,1); z = x + y; print z;`.
- **Documentation discrepancy:** Official Aptech documentation titles this error "Matrices are not conformable," while every real runtime observation recorded in this repository shows the literal stderr text "Matrix dimensions are incompatible." This catalog uses the runtime-observed text for its title/explanation, per its own verification policy of preferring runtime evidence when the two disagree — the documentation wording is most likely a paraphrased page title rather than a literal runtime string, but that is not independently confirmed.
- **Known triggers (possible causes, not confirmed):** an arithmetic or Kronecker-product operation performed on operands whose dimensions do not conform; operator precedence between the Kronecker-product operator (`.*.`) and standard matrix multiplication producing an unintended evaluation order.
- **Diagnostic questions:** What are the row/column dimensions of each operand in the reported operation? Does the expression mix the Kronecker-product operator (`.*.`) and matrix multiplication without explicit parentheses? (Diagnosis does not claim a missing transpose or any other specific cause unless the operand dimensions are actually supplied as evidence.)

### G0025 — Undefined symbol

- **Category:** Runtime Computation
- **Execution phase:** Runtime
- **Verification:** Real Runtime + Official Documentation
- **Generic interpretation:** Execution reached runtime before GAUSS reported an undefined symbol.
- **Recommended inspection step:** Inspect stderr and the generated GAUSS script for the referenced symbol.
- **Source:** Reproduced via `tgauss.exe -b` (`planning/v0.29.0-runtime-error-output-file-verification.md`) using `print undefinedvar;`, producing `error G0025 : Undefined symbol: 'undefinedvar'` with file/line info. Official Aptech documentation confirms an identical title and message format (example shown there: `G0025 : Undefined symbol: 'nobs' [estimate.gss, line 6]`) and documents the same underlying causes (a symbol referenced before definition, an unloaded library, or a procedure GAUSS hasn't been told about).
- **Known triggers (possible causes, not confirmed):** a variable or procedure referenced before it was assigned or defined; a required library or package not loaded; a user-defined procedure not visible because the file defining it was not included, or the code was run line-by-line instead of as a complete file.
- **Diagnostic questions:** Is the referenced symbol assigned or defined earlier in the same run? Is the library/package that defines it loaded? Was the file run as a complete program rather than line-by-line? (Diagnosis never guesses the correct symbol name or spelling.)

### G0014 — File not found

- **Category:** File I/O
- **Execution phase:** Runtime
- **Verification:** Real Runtime + Official Documentation
- **Generic interpretation:** GAUSS could not locate a file referenced by the script — for example a data file, an included source file, or a script path argument.
- **Recommended inspection step:** Confirm the referenced file exists and is reachable from GAUSS's current working directory or `SRC_PATH`, or supply an explicit full path.
- **Source:** Observed via `tgauss.exe -b` during `v0.28.0`'s non-interactive-invocation research (`planning/v0.28.0-real-gauss-invocation-research.md`). The specific test that produced it was an inconclusive `-e`-flag argument-parsing experiment, not an intentional file-not-found reproduction — but the resulting error text (`error G0014 : File not found '1+1;', line 1`) is genuine, unmodified GAUSS output. Official Aptech documentation independently confirms G0014 as "File not found," triggered when GAUSS cannot locate a referenced file in its current working directory or any directory in `SRC_PATH`.
- **Known triggers (possible causes, not confirmed):** the referenced file is not present in GAUSS's current working directory or `SRC_PATH`; a relative path was used from a different working directory than expected.
- **Diagnostic questions:** Does the referenced file exist at the expected location? What is GAUSS's current working directory for this run, and does it contain the file? (Diagnosis never automatically locates, opens, or reads the file.)

### G0290 — Library not found

- **Category:** Package or Library
- **Execution phase:** Startup
- **Verification:** Real Runtime + Official Documentation (upgraded from documentation-only in `v0.55.0`).
- **Generic interpretation:** GAUSS could not find a required application/library file (an `.lcg` library), typically because the corresponding GAUSS application module is not installed, or is not present under the active `GAUSSHOME` directory.
- **Recommended inspection step:** Confirm the required GAUSS application/library is installed under `GAUSSHOME` for the active GAUSS version before rerunning.
- **Source:** Real runtime: reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-expansion.md`) using `library optmum;` in an isolated scratch directory against this repository's real GAUSS 26.1.1 installation, whose `pkgs/` directory does not include `optmum` (confirmed installed modules: cmlmt, coint, comt, dccelib, gml, maxlikmt, optmt, pubtable, qardl, quaids, timeseries, tsmt, tspdlib), consistently producing `error G0290 : Library not found '<path>\optmum.lcg'`. Official Aptech documentation independently documents G0290 as "Library not found," occurring when a required application `.lcg` library file is missing from the active `GAUSSHOME` installation (e.g. an uninstalled application module such as `optmum`, `comt`, or `tsmt`) — the runtime-observed title matches the documented title exactly; no discrepancy to record.
- **Known triggers (possible causes, not confirmed):** the required GAUSS application/library module is not installed under the active `GAUSSHOME`.
- **Diagnostic questions:** Is the required application module (e.g. `optmum`, `comt`, `tsmt`) installed under `GAUSSHOME` for the active GAUSS version?

### G0058 — Index out of range

- **Category:** Indexing or Subscript
- **Execution phase:** Runtime
- **Verification:** Real Runtime only — not yet cross-checked against official Aptech documentation in this repository.
- **Generic interpretation:** Execution reached runtime before GAUSS reported that an index value fell outside the valid bounds of the object being indexed.
- **Recommended inspection step:** Inspect the reported index value and the object's actual dimensions.
- **Source:** Reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-expansion.md`) using both `x = ones(2,2); print x[5,5];` and `x = ones(2,2); print x[-1,1];`, each consistently producing `error G0058 : Index out of range`.
- **Known triggers (possible causes, not confirmed):** an index value greater than the object's number of rows or columns; an index value less than 1 (GAUSS uses 1-based indexing).
- **Diagnostic questions:** What are the row/column dimensions of the object being indexed? Is the reported index value within the range 1 to the object's row/column count? (Diagnosis never proposes a corrected index value.)

### G0159 — Wrong number of parameters

- **Category:** Procedure Invocation / Argument Validation
- **Execution phase:** Runtime
- **Verification:** Real Runtime only — not yet cross-checked against official Aptech documentation in this repository.
- **Generic interpretation:** Execution reached runtime before GAUSS reported that a procedure was called with a different number of arguments than its own declaration accepts.
- **Recommended inspection step:** Inspect the procedure's declared parameter list and the exact call site reported.
- **Source:** Reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-expansion.md`) using `proc(1) = myproc2(a, b); retp(a+b); endp; y = myproc2(1);`, consistently producing `error G0159 : Wrong number of parameters ''myproc2' expected 2 arguments, received 1'`.
- **Known triggers (possible causes, not confirmed):** a procedure call supplying fewer arguments than the procedure's `proc` declaration requires; a procedure call supplying more arguments than it accepts.
- **Diagnostic questions:** How many parameters does the called procedure's `proc` statement declare? How many arguments does the reported call site actually supply?

### G0104 — Argument must be positive

- **Category:** Argument Validation
- **Execution phase:** Runtime
- **Verification:** Real Runtime only — not yet cross-checked against official Aptech documentation in this repository.
- **Generic interpretation:** Execution reached runtime before GAUSS reported that a supplied argument did not satisfy a required strictly-positive-value constraint.
- **Recommended inspection step:** Inspect the actual value of the reported argument at the point of the call.
- **Source:** Reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-expansion.md`) using `x = eye(-1);`, consistently producing `error G0104 : Argument must be positive`.
- **Known triggers (possible causes, not confirmed):** a zero or negative value supplied where a function or procedure requires a strictly positive value (e.g. a matrix-construction dimension such as `eye`'s size argument).
- **Diagnostic questions:** What is the actual runtime value of the reported argument at the point of the call, and is it positive? (Diagnosis never proposes a replacement value.)

### G0071 — Type mismatch

- **Category:** Type Mismatch
- **Execution phase:** Runtime
- **Verification:** Real Runtime only — not yet cross-checked against official Aptech documentation in this repository.
- **Generic interpretation:** Execution reached runtime before GAUSS reported that an operation received an operand or argument of an unexpected type (for example a string where a numeric value was required).
- **Recommended inspection step:** Inspect the actual type of each operand or argument in the reported operation.
- **Source:** Reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-expansion.md`) using `x = sqrt("abc");`, consistently producing `error G0071 : Type mismatch`.
- **Known triggers (possible causes, not confirmed):** a string value supplied where a numeric scalar or matrix argument was required.
- **Diagnostic questions:** What is the actual type (string, scalar, matrix) of each operand or argument in the reported operation?

### G0048 — Matrix singular

- **Category:** Numerical
- **Execution phase:** Runtime
- **Verification:** Real Runtime only — not yet cross-checked against official Aptech documentation in this repository.
- **Generic interpretation:** Execution reached runtime before GAUSS reported that a matrix operation requiring inversion (or an equivalent operation) could not be completed because the supplied matrix is singular.
- **Recommended inspection step:** Inspect the matrix supplied to the reported operation for linear dependence among its rows or columns.
- **Source:** Reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-expansion.md`) using `x = ones(2,2); y = inv(x);`, consistently producing `error G0048 : Matrix singular`.
- **Known triggers (possible causes, not confirmed):** a matrix supplied to `inv` or an equivalent inversion-requiring operation has linearly dependent rows or columns (a zero, or near-zero, determinant).
- **Diagnostic questions:** Does the matrix supplied to the reported operation have linearly dependent rows or columns?

### G0047 — Rows don't match

- **Category:** Matrix Dimensions
- **Execution phase:** Runtime
- **Verification:** Real Runtime only — not yet cross-checked against official Aptech documentation in this repository.
- **Generic interpretation:** Execution reached runtime before GAUSS reported that a horizontal concatenation was attempted between operands with different numbers of rows.
- **Recommended inspection step:** Inspect the row counts of each operand in the reported horizontal-concatenation operation.
- **Source:** Reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-expansion.md`) using `x = ones(2,2); y = ones(3,3); z = x~y;`, consistently producing `error G0047 : Rows don't match`. Distinct code from `G0036` (arithmetic/Kronecker dimension mismatch) — specific to the horizontal-concatenation (`~`) operator.
- **Known triggers (possible causes, not confirmed):** a horizontal concatenation (`~`) attempted between operands with different numbers of rows.
- **Diagnostic questions:** What are the row counts of each operand in the reported horizontal-concatenation operation?

## Considered But Not Added (`v0.55.0`)

Two observations from `v0.55.0`'s real-runtime probing were deliberately **not** turned into catalog entries, per this catalog's own evidence standard:

- **`G0117` ("Invalid argument")** was genuinely observed (via `x = ones(2,2); print x["a","b"];`), but only through an indirect, compound trigger — GAUSS first emitted an uncoded `indexing error: attempting to access column 'b' - symbol isn't a dataframe.` line, then `G0117` itself. The exact condition that maps to `G0117` specifically (as opposed to the dataframe-indexing message that preceded it) was not isolated cleanly enough to state a non-speculative `known_trigger` for it this milestone. It may be added in a future milestone with a more targeted reproduction.
- A `loadd(...)` call against a missing file (`x = loadd("does_not_exist.csv");`) produced a genuine GAUSS runtime failure, but in a format this catalog's `G####` schema does not cover at all: `error : csvRead error: file '...' not found` (from `c:\gauss26\src\csv.src`), with **no `G####` code** anywhere in the message. `gauss_execution_interpreter.interpret_execution`'s error-detection regex only matches `error\s+G\d{4}`, so this genuinely correctly falls through to the interpreter's `insufficient_evidence` classification today — not a bug, but a known gap: some real GAUSS runtime failures are reported in a package-source-level format this catalog cannot yet represent. Recorded here, and in `KNOWN_LIMITATIONS.md`, rather than silently ignored.

## Future Placeholders (Not Yet Cataloged)

These categories exist in `gauss_error_catalog.GaussErrorCategory` because the interpreter's classification model anticipates them, but **no code is cataloged under them yet** — they are not documented here as if they were:

- **Startup or Licensing** — GAUSS License Manager errors are documented by Aptech, but without a confirmed `G####` code format comparable to the entries above; not added speculatively.
- **User Interruption** — no verified error code yet (e.g. a user-initiated `Ctrl+C`/break during a run).
- **Timeout** — not a GAUSS error code at all; it is an interpreter-level classification applied when execution evidence reports `execution_status: timed_out`, whether from a real, observed runtime timeout or from simulated/injected evidence. The interpreter's own wording always distinguishes which kind of timeout evidence it is describing (see `gauss_execution_interpreter.interpret_execution`'s timeout branch) rather than implying a live GAUSS timeout occurred when it did not.
- **Unknown** — the deliberate fallback for any `G####` code not in this catalog. It is not a placeholder to be "filled in" by guessing; it is preserved permanently as the honest answer for genuinely unverified codes.

## Adding a New Entry

1. Establish verification via one of the three accepted routes (real runtime reproduction, existing repository evidence, or official documentation) — never from memory or inference alone.
2. Add a `GaussErrorCatalogEntry` to `scripts/gauss_error_catalog.py`'s `_ENTRIES` tuple, including a `verification_status` tuple and a `verification_source` citation.
3. If official documentation and observed runtime evidence disagree, keep runtime evidence as authoritative for `title`/`generic_explanation` and record the disagreement in `documentation_discrepancy` — never silently pick one without saying so.
4. Add or extend a test in `scripts/test_gauss_execution_interpreter.py` proving the new entry is looked up and classified correctly.
5. If verified diagnostic knowledge exists (from the same accepted sources), populate `known_triggers`/`diagnostic_questions`/`required_evidence_for_diagnosis` — never with a general programming guess; omit them (leave the tuples empty) if no verified trigger knowledge exists yet. Add or extend a test in `scripts/test_gauss_execution_diagnostics.py`.
6. Update this document to match — by hand, since this file is not auto-generated.

No interpreter or diagnostic-engine code should need to change to add a new entry; `gauss_execution_interpreter.interpret_execution(...)` and `gauss_execution_diagnostics.diagnose_execution(...)` only look codes up in the catalog. See `docs/gauss-diagnostic-reasoning.md` for how diagnostic knowledge is consumed.
