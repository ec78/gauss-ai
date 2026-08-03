"""Immutable source-identity and repair-draft foundation models.

Position in the reasoning pipeline:

    ... -> Repair Planning (gauss_repair_planner.py, v0.56.0)
        -> Approval (gauss_repair_approval.py, v0.57.0)
        -> Repair Draft (this module, v0.59.0 -- Phase 1 of the v0.58.0 design)
        -> (Repair Application, future, not implemented)

Implements Phase 1 of `planning/v0.58.0-repair-application-safety-design.md`
(Sections 5, 6, 8, 9, 11): source identity, an immutable `RepairDraft` data
model, and deterministic structural validation. This module constructs and
validates data only.

It does NOT:
- generate a unified diff, patch file, replacement text, modified source, or
  generated code -- `EditScope` represents only a bounded location and a
  short description of intent (line range, target procedure/symbol,
  intended operation), never the edit's actual content
- read, write, or otherwise touch any file -- this module performs zero I/O;
  every hash, size, and timestamp is caller-supplied, exactly as
  `gauss_repair_approval.ApprovalRecord.recorded_at` is caller-supplied
  rather than computed from a live clock
- edit source code or apply a repair
- approve a draft (that is a future, separate, still-unimplemented layer --
  see the design document's Section 4.B)
- call GAUSS, an execution helper, or an LLM

`safe_to_apply` and `safe_to_prepare_draft` are structurally `False` on
every `RepairDraft` produced by `build_repair_draft(...)`, with no code path
in this module capable of setting either to `True`. This is the same
invariant `RepairPlan` (`v0.56.0`) and `ApprovalRecord` (`v0.57.0`) already
enforce, extended one layer further: a `RepairDraft` existing does not mean
drafting is "available" in any actionable sense. It means a structured
description of an intended, bounded edit has been recorded and validated,
nothing more.

This module never imports `gauss_repair_planner` or `gauss_repair_approval`
-- it consumes only a plan digest string (already computed elsewhere), never
a `RepairPlan` object itself, keeping this layer decoupled from the layers
above it the same way `gauss_repair_approval.py` stays decoupled from
execution/workspace modules.
"""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
from dataclasses import dataclass

#: A fixed, always-present disclosure -- never conditional, never reworded
#: per draft, so it cannot be accidentally omitted.
DRAFT_BOUNDARY_STATEMENT = (
    "This is a repair draft, not an applied repair. No file was read or written. No patch exists. "
    "No code was generated. No approval to edit files exists."
)

#: A conservative cap on edit-scope size, matching the "a future
#: implementation should also cap total changed lines" recommendation in
#: planning/v0.58.0-repair-application-safety-design.md's own threat table
#: (Section 21, "large patch abuse"). Enforced here, at the validation
#: layer, rather than left for a future implementation to remember.
MAX_EDIT_RANGE_LINES = 200

#: The only encoding this foundation model accepts as valid, mirroring
#: `gauss_workspace_file_reader.py`'s own UTF-8-only policy (explicit
#: rejection of anything else, never silent transcoding).
SUPPORTED_ENCODING = "utf-8"

_GENERIC_DRAFT_ASSUMPTIONS: tuple[str, ...] = (
    "The bound source_content_hash accurately reflects the file's content at the moment it was observed.",
    "No other undrafted change to the same file is in flight concurrently.",
)
_GENERIC_DRAFT_RISKS: tuple[str, ...] = (
    "This foundation model records an intended edit scope only; it does not verify the intended operation "
    "will produce syntactically or semantically correct GAUSS code.",
    "Any future application of this draft would require re-verifying the source content hash immediately "
    "before writing, since this draft's own binding can become stale at any time after it was generated.",
)
_GENERIC_DRAFT_VERIFICATION_STEPS: tuple[str, ...] = (
    "Before any future application, re-read and re-hash the target file and confirm the result matches this "
    "draft's own source content hash exactly.",
    "After any future application, re-hash the resulting file and confirm it differs from the pre-application "
    "hash in exactly the way the edit scope describes.",
)

#: Mirrors `gauss_repair_planner.py`'s own no-replacement-code test
#: convention (`test_24_no_replacement_code_without_source_context`):
#: a statement terminator or an assignment operator is a strong signal of
#: literal GAUSS code, which this model must never carry.
_BANNED_CODE_TOKENS: tuple[str, ...] = (";", " = ")


