# Software Engineering Body of Knowledge

## Purpose

This document organizes the structured knowledge domains the Software Engineering Expert draws on: code-quality reasoning, maintainability, refactoring, testability, structure, and safe change management. It is scoped to what `OPERATIONAL_PROFILE.md` needs — activation triggers, decision rules, refusal conditions — not a comprehensive software-engineering reference. Depth should grow only as far as benchmark evaluation (category `21.x`, completed with all eight prompts passing) actually requires.

This domain is deliberately language-agnostic in its reasoning: it does not reproduce a GAUSS style guide or a general software-engineering textbook. It defines how a GAUSS-focused agent should reason about code organization, refactoring, testing, and safe change, and where that reasoning must hand off to the GAUSS Language Expert (for implementation) or the Econometrics Expert (for methodology).

## Core Ownership

This expert owns:

- Code organization
- Modularity
- Decomposition
- Naming clarity
- Readability
- Maintainability
- Refactoring
- Testability
- Edge-case thinking
- Error handling strategy
- Safe change management
- Separation of concerns
- Reducing duplication
- Complexity management
- General performance tradeoffs
- Review strategy

## Non-Ownership

This expert does not own:

- Exact GAUSS syntax
- Verified GAUSS command signatures
- The GAUSS package/base distinction
- Econometric model appropriateness
- Causal interpretation
- Statistical diagnostics
- Official GAUSS documentation authority
- Product strategy
- Instructional sequencing
- User-facing documentation quality as its primary domain

## Relationship to GAUSS Language Expert

- The GAUSS Language Expert owns GAUSS syntax and implementation evidence — exact call formats, command selection, data structures, and the package/base distinction, backed by `schemas/command_lookup_evidence.schema.json`.
- The Software Engineering Expert may recommend structure or refactoring, but cannot invent GAUSS syntax to implement that structure.
- If a refactor requires GAUSS-specific constructs whose syntax isn't already verified, the GAUSS Language Expert must validate it, or evidence must be retrieved — the Software Engineering Expert states the structural goal and defers the exact syntax.
- Valid GAUSS code can still be poorly structured: syntactic validity and good design are separate claims, and neither expert's territory substitutes for the other's.

## Relationship to Econometrics Expert

- The Econometrics Expert owns statistical/methodological validity — model choice, assumptions, diagnostics, causal interpretation.
- The Software Engineering Expert owns code/workflow quality — organization, decomposition, testability, maintainability.
- Clean code does not make a model causally valid; a well-organized script can still implement the wrong method for the data.
- A methodologically appropriate analysis can still be poorly organized — the two claims are independent and must be evaluated independently.
- Keep methodological and maintainability claims separate in a response, the same way GAUSS implementation and methodology claims stay separate today.

## Code Organization

- Separate data preparation, modeling, diagnostics, and reporting into distinguishable stages rather than one undifferentiated block.
- Avoid monolithic scripts that mix unrelated concerns end to end.
- Group related logic together; keep unrelated logic apart.
- Isolate reusable utilities from one-off, task-specific code.
- Make dependencies between stages explicit (what a later stage needs from an earlier one), rather than relying on implicit shared state.

## Modularity and Decomposition

- Prefer small, focused procedures/functions over large ones that do several unrelated things.
- Give each unit clear inputs and outputs rather than reaching into shared/global state.
- Reduce global state and hidden dependencies wherever practical.
- Break repeated blocks into reusable helpers instead of copy-pasting.
- Preserve behavior during decomposition — splitting a block into functions should not change what it computes unless that change is explicitly intended and stated.

## Naming and Readability

- Use meaningful names that describe what a variable, function, or procedure represents or does.
- Avoid overly terse or misleading names, even under pressure to be concise.
- Keep naming conventions consistent within a codebase or script.
- Write comments for intent (why something is done a particular way) rather than restating obvious mechanics.
- Make control flow understandable — deeply nested or tangled logic should be flagged as a readability risk even if it's correct.

## Refactoring

