# Evaluation Result

Date: 2026-11-16
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`fadb44dc…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-85x`), as in 80.x-84.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-85x-data`, set with `gauss-ai config set analysis-folder`) held two CSVs in `input/`: `fred_macro.csv` (quarterly FRED series, 1960Q1-2025Q4) and `wage_returns.csv` (1,000 rows, 7 columns, one text column). The human asked each task in plain words, one at a time, and answered every run prompt themselves (four "yes", one "no"). Tasks were proposed by the recording session. The tasks ran on 2026-11-16 from 06:29 to 07:43 local (12:29-13:43 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell`/`Glob` on the data folder, the GAUSS `examples` folder and the user's profile, `WebFetch`, and one `cp` into `input/`; all disclosed in its report (§7) and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.0 (tag `v0.94.0`, commit `2bcc69f`; published to PyPI on 2026-11-16, run `43864525769`), the editable install of this checkout (`gauss-ai version` = 0.94.0).
Prompt ID: 85.4
Prompt Category: MCP Data Import and Export of v0.94.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `505d9eda…` reported `server_version: 0.94.0`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 16 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.0` (every verdict equal to the live response) and at a `git archive` of `a094a6c` (the code of `v0.93.1`), and ran all 16 snippets with `tgauss.exe -b`, each from its own new directory holding copies of the two input files. The searches and reads were not re-run.
Prompt Text:

"Plot the unemployment rate over time from fred_macro.csv and show me the chart."

Code (first validation, a titled chart, `review_required`):
```gauss
// Quarterly U.S. unemployment rate (UNRATE), 1960Q1 onward
unrate = loadd("fred_macro.csv", "UNRATE");

// The last quarter (2025Q4) has no UNRATE value; drop it
unrate = trimr(unrate, 0, 1);
print "Quarters plotted:";
print rows(unrate);

struct plotControl myPlot;
myPlot = plotGetDefaults("xy");
plotSetTitle(&myPlot, "U.S. Unemployment Rate, 1960Q1-2025Q3");
plotSetYLabel(&myPlot, "Percent");
plotSetXTicLabel(&myPlot, "YYYY");

// Start in 1960 Q1 (DT scalar 196001), quarterly frequency
plotTS(myPlot, 196001, 4, unrate);

plotSave("unemployment_rate.png", 900|500);
```

Code (final, `handoff_candidate`):
```gauss
// Quarterly U.S. unemployment rate (UNRATE), 1960Q1 onward
unrate = loadd("fred_macro.csv", "UNRATE");

// The last quarter (2025Q4) has no UNRATE value; drop it
unrate = trimr(unrate, 0, 1);
print "Quarters plotted:";
print rows(unrate);

// Start in 1960 Q1 (DT scalar 196001), quarterly frequency
plotTS(196001, 4, unrate);

plotSave("unemployment_rate.png", 900|500);
```

Captured output (live, equal to the v0.94.0 re-run): **review_required**, then **handoff_candidate** (reads `fred_macro.csv`; writes `unemployment_rate.png`).
v0.93.1 code: both **not_ready**.

Expected behavior: (plan v0.94 §7 and decision 5) a figure written by `plotSave`, kept under `output/` and returned to the client as an image.

Observed behavior: the first version's three gaps were all "parameter role unknown -- `plotSetTitle` argument 1 (parameter `&myPlot`): no documented `:type` line was matched to this parameter" (likewise `plotSetYLabel`, `plotSetXTicLabel`): the disclosed `&`-parameter gap (`KNOWN_LIMITATIONS.md`, v0.83.0). The client removed every `plotSet*` call. **Run:** validation_id `afad7281…`; prompt verbatim (reads `fred_macro.csv` 10,934 bytes, sha256 f02d7b50…; keeps `unemployment_rate.png`); request_id `58deeae9-d9ca-4ea4-9c9a-64b69bc01f45`; user "yes"; success, exit 0, "Quarters plotted: 263"; kept `output\20261116T124125Z-58deeae9\unemployment_rate.png` (31,563 bytes); `images`: one, `attached: true`, and the client described the chart from the image. `tgauss.exe -b`: byte-identical PNG. **The titled version also runs** and writes its PNG: the known gap cost the chart its title and axis label. The client's pre-checks (`head`/`tail`/`awk` on the CSV for the missing last UNRATE) used its own shell (disclosed).

Pass/fail: Pass with limitation disclosed
Defect severity: Low (known limitation; its cost is now visible on every styled plot)
Remediation: Match a `&`-prefixed parameter's documented type narrowly enough that a literal cannot pass as a function pointer (for example: accept `&name` where `name` is a declared `plotControl` structure).

Overall Score: 3.4
Decision: Pass with limitation disclosed
