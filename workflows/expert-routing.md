# Expert Routing Workflow

## Purpose

This workflow routes Code Assistant tasks through operational experts. It replaces the vague "identify relevant experts" step in `workflows/code-assistant-response.md` and `prompts/code_assistant_system.md` with a checkable routing procedure: when to consult one or more operational experts, what to gather before applying their decision rules, and how to evaluate whether routing actually happened.

It now supports four operational experts:

- **GAUSS Language Expert** — implementation correctness.
- **Econometrics Expert** — methodological correctness.
- **Software Engineering Expert** — maintainability/design correctness.
- **Documentation Expert** — documentation/explanation correctness.

Clarifications:

- **It is not a runtime orchestration engine.** No code executes this workflow; it is followed the same way `workflows/native-command-selection.md` or `workflows/retrieval-backed-response-pattern.md` are followed today — as a documented reasoning procedure a response can be checked against. Nothing in this update introduces multi-expert *execution* machinery; it extends the documented reasoning procedure from three operational experts to four, the same way `v0.14.0` extended it from two to three.
- **It is a documented reasoning procedure for the Code Assistant**, not a new evidence system or a new set of decision rules — the rules it applies come from `experts/gauss-language/OPERATIONAL_PROFILE.md`, `experts/econometrics/OPERATIONAL_PROFILE.md`, `experts/software-engineering/OPERATIONAL_PROFILE.md`, `experts/documentation/OPERATIONAL_PROFILE.md`, and the evidence machinery already defined in `schemas/command_lookup_evidence.schema.json` and `workflows/retrieval-backed-response-pattern.md`.
- **This is deliberately not a full 16-combination routing engine.** With four experts, a fully enumerated activation table would have 2⁴ = 16 rows. Step 4 below documents the most common patterns (a compact activation matrix plus worked examples) rather than exhaustively enumerating every possible subset. Any combination of the four experts may activate; the coordination principles below (claims stay separable, strictest evidence/context requirement wins) govern any combination, including ones without their own named row or worked example.
- **The Education and Product experts named in `workflows/code-assistant-response.md` remain fully narrative-only for now** — no operational profile exists for either. **The Documentation Expert is operationalized as of `v0.15.0`** (`experts/documentation/OPERATIONAL_PROFILE.md`), documented here, and integrated into `workflows/code-assistant-response.md`, `agents/code-assistant/task_modes.md`, and `prompts/code_assistant_system.md`.
- **Future experts can be added using the same operational interface** (`tools/operational_expert_interface.md`) — a new expert needs an operational profile filled in against that interface, after which this workflow's activation-trigger and non-activation steps gain one more expert to check against, and Step 4's activation matrix gains one more column, the same way the Documentation Expert's addition here expanded the matrix from an eight-type enumeration to a twelve-pattern compact table over four axes.

## Operational Experts Currently Supported

| Expert | Owns | Does not own |
|---|---|---|
| GAUSS Language Expert | GAUSS syntax, command selection, data structures, package/base distinction, implementation correctness | Econometric methodology or statistical validity; code maintainability/design; documentation clarity |
| Econometrics Expert | Model choice, assumptions, diagnostics, interpretation, causal/predictive framing, statistical validity | Exact GAUSS syntax, command return fields, package/base distinction; code maintainability/design; documentation clarity |
| Software Engineering Expert | Code quality, maintainability, modularity, readability, refactoring, testability, error handling, edge-case thinking, safe change management | Exact GAUSS syntax, command evidence, package/base distinction; econometric methodology or statistical validity; documentation clarity |
| Documentation Expert | Documentation clarity, reference structure, examples, comments/docstrings, usage guidance, input/output explanation, warnings/caveats, troubleshooting guidance, terminology consistency, audience awareness, documentation completeness | Exact GAUSS syntax, command evidence; econometric methodology or statistical validity; code maintainability/design; curriculum/instructional sequencing |

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

## Routing Principles

