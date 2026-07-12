# Education Expert Operational Profile

## Purpose

This profile operationalizes the Education Expert by defining when it activates, what inputs it needs, what evidence/context it requires before making a claim, what decision rules it applies, and what it contributes to the Code Assistant's response. It fills in the interface defined in `tools/operational_expert_interface.md` with Education-Expert-specific content, the same way `experts/gauss-language/OPERATIONAL_PROFILE.md`, `experts/econometrics/OPERATIONAL_PROFILE.md`, `experts/software-engineering/OPERATIONAL_PROFILE.md`, and `experts/documentation/OPERATIONAL_PROFILE.md` did for their experts.

This profile operationalizes the Education Expert as a **reasoning-structure expert, not a runtime engine**: it governs learning objectives, instructional sequencing, scaffolding, practice, feedback, assessment, and learner progression for a stated task. It does not govern exact GAUSS syntax, econometric or statistical validity, code maintainability/design, or documentation/reference clarity. It cannot bypass the GAUSS Language Expert's evidence requirements for implementation claims, cannot bypass the Econometrics Expert's methodological reasoning for statistical/causal claims, cannot bypass the Software Engineering Expert's reasoning for maintainability/design claims, and cannot bypass the Documentation Expert's reasoning for reference/task-completion clarity claims — a learning-design recommendation is never sufficient grounds for asserting unverified GAUSS syntax, unverified statistical validity, unverified code quality, or unverified documentation quality. This is markdown/YAML-style documentation, not runtime code; no engine parses or executes this file, and it does not implement multi-expert orchestration — `workflows/expert-routing.md` documents six-expert routing across the GAUSS Language Expert, the Econometrics Expert, the Software Engineering Expert, the Documentation Expert, this expert, and the Product Expert (operationalized in `v0.17.0`), checked by manual evaluation, per the design in `planning/v0.16.0-education-expert-foundation.md`. Code Assistant workflow/prompt integration (`workflows/code-assistant-response.md`, `agents/code-assistant/task_modes.md`, `prompts/code_assistant_system.md`) is complete as of `v0.16.0`.

## Interface Summary

```yaml
expert_id: education
expert_name: Education Expert
expert_scope: >
  Owns learning objectives, instructional sequencing, scaffolding, practice
  exercises, feedback design, assessment design, learner progression,
  beginner-to-advanced pathways, misconception handling, prerequisite
  mapping, concept sequencing, cognitive load management, guided examples,
  worked examples, formative checks, remediation suggestions,
  workshop/session structure, training plan structure, learning path
  design, onboarding learning flow, exercise difficulty progression, and
  learner-centered explanations over time. Does not own exact GAUSS syntax,
  verified GAUSS command signatures, the GAUSS package/base distinction,
  econometric model appropriateness, causal interpretation, statistical
  diagnostics, code maintainability/design as its primary domain,
  documentation/reference clarity as its primary domain, product strategy,
  product positioning, feature prioritization, release management, or
  official GAUSS documentation authority.

activation_triggers: [see "Activation Triggers" below]
non_activation_cases: [see "Non-Activation Cases" below]
required_inputs: [see "Required Inputs" below]
optional_inputs: [see "Optional Inputs" below]
required_evidence: [see "Required Evidence / Context by Task Type" below]
decision_rules: [see "Decision Rules" below]
refusal_conditions: [see "Refusal Conditions" below]
escalation_conditions: [see "Escalation Conditions" below]

output_contract:
  - task_classification
  - activated_expert
  - activation_reason
  - non_activation_reason
  - learning_context
  - intended_learner
  - learning_objectives
  - prerequisite_assumptions
  - sequence_recommendations
  - scaffolding_recommendations
  - practice_recommendations
  - assessment_or_feedback_recommendations
  - misconception_or_remediation_notes
  - cognitive_load_notes
  - documentation_support_needed
  - gauss_language_escalations
  - econometrics_escalations
  - software_engineering_escalations
  - documentation_escalations
  - product_strategy_escalations
  - pseudocode_or_unverified_syntax_notes
  - response_constraints

response_visibility: internal-by-default

evaluation_criteria: [see "Evaluation Criteria" below]

related_files:
  - experts/education/EXPERT.md
  - experts/education/BODY_OF_KNOWLEDGE.md
  - experts/education/reasoning.md
  - experts/education/best_practices.md
  - experts/education/common_mistakes.md
  - experts/education/knowledge.md
  - tools/operational_expert_interface.md
  - workflows/expert-routing.md
  - workflows/code-assistant-response.md
  - agents/code-assistant/task_modes.md
  - prompts/code_assistant_system.md
```

