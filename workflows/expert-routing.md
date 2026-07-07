# Expert Routing Workflow

## Purpose

This workflow routes Code Assistant tasks through operational experts. It replaces the vague "identify relevant experts" step in `workflows/code-assistant-response.md` and `prompts/code_assistant_system.md` with a checkable routing procedure: when to consult one or more operational experts, what to gather before applying their decision rules, and how to evaluate whether routing actually happened.

It now supports two operational experts:

- **GAUSS Language Expert** — implementation correctness.
- **Econometrics Expert** — methodological correctness.

Clarifications:

- **It is not a runtime orchestration engine.** No code executes this workflow; it is followed the same way `workflows/native-command-selection.md` or `workflows/retrieval-backed-response-pattern.md` are followed today — as a documented reasoning procedure a response can be checked against. Nothing in this update introduces multi-expert *execution* machinery; it defines a checkable reasoning procedure for single-expert and multi-expert routing, the same way `v0.8.0` defined one for single-expert routing.
- **It is a documented reasoning procedure for the Code Assistant**, not a new evidence system or a new set of decision rules — the rules it applies come from `experts/gauss-language/OPERATIONAL_PROFILE.md`, `experts/econometrics/OPERATIONAL_PROFILE.md`, and the evidence machinery already defined in `schemas/command_lookup_evidence.schema.json` and `workflows/retrieval-backed-response-pattern.md`.
- **The Software Engineering, Documentation, and Education experts named in `workflows/code-assistant-response.md` remain narrative-only for now.** This workflow's steps are written generically enough to extend to a third expert later without another rewrite.
- **Future experts can be added using the same operational interface** (`tools/operational_expert_interface.md`) — a new expert needs an operational profile filled in against that interface, after which this workflow's activation-trigger and non-activation steps gain one more expert to check against, and Step 4's routing-type categories gain one more dimension.

## Operational Experts Currently Supported

| Expert | Owns | Does not own |
|---|---|---|
| GAUSS Language Expert | GAUSS syntax, command selection, data structures, package/base distinction, implementation correctness | Econometric methodology or statistical validity |
| Econometrics Expert | Model choice, assumptions, diagnostics, interpretation, causal/predictive framing, statistical validity | Exact GAUSS syntax, command return fields, package/base distinction |

## Routing Principles

- Activate experts based on task/content triggers, not just keyword matching — a task can involve GAUSS or econometrics without either word appearing (e.g. "translate this R model" implies GAUSS as the target; "does this coefficient mean X causes Y" implies econometric interpretation).
- Expert activation is internal by default; the Code Assistant does not need to announce which expert(s) it consulted.
- Correct routing is evaluated through response behavior — whether decision rules were applied and evidence/context thresholds were honored — not through a self-reported label.
- Expert profiles add constraints and decision rules; they do not loosen evidence requirements. An expert can require more evidence than the general workflow demands, never less.
- Evidence requirements for GAUSS claims remain governed by the evidence schema (`schemas/command_lookup_evidence.schema.json`) and the retrieval-backed response pattern (`workflows/retrieval-backed-response-pattern.md`); this workflow routes *to* those, it does not redefine them.
- Non-activation cases matter as much as activation cases; do not over-route to either expert for tasks that do not need them. Unnecessary activation is itself a routing failure, not a safe default.
- Different experts own different failure modes: implementation correctness and methodological correctness are never the same claim, and neither expert may answer for the other's domain.
- Command availability is not methodological validity — a GAUSS command existing for a method is never evidence the method is the right choice for the user's data.
- Methodological appropriateness is not implementation evidence — a method being the right statistical choice is never evidence that specific GAUSS syntax exists or works as described.
- When both experts activate, keep implementation and methodology claims separate in substance, even when the final response reads as one coherent answer.
- If the two experts' conclusions appear to conflict (for example, a command exists and is syntactically fine, but the recommended model isn't appropriate for the data), surface the distinction explicitly rather than silently resolving it in either direction.
- The strictest applicable evidence/context requirement wins — if a task touches both domains, meeting only one expert's bar is not sufficient to answer the whole question.

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

Add a second classification axis, independent of task mode, that this workflow's routing decision actually consumes:

