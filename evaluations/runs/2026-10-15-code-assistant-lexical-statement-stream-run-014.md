# Evaluation Result

Date: 2026-10-15
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.14
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 352fc674f22b467fae1e3113c26898e9. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"How do I sort a matrix by a column in GAUSS?"

The user asked this question twice in a row; both are recorded here.

Searches:
```
search_docs("sort a matrix by a column") -> "ungrounded"; unmatched ["sort"]; ambiguous ["sort a matrix by a column"];
    candidates (ambiguous_resolution): sortmc ("Sorts a matrix on multiple columns"),
    sortr/sortrc ("Sorts the columns ... with respect to a specified row"); candidates_truncated false
search_docs("sortmc") -> grounded; sortmc.rst, whose own example includes `s1 = sortc(x, 1);`
search_docs("sortc")  -> grounded; sortc.rst (sent in parallel with the sortmc lookup: prior knowledge)
second asking: search_docs("sort a matrix by a column") -> byte-for-byte the same result
```

Code:
```gauss
x = { 4 7 3,
      1 3 2,
      3 4 8 };

// Sort the rows of x by column 2, ascending (sort_order 1 is the default)
y_up = sortc(x, 2);

// Sort the rows of x by column 2, descending
y_down = sortc(x, 2, -1);
```
(plus four `print` lines)

Captured output: `handoff_candidate`; both the 2-argument and 3-argument forms signature-compatible; `coverage_gaps []`.

Compared with v0.83.0: **review_required** (`sortc` argument 1 assigned from the expression `{ 4 7 3,`). In 73.12 the
client wrote the literal on one line on purpose to avoid that; here it used the docs' own multi-line layout.

Expected behavior: `sortc(x, c)` reaches handoff_candidate. A plain search offers a candidate the client can follow to the right page.

Observed behavior: Code as expected, and the client no longer had to flatten its literal (73.10 fix). **Search: the known 73.12 recall gap reproduces exactly** (`KNOWN_LIMITATIONS.md`): `sortc` is never offered. The `sortmc` candidate's example does lead to `sortc`, but the client also searched `sortc` by name from prior knowledge. The repeated question gave an identical search result (deterministic).

Pass/fail: Pass with limitation disclosed
Defect severity: Minor (known search recall gap, 73.12)
Remediation: None new; already recorded for the search/grounding milestone.

Overall Score: 3.3
Decision: Pass with limitation disclosed
