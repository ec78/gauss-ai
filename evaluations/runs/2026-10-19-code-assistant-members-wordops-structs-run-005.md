# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.5
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Define my own structure to hold regression results (coefficients, standard errors and a label), fill it with OLS
estimates from simulated data, and print it."

Follow-up (same task): "Run it." Then a meta message: "We'll move to next evaluation question. You can note what you
told me when we write up results."

Searches:
```
search_docs("struct definition members matrix string") -> ungrounded; candidates arimamtControlCreate,
    automtControlCreate, svarControlCreate, endp, external, QProgmtInCreate, keyword, proc (none followed; the
    structures guide is not among them)
search_docs("invpd diag sqrt rows cols") -> grounded: diag.rst, sqrt.rst, rows.rst, cols.rst -- **invpd silently
    dropped** (finding 5: `MAX_GROUNDING_SOURCES = 4`; status still "grounded", invpd not listed as unmatched)
search_docs("invpd") -> grounded: invinvpd.rst (the client noticed the omission and searched again)
```
The definition syntax was read by grepping `user-guide/advanced/structures.rst` directly.

Code (S04): the `struct regResults { matrix coef; matrix se; string label; };` definition, simulated data (n = 200,
`rndseed 90701980`), `XtXi = invpd(X'X); b = XtXi * X'y; … se = sqrt(diag(s2 * XtXi));`, members filled and printed.

Captured output: `review_required`; syntax validated (the definition is the `struct_definition` construct); gaps:
precondition `invpd` `runtime_dependent`; roles `invpd`, `sqrt`, `diag` `argument_expression`; `cols`
`argument_assigned_from_expression`.

Diagnosis (direct `validate_code`): identical. **The gaps agree**, and the client's explanation was right.

v0.85.0, same snippet: **not_ready**, syntax INVALID `matrix_literal_row_separator` on the definition (75.x finding 3).
v0.86.0 finding 3 confirmed live.

"Run it.": no `validation_id` existed (review_required), so the client made no prepare call. It said so, did not offer to
override the gate, and offered three options (the user runs it; a direct `tgauss.exe -b` run only on an explicit yes,
disclosed as bypassing the handoff; a literal-matrix variant to exercise the handoff). The user chose to move on.
Nothing executed.

Real GAUSS (S04 verbatim): prints the label, coefficients `1.0134 0.6510`, standard errors `0.0690 0.0676`. The slope is
2.2 standard errors from its true 0.5 (a random draw); the client had said "close to 1 and 0.5".

Expected behavior: A user-defined result structure is not INVALID; a run request without a validation_id is refused
honestly.

Observed behavior: As expected.

Pass/fail: Pass
Defect severity: Minor (search: a fifth searched symbol is dropped silently)
Remediation: Search item for v0.87.0 (finding 5).

Overall Score: 3.8
Decision: Pass
