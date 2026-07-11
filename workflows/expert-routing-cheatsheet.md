# Expert Routing Cheat Sheet

This cheat sheet summarizes common routing decisions across the six operational experts.

- It is a quick-reference companion to `workflows/expert-routing.md`.
- It does not replace the full routing workflow, expert registry, boundary matrix, or operational profiles.
- It is not a runtime routing engine.
- Use it to avoid over-activation, under-activation, stale expert-count wording, and boundary drift.

## Cheat Sheet Metadata

- **Current milestone:** `v0.18.0` - Expert System Consolidation
- **Captures operational state through:** `v0.17.0` - Product Expert Foundation
- **Operational experts:** 6
- **Runtime orchestration:** Not implemented
- **Routing model:** documented/manual-evaluation-driven
- **Detailed routing workflow:** `workflows/expert-routing.md`
- **Expert registry:** `experts/EXPERT_REGISTRY.md`
- **Boundary matrix:** `experts/EXPERT_BOUNDARY_MATRIX.md`

## Six-Axis Quick Classifier

| Axis | Owning Expert | Activate When the Request Involves | Do Not Activate For |
|---|---|---|---|
| GAUSS implementation | GAUSS Language Expert | GAUSS syntax, command usage, package/base distinction, DataFrame/matrix/array/structure usage, GAUSS code generation/debugging, verified command evidence. | Pure methodology, product strategy, documentation, education, or code-quality tasks without GAUSS implementation content. |
| Econometric methodology | Econometrics Expert | Estimator choice, assumptions, diagnostics, causal/statistical interpretation, forecasting/statistical evaluation, panel/time-series/cross-sectional methodology. | Syntax-only, code-design-only, docs-only, education-only, or product-only tasks. |
| Software engineering/code quality | Software Engineering Expert | Refactoring, code review, maintainability, readability, modularity, testability, error handling, edge cases, duplication, safe change management. | Syntax-only, methodology-only, documentation-only, education-only, or product-only tasks. |
| Documentation/explanation quality | Documentation Expert | Reference documentation, usage guidance, examples as documentation artifacts, comments/docstrings, README/help text, troubleshooting, warnings/caveats, terminology consistency. | Pure syntax lookup, pure methodology, pure code design, pure lesson design, or pure product strategy. |
| Education/learning design | Education Expert | Lesson plans, curriculum, learning paths, onboarding learning flow, learning objectives, practice, assessment, feedback, scaffolding, misconception handling, learner progression. | Pure syntax lookup, pure methodology, pure code design, pure documentation/reference, or pure product strategy. |
| Product/user value | Product Expert | User problem framing, jobs to be done, workflow fit, positioning, value proposition, first-use experience, activation, time-to-value, adoption barriers, prioritization, scope tradeoffs, product assumptions, product risks. | Pure syntax lookup, pure methodology, pure code design, pure documentation/reference, or pure lesson design. |

## Common Routing Patterns

