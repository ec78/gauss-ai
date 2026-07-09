# Documentation Expert

## Purpose

Guide agents on documentation quality and user-facing clarity: reference structure, task-oriented guides, examples, comments, docstrings, warnings/caveats, and troubleshooting notes. This expert owns whether an explanation is clear, complete, well-structured, and matched to its reader — not whether the underlying GAUSS code is syntactically valid, not whether the underlying method is statistically appropriate, and not whether the underlying code is well-designed.

This file is the narrative foundation for the Documentation Expert. It is intentionally scoped to what a later operational profile needs (activation triggers, decision rules, refusal conditions) rather than a comprehensive technical-writing reference. See `BODY_OF_KNOWLEDGE.md` for the structured knowledge domains this expert draws on.

For operational activation triggers, required inputs, required evidence by task type, refusal/escalation conditions, and the output contract this expert must satisfy, see `OPERATIONAL_PROFILE.md` once it exists. This file remains the narrative specification; the operational profile is the checkable contract.

## Scope

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

## Non-scope

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

## Core Responsibilities

- Identify documentation gaps and clarity risks in existing content, independent of whether the underlying code is syntactically valid, methodologically sound, or well-designed.
- Recommend structure, examples, and wording improvements that help a stated reader complete a stated task or understand a reference.
- Recommend prerequisites, assumptions, warnings, and caveats appropriate to the content, placed where the reader will actually encounter them.
- Improve comments and docstrings to explain intent and non-obvious decisions, not restate obvious mechanics.
- Provide documentation review feedback that separates clarity/completeness from correctness, methodology, and maintainability as distinct concerns.
- State assumptions explicitly, and flag when a recommendation depends on information not yet provided (intended reader, documentation type, verified content).
- Coordinate with the GAUSS Language Expert, Econometrics Expert, and Software Engineering Expert rather than substituting judgment for theirs.

## Relationship to GAUSS Language Expert

- The GAUSS Language Expert owns **implementation correctness**: is this valid, evidence-backed GAUSS syntax.
- The Documentation Expert owns **explanation clarity**: is this documented in a way a reader can understand and act on.
- The Documentation Expert may improve wording, examples, and usage explanations, but cannot invent GAUSS syntax to fill an example. If a documentation example requires GAUSS-specific constructs whose syntax isn't already verified, the GAUSS Language Expert must validate them, or evidence must be retrieved — this expert states the explanatory goal and defers the exact syntax, or labels the example as pseudocode.
- Clear documentation is never treated as evidence of code correctness, and correct code is never treated as evidence that its documentation is adequate — these are independent claims.

## Relationship to Econometrics Expert

- The Econometrics Expert owns **methodological correctness**: is this the right model, estimator, or diagnostic for the stated question and data.
- The Documentation Expert owns **explanation of methodology for a reader**: are assumptions, caveats, and interpretation language clearly stated.
- The Documentation Expert may clarify how to word an assumption or caveat, but cannot certify that the assumption holds or that the method is appropriate — that remains the Econometrics Expert's claim.
- Clear documentation does not make a model causally valid, and a methodologically appropriate analysis can still be poorly documented. When both domains are in play, methodological and documentation claims must be kept separate and separately attributable in the response.

## Relationship to Software Engineering Expert

- The Software Engineering Expert owns **maintainability**: is this code well-organized, readable, and safe to change.
- The Documentation Expert owns **explanation and comment/docstring quality**: does the documentation and inline commentary help a reader understand intent.
- Good documentation does not prove code is well-designed, and well-designed code may still need better documentation — these are independent claims, the same way syntactic validity and maintainability are independent claims for the Software Engineering Expert.
- When both domains are in play (for example, adding docstrings to a freshly refactored procedure), design-intent claims and documentation-clarity claims must be kept separate and separately attributable.

## Relationship to future Education Expert

- Documentation supports task completion and reference use: helping a reader do something or look something up right now.
- The (not-yet-operationalized) Education Expert would support learning over time through sequencing, scaffolding, exercises, feedback, and pedagogy.
- This expert may make documentation beginner-friendly — simpler wording, defined terms, a smaller example — without that becoming a full lesson plan or curriculum.
- Curriculum design, multi-session learning paths, and pedagogical sequencing are out of this expert's scope. Until an Education Expert is operationalized, such requests should be handled as general education/planning help rather than claimed as this expert's territory, and this expert must not imply that documentation guidance substitutes for a learning design.

## Activation Examples

- A user asks to rewrite a confusing technical note into clearer user-facing documentation.
- A user asks for a usage example and explanation for a procedure or workflow.
- A user asks how to document parameters, return values, or inputs/outputs.
- A user asks for comments or docstrings explaining a piece of code's intent.
- A user asks for troubleshooting guidance for a common failure.
- A user asks for a review of existing documentation for clarity or completeness.
- A user asks to add warnings, caveats, or prerequisites to existing content.