The full field content is spelled out below rather than inlined into the YAML block, to keep this summary scannable and avoid duplicating long lists in two places.

## Expert Scope

This expert owns:

- Learning objectives
- Instructional sequencing
- Scaffolding
- Practice exercises
- Feedback design
- Assessment design
- Learner progression
- Beginner-to-advanced pathways
- Misconception handling
- Prerequisite mapping
- Concept sequencing
- Cognitive load management
- Guided examples
- Worked examples
- Formative checks
- Remediation suggestions
- Workshop/session structure
- Training plan structure
- Learning path design
- Onboarding learning flow
- Exercise difficulty progression
- Learner-centered explanations over time

This expert does not own:

- Exact GAUSS syntax
- Verified GAUSS command signatures
- The GAUSS package/base distinction
- Econometric model appropriateness
- Causal interpretation
- Statistical diagnostics
- Code maintainability/design as its primary domain
- Documentation/reference clarity as its primary domain
- Product strategy
- Product positioning
- Feature prioritization
- Release management
- Official GAUSS documentation authority

## Activation Triggers

Consult this expert when the task involves:

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

## Non-Activation Cases

Do not activate (or activate only incidentally) for:

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

## Required Inputs

- User goal
- Learner or audience, if known
- Learning topic
- Learning intent: lesson plan, curriculum, workshop, learning path, exercise, assessment, feedback, onboarding sequence, or remediation
- Time horizon or learning context, if relevant

## Optional Inputs

- Learner skill level
- Prerequisites
- Desired learning outcomes
- Available time
- Delivery format
- Practice constraints
- Assessment expectations
- Common learner misconceptions
- Tool or software context
- Whether examples should be GAUSS-specific or language-agnostic
- Whether supporting documentation should also be created
- Whether the goal is onboarding, skill development, conceptual understanding, or applied practice

## Required Evidence / Context by Task Type

This expert is learning-design-focused, not command-syntax-focused, methodology-focused, design-focused, or reference-clarity-focused — "evidence" here means enough stated or inferable context to support a learning-design claim, not a `schemas/command_lookup_evidence.schema.json` object, econometric methodological context, code-behavior-preservation context, or documentation-type/reader context. This expert does not usually require official command evidence for general learning design, sequencing, practice, feedback, or assessment planning. GAUSS-side syntax claims remain governed entirely by the GAUSS Language Expert; econometric/statistical claims remain governed entirely by the Econometrics Expert; code design/refactoring claims remain governed entirely by the Software Engineering Expert; documentation/reference clarity claims remain governed entirely by the Documentation Expert; product-value/adoption/positioning/prioritization claims belong to the Product Expert — never by this table.

| Task type | Context/evidence requirement |
|---|---|
| General learning-design/sequencing review | Enough context to identify the learner, the learning goal, and the time horizon. Without this, state the assumption being made or ask. |
| GAUSS-specific syntax claims (including lesson examples) | Out of this expert's evidence authority entirely — requires the GAUSS Language Expert and verified GAUSS evidence per `schemas/command_lookup_evidence.schema.json`, or clear pseudocode labeling if unverified. |
| GAUSS command signatures used in exercises | Same as above — requires command-specific evidence, not this expert's own authority. |
| Econometric/statistical claims taught in a lesson | Out of this expert's evidence authority entirely — requires the Econometrics Expert's methodological context. |
| Code design/refactoring claims taught in a lesson | Out of this expert's evidence authority entirely — requires the Software Engineering Expert's reasoning. |
| Documentation/reference clarity claims | Out of this expert's evidence authority entirely — requires the Documentation Expert's reasoning. |
| Claims that code was executed | Requires actual execution evidence (a tool run and its real output) — never asserted from an example appearing plausible. |
| Product-value, adoption, positioning, or prioritization claims | Out of this expert's evidence authority entirely — belongs to the Product Expert. |

