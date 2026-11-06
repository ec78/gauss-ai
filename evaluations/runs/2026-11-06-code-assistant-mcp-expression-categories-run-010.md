# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`8ab50628…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-82x`), as in 80.x and 81.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes", one "no") and one of the client's own numbered options ("1"). Tasks 82.1-82.9 were proposed by the recording session; 82.10-82.14 were the user's own. All tasks ran on 2026-11-06, 06:34-06:53 local (11:34-11:53 UTC). The client used gauss-ai tools plus five PowerShell commands that checked paths, listed folders and read executable version numbers (82.9, 82.12, 82.14); it read no file's contents, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.91.0 (tag `v0.91.0`, commit `5b07a28`; published to PyPI on 2026-11-06, run `42206846915`), the editable install of this checkout (`gauss-ai version` = 0.91.0).
Prompt ID: 82.10
Prompt Category: MCP Expression Categories of v0.91.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.91.0 over stdio, registered at local scope for the folder under both drive-letter spellings (`C:/…` and `c:/…`) with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session (`f7274c39…`) served every task; `gauss_session_start` reported `server_version: 0.91.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 37 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.91.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.90.0` (`1ee121c`), diagnosed each non-candidate verdict with `validate_code(...)` directly, re-ran all five approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory, and ran every other non-blocked snippet the same way.
Prompt Text:

"Generate two series of random normal data with 150 observations and create a scatter plot of the data using default formatting. Save the plot and display it here."

The client searched `plotScatter plotSave` (grounded).

Code (c20):
```gauss
// Reproducible draws
rndseed 20261106;

// Two series of 150 standard-normal observations
x = rndn(150, 1);
y = rndn(150, 1);

// Scatter plot with default formatting
plotScatter(x, y);

// Save as a 640x480 pixel PNG
plotSave("C:/Users/Owner/AppData/Local/Temp/claude/04e4e9b5beb787a0/8ab50628-8c5e-43ae-b771-63264529b4ae/scratchpad/scatter.png", 640 | 480);
```
Captured output (live, identical on the v0.91.0 re-run): **not_ready**.
Reasons beyond the standard ones: "line 12: `plotsave` is a system-touching statement (file_write) -- controlled execution only runs self-contained snippets that compute in memory"
v0.90.0: identical.

The client said the run path cannot draw or save a plot (`plotSave` writes a file, the run directory is deleted, and `tgauss.exe` may not draw plots), and gave the code to run in the GAUSS desktop app.

Expected behavior: (the user's own task) `plotSave` is a file write and is `not_ready`.

Observed behavior: as expected; the reason names line 12's `plotsave` (`file_write`). v0.90.0: the same verdict. Plots remain invisible through gauss-ai (81.x finding 3; the analysis-workspace milestone).

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
