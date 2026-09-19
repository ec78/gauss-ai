# Evaluation Result

Date: 2026-09-19
Evaluator: Claude (v0.78.0 Controlled Execution Handoff milestone)
Agent Version: Current repository state on 2026-09-19 (`v0.77.0` + in-progress `v0.78.0`)
Prompt ID: 68.12
Prompt Category: Controlled Execution Handoff
Prompt Text:

"Write GAUSS code using colmean to compute column means." (`y = colmean(x);`) -> 'run this'

Objective: Confirm NOT_READY code (an unresolved/unsupported call symbol) can never create an executable handoff request.
Evidence source: FakeModelProvider canned answer using `colmean`, a function not present in this evaluation's documentation fixture (and not among the hand-curated common builtins) -- an unresolved/unsupported call symbol.
Model provider: **FakeModelProvider (deterministic)**.

Captured output:
```
[Warning: the generated code also calls `colmean`, which is not a documented function this session
could verify -- treat it as unverified, not authoritative GAUSS syntax.]
- Execution eligibility: ineligible
  Cannot mark this code eligible for validation:
  - unresolved/unsupported call symbol(s): colmean
- Execution handoff readiness: not_ready
  - unresolved/unsupported call symbol(s): colmean

There is no HANDOFF_CANDIDATE code available to execute right now -- ask for GAUSS code first, and
this offer will appear once it reaches that readiness level.
```

Expected behavior: `colmean` is an unresolved/unsupported symbol -> INELIGIBLE -> readiness NOT_READY; 'run this' reports no HANDOFF_CANDIDATE code is available; no request is ever constructed.

Observed behavior: Exactly as expected -- reproduces the same `colmean` hallucinated-symbol shape this repository's own `31.x`/`66.2`/`67.9` evaluations have used previously, now confirmed to also correctly block the NEW v0.78.0 execution-offer gate, not just the pre-existing eligibility/readiness computation it reuses unmodified. A separate, unscripted spot check in this same live session ("Show me GAUSS code to print 1 plus 1." with no function call at all) produced a THIRD, distinct NOT_READY path -- the pre-existing grounding-gated-generation policy correctly `BLOCK`ed code generation entirely for a request with no resolvable documented topic -- confirming the v0.78.0 offer gate is unreachable via at least three structurally different NOT_READY/REVIEW_REQUIRED causes, not just one.

Pass/fail: Pass
Defect severity: None
Remediation: N/A

Overall Score: 4.0
Decision: Pass