- **Implementation-focused** — the answer turns on GAUSS syntax, command selection, or language mechanics, with no statistical-methodology claim needed.
- **Methodology-focused** — the answer turns on model/estimator choice, assumptions, diagnostics, or interpretation, with no GAUSS implementation requested.
- **Mixed implementation + methodology** — both are genuinely in play; neither alone answers the question.
- **Neither** — the task involves no GAUSS syntax and no statistical-methodology question at all.

Examples:

- "What is the exact syntax for `olsmt`?" → implementation-focused.
- "Is OLS appropriate for this causal question?" → methodology-focused.
- "Translate this regression into GAUSS and tell me what diagnostics to run" → mixed.
- "Write a changelog entry" → neither.

This step is the same task-mode classification already required by `workflows/code-assistant-response.md` Step 1 and `prompts/code_assistant_system.md`'s "Classify the task" step, with the second axis added specifically for this workflow's routing decision — it is not a new classification pass end to end.

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

### Neither expert

Do not activate either expert for tasks such as:

- Changelog entries
- Release readiness notes
- General project tracking
- Repository housekeeping with no GAUSS syntax and no statistical-methodology question

Negative routing is part of correctness, not an afterthought, for both experts individually and for the neither-expert case. A response that applies GAUSS-specific or econometric decision rules and evidence/context requirements to a task that never needed them is a routing failure in the same way a missed activation is — it adds unrequested scope, and evaluation (Step 11) checks for it explicitly.

## Step 4 — Determine Routing Type

Combine the results of Steps 2 and 3 into one of four routing types:

### GAUSS-only

Use when:

- Exact syntax, command signatures, return fields, package/base distinction, data structures, or GAUSS debugging are central.
- No statistical-methodology claim is needed.

### Econometrics-only

Use when:

- The user asks about model choice, assumptions, interpretation, diagnostics, or causal/predictive framing.
- No GAUSS implementation or syntax is requested.

### Both experts

Use when:

- The user asks for econometric analysis implemented in GAUSS.
- Translating statistical code into GAUSS.
- Choosing a GAUSS command for a statistical method.
- Reviewing GAUSS analysis code for both syntax and methodology.
- Explaining GAUSS model output.
- Recommending diagnostics to run in GAUSS.
- Valid GAUSS code may still be statistically inappropriate.

### Neither

Use when:

- The task is writing, project management, or release tracking, and has no GAUSS syntax issue and no statistical-methodology issue.

## Step 5 — Gather Required Inputs

Gather inputs based on the routing type determined in Step 4. Do not gather the full input set for an expert that isn't activating.

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

**For both (when routing type is "both"):**

- Gather both sets above, but do not block on every optional detail from either side.
- Ask a focused clarifying question only when missing information would materially change the answer, per `agents/code-assistant/task_modes.md`'s Clarifying Question Rules.
- Otherwise, state a clearly stated assumption for whichever side is underspecified (for example, "I'll assume your input is a numeric matrix" for the GAUSS side, or "I'll assume this is a predictive, not causal, goal" for the econometrics side).

## Step 6 — Determine Evidence and Context Needed

**For the GAUSS Language Expert**, use the Required Evidence by Task Type table in `experts/gauss-language/OPERATIONAL_PROFILE.md`. Baseline rules, restated here for quick reference but governed there:

- Exact syntax/defaults/returns require `source_authority: official_docs` or `official_package_docs` evidence.
- Category lists (`source_authority: category_list`) support discovery only.
- Curated notes (`source_authority: curated_command_note`) cannot override official docs.
- The retrieval-backed response pattern (`workflows/retrieval-backed-response-pattern.md`) governs how each evidence state (found, ambiguous, conflict, stale, etc.) shapes the response.

**For the Econometrics Expert**, use the Required Evidence / Context by Task Type table in `experts/econometrics/OPERATIONAL_PROFILE.md`. Baseline rules, restated here but governed there:

- Methodological claims require adequate context for goal, data structure, outcome type, and main assumptions.
- Causal claims require identification/design support, not regression output alone.
- Forecasting claims require time ordering and a validation strategy.
- Interpretation requires model, variable, and output context.
- Command availability is never evidence of methodological appropriateness.

**For both (when routing type is "both"):**

