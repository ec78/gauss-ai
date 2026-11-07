# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`f9c5e81c…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-83x`), as in 80.x-82.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes"). Tasks were proposed by the recording session. All tasks ran on 2026-11-06, 19:47-21:34 local (2026-11-07 00:47-02:34 UTC), with a pause between 00:49 and 02:17 UTC and a client-side API outage (`ENOTFOUND`, 02:17-02:20 UTC) during 83.4. The client used gauss-ai tools plus, in 83.6, 83.7, 83.8 and 83.10, `Read`, `Grep` and `Bash` on the installed packages' sources and indexes (all read-only, all disclosed in its report); it read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.92.0 (tag `v0.92.0`, commit `e3a995d`; published to PyPI on 2026-11-06, run `42319052456`), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.92.0).
Prompt ID: 83.7
Prompt Category: MCP Installed Libraries of v0.92.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.92.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss. One server session (`046a4026…`) served every task; `gauss_session_start` reported `server_version: 0.92.0`, `real_gauss_allowed: true` and `installed_libraries` allowed `cmlmt, comt, gml, maxlikmt, optmt, sslib, tsmt, tspdlib`, not allowed `coint, dccelib, pubtable, qardl, quaids, timeseries, pgraph`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 22 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.92.0`: **every live response equals the re-run in every field** (ids and digests aside). It compared every one with a `git archive` of `v0.91.1` (`696259d`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all five approved snippets with `tgauss.exe -b`, each from its own new empty directory.
Prompt Text:

"Estimate a GARCH(1,1) model on simulated returns and print the parameters."

`gauss_search_docs("garchFit GARCH(1,1) estimation")`; then `Grep` and four `Bash` commands over `C:\gauss26\pkgs` (`.lcg` and `.src` files, `gauss.cfg`; disclosed).

Code (c08):
```gauss
new;
library tsmt;

// Set seed for repeatable results
rndseed 90210;

// True GARCH(1,1) parameters
omega = 0.1;
alpha = 0.1;
beta = 0.8;

// Simulate 1000 returns, plus 500 burn-in draws that are discarded
n = 1500;
z = rndn(n, 1);
h = zeros(n, 1);
r = zeros(n, 1);
h[1] = omega / (1 - alpha - beta);
r[1] = sqrt(h[1]) * z[1];
for t(2, n, 1);
    h[t] = omega + alpha * r[t-1]^2 + beta * h[t-1];
    r[t] = sqrt(h[t]) * z[t];
endfor;
y = r[501:n];

// Estimate GARCH(1,1); garchFit prints the parameter estimates
struct garchEstimation gOut;
gOut = garchFit(y, 1, 1);

print "True values: omega = 0.1, alpha = 0.1, beta = 0.8";
```
Captured output (live, identical on the v0.92.0 re-run): **handoff_candidate**.
Reasons: the five standard handoff reasons, ending "validation coverage is broad".
v0.91.1: **not_ready**.

Before the prompt, the client told the user the run might stop at the `timeseries` placeholder `garchFit`.

Execution handoff (prepare, `request_id` `e90ca300-6e49-46e0-bed0-6861d7b4cb53`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
new;
library tsmt;

// Set seed for repeatable results
rndseed 90210;

// True GARCH(1,1) parameters
omega = 0.1;
alpha = 0.1;
beta = 0.8;

// Simulate 1000 returns, plus 500 burn-in draws that are discarded
n = 1500;
z = rndn(n, 1);
h = zeros(n, 1);
r = zeros(n, 1);
h[1] = omega / (1 - alpha - beta);
r[1] = sqrt(h[1]) * z[1];
for t(2, n, 1);
    h[t] = omega + alpha * r[t-1]^2 + beta * h[t-1];
    r[t] = sqrt(h[t]) * z[t];
endfor;
y = r[501:n];

// Estimate GARCH(1,1); garchFit prints the parameter estimates
struct garchEstimation gOut;
gOut = garchFit(y, 1, 1);

print "True values: omega = 0.1, alpha = 0.1, beta = 0.8";
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Library: tsmt (C:\gauss26\pkgs\timeseries\lib\tsmt.lcg)
Request digest: ff831b2d8ec18638ff92b763be09d126d12f0735d788fe63c945c8b8704af7f7

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id`: outcome `execution_failed`; the full rendered result:
~~~~text
GAUSS returned an execution error.

stdout:
(none)

stderr:

GAUSS 26.1.4 (Aug 17 2026, 5565) 64-bit
(C)Copyright 1984-2026 Aptech Systems, Inc.
All Rights Reserved Worldwide.


Job: inline_jbljzx7b.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_n2d0jjjh\.gauss_code_execution_generated )
Fri Nov  6 20:29:21 2026


error G0507 : Undefined structure 'garchEstimation gOut'
	C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_n2d0jjjh\.gauss_code_execution_generated\inline_jbljzx7b.gss, line 26
error G0008 : Syntax error 'gOut'
	C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_n2d0jjjh\.gauss_code_execution_generated\inline_jbljzx7b.gss, line 26


GAUSS exit status: 0

No retry or repair was attempted.
~~~~
Real GAUSS (`tgauss.exe -b`, recording session, own new empty directory): the same stdout and the same errors; no file created.

Expected behavior: (plan v0.92 §2.5) `garchFit` resolves through `library tsmt;` and may fail at run time inside the incomplete `timeseries` code.

Observed behavior: **a false `handoff_candidate`.** The code declares `struct garchEstimation gOut;`, a structure defined only in the legacy `pkgs\tsmt\src\tsmt.sdf`; the index GAUSS loads for `library tsmt;` defines `garchResult` instead (lb24: `struct garchResult r;` is defined). GAUSS stopped at compile time with `G0507: Undefined structure 'garchEstimation gOut'` before reaching `garchFit`. The validator checks calls against the index but not structure types, which `KNOWN_LIMITATIONS.md` discloses for v0.92.0 ("A package structure type ... without its library is not flagged"); this is the first time a client hit it. No harm beyond a failed run: nothing was written, and the result equals direct `tgauss.exe -b`.

Pass/fail: Fail
Defect severity: Low (a compile-time failure; disclosed limitation, now live)
Remediation: Check `struct <type>` declarations against the active indexes (plan v0.92 §12, finding 1).

Overall Score: 2.5
Decision: Fail
