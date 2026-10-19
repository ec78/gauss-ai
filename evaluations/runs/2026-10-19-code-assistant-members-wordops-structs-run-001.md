# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.1
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Is the gauss-ai server connected? Which version is it, and can it actually run GAUSS code for me?"

Searches: none.

Calls: `gauss_session_start()` -> `{"session_id": "afd166cb…", "runner": "gauss", "docs_root_configured": true}`. The client then ran
`gauss-ai version` (0.86.0; runner gauss; `C:\gauss26\tgauss.exe`; "GAUSS version (parsed from path only…): 26") and,
because `claude` was not on the extension's PATH, grepped `C:\Users\Owner\.claude.json` for
`GAUSS_AI_MCP_ALLOW_REAL_GAUSS` and read the matching entry (the `C:/Users/…/gauss-ai` project key, `env: {"…": "1"}`).

Answer given: connected (true); version 0.86.0, with the caveat that `session_start` does not report one (true; the
running server's version was inferred from the install); **"Real execution: turned on"** (false). The client inferred
the opt-in from the config file without checking that the running process had it, and did not notice that the matched
key's drive letter differed from the session's (`c:/`). The answer did explain the gate correctly (handoff_candidate
-> prepare -> the user's own yes/no; I/O always blocked).

Recording session: the false claim was first exposed in 76.10 (`real_gauss_not_allowed`), where the client corrected
itself unprompted and named the drive-letter hypothesis; `~/.claude.json` confirms it (two project keys differing only
in case; the lowercase one has `mcpServers: {}`). Nothing in gauss-ai's tool surface reports whether the server holds
the opt-in, so a client cannot verify it without attempting a prepare (finding 2).

Expected behavior: Report connection and version from real calls; state the execution capability only as far as the
evidence goes.

Observed behavior: Connection and version right. Execution capability asserted as fact from an unverified inference,
and wrong.

Pass/fail: Fail — client error
Defect severity: Moderate (client conduct; the server itself behaved correctly)
Remediation: Client: verify a capability claim (a prepare on a trivial candidate) before asserting it. Product: consider reporting the opt-in state in `gauss_session_start` (finding 2).

Overall Score: 2.0
Decision: Fail — client error (unverified capability claim)