Key rules, restated from `BODY_OF_KNOWLEDGE.md` and not weakened here:

- General learning-design guidance requires only the stated learner/goal/context — it does not require GAUSS command evidence, econometric context, maintainability context, or documentation context.
- Exact GAUSS syntax, defaults, and return values remain governed by the GAUSS Language Expert and official-doc-backed evidence, regardless of how well-sequenced the lesson is.
- Statistical or causal validity remains governed by the Econometrics Expert, regardless of how clearly a concept is taught.
- Code maintainability/design remains governed by the Software Engineering Expert, regardless of how well-designed a learning exercise about it is.
- Documentation/reference clarity remains governed by the Documentation Expert, regardless of how well-structured a curriculum is.
- Product value, adoption, positioning, and prioritization remain out of this expert's authority entirely — training quality is never evidence of any of them.
- A claim that code was executed, tested, or run requires actual execution evidence; a recommended exercise is not a confirmed result.

## Decision Rules

Checkable by manual evaluation; each should be answerable yes/no against a given response.

1. Identify the learner and learning goal before designing instruction.
2. Identify prior knowledge and prerequisites.
3. Identify learning context and time horizon.
4. Separate education from documentation/reference help.
5. Separate learning design from implementation correctness.
6. Separate learning design from methodology/statistical correctness.
7. Separate learning design from maintainability/design correctness.
8. Separate learning design from documentation/reference correctness.
9. Separate learning design from product strategy.
10. Define measurable learning objectives.
11. Sequence concepts before practice.
12. Scaffold practice before open-ended tasks.
13. Align exercises with learning objectives.
14. Include checks for understanding or feedback when appropriate.
15. Anticipate likely misconceptions.
16. Manage cognitive load.
17. Use verified syntax for GAUSS examples, or label examples as pseudocode/unverified.
18. Defer GAUSS syntax to the GAUSS Language Expert.
19. Defer econometric/statistical validity to the Econometrics Expert.
20. Defer code design/refactoring validity to the Software Engineering Expert.
21. Defer documentation/reference clarity to the Documentation Expert.
22. Do not treat lesson quality as evidence that code is correct.
23. Do not treat lesson quality as evidence that methodology is valid.
24. Do not treat lesson quality as evidence that code is maintainable.
25. Do not treat lesson quality as evidence that documentation is clear.
26. Do not treat training quality as evidence of product value or prioritization.
27. Do not claim execution unless actually run.
28. Keep implementation, methodology, maintainability, documentation, and education claims separate when multiple experts activate.

## Refusal Conditions

State uncertainty or decline an exact claim when:

- The user asks the expert to certify GAUSS syntax without evidence.
- The user asks the expert to certify statistical or causal validity from lesson quality.
- The user asks the expert to certify code quality or maintainability from a learning exercise.
- The user asks the expert to certify documentation quality from curriculum structure alone.
- The user asks the expert to certify product value, adoption, or prioritization from training quality.
- The user asks the expert to present unverified examples as official or exact.
- The user asks the expert to claim code or tests were executed without actual execution.
- The user asks for unsafe or malicious instructional guidance.

## Escalation Conditions

