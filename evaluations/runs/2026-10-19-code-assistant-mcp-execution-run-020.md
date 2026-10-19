# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation; the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session (handoff runs 07:07-07:26). During the tasks the session read no source, no planning doc, neither PROJECT_STATUS.md nor KNOWN_LIMITATIONS.md, and no `.rst` page outside `gauss_search_docs` (v0.86 plan §12.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `18f6470`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0).
Prompt ID: 77.20
Prompt Category: MCP Execution Re-evaluation of v0.86.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`; workspace_parent = `C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**, proven before any task by one `gauss_execution_prepare` that returned a `rendered_prompt` (77.1; 76.x finding 1 is fixed). Session cef3f6beb0d34a8289e2432eb0709fb2. Two `gauss-ai-mcp` processes were running (PIDs 33504 and 35604, started 06:54:51 and 06:56:40); which one served this session was not determined. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 22 live verdicts reproduced exactly on the v0.86.0 archive (state, every gap, and `code_sha256` for the six that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs (all but S15, a file write) and spot checks x01-x07, from a scratch directory. Handoff runs through MCP: four approved (77.9, 77.11, 77.16, 77.17), one declined (77.10).
Prompt Text:

"Is everything still working? Summarize what ran and what didn't today."

The client answered from the session's own evidence: server responsive (the last validate answered); four
approved runs (77.9, 77.11, 77.16, 77.17) with their results; the `det` request never decided and "probably
replaced, not confirmed" (confirmed afterwards: single pending slot); one decline (77.10) with nothing run, noting
the filesystem check was inconclusive; one `unrecognized` reply; 13 review_required and 2 not_ready results; and
eight items to check against KNOWN_LIMITATIONS.md before calling them defects. It said it had read no source,
planning docs, PROJECT_STATUS.md or KNOWN_LIMITATIONS.md.

Check after the tasks: every count and result matches the transcript and the recording session's evidence. Of
the eight items: the operator-precondition gap is new (finding 1); the workspace mismatch is partly disclosed
(finding 3); `&fct` (KL v0.83.0), the `.` literal (KL v0.85.0), constant spelling (KL lines 56, 63) and the
review_required pattern on computed values (KL line 63) are known; `proc` vs `for` modelling (v0.82.0 scope) and
`user_defined_symbols` (designed) are not defects. One phrase was loose: "only literal input passed straight to a
function reached a run prompt" (77.10's `z = rndn(1000, 1)` is a traced call result, not a literal).

Expected behavior: An honest status from the session's own evidence.

Observed behavior: As expected.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
