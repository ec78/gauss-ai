# Evaluation Result

Date: 2026-11-18
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`0280b330...`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-86x`), as in 80.x-85.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-86x-data`) held fresh copies of 85.x's two original CSVs in `input/` (`fred_macro.csv`, `wage_returns.csv`) and an empty `output/`. The human asked each task in plain words, one at a time, and answered every run prompt themselves (eight "yes", one "no"). The tasks and their expected outcomes were stated to the user before the run (plan v0.94 §15). The tasks ran on 2026-11-18 from 06:01 to 06:22 local (12:01-12:22 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell` on the data folder, the GAUSS `examples` folder and the user's Desktop, one `curl` to FRED, and `AskUserQuestion`; all disclosed in its report and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.1 (tag `v0.94.1`, commit `e55b271`; published to PyPI on 2026-11-18, run `44298126085`), the editable install of this checkout (`gauss-ai version` = 0.94.1).
Prompt ID: 86.2
Prompt Category: MCP Data Import and Export of v0.94.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.1 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `59e30e87...` reported `server_version: 0.94.1`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 24 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.1` (every verdict equal to the live response) and at a `git archive` of `v0.94.0`, and ran all 24 with `tgauss.exe -b`, each from its own new directory holding copies of the input files (all 24 exit 0 with no GAUSS error). The searches and reads were not re-run.
Prompt Text:

"Regress LogWage on Education, Experience and Union and save the coefficients and standard errors to a CSV with column headers."

Code (validation 6, `review_required`):
```gauss
// Load the full sample (all 1,000 people)
wage = loadd("wage_returns.csv");

// OLS with a constant; prints the standard regression table
struct olsmtOut out;
out = olsmt(wage, "LogWage ~ Education + Experience + Union");

// Build the results table: variable name, coefficient, standard error
vars = "CONSTANT" $| "Education" $| "Experience" $| "Union";
names_df = asDF(vars, "Variable");
est_df = asDF(out.b ~ out.stderr, "Coefficient", "StdError");
results = names_df ~ est_df;

print results;

ret = saved(results, "logwage_ols_coefficients.csv");
print "saved returned " ret;
```
Code (validation 7, `handoff_candidate`):
```gauss
// OLS on the full sample, with a constant; prints the standard regression table
struct olsmtOut out;
out = olsmt("wage_returns.csv", "LogWage ~ Education + Experience + Union");

// Rows are in order: CONSTANT, Education, Experience, Union
est = out.b ~ out.stderr;
print est;

// Save with column headers
hdr = "Coefficient" $| "StdError";
ret = saved(est, "logwage_ols_coefficients.csv", hdr);
print "saved returned " ret;
```

Captured output (live, equal to the v0.94.1 re-run): **review_required**, then **handoff_candidate**.
v0.94.0 code: both **review_required** (the `$|` header is v0.94.1's).

Expected behavior: (plan v0.94 §15) a `$|` header row validates and the CSV keeps its header.

Observed behavior: as expected. The first version's gaps: `olsmt` argument 1 traced to `loadd`'s documented `matrix` against `string/dataframe` (`return_type_imprecise`); `asDF` arguments 2-3 `documented_type_missing`; `saved` argument 1 from `names_df ~ est_df` ("an operand's category (dataframe) is not numeric"). The client passed the file name to `olsmt` and dropped the variable-name column, and told the user so before the prompt. **Run:** request_id `c4a16a16-2a41-4588-af67-83ed32f5db0c`; user "yes"; success, exit 0, the OLS table (1,000 cases, R² 0.529); kept `logwage_ols_coefficients.csv` (headers `Coefficient,StdError`, four rows) in `output\20261118T120445Z-c4a16a16`. `tgauss.exe -b`: both versions run with no error.

Pass/fail: Pass with defect recorded
Defect severity: Low
Remediation: None new; dataframe concatenation and `loadd`'s `:rtype` are disclosed coverage candidates (v0.96).

Overall Score: 3.5
Decision: Pass with defect recorded
