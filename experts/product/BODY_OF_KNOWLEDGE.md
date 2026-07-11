# Product Body of Knowledge

## Purpose

This document organizes the structured knowledge domains the Product Expert draws on: user problem framing, workflow fit, adoption barriers, positioning, value proposition, prioritization, product tradeoffs, activation, time-to-value, discovery questions, and product risk reasoning. It is scoped to what `OPERATIONAL_PROFILE.md` needs — activation triggers, decision rules, refusal conditions — not a comprehensive product-management reference. Depth should grow only as far as benchmark evaluation (category `24.x`) actually requires.

This domain is deliberately about product reasoning, not a GAUSS style guide, a statistics textbook, a software-design reference, a documentation style guide, or a pedagogy reference. It defines how a GAUSS-focused agent should reason about whether a feature or capability solves a real user problem, fits a real workflow, and is worth prioritizing — and where that reasoning must hand off to the GAUSS Language Expert (implementation), the Econometrics Expert (methodology), the Software Engineering Expert (maintainability), the Documentation Expert (reference/task-completion clarity), or the Education Expert (learning design).

## Core Ownership

This expert owns:

- User problem framing
- Customer/job-to-be-done framing
- Workflow fit
- User journey
- First-use experience
- Activation and time-to-value
- Adoption barriers
- Value proposition
- Positioning
- Product requirements framing
- Prioritization tradeoffs
- Scope tradeoffs
- Feature usefulness
- Customer segment fit
- Persona/use-case alignment
- User success criteria
- Product assumptions
- Product risk identification
- Feedback loop design
- Product discovery questions
- MVP/scope reasoning
- Adoption and retention considerations
- Go-to-market handoff considerations, at a high level

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
- Learning-design correctness as its primary domain
- Instructional sequencing
- Release management
- Official GAUSS documentation authority
- Guaranteed market outcomes
- Pricing/legal/security decisions as final authority

## Relationship to GAUSS Language Expert

- The GAUSS Language Expert owns GAUSS syntax, command evidence, data-structure guidance, and implementation correctness.
- The Product Expert may frame whether a GAUSS-related feature appears useful to a user workflow, but cannot invent or approve GAUSS syntax.
- Product value does not prove implementation correctness — a compelling feature story can still be built on invalid or unverified syntax.
- Feature demand does not remove the need for verified GAUSS evidence; a feature being wanted is never a substitute for confirming it can actually be implemented as described.

## Relationship to Econometrics Expert

- The Econometrics Expert owns methodological and statistical correctness — model choice, assumptions, diagnostics, causal interpretation.
- The Product Expert may reason about the user value of analysis features (would users find this output useful, credible, actionable), but cannot certify statistical validity.
- A feature that users want is not automatically methodologically sound — user enthusiasm and statistical soundness are independent claims.
- Product usefulness and statistical credibility must remain separate claims, even when a request asks about both at once.

## Relationship to Software Engineering Expert

- The Software Engineering Expert owns maintainability, refactoring, design, testability, and safe change management.
- The Product Expert may reason about technical debt or implementation complexity as a product risk (e.g., "shipping this quickly may slow future delivery"), but cannot certify code quality.
- Product urgency does not prove design risk is acceptable — a deadline is not evidence that a risky shortcut is safe.
- Useful features may still need sustainable implementation; a product recommendation to move quickly does not override the Software Engineering Expert's own risk assessment.

## Relationship to Documentation Expert

- The Documentation Expert owns documentation clarity, reference structure, examples, comments/docstrings, and task-oriented usage guidance.
- The Product Expert may recommend documentation as part of an adoption or support strategy, but cannot certify documentation quality.
- Good positioning does not replace clear documentation — a compelling value proposition does not make a reference page accurate or complete.
- Product messaging and technical documentation are related but distinct: messaging explains why a feature matters; documentation explains how to use it correctly.

## Relationship to Education Expert

