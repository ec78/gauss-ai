# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation; the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session (handoff runs 07:07-07:26). During the tasks the session read no source, no planning doc, neither PROJECT_STATUS.md nor KNOWN_LIMITATIONS.md, and no `.rst` page outside `gauss_search_docs` (v0.86 plan §12.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `18f6470`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0).
Prompt ID: 77.4
Prompt Category: MCP Execution Re-evaluation of v0.86.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`; workspace_parent = `C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**, proven before any task by one `gauss_execution_prepare` that returned a `rendered_prompt` (77.1; 76.x finding 1 is fixed). Session cef3f6beb0d34a8289e2432eb0709fb2. Two `gauss-ai-mcp` processes were running (PIDs 33504 and 35604, started 06:54:51 and 06:56:40); which one served this session was not determined. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 22 live verdicts reproduced exactly on the v0.86.0 archive (state, every gap, and `code_sha256` for the six that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs (all but S15, a file write) and spot checks x01-x07, from a scratch directory. Handoff runs through MCP: four approved (77.9, 77.11, 77.16, 77.17), one declined (77.10).
Prompt Text:

"Estimate a simple linear IV model with gmmFit on simulated data, and set the starting values in the control structure."

Searches:
```
search_docs("gmmFit") -> grounded: gmmfit.rst
search_docs("gmmControlCreate start values") -> partially_grounded: gmmfitcontrolcreate.rst (example declares `struct gmmFitControl c;`); `start`, `values` unmatched
```

Code (S03):
```gauss
proc (1) = ivMoments(b, y, x, z);
    local e;
    e = y - x * b;
    retp(z .* e);
endp;

rndseed 8675309;
n = 500;
z1 = rndn(n, 1);
z2 = rndn(n, 1);
u = rndn(n, 1);
v = 0.5 * u + rndn(n, 1);
x1 = 0.8 * z1 + 0.6 * z2 + v;
y = 1 + 2 * x1 + u;

x = ones(n, 1) ~ x1;
z = ones(n, 1) ~ z1 ~ z2;

struct gmmFitControl gCtl;
gCtl = gmmControlCreate();
gCtl.bStart = { 0, 0 };

struct gmmOut gOut;
gOut = gmmFit(&ivMoments, y, x, z, gCtl);
```

Captured output: **review_required**; gaps: `control_flow_block`; `gmmFit` arg 1 `documented_type_missing`
(`&fct`); arg 2 `argument_assigned_from_expression` (`y`); args 3-5 `variadic_position`. No issues.

Diagnosis (direct `validate_code`): identical. Client explanation right. It told the user the docs "confirmed"
`gmmControlCreate`, "whose example declares `struct gmmFitControl`", and wrote that declaration. That is a
faithful reading of the published page, but the page is wrong upstream (75.x finding 8; 76.x e03).

v0.85.0, same snippet: not_ready, syntax INVALID (`let_statement_shape` on `gCtl.bStart = {…}`, line 21).

Real GAUSS (S03): **fails at compile time**: `G0507 Undefined structure 'gmmFitControl gCtl'` (line 19), then
G0008 ×2. Spot check x01 (the same program with `struct gmmControl gCtl;`) runs: GMM table, `paramEst`
`1.0165 1.9982` (true values 1 and 2), so the docs' structure name is the program's only error. The validator
cannot see it: structure types are not modelled (KL v0.86.0).

Expected behavior: review_required with the disclosed gaps; a working program.

Observed behavior: Verdict as expected. The program fails on the documented-but-nonexistent `gmmFitControl` (known upstream doc error, 75.x finding 8), which the client presented as docs-confirmed.

Pass/fail: Pass with defect recorded
Defect severity: Minor (upstream docs; known)
Remediation: None in gauss-ai (structure types out of scope, KL v0.86.0). Reporting `gmmfitcontrolcreate.rst` upstream remains the user's choice.

Overall Score: 3.0
Decision: Pass
