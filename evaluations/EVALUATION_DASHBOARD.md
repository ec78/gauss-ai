# Evaluation Dashboard

This dashboard summarizes benchmark and evaluation status across the GAUSS AI expert system.

It is a consolidation reference, not an automated scoring engine. The source of truth remains:

- `evaluations/benchmark-prompts.md`
- `evaluations/benchmark-coverage.md`
- `evaluations/runs/INDEX.md`
- individual files under `evaluations/runs/`
- `scripts/check_evaluation_tracking.py`
- `scripts/check_release_readiness.py`

Use this dashboard to understand coverage by milestone, prompt range, expert category, pass/fail state, known historical exceptions, and current validation guard status. If anything here appears to disagree with a live guard run, trust the live run — this file is a snapshot, not a substitute for it.

## Dashboard Metadata

- Current milestone: `v0.18.0` - Expert System Consolidation.
- Captures evaluation state through: `v0.17.0` - Product Expert Foundation.
- Evaluation model: manual benchmark evaluation with tracking guard. No runtime scoring engine exists.
- Runtime scoring engine: Not implemented.
- Benchmark prompts source: `evaluations/benchmark-prompts.md`.
- Benchmark coverage source: `evaluations/benchmark-coverage.md`.
- Run index source: `evaluations/runs/INDEX.md`.
- Scoring rubric: `evaluations/scoring.md`.
- Manual evaluation workflow: `workflows/manual-evaluation.md`.
- Tracking guard: `scripts/check_evaluation_tracking.py`.
- Release-readiness guard: `scripts/check_release_readiness.py`.

## Current Evaluation State

Captured by running `scripts/check_evaluation_tracking.py`, `scripts/check_release_readiness.py`, and `scripts/validate_all_evidence.py` (default, `--json`, and `--strict`) against the repository state after `v0.17.0`:

- Prompt IDs: 113.
- Coverage rows: 113.
- Run files referenced: 100.
- Index entries: 105.
- Tracking errors: 0.
- Documented tracking warnings: 2.
- Current active ("Not Run" in the highest-numbered active category) warnings: 0 — the `24.x` category is fully evaluated, so the tracking guard's "current active category" check has nothing to flag.
- Default tracking guard (`check_evaluation_tracking.py`): PASS.
- JSON tracking guard (`check_evaluation_tracking.py --json`): `overall_pass: true`.
- Strict tracking guard (`check_evaluation_tracking.py --strict`): FAIL — expected, both current warnings are the two documented historical ones (see "Known Warnings and Historical Exceptions" below).
- Release-readiness default (`check_release_readiness.py`): PASS.
- Release-readiness JSON (`check_release_readiness.py --json`): `overall_pass: true`.
- Release-readiness strict (`check_release_readiness.py --strict`): informational FAIL — `strict_pass: false`, but `overall_pass` remains `true` because strict results never affect this script's own exit code.
- Evidence validation default (`validate_all_evidence.py`): PASS.
- Evidence validation JSON (`validate_all_evidence.py --json`): `overall_pass: true`.
- Evidence validation strict (`validate_all_evidence.py --strict`): FAIL — expected, due to the documented `glm`/`olsmt` HDF5-URI path-warning false positives.

Important:

- A default PASS does not mean zero warnings. The tracking guard's default PASS above still carries 2 documented warnings; the evidence validator's default PASS still carries warnings from the `glm`/`olsmt` HDF5-URI false positives.
- Strict-mode failures are expected and are limited to the documented warning-promoted-to-failure cases named in this file. They are not a signal of new defects.
- Evidence validation is structural (schema conformance, required fields, path-warning heuristics), not semantic or execution validation. It does not confirm that any documented GAUSS syntax is correct or that any example runs.
- GAUSS code is not executed by any of these checks. All checks here operate on markdown files, JSON evidence files, and schema definitions only.

## Benchmark Category Summary

