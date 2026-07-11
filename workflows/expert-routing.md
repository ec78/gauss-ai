# Expert Routing Workflow

## Purpose

This workflow routes Code Assistant tasks through operational experts. It replaces the vague "identify relevant experts" step in `workflows/code-assistant-response.md` and `prompts/code_assistant_system.md` with a checkable routing procedure: when to consult one or more operational experts, what to gather before applying their decision rules, and how to evaluate whether routing actually happened.

It now supports six operational experts:

- **GAUSS Language Expert** — implementation correctness.
- **Econometrics Expert** — methodological correctness.
- **Software Engineering Expert** — maintainability/design correctness.
- **Documentation Expert** — documentation/explanation correctness.
- **Education Expert** — learning-design correctness.
- **Product Expert** — product/user-value correctness.

Clarifications:

- **It is not a runtime orchestration engine.** No code executes this workflow; it is followed the same way `workflows/native-command-selection.md` or `workflows/retrieval-backed-response-pattern.md` are followed today — as a documented reasoning procedure a response can be checked against. Nothing in this update introduces multi-expert *execution* machinery; it extends the documented reasoning procedure from five operational experts to six, the same way `v0.16.0` extended it from four to five.
- **It is a documented reasoning procedure for the Code Assistant**, not a new evidence system or a new set of decision rules — the rules it applies come from `experts/gauss-language/OPERATIONAL_PROFILE.md`, `experts/econometrics/OPERATIONAL_PROFILE.md`, `experts/software-engineering/OPERATIONAL_PROFILE.md`, `experts/documentation/OPERATIONAL_PROFILE.md`, `experts/education/OPERATIONAL_PROFILE.md`, `experts/product/OPERATIONAL_PROFILE.md`, and the evidence machinery already defined in `schemas/command_lookup_evidence.schema.json` and `workflows/retrieval-backed-response-pattern.md`.
- **This is deliberately not a full 64-combination routing engine.** With six experts, a fully enumerated activation table would have 2⁶ = 64 rows. Step 4 below documents the most common patterns (a compact activation matrix plus worked examples) rather than exhaustively enumerating every possible subset. Any combination of the six experts may activate; the coordination principles below (claims stay separable, strictest evidence/context requirement wins) govern any combination, including ones without their own named row or worked example.
- **The Product Expert is operationalized as of `v0.17.0`** (`experts/product/OPERATIONAL_PROFILE.md`), documented here for the first time. **Code Assistant workflow/prompt integration for the Product Expert is not yet done** — `workflows/code-assistant-response.md`, `agents/code-assistant/task_modes.md`, and `prompts/code_assistant_system.md` still reflect five-expert integration only, and updating them is a separate, planned follow-up task (`planning/v0.17.0-product-expert-foundation.md`).
- **Future experts can be added using the same operational interface** (`tools/operational_expert_interface.md`) — a new expert needs an operational profile filled in against that interface, after which this workflow's activation-trigger and non-activation steps gain one more expert to check against, and Step 4's activation matrix gains one more column, the same way the Product Expert's addition here expanded the matrix from a fourteen-pattern table over five axes to a sixteen-pattern table over six axes.

## Operational Experts Currently Supported

| Expert | Owns | Does not own |
|---|---|---|
| GAUSS Language Expert | GAUSS syntax, command selection, data structures, package/base distinction, implementation correctness | Econometric methodology or statistical validity; code maintainability/design; documentation clarity; learning design; product/user-value reasoning |
| Econometrics Expert | Model choice, assumptions, diagnostics, interpretation, causal/predictive framing, statistical validity | Exact GAUSS syntax, command return fields, package/base distinction; code maintainability/design; documentation clarity; learning design; product/user-value reasoning |
| Software Engineering Expert | Code quality, maintainability, modularity, readability, refactoring, testability, error handling, edge-case thinking, safe change management | Exact GAUSS syntax, command evidence, package/base distinction; econometric methodology or statistical validity; documentation clarity; learning design; product/user-value reasoning |
| Documentation Expert | Documentation clarity, reference structure, examples, comments/docstrings, usage guidance, input/output explanation, warnings/caveats, troubleshooting guidance, terminology consistency, audience awareness, documentation completeness | Exact GAUSS syntax, command evidence; econometric methodology or statistical validity; code maintainability/design; instructional sequencing/learning design; product/user-value reasoning |
| Education Expert | Learning objectives, instructional sequencing, scaffolding, practice exercises, feedback design, assessment design, learner progression, prerequisite mapping, misconception handling, cognitive load management, workshop/session structure, training plans, learning paths, onboarding learning flow | Exact GAUSS syntax, command evidence; econometric methodology or statistical validity; code maintainability/design; documentation/reference clarity as its primary domain; product strategy |
| Product Expert | User problem framing, customer/job-to-be-done framing, workflow fit, user journey, first-use experience, activation and time-to-value, adoption barriers, value proposition, positioning, product requirements framing, prioritization tradeoffs, scope tradeoffs, feature usefulness, customer segment fit, product assumptions, product risk identification, product discovery questions, MVP/scope reasoning, adoption and retention considerations | Exact GAUSS syntax, command evidence; econometric methodology or statistical validity; code maintainability/design as its primary domain; documentation/reference clarity as its primary domain; learning-design correctness as its primary domain; guaranteed market outcomes |

### Software Engineering Expert — Failure Modes Prevented

- Treating valid code as well-designed code.
- Unsafe refactors that silently change behavior.
- Duplicated or tangled logic left unaddressed.
- Unclear naming that obscures intent.
- Hidden dependencies between parts of the code.
- Missing validation/testing strategy for risky changes.
- Claiming code was executed when it was not.
- Treating clean code as statistical validity.

### Documentation Expert — Failure Modes Prevented

- Clear prose being treated as syntax correctness.
- Documentation clarity being treated as statistical validity.
- Documentation quality being treated as code maintainability.
- Unverified examples presented as exact syntax.
- Missing prerequisites.
- Missing inputs/outputs.
- Buried caveats.
- Unclear audience assumptions.
- Confusing reference and tutorial structures.
- Replacing education/curriculum design with documentation.

### Education Expert — Failure Modes Prevented

- Content lists being treated as learning sequences.
- Clear documentation being treated as instruction.
- Lessons without measurable objectives.
- Exercises that do not match objectives.
- Missing prerequisites.
- Missing feedback or assessment.
- Overloading beginners too early.
- Unsupported syntax in lessons.
- Unsupported methodology claims in lessons.
- Training quality being treated as product value.
- Education being conflated with product strategy.

### Product Expert — Failure Modes Prevented

- Feature ideas being treated as validated user problems.
- Product value being treated as implementation correctness.
- User demand being treated as statistical validity.
- Product urgency being treated as acceptable design risk.
- Good documentation or training being treated as product validation.
- Internal enthusiasm being treated as customer evidence.
- Polished demos being treated as proof of value.
- Prioritization without tradeoff criteria.
- Vague customer segments.
- Missing adoption-barrier analysis.
- Market claims without evidence.

## Routing Principles

