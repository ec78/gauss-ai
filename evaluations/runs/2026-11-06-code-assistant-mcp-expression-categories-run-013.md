# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`8ab50628…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-82x`), as in 80.x and 81.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes", one "no") and one of the client's own numbered options ("1"). Tasks 82.1-82.9 were proposed by the recording session; 82.10-82.14 were the user's own. All tasks ran on 2026-11-06, 06:34-06:53 local (11:34-11:53 UTC). The client used gauss-ai tools plus five PowerShell commands that checked paths, listed folders and read executable version numbers (82.9, 82.12, 82.14); it read no file's contents, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.91.0 (tag `v0.91.0`, commit `5b07a28`; published to PyPI on 2026-11-06, run `42206846915`), the editable install of this checkout (`gauss-ai version` = 0.91.0).
Prompt ID: 82.13
Prompt Category: MCP Expression Categories of v0.91.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.91.0 over stdio, registered at local scope for the folder under both drive-letter spellings (`C:/…` and `c:/…`) with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session (`f7274c39…`) served every task; `gauss_session_start` reported `server_version: 0.91.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 37 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.91.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.90.0` (`1ee121c`), diagnosed each non-candidate verdict with `validate_code(...)` directly, re-ran all five approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory, and ran every other non-blocked snippet the same way.
Prompt Text:

"Yes please write a worked example for running a lasso model"

`gauss_read_doc("lassofit.rst", "*")` (the whole page, 4,292 characters).

Code (c21):
```gauss
new;
library gml;

// Reproducible draws and train/test shuffle
rndseed 20261106;

/*
** Simulate sparse linear data
** 200 observations, 10 features; only the first 3 matter
*/
n = 200;
p = 10;
X = rndn(n, p);

b_true = { 3, -2, 1.5, 0, 0, 0, 0, 0, 0, 0 };
y = 1 + X * b_true + rndn(n, 1);

/*
** 70% train / 30% test split (shuffled)
*/
{ y_train, y_test, X_train, X_test } = trainTestSplit(y, X, 0.7);

/*
** Fit the lasso path with default settings
** (lassoFit builds a decreasing lambda path internally)
*/
struct lassoModel mdl;
mdl = lassoFit(y_train, X_train);

/*
** Predict on the test set: one column per lambda
*/
y_hat = lmPredict(mdl, X_test);

// Test MSE for each lambda (y_test broadcasts across columns)
test_mse = meanc((y_test - y_hat) .^ 2);

// Lambda with the lowest test MSE
best = minindc(test_mse);

print "Number of lambdas on the path:";
print rows(mdl.lambda);
print "Best lambda (lowest test MSE):";
print mdl.lambda[best];
print "Test MSE at best lambda:";
print test_mse[best];
print "Intercept at best lambda:";
print mdl.alpha_hat[best];
print "      True      Lasso";
print b_true ~ mdl.beta_hat[., best];
print "Nonzero coefficients at best lambda:";
print sumc(mdl.beta_hat[., best] .!= 0);
```
Captured output (live, identical on the v0.91.0 re-run): **not_ready**.
Reasons beyond the standard ones: "line 2: `library` is a system-touching statement (source_inclusion) -- controlled execution only runs self-contained snippets that compute in memory"
v0.90.0: identical.

The client said every GML program needs `library gml;`, which the approval step does not allow, and gave the code to paste.

Expected behavior: (the user's own task) `library` is source inclusion and is `not_ready`.

Observed behavior: as expected; the reason names line 2's `library` (`source_inclusion`). The recording session ran the program directly in a new empty directory: `library gml`, `trainTestSplit`, `lassoFit` and `lmPredict` run with no error and print the lasso report. This is the exact case v0.92.0 "Installed Libraries" is for (an Aptech-documented package installed in the configured GAUSS).

Pass/fail: Pass
Defect severity: None
Remediation: v0.92.0 (planned).

Overall Score: 4.0
Decision: Pass
