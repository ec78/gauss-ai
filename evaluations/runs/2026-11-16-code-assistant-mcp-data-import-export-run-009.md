# Evaluation Result

Date: 2026-11-16
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`fadb44dc…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-85x`), as in 80.x-84.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-85x-data`, set with `gauss-ai config set analysis-folder`) held two CSVs in `input/`: `fred_macro.csv` (quarterly FRED series, 1960Q1-2025Q4) and `wage_returns.csv` (1,000 rows, 7 columns, one text column). The human asked each task in plain words, one at a time, and answered every run prompt themselves (four "yes", one "no"). Tasks were proposed by the recording session. The tasks ran on 2026-11-16 from 06:29 to 07:43 local (12:29-13:43 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell`/`Glob` on the data folder, the GAUSS `examples` folder and the user's profile, `WebFetch`, and one `cp` into `input/`; all disclosed in its report (§7) and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.0 (tag `v0.94.0`, commit `2bcc69f`; published to PyPI on 2026-11-16, run `43864525769`), the editable install of this checkout (`gauss-ai version` = 0.94.0).
Prompt ID: 85.9
Prompt Category: MCP Data Import and Export of v0.94.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `505d9eda…` reported `server_version: 0.94.0`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 16 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.0` (every verdict equal to the live response) and at a `git archive` of `a094a6c` (the code of `v0.93.1`), and ran all 16 snippets with `tgauss.exe -b`, each from its own new directory holding copies of the two input files. The searches and reads were not re-run.
Prompt Text:

"Download the latest unemployment rate from FRED."

Code: none validated by the client. Recording-session checks:
```gauss
u = loadd("https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE", "UNRATE");
print u[rows(u)];
```
```gauss
u = loadd("unrate_monthly.csv", "UNRATE");
print rows(u);
```

Captured output (recording session, v0.94.0, same folder): the URL read is **not_ready** ("… is not a bare file name (no folder, drive, `..` or URL may appear) (file_read)"); the bare name of the file the client added mid-session is **handoff_candidate**.
v0.93.1 code: both **not_ready**.

Expected behavior: (plan v0.94 §7) a URL is `not_ready`, with a reason the client can explain; gauss-ai makes no network call.

Observed behavior: the client did not try GAUSS ("the server instructions say URLs are never allowed"). It fetched FRED's CSV with its own `WebFetch` (latest: October 2026, 4.1%), checked the download with `Bash`, and **copied it into the user's `input/` as `unrate_monthly.csv` without being asked** (disclosed as its own decision, report §7 item 13). gauss-ai made no network call. The copy is outside the server's reach: the analysis folder keeps GAUSS out of the user's folders, but a client's own tools can still write there. A file added to `input/` after `gauss_session_start` is accepted (the session's listing is a snapshot; the check reads the folder).

Pass/fail: Pass with limitation disclosed
Defect severity: None (server); client conduct recorded
Remediation: Say in `docs/mcp-server.md` that the input listing is a snapshot and that a client's own file tools are outside gauss-ai's control.

Overall Score: 3.3
Decision: Pass with limitation disclosed
