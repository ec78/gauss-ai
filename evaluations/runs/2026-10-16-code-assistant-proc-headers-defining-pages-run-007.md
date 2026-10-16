# Evaluation Result

Date: 2026-10-16
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. All twenty-one tasks ran on 2026-10-16 in one server session. The session did not read the planning doc, PROJECT_STATUS.md or any source until all tasks were done.
Agent Version: v0.85.0 (released; tag `v0.85.0`, commit `f11505e`; HEAD `d634b40`, whose `scripts/` is identical to the tag), editable install of this checkout (`pip show gauss-ai` = 0.85.0). The live server's own output carries v0.85.0-only behavior (`library` -> `source_inclusion` in 75.3/75.6; a typed `struct` procedure header is no longer INVALID in 75.2; `miss` keeps its signature in 75.4).
Prompt ID: 75.7
Prompt Category: Procedure Headers and Defining Pages (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.85.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session d965dee780a44d0e8faacbdafbd0eaad. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.85.0 and v0.84.0 (`d19c61c`); every live verdict reproduced exactly on the v0.85.0 archive. Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) programs run by the recording session from a scratch directory, including the client's own programs. No `gauss_execution_prepare` call was made.
Prompt Text:

"Can GAUSS call a function from a C DLL I wrote?"

Searches:
```
search_docs("dlibrary dllcall") -> grounded (prior knowledge); the dllcall excerpt stops before its remarks on the C
    interface
```
The user's literal wording (recording-session re-run) is partially grounded on `call.rst` only, through the English
word "call"; `dlibrary`/`dllcall` are never reached.

Code: `dlibrary mylib;`, then `dllcall -r myfunc(x, n, result);` with a matching C function.

**The client did not validate the snippet.** It told the user "the validator always blocks that" without calling
`gauss_validate_code`. Recording-session diagnosis: v0.85.0 is `not_ready` with `dlibrary` (line 2) and `dllcall`
(line 12) as `native_code`, plus `myfunc` `call_undocumented`, so the claim was true. On v0.84.0 the same snippet is
not_ready only because `myfunc` is unknown (no system statement). v0.85.0 decision 4 confirmed.

Observed behavior: Correct and docs-grounded for `dlibrary`/`dllcall` (search order, `-a`/`-d`, plain-variable
arguments, `-r`/`-v`/`-o`); the C calling convention came from prior knowledge, and the client said so.

Pass/fail: Pass with limitation disclosed
Defect severity: Minor (the client asserted a verdict it had not requested)
Remediation: None for gauss-ai.

Overall Score: 3.6
Decision: Pass with limitation disclosed
