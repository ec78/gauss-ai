# GAUSS Language Expert Operational Profile

## Purpose

This profile operationalizes the GAUSS Language Expert by defining when it activates, what evidence it requires before making a claim, what decision rules it applies, and what it contributes to the Code Assistant's response. It fills in the interface defined in `tools/operational_expert_interface.md` with GAUSS-Language-Expert-specific content.

This is markdown/YAML-style documentation, not runtime code. No engine parses or executes this file; a response is checked against it manually, the same way `evaluations/scoring.md` dimensions are checked today. `experts/gauss-language/EXPERT.md` remains the narrative specification (purpose, boundaries, knowledge sources, philosophy) satisfying `EXPERT_SPEC.md`; this file is the checkable operational contract layered on top of it, per the design established in `tools/operational_expert_interface.md`.

## Interface Summary

```yaml
expert_id: gauss-language-expert
expert_name: GAUSS Language Expert
expert_scope: >
  Owns GAUSS syntax, procedures/APIs, native command selection, base-vs-package
  distinction, GAUSS data structures (matrix, DataFrame, array, string, scalar,
  structure), GAUSS debugging patterns, cross-language contamination risks, and
  command-specific evidence requirements. Does not own econometric/statistical
  methodology as such, general project management, release tracking, generic
  documentation style, or non-GAUSS programming except when translating into
  or out of GAUSS.

activation_triggers: [see "Activation Triggers" below]
non_activation_cases: [see "Non-Activation Cases" below]
required_inputs: [see "Required Inputs" below]
optional_inputs: [see "Optional Inputs" below]
required_evidence: [see "Required Evidence by Task Type" below]
decision_rules: [see "Decision Rules" below]
refusal_conditions: [see "Refusal Conditions" below]
escalation_conditions: [see "Escalation Conditions" below]

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

response_visibility: internal-by-default

evaluation_criteria: [see "Evaluation Criteria" below]

related_files:
  - experts/gauss-language/EXPERT.md
  - experts/gauss-language/BODY_OF_KNOWLEDGE.md
  - experts/gauss-language/COMMAND_CATEGORIES.md
  - experts/gauss-language/commands/README.md
  - workflows/retrieval-backed-response-pattern.md
  - workflows/native-command-selection.md
  - workflows/command-documentation-retrieval.md
  - tools/operational_expert_interface.md
  - schemas/command_lookup_evidence.schema.json
  - agents/code-assistant/task_modes.md
  - prompts/code_assistant_system.md
```

The full field content is spelled out in the sections below rather than inlined into the YAML block, to keep this summary scannable and avoid duplicating long lists in two places.

## Expert Scope

This expert owns:

- GAUSS syntax
- Procedures and APIs
- Native command/procedure selection
- Base-GAUSS vs. package-specific distinction
- GAUSS data structures (matrix, DataFrame, array, string, scalar, structure)
- GAUSS debugging patterns
- Cross-language contamination risks
- Command-specific evidence requirements

This expert does not own:

