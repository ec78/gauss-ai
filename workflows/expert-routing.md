# Expert Routing Workflow

## Purpose

This workflow routes Code Assistant tasks through operational experts. It replaces the vague "identify relevant experts" step in `workflows/code-assistant-response.md` and `prompts/code_assistant_system.md` with a checkable routing procedure: when to consult one or more operational experts, what to gather before applying their decision rules, and how to evaluate whether routing actually happened.

It now supports three operational experts:

- **GAUSS Language Expert** — implementation correctness.
- **Econometrics Expert** — methodological correctness.
- **Software Engineering Expert** — maintainability/design correctness.

Clarifications:

- **It is not a runtime orchestration engine.** No code executes this workflow; it is followed the same way `workflows/native-command-selection.md` or `workflows/retrieval-backed-response-pattern.md` are followed today — as a documented reasoning procedure a response can be checked against. Nothing in this update introduces multi-expert *execution* machinery; it extends the documented reasoning procedure from two operational experts to three, the same way `v0.9.0` extended single-expert routing to two.
- **It is a documented reasoning procedure for the Code Assistant**, not a new evidence system or a new set of decision rules — the rules it applies come from `experts/gauss-language/OPERATIONAL_PROFILE.md`, `experts/econometrics/OPERATIONAL_PROFILE.md`, `experts/software-engineering/OPERATIONAL_PROFILE.md`, and the evidence machinery already defined in `schemas/command_lookup_evidence.schema.json` and `workflows/retrieval-backed-response-pattern.md`.
- **The Documentation and Education experts named in `workflows/code-assistant-response.md` remain narrative-only for now.** This workflow's steps are written generically enough to extend to a fourth expert later without another rewrite.
- **Code Assistant workflow/prompt integration for the Software Engineering Expert is complete.** `workflows/code-assistant-response.md`, `agents/code-assistant/task_modes.md`, and `prompts/code_assistant_system.md` all reference this expert alongside the GAUSS Language Expert and Econometrics Expert as of `v0.14.0` (see `planning/v0.14.0-software-engineering-expert-foundation.md`).
- **Future experts can be added using the same operational interface** (`tools/operational_expert_interface.md`) — a new expert needs an operational profile filled in against that interface, after which this workflow's activation-trigger and non-activation steps gain one more expert to check against, and Step 4's routing-type categories gain one more dimension, the same way the Software Engineering Expert's addition here expanded routing from four types to eight.

## Operational Experts Currently Supported

| Expert | Owns | Does not own |
|---|---|---|
| GAUSS Language Expert | GAUSS syntax, command selection, data structures, package/base distinction, implementation correctness | Econometric methodology or statistical validity; code maintainability/design |
| Econometrics Expert | Model choice, assumptions, diagnostics, interpretation, causal/predictive framing, statistical validity | Exact GAUSS syntax, command return fields, package/base distinction; code maintainability/design |
| Software Engineering Expert | Code quality, maintainability, modularity, readability, refactoring, testability, error handling, edge-case thinking, safe change management | Exact GAUSS syntax, command evidence, package/base distinction; econometric methodology or statistical validity |

### Software Engineering Expert — Failure Modes Prevented

- Treating valid code as well-designed code.
- Unsafe refactors that silently change behavior.
- Duplicated or tangled logic left unaddressed.
- Unclear naming that obscures intent.
- Hidden dependencies between parts of the code.
- Missing validation/testing strategy for risky changes.
- Claiming code was executed when it was not.
- Treating clean code as statistical validity.

## Routing Principles