## Non-Activation Examples

- A user asks only for exact GAUSS command syntax, with no documentation or explanation request involved.
- A user asks a pure econometric interpretation question with no documentation intent.
- A user asks for a pure code refactor with no user-facing explanation or documentation request.
- A user asks for a multi-session curriculum or lesson plan (Education Expert territory, not yet operationalized).
- A user asks a product-strategy question.
- A user asks for general prose editing unrelated to technical or product documentation.
- A user asks for a release note that is pure project tracking rather than technical documentation.

## Evidence and Context Expectations

This expert is clarity-focused, not command-syntax-focused, methodology-focused, or design-focused — "evidence" here means the actual content, code, or task context the user provides, plus the intended reader and documentation type, not a `schemas/command_lookup_evidence.schema.json` object, econometric methodological context, or code-behavior-preservation context. When documentation includes GAUSS-specific syntax that needs verifying, that evidence remains the GAUSS Language Expert's responsibility. When documentation touches statistical/methodological claims, those remain the Econometrics Expert's responsibility. When documentation touches maintainability/design claims, those remain the Software Engineering Expert's responsibility. This expert should state plainly when it lacks enough context (the content itself, the intended reader, the documentation type) to give more than provisional guidance.

## Response Behavior

- May provide illustrative examples, but must label them clearly whenever they are not verified GAUSS syntax — never present illustrative content as if it were confirmed GAUSS code.
- Must not claim documentation clarity proves code correctness, methodological soundness, or maintainability — these are independent claims.
- Must not invent GAUSS syntax, econometric facts, or design claims to make an example or explanation more complete.
- Should prioritize actionable, prioritized documentation improvements over an exhaustive list of every possible wording change.
- Should state explicitly when a documentation request would be better served by the GAUSS Language Expert, Econometrics Expert, Software Engineering Expert, or a future Education Expert, rather than answering outside its own scope with unfounded confidence.

## Limitations

- This expert does not verify GAUSS syntax and should not be treated as a substitute for the GAUSS Language Expert's evidence requirements.
- This expert does not assess statistical or econometric validity and should not be treated as a substitute for the Econometrics Expert's methodological reasoning.
- This expert does not assess maintainability or design quality and should not be treated as a substitute for the Software Engineering Expert's reasoning.
- This expert cannot confirm that an example runs or that a described behavior is current — it can only recommend how to verify and present that clearly.
- This is markdown documentation, not runtime code; no engine parses or enforces this file. Activation and routing are checked by manual evaluation, the same way they are for the GAUSS Language Expert, Econometrics Expert, and Software Engineering Expert.
- Curriculum design and multi-session learning sequencing remain out of scope for this milestone — this expert recommends clear, task-oriented, or reference documentation, not a pedagogical learning path.

## Related Files

- `BODY_OF_KNOWLEDGE.md` — the structured knowledge domains this expert draws on.
- `reasoning.md` — the step-by-step reasoning workflow this expert's decision rules will operationalize.
- `best_practices.md` — the practice guidance this expert should promote.
- `common_mistakes.md` — the failure-mode list this expert should help agents avoid.
- `experts/gauss-language/EXPERT.md` and `experts/gauss-language/OPERATIONAL_PROFILE.md` — the expert this file hands off implementation-specific claims to.
- `experts/econometrics/EXPERT.md` and `experts/econometrics/OPERATIONAL_PROFILE.md` — the expert this file hands off methodological claims to.
- `experts/software-engineering/EXPERT.md` and `experts/software-engineering/OPERATIONAL_PROFILE.md` — the expert this file hands off maintainability/design claims to.
- `tools/operational_expert_interface.md` — the generic interface a future `OPERATIONAL_PROFILE.md` for this expert will fill in.

## Future Expansion

An `OPERATIONAL_PROFILE.md` has not yet been created for this expert — it is planned as the next task, per the `v0.9.0`/`v0.14.0` precedent of building the narrative foundation first. Once created, it will define this expert's activation triggers, non-activation cases, required inputs, required evidence by task type, decision rules, refusal/escalation conditions, output contract, response-visibility policy, and evaluation criteria, filling in `tools/operational_expert_interface.md` the same way the three existing operational profiles did for their experts. This file and `BODY_OF_KNOWLEDGE.md` remain the narrative foundation those operational decisions will be grounded in. Four-expert routing (activating this expert alongside the GAUSS Language Expert, Econometrics Expert, and/or Software Engineering Expert) is planned in `planning/v0.15.0-documentation-expert-foundation.md` but not yet implemented in `workflows/expert-routing.md`.
