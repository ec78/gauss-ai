# v0.62.0 - Bounded Single-File Repair Application Transaction

This release implements Section 14 (Application Transaction) of `planning/v0.58.0-repair-application-safety-design.md` under a deliberately conservative bound. **`scripts/gauss_repair_application.py` is the first module in this repository's history capable of writing to a real file.** It is bounded to exactly one existing UTF-8 `.gss` file, in exactly one workspace, for exactly one already-approved `RepairDraft` that has passed strategy approval, draft approval, application approval, and a freshly re-evaluated Application Gate.

## Evaluated

- A new `52.x` Repair Application Transaction benchmark category was added (ten prompts, matching coverage rows) and **fully evaluated** against real, executed evidence — including a genuine on-disk file modification, not simulated: 10/10 Passed at 4.0, 0 Critical/Major/Minor defects.

## Added

- `scripts/gauss_repair_application.py`: `apply_repair(...)` performs, in order: re-validate source identity (a real, hash-verified read via `gauss_workspace_file_reader.read_workspace_file(...)`), re-evaluate the application gate (`evaluate_application_gate(...)`, called fresh, right before any write), create a workspace-contained backup, construct and validate an in-memory candidate from caller-supplied `replacement_text`, write a temporary file in the target's own directory, atomically replace the target (`os.replace(...)`), verify the resulting hash, and return an immutable `ApplicationResult`.
- `ApplicationTransactionOutcome` (`applied`/`blocked`/`failed`), `ApplicationTransactionCheck` (16 named checks), `ApplicationResult`, `BackupIdentity`.
- CLI `apply-repair <draft_digest> --replacement-text TEXT`/`show-application-result` commands, mirroring `approve-repair-application`'s own stale-digest-rejection behavior.

## No Content Is Generated

Every repair-layer module through `v0.61.0` was deliberately incapable of carrying literal replacement code. This module is the one place literal content is finally needed, and it is supplied **explicitly by the caller** — never inferred, generated, or reconstructed. This module validates structural well-formedness only (non-empty, changed, bounded size, no NUL bytes, bounded line count); it never validates GAUSS syntax or semantic correctness.

## Fail Closed, Always

Every check is evaluated in order; the first failure halts the transaction immediately, and `ApplicationResult.checks` contains only the checks actually reached. Two failure categories exist below `applied`:

- **`blocked`** — a precondition failed before any write was attempted. The target file is byte-for-byte unchanged in every blocked scenario, verified directly by test.
- **`failed`** — a write was attempted (a temp file was created) but did not reach a verified, successful state (temp-write failure, atomic-replace failure, or a post-write hash mismatch). The backup is the recovery path in every case; no automatic rollback, retry, or rerun occurs.

## Backup Model

Exactly one backup per attempt, workspace-contained, named from the target's own relative path plus a content-hash prefix plus a timestamp. **Never overwritten** — a name collision appends a numeric suffix and retries. **Never deleted**, including when a transaction subsequently blocks or fails on a later step (backup creation happens before candidate construction/validation, per this milestone's own specified step order).

## Atomic Replace, Not Best-Effort

`os.replace(...)` is the sole target-mutation mechanism — atomic when the temp file lives in the target's own directory, a hard precondition this module enforces by construction. Unavailability or failure reports `failed`, never a fallback to a non-atomic direct overwrite. Both the replace and temp-write steps are injectable (mirroring `WorkspaceRegistry`'s own `clock`/`id_factory` convention), enabling deterministic failure-path tests without OS-level flakiness.

## No Rerun

`ApplicationResult` carries no rerun field of any kind. The module imports no execution/orchestration module. Every CLI response discloses `rerun_performed: false` unconditionally, plus a `next_step` line naming the separate, ordinary `request`/`plan`/`confirm`/`execute` confirmation still required before the repaired code is ever run.

## Not Implemented

Automatic rollback/restore, durable audit, multi-file repair, batch application, directory creation, whole-file replacement, patch merging, diff fuzzing, AST rewriting, cloud storage, durable sessions, automatic reruns, automatic retries. `scripts/gauss_repair_planner.py`, `scripts/gauss_repair_approval.py`, `scripts/gauss_repair_draft.py`, `scripts/gauss_repair_draft_approval.py`, `scripts/gauss_repair_application_approval.py`, and `scripts/gauss_repair_application_gate.py` have zero diff.

## Documentation Updates

`README.md`, `ROADMAP.md` (new `v0.62.0` section; the "Repair Application" future candidate updated to reflect the transaction as implemented), `KNOWN_LIMITATIONS.md`, `CHANGELOG.md`, and the new `docs/gauss-repair-application.md`.

## Remaining Limitations

- Single-file, single-attempt only — no multi-file repair, no batch application.
- No automatic rollback — a backup exists, but restoring it is not implemented anywhere in this module.
- No durable audit trail beyond the in-memory `ApplicationResult` for the current process.
- `replacement_text` is never validated for GAUSS syntax or semantic correctness — only structural well-formedness.
- Process-local only — `last_application_result` is not durable, not shared across processes, cleared by `reset`.

## Next Recommended Milestone

With a bounded, tested, single-file transaction now in place, the natural next candidate is Section 20's separately-scoped rerun workflow — wiring an applied repair's resulting code identity into a fresh, ordinary execution request through the existing `request`/`plan`/`confirm`/`execute` path, explicitly not a repair-specific execution shortcut. This milestone deliberately does not request or imply that authorization.