- GAUSS command evidence and econometric methodological context are separate requirements. Meeting one does not satisfy the other, and satisfying neither is not offset by high confidence on the other side.
- If either side is missing, preserve uncertainty for that side only — do not let a fully-satisfied GAUSS evidence bar imply the methodology is also settled, or vice versa.

## Step 7 — Route to Retrieval or Clarification

- Route to `workflows/command-documentation-retrieval.md` when GAUSS command evidence is missing, then use `workflows/retrieval-backed-response-pattern.md` to handle the resulting state (`found_complete`, `found_incomplete`, `not_found`, `ambiguous`, `conflict`, `stale`, or `error`). Do not answer exact GAUSS syntax, defaults, or return values from memory while this is pending.
- Ask the user for methodological context when goal, design, outcome type, or data structure is missing and materially affects the recommendation.
- Do not ask unnecessary questions when a safe assumption is enough, on either side.
- In both-experts cases, it is acceptable to provide implementation guidance with methodology caveats, or methodology guidance with implementation caveats, as long as the missing side is stated explicitly rather than silently glossed over.

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

### Coordination rules

- The GAUSS Language Expert owns implementation correctness.
- The Econometrics Expert owns methodological correctness.
- The Econometrics Expert may recommend a method but cannot invent GAUSS syntax to express it.
- The GAUSS Language Expert may recommend a command but cannot claim statistical appropriateness by availability alone.
- If both activate, the final response should separate the implementation recommendation from the methodology recommendation when it helps clarity — they do not need separate labeled sections in every response, but they must be distinguishable in substance.
- If one expert's side is uncertain (missing evidence, missing context), do not let confidence on the other side mask that uncertainty. A verified GAUSS command and an unverified methodological fit are not the same as a fully verified answer.

## Step 9 — Produce Internal Routing Output

Use the output contract, extended for multiple experts:

- `task_classification`
- `routing_type` — one of `gauss_only`, `econometrics_only`, `both`, `neither`
- `activated_experts`
- `activation_reason_by_expert`
- `non_activation_reason_by_expert`, when relevant
- `evidence_needed_by_expert`
- `context_needed_by_expert`
- `evidence_or_context_used`
- `implementation_recommendation`
- `methodology_recommendation`
- `conflicts_or_tensions`
- `response_constraints`
- `validation_or_diagnostic_suggestions`

These fields remain internal by default. They do not need to appear as labels in the user-facing response — they are the internal structure the response should satisfy in substance, the same way a response satisfies `evaluations/scoring.md` dimensions without printing their names.

## Step 10 — Compose the User Response

The final response should:

- Answer the user naturally, without a forced expert-routing preamble.
- Show expert routing through correctness, evidence/context use, and uncertainty handling, not a literal "expert activated" label.
- Separate implementation and methodology claims when both matter, so neither is misread as validating the other.
- Cite or name GAUSS evidence when appropriate (a source file, a curated note, an official doc reference).
- State assumptions and caveats explicitly for methodology claims, the same way GAUSS-side assumptions are stated.
- Include validation suggestions (for generated/translated/debugged GAUSS code) or diagnostic suggestions (for methodological recommendations) when the task calls for one.
- Avoid overclaiming: never state or imply that GAUSS code was executed, that schema/structural validity is the same as semantic correctness, or that a methodologically sound recommendation has been implementation-verified (or vice versa).

## Step 11 — Evaluate Routing

Manual evaluation should check:

- Correct routing type (GAUSS-only, econometrics-only, both, or neither) for the task at hand.
- Correct expert activation, or correct non-activation, for each expert individually.
- Evidence threshold met for any exact GAUSS syntax/defaults/returns claim.
- Context threshold met for any methodological claim (goal, data structure, design support for causal claims, etc.).
- No invented GAUSS syntax, procedures, or APIs.
- No unsupported causal or statistical-validity claims.
- Uncertainty preserved on each side independently — one side being resolved does not paper over the other being unresolved.
- No over-routing — the response does not apply GAUSS-specific or econometric reasoning to a task from either expert's Non-Activation Cases list.
- Conflicts or tensions between the two experts' conclusions are surfaced when they exist, not silently resolved.
- Validation or diagnostic suggestions included where appropriate.

## Routing Examples

