# Evaluation Result

Date: 2026-10-12
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. The session did not read the planning doc or PROJECT_STATUS.md until all fifteen tasks were done. (It did read validator source during 73.10 and 73.14, to locate the defects it had just observed.)
Agent Version: v0.83.0 (released; tag `v0.83.0`, commit `2740519`; HEAD `a6f2b80`), editable install of this checkout
Prompt ID: 73.2
Prompt Category: Verdict Explanations and Search Recall (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.83.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). No session (search only). The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs.
Prompt Text:

"Look up how to compute a covariance matrix in GAUSS."

Captured output (abridged, verbatim fields):
```
search_docs("compute a covariance matrix") -> "ungrounded"; sources []; unmatched ["covariance"];
    candidates (keyword_match): robustSE, varCovMS/varCovXS, varCovM/varCovX, vcms/vcxs, vcm/vcx,
    ssKalmanSmooth, rndMVn, rndMVt; candidates_truncated true; candidate_note present
search_docs("varCovXS varCovMS") -> "grounded"; varcovmsvarcovxs.rst
search_docs("varCovX varCovM")   -> "grounded"; varcovmvarcovx.rst
search_docs("vcx vcm")           -> "grounded"; vcmvcx.rst (clean Syntax line, ddof documented)
```

Supplementary (recording session): the derived concept index does carry `covariance` for `vcx` (keywords `vcm, vcx, estimate, variance, covariance`); the plain query matches it on one keyword, below `MIN_KEYWORD_OVERLAP` = 2, so it is a mode-B candidate by design (planning §2.4, §3.4).

Expected behavior: The 72.16 query, re-asked unsteered. Grounding status stays `ungrounded` (the gate is unchanged by design); v0.83.0's F4 adds labeled candidates, with `vcmvcx.rst` among them, and the client follows a candidate to a grounded page.

Observed behavior: F4 confirmed live: the plain query returned eight labeled candidates with the four `vc*`/`varCov*` pages near the top. **The client followed three candidates back to grounded pages** and answered correctly from them (`vcx` with `ddof`, the `varCovXS`/`varCovX` N-1/N split, the constant-first requirement for the moment-matrix forms). Unlike 72.16, the client's first query was the plain question, not a function name. **Client explanation error:** it said the concept index has nothing mapping "covariance" to `vcx`. In fact the derived index has that keyword; one keyword is below the resolution threshold, by design.

Pass/fail: Pass
Defect severity: Minor (client misdescribed why the query was ungrounded)
Remediation: None needed for the verdict. The client's explanation is corrected here.

Overall Score: 3.8
Decision: Pass
