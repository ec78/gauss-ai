# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

None active. `v0.74.0 — Deterministic Pre-Execution Validation & Grounding Coverage Expansion` is **complete, committed, tagged, pushed, and released**. Per this repository's own workflow rule (see `CLAUDE.md`), the next milestone should NOT be started automatically — it needs a deliberate decision from the user, informed by `planning/v0.74.0-pre-execution-validation.md`'s own recommendation (Section 16: ready for alpha testing of pre-execution validation; NOT ready for a controlled-execution-handoff milestone yet).

## Completed Work

- `v0.70.0`–`v0.74.0` are complete, committed, tagged, pushed, and released. Latest: tag `v0.74.0`, commit `83f45aa`, release at `https://github.com/ec78/gauss-ai/releases/tag/v0.74.0`.
- `v0.74.0` added two new modules: `scripts/gauss_doc_concept_index.py` (a documentation-derived concept index supplementing the `v0.73.0` 5-entry curated alias table) and `scripts/gauss_pre_execution_validation.py` (documented call-signature extraction/compatibility checking, a small set of deterministic documented-precondition validators, and an explicit `INELIGIBLE`/`REQUIRES_CLARIFICATION`/`ELIGIBLE_FOR_VALIDATION` verdict). Full design, live-evaluation evidence, and honest limitations are in `planning/v0.74.0-pre-execution-validation.md` (its own 16-section readiness assessment) — read that file rather than asking for a re-summary.
- Four real defects were found live during `v0.74.0`'s own development and fixed within the milestone (see that planning doc's Section 8/9): corpus-generic-word false matches in the new derived index against the real ~2,063-file docs corpus; GAUSS comments mistaken for function calls; a builtin inconsistently labeled "not documented" between two checkers; a cross-turn false positive on a function grounded only in an earlier conversation turn. One limitation was found and honestly disclosed but NOT fixed: the new eligibility computation only runs for `CODE_GENERATION`-classified turns, not QA-classified code-shaped answers.
- `CLAUDE.md`/`PROJECT_STATUS.md` were introduced earlier in this session (previously neither existed) — a lightweight persistent-context system so future sessions don't depend on chat history.

## Decisions

- Nothing pending. All `v0.74.0` design decisions are recorded in `planning/v0.74.0-pre-execution-validation.md` (signature-extraction approach, precondition-validator scope, eligibility rule, document-frequency keyword filter, etc.) — that file is now the durable record, not this one.

## Tests / Validation

- Full suite as of the `v0.74.0` release: **42 test files, 1,311 test functions, all passing**. Zero diff on every core execution/repair/verification/approval module.
- Live evaluation: category `64.x` (10 scenarios), run against the real local Ollama service and `qwen2.5-coder:7b`, transcripts in `evaluations/runs/2026-09-12-code-assistant-pre-execution-validation-run-*.md`. A bounded set of real `tgauss.exe -b` spot checks were also run (5 examples: `meanc`, `reshape`+`meanc`, valid `invpd`, invalid `invpd`, `sumc`) — all results recorded in the planning doc's Section 10.
- `gauss-ai version`/`doctor`/an end-to-end conversational smoke test (Q&A → grounded generation → `invpd` precondition violation → execution-boundary redirect) were all re-verified against the real installed CLI before release.
- `python scripts/check_release_readiness.py` passes with only the same pre-existing, previously-documented historical warnings (nothing new introduced by `v0.74.0`).

## Known Issues

- Carried over and expanded from `v0.73.0` — see `planning/v0.74.0-pre-execution-validation.md` Section 15 ("Remaining limitations") for the current, authoritative list: argument-count-only signature checking (no order/type/shape); only one precondition family (`invpd`) has a deterministic validator; the documentation-derived concept index has no synonym awareness (a real, disclosed near-miss: "maximum value" resolved toward `maxindc` instead of the more fitting `maxc`); the QA-intent eligibility gap noted above; model dependence remains real (the exact `tscsmtControl` hallucination reproduced live again in this milestone's own evaluation).

## Next Steps

None committed. Do not start `v0.75` (or any controlled-execution-handoff milestone) without an explicit, separate decision from the user — this is a hard workflow rule (see `CLAUDE.md`), not just a suggestion, and is doubly true here since `planning/v0.74.0-pre-execution-validation.md`'s own Section 16 explicitly recommends against it for now. If/when a next milestone is requested, read that file's Section 15/16 first.

## Handoff Notes

- This session is ending here at the user's own request ("continue with v0.74, then start a fresh session after that"). A fresh session can resume purely from `CLAUDE.md` + this file + `git log`/`git status` + `planning/v0.74.0-pre-execution-validation.md` — no chat history dependency.
- Real-environment paths referenced in prior work (Ollama endpoint `http://localhost:11434`, GAUSS executable `C:\gauss26\tgauss.exe`, docs-root `C:/Users/eclow/Documents/GitHub/docs/docs`) are non-secret and already referenced elsewhere in this repo (`README.md`, `scripts/README.md`) — safe to reuse in future sessions on this same machine for any further live-evaluation work.
- Nothing is currently uncommitted or in a half-finished state — `git status` should be clean at the point this file was last written.
