# Evaluation Result

Date: 2026-11-18
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`0280b330...`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-86x`), as in 80.x-85.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-86x-data`) held fresh copies of 85.x's two original CSVs in `input/` (`fred_macro.csv`, `wage_returns.csv`) and an empty `output/`. The human asked each task in plain words, one at a time, and answered every run prompt themselves (eight "yes", one "no"). The tasks and their expected outcomes were stated to the user before the run (plan v0.94 §15). The tasks ran on 2026-11-18 from 06:01 to 06:22 local (12:01-12:22 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell` on the data folder, the GAUSS `examples` folder and the user's Desktop, one `curl` to FRED, and `AskUserQuestion`; all disclosed in its report and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.1 (tag `v0.94.1`, commit `e55b271`; published to PyPI on 2026-11-18, run `44298126085`), the editable install of this checkout (`gauss-ai version` = 0.94.1).
Prompt ID: 86.4
Prompt Category: MCP Data Import and Export of v0.94.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.1 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `59e30e87...` reported `server_version: 0.94.1`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 24 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.1` (every verdict equal to the live response) and at a `git archive` of `v0.94.0`, and ran all 24 with `tgauss.exe -b`, each from its own new directory holding copies of the input files (all 24 exit 0 with no GAUSS error). The searches and reads were not re-run.
Prompt Text:

"Load fred_macro.csv, rename the columns to something more readable, and print the first five rows"

Code (validation 10, `review_required`):
```gauss
// Load all columns: date, GDPC1, CPIAUCSL, FEDFUNDS, UNRATE, GS10
macro = loadd("fred_macro.csv");

// Readable names, in the same column order
newnames = "Date" $| "RealGDP" $| "CPI" $| "FedFundsRate" $| "UnemploymentRate" $| "Treasury10Yr";
macro = dfname(macro, newnames);

print head(macro, 5);
```
Code (validation 11, `review_required`):
```gauss
// Load all columns: date, GDPC1, CPIAUCSL, FEDFUNDS, UNRATE, GS10
macro = loadd("fred_macro.csv");

// Readable names, in the same column order
macro = setColNames(macro, "Date" $| "RealGDP" $| "CPI" $| "FedFundsRate" $| "UnemploymentRate" $| "Treasury10Yr");

print head(macro, 5);
```
Code (validation 12, `review_required`):
```gauss
// Load all columns: date, GDPC1, CPIAUCSL, FEDFUNDS, UNRATE, GS10
macro = loadd("fred_macro.csv");

// Readable names, in the same column order (6x1 string array)
string newnames = { "Date", "RealGDP", "CPI", "FedFundsRate", "UnemploymentRate", "Treasury10Yr" };
macro = setColNames(macro, newnames);

print head(macro, 5);
```
Code (validation 13, `not_ready`):
```gauss
// Load all columns: date, GDPC1, CPIAUCSL, FEDFUNDS, UNRATE, GS10
macro = loadd("fred_macro.csv");

// Readable names, in the same column order
hdr = "Date" $| "RealGDP" $| "CPI" $| "FedFundsRate" $| "UnemploymentRate" $| "Treasury10Yr";

// Write a copy with the new column names, then reload it
ret = saved(macro, "fred_macro_renamed.csv", hdr);
macro2 = loadd("fred_macro_renamed.csv");

print head(macro2, 5);
```
Code (validation 14, `handoff_candidate`):
```gauss
// Load all columns: date, GDPC1, CPIAUCSL, FEDFUNDS, UNRATE, GS10
macro = loadd("fred_macro.csv");

// Readable names, in the same column order
hdr = "Date" $| "RealGDP" $| "CPI" $| "FedFundsRate" $| "UnemploymentRate" $| "Treasury10Yr";

// Write a copy with the new column names
ret = saved(macro, "fred_macro_renamed.csv", hdr);
print "saved returned " ret;

// First five rows (printed with the original names)
print head(macro, 5);
```

Captured output (live, equal to the v0.94.1 re-run): **review_required** x3, **not_ready**, **handoff_candidate**.
v0.94.0 code: the same, except the last is **review_required** (its `$|` header is v0.94.1's).

Expected behavior: (plan v0.94 §15) the declared-string version stays `review_required` (`string_declaration_imprecise`), never `not_ready`.

Observed behavior: as expected for the declaration (validation 12). **Defect:** for validations 10-11 the gap on `varnames` read "the argument (an expression whose every operand is numeric; its shape is not computed) is numeric, but the documented type ... (vector) does not accept every numeric matrix" (`expression_category_imprecise`). The status is right (a string array against a parameter the docs call `Mx1 vector`, as in §14.3), but the text is wrong: the recording session found that a `$+`/`$|`/`$~` join of strings (category `string`, origin `expression_category`) falls into the numeric branch's wording. The client concluded "the validator reads the `$|` joins as numbers". Validation 13 read back a file the run writes (`not_ready`: "not in the analysis folder's input folder"), as the rules say. The client then offered three options; the user chose A, a program that writes a renamed copy and prints the old names. **Run:** request_id `f428f634-9054-472c-90da-e531085b64ae`; user "yes"; success, exit 0; kept `fred_macro_renamed.csv` in `output\20261118T120938Z-f428f634`. The renamed table the client showed came from the file's header, not GAUSS output (disclosed). **`tgauss.exe -b`: validations 10-12 all run and print the five rows with the new names**; the program the user asked for was never offered.

Pass/fail: Pass with defect recorded
Defect severity: Medium
Remediation: Say "a string or string array" for a string join (plan v0.94 §16). Whether a string array may satisfy a `vector` names parameter stays a decision (the docs' own `setColNames` example passes `"Planes"$|"Trains"$|...`).

Overall Score: 2.6
Decision: Pass with defect recorded
