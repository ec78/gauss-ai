# Expert Routing Workflow

## Purpose

This workflow replaces the vague "identify relevant experts" step currently in `workflows/code-assistant-response.md` and `prompts/code_assistant_system.md` with a checkable routing procedure: when to consult an operational expert, what to gather before applying its decision rules, and how to evaluate whether routing actually happened.

Clarifications:

- **It is not a runtime orchestration engine.** No code executes this workflow; it is followed the same way `workflows/native-command-selection.md` or `workflows/retrieval-backed-response-pattern.md` are followed today — as a documented reasoning procedure a response can be checked against.
- **It is a documented reasoning procedure for the Code Assistant**, not a new evidence system or a new set of decision rules — the rules it applies come from `experts/gauss-language/OPERATIONAL_PROFILE.md` and the evidence machinery already defined in `schemas/command_lookup_evidence.schema.json` and `workflows/retrieval-backed-response-pattern.md`.
- **It currently supports the GAUSS Language Expert as the first operational expert.** The Econometrics, Software Engineering, Documentation, and Education experts named in `workflows/code-assistant-response.md` remain narrative-only for now; this workflow's steps are written generically enough to extend to them later without a rewrite.
- **Future experts can be added using the same operational interface** (`tools/operational_expert_interface.md`) — a new expert needs an operational profile filled in against that interface, after which this workflow's Step 2 gains one more expert to check activation triggers against.

## Routing Principles

- Activate experts based on task/content triggers, not just keyword matching — a task can involve GAUSS without the word "GAUSS" appearing (e.g. "translate this R model" implies GAUSS as the target).
- Expert activation is internal by default; the Code Assistant does not need to announce which expert it consulted.
- Correct routing is evaluated through response behavior — whether decision rules were applied and evidence thresholds were honored — not through a self-reported label.
- Expert profiles add constraints and decision rules; they do not loosen evidence requirements. An expert can require more evidence than the general workflow demands, never less.
- Evidence requirements remain governed by the evidence schema (`schemas/command_lookup_evidence.schema.json`) and the retrieval-backed response pattern (`workflows/retrieval-backed-response-pattern.md`); this workflow routes *to* those, it does not redefine them.
- Non-activation cases matter as much as activation cases; do not over-route to GAUSS expertise for tasks that do not need it. Unnecessary activation is itself a routing failure, not a safe default.

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

For each task, identify whether the answer will involve:

- GAUSS code
- GAUSS syntax
- GAUSS command/procedure selection
- GAUSS data-structure choice
- Package/base-GAUSS distinction
- Version-sensitive GAUSS behavior
- Cross-language translation into or out of GAUSS
- Hallucination risk around GAUSS (an unfamiliar command name, or a cross-language idiom appearing where GAUSS syntax is expected)

This step is the same task classification already required by `workflows/code-assistant-response.md` Step 1 and `prompts/code_assistant_system.md`'s "Classify the task" step; it is not a new classification pass, only the input this workflow's routing decision consumes.

## Step 2 — Match Activation Triggers

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

## Step 3 — Check Non-Activation Cases

Do not activate the GAUSS Language Expert for:

- General writing unrelated to GAUSS
- Release tracking
- Changelog drafting
- Readiness-checklist bookkeeping
- General project management
- Generic statistics/econometrics explanations with no GAUSS implementation
- Non-GAUSS conceptual explanations, unless a GAUSS implementation is also requested

Negative routing is part of correctness, not an afterthought. A response that applies GAUSS-specific decision rules and evidence requirements to a task that never needed them is a routing failure in the same way a missed activation is — it adds unrequested scope, and evaluation (Step 10) checks for it explicitly.

## Step 4 — Gather Required Inputs

Before applying the expert profile, identify:

- Task mode
- User intent
- Code snippet or command name, when present
- Source language, for translation tasks
- Requested output type
- Available evidence/retrieval context
- Known GAUSS version, if the task is version-sensitive

If required inputs are missing:

- Ask a focused clarifying question when the missing information would materially change the answer, per `agents/code-assistant/task_modes.md`'s Clarifying Question Rules, or
- Proceed with a clearly stated assumption if a safe one exists and is consistent with the profile (for example, "I'll assume your input is a numeric matrix" from the existing task-modes guidance).

## Step 5 — Determine Evidence Needed

Use the Required Evidence by Task Type table in `experts/gauss-language/OPERATIONAL_PROFILE.md`. Baseline rules, restated here for quick reference but governed there:

- Exact syntax/defaults/returns require `source_authority: official_docs` or `official_package_docs` evidence.
- Category lists (`source_authority: category_list`) support discovery only.
- Curated notes (`source_authority: curated_command_note`) cannot override official docs.
- Stale evidence (`stale_evidence.is_stale: true`) must be disclosed, not silently treated as current.
- Ambiguous evidence (`retrieval_status: ambiguous`) requires disambiguation.
- Conflicting evidence (`retrieval_status: conflict`) resolves in favor of official evidence.
- Schema validity (a file passing `scripts/validate_lookup_evidence.py` or `scripts/validate_all_evidence.py`) does not prove GAUSS semantic correctness or that any GAUSS code was executed.

## Step 6 — Route to Retrieval When Needed

If command-specific evidence is required but not yet available:

- Route to `workflows/command-documentation-retrieval.md` for the hybrid discovery/retrieval strategy (categories for discovery, official docs for syntax, curated notes as a small cache).
- Use `workflows/retrieval-backed-response-pattern.md` to handle the resulting state: `found_complete`, `found_incomplete`, `not_found`, `ambiguous`, `conflict`, `stale`, or `error`.
- Do not answer exact syntax, defaults, or return values from memory while this step is pending — either complete the retrieval or state plainly that verification is needed.

## Step 7 — Apply Expert Decision Rules

Apply the GAUSS Language Expert's decision rules from `experts/gauss-language/OPERATIONAL_PROFILE.md`:

- No invented GAUSS syntax, packages, procedures, or APIs.
- Prefer official-doc-backed command evidence for exact syntax, defaults, and return values.
- Curated notes are subordinate to official evidence.
- Prefer verified native GAUSS procedures when appropriate.
- Use manual matrix implementations only in the allowed cases (teaching, customization, no suitable native command, intentionally transparent examples).
- Distinguish matrix, DataFrame, array, scalar, string, and structure usage.
- State package dependencies when package-specific functions are used.
- No execution claims without an actual execution.
- Preserve uncertainty when evidence is incomplete, stale, ambiguous, or conflicting.
- Identify cross-language contamination.
- Handle version-sensitive choices with current evidence, disclosing staleness where it applies.
- Provide a validation suggestion where the task calls for one.

## Step 8 — Produce Expert Output Internally

Use the output contract from `experts/gauss-language/OPERATIONAL_PROFILE.md`:

- `task_classification`
- `activation_reason`
- `activated_knowledge_domains`
- `evidence_needed`
- `evidence_used`
- `verified_facts`
- `decision_recommendation`
- `risks_or_uncertainties`
- `response_constraints`
- `validation_suggestions`

These fields do not need to appear as labels in the user-facing response. They are the internal structure the response should satisfy in substance — the same way a response satisfies `evaluations/scoring.md` dimensions without printing their names.

## Step 9 — Compose the User Response

The final response should:

- Answer the user naturally, without a forced expert-routing preamble.
- Show expert routing through correctness, evidence use, and uncertainty handling.
- Avoid unnecessary "expert activated" labels.
- Cite or name evidence when appropriate (a source file, a curated note, an official doc reference).
- Include validation suggestions for generated, translated, or debugged GAUSS code.
- Avoid overclaiming what schema validation or evidence review proves — never state or imply that GAUSS code was executed, or that structural validity is the same as semantic correctness.

## Step 10 — Evaluate Routing

Manual evaluation should check:

- Correct expert activation, or correct non-activation, for the task at hand.
- Evidence threshold met for any exact syntax/defaults/returns claim.
- Decision rules applied, visibly, in substance.
- Uncertainty preserved for incomplete, stale, ambiguous, or conflicting evidence.
- No invented syntax, procedures, or APIs.
- No false execution claim.
- Validation suggestions included when the task required one.
- The response does not over-route — it does not apply GAUSS-specific reasoning to a task from the Non-Activation Cases list.

## Routing Examples

1. **R-to-GAUSS regression translation.** Activate the GAUSS Language Expert (Code Translation trigger). Route to retrieval for the native `olsmt` procedure per Step 6 rather than defaulting to manual matrix OLS; include a validation step comparing `out.b` against R's `coef(model)`.
2. **Python-style `.find()` used in GAUSS string code.** Activate the expert (Debugging + cross-language-idiom trigger). Retrieve or verify `strindx`'s not-found return value (`0`, not `-1`) before presenting the fix.
3. **Choosing between `qnewtonmt` and `minimize` for an optimization task.** Activate the expert (version-sensitive-choice trigger). Present both as valid native options, using current, non-stale evidence for each, and disclose if either evidence source is stale rather than picking one silently.
4. **Changelog update for `v0.8.0`.** Do not activate the GAUSS Language Expert — this is release tracking, a Non-Activation Case, even though the changelog entries mention GAUSS-related work.
5. **Generic explanation of OLS with no GAUSS code requested.** Do not activate the GAUSS Language Expert — this is econometric methodology without a GAUSS implementation request; it would route to the Econometrics Expert's domain instead, per `experts/gauss-language/OPERATIONAL_PROFILE.md`'s Escalation Conditions.
6. **DataFrame vs. matrix design question.** Activate the expert (data-structure-choice trigger). Use `BODY_OF_KNOWLEDGE.md` decision guidance directly; this evidence class does not require command-specific retrieval.
7. **Ambiguous command evidence (multiple plausible documentation matches).** Activate the expert, then escalate the ambiguity to the user per `workflows/retrieval-backed-response-pattern.md` state D, rather than silently picking the higher-confidence candidate or inventing syntax to resolve it.

## Relationship to Existing Files

- **`tools/operational_expert_interface.md`** — defines the generic interface (activation triggers, evidence requirements, decision rules, output contract, evaluation criteria) that this workflow routes against. This workflow does not redefine that interface's fields.
- **`experts/gauss-language/OPERATIONAL_PROFILE.md`** — the filled-in profile this workflow's Steps 2, 5, 7, and 8 are sourced from. If the profile changes, this workflow's step content should be updated to match rather than allowed to drift.
- **`workflows/code-assistant-response.md`** — this workflow is the specialization of that document's Step 2 ("Identify Relevant Experts") for the GAUSS Language Expert; the general response workflow still governs task classification, retrieval need, and response composition around it.
- **`workflows/retrieval-backed-response-pattern.md`** — governs Step 6 and the evidence-state handling this workflow routes to; this workflow does not redefine states A-H.
- **`workflows/command-documentation-retrieval.md`** — governs the hybrid discovery/retrieval strategy this workflow routes to in Step 6.
- **`workflows/native-command-selection.md`** — governs the native-vs-manual decision this workflow's Step 7 decision rules 4-5 reference.
- **`agents/code-assistant/task_modes.md`** — the task-mode definitions consumed in Step 1 and the Clarifying Question Rules referenced in Step 4.
- **`prompts/code_assistant_system.md`** — the system prompt whose "Identify the relevant expertise" step this workflow operationalizes; not yet updated to reference this workflow (see Suggested Next Task).

## Maintenance Notes

Update this workflow when `experts/gauss-language/OPERATIONAL_PROFILE.md` changes, when a new expert's operational profile is added (extending Step 2's trigger list and Step 3's non-activation list to cover it), or when benchmark evaluations (planned as category 15.x, "Expert Routing") reveal a routing failure mode not yet covered by Step 10.