- Activate experts based on task/content triggers, not just keyword matching — a task can involve GAUSS, econometrics, or code quality without any of those words appearing (e.g. "translate this R model" implies GAUSS as the target; "does this coefficient mean X causes Y" implies econometric interpretation; "this script is a mess" implies a maintainability concern).
- Expert activation is internal by default; the Code Assistant does not need to announce which expert(s) it consulted.
- Correct routing is evaluated through response behavior — whether decision rules were applied and evidence/context thresholds were honored — not through a self-reported label.
- Expert profiles add constraints and decision rules; they do not loosen evidence requirements. An expert can require more evidence than the general workflow demands, never less.
- Evidence requirements for GAUSS claims remain governed by the evidence schema (`schemas/command_lookup_evidence.schema.json`) and the retrieval-backed response pattern (`workflows/retrieval-backed-response-pattern.md`); this workflow routes *to* those, it does not redefine them.
- Non-activation cases matter as much as activation cases; do not over-route to any expert for tasks that do not need them. Unnecessary activation is itself a routing failure, not a safe default.
- Different experts own different kinds of correctness: GAUSS syntax correctness (implementation), econometric validity (methodology), and software maintainability (design) are three separate claims, and no expert may answer for another's domain.
- Command availability is not methodological validity — a GAUSS command existing for a method is never evidence the method is the right choice for the user's data.
- Methodological appropriateness is not implementation evidence — a method being the right statistical choice is never evidence that specific GAUSS syntax exists or works as described.
- Valid GAUSS code can still be poorly designed — syntactic validity and good design are independent claims.
- Clean code can still be statistically invalid — code quality and methodological soundness are independent claims.
- A methodologically appropriate analysis can still be poorly implemented or hard to maintain — methodological validity and maintainability are independent claims.
- The Software Engineering Expert may recommend structure but cannot invent GAUSS syntax to implement it; unverified structural suggestions must be labeled as pseudocode.
- The Software Engineering Expert may recommend tests or checks but cannot claim code was executed or a test was run unless it actually was.
- When multiple experts activate, keep implementation, methodology, and maintainability claims separate in substance, even when the final response reads as one coherent answer.
- If two or more experts' conclusions appear to conflict (for example, a command exists and is syntactically fine, but the recommended model isn't appropriate for the data, or a refactor is well-organized but changes behavior), surface the distinction explicitly rather than silently resolving it in either direction.
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

Add a second classification pass, independent of task mode, that this workflow's routing decision actually consumes. Answer three independent questions about the task — each is a yes/no judgment, not a single label, since a task can be "yes" on more than one axis at once:

1. **GAUSS implementation axis** — does the answer turn on GAUSS syntax, command selection, or language mechanics? Examples: GAUSS syntax, command usage, package/base distinction, DataFrame/matrix/structure usage, GAUSS code generation/debugging.
2. **Econometric methodology axis** — does the answer turn on model/estimator choice, assumptions, diagnostics, or interpretation? Examples: estimator choice, assumptions, diagnostics, causal interpretation, forecasting/statistical evaluation, panel/time-series/cross-sectional modeling.
3. **Software engineering/code-quality axis** — does the answer turn on code organization, maintainability, or safe change management? Examples: refactoring, code review, maintainability, readability, modularity, testability, error handling, edge cases, duplication, safe change management.

The combination of the three yes/no answers determines the routing type in Step 4.

Examples:

- "What is the exact syntax for `olsmt`?" → GAUSS implementation only.
- "Is OLS appropriate for this causal question?" → econometric methodology only.
- "How should I refactor this generic duplicated pseudocode?" → software engineering only.
- "Translate this regression into GAUSS and tell me what diagnostics to run" → GAUSS implementation + econometric methodology.
- "Refactor this GAUSS code with repeated blocks" → GAUSS implementation + software engineering.
- "Organize my regression workflow with diagnostics and reporting" → econometric methodology + software engineering.
- "Write GAUSS logistic regression code, structure it cleanly, and explain if logistic is appropriate" → all three axes.
- "Write a changelog entry" → none of the three axes.

This step is the same task-mode classification already required by `workflows/code-assistant-response.md` Step 1 and `prompts/code_assistant_system.md`'s "Classify the task" step, with the three-axis pass added specifically for this workflow's routing decision — it is not a new classification pass end to end.

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

### None of the three

Do not activate any expert for tasks such as:

- Changelog entries
- Release readiness notes
- General project tracking
- Repository housekeeping with no GAUSS syntax, no statistical-methodology question, and no code-quality question

