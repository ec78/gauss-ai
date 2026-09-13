# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

None active. `v0.75.0 — Validation Coverage & Universal Code Eligibility` is **complete, committed, tagged, pushed, and released**. Per this repository's own workflow rule (see `CLAUDE.md`), the next milestone should NOT be started automatically — it needs a deliberate decision from the user, informed by `planning/v0.75.0-universal-code-validation.md`'s own recommendation (Section 16: ready for alpha testing of universal code validation; NOT ready for a controlled-execution-handoff milestone yet).

## Completed Work

- `v0.75.0` closes the exact QA-intent eligibility gap `v0.74.0` disclosed but did not fix: `ConversationEngine.ask(...)` now computes the generation gate for every intent (not only `CODE_GENERATION`), and the pre-execution validation pass now runs whenever the answer contains code, for any intent. Beyond the routing fix, this milestone broadened `gauss_pre_execution_validation.py`'s own evidence: documented parameter category/shape extraction from real `:type` lines (`DocumentedParameter`/`classify_documented_type`), literal-argument-vs-documented-type role checking (`check_parameter_roles`, `MATCH`/`MISMATCH`/`UNKNOWN`), two new precondition families (`solpd`, `chol`) plus an upgraded `inv` invertibility check, a structured predicted-output-claim model (`PredictedOutputClaim`/`analyze_predicted_output`, kept structurally separate from execution eligibility), and a `ValidationCoverage` summary.
- Three real defects were found live during `v0.75.0`'s own development and fixed within the milestone: a pre-existing `v0.74.0` documentation-derived-concept-index false-ambiguity bug (ordinary English pronoun/auxiliary words "can"/"you" coincidentally tying two unrelated real doc pages) that was inert before this milestone's routing fix made it consequential for QA-classified turns; and two predicted-output-claim detection gaps (a model's claimed output inside its own fenced code block was not captured; a leading text label inside that fence made the whole block unparseable). All three are fixed and covered by regression tests. The exact `v0.74.0` wrong-model-prediction finding (`invpd({2 1, 1 2})`'s real inverse vs. a wrong model claim) was reconstructed and correctly detected as `MISMATCH`; a correct prediction on the same code was correctly `VERIFIED`. Three new/upgraded precondition families were independently confirmed against real `tgauss.exe -b` execution across seven spot checks, all converging exactly.
- Full design, live-evaluation evidence, and honest limitations are in `planning/v0.75.0-universal-code-validation.md` (its own 16-section readiness assessment) — read that file rather than asking for a re-summary.
- `v0.70.0`–`v0.75.0` are complete, committed, tagged, pushed, and released. Latest: tag `v0.75.0`, commit `d6a9064`, release at `https://github.com/ec78/gauss-ai/releases/tag/v0.75.0`.

## Decisions

- `ExecutionEligibility` deliberately remains a 3-state enum (`INELIGIBLE`/`REQUIRES_CLARIFICATION`/`ELIGIBLE_FOR_VALIDATION`) — a fourth "eligible with caveats" tier was considered (per the milestone brief's own Phase 14) and rejected in favor of the new `ValidationCoverage` summary, which gives a caller the same nuance without proliferating eligibility states. Documented in `gauss_pre_execution_validation.py`'s own top-of-file docstring and in the planning doc's Section 10.
- Predicted-output verification structurally cannot influence `ExecutionEligibility` — `compute_eligibility(...)` takes no predicted-output argument at all, by design, so a wrong prediction never makes correctly-generated code ineligible and a right-looking prediction is never treated as execution evidence.
- All other `v0.75.0` design decisions (signature-metadata extraction scope, which precondition families were added and why, predicted-output detection/verification scope) are recorded in `planning/v0.75.0-universal-code-validation.md` — that file is the durable record.

## Tests / Validation

- Full suite as of this session: **42 test files, 1,363 test functions, all passing**. Zero diff on every core execution/repair/verification/approval module.
- Live evaluation: category `65.x` (10 scenarios), run against the real local Ollama service and `qwen2.5-coder:7b`, transcripts in `evaluations/runs/2026-09-12-code-assistant-universal-code-validation-run-*.md`. Seven bounded real `tgauss.exe -b` spot checks were also run (`inv` singular, `invpd` valid, `solpd` valid/invalid/upper-triangle-only, `chol` valid/invalid) — all results recorded in the planning doc's Section 9.
- `python scripts/check_release_readiness.py` passes with only the same pre-existing, previously-documented historical warnings (nothing new introduced by `v0.75.0`).
- `gauss-ai version`/`doctor` re-verified against the real installed CLI (real Ollama reachable, real `tgauss.exe` configured, real docs-root configured) — both correctly report `0.75.0` (a pre-existing duplicated-version-string pattern was found and fixed: `gauss_ai_cli.py`'s own hardcoded `__version__` was still `0.74.0` after the `pyproject.toml` bump, corrected in the same commit).

## Known Issues

- See `planning/v0.75.0-universal-code-validation.md` Section 15 ("Remaining limitations") for the current, authoritative list: signature/parameter-role checking is positional-and-literal-only and only parses the `.. function::`-directive documentation style; precondition coverage is four families (`invpd`, `inv`, `solpd`, `chol`) out of GAUSS's full command surface; predicted-output verification covers only a handful of literal patterns, and this milestone's own live evaluation shows DETECTION itself (not just verification) still needs continued hardening against real model output shapes; the documentation-derived concept index's false-ambiguity risk is mitigated (the specific pronoun/auxiliary-word class found live is fixed) but not eliminated in general; model dependence remains real (non-standard `;`-vs-`,` matrix-literal syntax and wrong numeric predictions were both observed live again in this milestone's own evaluation).

## Next Steps

None committed. Do not start `v0.76` (or any controlled-execution-handoff milestone) without an explicit, separate decision from the user — this is a hard workflow rule (see `CLAUDE.md`), and is doubly true here since `planning/v0.75.0-universal-code-validation.md`'s own Section 16 explicitly recommends against it for now. If/when a next milestone is requested, read that file's Section 15/16 first.

Do not start `v0.76` (or any controlled-execution-handoff milestone) without an explicit, separate decision from the user — this is a hard workflow rule (see `CLAUDE.md`), and is doubly true here since `planning/v0.75.0-universal-code-validation.md`'s own Section 16 explicitly recommends against it for now.

## Handoff Notes

- Real-environment paths referenced in this session (Ollama endpoint `http://localhost:11434`, GAUSS executable `C:\gauss26\tgauss.exe`, docs-root `C:/Users/eclow/Documents/GitHub/docs/docs`, config file `C:\Users\Owner\.gauss-ai\config.json`) are non-secret and already referenced elsewhere in this repo — safe to reuse in future sessions on this same machine for any further live-evaluation work.
- Working tree should be clean once this session's commit lands — verify with `git status` before resuming.
