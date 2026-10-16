# Evaluation Result

Date: 2026-10-16
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. All twenty-one tasks ran on 2026-10-16 in one server session. The session did not read the planning doc, PROJECT_STATUS.md or any source until all tasks were done.
Agent Version: v0.85.0 (released; tag `v0.85.0`, commit `f11505e`; HEAD `d634b40`, whose `scripts/` is identical to the tag), editable install of this checkout (`pip show gauss-ai` = 0.85.0). The live server's own output carries v0.85.0-only behavior (`library` -> `source_inclusion` in 75.3/75.6; a typed `struct` procedure header is no longer INVALID in 75.2; `miss` keeps its signature in 75.4).
Prompt ID: 75.2
Prompt Category: Procedure Headers and Defining Pages (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.85.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session d965dee780a44d0e8faacbdafbd0eaad. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.85.0 and v0.84.0 (`d19c61c`); every live verdict reproduced exactly on the v0.85.0 archive. Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) programs run by the recording session from a scratch directory, including the client's own programs. No `gauss_execution_prepare` call was made.
Prompt Text:

"Write GAUSS code that minimizes my own procedure myObj with sqpSolveMT. My parameters are a 2x1 vector of coefficients."

Searches:
```
search_docs("sqpSolveMT") -> grounded (prior knowledge); the excerpt stops inside the ctl table (known: long-page
    excerpts stop before Outputs)
search_docs("pvPack pvUnpack pvCreate") -> grounded (prior knowledge)
search_docs("sqpSolveMTout structure members par fct retcode, sqpSolveMT example library") -> partially_grounded;
    unmatched `sqpsolvemtout`; the output structure's members were never shown
```

Code (abridged; the full program is the objective below plus `PV` packing, a default control structure and prints):
```gauss
struct sqpSolveMTOut out;
out = sqpSolveMT(&myObj, par1, ctl);
b_hat = pvUnpack(out.par, "b");
...
proc myObj(struct PV p);
    local b;
    b = pvUnpack(p, "b");
    retp((b[1] - 1)^2 + (b[2] + 2)^2);
endp;
```

Captured output: `review_required`; coverage_gaps: syntax `unmodelled_construct` (control_flow_block);
`sqpSolveMT` arg 1 `&fct` `documented_type_missing`; arg 3 `variadic_position`; `pvUnpack` arg 1
`argument_expression` (`out.par`) and `argument_untraced` (`p`). No syntax issue.

Diagnosis (direct `validate_code`): identical. **The gaps the client saw agree with the diagnosis**, and the client
explained each one correctly. The `&fct` cause is the known, disclosed `&`-parameter limitation (`KNOWN_LIMITATIONS.md`,
v0.83.0), so the reason text is false about the docs, as recorded since 74.16.

v0.84.0, same snippet: **not_ready**, syntax INVALID `call_argument_missing_separator` on `proc myObj(struct PV p);`
(the 74.18 defect). This is v0.85.0 finding 1 confirmed live, on the short header form (`proc name(...)`, no `(n) =`;
spot check h7).

Real GAUSS (recording session, the client's program verbatim): converges, `0.99999989 -1.9999994`, `fct 4.2e-13`,
`retcode 0`. The members `out.par`, `out.fct` and `out.retcode`, which the client flagged as prior knowledge, are right.

Expected behavior: The idiomatic objective with a typed `struct PV` parameter is review_required at worst, never
syntax INVALID.

Observed behavior: As expected. The client disclosed which details were not grounded.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
