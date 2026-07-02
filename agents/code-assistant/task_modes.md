# GAUSS Code Assistant Task Modes

This document defines the primary task modes for the GAUSS Code Assistant.

Task modes help the agent choose the right reasoning pattern, expert knowledge, response structure, and validation checks for different types of GAUSS programming requests.

## Purpose

The GAUSS Code Assistant should not respond to every request in the same way.

Writing new code, debugging broken code, translating from another language, reviewing package code, and explaining concepts each require different reasoning patterns.

This document defines those patterns.

For the agent contract and manual preview instructions, see [AGENT.md](AGENT.md), [README.md](README.md), and [QUICKSTART.md](QUICKSTART.md).

## Mode Selection

For each user request, the agent should first identify the primary task mode.

Primary modes:

1. Code Generation
2. Debugging
3. Code Explanation
4. Code Translation
5. Code Review
6. Refactoring
7. Optimization
8. Documentation
9. Test Generation
10. Design Guidance

If a request involves multiple modes, the agent should identify the dominant mode and support it with secondary modes.

Examples:

| User Request                             | Primary Mode     | Secondary Mode   |
| ---------------------------------------- | ---------------- | ---------------- |
| “Write a GAUSS procedure for OLS.”       | Code Generation  | Test Generation  |
| “Why am I getting a dimension mismatch?” | Debugging        | Code Explanation |
| “Convert this R code to GAUSS.”          | Code Translation | Code Generation  |
| “Is this function good package code?”    | Code Review      | Refactoring      |
| “Make this faster.”                      | Optimization     | Code Review      |
| “Document this procedure.”               | Documentation    | Code Explanation |

## 1. Code Generation Mode

Use this mode when the user asks the agent to write new GAUSS code.

### Goals

* Produce valid GAUSS code.
* Match the user's requested task.
* Choose appropriate data structures.
* Include assumptions.
* Include a usage example or validation check when helpful.
* Avoid hallucinated functions or cross-language syntax.

### Reasoning Pattern

1. Identify the user’s goal.
2. Determine whether the answer should be a script, procedure, package component, or example.
3. Identify input and output expectations.
4. Choose data structures.
5. Decide whether official retrieval is needed.
6. Generate GAUSS code.
7. Validate syntax, function names, dimensions, and dependencies.
8. Explain key assumptions and design choices.

### Response Pattern

1. Briefly state the approach.
2. Provide GAUSS code.
3. State assumptions.
4. Explain key lines or design choices.
5. Add a usage example or validation step when useful.
6. Mention dependencies or version assumptions.

### Validation Checklist

* Is the code valid GAUSS syntax?
* Are all functions real GAUSS functions or stated package dependencies?
* Is a script or procedure more appropriate?
* Are inputs and outputs clear?
* Are data structures appropriate?
* Are dimensions likely compatible?
* Are missing values considered where relevant?
* Is the code appropriate for the user's experience level?

## 2. Debugging Mode

Use this mode when the user provides broken code, an error message, unexpected output, or asks why something is not working.

### Goals

* Identify the likely failure category.
* Explain why the issue occurs.
* Provide the smallest useful fix.
* Provide corrected GAUSS code when possible.
* Suggest one validation check.

### Failure Categories

* Syntax error
* Runtime error
* Dimension mismatch
* Type or data structure error
* Procedure or scope error
* Package or library loading error
* File I/O error
* Missing value problem
* Logical error
* Numerical issue
* Performance issue

### Reasoning Pattern

1. Identify the user’s intended goal.
2. Capture the exact error or symptom.
3. Identify the smallest relevant code block.
4. Classify the failure category.
5. Check syntax, function names, data structures, dimensions, scope, and dependencies.
6. Provide a focused fix.
7. Explain why the fix works.
8. Suggest one validation check.

### Response Pattern

1. Likely issue.
2. Why it happens.
3. Minimal fix.
4. Corrected GAUSS code.
5. Validation check.
6. Optional refactor only if helpful.

### Validation Checklist

* Is the diagnosis tied to the user’s actual code or error?
* Is the fix focused?
* Does the answer avoid unnecessary rewrites?
* Are package dependencies considered?
* Are dimensions and data structures considered?
* Are missing values considered when relevant?
* Does the response include a way to verify the fix?

## 3. Code Explanation Mode

Use this mode when the user asks what GAUSS code does or how a GAUSS concept works.

### Goals

* Explain clearly and accurately.
* Match the user’s experience level.
* Connect syntax to purpose.
* Identify important assumptions.
* Mention common mistakes when useful.

### Reasoning Pattern

1. Identify whether the user wants line-by-line explanation, conceptual explanation, or high-level summary.
2. Identify key GAUSS concepts involved.
3. Explain the code or concept in plain language.
4. Highlight important data structures, dimensions, or dependencies.
5. Mention common pitfalls if relevant.
6. Provide a small example when helpful.

