# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`8ab50628…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-82x`), as in 80.x and 81.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes", one "no") and one of the client's own numbered options ("1"). Tasks 82.1-82.9 were proposed by the recording session; 82.10-82.14 were the user's own. All tasks ran on 2026-11-06, 06:34-06:53 local (11:34-11:53 UTC). The client used gauss-ai tools plus five PowerShell commands that checked paths, listed folders and read executable version numbers (82.9, 82.12, 82.14); it read no file's contents, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.91.0 (tag `v0.91.0`, commit `5b07a28`; published to PyPI on 2026-11-06, run `42206846915`), the editable install of this checkout (`gauss-ai version` = 0.91.0).
Prompt ID: 82.7
Prompt Category: MCP Expression Categories of v0.91.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.91.0 over stdio, registered at local scope for the folder under both drive-letter spellings (`C:/…` and `c:/…`) with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session (`f7274c39…`) served every task; `gauss_session_start` reported `server_version: 0.91.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 37 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.91.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.90.0` (`1ee121c`), diagnosed each non-candidate verdict with `validate_code(...)` directly, re-ran all five approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory, and ran every other non-blocked snippet the same way.
Prompt Text:

"Estimate an OLS regression on simulated data with olsmt, and print the coefficients and their standard errors."

The client read `olsmt.rst` with `gauss_read_doc` (section "Output" → `unknown_section` with the section list; then "Basic usage with matrices"; then "Format" at offsets 0 and 8000).

Code (c18):
```gauss
// Reproducible draws
rndseed 20261106;

n = 100;

// Two standard-normal regressors (olsmt adds the constant itself)
x = rndn(n, 2);

// True coefficients: constant 1, slopes 2 and -0.5; noise sd 0.5
y = 1 + x * (2 | -0.5) + 0.5 * rndn(n, 1);

// OLS with matrices passed directly; suppress the printed report
struct olsmtControl ctl;
ctl = olsmtControlCreate();
ctl.output = 0;

struct olsmtOut out;
out = olsmt("", y, x, ctl);

print "      True        OLS         SE";
print (1 | 2 | -0.5) ~ out.b ~ out.stderr;
```
Captured output (live, identical on the v0.91.0 re-run): **review_required**.
Reasons beyond the standard ones: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `olsmt` argument 2 (parameter `depvar`): no documented `:type` line was matched to this parameter"; "parameter role unknown -- `olsmt` argument 4 (parameter `ctl`): no documented `:type` line was matched to this parameter"
v0.90.0: identical.

Not run (no prompt). The client gave the code to paste and a table of the values it expected, from 82.2's run on the same draws.

Expected behavior: (plan v0.91 §7; 81.7 again) `olsmt` stays `review_required` for `depvar`.

Observed behavior: as expected: `depvar` and `ctl` have no matched `:type` (81.x finding 1; `KNOWN_LIMITATIONS.md`). Unlike 81.7, the client used the matrix form, so no `asdf` gap appeared. The recording session ran the code directly: its coefficients and standard errors equal 82.2's, as the client predicted. `gauss_read_doc`'s `unknown_section` reply led the client to the right section in one step.

Pass/fail: Pass
Defect severity: None (known)
Remediation: 81.x finding 1 (documentation extraction).

Overall Score: 3.6
Decision: Pass
