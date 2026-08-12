# v0.69.0 - Alpha Feedback Integration and AI-Assisted Repair Draft Generation

This milestone responds to five real observations from the first private alpha session (`v0.68.0`) with product-experience improvements, and implements the first, deliberately narrow version of AI-assisted repair-draft candidate generation — without redesigning the safety architecture. The pipeline remains Execution → Interpretation → Diagnosis → Strategy → Draft → Application → Verification → Review; no existing approval, application, verification, or review guarantee was weakened.

## Alpha Findings Addressed

1. **Workspace-parent configuration confusion on failure** — `gauss-ai init`'s write-check warning now explicitly states the value was NOT SAVED, both inline and in a new end-of-run summary line, instead of silently continuing.
2. **Runner-selection prompt lacked explanation** — `gauss-ai init` now explains what `fake` (no real GAUSS, safe, the default) and `gauss` (runs your real, configured executable) mean immediately before the prompt.
3. **Line numbers requested before evidence was shown** — the guided workflow now always calls the new `suggest-repair-draft` step, which prints the detected error and diagnosis evidence, immediately after strategy approval and before any line-number prompt.
4. **Users expect the assistant to propose drafts, not just strategy** — addressed by AI-assisted candidate generation (below).
5. **Too many internal stages exposed** — when a candidate is available, five free-text prompts (line start, line end, operation, description, replacement text) collapse into a single accept/edit/reject decision. No approval step itself was removed, hidden, or merged.

## AI-Assisted Repair Draft Generation

New module `scripts/gauss_repair_draft_generation.py`. "AI-assisted" here means bounded, deterministic, catalog-and-pattern-driven generation — this repository has no LLM integration anywhere, and this module adds none. It recognizes exactly one safe, unambiguous source pattern in this first version: G0105's own catalog-verified empty-assignment trigger (`x = ;`). Every other cataloged error code, and every non-matching G0105 occurrence, honestly reports `no_candidate_available` rather than fabricating a guess — mirroring `gauss_repair_planner.py`'s own `BLOCKED_BY_MISSING_SOURCE` precedent, applied one layer further, to literal code instead of only inspection strategies. Every candidate's confidence is capped at `medium` (never `high`), and its reasoning always explicitly discloses the substituted value as a placeholder, never a claim about the user's actual intent.

## Where a Candidate Plugs Into the Existing Pipeline

`RepairDraft`'s own structural model (`gauss_repair_draft.py`) already bans literal code tokens from its description fields, and its fixed boundary statement already reads "No code was generated" — both remain true unchanged. A candidate's `suggested_operation`/`suggested_description` are code-token-free text used only to pre-fill `repair-draft`'s existing `--operation`/`--description` arguments (verified by a dedicated regression test against `gauss_repair_draft`'s own banned-token list). The candidate's actual code (`proposed_replacement_text`) reaches the pipeline only as the same `apply-repair --replacement-text` argument a manual tester has always had to supply by hand — after strategy approval, draft construction, draft approval, application approval, and a freshly re-evaluated application gate, exactly as before. `gauss_repair_application.py`'s own "no content is generated, inferred, or reconstructed by this module" claim remains true unchanged.

## New Adapter Command

`suggest-repair-draft` (no arguments) — requires an existing repair plan and the pending request's source code; returns zero or more candidates with affected statement, proposed replacement, reasoning, and confidence, plus an explicit "proposal only" disclosure. Available identically through the lower-level REPL and the guided workflow — the guided workflow calls it via the same `handle_line(...)` path every other step uses, never a second implementation.

## Guided Workflow UX

Immediately after strategy approval, the guided workflow now always runs `suggest-repair-draft`. If exactly one candidate is generated, the user is asked directly to accept, edit, or reject it; if more than one, the user first chooses which to review. Accepting fills in the draft's line range/operation/description and the eventual `apply-repair --replacement-text` from the candidate. Editing keeps the candidate's line range/operation/description but lets the user supply their own replacement text. Rejecting (or no candidate being available) falls back to exactly the prior fully manual entry, unchanged. Immediately before the final "approve applying" question, the exact replacement text about to be applied is now printed again, regardless of its source.

## Tests Added

