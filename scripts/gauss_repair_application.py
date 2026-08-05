"""Bounded, deterministic, single-file repair application transaction.

Position in the reasoning pipeline:

    ... -> Repair Draft Approval (gauss_repair_draft_approval.py, v0.60.0)
        -> Repair Application Approval (gauss_repair_application_approval.py, v0.61.0)
        -> Repair Application Gate (gauss_repair_application_gate.py, v0.61.0)
        -> Repair Application Transaction (this module, v0.62.0)
        -> (Separate rerun approval, future -- the existing
            request/plan/confirm/execute path, not repair-specific)

**This is the first module in this repository's history capable of writing
to a real file.** Every module through `v0.61.0` was zero-I/O by design;
this module is the deliberate, narrowly-scoped exception, implementing
Section 14 (Application Transaction) of
`planning/v0.58.0-repair-application-safety-design.md` under the conservative
bound `planning/v0.62.0-bounded-repair-application.md` sets.

Scope, restated from the authorizing task: exactly one existing UTF-8 `.gss`
file, in exactly one workspace, for exactly one already-approved
`RepairDraft` that has passed strategy approval, draft approval, application
approval, and a freshly re-evaluated Application Gate. A bounded, structured
line-range replacement only -- never multiple files, new files, renames,
deletes, directory creation, whole-file replacement, binary content,
non-UTF-8 content, patch merging, diff fuzzing, AST rewriting, cloud
storage, durable sessions, automatic reruns, automatic rollback, or
automatic retries. No code path in this module launches GAUSS, calls an
execution helper, or triggers a rerun.

**No content is generated, inferred, or reconstructed by this module.** The
exact replacement text for the approved line range must be supplied
explicitly by the caller (`replacement_text`) -- exactly the same
"never generate code" boundary every prior repair-layer module already
enforces, now applied to the one module that actually needs literal
replacement content in order to write anything. This module does not
validate GAUSS syntax or semantic correctness; it validates only that the
resulting file is a well-formed, bounded, UTF-8 text substitution.

**Fail closed, always.** Every precondition is re-verified immediately
before any write is attempted -- source content hash, the full four-layer
approval chain (via a fresh `evaluate_application_gate(...)` call), and
candidate well-formedness. Any single check failing blocks the entire
transaction; nothing is written, and no fallback or partial write path
exists. A backup of the pre-application content is created before any
write is attempted, is never overwritten, and is never silently deleted
-- including when the transaction subsequently blocks.

This module reuses, rather than re-derives, every precedent it can:
`gauss_workspace_file_reader.read_workspace_file(...)` for the one real,
verified content-hash-computing read path in this repository;
`gauss_workspace.WorkspaceRegistry.resolve_within_workspace(...)` for path
containment (symlink-following, traversal-rejecting, identical to every
other workspace-bound module); `gauss_repair_application_gate.
evaluate_application_gate(...)` for the full approval-chain re-verification;
`gauss_repair_draft.MAX_EDIT_RANGE_LINES` for the same large-patch-abuse
bound Phase 2 validation already established.
"""

from __future__ import annotations

import enum
import hashlib
import os
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import gauss_repair_application_approval as application_approval_mod
import gauss_repair_application_gate as gate_mod
import gauss_repair_draft as repair_draft_mod
import gauss_repair_draft_approval as draft_approval_mod
import gauss_repair_planner as repair_planner
import gauss_workspace as workspace_mod
import gauss_workspace_file_reader as file_reader_mod

#: Only this one file type is ever eligible for application, matching this
#: milestone's own absolute scope ("one existing UTF-8 .gss source file").
ALLOWED_APPLICATION_FILE_TYPE = "gss"

#: Reused directly from Phase 2 draft validation (`v0.59.0`) so the same
#: large-patch-abuse bound applies consistently at both layers.
MAX_EDIT_RANGE_LINES = repair_draft_mod.MAX_EDIT_RANGE_LINES

#: Reused directly from the file reader's own reviewed ceiling -- a
#: candidate is rejected outright if it would exceed this, never truncated.
MAX_CANDIDATE_BYTES = file_reader_mod.ABSOLUTE_MAX_BYTES