- Activate experts based on task/content triggers, not just keyword matching — a task can involve GAUSS, econometrics, code quality, documentation, learning design, or product reasoning without any of those words appearing (e.g. "translate this R model" implies GAUSS as the target; "does this coefficient mean X causes Y" implies econometric interpretation; "this script is a mess" implies a maintainability concern; "I can't tell what this function expects" implies a documentation concern; "how do I get my team up to speed on this" implies a learning-design concern; "will people actually use this" implies a product concern).
- Expert activation is internal by default; the Code Assistant does not need to announce which expert(s) it consulted.
- Correct routing is evaluated through response behavior — whether decision rules were applied and evidence/context thresholds were honored — not through a self-reported label.
- Expert profiles add constraints and decision rules; they do not loosen evidence requirements. An expert can require more evidence than the general workflow demands, never less.
- Evidence requirements for GAUSS claims remain governed by the evidence schema (`schemas/command_lookup_evidence.schema.json`) and the retrieval-backed response pattern (`workflows/retrieval-backed-response-pattern.md`); this workflow routes *to* those, it does not redefine them.
- Non-activation cases matter as much as activation cases; do not over-route to any expert for tasks that do not need them. Unnecessary activation is itself a routing failure, not a safe default.
- Different experts own different kinds of correctness: GAUSS syntax correctness (implementation), econometric validity (methodology), software maintainability (design), documentation clarity (explanation), learning design (education), and user value (product) are six separate claims, and no expert may answer for another's domain.
- Command availability is not methodological validity — a GAUSS command existing for a method is never evidence the method is the right choice for the user's data.
- Methodological appropriateness is not implementation evidence — a method being the right statistical choice is never evidence that specific GAUSS syntax exists or works as described.
- Valid GAUSS code can still be poorly designed — syntactic validity and good design are independent claims.
- Clean code can still be statistically invalid — code quality and methodological soundness are independent claims.
- A methodologically appropriate analysis can still be poorly implemented or hard to maintain — methodological validity and maintainability are independent claims.
- Clear documentation does not prove code correctness, statistical validity, or maintainability — documentation clarity is an independent claim from all three.
- Valid GAUSS code may still be poorly documented; a methodologically correct analysis may still be poorly documented; well-designed code may still need better documentation — documentation quality never follows automatically from the other three.
- A well-designed lesson does not prove code correctness, statistical validity, maintainability, or documentation quality — learning design is an independent claim from all four.
- A good training plan does not prove product value, adoption, or prioritization — training quality and product decisions are independent claims.
- Product value does not prove code correctness, statistical validity, maintainability, documentation quality, or education quality — product/user-value reasoning is an independent claim from all five.
- Strong user demand does not prove statistical validity — users wanting a feature is not evidence the underlying method is sound.
- Product urgency does not prove design risk is acceptable — a deadline is not evidence that a risky shortcut is safe.
- Good documentation or training does not prove product value — clear docs or well-taught onboarding can support adoption without proving the underlying feature is valuable or should be prioritized.
- The Software Engineering Expert may recommend structure but cannot invent GAUSS syntax to implement it; unverified structural suggestions must be labeled as pseudocode.
- The Software Engineering Expert may recommend tests or checks but cannot claim code was executed or a test was run unless it actually was.
- The Documentation Expert may improve wording, examples, and user-facing structure but cannot invent GAUSS syntax; any example must use verified syntax or be labeled pseudocode/unverified.
- The Documentation Expert may clarify statistical caveats for a reader but cannot certify methodology; it may write comments/docstrings but cannot certify code design.
- The Education Expert may sequence, scaffold, and assess learning but cannot invent GAUSS syntax; any example used in a lesson must use verified syntax or be labeled pseudocode/unverified.
- The Education Expert may teach statistical concepts but cannot certify methodology; it may design code-quality learning exercises but cannot certify code design; it may use documentation as supporting material but does not replace the Documentation Expert.
- The Education Expert is distinct from the Documentation Expert (documentation supports task completion and reference use right now; education supports learning over time through sequencing, scaffolding, exercises, and pedagogy) and from the Product Expert (education supports learner development; the Product Expert owns user problem framing, workflow fit, adoption, positioning, value proposition, and prioritization) — a good training curriculum is never evidence a feature is valuable or should be prioritized.
- The Product Expert may frame user problems, product tradeoffs, adoption risks, value propositions, and discovery questions but cannot invent GAUSS syntax.
- The Product Expert may reason about the user value of an analysis feature but cannot certify methodology.
- The Product Expert may reason about technical debt or implementation complexity as a product risk but cannot certify code design.
- The Product Expert may recommend documentation or education as adoption supports but cannot certify documentation or learning quality.
- Product hypotheses must be labeled as hypotheses when evidence is missing — a plausible narrative is not validated demand.
- Market validation, adoption certainty, product-market fit, and prioritization certainty require actual user/customer evidence, not an internally plausible narrative alone.
- The Product Expert is distinct from the Documentation Expert (documentation helps a reader complete a task or understand a reference right now; product frames whether the underlying feature solves a real problem and is positioned/prioritized correctly) and from the Education Expert (education supports learner development for users who already need the product; product frames whether the product itself is worth building, teaching, or documenting at all, plus adoption/positioning/prioritization).
- When multiple experts activate, keep implementation, methodology, maintainability, documentation, education, and product claims separate in substance, even when the final response reads as one coherent answer.
- If two or more experts' conclusions appear to conflict (for example, a command exists and is syntactically fine, but the recommended model isn't appropriate for the data, or a refactor is well-organized but changes behavior, or a feature is well-positioned but the underlying syntax is unverified), surface the distinction explicitly rather than silently resolving it in either direction.
- The strictest applicable evidence/context requirement wins — if a task touches multiple domains, meeting only one expert's bar is not sufficient to answer the whole question.

## Step 1 — Classify the Task

Use the Code Assistant's existing task modes (`agents/code-assistant/task_modes.md`):

- Code Generation
- Debugging
- Code Explanation
- Code Translation
- Code Review
- Refactoring
- Optimization
- Documentation
- Test Generation
- Design Guidance

Add a second classification pass, independent of task mode, that this workflow's routing decision actually consumes. Answer six independent questions about the task — each is a yes/no judgment, not a single label, since a task can be "yes" on more than one axis at once:

1. **GAUSS implementation axis** — does the answer turn on GAUSS syntax, command selection, or language mechanics? Examples: GAUSS syntax, command usage, package/base distinction, DataFrame/matrix/structure usage, GAUSS code generation/debugging.
2. **Econometric methodology axis** — does the answer turn on model/estimator choice, assumptions, diagnostics, or interpretation? Examples: estimator choice, assumptions, diagnostics, causal interpretation, forecasting/statistical evaluation, panel/time-series/cross-sectional modeling.
3. **Software engineering/code-quality axis** — does the answer turn on code organization, maintainability, or safe change management? Examples: refactoring, code review, maintainability, readability, modularity, testability, error handling, edge cases, duplication, safe change management.
4. **Documentation/explanation-quality axis** — does the answer turn on how clearly something is explained, structured, or documented for a reader? Examples: writing or improving docs, reference structure, examples, comments/docstrings, usage notes, parameter/return explanations, troubleshooting guidance, warnings/caveats, README/help text, audience clarity, terminology consistency.
5. **Education/learning-design axis** — does the answer turn on how a topic is sequenced, scaffolded, practiced, and assessed for a learner over time? Examples: lesson plans, curriculum design, learning paths, training plans, workshop outlines, learning objectives, practice exercises, quizzes or assessments, feedback prompts, scaffolding, concept sequencing, beginner-to-advanced progression, misconception correction, prerequisite mapping, guided practice, worked examples for learning.
6. **Product/user-value axis** — does the answer turn on whether a feature or capability solves a real user problem, fits a user's workflow, and has a credible path to adoption? Examples: product strategy, positioning, user problem framing, jobs to be done, workflow fit, user journey, first-use experience, activation, time-to-value, adoption barriers, feature prioritization, value proposition, product scope, MVP framing, product tradeoffs, customer segment fit, product discovery questions, success criteria, product risk assessment.

The combination of the six yes/no answers determines the routing pattern in Step 4.

Examples:

- "What is the exact syntax for `olsmt`?" → GAUSS implementation only.
- "Is OLS appropriate for this causal question?" → econometric methodology only.
- "How should I refactor this generic duplicated pseudocode?" → software engineering only.
- "Rewrite this technical note into clearer user-facing documentation." → documentation only.
- "Create a three-part learning sequence for a generic technical concept." → education only.
- "Does this feature idea solve a real user problem?" → product/user-value only.
- "Translate this regression into GAUSS and tell me what diagnostics to run" → GAUSS implementation + econometric methodology.
- "Document this GAUSS procedure and include a usage example." → GAUSS implementation + documentation.
- "Teach beginners how to write a GAUSS procedure." → GAUSS implementation + education.
- "Add comments/docstrings explaining the design intent of this helper function." → software engineering + documentation.
- "Turn refactoring principles into a practice exercise." → software engineering + education.
- "Should we ship quickly or refactor first because technical debt may affect future product work?" → software engineering + product/user-value.
- "Teach logistic regression in GAUSS, structure reusable code, document the workflow, design practice exercises, and frame the product value." → all six axes.
- "Write a changelog entry" → none of the six axes.

This step is the same task-mode classification already required by `workflows/code-assistant-response.md` Step 1 and `prompts/code_assistant_system.md`'s "Classify the task" step, with the six-axis pass added specifically for this workflow's routing decision — it is not a new classification pass end to end.

## Step 2 — Match Expert Activation Triggers

### GAUSS Language Expert triggers

Use `experts/gauss-language/OPERATIONAL_PROFILE.md` as the source of truth — the list below mirrors its Activation Triggers section and should not be allowed to drift from it.

Route through the GAUSS Language Expert when the task involves:

- GAUSS code generation
- GAUSS debugging
- GAUSS code translation
- GAUSS code review
- Refactoring or optimizing GAUSS code
- GAUSS test generation
- GAUSS command/procedure selection
- GAUSS syntax verification
- DataFrame vs. matrix vs. array vs. structure decisions
- Package-specific vs. base-GAUSS distinction
- Unfamiliar command names or cross-language idioms
- Version-sensitive choices such as `qnewtonmt` vs. `minimize`

### Econometrics Expert triggers

Use `experts/econometrics/OPERATIONAL_PROFILE.md` as the source of truth — the list below mirrors its Activation Triggers section and should not be allowed to drift from it.

Route through the Econometrics Expert when the task involves:

- Model or estimator appropriateness
- Coefficient, p-value, confidence interval, prediction interval, or model-output interpretation
- Diagnostics or robustness-check recommendations
- Causal interpretation or identification concerns
- Endogeneity, omitted variables, selection bias, or treatment/control design
- Panel/time-series/cross-sectional/forecasting/IV/GMM/GLM/quantile method choice
- Methodological code review
- Valid-code-but-statistically-questionable scenarios
- Translating or implementing an econometric method in GAUSS where methodology and implementation both matter

### Software Engineering Expert triggers

Use `experts/software-engineering/OPERATIONAL_PROFILE.md` as the source of truth — the list below mirrors its Activation Triggers section and should not be allowed to drift from it.

Route through the Software Engineering Expert when the task involves:

- Refactoring requests
- Code review requests
- Maintainability concerns
- Readability concerns
- Modularity or decomposition requests
- Duplicated logic
- Procedure/function design
- Test strategy
- Error handling
- Edge cases
- Project/code organization
- Safe incremental changes
- Complexity concerns
- Reviewing generated code for design weaknesses
- Requests to clean up messy code
- Requests to make code easier to maintain, test, or extend

### Documentation Expert triggers

