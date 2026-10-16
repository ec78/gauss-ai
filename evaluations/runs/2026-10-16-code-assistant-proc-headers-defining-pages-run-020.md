# Evaluation Result

Date: 2026-10-16
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. All twenty-one tasks ran on 2026-10-16 in one server session. The session did not read the planning doc, PROJECT_STATUS.md or any source until all tasks were done.
Agent Version: v0.85.0 (released; tag `v0.85.0`, commit `f11505e`; HEAD `d634b40`, whose `scripts/` is identical to the tag), editable install of this checkout (`pip show gauss-ai` = 0.85.0). The live server's own output carries v0.85.0-only behavior (`library` -> `source_inclusion` in 75.3/75.6; a typed `struct` procedure header is no longer INVALID in 75.2; `miss` keeps its signature in 75.4).
Prompt ID: 75.20
Prompt Category: Procedure Headers and Defining Pages (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.85.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session d965dee780a44d0e8faacbdafbd0eaad. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.85.0 and v0.84.0 (`d19c61c`); every live verdict reproduced exactly on the v0.85.0 archive. Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) programs run by the recording session from a scratch directory, including the client's own programs. No `gauss_execution_prepare` call was made.
Prompt Text:

"Do I have to declare my structures before using them in GAUSS?"

Searches: `search_docs("struct declare structure definition instance")` -> partially_grounded on `declare.rst` and
the structures guide (excerpt: only the structure-pointer section). The user's literal wording grounds the same way.

Code:
```gauss
struct regResults {
    matrix b;
    matrix se;
    string label;
};
struct regResults r;
r.b = zeros(2, 1);
...
```
Captured output: `not_ready`, syntax INVALID `matrix_literal_row_separator` ("GAUSS matrix literal uses unsupported
row separator `;`"). The client recognized a structure definition, not a matrix literal, and isolated it: two- and
one-member definitions (`struct pt { matrix x; };`) are rejected the same way. Real GAUSS (sc04): the program runs
and prints `OLS 0 0`. Identical on v0.84.0. Reach: every snippet that defines its own structure type.

**Wrong client guess:** the client added that the definition "hides `p` and `pt` from the rest of the analysis",
because `user_defined_symbols` was empty. The recording session found that the snippet simply has no plain
assignment target to collect (only `r.b = ...` member writes); a definition followed by `q = zeros(1, 1);` collects
`q` normally.

Answer: "Yes", with the declaration rules. The user then corrected it for GAUSS 26 (75.21). The recording-session spot
checks show the answer was right for `pvCreate()`-style producers (sc06 `G0181`, sc08 `G0025`) and wrong when the
producing procedure declares a `(struct T)` return type (sc07, sc09).

Expected behavior: Valid GAUSS is never a syntax INVALID.

Observed behavior: **Real defect found live: a false INVALID** on every user-defined structure type; pre-existing,
safe direction. The client's answer was incomplete for GAUSS 26.

Pass/fail: Fail
Defect severity: Moderate (false INVALID on every structure definition; pre-existing; safe direction)
Remediation: Next milestone: `matrix_literal_row_separator` must not read a `struct Name { ... };` definition as a literal; sc04 is the provenance.

Overall Score: 2.3
Decision: Fail — real defect
