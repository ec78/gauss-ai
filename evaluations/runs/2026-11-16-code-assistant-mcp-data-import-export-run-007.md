# Evaluation Result

Date: 2026-11-16
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`fadb44dc…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-85x`), as in 80.x-84.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The analysis folder (`C:\Users\Owner\Documents\gauss-ai-85x-data`, set with `gauss-ai config set analysis-folder`) held two CSVs in `input/`: `fred_macro.csv` (quarterly FRED series, 1960Q1-2025Q4) and `wage_returns.csv` (1,000 rows, 7 columns, one text column). The human asked each task in plain words, one at a time, and answered every run prompt themselves (four "yes", one "no"). Tasks were proposed by the recording session. The tasks ran on 2026-11-16 from 06:29 to 07:43 local (12:29-13:43 UTC); the client's report was requested only after the last task. Besides gauss-ai tools the client used `Bash`/`PowerShell`/`Glob` on the data folder, the GAUSS `examples` folder and the user's profile, `WebFetch`, and one `cp` into `input/`; all disclosed in its report (§7) and confirmed against the transcript. It read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.94.0 (tag `v0.94.0`, commit `2bcc69f`; published to PyPI on 2026-11-16, run `43864525769`), the editable install of this checkout (`gauss-ai version` = 0.94.0).
Prompt ID: 85.7
Prompt Category: MCP Data Import and Export of v0.94.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.94.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss, `analysis_folder` as above. Server session `505d9eda…` reported `server_version: 0.94.0`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 16 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation and the same analysis folder at `v0.94.0` (every verdict equal to the live response) and at a `git archive` of `a094a6c` (the code of `v0.93.1`), and ran all 16 snippets with `tgauss.exe -b`, each from its own new directory holding copies of the two input files. The searches and reads were not re-run.
Prompt Text:

"Load the beef prices example dataset that ships with GAUSS and tell me its average price"

Code (first validation, `not_ready`):
```gauss
// Average beef price from the GAUSS example dataset
price = loadd(getGAUSSHome("examples/beef_prices.csv"), "beef_price");
print "Observations:";
print rows(price);
print "Average beef price:";
print meanc(price);
```

Code (final, `handoff_candidate`):
```gauss
// Average beef price from the GAUSS example dataset
price = loadd(getGAUSSHome() $+ "examples/beef_prices.csv", "beef_price");
print "Observations:";
print rows(price);
print "Average beef price:";
print meanc(price);
```

Captured output (live, equal to the v0.94.0 re-run): **not_ready** ("getGAUSSHome: documented form(s) accept 0 argument(s); this call passed 1"), then **handoff_candidate** (`file_accesses`: `loadd` reads `examples/beef_prices.csv`, location `gauss_examples`, path `C:\gauss26\examples\beef_prices.csv`).
v0.93.1 code: both **not_ready** (`loadd` reads a file).

Expected behavior: (plan v0.94 decision 2, deviation 5) GAUSS example data read in place; the one-argument `getGAUSSHome("…")` stays a signature issue until aptech/docs#7 is fixed. (plan v0.94 §7) one run the user declines; nothing is copied or kept.

Observed behavior: as expected. The client fixed the call from the issue text alone. **Run:** validation_id `630ea2e1…`; prompt verbatim with "Reads in place (GAUSS example data, not changed): C:\gauss26\examples\beef_prices.csv (4,189 bytes, sha256 f8418b7f364e10f2...)" and no "Keeps" line; request_id `010aa17b-c3b8-4c03-a632-56ae7c9d3094`; user "no"; `outcome: "declined"`, "No code was executed." No output folder was created (the `output/` listing after the session holds only 85.3, 85.4 and 85.6's folders). `tgauss.exe -b` (recording session): 285 observations, mean 122.6594, for both versions. **Wording finding:** the server instructions say "Paths, URLs and names built at run time are never allowed", yet `getGAUSSHome() $+ "examples/…"` is allowed by design; the client flagged the contradiction (report §9.1). **Client misstatement:** it told the user "I declined the run"; the user declined.

Pass/fail: Pass
Defect severity: Low (server-instruction wording)
Remediation: Reword the instructions: names built at run time are refused, except GAUSS's example data through `getGAUSSHome() $+ "examples/…"`.

Overall Score: 3.8
Decision: Pass
