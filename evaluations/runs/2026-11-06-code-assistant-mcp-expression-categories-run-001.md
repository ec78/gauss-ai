# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`8ab50628…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-82x`), as in 80.x and 81.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes", one "no") and one of the client's own numbered options ("1"). Tasks 82.1-82.9 were proposed by the recording session; 82.10-82.14 were the user's own. All tasks ran on 2026-11-06, 06:34-06:53 local (11:34-11:53 UTC). The client used gauss-ai tools plus five PowerShell commands that checked paths, listed folders and read executable version numbers (82.9, 82.12, 82.14); it read no file's contents, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.91.0 (tag `v0.91.0`, commit `5b07a28`; published to PyPI on 2026-11-06, run `42206846915`), the editable install of this checkout (`gauss-ai version` = 0.91.0).
Prompt ID: 82.1
Prompt Category: MCP Expression Categories of v0.91.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.91.0 over stdio, registered at local scope for the folder under both drive-letter spellings (`C:/…` and `c:/…`) with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session (`f7274c39…`) served every task; `gauss_session_start` reported `server_version: 0.91.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 37 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.91.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.90.0` (`1ee121c`), diagnosed each non-candidate verdict with `validate_code(...)` directly, re-ran all five approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory, and ran every other non-blocked snippet the same way.
Prompt Text:

"Simulate 100 observations with two regressors and a constant, generate y from known coefficients plus noise, and estimate the OLS coefficients using matrix algebra. Print them."

`gauss_session_start`: `server_version: 0.91.0`, `runner: gauss`, `docs_root_configured: true`, `real_gauss_allowed: true` (the opt-in confirmed before the first task, as CLAUDE.md requires).

Code (c01):
```gauss
// Reproducible draws
rndseed 20261106;

n = 100;

// Design matrix: constant + two standard-normal regressors
X = ones(n, 1) ~ rndn(n, 2);

// True coefficients: constant, beta1, beta2
b_true = { 1.0, 2.0, -0.5 };

// Noise with sd = 0.5
e = 0.5 * rndn(n, 1);

// Dependent variable
y = X * b_true + e;

// OLS via normal equations: b = (X'X)^-1 X'y
b_hat = invpd(X'X) * (X'y);

print "True coefficients:";
print b_true;
print "OLS estimates:";
print b_hat;
```
Captured output (live, identical on the v0.91.0 re-run): **review_required**.
Reasons beyond the standard ones: "runtime-dependent precondition(s) remain unverified for: invpd"; "validation coverage is partial (incomplete: preconditions unknown), short of the broad evidence required for handoff candidacy"
v0.90.0: **review_required** (reasons differ: v0.90.0 says the expression is never evaluated).

The client said `invpd` has a runtime precondition the checker cannot verify, and rewrote the solve with the `/` operator.

Code (c02):
```gauss
// Reproducible draws
rndseed 20261106;

n = 100;

// Design matrix: constant + two standard-normal regressors
X = ones(n, 1) ~ rndn(n, 2);

// True coefficients: constant, beta1, beta2
b_true = { 1.0, 2.0, -0.5 };

// Noise with sd = 0.5
e = 0.5 * rndn(n, 1);

// Dependent variable
y = X * b_true + e;

// OLS via normal equations: solve (X'X) b = X'y
XtX = X'X;
Xty = X'y;
b_hat = Xty / XtX;

print "True coefficients:";
print b_true;
print "OLS estimates:";
print b_hat;
```
Captured output (live, identical on the v0.91.0 re-run): **handoff_candidate**.
Reasons: the five standard handoff reasons, ending "validation coverage is broad".
v0.90.0: identical.

Execution handoff (prepare, `request_id` `8bca7f04-1b45-4cf0-9723-00b5c202f2d6`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
// Reproducible draws
rndseed 20261106;

n = 100;

// Design matrix: constant + two standard-normal regressors
X = ones(n, 1) ~ rndn(n, 2);

// True coefficients: constant, beta1, beta2
b_true = { 1.0, 2.0, -0.5 };

// Noise with sd = 0.5
e = 0.5 * rndn(n, 1);

// Dependent variable
y = X * b_true + e;

// OLS via normal equations: solve (X'X) b = X'y
XtX = X'X;
Xty = X'y;
b_hat = Xty / XtX;

print "True coefficients:";
print b_true;
print "OLS estimates:";
print b_hat;

```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: 0cd403d7e07fc3ba467aa9ec9051f118d264f8d2edb8e81d98f2e00b53581778

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id`: outcome `success`; stdout:
```
True coefficients:

       1.0000000 
       2.0000000 
     -0.50000000 
OLS estimates:

      0.96299211 
       2.0310582 
     -0.52392235
```
Real GAUSS (`tgauss.exe -b`, recording session, own new empty directory): byte-identical stdout; no file created.

Expected behavior: (plan v0.91 §7) the matrix-algebra OLS with a constant column built by concatenation reaches `handoff_candidate`, and an approved run equals direct `tgauss.exe -b`.

Observed behavior: as expected. The client wrote the constant column as `ones(n, 1) ~ rndn(n, 2)` unprompted, and the expression was accepted in both versions. Its first version used `invpd(X'X) * (X'y)` and was review_required for the `invpd` precondition only (v0.90.0 also named `X'X` as a never-evaluated expression). It then used `Xty / XtX`, which reached a prompt and ran. That `/` with a runtime divisor is not checked is disclosed (`KNOWN_LIMITATIONS.md`, v0.87.0; 77.17), and the client said so itself in its report. `c02` is handoff_candidate on v0.90.0 too, so this task's run does not depend on v0.91.0.

Pass/fail: Pass
Defect severity: None
Remediation: None (the `/` divisor limitation is disclosed; see 82.2).

Overall Score: 3.8
Decision: Pass
