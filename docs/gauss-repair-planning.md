# GAUSS Repair Planning

## Purpose

`scripts/gauss_repair_planner.py` (`v0.56.0`) is a deterministic, evidence-bound layer that reasons over an existing execution result, its interpretation, and its diagnosis to answer: *what bounded repair strategy should be considered, what evidence and approval are needed before drafting or applying a change, and how should a future repair be verified?*

It never answers: *here is the exact code to apply.* That question belongs to a future, distinct, not-yet-implemented Repair Application stage. Even when the caller supplies explicit source context, this module never generates replacement code, a diff, or a patch — it only sharpens which inspection question is most relevant and narrows what's still missing.

As of `v0.57.0`, `requires_explicit_approval` is consumed by a new downstream layer, `scripts/gauss_repair_approval.py` — see `docs/gauss-repair-approval.md`. This does not change repair planning's own responsibilities in any way: `gauss_repair_planner.py` still knows nothing about approval beyond exposing `repair_plan_digest(...)`, a pure identity function over its own `RepairPlan` output, which the approval layer consumes without this module importing anything back from it.

## Position in the Reasoning Pipeline

```
Execution
  -> Evidence Collection      (gauss_execution_workflow.py / gauss_code_execution.py)
  -> Interpretation           (gauss_execution_interpreter.py, v0.51.0)
  -> Verified Knowledge       (gauss_error_catalog.py, v0.51.0-v0.56.0)
  -> Diagnosis                (gauss_execution_diagnostics.py, v0.54.0-v0.55.0)
  -> Repair Planning          (gauss_repair_planner.py, v0.56.0 -- this layer)
  -> Approval                 (gauss_repair_approval.py, v0.57.0)
  -> Repair Application       (future, not implemented)
```

| Stage | Answers | Does not answer |
|---|---|---|
| Interpretation | What happened? | Why did it happen? What should I check next? |
| Diagnosis | What verified causes may explain it? What evidence is missing? | What exact code fixes it? |
| Repair Planning | What bounded strategy should be considered? What evidence/approval are needed before drafting or applying a change? How should a future repair be verified? | What exact code should be applied? |
| Repair Application (future) | What specific, approved change was applied? | — |

`plan_repair(...)` internally calls `interpret_execution(...)` and `diagnose_execution(...)` — the same pure functions `interpret` and `diagnose` already use — rather than re-deriving classification or diagnostic reasoning a second, possibly divergent way. It never invokes `interpret`'s or `diagnose`'s own CLI command as a side effect, and neither of those commands invokes `repair-plan`.

## Deterministic Architecture

`plan_repair(evidence: ExecutionEvidence, source_context: SourceContext | None = None) -> RepairPlan` is a pure function: identical input always produces an identical, `==`-comparable output (`test_19_deterministic_repeated_planning` asserts this directly).