| Prompt Range | Category / Milestone | Primary Purpose | Prompts | Run Files | Result | Notes |
|---|---|---|---:|---:|---|---|
| 1.x | Code Generation (early baseline) | Foundational GAUSS code generation behavior | 3 | 1 | 1 Passed (1.2, 4.0) / 2 Not Run | Historical baseline category; 1.1 and 1.3 have never been run. Predates the six-expert system entirely. |
| 2.x | Debugging (early baseline) | Foundational GAUSS debugging behavior | 3 | 1 | 1 Passed (2.2, 3.9) / 2 Not Run | 2.2's linked run file predates stable Prompt IDs and records internal Prompt ID `2.3` — a documented historical mismatch, not a defect. See "Known Warnings and Historical Exceptions" below. |
| 3.x | Code Explanation | Beginner/advanced explanation quality | 2 | 1 | 1 Passed (3.1, 4.0) / 1 Not Run | 3.2 has never been run. |
| 4.x | Code Translation | Cross-language translation into GAUSS | 3 | 1 | 1 Passed (4.3, 3.9) / 2 Not Run | 4.1 and 4.2 have never been run against their current prompt text; two older runs (historical run-003/run-004) evaluated earlier, differently-worded versions of this category and are tracked separately in `benchmark-coverage.md`'s "Completed Runs Not Directly Covered By Current Stable Prompts" section. |
| 5.x | Code Review | Package/API review quality | 2 | 1 | 1 Passed (5.1, 4.0) / 1 Not Run | 5.2 has never been run. |
| 6.x | Refactoring | Behavior-preserving refactor guidance | 2 | 1 | 1 Passed (6.1, 4.0) / 1 Not Run | 6.2 has never been run. |
| 7.x | Optimization | Vectorization/efficiency guidance | 2 | 1 | 1 Passed (7.1, 4.0) / 1 Not Run | 7.2 has never been run. |
| 8.x | Documentation (early baseline) | Procedure/package documentation quality | 2 | 1 | 1 Passed (8.1, 3.9) / 1 Not Run | 8.2 has never been run. Predates the Documentation Expert (`v0.15.0`). |
| 9.x | Test Generation | Test-case design for GAUSS procedures | 2 | 1 | 1 Passed (9.1, 4.0) / 1 Not Run | 9.2 has never been run. |
| 10.x | Design Guidance | Data-representation and audience-fit guidance | 2 | 1 | 1 Passed (10.1, 3.9) / 1 Not Run | 10.2 has never been run. |
| 11.x | Retrieval | Command-doc lookup and evidence use | 3 | 3 | 3/3 Passed (3.8-4.0) | All prompts run and passed. |
| 12.x | Retrieval Integration | Retrieval-evidence-shaped response behavior | 6 | 6 | 6/6 Passed (3.9-4.0) | All prompts run and passed. |
| 13.x | Evidence Schema | Schema-aligned evidence object handling | 7 | 7 | 7/7 Passed (4.0) | All prompts run and passed. |
| 14.x | Automated Evidence Validation | `validate_all_evidence.py` behavior and regressions | 5 | 5 | 5/5 Passed (4.0) | All prompts run and passed. |
| 15.x | Expert Routing / Operational Expert Modules (`v0.8.0`) | GAUSS Language Expert activation and boundaries | 7 | 7 | 7/7 Passed (4.0) | All prompts run and passed; see `planning/v0.8.0-readiness-checklist.md`. |
| 16.x | Multi-Expert Routing (`v0.9.0`) | GAUSS + Econometrics routing separation | 8 | 8 | 8/8 Passed (4.0) | All prompts run and passed; see `planning/v0.9.0-readiness-checklist.md`. |
| 17.x | Evidence Coverage and Tracking Guards (`v0.10.0`) | Evidence/tracking regression coverage | 6 | 6 | 6/6 Passed (4.0) | All prompts run and passed. Two of these prompts (17.5, 17.6) are the historical precedent documented in `workflows/manual-evaluation.md`'s Benchmark Authoring Guidance for avoiding hardcoded volatile counts. |
| 18.x | Repository Hygiene and Evaluation Policy Cleanup (`v0.11.0`) | Hygiene/evaluation-policy coverage | 6 | 6 | 6/6 Passed (4.0) | All prompts run and passed. |
| 19.x | GAUSS Language Knowledge Cleanup and CI Guard Prep (`v0.12.0`) | Release-readiness guard prep | 5 | 5 | 5/5 Passed (4.0) | All prompts run and passed; see `planning/v0.12.0-readiness-checklist.md`. |
| 20.x | Default CI Guard Integration (`v0.13.0`) | Default CI guard coverage | 5 | 5 | 5/5 Passed (4.0) | All prompts run and passed. |
| 21.x | Software Engineering Expert Foundation (`v0.14.0`) | Software Engineering Expert routing and boundaries | 8 | 8 | 8/8 Passed (4.0) | All prompts run and passed; see `planning/v0.14.0-readiness-checklist.md`. |
| 22.x | Documentation Expert Foundation (`v0.15.0`) | Documentation Expert routing and boundaries | 8 | 8 | 8/8 Passed (4.0) | All prompts run and passed; see `planning/v0.15.0-readiness-checklist.md`. |
| 23.x | Education Expert Foundation (`v0.16.0`) | Education Expert routing and boundaries | 8 | 8 | 8/8 Passed (4.0) | All prompts run and passed; see `planning/v0.16.0-readiness-checklist.md`. |
| 24.x | Product Expert Foundation (`v0.17.0`) | Product Expert routing and boundaries | 8 | 8 | 8/8 Passed (4.0) | All prompts run and passed; see `planning/v0.17.0-readiness-checklist.md`. |
| 25.x | Expert System Consolidation (`v0.18.0`) | Consolidated-artifact routing/boundary checks | 0 | 0 | Not added | Optional; proposed in `planning/v0.18.0-expert-system-consolidation.md`'s "Benchmark Plan" section but not yet added. Would only be added after the consolidation documents (registry, boundary matrix, cheat sheet, maintenance guide) exist. |

