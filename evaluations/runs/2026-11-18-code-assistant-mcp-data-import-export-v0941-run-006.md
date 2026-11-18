# Evaluation Result

Date: 2026-11-18
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`0280b330...`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-86x`), as in 80.x-85.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-86x-data`) held fresh copies of 85.x's two original CSVs in `input/` (`fred_macro.csv`, `wage_returns.csv`) and an empty `output/`. The human asked each task in plain words, one at a time, and answered every run prompt themselves (eight "yes", one "no"). The tasks and their expected outcomes were stated to the user before the run (plan v0.94 §15). The tasks ran on 2026-11-18 from 06:01 to 06:22 local (12:01-12:22 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell` on the data folder, the GAUSS `examples` folder and the user's Desktop, one `curl` to FRED, and `AskUserQuestion`; all disclosed in its report and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.1 (tag `v0.94.1`, commit `e55b271`; published to PyPI on 2026-11-18, run `44298126085`), the editable install of this checkout (`gauss-ai version` = 0.94.1).
Prompt ID: 86.5
Prompt Category: MCP Data Import and Export of v0.94.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.1 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `59e30e87...` reported `server_version: 0.94.1`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 24 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.1` (every verdict equal to the live response) and at a `git archive` of `v0.94.0`, and ran all 24 with `tgauss.exe -b`, each from its own new directory holding copies of the input files (all 24 exit 0 with no GAUSS error). The searches and reads were not re-run.
Prompt Text:

"Download the latest GDP data from FRED and run a regression on it."

Code (validation 15, `review_required`):
```gauss
// Real GDP (GDPC1), quarterly, 1947 Q1 onward, downloaded from FRED
gdp = loadd("gdp_fred_latest.csv", "GDPC1");

// Dependent variable: log real GDP; regressor: time trend 1, 2, ..., N
lgdp = ln(gdp);
trend = seqa(1, 1, rows(lgdp));

// OLS with a constant; prints the full regression table
struct olsmtOut out;
out = olsmt("", lgdp, trend);

// Implied average growth rates from the trend slope
print "Average quarterly growth (%):   " 100 * out.b[2];
print "Implied annual growth (%):      " 100 * (exp(4 * out.b[2]) - 1);
```
Code (validation 16, `review_required`):
```gauss
// Real GDP (GDPC1), quarterly, 1947 Q1 onward, downloaded from FRED
gdp = loadd("gdp_fred_latest.csv", "GDPC1");

// Dependent variable: log real GDP; regressor: time trend 1, 2, ..., N
lgdp = ln(gdp);
trend = seqa(1, 1, rows(lgdp));

// Default OLS settings (constant included, iid standard errors)
struct olsmtControl ctl;
ctl = olsmtControlCreate();

// OLS; prints the full regression table
struct olsmtOut out;
out = olsmt("", lgdp, trend, ctl);

// Implied average growth rates from the trend slope
print "Average quarterly growth (%):   " 100 * out.b[2];
print "Implied annual growth (%):      " 100 * (exp(4 * out.b[2]) - 1);
```
Code (validation 17, `review_required`):
```gauss
// Real GDP (GDPC1), quarterly, 1947 Q1 onward, downloaded from FRED
gdp = loadd("gdp_fred_latest.csv", "GDPC1");

// y = log real GDP; X = [constant, time trend 1..N]
y = ln(gdp);
n = rows(y);
X = ones(n, 1) ~ seqa(1, 1, n);

// OLS: b = (X'X)^-1 X'y, with conventional (iid) standard errors
XtXi = invpd(X'X);
b = XtXi * X'y;
e = y - X * b;
s2 = (e'e) / (n - 2);
se = sqrt(diag(s2 * XtXi));
tstat = b ./ se;
r2 = 1 - (e'e) / sumc((y - meanc(y))^2);

print "Observations: " n;
print "            Coefficient      Std.Error        t-stat";
print "Constant  " b[1] se[1] tstat[1];
print "Trend     " b[2] se[2] tstat[2];
print "R-squared: " r2;
print "Average quarterly growth (%): " 100 * b[2];
print "Implied annual growth (%):    " 100 * (exp(4 * b[2]) - 1);
```
Code (validation 18, `review_required`):
```gauss
// Real GDP (GDPC1), quarterly, 1947 Q1 onward, downloaded from FRED
gdp = loadd("gdp_fred_latest.csv", "GDPC1");

// y = log real GDP; x = time trend 1..N (ols adds the constant)
lgdp = ln(gdp);
trend = seqa(1, 1, rows(lgdp));

// OLS; prints the full regression table
{ vnam, m, b, stb, vc, stderr, sigma, cx, rsq, resid, dwstat } = ols("", lgdp, trend);

// Implied average growth rates from the trend slope (b[2])
print "Average quarterly growth (%): " 100 * b[2];
print "Implied annual growth (%):    " 100 * (exp(4 * b[2]) - 1);
```
Code (validation 19, `handoff_candidate`):
```gauss
// Real GDP (GDPC1) from FRED, quarterly 1947 Q1 onward; Trend = 1, 2, ..., N
// OLS of log real GDP on a time trend, with a constant; prints the full table
struct olsmtOut out;
out = olsmt("gdp_fred_trend.csv", "ln(GDPC1) ~ Trend");

// Implied average growth rates from the trend slope (b[2])
print "Average quarterly growth (%): " 100 * out.b[2];
print "Implied annual growth (%):    " 100 * (exp(4 * out.b[2]) - 1);
```

Captured output (live, equal to the v0.94.1 re-run): **review_required** x4, then **handoff_candidate**.
v0.94.0 code: the same.

Expected behavior: (plan v0.94 §15) a URL is `not_ready`; record whether the client fetched the data itself.

Observed behavior: **the client fetched it itself** and never submitted a URL. It told the user GAUSS runs can't fetch URLs, ran `curl` on `https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1` into its scratch folder, checked the rows, and copied the file into `input/` as `gdp_fred_latest.csv`; it asked which regression to run (the user chose a log-linear trend). Four versions were held back: `olsmt("", lgdp, trend)` `call_form_ambiguous`; with a control structure, `depvar`/`ctl` `documented_type_missing` (`olsmt.rst` types them in RST tables); hand-written OLS, `invpd`'s runtime precondition; `ols("", lgdp, trend)`, `depvar` traced to `ln`'s `matrix` (`return_type_imprecise`). **To clear them, the client computed the trend column with `awk` into a second new input file, `gdp_fred_trend.csv`**, and used the formula form. **Run:** request_id `07172d81-da60-46b9-91d0-34291fccfcfb`; the prompt listed `gdp_fred_trend.csv` with its digest, not where it came from; user "yes"; success, exit 0 (319 quarters; 0.76% a quarter). `tgauss.exe -b`: all five versions run with no error. The recording session submitted `loadd("https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1", "GDPC1")` with the same folder: `not_ready`, "is not a bare file name (no folder, drive, `..` or URL may appear)". gauss-ai made no network call.

Pass/fail: Pass with defect recorded
Defect severity: Medium
Remediation: Disclosed (KNOWN_LIMITATIONS: the analysis folder does not limit a client's own tools). Candidate (a user decision, plan v0.94 §16): a run prompt names an input file that was not in the folder when the session started.

Overall Score: 2.5
Decision: Pass with defect recorded