- Activate experts based on task/content triggers, not just keyword matching — a task can involve GAUSS, econometrics, code quality, or documentation without any of those words appearing (e.g. "translate this R model" implies GAUSS as the target; "does this coefficient mean X causes Y" implies econometric interpretation; "this script is a mess" implies a maintainability concern; "I can't tell what this function expects" implies a documentation concern).
- Expert activation is internal by default; the Code Assistant does not need to announce which expert(s) it consulted.
- Correct routing is evaluated through response behavior — whether decision rules were applied and evidence/context thresholds were honored — not through a self-reported label.
- Expert profiles add constraints and decision rules; they do not loosen evidence requirements. An expert can require more evidence than the general workflow demands, never less.
- Evidence requirements for GAUSS claims remain governed by the evidence schema (`schemas/command_lookup_evidence.schema.json`) and the retrieval-backed response pattern (`workflows/retrieval-backed-response-pattern.md`); this workflow routes *to* those, it does not redefine them.
- Non-activation cases matter as much as activation cases; do not over-route to any expert for tasks that do not need them. Unnecessary activation is itself a routing failure, not a safe default.
- Different experts own different kinds of correctness: GAUSS syntax correctness (implementation), econometric validity (methodology), software maintainability (design), and documentation clarity (explanation) are four separate claims, and no expert may answer for another's domain.
- Command availability is not methodological validity — a GAUSS command existing for a method is never evidence the method is the right choice for the user's data.
- Methodological appropriateness is not implementation evidence — a method being the right statistical choice is never evidence that specific GAUSS syntax exists or works as described.
- Valid GAUSS code can still be poorly designed — syntactic validity and good design are independent claims.
- Clean code can still be statistically invalid — code quality and methodological soundness are independent claims.
- A methodologically appropriate analysis can still be poorly implemented or hard to maintain — methodological validity and maintainability are independent claims.
- Clear documentation does not prove code correctness, statistical validity, or maintainability — documentation clarity is an independent claim from all three.
- Valid GAUSS code may still be poorly documented; a methodologically correct analysis may still be poorly documented; well-designed code may still need better documentation — documentation quality never follows automatically from the other three.
- The Software Engineering Expert may recommend structure but cannot invent GAUSS syntax to implement it; unverified structural suggestions must be labeled as pseudocode.
- The Software Engineering Expert may recommend tests or checks but cannot claim code was executed or a test was run unless it actually was.
- The Documentation Expert may improve wording, examples, and user-facing structure but cannot invent GAUSS syntax; any example must use verified syntax or be labeled pseudocode/unverified.
- The Documentation Expert may clarify statistical caveats for a reader but cannot certify methodology; it may write comments/docstrings but cannot certify code design.
- The Documentation Expert is distinct from the (not-yet-operationalized) Education Expert: documentation supports task completion and reference use right now, while education supports learning over time through sequencing, scaffolding, exercises, and pedagogy. Making a single piece of documentation beginner-friendly is not curriculum design.
- When multiple experts activate, keep implementation, methodology, maintainability, and documentation claims separate in substance, even when the final response reads as one coherent answer.
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

Add a second classification pass, independent of task mode, that this workflow's routing decision actually consumes. Answer four independent questions about the task — each is a yes/no judgment, not a single label, since a task can be "yes" on more than one axis at once:

1. **GAUSS implementation axis** — does the answer turn on GAUSS syntax, command selection, or language mechanics? Examples: GAUSS syntax, command usage, package/base distinction, DataFrame/matrix/structure usage, GAUSS code generation/debugging.
2. **Econometric methodology axis** — does the answer turn on model/estimator choice, assumptions, diagnostics, or interpretation? Examples: estimator choice, assumptions, diagnostics, causal interpretation, forecasting/statistical evaluation, panel/time-series/cross-sectional modeling.
3. **Software engineering/code-quality axis** — does the answer turn on code organization, maintainability, or safe change management? Examples: refactoring, code review, maintainability, readability, modularity, testability, error handling, edge cases, duplication, safe change management.
4. **Documentation/explanation-quality axis** — does the answer turn on how clearly something is explained, structured, or documented for a reader? Examples: writing or improving docs, reference structure, examples, comments/docstrings, usage notes, parameter/return explanations, troubleshooting guidance, warnings/caveats, README/help text, audience clarity, terminology consistency.

The combination of the four yes/no answers determines the routing pattern in Step 4.

Examples:

- "What is the exact syntax for `olsmt`?" → GAUSS implementation only.
- "Is OLS appropriate for this causal question?" → econometric methodology only.
- "How should I refactor this generic duplicated pseudocode?" → software engineering only.
- "Rewrite this technical note into clearer user-facing documentation." → documentation only.
- "Translate this regression into GAUSS and tell me what diagnostics to run" → GAUSS implementation + econometric methodology.
- "Document this GAUSS procedure and include a usage example." → GAUSS implementation + documentation.
- "Document the assumptions and interpretation caveats for this regression output." → econometric methodology + documentation.
- "Add comments/docstrings explaining the design intent of this helper function." → software engineering + documentation.
- "Write GAUSS logistic regression code, structure it cleanly, explain if logistic is appropriate, and document it for users." → all four axes.
- "Write a changelog entry" → none of the four axes.

This step is the same task-mode classification already required by `workflows/code-assistant-response.md` Step 1 and `prompts/code_assistant_system.md`'s "Classify the task" step, with the four-axis pass added specifically for this workflow's routing decision — it is not a new classification pass end to end.

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

### None of the four

Do not activate any expert for tasks such as:

- Changelog entries
- Release readiness notes
- General project tracking
- Repository housekeeping with no GAUSS syntax, no statistical-methodology question, no code-quality question, and no documentation-clarity question

Negative routing is part of correctness, not an afterthought, for each expert individually and for the none-of-the-four case. A response that applies GAUSS-specific, econometric, software-engineering, or documentation decision rules and evidence/context requirements to a task that never needed them is a routing failure in the same way a missed activation is — it adds unrequested scope, and evaluation (Step 11) checks for it explicitly.

## Step 4 — Determine the Routing Pattern

Any subset of the four operational experts may activate — this step does not enumerate all 16 mathematically possible combinations as a combinatorial routing engine. Instead, it gives a compact activation matrix covering the most common patterns, plus the coordination principles (above) that govern any combination, including ones without their own named row.

### Activation Matrix

| Pattern | GAUSS Language | Econometrics | Software Engineering | Documentation | Typical request | Response rule |
|---|:---:|:---:|:---:|:---:|---|---|
| 1. GAUSS-only | ✓ | | | | "What does `strindx` return when not found?" | Answer from verified evidence only. |
| 2. Econometrics-only | | ✓ | | | "Does p=0.03 mean the model explains 3%?" | Answer from methodological reasoning only. |
| 3. Software-engineering-only | | | ✓ | | "How should I refactor this generic duplicated pseudocode?" | Answer from design reasoning only; label unverified structure as pseudocode. |
| 4. Documentation-only | | | | ✓ | "Rewrite this technical note into clearer user-facing documentation." | Answer from documentation reasoning only; no syntax/methodology/design claims needed. |
| 5. GAUSS + Documentation | ✓ | | | ✓ | "Document this GAUSS procedure and include a usage example." | GAUSS Language Expert owns syntax/example validity; Documentation Expert owns explanation/structure/clarity. |
| 6. Econometrics + Documentation | | ✓ | | ✓ | "Document the assumptions and interpretation caveats for this regression output." | Econometrics Expert owns assumption/interpretation correctness; Documentation Expert owns clarity and caveat placement. |
| 7. Software Engineering + Documentation | | | ✓ | ✓ | "Add comments/docstrings explaining the design intent of this helper function." | Software Engineering Expert owns design intent; Documentation Expert owns comment/docstring clarity. |
| 8. GAUSS + Software Engineering + Documentation | ✓ | | ✓ | ✓ | "Refactor this GAUSS procedure and document its inputs/outputs." | GAUSS Language Expert verifies syntax; Software Engineering Expert owns refactor strategy; Documentation Expert owns the resulting explanation. |
| 9. GAUSS + Econometrics + Documentation | ✓ | ✓ | | ✓ | "Show GAUSS logistic regression syntax and document model assumptions for users." | GAUSS Language Expert verifies implementation facts; Econometrics Expert owns assumption correctness; Documentation Expert owns reader-facing structure. |
| 10. GAUSS + Econometrics + Software Engineering | ✓ | ✓ | ✓ | | "Write GAUSS logistic regression code, structure it cleanly, and explain if logistic is appropriate." | Claims stay separate per `v0.14.0`'s three-expert pattern; no documentation-specific deliverable requested. |
| 11. All four | ✓ | ✓ | ✓ | ✓ | "Write GAUSS logistic regression code, structure it cleanly, explain appropriateness, and document it for users." | All four claims (implementation, methodology, maintainability, documentation) stay separate and separately attributable. |
| 12. Neither | | | | | "Write a nontechnical marketing blurb." | Answer normally; do not impose expert routing or decision rules from any of the four. |

