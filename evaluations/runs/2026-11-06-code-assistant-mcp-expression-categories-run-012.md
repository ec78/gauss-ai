# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`8ab50628…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-82x`), as in 80.x and 81.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes", one "no") and one of the client's own numbered options ("1"). Tasks 82.1-82.9 were proposed by the recording session; 82.10-82.14 were the user's own. All tasks ran on 2026-11-06, 06:34-06:53 local (11:34-11:53 UTC). The client used gauss-ai tools plus five PowerShell commands that checked paths, listed folders and read executable version numbers (82.9, 82.12, 82.14); it read no file's contents, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.91.0 (tag `v0.91.0`, commit `5b07a28`; published to PyPI on 2026-11-06, run `42206846915`), the editable install of this checkout (`gauss-ai version` = 0.91.0).
Prompt ID: 82.12
Prompt Category: MCP Expression Categories of v0.91.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.91.0 over stdio, registered at local scope for the folder under both drive-letter spellings (`C:/…` and `c:/…`) with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session (`f7274c39…`) served every task; `gauss_session_start` reported `server_version: 0.91.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 37 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.91.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.90.0` (`1ee121c`), diagnosed each non-candidate verdict with `validate_code(...)` directly, re-ran all five approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory, and ran every other non-blocked snippet the same way.
Prompt Text:

"Does GAUSS have any pre-built machine learning models that I can use? If so what models are supported?"

Five searches (machine learning / random forest; lasso, ridge, k-means …; `lassoFit ridgeFit kmeansFit knnFit pcaFit`; `trainTestSplit classificationMetrics cvSplit predict`; `pcaFit pcaTransform`), and one PowerShell `Test-Path "C:\gauss26\pkgs\gml"` (True). The plain-words query was ungrounded (`machine`, `learning`, `forest`, `decision`, `tree` unmatched); the name queries grounded.

Expected behavior: (the user's own task) an accurate, grounded answer.

Observed behavior: accurate as far as checked, with one exception found later (correction, 2026-11-06, planning v0.92 §9.5): the client said `trainTestSplit` "also accepts a file name and formula", but `traintestsplit.rst` documents only `trainTestSplit(y, X, train_pct [, shuffle])` and mentions no file. Otherwise: the listed functions exist in the docs, and the client said that `decForestRFit`, `decForestCFit` and `plotVariableImportance` appeared only as candidate names, without their argument details. It used the shell to confirm GML is installed, which gauss-ai cannot do (v0.92.0 "Installed Libraries" would). The plain-words query's failure to ground is the known prose-recall limit (v0.88.0).

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 3.6
Decision: Pass
