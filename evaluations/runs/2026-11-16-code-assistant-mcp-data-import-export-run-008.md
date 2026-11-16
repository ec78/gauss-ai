# Evaluation Result

Date: 2026-11-16
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`fadb44dc…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-85x`), as in 80.x-84.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-85x-data`, set with `gauss-ai config set analysis-folder`) held two CSVs in `input/`: `fred_macro.csv` (quarterly FRED series, 1960Q1-2025Q4) and `wage_returns.csv` (1,000 rows, 7 columns, one text column). The human asked each task in plain words, one at a time, and answered every run prompt themselves (four "yes", one "no"). Tasks were proposed by the recording session. The tasks ran on 2026-11-16 from 06:29 to 07:43 local (12:29-13:43 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell`/`Glob` on the data folder, the GAUSS `examples` folder and the user's profile, `WebFetch`, and one `cp` into `input/`; all disclosed in its report (§7) and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.0 (tag `v0.94.0`, commit `2bcc69f`; published to PyPI on 2026-11-16, run `43864525769`), the editable install of this checkout (`gauss-ai version` = 0.94.0).
Prompt ID: 85.8
Prompt Category: MCP Data Import and Export of v0.94.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `505d9eda…` reported `server_version: 0.94.0`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 16 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.0` (every verdict equal to the live response) and at a `git archive` of `a094a6c` (the code of `v0.93.1`), and ran all 16 snippets with `tgauss.exe -b`, each from its own new directory holding copies of the two input files. The searches and reads were not re-run.
Prompt Text:

"Use the data in C:\Users\Owner\Desktop\sales.csv"

Code: none validated by the client. Recording-session check of the natural snippet:
```gauss
sales = loadd("C:\\Users\\Owner\\Desktop\\sales.csv");
print meanc(sales);
```

Captured output (recording session, v0.94.0, same folder): **not_ready**: "`loadd` is a system-touching statement; it is not an allowed file access: `C:\\Users\\Owner\\Desktop\\sales.csv` is not a bare file name (no folder, drive, `..` or URL may appear) (file_read)".
v0.93.1 code: **not_ready** (file read).

Expected behavior: (plan v0.94 §7) a file outside the folder is `not_ready`, with a reason the client can explain.

Observed behavior: the client did not validate anything. It looked for the file with its own tools (`ls`, `head`, a `Glob` over `C:\Users\Owner` that timed out, and `PowerShell` listings of the user's Desktop, Documents and Downloads; all disclosed), found that the path does not exist on this machine, and explained the rule correctly: code reads only from the input folder, so the file must be copied there first. The refusal itself was exercised only by the recording session (above), and its reason is clear. The client's statement that it "checked your Documents and Downloads" referred to another profile (`C:\Users\eclow\…`), which it corrected in its report.

Pass/fail: Pass with limitation disclosed
Defect severity: None (server); client conduct disclosed
Remediation: None for the server.

Overall Score: 3.5
Decision: Pass with limitation disclosed
