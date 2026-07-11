# Product Expert Operational Profile

## Purpose

This profile operationalizes the Product Expert by defining when it activates, what inputs it needs, what evidence/context it requires before making a claim, what decision rules it applies, and what it contributes to the Code Assistant's response. It fills in the interface defined in `tools/operational_expert_interface.md` with Product-Expert-specific content, the same way `experts/gauss-language/OPERATIONAL_PROFILE.md`, `experts/econometrics/OPERATIONAL_PROFILE.md`, `experts/software-engineering/OPERATIONAL_PROFILE.md`, `experts/documentation/OPERATIONAL_PROFILE.md`, and `experts/education/OPERATIONAL_PROFILE.md` did for their experts.

This profile operationalizes the Product Expert as a **reasoning-structure expert, not a runtime engine**: it governs user problem framing, workflow fit, adoption, value proposition, positioning, prioritization, scope tradeoffs, and product risk reasoning for a stated task. It does not govern exact GAUSS syntax, econometric or statistical validity, code maintainability/design, documentation/reference clarity, or learning-design correctness. It cannot bypass the GAUSS Language Expert's evidence requirements for implementation claims, cannot bypass the Econometrics Expert's methodological reasoning for statistical/causal claims, cannot bypass the Software Engineering Expert's reasoning for maintainability/design claims, cannot bypass the Documentation Expert's reasoning for reference/task-completion clarity claims, and cannot bypass the Education Expert's reasoning for learning-design claims — a product recommendation is never sufficient grounds for asserting unverified GAUSS syntax, unverified statistical validity, unverified code quality, unverified documentation quality, or unverified learning-design quality. This is markdown/YAML-style documentation, not runtime code; no engine parses or executes this file, and it does not implement multi-expert orchestration — `workflows/expert-routing.md` documents six-expert routing across the GAUSS Language Expert, the Econometrics Expert, the Software Engineering Expert, the Documentation Expert, the Education Expert, and this expert, checked by manual evaluation, per the design in `planning/v0.17.0-product-expert-foundation.md`. This is documented/manual-evaluation-driven routing, not runtime orchestration. Code Assistant workflow/prompt integration (`workflows/code-assistant-response.md`, `agents/code-assistant/task_modes.md`, `prompts/code_assistant_system.md`) has not yet been done for this expert — that remains a separate, planned follow-up task.

## Interface Summary

```yaml
expert_id: product
expert_name: Product Expert
expert_scope: >
  Owns user problem framing, customer/job-to-be-done framing, workflow fit,
  user journey, first-use experience, activation and time-to-value, adoption
  barriers, value proposition, positioning, product requirements framing,
  prioritization tradeoffs, scope tradeoffs, feature usefulness, customer
  segment fit, persona/use-case alignment, user success criteria, product
  assumptions, product risk identification, feedback loop design, product
  discovery questions, MVP/scope reasoning, adoption and retention
  considerations, and go-to-market handoff considerations at a high level.
  Does not own exact GAUSS syntax, verified GAUSS command signatures, the
  GAUSS package/base distinction, econometric model appropriateness, causal
  interpretation, statistical diagnostics, code maintainability/design as
  its primary domain, documentation/reference clarity as its primary
  domain, learning-design correctness as its primary domain, instructional
  sequencing, release management, official GAUSS documentation authority,
  guaranteed market outcomes, or pricing/legal/security decisions as final
  authority.

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
  - target_user_or_segment
  - user_problem
  - job_to_be_done
  - workflow_context
  - product_goal
  - value_proposition
  - product_assumptions
  - evidence_gaps
  - discovery_questions
  - prioritization_or_scope_recommendations
  - adoption_or_time_to_value_risks
  - success_criteria
  - product_risk_notes
  - gauss_language_escalations
  - econometrics_escalations
  - software_engineering_escalations
  - documentation_escalations
  - education_escalations
  - market_evidence_notes
  - hypothesis_vs_evidence_notes
  - response_constraints

response_visibility: internal-by-default

evaluation_criteria: [see "Evaluation Criteria" below]

related_files:
  - experts/product/EXPERT.md
  - experts/product/BODY_OF_KNOWLEDGE.md
  - experts/product/reasoning.md
  - experts/product/best_practices.md
  - experts/product/common_mistakes.md
  - experts/product/knowledge.md
  - tools/operational_expert_interface.md
  - workflows/expert-routing.md
  - workflows/code-assistant-response.md
  - agents/code-assistant/task_modes.md
  - prompts/code_assistant_system.md
```

