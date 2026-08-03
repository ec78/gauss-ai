# v0.55.0 - Verified Diagnostic Coverage Expansion

This release broadens the verified GAUSS error knowledge available to the interpreter and diagnostic engine (`scripts/gauss_error_catalog.py`), growing the catalog from 5 to 11 entries — entirely through real GAUSS 26.1.1 runtime reproduction, this repository's strongest evidence tier. No repair behavior was added.

## Evaluated

- All ten `46.x` Verified Diagnostic Coverage Expansion prompts: 10/10 Pass at 4.0, zero Critical/Major/Minor defects.
- 15 real GAUSS invocations (`tgauss.exe -b`) performed during this milestone's own bounded, safe evidence-gathering probe, plus the optional real-runner smoke test for validation completeness. No package install/removal, no license/environment change, zero lingering `gauss`/`tgauss` processes confirmed after both.

## Added

- Six new catalog entries, each backed solely by real-runtime reproduction (not yet independently cross-checked against official documentation, disclosed as such): `G0058` (Index out of range), `G0159` (Wrong number of parameters), `G0104` (Argument must be positive), `G0071` (Type mismatch), `G0048` (Matrix singular), `G0047` (Rows don't match).
- Three new `GaussErrorCategory` values (`indexing_subscript`, `argument_validation`, `type_mismatch`); the previously-empty `numerical` category gained its first entry (`G0048`); `matrix_dimension` gained a second, distinct code (`G0047`) alongside `G0036`.
- `scripts/test_gauss_error_catalog.py` — a new, dedicated catalog-integrity test file (18 tests: verification metadata, duplicate/empty-status rejection, documentation-only vs. dual-sourced vs. real-runtime-only labeling, category population, no-repair-instruction checks).
- 8 new interpreter tests, 9 new diagnostic-engine tests, 2 new CLI tests — one per new code plus regression coverage for the pre-existing five.
- `planning/v0.55.0-verified-diagnostic-coverage-expansion.md` — full evidence-gathering method, the complete 15-scenario probe table, and rationale for what was and wasn't added.

## `G0290` Runtime Verification

Upgraded from documentation-only to dual-sourced (Real Runtime + Official Documentation). Reproduced via `library optmum;` in an isolated scratch directory against this installation's real, confirmed-absent package (`optmum` is not among the 13 modules under `pkgs/`). The runtime-observed title ("Library not found") matches official Aptech documentation exactly — no discrepancy. This is an intentional, evidence-driven supersession of `v0.53.0`/`v0.54.0`'s own documentation-only assertions for `G0290`; the two pre-existing tests asserting the old status were updated in place with an explicit comment, not silently changed.

## What Was Not Added

- `G0117` ("Invalid argument") was genuinely observed but only via an indirect, compound trigger (an uncoded dataframe-indexing message preceding it) — too ambiguous to state a non-speculative `known_trigger`.
- A `csvRead` "file not found" failure (via `loadd` against a missing file) was discovered to use a format with **no `G####` code at all** (`error : csvRead error: ...`). The interpreter's regex correctly does not match it, falling through to `insufficient_evidence` honestly — a documented schema gap, not a bug.

Both are documented in `docs/gauss-error-catalog.md`'s new "Considered But Not Added" section and in `KNOWN_LIMITATIONS.md`.

## Confidence Model (unchanged)

Cause-level confidence remains capped at `low` for every catalog-derived cause, including all six new codes — catalog breadth never raises the confidence ceiling. Verified directly for all 11 codes.

## No Interpreter or Diagnostic-Engine Logic Changed

Both `interpret_execution(...)` and `diagnose_execution(...)` continue to only look codes up in the catalog; adding six new entries plus upgrading one required zero control-flow changes to either module. No new CLI command; existing `interpret`/`diagnose` commands handle every new code without modification.

## Safety Boundaries (unchanged, re-verified)

Execution, confirmation, provenance, output-reading, workspace-recovery, and repair-boundary contracts are all unchanged. No new entry introduces execution, retry, file-reading, or workspace mutation as a side effect of interpretation or diagnosis.

## Remaining Limitations

- The six codes added this milestone are real-runtime-verified only; none has yet been independently cross-checked against official Aptech documentation in this repository.
- Most real GAUSS error codes remain uncataloged and are still classified generically (`unknown`).
- Some real GAUSS runtime failures are not reported in the `error G####` format this catalog's lookup depends on at all — a documented, genuine gap, not a defect.
- `G0117` remains uncataloged pending a cleaner, non-compound reproduction.
- Diagnosis still cannot inspect variable values, matrix shapes, or source code content; still does not repair code, retry, or establish statistical/methodological validity; no durable session integration.

## Next Recommended Milestone

Durable execution sessions or evidence-aware repair planning are the two named candidates in this project's own roadmap. A further diagnostic-coverage expansion remains available but is now lower-priority evidence-wise, since this milestone's own bounded probe already found and cataloged every cleanly-reproducible error from its candidate list, leaving mostly harder-to-safely-reproduce categories (startup/licensing) or documentation cross-checks as the remaining low-risk work in that direction.
