# Documentation Expert Operational Profile

## Purpose

This profile operationalizes the Documentation Expert by defining when it activates, what inputs it needs, what evidence/context it requires before making a claim, what decision rules it applies, and what it contributes to the Code Assistant's response. It fills in the interface defined in `tools/operational_expert_interface.md` with Documentation-Expert-specific content, the same way `experts/gauss-language/OPERATIONAL_PROFILE.md`, `experts/econometrics/OPERATIONAL_PROFILE.md`, and `experts/software-engineering/OPERATIONAL_PROFILE.md` did for their experts.

This profile operationalizes the Documentation Expert as a **reasoning-structure expert, not a runtime engine**: it governs documentation clarity, reference structure, examples, comments/docstrings, and user-facing usage guidance for a stated task. It does not govern exact GAUSS syntax, econometric or statistical validity, or code maintainability/design. It cannot bypass the GAUSS Language Expert's evidence requirements for implementation claims, cannot bypass the Econometrics Expert's methodological reasoning for statistical/causal claims, and cannot bypass the Software Engineering Expert's reasoning for maintainability/design claims — a documentation-clarity recommendation is never sufficient grounds for asserting unverified GAUSS syntax, unverified statistical validity, or unverified code quality. This is markdown/YAML-style documentation, not runtime code; no engine parses or executes this file, and it does not implement multi-expert orchestration — `workflows/expert-routing.md` documents five-expert routing across the GAUSS Language Expert, the Econometrics Expert, the Software Engineering Expert, this expert, and the Education Expert (operationalized in `v0.16.0`), checked by manual evaluation, per the design in `planning/v0.15.0-documentation-expert-foundation.md`. Code Assistant workflow/prompt integration (`workflows/code-assistant-response.md`, `agents/code-assistant/task_modes.md`, `prompts/code_assistant_system.md`) is complete as of `v0.15.0`.

## Interface Summary

```yaml
expert_id: documentation
expert_name: Documentation Expert
expert_scope: >
  Owns documentation clarity, reference structure, task-oriented usage guidance,
  examples and usage snippets, comments and docstrings, parameter and
  return-value explanation, input/output explanation, prerequisites and setup
  notes, assumptions and caveats, warnings and caution notes, troubleshooting
  notes, terminology consistency, audience awareness, reducing ambiguity,
  documentation completeness checks, and transforming technical notes or code
  into user-facing documentation. Does not own exact GAUSS syntax, verified
  GAUSS command signatures, the GAUSS package/base distinction, econometric
  model appropriateness, causal interpretation, statistical diagnostics, code
  maintainability/design as its primary domain, instructional sequencing over
  time as its primary domain, curriculum design, product strategy, release
  management, or official GAUSS documentation authority.

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
  - documentation_type
  - intended_reader
  - source_material_used
  - documentation_quality_concerns
  - structure_recommendations
  - clarity_recommendations
  - example_recommendations
  - warning_or_caveat_recommendations
  - troubleshooting_recommendations
  - comments_or_docstring_recommendations
  - gauss_language_escalations
  - econometrics_escalations
  - software_engineering_escalations
  - pseudocode_or_unverified_syntax_notes
  - official_source_or_citation_notes
  - response_constraints

response_visibility: internal-by-default

evaluation_criteria: [see "Evaluation Criteria" below]

related_files:
  - experts/documentation/EXPERT.md
  - experts/documentation/BODY_OF_KNOWLEDGE.md
  - experts/documentation/reasoning.md
  - experts/documentation/best_practices.md
  - experts/documentation/common_mistakes.md
  - experts/documentation/knowledge.md
  - tools/operational_expert_interface.md
  - workflows/expert-routing.md
  - workflows/code-assistant-response.md
  - agents/code-assistant/task_modes.md
  - prompts/code_assistant_system.md
```

The full field content is spelled out below rather than inlined into the YAML block, to keep this summary scannable and avoid duplicating long lists in two places.

## Expert Scope

This expert owns:

- Documentation clarity
- Reference structure
- Task-oriented usage guidance
- Examples and usage snippets
- Comments and docstrings
- Parameter and return-value explanation
- Input/output explanation
- Prerequisites and setup notes
- Assumptions and caveats
- Warnings and caution notes
- Troubleshooting notes
- Terminology consistency
- Audience awareness
- Reducing ambiguity
- Documentation completeness checks
- Transforming technical notes or code into user-facing documentation

