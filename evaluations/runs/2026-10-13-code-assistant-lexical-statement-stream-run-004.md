# Evaluation Result

Date: 2026-10-13
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.4
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 00fb446d1d1243579e25095018809d9b. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"Compute the inverse of a 3x3 matrix and print the result with a label like "inverse = ".""

Search: `search_docs("inverse of a matrix inv")` -> grounded; invinvpd.rst.

Code:
```gauss
// Square, invertible 3x3 matrix (determinant = 25)
x = { 3 2 1,
      0 1 -2,
      1 3 4 };

xi = inv(x);

print "inverse = ";
print xi;
```

Captured output: `handoff_candidate`; `preconditions: [{"symbol":"inv","status":"satisfied","explanation":"the
literal input matrix is square with a nonzero determinant (verified by exact determinant computation)"}]`;
`precondition_check: complete`; `coverage_gaps []`; prepare -> `real_gauss_not_allowed`.

Compared with v0.83.0: **review_required** ("runtime-dependent precondition(s) remain unverified for: inv"; `inv`
argument 1 assigned from the expression `{ 3 2 1,`). The multi-line literal now reaches the precondition tracer too.

Expected behavior: handoff_candidate, with `inv`'s documented square-and-invertible precondition SATISFIED on the traced literal.

Observed behavior: As expected. The precondition tracer now reads the whole three-line literal (v0.84.0 §3.3 P4/P5) and verifies invertibility exactly. The client chose `inv` over `invpd` because the matrix is not symmetric, and its hand-computed inverse is correct.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
