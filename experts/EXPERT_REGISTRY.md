# Expert Registry

This registry summarizes the operational expert system in one place.

- It is a consolidation reference, not a runtime routing engine.
- Full expert behavior remains defined in each expert's `EXPERT.md`, `BODY_OF_KNOWLEDGE.md` where present, `reasoning.md`, `best_practices.md`, `common_mistakes.md`, and `OPERATIONAL_PROFILE.md`.
- `workflows/expert-routing.md` remains the detailed routing workflow — the authoritative activation matrix, decision rules, output contract, and worked examples live there, not here.
- This registry is intended to reduce drift and make ownership, non-ownership, escalation, and related files easier to audit at a glance, so a reader (or a future contributor adding an expert) does not need to read every operational profile in full just to find out who owns what.

## Registry Metadata

- **Current milestone:** `v0.18.0` - Expert System Consolidation
- **Captures operational state through:** `v0.17.0` - Product Expert Foundation
- **Operational experts:** 6
- **Runtime orchestration:** Not implemented
- **Routing model:** documented/manual-evaluation-driven
- **Detailed routing workflow:** `workflows/expert-routing.md`
- **Code Assistant workflow:** `workflows/code-assistant-response.md`
- **Operational interface:** `tools/operational_expert_interface.md`

## Operational Expert Summary

| Expert ID | Expert Name | Correctness Dimension | Primary Ownership | Does Not Own | Operational Profile | Foundation Files |
|---|---|---|---|---|---|---|
| `gauss-language` | GAUSS Language Expert | Implementation correctness | GAUSS syntax, command usage, data structures, package/base distinction, implementation patterns, official-doc-backed command evidence | Statistical validity, maintainability/design quality, documentation clarity, learning design, product/user-value reasoning | `experts/gauss-language/OPERATIONAL_PROFILE.md` | `experts/gauss-language/EXPERT.md`; `experts/gauss-language/BODY_OF_KNOWLEDGE.md`; `experts/gauss-language/COMMAND_CATEGORIES.md`; `experts/gauss-language/commands/README.md` |
| `econometrics` | Econometrics Expert | Methodological correctness | Estimator choice, assumptions, diagnostics, causal interpretation, forecasting/statistical evaluation, panel/time-series/cross-sectional methodology | GAUSS syntax, command signatures, package/base distinction, maintainability/design quality, documentation clarity, learning design, product/user-value reasoning | `experts/econometrics/OPERATIONAL_PROFILE.md` | `experts/econometrics/EXPERT.md`; `experts/econometrics/BODY_OF_KNOWLEDGE.md`; `experts/econometrics/reasoning.md`; `experts/econometrics/best_practices.md`; `experts/econometrics/common_mistakes.md`; `experts/econometrics/knowledge.md` |
| `software-engineering` | Software Engineering Expert | Maintainability/design correctness | Code organization, refactoring, readability, modularity, testability, error handling, edge cases, duplication, safe change management | GAUSS syntax, command evidence, statistical validity, documentation clarity, learning design, product/user-value reasoning | `experts/software-engineering/OPERATIONAL_PROFILE.md` | `experts/software-engineering/EXPERT.md`; `experts/software-engineering/BODY_OF_KNOWLEDGE.md`; `experts/software-engineering/reasoning.md`; `experts/software-engineering/best_practices.md`; `experts/software-engineering/common_mistakes.md`; `experts/software-engineering/knowledge.md` |
| `documentation` | Documentation Expert | Documentation/explanation correctness | Documentation clarity, reference structure, examples, comments/docstrings, usage guidance, parameter/return explanations, troubleshooting, caveats, terminology consistency | GAUSS syntax validity, statistical validity, maintainability/design quality, learning design, product/user-value reasoning | `experts/documentation/OPERATIONAL_PROFILE.md` | `experts/documentation/EXPERT.md`; `experts/documentation/BODY_OF_KNOWLEDGE.md`; `experts/documentation/reasoning.md`; `experts/documentation/best_practices.md`; `experts/documentation/common_mistakes.md`; `experts/documentation/knowledge.md` |
| `education` | Education Expert | Education/learning-design correctness | Learning objectives, instructional sequencing, scaffolding, practice exercises, feedback, assessment, misconception handling, prerequisite mapping, learner progression | GAUSS syntax validity, statistical validity, maintainability/design quality, documentation/reference clarity, product/user-value reasoning | `experts/education/OPERATIONAL_PROFILE.md` | `experts/education/EXPERT.md`; `experts/education/BODY_OF_KNOWLEDGE.md`; `experts/education/reasoning.md`; `experts/education/best_practices.md`; `experts/education/common_mistakes.md`; `experts/education/knowledge.md` |
| `product` | Product Expert | Product/user-value correctness | User problem framing, workflow fit, first-use experience, activation, time-to-value, adoption barriers, value proposition, positioning, prioritization, scope tradeoffs, discovery questions, product assumptions, product risk reasoning | GAUSS syntax validity, statistical validity, maintainability/design quality, documentation/reference clarity, learning-design quality, market proof, adoption certainty, product-market fit | `experts/product/OPERATIONAL_PROFILE.md` | `experts/product/EXPERT.md`; `experts/product/BODY_OF_KNOWLEDGE.md`; `experts/product/reasoning.md`; `experts/product/best_practices.md`; `experts/product/common_mistakes.md`; `experts/product/knowledge.md` |

