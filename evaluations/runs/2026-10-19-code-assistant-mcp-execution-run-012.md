# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation; the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session (handoff runs 07:07-07:26). During the tasks the session read no source, no planning doc, neither PROJECT_STATUS.md nor KNOWN_LIMITATIONS.md, and no `.rst` page outside `gauss_search_docs` (v0.86 plan §12.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `18f6470`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0).
Prompt ID: 77.12
Prompt Category: MCP Execution Re-evaluation of v0.86.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`; workspace_parent = `C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**, proven before any task by one `gauss_execution_prepare` that returned a `rendered_prompt` (77.1; 76.x finding 1 is fixed). Session cef3f6beb0d34a8289e2432eb0709fb2. Two `gauss-ai-mcp` processes were running (PIDs 33504 and 35604, started 06:54:51 and 06:56:40); which one served this session was not determined. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 22 live verdicts reproduced exactly on the v0.86.0 archive (state, every gap, and `code_sha256` for the six that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs (all but S15, a file write) and spot checks x01-x07, from a scratch directory. Handoff runs through MCP: four approved (77.9, 77.11, 77.16, 77.17), one declined (77.10).
Prompt Text:

"Create an array of 3 DS structures, give each one its own small data matrix, and print the mean of each."

Searches:
```
search_docs("array of structures reshape struct instance") -> partially_grounded: structures guide, reshape.rst, arrays guide; `struct` unmatched
search_docs("vecr vec") -> grounded: vecvecr.rst
```
`reshape` of a structure came from prior knowledge, disclosed (`reshape.rst` documents an NxK matrix).

Code (S12):
```gauss
struct DS d;
d = dsCreate();
d = reshape(d, 3, 1);

d[1].dataMatrix = { 1 2, 3 4 };
d[2].dataMatrix = { 10 20 30, 40 50 60 };
d[3].dataMatrix = { 0.5, 1.5, 2.5, 3.5 };

for i(1, 3, 1);
    print "Mean of structure " i ":";
    print meanc(vecr(d[i].dataMatrix));
endfor;
```

Captured output: **review_required**; `reshape` arg 1 `argument_untraced` (`d` has two assignments);
`meanc` arg 1 and `vecr` arg 1 `argument_expression` (`vecr(d[i].dataMatrix)`, `d[i].dataMatrix`).
Syntax validated (the `for` loop is a modelled `for_block`). No issues.

Diagnosis (direct `validate_code`): identical. The client was right that the `for … endfor` loop is modelled
while `proc … endp` is not (v0.82.0's scope), and right that the struct-into-`reshape` type is never compared
because the argument is untraced. (76.13's client had said loops can't be validated.)

v0.85.0, same snippet: not_ready, syntax INVALID (`let_statement_shape` ×3, lines 5-7).

Real GAUSS (S12): `2.5`, `35`, `2`, as predicted; `reshape` of a structure works (= 76.x e05).

Expected behavior: Member-target literals on structure-array elements are not INVALID; review_required.

Observed behavior: As expected (= 76.13, without the client misstatement).

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