21 new tests in `scripts/test_gauss_repair_draft_generation.py` (honest no-candidate cases across every not-applicable execution phase, real single/multi-candidate generation, indentation preservation, a hard cap on candidate count, never-fabricated-certainty, no-banned-code-token compatibility with `gauss_repair_draft.py`, determinism, and an architectural test locking the generator registry to exactly one error code). 8 new tests in `scripts/test_gauss_ai_guided_repair.py` (accept/edit/reject flows against real applied file content, evidence-before-manual-entry ordering, multi-candidate selection, and safety-boundary regressions proving an accepted candidate still requires independent draft/application approval). 7 new tests in `scripts/test_gauss_code_assistant_cli.py` (command wiring, honest no-candidate output, reset behavior, and full pipeline compatibility from candidate fields through to a genuinely applied file). 2 new tests in `scripts/test_gauss_ai_init.py` (the workspace-parent-failure and runner-explanation messaging fixes).

## Full Regression Results

All 37 test files pass, zero regressions. Zero diff on every core application/verification module: `gauss_repair_application.py`, `gauss_repair_application_approval.py`, `gauss_repair_application_gate.py`, `gauss_repair_draft_approval.py`, `gauss_verification_execution.py`, `gauss_verification_review.py`, plus `gauss_repair_draft.py`, `gauss_repair_planner.py`, `gauss_error_catalog.py`, `gauss_execution_diagnostics.py`, and `gauss_execution_interpreter.py`.

## Real Alpha Validation

Every user-facing scenario was driven through the installed `gauss-ai` entry point (a real, dedicated `pip install -e .` venv), invoked as a subprocess. Real GAUSS 26.1.1 (`c:\gauss26\tgauss.exe`) reproduced G0105 for both an accept and an edit full repair-application-verification-review cycle, and reproduced G0036 to prove the honest no-candidate fallback for a code this first version does not cover. Fake mode was used to validate reject-to-manual-entry and multi-candidate selection. The original source file was independently confirmed byte-for-byte unchanged after every run. `gauss-ai init`'s two messaging fixes were confirmed via the installed CLI with a deliberately unwritable path and a fresh, isolated configuration.

## 59.x Benchmark Results

A new `59.x` Alpha Feedback Integration and AI-Assisted Repair Draft Generation category (ten prompts) was fully evaluated against real, executed evidence — real GAUSS repair cycles through the installed CLI, dedicated regression tests for transcript ordering and approval independence, and a `git diff`/source-scan architectural proof. **10/10 Passed at 4.0. Zero defects found.**

## Evaluation Tracking

`check_evaluation_tracking.py --json` reports 554 prompt IDs, 554 coverage rows, 521 run files referenced, 526 index entries, 0 errors, and the same 3 pre-existing historical warnings carried from prior milestones — `overall_pass: true`.

## Release Readiness

`check_release_readiness.py` — PASS (`validate_all_evidence.py` PASS, `check_evaluation_tracking.py` PASS).

## Supported Alpha Environment

**Windows**, verified against **GAUSS 26.1.1** for real execution. Python 3.10+. Fake-mode testing has no OS-specific dependency but has only been exercised on Windows. macOS/Linux real-GAUSS execution is not claimed or supported.

## Alpha Readiness Classification

**Private Alpha.** Real alpha feedback was incorporated for the first time, and the first version of AI-assisted repair drafting was added and validated end to end against real GAUSS, with zero defects found and every existing safety boundary independently re-proven unbypassable through the new path. Not yet broader-alpha-ready: candidate-pattern coverage remains deliberately limited to one error code, and real-GAUSS verification remains bounded to one machine, one GAUSS version, and Windows only.

## Not Implemented

Broader candidate-pattern coverage beyond G0105's empty-assignment case; any real LLM/external-model integration; automatic acceptance or application of a candidate; automatic rerun/retry; autonomous repair; rollback; multi-file candidates; a conversational chatbot; IDE integration; project-wide reasoning; durable sessions; new approval layers.

## Recommendation for the Next Milestone

Gather further real alpha feedback on the new candidate-acceptance UX, and consider whether a second, similarly bounded and independently verified source pattern (for a different cataloged error code) is warranted before broadening pattern coverage further. This milestone deliberately does not request or imply that authorization.
