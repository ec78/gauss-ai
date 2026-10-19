# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation; the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session (handoff runs 07:07-07:26). During the tasks the session read no source, no planning doc, neither PROJECT_STATUS.md nor KNOWN_LIMITATIONS.md, and no `.rst` page outside `gauss_search_docs` (v0.86 plan §12.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `18f6470`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0).
Prompt ID: 77.3
Prompt Category: MCP Execution Re-evaluation of v0.86.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`; workspace_parent = `C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**, proven before any task by one `gauss_execution_prepare` that returned a `rendered_prompt` (77.1; 76.x finding 1 is fixed). Session cef3f6beb0d34a8289e2432eb0709fb2. Two `gauss-ai-mcp` processes were running (PIDs 33504 and 35604, started 06:54:51 and 06:56:40); which one served this session was not determined. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 22 live verdicts reproduced exactly on the v0.86.0 archive (state, every gap, and `code_sha256` for the six that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs (all but S15, a file write) and spot checks x01-x07, from a scratch directory. Handoff runs through MCP: four approved (77.9, 77.11, 77.16, 77.17), one declined (77.10).
Prompt Text:

"Minimize (b1 - 3)^2 + (b2 + 1)^2 with sqpSolveMT, starting from 0, 0, with both parameters bounded between -5 and 5."

Searches:
```
search_docs("sqpSolveMT") -> grounded: sqpsolvemt.rst (excerpt truncated at ctl.eqProc)
search_docs("sqpSolveMTControlCreate bounds") -> grounded: sqpsolvemtcontrolcreate.rst; `bounds` ambiguous; candidates mlmt-ug-bounds, optmt-ug-bounds, optmt-bounds-example
search_docs("sqpSolveMT ctl.bounds member") -> partially_grounded: sqpsolvemt.rst; `ctl`, `member` unmatched; same three candidates
search_docs("pvPack pvUnpack pvCreate") -> grounded: pvpack.rst, pvunpack.rst, pvcreate.rst
```
The client did not follow the candidates (OPTMT/MLMT pages, not sqpSolveMT) and said `ctl.bounds`,
`sqpSolveMTout` and its members came from prior knowledge.

Code (S02):
```gauss
proc (1) = objFn(struct PV p);
    local b;
    b = pvUnpack(p, "b");
    retp((b[1] - 3)^2 + (b[2] + 1)^2);
endp;

struct PV p0;
p0 = pvCreate();
p0 = pvPack(p0, 0|0, "b");

struct sqpSolveMTControl ctl;
ctl = sqpSolveMTControlCreate();
ctl.bounds = { -5 5, -5 5 };

struct sqpSolveMTout out;
out = sqpSolveMT(&objFn, p0, ctl);

print "Estimates:";
print pvUnpack(out.par, "b");
print "Function value:";
print out.fct;
print "Return code:";
print out.retcode;
```

Captured output: **review_required**; gaps: `control_flow_block`; `pvUnpack` arg 1 `argument_untraced` (`p`,
a `proc` parameter); `pvPack` arg 2 `argument_expression` (`0|0`); `sqpSolveMT` arg 1 `documented_type_missing`
(`&fct`); arg 3 `variadic_position`; `pvUnpack` arg 1 `argument_expression` (`out.par`). No issues.

Diagnosis (direct `validate_code`): identical. Client explanation right; it flagged the `&fct` gap as a
possible defect to check against the disclosed v0.83.0 `&`-parameter gap, which it is (KL v0.83.0).

v0.85.0, same snippet: not_ready, syntax INVALID (`let_statement_shape` on `ctl.bounds = {…}`, line 13).

Real GAUSS (S02): estimates `2.9999999 -0.99999998`, function value `4.8170459e-15`, return code `0`, as predicted.

Expected behavior: review_required with the disclosed `&` and `...` gaps; a correct program.

Observed behavior: As expected (= 76.3).

Pass/fail: Pass
Defect severity: None (known limitations)
Remediation: None.

Overall Score: 4.0
Decision: Pass
