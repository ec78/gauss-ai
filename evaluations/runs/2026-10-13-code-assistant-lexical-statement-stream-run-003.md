# Evaluation Result

Date: 2026-10-13
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.3
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 00fb446d1d1243579e25095018809d9b. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"Compute the eigenvalues of a symmetric 3x3 matrix."

Search: `search_docs("eigenvalues of a symmetric matrix eigh")` -> partially_grounded; eigh.rst (unmatched
"eigenvalues", "symmetric"). The query was steered by prior knowledge: the client named `eigh` itself.

Code:
```gauss
// Symmetric 3x3 matrix
x = {  2 -1  0,
      -1  2 -1,
       0 -1  2 };

va = eigh(x);

print "eigenvalues = ";
print va;
```

Captured output: `handoff_candidate`, coverage complete, `coverage_gaps []`, validation_id `9ff6e425...`; prepare ->
`real_gauss_not_allowed`.

Compared with v0.83.0: **review_required**, "parameter role unknown -- `eigh` argument 1 (parameter `x`): `x` is
assigned from an expression (`{  2 -1  0,`)": exactly the 73.10 defect.

Expected behavior: handoff_candidate for `eigh` on a traced literal matrix, however the literal is laid out.

Observed behavior: As expected. The 73.10 fix holds live on the same task that found it. The client's hand-computed eigenvalues (2-sqrt2, 2, 2+sqrt2) are correct; it said it could not confirm `eigh`'s output order from the excerpt.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
