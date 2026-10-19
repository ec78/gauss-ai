# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.2
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Write a procedure that takes a DS structure and returns the column means of its data member. Use a small 3x2 matrix as the data."

Searches:
```
search_docs("dsCreate DS structure") -> grounded: dscreate.rst, user-guide/advanced/structures.rst
search_docs("meanc") -> grounded: meanc.rst
```
Both named functions directly (prior knowledge). The declaration `struct DS myData;` follows `dscreate.rst`'s example
(and the auto-loaded memory note on GAUSS 26 declarations).

Code (S01):
```gauss
proc (1) = dsColMeans(struct DS d);
    retp(meanc(d.dataMatrix));
endp;

struct DS myData;
myData = dsCreate();
myData.dataMatrix = { 1 2,
                      3 4,
                      5 6 };

mu = dsColMeans(myData);
print mu;
```

Captured output: `review_required`; coverage_gaps: syntax `unmodelled_construct` (control_flow_block); signature
`dsColMeans` `call_undocumented`; `meanc` arg 1 `argument_expression` (`d.dataMatrix`). No syntax issue.

Diagnosis (direct `validate_code`): identical. coverage: signature partial, parameter roles unknown, syntax partial.
`parameter_role_checks`: one, `meanc` x, `unresolved`/`argument_expression`. **The gaps the client saw agree**, and its
explanation of each was right.

v0.85.0, same snippet: **not_ready**, syntax INVALID `let_statement_shape` on `myData.dataMatrix = {...}` (75.x
finding 1). v0.86.0 finding 1 confirmed live.

Real GAUSS (recording session, S01 verbatim): prints `3.0000000 4.0000000`, as the client said.

Expected behavior: A member literal is not INVALID; the `proc` keeps it at review_required.

Observed behavior: As expected.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
