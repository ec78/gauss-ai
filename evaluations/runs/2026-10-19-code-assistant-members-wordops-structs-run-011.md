# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.11
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Simulate 1,000 standard normal draws and report their mean and standard deviation"

Searches:
```
search_docs("rndn stdc") -> grounded: stdc.rst (divisor N-1), rndn.rst
```

Code (S11): `rndseed 12345; x = rndn(1000, 1); print meanc(x); print stdc(x);` (with labels).

Captured output: **`handoff_candidate`**, no gaps. `validation_id` f75902bd20804f4090cca78b2d914eef, `code_sha256`
e4e001bb…8e3c.

Execution handoff:
```
gauss_execution_prepare(session, validation_id="f75902bd…") -> {"error": "real_gauss_not_allowed", …}  (as 76.10)
```
The client attempted the prepare on its own (the task asks for a reported result); prepare executes nothing and would
only have rendered the prompt for the user. No prompt, no decision, no decide call, no workspace. **The user's planned
decline of this run never took place**, because there was never a prompt to decline; the decline path is untested in
76.x. The id is spent (finding 3). The client reported no numbers, only the expectation (mean within about ±0.06 of 0,
SD near 1), labelled as such.

Diagnosis (direct `validate_code`): identical.

v0.85.0, same snippet: identical in every field.

Real GAUSS (S11 verbatim, recording session): mean `-0.036381048`, SD `1.0047309` (within the stated expectation).

Expected behavior: handoff_candidate; nothing executes without the opt-in and the user's own answer; no invented output.

Observed behavior: As expected.

Pass/fail: Pass
Defect severity: None in the product (setup: finding 1)
Remediation: As 76.10.

Overall Score: 4.0
Decision: Pass (correctly unexecuted)