## Activation Summary

Concise, registry-level activation guidance for each expert. This is not a full copy of any `OPERATIONAL_PROFILE.md` — see each expert's Activation Triggers, Non-Activation Cases, and Escalation Conditions sections for the complete, authoritative list.

### GAUSS Language Expert

- **Activate when the user asks about:** GAUSS syntax, command usage, data structures, package/base distinction, implementation patterns, code generation/debugging involving GAUSS.
- **Do not activate for:** pure methodology, product, education, documentation, or code-quality reasoning without GAUSS implementation content.
- **Escalate to:** Econometrics for methodology; Software Engineering for maintainability/design; Documentation for docs clarity; Education for learning design; Product for user value/product strategy.

### Econometrics Expert

- **Activate when the user asks about:** estimator choice, assumptions, diagnostics, causal/statistical interpretation, forecasting/statistical evaluation, panel/time-series/cross-sectional methodology.
- **Do not activate for:** syntax-only, code-design-only, documentation-only, education-only, or product-only tasks.
- **Escalate to:** GAUSS for implementation syntax; Software Engineering for maintainability; Documentation for explanation/docs; Education for teaching/learning flow; Product for user value/adoption/prioritization.

### Software Engineering Expert

- **Activate when the user asks about:** refactoring, code review, maintainability, modularity, readability, testability, error handling, edge cases, safe change management.
- **Do not activate for:** syntax-only, methodology-only, documentation-only, education-only, or product-only tasks.
- **Escalate to:** GAUSS for syntax; Econometrics for statistical validity; Documentation for user-facing docs; Education for exercises/learning sequence; Product for product tradeoffs or user impact.

### Documentation Expert

- **Activate when the user asks about:** reference documentation, usage guidance, comments/docstrings, examples, README/help text, troubleshooting, warnings/caveats, terminology consistency.
- **Do not activate for:** pure syntax lookup, pure methodology, pure code design, pure lesson design, or pure product strategy.
- **Escalate to:** GAUSS for syntax/evidence; Econometrics for methodological claims; Software Engineering for code-quality claims; Education for learning design; Product for positioning/user value/adoption framing.

### Education Expert

- **Activate when the user asks about:** lesson plans, curriculum, learning paths, onboarding learning flow, learning objectives, practice, assessment, feedback, scaffolding, misconception handling.
- **Do not activate for:** pure syntax lookup, pure methodology, pure code design, pure documentation/reference, or pure product strategy.
- **Escalate to:** GAUSS for syntax; Econometrics for methodology; Software Engineering for design/testability; Documentation for reference docs; Product for adoption/product strategy/user value.

### Product Expert

- **Activate when the user asks about:** user problem framing, jobs to be done, workflow fit, positioning, value proposition, first-use experience, activation, time-to-value, adoption barriers, prioritization, scope tradeoffs, product assumptions and risks.
- **Do not activate for:** pure syntax lookup, pure methodology, pure code design, pure documentation/reference, or pure lesson design.
- **Escalate to:** GAUSS for syntax; Econometrics for methodology; Software Engineering for design/technical debt; Documentation for docs clarity; Education for learning/onboarding design.

## Common Boundary Rules

