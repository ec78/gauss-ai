# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`8ab50628…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-82x`), as in 80.x and 81.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes", one "no") and one of the client's own numbered options ("1"). Tasks 82.1-82.9 were proposed by the recording session; 82.10-82.14 were the user's own. All tasks ran on 2026-11-06, 06:34-06:53 local (11:34-11:53 UTC). The client used gauss-ai tools plus five PowerShell commands that checked paths, listed folders and read executable version numbers (82.9, 82.12, 82.14); it read no file's contents, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.91.0 (tag `v0.91.0`, commit `5b07a28`; published to PyPI on 2026-11-06, run `42206846915`), the editable install of this checkout (`gauss-ai version` = 0.91.0).
Prompt ID: 82.6
Prompt Category: MCP Expression Categories of v0.91.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.91.0 over stdio, registered at local scope for the folder under both drive-letter spellings (`C:/…` and `c:/…`) with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session (`f7274c39…`) served every task; `gauss_session_start` reported `server_version: 0.91.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 37 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.91.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.90.0` (`1ee121c`), diagnosed each non-candidate verdict with `validate_code(...)` directly, re-ran all five approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory, and ran every other non-blocked snippet the same way.
Prompt Text:

"Run an OLS regression with olsmt where y = 2, 3, 1, 7, 5 and x has rows (1 3 2), (2 3 1), (7 1 7), (5 3 1), (3 5 5). Print the coefficients."

The client searched `olsmt` (grounded) and validated the documented matrix form:

Code (c14):
```gauss
// Dependent variable (5x1)
y = { 2, 3, 1, 7, 5 };

// Independent variables (5x3)
x = { 1 3 2,
      2 3 1,
      7 1 7,
      5 3 1,
      3 5 5 };

// OLS with matrices passed directly (empty dataset name)
struct olsmtOut out;
out = olsmt("", y, x);

print "Coefficients (CONSTANT, X1, X2, X3):";
print out.b;
```
Captured output (live, identical on the v0.91.0 re-run): **review_required**.
Reasons beyond the standard ones: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `olsmt` argument 2 (parameter `depvar`): no documented `:type` line was matched to this parameter"
v0.90.0: identical.

It then tried the formula form with `asDF` (after one search), then `setColNames`:

Code (c15):
```gauss
// Dependent variable (5x1)
y = { 2, 3, 1, 7, 5 };

// Independent variables (5x3)
x = { 1 3 2,
      2 3 1,
      7 1 7,
      5 3 1,
      3 5 5 };

// Combine into a named dataframe
df = asDF(y ~ x, "y", "X1", "X2", "X3");

// OLS using a formula string (constant included by default)
struct olsmtOut out;
out = olsmt(df, "y ~ X1 + X2 + X3");

print "Coefficients (CONSTANT, X1, X2, X3):";
print out.b;
```
Captured output (live, identical on the v0.91.0 re-run): **review_required**.
Reasons beyond the standard ones: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `asDF` argument 2 (parameter `varname_1`): no documented `:type` line was matched to this parameter"; "parameter role unknown -- `asDF` argument 3 (parameter `varname_2`): no documented `:type` line was matched to this parameter"
v0.90.0: **review_required** (reasons differ: v0.90.0 says the expression is never evaluated).

Code (c16):
```gauss
// Dependent variable (5x1)
y = { 2, 3, 1, 7, 5 };

// Independent variables (5x3)
x = { 1 3 2,
      2 3 1,
      7 1 7,
      5 3 1,
      3 5 5 };

// Combine into a dataframe with named columns
df = setColNames(y ~ x, "y" $| "X1" $| "X2" $| "X3");

// OLS using a formula string (constant included by default)
struct olsmtOut out;
out = olsmt(df, "y ~ X1 + X2 + X3");

print "Coefficients (CONSTANT, X1, X2, X3):";
print out.b;
```
Captured output (live, identical on the v0.91.0 re-run): **review_required**.
Reasons beyond the standard ones: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `setColNames` argument 2 (parameter `varnames`): `"y" $| "X1" $| "X2" $| "X3"` is an expression whose category could not be determined: it contains a string"
v0.90.0: **review_required** (reasons differ: v0.90.0 says the expression is never evaluated).

Code (c17):
```gauss
// Dependent variable (5x1)
y = { 2, 3, 1, 7, 5 };

// Independent variables (5x3)
x = { 1 3 2,
      2 3 1,
      7 1 7,
      5 3 1,
      3 5 5 };

// Column names (4x1 string array)
string names = { "y", "X1", "X2", "X3" };

// Combine into a dataframe with named columns
df = setColNames(y ~ x, names);

// OLS using a formula string (constant included by default)
struct olsmtOut out;
out = olsmt(df, "y ~ X1 + X2 + X3");

print "Coefficients (CONSTANT, X1, X2, X3):";
print out.b;
```
Captured output (live, identical on the v0.91.0 re-run): **review_required**.
Reasons beyond the standard ones: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `setColNames` argument 2 (parameter `varnames`): `names` has no single traceable assignment earlier in this code"
v0.90.0: **review_required** (reasons differ: v0.90.0 says the expression is never evaluated).

The client stopped, listed the four attempts and their reasons accurately, and offered two options: run the `olsmt` code yourself, or matrix algebra here. The user answered "1"; the client gave the code to paste, marked as not checked or approved.

Expected behavior: (plan v0.91 §7; 81.5 again) `olsmt` stays `review_required` for `depvar` (81.x finding 1, out of scope).

Observed behavior: as expected for `olsmt`. Two further gaps appeared on the way. `"y" $| "X1" $| …` is a string expression ("it contains a string"; by design, only numeric categories exist). **`string names = { "y", "X1", "X2", "X3" };` is not a traceable assignment** ("`names` has no single traceable assignment"). The recording session confirmed this for every typed declaration (`string s = "a";`, `matrix y = x;`), on v0.90.0 too, so it is pre-existing and undisclosed (plan §12, finding 3). It is safe-direction. Spot checks td01-td07 show why a literal-only rule is right: GAUSS reads a typed declaration's initializer as a literal, so `x = 4; matrix y = x;` makes `y` the character constant "X" (prints `+DEN`) and `s = "a"; string t = s;` prints `S` (GAUSS 26.1.4 and 27.0.0 alike). All four versions run in GAUSS with no error. The client's statement that the data are the `olsmt` page's worked example, with constant -3.1489 (SE 1.3221), is correct (`olsmt.rst` lines 259-262).

Pass/fail: Pass
Defect severity: Low
Remediation: A typed declaration with a literal initializer could be traced (finding 3).

Overall Score: 3.6
Decision: Pass
