# Evaluation Result

Date: 2026-11-18
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`0280b330...`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-86x`), as in 80.x-85.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-86x-data`) held fresh copies of 85.x's two original CSVs in `input/` (`fred_macro.csv`, `wage_returns.csv`) and an empty `output/`. The human asked each task in plain words, one at a time, and answered every run prompt themselves (eight "yes", one "no"). The tasks and their expected outcomes were stated to the user before the run (plan v0.94 §15). The tasks ran on 2026-11-18 from 06:01 to 06:22 local (12:01-12:22 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell` on the data folder, the GAUSS `examples` folder and the user's Desktop, one `curl` to FRED, and `AskUserQuestion`; all disclosed in its report and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.1 (tag `v0.94.1`, commit `e55b271`; published to PyPI on 2026-11-18, run `44298126085`), the editable install of this checkout (`gauss-ai version` = 0.94.1).
Prompt ID: 86.7
Prompt Category: MCP Data Import and Export of v0.94.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.1 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `59e30e87...` reported `server_version: 0.94.1`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 24 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.1` (every verdict equal to the live response) and at a `git archive` of `v0.94.0`, and ran all 24 with `tgauss.exe -b`, each from its own new directory holding copies of the input files (all 24 exit 0 with no GAUSS error). The searches and reads were not re-run.
Prompt Text:

"Run a regression using one of GAUSS's built-in example datasets."

Code (validation 22, `handoff_candidate`):
```gauss
// GAUSS example dataset: 1978 automobile data (74 car models)
fname = getGAUSSHome() $+ "examples/auto2.dta";

// OLS of price on fuel economy and weight, with a constant; prints the full table
struct olsmtOut out;
out = olsmt(fname, "price ~ mpg + weight");
```

Captured output (live, equal to the v0.94.1 re-run): **handoff_candidate** (`file_accesses`: `location: gauss_examples`, `C:\gauss26\examples\auto2.dta`).
v0.94.0 code: the same.

Expected behavior: (plan v0.94 §15) the two-part `getGAUSSHome() $+` idiom is allowed; the one-argument form is refused.

Observed behavior: as expected for the idiom, on the first try; the client listed the examples folder with its own shell first. The one-argument form was not attempted. **Run:** request_id `d9abda40-9b88-42a9-ae06-3bd0cce4b016`; the prompt said "Reads in place (GAUSS example data, not changed): C:\gauss26\examples\auto2.dta (6,716 bytes, sha256 e99dc1ea75fdad23...)"; user "yes"; success, exit 0 (74 cases, R² 0.293). `tgauss.exe -b`: the same table.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