Use `experts/documentation/OPERATIONAL_PROFILE.md` as the source of truth — the list below mirrors its Activation Triggers section and should not be allowed to drift from it.

Route through the Documentation Expert when the task involves:

- Writing or improving documentation
- Explaining code for users
- Writing examples
- Writing comments or docstrings
- Documenting procedures/functions
- Documenting inputs/outputs
- Explaining parameters or return values
- Creating usage notes
- Turning technical notes into user-facing docs
- Improving reference pages
- Writing troubleshooting guidance
- Reducing ambiguity
- Making documentation beginner-friendly without creating a full lesson plan
- Adding warnings, caveats, or prerequisites
- Documenting assumptions
- Improving help text or README sections
- Reviewing docs for clarity/completeness

### Education Expert triggers

Use `experts/education/OPERATIONAL_PROFILE.md` as the source of truth — the list below mirrors its Activation Triggers section and should not be allowed to drift from it.

Route through the Education Expert when the task involves:

- Lesson plans
- Curriculum design
- Learning paths
- Training plans
- Onboarding learning sequences
- Workshop outlines
- Learning objectives
- Practice exercises
- Quizzes or assessments
- Feedback prompts
- Scaffolding
- Concept sequencing
- Beginner-to-advanced progression
- Misconception correction
- Prerequisite mapping
- Guided practice
- Worked examples for learning
- Remediation activities
- Teaching GAUSS concepts
- Teaching econometric concepts
- Teaching coding or workflow concepts
- Turning a topic into a learning experience over time

### Product Expert triggers

Use `experts/product/OPERATIONAL_PROFILE.md` as the source of truth — the list below mirrors its Activation Triggers section and should not be allowed to drift from it.

Route through the Product Expert when the task involves:

- Product strategy
- Product positioning
- User problem framing
- Customer problems
- Jobs to be done
- Workflow fit
- User journey
- Onboarding experience as product experience
- First-use experience
- Activation
- Time-to-value
- Adoption barriers
- Feature prioritization
- Feature usefulness
- Value proposition
- Customer segment fit
- Product requirements
- Product scope
- MVP framing
- Product tradeoffs
- User feedback interpretation
- Product discovery questions
- User success criteria
- Release impact framing
- Roadmap tradeoffs
- Product risk assessment

## Step 3 — Check Non-Activation Cases

### GAUSS Language Expert non-activation

Do not activate the GAUSS Language Expert for:

- General writing unrelated to GAUSS
- Release tracking
- Changelog drafting
- Readiness-checklist bookkeeping
- General project management
- Generic statistics/econometrics explanations with no GAUSS implementation
- Non-GAUSS conceptual explanations, unless a GAUSS implementation is also requested

### Econometrics Expert non-activation

Do not activate the Econometrics Expert for:

- Exact GAUSS syntax only
- GAUSS command return fields only
- Package/base-GAUSS distinction only
- Low-level syntax/debugging only
- Release tracking
- Changelog drafting
- General writing
- Generic programming architecture with no statistical modeling issue
- Purely mechanical formatting/documentation tasks

### Software Engineering Expert non-activation

Do not activate the Software Engineering Expert for:

- Simple GAUSS syntax lookup only
- Exact GAUSS command documentation retrieval only
- Pure econometric interpretation without code/design concerns
- Pure documentation writing
- Pure education/lesson planning
- Product strategy
- General prose editing
- Release-note writing
- CI guard questions, unless code/design quality is involved
- Simple factual questions unrelated to software design or code quality

### Documentation Expert non-activation

Do not activate the Documentation Expert for:

- Simple GAUSS syntax lookup only
- Exact command documentation retrieval only, unless the user asks to rewrite or explain it
- Pure econometric interpretation without documentation intent
- Pure code refactoring without user-facing explanation/documentation intent
- Pure education/lesson planning
- Curriculum design
- Product strategy
- General prose editing unrelated to technical/product documentation
- Release-note writing, unless the release note is technical documentation
- CI guard questions, unless documentation clarity is involved
- Simple factual questions unrelated to documentation quality

### Education Expert non-activation

Do not activate the Education Expert for:

- Simple GAUSS syntax lookup only
- Exact command documentation retrieval only
- Pure econometric interpretation without teaching/learning intent
- Pure code refactoring without teaching/learning intent
- Pure documentation/reference writing without learning progression
- Product strategy
- General prose editing unrelated to learning design
- Release-note writing
- CI guard questions, unless learning/evaluation design is involved
- Simple factual questions unrelated to learning design
- A one-off explanation when the user does not ask for teaching sequence, practice, scaffolding, or learning progression

### Product Expert non-activation

Do not activate the Product Expert for:

- Simple GAUSS syntax lookup only
- Exact command documentation retrieval only
- Pure econometric interpretation without product/user-value intent
- Pure code refactoring without product/user-value intent
- Pure documentation/reference writing without product/user-value intent
- Pure education/lesson planning without product/user-value intent
- General prose editing unrelated to product strategy or user value
- Release-note writing, unless product positioning or user impact framing is requested
- CI guard questions, unless product risk or user impact is involved
- Simple factual questions unrelated to product reasoning

### None of the six

Do not activate any expert for tasks such as:

- Changelog entries
- Release readiness notes
- General project tracking
- Repository housekeeping with no GAUSS syntax, no statistical-methodology question, no code-quality question, no documentation-clarity question, no learning-design question, and no product-reasoning question

Negative routing is part of correctness, not an afterthought, for each expert individually and for the none-of-the-six case. A response that applies GAUSS-specific, econometric, software-engineering, documentation, education, or product decision rules and evidence/context requirements to a task that never needed them is a routing failure in the same way a missed activation is — it adds unrequested scope, and evaluation (Step 11) checks for it explicitly.

## Step 4 — Determine the Routing Pattern

Any subset of the six operational experts may activate — this step does not enumerate all 64 mathematically possible combinations as a combinatorial routing engine. Instead, it gives a compact activation matrix covering the most common patterns, plus the coordination principles (above) that govern any combination, including ones without their own named row.

### Activation Matrix

| Pattern | GAUSS Language | Econometrics | Software Engineering | Documentation | Education | Product | Typical request | Response rule |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|---|
| 1. GAUSS-only | ✓ | | | | | | "What does `strindx` return when not found?" | Answer from verified evidence only. |
| 2. Econometrics-only | | ✓ | | | | | "Does p=0.03 mean the model explains 3%?" | Answer from methodological reasoning only. |
| 3. Software-engineering-only | | | ✓ | | | | "How should I refactor this generic duplicated pseudocode?" | Answer from design reasoning only; label unverified structure as pseudocode. |
| 4. Documentation-only | | | | ✓ | | | "Rewrite this technical note into clearer user-facing documentation." | Answer from documentation reasoning only; no syntax/methodology/design claims needed. |
| 5. Education-only | | | | | ✓ | | "Create a three-part learning sequence for a generic technical concept." | Answer from learning-design reasoning only; define objectives, sequence, practice, and checks for understanding. |
| 6. Product-only | | | | | | ✓ | "Does this feature idea solve a real user problem?" | Answer from product reasoning only; frame the user, problem, workflow, assumptions, and discovery questions; do not treat the idea as validated without evidence. |
| 7. Product + Documentation | | | | ✓ | | ✓ | "Turn this feature into positioning and a user-facing help section." | Product Expert owns value proposition, user problem, and positioning; Documentation Expert owns clarity, reference/usage structure, and examples; keep product claims separate from documentation quality. |
| 8. Product + Education | | | | | ✓ | ✓ | "Can onboarding training reduce adoption friction for this feature?" | Product Expert owns adoption-barrier and time-to-value reasoning; Education Expert owns learning sequence, practice, and onboarding learning flow; does not claim training quality proves feature value. |
| 9. Product + GAUSS | ✓ | | | | | ✓ | "Should we add this GAUSS feature, and is the proposed syntax valid?" | Product Expert owns user problem, workflow fit, and prioritization tradeoffs; GAUSS Language Expert owns the syntax/evidence boundary; does not invent or approve GAUSS syntax without evidence. |
| 10. Product + Econometrics | | ✓ | | | | ✓ | "Would adding this analysis feature make users trust the results more?" | Product Expert owns user value, workflow, and adoption reasoning; Econometrics Expert owns whether the analysis is statistically/methodologically valid; does not claim product usefulness proves statistical validity. |
| 11. Product + Software Engineering | | | ✓ | | | ✓ | "Should we ship quickly or refactor first because technical debt may affect future product work?" | Product Expert owns user value, timing, and scope tradeoff; Software Engineering Expert owns maintainability/design risk; does not treat product urgency as proof design risk is acceptable. |
| 12. Documentation + Education + Product | | | | ✓ | ✓ | ✓ | "Do we need docs, training, or product changes to help users adopt this workflow?" | Product Expert owns adoption framing and tradeoffs; Documentation Expert owns reference clarity; Education Expert owns learning sequence and practice; keep all three claims separately attributable. |
| 13. GAUSS + Documentation + Education + Product | ✓ | | | ✓ | ✓ | ✓ | "Design a beginner onboarding flow for a GAUSS feature with docs and product framing." | GAUSS Language Expert verifies syntax; Documentation Expert owns reference support; Education Expert owns the onboarding learning sequence; Product Expert owns onboarding-as-product-experience framing and adoption strategy. |
| 14. GAUSS + Econometrics + Product | ✓ | ✓ | | | | ✓ | "Should we add a GAUSS econometric feature, and would it be methodologically appropriate?" | GAUSS Language Expert verifies syntax; Econometrics Expert owns methodological appropriateness; Product Expert owns user value and prioritization; claims stay separate. |
| 15. All six | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | "Design a GAUSS econometrics feature, structure implementation risks, document it, teach it, and frame product value." | All six claims (implementation, methodology, maintainability, documentation, education, product) stay separate and separately attributable. |
| 16. Neither | | | | | | | "Write a nontechnical announcement." | Answer normally; do not impose expert routing or decision rules from any of the six. |

