# Evaluation Result

Date: 2026-10-16
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. All twenty-one tasks ran on 2026-10-16 in one server session. The session did not read the planning doc, PROJECT_STATUS.md or any source until all tasks were done.
Agent Version: v0.85.0 (released; tag `v0.85.0`, commit `f11505e`; HEAD `d634b40`, whose `scripts/` is identical to the tag), editable install of this checkout (`pip show gauss-ai` = 0.85.0). The live server's own output carries v0.85.0-only behavior (`library` -> `source_inclusion` in 75.3/75.6; a typed `struct` procedure header is no longer INVALID in 75.2; `miss` keeps its signature in 75.4).
Prompt ID: 75.19
Prompt Category: Procedure Headers and Defining Pages (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.85.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session d965dee780a44d0e8faacbdafbd0eaad. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.85.0 and v0.84.0 (`d19c61c`); every live verdict reproduced exactly on the v0.85.0 archive. Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) programs run by the recording session from a scratch directory, including the client's own programs. No `gauss_execution_prepare` call was made.
Prompt Text:

"How can I identify outliers in my data using GAUSS? Write me an example code snippet."

Searches:
```
search_docs("outliers detect") -> ungrounded; one candidate, plotSetJitterRange (box-plot jitter; not followed)
search_docs("stdc selif sumc") -> grounded (prior knowledge)
search_docs("findIdx") -> grounded (from selif's seealso line)
```
The user's literal wording (recording-session re-run) is partially grounded on `datalist.rst` through the word
"data" (the 74.19 class).

Code (abridged; z-score and IQR rules):
```gauss
q = quantile(x, 0.25 | 0.75);
iqr = q[2] - q[1];
lower = q[1] - 1.5 * iqr;
upper = q[2] + 1.5 * iqr;
flag_iqr = (x .< lower) .or (x .> upper);
idx_z = findIdx(flag_z);
x_clean = delif(x, flag_iqr);
```

Attempt 1: `not_ready`, "ambiguous topic(s) remain unresolved: or"; `or` in `unknown_symbols`. The client suspected
a false positive, checked that the `selif` page uses the same `(...) .and (...)` pattern, and isolated it with three
minimal snippets: `.or (` -> unknown `or`; `.and (` -> grounds by accident on `logical-and.rst`; `.or` without the
parenthesis -> no call. Its diagnosis was right.

Recording-session diagnosis: `_CALL_SHAPED_RE = r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\("`
(`gauss_pre_execution_validation.py:197`) matches `or(` after the dot, and `extract_generated_calls` excludes no
preceding `.`. Reach (probes): `.or (`, `.not (`, `.xor (`, `.eq (` and the plain `or (`, `not (` are all unknown calls
(not_ready); `.and (`/`and (` reach `logical-and.rst` (`signature_not_extracted`, review_required). Inside a call
argument, `meanc((x .< 2) .or (x .> 8))` is also a syntax INVALID (`call_argument_missing_separator`: word operators
are not operators to that rule). Real GAUSS: all of these run (sc05, sc12, sc13). Identical on v0.84.0. Not in
`KNOWN_LIMITATIONS.md` or earlier planning docs.

Attempt 2 (**the client removed that line's parentheses only to check the rest, and disclosed it**; its answer kept
the parentheses): `review_required`, six expression gaps; agree.

**Client defect:** the program does not run in real GAUSS: `G0276 Illegal use of reserved word 'lower'` and
`'upper'`. The validator listed both in `user_defined_symbols` without comment; no rule checks reserved words (the
v0.84 plan's probe t5 already knew `det = 3;` -> G0276). With `lo`/`hi` the program flags exactly rows 17, 88 and
150 (z-score), 5 rows by IQR, and leaves 195 rows.

Expected behavior: Valid GAUSS operators are never unknown calls; the code given to the user runs.

Observed behavior: **Real defect found live** (a false not_ready on GAUSS's element-wise logical operators, and a
false INVALID inside calls), correctly diagnosed by the client. **The client's own code was broken** (reserved
words), and nothing in the validation chain caught it.

Pass/fail: Fail
Defect severity: Moderate (false not_ready/INVALID on logical operators; pre-existing; safe direction); Minor (reserved words unchecked)
Remediation: Next milestone: a name preceded by `.` (and the word operators `and`/`or`/`not`/`xor`/`eqv` and relational words) is never a call, and is an operator for `call_argument_missing_separator`; consider a reserved-word rule backed by spot checks.

Overall Score: 2.0
Decision: Fail — real defect