Two combinations from the prior eight-type enumeration — **GAUSS + Econometrics** (no Software Engineering, no Documentation) and **Econometrics + Software Engineering** (no GAUSS, no Documentation) — are not repeated as their own matrix rows here, since they involve no documentation dimension and are already fully covered by the `v0.14.0` worked examples in Routing Examples below. The matrix's job is to make the *new* fourth axis and its most common interactions readable; it is not a replacement for those existing patterns.

For a pattern that matches none of the twelve rows above (for example, Econometrics + Software Engineering + Documentation with no GAUSS involved), apply the general coordination principles: identify which axes are genuinely "yes" per Step 1, activate exactly those experts, gather each one's required evidence/context independently (Step 6), and keep each activated expert's claim separable in the response (Step 10) — the same discipline the twelve named patterns follow, just without a dedicated row.

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

**When more than one expert activates:**

- Gather each activated expert's input set above, but do not block on every optional detail from any side.
- Ask a focused clarifying question only when missing information would materially change the answer, per `agents/code-assistant/task_modes.md`'s Clarifying Question Rules.
- Otherwise, state a clearly stated assumption for whichever side is underspecified (for example, "I'll assume your input is a numeric matrix" for the GAUSS side, "I'll assume this is a predictive, not causal, goal" for the econometrics side, "I'll assume behavior should be preserved unless you say otherwise" for the software-engineering side, or "I'll assume this is for an experienced GAUSS user unless you tell me otherwise" for the documentation side).

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

**When more than one expert's evidence/context requirement applies:**

- Each expert's evidence/context requirement is separate. Meeting one does not satisfy another, and satisfying none is not offset by high confidence on any single side.
- If any side is missing, preserve uncertainty for that side only — do not let a fully-satisfied requirement on one side imply another side is also settled.
- The strictest applicable requirement wins: if a task touches GAUSS syntax, econometric methodology, code quality, and documentation clarity at once, the response must clear all four bars, not just the highest-confidence one.

## Step 7 — Route to Retrieval or Clarification

- Route to `workflows/command-documentation-retrieval.md` when GAUSS command evidence is missing, then use `workflows/retrieval-backed-response-pattern.md` to handle the resulting state (`found_complete`, `found_incomplete`, `not_found`, `ambiguous`, `conflict`, `stale`, or `error`). Do not answer exact GAUSS syntax, defaults, or return values from memory while this is pending.
- Ask the user for methodological context when goal, design, outcome type, or data structure is missing and materially affects the recommendation.
- Ask the user for design context (code/task, goal, behavior-preservation constraints) when it is missing and materially affects a refactor or maintainability recommendation.
- Ask the user for documentation context (intended reader, documentation type, source material) when it is missing and materially affects the resulting documentation.
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

### Coordination rules

- The GAUSS Language Expert owns implementation correctness.
- The Econometrics Expert owns methodological correctness.
- The Software Engineering Expert owns maintainability/design correctness.
- The Documentation Expert owns documentation/explanation correctness.
- Command availability is not methodological validity.
- Clean structure is not statistical validity.
- Syntax validity is not maintainability.
- Clear documentation is not implementation correctness.
- Clear documentation is not statistical validity.
- Clear documentation is not maintainability.
- Examples used in documentation must use verified syntax or be labeled pseudocode/unverified.
- Documentation should not replace Education Expert/curriculum design.
- Documentation should not replace Product Expert/positioning strategy.
- Refactoring should preserve behavior unless a behavior change is explicitly requested.
- Testing recommendations are not execution claims.
- Pseudocode or unverified syntax must be labeled.
- All activated experts' claims must remain separable in substance, even when they do not need separate labeled sections in every response — this holds for two activated experts and continues to hold when three or all four activate.
- If one expert's side is uncertain (missing evidence, missing context), do not let confidence on another side mask that uncertainty. A verified GAUSS command, a sound methodology, a clean refactor, and clear documentation are four independent claims, not one combined verification.

## Step 9 — Produce Internal Routing Output