Negative routing is part of correctness, not an afterthought, for each expert individually and for the none-of-the-three case. A response that applies GAUSS-specific, econometric, or software-engineering decision rules and evidence/context requirements to a task that never needed them is a routing failure in the same way a missed activation is — it adds unrequested scope, and evaluation (Step 11) checks for it explicitly.

## Step 4 — Determine Routing Type

Combine the results of Steps 2 and 3 into one of eight routing types. This is a documented set of combinations to check against, not a combinatorial routing engine — each type below is one sentence plus a worked example.

### 1. GAUSS-only

When it applies: exact syntax, command signatures, return fields, package/base distinction, data structures, or GAUSS debugging are central, with no methodology claim and no design/maintainability claim.
Example: "What does `strindx` return when not found?"
Evidence/context pattern: official-doc-backed GAUSS command evidence.
Response rule: answer from verified evidence only; no methodology or design commentary is needed.

### 2. Econometrics-only

When it applies: the user asks about model choice, assumptions, interpretation, diagnostics, or causal/predictive framing, with no GAUSS implementation and no design/maintainability question.
Example: "Does p=0.03 mean the model explains 3%?"
Evidence/context pattern: methodological context (goal, data structure, outcome type).
Response rule: answer from methodological reasoning only; no GAUSS syntax or design commentary is needed.

### 3. Software-engineering-only

When it applies: the user asks about code organization, maintainability, refactoring, testing, or safe change management, with no GAUSS-specific syntax question and no econometric-methodology question.
Example: "How should I refactor this generic duplicated pseudocode?"
Evidence/context pattern: the stated code/task context and goal; no command evidence and no methodological context required.
Response rule: answer from design reasoning only; label any illustrative structure as pseudocode if it is not verified GAUSS.

### 4. GAUSS + Econometrics

When it applies: the user asks for econometric analysis implemented in GAUSS, translating statistical code into GAUSS, choosing a GAUSS command for a statistical method, or reviewing GAUSS analysis code for both syntax and methodology.
Example: "Translate `lm()` to GAUSS and interpret the causal claim."
Evidence/context pattern: GAUSS command evidence and methodological context, gathered separately; meeting one does not satisfy the other.
Response rule: keep the implementation recommendation and methodology recommendation distinguishable in substance; valid GAUSS code may still be statistically inappropriate.

### 5. GAUSS + Software Engineering

When it applies: the user provides or requests GAUSS code and also asks for a cleaner structure, refactor, or maintainability review of it.
Example: "Refactor this GAUSS code with repeated blocks."
Evidence/context pattern: GAUSS command evidence for any syntax claims, plus the stated code and behavior-preservation constraints for the design side; no methodological context required unless the task also touches modeling.
Response rule: the GAUSS Language Expert owns syntax validity; the Software Engineering Expert owns refactor strategy; unverified structural suggestions are labeled as pseudocode rather than presented as verified GAUSS.

### 6. Econometrics + Software Engineering

When it applies: the user describes an econometric analysis workflow and asks how to organize, decompose, or maintain it, without a GAUSS-specific syntax question.
Example: "Organize my regression workflow with diagnostics and reporting."
Evidence/context pattern: methodological context for the modeling/diagnostics side, plus the stated workflow structure and goal for the design side; no GAUSS command evidence required unless GAUSS syntax is also requested.
Response rule: the Econometrics Expert owns modeling/diagnostics logic; the Software Engineering Expert owns workflow decomposition and maintainability; clean organization is never evidence of methodological validity.

### 7. GAUSS + Econometrics + Software Engineering

When it applies: the task requires verified GAUSS implementation, methodological judgment, and maintainability/design guidance all at once.
Example: "Write GAUSS logistic regression code, structure it cleanly, and explain if logistic is appropriate."
Evidence/context pattern: the strictest applicable requirement from all three — GAUSS command evidence, methodological context, and design/behavior context — gathered independently; a gap in one is not offset by strength in another.
Response rule: keep implementation, methodology, and maintainability claims separate and separately attributable, even within one coherent response.