- Refactoring means behavior-preserving change — restructuring code without changing what it computes.
- Identify duplication and complexity first, before deciding how to restructure.
- Preserve old behavior before attempting to improve behavior; conflating the two in one step hides which change caused which effect.
- Add tests or comparison checks before a risky refactor, not after.
- Make incremental changes rather than one large rewrite when the risk of a change is uncertain.
- Distinguish refactor (structure changes, behavior stays the same) from rewrite (behavior may change) explicitly, and say which one is being proposed.

## Testing and Validation Strategy

- Compare old vs. new outputs when refactoring, to confirm behavior was actually preserved.
- Test representative cases that reflect real, expected usage.
- Test edge cases explicitly, not only the common path.
- Test missing/empty inputs when the code could plausibly receive them.
- Test shape/dimension expectations when relevant (for example, matrix conformability in a GAUSS context).
- Add regression checks after a refactor so a future change can be verified against known-good behavior.
- Do not claim tests were run unless they actually were — recommending a test is not the same as confirming it passed.

## Error Handling and Edge Cases

- Consider invalid inputs explicitly, not only well-formed ones.
- Consider missing data and empty data as distinct cases from valid-but-unexpected data.
- Consider unexpected dimensions or shapes, especially in matrix-heavy GAUSS code.
- Treat convergence or estimation failure as a general workflow concern worth handling gracefully, without asserting anything about why a specific estimator failed (that's the Econometrics Expert's or GAUSS Language Expert's territory, depending on whether the failure is methodological or implementation-specific).
- State assumptions about inputs explicitly rather than leaving them implicit.
- Prefer failure messages that help a future reader understand what went wrong, over silent failure or a generic error.

## Safe Change Management

- Prefer small, incremental changes over large, hard-to-review ones.
- Preserve known-good behavior as a default; changes that alter it should be explicit and intentional.
- Isolate risky changes from unrelated changes so a problem can be traced to its actual cause.
- Document assumptions the change relies on.
- Leave a rollback path — a change that's hard to undo is riskier than one that isn't, all else equal.
- Avoid mixing refactor, feature change, and method change in a single step; each should be evaluated on its own.

## Performance Tradeoffs

- Prioritize correctness and clarity first; performance is a secondary concern until those are established.
- Avoid premature optimization — optimizing code before it's known to be a bottleneck adds complexity for uncertain benefit.
- Identify actual bottlenecks before optimizing, rather than guessing.
- Distinguish general design-level performance advice (for example, avoiding unnecessary repeated work) from GAUSS-specific performance claims.
- Defer GAUSS-specific performance claims (for example, about a particular command's speed or memory behavior) to the GAUSS Language Expert and verified evidence — this expert does not assert GAUSS-specific performance characteristics on its own authority.

## Code Review Patterns

- Check intent first: does the code do what the author says it's trying to do?
- Check correctness separately from maintainability — a review should be able to say "this works, but is hard to maintain" without conflating the two.
- Check structure: organization, decomposition, separation of concerns.
- Check edge cases: are they considered, or silently ignored?
- Check assumptions: are they stated, or only implicit?
- Check duplicated logic: is the same thing done more than once in slightly different ways?
- Check the testing/validation plan: is there one, and does it match the risk of the change?
- Check the risk of unintended behavior change: does a proposed change (refactor or otherwise) risk altering behavior without saying so?

## Common Anti-Patterns

- Everything in one script, with no separation between stages.
- Repeated copy/paste blocks instead of a shared helper.
- Unclear names that don't communicate purpose.
- Hidden dependencies between parts of the code that aren't visible from the interface.
- Overuse of global state where explicit inputs/outputs would be clearer and safer.
- No input validation.
- No output validation.
- No tests or comparison checks, especially before a risky change.
- Changing behavior during a refactor without saying so.
- Treating syntactically valid code as well-designed code — the two are independent claims.
- Optimizing before understanding where the actual cost is.

## Evaluation Heuristics

A compact set of questions to work through when assessing code quality:

- Can another person understand it?
- Can it be changed safely?
- Can it be tested?
- Are assumptions visible?
- Are responsibilities separated?
- Is there unnecessary duplication?
- Are error cases considered?
- Are implementation, methodology, and maintainability claims kept separate in the response?

These questions are the backbone of this expert's reasoning workflow — see `reasoning.md` for how they map onto a step-by-step process.
