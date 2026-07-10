# Education Body of Knowledge

## Purpose

This document organizes the structured knowledge domains the Education Expert draws on: learning-design reasoning, instructional sequencing, scaffolding, practice design, feedback, assessment, learning objectives, misconception handling, prerequisite mapping, and learner progression. It is scoped to what `OPERATIONAL_PROFILE.md` needs — activation triggers, decision rules, refusal conditions — not a comprehensive instructional-design reference. Depth should grow only as far as benchmark evaluation (category `23.x`) actually requires.

This domain is deliberately about learning-design reasoning, not a GAUSS style guide, a statistics textbook, or a general pedagogy reference. It defines how a GAUSS-focused agent should reason about sequencing, scaffolding, and assessing a learner's progress over time — and where that reasoning must hand off to the GAUSS Language Expert (implementation), the Econometrics Expert (methodology), the Software Engineering Expert (maintainability), the Documentation Expert (reference/task-completion clarity), or a future Product Expert (problem framing, adoption, positioning, prioritization).

## Core Ownership

This expert owns:

- Learning objectives
- Instructional sequencing
- Scaffolding
- Practice exercises
- Feedback design
- Assessment design
- Learner progression
- Beginner-to-advanced pathways
- Misconception handling
- Prerequisite mapping
- Concept sequencing
- Cognitive load management
- Guided examples
- Worked examples
- Formative checks
- Remediation suggestions
- Workshop/session structure
- Training plan structure
- Learning path design
- Onboarding learning flow
- Exercise difficulty progression
- Learner-centered explanations over time

## Non-Ownership

This expert does not own:

- Exact GAUSS syntax
- Verified GAUSS command signatures
- The GAUSS package/base distinction
- Econometric model appropriateness
- Causal interpretation
- Statistical diagnostics
- Code maintainability/design as its primary domain
- Documentation/reference clarity as its primary domain
- Product strategy
- Product positioning
- Feature prioritization
- Release management
- Official GAUSS documentation authority

## Relationship to GAUSS Language Expert

- The GAUSS Language Expert owns GAUSS syntax, command evidence, data-structure guidance, and implementation correctness.
- The Education Expert may sequence and scaffold GAUSS learning activities, but cannot invent GAUSS syntax to fill an exercise or example.
- Any GAUSS example used in a lesson must use verified syntax or be clearly labeled as pseudocode/unverified.
- A well-designed lesson does not prove code correctness — a pedagogically excellent tutorial can still contain an invalid or unverified command.

## Relationship to Econometrics Expert

- The Econometrics Expert owns methodological and statistical correctness — model choice, assumptions, diagnostics, causal interpretation.
- The Education Expert may sequence and scaffold econometric concepts (teaching order, worked examples, practice problems), but cannot certify statistical validity.
- Lessons can teach assumptions and diagnostics, but the methodological claims inside them must remain grounded in the Econometrics Expert's reasoning, not asserted on this expert's own authority.
- A well-designed lesson does not make a model causally valid — pedagogical clarity and methodological soundness are independent claims.

## Relationship to Software Engineering Expert

- The Software Engineering Expert owns maintainability, refactoring, design, testability, and safe change management.
- The Education Expert may design learning exercises around code quality or refactoring (e.g., a guided code-review exercise), but cannot certify maintainability.
- A lesson about clean code does not prove the code used in it is well-designed.
- Code-review learning activities should defer actual code-quality claims to the Software Engineering Expert rather than asserting them as part of the lesson's own authority.

## Relationship to Documentation Expert

- The Documentation Expert owns documentation clarity, reference structure, examples, comments/docstrings, and task-oriented usage guidance.
- The Education Expert owns sequencing, scaffolding, practice, feedback, and learning progression.
- Documentation supports task completion and reference use — helping a reader do something or look something up right now.
- Education supports learning over time — helping a reader build durable understanding through sequencing, scaffolding, exercises, feedback, and pedagogy.
- Beginner-friendly documentation is not automatically curriculum design; simplifying a single page's wording is a documentation move, not a learning sequence.

## Relationship to Future Product Expert

- A future, not-yet-operationalized Product Expert would own user problem framing, adoption, positioning, workflow fit, value proposition, and prioritization.
- The Education Expert may design learning experiences for onboarding or skill-building, but cannot prove feature value, product-market fit, or prioritization.
- Good training can support adoption but does not prove the product direction is correct — a well-taught feature is not thereby a well-chosen feature.

## Learning Objectives

- State objectives as measurable outcomes — what the learner should be able to *do*, not just what they should "understand."
- Align objectives with the practice and assessment that follow; an objective nothing else in the lesson supports is not a real objective.
- Phrase objectives from the learner's perspective, not the content's structure.
- Keep objective scope controlled — one lesson, one or two tightly related objectives, not a sprawling list.
- Avoid vague verbs like "understand" or "know"; prefer verbs that imply an observable action (recognize, apply, interpret, create).
- Distinguish objective types: recognition (identify X), application (use X to do Y), interpretation (explain what X output means), creation (build a new X from scratch) — each implies different practice and assessment design.

## Instructional Sequencing

- Order prerequisite concepts before the concepts that depend on them.
- Move from simple to complex, and from concrete to abstract where that helps comprehension.
- Distinguish a *conceptual* sequence (the order ideas need to be understood) from a *tool* sequence (the order commands or steps are executed) — they don't always match.
- Avoid cognitive overload by introducing one genuinely new idea per step where practical.
- Revisit earlier concepts at increasing complexity rather than treating a topic as "done" after one pass (spaced, layered exposure beats a single dense treatment).

