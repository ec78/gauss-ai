# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`f9c5e81c…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-83x`), as in 80.x-82.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes"). Tasks were proposed by the recording session. All tasks ran on 2026-11-06, 19:47-21:34 local (2026-11-07 00:47-02:34 UTC), with a pause between 00:49 and 02:17 UTC and a client-side API outage (`ENOTFOUND`, 02:17-02:20 UTC) during 83.4. The client used gauss-ai tools plus, in 83.6, 83.7, 83.8 and 83.10, `Read`, `Grep` and `Bash` on the installed packages' sources and indexes (all read-only, all disclosed in its report); it read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.92.0 (tag `v0.92.0`, commit `e3a995d`; published to PyPI on 2026-11-06, run `42319052456`), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.92.0).
Prompt ID: 83.6
Prompt Category: MCP Installed Libraries of v0.92.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.92.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss. One server session (`046a4026…`) served every task; `gauss_session_start` reported `server_version: 0.92.0`, `real_gauss_allowed: true` and `installed_libraries` allowed `cmlmt, comt, gml, maxlikmt, optmt, sslib, tsmt, tspdlib`, not allowed `coint, dccelib, pubtable, qardl, quaids, timeseries, pgraph`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 22 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.92.0`: **every live response equals the re-run in every field** (ids and digests aside). It compared every one with a `git archive` of `v0.91.1` (`696259d`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all five approved snippets with `tgauss.exe -b`, each from its own new empty directory.
Prompt Text:

"Test a simulated random walk that has a level shift for a unit root, allowing for one structural break."

`gauss_search_docs("Zivot-Andrews unit root test one structural break tspdlib")`.

Code (c05):
```gauss
new;
library tsmt;

// Set seed for repeatable results
rndseed 52011;

// Simulate a 200-observation random walk
T = 200;
e = rndn(T, 1);
rw = cumsumc(e);

// Add a level shift of 5 starting at observation 101
shift = 5 * (seqa(1, 1, T) .> 100);
yt = rw + shift;

// Zivot-Andrews test allowing one break in the intercept
max_lags = 4;
trim_end = 0.15;
break_type = -1;
which_output = 1;
{ t_test, break_pt } = zandrews(yt, max_lags, trim_end, break_type, which_output);

print "Zivot-Andrews statistic: " t_test;
print "Estimated break point:   " break_pt;
```
Captured output (live, identical on the v0.92.0 re-run): **not_ready**.
Reasons beyond the standard ones: "line 21: `zandrews` is documented as part of the `tsmt` package, but no installed index of that package lists it in the configured GAUSS -- GAUSS would stop with G0025 (undefined symbol)"
v0.91.1: **not_ready** (reasons differ).

The client switched to `tspdlib`'s `adf_1break`, read `tspdlib/docs/adf_1br.rst` in full with `gauss_read_doc`, and passed all five documented arguments:

Code (c06):
```gauss
new;
library tspdlib;

// Set seed for repeatable results
rndseed 52011;

// Simulate a 200-observation random walk
T = 200;
e = rndn(T, 1);
rw = cumsumc(e);

// Add a level shift of 5 starting at observation 101
shift = 5 * (seqa(1, 1, T) .> 100);
y = rw + shift;

// ADF test with one break in the level
model = 1;
pmax = 8;
ic = 3;
trimm = 0.10;
{ tstat, tb, lags, cv } = adf_1break(y, model, pmax, ic, trimm);

print "ADF statistic (minimum): " tstat;
print "Estimated break point:   " tb;
print "Lags selected:           " lags;
print "Critical values (1%, 5%, 10%):";
print cv;
```
Captured output (live, identical on the v0.92.0 re-run): **handoff_candidate**.
Reasons: the five standard handoff reasons, ending "validation coverage is broad".
v0.91.1: **not_ready**.

Execution handoff (prepare, `request_id` `2fb666ba-d512-46b8-96f9-0c68467c9a5f`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
new;
library tspdlib;

// Set seed for repeatable results
rndseed 52011;

// Simulate a 200-observation random walk
T = 200;
e = rndn(T, 1);
rw = cumsumc(e);

// Add a level shift of 5 starting at observation 101
shift = 5 * (seqa(1, 1, T) .> 100);
y = rw + shift;

// ADF test with one break in the level
model = 1;
pmax = 8;
ic = 3;
trimm = 0.10;
{ tstat, tb, lags, cv } = adf_1break(y, model, pmax, ic, trimm);

print "ADF statistic (minimum): " tstat;
print "Estimated break point:   " tb;
print "Lags selected:           " lags;
print "Critical values (1%, 5%, 10%):";
print cv;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Library: tspdlib (C:\gauss26\pkgs\tspdlib\lib\tspdlib.lcg)
Request digest: e7c03e579c18050c03d15f2e0d72175e19f79e44eb30d5d4563cd671df8189de

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id`: outcome `execution_failed`; the full rendered result:
~~~~text
GAUSS returned an execution error.

stdout:
Program execute failed


stderr:

GAUSS 26.1.4 (Aug 17 2026, 5565) 64-bit
(C)Copyright 1984-2026 Aptech Systems, Inc.
All Rights Reserved Worldwide.