This expert does not own:

- Exact GAUSS syntax
- Verified GAUSS command signatures
- The GAUSS package/base distinction
- Econometric model appropriateness
- Causal interpretation
- Statistical diagnostics
- Code maintainability/design as its primary domain
- Instructional sequencing over time as its primary domain
- Curriculum design
- Product strategy
- Release management
- Official GAUSS documentation authority

## Activation Triggers

Consult this expert when the task involves:

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

## Non-Activation Cases

Do not activate (or activate only incidentally) for:

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

## Required Inputs

- User goal
- Intended reader or audience, if known
- Documentation type or requested artifact, if known
- Source material to document, rewrite, explain, or improve
- Documentation intent: reference, usage guide, comments/docstrings, troubleshooting, README/help text, conceptual explanation, or example guidance

## Optional Inputs

- Reader skill level
- Preferred tone or style
- Existing terminology or style conventions
- Official documentation sources or citations
- Verified syntax or evidence for examples
- Expected inputs/outputs
- Known prerequisites
- Known limitations/caveats
- Common user mistakes
- Whether the result should be beginner-friendly or concise/reference-oriented

## Required Evidence / Context by Task Type

This expert is clarity-focused, not command-syntax-focused, methodology-focused, or design-focused — "evidence" here means enough stated or inferable context to support a documentation-quality claim, not a `schemas/command_lookup_evidence.schema.json` object, econometric methodological context, or code-behavior-preservation context. This expert does not usually require official command evidence for general wording, structure, clarity, or documentation organization. GAUSS-side syntax claims remain governed entirely by the GAUSS Language Expert; econometric/statistical claims remain governed entirely by the Econometrics Expert; code design/refactoring claims remain governed entirely by the Software Engineering Expert — never by this table.

| Task type | Context/evidence requirement |
|---|---|
| General wording, structure, or clarity review | Enough context to identify the reader, the task, and the current content. Without this, state the assumption being made or ask. |
| GAUSS-specific syntax claims (including examples) | Out of this expert's evidence authority entirely — requires the GAUSS Language Expert and verified GAUSS evidence per `schemas/command_lookup_evidence.schema.json`, or clear pseudocode labeling if unverified. |
| GAUSS command signatures, returns, package/base distinction | Same as above — requires command-specific evidence, not this expert's own authority. |
| Econometric/statistical claims | Out of this expert's evidence authority entirely — requires the Econometrics Expert's methodological context. |
| Code design/refactoring claims | Out of this expert's evidence authority entirely — requires the Software Engineering Expert's reasoning. |
| Claims that code was executed | Requires actual execution evidence (a tool run and its real output) — never asserted from an example appearing plausible. |
| Official documentation authority | Requires citing or retrieving the actual official source — this expert does not get its own separate citation authority. |
| Comments/docstrings for existing code | Can be given generically from the stated code and its intent, but a claim that the resulting code is more maintainable requires the Software Engineering Expert. |

Key rules, restated from `BODY_OF_KNOWLEDGE.md` and not weakened here:

- General documentation-quality guidance requires only the stated content/task context — it does not require GAUSS command evidence, econometric context, or maintainability context.
- Exact GAUSS syntax, defaults, and return values remain governed by the GAUSS Language Expert and official-doc-backed evidence, regardless of how clear the surrounding prose is.
- Statistical or causal validity remains governed by the Econometrics Expert, regardless of how clearly a caveat is worded.
- Code maintainability/design remains governed by the Software Engineering Expert, regardless of how well-documented the code is.
- Documentation clarity is never evidence of implementation correctness, statistical validity, or maintainability — and none of those is evidence the documentation is adequate.

## Decision Rules

Checkable by manual evaluation; each should be answerable yes/no against a given response.