1. **Exact `olsmt` syntax only.** GAUSS Language Expert only — implementation-focused, no methodology claim requested.
2. **"Is OLS appropriate for this causal question?" with no GAUSS code requested.** Econometrics Expert only — methodology-focused, no implementation claim requested.
3. **Translate R's `lm()` to GAUSS and explain what diagnostics to run.** Both experts — GAUSS Language Expert handles the `olsmt` translation and evidence-backed syntax; Econometrics Expert handles the diagnostic recommendations, kept as a separate contribution rather than blended into the code explanation.
4. **Valid GAUSS regression code, but an omitted-variable concern in the setup.** Both experts — GAUSS Language Expert confirms the code is syntactically sound; Econometrics Expert flags the methodological issue explicitly rather than letting syntactic validity imply statistical soundness.
5. **Generic OLS concept explanation with no implementation requested.** Econometrics Expert only, per Step 3's GAUSS Language Expert non-activation case for "generic statistics/econometrics explanations with no GAUSS implementation."
6. **Changelog update for a release.** Neither expert — release tracking, even when the changelog entries describe GAUSS-related or econometrics-related work.
7. **Ambiguous GAUSS command evidence (multiple plausible documentation matches).** GAUSS Language Expert only, with escalation to retrieval per Step 7 and `workflows/retrieval-backed-response-pattern.md` state D — the ambiguity is resolved by asking or re-retrieving, never by inventing syntax.
8. **Forecast model selection with GAUSS implementation also requested.** Both experts — Econometrics Expert recommends the forecasting approach and validation strategy; GAUSS Language Expert verifies whether a native command exists and what its evidence-backed syntax is.
9. **"What does this p-value mean?" with no GAUSS syntax question.** Econometrics Expert only — pure interpretation, no implementation claim involved.

## Relationship to Existing Files

- **`tools/operational_expert_interface.md`** — defines the generic interface (activation triggers, evidence/context requirements, decision rules, output contract, evaluation criteria) that this workflow routes against for both experts. This workflow does not redefine that interface's fields.
- **`experts/gauss-language/OPERATIONAL_PROFILE.md`** — the filled-in GAUSS Language Expert profile this workflow's GAUSS-side steps are sourced from. If the profile changes, this workflow's GAUSS-side content should be updated to match rather than allowed to drift.
- **`experts/econometrics/OPERATIONAL_PROFILE.md`** — the filled-in Econometrics Expert profile this workflow's econometrics-side steps are sourced from, following the same drift-prevention principle.
- **`workflows/code-assistant-response.md`** — this workflow is the specialization of that document's Step 2 ("Identify Relevant Experts") for both operational experts; the general response workflow still governs task classification, retrieval need, and response composition around it. Not yet updated to reference the multi-expert version of this workflow (see Maintenance Notes / next task).
- **`workflows/retrieval-backed-response-pattern.md`** — governs Step 7's GAUSS-side evidence-state handling; this workflow does not redefine states A-H.
- **`workflows/command-documentation-retrieval.md`** — governs the hybrid discovery/retrieval strategy this workflow routes to in Step 7 for GAUSS command evidence.
- **`workflows/native-command-selection.md`** — governs the native-vs-manual decision this workflow's Step 8 GAUSS-side rules reference.
- **`agents/code-assistant/task_modes.md`** — the task-mode definitions consumed in Step 1 and the Clarifying Question Rules referenced in Step 5. Not yet updated for multi-expert routing (see Maintenance Notes / next task).
- **`prompts/code_assistant_system.md`** — the system prompt whose "Identify the relevant expertise" step this workflow operationalizes. Not yet updated for multi-expert routing (see Maintenance Notes / next task).

## Maintenance Notes

- Update this workflow when either `OPERATIONAL_PROFILE.md` changes, or when a new operational expert is added (extending Step 2's trigger lists, Step 3's non-activation lists, and Step 4's routing-type categories to cover it).
- Keep each expert's trigger/non-activation lists in this workflow aligned with its own `OPERATIONAL_PROFILE.md` — this workflow should mirror those profiles, never diverge from them.
- Future benchmark category `16.x` should test GAUSS-only, econometrics-only, both-experts, and neither-expert routing, extending the single-expert coverage already validated by `15.x`.
