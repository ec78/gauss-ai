# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.14
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Write a procedure that takes a pointer to a structure I define and doubles one of its matrix members."
(sent in one message with 76.15; the client handled the two separately)

Searches: none through the tool; the client read the structures guide's "Structure Pointers" section (lines 506-565:
`proc (0) = setDefaults(struct myModelControl *p); p->maxIters = 100; … setDefaults(cp);`).

Code (S14): `struct myData { matrix x; string label; };` `proc (0) = doubleX(struct myData *p); p->x = 2 * p->x; endp;`
then `s.x = {1 2, 3 4}; s.label = "example"; struct myData *sp; sp = &s; doubleX(sp); print s.label; print s.x;`

Captured output: **`not_ready`**, "no documented GAUSS function call was found to ground this code against"; gaps:
`control_flow_block`, `doubleX` `call_undocumented`.

Diagnosis (direct `validate_code`): identical. The code calls no library function, so not_ready under the v0.80.0
no-documented-call policy is its true reason. The client explained it as designed behavior and **declined to add a
gratuitous library call to improve the verdict**.

v0.85.0, same snippet: not_ready, with false syntax INVALIDs as well (`matrix_literal_row_separator` on the definition,
`let_statement_shape` on `s.x = {...}`). v0.86.0 removes both; the state is unchanged.

Real GAUSS (S14 verbatim): `example`, `2 4 / 6 8`, as the client said.

Expected behavior: not_ready for the true reason; no false syntax issue.

Observed behavior: As expected.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
