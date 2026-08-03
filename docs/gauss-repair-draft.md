# GAUSS Repair Draft

## Purpose

`scripts/gauss_repair_draft.py` (`v0.59.0`) implements Phase 1 of `planning/v0.58.0-repair-application-safety-design.md`: immutable source-identity models, an immutable `RepairDraft` model, and deterministic structural validation. It answers exactly one question: *given an explicit, caller-supplied description of a bounded intended edit, is that description well-formed, bounded, and internally consistent?*

It does not answer, and has no capability to answer, *is this edit correct*, *should this edit be applied*, or *what code implements this edit*. There is no drafting intelligence in this module — nothing generates an edit's content. A `RepairDraft` is constructed entirely from what a caller explicitly supplies.

## Architecture

Every model in this module is an immutable (`frozen=True`) dataclass, and the module itself performs **zero I/O**: no file is ever read, written, or hashed by this code. Every hash, size, and timestamp appearing in a `SourceIdentity` or `RepairDraft` is caller-supplied — the same "caller-asserted, never computed here" convention `gauss_workspace.py`'s own `ManifestFileEntry.checksum`/`.size` fields already use, and the same "caller-supplied clock, never a live one" convention `gauss_repair_approval.ApprovalRecord.recorded_at` already uses.

This module imports nothing from `gauss_repair_planner.py` or `gauss_repair_approval.py` — it consumes a plan digest as a plain string, never a `RepairPlan` object, keeping this layer fully decoupled from the layers above it.

### Data Model

```
SourceArtifact          -- a stable "which file" reference, independent of content
  workspace_id
  relative_path
  file_type

SourceIdentity           -- "this file, in exactly this state"
  artifact: SourceArtifact
  content_hash            (SHA-256 hex, caller-supplied -- authoritative for staleness)
  size
  encoding
  line_range               (optional)
  observed_at               (optional, caller-supplied clock value)

EditScope                -- location and nature of an intended edit, never its content
  line_start
  line_end
  intended_operation        (a short description, e.g. "insert missing statement terminator")
  target_procedure          (optional)
  target_symbol              (optional)

RepairDraft               -- immutable, content-identified
  repair_draft_id
  repair_plan_digest
  source_identity: SourceIdentity
  edit_scope: EditScope
  proposed_change_description
  assumptions / risks / verification_steps
  generated_at / generated_by
  approval_required          (always True via the sanctioned constructor)
  safe_to_prepare_draft       (always False)
  safe_to_apply                 (always False)
  draft_boundary
```

`SourceArtifact` and `SourceIdentity` are deliberately separate: an artifact is "which file" (stable across content changes); an identity is "which file, in exactly this content state" (changes whenever the content does). This split is what makes hash-mismatch and workspace-mismatch independently testable — two `SourceIdentity` snapshots can share an artifact while differing only in `content_hash`.

## Digests

`repair_draft_digest(draft) -> str` follows the exact convention `gauss_repair_planner.repair_plan_digest` and `gauss_runtime_orchestration.compute_request_hash` already established: a canonical dict over every field in fixed order, `json.dumps(..., sort_keys=False, ensure_ascii=True, separators=(",", ":"))`, then SHA-256.

**`repair_draft_id` is deliberately excluded from the digest.** The digest represents *content* identity, not *instance* identity — mirroring how `RepairPlan` has no ID field for `repair_plan_digest` to exclude in the first place. Two independently constructed drafts with identical content but different `repair_draft_id` values produce the same digest (`test_11_draft_id_excluded_from_digest`); this is intentional, not an oversight.

`source_identity_digest(identity) -> str` is a smaller, independently useful sibling function following the identical convention, over `SourceIdentity` alone.