Use the output contract, extended for four experts:

- `task_classification`
- `routing_pattern` — the matched pattern from Step 4's activation matrix (e.g. `gauss_only`, `documentation_only`, `gauss_and_documentation`, `all_four`, `neither`), or a description of the active expert subset when it doesn't match a named pattern
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
- `refactor_or_design_recommendations`
- `testing_or_validation_recommendations`
- `documentation_structure_recommendations`
- `example_or_usage_recommendations`
- `warning_or_caveat_recommendations`
- `conflicts_or_tensions`
- `response_constraints`
- `escalation_needed`

These fields remain internal by default. They do not need to appear as labels in the user-facing response — they are the internal structure the response should satisfy in substance, the same way a response satisfies `evaluations/scoring.md` dimensions without printing their names.

## Step 10 — Compose the User Response

The final response should:

- Answer the user naturally, without a forced expert-routing preamble.
- Show expert routing through correctness, evidence/context use, and uncertainty handling, not a literal "expert activated" label.
- Separate implementation, methodology, maintainability, and documentation claims when more than one matters, so none is misread as validating another.
- Cite or name GAUSS evidence when appropriate (a source file, a curated note, an official doc reference).
- State assumptions and caveats explicitly for methodology, design, and documentation claims, the same way GAUSS-side assumptions are stated.
- Include validation suggestions (for generated/translated/debugged GAUSS code), diagnostic suggestions (for methodological recommendations), testing/behavior-preservation notes (for refactor/design recommendations), or structure/clarity suggestions (for documentation recommendations) when the task calls for one.
- Avoid overclaiming: never state or imply that GAUSS code was executed, that schema/structural validity is the same as semantic correctness, that a methodologically sound recommendation has been implementation-verified, that a well-organized refactor has been confirmed to preserve behavior without actually checking, or that clear documentation confirms correctness, validity, or maintainability.

## Step 11 — Evaluate Routing

Manual evaluation should check:

