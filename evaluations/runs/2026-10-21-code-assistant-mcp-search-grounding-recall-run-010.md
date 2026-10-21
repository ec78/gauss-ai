# Evaluation Result

Date: 2026-10-21
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`c60c77d5…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All thirteen tasks ran on 2026-10-21, 19:10-19:30 local (23:10-23:30 UTC). During the tasks the client read GAUSS documentation files and the installed package's `package.json` directly from disk, but no gauss-ai source file, `KNOWN_LIMITATIONS.md`, `PROJECT_STATUS.md` or planning doc; `CLAUDE.md` and one memory note were in its context from the start (v0.88 plan §11.7).
Agent Version: v0.88.0 (released: tag `v0.88.0`, commit `be3df16`, pushed and published on GitHub at 18:57 local, before the tasks), editable install of this checkout (`gauss-ai version` = 0.88.0).
Prompt ID: 79.10
Prompt Category: MCP Search and Grounding Recall of v0.88.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.88.0 over stdio (two `gauss-ai-mcp.exe` processes, PIDs 34308 and 17696, both started 19:09:47 local, after the v0.88.0 install at 19:04:56; which one served the conversation was not determined, but every response carries v0.88.0-only fields such as `omitted_topics` and the `derived_from_docs`/`statement_page`/`non_defining_page` candidate origins). Real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). One server session (`4120e487…`) served all tasks; `gauss_session_start` reported `real_gauss_allowed: true`, and 79.1's prepare rendered a prompt. The client model wrote every query and snippet itself. Post-run: the recording session (the same conversation, after the tasks) re-ran every search query and snippet by calling each archive's own `gauss_mcp_server` tool functions on `git archive`s of v0.88.0 (`be3df16`) and v0.87.0 (`4103280`), each archive's modules asserted imported. **All 24 live responses (13 searches, 11 validations) are identical to the v0.88.0 re-run in every field** (excerpt text, candidates, reasons, gaps, `code_sha256`; `validation_id` aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) runs of every client snippet except 79.4's `dllcall` (its DLL does not exist), each from its own new empty directory.
Prompt Text:

"please search and explain the following GAUSS functions: invpd diag sqrt rows cols"

Search `invpd diag sqrt rows cols` (live, identical on the v0.88.0 re-run): **partially_grounded**
- sources: `invpd` (invinvpd.rst), `diag` (diag.rst), `sqrt` (sqrt.rst), `rows` (rows.rst)
- unmatched: none; ambiguous: none; **omitted_topics: ['cols']**
- v0.87.0, same query: **grounded**; sources: `diag` (diag.rst), `sqrt` (sqrt.rst), `rows` (rows.rst), `cols` (cols.rst); unmatched: none; ambiguous: none; candidates: none

Search `cols` (live, identical on the v0.88.0 re-run): **grounded**
- sources: `cols` (cols.rst)
- unmatched: none; ambiguous: none
- v0.87.0, same query: identical

Code (call #26):
```gauss
// Simulated regression data
rndseed 90701980;
n = 500;
x = ones(n, 1) ~ rndn(n, 2);
btrue = { 1, 0.5, -0.25 };
y = x * btrue + rndn(n, 1);

nobs = rows(x);
k = cols(x);

// OLS: x'x is symmetric positive definite, so invpd applies
xxi = invpd(x'x);
b = xxi * x'y;

// Residual variance and standard errors
e = y - x * b;
s2 = e'e / (nobs - k);
se = sqrt(diag(s2 * xxi));

print "nobs = " nobs "  k = " k;
print "  coef        se";
print b ~ se;
```

Captured output (live, reproduced exactly on v0.88.0): **review_required**; preconditions: `invpd` unverified.
Reasons: "runtime-dependent precondition(s) remain unverified for: invpd"; "validation coverage is partial (incomplete: parameter roles partial, preconditions unknown), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `rows` argument 1 (parameter `x`): `x` is assigned from an expression (`ones(n, 1) ~ rndn(n, 2)`), which is never evaluated"; "parameter role unknown -- `cols` argument 1 (parameter `x`): `x` is assigned from an expression (`ones(n, 1) ~ rndn(n, 2)`), which is never evaluated"; "parameter role unknown -- `invpd` argument 1 (parameter `x`): `x'x` is an expression, and expressions are never evaluated"; "parameter role unknown -- `sqrt` argument 1 (parameter `x`): `diag(s2 * xxi)` is an expression, and expressions are never evaluated"; "parameter role unknown -- `diag` argument 1 (parameter `x`): `s2 * xxi` is an expression, and expressions are never evaluated"
Coverage gaps: parameter_role/rows arg 1 `argument_assigned_from_expression`; parameter_role/cols arg 1 `argument_assigned_from_expression`; parameter_role/invpd arg 1 `argument_expression`; parameter_role/sqrt arg 1 `argument_expression`; parameter_role/diag arg 1 `argument_expression`; precondition/invpd `runtime_dependent`
v0.87.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): exit 0, no error; the directory held only `prog.gss` afterwards. Stdout:

```text
nobs =        500.00000   k =        3.0000000 
  coef        se

       1.0059781      0.044605619 
      0.49255163      0.044671686 
     -0.26959820      0.042537041 
```

Expected behavior: The five-function search: a fifth documented symbol is named in `omitted_topics` (§3.10; v0.87.0 dropped one silently) and tier 3 ranks `invpd` in.

Observed behavior: **`omitted_topics: ['cols']`** with the omitted note; the bundle is `partially_grounded`. The client searched `cols` separately as the note says, and explained all five. On v0.87.0 the same query is `grounded` on `diag`, `sqrt`, `rows`, `cols` and **silently drops `invpd`** (the 76.5/77.5/78.11 finding). The client's OLS example is review_required: five expression gaps and `invpd`'s `runtime_dependent` precondition, all named correctly. Real GAUSS: coefficients 1.006, 0.493, -0.270 with standard errors near 0.044, as predicted.

Search: the user's own list. **`omitted_topics` was used**: it led the client to search `cols` on its own.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