Several combinations from the prior five-expert matrix — **GAUSS + Education**, **Econometrics + Education**, **Documentation + Education**, **Software Engineering + Education**, **GAUSS + Documentation + Education**, **Econometrics + Documentation + Education**, **GAUSS + Econometrics + Documentation + Education**, and **all five** — plus older combinations from the four-expert-era matrix — **GAUSS + Econometrics**, **GAUSS + Software Engineering**, **Econometrics + Software Engineering**, **GAUSS + Software Engineering + Documentation**, **GAUSS + Econometrics + Documentation**, and **GAUSS + Econometrics + Software Engineering** — are not repeated as their own matrix rows here, since they involve no product dimension and are already fully covered by the `v0.14.0`-`v0.16.0` worked examples in Routing Examples below. The matrix's job is to make the *new* sixth axis and its most common interactions readable; it is not a replacement for those existing patterns.

For a pattern that matches none of the sixteen rows above (for example, Software Engineering + Documentation + Product with no GAUSS, Econometrics, or Education involved), apply the general coordination principles: identify which axes are genuinely "yes" per Step 1, activate exactly those experts, gather each one's required evidence/context independently (Step 6), and keep each activated expert's claim separable in the response (Step 10) — the same discipline the sixteen named patterns follow, just without a dedicated row.

## Step 5 — Gather Required Inputs

Gather inputs based on the routing pattern determined in Step 4. Do not gather the full input set for an expert that isn't activating.

**For the GAUSS Language Expert:**

- Code snippet or command name, when present
- Source language, for translation tasks
- Requested output type
- Available GAUSS evidence/retrieval context
- Known GAUSS version, if the task is version-sensitive

**For the Econometrics Expert:**

- Research or business question
- Outcome/dependent variable
- Explanatory variables
- Goal: causal, predictive, descriptive, diagnostic, forecasting
- Data structure
- Unit of observation
- Model/estimator under consideration
- Available output/code
- Sample definition/missing-data handling

**For the Software Engineering Expert:**

- User goal
- Code or workflow description, when code review/refactor is requested
- Target language/context, if implementation-specific advice is requested
- Change intent: review, refactor, testing, organization, error handling, or design guidance

**For the Documentation Expert:**

- User goal
- Intended reader or audience, if known
- Documentation type or requested artifact, if known (reference, usage guide, comments/docstrings, troubleshooting, README/help text, conceptual explanation)
- Source material to document, rewrite, explain, or improve

**For the Education Expert:**

- User goal
- Learner or audience, if known
- Learning topic
- Learning intent: lesson plan, curriculum, workshop, learning path, exercise, assessment, feedback, onboarding sequence, or remediation
- Time horizon or learning context, if relevant

**For the Product Expert:**

- User goal
- Target user or customer segment, if known
- Product idea, feature, workflow, or decision under consideration
- Product intent: problem framing, positioning, prioritization, scope, discovery, adoption, onboarding, or value proposition
- Known user problem or workflow context, if available

**When more than one expert activates:**

- Gather each activated expert's input set above, but do not block on every optional detail from any side.
- Ask a focused clarifying question only when missing information would materially change the answer, per `agents/code-assistant/task_modes.md`'s Clarifying Question Rules.
- Otherwise, state a clearly stated assumption for whichever side is underspecified (for example, "I'll assume your input is a numeric matrix" for the GAUSS side, "I'll assume this is a predictive, not causal, goal" for the econometrics side, "I'll assume behavior should be preserved unless you say otherwise" for the software-engineering side, "I'll assume this is for an experienced GAUSS user unless you tell me otherwise" for the documentation side, "I'll assume the learner has no prior GAUSS experience unless you tell me otherwise" for the education side, or "I'll assume a general, not-yet-specified user segment unless you tell me otherwise" for the product side).

## Step 6 — Determine Evidence and Context Needed

**For the GAUSS Language Expert**, use the Required Evidence by Task Type table in `experts/gauss-language/OPERATIONAL_PROFILE.md`. Baseline rules, restated here for quick reference but governed there:

- Exact syntax/defaults/returns require `source_authority: official_docs` or `official_package_docs` evidence.
- Category lists (`source_authority: category_list`) support discovery only.
- Curated notes (`source_authority: curated_command_note`) cannot override official docs.
- The retrieval-backed response pattern (`workflows/retrieval-backed-response-pattern.md`) governs how each evidence state (found, ambiguous, conflict, stale, etc.) shapes the response.
- Context needed: official GAUSS command evidence for exact syntax/signatures/returns/package status; GAUSS language rules and data-structure guidance.

**For the Econometrics Expert**, use the Required Evidence / Context by Task Type table in `experts/econometrics/OPERATIONAL_PROFILE.md`. Baseline rules, restated here but governed there:

- Methodological claims require adequate context for goal, data structure, outcome type, and main assumptions.
- Causal claims require identification/design support, not regression output alone.
- Forecasting claims require time ordering and a validation strategy.
- Interpretation requires model, variable, and output context.
- Command availability is never evidence of methodological appropriateness.
- Context needed: methodological context, data structure, outcome type, identification/assumption context, diagnostics/validation context.

**For the Software Engineering Expert**, use the Required Evidence / Context by Task Type table in `experts/software-engineering/OPERATIONAL_PROFILE.md`. Baseline rules, restated here but governed there:

- General design/maintainability guidance usually does not require official GAUSS command evidence or econometric context — the stated code/task context and goal are enough.
- If design guidance becomes a GAUSS-specific syntax claim (e.g., a recommended structure implies specific GAUSS constructs), route/escalate that claim to the GAUSS Language Expert rather than asserting it on this expert's own authority.
- If design guidance affects modeling interpretation (e.g., a workflow reorganization changes how a sample or estimator is applied), route/escalate that claim to the Econometrics Expert rather than asserting it on this expert's own authority.
- A claim that code was executed, tested, or run requires actual execution evidence; a recommended test is not a confirmed result.
- Context needed: code or workflow structure, user goal, change intent, behavior-preservation constraints, testing/validation expectations, maintainability constraints.

**For the Documentation Expert**, use the Required Evidence / Context by Task Type table in `experts/documentation/OPERATIONAL_PROFILE.md`. Baseline rules, restated here but governed there:

- The Documentation Expert usually does not need official command evidence for general wording, structure, or clarity work — the stated content, intended reader, and documentation type are enough.
- If documentation includes GAUSS syntax or examples, route/escalate that claim to the GAUSS Language Expert rather than asserting it on this expert's own authority.
- If documentation includes model assumptions or interpretation, route/escalate that claim to the Econometrics Expert rather than asserting it on this expert's own authority.
- If documentation includes design intent, comments/docstrings framed as proving maintainability, or refactoring rationale, route/escalate that claim to the Software Engineering Expert rather than asserting it on this expert's own authority.
- Documentation clarity is never evidence of correctness, validity, or maintainability.
- Context needed: source material to document or rewrite, intended reader/audience, documentation type, documentation intent, terminology/style conventions, verified syntax/evidence for any examples included, known prerequisites/caveats/warnings/assumptions.

**For the Education Expert**, use the Required Evidence / Context by Task Type table in `experts/education/OPERATIONAL_PROFILE.md`. Baseline rules, restated here but governed there:

- The Education Expert usually does not need official command evidence for general learning design, sequencing, practice, feedback, or assessment planning — the stated learner, learning goal, and time horizon are enough.
- If lessons include GAUSS syntax or examples, route/escalate that claim to the GAUSS Language Expert rather than asserting it on this expert's own authority.
- If lessons include statistical methodology, assumptions, diagnostics, or interpretation, route/escalate that claim to the Econometrics Expert rather than asserting it on this expert's own authority.
- If lessons include refactoring/design/testability judgments, route/escalate that claim to the Software Engineering Expert rather than asserting it on this expert's own authority.
- If lessons include documentation/reference quality claims, route/escalate that claim to the Documentation Expert rather than asserting it on this expert's own authority.
- If a lesson implies product value, adoption, positioning, or prioritization, route that claim to the Product Expert — never assert it on this expert's own authority.
- Education quality is never evidence of implementation correctness, statistical validity, maintainability/design quality, documentation quality, or product value.
- Context needed: learner or audience, learning goal, prior knowledge/prerequisites, learning context and time horizon, delivery format, desired learning outcomes, practice/assessment expectations, common misconceptions, tool/software context, whether examples should be GAUSS-specific or language-agnostic.

**For the Product Expert**, use the Required Evidence / Context by Task Type table in `experts/product/OPERATIONAL_PROFILE.md`. Baseline rules, restated here but governed there:

