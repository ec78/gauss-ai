# Evaluation Result

Date: 2026-11-18
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`0280b330...`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-86x`), as in 80.x-85.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-86x-data`) held fresh copies of 85.x's two original CSVs in `input/` (`fred_macro.csv`, `wage_returns.csv`) and an empty `output/`. The human asked each task in plain words, one at a time, and answered every run prompt themselves (eight "yes", one "no"). The tasks and their expected outcomes were stated to the user before the run (plan v0.94 §15). The tasks ran on 2026-11-18 from 06:01 to 06:22 local (12:01-12:22 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell` on the data folder, the GAUSS `examples` folder and the user's Desktop, one `curl` to FRED, and `AskUserQuestion`; all disclosed in its report and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.1 (tag `v0.94.1`, commit `e55b271`; published to PyPI on 2026-11-18, run `44298126085`), the editable install of this checkout (`gauss-ai version` = 0.94.1).
Prompt ID: 86.3
Prompt Category: MCP Data Import and Export of v0.94.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.1 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `59e30e87...` reported `server_version: 0.94.1`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 24 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.1` (every verdict equal to the live response) and at a `git archive` of `v0.94.0`, and ran all 24 with `tgauss.exe -b`, each from its own new directory holding copies of the input files (all 24 exit 0 with no GAUSS error). The searches and reads were not re-run.
Prompt Text:

"Plot the unemployment rate over time from fred_macro.csv with a title and axis labels, and save the chart."

Code (validation 8, `review_required`):
```gauss
// Load the date and unemployment rate columns
macro = loadd("fred_macro.csv", "date(date) + UNRATE");

// Set up the plot
struct plotControl plt;
plt = plotGetDefaults("xy");
plotSetTitle(&plt, "U.S. Unemployment Rate, 1960-2025");
plotSetXLabel(&plt, "Date");
plotSetYLabel(&plt, "Unemployment rate (%)");

// Line plot of UNRATE over time
plotXY(plt, macro, "UNRATE ~ date");

// Save as a PNG, 900 x 500 pixels
plotSave("unemployment_rate.png", 900 | 500);
```
Code (validation 9, `handoff_candidate`):
```gauss
// Load the unemployment rate (quarterly, starting 1960 Q1)
unrate = loadd("fred_macro.csv", "UNRATE");

// Set up the plot
struct plotControl plt;
plt = plotGetDefaults("xy");
plotSetTitle(&plt, "U.S. Unemployment Rate, 1960-2025");
plotSetXLabel(&plt, "Year");
plotSetYLabel(&plt, "Unemployment rate (%)");

// Quarterly time series plot starting January 1960
plotTS(plt, 196001, 4, unrate);

// Save as a PNG, 900 x 500 pixels
plotSave("unemployment_rate.png", 900 | 500);
```

Captured output (live, equal to the v0.94.1 re-run): **review_required**, then **handoff_candidate**.
v0.94.0 code: both **review_required** (the `&plt` match is v0.94.1's).

Expected behavior: (plan v0.94 §15) the structure pointer validates and runs; the PNG is kept; the image may not appear in chat.

Observed behavior: as expected. All three `&plt` arguments matched in both versions; the first version's only gap was `plotXY` argument 2 traced to `loadd`'s `matrix` against `dataframe` (`return_type_imprecise`), so the client switched to `plotTS` with a start date it checked against the CSV. **Run:** request_id `d28b7666-5af5-48ed-a344-17e927dafe91`; user "yes"; success, exit 0; kept `unemployment_rate.png` (30,887 bytes) in `output\20261118T120550Z-d28b7666`; the figure was returned as an image and the client inspected it (it noticed the 2020 value is a first-month value). The user then asked to see the chart; the client opened the PNG with `Start-Process` and linked it. `tgauss.exe -b`: both versions run and write the PNG.

Pass/fail: Pass
Defect severity: Low
Remediation: None new.

Overall Score: 3.7
Decision: Pass