class DraftValidationCheck(enum.Enum):
    WORKSPACE_MATCH = "workspace_match"
    HASH_MATCH = "hash_match"
    VALID_UTF8_ENCODING = "valid_utf8_encoding"
    VALID_RANGE = "valid_range"
    BOUNDED_SCOPE = "bounded_scope"
    SINGLE_FILE = "single_file"
    IMMUTABLE_IDENTITY = "immutable_identity"
    DETERMINISTIC_DIGEST = "deterministic_digest"
    REVERSIBLE_REPRESENTATION = "reversible_representation"
    NO_GENERATED_CODE = "no_generated_code"


@dataclass(frozen=True)
class SourceArtifact:
    """A stable "which file" reference -- independent of content. Two
    `SourceArtifact` instances with equal fields refer to the same file
    identity regardless of what that file currently contains."""

    workspace_id: str
    relative_path: str
    #: e.g. ".gss" -- mirrors `gauss_workspace_file_reader.py`'s own
    #: dot-prefixed extension convention.
    file_type: str


@dataclass(frozen=True)
class SourceIdentity:
    """A specific, content-bound snapshot of a `SourceArtifact` -- "this
    file, in exactly this state." Every hash/size/timestamp here is
    supplied by the caller; this module performs no filesystem read of its
    own (mirrors `gauss_workspace.ManifestFileEntry`'s own "caller-asserted,
    never computed here" contract). The content hash, not the artifact
    reference alone, is authoritative for detecting whether a bound source
    has gone stale -- see the design document's Section 6."""

    artifact: SourceArtifact
    content_hash: str
    size: int
    encoding: str
    #: An optional source-range identity -- meaningful only alongside
    #: `content_hash` (a range alone says nothing about content outside it).
    line_range: tuple[int, int] | None = None
    #: Caller-supplied clock value, never computed internally -- mirrors
    #: `ApprovalRecord.recorded_at`.
    observed_at: str | None = None


@dataclass(frozen=True)
class EditScope:
    """Describes only the bounded location and nature of an intended edit --
    never the edit's actual content. No unified diff, patch, replacement
    text, or generated code is representable in this model; see the module
    docstring."""

    line_start: int
    line_end: int
    intended_operation: str
    target_procedure: str | None = None
    target_symbol: str | None = None


@dataclass(frozen=True)
class RepairDraft:
    repair_draft_id: str
    #: The exact `gauss_repair_planner.repair_plan_digest(plan)` value this
    #: draft claims to be derived from -- a plain string; this module never
    #: imports the module that produces it (see module docstring).
    repair_plan_digest: str
    source_identity: SourceIdentity
    edit_scope: EditScope
    proposed_change_description: str
    assumptions: tuple[str, ...]
    risks: tuple[str, ...]
    verification_steps: tuple[str, ...]
    #: Caller-supplied clock value, never computed internally.
    generated_at: str
    #: e.g. "explicit_caller_input" -- never a claim of automated
    #: generation, since no drafting intelligence exists in this milestone.
    generated_by: str
    approval_required: bool
    #: Always `False` -- no draft-generation-of-a-further-draft capability
    #: exists. Checked structurally by `test_safe_to_prepare_draft_always_false`.
    safe_to_prepare_draft: bool
    #: Always `False` -- this milestone implements the draft model only.
    #: Checked structurally by `test_safe_to_apply_always_false`.
    safe_to_apply: bool
    draft_boundary: str


def build_repair_draft(
    *,
    repair_draft_id: str,
    repair_plan_digest: str,
    source_identity: SourceIdentity,
    edit_scope: EditScope,
    proposed_change_description: str,
    generated_at: str,
    generated_by: str = "explicit_caller_input",
) -> RepairDraft:
    """Convenience constructor filling in the fixed, generic assumptions/
    risks/verification_steps/boundary/safety fields -- never content-specific,
    since this module has no drafting intelligence of its own. Equivalent to
    constructing `RepairDraft(...)` directly with these same generic values;
    provided only so call sites (the CLI, tests) don't repeat them. Direct
    `RepairDraft(...)` construction remains available -- e.g. for a test that
    deliberately wants to inspect a differently-shaped draft."""
    return RepairDraft(
        repair_draft_id=repair_draft_id,
        repair_plan_digest=repair_plan_digest,
        source_identity=source_identity,
        edit_scope=edit_scope,
        proposed_change_description=proposed_change_description,
        assumptions=_GENERIC_DRAFT_ASSUMPTIONS,
        risks=_GENERIC_DRAFT_RISKS,
        verification_steps=_GENERIC_DRAFT_VERIFICATION_STEPS,
        generated_at=generated_at,
        generated_by=generated_by,
        approval_required=True,
        safe_to_prepare_draft=False,
        safe_to_apply=False,
        draft_boundary=DRAFT_BOUNDARY_STATEMENT,
    )