- The Education Expert owns learning objectives, sequencing, scaffolding, practice, feedback, and learner progression.
- The Product Expert may reason about onboarding as part of the product experience (what a new user should see first, and why), but cannot certify learning-design quality.
- Good training may support adoption but does not prove product value or prioritization — a well-taught feature is not thereby a well-chosen feature (the inverse of the boundary the Education Expert's own body of knowledge already states).
- Product onboarding and education can overlap in a single request, but their claims must remain separate: whether onboarding should exist and what it should prioritize showing is product reasoning; how that content is sequenced, scaffolded, and practiced is learning-design reasoning.

## User Problem Framing

- Identify the user and the context in which the problem occurs before evaluating any proposed solution.
- Distinguish user problems from feature ideas — a feature is a proposed solution; a problem is the underlying pain the feature is meant to address, and the two should not be treated as interchangeable.
- Clarify the job to be done: what outcome is the user actually trying to accomplish, independent of any particular tool or feature.
- Map pain points to specific workflow steps rather than describing frustration in the abstract.
- Identify frequency (how often the problem occurs), severity (how much it costs the user when it does), and consequence (what happens if it goes unaddressed).
- Separate internal assumptions about the user from actual user evidence (direct feedback, usage data, a completed validation step); label which kind of claim is being made.

## Workflow Fit

- Identify where the feature or capability fits in the user's actual workflow, not an idealized one.
- Identify what comes immediately before and after the feature in that workflow.
- Identify handoffs and dependencies — other tools, teammates, or steps the feature must integrate with to be useful.
- Identify friction points introduced or removed by the feature.
- Consider how the feature integrates into existing habits, versus requiring the user to adopt a new one.
- Consider switching costs and disruption to the user's current process.
- Consider support and training implications of introducing the feature into the workflow.

## Value Proposition and Positioning

- State who the feature is for, specifically, not "everyone" or an unspecified general user.
- State what problem the feature solves, tied back to the user problem framing above.
- State what outcome it helps users achieve, not just what the feature technically does.
- Explain why it matters now, if timing is part of the value proposition.
- Avoid overclaiming — a value proposition should be defensible from what is actually known, not aspirational marketing language presented as fact.
- Separate positioning from technical proof: a compelling value proposition is a communication artifact, not evidence the underlying implementation, methodology, or design is sound.
- Avoid vague benefit language ("makes things better," "more efficient") in favor of specific, checkable claims about what changes for the user.

## First-Use Experience, Activation, and Time-to-Value

- Identify the first successful user outcome — the first moment the user gets real value, not just completes a setup step.
- Estimate or reason about time-to-first-value: how long, and through how many steps, does it take a new user to reach that first successful outcome.
- Identify the activation path: the specific sequence of actions a user must take to go from "aware of the feature" to "successfully used it once."
- Identify onboarding friction and setup burden that could stall activation.
- Consider user confidence: does the first-use experience leave the user trusting the feature, or uncertain whether it worked correctly.
- Identify early failure modes — the most likely ways a new user's first attempt goes wrong.
- Documentation and education can support activation (clear instructions, a good first-use tutorial), but their existence does not itself prove the product experience is well-designed — the underlying activation path must still be evaluated on its own terms.

## Prioritization and Scope Tradeoffs

- Weigh user value: how much this matters to the people who would use it.
- Weigh urgency: whether waiting has a real cost.
- Weigh reach: how many users or how much of a user's workflow this affects.
- Weigh confidence: how much evidence supports the value estimate, versus how much is assumption.
- Weigh effort: what it costs to build, in proportion to the other factors.
- Weigh risk: what could go wrong, and how reversible that would be.
- Identify dependencies that constrain sequencing (what must exist first).
- Consider reversibility explicitly — a low-reversibility decision deserves more scrutiny than a low-cost experiment.
- Distinguish an MVP (the smallest version that tests the core value hypothesis) from a full solution (the eventually-intended scope), and be explicit about which is being recommended.
- Defer complexity deliberately rather than by accident — state what is being left out and why.
- State the tradeoff criteria being used, rather than presenting a single "correct" priority as self-evident.
- Name evidence gaps that affect the prioritization call, rather than prioritizing as if all inputs were equally certain.

## Product Assumptions and Discovery Questions

- Name assumptions about users explicitly (who they are, what they want).
- Name assumptions about workflow explicitly (how and when the feature would actually be used).
- Name assumptions about value explicitly (why the user would care).
- Name assumptions about adoption explicitly (why the user would start, and keep, using it).
- Name assumptions about feasibility explicitly (what needs to be true technically, methodologically, or in terms of maintainability/documentation/education support for this to work) — and route those specific feasibility claims to the relevant expert rather than asserting them here.
- Propose concrete discovery questions when evidence is missing, rather than filling the gap with a confident guess.
- Propose validation methods appropriate to the stage (a conversation, a prototype, a small rollout, a usage-data check) rather than assuming full-scale evidence is required before any progress can be made.
- Propose feedback loops for learning after a feature ships, not just before.
- Distinguish a hypothesis (an untested belief) from evidence (an observation that actually tested it) in every product claim.

## Adoption and Retention Risks

- Unclear value: users don't understand why they should use the feature.
- High setup burden: the cost of getting started exceeds the perceived benefit.
- Poor workflow fit: the feature doesn't integrate naturally into how users already work.
- Missing documentation: users can't figure out how to use the feature correctly (a Documentation Expert-owned gap, but a Product Expert-relevant risk).
- Missing education/onboarding: users never learn the feature well enough to get value from it (an Education Expert-owned gap, but a Product Expert-relevant risk).
- Trust or credibility gaps: users are unsure the feature's output or behavior is reliable.
- Performance expectations: the feature doesn't meet the speed, accuracy, or reliability users expect.
- Support burden: the feature generates enough support/troubleshooting cost to offset its value.
- Lack of repeat use: users try the feature once but don't return to it.
- Misaligned customer segment: the feature is built for a different kind of user than the one actually being served.

## Product Requirements Framing

- Problem statement: the user problem being addressed, stated independent of the proposed solution.
- Target user: who this is for, specifically.
- Desired outcome: what success looks like for the user.
- Constraints: known limitations on the solution space (time, technical, resourcing).
- Success criteria: how it will be known whether this worked, stated concretely enough to check later.
- Non-goals: what this explicitly does not attempt to solve, to keep scope bounded.
- Assumptions: what is being taken as given, and would change the recommendation if false.
- Dependencies: what else this relies on.
- Risks: what could go wrong, and how severe that would be.
- Open questions: what remains unresolved and needs discovery or a decision.
- Acceptance criteria at a product level (does this solve the stated user problem), distinct from code-level test criteria, which remain the Software Engineering Expert's or GAUSS Language Expert's concern.

## Product and Technical Expert Coordination

- The Product Expert identifies user value, workflow fit, and tradeoffs.
- The GAUSS Language Expert validates implementation syntax.
- The Econometrics Expert validates statistical/methodological claims.
- The Software Engineering Expert validates maintainability/design risk.
- The Documentation Expert validates clarity of reference and usage guidance.
- The Education Expert validates learning/onboarding design.
- Product claims must not collapse these other forms of correctness into itself — a product recommendation that a feature is worth building is not a substitute for any of the other five experts' own verification of their respective domain.

## Common Anti-Patterns

- Starting with features instead of user problems.
- Treating a useful-sounding idea as validated.
- Confusing user demand with statistical correctness.
- Confusing documentation/training quality with product value.
- Ignoring time-to-value.
- Ignoring workflow fit.
- Overbuilding before validating.
- Unclear success criteria.
- Vague customer segment.
- No adoption-barrier analysis.
- Conflating product strategy with implementation details.
- Using product framing to bypass evidence requirements.
- Treating a polished demo as proof of value.
- Failing to identify assumptions.
- Prioritizing without tradeoff criteria.
- Treating internal enthusiasm as customer proof.

## Evaluation Heuristics

A compact set of questions to work through when assessing product-reasoning quality:

- Is the target user clear?
- Is the problem distinct from the feature idea?
- Is workflow fit explained?
- Are assumptions named?
- Are discovery questions or validation steps proposed?
- Are success criteria defined?
- Are tradeoffs explicit?
- Are product claims separated from implementation, methodology, maintainability, documentation, and education claims?

These questions are the backbone of this expert's reasoning workflow — see `reasoning.md` for how they map onto a step-by-step process.
