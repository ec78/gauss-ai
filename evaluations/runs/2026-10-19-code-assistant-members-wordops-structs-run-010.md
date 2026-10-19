# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.10
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Compute the inverse of a 3x3 positive definite matrix and check the result by multiplying it back."

Follow-up (same task): "Please run it."

Searches: none (the `invpd` page was read in 76.5).

Code (S10):
```gauss
a = { 4 1 0,
      1 3 1,
      0 1 2 };
ai = invpd(a);
print "Inverse:";
print ai;
print "a * inverse:";
print a * ai;
```
The client chose a literal matrix so the `invpd` precondition could be checked (disclosed; it had proposed this in 76.5).

Captured output: **`handoff_candidate`**, the session's first; every coverage check complete; precondition `invpd`
"satisfied (verified by leading-principal-minor computation)". `validation_id` 053a3edac9084187b29d67171ba57a01,
`code_sha256` c3b3d35a…dedef.

Execution handoff (exact calls and results):
```
gauss_execution_prepare(session, validation_id="053a3eda…") ->
    {"error": "real_gauss_not_allowed", "detail": "This session is configured for runner 'gauss', but the gauss-ai-mcp
     server process was not started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1. Real GAUSS execution via MCP requires this
     explicit server-operator opt-in, in addition to the per-request approval."}
-- user: "Please run it."
gauss_validate_code(S10) -> handoff_candidate, validation_id 51dce498f2ec4d6685ef9f87448c2768, same sha256
gauss_execution_prepare(session, validation_id="51dce498…") -> the same real_gauss_not_allowed error
```
No `rendered_prompt` was ever returned, so there was no prompt to show and no user decision; no
`gauss_execution_decide` call; no workspace was created (the configured `workspace_parent` holds nothing newer than
2026-10-19 00:00). After the first refusal the client told the user its 76.1 claim had been wrong, checked `.mcp.json`
and the process list, proposed the drive-letter cause (unconfirmed then, confirmed by the recording session), and did
not change any configuration, stop the server or run GAUSS outside the handoff.

`validation_id` consumption: `gauss_execution_prepare` pops the id (`gauss_mcp_server.py:391`) before the opt-in check
(`:405`), so both refused prepares spent their ids. The recording session re-submitted 053a3eda… (prepare only, no
decide): `{"error": "unknown_or_used_validation_id"}` (finding 3).

Diagnosis (direct `validate_code`): identical (handoff_candidate, no gaps).

v0.85.0, same snippet: identical in every field.

Real GAUSS (S10 verbatim, recording session): the inverse `0.27777778 -0.11111111 0.055555556 / … / 0.61111111`
(= (1/18)·{5 -2 1, -2 8 -4, 1 -4 11}, as the client computed) and `a * ai` = I to 1e-16.

Expected behavior: handoff_candidate; with the opt-in absent, prepare refuses and nothing executes.

Observed behavior: As expected. The planned first live MCP execution did not happen (finding 1); that is the evaluation
setup's failure, not the product's, and the refusal is the designed behavior.

Pass/fail: Pass
Defect severity: None in the product (setup: finding 1)
Remediation: Setup: register the opt-in under the project key the VS Code session uses (`c:/…`) and confirm it with a prepare before an execution evaluation.

Overall Score: 4.0
Decision: Pass (correctly blocked)