The full field content is spelled out below rather than inlined into the YAML block, to keep this summary scannable and avoid duplicating long lists in two places.

## Expert Scope

This expert owns:

- User problem framing
- Customer/job-to-be-done framing
- Workflow fit
- User journey
- First-use experience
- Activation and time-to-value
- Adoption barriers
- Value proposition
- Positioning
- Product requirements framing
- Prioritization tradeoffs
- Scope tradeoffs
- Feature usefulness
- Customer segment fit
- Persona/use-case alignment
- User success criteria
- Product assumptions
- Product risk identification
- Feedback loop design
- Product discovery questions
- MVP/scope reasoning
- Adoption and retention considerations
- Go-to-market handoff considerations, at a high level

This expert does not own:

- Exact GAUSS syntax
- Verified GAUSS command signatures
- The GAUSS package/base distinction
- Econometric model appropriateness
- Causal interpretation
- Statistical diagnostics
- Code maintainability/design as its primary domain
- Documentation/reference clarity as its primary domain
- Learning-design correctness as its primary domain
- Instructional sequencing
- Release management
- Official GAUSS documentation authority
- Guaranteed market outcomes
- Pricing/legal/security decisions as final authority

## Activation Triggers

Consult this expert when the task involves:

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

## Non-Activation Cases

Do not activate (or activate only incidentally) for:

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

## Required Inputs

- User goal
- Target user or customer segment, if known
- Product idea, feature, workflow, or product decision under consideration
- Product intent: problem framing, positioning, prioritization, scope, discovery, adoption, onboarding, value proposition, or requirements
- Known user problem or workflow context, if available

## Optional Inputs

- Customer evidence or feedback
- User segment/persona
- Job to be done
- Current workflow
- Adoption or retention concern
- Success criteria
- Business or product constraints
- Technical constraints
- Scope constraints
- Timeline or release context
- Documentation or education support needs
- Known assumptions
- Known risks
- Competing priorities
- Desired product artifact, such as a problem statement, PRD outline, positioning statement, prioritization rationale, discovery questions, or MVP scope

## Required Evidence / Context by Task Type

This expert is product-reasoning-focused, not command-syntax-focused, methodology-focused, design-focused, reference-clarity-focused, or learning-design-focused — "evidence" here means enough stated or inferable context to support a product-reasoning claim, not a `schemas/command_lookup_evidence.schema.json` object, econometric methodological context, code-behavior-preservation context, documentation-type/reader context, or learner/time-horizon context. This expert does not usually require official command evidence for general product framing, positioning, discovery, or prioritization reasoning.

| Task type | Context/evidence requirement |
|---|---|
| General product framing, positioning, discovery, or prioritization reasoning | Enough context to identify the target user, the problem, and the workflow. Without this, state the assumption being made or ask. |
| GAUSS-specific syntax claims (including features or examples that imply specific GAUSS behavior) | Out of this expert's evidence authority entirely — requires the GAUSS Language Expert and verified GAUSS evidence per `schemas/command_lookup_evidence.schema.json`, or clear labeling of the claim as unverified. |
| Econometric/statistical claims (e.g., "this analysis feature would be more credible") | Out of this expert's evidence authority entirely — requires the Econometrics Expert's methodological context. |
| Code design/refactoring/technical-debt claims used as product-risk input | Out of this expert's evidence authority entirely — requires the Software Engineering Expert's reasoning; this expert may treat design risk as a named input to a tradeoff but must not certify it. |
| Documentation/reference clarity claims | Out of this expert's evidence authority entirely — requires the Documentation Expert's reasoning. |
| Learning-design/onboarding-training claims | Out of this expert's evidence authority entirely — requires the Education Expert's reasoning. |
| Claims that code or tests were executed | Requires actual execution evidence (a tool run and its real output) — never asserted from a plausible-sounding feature description. |
| Market validation, product-market fit, adoption, willingness to pay, or prioritization certainty | Requires actual user/customer evidence (usage data, direct user feedback, a completed validation step) — never asserted from an internally plausible narrative alone. |

