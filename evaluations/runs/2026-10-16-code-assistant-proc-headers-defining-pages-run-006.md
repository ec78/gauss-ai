# Evaluation Result

Date: 2026-10-16
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. All twenty-one tasks ran on 2026-10-16 in one server session. The session did not read the planning doc, PROJECT_STATUS.md or any source until all tasks were done.
Agent Version: v0.85.0 (released; tag `v0.85.0`, commit `f11505e`; HEAD `d634b40`, whose `scripts/` is identical to the tag), editable install of this checkout (`pip show gauss-ai` = 0.85.0). The live server's own output carries v0.85.0-only behavior (`library` -> `source_inclusion` in 75.3/75.6; a typed `struct` procedure header is no longer INVALID in 75.2; `miss` keeps its signature in 75.4).
Prompt ID: 75.6
Prompt Category: Procedure Headers and Defining Pages (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.85.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session d965dee780a44d0e8faacbdafbd0eaad. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.85.0 and v0.84.0 (`d19c61c`); every live verdict reproduced exactly on the v0.85.0 archive. Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) programs run by the recording session from a scratch directory, including the client's own programs. No `gauss_execution_prepare` call was made.
Prompt Text:

"Run a unit root test with a structural break using the tspdlib package."

Searches:
```
search_docs("tspdlib unit root test structural break") -> partially_grounded on break.rst (the `break` STATEMENT,
    reached through the English word "break"); unmatched tspdlib, unit, root
search_docs("zandrews") -> grounded on tsmt/zandrews.rst (prior knowledge; the client noted it is TSMT, not tspdlib)
search_docs("adf_1break lm_1break") -> grounded on the tspdlib pages (prior knowledge); 3 relevant candidates
    (adf_2breaks, Fourier_ADF, qr_fourier_adf), named in the answer but not opened
search_docs("unit root test with a structural break") -> break.rst again
```
The user's literal wording (recording-session re-run) grounds on `run.rst` and `break.rst`: two English words in
the question resolve to GAUSS command pages (new; see planning v0.85 §11.5).

Code (abridged): `library tspdlib;`, a simulated random walk with a level shift at 121, then
`{ tstat, tb, lags, cv } = adf_1break(y, model, pmax, ic, trimm);` with the documented optional arguments.

Captured output: `not_ready`, one reason: `library` (`source_inclusion`, line 1). Otherwise grounded, syntax
validated; gaps `cumsumc` arg 1 `argument_expression`, `adf_1break` arg 1 `argument_assigned_from_expression`.
Diagnosis identical; agree.

v0.84.0, same snippet: **review_required** with no system statement. v0.85.0's `library` registration (74.17's
open question, decided 2026-10-15) confirmed live.

Real GAUSS (client's program verbatim): **fails**, `G0152 Variable not initialized` in tspdlib `getlag.src` line 77.
Cause, from the installed package (tspdlib 3.0.2): the real signature is
`ADF_1break(y, model[, outlier, pmax, ic, trimm])` (`adf_1br.src` header and `dynargsGet(1|4, 1, 8, 3, 0.10)`), but
both the package's own `docs/adf_1br.rst` and the published copy document `(y, model [, pmax, ic, trimm])`. Every
positional optional argument shifts by one, so `ic` received `0.10` and no lag was ever selected.
`adf_1break(y, model)` and `adf_1break(y, model, 1, pmax, ic, trimm)` both run: ADF `-2.458`, break at 114, 0 lags,
critical values `-5.34 -4.80 -4.58`, unit root not rejected (as the client predicted). The validator checked the
call correctly against the docs it has. On v0.84.0 the *correct* 6-argument call is a false INCOMPATIBLE
("documented form(s) accept 2-5 argument(s)"); on v0.85.0 `library` masks it.

Expected behavior: tspdlib code is not_ready because of `library`, with a true reason.

Observed behavior: As expected for gauss-ai. The client followed the documentation exactly and still produced code
that fails: an upstream documentation defect (tspdlib), which no docs-grounded check can catch.

Pass/fail: Pass with defect recorded
Defect severity: Upstream (tspdlib 3.0.2 docs omit `outlier`); Minor (search: English words ground on command pages)
Remediation: Report the `adf_1break` doc error upstream (user's choice). Search/grounding milestone: English words in a question should not resolve to command pages.

Overall Score: 3.0
Decision: Pass with defect recorded
