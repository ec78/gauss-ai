# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.16
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Sort a matrix by its second column."

Searches:
```
search_docs("sortc") -> grounded: sortc.rst
```
The client searched `sortc` by name (prior knowledge). The user's own wording, re-run by the recording session, is
ungrounded and never offers `sortc` (candidates date.rst, sortmc.rst, sortrsortrc.rst, sumc.rst): the known 73.12 recall
gap, identical on both archives.

Code (S16): `x = {4 7 3, 1 3 2, 3 4 8, 2 9 5}; y = sortc(x, 2); print y;`

Captured output: **`handoff_candidate`**, no gaps; `validation_id` ede93f4f1aee4ed5a3faeacd19712d73 (never prepared:
not asked to run; opt-in absent).

Diagnosis (direct `validate_code`): identical. v0.85.0: identical in every field.

Real GAUSS (S16 verbatim): rows `1 3 2 / 3 4 8 / 4 7 3 / 2 9 5`, as the client said.

Expected behavior: handoff_candidate; correct answer.

Observed behavior: As expected; the query was steered by prior knowledge around a known recall gap.

Pass/fail: Pass
Defect severity: None (known search gap)
Remediation: None (v0.87.0 search milestone).

Overall Score: 3.6
Decision: Pass