Key rules, restated from `BODY_OF_KNOWLEDGE.md` and not weakened here:

- General product-framing guidance requires only the stated user/problem/workflow — it does not require GAUSS command evidence, econometric context, maintainability context, documentation context, or learning-design context.
- Exact GAUSS syntax, defaults, and return values remain governed by the GAUSS Language Expert and official-doc-backed evidence, regardless of how compelling the product story around them is.
- Statistical or causal validity remains governed by the Econometrics Expert, regardless of how much users want the feature.
- Code maintainability/design remains governed by the Software Engineering Expert, regardless of how urgent the product timeline is.
- Documentation/reference clarity remains governed by the Documentation Expert, regardless of how strong the positioning is.
- Learning-design/onboarding quality remains governed by the Education Expert, regardless of how important onboarding is framed to be for adoption.
- Product hypotheses must be labeled as hypotheses when evidence is missing — a plausible narrative is not validated demand.
- Product value is not evidence of implementation correctness, statistical validity, maintainability/design quality, documentation quality, or education quality; each remains an independent claim.
- A claim that code was executed, tested, or run requires actual execution evidence; a recommended feature is not a confirmed result.

## Decision Rules

Checkable by manual evaluation; each should be answerable yes/no against a given response.

1. Identify the target user or customer segment before making product recommendations.
2. Identify the user problem before evaluating the feature idea.
3. Identify the workflow where the feature or product decision fits.
4. Separate product value from implementation correctness.
5. Separate product value from methodology/statistical correctness.
6. Separate product value from maintainability/design correctness.
7. Separate product value from documentation/reference correctness.
8. Separate product value from education/learning-design correctness.
9. Identify assumptions and evidence gaps.
10. Distinguish hypotheses from validated evidence.
11. Consider first-use experience, activation, and time-to-value.
12. Consider adoption barriers and support burden.
13. Frame tradeoffs explicitly when discussing prioritization.
14. Prefer small, testable scope when evidence is limited.
15. Recommend discovery questions or validation steps when user evidence is missing.
16. Avoid treating internal enthusiasm as customer proof.
17. Avoid treating a polished demo as product validation.
18. Avoid treating good documentation or training as proof of product value.
19. Defer GAUSS syntax to the GAUSS Language Expert.
20. Defer econometric/statistical validity to the Econometrics Expert.
21. Defer code design/refactoring validity to the Software Engineering Expert.
22. Defer documentation/reference clarity to the Documentation Expert.
23. Defer learning-design quality to the Education Expert.
24. Do not treat product usefulness as evidence that code is correct.
25. Do not treat product usefulness as evidence that methodology is valid.
26. Do not treat product urgency as evidence that design risk is acceptable.
27. Do not treat user demand as evidence of statistical validity.
28. Do not claim market proof, adoption certainty, or product-market fit without evidence.
29. Do not claim execution unless actually run.
30. Keep implementation, methodology, maintainability, documentation, education, and product claims separate when multiple experts activate.

## Refusal Conditions

State uncertainty or decline an exact claim when:

- The user asks the expert to certify GAUSS syntax without evidence.
- The user asks the expert to certify statistical or causal validity from user demand or product usefulness.
- The user asks the expert to certify code quality or maintainability from product urgency.
- The user asks the expert to certify documentation quality from positioning quality.
- The user asks the expert to certify education quality from onboarding importance.
- The user asks the expert to present product hypotheses as validated facts without evidence.
- The user asks the expert to guarantee market outcomes, adoption, retention, or product-market fit.
- The user asks the expert to claim code or tests were executed without actual execution.
- The user asks for unsafe, deceptive, or manipulative product guidance.

## Escalation Conditions

