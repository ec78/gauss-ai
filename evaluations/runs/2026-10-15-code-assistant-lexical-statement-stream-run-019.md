# Evaluation Result

Date: 2026-10-15
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.19
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 352fc674f22b467fae1e3113c26898e9. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"What GAUSS functions are available to help with basic data cleaning?"

Searches:
```
search_docs("data cleaning missing values") -> partially_grounded on datalist.rst through the bare token "data"
    (irrelevant); unmatched cleaning/missing/values
search_docs("packr ismiss missrv miss"), ("selif delif unique delrows"), ("strtrim strreplace counts") -> grounded
    (prior knowledge)
```
In the first steered result, the source labelled topic `miss`, citation `missmissrv.rst`, carried the **text of
ismiss.rst**.

Code (abridged):
```gauss
x = {  1    2    3,
       4    .    6,
       7 -999    9,
       4    .    6,
     150   11   12 };
x = miss(x, -999);
print "any missing? " ismiss(x);
x_complete = packr(x);
x_filled = missrv(x, 0);
x_trim = delif(x_filled, x_filled[., 1] .> 100);
print unique(x_trim[., 1]);
```

Captured output: `review_required`; coverage_gaps: **signature/miss/signature_not_extracted**;
**parameter_role ismiss/packr/missrv arg 1: return_type_undocumented** ("`x` is assigned from `miss(x, -999)`, whose
documentation gives no checkable return type"); delif arg 2 and unique arg 1: argument_expression.

Diagnosis (direct `validate_code` plus `command_doc_lookup`): `command_doc_lookup.lookup("miss", ...)` ranks
**ismiss.rst first** (then missmissrv.rst, plotsetmissgap.rst, missex.rst ...). `extract_documented_signature("miss",
best_match)` then searches ismiss's syntax block (`x_ismiss = ismiss(x)`), finds no `miss(` call, and returns
`extraction_status unknown` with no return categories. missmissrv.rst itself documents `y = miss(x, v)` and
`:rtype y: max(N,L) by max(K,M) matrix`, which `classify_documented_type` reads as `matrix`. So one wrong top match
causes the signature gap, the three return-type gaps, and the mismatched search excerpt. **The gaps the client saw
agree with what the validator did, but two of their causes are false about the docs.** Same on v0.83.0.

Expected behavior: A correct answer from grounded pages. Partial verdicts name true causes.

Observed behavior: Answer correct (`ismiss`, `miss`, `missrv`, `packr`, `selif`, `delif`, `delrows`, `unique`, `counts`, `strtrim`, `strreplace`). **Real defect found live:** the docs lookup for `miss` returns the wrong page (`ismiss.rst`, a substring match outranks the page that documents `miss`). That makes a documented function's signature "unknown", hides its documented return type from three downstream role checks, and labels a search excerpt with the wrong page. It showed only in the conservative direction here. Whether a wrong top match can ever make an argument check pass against the wrong page was not established. The plain-language question grounded on the irrelevant `datalist` page.

Pass/fail: Fail
Defect severity: Moderate (wrong page used as evidence for a documented symbol; conservative here; search recall)
Remediation: Next milestone (planning v0.85 §3.2): every per-symbol lookup in the validation path uses the page grounding already resolved (`max_results=3` + `_resolve_ambiguous_by_definition`), falling back to today's page when that stays ambiguous. Refined 2026-10-15: the root cause is that `lookup(..., max_results=1)` truncates before its tie check, so a tie is always "found"; over all 1,418 documented symbols only `miss` is affected.

Overall Score: 2.8
Decision: Fail — real defect
