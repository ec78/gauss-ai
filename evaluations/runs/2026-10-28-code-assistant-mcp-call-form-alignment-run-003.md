# Evaluation Result

Date: 2026-10-28
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`a3570b26…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-81x`), as in 80.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, answered every run prompt themselves, and answered three of the client's own numbered options ("2", "1", "1"). All tasks ran on 2026-10-28, 06:01-06:19 local (11:01-11:19 UTC). The client used only gauss-ai tools: no file read, no shell command, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.90.0 (tag `v0.90.0`, commit `1ee121c`, pushed 2026-10-24; not yet on PyPI), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.90.0).
Prompt ID: 81.3
Prompt Category: MCP Call-Form Alignment of v0.90.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.90.0 over stdio, registered at user scope with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs` (the 2026-10-23 fetch), `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session served every task; `gauss_session_start` reported `server_version: 0.90.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 25 search, read and validation calls through `gauss_mcp_server`'s tool functions at `v0.90.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.89.3` (`328dffa`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all eight approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory.
Prompt Text:

"Make an autocorrelation plot of the series 1, 3, 2, 5, 4, 6, 5, 8, 7, 9 for the first 3 lags, and run it."

Search `plotACF autocorrelation function plot acf` (#9): partially grounded.

Code (#10):
```gauss
x = { 1, 3, 2, 5, 4, 6, 5, 8, 7, 9 };

// Max lags and order of differencing
k = 3;
d = 0;

// Print the sample autocorrelations
rk = acf(x, k, d);
print rk;

// ACF plot
plotACF(x, k, d);
```
Captured output (live, identical on the v0.90.0 re-run): **handoff_candidate**.
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad".
**v0.89.3: not_ready** (the misalignment).

Execution handoff (prepare #11, `request_id` `5b2524cb-5090-4778-9834-af31429e87cc`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
x = { 1, 3, 2, 5, 4, 6, 5, 8, 7, 9 };

// Max lags and order of differencing
k = 3;
d = 0;

// Print the sample autocorrelations
rk = acf(x, k, d);
print rk;

// ACF plot
plotACF(x, k, d);
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: c8330c1396ae3ff731d4cc5b9753f33817fbc5ec5ed70a74f0f6f6567d817398

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id` (decide #12): outcome `success`; stdout:
```
0.45000000 
      0.50000000 
    -0.033333333
```
Real GAUSS (`tgauss.exe -b`, recording session): byte-identical stdout.

The client printed `acf(x, k, d)` alongside the plot, so the run had a checkable result; it said it reproduced the values by hand.

Expected behavior: as 81.2.

Observed behavior: as expected.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