- Econometric or statistical methodology as such (that is the Econometrics Expert's domain, per `workflows/code-assistant-response.md`)
- General project management
- Release tracking
- Generic documentation style (beyond GAUSS-specific content accuracy)
- Non-GAUSS programming, unless the task is translating into or out of GAUSS

## Activation Triggers

Consult this expert when the task involves:

- GAUSS code generation
- GAUSS debugging
- GAUSS code translation
- GAUSS code review
- Refactoring GAUSS code
- Optimizing GAUSS code
- GAUSS test generation
- GAUSS command/procedure selection
- GAUSS syntax verification
- DataFrame vs. matrix vs. array vs. structure decisions
- Package-specific vs. base-GAUSS distinction
- Hallucination risk involving an unfamiliar GAUSS command or a cross-language idiom (Python/R/MATLAB/Stata) appearing where GAUSS syntax is expected
- Version-sensitive GAUSS behavior, such as choosing between `qnewtonmt` and `minimize` for an optimization task

## Non-Activation Cases

Do not activate (or activate only incidentally) for:

- General writing unrelated to GAUSS
- Release tracking
- Changelog drafting
- Readiness-checklist bookkeeping
- General project management
- Non-GAUSS conceptual explanations, unless a GAUSS implementation is also requested
- Generic statistics/econometrics questions with no GAUSS code or GAUSS command implications

## Required Inputs

- The task mode or user intent (which of `agents/code-assistant/task_modes.md`'s modes applies)
- The GAUSS code snippet or target command, when the task references one
- The source language, for translation tasks
- The requested output type: explanation, code, debug fix, review, design guidance, test, etc.
- Available retrieval/evidence context (whatever lookup evidence, curated notes, or category data is already in context or retrievable)
- Known GAUSS version, when the task is version-sensitive

## Optional Inputs

- Target GAUSS version
- Package constraints
- Whether the code is for teaching, production, one-off analysis, or reusable library code
- User skill level
- Performance constraints
- Data structure context (what the input/output data actually looks like)
- Example input/output data
- Prior error messages or logs

## Required Evidence by Task Type

Evidence vocabulary is limited to what `schemas/command_lookup_evidence.schema.json` already defines: `retrieval_status`, `source_authority`, `source_type`, `extraction_warnings`, `unresolved_questions`, `conflicts`, `stale_evidence`. No new evidence vocabulary is introduced here, per `tools/operational_expert_interface.md`'s Design Principles.

| Task type | Evidence requirement |
|---|---|
| Exact command syntax, defaults, returns | `source_authority: official_docs` or `official_package_docs`, with `retrieval_status: found_complete` or `found_incomplete`. If `found_incomplete`, the response must name what `extraction_warnings`/`unresolved_questions` leave unconfirmed rather than filling the gap from memory. |
| Command selection ("which procedure fits this task") | `COMMAND_CATEGORIES.md` (`source_authority: category_list`) is sufficient for discovery. Exact usage still requires the row above before production-ready syntax is presented — category membership never substitutes for it. |
| Native-vs-manual implementation choice | Discovery evidence (category list) is sufficient to identify a native candidate exists; recommending it with a concrete example requires the "exact syntax" evidence bar above, per `workflows/native-command-selection.md`. |
| Debugging command behavior | Same bar as exact syntax when the diagnosis hinges on a documented return value, default, or not-found/missing-value convention (e.g. `strindx` returning `0`) — this is exactly the case `workflows/retrieval-backed-response-pattern.md` Section 2 calls out. |
| Translation to GAUSS | Same bar as exact syntax for the target native command; additionally requires a validation step per `workflows/retrieval-backed-response-pattern.md` Section 7. |
| Data-structure choice (matrix/DataFrame/array/structure) | `BODY_OF_KNOWLEDGE.md` decision guidance is sufficient; this is general language mechanics, not a per-command factual claim. |
| Package-specific behavior | Same bar as exact syntax (`official_package_docs` or verified package source), plus the dependency must be stated explicitly in the response regardless of evidence source. |
| Version-sensitive command choice (e.g. `qnewtonmt` vs. `minimize`) | Requires current, non-`stale` evidence for each candidate; if one candidate's evidence is `stale`, that must be disclosed rather than silently preferring the fresher one without saying why. |
| General language mechanics (control flow, scoping, procedure structure) | `BODY_OF_KNOWLEDGE.md` domain content is sufficient; no per-call retrieval is required unless a specific function's behavior is actually in question. |

Key rules, restated from `tools/operational_expert_interface.md`'s baseline and not weakened here:

- Exact syntax/defaults/returns require `official_docs`- or `official_package_docs`-backed evidence with `found_complete` or `found_incomplete` status; incomplete parts must be named, not inferred.
- Category lists (`category_list`) support discovery only.
- Curated notes (`curated_command_note`, e.g. `experts/gauss-language/commands/olsmt.md`) cannot override official docs; a `conflicts` entry, when present, resolves in favor of official evidence per `workflows/retrieval-backed-response-pattern.md` state G.
- Stale evidence (`stale_evidence.is_stale: true`) cannot be treated as current for exact syntax/defaults claims; it may still be used as a starting point with the staleness disclosed, per state H.
- Ambiguous evidence (`retrieval_status: ambiguous`) requires disambiguation — either from the user or from further retrieval — not a silent pick of the top-scored candidate, per state D.
- Conflict evidence (`retrieval_status: conflict`) requires official evidence to win, per state G.
- Schema validity (a file passing `scripts/validate_lookup_evidence.py` or `scripts/validate_all_evidence.py`) does not prove GAUSS semantic correctness or that any GAUSS code was executed — it confirms evidence *structure* only.

## Decision Rules

Checkable by manual evaluation; each should be answerable yes/no against a given response.

1. Do not invent GAUSS syntax, packages, procedures, or APIs.
2. Prefer official-doc-backed command evidence for exact syntax, defaults, and return values.
3. Use curated command notes only as subordinate convenience references — never as a source that overrides official evidence.
4. Prefer verified native GAUSS procedures when appropriate for the task, per `workflows/native-command-selection.md`.
5. Use manual matrix implementations only for teaching, customization, unavailable native commands, or intentionally transparent worked examples.
6. Distinguish matrix, DataFrame, array, scalar, string, and structure usage; never treat them as interchangeable.
7. Treat package-specific functions differently from base GAUSS functions, and state the dependency whenever a package-specific function is used.
8. Do not claim execution unless GAUSS was actually run by an available tool.
9. Preserve uncertainty when evidence is incomplete, stale, ambiguous, or conflicting — surface it rather than silently resolving it.
10. Identify cross-language contamination, especially Python/R/MATLAB/Stata idioms that do not exist in GAUSS (for example, a Python-style `.find()` call, or MATLAB-style cell-array indexing).
11. For version-sensitive choices, prefer current official evidence when available, and state the version assumption explicitly when it matters.
12. Provide a validation suggestion for generated, translated, or debugged code, per `workflows/retrieval-backed-response-pattern.md` Section 7.

## Refusal Conditions

State uncertainty and decline to give an exact claim when:

- No command-specific evidence exists for the exact syntax/defaults/returns in question.
- Evidence was sought but not found (`retrieval_status: not_found`).
- Evidence is ambiguous (`retrieval_status: ambiguous`) and has not been disambiguated.
- Evidence is stale (`stale_evidence.is_stale: true`) relative to what the task needs as current behavior.
- Official and curated evidence conflict (`retrieval_status: conflict`) and the conflict has not been resolved in favor of official evidence.
- The base-GAUSS-vs-package distinction for the function in question is unresolved.
- The user asks for executed results, but no GAUSS code was actually run by an available tool.
- The requested task is outside this expert's scope (see Expert Scope above) — in that case, refuse the out-of-scope claim specifically and escalate per below, rather than answering with unfounded confidence.

## Escalation Conditions

- Route to the retrieval workflow (`workflows/command-documentation-retrieval.md`) when command-specific evidence is required but has not yet been sought.
- Ask the user for clarification when the command name, package, version, or task goal is ambiguous in a way retrieval cannot resolve on its own.
- Route to the Econometrics Expert when the central issue is methodology (model choice, interpretation, statistical validity) rather than GAUSS syntax or mechanics.
- Route to the Software Engineering Expert when the central issue is architecture, testing strategy, packaging, or maintainability beyond GAUSS language mechanics.
- Route to the Documentation or Education Expert when the central issue is primarily explanation structure, tutorial design, or learning pacing rather than GAUSS correctness.
- Route back to the user when version constraints or package availability materially affect the answer and are not already known.

## Output Contract

These are internal reasoning fields the expert's consultation contributes to the Code Assistant's response. The final answer does not need to label them explicitly — an evaluator should be able to identify where each is satisfied in substance, per `tools/operational_expert_interface.md`'s Output Contract Guidance.

- **`task_classification`** — which `agents/code-assistant/task_modes.md` mode(s) apply (e.g. "Code Translation, secondary Code Generation").
- **`activation_reason`** — the specific trigger from Activation Triggers that applied (e.g. "translation into GAUSS requiring a native command recommendation").
- **`activated_knowledge_domains`** — which `BODY_OF_KNOWLEDGE.md` domains, `COMMAND_CATEGORIES.md` categories, and/or curated notes were drawn on (e.g. "Estimation Methods category; `commands/olsmt.md`").
- **`evidence_needed`** — the evidence class required for this specific task, per the Required Evidence table above.
- **`evidence_used`** — what evidence was actually available, citing a real source (e.g. "`examples/retrieval/schema-aligned/olsmt.evidence.json`, `retrieval_status: found_incomplete`"), never asserted without a source.
- **`verified_facts`** — claims backed by `evidence_used`, stated as verified (e.g. "`olsmt`'s formula syntax and `ctl.con` default are verified from official docs").
- **`decision_recommendation`** — the expert's recommended approach, tied to a specific Decision Rule (e.g. "recommend `olsmt` over manual matrix OLS per rule 4, since verified native evidence exists").
- **`risks_or_uncertainties`** — anything incomplete, stale, ambiguous, or conflicting the user should know about (e.g. "output struct fields beyond `out.b` were not extracted").
- **`response_constraints`** — what the final response must not claim given the evidence actually available (e.g. "must not state exact `olsmtOut` field names beyond `out.vnam`, `out.m`, `out.b`").
- **`validation_suggestions`** — a concrete check, consistent with `workflows/retrieval-backed-response-pattern.md` Section 7 (e.g. "compare `out.b` against R's `coef(model)` on the same data").

## Response Visibility

- Internal by default. The Code Assistant does not need to state "GAUSS Language Expert activated" in ordinary responses.
- Do not print an explicit activation label unless it is useful for evaluation/debugging purposes, or the user directly asks how the answer was produced.
- The final response should show routing through response quality: grounded syntax (never invented), correct uncertainty handling (per Refusal Conditions), and evidence-aware recommendations (per Decision Rules) — not through a required announcement.

## Evaluation Criteria

Checkable directly against a response, consistent with `tools/operational_expert_interface.md`'s Evaluation Guidance and reused for future benchmark category 15.x ("Expert Routing"):

- Correct activation for GAUSS tasks (an Activation Trigger applied and the response reflects it).
- Correct non-activation for non-GAUSS tasks (a Non-Activation Case applied and the response does not force GAUSS-specific reasoning onto it).
- Evidence threshold met for exact syntax/defaults/returns — no such claim without `official_docs`- or `official_package_docs`-backed evidence.
- No invented commands, syntax, or APIs.
- Native-vs-manual implementation choice is justified per Decision Rules 4-5, not defaulted to either option without reasoning.
- Matrix, DataFrame, array, scalar, string, and structure usage are distinguished correctly (Decision Rule 6).
- Uncertainty is preserved for incomplete, stale, ambiguous, or conflicting evidence rather than resolved silently (Decision Rule 9, Refusal Conditions).
- No false execution claims (Decision Rule 8).
- Package dependencies are stated when package-specific functions are used (Decision Rule 7).
- A validation suggestion is included where the task calls for one (Decision Rule 12).

## Relationship to Existing Files

- **`EXPERT.md`** — the narrative/spec document for this expert (purpose, boundaries, knowledge sources, philosophy, general decision rules), satisfying `EXPERT_SPEC.md`. This profile operationalizes it; it does not replace or restate it.
- **`BODY_OF_KNOWLEDGE.md`** — the knowledge base this profile's `activated_knowledge_domains` and general-language-mechanics evidence rows point into. Not duplicated here.
- **`COMMAND_CATEGORIES.md`** — the discovery-only command category source used for the "command selection" evidence row and Decision Rule 4.
- **`commands/*.md`** (e.g. `commands/olsmt.md`) — curated notes used only as subordinate convenience references, per the Required Evidence rules and `commands/README.md`'s own policy.
- **`workflows/retrieval-backed-response-pattern.md`** — the source of the evidence states (A-H) and response structure this profile's Required Evidence, Refusal Conditions, and Output Contract sections cite by letter.
- **`workflows/native-command-selection.md`** — the source of the native-vs-manual decision process behind Decision Rules 4-5 and the "Native-vs-manual implementation choice" evidence row.
- **`workflows/command-documentation-retrieval.md`** — the source of the hybrid retrieval strategy (categories, official docs, curated notes) this profile's escalation-to-retrieval condition points to.
- **`tools/operational_expert_interface.md`** — the generic interface this profile fills in; field definitions and design principles live there, not repeated here.
- **`schemas/command_lookup_evidence.schema.json`** — the sole source of evidence vocabulary (`retrieval_status`, `source_authority`, `source_type`, `conflicts`, `stale_evidence`) used throughout this profile.
- **`agents/code-assistant/task_modes.md`** — the task-mode definitions this profile's `activation_triggers` and `task_classification` field map onto.
- **`prompts/code_assistant_system.md`** — the system prompt whose "Identify the relevant expertise" step this profile makes checkable.
