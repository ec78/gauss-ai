# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation; the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session (handoff runs 07:07-07:26). During the tasks the session read no source, no planning doc, neither PROJECT_STATUS.md nor KNOWN_LIMITATIONS.md, and no `.rst` page outside `gauss_search_docs` (v0.86 plan §12.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `18f6470`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0).
Prompt ID: 77.13
Prompt Category: MCP Execution Re-evaluation of v0.86.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`; workspace_parent = `C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**, proven before any task by one `gauss_execution_prepare` that returned a `rendered_prompt` (77.1; 76.x finding 1 is fixed). Session cef3f6beb0d34a8289e2432eb0709fb2. Two `gauss-ai-mcp` processes were running (PIDs 33504 and 35604, started 06:54:51 and 06:56:40); which one served this session was not determined. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 22 live verdicts reproduced exactly on the v0.86.0 archive (state, every gap, and `code_sha256` for the six that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs (all but S15, a file write) and spot checks x01-x07, from a scratch directory. Handoff runs through MCP: four approved (77.9, 77.11, 77.16, 77.17), one declined (77.10).
Prompt Text:

"Write a procedure that takes a pointer to a structure I define and doubles one of its matrix members."

Searches:
```
search_docs("Structure Pointers -> operator procedure argument") -> partially_grounded: structures guide, address-operator.rst (function pointers, not struct pointers); `pointers` unmatched
```

Code (S13):
```gauss
struct myData {
    matrix x;
    string name;
};

proc (0) = doubleX(struct myData *p);
    p->x = 2 * p->x;
endp;

struct myData s;
s.x = { 1 2, 3 4 };
s.name = "example";

doubleX(&s);

print s.name;
print s.x;
```

Captured output: **not_ready**, ungrounded: "no documented GAUSS function call was found to ground this code
against"; gaps `control_flow_block`, `doubleX` `call_undocumented`; syntax partial.

Diagnosis (direct `validate_code`): identical. The client called it designed behavior and did not add a
gratuitous library call to reach a verdict.

v0.85.0, same snippet: not_ready, plus syntax INVALID (`matrix_literal_row_separator` on the definition, line 1;
`let_statement_shape` on `s.x = {…}`, line 11).

Real GAUSS (S13): `example`, then `2 4 / 6 8`, as predicted.

Expected behavior: not_ready for the true reason (no documented call).

Observed behavior: As expected (= 76.14).

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
