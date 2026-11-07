# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`f9c5e81c…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-83x`), as in 80.x-82.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes"). Tasks were proposed by the recording session. All tasks ran on 2026-11-06, 19:47-21:34 local (2026-11-07 00:47-02:34 UTC), with a pause between 00:49 and 02:17 UTC and a client-side API outage (`ENOTFOUND`, 02:17-02:20 UTC) during 83.4. The client used gauss-ai tools plus, in 83.6, 83.7, 83.8 and 83.10, `Read`, `Grep` and `Bash` on the installed packages' sources and indexes (all read-only, all disclosed in its report); it read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.92.0 (tag `v0.92.0`, commit `e3a995d`; published to PyPI on 2026-11-06, run `42319052456`), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.92.0).
Prompt ID: 83.3
Prompt Category: MCP Installed Libraries of v0.92.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.92.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss. One server session (`046a4026…`) served every task; `gauss_session_start` reported `server_version: 0.92.0`, `real_gauss_allowed: true` and `installed_libraries` allowed `cmlmt, comt, gml, maxlikmt, optmt, sslib, tsmt, tspdlib`, not allowed `coint, dccelib, pubtable, qardl, quaids, timeseries, pgraph`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 22 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.92.0`: **every live response equals the re-run in every field** (ids and digests aside). It compared every one with a `git archive` of `v0.91.1` (`696259d`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all five approved snippets with `tgauss.exe -b`, each from its own new empty directory.
Prompt Text:

"Split 200 rows of simulated data into training and test sets, 70/30, and print how many rows are in each"

The client searched "split data into training and test sets trainTestSplit" (grounded).

Code (c02):
```gauss
library gml;

// Set seed for repeatable sampling
rndseed 23324;

// Simulate 200 observations: 1 dependent variable, 3 regressors
X = rndn(200, 3);
y = X * { 0.5, -1, 2 } + rndn(200, 1);

// Shuffle and split 70/30
{ y_train, y_test, X_train, X_test } = trainTestSplit(y, X, 0.7);

print "Training rows: " rows(X_train);
print "Test rows:     " rows(X_test);
```
Captured output (live, identical on the v0.92.0 re-run): **review_required**.
Reasons beyond the standard ones: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `rows` argument 1 (parameter `x`): `X_train` has no single traceable assignment earlier in this code"; "parameter role unknown -- `rows` argument 1 (parameter `x`): `X_test` has no single traceable assignment earlier in this code"
v0.91.1: **not_ready**.

Expected behavior: (plan v0.92 §7) a GML program with `library gml;` gets past the library rule.

Observed behavior: the `library gml;` line was accepted and the result names the bound index (`libraries`: `gml`, `C:\gauss26\pkgs\gml\lib\gml.lcg`). The program stays review_required because names assigned by a multiple return (`{ y_train, y_test, X_train, X_test } = trainTestSplit(...)`) are never traced, so `rows(X_train)` cannot be confirmed (pre-existing; 82.13 the same). The client did not reshape the code and said why. At v0.91.1: not_ready (`library` was source inclusion).

Pass/fail: Pass
Defect severity: Low
Remediation: Multiple-return tracing (plan v0.92 §12, finding 3).

Overall Score: 3.6
Decision: Pass
