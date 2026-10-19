# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.3
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Minimize (b1 - 3)^2 + (b2 + 1)^2 with sqpSolveMT, starting from 0, 0, with both parameters bounded between -5 and 5."

Searches:
```
search_docs("sqpSolveMT") -> grounded: sqpsolvemt.rst; excerpt stops inside the ctl table (known: long-page excerpts
    stop before Outputs)
search_docs("sqpSolveMTControlCreate bounds") -> grounded: sqpsolvemtcontrolcreate.rst; `bounds` ambiguous; candidates
    mlmt-ug-bounds, optmt-ug-bounds, optmt-bounds-example (not followed; not sqpSolveMT pages)
search_docs("sqpSolveMTControl bounds member Kx2 matrix; sqpSolveMTout par fct") -> ungrounded; same 3 candidates
search_docs("pvPack pvGetParVector") -> grounded: pvpack.rst, pvgetparvector.rst
```
The `ctl.bounds` member ("1x2 or Kx2 … If 1x2 all parameters have same bounds") and the output members were then read by
grepping `C:/Users/Owner/.gauss-ai/docs/sqpsolvemt.rst` directly, outside the tool (disclosed to the user).

Code (S02, abridged):
```gauss
proc (1) = quadObj(struct PV p);
    local b;
    b = pvUnpack(p, "b");
    retp((b[1] - 3)^2 + (b[2] + 1)^2);
endp;
struct sqpSolveMTControl ctl;
ctl = sqpSolveMTControlCreate();
ctl.bounds = -5 ~ 5;
struct PV par1;
par1 = pvCreate();
par1 = pvPack(par1, 0 | 0, "b");
struct sqpSolveMTout out;
out = sqpSolveMT(&quadObj, par1, ctl);
print pvUnpack(out.par, "b"); print out.fct; print out.retcode;   // (three labelled prints in the original)
```

Captured output: `review_required`; coverage_gaps: syntax `unmodelled_construct`; `pvUnpack` arg 1 `argument_untraced`
(`p`) and `argument_expression` (`out.par`); `pvPack` arg 2 `argument_expression` (`0 | 0`); `sqpSolveMT` arg 1 `&fct`
`documented_type_missing`; arg 3 `variadic_position`.

Diagnosis (direct `validate_code`): identical. **The gaps agree**, and the client explained each correctly, including
that `&fct` is "probably the `&`-parameter gap that v0.83.0 left unfixed on purpose" (it is: `KNOWN_LIMITATIONS.md`,
v0.83.0; the client knew of it from the auto-loaded CLAUDE.md, not from reading the file, which it said it had not checked).

v0.85.0, same snippet: identical in every field (no member literal, word operator or definition in it).

Real GAUSS (S02 verbatim): `2.9999999 -0.99999998`, `fct 4.8e-15`, `retcode 0`; the bounds do not bind, as the client said.

Expected behavior: review_required with the disclosed `&` and `...` gaps; correct program.

Observed behavior: As expected.

Pass/fail: Pass
Defect severity: None (known, disclosed limitations)
Remediation: None.

Overall Score: 4.0
Decision: Pass