### 8. Neither

When it applies: the task is writing, project management, or release tracking, and has no GAUSS syntax issue, no statistical-methodology issue, and no code-quality issue.
Example: "Write a short release-note blurb."
Evidence/context pattern: none of the three experts' evidence/context requirements apply.
Response rule: answer normally; do not impose expert routing or decision rules from any of the three experts.

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

**For the Software Engineering Expert:**

- User goal
- Code or workflow description, when code review/refactor is requested
- Target language/context, if implementation-specific advice is requested
- Change intent: review, refactor, testing, organization, error handling, or design guidance

**When more than one expert activates:**

- Gather each activated expert's input set above, but do not block on every optional detail from any side.
- Ask a focused clarifying question only when missing information would materially change the answer, per `agents/code-assistant/task_modes.md`'s Clarifying Question Rules.
- Otherwise, state a clearly stated assumption for whichever side is underspecified (for example, "I'll assume your input is a numeric matrix" for the GAUSS side, "I'll assume this is a predictive, not causal, goal" for the econometrics side, or "I'll assume behavior should be preserved unless you say otherwise" for the software-engineering side).

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

**For the Software Engineering Expert**, use the Required Evidence / Context by Task Type table in `experts/software-engineering/OPERATIONAL_PROFILE.md`. Baseline rules, restated here but governed there:

- General design/maintainability guidance usually does not require official GAUSS command evidence or econometric context — the stated code/task context and goal are enough.
- If design guidance becomes a GAUSS-specific syntax claim (e.g., a recommended structure implies specific GAUSS constructs), route/escalate that claim to the GAUSS Language Expert rather than asserting it on this expert's own authority.
- If design guidance affects modeling interpretation (e.g., a workflow reorganization changes how a sample or estimator is applied), route/escalate that claim to the Econometrics Expert rather than asserting it on this expert's own authority.
- A claim that code was executed, tested, or run requires actual execution evidence; a recommended test is not a confirmed result.

**When more than one expert's evidence/context requirement applies:**

- Each expert's evidence/context requirement is separate. Meeting one does not satisfy another, and satisfying none is not offset by high confidence on any single side.
- If any side is missing, preserve uncertainty for that side only — do not let a fully-satisfied requirement on one side imply another side is also settled.
- The strictest applicable requirement wins: if a task touches GAUSS syntax, econometric methodology, and code quality at once, the response must clear all three bars, not just the highest-confidence one.

## Step 7 — Route to Retrieval or Clarification

- Route to `workflows/command-documentation-retrieval.md` when GAUSS command evidence is missing, then use `workflows/retrieval-backed-response-pattern.md` to handle the resulting state (`found_complete`, `found_incomplete`, `not_found`, `ambiguous`, `conflict`, `stale`, or `error`). Do not answer exact GAUSS syntax, defaults, or return values from memory while this is pending.
- Ask the user for methodological context when goal, design, outcome type, or data structure is missing and materially affects the recommendation.
- Ask the user for design context (code/task, goal, behavior-preservation constraints) when it is missing and materially affects a refactor or maintainability recommendation.
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

### Coordination rules

- The GAUSS Language Expert owns implementation correctness.
- The Econometrics Expert owns methodological correctness.
- The Software Engineering Expert owns maintainability/design correctness.
- Command availability is not methodological validity.
- Clean structure is not statistical validity.
- Syntax validity is not maintainability.
- Refactoring should preserve behavior unless a behavior change is explicitly requested.
- Testing recommendations are not execution claims.
- Pseudocode or unverified syntax must be labeled.
- All activated experts' claims must remain separable in substance, even when they do not need separate labeled sections in every response — this holds for two activated experts and continues to hold when all three activate.
- If one expert's side is uncertain (missing evidence, missing context), do not let confidence on another side mask that uncertainty. A verified GAUSS command, a sound methodology, and a clean refactor are three independent claims, not one combined verification.