Neither digest is stored as a field on the object it identifies (unlike the milestone's own suggested field list, which named `draft_digest` as a `RepairDraft` field) — this mirrors `RepairPlan`'s existing precedent exactly, and avoids the self-reference problem a stored digest field would otherwise create (the digest would need to be computed before the object exists, then passed into its own constructor, and would need special-casing to exclude itself from its own canonicalization).

## Validation

`validate_repair_draft(draft, current_source_identity=None) -> DraftValidationResult` is pure and performs no I/O. It runs ten checks:

| Check | What it verifies |
|---|---|
| `workspace_match` | If a current identity is supplied, its workspace/path match the draft's bound identity |
| `hash_match` | If a current identity is supplied, its content hash matches the draft's bound hash — **the critical stale-source signal** |
| `valid_utf8_encoding` | The declared encoding is exactly `"utf-8"` |
| `valid_range` | The edit's line range is a well-formed, closed, positive range |
| `bounded_scope` | The range does not exceed `MAX_EDIT_RANGE_LINES` (200) |
| `single_file` | Structurally guaranteed — the data model has no way to reference more than one file |
| `immutable_identity` | The bound `SourceIdentity` is a genuine frozen dataclass |
| `deterministic_digest` | The draft's digest is stable across repeated computation |
| `reversible_representation` | A bounded range and a non-empty description together exist |
| `no_generated_code` | Neither the description nor the intended operation contains code-shaped tokens (`;`, `" = "`) |

`current_source_identity` is optional and, when omitted, `workspace_match`/`hash_match` are reported as trivially passing with an explicit "comparison skipped" detail — this module never fetches a "current" state itself; a future caller would be responsible for freshly re-reading and re-hashing the real file through an authorized path before calling this function with the result.

**Validation proves structural safety only.** It never proves the intended operation is a correct GAUSS fix, and it never proves a draft is safe to apply.

## Relationship to Repair Planning

`gauss_repair_planner.py` (`v0.56.0`) is unaffected. A `RepairDraft` references a `RepairPlan`'s digest as a plain string; the planner module has no knowledge that drafts exist.

## Relationship to Repair Approval

`gauss_repair_approval.py` (`v0.57.0`) is unaffected. Strategy approval (recording a decision about a `RepairPlan`) remains completely separate from, and does not authorize, anything about a `RepairDraft`.

**As of `v0.60.0`, draft approval exists** — `scripts/gauss_repair_draft_approval.py`, documented in `docs/gauss-repair-draft-approval.md`. It consumes a `RepairDraft` and `repair_draft_digest(...)` exclusively; this module (`gauss_repair_draft.py`) has no knowledge that it exists, the same decoupling `gauss_repair_planner.py` maintains from `gauss_repair_approval.py`.

## Relationship to Future Repair Application

Nothing here is applicable. `safe_to_apply` and `safe_to_prepare_draft` are `False` on every `RepairDraft` the sanctioned `build_repair_draft(...)` constructor produces, with no code path capable of setting either to `True`. There is no patch, no diff, no replacement text, and no file-mutation capability anywhere in this module — see `planning/v0.58.0-repair-application-safety-design.md` for what a future implementation would still need to add (draft approval, application approval, the application transaction, backup/rollback, audit).

## CLI Usage

```
gauss-mvp> repair-draft --path model.gss --content-hash <sha256> --size 200 \
    --line-start 5 --line-end 5 \
    --operation "insert missing semicolon" \
    --description "Insert a missing statement terminator at the reported line."
...
draft_digest: ...
safe_to_apply: false
safe_to_prepare_draft: false
disclosure: This is NOT an applied repair.
disclosure: No files were modified.
disclosure: No patch exists.
disclosure: No code has been generated.
disclosure: No approval to edit files exists.

gauss-mvp> show-repair-draft
```

`repair-draft` requires a repair plan to already exist (`run 'repair-plan' first`) and requires every content/hash/range field explicitly — nothing is read from a file, and `--workspace-id` defaults only to the adapter's own already-established active workspace, never to an inferred or auto-discovered one. `show-repair-draft` re-displays the adapter's `last_repair_draft` without recomputing anything new. Both are available any time after a draft has been constructed; `reset` clears `last_repair_draft` exactly as it already clears `last_repair_plan` and the approval store.

## Safety Boundaries

- Zero I/O: no `open(`, no `read_text(`, no `write_text(`, no filesystem mutation of any kind (checked structurally by `test_39_no_filesystem_mutation_in_module_source`).
- No import of any execution, workspace, orchestration, or LLM-related module (checked structurally by `test_40_no_forbidden_imports`).
- `safe_to_apply`/`safe_to_prepare_draft` are always `False` — checked across every constructed-draft scenario the test suite exercises.
- No patch, diff, replacement text, or generated code is representable in `EditScope`/`RepairDraft` at all — validated at construction-adjacent time by the `no_generated_code` check.
- The CLI never calls `execute`, `plan`, or `confirm`; never mutates workspace state; never adds an approval record.

## Limitations

- This is a foundation model only. No draft-generation logic exists — every field is explicitly supplied by whoever calls `build_repair_draft(...)` (a human via the CLI, or a test).
- Draft approval exists (`v0.60.0`, see "Relationship to Repair Approval" above), but nothing consumes an approval decision toward drafting refinement or application — see `docs/gauss-repair-draft-approval.md`.
- No persistence: `last_repair_draft` is process-local, cleared by `reset`, gone on process exit — consistent with every other stage's own current behavior.
- Validation is structural only; it does not, and cannot, assess GAUSS correctness.
- `current_source_identity` re-verification is available as a function parameter but this module never obtains a "current" value itself — no I/O exists here to do so.
- No backup, rollback, audit, or application capability exists — those remain future, separately authorized milestones per `planning/v0.58.0-repair-application-safety-design.md`.