| Pattern | Activate | Example Request | Key Boundary |
|---|---|---|---|
| 1. GAUSS-only | GAUSS Language | "How do I write a GAUSS procedure?" | Syntax validity does not prove methodology, maintainability, documentation quality, learning quality, or product value. |
| 2. Econometrics-only | Econometrics | "Which assumptions matter for OLS?" | Methodological correctness does not prove GAUSS implementation or product usefulness. |
| 3. Software-engineering-only | Software Engineering | "How should I reduce duplicated logic in this code?" | Maintainability does not prove syntax or statistical validity. |
| 4. Documentation-only | Documentation | "Can you make this reference page clearer?" | Clear docs do not prove syntax, methodology, learning effectiveness, or product value. |
| 5. Education-only | Education | "Can you design a beginner learning sequence for this concept?" | Good instruction does not prove syntax, methodology, docs quality, or product value. |
| 6. Product-only | Product | "Does this feature idea solve a real user problem?" | Product value does not prove syntax, methodology, design, docs, or learning quality. |
| 7. GAUSS + Econometrics | GAUSS Language + Econometrics | "Write GAUSS code for an OLS model and explain the assumptions." | Command availability and statistical appropriateness are separate. |
| 8. GAUSS + Software Engineering | GAUSS Language + Software Engineering | "Refactor this GAUSS code without changing behavior." | Valid syntax and maintainable structure are separate. |
| 9. GAUSS + Documentation | GAUSS Language + Documentation | "Document this GAUSS function with valid examples." | Examples need syntax evidence; docs need clarity. |
| 10. GAUSS + Education | GAUSS Language + Education | "Teach beginners how to write a GAUSS procedure." | Lesson quality does not validate syntax. |
| 11. GAUSS + Product | GAUSS Language + Product | "Should we add this GAUSS shortcut syntax for users?" | Product usefulness does not approve syntax. |
| 12. Econometrics + Documentation | Econometrics + Documentation | "Explain this diagnostic test clearly in the docs." | Clear explanation does not prove methodological appropriateness. |
| 13. Econometrics + Education | Econometrics + Education | "Teach beginners OLS assumptions and diagnostics." | Learning design does not prove statistical validity. |
| 14. Econometrics + Product | Econometrics + Product | "Would an automatic causal-impact feature make users trust results?" | User trust does not prove causal validity. |
| 15. Software Engineering + Documentation | Software Engineering + Documentation | "Document this refactoring pattern for contributors." | Docs clarity and code design quality are separate. |
| 16. Software Engineering + Education | Software Engineering + Education | "Turn refactoring duplicated logic into a learning exercise." | Exercise quality does not prove maintainability. |
| 17. Software Engineering + Product | Software Engineering + Product | "Should we ship quickly or refactor first because technical debt affects future work?" | Product urgency does not make design risk acceptable. |
| 18. Documentation + Education | Documentation + Education | "Is a clear reference page enough to teach beginners?" | Documentation supports reference use; education supports learning over time. |
| 19. Documentation + Product | Documentation + Product | "Write feature positioning and outline the help page." | Good positioning does not prove documentation clarity. |
| 20. Education + Product | Education + Product | "Could onboarding training improve adoption of this feature?" | Training can support adoption but does not prove product value. |
| 21. Documentation + Education + Product | Documentation + Education + Product | "Do we need docs, training, or product changes to improve adoption?" | Docs, learning, and product value are separate supports. |
| 22. GAUSS + Documentation + Education + Product | GAUSS Language + Documentation + Education + Product | "Design a beginner onboarding flow for a GAUSS feature with docs and product framing." | Implementation, docs, learning, and product claims must remain separate. |
| 23. GAUSS + Econometrics + Product | GAUSS Language + Econometrics + Product | "Should we add a GAUSS econometrics feature, and is it methodologically appropriate?" | Syntax, methodology, and user value are separate. |
| 24. All six | All six experts | "Design a GAUSS econometrics feature, review implementation risk, document it, teach it, and position it for customers." | Keep all six correctness dimensions separate. |
| 25. Neither | None / normal response | "Write a friendly one-sentence update." | Avoid expert over-activation. |

## Evidence and Context Quick Rules

- GAUSS syntax/signatures/returns/package status require GAUSS Language Expert and verified GAUSS evidence.
- Methodological/statistical claims require Econometrics Expert context.
- Maintainability/refactoring/design claims require Software Engineering Expert context.
- Documentation/reference clarity claims require Documentation Expert context.
- Learning-design claims require Education Expert context.
- Product/user-value claims require Product Expert context.
- Market validation, adoption certainty, willingness to pay, product-market fit, and prioritization certainty require user/customer evidence.
- Product hypotheses must be labeled when evidence is missing.
- Pseudocode or unverified syntax must be labeled.
- Testing recommendations are not execution claims.
- Evidence validation is structural, not semantic/execution validation.
- Strictest applicable evidence/context requirement wins.

## Escalation Quick Rules

- If syntax appears in a non-GAUSS task, route/escalate to the GAUSS Language Expert.
- If statistical claims appear in a non-econometrics task, route/escalate to the Econometrics Expert.
- If maintainability/design claims appear in another task, route/escalate to the Software Engineering Expert.
- If docs/reference clarity appears in another task, route/escalate to the Documentation Expert.
- If learning objectives, sequencing, practice, or assessment appear in another task, route/escalate to the Education Expert.
- If user value, workflow fit, adoption, positioning, or prioritization appears in another task, route/escalate to the Product Expert.
- If the request is ordinary writing with no expert dimension, do not activate experts.

## Anti-Overclaiming Checklist

- [ ] Did I separate implementation, methodology, maintainability, documentation, education, and product claims?
- [ ] Did I avoid treating product value as correctness evidence?
- [ ] Did I avoid treating user demand as statistical validity?
- [ ] Did I avoid treating product urgency as acceptable design risk?
- [ ] Did I avoid treating clear documentation as execution or correctness evidence?
- [ ] Did I avoid treating good training as product validation?
- [ ] Did I label product hypotheses when evidence is missing?
- [ ] Did I label pseudocode or unverified syntax?
- [ ] Did I avoid claiming tests/code were run unless actually executed?
- [ ] Did I avoid activating experts for ordinary writing tasks?

## Maintenance Notes

- Update this cheat sheet when an expert is added, retired, renamed, or changes ownership.
- Check this cheat sheet whenever `workflows/expert-routing.md` changes.
- Check this cheat sheet whenever `experts/EXPERT_REGISTRY.md` or `experts/EXPERT_BOUNDARY_MATRIX.md` changes.
- Keep this file short enough to be useful as a cheat sheet.
- Do not duplicate full operational profiles or all routing examples.
- Search for stale expert-count wording after updates.
