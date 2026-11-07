# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`f9c5e81c…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-83x`), as in 80.x-82.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes"). Tasks were proposed by the recording session. All tasks ran on 2026-11-06, 19:47-21:34 local (2026-11-07 00:47-02:34 UTC), with a pause between 00:49 and 02:17 UTC and a client-side API outage (`ENOTFOUND`, 02:17-02:20 UTC) during 83.4. The client used gauss-ai tools plus, in 83.6, 83.7, 83.8 and 83.10, `Read`, `Grep` and `Bash` on the installed packages' sources and indexes (all read-only, all disclosed in its report); it read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.92.0 (tag `v0.92.0`, commit `e3a995d`; published to PyPI on 2026-11-06, run `42319052456`), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.92.0).
Prompt ID: 83.1
Prompt Category: MCP Installed Libraries of v0.92.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.92.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss. One server session (`046a4026…`) served every task; `gauss_session_start` reported `server_version: 0.92.0`, `real_gauss_allowed: true` and `installed_libraries` allowed `cmlmt, comt, gml, maxlikmt, optmt, sslib, tsmt, tspdlib`, not allowed `coint, dccelib, pubtable, qardl, quaids, timeseries, pgraph`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 22 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.92.0`: **every live response equals the re-run in every field** (ids and digests aside). It compared every one with a `git archive` of `v0.91.1` (`696259d`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all five approved snippets with `tgauss.exe -b`, each from its own new empty directory.
Prompt Text:

"Start a gauss-ai session, then check and run: x = { 1, 1 }; print sumc(x);"

`gauss_session_start`: `server_version: 0.92.0`, `runner: gauss`, `docs_root_configured: true`, `real_gauss_allowed: true`, and `installed_libraries` (new in v0.92.0): allowed `cmlmt, comt, gml, maxlikmt, optmt, sslib, tsmt, tspdlib`; not allowed `coint, dccelib, pubtable, qardl, quaids, timeseries, pgraph`.

Code (c01):
```gauss
x = { 1, 1 }; print sumc(x);
```
Captured output (live, identical on the v0.92.0 re-run): **handoff_candidate**.
Reasons: the five standard handoff reasons, ending "validation coverage is broad".
v0.91.1: identical.

The prompt was shown; the user answered it after 83.3 ("yes" at 00:49:27 UTC). No other prepare was made in between, so it was not superseded.

Execution handoff (prepare, `request_id` `39b02132-d861-4f87-86fb-163cf84fe174`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
x = { 1, 1 }; print sumc(x);
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: bb9928c82c26b6842abe37cf9bdd3dac5d73e42f0c6741b3afbd0b9945121cda

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id`: outcome `success`; stdout:
```
       2.0000000
```
Real GAUSS (`tgauss.exe -b`, recording session, own new empty directory): byte-identical stdout; no file created.

Expected behavior: the opt-in confirmed by `real_gauss_allowed: true` and one approved prompt (CLAUDE.md); `installed_libraries` reported.

Observed behavior: as expected; the run is byte-identical to direct `tgauss.exe -b`.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