The module has no import of `gauss_code_execution`, `gauss_workspace`, `gauss_runtime_orchestration`, `gauss_execution_adapter`, or `gauss_execution_workflow` — structurally, not just by convention (`test_29_repair_planner_module_has_no_execution_or_workspace_imports` checks the module's own source for these import statements). It never launches GAUSS, calls an execution helper, mutates workspace state, edits source code, reads or writes files, accesses the network, calls an LLM, retries, applies a patch, or constructs a new execution proposal.

## Data Model

```
RepairPlan
  repair_status              one of RepairStatus's values
  confidence                 one of DiagnosticConfidence's values (reused, not duplicated)
  summary
  repair_strategy             short label for the top-ranked strategy, or None
  proposed_actions            tuple[RepairAction, ...], ranked top-first
  target_scope                a descriptive area of attention, never a literal path/line unless supplied
  source_context_used
  supporting_evidence
  assumptions
  missing_evidence
  risks
  verification_steps
  questions_to_answer         reused directly from DiagnosticAssessment.questions_to_ask
  requires_user_input
  requires_explicit_approval
  safe_to_prepare_draft       always False in this milestone
  safe_to_apply                always False -- see "Application Boundary" below
  repair_boundary              fixed disclosure, always present
  source_error_code
  source_error_category
  knowledge_verification       VerificationStatus values from the matched catalog entry

RepairAction
  action_id
  action_type                 always "inspect" this milestone -- never "edit"/"apply"/"patch"
  description
  target
  preconditions
  evidence_basis
  confidence
  is_concrete_edit             always False
  requires_source_context
  requires_user_approval
```

Confidence reuses `gauss_execution_diagnostics.DiagnosticConfidence` directly (`RepairConfidence = diag.DiagnosticConfidence`) rather than defining a parallel scale, per this project's own convention of not duplicating existing models.

## Source-Context Model

```
SourceContext
  code_text        | None
  line_start       | None
  line_end         | None
  matrix_shapes    : tuple[str, ...]   e.g. ("A=2x3", "B=4x5")
  referenced_paths : tuple[str, ...]
  procedure_name   | None
  argument_summary | None
```

Every field is optional and populated only from what the caller explicitly supplies — never by reading a file, inferring omitted code, or reconstructing anything. An empty `SourceContext` (`SourceContext().is_empty() == True`) behaves identically to `source_context=None`.

Whether supplied context is *relevant* to a given catalog entry is decided by a small, explainable lookup table (`_CATEGORY_RELEVANT_CONTEXT_FIELDS`) mapping each `GaussErrorCategory` to the `SourceContext` field names that matter for it — e.g. `matrix_shapes`/`code_text` for `matrix_dimension`, `referenced_paths` for `file_io`. This is a deterministic presence check, never opaque scoring: if any relevant field is populated, the context is considered relevant; otherwise it is not, regardless of what else was supplied. Irrelevant context (e.g. a `procedure_name` for a matrix-dimension error) is still recorded as "used" (the caller did supply something), but does not narrow the plan.

## Repair-Status Model

`RepairStatus` (nine values, one more than this milestone's own minimum list — `TIMEOUT` was added for parity with `DiagnosticStatus.TIMEOUT` rather than overloading `STRATEGY_AVAILABLE`'s meaning for a non-cataloged, generic-only case):

| Status | When |
|---|---|
| `successful_execution_no_repair_needed` | Execution completed with no detected error. |
| `not_applicable` | No execution has launched or completed yet. |
| `timeout` | Execution timed out (real or simulated/injected evidence). Generic, code-independent guidance only. |
| `strategy_available` | A cataloged error matched, has authored repair strategies, and no relevant source context was supplied. |
| `draft_possible_with_more_context` | Same as above, but the caller supplied source context relevant to this code's own preconditions. Still never a concrete edit. |
| `blocked_by_missing_source` | A cataloged entry matched but has no authored `repair_strategies` yet (structurally supported; does not fire for any of the 11 codes cataloged as of `v0.56.0`). |
| `unknown_error` | An uncataloged `G####` code. |
| `insufficient_evidence` | The underlying execution evidence itself is too sparse to classify at all. |

Never used: "repaired," "fixed," "solved," "guaranteed" — these would imply an outcome this module cannot establish.

## Confidence Model

Identical philosophy to diagnosis, deliberately conservative:

- Every catalog-derived `RepairAction` is `low` confidence, uniformly — regardless of whether the underlying error classification itself is `high` confidence, and regardless of whether relevant source context was supplied (`draft_possible_with_more_context` does **not** raise confidence above `low`; it only narrows `missing_evidence`). `test_20_conservative_confidence_ceiling` asserts this across all 11 cataloged codes.
- `successful_execution_no_repair_needed` mirrors the interpretation's own confidence (there is genuinely nothing to be uncertain about).
- Everything else (`not_applicable`, `timeout`, `unknown_error`, `blocked_by_missing_source`, `insufficient_evidence`) is `insufficient_evidence`.

A high-confidence error classification never implies a high-confidence repair — this is the same principle diagnosis already established for cause-level confidence, carried one layer further.

## Repair-Strategy Ranking

`_actions_from_entry(...)` builds one `RepairAction` per `repair_strategies` string on the matched catalog entry, in declaration order. As of `v0.56.0` every entry authors exactly one strategy, so ranking has no observable effect yet — but the ranking function is real, documented, and tested (not a placeholder), ready to extend once an entry has more than one strategy. Ranking would be driven by precondition/context relevance, never by how common a strategy is believed to be, and never by opaque scoring.

If evidence is insufficient to say anything code-specific, no speculative strategy is ever ranked — the plan returns `insufficient_evidence` or `unknown_error` with an empty `proposed_actions` tuple instead.

## Verified Repair-Planning Knowledge

`GaussErrorCatalogEntry` gained four fields in `v0.56.0`, populated only from the same accepted evidence sources as the entry's own `verification_status` or from conservative, generic inspection language:

- `repair_strategies: tuple[str, ...]` — bounded inspection strategies, never replacement code.
- `repair_preconditions: tuple[str, ...]` — what source context would be needed to narrow further.
- `repair_verification_steps: tuple[str, ...]` — how a human should confirm a future repair actually addressed this code.
- `repair_risks: tuple[str, ...]` — generic, conservative cautions about this code's repair space, never a claim about a specific fix's risk (since no specific fix is ever proposed).

All 11 cataloged codes carry this knowledge as of `v0.56.0`. Every strategy is phrased as an inspection/decision prompt, never a concrete edit — for example, `G0036`'s strategy is "Inspect the dimensions and intended roles of both operands before deciding whether the operation, operand construction, or orientation needs adjustment," never "Transpose the left matrix."

## Approval Boundary

`requires_explicit_approval` is `True` exactly when a plan has at least one proposed, code-specific `RepairAction` (`strategy_available` or `draft_possible_with_more_context`); `False` for every other status, since there is nothing yet to approve. As of `v0.57.0`, this field is consumed by `gauss_repair_approval.py`'s `RepairApprovalStore`, which records an explicit accept/decline decision hash-bound to this plan's own `repair_plan_digest(...)` — see `docs/gauss-repair-approval.md`. Recording a decision does not change anything about the plan itself, and does not flip `safe_to_apply` or `safe_to_prepare_draft`.

## Application Boundary

`safe_to_apply` is **always `False`**, in every version through `v0.57.0` — a critical, structurally-tested invariant (`test_21_safe_to_apply_always_false` checks it across every reachable status; `gauss_repair_approval.py`'s own `ApprovalRecord.safe_to_apply` is likewise always `False`, tested independently). `safe_to_prepare_draft` is likewise always `False`: no draft-generation capability exists yet, even when source context is rich enough to narrow a plan to `draft_possible_with_more_context`, and even after a plan is approved. Every `RepairAction.is_concrete_edit` is always `False`, and no `action_type` is ever `"edit"`, `"apply"`, `"patch"`, `"rewrite"`, or `"replace"` (`test_33_no_edit_or_apply_action_types`).

`repair_boundary` is a fixed, always-present string: *"This is a repair plan, not an applied repair. No code was modified. GAUSS was not rerun. User approval would be required before any future repair application."*

## Verification Planning

Every cataloged entry's `repair_verification_steps` describes how a human — not this repository — should confirm a future repair actually resolved the reported error, e.g. for `G0036`: "Confirm the corrected operands produce a result with the intended dimensions before rerunning the full script." This is planning-only language; it never claims this repository performs that verification automatically, and it never triggers a rerun.

## CLI Usage

```
gauss-mvp> repair-plan
gauss-mvp> repair-plan --source-text "x = ;"
gauss-mvp> repair-plan --matrix-shape A=2x3 --matrix-shape B=4x5
gauss-mvp> repair-plan --path data.csv --procedure myproc --args "1 argument, 2 expected" --line-start 4 --line-end 6
```

Available any time after `execute` (mirrors `interpret`'s and `diagnose`'s own availability rule) — `run 'execute' before requesting a repair plan` is reported honestly if no result exists yet. `repair-plan` never calls `execute`, `plan`, or `confirm`; never auto-displays stdout/stderr; never auto-reads output files; never resets or mutates workspace state; deterministic across repeated calls with identical arguments.

### Example: a cataloged code with no source context (`G0105`)

```
gauss-mvp> repair-plan
REAL_WORKFLOW: Repair planning from existing evidence, interpretation, and diagnosis only.
REPAIR_PLAN_BOUNDARY: No GAUSS launch, no execute, no plan, no retry, no code edit, no file write, no patch application, no new execution proposal, no workspace mutation.
repair_status: strategy_available
confidence: low
summary: GAUSS reported Bad expression or missing arguments (G0105). 1 catalog-verified inspection strategy(ies) are proposed below; none is applied or guaranteed to resolve the error.
proposed_repair_strategy: Inspect and complete or correct the invalid expression at the reported parser location before rerunning.
missing_evidence:
  - the exact source text at and immediately before the reported parser location
...
safe_to_prepare_draft: false
safe_to_apply: false
repair_boundary: This is a repair plan, not an applied repair. No code was modified. GAUSS was not rerun. User approval would be required before any future repair application.
application_boundary: No patch was applied. No file was modified. GAUSS was not rerun.
```

### Example: the same code with relevant source context supplied

```
gauss-mvp> repair-plan --matrix-shape A=2x3 --matrix-shape B=4x5
...
repair_status: draft_possible_with_more_context
source_context_used: true
missing_evidence:
(empty -- the supplied shapes satisfy this entry's own repair_preconditions)
safe_to_prepare_draft: false
safe_to_apply: false
```

Even here, no replacement code is generated — the plan only narrows `missing_evidence` and reflects that the supplied context was used; drafting itself remains structurally unimplemented.

## Recommended User Sequence

```
execute
interpret
diagnose
repair-plan
approve-repair <plan_digest> / decline-repair <plan_digest>   (explicit decision only; see docs/gauss-repair-approval.md)
stdout / stderr         (explicitly, when needed)
outputs
read <path>              (explicitly, when needed)
provenance
reset                     (before a new single-shot attempt)
```

## Safety Boundaries

- `repair-plan` does not rerun GAUSS, retry, or create a new execution proposal.
- `repair-plan` does not read or write any file, and does not edit source code.
- `repair-plan` never produces `safe_to_apply: true` or a concrete edit.
- `repair-plan` does not establish methodological or statistical correctness — a completed execution with no repair needed states this explicitly.
- Cause/strategy confidence may be, and typically is, lower than the error-classification confidence it is derived from.
- Unknown GAUSS error codes never inherit a known code's repair strategies.
- Supplying source context narrows `missing_evidence` and may change `repair_status`; it never raises confidence above `low` and never enables `safe_to_apply`/`safe_to_prepare_draft`.

## Limitations

- Repair planning is strategy-level only — it never produces an applied repair, a patch, or replacement code, regardless of how much source context is supplied.
- No repair-application workflow exists yet. As of `v0.57.0`, `requires_explicit_approval` is consumed by a real, tested approval-recording mechanism (`docs/gauss-repair-approval.md`) — but recording a decision still does not enable applying anything; no consumer of an approval decision exists.
- No automatic editing, retry, or rerun.
- No durable session integration; a repair plan (and any approval decision recorded against it) is available only for the current adapter session, cleared by `reset`.
- Source context must be supplied explicitly through the bounded CLI flags (or directly to `plan_repair(...)`); it is never read from a file or inferred.
- Unknown GAUSS error codes remain generic (`unknown_error` status, no proposed actions).
- No statistical or methodological validity assessment.
- No guarantee that any proposed strategy will resolve the underlying error.