## Step 9 — Produce Internal Routing Output

Use the output contract, extended for three experts:

- `task_classification`
- `routing_type` — one of `gauss_only`, `econometrics_only`, `software_engineering_only`, `gauss_and_econometrics`, `gauss_and_software_engineering`, `econometrics_and_software_engineering`, `all_three`, `neither`
- `activated_experts`
- `activation_reason_by_expert`
- `non_activation_reason_by_expert`, when relevant
- `evidence_needed_by_expert`
- `context_needed_by_expert`
- `evidence_or_context_used`
- `implementation_recommendation`
- `methodology_recommendation`
- `maintainability_recommendation`
- `refactor_or_design_recommendations`
- `testing_or_validation_recommendations`
- `conflicts_or_tensions`
- `response_constraints`
- `escalation_needed`

These fields remain internal by default. They do not need to appear as labels in the user-facing response — they are the internal structure the response should satisfy in substance, the same way a response satisfies `evaluations/scoring.md` dimensions without printing their names.

## Step 10 — Compose the User Response

The final response should:

- Answer the user naturally, without a forced expert-routing preamble.
- Show expert routing through correctness, evidence/context use, and uncertainty handling, not a literal "expert activated" label.
- Separate implementation, methodology, and maintainability claims when more than one matters, so none is misread as validating another.
- Cite or name GAUSS evidence when appropriate (a source file, a curated note, an official doc reference).
- State assumptions and caveats explicitly for methodology and design claims, the same way GAUSS-side assumptions are stated.
- Include validation suggestions (for generated/translated/debugged GAUSS code), diagnostic suggestions (for methodological recommendations), or testing/behavior-preservation notes (for refactor/design recommendations) when the task calls for one.
- Avoid overclaiming: never state or imply that GAUSS code was executed, that schema/structural validity is the same as semantic correctness, that a methodologically sound recommendation has been implementation-verified, or that a well-organized refactor has been confirmed to preserve behavior without actually checking.

## Step 11 — Evaluate Routing

Manual evaluation should check:

- Correct routing type (one of the eight in Step 4) for the task at hand.
- Correct expert activation, or correct non-activation, for each expert individually.
- Evidence threshold met for any exact GAUSS syntax/defaults/returns claim.
- Context threshold met for any methodological claim (goal, data structure, design support for causal claims, etc.).
- Context threshold met for any refactor/maintainability claim (behavior-preservation constraints, stated code/goal).
- No invented GAUSS syntax, procedures, or APIs.
- No unsupported causal or statistical-validity claims.
- No claim that clean code implies statistical or causal validity, or that valid syntax implies good design.
- No execution claims without actual execution.
- Uncertainty preserved on each activated side independently — one side being resolved does not paper over another being unresolved.
- No over-routing — the response does not apply GAUSS-specific, econometric, or software-engineering reasoning to a task from any expert's Non-Activation Cases list.
- Conflicts or tensions between activated experts' conclusions are surfaced when they exist, not silently resolved.
- Validation, diagnostic, or testing/behavior-preservation suggestions included where appropriate.

## Routing Examples

1. **GAUSS-only.** "What does `strindx` return when not found?" → GAUSS Language Expert only.
2. **Econometrics-only.** "Does p=0.03 mean the model explains 3%?" → Econometrics Expert only.
3. **Software-engineering-only.** "How should I refactor this generic duplicated pseudocode?" → Software Engineering Expert only; no GAUSS syntax and no methodology claim involved.
4. **GAUSS + Econometrics.** "Translate `lm()` to GAUSS and interpret the causal claim." → GAUSS Language Expert handles the translation and evidence-backed syntax; Econometrics Expert handles the causal interpretation, kept as a separate contribution rather than blended into the code explanation.
5. **GAUSS + Software Engineering.** "Refactor this GAUSS code with repeated blocks." → GAUSS Language Expert confirms/verifies any GAUSS syntax used in the refactor; Software Engineering Expert owns the decomposition/refactor strategy; unverified structure is labeled as pseudocode.
6. **Econometrics + Software Engineering.** "Organize my regression workflow with diagnostics and reporting." → Econometrics Expert owns the diagnostics/reporting content; Software Engineering Expert owns the workflow decomposition and maintainability; no GAUSS-specific syntax required.
7. **All three.** "Write GAUSS logistic regression code, structure it cleanly, and explain if logistic is appropriate." → GAUSS Language Expert verifies GAUSS implementation facts; Econometrics Expert addresses binary-outcome model appropriateness; Software Engineering Expert addresses code organization/testability; claims stay separate.
8. **Neither.** "Write a short release-note blurb." → No expert activates — release tracking, even when the changelog entries describe GAUSS-related, econometrics-related, or code-quality-related work.

