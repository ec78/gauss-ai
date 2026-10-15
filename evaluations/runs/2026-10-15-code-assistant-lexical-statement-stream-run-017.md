# Evaluation Result

Date: 2026-10-15
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.17
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 352fc674f22b467fae1e3113c26898e9. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"I need a comprehensive unit root testing library. I want something that can handle data with structural breaks. Is there a GAUSS package available for this?"

Searches:
```
search_docs("unit root test with structural breaks") -> "ungrounded"; unmatched unit/root/structural; ambiguous "test";
    candidates mvnTest, grangerTest, cdTest (none relevant)
search_docs("Zivot Andrews zaUnitRoot") -> partially_grounded; tsmt/zandrews.rst
search_docs("tspdlib") -> "ungrounded"; one candidate: tspdlib-landing (tspdlib/docs/tspdlib-landing.rst)
search_docs("tspdlib-landing") -> "ungrounded"; unmatched ["tspdlib","landing"]; the same candidate again
search_docs("adf augmented dickey fuller") -> partially_grounded; tspdlib/docs/adftspd.rst
search_docs("adf_1break adf_2breaks"), ("lm_1break lm_2breaks lmkpss"), ("fourier_adf fourier_lm fourier_kpss")
    -> grounded on tspdlib/docs pages; ambiguous candidates also offered qr_fourier_adf(_bootstrap)
```
All searches after the first were steered by prior knowledge of TSPDLIB and its function names.

Code (simulated data, because `loadd` would be file_read):
```gauss
library tspdlib;
rndseed 4321;
T = 200;
y = cumsumc(rndn(T, 1));
y[101:T] = y[101:T] + 5;
{ tstat, tb, lags, cv } = adf_1break(y, 1);
```
(plus five `print` lines)

Captured output: `review_required`; only gap parameter_role/cumsumc/1/x/argument_expression ("`rndn(T, 1)` is an
expression"); `system_statements []`.

Diagnosis (direct `validate_code`): `cumsumc` arg 0 `unknown`; `adf_1break` arg 0 matches (`y` traced to `cumsumc`'s
documented return). **The gap the client saw agrees with the direct diagnosis.** Same on v0.83.0.
`_candidate_tokens("tspdlib-landing")` returns `['tspdlib', 'landing']`.

Expected behavior: A correct answer from grounded pages. Any partial verdict names its cause.

Observed behavior: Answer correct (TSPDLIB: `adf`, `adf_1break/2breaks`, `LM_1break/2breaks`, `LMkpss`, `Fourier_ADF/LM/KPSS`, quantile Fourier tests; TSMT `zandrews`). Verdict as designed: a call nested as an argument is an expression, and expressions are never evaluated, although a variable assigned from the same call is traced. **Search defect found live (minor):** the server tells the client to "search a candidate's name to read its documentation", but a candidate whose name contains a hyphen (`tspdlib-landing`) cannot be opened that way, because the name is tokenized on `-`. The plain-language question also found none of the relevant pages. **Open question, not claimed as a defect:** `library tspdlib;` produces no system statement; `library` loads package code from disk, and `run`/`#include` are registered as source inclusion.

Pass/fail: Pass with defect recorded
Defect severity: Minor (search: hyphenated candidates cannot be opened; plain-language recall)
Remediation: Search/grounding milestone: resolve a candidate by its exact listed symbol (hyphens included). Decide whether `library` belongs in `_SYSTEM_STATEMENT_REGISTRY` (user decision).

Overall Score: 3.0
Decision: Pass with defect recorded
