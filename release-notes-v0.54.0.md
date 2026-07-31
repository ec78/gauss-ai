# v0.54.0 - Evidence-Based Diagnostic Reasoning

This release adds a new Diagnosis stage to the project's staged reasoning pipeline (Execution → Evidence Collection → Interpretation → Verified Knowledge → **Diagnosis** → Repair Planning), strictly separate from the not-yet-implemented Repair stage.

## Evaluated

- All ten `45.x` Evidence-Based Diagnostic Reasoning prompts: 10/10 Pass at 4.0, zero Critical/Major/Minor defects.
- No real GAUSS invocation was required or performed — this milestone reasons over already-verified catalog knowledge and a pure diagnostic engine.

## Added

- `scripts/gauss_execution_diagnostics.py`: a new, pure, deterministic diagnostic engine. `diagnose_execution(evidence) -> DiagnosticAssessment` calls the existing interpreter internally rather than duplicating classification logic; has zero import of any execution/workspace/orchestration module.
- `DiagnosticAssessment`/`DiagnosticCause` dataclasses and `DiagnosticStatus`/`DiagnosticConfidence` enums.
- Three new fields on `GaussErrorCatalogEntry` (`known_triggers`, `diagnostic_questions`, `required_evidence_for_diagnosis`), populated for all five existing codes from the same accepted evidence sources as each entry's own verification status.
- CLI `diagnose` command, alongside `interpret`.
- `docs/gauss-diagnostic-reasoning.md` — purpose, pipeline position, confidence model, cause-ranking rules, CLI usage, and safety boundaries.
- `docs/gauss-error-catalog.md` updated with each entry's diagnostic knowledge, explicitly distinguishing verified error meaning, possible (unconfirmed) diagnostic cause, and out-of-scope repair advice.

## Confidence Model

`high` / `medium` / `low` / `insufficient_evidence` — never "certain," "guaranteed," or "proven." Cause-level confidence is capped at `low` for every catalog-derived possible cause, uniformly, even when the underlying error classification is `high` confidence. Example: `G0036` supports high confidence that incompatible matrix dimensions were reported; it does not automatically support high confidence that a specific cause (e.g. a missing transpose) explains it — this engine has no source-code-content evidence to distinguish between the several plausible triggers a cataloged error may have.

## Repair Boundary

`DiagnosticAssessment` has no field capable of holding replacement code — structurally, not just by convention. A fixed disclosure, `"Diagnosis does not modify or repair the program."`, is present in every diagnostic branch. No cause description, summary, or recommended step contains rewrite language anywhere in the module.

## CLI Behavior

`diagnose` is available any time after `execute` (mirrors `interpret`'s own rule); reports unavailability honestly if no result exists. It never calls `execute`, `plan`, or `confirm`; never auto-displays stdout/stderr; never auto-reads output files; never resets or mutates workspace state; produces identical output for identical evidence on repeated calls.

Recommended sequence after `execute`:
```
interpret
diagnose
stdout / stderr   (explicitly, when needed)
outputs
read <path>       (explicitly, when needed)
provenance
reset             (before a new single-shot attempt)
```

## Interpretation/Diagnosis Boundary

`interpret` answers "what happened?" `diagnose` answers "what verified causes may explain it, what evidence is missing, and what should be inspected next?" Neither answers "what exact code should replace the current code?" `diagnose` calls `interpret_execution(...)` internally (the same pure function `interpret` uses) rather than re-deriving classification a second way; neither command silently invokes the other's CLI surface or mutates state as a side effect of the other.

## Safety Boundaries (unchanged, re-verified)

Execution, confirmation, provenance, output-reading, and workspace-recovery contracts are all unchanged by this release. Diagnosis adds no execution behavior of any kind — it is a pure read of already-captured evidence.

## Remaining Limitations

- Diagnosis is limited to this repository's verified catalog knowledge; it does not reason from general programming knowledge and cannot infer user intent.
- Diagnosis cannot inspect variable values, matrix shapes, or source code content unless that evidence is directly supplied (today's execution evidence model does not provide it).
- Diagnosis does not repair code and does not retry.
- Unknown GAUSS error codes produce no diagnosis causes at all, and never inherit a known code's causes by similarity.
- `G0290`'s diagnostic knowledge remains documentation-only, mirroring its own catalog-entry verification status.
- No durable session integration; a diagnosis is available only for the current adapter session's captured result, cleared by `reset`.
- No statistical or methodological validity assessment.

## Next Recommended Milestone

Expand the verified error catalog further (more real-runtime-confirmed codes, and where possible upgrading `G0290` from documentation-only to dual-sourced) before attempting Repair Planning — Repair Planning's own quality will be bounded by how much verified knowledge Diagnosis has to draw on.
