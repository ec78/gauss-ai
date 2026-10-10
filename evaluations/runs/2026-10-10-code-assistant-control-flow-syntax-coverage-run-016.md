# Evaluation Result

Date: 2026-10-10
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation; the human asked each task in plain words, one at a time, with no steering toward a code shape. The session did not read the planning doc or PROJECT_STATUS.md until all sixteen tasks were done.
Agent Version: v0.82.0 (uncommitted on top of c126524), `gauss-ai-mcp` reinstalled with v0.82.0 before the conversation
Prompt ID: 72.16
Prompt Category: Bounded Control-Flow Syntax Coverage (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.82.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, but the server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session e1fef0c4db0a4ae2b6a0bcc2c55d4f8f. The client model wrote every snippet itself, uncoaxed.
Prompt Text:

"Look up how to compute a covariance matrix in GAUSS."

Captured output (abridged, verbatim fields):
```
Live (client's own query, which already named the functions):
search_docs("vcx vcm covariance matrix") -> "partially_grounded"; vcx, vcm (vcmvcx.rst, clean Syntax line
                 "vc = vcm(m [, ddof]); vc = vcx(x [, ddof])"); unmatched ["covariance"];
                 ambiguous ["vcx vcm covariance matrix"]

Supplementary (run by the recording session after the tasks, to answer PROJECT_STATUS's re-check request; the
lookup is deterministic, so the result does not depend on which session sends it):
search_docs("compute a covariance matrix") -> "ungrounded"; sources []; unmatched ["covariance"]
```

Expected behavior: A documentation lookup, no code. The 71.5 garbled `vcmvcx.rst` Syntax line should be clean (§3.6 fix). PROJECT_STATUS asked for an unsteered re-check of the preliminary observation that the plain query returns ungrounded with no sources (search-side grounding is out of v0.82.0 scope).

Observed behavior: The Syntax line is clean (71.5 fix confirmed live). The client answered correctly from the docs (`vcx`, `vcm`, the `ddof` divisor, the constant-first requirement for `vcm`). But the client's live query was **steered by its own prior knowledge**: it put `vcx vcm` in the query, which is what made the search find the page. The plain-language query returns **ungrounded with no sources at all**, so a client without that prior knowledge would get nothing. The preliminary observation is reproduced: a real, if out-of-scope, weakness of `gauss_search_docs` for plain questions. It is worse than 71.5, where the similar query at least returned the page.

Pass/fail: Pass with limitation (answer correct; search fails on the plain question)
Defect severity: Minor (search-side grounding; validation unaffected; disclosed as out of scope)
Remediation: Disclosed in KNOWN_LIMITATIONS. Candidate for a later milestone: concept-to-function resolution in `gauss_search_docs` (the `resolve_concepts` index the `ask()` path already has).

Overall Score: 3.0
Decision: Pass with limitation disclosed
