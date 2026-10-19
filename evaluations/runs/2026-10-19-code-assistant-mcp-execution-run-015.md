# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation; the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session (handoff runs 07:07-07:26). During the tasks the session read no source, no planning doc, neither PROJECT_STATUS.md nor KNOWN_LIMITATIONS.md, and no `.rst` page outside `gauss_search_docs` (v0.86 plan §12.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `18f6470`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0).
Prompt ID: 77.15
Prompt Category: MCP Execution Re-evaluation of v0.86.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`; workspace_parent = `C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**, proven before any task by one `gauss_execution_prepare` that returned a `rendered_prompt` (77.1; 76.x finding 1 is fixed). Session cef3f6beb0d34a8289e2432eb0709fb2. Two `gauss-ai-mcp` processes were running (PIDs 33504 and 35604, started 06:54:51 and 06:56:40); which one served this session was not determined. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 22 live verdicts reproduced exactly on the v0.86.0 archive (state, every gap, and `code_sha256` for the six that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs (all but S15, a file write) and spot checks x01-x07, from a scratch directory. Handoff runs through MCP: four approved (77.9, 77.11, 77.16, 77.17), one declined (77.10).
Prompt Text:

"Save a matrix of results to a file called results.fmt."

Searches:
```
search_docs("save matrix to .fmt file") -> partially_grounded: save.rst; `fmt`, `file` unmatched; whole query ambiguous; 8 candidates (colsf, datasave, plotsave, readr, rowsf, saveall, saveStruct, savewind)
```
The client used `save.rst` (grounded) and cited the `rowsf`/`colsf`/`readr` candidates' purpose lines for
".fmt = GAUSS matrix file"; it did not search a candidate's name.

Code (S15):
```gauss
results = { 1.25 0.30,
           -0.40 0.12,
            2.10 0.55 };

save results;
```

Captured output: **not_ready**: "line 5: `save` is a system-touching statement (file_write) -- controlled execution
only runs self-contained snippets that compute in memory"; also ungrounded (no documented call). No
`validation_id`. The client called the block correct, told the user to run it in GAUSS themselves, and did not
look for a way around it.

Diagnosis (direct `validate_code`): identical. v0.85.0: identical.

The user's own wording, re-run by the recording session (both archives identical): partially_grounded on `save.rst`.

Real GAUSS: not run (a file write is outside the print-only rule).

Expected behavior: not_ready via the system-statement registry (`save`, file_write); nothing written.

Observed behavior: As expected: correctly blocked.

Pass/fail: Pass (correctly blocked)
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
