# Benchmark Coverage

This file tracks which benchmark prompts have been manually evaluated. Statuses use the stable Prompt IDs from `evaluations/benchmark-prompts.md`.

Some early runs predate stable Prompt ID assignment. Where a run does not match the current benchmark prompt for its recorded ID, the note explains the mismatch rather than treating it as exact coverage.

| Prompt ID | Category | Benchmark Name | Status | Latest Run | Latest Score | Notes |
|---:|---|---|---|---|---:|---|
| 1.1 | Code Generation | Matrix summary procedure | Not Run | N/A | N/A | None. |
| 1.2 | Code Generation | String parser | Passed | [2026-07-01-code-assistant-manual-run-009.md](runs/2026-07-01-code-assistant-manual-run-009.md) | 4.0 | Valid GAUSS procedure using `strindx`, `strlen`, and `strsect`, with clear `strindx == 0` handling and return behavior. |
| 1.3 | Code Generation | DataFrame cleaning script | Not Run | N/A | N/A | None. |
| 2.1 | Debugging | Array dimension error | Not Run | N/A | N/A | Run 002 records Prompt ID 2.1, but it evaluated a separate trimmed-`y` dimension mismatch prompt, not the current array dimension benchmark. |
| 2.2 | Debugging | String search bug | Passed | [2026-06-30-code-assistant-manual-run-001.md](runs/2026-06-30-code-assistant-manual-run-001.md) | 3.9 | Run 001 predates stable IDs and records Prompt ID 2.3, but maps by benchmark content to GAUSS string search and `strindx == 0` behavior. |
| 2.3 | Debugging | Scope and package dependency | Not Run | N/A | N/A | Run 001 records historical Prompt ID 2.3 but did not evaluate the current scope/package dependency benchmark. |
| 3.1 | Code Explanation | Beginner matrix explanation | Passed | [2026-07-01-code-assistant-manual-run-010.md](runs/2026-07-01-code-assistant-manual-run-010.md) | 4.0 | Clear beginner explanation of matrix dimensions, `mu'`, and the sample variance-covariance calculation. |
| 3.2 | Code Explanation | Advanced structure explanation | Not Run | N/A | N/A | None. |
| 4.1 | Code Translation | MATLAB to GAUSS | Not Run | N/A | N/A | Run 003 records Prompt ID 4.1, but it evaluated a Python string `.find()` translation, not the current MATLAB benchmark. |
| 4.2 | Code Translation | Python to GAUSS | Not Run | N/A | N/A | No completed run covers the current matrix/missing-value Python translation prompt. Run 004 records historical Prompt ID 4.2 but evaluated R regression setup. |
| 4.3 | Code Translation | R to GAUSS regression setup | Passed | [2026-07-01-code-assistant-manual-run-008.md](runs/2026-07-01-code-assistant-manual-run-008.md) | 3.9 | Latest run validates the hybrid strategy: categories for discovery, curated `olsmt` note for verified format, and official docs as authoritative. |
| 5.1 | Code Review | Review public API design | Passed | [2026-06-30-code-assistant-manual-run-006.md](runs/2026-06-30-code-assistant-manual-run-006.md) | 4.0 | Strong public/helper separation, `y`/`x`/`ctl` validation, control defaults, dependency clarity, and GAUSS-specific maintainability review. |
| 5.2 | Code Review | Review matrix and array usage | Not Run | N/A | N/A | None. |
| 6.1 | Refactoring | Procedure cleanup | Passed | [2026-07-01-code-assistant-manual-run-011.md](runs/2026-07-01-code-assistant-manual-run-011.md) | 4.0 | GAUSS-specific refactoring guidance preserves the public procedure and separates computation, reporting, and file output. |
| 6.2 | Refactoring | Control structure defaults | Not Run | N/A | N/A | None. |
| 7.1 | Optimization | Loop to matrix operation | Passed | [2026-07-01-code-assistant-manual-run-012.md](runs/2026-07-01-code-assistant-manual-run-012.md) | 4.0 | Recommends native `sumc`, explains matrix dimensions, preserves loop semantics, and addresses missing-value implications. |
| 7.2 | Optimization | String processing efficiency | Not Run | N/A | N/A | None. |
| 8.1 | Documentation | Procedure usage docs | Passed | [2026-07-01-code-assistant-manual-run-013.md](runs/2026-07-01-code-assistant-manual-run-013.md) | 3.9 | Practical GAUSS-facing docs for `winsorizeDF` cover inputs, output, assumptions, missing values, and example call without unsupported methods. |
| 8.2 | Documentation | Package README section | Not Run | N/A | N/A | None. |
| 9.1 | Test Generation | Matrix procedure tests | Passed | [2026-07-01-code-assistant-manual-run-014.md](runs/2026-07-01-code-assistant-manual-run-014.md) | 4.0 | Covers normal, constant-column, missing-value, single-row, and dimension edge cases with clear GAUSS-shaped invariants. |
| 9.2 | Test Generation | String utility tests | Not Run | N/A | N/A | None. |
| 10.1 | Design Guidance | Choose data representation | Passed | [2026-07-01-code-assistant-manual-run-015.md](runs/2026-07-01-code-assistant-manual-run-015.md) | 3.9 | Recommends structures as primary model-result objects while distinguishing matrices, DataFrames, and arrays by role. |
| 10.2 | Design Guidance | Beginner vs advanced response | Not Run | N/A | N/A | None. |
| 11.1 | Retrieval | Look up `olsmt` syntax and intercept behavior | Passed | [2026-07-02-code-assistant-retrieval-run-001.md](runs/2026-07-02-code-assistant-retrieval-run-001.md) | 3.8 | Used categories for discovery and official `olsmt` lookup evidence to verify syntax and answer the intercept question directly. Improvement: add a concrete validation step, such as comparing `out.b` against R's `coef(model)`. |
| 11.2 | Retrieval | Look up `strindx` not-found behavior | Passed | [2026-07-02-code-assistant-retrieval-run-002.md](runs/2026-07-02-code-assistant-retrieval-run-002.md) | 3.75 | Verified `strindx` returns `0` when not found from official lookup evidence, contrasted with Python `.find()`'s `-1`. Improvement: add a second example showing the found branch. |
| 11.3 | Retrieval | Look up category-only command candidate | Passed | [2026-07-02-code-assistant-retrieval-run-003.md](runs/2026-07-02-code-assistant-retrieval-run-003.md) | 4.0 | Treated category membership as discovery only, refused to invent syntax, and recommended `scripts/command_doc_lookup.py` before giving exact usage. |
| 12.1 | Retrieval Integration | Docs found but extraction incomplete | Passed | [2026-07-04-code-assistant-retrieval-integration-run-003.md](runs/2026-07-04-code-assistant-retrieval-integration-run-003.md) | 4.0 | Safely gave only verified `olsmtOut` fields and named truncated extraction. Follow-up: improve full `olsmtOut` extraction. |
| 12.2 | Retrieval Integration | Docs not found | Passed | [2026-07-04-code-assistant-retrieval-integration-run-004.md](runs/2026-07-04-code-assistant-retrieval-integration-run-004.md) | 4.0 | Refused invented syntax when docs were not found and offered safe spelling, package, version, source, and alternate-name checks. |
| 12.3 | Retrieval Integration | Ambiguous command match | Passed | [2026-07-04-code-assistant-retrieval-integration-run-005.md](runs/2026-07-04-code-assistant-retrieval-integration-run-005.md) | 4.0 | Reported ambiguity and requested disambiguating context instead of silently choosing a candidate. Follow-up: test with a real ambiguous-match pair when found. |
| 12.4 | Retrieval Integration | Curated note vs official docs | Passed | [2026-07-04-code-assistant-retrieval-integration-run-006.md](runs/2026-07-04-code-assistant-retrieval-integration-run-006.md) | 4.0 | Made official command-specific docs authoritative over curated notes and recommended correcting stale notes. |
| 12.5 | Retrieval Integration | Translation response needs validation step | Passed | [2026-07-04-code-assistant-retrieval-integration-run-001.md](runs/2026-07-04-code-assistant-retrieval-integration-run-001.md) | 3.9 | Included verified `olsmt` syntax, assumptions, unresolved docs gaps, and a concrete coefficient-comparison validation step. |
| 12.6 | Retrieval Integration | Debugging response requires return-behavior retrieval | Passed | [2026-07-04-code-assistant-retrieval-integration-run-002.md](runs/2026-07-04-code-assistant-retrieval-integration-run-002.md) | 4.0 | Used retrieved `strindx` return behavior, corrected `idx == -1` to `idx == 0`, and added found/not-found tests. |
| 13.1 | Evidence Schema | Valid schema-aligned evidence | Not Run | N/A | N/A | Tests whether the assistant confirms schema validity and states source authority/type before using verified fields from a `found_complete` evidence object. |
| 13.2 | Evidence Schema | Stale evidence warning | Not Run | N/A | N/A | Tests whether the assistant surfaces `stale_evidence.is_stale` and recommends refreshing the lookup rather than treating stale evidence as current. |
| 13.3 | Evidence Schema | Official docs vs curated note conflict | Not Run | N/A | N/A | Tests whether a schema-represented `conflict` entry is resolved in favor of official docs, with the conflict flagged and the curated note recommended for correction. |
| 13.4 | Evidence Schema | Ambiguous evidence object | Not Run | N/A | N/A | Tests whether an `ambiguous` evidence object with multiple candidates is reported as ambiguous rather than silently resolved to one candidate. |
| 13.5 | Evidence Schema | Found incomplete with extraction warnings | Not Run | N/A | N/A | Tests whether a `found_incomplete` evidence object with truncated-returns warnings yields only verified fields plus explicit unresolved questions. |
| 13.6 | Evidence Schema | Schema validation failure | Not Run | N/A | N/A | Tests whether the assistant refuses to treat schema-invalid evidence (missing `schema_version`/`retrieval_status`/`source_authority`) as reliable structured evidence. |
| 13.7 | Evidence Schema | Validator path warning | Not Run | N/A | N/A | Tests whether the assistant distinguishes a validation pass-with-warnings from a failure, and recognizes path-shaped official-docs example text as a likely false positive rather than an automatic rejection. |

## Completed Runs Not Directly Covered By Current Stable Prompts

- [2026-06-30-code-assistant-manual-run-002.md](runs/2026-06-30-code-assistant-manual-run-002.md): evaluated a trimmed-`y` row-alignment dimension mismatch prompt under historical Prompt ID 2.1.
- [2026-06-30-code-assistant-manual-run-003.md](runs/2026-06-30-code-assistant-manual-run-003.md): evaluated Python `.find()` to GAUSS `strindx` translation under historical Prompt ID 4.1.