- Command availability is not methodological validity.
- Syntax correctness is not maintainability.
- Clean code is not statistical validity.
- Clear documentation is not implementation correctness.
- Clear documentation is not statistical validity.
- Clear documentation is not learning effectiveness.
- Good instruction is not implementation correctness.
- Good instruction is not documentation quality.
- Good instruction is not product validation.
- Product value is not syntax correctness.
- Product value is not statistical validity.
- Product value is not maintainability.
- Product value is not documentation quality.
- Product value is not learning-design quality.
- User demand is not statistical validity.
- Product urgency is not acceptable design risk.
- Good documentation or training is not proof of product value.
- Evidence validation is structural, not execution.
- Testing recommendations are not execution claims.
- Pseudocode or unverified syntax must be labeled.
- Product hypotheses must be labeled when evidence is missing.
- Strictest applicable evidence/context requirement wins.

## Related Files by Expert

### GAUSS Language Expert

- `experts/gauss-language/EXPERT.md`
- `experts/gauss-language/BODY_OF_KNOWLEDGE.md`
- `experts/gauss-language/reasoning.md`
- `experts/gauss-language/best_practices.md`
- `experts/gauss-language/common_mistakes.md`
- `experts/gauss-language/knowledge.md`
- `experts/gauss-language/OPERATIONAL_PROFILE.md`
- `experts/gauss-language/COMMAND_CATEGORIES.md`
- `experts/gauss-language/commands/README.md`
- `experts/gauss-language/commands/olsmt.md`

### Econometrics Expert

- `experts/econometrics/EXPERT.md`
- `experts/econometrics/BODY_OF_KNOWLEDGE.md`
- `experts/econometrics/reasoning.md`
- `experts/econometrics/best_practices.md`
- `experts/econometrics/common_mistakes.md`
- `experts/econometrics/knowledge.md`
- `experts/econometrics/OPERATIONAL_PROFILE.md`

### Software Engineering Expert

- `experts/software-engineering/EXPERT.md`
- `experts/software-engineering/BODY_OF_KNOWLEDGE.md`
- `experts/software-engineering/reasoning.md`
- `experts/software-engineering/best_practices.md`
- `experts/software-engineering/common_mistakes.md`
- `experts/software-engineering/knowledge.md`
- `experts/software-engineering/OPERATIONAL_PROFILE.md`

### Documentation Expert

- `experts/documentation/EXPERT.md`
- `experts/documentation/BODY_OF_KNOWLEDGE.md`
- `experts/documentation/reasoning.md`
- `experts/documentation/best_practices.md`
- `experts/documentation/common_mistakes.md`
- `experts/documentation/knowledge.md`
- `experts/documentation/OPERATIONAL_PROFILE.md`

### Education Expert

- `experts/education/EXPERT.md`
- `experts/education/BODY_OF_KNOWLEDGE.md`
- `experts/education/reasoning.md`
- `experts/education/best_practices.md`
- `experts/education/common_mistakes.md`
- `experts/education/knowledge.md`
- `experts/education/OPERATIONAL_PROFILE.md`

### Product Expert

- `experts/product/EXPERT.md`
- `experts/product/BODY_OF_KNOWLEDGE.md`
- `experts/product/reasoning.md`
- `experts/product/best_practices.md`
- `experts/product/common_mistakes.md`
- `experts/product/knowledge.md`
- `experts/product/OPERATIONAL_PROFILE.md`

## Maintenance Notes

- Update this registry whenever a new expert is added, renamed, operationalized, or retired.
- Update this registry whenever ownership boundaries change.
- After updating this registry, check:
  - `workflows/expert-routing.md`
  - `workflows/code-assistant-response.md`
  - `agents/code-assistant/task_modes.md`
  - `prompts/code_assistant_system.md`
  - All `OPERATIONAL_PROFILE.md` files
  - `README.md`
  - `ROADMAP.md`
  - `KNOWN_LIMITATIONS.md`
  - `evaluations/benchmark-prompts.md`
  - `evaluations/benchmark-coverage.md`
  - `evaluations/runs/INDEX.md`
  - `CHANGELOG.md`
- This registry should summarize, not replace, detailed operational profiles.
- Avoid copying long decision-rule lists here; link to profiles instead.
- Treat this file as the first place to check for stale expert-count or ownership wording.
