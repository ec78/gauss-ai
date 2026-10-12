# Evaluation Result

Date: 2026-10-12
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. The session did not read the planning doc or PROJECT_STATUS.md until all fifteen tasks were done. (It did read validator source during 73.10 and 73.14, to locate the defects it had just observed.)
Agent Version: v0.83.0 (released; tag `v0.83.0`, commit `2740519`; HEAD `a6f2b80`), editable install of this checkout
Prompt ID: 73.12
Prompt Category: Verdict Explanations and Search Recall (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.83.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session f5aa11bcb4f042a5b8c68f9b36f29030. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs.
Prompt Text:

"Sort a matrix by its second column."

Attempt 1:
```gauss
x = { 4 7 3, 1 3 2, 3 4 8 };
y = sortc(x, 2);
y_desc = sortc(x, 2, -1);
print "Sorted by column 2 (ascending):";
print y;
print "Sorted by column 2 (descending):";
print y_desc;
```

Captured output (abridged, verbatim fields):
```
search_docs("sort a matrix by a column") -> "ungrounded"; unmatched ["sort"]; ambiguous ["sort a matrix by a column"];
    candidates (ambiguous_resolution): sortmc, sortr/sortrc     <- sortc absent
search_docs("sortc") -> "grounded"; sortc.rst
validate_code -> "handoff_candidate"; coverage all complete; coverage_gaps []
```

Post-run diagnosis (recording session, the derived concept index):
```
sortc  sortc.rst        keywords ('sortc', 'sort', 'dataframe')
sortmc sortmc.rst       keywords ('sortmc', 'sort', 'multiple', 'column')
sortr  sortrsortrc.rst  keywords ('sortr', 'sortrc', 'sort', 'column', ...)
```
`sortc`'s Purpose text yields no `column` keyword, so it overlaps the query on one keyword while `sortmc` and `sortr` overlap on two. The ambiguous resolution keeps only the two-keyword ties. Mode B does not run when there are ambiguous candidates (§3.4), so `sortc` cannot appear.

Expected behavior: Mode A candidates (planning §2.4 listed `sortmc`, `sortr`, `sortrc`). The client follows a candidate to a grounded page and writes `sortc`-based code.

Observed behavior: The code verdict is correct (handoff_candidate). **The client did not follow a candidate.** None was the standard function, so it searched `sortc` from its own prior knowledge. A client without that knowledge would have used `sortmc` or `sortr`, both less direct. The client flagged this itself as the worst recall miss of the session. **Steering disclosure:** the client wrote the matrix on one line on purpose, to avoid the 73.10 defect, and said so.

Pass/fail: Pass with limitation (code and answer correct; the search candidates omit the standard function)
Defect severity: Minor (search recall: the right page is not offered; nothing wrong is grounded)
Remediation: Next milestone, search side: a curated alias (`sort` → `sortc`), or let a one-keyword exact-token page compete with ambiguous two-keyword ties. Either needs the gate-equivalence tests.

Overall Score: 3.2
Decision: Pass with limitation disclosed
