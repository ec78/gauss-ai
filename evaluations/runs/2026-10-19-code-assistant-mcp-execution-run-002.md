# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation; the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session (handoff runs 07:07-07:26). During the tasks the session read no source, no planning doc, neither PROJECT_STATUS.md nor KNOWN_LIMITATIONS.md, and no `.rst` page outside `gauss_search_docs` (v0.86 plan §12.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `18f6470`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0).
Prompt ID: 77.2
Prompt Category: MCP Execution Re-evaluation of v0.86.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`; workspace_parent = `C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**, proven before any task by one `gauss_execution_prepare` that returned a `rendered_prompt` (77.1; 76.x finding 1 is fixed). Session cef3f6beb0d34a8289e2432eb0709fb2. Two `gauss-ai-mcp` processes were running (PIDs 33504 and 35604, started 06:54:51 and 06:56:40); which one served this session was not determined. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 22 live verdicts reproduced exactly on the v0.86.0 archive (state, every gap, and `code_sha256` for the six that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs (all but S15, a file write) and spot checks x01-x07, from a scratch directory. Handoff runs through MCP: four approved (77.9, 77.11, 77.16, 77.17), one declined (77.10).
Prompt Text:

"Write a procedure that takes a DS structure and returns the column means of its data member. Use a small 3x2 matrix as the data."

Searches:
```
search_docs("dsCreate DS structure dataMatrix meanc") -> partially_grounded: meanc.rst, dscreate.rst, structures guide; `datamatrix` unmatched
search_docs("DS structure members dataMatrix vnames") -> partially_grounded: structures guide; `members`, `datamatrix`, `vnames` unmatched
```

Code (S01):
```gauss
proc (1) = dsColMeans(struct DS d);
    retp(meanc(d.dataMatrix));
endp;

struct DS myData;
myData = dsCreate();
myData.dataMatrix = { 1 2, 3 4, 5 6 };

print dsColMeans(myData);
```

Captured output: **review_required**; gaps: syntax `control_flow_block` (`unmodelled_construct`); signature
`dsColMeans` `call_undocumented`; `meanc` arg 1 `argument_expression` (`d.dataMatrix`). No issues.
No `validation_id`.

Diagnosis (direct `validate_code`): identical. The client's explanation (the `proc` block, the undocumented
own procedure, the member expression) was right; it disclosed that `dataMatrix` came from prior knowledge,
not from a grounded page.

v0.85.0, same snippet: not_ready, syntax INVALID (`let_statement_shape` on `myData.dataMatrix = {…}`, line 7).

Real GAUSS (S01): `3.0000000 4.0000000`, as predicted.

Expected behavior: A member literal is not INVALID; the `proc` keeps it at review_required.

Observed behavior: As expected (= 76.2).

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
