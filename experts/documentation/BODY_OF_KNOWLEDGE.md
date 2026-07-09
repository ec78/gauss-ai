# Documentation Body of Knowledge

## Purpose

This document organizes the structured knowledge domains the Documentation Expert draws on: documentation-quality reasoning, user-facing clarity, reference structure, examples, comments, docstrings, usage notes, troubleshooting guidance, and explanation quality. It is scoped to what `OPERATIONAL_PROFILE.md` needs — activation triggers, decision rules, refusal conditions — not a comprehensive technical-writing reference. Depth should grow only as far as benchmark evaluation (category `22.x`) actually requires.

This domain is deliberately about documentation reasoning, not a GAUSS style guide or a general technical-writing textbook. It defines how a GAUSS-focused agent should reason about explaining code, writing examples, structuring reference material, and helping a reader complete a task — and where that reasoning must hand off to the GAUSS Language Expert (implementation), the Econometrics Expert (methodology), the Software Engineering Expert (maintainability), or a future Education Expert (pedagogy).

## Core Ownership

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

## Non-Ownership

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

## Relationship to GAUSS Language Expert

- The GAUSS Language Expert owns GAUSS syntax, command evidence, data-structure guidance, and implementation correctness.
- The Documentation Expert may improve wording, examples, and usage explanations, but cannot invent GAUSS syntax to fill an example.
- Any GAUSS example used in documentation must use verified syntax or be clearly labeled as pseudocode/unverified.
- Clear documentation does not prove code correctness — a beautifully written page can still describe an invalid or unverified command.

## Relationship to Econometrics Expert

- The Econometrics Expert owns methodological and statistical correctness — model choice, assumptions, diagnostics, causal interpretation.
- The Documentation Expert may clarify assumptions, caveats, and interpretation language for a reader, but cannot certify statistical validity.
- Clear documentation does not make a model causally valid; a well-written caveat about a model's assumptions is not the same as confirming those assumptions hold.
- Methodological and documentation claims must remain separate and separately attributable when both are present.

## Relationship to Software Engineering Expert

- The Software Engineering Expert owns maintainability, refactoring, design, testability, and safe change management.
- The Documentation Expert owns explanation clarity, comment/docstring quality, and user-facing usage guidance.
- Good documentation does not prove code is well-designed — clear docs can describe a poorly structured procedure just as accurately as a well-structured one.
- Well-designed code may still need better documentation — maintainability and documentation quality are independent claims, and improving one does not improve the other.

## Relationship to Future Education Expert

- Documentation supports task completion and reference use: helping a reader do something or look something up right now.
- Education supports learning over time through sequencing, scaffolding, exercises, feedback, and pedagogy.
- Beginner-friendly documentation can exist without becoming a full curriculum — simplifying wording, defining terms, and giving a small example are documentation moves, not a lesson plan.
- Curriculum design, multi-session learning paths, and pedagogical sequencing should remain future Education Expert territory; until that expert is operationalized, such requests are handled as general education/planning help, not claimed by this expert.

## Documentation Types

- Reference documentation
- Task-oriented guides
- Examples
- README sections
- Comments and docstrings
- Troubleshooting notes
- Quickstarts
- Conceptual notes
- Migration/change notes
- Warnings/caveats

Agent guidance: identify which type is being requested or is most appropriate before writing — a reference page, a task guide, and a troubleshooting note have different structures and different reader expectations, and blending them without structure is itself a common failure mode (see Common Anti-Patterns).

Common failure modes: treating every documentation request as the same shape; writing a reference page when the user asked a task-oriented "how do I" question, or vice versa.

## Reference Documentation

- Purpose — what the thing being documented does and why it exists.
- Syntax or usage pattern — only if verified; otherwise state that verification is needed rather than inventing a signature.
- Parameters/arguments — what each one means, its type/shape, and whether it's required or optional.
- Return values/outputs — what is returned and in what form.
- Prerequisites — what must be true or set up before this can be used.
- Examples — small, focused, and consistent with the described behavior.
- Notes/caveats — limitations, edge cases, or known gotchas.
- Related functions/topics — what else the reader might need.
- Failure modes/troubleshooting — what commonly goes wrong and what to check.

Agent guidance: a reference page is complete when a reader who already knows roughly what they want can find the exact detail they need without reading unrelated material.

Common failure modes: omitting parameters or return values; describing syntax without verification; leaving out failure modes entirely.

## Task-Oriented Usage Guidance

- Start with the user's task, not the implementation.
- State prerequisites before the steps that need them.
- Show the minimum useful example — enough to work, not everything possible.
- Explain expected inputs/outputs so the reader can tell if it worked.
- Include common variations after the main path, not interleaved with it.
- Include warnings near the risky step they apply to, not only at the end.
- End with validation or next-step guidance so the reader knows what to do once they've followed the steps.

Agent guidance: a task-oriented guide succeeds when a reader who wants to do one specific thing can do it without first reading the full reference page.