def _canonical_source_identity(identity: SourceIdentity) -> dict:
    return {
        "workspace_id": identity.artifact.workspace_id,
        "relative_path": identity.artifact.relative_path,
        "file_type": identity.artifact.file_type,
        "content_hash": identity.content_hash,
        "size": identity.size,
        "encoding": identity.encoding,
        "line_range": list(identity.line_range) if identity.line_range is not None else None,
        "observed_at": identity.observed_at,
    }


def source_identity_digest(identity: SourceIdentity) -> str:
    """Deterministic SHA-256 fingerprint over a `SourceIdentity`'s full
    content, in fixed field order -- mirrors
    `gauss_repair_planner.repair_plan_digest`'s own convention (canonical
    dict -> `json.dumps(..., sort_keys=False)` -> SHA-256)."""
    serialized = json.dumps(_canonical_source_identity(identity), sort_keys=False, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def repair_draft_digest(draft: RepairDraft) -> str:
    """Deterministic SHA-256 fingerprint over a `RepairDraft`'s full
    identifying content, in fixed field order. Deliberately excludes
    `repair_draft_id`: the digest represents *content* identity, not
    *instance* identity -- the same reason `repair_plan_digest` hashes no
    plan-instance ID (RepairPlan has none). Two independently constructed
    drafts with identical content but different `repair_draft_id` values
    produce the same digest; `test_11_draft_id_excluded_from_digest`
    asserts this directly."""
    canonical = {
        "repair_plan_digest": draft.repair_plan_digest,
        "source_identity": _canonical_source_identity(draft.source_identity),
        "edit_scope": {
            "line_start": draft.edit_scope.line_start,
            "line_end": draft.edit_scope.line_end,
            "intended_operation": draft.edit_scope.intended_operation,
            "target_procedure": draft.edit_scope.target_procedure,
            "target_symbol": draft.edit_scope.target_symbol,
        },
        "proposed_change_description": draft.proposed_change_description,
        "assumptions": list(draft.assumptions),
        "risks": list(draft.risks),
        "verification_steps": list(draft.verification_steps),
        "generated_at": draft.generated_at,
        "generated_by": draft.generated_by,
        "approval_required": draft.approval_required,
        "safe_to_prepare_draft": draft.safe_to_prepare_draft,
        "safe_to_apply": draft.safe_to_apply,
        "draft_boundary": draft.draft_boundary,
    }
    serialized = json.dumps(canonical, sort_keys=False, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DraftValidationCheckResult:
    check: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class DraftValidationResult:
    draft_digest: str
    checks: tuple[DraftValidationCheckResult, ...]
    all_passed: bool
    failed_checks: tuple[str, ...]


def validate_repair_draft(
    draft: RepairDraft, current_source_identity: SourceIdentity | None = None
) -> DraftValidationResult:
    """Pure, deterministic structural validation. Performs no I/O, no file
    read, no write, no mutation of `draft`. `current_source_identity`, if
    supplied, represents a freshly re-observed source state to compare the
    draft's own bound identity against -- this module never obtains that
    value itself; a future caller would be responsible for re-reading and
    re-hashing the real file through an authorized path before calling this
    function.

    Validation proves structural safety only -- it never proves the
    intended operation is a correct GAUSS fix."""
    results: list[DraftValidationCheckResult] = []

    def record(check: DraftValidationCheck, passed: bool, detail: str) -> None:
        results.append(DraftValidationCheckResult(check=check.value, passed=passed, detail=detail))

    if current_source_identity is not None:
        workspace_match = (
            draft.source_identity.artifact.workspace_id == current_source_identity.artifact.workspace_id
            and draft.source_identity.artifact.relative_path == current_source_identity.artifact.relative_path
        )
        record(
            DraftValidationCheck.WORKSPACE_MATCH,
            workspace_match,
            "workspace and path match the supplied current source identity"
            if workspace_match
            else "the supplied current source identity targets a different workspace or path than this draft was bound to",
        )
        hash_match = draft.source_identity.content_hash == current_source_identity.content_hash
        record(
            DraftValidationCheck.HASH_MATCH,
            hash_match,
            "content hash matches the supplied current source identity"
            if hash_match
            else "the bound source content hash no longer matches the supplied current source identity -- "
            "the source has changed since this draft was generated",
        )
    else:
        record(DraftValidationCheck.WORKSPACE_MATCH, True, "no current source identity supplied; workspace/path comparison skipped")
        record(DraftValidationCheck.HASH_MATCH, True, "no current source identity supplied; hash comparison skipped")

    valid_encoding = draft.source_identity.encoding == SUPPORTED_ENCODING
    record(
        DraftValidationCheck.VALID_UTF8_ENCODING,
        valid_encoding,
        f"encoding is {draft.source_identity.encoding!r}"
        if valid_encoding
        else f"only {SUPPORTED_ENCODING!r} is a valid declared encoding; got {draft.source_identity.encoding!r}",
    )

    line_start = draft.edit_scope.line_start
    line_end = draft.edit_scope.line_end
    valid_range = isinstance(line_start, int) and isinstance(line_end, int) and line_start >= 1 and line_end >= line_start
    record(
        DraftValidationCheck.VALID_RANGE,
        valid_range,
        "line range is well-formed" if valid_range else f"line range [{line_start}, {line_end}] is not a valid, closed, positive range",
    )

    span = (line_end - line_start + 1) if valid_range else None
    bounded = valid_range and span is not None and span <= MAX_EDIT_RANGE_LINES
    record(
        DraftValidationCheck.BOUNDED_SCOPE,
        bounded,
        f"range spans {span} line(s), within the {MAX_EDIT_RANGE_LINES}-line bound"
        if bounded
        else f"edit range is invalid or exceeds the {MAX_EDIT_RANGE_LINES}-line bound",
    )

    # Structurally guaranteed by the data model: SourceIdentity/EditScope
    # each reference exactly one workspace_id/relative_path pair, never a
    # list -- there is no code path in this module that could construct a
    # multi-file draft.
    record(DraftValidationCheck.SINGLE_FILE, True, "structurally guaranteed: one workspace_id/relative_path pair per draft")

    identity_params = getattr(type(draft.source_identity), "__dataclass_params__", None)
    identity_is_frozen = dataclasses.is_dataclass(draft.source_identity) and bool(identity_params) and identity_params.frozen
    record(
        DraftValidationCheck.IMMUTABLE_IDENTITY,
        bool(identity_is_frozen),
        "source identity is a frozen dataclass" if identity_is_frozen else "source identity is not immutable",
    )

    digest_once = repair_draft_digest(draft)
    digest_twice = repair_draft_digest(draft)
    deterministic = digest_once == digest_twice
    record(
        DraftValidationCheck.DETERMINISTIC_DIGEST,
        deterministic,
        "digest is stable across repeated computation" if deterministic else "digest computation is non-deterministic",
    )

    reversible = valid_range and bool(draft.proposed_change_description.strip())
    record(
        DraftValidationCheck.REVERSIBLE_REPRESENTATION,
        reversible,
        "bounded range and a non-empty description together support a future reversible representation"
        if reversible
        else "missing a bounded range or a description; not a candidate for a reversible representation",
    )

    text_to_scan = f"{draft.proposed_change_description} {draft.edit_scope.intended_operation}"
    no_generated_code = not any(token in text_to_scan for token in _BANNED_CODE_TOKENS)
    record(
        DraftValidationCheck.NO_GENERATED_CODE,
        no_generated_code,
        "no replacement-code-shaped tokens found"
        if no_generated_code
        else "description/intended_operation contains code-shaped content (e.g. ';' or ' = '), which this "
        "foundation model must never represent",
    )

    all_passed = all(r.passed for r in results)
    failed = tuple(r.check for r in results if not r.passed)
    return DraftValidationResult(draft_digest=digest_once, checks=tuple(results), all_passed=all_passed, failed_checks=failed)