Counts above are taken directly from `evaluations/benchmark-coverage.md` and `evaluations/runs/INDEX.md`. Categories `1.x` through `10.x` predate stable Prompt ID conventions in places and are summarized as "early baseline" or historical where a prompt has never been run; these were not invented to force full coverage, and their `Not Run` prompts remain genuinely not run today.

## Expert Foundation Evaluation Summary

| Expert / System Area | Prompt Range | Benchmarks | Result | Key Boundaries Tested | Readiness Reference |
|---|---|---|---|---|---|
| GAUSS Language Expert | 15.x | 7 prompts | 7/7 Passed, 4.0 | Implementation correctness; no invented syntax; evidence-backed exact syntax/return behavior; activation vs. non-activation for non-GAUSS tasks. | `planning/v0.8.0-readiness-checklist.md`, `planning/v0.12.0-readiness-checklist.md` |
| Econometrics Expert | 16.x | 8 prompts | 8/8 Passed, 4.0 | Methodology vs. syntax separation; GAUSS-only, Econometrics-only, both-expert, and neither-expert routing. | `planning/v0.9.0-readiness-checklist.md` |
| Software Engineering Expert | 21.x | 8 prompts | 8/8 Passed, 4.0 | Maintainability/design vs. syntax and statistical validity; does not override GAUSS evidence; does not make causal claims. | `planning/v0.14.0-readiness-checklist.md` |
| Documentation Expert | 22.x | 8 prompts | 8/8 Passed, 4.0 | Documentation clarity vs. syntax, statistical, design, and education boundaries; does not validate syntax; does not replace the Education Expert. | `planning/v0.15.0-readiness-checklist.md` |
| Education Expert | 23.x | 8 prompts | 8/8 Passed, 4.0 | Learning design vs. syntax, documentation, and product boundaries; does not validate syntax; does not replace the Product Expert. | `planning/v0.16.0-readiness-checklist.md` |
| Product Expert | 24.x | 8 prompts | 8/8 Passed, 4.0 | Product/user value vs. syntax, statistical, design, documentation, and education boundaries; does not invent GAUSS syntax; does not replace Documentation or Education. | `planning/v0.17.0-readiness-checklist.md` |
| Six-expert system (consolidated) | 25.x (proposed) | 0-8 prompts | Not run | Would test whether the consolidated registry/boundary matrix/cheat sheet answer routing and boundary questions correctly, not re-test `21.x`-`24.x` boundaries. | `planning/v0.18.0-expert-system-consolidation.md` |

## Known Warnings and Historical Exceptions

