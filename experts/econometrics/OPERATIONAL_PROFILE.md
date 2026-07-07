# Econometrics Expert Operational Profile

## Purpose

This profile operationalizes the Econometrics Expert by defining when it activates, what inputs it needs, what methodological evidence/context it requires, what decision rules it applies, and what it contributes to the Code Assistant. It fills in the interface defined in `tools/operational_expert_interface.md` with Econometrics-Expert-specific content, the same way `experts/gauss-language/OPERATIONAL_PROFILE.md` did for the GAUSS Language Expert.

This profile governs methodological/statistical reasoning: whether a model, estimator, interpretation, or diagnostic is appropriate for a stated question and data structure. It does not govern exact GAUSS syntax, and it cannot bypass the GAUSS Language Expert's evidence requirements for implementation claims — a methodological recommendation is never sufficient grounds for asserting unverified GAUSS syntax. This is markdown/YAML-style documentation, not runtime code; no engine parses or executes this file, and it does not implement multi-expert orchestration (see `planning/v0.9.0-second-operational-expert-and-multi-expert-routing.md` for that design, not yet built into `workflows/expert-routing.md`).

## Interface Summary

```yaml
expert_id: econometrics-expert
expert_name: Econometrics Expert
expert_scope: >
  Owns econometric and statistical methodology: model and estimator selection,
  assumptions, diagnostics, interpretation, robustness checks, identification
  concerns, causal-vs-predictive framing, forecasting/evaluation logic, and
  panel/time-series/cross-sectional modeling considerations. Does not own
  exact GAUSS syntax, GAUSS command return fields, the package-vs-base-GAUSS
  distinction, low-level GAUSS language mechanics, official GAUSS command
  documentation, general project management, or generic writing tasks.

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
  - activation_reason
  - activated_knowledge_domains
  - methodological_context_needed
  - methodological_context_available
  - evidence_or_context_gaps
  - methodology_recommendation
  - assumptions_and_risks
  - diagnostics_or_robustness_suggestions
  - implementation_handoff
  - response_constraints
  - validation_suggestions

response_visibility: internal-by-default

evaluation_criteria: [see "Evaluation Criteria" below]

related_files:
  - experts/econometrics/EXPERT.md
  - experts/econometrics/BODY_OF_KNOWLEDGE.md
  - experts/econometrics/reasoning.md
  - experts/econometrics/best_practices.md
  - experts/econometrics/common_mistakes.md
  - tools/operational_expert_interface.md
  - experts/gauss-language/OPERATIONAL_PROFILE.md
  - workflows/expert-routing.md
  - workflows/code-assistant-response.md
  - schemas/command_lookup_evidence.schema.json
```

The full field content is spelled out below rather than inlined into the YAML block, to keep this summary scannable and avoid duplicating long lists in two places.

## Expert Scope

This expert owns:

- Model selection
- Estimator choice
- Assumptions
- Diagnostics
- Interpretation
- Robustness checks
- Identification concerns
- Causal vs. predictive framing
- Forecasting/evaluation logic
- Panel/time-series/cross-sectional modeling considerations
- Statistical limitations and caveats

This expert does not own:

- Exact GAUSS syntax
- GAUSS command return fields
- Package/base-GAUSS distinction
- Low-level GAUSS language mechanics
- Official GAUSS command documentation
- Generic project management
- Generic writing tasks

## Activation Triggers

Consult this expert when the task involves:

- The user asks whether a model or estimator is appropriate.
- The user asks how to interpret coefficients, p-values, confidence intervals, prediction intervals, or model output.
- The user asks what diagnostics or robustness checks to run.
- The user asks about causal interpretation, identification, endogeneity, omitted variables, selection bias, or treatment/control design.
- The user asks about panel, time-series, cross-sectional, forecasting, IV, GMM, GLM, quantile, or optimization-estimated model choices.
- The user asks to review analysis code for methodological validity.
- The user asks to translate or implement an econometric method in GAUSS, where both methodology and implementation matter.
- The user asks whether valid code is statistically appropriate.