## Relationship to Existing Files

- **`tools/operational_expert_interface.md`** — defines the generic interface (activation triggers, evidence/context requirements, decision rules, output contract, evaluation criteria) that this workflow routes against for all three experts. This workflow does not redefine that interface's fields.
- **`experts/gauss-language/OPERATIONAL_PROFILE.md`** — the filled-in GAUSS Language Expert profile this workflow's GAUSS-side steps are sourced from. If the profile changes, this workflow's GAUSS-side content should be updated to match rather than allowed to drift.
- **`experts/econometrics/OPERATIONAL_PROFILE.md`** — the filled-in Econometrics Expert profile this workflow's econometrics-side steps are sourced from, following the same drift-prevention principle.
- **`experts/software-engineering/OPERATIONAL_PROFILE.md`** — the filled-in Software Engineering Expert profile this workflow's software-engineering-side steps are sourced from, following the same drift-prevention principle. Added in `v0.14.0`.
- **`workflows/code-assistant-response.md`** — this workflow is the specialization of that document's Step 2 ("Identify Relevant Experts") for all three operational experts. Step 2 was updated in `v0.9.0` to reference this workflow's four-way routing, and updated again in `v0.14.0` to reference the eight-way routing and the Software Engineering Expert added here.
- **`workflows/retrieval-backed-response-pattern.md`** — governs Step 7's GAUSS-side evidence-state handling; this workflow does not redefine states A-H.
- **`workflows/command-documentation-retrieval.md`** — governs the hybrid discovery/retrieval strategy this workflow routes to in Step 7 for GAUSS command evidence.
- **`workflows/native-command-selection.md`** — governs the native-vs-manual decision this workflow's Step 8 GAUSS-side rules reference.
- **`agents/code-assistant/task_modes.md`** — the task-mode definitions consumed in Step 1 and the Clarifying Question Rules referenced in Step 5. Updated for multi-expert routing in `v0.9.0`, and updated again in `v0.14.0` so each task mode names the Software Engineering Expert's activation conditions alongside the other two experts'.
- **`prompts/code_assistant_system.md`** — the system prompt whose "Identify the relevant expertise" step this workflow operationalizes. Updated for multi-expert routing in `v0.9.0`, and updated again in `v0.14.0` to reference the Software Engineering Expert and the eight-way routing.

## Maintenance Notes

- Update this workflow when any `OPERATIONAL_PROFILE.md` changes, or when a new operational expert is added (extending Step 2's trigger lists, Step 3's non-activation lists, and Step 4's routing-type categories to cover it).
- Keep each expert's trigger/non-activation lists in this workflow aligned with its own `OPERATIONAL_PROFILE.md` — this workflow should mirror those profiles, never diverge from them.
- Benchmark category `16.x` (Multi-Expert Routing) tested GAUSS-only, econometrics-only, both-experts, and neither-expert routing, extending the single-expert coverage validated by `15.x` — completed and evaluated (all eight prompts passed) in `v0.9.0`.
- Benchmark category `21.x` (Software Engineering Expert Foundation), planned in `planning/v0.14.0-software-engineering-expert-foundation.md`, is intended to exercise the eight routing types documented here, including the five new combinations involving the Software Engineering Expert — not yet run as of this workflow update.
