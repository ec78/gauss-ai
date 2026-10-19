# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.18
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"What happens in GAUSS if I assign a matrix literal to a scalar member of a structure?"

Searches:
```
search_docs("structure member type mismatch error assigning matrix to scalar") -> partially_grounded: type.rst,
    user-guide/advanced/structures.rst; `member`, `mismatch` unmatched
```
The client also grepped and read the structures guide's member-type table (lines 134-183: "`scalar` — A single numeric
value. This type is unique to structures"), and **grepped `scripts/gauss_error_catalog.py`, a source file**, for a
structure entry (none). It then probed the validator with S18:

```gauss
struct counter {
    scalar count;
    matrix data;
};
struct counter c;
c.count = { 1 2,
            3 4 };
print c.count;
```

Captured output: `not_ready` (no documented call only); syntax `validated`; nothing about the scalar member.

Answer given: neither the docs nor the error catalog say; "my guess is a type error … I'm not confirming that or naming
an error code without evidence"; the validator does not check member types, recorded as a possible gap to check against
`KNOWN_LIMITATIONS.md` and the v0.86.0 plan before calling it a defect; a `tgauss.exe -b` spot check offered only on an
explicit yes.

Recording session: the gap is disclosed (v0.86.0 plan §5, m12; `KNOWN_LIMITATIONS.md`: "a brace literal assigned to a
`scalar` member (`G0071 Type mismatch`)"). Real GAUSS (S18 and spot check e01): `G0071 : Type mismatch 'COUNT'`, then a
cascade `G0025 Undefined symbol 'c'`; e02 (`c.count = 7;`) prints 7. So the answer to the user's question is a
compile-time `G0071`, which the client did not know and did not invent.

v0.85.0, same snippet: not_ready, with false INVALIDs (`matrix_literal_row_separator`, `let_statement_shape`).

Expected behavior: answer from evidence or say it is unknown; no invented error code.

Observed behavior: An honest "not documented" answer; the disclosed limitation was not found because the client did not
read `KNOWN_LIMITATIONS.md` during the tasks.

Pass/fail: Pass with limitation disclosed
Defect severity: None (known limitation)
Remediation: None.

Overall Score: 3.5
Decision: Pass with limitation disclosed
