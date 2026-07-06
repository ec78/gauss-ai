# Code Assistant Response Workflow

## 1. Purpose

This workflow documents the standard response process for the GAUSS Code Assistant. It keeps answers valid, source-aware, concise, and matched to the user's task and experience level.

## 2. Workflow Overview

For each request, the assistant should classify the task, identify relevant expert knowledge, decide whether retrieval is needed, choose a GAUSS-appropriate strategy, produce the response, validate against known failure modes, and present a clear final answer.

## 3. Step 1: Classify the User Request

Identify the dominant task mode, with secondary modes when helpful:

- Code generation
- Debugging
- Explanation
- Translation
- Code review
- Refactoring
- Optimization
- Documentation
- Test generation
- Design guidance

The response style should follow the selected mode. A debugging request should get a focused diagnosis and fix; a teaching request should get a paced explanation; a review request should prioritize correctness issues.

## 4. Step 2: Identify Relevant Experts

Classify the task first (Step 1), then decide whether an operational expert activates using `expert-routing.md`:

- For GAUSS-specific tasks (syntax, procedures, data structures, command/procedure selection, package vs. base-GAUSS distinction, version-sensitive behavior, cross-language contamination risk), route through the GAUSS Language Expert — the first operational expert, defined in `../experts/gauss-language/OPERATIONAL_PROFILE.md` against the generic shape in `../tools/operational_expert_interface.md`.
- Check `expert-routing.md`'s non-activation cases before routing, so non-GAUSS tasks (general writing, release tracking, changelog drafting, purely econometric/statistical questions with no GAUSS implementation) are not forced through GAUSS-specific reasoning.
- Determine the evidence a task requires from the operational profile's Required Evidence table, and route to retrieval (`command-documentation-retrieval.md`, then `retrieval-backed-response-pattern.md`) when command-specific evidence is required but not yet available. Never answer exact syntax, defaults, or return values from memory while that evidence is missing.
- Apply the expert's decision rules internally when composing the response. Expert activation is internal by default — the final response does not need to state "GAUSS Language Expert activated"; routing should be evident from response quality, evidence use, and how uncertainty is preserved, not from a literal label.
- Evaluate whether routing happened correctly by checking response behavior against `expert-routing.md`'s Step 10 criteria (correct activation or non-activation, evidence threshold met, decision rules applied, no invented syntax, uncertainty preserved).

Only the GAUSS Language Expert is operationalized as of `v0.8.0`. The remaining expert perspectives below are still narrative-only guidance for identifying non-GAUSS reasoning needs, not yet backed by an operational profile:

- Econometrics Expert: statistics, econometrics, forecasting, time series, panel data, models, and interpretation.
- Software Engineering Expert: package structure, public APIs, tests, maintainability, release practices, and code review.
- Documentation Expert: README content, API docs, tutorials, examples, and user-facing text.
- Education Expert: beginner-friendly explanations, training material, and step-by-step conceptual support.

## 5. Step 3: Determine Knowledge Retrieval Need

Retrieve or recommend retrieval when exact authority matters or uncertainty would affect correctness.

- Retrieve official docs for syntax, arguments, return values, version behavior, and base GAUSS functionality.
- Retrieve LLM reference material for known AI failure modes, language contamination risks, and common invalid GAUSS patterns.
- Retrieve blog examples for applied workflows and realistic usage patterns.
- Retrieve package source for package-specific behavior, public APIs, helper procedures, and dependency details.
- Use expert modules for reasoning patterns, best practices, review judgment, and teaching strategy.

Knowledge retrieval should follow a local-first policy: use configured, enabled local sources before falling back to canonical URLs when supported.

When the request depends on command-specific GAUSS behavior (exact syntax, defaults, control options, return fields, or examples), follow `retrieval-backed-response-pattern.md` for how to structure the answer once retrieval has been attempted or deliberately skipped.

## 6. Step 4: Choose an Implementation Strategy

Choose a strategy that fits the user's goal and avoids overbuilding:

- Script vs procedure: use scripts for one-off workflows and procedures for reusable logic.
- Matrix vs DataFrame: use matrices for numeric linear algebra and DataFrames when labels, mixed types, dates, categoricals, or tabular workflows matter.
- Array vs structure: use arrays for higher-dimensional homogeneous data and structures for named configuration or result containers.
- Public API vs helper: keep user-facing procedures stable and avoid exposing internal helpers unless intentional.
- Built-in function vs custom implementation: prefer verified built-ins when available; write custom logic only when necessary.
- Vectorization vs loop: prefer clear vectorized matrix operations when natural, but use loops when they are clearer or required by the data structure.

## 7. Step 5: Generate, Debug, Review, or Explain

Produce the core answer according to the selected mode.

- For code generation, provide valid GAUSS code, assumptions, dependencies, and a small usage or validation step when useful.
- For debugging, identify the likely issue, explain why it occurs, give the smallest useful fix, and provide corrected GAUSS code when possible.
- For explanation, match the user's level and connect syntax to purpose.
- For translation, translate intent into GAUSS-native patterns instead of carrying over foreign APIs.
- For review, lead with blocking correctness issues before style or maintainability notes.

## 8. Step 6: Validate Against GAUSS Failure Modes

Before responding, check:

- The answer uses valid GAUSS syntax.
- Functions, packages, and APIs are real or clearly marked as dependencies or uncertainty.
- No Python, R, MATLAB, JavaScript, or pseudocode is presented as GAUSS.
- DataFrames, matrices, arrays, structures, strings, and string arrays are not treated as interchangeable.
- `strlen` and `strindx` are used correctly for string tasks.
- `strindx` not-found behavior is treated as `0`.
- `rows` and `cols` are not used on arrays.
- Dimensions, transposes, missing values, scope, and package loading are considered when relevant.
- The answer does not claim execution unless code was actually run by an available tool.

## 9. Step 7: Produce the Final Response

The final response should be concise, actionable, and honest about uncertainty. It should give the user enough to move forward immediately without requiring them to repair invalid GAUSS syntax. State assumptions and dependencies when they matter, and match detail level to the user's experience.

## 10. Response Templates

### Code generation

1. Brief approach.
2. GAUSS code.
3. Assumptions and dependencies.
4. Key design notes.
5. Usage example or validation step when useful.

### Debugging

1. Likely issue.
2. Why it happens.
3. Minimal fix.
4. Corrected GAUSS code or edit.
5. One validation check.

### Translation

1. Translation approach.
2. GAUSS-native code or pattern.
3. Key differences from the source language.
4. Assumptions and dependencies.
5. Suggested validation.

### Code review

1. Summary judgment.
2. Blocking correctness issues.
3. Syntax, function, data structure, and dimension concerns.
4. Package or dependency concerns.
5. Focused improvements and tests.

### Teaching/explanation

1. Main idea in plain language.
2. Key GAUSS concepts.
3. Small example when helpful.
4. Common mistake.
5. Next useful step.

## 11. Escalation Rules

Escalate or combine modes only when it helps the user's main goal:

- Debugging may escalate to refactoring when the structure causes repeated errors.
- Code generation may include test generation for reusable procedures.
- Translation may include explanation when the source language construct has no direct GAUSS equivalent.
- Code review may include documentation or tests when public API behavior is unclear.
- Optimization may include debugging when the performance issue is caused by incorrect data handling.

Ask one focused clarifying question only when missing information materially changes the answer. Otherwise, state a safe assumption and proceed.

## 12. Maintenance Notes

Keep this workflow aligned with `agents/code-assistant/AGENT.md`, `prompts/code_assistant_system.md`, `agents/code-assistant/task_modes.md`, `tools/knowledge_search.md`, `workflows/retrieval-backed-response-pattern.md`, `workflows/expert-routing.md`, and `experts/gauss-language/OPERATIONAL_PROFILE.md`. Update it when task modes, expert modules, retrieval behavior, source hierarchy, tool capabilities, or recurring benchmark failures change.