- Correct routing pattern (per Step 4's activation matrix and coordination principles) for the task at hand.
- Correct expert activation, or correct non-activation, for each expert individually.
- Evidence threshold met for any exact GAUSS syntax/defaults/returns claim.
- Context threshold met for any methodological claim (goal, data structure, design support for causal claims, etc.).
- Context threshold met for any refactor/maintainability claim (behavior-preservation constraints, stated code/goal).
- Context threshold met for any documentation claim (intended reader, documentation type, source material).
- No invented GAUSS syntax, procedures, or APIs.
- No unsupported causal or statistical-validity claims.
- No claim that clean code implies statistical or causal validity, or that valid syntax implies good design.
- No claim that documentation clarity implies GAUSS syntax correctness, statistical validity, or maintainability.
- No execution claims without actual execution.
- Uncertainty preserved on each activated side independently — one side being resolved does not paper over another being unresolved.
- No over-routing — the response does not apply GAUSS-specific, econometric, software-engineering, or documentation reasoning to a task from any expert's Non-Activation Cases list.
- Conflicts or tensions between activated experts' conclusions are surfaced when they exist, not silently resolved.
- Validation, diagnostic, testing/behavior-preservation, or documentation-structure suggestions included where appropriate.

## Routing Examples

The first eight examples below predate the Documentation Expert (`v0.9.0`-`v0.14.0`) and are kept as concise one-line references. The eight after them are new for `v0.15.0` and use an expanded format (request, activated experts, why, response rule, key boundary) to make the Documentation Expert's boundaries explicit.

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

15. **All four.**
    - Request: "Write GAUSS logistic regression code, structure it cleanly, explain appropriateness, and document it for users."
    - Activated experts: GAUSS Language Expert, Econometrics Expert, Software Engineering Expert, Documentation Expert.
    - Why: implementation, methodology, maintainability, and documentation are all genuinely in play.
    - Response rule: keep all four claims separate and separately attributable, even within one coherent response; use local evidence (e.g. `glm.evidence.json`) for implementation facts.
    - Key boundary: does not claim execution; does not invent syntax; does not let clean code or clear documentation imply model validity.

16. **Documentation Expert does not replace Education Expert.**
    - Request: "Give beginners a six-week curriculum to learn econometrics in GAUSS."
    - Activated experts: none of the four operational experts in their full sense — this is Education Expert territory, and the Education Expert is not yet operationalized.
    - Why: multi-session sequencing, scaffolding, and pedagogy are explicitly out of the Documentation Expert's scope.
    - Response rule: handle as general education/planning help, or state explicitly that this is future Education Expert territory; the Documentation Expert may support individual reference-doc clarity within such a plan but must not claim ownership of the curriculum design itself.
    - Key boundary: does not overclaim Education Expert operationalization, and does not let documentation guidance substitute for a learning design.

## Relationship to Existing Files

- **`tools/operational_expert_interface.md`** — defines the generic interface (activation triggers, evidence/context requirements, decision rules, output contract, evaluation criteria) that this workflow routes against for all four experts. This workflow does not redefine that interface's fields.
- **`experts/gauss-language/OPERATIONAL_PROFILE.md`** — the filled-in GAUSS Language Expert profile this workflow's GAUSS-side steps are sourced from. If the profile changes, this workflow's GAUSS-side content should be updated to match rather than allowed to drift.
- **`experts/econometrics/OPERATIONAL_PROFILE.md`** — the filled-in Econometrics Expert profile this workflow's econometrics-side steps are sourced from, following the same drift-prevention principle.
- **`experts/software-engineering/OPERATIONAL_PROFILE.md`** — the filled-in Software Engineering Expert profile this workflow's software-engineering-side steps are sourced from, following the same drift-prevention principle. Added in `v0.14.0`.
- **`experts/documentation/OPERATIONAL_PROFILE.md`** — the filled-in Documentation Expert profile this workflow's documentation-side steps are sourced from, following the same drift-prevention principle. Added in `v0.15.0`.
- **`workflows/code-assistant-response.md`** — this workflow is the specialization of that document's Step 2 ("Identify Relevant Experts"). Step 2 was updated in `v0.9.0` to reference two-expert routing, again in `v0.14.0` to reference three-expert, eight-pattern routing, and again in `v0.15.0` to reference the Documentation Expert and the four-axis routing pattern added here.
- **`workflows/retrieval-backed-response-pattern.md`** — governs Step 7's GAUSS-side evidence-state handling; this workflow does not redefine states A-H.
- **`workflows/command-documentation-retrieval.md`** — governs the hybrid discovery/retrieval strategy this workflow routes to in Step 7 for GAUSS command evidence.
- **`workflows/native-command-selection.md`** — governs the native-vs-manual decision this workflow's Step 8 GAUSS-side rules reference.
- **`agents/code-assistant/task_modes.md`** — the task-mode definitions consumed in Step 1 and the Clarifying Question Rules referenced in Step 5. Updated for multi-expert routing in `v0.9.0`, again in `v0.14.0` for the Software Engineering Expert, and again in `v0.15.0` so each task mode names the Documentation Expert's activation conditions alongside the other three experts'.
- **`prompts/code_assistant_system.md`** — the system prompt whose "Identify the relevant expertise" step this workflow operationalizes. Updated for multi-expert routing in `v0.9.0`, again in `v0.14.0` for the Software Engineering Expert, and again in `v0.15.0` to reference the Documentation Expert and the four-axis routing pattern.

## Maintenance Notes

- Update this workflow when any `OPERATIONAL_PROFILE.md` changes, or when a new operational expert is added (extending Step 2's trigger lists, Step 3's non-activation lists, and Step 4's activation matrix to cover it).
- Keep each expert's trigger/non-activation lists in this workflow aligned with its own `OPERATIONAL_PROFILE.md` — this workflow should mirror those profiles, never diverge from them.
- Benchmark category `16.x` (Multi-Expert Routing) tested GAUSS-only, econometrics-only, both-experts, and neither-expert routing, extending the single-expert coverage validated by `15.x` — completed and evaluated (all eight prompts passed) in `v0.9.0`.
- Benchmark category `21.x` (Software Engineering Expert Foundation) exercised the eight routing types that existed before this update, including the five combinations involving the Software Engineering Expert — completed and evaluated (all eight prompts passed) in `v0.14.0`.
- Benchmark category `22.x` (Documentation Expert Foundation), planned in `planning/v0.15.0-documentation-expert-foundation.md`, is intended to exercise the Documentation Expert and the new documentation-related patterns documented here — not yet run as of this workflow update.