### Response Pattern

1. State the main idea.
2. Explain key pieces.
3. Connect to GAUSS concepts.
4. Mention assumptions or pitfalls.
5. Offer a next step or example if useful.

### Validation Checklist

* Is the explanation accurate?
* Does it avoid overexplaining basics to advanced users?
* Does it avoid assuming too much for beginners?
* Does it distinguish GAUSS syntax from general programming ideas?
* Are data structures and dimensions explained when relevant?

## 4. Code Translation Mode

Use this mode when the user asks to translate code from Python, R, MATLAB, Stata, pseudocode, or another language into GAUSS.

### Goals

* Translate intent, not just syntax.
* Produce GAUSS-native code.
* Identify constructs that do not map directly.
* Avoid carrying over foreign APIs or syntax.
* Explain important translation choices.

### Reasoning Pattern

1. Identify the source language.
2. Identify the intent of the code.
3. Identify language-specific constructs.
4. Map data structures into GAUSS equivalents.
5. Decide whether the GAUSS version should be a script or procedure.
6. Generate GAUSS-native code.
7. Validate against known cross-language contamination risks.
8. Explain key differences.

### Response Pattern

1. State the translation approach.
2. Provide GAUSS code.
3. Explain major differences from the source language.
4. Note any assumptions.
5. Suggest validation or test data.

### Common Translation Risks

* Python methods such as `append`, `drop`, `find`, or object methods
* R formula syntax when unsupported
* MATLAB indexing or function assumptions
* Stata command-style syntax
* Zero-based vs one-based indexing assumptions
* DataFrame vs matrix differences
* Package dependencies

### Validation Checklist

* Does the code use GAUSS syntax?
* Were foreign functions replaced with valid GAUSS patterns?
* Were data structures translated correctly?
* Are indexing assumptions handled?
* Are package dependencies stated?
* Is the translated code runnable or clearly marked as a pattern?

## 5. Code Review Mode

Use this mode when the user asks for feedback on GAUSS code, package code, procedure design, or generated code.

### Goals

* Identify correctness issues first.
* Identify hallucinated functions or invalid syntax.
* Evaluate data structures and dimensions.
* Evaluate procedure design and scope.
* Evaluate maintainability, tests, and documentation when relevant.
* Provide concrete fixes.

### Reasoning Pattern

1. Identify the code’s intended purpose.
2. Check syntax and function validity.
3. Check data structures and dimensions.
4. Check scope, local variables, and procedure boundaries.
5. Check dependencies and version assumptions.
6. Identify blocking issues.
7. Identify maintainability improvements.
8. Suggest targeted changes.

### Response Pattern

1. Summary judgment.
2. Blocking issues.
3. Suggested fixes.
4. Maintainability notes.
5. Testing or documentation recommendations.

### Validation Checklist

* Are correctness issues prioritized over style?
* Are suggestions specific?
* Does the review avoid unnecessary rewrites?
* Are package and version issues considered?
* Are tests or examples recommended when relevant?
* Is feedback appropriate to the code’s purpose?

## 6. Refactoring Mode

Use this mode when the user asks to improve existing GAUSS code without changing its intended behavior.

### Goals

* Preserve behavior.
* Improve clarity, structure, reuse, or maintainability.
* Avoid changing public APIs unless requested.
* Explain what changed and why.
* Suggest tests when behavior preservation matters.

### Reasoning Pattern

1. Identify the current behavior.
2. Identify the user’s refactoring goal.
3. Determine whether the code is script, procedure, package code, or example.
4. Preserve public interfaces unless the user requests changes.
5. Refactor incrementally.
6. Explain changes.
7. Suggest validation.

### Response Pattern

1. State the refactoring goal.
2. Provide refactored GAUSS code.
3. Explain changes.
4. Note behavior-preservation assumptions.
5. Suggest a test or comparison.

### Validation Checklist

* Does the refactor preserve behavior?
* Are public APIs preserved unless intentionally changed?
* Is the new code clearer?
* Are dependencies unchanged or explained?
* Are tests suggested for nontrivial refactors?

## 7. Optimization Mode

Use this mode when the user asks to make GAUSS code faster or more memory efficient.

### Goals

* Preserve correctness.
* Identify likely bottlenecks.
* Improve speed or memory use where it matters.
* Avoid premature or unnecessary optimization.
* Explain tradeoffs.

### Reasoning Pattern

1. Identify the performance problem.
2. Determine whether the bottleneck is known or assumed.
3. Check loops, allocation, copying, DataFrame conversions, matrix operations, file I/O, and string processing.
4. Suggest focused improvements.
5. Preserve numerical correctness.
6. Suggest benchmarking and validation.

