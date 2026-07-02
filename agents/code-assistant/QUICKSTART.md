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

- [prompts/system_prompt.md](../../prompts/system_prompt.md)
- [prompts/code_assistant_system.md](../../prompts/code_assistant_system.md)
- [agents/code-assistant/AGENT.md](AGENT.md)
- [agents/code-assistant/task_modes.md](task_modes.md)
- [experts/gauss-language/BODY_OF_KNOWLEDGE.md](../../experts/gauss-language/BODY_OF_KNOWLEDGE.md)
- [experts/gauss-language/COMMAND_CATEGORIES.md](../../experts/gauss-language/COMMAND_CATEGORIES.md)
- [workflows/native-command-selection.md](../../workflows/native-command-selection.md)
- [workflows/command-documentation-retrieval.md](../../workflows/command-documentation-retrieval.md)
- [workflows/code-assistant-response.md](../../workflows/code-assistant-response.md)
- [evaluations/benchmark-prompts.md](../../evaluations/benchmark-prompts.md)
- [evaluations/scoring.md](../../evaluations/scoring.md)
- [evaluations/benchmark-coverage.md](../../evaluations/benchmark-coverage.md)

Use fewer files for small experiments, but include official-doc retrieval guidance whenever exact command syntax matters.

## Manual Trial Workflow

1. Choose a task mode: debugging, translation, review, explanation, refactoring, optimization, documentation, test generation, or design guidance.
2. Provide the Code Assistant system prompt and the relevant context files listed above.
3. Ask the user task, including any GAUSS code, error messages, source-language snippets, or data-structure details.
4. Check whether official command documentation is needed for exact syntax, arguments, return values, examples, package behavior, or version behavior.
5. If official documentation is available in context or through retrieval tools, the assistant should retrieve or inspect it on the user's behalf before deferring verification to the user.
6. Review the response against known GAUSS failure modes: invented functions, cross-language syntax, wrong data structure assumptions, dimension mistakes, missing dependency notes, and unverified command syntax.
7. Optionally record the result as a manual evaluation using [workflows/manual-evaluation.md](../../workflows/manual-evaluation.md).

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

## Trust And Verification

The assistant should not invent GAUSS syntax. Native command categories identify candidate commands, official command-specific documentation verifies exact usage, and curated notes are only short convenience references. If official docs are available, the assistant should verify them on the user's behalf. Users should be told to verify manually only when the assistant cannot access or retrieve the needed documentation. Generated code should be reviewed and tested before production use.

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
