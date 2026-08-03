# GAUSS Diagnostic Reasoning

## Purpose

`scripts/gauss_execution_diagnostics.py` (`v0.54.0`, catalog knowledge expanded in `v0.55.0`) is a deterministic, evidence-bound layer that reasons over an existing execution result to answer: *what verified causes might explain this, what evidence is still missing, and what should be inspected next?*

It never answers: *what exact code should replace the current code?* That question belongs to the downstream Repair Planning stage (`scripts/gauss_repair_planner.py`, `v0.56.0`), which itself stops at a bounded strategy and never applies a change either -- see `docs/gauss-repair-planning.md`. Diagnosis's own responsibilities are unchanged by that layer's addition: `diagnose` still does not propose a strategy, does not rank repair actions, and does not know `gauss_repair_planner` exists (no import in either direction beyond the planner reusing `diagnose_execution(...)` internally).

## Position in the Reasoning Pipeline

```
Execution
  -> Evidence Collection      (gauss_execution_workflow.py / gauss_code_execution.py)
  -> Interpretation           (gauss_execution_interpreter.py, v0.51.0)
  -> Verified Knowledge       (gauss_error_catalog.py, v0.51.0-v0.56.0)
  -> Diagnosis                (gauss_execution_diagnostics.py, v0.54.0 -- this layer)
  -> Repair Planning          (gauss_repair_planner.py, v0.56.0)
  -> Repair Application       (future, not implemented)
```

Each stage consumes the one before it and adds a narrower kind of claim:

| Stage | Answers | Does not answer |
|---|---|---|
| Interpretation | What happened? (completed / failed / timed out / blocked; which cataloged error code, if any) | Why did it happen? What should I check next? |
| Diagnosis | What verified causes may explain it? What evidence is missing? What should be inspected next? | What exact code fixes it? |
| Repair Planning | What bounded strategy should be considered? What evidence/approval are needed first? | What exact code should be applied? |
| Repair Application (future) | What specific, approved change was applied? | — |

`diagnose` internally calls `interpret_execution(...)` — the same pure function `interpret` calls — rather than re-deriving `execution_phase`/`failure_type`/etc. a second, possibly divergent way. This is the only place the two commands share logic; neither silently invokes the other's CLI command, and neither mutates state as a side effect of the other.

## Deterministic Architecture

`diagnose_execution(evidence: ExecutionEvidence) -> DiagnosticAssessment` is a pure function: identical input always produces an identical, `==`-comparable output (a dedicated test, `test_16_deterministic_repeated_assessment`, asserts this directly).

