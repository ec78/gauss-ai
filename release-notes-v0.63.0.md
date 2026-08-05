# v0.63.0 - Repair Application Evaluation and Hardening

This is an **evaluation milestone**. `scripts/gauss_repair_application.py` (`v0.62.0`) — this repository's first module capable of writing to a real file — was exercised under real filesystem conditions across twenty named scenarios, using the actual application workflow (direct module calls and the real CLI path) against real, on-disk, temp-directory-backed workspaces and genuine `.gss` files. No new capability was added.

## Two Genuine Defects Found and Fixed

Both are narrowly-scoped, evaluation-driven fixes to the transaction module itself — no capability was broadened, no rerun/rollback/durable-session logic was added, and no other module was touched.

**1. Empty or whitespace-only `replacement_text` silently deleted the edit range.** Zero replacement lines spliced into the file is indistinguishable from *deleting* the edit range, and the transaction applied this without any distinct signal — a scope violation ("no deletes") this repository's own design explicitly excludes. **Fixed**: a new `REPLACEMENT_TEXT_NON_EMPTY` check blocks with reason `replacement_text_empty` before candidate construction ever runs.

**2. An uncaught `UnicodeEncodeError` for non-UTF-8-encodable replacement text.** A `replacement_text` containing a lone UTF-16 surrogate (or any other content not representable in UTF-8) raised an uncaught exception straight out of `apply_repair(...)`, crashing the caller — a direct violation of the module's own fail-closed design, since every other malformed-input scenario returns a clean `blocked` result. **Fixed**: the encode call is now wrapped; a `UnicodeEncodeError` is caught and converted into a `blocked` result with reason `candidate_not_utf8_encodable`.

A successful application now reports **18 named checks** (previously 16) — purely additive; no existing check's name, ordering, or semantics changed.

## Evaluated

All twenty named dimensions from the authorizing task were exercised for real and are documented with genuine evidence in the ten `53.x` run files: beginning/middle/end-of-file edits, empty replacements, Unicode handling, malformed replacement text, stale source hash, workspace mismatch, path mismatch, backup creation, backup collision handling, atomic replacement failure, interrupted-transaction behavior, post-write hash verification, repeated application attempts, `ApplicationResult` correctness, target-file integrity after blocked operations, and proof of zero side effects (no rerun, no approval mutation, no planning-artifact mutation). **10/10 Passed at 4.0.**

## Testing

`scripts/test_gauss_repair_application.py` grew from 27 to 33 tests: `test_28`/`test_29` are direct regression tests for the two fixes; `test_30`-`test_33` directly cover beginning/middle/end-of-file edits, Unicode content, and repeated sequential applications — dimensions this evaluation specifically probed. `test_09` was updated to reflect the more specific blocking reason the first fix introduced. Full existing regression suite (26 test files) re-run and passing unchanged.

## Historical Records Left Untouched

`CHANGELOG.md`'s `v0.62.0` entry, `release-notes-v0.62.0.md`, and the `52.x` benchmark prompt/run files still correctly state "16 checks" — accurate at the time they were written. This repository's long-standing policy against rewriting historical evaluation records extends to historical release notes and changelog entries as well.

## Not Implemented

Rerun, rollback, durable sessions — none were added, per this milestone's own explicit scope. `scripts/gauss_repair_planner.py`, `scripts/gauss_repair_approval.py`, `scripts/gauss_repair_draft.py`, `scripts/gauss_repair_draft_approval.py`, `scripts/gauss_repair_application_approval.py`, and `scripts/gauss_repair_application_gate.py` have zero diff.

## Documentation Updates

`README.md`, `ROADMAP.md` (new `v0.63.0` section), `KNOWN_LIMITATIONS.md`, `CHANGELOG.md`, and `docs/gauss-repair-application.md` (updated to reflect 18 checks and the two fixes).

## Recommendation for the Next Milestone

With a bounded, evaluated, and hardened transaction now in place — zero further defects found across eighteen of the twenty evaluated scenarios, and both defects that were found immediately fixed within this same milestone — the evidence supports proceeding to the design's own Section 20: a separately-scoped rerun workflow, wiring an applied repair's resulting code identity into a fresh, ordinary execution request through the existing `request`/`plan`/`confirm`/`execute` path, explicitly never a repair-specific execution shortcut. This milestone deliberately does not request or imply that authorization.
