# Evaluation Result

Date: 2026-10-16
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. All twenty-one tasks ran on 2026-10-16 in one server session. The session did not read the planning doc, PROJECT_STATUS.md or any source until all tasks were done.
Agent Version: v0.85.0 (released; tag `v0.85.0`, commit `f11505e`; HEAD `d634b40`, whose `scripts/` is identical to the tag), editable install of this checkout (`pip show gauss-ai` = 0.85.0). The live server's own output carries v0.85.0-only behavior (`library` -> `source_inclusion` in 75.3/75.6; a typed `struct` procedure header is no longer INVALID in 75.2; `miss` keeps its signature in 75.4).
Prompt ID: 75.13
Prompt Category: Procedure Headers and Defining Pages (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.85.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session d965dee780a44d0e8faacbdafbd0eaad. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.85.0 and v0.84.0 (`d19c61c`); every live verdict reproduced exactly on the v0.85.0 archive. Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) programs run by the recording session from a scratch directory, including the client's own programs. No `gauss_execution_prepare` call was made.
Prompt Text:

"How do I compute the 95th percentile of each column?"

Searches:
```
search_docs("quantile percentile of each column") -> partially_grounded on quantile (the client named it from prior
    knowledge); unmatched percentile, each
```
The user's literal wording (recording-session re-run) still grounds **full** on `setColDateFormats.rst`, on v0.84.0
and v0.85.0 alike: the known false full grounding (v0.86 draft finding 1), reproduced with "each column".

Code: `p95 = quantile(x, 0.95);` on a `rndn(1000, 4)` matrix.

Captured output: **handoff_candidate**. v0.84.0: identical. The client also noted that the `quantile` page's example
labels the .025/.975 rows "95 percentiles" (they bound a central 95% interval).

Pass/fail: Pass with limitation disclosed
Defect severity: Minor (known search issues; the client's query was steered by prior knowledge)
Remediation: Search/grounding milestone (v0.86 draft findings 1-2).

Overall Score: 3.6
Decision: Pass with limitation disclosed
