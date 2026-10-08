# Evaluation Result

Date: 2026-10-08
Evaluator: Claude (v0.81.0 Idiomatic Handoff Candidacy milestone), driven live through a real connected Claude Code session; the human asked each task in plain words, one at a time, with no steering toward a particular code shape
Agent Version: v0.81.0 (uncommitted on top of e056353), `gauss-ai-mcp` reinstalled and restarted via VS Code window reload
Prompt ID: 71.2
Prompt Category: Idiomatic Handoff Candidacy (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.81.0 process over stdio; real config (docs_root = local develop-branch docs clone `C:/Users/eclow/Documents/GitHub/docs/docs`, verdict-identical to `~/.gauss-ai/docs` per the 2026-10-08 re-baseline; runner = gauss, but the server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 2a560df427f84f18a292986a6699cdd0. The client model wrote every snippet itself, uncoaxed.
Prompt Text:

"Show me how to compute OLS coefficients by hand in GAUSS."

Code the client wrote:
```gauss
rndseed 90701980;
n = 1000;
x1 = rndn(n, 1);
x2 = rndn(n, 1);
x = ones(n, 1)~x1~x2;
btrue = { 1, 0.5, -2 };
y = x*btrue + rndn(n, 1);
b = invpd(x'x)*x'y;
e = y - x*b;
k = cols(x);
s2 = (e'e)/(n - k);
se = sqrt(diag(s2*invpd(x'x)));
print "Coefficients:";
print b;
print "Standard errors:";
print se;
```

Captured output (abridged, verbatim fields):
```
search_docs("invpd ones rndn") -> "grounded"; invpd source (invinvpd.rst) carries the documented OLS example bols = invpd(x'x)*x'y
validate_code -> handoff_readiness "review_required"; reasons: "runtime-dependent precondition(s) remain unverified for: invpd",
                 "validation coverage is partial"; called_symbols ["rndn","ones","invpd","cols","sqrt","diag"]; unknown_symbols [];
                 syntax "validated"; preconditions: invpd "unverified" x2 ("the input is a runtime value or expression,
                 not a literal matrix"); execution_offer_eligible false; no validation_id
```

Expected behavior: review_required, by design (planning §6: expressions are never evaluated, so `invpd(x'x)` stays UNVERIFIED). No false VIOLATED or MISMATCH; all six functions grounded.

Observed behavior: Exactly as expected. Both invpd calls UNVERIFIED (not VIOLATED), every symbol grounded, syntax validated. The client wrote the documented idiom unprompted (it is the official invpd page example). The product consequence, honestly stated: the most common hand-rolled econometrics idiom cannot reach handoff_candidate; that is a deliberate, documented limit, not a defect.

Pass/fail: Pass
Defect severity: None (documented by-design limitation)
Remediation: None in v0.81.0. Already listed in planning §6 and KNOWN_LIMITATIONS.

Overall Score: 4.0
Decision: Pass