- The Product Expert usually does not need official command evidence for general product framing, positioning, discovery, or prioritization reasoning — the stated target user, problem, and workflow are enough.
- If product reasoning includes GAUSS syntax or examples, route/escalate that claim to the GAUSS Language Expert rather than asserting it on this expert's own authority.
- If product reasoning includes statistical methodology, assumptions, diagnostics, or interpretation, route/escalate that claim to the Econometrics Expert rather than asserting it on this expert's own authority.
- If product reasoning includes refactoring/design/testability or technical-debt judgments, route/escalate that claim to the Software Engineering Expert rather than asserting it on this expert's own authority.
- If product reasoning includes documentation/reference quality, route/escalate that claim to the Documentation Expert rather than asserting it on this expert's own authority.
- If product reasoning includes learning sequence, training, assessment, or pedagogy, route/escalate that claim to the Education Expert rather than asserting it on this expert's own authority.
- Market validation, product-market fit, adoption, willingness to pay, or prioritization certainty require actual user/customer evidence — never asserted from an internally plausible narrative alone.
- Product hypotheses must be labeled as hypotheses when evidence is missing.
- Product value is never evidence of implementation correctness, statistical validity, maintainability/design quality, documentation quality, or education quality.
- Context needed: target user or customer segment, user problem or job to be done, workflow context, product idea/feature/decision under consideration, product intent (problem framing, positioning, prioritization, scope, discovery, adoption, onboarding, or value proposition), customer evidence or feedback if available, success criteria, adoption or retention concerns, product assumptions and risks, competing priorities or constraints.

**When more than one expert's evidence/context requirement applies:**

- Each expert's evidence/context requirement is separate. Meeting one does not satisfy another, and satisfying none is not offset by high confidence on any single side.
- If any side is missing, preserve uncertainty for that side only — do not let a fully-satisfied requirement on one side imply another side is also settled.
- The strictest applicable requirement wins: if a task touches GAUSS syntax, econometric methodology, code quality, documentation clarity, learning design, and product value at once, the response must clear all six bars, not just the highest-confidence one.

## Step 7 — Route to Retrieval or Clarification

- Route to `workflows/command-documentation-retrieval.md` when GAUSS command evidence is missing, then use `workflows/retrieval-backed-response-pattern.md` to handle the resulting state (`found_complete`, `found_incomplete`, `not_found`, `ambiguous`, `conflict`, `stale`, or `error`). Do not answer exact GAUSS syntax, defaults, or return values from memory while this is pending.
- Ask the user for methodological context when goal, design, outcome type, or data structure is missing and materially affects the recommendation.
- Ask the user for design context (code/task, goal, behavior-preservation constraints) when it is missing and materially affects a refactor or maintainability recommendation.
- Ask the user for documentation context (intended reader, documentation type, source material) when it is missing and materially affects the resulting documentation.
- Ask the user for learning context (learner, prior knowledge, time horizon) when it is missing and materially affects the resulting learning design.
- Ask the user for product context (target user, problem, workflow, existing evidence) when it is missing and materially affects the resulting product recommendation.
- Do not ask unnecessary questions when a safe assumption is enough, on any side.
- In multi-expert cases, it is acceptable to provide guidance on one side with caveats for the others, as long as each missing side is stated explicitly rather than silently glossed over.

## Step 8 — Apply Expert Decision Rules

### GAUSS Language Expert rules

Apply the decision rules from `experts/gauss-language/OPERATIONAL_PROFILE.md`, summarized:

- No invented GAUSS syntax, packages, procedures, or APIs.
- Prefer official-doc-backed command evidence for exact syntax, defaults, and return values.
- Prefer verified native GAUSS procedures when appropriate; use manual implementations only in the allowed cases (teaching, customization, no suitable native command, transparent examples).
- Distinguish matrix, DataFrame, array, scalar, string, and structure usage.
- No execution claims without an actual execution.
- Preserve uncertainty when evidence is incomplete, stale, ambiguous, or conflicting.

### Econometrics Expert rules

Apply the decision rules from `experts/econometrics/OPERATIONAL_PROFILE.md`, summarized:

- Start with the user's goal (causal, predictive, descriptive, diagnostic, forecasting).
- Identify the data structure before recommending an estimator; match the estimator to outcome type, data structure, and target quantity.
- No causal claims without design/identification support.
- State assumptions and the consequences if they fail; recommend diagnostics/robustness checks appropriate to the method.
- Distinguish statistical from practical significance.
- Do not treat command availability as methodological validity.
- Do not invent GAUSS syntax while giving methodological advice.

### Software Engineering Expert rules

Apply the decision rules from `experts/software-engineering/OPERATIONAL_PROFILE.md`, summarized:

- Separate correctness, methodology, and maintainability claims in the response.
- Do not treat syntactically valid code as well-designed code.
- Do not treat clean code as statistically or causally valid.
- Prefer behavior-preserving refactors unless the user asks for a behavior change; make behavior changes explicit when a recommendation would introduce one.
- Recommend incremental changes for risky refactors rather than one large rewrite.
- Identify tests/checks needed before or after refactoring, proportional to risk.
- Label pseudocode or unverified syntax clearly whenever a structural example is not verified GAUSS.
- Defer GAUSS syntax to the GAUSS Language Expert and econometric/statistical validity to the Econometrics Expert — never invent GAUSS constructs or assert methodological soundness on this expert's own authority.
- Avoid premature optimization; prioritize high-risk design issues before style-only issues.
- Do not claim execution unless code was actually run by an available tool.

### Documentation Expert rules

Apply the decision rules from `experts/documentation/OPERATIONAL_PROFILE.md`, summarized:

- Identify the intended reader and documentation type before rewriting or creating documentation.
- Separate documentation clarity from implementation correctness, methodological/statistical correctness, and maintainability/design correctness.
- Do not treat well-written docs, clear explanation, or good comments as evidence that code is correct, a model is valid, or code is well-designed.
- Use verified syntax for examples, or label examples as pseudocode/unverified.
- Keep warnings and caveats close to the steps or claims they affect.
- Prefer task-oriented structure for "how do I" requests and reference structure for command/procedure documentation.
- Keep comments focused on intent, assumptions, and non-obvious decisions, not mechanics.
- Defer GAUSS syntax to the GAUSS Language Expert, econometric/statistical validity to the Econometrics Expert, and code design/refactoring validity to the Software Engineering Expert.
- Do not claim execution unless code was actually run by an available tool.
- Do not replace Education Expert or Product Expert work with documentation work.

### Education Expert rules

Apply the decision rules from `experts/education/OPERATIONAL_PROFILE.md`, summarized:

- Identify the learner and learning goal, and prior knowledge/prerequisites, before designing instruction.
- Separate learning design from implementation correctness, methodological/statistical correctness, maintainability/design correctness, documentation/reference correctness, and product strategy.
- Do not treat lesson quality as evidence that code is correct, methodology is valid, code is maintainable, documentation is clear, or a product decision is justified.
- Define measurable learning objectives; sequence concepts before practice; scaffold practice before open-ended tasks; align exercises with objectives.
- Include checks for understanding or feedback when appropriate; anticipate likely misconceptions; manage cognitive load.
- Use verified syntax for GAUSS examples, or label examples as pseudocode/unverified.
- Defer GAUSS syntax to the GAUSS Language Expert, econometric/statistical validity to the Econometrics Expert, code design/refactoring validity to the Software Engineering Expert, documentation/reference clarity to the Documentation Expert, and product strategy to the Product Expert.
- Do not claim execution unless code was actually run by an available tool.

### Product Expert rules

Apply the decision rules from `experts/product/OPERATIONAL_PROFILE.md`, summarized:

- Identify the target user or customer segment and the user problem before evaluating a feature idea.
- Identify the workflow where the feature or product decision fits.
- Separate product value from implementation correctness, methodological/statistical correctness, maintainability/design correctness, documentation/reference correctness, and education/learning-design correctness.
- Identify assumptions and evidence gaps; distinguish hypotheses from validated evidence.
- Consider first-use experience, activation, time-to-value, and adoption barriers.
- Frame tradeoffs explicitly when discussing prioritization; prefer small, testable scope when evidence is limited.
- Recommend discovery questions or validation steps when user evidence is missing.
- Avoid treating internal enthusiasm or a polished demo as customer proof.
- Defer GAUSS syntax to the GAUSS Language Expert, econometric/statistical validity to the Econometrics Expert, code design/refactoring validity to the Software Engineering Expert, documentation/reference clarity to the Documentation Expert, and learning-design quality to the Education Expert.
- Do not claim market proof, adoption certainty, or product-market fit without evidence.
- Do not claim execution unless code was actually run by an available tool.

### Coordination rules

- The GAUSS Language Expert owns implementation correctness.
- The Econometrics Expert owns methodological correctness.
- The Software Engineering Expert owns maintainability/design correctness.
- The Documentation Expert owns documentation/explanation correctness.
- The Education Expert owns learning-design correctness.
- The Product Expert owns product/user-value correctness.
- Command availability is not methodological validity.
- Clean structure is not statistical validity.
- Syntax validity is not maintainability.
- Clear documentation is not implementation correctness.
- Clear documentation is not statistical validity.
- Clear documentation is not maintainability.
- Good instruction is not implementation correctness.
- Good instruction is not statistical validity.
- Good instruction is not maintainability.
- Good instruction is not documentation quality.
- Good instruction is not product value.
- Product value is not implementation correctness.
- Product value is not statistical validity.
- Product value is not maintainability.
- Product value is not documentation quality.
- Product value is not education quality.
- User demand is not statistical validity.
- Product urgency is not acceptable design risk.
- Good documentation or training is not product validation.
- Product hypotheses must be labeled when evidence is missing.
- Education should not replace Documentation Expert/reference work.
- Education should not replace Product Expert/product strategy.
- Examples must use verified syntax or be labeled pseudocode/unverified.
- Testing recommendations are not execution claims.
- Pseudocode or unverified syntax must be labeled.
- All activated experts' claims must remain separable in substance, even when they do not need separate labeled sections in every response — this holds for two activated experts and continues to hold when three, four, five, or all six activate.
- If one expert's side is uncertain (missing evidence, missing context), do not let confidence on another side mask that uncertainty. A verified GAUSS command, a sound methodology, a clean refactor, clear documentation, a well-designed lesson, and a credible product recommendation are six independent claims, not one combined verification.

