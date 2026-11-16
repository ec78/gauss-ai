# Evaluation Result

Date: 2026-11-16
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`fadb44dc…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-85x`), as in 80.x-84.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-85x-data`, set with `gauss-ai config set analysis-folder`) held two CSVs in `input/`: `fred_macro.csv` (quarterly FRED series, 1960Q1-2025Q4) and `wage_returns.csv` (1,000 rows, 7 columns, one text column). The human asked each task in plain words, one at a time, and answered every run prompt themselves (four "yes", one "no"). Tasks were proposed by the recording session. The tasks ran on 2026-11-16 from 06:29 to 07:43 local (12:29-13:43 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell`/`Glob` on the data folder, the GAUSS `examples` folder and the user's profile, `WebFetch`, and one `cp` into `input/`; all disclosed in its report (§7) and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.0 (tag `v0.94.0`, commit `2bcc69f`; published to PyPI on 2026-11-16, run `43864525769`), the editable install of this checkout (`gauss-ai version` = 0.94.0).
Prompt ID: 85.2
Prompt Category: MCP Data Import and Export of v0.94.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `505d9eda…` reported `server_version: 0.94.0`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 16 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.0` (every verdict equal to the live response) and at a `git archive` of `a094a6c` (the code of `v0.93.1`), and ran all 16 snippets with `tgauss.exe -b`, each from its own new directory holding copies of the two input files. The searches and reads were not re-run.
Prompt Text:

"Load wage_returns.csv and give me summary statistics for each column."

Code (first validation, `review_required`):
```gauss
// Load all columns; treat Region as a categorical variable
df = loadd("wage_returns.csv", "Wage + Education + Experience + Female + Union + cat(Region) + LogWage");

print "Rows, columns:";
print rows(df)~cols(df);

// Summary statistics for every column
call dstatmt(df);
```

Code (final, `handoff_candidate`):
```gauss
// Summary statistics for every column of wage_returns.csv
// Region is treated as a categorical variable
call dstatmt("wage_returns.csv", "Wage + Education + Experience + Female + Union + cat(Region) + LogWage");
```

Captured output (live, equal to the v0.94.0 re-run): first **review_required**, final **handoff_candidate** (`file_accesses`: `dstatmt` reads `wage_returns.csv` from `input`).
v0.93.1 code: both **not_ready** (`loadd` / `dstatmt` read a file).

Expected behavior: (plan v0.94 §7) load the file and summarize it; with the folder, a candidate whose prompt lists the input with its digest.

Observed behavior: the first version's only gap: "`dstatmt` argument 1 (parameter `data`): the argument (traced to `df = ...`, a call whose documented return type is matrix) may not fit the documented type for parameter 'data' (string/dataset)" (`return_type_imprecise`). The client passed the file name to `dstatmt` instead (documented: "A dataframe or the name of dataset"). **Run:** validation_id `d9eddde1…`; prompt shown verbatim with "Reads (copied from …\input; the originals are not changed): wage_returns.csv (51,768 bytes, sha256 16266b418302b125...)"; request_id `be32998b-e1ff-45ee-b533-e9b59f3b2a30`; user "yes"; success, exit 0, the `dstatmt` table (1,000 valid, 0 missing; Region a category, Midwest-West); no files written. `tgauss.exe -b`: the same table for both versions. **The first version was a false gap:** `loadd` returns a table with column names, which `dstatmt` accepts, but `loadd.rst` types its return `NxK matrix`, which the role check cannot tell from a plain matrix. (Not a docs error: GAUSS's `type` gives 6, matrix, for `loadd`'s result with or without a text column, sp941f; a dataframe is a matrix with column metadata.) The gap text also calls a documented "dataframe" a "dataset", which the client found confusing (report §9.3). `cat(Region)` came from the client's own knowledge (the search left "cat" ambiguous).

Pass/fail: Pass
Defect severity: Low (a false gap from `loadd.rst`'s `:rtype`; wording)
Remediation: Say "dataframe" in reason text where the docs say dataframe (done in v0.94.1). Telling a loaded table from a plain matrix would need the file's header: a later candidate.

Overall Score: 3.8
Decision: Pass
