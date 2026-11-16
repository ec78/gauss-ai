# Evaluation Result

Date: 2026-11-16
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`fadb44dc…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-85x`), as in 80.x-84.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-85x-data`, set with `gauss-ai config set analysis-folder`) held two CSVs in `input/`: `fred_macro.csv` (quarterly FRED series, 1960Q1-2025Q4) and `wage_returns.csv` (1,000 rows, 7 columns, one text column). The human asked each task in plain words, one at a time, and answered every run prompt themselves (four "yes", one "no"). Tasks were proposed by the recording session. The tasks ran on 2026-11-16 from 06:29 to 07:43 local (12:29-13:43 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell`/`Glob` on the data folder, the GAUSS `examples` folder and the user's profile, `WebFetch`, and one `cp` into `input/`; all disclosed in its report (§7) and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.0 (tag `v0.94.0`, commit `2bcc69f`; published to PyPI on 2026-11-16, run `43864525769`), the editable install of this checkout (`gauss-ai version` = 0.94.0).
Prompt ID: 85.1
Prompt Category: MCP Data Import and Export of v0.94.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `505d9eda…` reported `server_version: 0.94.0`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 16 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.0` (every verdict equal to the live response) and at a `git archive` of `a094a6c` (the code of `v0.93.1`), and ran all 16 snippets with `tgauss.exe -b`, each from its own new directory holding copies of the two input files. The searches and reads were not re-run.
Prompt Text:

"Start a gauss-ai session. Which data files can you use, and are real GAUSS runs enabled?"

Code: none.

Captured output (live): `gauss_session_start` returned `server_version: "0.94.0"`, `runner: "gauss"`, `real_gauss_allowed: true`, the installed libraries (allowed: cmlmt, comt, gml, maxlikmt, optmt, sslib, tsmt, tspdlib), and `analysis_folder` with its `input`/`output` paths, `input_files` `fred_macro.csv` (10,934 bytes) and `wage_returns.csv` (51,768 bytes), and the note on bare names.
v0.93.1 code: no `analysis_folder` field (not applicable).

Expected behavior: (plan v0.94 §7 and decision 7) the analysis folder and its input files are reported by name and size, never by content; the opt-in is reported, and proven by the first prepare.

Observed behavior: as expected. The client named both files with sizes, said bare names are read and named writes are kept in a new folder under `output/`, and added the right caveat: the opt-in shows the server allows real runs, not that GAUSS starts. **The opt-in was proven** by 85.2's prepare, which returned a `rendered_prompt` (and then ran). **Setup finding (recorded in plan v0.94 §13):** the user's first conversation was opened in the analysis folder itself (`gauss-ai-85x-data`), where no server is registered; with no gauss-ai tools, that client listed the folder and read the CSVs' first rows with `PowerShell`, then offered to run `tgauss.exe` directly. It was stopped before any task; it ran no GAUSS.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