## Step 9 — Produce Internal Routing Output

Use the output contract, extended for six experts:

- `task_classification`
- `routing_pattern` — the matched pattern from Step 4's activation matrix (e.g. `gauss_only`, `product_only`, `gauss_and_product`, `all_six`, `neither`), or a description of the active expert subset when it doesn't match a named pattern
- `activated_experts`
- `activation_reason_by_expert`
- `non_activation_reason_by_expert`, when relevant
- `evidence_needed_by_expert`
- `context_needed_by_expert`
- `evidence_or_context_used`
- `implementation_recommendation`
- `methodology_recommendation`
- `maintainability_recommendation`
- `documentation_recommendation`
- `education_recommendation`
- `product_recommendation`
- `refactor_or_design_recommendations`
- `testing_or_validation_recommendations`
- `documentation_structure_recommendations`
- `example_or_usage_recommendations`
- `warning_or_caveat_recommendations`
- `learning_objectives`
- `sequencing_recommendations`
- `scaffolding_recommendations`
- `practice_or_assessment_recommendations`
- `feedback_or_remediation_recommendations`
- `target_user_or_segment`
- `user_problem`
- `workflow_context`
- `value_proposition`
- `product_assumptions`
- `evidence_gaps`
- `discovery_questions`
- `prioritization_or_scope_recommendations`
- `adoption_or_time_to_value_risks`
- `success_criteria`
- `conflicts_or_tensions`
- `response_constraints`
- `escalation_needed`

These fields remain internal by default. They do not need to appear as labels in the user-facing response — they are the internal structure the response should satisfy in substance, the same way a response satisfies `evaluations/scoring.md` dimensions without printing their names.

## Step 10 — Compose the User Response

The final response should:

- Answer the user naturally, without a forced expert-routing preamble.
- Show expert routing through correctness, evidence/context use, and uncertainty handling, not a literal "expert activated" label.
- Separate implementation, methodology, maintainability, documentation, education, and product claims when more than one matters, so none is misread as validating another.
- Cite or name GAUSS evidence when appropriate (a source file, a curated note, an official doc reference).
- State assumptions and caveats explicitly for methodology, design, documentation, education, and product claims, the same way GAUSS-side assumptions are stated.
- Include validation suggestions (for generated/translated/debugged GAUSS code), diagnostic suggestions (for methodological recommendations), testing/behavior-preservation notes (for refactor/design recommendations), structure/clarity suggestions (for documentation recommendations), sequencing/scaffolding/assessment suggestions (for learning-design recommendations), or discovery-question/validation-step suggestions (for product recommendations) when the task calls for one.
- Avoid overclaiming: never state or imply that GAUSS code was executed, that schema/structural validity is the same as semantic correctness, that a methodologically sound recommendation has been implementation-verified, that a well-organized refactor has been confirmed to preserve behavior without actually checking, that clear documentation confirms correctness/validity/maintainability, that a well-designed lesson confirms correctness/validity/maintainability/documentation quality/product value, or that a compelling product recommendation confirms correctness/validity/maintainability/documentation quality/education quality.

## Step 11 — Evaluate Routing

Manual evaluation should check:

- Correct routing pattern (per Step 4's activation matrix and coordination principles) for the task at hand.
- Correct expert activation, or correct non-activation, for each expert individually.
- Evidence threshold met for any exact GAUSS syntax/defaults/returns claim.
- Context threshold met for any methodological claim (goal, data structure, design support for causal claims, etc.).
- Context threshold met for any refactor/maintainability claim (behavior-preservation constraints, stated code/goal).
- Context threshold met for any documentation claim (intended reader, documentation type, source material).
- Context threshold met for any learning-design claim (learner, learning goal, time horizon).
- Context threshold met for any product claim (target user, problem, workflow, existing evidence).
- No invented GAUSS syntax, procedures, or APIs.
- No unsupported causal or statistical-validity claims.
- No claim that clean code implies statistical or causal validity, or that valid syntax implies good design.
- No claim that documentation clarity implies GAUSS syntax correctness, statistical validity, or maintainability.
- No claim that lesson/learning-design quality implies GAUSS syntax correctness, statistical validity, maintainability, documentation quality, or product value.
- No claim that product value or positioning implies GAUSS syntax correctness, statistical validity, maintainability, documentation quality, or education quality.
- No claim of market proof, adoption certainty, or product-market fit without user/customer evidence.
- No execution claims without actual execution.
- Uncertainty preserved on each activated side independently — one side being resolved does not paper over another being unresolved.
- No over-routing — the response does not apply GAUSS-specific, econometric, software-engineering, documentation, education, or product reasoning to a task from any expert's Non-Activation Cases list.
- Conflicts or tensions between activated experts' conclusions are surfaced when they exist, not silently resolved.
- Validation, diagnostic, testing/behavior-preservation, documentation-structure, learning-design, or product-discovery suggestions included where appropriate.

## Routing Examples

The first sixteen examples below predate the Education Expert (`v0.9.0`-`v0.15.0`). Examples 1-8 are kept as concise one-line references; 9-16 use the expanded format (request, activated experts, why, response rule, key boundary) introduced in `v0.15.0`. Examples 17-26 were added for `v0.16.0` to make the Education Expert's boundaries explicit. Examples 27-36 are new for `v0.17.0` and use the same expanded format to make the Product Expert's boundaries explicit.

1. **GAUSS-only.** "What does `strindx` return when not found?" → GAUSS Language Expert only.
2. **Econometrics-only.** "Does p=0.03 mean the model explains 3%?" → Econometrics Expert only.
3. **Software-engineering-only.** "How should I refactor this generic duplicated pseudocode?" → Software Engineering Expert only; no GAUSS syntax and no methodology claim involved.
4. **GAUSS + Econometrics.** "Translate `lm()` to GAUSS and interpret the causal claim." → GAUSS Language Expert handles the translation and evidence-backed syntax; Econometrics Expert handles the causal interpretation, kept as a separate contribution rather than blended into the code explanation.
5. **GAUSS + Software Engineering.** "Refactor this GAUSS code with repeated blocks." → GAUSS Language Expert confirms/verifies any GAUSS syntax used in the refactor; Software Engineering Expert owns the decomposition/refactor strategy; unverified structure is labeled as pseudocode.
6. **Econometrics + Software Engineering.** "Organize my regression workflow with diagnostics and reporting." → Econometrics Expert owns the diagnostics/reporting content; Software Engineering Expert owns the workflow decomposition and maintainability; no GAUSS-specific syntax required.
7. **GAUSS + Econometrics + Software Engineering.** "Write GAUSS logistic regression code, structure it cleanly, and explain if logistic is appropriate." → GAUSS Language Expert verifies GAUSS implementation facts; Econometrics Expert addresses binary-outcome model appropriateness; Software Engineering Expert addresses code organization/testability; claims stay separate.
8. **Neither.** "Write a short release-note blurb." → No expert activates — release tracking, even when the changelog entries describe GAUSS-related, econometrics-related, or code-quality-related work.

9. **Documentation-only.**
   - Request: "Rewrite this technical note into clearer user-facing documentation."
   - Activated experts: Documentation Expert only.
   - Why: the request is purely about clarity/structure with no GAUSS syntax, methodology, or design content.
   - Response rule: improve structure, clarity, assumptions, and reader guidance; do not invent technical details not present in the source note.
   - Key boundary: does not activate GAUSS, Econometrics, or Software Engineering.

10. **GAUSS + Documentation.**
    - Request: "Document this GAUSS procedure and include a usage example."
    - Activated experts: GAUSS Language Expert, Documentation Expert.
    - Why: the example needs verified GAUSS syntax; the explanation, structure, and parameter descriptions are a documentation concern.
    - Response rule: GAUSS Language Expert owns syntax/example validity; Documentation Expert owns explanation, structure, and usage clarity.
    - Key boundary: examples use verified syntax or are clearly labeled pseudocode; no command behavior is invented.

11. **Econometrics + Documentation.**
    - Request: "Document the assumptions and interpretation caveats for this regression output."
    - Activated experts: Econometrics Expert, Documentation Expert.
    - Why: the assumptions/interpretation content must be methodologically correct; the wording, structure, and placement of caveats is a documentation concern.
    - Response rule: Econometrics Expert owns assumption/interpretation correctness; Documentation Expert owns clarity, caveat placement, and reader-facing explanation.
    - Key boundary: does not overclaim causal validity from clearly worded caveats.

12. **Software Engineering + Documentation.**
    - Request: "Add comments/docstrings explaining the design intent of this helper function."
    - Activated experts: Software Engineering Expert, Documentation Expert.
    - Why: design intent is a maintainability judgment; comment/docstring wording and clarity is a documentation concern.
    - Response rule: Software Engineering Expert owns design intent/maintainability; Documentation Expert owns comment/docstring clarity — comments explain intent, not obvious mechanics.
    - Key boundary: does not claim tests were run.

13. **GAUSS + Software Engineering + Documentation.**
    - Request: "Refactor this GAUSS procedure and document its inputs/outputs."
    - Activated experts: GAUSS Language Expert, Software Engineering Expert, Documentation Expert.
    - Why: the refactor needs verified GAUSS syntax and behavior-preserving design reasoning; the resulting inputs/outputs need clear documentation.
    - Response rule: GAUSS Language Expert verifies syntax; Software Engineering Expert owns refactor strategy and behavior preservation; Documentation Expert owns the resulting explanation.
    - Key boundary: unverified structural suggestions are labeled as pseudocode; no test/execution claim is made.

14. **GAUSS + Econometrics + Documentation.**
    - Request: "Show GAUSS logistic regression syntax and document model assumptions for users."
    - Activated experts: GAUSS Language Expert, Econometrics Expert, Documentation Expert.
    - Why: the syntax needs verified GAUSS evidence; the assumptions need methodological correctness; the user-facing explanation needs documentation clarity.
    - Response rule: keep the implementation, methodology, and documentation contributions separately attributable rather than blended.
    - Key boundary: does not let a verified `glm` call imply the model itself is automatically appropriate.

15. **GAUSS + Econometrics + Software Engineering + Documentation.**
    - Request: "Write GAUSS logistic regression code, structure it cleanly, explain appropriateness, and document it for users."
    - Activated experts: GAUSS Language Expert, Econometrics Expert, Software Engineering Expert, Documentation Expert.
    - Why: implementation, methodology, maintainability, and documentation are all genuinely in play.
    - Response rule: keep all four claims separate and separately attributable, even within one coherent response; use local evidence (e.g. `glm.evidence.json`) for implementation facts.
    - Key boundary: does not claim execution; does not invent syntax; does not let clean code or clear documentation imply model validity.

16. **Documentation Expert does not replace Education Expert.**
    - Request: "Give beginners a six-week curriculum to learn econometrics in GAUSS."
    - Activated experts: Documentation Expert may support individual reference-doc clarity; Education Expert owns the curriculum itself as of `v0.16.0`.
    - Why: multi-session sequencing, scaffolding, and pedagogy are the Education Expert's territory, not the Documentation Expert's.
    - Response rule: the Education Expert designs the sequence, objectives, practice, and assessment; the Documentation Expert supports individual reference material within it but does not own the curriculum design itself.
    - Key boundary: does not let documentation guidance substitute for a learning design.

17. **Education-only.**
    - Request: "Create a three-part learning sequence for a generic technical concept."
    - Activated experts: Education Expert only.
    - Why: the request is purely about sequencing, scaffolding, and practice with no GAUSS syntax, methodology, design, or documentation content.
    - Response rule: define learner goal, prerequisites, sequence, practice, and checks for understanding; do not turn the result into a reference page only.
    - Key boundary: does not activate GAUSS, Econometrics, Software Engineering, or Documentation.

18. **GAUSS + Education.**
    - Request: "Teach beginners how to write a GAUSS procedure."
    - Activated experts: GAUSS Language Expert, Education Expert.
    - Why: any GAUSS example in the tutorial needs verified syntax; the teaching sequence, scaffolding, and practice design are a learning-design concern.
    - Response rule: GAUSS Language Expert owns syntax correctness; Education Expert owns learning sequence, scaffolding, practice, and checks for understanding.
    - Key boundary: uses verified syntax or labels pseudocode clearly; does not invent GAUSS syntax.

19. **Econometrics + Education.**
    - Request: "Build a learning plan for OLS assumptions and diagnostics."
    - Activated experts: Econometrics Expert, Education Expert.
    - Why: the assumptions/diagnostics content must be methodologically correct; the learning sequence, scaffolding, misconceptions, and assessment design are a learning-design concern.
    - Response rule: Econometrics Expert owns methodological correctness; Education Expert owns sequence, scaffolding, practice, misconceptions, and assessment.
    - Key boundary: does not overclaim causal validity; does not require the GAUSS Language Expert unless syntax is discussed.

20. **Documentation + Education.**
    - Request: "Is this reference page enough to teach beginners, or do I need exercises?"
    - Activated experts: Documentation Expert, Education Expert.
    - Why: the reference page's clarity is a documentation concern; whether it's sufficient for durable learning is a learning-design concern.
    - Response rule: Documentation Expert owns reference clarity; Education Expert explains why learning generally requires sequencing, practice, feedback, and scaffolding beyond a single reference page.
    - Key boundary: clearly distinguishes documentation from education rather than treating them as interchangeable.

21. **Software Engineering + Education.**
    - Request: "Turn refactoring principles into a practice exercise."
    - Activated experts: Software Engineering Expert, Education Expert.
    - Why: the code-quality/refactoring principles themselves are a maintainability concern; turning them into a practiced, assessed exercise is a learning-design concern.
    - Response rule: Software Engineering Expert owns the code-quality/refactoring principles; Education Expert owns exercise design, progression, feedback, and assessment.
    - Key boundary: does not claim tests were run; does not claim maintainability from lesson quality alone.

22. **GAUSS + Documentation + Education.**
    - Request: "Write a beginner GAUSS tutorial with a reference summary."
    - Activated experts: GAUSS Language Expert, Documentation Expert, Education Expert.
    - Why: the tutorial's GAUSS content needs verified syntax; the reference summary is a documentation concern; the tutorial's sequence and scaffolding are a learning-design concern.
    - Response rule: keep syntax verification, reference-summary structure, and tutorial sequencing separately attributable.
    - Key boundary: unverified examples are labeled pseudocode; the reference summary is not presented as a substitute for the tutorial's scaffolding, or vice versa.

23. **Econometrics + Documentation + Education.**
    - Request: "Create learner-facing documentation and exercises for regression interpretation."
    - Activated experts: Econometrics Expert, Documentation Expert, Education Expert.
    - Why: interpretation correctness is methodological; the documentation content is a documentation concern; the exercises and their sequencing are a learning-design concern.
    - Response rule: Econometrics Expert owns interpretation correctness; Documentation Expert owns the reference content; Education Expert owns the exercise sequence, practice, and assessment.
    - Key boundary: does not overclaim causal validity; does not let clear documentation or well-designed exercises substitute for methodological correctness.

24. **GAUSS + Econometrics + Documentation + Education.**
    - Request: "Teach logistic regression in GAUSS with assumptions, examples, and learner checks."
    - Activated experts: GAUSS Language Expert, Econometrics Expert, Documentation Expert, Education Expert.
    - Why: implementation, methodology, documentation, and learning design are all genuinely in play, with no maintainability/refactor request.
    - Response rule: keep the implementation, methodology, documentation, and education contributions separately attributable rather than blended.
    - Key boundary: does not let a verified `glm` call, a clear reference page, or a well-designed learner check imply the model itself is automatically appropriate.

25. **All five.**
    - Request: "Teach logistic regression in GAUSS, structure reusable code, document the workflow, and design practice exercises."
    - Activated experts: GAUSS Language Expert, Econometrics Expert, Software Engineering Expert, Documentation Expert, Education Expert.
    - Why: implementation, methodology, maintainability, documentation, and learning design are all genuinely in play.
    - Response rule: keep all five claims separate and separately attributable, even within one coherent response; use local evidence (e.g. `glm.evidence.json`) for implementation facts.
    - Key boundary: does not claim execution; does not invent syntax; does not let clean code, clear documentation, or a well-designed lesson imply model validity or vice versa.

26. **Neither.**
    - Request: "Write a nontechnical announcement."
    - Activated experts: none of the six.
    - Why: the request is general writing unrelated to GAUSS, econometrics, code quality, documentation, learning design, or product strategy.
    - Response rule: answer normally; do not impose expert routing or decision rules from any of the six.
    - Key boundary: negative routing holds even when the request superficially resembles a release note or announcement that other experts' domains sometimes touch.

27. **Product-only.**
    - Request: "Does this feature idea solve a real user problem?"
    - Activated experts: Product Expert only.
    - Why: the request is purely about problem framing and user value with no GAUSS syntax, methodology, design, documentation, or learning-design content.
    - Response rule: frame the target user, the underlying problem, the workflow it fits into, assumptions being made, and discovery questions or validation steps; do not treat the idea as validated without user evidence.
    - Key boundary: does not activate GAUSS, Econometrics, Software Engineering, Documentation, or Education.

28. **Product + Documentation.**
    - Request: "Turn this feature into positioning and a user-facing help section."
    - Activated experts: Product Expert, Documentation Expert.
    - Why: the value proposition and positioning are a product concern; the help section's clarity and structure are a documentation concern.
    - Response rule: Product Expert owns the value proposition, user problem, and positioning; Documentation Expert owns clarity, reference/usage structure, and examples in the help section.
    - Key boundary: keeps product claims separate from documentation quality — strong positioning does not itself make the help section accurate or complete, and vice versa.

29. **Product + Education.**
    - Request: "Can onboarding training reduce adoption friction for this feature?"
    - Activated experts: Product Expert, Education Expert.
    - Why: adoption-barrier and time-to-value reasoning is a product concern; the training's learning sequence and practice design is a learning-design concern.
    - Response rule: Product Expert owns adoption-barrier and time-to-value reasoning; Education Expert owns the learning sequence, practice, and onboarding learning flow.
    - Key boundary: does not claim training quality proves feature value; onboarding training can reduce friction without proving the feature is worth prioritizing.

30. **Product + GAUSS.**
    - Request: "Should we add this GAUSS feature, and is the proposed syntax valid?"
    - Activated experts: Product Expert, GAUSS Language Expert.
    - Why: whether the feature is worth adding is a product concern; whether the proposed syntax is valid is a GAUSS implementation concern.
    - Response rule: Product Expert owns user problem, workflow fit, and prioritization tradeoffs; GAUSS Language Expert owns the syntax/evidence boundary.
    - Key boundary: does not invent or approve GAUSS syntax without evidence, even when the product case for the feature is strong.

31. **Product + Econometrics.**
    - Request: "Would adding this analysis feature make users trust the results more?"
    - Activated experts: Product Expert, Econometrics Expert.
    - Why: user trust and adoption reasoning is a product concern; whether the analysis is statistically/methodologically valid is an econometrics concern.
    - Response rule: Product Expert owns user value, workflow, and adoption reasoning; Econometrics Expert owns whether the analysis is statistically/methodologically valid.
    - Key boundary: does not claim product usefulness proves statistical validity — users trusting a result more is not evidence the result is correct.

32. **Product + Software Engineering.**
    - Request: "Should we ship quickly or refactor first because technical debt may affect future product work?"
    - Activated experts: Product Expert, Software Engineering Expert.
    - Why: the timing/scope tradeoff is a product concern; the maintainability/design risk assessment is a software-engineering concern.
    - Response rule: Product Expert owns user value, timing, and scope tradeoff; Software Engineering Expert owns maintainability/design risk.
    - Key boundary: does not treat product urgency as proof that a design risk is acceptable — the Software Engineering Expert's own risk assessment still governs that claim.

33. **Documentation + Education + Product.**
    - Request: "Do we need docs, training, or product changes to help users adopt this workflow?"
    - Activated experts: Documentation Expert, Education Expert, Product Expert.
    - Why: reference clarity is a documentation concern; learning sequence and practice is a learning-design concern; adoption framing and tradeoffs are a product concern.
    - Response rule: Product Expert owns adoption framing and tradeoffs; Documentation Expert owns reference clarity; Education Expert owns learning sequence and practice; keep all three claims separately attributable.
    - Key boundary: does not let any one of the three substitute for another — good docs, good training, and a good product decision are three separate claims.

34. **GAUSS + Documentation + Education + Product.**
    - Request: "Design a beginner onboarding flow for a GAUSS feature with docs and product framing."
    - Activated experts: GAUSS Language Expert, Documentation Expert, Education Expert, Product Expert.
    - Why: the onboarding flow's GAUSS content needs verified syntax; the reference support is a documentation concern; the onboarding learning sequence is a learning-design concern; the onboarding-as-product-experience framing and adoption strategy is a product concern.
    - Response rule: keep syntax verification, reference support, onboarding sequence, and product/adoption framing separately attributable.
    - Key boundary: unverified examples are labeled pseudocode; product framing of onboarding does not substitute for the Education Expert's sequencing/scaffolding work, or vice versa.

35. **GAUSS + Econometrics + Product.**
    - Request: "Should we add a GAUSS econometric feature, and would it be methodologically appropriate?"
    - Activated experts: GAUSS Language Expert, Econometrics Expert, Product Expert.
    - Why: the syntax needs verified GAUSS evidence; the methodological appropriateness needs econometric reasoning; whether the feature is worth adding needs product framing.
    - Response rule: GAUSS Language Expert verifies syntax; Econometrics Expert owns methodological appropriateness; Product Expert owns user value and prioritization; claims stay separate.
    - Key boundary: does not let a verified command or a compelling product case imply the method itself is methodologically appropriate.

36. **All six.**
    - Request: "Design a GAUSS econometrics feature, structure implementation risks, document it, teach it, and frame product value."
    - Activated experts: GAUSS Language Expert, Econometrics Expert, Software Engineering Expert, Documentation Expert, Education Expert, Product Expert.
    - Why: implementation, methodology, maintainability, documentation, learning design, and product value are all genuinely in play.
    - Response rule: keep all six claims separate and separately attributable, even within one coherent response; use local evidence (e.g. `glm.evidence.json`) for implementation facts.
    - Key boundary: does not claim execution; does not invent syntax; does not let clean code, clear documentation, a well-designed lesson, or a compelling product recommendation imply any of the other five are automatically satisfied.

## Relationship to Existing Files

- **`tools/operational_expert_interface.md`** — defines the generic interface (activation triggers, evidence/context requirements, decision rules, output contract, evaluation criteria) that this workflow routes against for all six experts. This workflow does not redefine that interface's fields.
- **`experts/gauss-language/OPERATIONAL_PROFILE.md`** — the filled-in GAUSS Language Expert profile this workflow's GAUSS-side steps are sourced from. If the profile changes, this workflow's GAUSS-side content should be updated to match rather than allowed to drift.
- **`experts/econometrics/OPERATIONAL_PROFILE.md`** — the filled-in Econometrics Expert profile this workflow's econometrics-side steps are sourced from, following the same drift-prevention principle.
- **`experts/software-engineering/OPERATIONAL_PROFILE.md`** — the filled-in Software Engineering Expert profile this workflow's software-engineering-side steps are sourced from, following the same drift-prevention principle. Added in `v0.14.0`.
- **`experts/documentation/OPERATIONAL_PROFILE.md`** — the filled-in Documentation Expert profile this workflow's documentation-side steps are sourced from, following the same drift-prevention principle. Added in `v0.15.0`.
- **`experts/education/OPERATIONAL_PROFILE.md`** — the filled-in Education Expert profile this workflow's education-side steps are sourced from, following the same drift-prevention principle. Added in `v0.16.0`.
- **`experts/product/OPERATIONAL_PROFILE.md`** — the filled-in Product Expert profile this workflow's product-side steps are sourced from, following the same drift-prevention principle. Added in `v0.17.0`.
- **`workflows/code-assistant-response.md`** — this workflow is the specialization of that document's Step 2 ("Identify Relevant Experts"). Step 2 was updated in `v0.9.0` to reference two-expert routing, again in `v0.14.0` for three-expert/eight-pattern routing, again in `v0.15.0` for the Documentation Expert and four-axis routing, and again in `v0.16.0` to reference the Education Expert and the five-axis routing pattern. **It has not yet been updated for the Product Expert or six-axis routing** — that integration is a separate, planned `v0.17.0` follow-up task.
- **`workflows/retrieval-backed-response-pattern.md`** — governs Step 7's GAUSS-side evidence-state handling; this workflow does not redefine states A-H.
- **`workflows/command-documentation-retrieval.md`** — governs the hybrid discovery/retrieval strategy this workflow routes to in Step 7 for GAUSS command evidence.
- **`workflows/native-command-selection.md`** — governs the native-vs-manual decision this workflow's Step 8 GAUSS-side rules reference.
- **`agents/code-assistant/task_modes.md`** — the task-mode definitions consumed in Step 1 and the Clarifying Question Rules referenced in Step 5. Updated for multi-expert routing in `v0.9.0`, again in `v0.14.0` for the Software Engineering Expert, again in `v0.15.0` for the Documentation Expert, and again in `v0.16.0` for the Education Expert. **It has not yet been updated for the Product Expert** — that integration is a separate, planned `v0.17.0` follow-up task.
- **`prompts/code_assistant_system.md`** — the system prompt whose "Identify the relevant expertise" step this workflow operationalizes. Updated for multi-expert routing in `v0.9.0`, again in `v0.14.0` for the Software Engineering Expert, again in `v0.15.0` for the Documentation Expert, and again in `v0.16.0` for the Education Expert and the five-axis routing pattern. **It has not yet been updated for the Product Expert** — that integration is a separate, planned `v0.17.0` follow-up task.

## Maintenance Notes

- Update this workflow when any `OPERATIONAL_PROFILE.md` changes, or when a new operational expert is added (extending Step 2's trigger lists, Step 3's non-activation lists, and Step 4's activation matrix to cover it).
- Keep each expert's trigger/non-activation lists in this workflow aligned with its own `OPERATIONAL_PROFILE.md` — this workflow should mirror those profiles, never diverge from them.
- Benchmark category `16.x` (Multi-Expert Routing) tested GAUSS-only, econometrics-only, both-experts, and neither-expert routing, extending the single-expert coverage validated by `15.x` — completed and evaluated (all eight prompts passed) in `v0.9.0`.
- Benchmark category `21.x` (Software Engineering Expert Foundation) exercised the eight routing types that existed before that update, including the five combinations involving the Software Engineering Expert — completed and evaluated (all eight prompts passed) in `v0.14.0`.
- Benchmark category `22.x` (Documentation Expert Foundation) exercised the Documentation Expert and the documentation-related routing patterns — completed and evaluated (all eight prompts passed) in `v0.15.0`.
- Benchmark category `23.x` (Education Expert Foundation) exercised the Education Expert and the new education-related routing patterns documented here — completed and evaluated (all eight prompts passed at 4.0) in `v0.16.0`.
- Benchmark category `24.x` (Product Expert Foundation), planned in `planning/v0.17.0-product-expert-foundation.md`, is intended to exercise the Product Expert and the new product-related routing patterns documented here — not yet run as of this workflow update.