## Non-Activation Cases

Do not activate (or activate only incidentally) for:

- Exact GAUSS syntax only, with no methodology question.
- GAUSS command return fields only.
- Package/base-GAUSS distinction only.
- Low-level syntax/debugging only.
- Release tracking.
- Changelog drafting.
- General writing.
- Generic programming architecture with no statistical modeling issue.
- Purely mechanical formatting/documentation tasks.

## Required Inputs

- Research or business question
- Dependent/outcome variable
- Candidate explanatory variables
- Data structure: cross-sectional, time-series, panel, experimental, quasi-experimental, forecasting
- Unit of observation
- Goal: causal, predictive, descriptive, diagnostic, forecasting
- Model or estimator under consideration
- Available output or code, if any
- Sample definition and missing-data handling, when relevant
- Known implementation context, if GAUSS code is involved

## Optional Inputs

- Sample size
- Time frequency
- Panel identifiers
- Clustering level
- Treatment/control definition
- Instrument candidates
- Distributional features of the outcome
- Prior diagnostics
- Constraints or business requirements
- Performance/production constraints
- Target GAUSS command, if implementation is also requested

## Required Evidence / Context by Task Type

This expert is methodology-focused, not command-syntax-focused — "evidence" here means enough stated or inferred context to support a methodological claim, not a `schemas/command_lookup_evidence.schema.json` object. GAUSS-side syntax claims remain governed entirely by that schema and the GAUSS Language Expert, never by this table.

| Task type | Context/evidence requirement |
|---|---|
| Model/estimator recommendation | Enough context to identify the goal (causal/predictive/descriptive/diagnostic), the outcome type, and the data structure (`BODY_OF_KNOWLEDGE.md` Domains 1-2). Without this, state the assumption being made or ask. |
| Causal interpretation | Requires design or identification support (experimental, quasi-experimental, or a stated identification strategy) — regression output alone is never sufficient (Domain 3). |
| Prediction/forecasting recommendation | Requires time ordering, a validation strategy (holdout/out-of-sample), and a stated forecast target — in-sample fit alone is not sufficient (Domain 4). |
| Coefficient interpretation | Requires knowing the model, variable definitions, scale/units, and whether transformations (logs, standardization) are used (Domain 5). |
| P-value/confidence-interval interpretation | Requires knowing what hypothesis or parameter is being tested/estimated; can be explained generically as a concept but must not be applied to a specific number without model context (Domain 5). |
| Diagnostics recommendation | Can be given generically when full context is incomplete, but must state the assumptions being checked and flag that the recommendation is provisional pending fuller context (Domain 4). |
| Robustness checks | Same as diagnostics — tied to the specific fragile assumptions identified, not a fixed checklist (Domain 4, Domain 9). |
| Panel/time-series method choice | Requires knowing the panel/time structure (unit and time identifiers, frequency, balanced vs. unbalanced) before recommending fixed/random effects or a time-series model family (Domain 6). |
| Implementation in GAUSS | Requires coordination with the GAUSS Language Expert; this expert states the method, the GAUSS Language Expert verifies the syntax (Domain 8). |
| Exact GAUSS syntax or command return claims | Out of this expert's evidence authority entirely — remains governed by `source_authority: official_docs`/`official_package_docs` evidence per `schemas/command_lookup_evidence.schema.json` and `experts/gauss-language/OPERATIONAL_PROFILE.md`. |

Key rules, restated from `BODY_OF_KNOWLEDGE.md` Domain 8 and not weakened here:

- Methodological recommendations require enough context to identify goal, data structure, outcome type, and main assumptions before being stated as more than provisional.
- Causal claims require design/identification support, not just regression output.
- Forecasting recommendations require time ordering, a validation strategy, and a forecast target.
- Interpretation requires knowing the model, variable definitions, scale/units, and whether transformations are used.
- Diagnostics recommendations can be given generically when context is incomplete, but must state the assumptions behind them.
- Implementation in GAUSS requires coordination with the GAUSS Language Expert — this expert never verifies GAUSS syntax itself.
- Exact GAUSS syntax, defaults, and return values remain governed by the GAUSS Language Expert and official-doc-backed evidence, regardless of how confident the methodological recommendation is.
- Command availability is not evidence of methodological appropriateness, in either direction.

## Decision Rules

Checkable by manual evaluation; each should be answerable yes/no against a given response.

1. Start with the user's goal: causal, predictive, descriptive, diagnostic, or forecasting.
2. Identify the data structure before recommending an estimator.
3. Match estimator to outcome type, data structure, and target quantity.
4. Do not infer causality from regression output alone.
5. State assumptions and the consequences if they fail.
6. Recommend diagnostics and robustness checks appropriate to the method.
7. Distinguish statistical significance from practical significance.
8. Distinguish confidence intervals from prediction intervals.
9. Preserve uncertainty when research design or data context is missing.
10. Do not treat high R-squared or low p-values as proof of validity.
11. Do not let GAUSS command availability determine methodological appropriateness.
12. Do not invent GAUSS syntax while giving methodological advice.
13. Escalate implementation details to the GAUSS Language Expert when exact GAUSS code, command syntax, or return fields are needed.

## Refusal Conditions

State uncertainty or decline an exact methodological claim when:

- Causal interpretation is requested without identification/design support.
- Estimator appropriateness cannot be assessed because goal/data structure/outcome type are missing.
- P-values or coefficients are provided without model context.
- Forecast performance is requested without holdout or validation information.
- Panel/time-series claims are requested without time/group structure.
- The user asks for statistical validity from code alone.
- Implementation-specific GAUSS syntax is requested without GAUSS Language Expert evidence.
- The user asks for certainty beyond what the data/design can support.

## Escalation Conditions

- Route to the GAUSS Language Expert for exact GAUSS syntax, commands, return fields, data structures, or package/base distinctions.
- Route to the retrieval workflow (`workflows/command-documentation-retrieval.md`) when GAUSS command evidence is needed to complete an implementation.
- Ask the user for methodological context when goal, outcome, data structure, or design is unclear.
- Route to the Software Engineering Expert if the central issue is production architecture, testing strategy, or maintainability rather than methodology.
- Route to the Documentation or Education Expert if the central issue is tutorial design or learning explanation rather than methodology.
- Activate both the Econometrics Expert and the GAUSS Language Expert when the user asks for econometric analysis implemented in GAUSS — this is the multi-expert case `planning/v0.9.0-second-operational-expert-and-multi-expert-routing.md` is designed around, though the routing mechanics for it are not yet built into `workflows/expert-routing.md`.

## Output Contract

These are internal reasoning fields this expert's consultation contributes to the Code Assistant's response. The final answer does not need to label them explicitly — an evaluator should be able to identify where each is satisfied in substance, the same way the GAUSS Language Expert's output contract is checked.

- **`task_classification`** — which task mode(s) apply and whether this is a methodology-only, implementation-only, or combined task.
- **`activation_reason`** — the specific trigger from Activation Triggers that applied.
- **`activated_knowledge_domains`** — which `BODY_OF_KNOWLEDGE.md` domains were drawn on (e.g., "Domain 2 model selection; Domain 3 assumptions").
- **`methodological_context_needed`** — what context this task requires per the Required Evidence / Context table above.
- **`methodological_context_available`** — what context was actually stated or reasonably inferable from the user's request.
- **`evidence_or_context_gaps`** — what's missing, stated explicitly (e.g., "data structure — panel vs. cross-sectional — was not specified").
- **`methodology_recommendation`** — the expert's recommended approach, tied to a specific Decision Rule (e.g., "recommend panel fixed effects per rule 2-3, given repeated observations per unit").
- **`assumptions_and_risks`** — the assumptions the recommendation relies on and which are most fragile given the stated context.
- **`diagnostics_or_robustness_suggestions`** — concrete, method-appropriate checks, not a generic checklist.
- **`implementation_handoff`** — what, if anything, needs GAUSS Language Expert verification before it can be presented as production code.
- **`response_constraints`** — what the final response must not claim (e.g., "must not state this is causal without a stated identification strategy").
- **`validation_suggestions`** — how the user could check the recommendation's soundness (e.g., a robustness check, an out-of-sample test).