- **Historical tracking warning — 2.2 / 2.3 Prompt ID mismatch:** the `2.2` coverage row (`evaluations/benchmark-coverage.md`) links to `evaluations/runs/2026-06-30-code-assistant-manual-run-001.md`, but that run file's own `Prompt ID:` field states `2.3`. This predates stable Prompt ID assignment and is documented in `evaluations/benchmark-coverage.md`'s "Historical Tracking Exceptions" section. It is a warning, not an error, and `--strict` promotes it to a failure by design.
- **Historical tracking warning — `v0.3.0` smoke-test file:** `evaluations/runs/2026-07-01-code-assistant-smoke-test-v0.3.0.md` predates Prompt-ID-based tracking entirely and is intentionally not indexed in `benchmark-coverage.md` or `runs/INDEX.md`. It is preserved as legitimate repository history, documented in the same "Historical Tracking Exceptions" section. It is a warning, not an error, and `--strict` promotes it to a failure by design.
- **Evidence warnings — `glm`/`olsmt` HDF5 URI false positives:** `examples/retrieval/schema-aligned/glm.evidence.json` and `olsmt.evidence.json` contain path-shaped strings from official documentation examples (an HDF5 URI) that the path-warning heuristic flags. These are reviewed false positives, not real local-path leaks, documented in `scripts/README.md`'s strict-mode policy notes. `--strict` promotes them to failures by design.
- **Current active-category "Not Run" warnings:** none. After the `v0.17.0` evaluation of `24.x`, the tracking guard's "current active category" check (which flags `Not Run` prompts in the highest-numbered category) has nothing to report, because every prompt in `24.x` is `Passed`.
- **Strict-mode policy:** default gates (`check_evaluation_tracking.py`, `validate_all_evidence.py`, `check_release_readiness.py`) pass. Strict modes are informational and fail only because the warnings above are promoted to failures. Strict failures should not block a release unless the project explicitly changes this policy — see `scripts/README.md` and prior readiness checklists (`v0.12.0` onward) for the policy's history.

## Guard Command Reference

```bash
python scripts/validate_all_evidence.py
python scripts/validate_all_evidence.py --json
python scripts/validate_all_evidence.py --strict

python scripts/check_evaluation_tracking.py
python scripts/check_evaluation_tracking.py --json
python scripts/check_evaluation_tracking.py --strict

python scripts/check_release_readiness.py
python scripts/check_release_readiness.py --json
python scripts/check_release_readiness.py --strict
```

Expected current results (captured at the same time as "Current Evaluation State" above):

- `validate_all_evidence.py` default: PASS.
- `validate_all_evidence.py --json`: PASS (`overall_pass: true`).
- `validate_all_evidence.py --strict`: expected FAIL, due to the known `glm`/`olsmt` HDF5-URI warnings.
- `check_evaluation_tracking.py` default: PASS.
- `check_evaluation_tracking.py --json`: `overall_pass: true`.
- `check_evaluation_tracking.py --strict`: expected FAIL, due to the two historical warnings.
- `check_release_readiness.py` default: PASS.
- `check_release_readiness.py --json`: `overall_pass: true`.
- `check_release_readiness.py --strict`: expected informational FAIL (`strict_pass: false`); default readiness (`overall_pass`) is unaffected, since strict results never change this script's own exit code.

## Dashboard Maintenance Notes

- Update this dashboard after each benchmark category is added.
- Update this dashboard after each benchmark category is evaluated.
- Update prompt counts, coverage counts, run-file counts, and index-entry counts after running the tracking guard — do not hand-derive them from memory.
- Update known warnings if historical exceptions are added or resolved.
- Do not treat this dashboard as the source of truth over `evaluations/benchmark-coverage.md`, `evaluations/runs/INDEX.md`, or the individual run files under `evaluations/runs/`. If this file and a live guard run ever disagree, the live guard run is correct and this file is stale.
- Do not claim GAUSS code execution from evidence validation or tracking-guard checks — both operate on markdown/JSON files only.
- Do not record "all passed" for a category unless `evaluations/benchmark-coverage.md` and the linked run files actually support it.
- When a new milestone adds benchmarks:
  - Add the category to the Benchmark Category Summary table.
  - Update the Expert Foundation Evaluation Summary table if the category belongs to an operational expert.
  - Update the guard-count summaries in "Current Evaluation State" after evaluation, using live tool output.
  - Link the milestone's readiness checklist once it exists.
