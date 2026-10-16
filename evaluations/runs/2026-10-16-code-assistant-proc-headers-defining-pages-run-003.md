# Evaluation Result

Date: 2026-10-16
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. All twenty-one tasks ran on 2026-10-16 in one server session. The session did not read the planning doc, PROJECT_STATUS.md or any source until all tasks were done.
Agent Version: v0.85.0 (released; tag `v0.85.0`, commit `f11505e`; HEAD `d634b40`, whose `scripts/` is identical to the tag), editable install of this checkout (`pip show gauss-ai` = 0.85.0). The live server's own output carries v0.85.0-only behavior (`library` -> `source_inclusion` in 75.3/75.6; a typed `struct` procedure header is no longer INVALID in 75.2; `miss` keeps its signature in 75.4).
Prompt ID: 75.3
Prompt Category: Procedure Headers and Defining Pages (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.85.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session d965dee780a44d0e8faacbdafbd0eaad. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.85.0 and v0.84.0 (`d19c61c`); every live verdict reproduced exactly on the v0.85.0 archive. Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) programs run by the recording session from a scratch directory, including the client's own programs. No `gauss_execution_prepare` call was made.
Prompt Text:

"Show me how to maximize a log-likelihood I write myself using optmt."

Searches:
```
search_docs("optmt") -> grounded; the excerpt shows `.. include:: include/optmtcontrolstruct.rst` and
    `.. include:: include/optmtresultsstruct.rst` UNEXPANDED
search_docs("optmt modelResults ind function gradient, ...") -> partially_grounded (optmt, library); unmatched
    modelresults, ind
search_docs("optmtControlCreate") -> grounded
search_docs("modelResults") -> ungrounded, no candidates
```
The control and results structure members live in `optmt/include/optmtcontrolstruct.rst` and
`optmt/include/optmtresultsstruct.rst` in the published docs; no excerpt shows them, because the `include`
directive is never expanded. This is a second cause, beside the known truncation, for structure members coming from
prior knowledge (new; see planning v0.85 §11.5).

Code (abridged):
```gauss
library optmt;
...
struct optmtResults out;
out = optmt(&negLogLik, par1, y, x, ctl);
...
proc negLogLik(struct PV p, y, x, ind);
    local beta, sigma, e, lnl;
    struct modelResults mm;
    ...
    if ind[1];
        ...
        mm.function = -sumc(lnl);
    endif;
    retp(mm);
endp;
```

Captured output: `not_ready`, one reason: line 1 `library` is a system-touching statement (`source_inclusion`).
All 10 functions grounded, signatures complete, no unknown symbol; gaps: `control_flow_block`, `&modelProc`
`documented_type_missing` (known `&` limitation), three `variadic_position`, expression/untraced arguments.

Diagnosis: identical; agree. The client called the not_ready expected (the add-on needs `library`) and explained it
correctly.

v0.84.0, same snippet: also not_ready, but for the 74.18 defect (`call_argument_missing_separator` on
`proc negLogLik(struct PV p, y, x, ind);`, line 36) with no system statement. v0.85.0 makes the reason true.

Real GAUSS (client's program verbatim): runs, `retcode 0`, beta `0.896 2.147`, sigma `1.360`, log-likelihood
`-345.31`. `modelResults`, `mm.function`, `ind[1]`, `out.par`, `out.fct` and `out.retcode` (all flagged by the
client as prior knowledge) are right.

Expected behavior: A user-written optmt objective is not_ready only because of `library` (v0.85.0 registry), with a
true reason.

Observed behavior: As expected.

Pass/fail: Pass
Defect severity: None (new excerpt cause recorded for the search milestone)
Remediation: Search/grounding milestone: excerpts should expand or cite `.. include::` targets.

Overall Score: 4.0
Decision: Pass
