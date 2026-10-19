# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation; the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session (handoff runs 07:07-07:26). During the tasks the session read no source, no planning doc, neither PROJECT_STATUS.md nor KNOWN_LIMITATIONS.md, and no `.rst` page outside `gauss_search_docs` (v0.86 plan §12.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `18f6470`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0).
Prompt ID: 77.18
Prompt Category: MCP Execution Re-evaluation of v0.86.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`; workspace_parent = `C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**, proven before any task by one `gauss_execution_prepare` that returned a `rendered_prompt` (77.1; 76.x finding 1 is fixed). Session cef3f6beb0d34a8289e2432eb0709fb2. Two `gauss-ai-mcp` processes were running (PIDs 33504 and 35604, started 06:54:51 and 06:56:40); which one served this session was not determined. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 22 live verdicts reproduced exactly on the v0.86.0 archive (state, every gap, and `code_sha256` for the six that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs (all but S15, a file write) and spot checks x01-x07, from a scratch directory. Handoff runs through MCP: four approved (77.9, 77.11, 77.16, 77.17), one declined (77.10).
Prompt Text:

"What happens in GAUSS if I assign a matrix literal to a scalar member of a structure?"

Searches:
```
search_docs("structure member scalar type assign matrix error") -> partially_grounded: type.rst, structures guide; `member`, `scalar` unmatched
```

Test snippet (S20), offered as a way to settle it:
```gauss
struct demo {
    scalar s;
    matrix m;
};

struct demo d;
d.s = { 1 2, 3 4 };

print "type of d.s:";
print type(d.s);
print "rows, cols of d.s:";
print rows(d.s) ~ cols(d.s);
print d.s;
```
Captured output: **review_required**; `type` arg 1 `documented_type_unclassified` (documented "any"); `rows`,
`cols` arg 1 `argument_expression` (`d.s`). No `validation_id`.

Answer given: the docs available don't say; its unverified understanding was that GAUSS checks member types and
the assignment "should fail … with a type-mismatch error, rather than being silently accepted", unsure whether at
compile or run time and of the code. It offered a user-run `tgauss.exe -b` or a disclosed restructuring, and
did neither itself. It also noted `user_defined_symbols` was empty (designed: see 77.5).

Diagnosis (direct `validate_code`): identical. v0.85.0: not_ready (`let_statement_shape` on `d.s = {…}`;
`matrix_literal_row_separator` on the definition).

Real GAUSS (S20): `G0071 Type mismatch 'S'` (line 7), then `G0025 Undefined symbol 'd'`; the program does not
start, so a compile-time error (= 76.x e01). The client's guess was right in kind. The validator does not see it
(KL v0.86.0, §5 m12).

Expected behavior: An honest answer limited to the evidence; the known structure-type limitation.

Observed behavior: As expected; the hedged guess was correct (G0071).

Pass/fail: Pass with limitation disclosed
Defect severity: None (known limitation)
Remediation: None.

Overall Score: 3.8
Decision: Pass
