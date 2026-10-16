# Evaluation Result

Date: 2026-10-16
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. All twenty-one tasks ran on 2026-10-16 in one server session. The session did not read the planning doc, PROJECT_STATUS.md or any source until all tasks were done.
Agent Version: v0.85.0 (released; tag `v0.85.0`, commit `f11505e`; HEAD `d634b40`, whose `scripts/` is identical to the tag), editable install of this checkout (`pip show gauss-ai` = 0.85.0). The live server's own output carries v0.85.0-only behavior (`library` -> `source_inclusion` in 75.3/75.6; a typed `struct` procedure header is no longer INVALID in 75.2; `miss` keeps its signature in 75.4).
Prompt ID: 75.16
Prompt Category: Procedure Headers and Defining Pages (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.85.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session d965dee780a44d0e8faacbdafbd0eaad. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.85.0 and v0.84.0 (`d19c61c`); every live verdict reproduced exactly on the v0.85.0 archive. Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) programs run by the recording session from a scratch directory, including the client's own programs. No `gauss_execution_prepare` call was made.
Prompt Text:

"What about the order procedure?"

Searches: `search_docs("order")` -> grounded; `search_docs("asDF")` -> grounded (checked after the validator named
`varname_1`).

The `order` page types `X` as an "NxK dataframe" that "Must have metadata", but its first example passes a plain
`reshape` matrix. The client noticed the contradiction and tested both.

Snippets and captured output (all `review_required`, no error):
- `order(x, 5|3|1)` on a plain matrix: gap `order` arg 1 `return_type_imprecise` ("may not fit the documented type
  ... a documented return type is not precise enough to call this a mismatch");
- `asDF(x, "a"$|"b"$|"c"$|"d"$|"e")` then `order(df, "e"$|"c"$|"a")`: gap `asDF` arg 2 `documented_type_missing`;
- the documented comma form `asDF(x, "a", "b", "c", "d", "e")` (the client switched after reading `asdf.rst`): gaps
  for `asDF` args 2-3 only. Arguments 4-6 fall on the documented `...`, typed `string`, so they match. Correct.

Diagnosis: identical; agree; the client explained each gap correctly. v0.84.0: identical.

Real GAUSS: `order(x, 5|3|1)` on a plain matrix runs (sc11), so the docs' example is right and "Must have metadata"
is over-strict; the validator's refusal to call it a mismatch was the right call. The dataframe version prints
`e c a b d` with headers.

Pass/fail: Pass
Defect severity: None (docs inconsistency handled conservatively)
Remediation: None.

Overall Score: 3.8
Decision: Pass