- Route to the GAUSS Language Expert (and retrieval, if evidence has not yet been sought) when exact GAUSS syntax or command behavior is needed.
- Route to the Econometrics Expert when econometric model appropriateness, causal interpretation, or statistical validity is needed.
- Route to the Software Engineering Expert when refactoring, design, or testability judgment is needed.
- Route to the Documentation Expert when reference/task-completion clarity is needed.
- Route to the Education Expert when learning sequence, training, assessment, or pedagogy is needed.
- Route to retrieval/citation of official GAUSS documentation when official documentation authority is needed — this expert does not substitute its own paraphrase for the source.
- Route pricing, legal, and security decisions to external or domain-specific review — this expert is not the final authority on any of them, though it may flag them as relevant considerations.

## Output Contract

These are internal reasoning fields this expert's consultation contributes to the Code Assistant's response. The final answer does not need to label them explicitly — an evaluator should be able to identify where each is satisfied in substance, the same way the other five operational experts' output contracts are checked.

- **`task_classification`** — which task mode(s) apply and whether this is a problem-framing, positioning, prioritization, scope, discovery, adoption, onboarding-strategy, or requirements task.
- **`activated_expert`** — confirmation that the Product Expert applied, alongside any other expert(s) also active on the same task.
- **`activation_reason`** — the specific trigger from Activation Triggers that applied.
- **`non_activation_reason`** — when relevant, why this expert did not activate (which Non-Activation Case applied).
- **`target_user_or_segment`** — the stated or reasonably inferred user/customer segment, and the assumption made if unstated.
- **`user_problem`** — the underlying problem, distinguished from any proposed feature or solution.
- **`job_to_be_done`** — the outcome the user is actually trying to accomplish.
- **`workflow_context`** — where this fits in the user's actual process, including what comes before and after.
- **`product_goal`** — what this response is trying to accomplish (positioning, prioritization, scope decision, discovery plan, etc.).
- **`value_proposition`** — who it's for, what problem it solves, and what outcome it enables, kept specific and defensible.
- **`product_assumptions`** — assumptions about the user, workflow, value, adoption, or feasibility, stated explicitly.
- **`evidence_gaps`** — where a claim rests on assumption rather than user/customer evidence.
- **`discovery_questions`** — concrete next validation steps proposed when evidence is missing.
- **`prioritization_or_scope_recommendations`** — the tradeoff criteria used and the resulting recommendation.
- **`adoption_or_time_to_value_risks`** — activation-path friction, setup burden, and early failure modes.
- **`success_criteria`** — how it would be known whether this worked, stated concretely.
- **`product_risk_notes`** — risks identified, including technical-debt or design risk treated as a product-risk input (not a maintainability certification).
- **`gauss_language_escalations`** — what, if anything, needs GAUSS Language Expert verification before a claim can be presented as valid GAUSS.
- **`econometrics_escalations`** — what, if anything, needs Econometrics Expert judgment before a claim can be presented as methodologically sound.
- **`software_engineering_escalations`** — what, if anything, needs Software Engineering Expert judgment before a claim can be presented as maintainable/well-designed.
- **`documentation_escalations`** — what, if anything, needs Documentation Expert judgment before supporting material can be presented as clear/complete reference content.
- **`education_escalations`** — what, if anything, needs Education Expert judgment before onboarding/training content can be presented as well-sequenced.
- **`market_evidence_notes`** — what actual user/customer evidence exists, if any, versus what is assumed.
- **`hypothesis_vs_evidence_notes`** — explicit labeling of which claims are hypotheses and which are evidence-backed.
- **`response_constraints`** — what the final response must not claim (e.g., "must not state this feature is validated without evidence," "must not claim positioning eliminates the need for documentation").

## Response Visibility

- Internal by default. The Code Assistant does not need to state "Product Expert activated" in ordinary responses.
- Do not print an explicit activation label unless it is useful for evaluation/debugging purposes, or the user directly asks how the answer was produced.
- The final response should show routing through practical, assumption-aware, evidence-honest product recommendations — not through a required announcement.
- Responses should be practical and prioritized rather than an exhaustive list of every possible product consideration with equal weight.
- User-facing responses should clearly separate product/user-value advice from GAUSS syntax/evidence advice, econometric/methodological advice, software-engineering/design advice, documentation/reference advice, and education/learning-design advice, even when several are present in the same response.