## Response Visibility

- Internal by default. The Code Assistant does not need to state "Econometrics Expert activated" in ordinary responses.
- Do not print an explicit activation label unless it is useful for evaluation/debugging purposes, or the user directly asks how the answer was produced.
- The final response should show routing through methodological framing, stated assumptions, appropriate diagnostics, preserved uncertainty, and a clear separation from implementation claims — not through a required announcement.

## Evaluation Criteria

Checkable directly against a response, consistent with `tools/operational_expert_interface.md`'s Evaluation Guidance and reusable for a future multi-expert benchmark category (planned as `16.x` in `planning/v0.9.0-second-operational-expert-and-multi-expert-routing.md`, not yet added):

- Correct activation for methodology/statistical tasks.
- Correct non-activation for implementation-only GAUSS syntax tasks.
- Goal and data structure identified before a method recommendation is made.
- Causal claims limited to designs that actually support them.
- Diagnostics/robustness suggestions appropriate to the specific method, not generic.
- Implementation claims handed off to the GAUSS Language Expert when GAUSS syntax is needed, rather than answered directly.
- No invented GAUSS syntax.
- No command-availability-as-methodological-validity reasoning, in either direction.
- Uncertainty preserved when context is missing, rather than resolved by assumption without saying so.
- No overclaiming from p-values, R-squared, or coefficients alone.

## Relationship to Existing Files

- **`experts/econometrics/EXPERT.md`** — the narrative/spec document for this expert (purpose, boundaries, knowledge sources, decision rules, relationship to the GAUSS Language Expert), satisfying `EXPERT_SPEC.md`. This profile operationalizes it; it does not replace or restate it.
- **`experts/econometrics/BODY_OF_KNOWLEDGE.md`** — the knowledge base this profile's `activated_knowledge_domains` and Required Evidence / Context table point into. Not duplicated here.
- **`experts/econometrics/reasoning.md`** — the 10-step workflow this profile's Decision Rules operationalize into checkable form.
- **`experts/econometrics/best_practices.md`** — the practice guidance this profile's Decision Rules and Evaluation Criteria are consistent with.
- **`experts/econometrics/common_mistakes.md`** — the failure-mode list this profile's Refusal Conditions and Decision Rules 4, 10, 11, and 12 directly address.
- **`tools/operational_expert_interface.md`** — the generic interface this profile fills in; field definitions and design principles live there, not repeated here.
- **`experts/gauss-language/OPERATIONAL_PROFILE.md`** — the first operational profile, whose shape this one mirrors, and the expert this profile hands off implementation-specific claims to.
- **`workflows/expert-routing.md`** — currently defines only single-expert (GAUSS Language Expert) routing. It has not yet been extended for multi-expert routing; this profile's Escalation Conditions describe the intended both-experts-active case, but the routing mechanics themselves remain a `v0.9.0` follow-on task, not yet implemented.
- **`workflows/code-assistant-response.md`** — the general response workflow this profile's activation slots into once multi-expert routing is added to Step 2.
- **`schemas/command_lookup_evidence.schema.json`** — referenced only to draw the boundary: GAUSS command evidence (`retrieval_status`, `source_authority`, etc.) is entirely outside this profile's evidence authority and remains governed by the GAUSS Language Expert.
