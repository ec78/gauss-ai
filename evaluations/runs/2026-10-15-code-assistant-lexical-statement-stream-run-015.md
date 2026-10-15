# Evaluation Result

Date: 2026-10-15
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.15
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 352fc674f22b467fae1e3113c26898e9. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"How do I compute the 95th percentile of a column?"

Searches (the client dropped "How do I" from the user's sentence):
```
search_docs("95th percentile of a column") -> "ungrounded"; unmatched ["percentile"]; 8 candidates, every one a
    keyword match on "column" only (asDate, cols, colsf, cumprodc, cumsumc, delcols, dfaddcol, dfname); truncated
search_docs("percentile") -> "ungrounded"; candidates box, plotBox ("box graph percentile method")
search_docs("quantile")   -> "grounded"; quantile.rst (prior knowledge)
```

Recording-session probe with the user's exact sentence: `search_docs("How do I compute the 95th percentile of a
column?")` -> **`grounded` on `setColDateFormats`** (setcoldateformats.rst). This is the known false full grounding
(v0.84.0 plan §2.5, `KNOWN_LIMITATIONS.md`), still present; the client happened to avoid it by trimming its query.

Attempt 1:
```gauss
// Reproducible example data: 1000 observations, 3 columns
rndseed 345567;
x = rndn(1000, 3);

// 95th percentile of column 2 only
p95_col2 = quantile(x[., 2], 0.95);
print "95th percentile of column 2 = " p95_col2;

// 95th percentile of every column at once (returns a 1x3 row)
p95_all = quantile(x, 0.95);
print "95th percentile of each column = " p95_all;
```
Attempt 2 (the client's diagnostic): `col2 = x[., 2];` then `quantile(col2, 0.95)`.

Captured output:
```
attempt 1 -> "review_required"; coverage_gaps: parameter_role/quantile/1/x/argument_expression ("`x[., 2]` is an expression")
attempt 2 -> "review_required"; coverage_gaps: parameter_role/quantile/1/x/argument_assigned_from_expression
             ("`col2` is assigned from an expression (`x[., 2]`), which is never evaluated")
```

Diagnosis (direct `validate_code`): `quantile` arg 0 role `unknown` in both; the whole-matrix call `quantile(x, 0.95)`
matches (traced to `rndn`'s documented return type). **The `coverage_gaps` the client saw agree with the direct
diagnosis.** Same verdicts on v0.83.0.

Expected behavior: `quantile` code; a column slice is an expression, so review_required with that cause named. No false not_ready.

Observed behavior: Verdict as expected. The client's diagnostic showed that routing the slice through a temporary variable does **not** launder the unknown: the tracer follows `col2` back to `x[., 2]`. That is the right behavior, and the client presented the natural code rather than a workaround. **Search: the known 73.13 recall gap reproduces** ("percentile" never reaches `quantile`), and the known `setColDateFormats` false full grounding is still live for the user's own wording.

Pass/fail: Pass with limitation disclosed
Defect severity: Minor (deferred expression inference; known search recall gap and known false grounding)
Remediation: None new; both search findings are already recorded for the search/grounding milestone.

Overall Score: 3.2
Decision: Pass with limitation disclosed
