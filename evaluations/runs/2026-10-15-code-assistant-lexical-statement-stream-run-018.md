# Evaluation Result

Date: 2026-10-15
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.18
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 352fc674f22b467fae1e3113c26898e9. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"Can you provide me sample GAUSS code to minimize a procedure I have written (use myFunc as function name) using the sgpSolveMT function?"

The user wrote "sgpSolveMT"; the client read it as `sqpSolveMT` and said so. `search_docs("sgpSolveMT")` ->
ungrounded with no candidates (no near-miss suggestion).

Searches: "pvPack pvUnpack pvCreate" (grounded), "sqpSolveMTControlCreate sqpSolveMTout" (partially_grounded;
`sqpsolvemtout` unmatched), "sqpSolveMT" (grounded, but the excerpt stops inside the control-structure table, before
Outputs), then "struct PV structure procedure argument" and "optmt" while trying to ground the `struct PV p` parameter
form (both inconclusive). The output members `out.par`/`out.fct`/`out.retcode` came from prior knowledge and the
client said so.

Code (abridged; the full snippet opens with a six-line `/* ... */` comment):
```gauss
proc (1) = myFunc(struct PV p);
    local b;
    b = pvUnpack(p, "b");
    retp((b[1] - 3)^2 + (b[2] + 1)^2);
endp;

b0 = { 0, 0 };
struct PV par1;
par1 = pvCreate();
par1 = pvPack(par1, b0, "b");
struct sqpSolveMTControl ctl;
ctl = sqpSolveMTControlCreate();
struct sqpSolveMTout out;
out = sqpSolveMT(&myFunc, par1, ctl);
print "estimated b = " pvUnpack(out.par, "b")';
print "f at minimum = " out.fct;
print "return code (0 = normal convergence) = " out.retcode;
```

Captured output (verbatim fields):
```
"not_ready"; syntax "invalid"
reason: syntax: call to `myFunc` has an argument with adjacent tokens separated only by whitespace and no comma or
        operator between them (`struct PV p`)
coverage_gaps: syntax/unmodelled_construct; parameter_role/pvUnpack/1/p1/argument_untraced;
               parameter_role/sqpSolveMT/1/&fct/documented_type_missing; parameter_role/sqpSolveMT/3/variadic_position;
               parameter_role/pvUnpack/1/p1/argument_expression
```

Diagnosis (direct `validate_code` plus source): the issue is rule `call_argument_missing_separator` at line 11 (the
`proc` header). `_check_call_argument_missing_separator` (`gauss_pre_execution_validation.py:2457`) scans every
call-shaped `name(` in the masked text and skips only `_BLOCK_CONSTRUCT_KEYWORDS`; the procedure name in
`proc (1) = myFunc(struct PV p);` is not a keyword, so the header's typed parameter list is checked as call arguments.
**v0.83.0 gives the same not_ready** (reported at line 6, because its comment stripper collapsed the six-line block
comment; v0.84.0's line 11 is correct). The `&fct` gap is 74.16's defect again.

Real `tgauss.exe -b` spot check (recording session, scratch directory, GAUSS 26):
```
s1: proc (1) = myFunc(struct PV p); ... print "S1_VALUE_AT_START " myFunc(par1);   -> S1_VALUE_AT_START 10.000000
s2: the client's program, unchanged in substance                                   -> S2_B 2.9999999 -0.99999998
                                                                                      S2_FCT 4.8170459e-15
                                                                                      S2_RET 0.0000000
```
A typed `struct` parameter in a `proc` header is valid GAUSS, and the client's program (including the
`sqpSolveMTout` members it took from prior knowledge) runs and converges.

Expected behavior: The idiomatic `sqpSolveMT` objective (`proc ... myFunc(struct PV p)`) is valid GAUSS: review_required at worst (a snippet-defined `proc` is an unmodelled block), never syntax INVALID.

Observed behavior: **Real defect found live: a false INVALID.** Valid GAUSS, confirmed by `tgauss.exe -b`, is rejected as a syntax violation, so the verdict is not_ready with a misleading reason. Every procedure with a typed `struct` parameter is affected; that is the standard calling convention for `sqpSolveMT`, `optmt`, `QNewtonmt`, `cmlmt` and `PV`/`DS`-based code generally. The defect predates v0.84.0 (identical on v0.83.0, and the rule dates from v0.77.0). It is in the safe direction: no `validation_id` is issued, and nothing could execute. The client's code and its uncertainty statements were right; it did not rewrite the code, because there is no other valid way to write the objective.

Pass/fail: Fail
Defect severity: Moderate (false INVALID on idiomatic code; safe direction; pre-existing since at least v0.83.0)
Remediation: Next milestone: `call_argument_missing_separator` must not treat a `proc`/`keyword` header's parameter list as a call (typed `struct <Type> <name>` parameters are legal); record the s1/s2 spot checks as provenance; regression test plus a verdict diff.

Overall Score: 2.5
Decision: Fail — real defect
