# GAUSS Code Assistant Quickstart

## What It Is

The GAUSS Code Assistant is a specialized assistant for writing, debugging, explaining, translating, reviewing, and improving GAUSS code. It is designed to use GAUSS-specific knowledge, benchmark-tested failure modes, and source-aware retrieval rules.

It is not a replacement for official GAUSS documentation. Exact command syntax, arguments, return values, examples, package behavior, and version-specific behavior should be verified against official documentation when they matter.

## What It Can Help With

- Write GAUSS scripts and procedures.
- Debug syntax, dimension, scope, string, package, and missing-value issues.
- Translate Python, R, MATLAB, Stata, or pseudocode into GAUSS-native patterns.
- Explain GAUSS matrix, DataFrame, array, structure, string, and procedure behavior.
- Review package APIs, helper procedures, dependencies, and public interfaces.
- Refactor GAUSS code while preserving behavior.
- Suggest tests, validation checks, documentation, and examples.

## Manual Context Files

When trying the assistant manually, provide the relevant files as context:

- `prompts/system_prompt.md`
- `prompts/code_assistant_system.md`
- `agents/code-assistant/AGENT.md`
- `agents/code-assistant/task_modes.md`
- `experts/gauss-language/BODY_OF_KNOWLEDGE.md`
- `experts/gauss-language/COMMAND_CATEGORIES.md`
- `workflows/native-command-selection.md`
- `workflows/command-documentation-retrieval.md`
- `workflows/code-assistant-response.md`
- `evaluations/benchmark-prompts.md`
- `evaluations/scoring.md`
- `evaluations/benchmark-coverage.md`

Use fewer files for small experiments, but include official-doc retrieval guidance whenever exact command syntax matters.

## Example Manual Workflow

1. Choose the user task: debugging, translation, review, explanation, refactoring, optimization, documentation, test generation, or design guidance.
2. Supply the Code Assistant prompt files and the GAUSS Language Expert guidance.
3. Add the user prompt and any GAUSS code snippet.
4. Ask the assistant to state assumptions, avoid invented syntax, and mark uncertain command syntax for verification.
5. Review the answer against `evaluations/scoring.md` if the response is part of an evaluation.
6. Verify official command documentation before using exact syntax in production.

## Example Prompts

### Debugging GAUSS Code

```text
I am getting the wrong result from this GAUSS string search. Fix it and explain the issue.

idx = strpos(file_name, ".csv");
if idx == -1;
   print "Not a CSV file";
endif;
```

Expected assistant behavior: replace non-GAUSS `strpos` with `strindx`, handle `strindx == 0`, and avoid Python or JavaScript string assumptions.

### Translating Python/R/MATLAB to GAUSS

```text
Translate this R workflow into GAUSS:

model <- lm(y ~ x1 + x2, data = df)
summary(model)
```

Expected assistant behavior: translate the intent, consider native GAUSS procedures such as `olsmt`, use command categories only for discovery, and verify command-specific docs before giving production syntax.

### Reviewing Package API Design

```text
Review a GAUSS package entry point that exposes fitModel(y, x, ctl) and helper procedures named with leading underscores.
```

Expected assistant behavior: distinguish public APIs from helpers, review `y`, `x`, and `ctl` validation, discuss control defaults, and keep advice GAUSS-specific.

### Explaining Matrix Code

```text
Explain this GAUSS code to a beginner:

x = rndn(100, 3);
mu = meanc(x);
xc = x - mu';
vcv = xc'xc / (rows(x) - 1);
```

Expected assistant behavior: explain dimensions, transposes, and the variance-covariance calculation in beginner-friendly GAUSS terms.

### Generating Tests

```text
Generate test cases for a GAUSS procedure that standardizes each matrix column.
```

Expected assistant behavior: cover normal, constant-column, missing-value, and dimension edge cases; state expected outputs or invariants; and avoid non-GAUSS testing frameworks.

## Interpreting Answers Safely

Trust the assistant most when it:

- Uses GAUSS-native syntax and terminology.
- States assumptions about data structures, dimensions, missing values, and packages.
- Distinguishes scripts, procedures, package APIs, and helper procedures.
- Refers to official documentation when exact command syntax matters.
- Clearly labels teaching fallbacks versus production recommendations.

Be cautious when an answer:

- Uses functions or methods from Python, R, MATLAB, JavaScript, or pseudocode.
- Gives exact command syntax without citing verified documentation or repository context.
- Treats matrices, arrays, DataFrames, structures, or strings as interchangeable.
- Claims code was run when no execution tool was used.
- Uses a manual implementation where a verified native GAUSS procedure should be considered.

## When To Verify Official Documentation

Retrieve or verify official GAUSS documentation when:

- Exact command syntax, arguments, return values, or examples matter.
- Package behavior or version-specific behavior matters.
- A command is discovered through `COMMAND_CATEGORIES.md`.
- A curated command note is stale, incomplete, or conflicts with official docs.
- The answer will be used in production or package documentation.

## What Not To Trust Without Verification

- New function names not found in official docs, package source, or curated notes.
- Exact signatures for commands discovered only through categories.
- Claimed output structure fields not verified against command docs.
- Package install/load instructions that are not sourced.
- Statistical procedure syntax copied from R, Python, MATLAB, or Stata.
