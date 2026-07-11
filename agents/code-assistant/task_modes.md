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

GAUSS code generation activates the GAUSS Language Expert (`../../workflows/expert-routing.md`, `../../experts/gauss-language/OPERATIONAL_PROFILE.md`); exact syntax, defaults, and return values still require official-doc-backed evidence, not general knowledge. If the code implements a statistical/econometric method, the Econometrics Expert (`../../experts/econometrics/OPERATIONAL_PROFILE.md`) may also activate to confirm the method fits the stated goal and data. The Software Engineering Expert (`../../experts/software-engineering/OPERATIONAL_PROFILE.md`) may also activate when structure, modularity, maintainability, or testability of the generated code is a genuine concern — for example, generating a reusable procedure API rather than a one-off script. The Documentation Expert (`../../experts/documentation/OPERATIONAL_PROFILE.md`) may activate when the user asks for usage examples, comments, docstrings, README/help text, parameter/return explanations, or user-facing explanation alongside the generated code. The Education Expert (`../../experts/education/OPERATIONAL_PROFILE.md`) may activate when the user asks for a tutorial, guided walkthrough, learning sequence, practice exercise, or beginner-to-advanced progression built around the generated code. The Product Expert (`../../experts/product/OPERATIONAL_PROFILE.md`) may activate when the generated code is tied to a product feature, user workflow, feature scope, MVP, adoption risk, or time-to-value — it owns the product framing, not the code itself.

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

GAUSS syntax, runtime, or command issues activate the GAUSS Language Expert (`../../workflows/expert-routing.md`, `../../experts/gauss-language/OPERATIONAL_PROFILE.md`). Statistical or modeling issues (wrong estimator, violated assumption, misread diagnostic) activate the Econometrics Expert (`../../experts/econometrics/OPERATIONAL_PROFILE.md`) instead. Bugs that could be either — or both, such as code that runs but produces a statistically questionable result — may activate both experts; keep the syntax fix and the methodological concern distinct. The Software Engineering Expert (`../../experts/software-engineering/OPERATIONAL_PROFILE.md`) may activate when the underlying issue is a design weakness rather than a syntax or methodology problem — poor error handling, missed edge cases, hidden dependencies, or a missing test/validation strategy that let the bug through. The Documentation Expert (`../../experts/documentation/OPERATIONAL_PROFILE.md`) may activate when the user asks for troubleshooting guidance, user-facing explanation of the error, or clearer error-handling notes for future readers. The Education Expert (`../../experts/education/OPERATIONAL_PROFILE.md`) may activate when the user asks to learn debugging concepts, design debugging practice, explain errors as a learning activity, or create remediation around common mistakes. The Product Expert (`../../experts/product/OPERATIONAL_PROFILE.md`) may activate when the bug's impact on users, adoption, release risk, time-to-value, or product scope is the actual concern, separate from the syntax/methodology/design fix itself. When the diagnosis depends on documented command-specific behavior (for example, a return-value field or a not-found/missing-value convention), follow `../../workflows/retrieval-backed-response-pattern.md` and include its validation-step requirement in the fix.

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

Explaining GAUSS syntax or code mechanics activates the GAUSS Language Expert (`../../workflows/expert-routing.md`). Explaining model interpretation or assumptions activates the Econometrics Expert (`../../experts/econometrics/OPERATIONAL_PROFILE.md`) instead. Explaining a GAUSS model's printed output may activate both — GAUSS-side mechanics from one, statistical meaning from the other. The Software Engineering Expert (`../../experts/software-engineering/OPERATIONAL_PROFILE.md`) may activate when the explanation includes structural or design tradeoffs (why the code is organized the way it is), rather than pure syntax or statistical mechanics. The Documentation Expert (`../../experts/documentation/OPERATIONAL_PROFILE.md`) should activate strongly when the explanation is intended for users, docs, README/help text, or reference material rather than an in-conversation answer only. The Education Expert (`../../experts/education/OPERATIONAL_PROFILE.md`) may activate when the explanation is meant to teach over time, build conceptual understanding, include practice, or scaffold a beginner, rather than answer a single in-conversation question. The Product Expert (`../../experts/product/OPERATIONAL_PROFILE.md`) may activate when the explanation is framed around user value, workflow fit, product impact, or adoption, rather than syntax or statistical mechanics alone. Purely conceptual, non-GAUSS, non-methodological, non-design, non-documentation, non-education, non-product explanations do not require any of the six.

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

