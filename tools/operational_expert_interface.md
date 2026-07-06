# Operational Expert Interface

## Purpose

This document defines how an expert module becomes *operational*: when it activates, what inputs it needs, what evidence it requires before making claims, what decision rules it applies, what it contributes back to the Code Assistant's response, and how that contribution can be checked.

Clarifications:

- **This is not a runtime API.** No code parses or executes the fields defined here. There is no expert runtime engine in `v0.8.0` and none is planned by this document.
- **It is a documentation contract for manual evaluation and prompt/workflow integration.** A response either does or does not satisfy a given expert's filled-in interface, and that can be checked by reading the response the same way `evaluations/scoring.md` dimensions are checked today — by a human evaluator inspecting content, not by an automated harness inspecting internal state.
- **It is reusable for future experts.** `experts/gauss-language/OPERATIONAL_PROFILE.md` is the first profile built on this interface. The Econometrics, Software Engineering, Documentation, and Education experts named in `workflows/code-assistant-response.md` can use the same shape later without redesigning it.

## Design Principles

- **Experts add domain-specific constraints; they do not loosen existing retrieval or evidence requirements.** An operational profile may require *more* evidence than the general workflow demands for a given claim, never less.
- **Experts consume the evidence schema and retrieval-backed response states; they do not create a competing evidence system.** Every evidence reference in an operational profile should resolve to a concept already defined in `schemas/command_lookup_evidence.schema.json` or `workflows/retrieval-backed-response-pattern.md`, not a new parallel vocabulary.
- **Expert activation is internal by default.** The Code Assistant is not expected to print "GAUSS Language Expert activated" in the user-facing response. The expert's reasoning shapes the response; it does not need to announce itself.
- **Expert routing should be visible through response quality, not necessarily through a literal label.** A correctly-routed response looks like one where the applicable decision rules were followed and the required evidence threshold was met — that is what an evaluator checks for, not a self-reported tag.
- **Expert profiles should reference source docs rather than duplicate large bodies of knowledge.** An operational profile points at `BODY_OF_KNOWLEDGE.md`, `COMMAND_CATEGORIES.md`, curated command notes, and the retrieval workflows; it does not re-explain their content inline.
- **Expert output should be checkable by manual evaluation.** Every field in the output contract (see below) should be answerable from the response text and the evidence actually available in context, without requiring instrumentation that does not exist.

## Interface Fields

| Field | Required/Optional | Expected Content | Notes |
|---|---|---|---|
| `expert_id` | Required | Stable, unique, kebab-case identifier (e.g. `gauss-language-expert`). | Used to reference the expert from routing workflows and benchmark prompts without repeating its full name. |
| `expert_name` | Required | Human-readable display name (e.g. "GAUSS Language Expert"). | Matches the corresponding `experts/<name>/EXPERT.md` title. |
| `expert_scope` | Required | One paragraph stating what domain this expert owns and, briefly, what it explicitly does not own. | Should stay consistent with the `EXPERT.md` Boundaries section for the same expert; do not let the two drift. |
| `activation_triggers` | Required | A list of concrete task/content conditions under which the Code Assistant must consult this expert. | Should map back to specific `agents/code-assistant/task_modes.md` modes or recognizable content signals (e.g. "response includes GAUSS code"), not vague phrases like "when relevant." |
| `non_activation_cases` | Required | A list of task types where this expert should not activate, or activates only incidentally. | Exists specifically so routing evaluations have a negative case to check (see Evaluation Guidance) — activation-only lists cannot be checked for over-triggering. |
| `required_inputs` | Required | Information the expert's reasoning step needs before it can proceed responsibly. | E.g. "the exact command name or code snippet in question," "the source language, if this is a translation task." |
| `optional_inputs` | Optional | Information that improves the answer but does not block a response if missing. | E.g. "target GAUSS version," "whether the code is one-off or reusable." |
| `required_evidence` | Required | A table or list mapping task type to the evidence class required before an exact claim may be made. | Must be expressed using existing evidence vocabulary — see Evidence Requirements below. This is the field most likely to be checked against `schemas/command_lookup_evidence.schema.json` directly. |
| `decision_rules` | Required | An ordered list of checkable rules the expert applies. | Each rule should be phrased so a evaluator can answer yes/no about whether a given response followed it — not just restated general good judgment. |
| `refusal_conditions` | Required | Conditions under which the expert must decline to give an exact claim (syntax, defaults, return values, etc.) and instead state uncertainty. | See Refusal and Escalation Guidance below for the baseline list every profile should include. |
| `escalation_conditions` | Required | Conditions under which the task should route to a different expert, back to the retrieval workflow, or back to the user for clarification. | Distinct from refusal: refusal states uncertainty and stops; escalation redirects the task somewhere more appropriate. |
| `output_contract` | Required | The set of internal fields this expert's reasoning step should produce for the Code Assistant to draw on. | See Output Contract Guidance below for the shared baseline fields; a profile may add domain-specific ones. |
| `response_visibility` | Required | A short statement of how much of the expert's reasoning should be visible in the final user-facing response versus kept internal. | Default per Design Principles is "internal by default, visible through response quality" — a profile only needs this field to state an exception if one applies. |
| `evaluation_criteria` | Required | A list of checkable criteria an evaluator can use to confirm this expert was correctly consulted (or correctly not consulted). | Should be usable directly when scoring a benchmark response — see Evaluation Guidance. |
| `related_files` | Required | Paths to the expert's narrative spec, knowledge base, curated notes, and any workflows this profile depends on or is depended on by. | Keeps the profile's cross-references explicit and lets a reader verify nothing was duplicated instead of referenced. |