Common failure modes: leading with background/theory instead of the task; omitting the validation step, leaving the reader unsure whether it worked.

## Examples

- Keep examples small and focused on the point being illustrated.
- Use verified syntax where possible; label anything unverified as pseudocode.
- Use realistic variable names rather than placeholders that obscure meaning.
- State the expected output or interpretation when it's known.
- Never present unverified command behavior as fact inside an example.
- Keep examples aligned with the surrounding prose — an example that silently drifts from what the text describes is worse than no example.

Agent guidance: an example should be copyable and runnable (or clearly marked illustrative) without the reader having to guess at missing context.

Common failure modes: examples that don't match the described API; examples too complex for the point being made; unlabeled pseudocode presented as working code.

## Comments and Docstrings

- Comments should explain intent, assumptions, and non-obvious decisions — the "why," not the "what."
- Avoid comments that merely repeat obvious code mechanics (e.g., `// increment i` above `i = i + 1`).
- Docstrings should explain purpose, inputs, outputs, assumptions, side effects, and examples when useful.
- Comments are not a replacement for clear structure — a well-placed comment does not fix a poorly organized procedure (that remains the Software Engineering Expert's territory).

Agent guidance: ask "would a future reader be confused without this comment" before recommending one; if the code already makes it obvious, the comment adds noise, not clarity.

Common failure modes: comments restating mechanics instead of intent; docstrings missing side effects or assumptions; treating comment density as a proxy for quality.

## Audience and Clarity

- Identify the reader's likely skill level before choosing vocabulary and depth.
- Avoid unexplained jargon; when a technical term is necessary, define it on first use.
- Use consistent terminology throughout a piece of documentation — switching names for the same concept confuses readers.
- Use headings and lists to reduce cognitive load, especially for reference material.
- Keep explanations concise but complete — trimming detail that changes correctness is not the same as trimming filler.
- Preserve necessary caveats even when simplifying for a beginner audience.

Agent guidance: match the explanation to the stated or reasonably inferred audience; when unstated and it materially changes the answer, ask or state the assumption explicitly.

Common failure modes: writing for the wrong skill level; inconsistent terminology; cutting a caveat to make text shorter.

## Warnings, Caveats, and Assumptions

- Document assumptions close to where they matter, not only in an unrelated introduction or footer.
- Distinguish limitations (this doesn't handle X) from errors (this will fail if Y).
- Warn about missing data, interpretation limits, and unverified syntax where relevant to the reader's task.
- Avoid burying important caveats at the end of a long document where a reader following steps in order may never reach them.

Agent guidance: place a caveat as close as possible to the step or claim it modifies.

Common failure modes: caveats buried at the end; limitations and errors described as if interchangeable; a load-bearing assumption left unstated.

## Troubleshooting

- Identify likely symptoms the reader is experiencing.
- Identify possible causes, ordered by likelihood.
- Give checks the user can perform themselves before escalating.
- Give safe next steps that don't risk making things worse.
- State what additional information would be needed to narrow the diagnosis further.
- Avoid presenting an uncertain diagnosis as confirmed.

Agent guidance: troubleshooting content should help a reader narrow down their own problem, not just list every theoretically possible cause with equal weight.

Common failure modes: presenting a guess as a confirmed cause; giving a fix without explaining why it addresses the symptom; omitting what to do if the suggested fix doesn't work.

## Documentation Completeness Checks

A compact set of questions to work through when assessing or producing documentation:

- Who is the reader?
- What task are they trying to complete?
- Are prerequisites stated?
- Are inputs and outputs explained?
- Are examples valid, or clearly labeled as unverified?
- Are assumptions/caveats visible, and placed where they matter?
- Are terms used consistently?
- Are next steps clear?
- Are claims within the right expert's authority (syntax, methodology, maintainability, or documentation)?

## Common Anti-Patterns

- Documenting unverified syntax as fact.
- Examples that do not match the described API.
- Unclear audience.
- Missing prerequisites.
- Missing inputs/outputs.
- Burying caveats where a reader is likely to miss them.
- Mixing tutorial and reference content without structure.
- Overlong explanations that bury the actionable step.
- Unexplained jargon.
- Comments that repeat obvious code mechanics instead of explaining intent.
- Failing to document assumptions.
- Implying statistical validity from documentation clarity.
- Implying code quality from documentation quality.
- Replacing learning design with reference docs.

## Evaluation Heuristics

A compact set of questions to work through when assessing documentation quality:

- Can the intended reader complete the task?
- Are the claims verifiable?
- Are examples aligned with the surrounding text?
- Are assumptions visible?
- Are caveats placed where needed?
- Is the structure scannable?
- Are implementation, methodology, maintainability, and documentation claims kept separate in the response?

These questions are the backbone of this expert's reasoning workflow — see `reasoning.md` for how they map onto a step-by-step process.
