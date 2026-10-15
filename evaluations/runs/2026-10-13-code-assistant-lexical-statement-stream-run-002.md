# Evaluation Result

Date: 2026-10-13
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.2
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 00fb446d1d1243579e25095018809d9b. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"Compute the determinant of a 3x3 matrix and print it with a label like "det = ..."."

Search: `search_docs("determinant of a matrix det")` -> partially_grounded; det.rst (unmatched "determinant").

Code (the client's only attempt):
```gauss
x = { 3 2 1,
      0 1 -2,
      1 3 4 };

d = det(x);

print "det = " d;
```

Captured output (verbatim fields):
```
validate_code -> "handoff_candidate"; called_symbols ["det"]; user_defined_symbols ["d","x"];
                 coverage all complete/not_applicable; coverage_gaps []; validation_id 4956536a...
gauss_execution_prepare -> {"error": "real_gauss_not_allowed", ...}
```

Compared with v0.83.0 (same snippet, direct `validate_code` on a `git archive` of `2740519`): **not_ready**, reason
"no documented GAUSS function call was found ...", `user_defined_symbols ("d","det","x")`: the 73.14 defect, plus the
73.10 multi-line literal.

Expected behavior: handoff_candidate for `det` on a traced literal matrix, whatever the label text and however the literal is laid out.

Observed behavior: As expected. **Both 73.x defects are fixed live in one snippet**: the `"det = "` label no longer makes `det` a variable (73.14), and the three-line literal in the docs' own layout is traced (73.10). The prepare call was refused by the operator gate.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
