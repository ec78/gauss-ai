# Evaluation Result

Date: 2026-10-16
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. All twenty-one tasks ran on 2026-10-16 in one server session. The session did not read the planning doc, PROJECT_STATUS.md or any source until all tasks were done.
Agent Version: v0.85.0 (released; tag `v0.85.0`, commit `f11505e`; HEAD `d634b40`, whose `scripts/` is identical to the tag), editable install of this checkout (`pip show gauss-ai` = 0.85.0). The live server's own output carries v0.85.0-only behavior (`library` -> `source_inclusion` in 75.3/75.6; a typed `struct` procedure header is no longer INVALID in 75.2; `miss` keeps its signature in 75.4).
Prompt ID: 75.17
Prompt Category: Procedure Headers and Defining Pages (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.85.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session d965dee780a44d0e8faacbdafbd0eaad. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.85.0 and v0.84.0 (`d19c61c`); every live verdict reproduced exactly on the v0.85.0 archive. Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) programs run by the recording session from a scratch directory, including the client's own programs. No `gauss_execution_prepare` call was made.
Prompt Text:

"What is the difference between a matrix and a dataframe in GAUSS?"

Searches:
```
search_docs("dataframe matrix metadata variable names types") -> ungrounded; 5 candidates: asdf, copyMetadata,
    getColTypes, hasMetaData, asMatrix (all relevant)
search_docs("hasMetaData asMatrix getColTypes") -> grounded (the client FOLLOWED the candidates)
search_docs("dftype dfname") -> grounded (from asMatrix's seealso line)
```
The user's literal wording (recording-session re-run) is ungrounded with five irrelevant date-difference candidates
(`etdays`, `ethsec`, `timediffdt`, ...), through the word "difference".

Observed behavior: Correct and grounded: a dataframe is a matrix with metadata (`hasMetaData`'s own wording), and
`asMatrix`'s remarks give the storage of dates (Posix seconds) and categories (integer keys).

**The client did not validate its conversion snippet** and said so. Recording-session diagnosis: v0.85.0 is
**not_ready**: `dftype (argument 2): the argument's literal category (string) does not match the documented type for
parameter 'types' (vector)`. That is false: `dftype.rst`'s own examples pass `"date"` and `"category"`, and real
GAUSS runs the snippet (`getColTypes` prints `category`). Pre-existing (identical on v0.84.0), safe direction; the
docs type a list of type *names* as "Mx1 vector". Also seen: `dfname` arg 1 `documented_type_missing`, because the
page's `:param X:` does not match the signature's `x` (a docs inconsistency).

Pass/fail: Pass with defect recorded
Defect severity: Minor (recording-session finding: false INCOMPATIBLE on a string where the docs say vector; not seen by the client)
Remediation: Next milestone candidate: a string literal should not be a mismatch for a documented vector whose own page passes strings (needs its own design).

Overall Score: 3.5
Decision: Pass with defect recorded