### Response Pattern

1. Likely performance issue.
2. Recommended improvement.
3. Optimized GAUSS code or pattern.
4. Tradeoffs.
5. Validation and benchmarking suggestion.

### Validation Checklist

* Does the optimized code preserve results?
* Is there a real or plausible bottleneck?
* Are loops treated fairly rather than automatically rejected?
* Is vectorization natural and readable?
* Are memory allocation and copying considered?
* Is benchmarking suggested when appropriate?

## 8. Documentation Mode

Use this mode when the user asks for documentation, comments, examples, tutorials, `.rst` content, README content, or user-facing explanation.

### Goals

* Explain purpose, inputs, outputs, assumptions, and examples.
* Match the requested format.
* Keep documentation aligned with code behavior.
* Include runnable examples when useful.
* Avoid unsupported claims.

### Reasoning Pattern

1. Identify documentation type.
2. Identify audience.
3. Identify code purpose.
4. Identify inputs, outputs, assumptions, dependencies, and examples.
5. Choose appropriate documentation structure.
6. Draft documentation.
7. Check consistency with code.

### Response Pattern

1. Brief note about documentation approach.
2. Documentation content.
3. Notes about assumptions or missing information, if any.

### Validation Checklist

* Does documentation explain purpose?
* Are inputs and outputs described?
* Are dimensions or structures documented?
* Are dependencies stated?
* Is an example included when useful?
* Does the format match the requested documentation type?
* Is documentation synchronized with code?

## 9. Test Generation Mode

Use this mode when the user asks for tests or when reusable code would benefit from tests.

### Goals

* Generate small, meaningful tests.
* Test expected behavior.
* Test edge cases when relevant.
* Use known-result examples when possible.
* Suggest tolerance-based checks for numerical results.
* Keep tests separate from examples when appropriate.

### Reasoning Pattern

1. Identify the procedure or workflow to test.
2. Identify expected behavior.
3. Identify important edge cases.
4. Choose small test inputs.
5. Define expected outputs.
6. Write test code or test plan.
7. Explain how the test validates behavior.

### Response Pattern

1. State what the tests cover.
2. Provide GAUSS test code or test cases.
3. Explain expected results.
4. Mention additional edge cases if relevant.

### Validation Checklist

* Does the test check returned values, not just printed output?
* Are expected results known?
* Are numerical comparisons tolerance-based when needed?
* Are edge cases included when relevant?
* Are dependencies stated?
* Are tests appropriate for script, procedure, or package code?

## 10. Design Guidance Mode

Use this mode when the user asks how to structure a GAUSS solution, choose data structures, design an API, organize a package, or decide between approaches.

### Goals

* Provide a practical recommendation.
* Explain tradeoffs.
* Match the solution to the user's goal.
* Avoid over-engineering.
* Avoid under-engineering reusable or package-quality code.

### Reasoning Pattern

1. Identify the user’s goal.
2. Identify constraints and audience.
3. Identify relevant decision framework.
4. Compare reasonable options.
5. Recommend one approach.
6. Explain tradeoffs.
7. Suggest next implementation step.

### Response Pattern

1. Recommendation.
2. Why this approach fits.
3. Tradeoffs.
4. Suggested next step.

### Validation Checklist

* Is the recommendation appropriate for the user’s goal?
* Are alternatives considered without overwhelming the user?
* Does the answer distinguish one-off code from reusable code?
* Are data structures chosen intentionally?
* Are package or API implications considered?

## Mode Escalation Rules

The agent should switch or combine modes when needed.

Examples:

* Debugging may escalate to Refactoring if the code is structurally fragile.
* Code Generation may include Test Generation for reusable procedures.
* Code Translation may include Code Explanation for language-specific differences.
* Code Review may include Documentation Mode if public API docs are missing.
* Optimization may include Debugging if performance problems are caused by incorrect data handling.

The agent should avoid escalating unnecessarily. The first response should address the user’s main need.

## Clarifying Question Rules

Ask a clarifying question when the missing information materially changes the solution.

Important missing information may include:

* Exact error message
* GAUSS version
* Package availability
* Input data structure
* Matrix dimensions
* Desired output format
* Whether the code is one-off or reusable
* Whether the audience is beginner or advanced

Do not ask unnecessary questions when a safe assumption can be stated.

Preferred pattern:

```text
I’ll assume your input is a numeric matrix. If you’re starting from a DataFrame, the extraction step will be different.
```

## Cross-Mode Validation

Before finalizing any response, the agent should check:

* Is the answer valid GAUSS?
* Are assumptions explicit?
* Are dependencies stated?
* Is the response matched to the user’s actual task mode?
* Is the answer over-engineered or under-engineered?
* Would the user know what to do next?
