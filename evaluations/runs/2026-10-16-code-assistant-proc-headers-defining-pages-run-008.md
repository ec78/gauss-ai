# Evaluation Result

Date: 2026-10-16
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. All twenty-one tasks ran on 2026-10-16 in one server session. The session did not read the planning doc, PROJECT_STATUS.md or any source until all tasks were done.
Agent Version: v0.85.0 (released; tag `v0.85.0`, commit `f11505e`; HEAD `d634b40`, whose `scripts/` is identical to the tag), editable install of this checkout (`pip show gauss-ai` = 0.85.0). The live server's own output carries v0.85.0-only behavior (`library` -> `source_inclusion` in 75.3/75.6; a typed `struct` procedure header is no longer INVALID in 75.2; `miss` keeps its signature in 75.4).
Prompt ID: 75.8
Prompt Category: Procedure Headers and Defining Pages (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.85.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session d965dee780a44d0e8faacbdafbd0eaad. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.85.0 and v0.84.0 (`d19c61c`); every live verdict reproduced exactly on the v0.85.0 archive. Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) programs run by the recording session from a scratch directory, including the client's own programs. No `gauss_execution_prepare` call was made.
Prompt Text:

"Write a procedure that takes a DS structure and returns the mean of its data member."

Searches:
```
search_docs("dsCreate DS structure dataMatrix") -> partially_grounded (dsCreate, structures guide); unmatched
    datamatrix; the DS members are not on the page
```

Attempt 1:
```gauss
proc (1) = dsMean(struct DS d);
    retp(meanc(d.dataMatrix));
endp;
struct DS myData;
myData = dsCreate();
myData.dataMatrix = { 1  2,
                      3  4,
                      5 12 };
m = dsMean(myData);
```
Captured output: `not_ready`, syntax INVALID `let_statement_shape`: "`myData.dataMatrix = {...}` is a `let`
statement, whose target must be a plain name". The client accepted this, called it "a bug in my first draft", told
the user "a `{ ... }` matrix literal can only be assigned to a plain variable name, not to a structure member", and
rewrote the code to assign the literal to `x` first.

**The rule is wrong for member targets.** Real GAUSS (recording session): `d.dataMatrix = { 1 2, 3 4 };` on a DS
(sc01), `g.bStart = { 0, 0 };` on a `gmmControl` (sc02) and `p.x = { 1 2, 3 4 };` on a user structure (sc03) all
run and print the literal. The rule's registry provenance (v0.82.0) cites `tgauss.exe -b` checks of *indexed*
targets only (`v[1:2] = {7, 8};`, `v[., 1] = {1, 2, 3};` -> G0008; `v[2] = {5};` -> G0047); the member branch
(`"." in target`, `_check_let_statements`) has no real-GAUSS evidence, and the v0.82 plan lists no member case.
Identical on v0.84.0.

Attempt 2 (literal assigned to `x`, then `myData.dataMatrix = x;`): `review_required`; gaps `control_flow_block`,
`dsMean` `call_undocumented`, `meanc` arg 1 `argument_expression` (`d.dataMatrix`). Agree; explained correctly.
v0.84.0 gives attempt 2 **not_ready** (the 74.18 header defect on `proc (1) = dsMean(struct DS d);`), so v0.85.0
finding 1 shows live here too. Real GAUSS: attempt 2 prints `3 6`.

Expected behavior: Valid GAUSS is never a syntax INVALID.

Observed behavior: **Real defect found live: a false INVALID** whose reason states a GAUSS rule that does not
exist; the client relayed it to the user as fact. Pre-existing since v0.82.0, safe direction (no execution offer).
Reach: any brace literal assigned to a structure member, which is the usual way to set a control structure's vector
member (75.18 hit it again).

Pass/fail: Fail
Defect severity: Moderate (false INVALID with a false explanation; pre-existing since v0.82.0; safe direction)
Remediation: Next milestone: restrict `let_statement_shape` to indexed targets (its evidence), with sc01-sc03 as provenance for allowing member targets.

Overall Score: 2.5
Decision: Fail — real defect