## YAML-style Template

```yaml
expert_id: <kebab-case-id>
expert_name: <Display Name>
expert_scope: >
  <one paragraph: what this expert owns, and what it explicitly does not>

activation_triggers:
  - <task mode or content signal>
  - <task mode or content signal>

non_activation_cases:
  - <task type that should not trigger this expert>
  - <task type that should not trigger this expert>

required_inputs:
  - <input the expert needs to proceed>

optional_inputs:
  - <input that improves but does not block the answer>

required_evidence:
  <task_type>: <evidence requirement, referencing retrieval_status / source_authority>
  <task_type>: <evidence requirement>

decision_rules:
  - <checkable rule>
  - <checkable rule>

refusal_conditions:
  - <condition under which the expert must state uncertainty instead of an exact claim>

escalation_conditions:
  - <condition under which the task should route elsewhere>

output_contract:
  - task_classification
  - activation_reason
  - activated_knowledge_domains
  - evidence_needed
  - evidence_used
  - verified_facts
  - decision_recommendation
  - risks_or_uncertainties
  - response_constraints
  - validation_suggestions

response_visibility: internal-by-default   # or: state the specific exception

evaluation_criteria:
  - <criterion an evaluator can check directly against a response>

related_files:
  - experts/<name>/EXPERT.md
  - experts/<name>/BODY_OF_KNOWLEDGE.md
  - workflows/retrieval-backed-response-pattern.md
```

This template is intentionally compact. A real profile (like `experts/gauss-language/OPERATIONAL_PROFILE.md`) fills in each field with real, task-specific content — this template should not itself grow into a full profile.

## Evidence Requirements

Expert profiles must express evidence requirements using vocabulary that already exists in `schemas/command_lookup_evidence.schema.json`, not a new one:

- `retrieval_status` — `found_complete`, `found_incomplete`, `not_found`, `ambiguous`, `conflict`, `stale`, `error`.
- `source_authority` — `official_docs`, `official_package_docs`, `official_source_code`, `curated_command_note`, `example_or_blog`, `category_list`, `model_knowledge`, `unknown`.
- `source_type` — the underlying artifact kind (`official_local_rst`, `curated_markdown`, `category_index`, etc.).
- `extraction_warnings` / `unresolved_questions` — signal that a `found_*` result is not necessarily complete; a profile's `required_evidence` should note when their presence changes what may be claimed.
- `conflicts` — signal that official and curated evidence disagree; a profile must not let its decision rules silently prefer curated evidence over an active conflict entry.
- `stale_evidence` — signal that evidence may not reflect current documentation; a profile must not let its decision rules treat stale evidence as equivalent to fresh evidence for exact-current-syntax claims.

Baseline rules every profile should state, refined as needed but never weakened:

- Exact command syntax, defaults, and return values require evidence with `source_authority: official_docs` or `official_package_docs` and a `retrieval_status` of `found_complete` or `found_incomplete` (with the incomplete parts named, not filled in).
- Curated notes (`source_authority: curated_command_note`) may support an answer but cannot override official evidence when a `conflict` entry exists; official evidence wins per `workflows/retrieval-backed-response-pattern.md` state G.
- Category lists (`source_authority: category_list`) support discovery only — they never satisfy the evidence requirement for exact syntax, per retrieval-backed-response-pattern state E.
- Schema validity (a file passing `scripts/validate_lookup_evidence.py` or `scripts/validate_all_evidence.py`) checks evidence *structure*, not GAUSS semantic correctness or execution. An expert profile must not treat "the evidence file is schema-valid" as equivalent to "the described GAUSS behavior is correct" or "GAUSS code was run."
- An expert profile may require stricter evidence than this baseline (for example, requiring `found_complete` specifically for a particularly failure-prone command), but may never accept weaker evidence than this baseline permits.

## Output Contract Guidance

An expert's contribution to a response is usually internal reasoning structure, not a literally printed section. The baseline output contract every profile should produce:

- `task_classification` — which task mode(s) apply and why this expert is relevant to them.
- `activation_reason` — the specific trigger from `activation_triggers` that applied.
- `activated_knowledge_domains` — which knowledge-base sections or command categories were drawn on.
- `evidence_needed` — the evidence class required for this specific task, per `required_evidence`.
- `evidence_used` — what evidence was actually available or retrieved, citing a real source (a file, a lookup result), not asserted in the abstract.
- `verified_facts` — claims supported by `evidence_used`, stated as verified.
- `decision_recommendation` — the expert's recommended approach, with the reasoning tied to a specific `decision_rules` entry where relevant.
- `risks_or_uncertainties` — anything incomplete, stale, ambiguous, or conflicting the user should know about.
- `response_constraints` — what the final response must not claim, given the evidence actually available.
- `validation_suggestions` — a concrete way to check the result, consistent with `workflows/retrieval-backed-response-pattern.md` Section 7's validation-step requirement.