#: Fixed, always-present disclosures -- one per outcome category, never
#: dynamically composed per specific reason, so no disclosure can ever be
#: worded in a way that overstates what happened.
APPLIED_BOUNDARY_STATEMENT = (
    "The repair was applied to the target file. A backup of the pre-application content was created and "
    "preserved. No GAUSS execution occurred. No rerun was performed. A separate, explicit confirmation is "
    "required before any future rerun."
)
BLOCKED_BOUNDARY_STATEMENT = (
    "The repair was NOT applied. No byte of the target file was written. Any backup created before the block "
    "was preserved, never deleted, and is not itself evidence that anything was applied."
)
FAILED_BOUNDARY_STATEMENT = (
    "The repair application did not complete successfully. Any backup created before the failure was preserved, "
    "never deleted. No automatic rollback, retry, or rerun occurred. Manual review is required before any "
    "further attempt."
)


class ApplicationTransactionOutcome(enum.Enum):
    #: Full success: source verified fresh, gate passed, candidate valid,
    #: backup created and verified, write completed, post-write hash
    #: confirmed.
    APPLIED = "applied"
    #: A precondition failed before any write was attempted. The target
    #: file was never touched. A backup may or may not exist, depending on
    #: how far the transaction reached before blocking.
    BLOCKED = "blocked"
    #: A write was attempted (a temporary file was created) but did not
    #: reach a verified, successful state. The target may or may not have
    #: been replaced, depending on exactly which step failed; the backup
    #: is the recovery path in every case.
    FAILED = "failed"


class ApplicationTransactionCheck(enum.Enum):
    SOURCE_HASH_FRESH = "source_hash_fresh"
    FILE_TYPE_ALLOWED = "file_type_allowed"
    APPLICATION_GATE_PASSED = "application_gate_passed"
    BACKUP_PATH_CONTAINED = "backup_path_contained"
    BACKUP_UNIQUE = "backup_unique"
    BACKUP_WRITTEN = "backup_written"
    BACKUP_HASH_VERIFIED = "backup_hash_verified"
    CANDIDATE_RANGE_WELL_FORMED = "candidate_range_well_formed"
    CANDIDATE_NON_EMPTY = "candidate_non_empty"
    CANDIDATE_CHANGED = "candidate_changed"
    CANDIDATE_WITHIN_SIZE_CEILING = "candidate_within_size_ceiling"
    CANDIDATE_NO_NUL_BYTES = "candidate_no_nul_bytes"
    CANDIDATE_WITHIN_LINE_BOUND = "candidate_within_line_bound"
    TEMP_WRITE_SUCCEEDED = "temp_write_succeeded"
    ATOMIC_REPLACE_SUCCEEDED = "atomic_replace_succeeded"
    POST_WRITE_HASH_MATCHES = "post_write_hash_matches"


@dataclass(frozen=True)
class ApplicationTransactionCheckResult:
    check: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class BackupIdentity:
    """A workspace-contained backup's own identity -- content hash computed
    at backup time, over the pre-application bytes actually written to the
    backup file. Never the target's own identity; a backup is a distinct
    file with its own path and hash."""

    relative_path: str
    content_hash: str
    size: int


@dataclass(frozen=True)
class ApplicationResult:
    """Immutable record of exactly one application-transaction attempt.
    Carries no rerun fields of any kind -- rerun is a separate, ordinary
    execution-confirmation concern (`request`/`plan`/`confirm`/`execute`),
    never implied or triggered by anything in this module."""

    application_id: str
    draft_digest: str
    workspace_id: str
    relative_path: str
    pre_application_content_hash: str
    post_application_content_hash: str | None
    backup: BackupIdentity | None
    outcome: str
    reason: str | None
    checks: tuple[ApplicationTransactionCheckResult, ...]
    applied_at: str
    application_boundary: str


class ApplicationBlockedError(Exception):
    """Not raised by `apply_repair(...)` itself -- reserved for callers that
    want a raise-on-block convenience wrapper. `apply_repair(...)` always
    returns an `ApplicationResult`, even for a blocked or failed outcome,
    exactly as every other layer in this pipeline returns a structured
    result rather than raising for an expected, named failure mode."""


def _boundary_for(outcome: ApplicationTransactionOutcome) -> str:
    if outcome == ApplicationTransactionOutcome.APPLIED:
        return APPLIED_BOUNDARY_STATEMENT
    if outcome == ApplicationTransactionOutcome.BLOCKED:
        return BLOCKED_BOUNDARY_STATEMENT
    return FAILED_BOUNDARY_STATEMENT


