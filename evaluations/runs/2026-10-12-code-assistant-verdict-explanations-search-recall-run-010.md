# Evaluation Result

Date: 2026-10-12
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. The session did not read the planning doc or PROJECT_STATUS.md until all fifteen tasks were done. (It did read validator source during 73.10 and 73.14, to locate the defects it had just observed.)
Agent Version: v0.83.0 (released; tag `v0.83.0`, commit `2740519`; HEAD `a6f2b80`), editable install of this checkout
Prompt ID: 73.10
Prompt Category: Verdict Explanations and Search Recall (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.83.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session f901c141918644d48e852d4bb886c5e0. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs.
Prompt Text:

"Compute the eigenvalues of a symmetric 3x3 matrix."

Attempt 1 (the client's first, idiomatic answer; the same layout as the docs' own examples):
```gauss
x = { 2 1 0,
      1 2 1,
      0 1 2 };
va = eigh(x);
print "Eigenvalues:";
print va;
```

Attempt 2 (a diagnostic by the client: the same matrix written on one line; presented to the user):
```gauss
x = { 2 1 0, 1 2 1, 0 1 2 };
va = eigh(x);
print "Eigenvalues:";
print va;
```

Captured output (abridged, verbatim fields):
```
search_docs("eigenvalues of a symmetric matrix") -> "ungrounded"; candidates: eigh, eighv, lapeigh*, lapgeigh*
search_docs("eigh") -> "grounded"; eigh.rst
attempt 1 -> "review_required"
  reason: "parameter role unknown -- `eigh` argument 1 (parameter `x`): `x` is assigned from an expression
           (`{ 2 1 0,`), which is never evaluated"
  coverage.parameter_role_check "unknown"
  coverage_gaps: [{check: parameter_role, symbol: eigh, argument: 1, cause: argument_assigned_from_expression,
                   detail: "... (`{ 2 1 0,`) ..."}]
attempt 2 -> "handoff_candidate"; coverage all complete; validation_id issued (not prepared: operator gate)
```

Post-run diagnosis (direct `validate_code` plus the internals):
```
_masked_statements(code) yields one statement PER LINE:
  (2, 'x = { 2 1 0,')  (3, '      1 2 1,')  (4, '      0 1 2 }')  (7, 'va = eigh(x)') ...
_governing_assignment('x', ...) -> '{ 2 1 0,'
```
`_masked_statements` (`gauss_pre_execution_validation.py:1264`) iterates `code.splitlines()` and only then splits on `;`, so a statement that spans lines is cut at the first newline. The role tracer and the precondition tracer both read assignments through it.

Supplementary probes (recording session, direct `validate_code`):

| Snippet | Verdict |
|---|---|
| `x = {1 2,`⏎`3 4}; m = meanc(x);` | review_required (same cause) |
| `x = {1 2, 2 1}; y = invpd(x);` (one line, not PD) | **not_ready** (precondition VIOLATED) |
| `x = {1 2,`⏎`2 1}; y = invpd(x);` (same matrix, two lines) | **review_required** (precondition UNVERIFIED, role unknown) |

Expected behavior: Mode A candidates including `eigh`; then handoff_candidate for a documented call on a traced literal matrix.

Observed behavior: Search was as expected; **the client followed `eigh` back to its grounded page.** The code verdict exposed a **real defect**: a multi-line matrix literal, the layout the GAUSS docs themselves use, is never traced, because the tracer splits statements at newlines. The client diagnosed this from the `coverage_gaps` detail (`{ 2 1 0,`), confirmed it with a one-line variant, and located the cause in `_masked_statements`. The direct diagnosis confirms that cause exactly. **`coverage_gaps` agreed with what the validator did**, and its quoted detail is what made the defect diagnosable. But its cause label (`argument_assigned_from_expression`) is wrong about the code, because the literal is not an expression. The supplementary probe shows the defect's worse side: a **known** SPD precondition violation drops from not_ready to review_required when the matrix spans two lines. That is a softer verdict than the evidence supports. It is not execution-reachable, because review_required issues no `validation_id`.

Pass/fail: Fail (real validator defect found live; the client's presented answer and diagnosis were correct)
Defect severity: Moderate (a common, documented code layout loses role tracing and downgrades a known precondition violation not_ready → review_required; never reaches handoff_candidate)
Remediation: Next milestone: split statements on `;` across the whole snippet while keeping line numbers, then re-run the CLAUDE.md verdict diff (the role tracer and precondition tracer both change).

Overall Score: 2.5
Decision: Fail — real defect, carried to the next milestone