Job: inline_2y_gksio.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_0bjsdxbq\.gauss_code_execution_generated )
Fri Nov  6 20:26:06 2026


error G0152 : Variable not initialized
	c:\gauss26\pkgs\tspdlib\src\getlag.src, line 77
Currently active call:
	c:\gauss26\pkgs\tspdlib\src\getlag.src, Line 77 in _get_lag
Traceback:
	c:\gauss26\pkgs\tspdlib\src\adf_1br.src, Line 176 in adf_1break
	C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_0bjsdxbq\.gauss_code_execution_generated\inline_2y_gksio.gss, Line 21 in  <main>


GAUSS exit status: 0

No retry or repair was attempted.
~~~~
Real GAUSS (`tgauss.exe -b`, recording session, own new empty directory): the same stdout and the same errors; no file created.

The client then read the installed source (`getlag.src`, `adf_1br.src`; disclosed) and found that the installed `ADF_1break(y, model, ...)` takes `outlier` third (`dynargsGet(1|4, 1, 8, 3, 0.10)`), which the docs page omits. It dropped the optional arguments:

Code (c07):
```gauss
new;
library tspdlib;

// Set seed for repeatable results
rndseed 52011;

// Simulate a 200-observation random walk
T = 200;
e = rndn(T, 1);
rw = cumsumc(e);

// Add a level shift of 5 starting at observation 101
shift = 5 * (seqa(1, 1, T) .> 100);
y = rw + shift;

// ADF test with one break in the level, using the library defaults:
// innovational outlier model, max 8 lags, t-stat lag selection, 10% trimming
model = 1;
{ tstat, tb, lags, cv } = adf_1break(y, model);

print "ADF statistic (minimum): " tstat;
print "Estimated break point:   " tb;
print "Lags selected:           " lags;
print "Critical values (1%, 5%, 10%):";
print cv;
```
Captured output (live, identical on the v0.92.0 re-run): **handoff_candidate**.
Reasons: the five standard handoff reasons, ending "validation coverage is broad".
v0.91.1: **not_ready**.

Execution handoff (prepare, `request_id` `8ac2f5a8-98ad-41fc-8b98-7b6bbb5872a7`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
new;
library tspdlib;

// Set seed for repeatable results
rndseed 52011;

// Simulate a 200-observation random walk
T = 200;
e = rndn(T, 1);
rw = cumsumc(e);

// Add a level shift of 5 starting at observation 101
shift = 5 * (seqa(1, 1, T) .> 100);
y = rw + shift;

// ADF test with one break in the level, using the library defaults:
// innovational outlier model, max 8 lags, t-stat lag selection, 10% trimming
model = 1;
{ tstat, tb, lags, cv } = adf_1break(y, model);

print "ADF statistic (minimum): " tstat;
print "Estimated break point:   " tb;
print "Lags selected:           " lags;
print "Critical values (1%, 5%, 10%):";
print cv;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Library: tspdlib (C:\gauss26\pkgs\tspdlib\lib\tspdlib.lcg)
Request digest: 38589996eef54e6c3bb601164f8a8cd74141ec40eff9f4ae4b4d548951124580

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id`: outcome `success`; stdout:
```

Test:                                                    ADF 
Ho:                                                Unit root 
Number of breaks:                                          1 
Lag selection:                          T-stat lag selection 
Trimming rate (%):                                        10 
Model:                                        Break in level 
==============================================================
ADF-stat:                                             -2.822
Chosen Lags:                                               6

Critical Values:
                            1%             5%            10%
                        -5.340         -4.800         -4.580
==============================================================

Estimated break dates:
                                         Date       Fraction
First break:                               43          0.215
==============================================================
Cannot reject the null hypothesis of a unit root.

ADF statistic (minimum):       -2.8219725 
Estimated break point:          43.000000 
Lags selected:                  6.0000000 
Critical values (1%, 5%, 10%):

      -5.3400000 
      -4.8000000 
      -4.5800000
```
Real GAUSS (`tgauss.exe -b`, recording session, own new empty directory): byte-identical stdout; no file created.

Expected behavior: (plan v0.92 §7) a `tspdlib` unit-root test with `library tspdlib;` reaches a prompt and runs.

Observed behavior: **as expected in the end, with two lessons.** (1) `zandrews` after `library tsmt;` was not_ready, "no installed index of that package lists it": correct, since GAUSS loads `pkgs\timeseries\lib\tsmt.lcg` and `library tsmt; f = &zandrews;` is `G0025` (recording-session spot check lb22), even though the legacy `pkgs\tsmt\lib\tsmt.lcg` lists it. (2) The documented five-argument call passed every check and failed at run time with `G0152` inside `tspdlib` (`getlag.src`, line 77), because **`adf_1br.rst` omits the installed `outlier` argument**: the arguments shifted (`outlier = 8`, `pmax = 3`, `ic = 0.10`). With `outlier` supplied, the call runs (lb23). This is a documentation error, for Aptech, and also explains the `G0152` row of plan v0.92 §9.4. The two-argument version ran; both runs, failure included, equal direct `tgauss.exe -b`.

Pass/fail: Pass
Defect severity: Low (upstream documentation)
Remediation: Report `tspdlib/docs/adf_1br.rst` to Aptech.

Overall Score: 3.4
Decision: Pass