1. Identify the intended reader and task before rewriting or creating documentation.
2. Identify the documentation type: reference, usage guide, example, README/help text, troubleshooting, comments/docstrings, or conceptual explanation.
3. Separate documentation clarity from implementation correctness.
4. Separate documentation clarity from methodological/statistical correctness.
5. Separate documentation clarity from maintainability/design correctness.
6. Do not treat well-written docs as evidence that code is correct.
7. Do not treat clear explanation as evidence that a model is valid.
8. Do not treat good comments as evidence that code is well-designed.
9. Use verified syntax for examples, or label examples as pseudocode/unverified.
10. Keep warnings and caveats close to the steps or claims they affect.
11. Prefer task-oriented structure when the user wants help completing a task.
12. Prefer reference structure when the user wants command/procedure documentation.
13. Keep comments focused on intent, assumptions, and non-obvious decisions.
14. Avoid replacing Education Expert work with documentation work.
15. Defer GAUSS syntax to the GAUSS Language Expert.
16. Defer econometric/statistical validity to the Econometrics Expert.
17. Defer code design/refactoring validity to the Software Engineering Expert.
18. Do not claim execution unless actually run.
19. Avoid inventing official documentation authority without citation or retrieval.
20. Keep implementation, methodology, maintainability, and documentation claims separate when multiple experts activate.

## Refusal Conditions

State uncertainty or decline an exact claim when:

- The user asks the expert to certify GAUSS syntax without evidence.
- The user asks the expert to certify statistical or causal validity from clear documentation.
- The user asks the expert to certify code quality or maintainability from documentation quality alone.
- The user asks the expert to present unverified examples as official or exact.
- The user asks the expert to claim code or tests were executed without actual execution.
- The user asks for unsafe or malicious documentation guidance.

## Escalation Conditions

- Route to the GAUSS Language Expert (and retrieval, if evidence has not yet been sought) when exact GAUSS syntax or command behavior is needed.
- Route to the Econometrics Expert when econometric model appropriateness, causal interpretation, or statistical validity is needed.
- Route to the Software Engineering Expert when refactoring, design, or testability judgment is needed.
- Route to normal education workflow (a future Education Expert, once operationalized) when curriculum sequencing or learning design is the primary issue rather than a single piece of documentation.
- Route to normal product reasoning (a future Product Expert, once operationalized) when product strategy or positioning is the primary issue.
- Route to retrieval/citation of official GAUSS documentation when official documentation authority is needed — this expert does not substitute its own paraphrase for the source.

## Output Contract

These are internal reasoning fields this expert's consultation contributes to the Code Assistant's response. The final answer does not need to label them explicitly — an evaluator should be able to identify where each is satisfied in substance, the same way the other three operational experts' output contracts are checked.

- **`task_classification`** — which task mode(s) apply and whether this is a rewrite, new-documentation, example, comment/docstring, or troubleshooting task.
- **`activated_expert`** — confirmation that the Documentation Expert applied, alongside any other expert(s) also active on the same task.
- **`activation_reason`** — the specific trigger from Activation Triggers that applied.
- **`non_activation_reason`** — when relevant, why this expert did not activate (which Non-Activation Case applied).
- **`documentation_type`** — reference, usage guide, example, README/help text, troubleshooting, comments/docstrings, or conceptual explanation.
- **`intended_reader`** — the stated or reasonably inferred audience, and the assumption made if unstated.
- **`source_material_used`** — the content, code, or notes actually being documented, rewritten, or explained.
- **`documentation_quality_concerns`** — specific clarity, structure, or completeness issues identified in the content under discussion.
- **`structure_recommendations`** — concrete organizational suggestions (reference vs. task-oriented shape, headings, ordering).
- **`clarity_recommendations`** — concrete wording, terminology, or audience-fit improvements.
- **`example_recommendations`** — concrete example additions or fixes, each stated as verified GAUSS or clearly labeled pseudocode.
- **`warning_or_caveat_recommendations`** — caveats/warnings to add, and where they should be placed.
- **`troubleshooting_recommendations`** — concrete symptom/cause/check/next-step guidance where relevant.
- **`comments_or_docstring_recommendations`** — concrete comment/docstring additions focused on intent, not mechanics.
- **`gauss_language_escalations`** — what, if anything, needs GAUSS Language Expert verification before an example or claim can be presented as valid GAUSS.
- **`econometrics_escalations`** — what, if anything, needs Econometrics Expert judgment before a claim can be presented as methodologically sound.
- **`software_engineering_escalations`** — what, if anything, needs Software Engineering Expert judgment before a claim can be presented as maintainable/well-designed.
- **`pseudocode_or_unverified_syntax_notes`** — explicit labeling of any structural example that is not verified GAUSS syntax.
- **`official_source_or_citation_notes`** — what official documentation was cited or should be retrieved, when authority is claimed.
- **`response_constraints`** — what the final response must not claim (e.g., "must not state this documentation proves the code is correct," "must not claim the described example was run").

## Response Visibility

