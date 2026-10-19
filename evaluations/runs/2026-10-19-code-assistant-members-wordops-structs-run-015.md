# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.15
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Identify outliers in a column of data using the IQR rule, and remove them." (second half of 76.14's message)

Searches:
```
search_docs("quantile") -> grounded: quantile.rst ("tp … Sample quantile type. Default is 4.")
```
`delif` was not searched; the validator grounded it on `delif.rst`.

Code (S15): a 14-value column with two outliers; `q = quantile(x, {0.25, 0.75})`, Tukey fences `q1 - 1.5*iqr`,
`q3 + 1.5*iqr`; `isOut = (x .< lo) .or (x .> hi); outliers = selif(x, isOut); clean = delif(x, isOut);`

The client disclosed that GAUSS's default quantile type is 4, not R's 7, and how to pass a type.

Captured output: `review_required`; gaps: `selif` and `delif` arg 2 `argument_assigned_from_expression` (`isOut`).

Diagnosis (direct `validate_code`): identical; `quantile`, `selif` and `delif` arg 1 are `traced_literal` matches.
**The gaps agree.**

v0.85.0, same snippet: **not_ready** (`or` unknown). v0.86.0 finding 2 confirmed live on the 75.19 task shape.

Real GAUSS (S15 verbatim): `Q1 13, Q3 15, IQR 2`, fences `10 18`, outliers `48 -10`, 12 values kept, as the client
computed. Spot check e06: types 4 and 7 give the same quartiles for this data.

Expected behavior: review_required; correct program.

Observed behavior: As expected.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