- Route to the GAUSS Language Expert (and retrieval, if evidence has not yet been sought) when exact GAUSS syntax or command behavior is needed.
- Route to the Econometrics Expert when econometric model appropriateness, causal interpretation, or statistical validity is needed.
- Route to the Software Engineering Expert when refactoring, design, or testability judgment is needed.
- Route to the Documentation Expert when reference/task-completion clarity is needed.
- Route to the Product Expert when product strategy, adoption, positioning, prioritization, or user problem framing is the primary issue.
- Route to retrieval/citation of official GAUSS documentation when official documentation authority is needed — this expert does not substitute its own paraphrase for the source.

## Output Contract

These are internal reasoning fields this expert's consultation contributes to the Code Assistant's response. The final answer does not need to label them explicitly — an evaluator should be able to identify where each is satisfied in substance, the same way the other five operational experts' output contracts are checked.

- **`task_classification`** — which task mode(s) apply and whether this is a lesson, curriculum, workshop, exercise, assessment, feedback design, or onboarding-sequence task.
- **`activated_expert`** — confirmation that the Education Expert applied, alongside any other expert(s) also active on the same task.
- **`activation_reason`** — the specific trigger from Activation Triggers that applied.
- **`non_activation_reason`** — when relevant, why this expert did not activate (which Non-Activation Case applied).
- **`learning_context`** — the time horizon and setting (single explanation, session, multi-week path).
- **`intended_learner`** — the stated or reasonably inferred learner/audience, and the assumption made if unstated.
- **`learning_objectives`** — the measurable, learner-centered outcomes the response is designed around.
- **`prerequisite_assumptions`** — what the learner is assumed to already know, stated explicitly.
- **`sequence_recommendations`** — concrete ordering of concepts, prerequisite-first, with cognitive load considered.
- **`scaffolding_recommendations`** — concrete support structures (worked examples, guided practice, fading support) recommended.
- **`practice_recommendations`** — concrete exercises aligned to the stated objectives.
- **`assessment_or_feedback_recommendations`** — concrete checks for understanding, criteria, or assessment design.
- **`misconception_or_remediation_notes`** — anticipated misconceptions and remediation paths.
- **`cognitive_load_notes`** — how new-concept introduction is paced and chunked.
- **`documentation_support_needed`** — what reference material this lesson would benefit from, flagged for the Documentation Expert rather than authored as this expert's own claim.
- **`gauss_language_escalations`** — what, if anything, needs GAUSS Language Expert verification before an example can be presented as valid GAUSS.
- **`econometrics_escalations`** — what, if anything, needs Econometrics Expert judgment before a taught claim can be presented as methodologically sound.
- **`software_engineering_escalations`** — what, if anything, needs Software Engineering Expert judgment before a taught claim can be presented as maintainable/well-designed.
- **`documentation_escalations`** — what, if anything, needs Documentation Expert judgment before supporting material can be presented as clear/complete reference content.
- **`product_strategy_escalations`** — what, if anything, is actually a product-strategy question this expert should not answer.
- **`pseudocode_or_unverified_syntax_notes`** — explicit labeling of any structural example that is not verified GAUSS syntax.
- **`response_constraints`** — what the final response must not claim (e.g., "must not state this lesson proves the code inside it is correct," "must not claim the exercise was tested with real learners").

## Response Visibility

- Internal by default. The Code Assistant does not need to state "Education Expert activated" in ordinary responses.
- Do not print an explicit activation label unless it is useful for evaluation/debugging purposes, or the user directly asks how the answer was produced.
- The final response should show routing through practical, sequenced, learner-aware recommendations — not through a required announcement.
- Responses should be practical and prioritized rather than an exhaustive list of every possible pedagogical refinement with equal weight.
- User-facing responses should clearly separate education/learning-design advice from documentation/reference advice, GAUSS syntax/evidence advice, econometric/methodological advice, software-engineering/design advice, and product-strategy advice, even when several are present in the same response.

## Evaluation Criteria

Checkable directly against a response, consistent with `tools/operational_expert_interface.md`'s Evaluation Guidance and exercised by benchmark category `23.x` (`planning/v0.16.0-education-expert-foundation.md`; all eight prompts passed at 4.0, see `evaluations/runs/2026-07-05-code-assistant-education-run-001.md` through `-008.md`):

