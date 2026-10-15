# Evaluation Result

Date: 2026-10-13
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.5
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 00fb446d1d1243579e25095018809d9b. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"Write well-commented GAUSS code that simulates data and computes OLS coefficients."

Search: `search_docs("rndn ones rndseed")` -> grounded (rndn, ones, rndseed pages); `invpd` was already read in
74.4. Later `search_docs("slash operator least squares solution y/x")` -> grounded; matrix-division.rst. The client
reached the slash operator from the remark on invinvpd.rst ("the slash operator `/` ... will provide greater accuracy").

Attempt 1 (abridged; the full snippet opens with a `/* ... */` block comment and has `//` comments on most lines):
```gauss
rndseed 90701980;
n = 1000;
x1 = rndn(n, 1);
x2 = rndn(n, 1);
X = ones(n, 1) ~ x1 ~ x2;
b_true = { 1, 0.5, -2 };
y = X * b_true + rndn(n, 1);
b_ols = invpd(X'X) * X'y;
print "true coefficients ~ OLS estimates = ";
print b_true ~ b_ols;
```
Attempt 2: identical except `b_ols = y / X;` (with a comment explaining QR least squares).

Captured output (verbatim fields):
```
attempt 1 -> "review_required"
  reasons: runtime-dependent precondition(s) remain unverified for: invpd;
           parameter role unknown -- `invpd` argument 1 (parameter `x`): `X'X` is an expression ...
  coverage_gaps: parameter_role/invpd/1/x/argument_expression; precondition/invpd/runtime_dependent
attempt 2 -> "handoff_candidate"; called_symbols ["rndn","ones"]; coverage_gaps []
```

Diagnosis (direct `validate_code`): attempt 1 has `invpd` role `unknown` (inferred `unknown`) and the `invpd`
precondition `unverified`, `parameter_role_check` partial, `precondition_check` unknown. **The `coverage_gaps` the
client saw agree with the direct diagnosis exactly.** Both attempts give the same verdicts on v0.83.0.

Expected behavior: Attempt 1 review_required: `X'X` is an expression and the SPD precondition is runtime-dependent. No false not_ready.

Observed behavior: As expected. The client explained the partial verdict correctly from `coverage_gaps` and did not misdiagnose it. **Disclosure: the client then rewrote the code** (`invpd(X'X)*X'y` -> `y / X`) so that it would reach candidacy. The rewrite is numerically better and is the docs' own recommendation, but it is shaping code around a validator limitation (expressions are never evaluated), as 72.3 recorded. The long commented header did not disturb lexing or line numbers.

Pass/fail: Pass with limitation disclosed
Defect severity: Minor (deferred expression inference; the client steered its code around it)
Remediation: None new; expression category inference stays deferred (72.3 finding 1).

Overall Score: 3.8
Decision: Pass with limitation disclosed
