# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`8ab50628…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-82x`), as in 80.x and 81.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes", one "no") and one of the client's own numbered options ("1"). Tasks 82.1-82.9 were proposed by the recording session; 82.10-82.14 were the user's own. All tasks ran on 2026-11-06, 06:34-06:53 local (11:34-11:53 UTC). The client used gauss-ai tools plus five PowerShell commands that checked paths, listed folders and read executable version numbers (82.9, 82.12, 82.14); it read no file's contents, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.91.0 (tag `v0.91.0`, commit `5b07a28`; published to PyPI on 2026-11-06, run `42206846915`), the editable install of this checkout (`gauss-ai version` = 0.91.0).
Prompt ID: 82.11
Prompt Category: MCP Expression Categories of v0.91.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.91.0 over stdio, registered at local scope for the folder under both drive-letter spellings (`C:/…` and `c:/…`) with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session (`f7274c39…`) served every task; `gauss_session_start` reported `server_version: 0.91.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 37 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.91.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.90.0` (`1ee121c`), diagnosed each non-candidate verdict with `validate_code(...)` directly, re-ran all five approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory, and ran every other non-blocked snippet the same way.
Prompt Text:

"What GAUSS procedures are available for estimating and GMM model?"

Two searches: "generalized method of moments GMM estimation procedure" and "gmmFit gmmFitIV gmmControlCreate" (both grounded on `gmmfit.rst`; the second also `gmmfitiv.rst`). Every search and read response equals the v0.91.0 and v0.90.0 re-runs.

Expected behavior: (the user's own task) an accurate, grounded answer.

Observed behavior: accurate. The client listed `gmmFit`, `gmmFitIV` and `gmmControlCreate` with their documented forms, and pointed out that the two pages name the output members differently (`gmmFit.rst`: `gOut.parEst`, `gOut.numParms`; `gmmfitiv.rst`: `gOut.paramEst`, `gOut.numParams`), saying it could not tell which is right. **GAUSS 26.1.4 rejects `parEst` and `numParms`** (`G0504`: Invalid structure member) and accepts `paramEst` and `numParams` (recording-session spot checks gm01-gm04). So `gmmfit.rst` is wrong: a documentation error for Aptech (plan §12, finding 5).

Pass/fail: Pass
Defect severity: None (documentation error upstream)
Remediation: Report `gmmfit.rst`'s member names to Aptech.

Overall Score: 4.0
Decision: Pass
