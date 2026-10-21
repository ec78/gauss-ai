# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.11
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"Simulate an OLS regression with 500 observations, an intercept and two regressors. Compute the coefficients with the / operator and their standard errors, then run it."

Code (S16):
```gauss
// Set the seed so the simulation is repeatable
rndseed 42;

n = 500;

// Intercept plus two standard normal regressors
X = ones(n, 1) ~ rndn(n, 2);

// True coefficients: intercept 1, slopes 0.5 and -2
btrue = { 1, 0.5, -2 };

// Simulate y with standard normal errors
y = X*btrue + rndn(n, 1);

// OLS coefficients via the '/' operator (least-squares solve)
b = y / X;

// Residuals and error variance, with n - k degrees of freedom
k = cols(X);
e = y - X*b;
s2 = (e'e) / (n - k);

// Covariance matrix of b and the standard errors
vb = s2 * invpd(X'X);
se = sqrt(diag(vb));

print "Coefficients, standard errors:";
print b~se;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **review_required**; preconditions: `invpd` unverified; coverage gaps: `cols` arg 1 `argument_assigned_from_expression`; `invpd` arg 1 `argument_expression`; `sqrt` arg 1 `argument_expression`; `diag` arg 1 `argument_assigned_from_expression`; `invpd` `runtime_dependent`.
Reasons: "runtime-dependent precondition(s) remain unverified for: invpd"; "validation coverage is partial (incomplete: parameter roles partial, preconditions unknown), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `cols` argument 1 (parameter `x`): `X` is assigned from an expression (`ones(n, 1) ~ rndn(n, 2)`), which is never evaluated"; "parameter role unknown -- `invpd` argument 1 (parameter `x`): `X'X` is an expression, and expressions are never evaluated"; "parameter role unknown -- `sqrt` argument 1 (parameter `x`): `diag(vb)` is an expression, and expressions are never evaluated"; "parameter role unknown -- `diag` argument 1 (parameter `x`): `vb` is assigned from an expression (`s2 * invpd(X'X)`), which is never evaluated"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs.

Expected behavior: The runtime-divisor gap is disclosed; whatever the verdict, an approved run matches direct GAUSS.

Observed behavior: review_required, from `invpd(X'X)` (runtime precondition) and four expression role gaps, not from `b = y / X`. The client told the user that `y / X` itself is not checked by design (a runtime divisor), and offered `eye(3) / (X'X)` as a way round the `invpd` gap without using it (probe P4: still review_required, from the other gaps). No prompt, nothing ran. Real GAUSS runs S16: coefficients 0.983, 0.506, −2.039 (true 1, 0.5, −2), SEs ≈ 0.047, as the client predicted. Search "diag sqrt ones rows cols" silently dropped `cols` (76.x finding 5, known; the client used `cols` anyway).

Pass/fail: Pass
Defect severity: None
Remediation: None (the search drop belongs to v0.88.0).

Overall Score: 4.0
Decision: Pass