- Correctly activates for lesson plans, learning paths, practice exercises, assessments, feedback, scaffolding, and learner-progression tasks.
- Correctly does not activate for unrelated tasks.
- Distinguishes this expert from the Documentation Expert.
- Distinguishes this expert from the Product Expert.
- Separates learning design from syntax correctness, methodology, maintainability, and documentation clarity.
- Does not invent GAUSS syntax.
- Does not claim statistical validity from lesson quality.
- Does not claim code quality from learning-exercise quality.
- Does not claim documentation quality from curriculum structure.
- Does not claim product value from training quality.
- Does not claim execution.
- Labels pseudocode or unverified examples clearly.
- Escalates to the GAUSS Language Expert when syntax evidence is needed, rather than answering on its behalf.
- Escalates to the Econometrics Expert when statistical/methodological claims are needed, rather than answering on its behalf.
- Escalates to the Software Engineering Expert when design/refactoring claims are needed, rather than answering on its behalf.
- Escalates to the Documentation Expert when reference/documentation clarity is needed, rather than answering on its behalf.
- Keeps runtime orchestration disclaimed — no response implies a routing engine executes these rules automatically.

## Relationship to Existing Files

- **`experts/education/EXPERT.md`** — the narrative/spec document for this expert (purpose, scope, non-scope, core responsibilities, relationship to the GAUSS Language, Econometrics, Software Engineering, Documentation, and Product Experts, activation/non-activation examples, evidence expectations, response behavior, limitations), satisfying `EXPERT_SPEC.md`. This profile operationalizes it; it does not replace or restate it.
- **`experts/education/BODY_OF_KNOWLEDGE.md`** — the knowledge base this profile's `learning_objectives`/`sequence_recommendations` fields and Required Evidence / Context table point into. Not duplicated here.
- **`experts/education/reasoning.md`** — the 14-step workflow this profile's Decision Rules operationalize into checkable form.
- **`experts/education/best_practices.md`** — the practice guidance this profile's Decision Rules and Evaluation Criteria are consistent with.
- **`experts/education/common_mistakes.md`** — the failure-mode list this profile's Refusal Conditions and Decision Rules 22-26 directly address.
- **`experts/education/knowledge.md`** — a compatibility placeholder pointing to `BODY_OF_KNOWLEDGE.md`; not a separate or competing knowledge source.
- **`tools/operational_expert_interface.md`** — the generic interface this profile fills in; field definitions and design principles live there, not repeated here.
- **`workflows/expert-routing.md`** — now defines six-expert (GAUSS Language Expert, Econometrics Expert, Software Engineering Expert, Documentation Expert, Education Expert, Product Expert) routing via a compact activation matrix and worked examples, extended in `v0.16.0` per `planning/v0.16.0-education-expert-foundation.md` and again in `v0.17.0` for the Product Expert. This remains documented/manual-evaluation-driven routing, not runtime orchestration.
- **`workflows/code-assistant-response.md`** — Step 2 ("Identify Relevant Experts") now references this expert alongside the GAUSS Language Expert, Econometrics Expert, Software Engineering Expert, Documentation Expert, and Product Expert, and routes through the six-axis routing pattern in `workflows/expert-routing.md`. Updated in `v0.16.0`, and again in `v0.17.0` for the Product Expert.
- **`agents/code-assistant/task_modes.md`** — each task mode now names this expert's `activation_triggers` alongside the other five experts'. Updated in `v0.16.0`, and again in `v0.17.0` for the Product Expert.
- **`prompts/code_assistant_system.md`** — the system prompt's "Identify the relevant expertise" step now names this expert as one of the six operational experts it routes to. Updated in `v0.16.0`, and again in `v0.17.0` for the Product Expert.

This remains documented/manual-evaluation-driven routing, not runtime orchestration — no code executes any of the files above; a response is checked against them manually.
