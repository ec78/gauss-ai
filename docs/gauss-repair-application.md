# GAUSS Repair Application Transaction

## Purpose

`scripts/gauss_repair_application.py` (`v0.62.0`) is the first module in this repository's history capable of writing to a real file. It implements Section 14 (Application Transaction) of `planning/v0.58.0-repair-application-safety-design.md`, bounded to exactly one existing UTF-8 `.gss` file, in exactly one workspace, for exactly one already-approved `RepairDraft` that has passed every upstream layer: strategy approval, draft approval, application approval, and a freshly re-evaluated Application Gate.

## What This Module Is Not

**Not a general-purpose file editor.** One file, one workspace, one bounded line-range substitution per call. No multiple files, new files, renames, deletes, directory creation, whole-file replacement, binary content, non-UTF-8 content, patch merging, diff fuzzing, or AST rewriting.

**Not a code generator.** The exact replacement text for the approved line range must be supplied explicitly by the caller (`replacement_text`) — this module never infers, generates, or reconstructs content. It validates only that the resulting substitution is well-formed, bounded, UTF-8 text; it never validates GAUSS syntax or semantic correctness.

**Not a rerun trigger.** Applying a repair never executes anything. `ApplicationResult` carries no rerun field of any kind, the module imports no execution/orchestration module, and every CLI response explicitly discloses `rerun_performed: false` plus the requirement that a separate, ordinary `request`/`plan`/`confirm`/`execute` confirmation is needed before the repaired code is ever run.

**Not a rollback mechanism.** A backup is always created and never deleted, but this module never restores one automatically — no automatic rollback, retry, or rerun occurs anywhere in this module.

## Position in the Reasoning Pipeline

```
Execution
  -> ... (Interpretation, Verified Knowledge, Diagnosis, Repair Planning, all prior layers)
  -> Repair Draft Approval          (gauss_repair_draft_approval.py, v0.60.0)
  -> Repair Application Approval    (gauss_repair_application_approval.py, v0.61.0)
  -> Repair Application Gate        (gauss_repair_application_gate.py, v0.61.0)
  -> Repair Application Transaction (this module, v0.62.0)
  -> (Separate rerun approval, future -- the existing request/plan/confirm/execute path)
```

## The Ten-Step Transaction

1. **Re-validate source identity** — a real, hash-verified read via `gauss_workspace_file_reader.read_workspace_file(...)`, the one real content-hash-computing read path in this repository.
2. **Re-evaluate the application gate** — a fresh `evaluate_application_gate(...)` call, right before any write, re-verifying the entire four-record approval chain and structural draft validation in one call.
3. **Create a workspace-contained backup** — before candidate construction even begins, per this milestone's own specified step order.
4. **Construct the repaired candidate** — a bounded, in-memory line-range substitution using the caller-supplied `replacement_text`.
5. **Validate the candidate** — non-empty, actually changed, within a size ceiling, no NUL bytes, within a line-count bound.
6. **Write a temporary file** in the target's own directory (a hard precondition for atomic replace to be atomic at all).
7. **Atomically replace the target** via `os.replace(...)` — fails closed, never falls back to an unsafe direct overwrite.
8. **Verify the resulting hash** against the constructed candidate's own hash.
9. **Record an immutable `ApplicationResult`.**
10. **Stop.** No rerun is triggered anywhere.

Eighteen named checks are recorded along the way (`ApplicationTransactionCheck`); the first failure halts the transaction immediately, so `ApplicationResult.checks` contains only the checks actually reached — its length is itself meaningful, verified evidence of exactly how far a given attempt got. Two of the eighteen — `REPLACEMENT_TEXT_NON_EMPTY` and `CANDIDATE_ENCODABLE` — were added during `v0.63.0`'s real-filesystem evaluation, after that evaluation found an empty/whitespace-only replacement was silently applied as a line deletion, and a non-UTF-8-encodable replacement raised an uncaught exception instead of a clean `blocked` result. See `planning/v0.63.0-repair-application-evaluation.md` for the full evaluation record.

## Outcomes

| Outcome | Meaning | Target file state |
|---|---|---|
| `applied` | Full success through step 8 | Modified, verified, byte-identical to the constructed candidate |
| `blocked` | A precondition failed before any write was attempted | Byte-for-byte unchanged (verified directly by test) |
| `failed` | A write was attempted (a temp file was created) but did not reach a verified, successful state | May or may not have been replaced, depending on exactly which step failed; the backup is the recovery path in every case |

## Backup Model

Exactly one backup per attempt: `<relative_path>.prerepair-<hash_prefix>-<timestamp>.bak`, written as a sibling of the target inside the same workspace (no new directory is ever created). A backup is **never overwritten** — if the computed name is taken, a numeric suffix is appended and retried. The backup's own content hash is verified immediately after writing; a mismatch blocks before any target write. Backups are never deleted, including when a transaction subsequently blocks or fails on a later step.

## Fail-Closed, Never Best-Effort

Every check that can fail, does block or fail the entire transaction — there is no fallback, no partial application, no merge, no fuzzy patch application, and no continuation after a failed backup, failed validation, or failed hash verification. `os.replace(...)` is the sole replace mechanism; if it is unavailable or fails, the transaction reports `failed` rather than falling back to a non-atomic write.

## Relationship to Every Upstream Layer

This module calls `evaluate_application_gate(...)` exactly as the CLI's own `check-repair-application-gate` command does, and never re-derives approval-chain logic a second way. It calls `gauss_workspace_file_reader.read_workspace_file(...)` and `gauss_workspace.WorkspaceRegistry.resolve_within_workspace(...)` rather than re-implementing hashing or path containment. `MAX_EDIT_RANGE_LINES` is reused directly from `gauss_repair_draft.py`'s own Phase 2 validation bound, and `MAX_CANDIDATE_BYTES` is reused directly from the file reader's own reviewed size ceiling.

## CLI Usage

```
gauss-mvp> apply-repair 39b11c4a12f3... --replacement-text "x = 2 + 2;"
REAL_WORKFLOW: Repair application transaction executed against the real workspace filesystem.
application_boundary: The repair was applied to the target file. A backup of the pre-application content was created and preserved. No GAUSS execution occurred. No rerun was performed. A separate, explicit confirmation is required before any future rerun.
outcome: applied
pre_application_content_hash: ...
post_application_content_hash: ...
backup_relative_path: model.gss.prerepair-...-....bak
file_modified: true
backup_created: true
rerun_performed: false
next_step: a separate, explicit rerun confirmation (request/plan/confirm/execute) is required before executing the repaired code; this command never triggers one.

gauss-mvp> show-application-result
```

`apply-repair` requires the caller to supply the exact current `draft_digest`, mirroring `approve-repair-application`'s own stale-digest-rejection behavior. `reset` clears `last_application_result`.

## Limitations

- Single-file, single-attempt only — no multi-file repair, no batch application.
- No automatic rollback — a backup exists, but restoring it is not implemented anywhere in this module.
- No durable audit trail beyond the in-memory `ApplicationResult` for the current process.
- `replacement_text` is never validated for GAUSS syntax or semantic correctness — only structural well-formedness (non-empty, changed, bounded, UTF-8, no NUL bytes).
- Process-local only — `last_application_result` is not durable, not shared across processes, cleared by `reset`.
- No statistical or methodological validity assessment — unchanged from every prior stage.
