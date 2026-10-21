# Evaluation Result

Date: 2026-10-21
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`c60c77d5…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All thirteen tasks ran on 2026-10-21, 19:10-19:30 local (23:10-23:30 UTC). During the tasks the client read GAUSS documentation files and the installed package's `package.json` directly from disk, but no gauss-ai source file, `KNOWN_LIMITATIONS.md`, `PROJECT_STATUS.md` or planning doc; `CLAUDE.md` and one memory note were in its context from the start (v0.88 plan §11.7).
Agent Version: v0.88.0 (released: tag `v0.88.0`, commit `be3df16`, pushed and published on GitHub at 18:57 local, before the tasks), editable install of this checkout (`gauss-ai version` = 0.88.0).
Prompt ID: 79.4
Prompt Category: MCP Search and Grounding Recall of v0.88.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.88.0 over stdio (two `gauss-ai-mcp.exe` processes, PIDs 34308 and 17696, both started 19:09:47 local, after the v0.88.0 install at 19:04:56; which one served the conversation was not determined, but every response carries v0.88.0-only fields such as `omitted_topics` and the `derived_from_docs`/`statement_page`/`non_defining_page` candidate origins). Real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). One server session (`4120e487…`) served all tasks; `gauss_session_start` reported `real_gauss_allowed: true`, and 79.1's prepare rendered a prompt. The client model wrote every query and snippet itself. Post-run: the recording session (the same conversation, after the tasks) re-ran every search query and snippet by calling each archive's own `gauss_mcp_server` tool functions on `git archive`s of v0.88.0 (`be3df16`) and v0.87.0 (`4103280`), each archive's modules asserted imported. **All 24 live responses (13 searches, 11 validations) are identical to the v0.88.0 re-run in every field** (excerpt text, candidates, reasons, gaps, `code_sha256`; `validation_id` aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) runs of every client snippet except 79.4's `dllcall` (its DLL does not exist), each from its own new empty directory.
Prompt Text:

"Can GAUSS call a function from a C DLL I wrote?"

Search `dlibrary dllcall` (live, identical on the v0.88.0 re-run): **grounded**
- sources: `dlibrary` (dlibrary.rst), `dllcall` (dllcall.rst)
- unmatched: none; ambiguous: none
- v0.87.0, same query: identical

The excerpts stopped before `dllcall`'s rules for the C side, so the client read the Remarks of `dllcall.rst` directly from the docs directory on disk (not through the tool).

Code (call #16):
```gauss
// Link mylib.dll (searched in the default dynamic library directory)
dlibrary mylib;

x = rndn(100, 1);
n = rows(x);
k = 2.5;

// Preallocate the output: the C function writes into it
out = zeros(n, 1);

// -r: fail if the C function returns nonzero
dllcall -r scalevec(x, n, k, out);

print out[1:5];
```

Captured output (live, reproduced exactly on v0.88.0): **not_ready**; preconditions: none.
Reasons: "line 2: `dlibrary` is a system-touching statement (native_code) -- controlled execution only runs self-contained snippets that compute in memory"; "line 12: `dllcall` is a system-touching statement (native_code) -- controlled execution only runs self-contained snippets that compute in memory"
Coverage gaps: signature/scalevec `call_undocumented`
System statements: `dlibrary` (native_code, line 2); `dllcall` (native_code, line 12)
v0.87.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): not run: `mylib.dll` does not exist, and calling it would test only the missing file.

Expected behavior: `dllcall`/`dlibrary` ground as code-marked symbols, not via the `call` statement page (v0.88 §9.4: "the C-DLL question loses `call.rst`"); `dlibrary`/`dllcall` are `native_code`, so not_ready.

Observed behavior: Grounded on both pages, identical on v0.87.0 (the query named them). not_ready for the two `native_code` statements plus the user-defined `scalevec` (unknown symbol, `call_undocumented` gap): correct, and the client explained all three. The C-side contract (int return, `double *` arguments, by-reference outputs, `-r`/`-v`/`-o` flags, the 100/1000 argument limits) was quoted from the page. The client flagged its row-major layout claim as unverified by the excerpt it read.

Search: **steered by prior knowledge**: the client searched `dlibrary dllcall` instead of the user's question. A recording-session probe of the question itself was not made; v0.88 §9.4 records that the plain C-DLL question no longer grounds `call.rst`. The 1,500-character excerpt was not enough for this answer, so the client read the page file itself.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 3.8
Decision: Pass
