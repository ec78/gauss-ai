# Scoring Rubric

Purpose:
This rubric is used to score responses to `evaluations/benchmark-prompts.md` for the GAUSS Code Assistant.

## Scoring Scale

- 4 = Excellent
- 3 = Good
- 2 = Partially correct
- 1 = Poor
- 0 = Failing / unsafe / unusable

## Core Scoring Dimensions

### 1. GAUSS Syntax Correctness

- 4: Uses valid GAUSS syntax, procedure structure, comments, indexing, control flow, and statement termination.
- 2: Mostly GAUSS-like but contains syntax errors, incomplete statements, or minor contamination from another language.
- 0: Produces non-GAUSS code, pseudocode, or GAUSS-shaped text that would be unusable.

### 2. Function and Package Validity

- 4: Uses real GAUSS functions and package APIs, with caveats when uncertain.
- 2: Uses plausible functions but includes unsupported or ambiguous calls.
- 0: Invents GAUSS functions, packages, or APIs without caveat.

### 3. Data Structure Reasoning

- 4: Correctly distinguishes matrices, DataFrames, arrays, structures, strings, and string arrays.
- 2: Handles common matrix cases but blurs other GAUSS data structures.
- 0: Applies the wrong data model, such as pandas, MATLAB tables, or Python lists.

### 4. Dimension and Numerical Awareness

- 4: Tracks rows, columns, conformability, missing values, transposes, and array dimensions accurately.
- 2: Notices some shape issues but misses edge cases or uses matrix-only functions too broadly.
- 0: Ignores dimension errors, uses `rows` or `cols` on arrays, or gives numerically invalid logic.

### 5. Task Mode Fit

- 4: Matches the requested mode: generation, debugging, explanation, review, translation, refactor, test, or design guidance.
- 2: Partly answers the task but drifts into unnecessary implementation or generic advice.
- 0: Answers the wrong task or ignores the requested audience or output format.

### 6. Explanation Quality

- 4: Clear, accurate, concise, and adapted to beginner or advanced users as requested.
- 2: Understandable but generic, too terse, too verbose, or mismatched to the audience.
- 0: Misleading, confusing, or confidently explains incorrect GAUSS behavior.

### 7. Assumptions and Dependencies

- 4: States relevant assumptions, package requirements, paths, versions, and execution limits.
- 2: Mentions some dependencies but leaves important setup or scope unclear.
- 0: Makes unsafe package/version claims or hides assumptions that affect correctness.

### 8. Maintainability and Best Practices

- 4: Produces idiomatic, readable GAUSS with stable public APIs and appropriate separation of concerns.
- 2: Works in principle but is brittle, overcomplicated, or poorly organized.
- 0: Encourages unmaintainable patterns, public use of internals, or behavior-changing refactors.

### 9. Testing or Validation

- 4: Provides appropriate GAUSS-focused checks, edge cases, expected outputs, or validation steps.
- 2: Suggests limited or generic validation.
- 0: Omits necessary validation or claims execution/results that did not occur.

### 10. Hallucination and Cross-Language Contamination Avoidance

- 4: Avoids Python, R, MATLAB, JavaScript, and unsupported GAUSS APIs unless explicitly translating from them.
- 2: Minor contamination appears but the response remains mostly useful.
- 0: Relies on another language's syntax, runtime, libraries, or concepts as if they were GAUSS.

## Automatic Failure Conditions

- Generates Python, R, MATLAB, JavaScript, or pseudocode instead of GAUSS when GAUSS code is requested.
- Invents GAUSS functions or packages without caveat.
- Claims code was executed when it was not.
- Gives statistically plausible but invalid GAUSS code.
- Ignores the central debugging issue.
- Provides unsafe or misleading package/version claims.

## Category-Specific Notes

- Code Generation: Score syntax, real GAUSS APIs, dimensions, missing values, and whether the code is usable without hidden non-GAUSS dependencies.
- Debugging: Highest weight goes to identifying the central bug, explaining the cause, and giving a GAUSS-valid fix.
- Translation: Reward preserving intent while removing source-language idioms and using GAUSS data structures correctly.
- Code Review: Reward actionable findings, public API awareness, package dependency checks, and risk-based severity.
- Documentation: Reward accurate GAUSS terminology, clear inputs/outputs, missing-value behavior, and realistic examples.
- Test Generation: Reward edge cases, expected outputs or invariants, and GAUSS-appropriate test style.
- Design Guidance: Reward tradeoff analysis across matrices, DataFrames, arrays, structures, scripts, procedures, packages, and public APIs.

## Overall Score

The overall score is the average of applicable dimension scores. Automatic failure conditions override the average and should result in a failing decision unless the issue is explicitly scoped as a harmless example or caveated uncertainty.

## Review Notes Template

Prompt:

Response:

Scores:

- GAUSS Syntax Correctness:
- Function and Package Validity:
- Data Structure Reasoning:
- Dimension and Numerical Awareness:
- Task Mode Fit:
- Explanation Quality:
- Assumptions and Dependencies:
- Maintainability and Best Practices:
- Testing or Validation:
- Hallucination Avoidance:

Overall Score:
Blocking Issues:
Suggested Improvements:
Decision: Pass / Needs Revision / Fail