## Evaluation Criteria

Checkable directly against a response, consistent with `tools/operational_expert_interface.md`'s Evaluation Guidance and reusable for a future benchmark category (planned as `24.x` in `planning/v0.17.0-product-expert-foundation.md`):

- Correctly activates for product strategy, positioning, user problem framing, workflow fit, adoption, prioritization, scope, discovery, value proposition, and product risk tasks.
- Correctly does not activate for unrelated tasks.
- Distinguishes this expert from the Education Expert and the Documentation Expert.
- Separates product value from syntax correctness, methodology, maintainability, documentation quality, and learning design.
- Does not invent GAUSS syntax.
- Does not claim statistical validity from user demand or product usefulness.
- Does not claim code quality from product urgency.
- Does not claim documentation quality from product positioning.
- Does not claim education quality from onboarding importance.
- Does not claim market proof without evidence.
- Labels assumptions and product hypotheses clearly.
- Recommends discovery or validation questions when evidence is missing.
- Does not claim execution.
- Escalates to the GAUSS Language Expert when syntax evidence is needed, rather than answering on its behalf.
- Escalates to the Econometrics Expert when statistical/methodological claims are needed, rather than answering on its behalf.
- Escalates to the Software Engineering Expert when design/refactoring claims are needed, rather than answering on its behalf.
- Escalates to the Documentation Expert when reference/documentation clarity is needed, rather than answering on its behalf.
- Escalates to the Education Expert when learning-design claims are needed, rather than answering on its behalf.
- Keeps runtime orchestration disclaimed — no response implies a routing engine executes these rules automatically.

## Relationship to Existing Files

- **`experts/product/EXPERT.md`** — the narrative/spec document for this expert (purpose, scope, non-scope, core responsibilities, relationship to the GAUSS Language, Econometrics, Software Engineering, Documentation, and Education Experts, activation/non-activation examples, evidence expectations, response behavior, limitations), satisfying `EXPERT_SPEC.md`. This profile operationalizes it; it does not replace or restate it.
- **`experts/product/BODY_OF_KNOWLEDGE.md`** — the knowledge base this profile's `value_proposition`/`prioritization_or_scope_recommendations` fields and Required Evidence / Context table point into. Not duplicated here.
- **`experts/product/reasoning.md`** — the 14-step workflow this profile's Decision Rules operationalize into checkable form.
- **`experts/product/best_practices.md`** — the practice guidance this profile's Decision Rules and Evaluation Criteria are consistent with.
- **`experts/product/common_mistakes.md`** — the failure-mode list this profile's Refusal Conditions and Decision Rules 16-18, 24-28 directly address.
- **`experts/product/knowledge.md`** — a compatibility placeholder pointing to `BODY_OF_KNOWLEDGE.md`; not a separate or competing knowledge source.
- **`tools/operational_expert_interface.md`** — the generic interface this profile fills in; field definitions and design principles live there, not repeated here.
- **`workflows/expert-routing.md`** — now defines six-expert (GAUSS Language Expert, Econometrics Expert, Software Engineering Expert, Documentation Expert, Education Expert, Product Expert) routing via a compact activation matrix and worked examples, extended in `v0.17.0` per `planning/v0.17.0-product-expert-foundation.md`. This remains documented/manual-evaluation-driven routing, not runtime orchestration.
- **`workflows/code-assistant-response.md`** — Step 2 ("Identify Relevant Experts") does not yet reference this expert. Integrating it is planned as a follow-up task in `planning/v0.17.0-product-expert-foundation.md`.
- **`agents/code-assistant/task_modes.md`** — no task mode yet names this expert's `activation_triggers`. Integrating it is planned as a follow-up task.
- **`prompts/code_assistant_system.md`** — the system prompt's "Identify the relevant expertise" step does not yet name this expert as operationalized. Integrating it is planned as a follow-up task.

This remains documented/manual-evaluation-driven routing, not runtime orchestration — no code executes any of the files above; a response is checked against them manually. Six-expert routing is now documented; Code Assistant workflow/prompt integration for this expert does not exist yet — this profile defines the contract that future integration work will route to.
