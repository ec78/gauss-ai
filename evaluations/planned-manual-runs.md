# Planned Manual Runs

This file lists the next manual evaluations to run after the first six completed Code Assistant runs. These planned runs broaden coverage across categories that are not yet heavily tested.

## Planned Runs

| Prompt ID | Category | Benchmark Name | Why This Should Be Tested Next | Specific Scoring Risks to Watch For | Planned Run File |
|---:|---|---|---|---|---|
| 1.1 | Code Generation | Matrix summary procedure | Exercises basic GAUSS procedure generation, matrix operations, and syntax validity. | Invalid `proc ... endp` structure, hallucinated summary helpers, Python/R/MATLAB contamination, unclear output shape. | `2026-06-30-code-assistant-manual-run-007.md` |
| 3.1 | Code Explanation | Beginner matrix explanation | Tests whether the assistant can explain matrix dimensions and transposes for a beginner. | Overly advanced explanation, weak dimension reasoning, language contamination, failure to explain `x - mu'` and `xc'xc`. | `2026-06-30-code-assistant-manual-run-008.md` |
| 6.2 | Refactoring | Control structure defaults | Covers reusable GAUSS API design and control-structure default patterns. | Invented structure syntax, unstable public APIs, generic refactoring advice, missing default merge behavior. | `2026-06-30-code-assistant-manual-run-009.md` |
| 7.2 | Optimization | String processing efficiency | Extends string coverage beyond correctness into performance and repeated `strlen`/`strindx` use. | Proposing unavailable regex/Python APIs, changing `strindx == 0` semantics, premature optimization, no validation. | `2026-06-30-code-assistant-manual-run-010.md` |
| 9.1 | Test Generation | Matrix procedure tests | Adds coverage for GAUSS-focused tests, edge cases, and numerical validation. | Non-GAUSS test frameworks, missing expected outputs, ignoring constant columns/missing values, no tolerance guidance. | `2026-06-30-code-assistant-manual-run-011.md` |

## Ready-to-Copy Evaluation Prompts

### Run 007 - Prompt 1.1

````text
Run a manual evaluation for the GAUSS Code Assistant.

Use these files as context:
- prompts/system_prompt.md
- prompts/code_assistant_system.md
- agents/code-assistant/AGENT.md
- agents/code-assistant/task_modes.md
- experts/gauss-language/BODY_OF_KNOWLEDGE.md
- evaluations/benchmark-prompts.md
- evaluations/scoring.md
- workflows/manual-evaluation.md

Evaluate benchmark Prompt 1.1 - Matrix summary procedure.

Prompt:

Write a GAUSS procedure `summarizeCols(x)` that returns a matrix with each column's mean, standard deviation, minimum, and maximum.

Expected behavior:
- Uses valid GAUSS procedure syntax and matrix operations.
- Avoids Python, R, or MATLAB idioms such as `def`, `data.frame`, or `end`.
- Does not invent unsupported GAUSS helper functions.

Tasks:
1. Generate the Code Assistant response to the benchmark prompt.
2. Score the response using `evaluations/scoring.md`.
3. Mark non-applicable dimensions as `N/A` and exclude them from the overall average.
4. Create a new evaluation run file in `evaluations/runs/` named `2026-06-30-code-assistant-manual-run-007.md`.
5. Use the result template from `workflows/manual-evaluation.md`.
6. Reference the stable Prompt ID from `evaluations/benchmark-prompts.md`.
7. Do not modify the prompts, agent files, expert files, benchmark files, scoring files, or previous evaluation runs.
````

### Run 008 - Prompt 3.1

````text
Run a manual evaluation for the GAUSS Code Assistant.

Use these files as context:
- prompts/system_prompt.md
- prompts/code_assistant_system.md
- agents/code-assistant/AGENT.md
- agents/code-assistant/task_modes.md
- experts/gauss-language/BODY_OF_KNOWLEDGE.md
- evaluations/benchmark-prompts.md
- evaluations/scoring.md
- workflows/manual-evaluation.md

Evaluate benchmark Prompt 3.1 - Beginner matrix explanation.

Prompt:

Explain this GAUSS code to a beginner:

```gauss
x = rndn(100, 3);
mu = meanc(x);
xc = x - mu';
vcv = xc'xc / (rows(x) - 1);
```

Expected behavior:
- Explains matrix dimensions and transposes plainly.
- Uses GAUSS terminology without drifting into Python or R.
- Adapts tone and detail for a beginner.