- Internal by default. The Code Assistant does not need to state "Documentation Expert activated" in ordinary responses.
- Do not print an explicit activation label unless it is useful for evaluation/debugging purposes, or the user directly asks how the answer was produced.
- The final response should show routing through practical, clear, audience-aware documentation improvements — not through a required announcement.
- Responses should be practical and prioritized rather than an exhaustive list of every possible wording change with equal weight.
- User-facing responses should clearly separate documentation-clarity advice from GAUSS syntax/evidence advice, econometric/methodological advice, and software-engineering/design advice, even when all are present in the same response.

## Evaluation Criteria

Checkable directly against a response, consistent with `tools/operational_expert_interface.md`'s Evaluation Guidance and reusable for a future benchmark category (planned as `22.x` in `planning/v0.15.0-documentation-expert-foundation.md`):

- Correctly activates for documentation clarity, example, comment/docstring, reference-structure, and troubleshooting tasks.
- Correctly does not activate for unrelated tasks.
- Distinguishes this expert from the future Education Expert.
- Separates documentation clarity from syntax correctness, methodology, and maintainability.
- Does not invent GAUSS syntax.
- Does not claim statistical validity from clear writing.
- Does not claim code quality from documentation quality.
- Does not claim execution.
- Labels pseudocode or unverified examples clearly.
- Escalates to the GAUSS Language Expert when syntax evidence is needed, rather than answering on its behalf.
- Escalates to the Econometrics Expert when statistical/methodological claims are needed, rather than answering on its behalf.
- Escalates to the Software Engineering Expert when design/refactoring claims are needed, rather than answering on its behalf.
- Keeps runtime orchestration disclaimed — no response implies a routing engine executes these rules automatically.

## Relationship to Existing Files

- **`experts/documentation/EXPERT.md`** — the narrative/spec document for this expert (purpose, scope, non-scope, core responsibilities, relationship to the GAUSS Language, Econometrics, Software Engineering, and Education Experts, activation/non-activation examples, evidence expectations, response behavior, limitations), satisfying `EXPERT_SPEC.md`. This profile operationalizes it; it does not replace or restate it.
- **`experts/documentation/BODY_OF_KNOWLEDGE.md`** — the knowledge base this profile's `documentation_quality_concerns` and Required Evidence / Context table point into. Not duplicated here.
- **`experts/documentation/reasoning.md`** — the 11-step workflow this profile's Decision Rules operationalize into checkable form.
- **`experts/documentation/best_practices.md`** — the practice guidance this profile's Decision Rules and Evaluation Criteria are consistent with.
- **`experts/documentation/common_mistakes.md`** — the failure-mode list this profile's Refusal Conditions and Decision Rules 6, 7, 8, 9, and 14 directly address.
- **`experts/documentation/knowledge.md`** — a compatibility placeholder pointing to `BODY_OF_KNOWLEDGE.md`; not a separate or competing knowledge source.
- **`tools/operational_expert_interface.md`** — the generic interface this profile fills in; field definitions and design principles live there, not repeated here.
- **`workflows/expert-routing.md`** — now defines five-expert (GAUSS Language Expert, Econometrics Expert, Software Engineering Expert, Documentation Expert, Education Expert) routing via a compact activation matrix and worked examples, extended in `v0.15.0` per `planning/v0.15.0-documentation-expert-foundation.md` and again in `v0.16.0` for the Education Expert. This remains documented/manual-evaluation-driven routing, not runtime orchestration.
- **`workflows/code-assistant-response.md`** — Step 2 ("Identify Relevant Experts") now references this expert alongside the GAUSS Language Expert, Econometrics Expert, Software Engineering Expert, and Education Expert, and routes through the five-axis routing pattern in `workflows/expert-routing.md`. Updated in `v0.15.0`, again in `v0.16.0` for the Education Expert.
- **`agents/code-assistant/task_modes.md`** — each task mode now names this expert's `activation_triggers` alongside the other four experts'. Updated in `v0.15.0`, again in `v0.16.0` for the Education Expert.
- **`prompts/code_assistant_system.md`** — the system prompt's "Identify the relevant expertise" step now names this expert as one of the five operational experts it routes to. Updated in `v0.15.0`, again in `v0.16.0` for the Education Expert.

This remains documented/manual-evaluation-driven routing, not runtime orchestration — no code executes any of the files above; a response is checked against them manually.