def _default_write_temp_file(directory: Path, prefix: str, content: bytes) -> str:
    """Writes `content` to a new, uniquely-named temporary file inside
    `directory` (the target's own parent directory -- required for
    `os.replace` to be atomic at all; see the design doc's platform
    caveats) and returns the temp file's own path as a string. Raises
    `OSError` on any failure; never partially writes and leaves a
    half-written file behind (the temp file is removed on a write error)."""
    fd, tmp_path = tempfile.mkstemp(dir=str(directory), prefix=prefix, suffix=".gauss-ai-tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(content)
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return tmp_path


def _backup_candidate_names(relative_path: str, pre_hash: str, timestamp: str) -> "list[str]":
    """Deterministic backup filename candidates, most-preferred first --
    derived from the target's own relative path plus the pre-application
    content-hash prefix plus a timestamp, per the design document's own
    naming convention (Section 15). A short numeric suffix is appended only
    if the preferred name is already taken, so a backup is NEVER overwritten
    (bounded to a small number of attempts; exhausting them is itself a
    hard failure, never a silent overwrite)."""
    hash_prefix = pre_hash[:12]
    base = f"{relative_path}.prerepair-{hash_prefix}-{timestamp}.bak"
    names = [base]
    for suffix in range(2, 1000):
        names.append(f"{relative_path}.prerepair-{hash_prefix}-{timestamp}-{suffix}.bak")
    return names


def _split_lines_preserving_terminators(text: str) -> "list[str]":
    """Splits into lines keeping each line's own terminator attached (via
    `str.splitlines(keepends=True)`), so reassembly never silently
    normalizes CRLF/LF line endings for any untouched line -- exactly the
    "no silent line-ending normalization" rule the design document requires
    (Section 7)."""
    return text.splitlines(keepends=True)


def _construct_candidate(
    original_content: str, edit_scope: "repair_draft_mod.EditScope", replacement_text: str
) -> "tuple[str | None, str | None]":
    """Pure, in-memory construction only -- no I/O. Returns
    `(candidate_content, None)` on success or `(None, reason)` if the
    edit range is not well-formed against the actual, freshly-read content.
    Never silently truncates an out-of-range slice -- Python's own list
    slicing would do exactly that, so bounds are checked explicitly first."""
    lines = _split_lines_preserving_terminators(original_content)
    line_start = edit_scope.line_start
    line_end = edit_scope.line_end
    if not (isinstance(line_start, int) and isinstance(line_end, int)):
        return None, "edit_scope line_start/line_end are not integers"
    if line_start < 1 or line_end < line_start:
        return None, f"edit range [{line_start}, {line_end}] is not a valid, closed, positive range"
    if line_end > len(lines):
        return None, f"edit range [{line_start}, {line_end}] exceeds the freshly-read file's {len(lines)} line(s)"

    replacement_lines = replacement_text.splitlines(keepends=True)
    if replacement_lines and not replacement_lines[-1].endswith(("\n", "\r")):
        # Preserve a clean boundary with whatever line follows the edit
        # range: only add a terminator when a following line still exists,
        # matching the terminator convention already used by this file
        # (never invented from nothing when the replacement is the file's
        # own new last line).
        if line_end < len(lines):
            dominant = "\r\n" if "\r\n" in original_content else "\n"
            replacement_lines[-1] = replacement_lines[-1] + dominant

    candidate_lines = lines[: line_start - 1] + replacement_lines + lines[line_end:]
    return "".join(candidate_lines), None


def apply_repair(
    *,
    repair_plan: "repair_planner.RepairPlan",
    repair_approval_record: object | None,
    repair_draft: "repair_draft_mod.RepairDraft",
    draft_approval_record: "draft_approval_mod.DraftApprovalRecord | None",
    application_approval_record: "application_approval_mod.ApplicationApprovalRecord | None",
    replacement_text: str,
    workspace_registry: "workspace_mod.WorkspaceRegistry",
    clock: Callable[[], float] = time.time,
    id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    replace_fn: Callable[[str, str], None] = os.replace,
    write_temp_file_fn: Callable[[Path, str, bytes], str] = _default_write_temp_file,
) -> ApplicationResult:
    """The single entry point. Performs, in order, exactly the ten steps
    `planning/v0.62.0-bounded-repair-application.md` specifies: re-validate
    source identity, re-evaluate the application gate, create a
    workspace-contained backup, construct the repaired candidate, validate
    it, write a temporary file, atomically replace the target, verify the
    resulting hash, record an immutable `ApplicationResult`, and stop. Any
    single failure blocks or fails the entire transaction -- there is no
    fallback and no partial-success path. Never triggers a rerun."""
    checks: "list[ApplicationTransactionCheckResult]" = []

    def record(check: ApplicationTransactionCheck, passed: bool, detail: str) -> None:
        checks.append(ApplicationTransactionCheckResult(check=check.value, passed=passed, detail=detail))

    def blocked(reason: str, *, backup: "BackupIdentity | None" = None, pre_hash: str = "") -> ApplicationResult:
        outcome = ApplicationTransactionOutcome.BLOCKED
        return ApplicationResult(
            application_id=id_factory(),
            draft_digest=draft_digest,
            workspace_id=artifact.workspace_id,
            relative_path=artifact.relative_path,
            pre_application_content_hash=pre_hash,
            post_application_content_hash=None,
            backup=backup,
            outcome=outcome.value,
            reason=reason,
            checks=tuple(checks),
            applied_at=str(clock()),
            application_boundary=_boundary_for(outcome),
        )

    def failed(reason: str, *, backup: "BackupIdentity | None", pre_hash: str) -> ApplicationResult:
        outcome = ApplicationTransactionOutcome.FAILED
        return ApplicationResult(
            application_id=id_factory(),
            draft_digest=draft_digest,
            workspace_id=artifact.workspace_id,
            relative_path=artifact.relative_path,
            pre_application_content_hash=pre_hash,
            post_application_content_hash=None,
            backup=backup,
            outcome=outcome.value,
            reason=reason,
            checks=tuple(checks),
            applied_at=str(clock()),
            application_boundary=_boundary_for(outcome),
        )

    draft_digest = repair_draft_mod.repair_draft_digest(repair_draft)
    artifact = repair_draft.source_identity.artifact

    # -- Step 1: re-validate source identity (a real, fresh, hash-verified read) --
    read_result = file_reader_mod.read_workspace_file(
        file_reader_mod.WorkspaceFileReadRequest(
            workspace_id=artifact.workspace_id,
            relative_path=artifact.relative_path,
            max_bytes=MAX_CANDIDATE_BYTES,
            allow_truncation=False,
        ),
        workspace_registry=workspace_registry,
    )
    if read_result.status != file_reader_mod.ReadStatus.COMPLETED.value:
        record(
            ApplicationTransactionCheck.SOURCE_HASH_FRESH, False,
            f"could not read the current target file ({read_result.error_code}): {read_result.error_message}",
        )
        return blocked(f"source_read_failed:{read_result.error_code}")

    hash_matches = read_result.checksum == repair_draft.source_identity.content_hash
    record(
        ApplicationTransactionCheck.SOURCE_HASH_FRESH, hash_matches,
        "freshly-read content hash matches the draft's own bound hash"
        if hash_matches
        else "the freshly-read content hash no longer matches the draft's own bound hash -- the source has changed",
    )
    if not hash_matches:
        return blocked("stale_source", pre_hash=read_result.checksum)

    file_type_ok = read_result.file_type == ALLOWED_APPLICATION_FILE_TYPE
    record(
        ApplicationTransactionCheck.FILE_TYPE_ALLOWED, file_type_ok,
        f"file type is {read_result.file_type!r}" if file_type_ok else f"only {ALLOWED_APPLICATION_FILE_TYPE!r} files are eligible for application; got {read_result.file_type!r}",
    )
    if not file_type_ok:
        return blocked("file_type_not_allowed", pre_hash=read_result.checksum)

    pre_hash = read_result.checksum
    original_content = read_result.content or ""

    # -- Step 2: re-evaluate the application gate, right before any write --
    current_source_identity = repair_draft_mod.SourceIdentity(
        artifact=artifact,
        content_hash=read_result.checksum,
        size=read_result.size_bytes or 0,
        encoding=read_result.encoding or "utf-8",
        line_range=repair_draft.source_identity.line_range,
        observed_at=str(clock()),
    )
    try:
        workspace_status = workspace_registry.get_workspace(artifact.workspace_id).status.value
    except workspace_mod.WorkspaceNotFoundError:
        workspace_status = None
    gate_result = gate_mod.evaluate_application_gate(
        repair_plan=repair_plan,
        repair_approval_record=repair_approval_record,
        repair_draft=repair_draft,
        draft_approval_record=draft_approval_record,
        application_approval_record=application_approval_record,
        current_source_identity=current_source_identity,
        workspace_status=workspace_status,
    )
    record(
        ApplicationTransactionCheck.APPLICATION_GATE_PASSED, gate_result.all_passed,
        "application gate passed every checkable precondition"
        if gate_result.all_passed
        else f"application gate failed: {', '.join(gate_result.failed_checks)}",
    )
    if not gate_result.all_passed:
        return blocked(f"gate_failed:{','.join(gate_result.failed_checks)}", pre_hash=pre_hash)

    target_path = workspace_registry.resolve_within_workspace(artifact.workspace_id, artifact.relative_path)
    if target_path is None:
        record(ApplicationTransactionCheck.BACKUP_PATH_CONTAINED, False, "target path no longer resolves inside the workspace")
        return blocked("target_path_escapes_workspace", pre_hash=pre_hash)

    # -- Step 3: create a workspace-contained backup, before anything else touches the filesystem --
    timestamp = str(clock()).replace(".", "-").replace(":", "-")
    backup_relative_candidates = _backup_candidate_names(artifact.relative_path, pre_hash, timestamp)
    backup_path: Path | None = None
    backup_relative_path: str | None = None
    for candidate_relative in backup_relative_candidates:
        candidate_path = workspace_registry.resolve_within_workspace(artifact.workspace_id, candidate_relative)
        if candidate_path is None:
            continue
        if not candidate_path.exists():
            backup_path = candidate_path
            backup_relative_path = candidate_relative
            break
    if backup_path is None or backup_relative_path is None:
        record(ApplicationTransactionCheck.BACKUP_PATH_CONTAINED, False, "no unique, workspace-contained backup path could be found")
        return blocked("backup_path_unavailable", pre_hash=pre_hash)
    record(ApplicationTransactionCheck.BACKUP_PATH_CONTAINED, True, f"backup path resolves inside the workspace: {backup_relative_path}")
    record(ApplicationTransactionCheck.BACKUP_UNIQUE, True, "no existing file occupies the chosen backup path")

    original_bytes = original_content.encode("utf-8")
    try:
        backup_path.write_bytes(original_bytes)
    except OSError as exc:
        record(ApplicationTransactionCheck.BACKUP_WRITTEN, False, f"failed to write backup file: {exc}")
        return blocked("backup_write_failed", pre_hash=pre_hash)
    record(ApplicationTransactionCheck.BACKUP_WRITTEN, True, f"backup written: {backup_relative_path}")

    backup_hash = hashlib.sha256(backup_path.read_bytes()).hexdigest()
    backup_hash_ok = backup_hash == pre_hash
    record(
        ApplicationTransactionCheck.BACKUP_HASH_VERIFIED, backup_hash_ok,
        "backup content hash matches the pre-application source hash"
        if backup_hash_ok
        else "backup content hash does NOT match the pre-application source hash -- backup integrity could not be confirmed",
    )
    backup_identity = BackupIdentity(relative_path=backup_relative_path, content_hash=backup_hash, size=len(original_bytes))
    if not backup_hash_ok:
        return blocked("backup_hash_mismatch", backup=backup_identity, pre_hash=pre_hash)

    # -- Step 4 & 5: construct and validate the repaired candidate (pure, in-memory) --
    candidate_content, construct_reason = _construct_candidate(original_content, repair_draft.edit_scope, replacement_text)
    range_ok = candidate_content is not None
    record(
        ApplicationTransactionCheck.CANDIDATE_RANGE_WELL_FORMED, range_ok,
        "edit range is well-formed against the freshly-read content" if range_ok else (construct_reason or "invalid edit range"),
    )
    if candidate_content is None:
        return blocked(f"candidate_range_invalid:{construct_reason}", backup=backup_identity, pre_hash=pre_hash)

    non_empty = bool(candidate_content.strip())
    record(
        ApplicationTransactionCheck.CANDIDATE_NON_EMPTY, non_empty,
        "candidate content is non-empty" if non_empty else "candidate content would be empty or whitespace-only -- refusing to write",
    )
    if not non_empty:
        return blocked("candidate_empty", backup=backup_identity, pre_hash=pre_hash)

    changed = candidate_content != original_content
    record(
        ApplicationTransactionCheck.CANDIDATE_CHANGED, changed,
        "candidate content differs from the original" if changed else "candidate content is byte-identical to the original -- nothing to apply",
    )
    if not changed:
        return blocked("candidate_unchanged", backup=backup_identity, pre_hash=pre_hash)

    candidate_bytes = candidate_content.encode("utf-8")
    within_size = len(candidate_bytes) <= MAX_CANDIDATE_BYTES
    record(
        ApplicationTransactionCheck.CANDIDATE_WITHIN_SIZE_CEILING, within_size,
        f"candidate is {len(candidate_bytes)} byte(s), within the {MAX_CANDIDATE_BYTES}-byte ceiling"
        if within_size
        else f"candidate is {len(candidate_bytes)} byte(s), exceeding the {MAX_CANDIDATE_BYTES}-byte ceiling",
    )
    if not within_size:
        return blocked("candidate_too_large", backup=backup_identity, pre_hash=pre_hash)

    no_nul = b"\x00" not in candidate_bytes
    record(
        ApplicationTransactionCheck.CANDIDATE_NO_NUL_BYTES, no_nul,
        "no NUL bytes in candidate content" if no_nul else "candidate content contains a NUL byte -- refusing to write binary-shaped content",
    )
    if not no_nul:
        return blocked("candidate_binary_shaped", backup=backup_identity, pre_hash=pre_hash)

    replacement_line_count = len(replacement_text.splitlines()) or 1
    within_line_bound = replacement_line_count <= MAX_EDIT_RANGE_LINES
    record(
        ApplicationTransactionCheck.CANDIDATE_WITHIN_LINE_BOUND, within_line_bound,
        f"replacement spans {replacement_line_count} line(s), within the {MAX_EDIT_RANGE_LINES}-line bound"
        if within_line_bound
        else f"replacement spans {replacement_line_count} line(s), exceeding the {MAX_EDIT_RANGE_LINES}-line bound",
    )
    if not within_line_bound:
        return blocked("candidate_exceeds_line_bound", backup=backup_identity, pre_hash=pre_hash)

    # -- Step 6: write the temporary file (same directory as the target) --
    try:
        tmp_path_str = write_temp_file_fn(target_path.parent, f".{target_path.name}.", candidate_bytes)
    except OSError as exc:
        record(ApplicationTransactionCheck.TEMP_WRITE_SUCCEEDED, False, f"temporary file write failed: {exc}")
        return failed("temp_write_failed", backup=backup_identity, pre_hash=pre_hash)
    record(ApplicationTransactionCheck.TEMP_WRITE_SUCCEEDED, True, "temporary candidate file written successfully")

    # -- Step 7: atomically replace the target --
    try:
        replace_fn(tmp_path_str, str(target_path))
    except OSError as exc:
        record(ApplicationTransactionCheck.ATOMIC_REPLACE_SUCCEEDED, False, f"atomic replace failed: {exc}")
        try:
            os.unlink(tmp_path_str)
        except OSError:
            pass
        return failed("atomic_replace_failed", backup=backup_identity, pre_hash=pre_hash)
    record(ApplicationTransactionCheck.ATOMIC_REPLACE_SUCCEEDED, True, "target file atomically replaced")

    # -- Step 8: verify the resulting hash --
    expected_post_hash = hashlib.sha256(candidate_bytes).hexdigest()
    post_read = file_reader_mod.read_workspace_file(
        file_reader_mod.WorkspaceFileReadRequest(
            workspace_id=artifact.workspace_id,
            relative_path=artifact.relative_path,
            max_bytes=MAX_CANDIDATE_BYTES,
            allow_truncation=False,
        ),
        workspace_registry=workspace_registry,
    )
    post_hash_ok = (
        post_read.status == file_reader_mod.ReadStatus.COMPLETED.value and post_read.checksum == expected_post_hash
    )
    record(
        ApplicationTransactionCheck.POST_WRITE_HASH_MATCHES, post_hash_ok,
        "post-write content hash matches the constructed candidate's own hash"
        if post_hash_ok
        else "post-write content hash does not match the constructed candidate -- the write did not verifiably complete as expected",
    )
    if not post_hash_ok:
        return failed("post_write_hash_mismatch", backup=backup_identity, pre_hash=pre_hash)

    # -- Step 9: record the immutable ApplicationResult. Step 10: stop. No rerun. --
    outcome = ApplicationTransactionOutcome.APPLIED
    return ApplicationResult(
        application_id=id_factory(),
        draft_digest=draft_digest,
        workspace_id=artifact.workspace_id,
        relative_path=artifact.relative_path,
        pre_application_content_hash=pre_hash,
        post_application_content_hash=post_read.checksum,
        backup=backup_identity,
        outcome=outcome.value,
        reason=None,
        checks=tuple(checks),
        applied_at=str(clock()),
        application_boundary=_boundary_for(outcome),
    )