Tasks:
1. Generate the Code Assistant response to the benchmark prompt.
2. Score the response using `evaluations/scoring.md`.
3. Mark non-applicable dimensions as `N/A` and exclude them from the overall average.
4. Create a new evaluation run file in `evaluations/runs/` named `2026-06-30-code-assistant-manual-run-008.md`.
5. Use the result template from `workflows/manual-evaluation.md`.
6. Reference the stable Prompt ID from `evaluations/benchmark-prompts.md`.
7. Do not modify the prompts, agent files, expert files, benchmark files, scoring files, or previous evaluation runs.
````

### Run 009 - Prompt 6.2

````text
Run a manual evaluation for the GAUSS Code Assistant.

Use these files as context:
- prompts/system_prompt.md
- prompts/code_assistant_system.md
- agents/code-assistant/AGENT.md
- agents/code-assistant/task_modes.md
- experts/gauss-language/BODY_OF_KNOWLEDGE.md
- evaluations/benchmark-prompts.md
- evaluations/scoring.md
- workflows/manual-evaluation.md

Evaluate benchmark Prompt 6.2 - Control structure defaults.

Prompt:

Suggest a refactor for repeated option parsing code across several GAUSS procedures.

Expected behavior:
- Recommends a shared control-structure initialization pattern.
- Handles missing fields and defaults clearly.
- Keeps package public APIs stable.

Tasks:
1. Generate the Code Assistant response to the benchmark prompt.
2. Score the response using `evaluations/scoring.md`.
3. Mark non-applicable dimensions as `N/A` and exclude them from the overall average.
4. Create a new evaluation run file in `evaluations/runs/` named `2026-06-30-code-assistant-manual-run-009.md`.
5. Use the result template from `workflows/manual-evaluation.md`.
6. Reference the stable Prompt ID from `evaluations/benchmark-prompts.md`.
7. Do not modify the prompts, agent files, expert files, benchmark files, scoring files, or previous evaluation runs.
````

### Run 010 - Prompt 7.2

````text
Run a manual evaluation for the GAUSS Code Assistant.

Use these files as context:
- prompts/system_prompt.md
- prompts/code_assistant_system.md
- agents/code-assistant/AGENT.md
- agents/code-assistant/task_modes.md
- experts/gauss-language/BODY_OF_KNOWLEDGE.md
- evaluations/benchmark-prompts.md
- evaluations/scoring.md
- workflows/manual-evaluation.md

Evaluate benchmark Prompt 7.2 - String processing efficiency.

Prompt:

Improve a GAUSS routine that repeatedly calls `strlen` and `strindx` inside nested loops over many names.

Expected behavior:
- Identifies redundant string work and possible caching.
- Preserves correct `strindx == 0` not-found behavior.
- Does not propose unavailable regex or Python string APIs.

Tasks:
1. Generate the Code Assistant response to the benchmark prompt.
2. Score the response using `evaluations/scoring.md`.
3. Mark non-applicable dimensions as `N/A` and exclude them from the overall average.
4. Create a new evaluation run file in `evaluations/runs/` named `2026-06-30-code-assistant-manual-run-010.md`.
5. Use the result template from `workflows/manual-evaluation.md`.
6. Reference the stable Prompt ID from `evaluations/benchmark-prompts.md`.
7. Do not modify the prompts, agent files, expert files, benchmark files, scoring files, or previous evaluation runs.
````

### Run 011 - Prompt 9.1

````text
Run a manual evaluation for the GAUSS Code Assistant.

Use these files as context:
- prompts/system_prompt.md
- prompts/code_assistant_system.md
- agents/code-assistant/AGENT.md
- agents/code-assistant/task_modes.md
- experts/gauss-language/BODY_OF_KNOWLEDGE.md
- evaluations/benchmark-prompts.md
- evaluations/scoring.md
- workflows/manual-evaluation.md

Evaluate benchmark Prompt 9.1 - Matrix procedure tests.

Prompt:

Generate test cases for a GAUSS procedure that standardizes each matrix column.

Expected behavior:
- Covers normal, constant-column, missing-value, and dimension edge cases.
- States expected outputs or invariants clearly.
- Avoids using non-GAUSS testing frameworks unless requested.

Tasks:
1. Generate the Code Assistant response to the benchmark prompt.
2. Score the response using `evaluations/scoring.md`.
3. Mark non-applicable dimensions as `N/A` and exclude them from the overall average.
4. Create a new evaluation run file in `evaluations/runs/` named `2026-06-30-code-assistant-manual-run-011.md`.
5. Use the result template from `workflows/manual-evaluation.md`.
6. Reference the stable Prompt ID from `evaluations/benchmark-prompts.md`.
7. Do not modify the prompts, agent files, expert files, benchmark files, scoring files, or previous evaluation runs.
````