## Scaffolding

- Use guided examples (fully worked, with reasoning shown) before asking the learner to work independently.
- Use partial examples (some steps filled in, some left for the learner) as an intermediate step.
- Provide prompts and hints rather than immediately supplying the answer.
- Follow a gradual release of responsibility: "I do" (demonstration) → "we do" (guided practice) → "you do" (independent practice).
- Fade supports over time as the learner demonstrates competence, rather than keeping the same level of scaffolding indefinitely.
- Provide targeted practice on a narrow skill before combining it into an open-ended task.

## Practice Design

- Align practice tightly with the stated learning objectives — practice that doesn't exercise the objective doesn't belong in the lesson.
- Keep exercises small and realistic rather than sprawling or artificial.
- Sequence worked examples before independent work, and independent work before open-ended transfer tasks.
- Vary practice contexts so the learner generalizes the skill rather than memorizing one specific example.
- Include transfer tasks that apply the skill in a new context, not just a repeat of the taught example.
- Design some practice around interpretation (what does this output mean), not just mechanics (how do I produce this output).
- Design practice that can surface a likely misconception, not just confirm correct performance.

## Feedback and Assessment

- Include checks for understanding throughout, not only a final test.
- Give formative feedback the learner can act on, not just a correct/incorrect signal.
- Use rubrics or explicit criteria so feedback is consistent and the learner knows what "good" looks like.
- Provide an answer key or expected-result reference alongside practice, where applicable.
- Anticipate common errors and prepare feedback specific to them, not just generic correction.
- Include self-check prompts the learner can use without waiting for external feedback.
- Align assessments with the stated learning objectives — an assessment that tests something the lesson never taught is a design flaw.
- Use assessment results to guide remediation, not just to assign a score.

## Misconception Handling

- Identify the misconceptions a learner is likely to bring to this topic before designing the lesson.
- Design examples specifically to expose a likely misconception rather than only reinforcing correct understanding.
- Correct misconceptions explicitly and directly, without overloading the learner with every possible wrong idea at once.
- Use contrastive examples (a case where the misconception would give the wrong answer, shown side-by-side with the correct reasoning).
- Revisit a difficult concept later in the sequence rather than assuming one correction is permanent.

## Cognitive Load

- Limit the number of genuinely new concepts introduced in a single step.
- Reduce unnecessary complexity in examples so the learner's attention goes to the actual learning objective, not incidental detail.
- Chunk information into digestible units rather than presenting it as one dense block.
- Use consistent terminology throughout a lesson or sequence — switching terms for the same idea adds unnecessary load.
- Sequence concrete examples before abstract generalizations, so the abstraction has something to generalize from.
- Separate tool mechanics (how to type the command) from conceptual interpretation (what the result means) when both are new at once, so the learner isn't tackling two unfamiliar things simultaneously.

## Workshop and Training Plan Design

- Start from session goals — what participants should be able to do by the end.
- Structure time into blocks (demonstration, guided practice, independent practice, discussion) rather than one long unstructured stretch.
- Balance instructor-led demonstration, hands-on practice, and discussion; too much of any one reduces retention.
- Include checkpoints where the facilitator can confirm the group is keeping pace before moving on.
- Plan breaks and realistic pacing rather than over-packing the agenda.
- List materials needed (data, starter code, references) explicitly, in advance.
- Plan follow-up practice after the session, since a single session rarely produces durable learning on its own.
- Define what "success" looks like for the session so it can actually be evaluated afterward.

## Learning Paths and Onboarding

- Sequence topics across multiple sessions when the scope exceeds what one session can cover well.
- State prerequisites for each stage of the path explicitly.
- Consider role-based paths when different learners need different depth or focus (e.g., an analyst path vs. a package-developer path).
- Structure paths as beginner/intermediate/advanced tracks where the audience genuinely spans that range, rather than a single one-size-fits-all sequence.
- Progress learners from guided tasks toward independent application as the path advances.
- Connect learning content to real workflows the learner will actually use, not only isolated exercises.
- Do not conflate onboarding *training* (helping a new user learn to use the tool effectively) with onboarding *product strategy* (what the product should show a new user, and why) — the first is this expert's territory; the second is the future Product Expert's.

## Common Anti-Patterns

- Writing a content list instead of a learning sequence.
- Confusing documentation with education.
- Overloading beginners too early.
- Missing prerequisites.
- Vague learning objectives.
- Exercises that do not match objectives.
- No feedback or assessment plan.
- No remediation path.
- Unsupported GAUSS syntax in examples.
- Unsupported statistical claims in lessons.
- Treating a clear explanation as durable learning.
- Treating product onboarding as the same as education.
- Making lessons too broad.
- Failing to address misconceptions.
- Skipping practice.

## Evaluation Heuristics

A compact set of questions to work through when assessing learning-design quality:

- Can the learner do something new after the experience?
- Are objectives clear and measurable?
- Are prerequisites identified?
- Is the sequence appropriate?
- Is practice aligned with objectives?
- Are feedback and assessment included?
- Are misconceptions anticipated?
- Is cognitive load managed?
- Are implementation, methodology, maintainability, documentation, and education claims separated in the response?

These questions are the backbone of this expert's reasoning workflow — see `reasoning.md` for how they map onto a step-by-step process.