The module has no import of `gauss_code_execution`, `gauss_workspace`, `gauss_runtime_orchestration`, or `gauss_execution_adapter` — structurally, not just by convention (`test_23_diagnosis_module_has_no_execution_or_workspace_imports` checks the module's own source for these import statements). It never launches GAUSS, calls an execution helper, mutates workspace state, edits source code, reads output files, accesses the network, calls an LLM, retries, constructs a repair, or writes a new request/plan.

## Data Model

```
DiagnosticAssessment
  diagnostic_status          one of DiagnosticStatus's values
  confidence                 one of DiagnosticConfidence's values
  summary
  possible_causes            tuple[DiagnosticCause, ...]
  supporting_evidence        known facts, from the interpretation
  contradicting_evidence     always empty today -- see "Contradicting Evidence" below
  missing_evidence
  questions_to_ask           bounded, closed-ended questions
  recommended_diagnostic_steps
  limitations
  repair_boundary            always "Diagnosis does not modify or repair the program."
  safe_to_continue
  requires_user_input
  source_error_code
  source_error_category
  knowledge_verification     VerificationStatus values from the matched catalog entry

DiagnosticCause
  cause_id
  title / description
  confidence                 always "low" for a catalog-derived cause -- see below
  supporting_evidence
  required_evidence          what would raise this cause's own confidence
  verification_source
  is_catalog_verified
```

### Contradicting Evidence

`contradicting_evidence` is a real field, not a placeholder that will quietly stay empty forever by design — but nothing this engine currently consumes can populate it honestly (there is no second, independent evidence source to compare against within a single execution result). It is included now so a future evidence source can populate it without a schema change, and a test (`test_13_contradictory_evidence`) documents today's honest emptiness rather than leaving it unverified.

## Confidence Model

Four values, `DiagnosticConfidence`: `high`, `medium`, `low`, `insufficient_evidence`. Never "certain," "guaranteed," or "proven."

Confidence reflects the strength of *available evidence*, not the *severity* of the error. Concretely:

- **Category-level confidence** (whether GAUSS reported a matrix-dimension error, a syntax error, etc.) can be `high` — that's a direct, verified read of the cataloged error code.
- **Cause-level confidence** (*which specific thing* caused that category of error) is `low` for every catalog-derived cause in this version, uniformly. `G0036` can support high confidence that incompatible matrix dimensions were reported; it does not automatically support high confidence that a missing transpose caused it — this engine has no source-code-content, variable-value, or matrix-shape evidence to distinguish between the several plausible triggers a cataloged error may have. `test_17_confidence_ceiling_behavior` asserts this holds for every cataloged code.
- **`DiagnosticAssessment.confidence`** mirrors this: `high` only for a clean no-failure result; `low` when at least one catalog-derived cause exists; `insufficient_evidence` for timeout, blocked-before-launch, uncataloged codes, and genuinely insufficient evidence.

## Cause Ranking

Deterministic and explainable, with no opaque scoring:

1. Look up `interpretation.error_code` in the catalog.
2. If found, build one `DiagnosticCause` per `known_triggers` entry on that catalog entry — each a short, evidence-grounded description of a situation known (from real runtime evidence or official documentation) to trigger this code.
3. Every such cause is assigned `low` confidence, uniformly — never ranked higher because a cause is common or intuitive; only evidence could justify that, and this engine does not currently have code-content evidence to supply it.
4. If no entry is found (uncataloged code) or no `known_triggers` exist, `possible_causes` is empty and `confidence` becomes `insufficient_evidence`.

No numeric/percentage scoring exists anywhere in this module.

## Verified Diagnostic Knowledge

`GaussErrorCatalogEntry` gained three fields in `v0.54.0`, populated only from the same accepted evidence sources as the entry's own `verification_status` (real GAUSS runtime evidence recorded in this repository, official Aptech documentation, or existing repository evidence with clear provenance):

- `known_triggers: tuple[str, ...]` — plausible cause descriptions.
- `diagnostic_questions: tuple[str, ...]` — bounded, closed-ended questions.
- `required_evidence_for_diagnosis: tuple[str, ...]` — what would be needed to raise cause-level confidence.

An entry with no verified trigger knowledge yet (there are none as of `v0.55.0` — all eleven cataloged codes have at least one `known_trigger`) would simply have empty tuples here, producing an `insufficient_evidence` diagnosis for that code rather than a padded, speculative one. See `docs/gauss-error-catalog.md` for the full per-code listing.

### Broader Coverage Does Not Mean More Certainty (`v0.55.0`)

`v0.55.0` grew the catalog from 5 to 11 verified codes, all through the same evidence discipline described above. This changes *how many* execution results this engine can diagnose at all — it does not change *how confidently* it diagnoses any single one:

- Broader catalog coverage never raises the cause-confidence ceiling described above. Every one of the six newly added codes' catalog-derived causes is still capped at `low`, exactly like the five pre-existing codes (`test_38_all_new_entries_produce_no_repair_shaped_output` and the per-code tests in `scripts/test_gauss_execution_diagnostics.py` assert this directly).
- Cause-level confidence remains entirely separate from error-code (category) confidence — a newly cataloged code such as `G0058` (Index out of range) can be reported with `high` confidence that an index was genuinely out of range, while every specific cause of *why* still stays `low`, same as `G0036` always has.
- Diagnosis still never reasons beyond the evidence supplied for a single execution result — more cataloged codes means more results this engine can recognize, not more inference within any one of them.
- Unknown codes remain unknown after expansion: growing the catalog does not cause any uncataloged code to inherit a nearby code's causes by similarity (`test_40_unknown_code_still_unknown_after_catalog_expansion`).
- Diagnosis still does not repair code, regardless of how much verified knowledge backs a given cause.

## Missing-Evidence Handling

Every diagnosis that isn't a clean "no failure" reports `missing_evidence` explicitly — what this engine would need (but does not have) to move beyond category-level confidence. This is never a promise that the repository can currently collect that evidence automatically; it is a list for the *user* to supply or investigate manually.

## CLI Usage

```
gauss-mvp> diagnose
```

Available any time after `execute` (mirrors `interpret`'s own availability rule) — `run 'execute' before diagnosing execution evidence` is reported honestly if no result exists yet. `diagnose` never calls `execute`, `plan`, or `confirm`; never auto-displays stdout/stderr; never auto-reads output files; never resets or mutates workspace state.

### Example: a cataloged code (`G0105`)

```
gauss-mvp> diagnose
REAL_WORKFLOW: Diagnostic reasoning from existing evidence and interpretation only.
DIAGNOSTIC_BOUNDARY: No GAUSS launch, no execute, no plan, no retry, no code edit, no automatic file read, no workspace mutation.
diagnostic_status: diagnosed
confidence: low
summary: GAUSS reported Bad expression or missing arguments (G0105). 3 known, catalog-verified possible cause(s) are listed below; none is confirmed.
...
possible_cause_count: 3
  cause[G0105_cause_1] (confidence=low, catalog_verified=True): a missing statement terminator (semicolon) on the reported line or the line before it
  ...
questions_to_ask:
  - Does the reported line, or the line immediately before it, end with a semicolon?
  ...
repair_boundary: Diagnosis does not modify or repair the program.
```

### Example: a successful run

```
gauss-mvp> diagnose
...
diagnostic_status: no_failure_detected
confidence: high
summary: Execution completed with no detected error; there is nothing to diagnose.
limitation: A completed execution does not establish statistical or methodological correctness.
repair_boundary: Diagnosis does not modify or repair the program.
```

## Recommended User Sequence

```
execute
interpret
diagnose
stdout / stderr        (explicitly, when needed)
outputs
read <path>             (explicitly, when needed)
provenance
reset                    (before a new single-shot attempt)
```

## Safety Boundaries

- `diagnose` does not rerun GAUSS.
- `diagnose` does not repair code, propose a code rewrite, or recommend an unverified GAUSS function.
- `diagnose` does not establish methodological or statistical correctness.
- Cause confidence may be, and typically is, lower than the error-classification confidence it's derived from.
- Unknown GAUSS error codes never inherit a known code's causes.
- A documentation-only-verified code never has its diagnosis implied to be runtime-confirmed (as of `v0.55.0`, no cataloged code is currently documentation-only — `G0290` was upgraded to dual-sourced this release — but the rule and its test coverage remain in place for any future documentation-only addition).

## Limitations

- Diagnosis is limited to this repository's verified catalog knowledge — it does not reason from general programming knowledge.
- Diagnosis cannot infer user intent, inspect variable values, or read source code; it works only from already-captured execution evidence.
- Diagnosis does not repair code and does not retry.
- Unknown GAUSS error codes remain generic (`unknown_error` status, no causes).
- No durable session integration; a diagnosis is available only for the current adapter session's captured result, cleared on `reset`.
- No statistical or methodological validity assessment.
- The six codes added in `v0.55.0` (`G0058`, `G0159`, `G0104`, `G0071`, `G0048`, `G0047`) are real-runtime-verified only; none has yet been independently cross-checked against official Aptech documentation in this repository.
- Many real GAUSS runtime failures still have no cataloged code at all and remain classified generically; some (e.g. certain package-source-level errors such as `csvRead`'s "file not found" message) are not even reported in the `error G####` format this catalog's lookup depends on — see `docs/gauss-error-catalog.md`'s "Considered But Not Added" section.
