# v0.56.0 - Evidence-Aware Repair Planning

This release adds a new Repair Planning stage to the project's staged reasoning pipeline (Execution → Evidence Collection → Interpretation → Verified Knowledge → Diagnosis → **Repair Planning** → Repair Application), strictly separate from the not-yet-implemented Repair Application stage. Repair planning never applies a change, generates replacement code, or guarantees a fix.

## Evaluated

- All ten `47.x` Evidence-Aware Repair Planning prompts: 10/10 Pass at 4.0, zero Critical/Major/Minor defects.
- No real GAUSS invocation was required or performed for this category — this milestone reasons over already-verified catalog knowledge and a pure repair-planning engine. The optional real-runner smoke test was run once for validation completeness only.

## Added

- `scripts/gauss_repair_planner.py`: a new, pure, deterministic repair-planning engine. `plan_repair(evidence, source_context=None) -> RepairPlan` calls the existing interpreter and diagnostic engine internally rather than duplicating classification/diagnostic logic; has zero import of any execution/workspace/orchestration module.
- `RepairPlan`/`RepairAction` dataclasses and a `RepairStatus` enum (`successful_execution_no_repair_needed`, `not_applicable`, `timeout`, `strategy_available`, `draft_possible_with_more_context`, `blocked_by_missing_source`, `unknown_error`, `insufficient_evidence`). Confidence reuses `gauss_execution_diagnostics.DiagnosticConfidence` directly rather than duplicating it.
- A new, optional `SourceContext` dataclass (`code_text`, `line_start`/`line_end`, `matrix_shapes`, `referenced_paths`, `procedure_name`, `argument_summary`) — populated only from what a caller explicitly supplies, never read from a file or inferred.
- Four new fields on `GaussErrorCatalogEntry` (`repair_strategies`, `repair_preconditions`, `repair_verification_steps`, `repair_risks`), populated for all 11 existing codes from the same accepted evidence sources as each entry's own verification status, or from conservative generic inspection language.
- CLI `repair-plan` command, alongside `interpret`/`diagnose`, with bounded `--source-text`/`--matrix-shape`/`--path`/`--procedure`/`--args`/`--line-start`/`--line-end` flags.
- `docs/gauss-repair-planning.md` — purpose, pipeline position, data model, source-context model, status/confidence models, ranking, approval/application boundaries, CLI usage, examples, safety boundaries, limitations.
- `docs/gauss-error-catalog.md` updated with each entry's repair strategy/verification/risks, explicitly distinguishing verified error meaning, possible diagnostic cause, bounded repair strategy, and out-of-scope repair application as four separate kinds of claim.

## Application Boundary (Critical Invariant)

`safe_to_apply` is **structurally always `False`** in this milestone — verified across every reachable status by a dedicated test. `safe_to_prepare_draft` is likewise always `False`: no draft-generation capability exists yet, even when the caller supplies source context relevant enough to narrow the plan to `draft_possible_with_more_context`. Every `RepairAction.is_concrete_edit` is `False`, and no `action_type` is ever `"edit"`, `"apply"`, `"patch"`, `"rewrite"`, or `"replace"`.

`repair_boundary` is a fixed disclosure present in every plan: *"This is a repair plan, not an applied repair. No code was modified. GAUSS was not rerun. User approval would be required before any future repair application."* The CLI additionally emits a dedicated `application_boundary` line on every call.

## Confidence Model

Reuses `DiagnosticConfidence` (`high`/`medium`/`low`/`insufficient_evidence`) rather than introducing a parallel scale. Every catalog-derived repair strategy is capped at `low`, uniformly — regardless of the underlying error classification's own confidence, and regardless of whether the caller supplied relevant source context. A high-confidence error classification never implies a high-confidence repair.

## Source Context

Explicit and bounded only. Supplying relevant context (e.g. matrix shapes for a `G0036` plan) narrows `missing_evidence` and shifts `repair_status` from `strategy_available` to `draft_possible_with_more_context`, sharpening the plan's summary — but never raises confidence, never sets `safe_to_apply`/`safe_to_prepare_draft` to `True`, and never generates replacement code or a diff. Irrelevant context (e.g. a procedure name for a matrix-dimension error) is recorded as supplied but does not narrow the plan.

## CLI Behavior

`repair-plan` is available any time after `execute` (mirrors `interpret`/`diagnose`'s own rule); reports unavailability honestly if no result exists. It never calls `execute`, `plan`, or `confirm`; never auto-displays stdout/stderr; never auto-reads output files; never resets or mutates workspace state; produces identical output for identical arguments on repeated calls.

Recommended sequence after `execute`:
```
interpret
diagnose
repair-plan
stdout / stderr   (explicitly, when needed)
outputs
read <path>       (explicitly, when needed)
provenance
reset             (before a new single-shot attempt)
```

## Interpretation / Diagnosis / Repair-Planning Boundary

`interpret` answers "what happened?" `diagnose` answers "what verified causes may explain it, and what evidence is missing?" `repair-plan` answers "what bounded strategy should be considered, what's needed before drafting or applying a change, and how should a future repair be verified?" None answers "what exact code should be applied?" `repair-plan` calls `interpret_execution(...)` and `diagnose_execution(...)` internally rather than re-deriving reasoning a second way; none of the three commands invokes another's CLI surface or mutates state as a side effect of another.

## Safety Boundaries (unchanged, re-verified)

Execution, confirmation, provenance, output-reading, workspace-recovery, interpretation, and diagnostic contracts are all unchanged by this release. Repair planning adds no execution, file-read/write, or workspace-mutation behavior of any kind — it is a pure read of already-captured evidence, optionally sharpened by explicit caller-supplied context.

## Remaining Limitations

- Repair planning is strategy-level only; it never produces an applied repair, a patch, or replacement code, regardless of source context supplied.
- No repair-application workflow exists yet; `requires_explicit_approval` documents a future requirement, not an implemented approval mechanism.
- No automatic editing, retry, or rerun.
- Source context must be supplied explicitly through bounded CLI flags or directly to `plan_repair(...)`; it is never read from a file or inferred.
- Unknown GAUSS error codes produce no repair strategy at all, and never inherit a known code's strategy by similarity.
- No durable session integration; a repair plan is available only for the current adapter session's captured result, cleared by `reset`.
- No statistical or methodological validity assessment.
- No guarantee that any proposed strategy will resolve the underlying error.

## Next Recommended Milestone

Durable execution sessions (needed before any future repair-application workflow could safely correlate a plan with the exact execution it was derived from across turns) or a scoped, explicitly-authorized approved-repair-application *design* phase — not implementation — that defines the approval mechanism `requires_explicit_approval` currently only documents. A further diagnostic/repair-strategy coverage expansion remains available but is lower-priority evidence-wise, since this milestone's own catalog already carries repair knowledge for all 11 existing codes.
