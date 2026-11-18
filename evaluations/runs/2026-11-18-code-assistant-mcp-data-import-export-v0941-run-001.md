# Evaluation Result

Date: 2026-11-18
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`0280b330...`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-86x`), as in 80.x-85.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-86x-data`) held fresh copies of 85.x's two original CSVs in `input/` (`fred_macro.csv`, `wage_returns.csv`) and an empty `output/`. The human asked each task in plain words, one at a time, and answered every run prompt themselves (eight "yes", one "no"). The tasks and their expected outcomes were stated to the user before the run (plan v0.94 §15). The tasks ran on 2026-11-18 from 06:01 to 06:22 local (12:01-12:22 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell` on the data folder, the GAUSS `examples` folder and the user's Desktop, one `curl` to FRED, and `AskUserQuestion`; all disclosed in its report and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.1 (tag `v0.94.1`, commit `e55b271`; published to PyPI on 2026-11-18, run `44298126085`), the editable install of this checkout (`gauss-ai version` = 0.94.1).
Prompt ID: 86.0
Prompt Category: MCP Data Import and Export of v0.94.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.1 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `59e30e87...` reported `server_version: 0.94.1`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 24 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.1` (every verdict equal to the live response) and at a `git archive` of `v0.94.0`, and ran all 24 with `tgauss.exe -b`, each from its own new directory holding copies of the input files (all 24 exit 0 with no GAUSS error). The searches and reads were not re-run.
Prompt Text:

"Start a GAUSS session and tell me what data files I have available. Then run a one-line GAUSS program that prints 2+2."

Code (validation 1, `not_ready`):
```gauss
print 2+2;
```
Code (validation 2, `handoff_candidate`):
```gauss
print sumc(2|2);
```

Captured output (live, equal to the v0.94.1 re-run): **not_ready** ("no documented GAUSS function call was found to ground this code against"), then **handoff_candidate**.
v0.94.0 code: the same.

Expected behavior: (plan v0.94 §15) the opt-in reported and proven by a run; both input files listed by name and size.

Observed behavior: `gauss_session_start` returned `server_version: "0.94.1"`, `real_gauss_allowed: true` and both input files with sizes. Bare `print 2+2;` is `not_ready` by long-standing design (code with no documented call is never eligible); the client wrote `print sumc(2|2);` and said why. **Run:** request_id `65d344e1-d12a-4452-bf7a-5a7d8e11fc45`; prompt shown verbatim; user "yes"; success, exit 0, `4.0000000`. This proves the opt-in. The client noted that `gauss_validate_code`'s description does not state the no-documented-call rule.

Pass/fail: Pass
Defect severity: None
Remediation: None (the client's note on the tool description is recorded in plan v0.94 §16).

Overall Score: 3.9
Decision: Pass
