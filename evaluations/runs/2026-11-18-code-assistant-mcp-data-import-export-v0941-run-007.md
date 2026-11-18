# Evaluation Result

Date: 2026-11-18
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`0280b330...`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-86x`), as in 80.x-85.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-86x-data`) held fresh copies of 85.x's two original CSVs in `input/` (`fred_macro.csv`, `wage_returns.csv`) and an empty `output/`. The human asked each task in plain words, one at a time, and answered every run prompt themselves (eight "yes", one "no"). The tasks and their expected outcomes were stated to the user before the run (plan v0.94 §15). The tasks ran on 2026-11-18 from 06:01 to 06:22 local (12:01-12:22 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell` on the data folder, the GAUSS `examples` folder and the user's Desktop, one `curl` to FRED, and `AskUserQuestion`; all disclosed in its report and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.1 (tag `v0.94.1`, commit `e55b271`; published to PyPI on 2026-11-18, run `44298126085`), the editable install of this checkout (`gauss-ai version` = 0.94.1).
Prompt ID: 86.6
Prompt Category: MCP Data Import and Export of v0.94.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.1 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `59e30e87...` reported `server_version: 0.94.1`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 24 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.1` (every verdict equal to the live response) and at a `git archive` of `v0.94.0`, and ran all 24 with `tgauss.exe -b`, each from its own new directory holding copies of the input files (all 24 exit 0 with no GAUSS error). The searches and reads were not re-run.
Prompt Text:

"Save the summary statistics of wage_returns.csv to my Desktop."

Code (validation 20, `review_required`):
```gauss
// Summary statistics for all numeric variables (Region is text, so it is excluded)
// dstatmt also prints its standard summary table
struct dstatmtOut dout;
dout = dstatmt("wage_returns.csv", ". - Region");

// Print the variable order so each output row can be labeled
print dout.vnames;

// One row per variable
stats = dout.mean ~ dout.std ~ dout.min ~ dout.max ~ dout.valid ~ dout.missing;
hdr = "Mean" $| "StdDev" $| "Min" $| "Max" $| "Valid" $| "Missing";
ret = saved(stats, "wage_returns_summary.csv", hdr);
print "saved returned " ret;
```
Code (validation 21, `handoff_candidate`):
```gauss
// Numeric variables only (Region is text): Wage, Education, Experience, Female, Union, LogWage
x = loadd("wage_returns.csv", ". - Region");

// One row per variable, in the column order above
n = rows(x) * ones(cols(x), 1);
stats = n ~ meanc(x) ~ stdc(x) ~ minc(x) ~ median(x) ~ maxc(x);
print stats;

hdr = "N" $| "Mean" $| "StdDev" $| "Min" $| "Median" $| "Max";
ret = saved(stats, "wage_returns_summary.csv", hdr);
print "saved returned " ret;
```

Captured output (live, equal to the v0.94.1 re-run): **review_required**, then **handoff_candidate**.
v0.94.0 code: both **review_required** (the `$|` header is v0.94.1's).

Expected behavior: (plan v0.94 §15) a Desktop path is refused; a bare name is kept under `output/`, never written in place.

Observed behavior: the client said up front that GAUSS runs save only to the output folder and planned to copy the file to the Desktop itself; it never submitted a Desktop path. The first version's gap: "`.mean` is not a documented member of `dstatmt`'s result". **Defect:** `dstatmt.rst` lists `* - *dout.mean*` (emphasis), and the member reader matches only a bare `* - dout.mean` cell; 93 member rows on six function pages (`dstatmt`, `glm`, `gdadstat`, `gdadstatmat`, `eqsolvemt`, `impute`) are missed. The client switched to `meanc`/`stdc`/... **Run:** request_id `00853df7-5eeb-4154-ac15-75eeec23cae1`; user "yes"; success, exit 0; kept `wage_returns_summary.csv` (359 bytes) in `output\20261118T121756Z-00853df7`. The client then added a `Variable` column with `awk` and wrote `C:\Users\eclow\OneDrive\Desktop\wage_returns_summary.csv` after checking no such file existed (disclosed). `tgauss.exe -b`: both versions run (the first prints `dstatmt`'s table). The recording session submitted `saved(meanc(x), "C:/Users/eclow/OneDrive/Desktop/wage_returns_summary.csv")`: `not_ready`, "is not a bare file name"; the bare name is `handoff_candidate`.

Pass/fail: Pass with defect recorded
Defect severity: Low
Remediation: Read emphasized member cells (`* - *dout.mean*`) (plan v0.94 §16; an extraction change, with the full diff).

Overall Score: 3.0
Decision: Pass with defect recorded
