# Evaluation Result

Date: 2026-11-18
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`0280b330...`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-86x`), as in 80.x-85.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-86x-data`) held fresh copies of 85.x's two original CSVs in `input/` (`fred_macro.csv`, `wage_returns.csv`) and an empty `output/`. The human asked each task in plain words, one at a time, and answered every run prompt themselves (eight "yes", one "no"). The tasks and their expected outcomes were stated to the user before the run (plan v0.94 §15). The tasks ran on 2026-11-18 from 06:01 to 06:22 local (12:01-12:22 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell` on the data folder, the GAUSS `examples` folder and the user's Desktop, one `curl` to FRED, and `AskUserQuestion`; all disclosed in its report and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.1 (tag `v0.94.1`, commit `e55b271`; published to PyPI on 2026-11-18, run `44298126085`), the editable install of this checkout (`gauss-ai version` = 0.94.1).
Prompt ID: 86.1
Prompt Category: MCP Data Import and Export of v0.94.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.1 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `59e30e87...` reported `server_version: 0.94.1`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 24 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.1` (every verdict equal to the live response) and at a `git archive` of `v0.94.0`, and ran all 24 with `tgauss.exe -b`, each from its own new directory holding copies of the input files (all 24 exit 0 with no GAUSS error). The searches and reads were not re-run.
Prompt Text:

"Using wage_returns.csv, make a dataset of only the women and save it as an Excel file"

Code (validation 3, `review_required`):
```gauss
// Load all variables; Region is read as a category
wage = loadd("wage_returns.csv");

// Keep only rows where Female equals 1
women = selif(wage, wage[., "Female"] .== 1);

print "Rows in full data:  " rows(wage);
print "Rows for women:     " rows(women);
print women[1:5, .];

// Save as Excel, keeping variable names as headers
ret = saved(women, "wage_returns_women.xlsx");
print "saved returned " ret;
```
Code (validation 4, `review_required`):
```gauss
// Load all variables; Region is read as a category
wage = loadd("wage_returns.csv");

// Column 4 is Female (1 = woman); build a 0/1 mask
mask = wage[., 4] .== 1;
women = selif(wage, mask);

print women[1:5, .];

// Save as Excel, keeping variable names as headers
ret = saved(women, "wage_returns_women.xlsx");
print "saved returned " ret;
```
Code (validation 5, `handoff_candidate`):
```gauss
// Load all variables; Region is read as a category
wage = loadd("wage_returns.csv");

// Column 4 is Female (1 = woman); find the row numbers of the women
idx = indexcat(wage[., 4], 1);
women = wage[idx, .];

print women[1:5, .];

// Save as Excel, keeping variable names as headers
ret = saved(women, "wage_returns_women.xlsx");
print "saved returned " ret;
```

Captured output (live, equal to the v0.94.1 re-run): **review_required**, **review_required**, **handoff_candidate**.
v0.94.0 code: all three **review_required** (the column slice is v0.94.1's).

Expected behavior: (plan v0.94 §15) a plain column filter reaches `handoff_candidate` in a few attempts.

Observed behavior: as expected on the third attempt, with `indexcat(wage[., 4], 1)`. The first two were held back by gaps the recording session confirmed with `validate_code(...)`: `selif` argument 2, `wage[., "Female"] .== 1`, "it indexes with a string" (`argument_expression`), and `saved`/`rows` argument 1 traced to `selif`'s documented return `string/dataframe/matrix` (`return_type_imprecise`). The client said each change was made to clear a gap, and that indexing by position is more fragile than by name. **Run:** request_id `cb8391ec-5471-43fe-ac4a-56f018e9d6d2`; user "yes"; success, exit 0, five rows with Female = 1 and Region as text; kept `wage_returns_women.xlsx` (36,149 bytes) in `output\20261118T120335Z-cb8391ec`; `xls.log` listed, not kept. The 496-row count the client reported came from its own `awk`, not from GAUSS. `tgauss.exe -b`: all three versions run with no error (the first prints 1,000 and 496 rows).

Pass/fail: Pass with defect recorded
Defect severity: Low
Remediation: Read a column by name, `x[., "Female"]`, as a column vector (plan v0.94 §16). `selif`'s return following its first argument is a coverage candidate.

Overall Score: 3.6
Decision: Pass with defect recorded
