# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.8
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Recode a vector so that values from 20 up to 30 become 1, above 30 up to 40 become 2, and everything else becomes 0."

Searches:
```
search_docs("recode") -> grounded: recode.rst (example uses bins (20, 30] and (30, 40]; "If every column of e contains a
    0, the original value of x will be unchanged")
```

Code (S08): `x = {15, 20, 25, 30, 30.5, 40, 41, 8, 35};` `e1 = (x .>= 20) .and (x .<= 30);`
`e2 = (x .> 30) .and (x .<= 40);` `e3 = .not (e1 .or e2);` `e = e1 ~ e2 ~ e3; v = {1, 2, 0}; y = recode(x, e, v);`

The client added `e3` (-> 0) because the docs say unmatched rows keep their value, and disclosed its reading of
"from 20" as inclusive (the docs example uses `20 < x`).

Captured output: `review_required`; one gap, `recode` arg 2 `argument_assigned_from_expression` (`e`).

Diagnosis (direct `validate_code`): identical; `recode` args 1 and 3 are `traced_literal` matches. **The gap agrees.**

v0.85.0, same snippet: **not_ready**: `not` an unknown call, `and` `signature_not_extracted`, and a false syntax INVALID
`call_argument_missing_separator` ("call to `not` … (`e1 .or e2`)"). v0.86.0 finding 2 confirmed live, including the
`.not (` and in-argument forms.

Real GAUSS (S08 verbatim): `0 1 1 1 2 2 0 0 2`, as the client said.

Expected behavior: word operators (`.and`, `.or`, `.not (`) are operators.

Observed behavior: As expected.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
