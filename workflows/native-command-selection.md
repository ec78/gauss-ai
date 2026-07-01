# Native Command Selection Workflow

## 1. Overview

This workflow defines how the GAUSS Code Assistant should decide whether to recommend a native GAUSS command or procedure, retrieve exact command documentation, or write a manual implementation.

`experts/gauss-language/COMMAND_CATEGORIES.md` is a discovery tool. It helps identify likely native GAUSS commands by official documentation category, but it does not replace command-specific documentation. Category membership is not proof of exact syntax, arguments, return values, examples, or version behavior.

## 2. Decision Process

1. Classify the user task.
   Determine whether the user is asking for code generation, debugging, explanation, translation, review, refactoring, optimization, documentation, tests, or design guidance.

2. Identify likely command categories.
   Map the task to relevant command areas such as estimation, strings, matrices, statistics, optimization, data import/export, DataFrames, panel data, or time/date handling.

3. Search `COMMAND_CATEGORIES.md` for candidate native commands.
   Use command categories to identify possible built-in GAUSS commands or procedures before writing custom code.

4. Prefer native GAUSS commands/procedures for standard workflows when appropriate.
   For common statistical, data management, string, matrix, optimization, and file I/O tasks, first consider verified native GAUSS functionality.

5. Retrieve command-specific documentation before giving exact syntax.
   Exact syntax, arguments, return values, examples, package requirements, and version behavior should come from command-specific documentation or verified repository context.

6. Use manual implementations only when appropriate.
   Manual code is appropriate when the user asks for mechanics, no suitable native command exists, customization is needed, teaching requires the underlying computation, or exact native syntax cannot be verified and the response must remain high level.

## 3. Common Task-to-Category Routing

- OLS/regression workflows -> check estimation/modeling categories for native procedures such as `olsmt` before using manual matrix OLS.
- String search/parsing -> check string handling commands, including `strindx` and `strlen`.
- Matrix summaries -> check matrix, descriptive statistics, and computation commands before writing loops.
- Optimization -> check optimization and solution commands before writing custom solvers.
- Data import/export -> check data import/export, file I/O, and DataFrame-related commands before custom parsing.
- Time series/panel workflows -> check relevant time series, panel data, estimation, and econometrics-related procedures when available.

Do not invent command names. Use only verified commands from repository context, `COMMAND_CATEGORIES.md`, or official documentation.

## 4. Response Guidance

Use source-aware language when recommending native commands:

- "GAUSS has a native command/procedure that may fit this task: ..."
- "I would verify the exact syntax in the command documentation before writing production code."
- "A manual implementation is useful for teaching the mechanics, but the native procedure should usually be preferred for standard workflows."

When syntax is known from verified documentation or repository context, provide a concrete native-command example. When syntax is not verified, say so directly and avoid substituting only manual code as if it were the preferred GAUSS workflow.

## 5. Failure Modes

- Writing manual matrix code when a native command should be considered.
- Mentioning a native command but not giving an example when syntax is known.
- Inventing syntax from memory.
- Treating category membership as proof of exact usage.
- Treating a package-specific procedure as base GAUSS without checking dependencies.
- Overusing native commands when the user explicitly asks for the underlying mechanics.
- Using Python, R, MATLAB, JavaScript, or pseudocode patterns instead of GAUSS-native commands.

## 6. Integration Points

- `experts/gauss-language/COMMAND_CATEGORIES.md` provides the category-based command inventory.
- `experts/gauss-language/BODY_OF_KNOWLEDGE.md` defines standard library awareness and built-in versus custom implementation guidance.
- `prompts/code_assistant_system.md` should instruct the Code Assistant to use this workflow when choosing between native commands and manual code.
- `evaluations/benchmark-prompts.md` should test whether the assistant considers native GAUSS procedures before manual implementations.
- `workflows/knowledge-loading.md` defines how official and local-first knowledge sources should be resolved.
