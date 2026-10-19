# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.7
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"From a matrix of daily returns, keep only the rows where the first column is positive and the second column is not missing."

Searches:
```
search_docs("selif") -> grounded: selif.rst
search_docs("test each element for missing value ismiss miss") -> partially_grounded: ismiss.rst (scalar, "1 if x
    contains any missing values"), element-by-element-multiplication.rst; `each` unmatched, `test` ambiguous;
    candidates mvnTest, grangerTest, cdTest (irrelevant)
```
The element-wise form `x .!= miss()` was found only by grepping all docs directly: it appears in the
`coming-to-gauss/intro-gauss-for-{python,r,matlab}-users.rst` guides (`selif(x, x .!= miss())`), which the search tool
did not surface.

Code (S07):
```gauss
r = {  0.012  0.004,
      -0.008  0.010,
       0.005      .,
       0.021 -0.003,
      -0.002      .,
       0.000  0.007,
       0.015  0.001 };
mask = (r[., 1] .> 0) .and (r[., 2] .!= miss());
kept = selif(r, mask);
print kept;
print rows(kept);
```

Captured output: `review_required`; gaps: `selif` arg 1 `argument_assigned_from_expression` (`r`, a literal), arg 2 the
same (`mask`); `rows` arg 1 `return_type_imprecise` (`selif` returns "MxK matrix, dataframe or string array").

Diagnosis (direct `validate_code`): identical. **The gaps agree.** The client guessed that the `.` elements stopped `r`
being read as a literal and said it had not confirmed it. The guess was right: in 76.8/76.15 plain brace literals are
`traced_literal`, and this is the disclosed pre-existing limitation "a matrix literal containing `.` (missing value)
elements is treated as an expression" (`KNOWN_LIMITATIONS.md`, v0.85.0; v0.85 plan §9.2 item 5). The client rightly did
not call it a defect.

v0.85.0, same snippet: review_required, plus a false `and` gap (`signature_not_extracted`, the accidental
`logical-and.rst` grounding) and `logical-and.rst` among the citations. v0.86.0 removes both: a reason-only change,
toward the evidence.

Real GAUSS (S07 verbatim): keeps rows 1, 4 and 7 and prints `3`. Spot check e04 confirms the client's caveat: with no
rows selected, `selif` returns a scalar missing, `scalmiss` is 1 and `rows` is 1.

Expected behavior: review_required with true gaps; the client does not reshape code around the `.` limitation.

Observed behavior: As expected; the known `.`-literal limitation reproduced live.

Pass/fail: Pass with limitation disclosed
Defect severity: None (known limitation)
Remediation: None.

Overall Score: 3.8
Decision: Pass with limitation disclosed
