# Evaluation Result

Date: 2026-10-15
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.12
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 352fc674f22b467fae1e3113c26898e9. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"Sum the integers from 1 to 20 with a loop."

Searches:
```
search_docs("for endfor loop") -> "ungrounded"; unmatched ["endfor"]; 8 keyword candidates (dataloop pages, getnr,
                                  getnrmt, vectordl, break), candidates_truncated true. No `for` page.
search_docs("for")             -> "ungrounded"; no sources, no candidates, unmatched_topics []
search_docs("break")           -> "grounded"; break.rst, whose example is a nested `for r(1, rows(x), 1); ... endfor;`
```
The client followed the `break` candidate ("Breaks out of a `do` or `for` loop") back to a grounded page and took the
`for` syntax from its example. The `for` reference page itself was never reached.

Code:
```gauss
// Running total, starting at zero
total = 0;

// Loop i = 1, 2, ..., 20 (start, stop, step) and accumulate
for i(1, 20, 1);
    total = total + i;
endfor;

print "sum of 1 to 20 = " total;
```

Captured output: `not_ready`, "no documented GAUSS function call was found to ground this code against";
`syntax: validated`; `user_defined_symbols ["total"]`.

Diagnosis: `"for"` is in the question stopword list (`gauss_conversation_engine.py:212`), so the bare query has no
token left: no sources, no candidates and an empty `unmatched_topics`. `i` is absent from `user_defined_symbols`
because `call_scan_view` blanks the `for` header counter (v0.84.0 §3.3), consistent with 73.7.

Expected behavior: not_ready with the no-documented-calls reason; syntax validated (`for ... endfor` is modelled).

Observed behavior: Verdict as expected; the client did not add a documented call to manufacture grounding. **Search finding (minor):** a query naming the `for` keyword cannot reach the `for` page. "for" alone returns nothing at all (stopword), and "for endfor loop" lists only keyword matches on "loop".

Pass/fail: Pass with limitation disclosed
Defect severity: Minor (search recall: the `for` keyword is a stopword)
Remediation: Search/grounding milestone: let a query that is exactly a documented keyword (`for`, `if`, `do`) reach its page.

Overall Score: 3.6
Decision: Pass with limitation disclosed