Translation into GAUSS activates the GAUSS Language Expert (`../../workflows/expert-routing.md`, `../../experts/gauss-language/OPERATIONAL_PROFILE.md`). Translating econometric or statistical code (a regression, a diagnostic, a forecasting model) may also activate the Econometrics Expert (`../../experts/econometrics/OPERATIONAL_PROFILE.md`) to confirm the method is still appropriate for the data, not just that the syntax translated correctly. The Software Engineering Expert (`../../experts/software-engineering/OPERATIONAL_PROFILE.md`) may activate when the translation also involves preserving behavior, restructuring for GAUSS idioms, or maintainability of the translated result, beyond a syntax-for-syntax conversion. The Documentation Expert (`../../experts/documentation/OPERATIONAL_PROFILE.md`) may activate when the user asks to document the translated code or explain migration differences for users, beyond the translation itself. The Education Expert (`../../experts/education/OPERATIONAL_PROFILE.md`) may activate when the user asks for a learning path or teaching sequence around translating between languages or tools, rather than a one-off translation. The Product Expert (`../../experts/product/OPERATIONAL_PROFILE.md`) may activate when the translation or migration affects product workflow, user adoption, positioning, or feature scope, beyond the translation itself. When the translation relies on a native command whose behavior was verified through documentation lookup, follow `../../workflows/retrieval-backed-response-pattern.md` and include its validation-step requirement (for example, comparing the GAUSS result against the source language's result on the same data).

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

GAUSS implementation correctness (hallucinated functions, invalid syntax, data-structure misuse) activates the GAUSS Language Expert (`../../workflows/expert-routing.md`, `../../experts/gauss-language/OPERATIONAL_PROFILE.md`). Methodological or statistical validity (wrong estimator, unchecked assumption, misinterpreted output) activates the Econometrics Expert (`../../experts/econometrics/OPERATIONAL_PROFILE.md`). Reviewing analysis code (code that runs a statistical model) often activates both, since correctness and appropriateness are separate questions. The Software Engineering Expert (`../../experts/software-engineering/OPERATIONAL_PROFILE.md`) should activate strongly for code review — maintainability, modularity, readability, testability, error handling, and duplicated logic are its core territory, separate from the GAUSS Language Expert's syntax check and the Econometrics Expert's methodological check. The Documentation Expert (`../../experts/documentation/OPERATIONAL_PROFILE.md`) may activate when the review includes comments, docstrings, docs, README/help text, or explanation clarity, separate from the other three experts' checks. The Education Expert (`../../experts/education/OPERATIONAL_PROFILE.md`) may activate when the review is meant to teach reviewers or learners through examples, exercises, feedback, or misconceptions, rather than only fix the code under review. The Product Expert (`../../experts/product/OPERATIONAL_PROFILE.md`) may activate when the review concerns product risk, release tradeoffs, user impact, or technical debt treated as a product risk — kept distinguishable from the Software Engineering Expert's own maintainability judgment, even when all six activate together.

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

GAUSS code structure activates the GAUSS Language Expert (`../../workflows/expert-routing.md`, `../../experts/gauss-language/OPERATIONAL_PROFILE.md`). The Econometrics Expert activates only if the refactor could change how a model, sample, or estimator is interpreted — for example, restructuring how missing values are dropped before estimation — not for a pure code-structure cleanup that preserves behavior. The Software Engineering Expert (`../../experts/software-engineering/OPERATIONAL_PROFILE.md`) should activate strongly for refactoring — it owns behavior-preserving restructuring, decomposition, and safe change management, separate from the GAUSS Language Expert's syntax verification of the resulting code; any unverified structural suggestion must be labeled as pseudocode rather than presented as verified GAUSS. The Documentation Expert (`../../experts/documentation/OPERATIONAL_PROFILE.md`) may activate when the user asks to document the refactored structure, inputs/outputs, design intent, or usage — separate from the refactor strategy itself. The Education Expert (`../../experts/education/OPERATIONAL_PROFILE.md`) may activate when the user asks to teach refactoring concepts, create refactoring exercises, or scaffold maintainability concepts for learners. The Product Expert (`../../experts/product/OPERATIONAL_PROFILE.md`) may activate when the refactor is tied to roadmap risk, feature delivery, scope tradeoffs, or future product work, separate from the refactor strategy itself.

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

GAUSS optimization command selection (for example, `qnewtonmt` vs. `minimize`) activates the GAUSS Language Expert (`../../workflows/expert-routing.md`, `../../experts/gauss-language/OPERATIONAL_PROFILE.md`), including version-sensitive choices. Whether an optimization-estimated model itself is methodologically appropriate (not just which optimizer to call) activates the Econometrics Expert (`../../experts/econometrics/OPERATIONAL_PROFILE.md`). The Software Engineering Expert (`../../experts/software-engineering/OPERATIONAL_PROFILE.md`) may activate for general complexity/design tradeoffs (avoiding premature optimization, identifying likely bottlenecks at a design level), but specific GAUSS performance claims (a particular command's speed or memory behavior) still require the GAUSS Language Expert and verified evidence, not this expert's own authority. The Documentation Expert (`../../experts/documentation/OPERATIONAL_PROFILE.md`) may activate when the user asks to document performance caveats, user-facing tradeoffs, or warnings about the optimized code's behavior. The Education Expert (`../../experts/education/OPERATIONAL_PROFILE.md`) may activate when the user asks to teach performance tradeoffs or design practice exercises around optimization concepts. The Product Expert (`../../experts/product/OPERATIONAL_PROFILE.md`) may activate when the performance tradeoff affects user value, activation, adoption, or product positioning, separate from the specific GAUSS performance claim.

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

Documentation describing GAUSS syntax, commands, or behavior activates the GAUSS Language Expert (`../../workflows/expert-routing.md`). Statistical interpretation or methodology-focused tutorial content activates the Econometrics Expert (`../../experts/econometrics/OPERATIONAL_PROFILE.md`) instead. The Software Engineering Expert (`../../experts/software-engineering/OPERATIONAL_PROFILE.md`) usually does not own user-facing documentation quality, but may activate when the request is about code comments or docstrings that explain design intent rather than polished user-facing text. The Documentation Expert (`../../experts/documentation/OPERATIONAL_PROFILE.md`) should activate strongly for this mode — documentation clarity, reference structure, examples, comments/docstrings, usage guidance, and audience awareness are its core territory. The Education Expert (`../../experts/education/OPERATIONAL_PROFILE.md`) may activate only when the documentation work becomes a lesson, tutorial sequence, exercise set, curriculum, or learning path — the Documentation Expert remains primary for reference/documentation clarity itself. The Product Expert (`../../experts/product/OPERATIONAL_PROFILE.md`) may activate when the documentation work includes positioning, user value, adoption, product impact, or feature framing — the Documentation Expert remains primary for reference/documentation clarity itself. General documentation with none of GAUSS syntax, statistical methodology, design-intent commentary, learning-sequence intent, or product-framing intent (README structure, general style) still activates the Documentation Expert for clarity/structure, but not the GAUSS Language, Econometrics, Software Engineering, Education, or Product Experts.

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

GAUSS code tests (checking return values, dimensions, edge cases) activate the GAUSS Language Expert (`../../workflows/expert-routing.md`, `../../experts/gauss-language/OPERATIONAL_PROFILE.md`). Statistical validation or diagnostic tests (checking that a model's assumptions hold, or that a diagnostic behaves as expected) activate the Econometrics Expert (`../../experts/econometrics/OPERATIONAL_PROFILE.md`). The Software Engineering Expert (`../../experts/software-engineering/OPERATIONAL_PROFILE.md`) should activate strongly for test generation — test strategy, edge-case coverage, regression checks, and behavior preservation are its core territory. The Documentation Expert (`../../experts/documentation/OPERATIONAL_PROFILE.md`) may activate when the user asks to document test intent, expected outputs, edge cases, or testing guidance for other users/readers. The Education Expert (`../../experts/education/OPERATIONAL_PROFILE.md`) may activate when tests are used as learning exercises, assessment items, checks for understanding, or practice tasks. The Product Expert (`../../experts/product/OPERATIONAL_PROFILE.md`) may activate when tests are tied to release confidence, product risk, user success criteria, acceptance criteria at a product level, or adoption-critical workflows — distinct from the Software Engineering Expert's own test-strategy ownership. Recommended tests must never be presented as already run; a recommended test is not a confirmed result.

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

GAUSS data-structure or implementation design choices activate the GAUSS Language Expert (`../../workflows/expert-routing.md`, `../../experts/gauss-language/OPERATIONAL_PROFILE.md`). Statistical design or modeling strategy (which estimator family fits the research question) activates the Econometrics Expert (`../../experts/econometrics/OPERATIONAL_PROFILE.md`). The Software Engineering Expert (`../../experts/software-engineering/OPERATIONAL_PROFILE.md`) should activate strongly for design guidance — organization, modularity, maintainability, and safe change management are its core territory. The Documentation Expert (`../../experts/documentation/OPERATIONAL_PROFILE.md`) may activate when the user asks to document design decisions, usage guidance, assumptions, or caveats arising from the recommendation. The Education Expert (`../../experts/education/OPERATIONAL_PROFILE.md`) may activate when the user asks to teach design concepts, build a learning sequence, or create practice around architecture/workflow decisions. The Product Expert (`../../experts/product/OPERATIONAL_PROFILE.md`) may activate when architecture/workflow decisions affect product scope, user journey, adoption, time-to-value, or prioritization. End-to-end analysis design (data structure through to model choice, implementation, code organization, user-facing documentation, learner-facing teaching, and product framing) may activate all six.

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
* Did the response choose the correct routing pattern — per the activation matrix and worked examples in `../../workflows/expert-routing.md` Step 4 (any subset of GAUSS Language, Econometrics, Software Engineering, Documentation, Education, and Product, including Neither)?
* Did it avoid over-routing, applying any expert's reasoning to a task from that expert's non-activation cases?
* If more than one expert activated, did the response keep the implementation, methodology, maintainability, documentation, education, and product recommendations separate, rather than blending them into one unqualified claim?
* Did the response avoid treating syntactically valid GAUSS as well-designed, or clean/well-organized code as statistically or causally valid?
* Did the response avoid treating clear documentation as proof of GAUSS syntax correctness, statistical validity, or code maintainability?
* Did the response avoid treating good instruction or lesson quality as proof of GAUSS syntax correctness, statistical validity, code maintainability, documentation quality, or product value?
* Did the response avoid treating a compelling product recommendation as proof of GAUSS syntax correctness, statistical validity, code maintainability, documentation quality, or education quality?
* If the Software Engineering Expert activated, did the response avoid inventing GAUSS syntax and avoid claiming a recommended test or refactor was actually executed?
* If the Documentation Expert activated, did the response label unverified examples as pseudocode, avoid inventing GAUSS syntax, and avoid treating the request as Education Expert curriculum design?
* If the Education Expert activated, did the response label unverified examples as pseudocode, avoid inventing GAUSS syntax, and avoid treating the request as Product Expert strategy/prioritization?
* If the Product Expert activated, did the response label product hypotheses clearly when evidence is missing, avoid inventing GAUSS syntax, and avoid claiming market proof, adoption certainty, or product-market fit without user/customer evidence?
