# v0.59.0 - Source Identity and Repair Draft Foundation

This release implements Phase 1 of `planning/v0.58.0-repair-application-safety-design.md`: immutable source-identity models, an immutable `RepairDraft` model, and deterministic structural validation. It creates data objects only — no patch generation, no file editing, no repair application.

## Evaluated

- A new `49.x` Repair Draft Foundation benchmark category was added (ten prompts, matching coverage rows) and deliberately left `Not Run`. No evaluation results were fabricated for this milestone.

## Added

- `scripts/gauss_repair_draft.py`: `SourceArtifact` (stable "which file" reference), `SourceIdentity` (a content-bound snapshot — artifact + hash + size + encoding), `EditScope` (bounded line range + intended operation, never content), and `RepairDraft` (the full immutable draft record). All frozen dataclasses; zero I/O anywhere in the module.
- `repair_draft_digest(draft)` and `source_identity_digest(identity)`, following the exact canonical-JSON/SHA-256 convention `repair_plan_digest` already established. `repair_draft_id` is deliberately excluded from the digest — content identity, not instance identity.
- `validate_repair_draft(draft, current_source_identity=None)`: ten pure, I/O-free structural checks — workspace/hash matching (the core stale-source signal), UTF-8-only encoding, well-formed and bounded (≤200-line) edit ranges, structural single-file/immutability/determinism guarantees, and a `no_generated_code` check rejecting code-shaped content in any descriptive field.
- CLI `repair-draft`/`show-repair-draft` commands, requiring an existing repair plan and every content/hash/range value explicitly — no auto-collection, no defaulting beyond the adapter's own already-established active workspace.
- `docs/gauss-repair-draft.md` — purpose, architecture, digest model, validation model, relationship to repair planning/approval/future application, safety boundaries, limitations.

## Critical Invariants (Unchanged, Extended One Layer)

`safe_to_apply` and `safe_to_prepare_draft` remain structurally `False` on every `RepairDraft` the sanctioned `build_repair_draft(...)` constructor produces, with no code path in the new module capable of setting either to `True` — the same invariant `RepairPlan` (`v0.56.0`) and `ApprovalRecord` (`v0.57.0`) already enforce. No unified diff, patch, replacement text, or generated code is representable anywhere in this model.

## Design Decisions Worth Noting

- **`SourceArtifact`/`SourceIdentity` split**, rather than one merged class, is what makes hash-mismatch and workspace-mismatch independently testable.
- **`SourceSnapshot`** (named as a candidate concept in the authorizing design) was not implemented as a separate class — `SourceIdentity` already is the snapshot concept; a third class would have added indirection without a distinction Phase 1 needs.
- **Neither digest is stored as a field** on the object it identifies, despite the milestone's own suggested field list naming `draft_digest` as a `RepairDraft` field — this mirrors `RepairPlan`'s existing precedent exactly (no `plan_digest` field either) and avoids a self-referential-construction problem.
- **`safe_to_prepare_draft` stays `False` even though a draft now exists** — the field tracks downstream capability, not object existence. No drafting-refinement or application mechanism exists downstream of a `RepairDraft`, so the answer stays `False`.
- **`MAX_EDIT_RANGE_LINES = 200`** implements the `v0.58.0` threat table's own "cap total changed lines" recommendation early, at the validation layer.

## Not Implemented

Draft approval, application approval, the application transaction, backup, rollback, audit, rerun, persistent draft storage, durable sessions, patch generation, diff generation, file writes, filesystem mutation. `scripts/gauss_repair_planner.py` and `scripts/gauss_repair_approval.py` have zero diff.

## Documentation Updates

`README.md`, `ROADMAP.md` (new `v0.59.0` section; the "Repair Application" future candidate updated to note Phase 1/2 are now implemented), `KNOWN_LIMITATIONS.md`, `CHANGELOG.md`, and `docs/gauss-repair-planning.md` were all updated.

## Remaining Limitations

- No draft-generation intelligence exists — every field is explicitly supplied by the caller.
- No draft-approval mechanism exists; approving a `RepairPlan` says nothing about any draft.
- No application consumer of a `RepairDraft` exists.
- No persistence: `last_repair_draft` is process-local, cleared by `reset`.
- Validation proves structural safety only, never GAUSS correctness.
- `current_source_identity` re-verification is available as a function parameter, but this module never obtains a "current" value itself — no I/O exists here to do so.

## Next Recommended Milestone

Phase 3 of the `v0.58.0` design: a draft-review and approval workflow, mirroring `gauss_repair_approval.py`'s own conflict/revoke discipline but keyed by `repair_draft_digest`. This requires no new I/O and is the next unimplemented phase in the design document's own dependency order. Phase 4 (the local single-file application prototype) should not be attempted until draft approval exists.