**The final user-facing response does not need to literally print these ten fields as labeled sections.** A well-routed response satisfies them in substance — an evaluator should be able to point to the part of the response that corresponds to each field, even if the response itself reads naturally rather than as a structured report.

## Refusal and Escalation Guidance

An expert profile's `refusal_conditions` should, at minimum, cover:

- Required evidence is missing entirely (no matching command-specific documentation found).
- Evidence exists but is stale relative to current official documentation, and the task requires exact current syntax or defaults.
- Evidence is ambiguous (multiple plausible candidates, per retrieval-backed-response-pattern state D).
- Official and curated evidence conflict and the conflict has not been resolved in favor of official evidence.
- The task is outside the expert's stated `expert_scope`.
- The user asks for execution results, but no GAUSS code was actually run by an available tool.
- The package-vs-base-GAUSS distinction for a function is unresolved (evidence doesn't establish whether a function is base GAUSS or requires a specific package).

`escalation_conditions` differ from refusal: refusal states uncertainty and stops there; escalation redirects the task — to a different expert (when the primary issue is outside this expert's domain, e.g. econometric methodology rather than GAUSS syntax), back to the retrieval workflow (when the right next step is running `scripts/command_doc_lookup.py`, not answering from what's already in context), or back to the user (when disambiguating information is required, per state D).

## Evaluation Guidance

Manual evaluations of expert-routed responses should check:

- Did the correct expert activate for this task, per its `activation_triggers`?
- Did the response apply the expert's `decision_rules`, visibly, in substance?
- Did the response meet the `required_evidence` threshold for the claims it made — no exact syntax/defaults/returns without `official_docs`- or `official_package_docs`-backed evidence?
- Did it avoid inventing unsupported syntax, procedures, or behavior?
- Did it preserve uncertainty when evidence was incomplete, stale, ambiguous, or conflicting, rather than resolving it silently?
- Did it avoid unnecessary activation for a task in `non_activation_cases`?
- Did it correctly distinguish schema validation (structure) from GAUSS semantic correctness or execution, wherever that distinction was relevant?

This is the same manual-evaluation discipline already used for `evaluations/scoring.md` dimensions and for the 11.x-14.x benchmark categories — no new evaluation infrastructure is introduced by this interface. Future benchmark prompts (planned as category 15.x, "Expert Routing," in `planning/v0.8.0-operational-expert-modules.md`) will test these criteria directly, the same way 13.x tested evidence-schema states and 14.x tested validator aggregation behavior.

## Relationship to Existing Specs

- **`EXPERT_SPEC.md`** — defines the narrative specification every expert module's `EXPERT.md` should follow (Purpose, Role, Knowledge Profile, Reasoning Profile, Best Practices, Common Mistakes, Agent Usage, Inputs, Outputs, Success Criteria, Failure Modes). This interface does not replace `EXPERT_SPEC.md`; it adds a second, more mechanical layer for the subset of an expert's content that needs to be checkable rather than only narrative (activation, evidence thresholds, refusal/escalation, output contract). An expert's `EXPERT.md` should continue to satisfy `EXPERT_SPEC.md`; its `OPERATIONAL_PROFILE.md` fills in this interface.
- **`AGENT_SPEC.md`** — defines the Code Assistant's own specification, including an "Experts" list under its Internal Interface. This interface is what makes that list actionable: instead of the agent spec naming an expert only by reference, the expert's operational profile defines what consulting it actually requires.
- **`TOOL_SPEC.md`** — defines tool specifications (capability, inputs, outputs, permissions, failure modes). Not directly used by this interface, but structurally analogous: both specs exist so a capability (tool or expert) can be evaluated against a fixed contract rather than ad hoc judgment.
- **`KNOWLEDGE_SPEC.md`** — defines source hierarchy, conflict resolution, and the separation between factual knowledge and expert reasoning ("Expert modules may guide interpretation, but they should not override authoritative factual sources"). This interface's Evidence Requirements section is the operational enforcement of that exact principle for the GAUSS Language Expert and any future expert.
- **`workflows/retrieval-backed-response-pattern.md`** — defines the retrieval states (A-H) and response structure this interface's evidence vocabulary is drawn from. An expert profile's `required_evidence` and `refusal_conditions` should cite these states by letter where applicable rather than redescribing them.
- **`schemas/command_lookup_evidence.schema.json`** — the formal schema whose `retrieval_status`, `source_authority`, `source_type`, `conflicts`, and `stale_evidence` fields are this interface's only vocabulary for evidence. Nothing in an expert profile should introduce an evidence concept this schema cannot represent.
