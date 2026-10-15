# Evaluation Result

Date: 2026-10-15
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.10
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 352fc674f22b467fae1e3113c26898e9. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"Write a small procedure that squares its input, and use it on a vector."

Search: `search_docs("proc retp endp define a procedure")` -> partially_grounded; proc.rst, retp.rst, endp.rst
(steered by prior knowledge).

Code:
```gauss
// Procedure that returns the element-by-element square of its input
proc (1) = square(x);
    retp(x .* x);
endp;

// Column vector 1, 2, 3, 4, 5
v = seqa(1, 1, 5);

// Apply the procedure to every element of the vector
v_sq = square(v);

print "v ~ v squared = ";
print v ~ v_sq;
```

Captured output (verbatim fields):
```
"review_required"
reasons: syntax validation coverage is partial ... (unmodelled construct(s): control_flow_block);
         no documentation was found for `square`, so its call signature cannot be checked (a procedure
         defined in this snippet is never checked against documentation); validation coverage is partial ...
coverage_gaps: syntax/unmodelled_construct; signature/square/call_undocumented
user_defined_symbols ["square","v","v_sq"]; unknown_symbols []
```

Diagnosis (direct `validate_code`): syntax `partial` with `unknown_constructs ('control_flow_block',)`; `square`
`documented=False`, `signature_known=False`. **The `coverage_gaps` the client saw agree with the direct diagnosis.**
v0.83.0 gives the same state, but its gap list has no `call_undocumented` entry (finding 3 of 73.x).

Expected behavior: review_required with both causes named (v0.84.0 plan §5: a call to a snippet's own `proc` stays review_required with a named `call_undocumented` gap).

Observed behavior: As expected. The v0.84.0 finding-3 change is visible live: the partial signature check now names `square`. `square` is correctly user-defined, not a hallucinated unknown. The client explained both gaps correctly and did not reshape the code to avoid the `proc`.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
