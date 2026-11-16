# Evaluation Result

Date: 2026-11-16
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`fadb44dc…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-85x`), as in 80.x-84.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-85x-data`, set with `gauss-ai config set analysis-folder`) held two CSVs in `input/`: `fred_macro.csv` (quarterly FRED series, 1960Q1-2025Q4) and `wage_returns.csv` (1,000 rows, 7 columns, one text column). The human asked each task in plain words, one at a time, and answered every run prompt themselves (four "yes", one "no"). Tasks were proposed by the recording session. The tasks ran on 2026-11-16 from 06:29 to 07:43 local (12:29-13:43 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell`/`Glob` on the data folder, the GAUSS `examples` folder and the user's profile, `WebFetch`, and one `cp` into `input/`; all disclosed in its report (§7) and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.0 (tag `v0.94.0`, commit `2bcc69f`; published to PyPI on 2026-11-16, run `43864525769`), the editable install of this checkout (`gauss-ai version` = 0.94.0).
Prompt ID: 85.6
Prompt Category: MCP Data Import and Export of v0.94.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `505d9eda…` reported `server_version: 0.94.0`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 16 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.0` (every verdict equal to the live response) and at a `git archive` of `a094a6c` (the code of `v0.93.1`), and ran all 16 snippets with `tgauss.exe -b`, each from its own new directory holding copies of the two input files. The searches and reads were not re-run.
Prompt Text:

"Save the rows for women from wage_returns.csv to an Excel file."

Code (seven validations; the first and the final shown; all seven in the transcript and in the client's report):
```gauss
// Load all columns of the wage data (Region is a text column)
wages = loadd("wage_returns.csv");

// Keep only the rows where Female = 1
women = selif(wages, wages[., "Female"] .== 1);

print "Rows for women:";
print rows(women);
print "First 5 rows:";
print women[1:5, .];

// Save to Excel, keeping the column names
ret = saved(women, "wage_returns_women.xlsx");
print "saved returned (1 = success):";
print ret;
```

```gauss
// Load all columns of the wage data
// Columns: Wage, Education, Experience, Female, Union, Region, LogWage
wages = loadd("wage_returns.csv");

// Load the Female indicator (0/1) on its own, as a column vector
female = vec(loadd("wage_returns.csv", "Female"));

// Row numbers where Female = 1
idx = indexcat(female, 1);
print "Rows for women:";
print rows(idx);

// Keep those rows, all columns
women = wages[idx, .];

// Save to Excel, keeping the column names
ret = saved(women, "wage_returns_women.xlsx");
print "saved returned (1 = success):";
print ret;
```

Captured output (live, equal to the v0.94.0 re-run): six **review_required**, then **handoff_candidate** (reads `wage_returns.csv` twice; writes `wage_returns_women.xlsx`).
v0.93.1 code: all seven **not_ready**.

Expected behavior: (plan v0.94 §3.2) a filtered table written with `saved` to `.xlsx` and kept.

Observed behavior: the gaps, in order: `selif` argument 2 "it indexes with a string" (`wages[., "Female"]`), and `rows`/`saved` "a call whose documented return type is string/dataset/matrix" (`selif`'s union return); `selif` argument 2 "an expression whose every operand is numeric; its shape is not computed" (`wages[., 4] .== 1`); `saved` argument 1 "operand `sorted` is not numeric, so its index is not modelled"; `trimr` arguments 1 and 3 (`sortc`'s union return; `1000 - nf`); `indexcat` argument 1 (the column slice `wages[., 4]`); `indexcat` argument 1 "a call whose documented return type is matrix" for `loadd(…, "Female")`. The client cleared the last with a `vec(...)` wrapper that changes nothing (disclosed). After the second, it offered the user a Python script outside gauss-ai; the user chose to keep trying in GAUSS. **Run:** validation_id `511d1ac6…`; prompt verbatim (read sha256 16266b41…; keeps `wage_returns_women.xlsx`); request_id `294a1bf2-973a-4b13-8a23-39ad2d410d6c`; user "yes"; success, exit 0, "Rows for women: 496", `saved` 1; kept `output\20261116T125620Z-294a1bf2\wage_returns_women.xlsx` (36,148 bytes); `files_not_kept: ["xls.log"]`, listed in the result. The client opened the workbook with `openpyxl` (disclosed): header row of all 7 names, 496 rows, Female all 1, Region text. `tgauss.exe -b`: the same rows and header. **All seven versions run in GAUSS** and write the same 496 rows: six false gaps, seven attempts.

Pass/fail: Pass with defect recorded
Defect severity: Medium (the most common data-preparation step needed seven attempts and a no-op wrapper)
Remediation: Compute the shape of a column slice `x[., k]` (a vector) and of an element-wise comparison of one vector with a scalar (a vector); read a string column index on a dataframe as a column.

Overall Score: 3.0
Decision: Pass with defect recorded
