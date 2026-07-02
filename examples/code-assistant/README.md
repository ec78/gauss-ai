# Code Assistant Examples

These examples show how to try the GAUSS Code Assistant manually and what each example is intended to test.

## 1. Debug String Search

User prompt:

```text
Fix this GAUSS string code:

idx = strpos(file_name, ".csv");
if idx == -1;
   print "Not a CSV file";
endif;
```

What the assistant should do:

- Identify `strpos` as non-GAUSS.
- Use `strindx`.
- Check for `strindx == 0` when not found.
- Avoid Python, JavaScript, or MATLAB string methods.

Risk or failure mode:

- Cross-language string contamination and incorrect not-found semantics.

Reference:

- Benchmark content related to Prompt 2.2 in [benchmark prompts](../../evaluations/benchmark-prompts.md).
- Evaluation run [2026-06-30-code-assistant-manual-run-001.md](../../evaluations/runs/2026-06-30-code-assistant-manual-run-001.md).

## 2. Fix Dimension Mismatch

User prompt:

```text
I am getting a dimension mismatch after trimming y before regression. Explain the likely issue and suggest a minimal fix.
```

What the assistant should do:

- Explain that trimming `y` can leave `x` and `y` with different row counts.
- Recommend checking `rows(y)` and `rows(x)`.
- Suggest aligning `x` and `y` rows intentionally.
- Avoid blindly transposing objects as a fake fix.

Risk or failure mode:

- Treating dimension mismatch as a transpose problem instead of row alignment.

Reference:

- Evaluation run [2026-06-30-code-assistant-manual-run-002.md](../../evaluations/runs/2026-06-30-code-assistant-manual-run-002.md).

## 3. Translate R OLS Workflow

User prompt:

```text
Translate this R-style workflow into GAUSS:

model <- lm(y ~ x1 + x2, data = df)
summary(model)
```

What the assistant should do:

- Translate intent rather than copying R syntax.
- Use command categories only to discover native candidates.
- Identify `olsmt` as the relevant native GAUSS OLS procedure when appropriate.
- Treat official command-specific documentation as authoritative for exact syntax.
- Use the curated `olsmt` note only as a short convenience reference.
- Keep manual matrix OLS as a teaching fallback, not the main production answer.

Risk or failure mode:

- Inventing an `lm` clone, inventing `olsmt` syntax, or presenting manual matrix OLS as the only GAUSS-native path.

Reference:

- Benchmark Prompt 4.3 in [benchmark prompts](../../evaluations/benchmark-prompts.md).
- Evaluation runs [2026-07-01-code-assistant-manual-run-007.md](../../evaluations/runs/2026-07-01-code-assistant-manual-run-007.md) and [2026-07-01-code-assistant-manual-run-008.md](../../evaluations/runs/2026-07-01-code-assistant-manual-run-008.md).

## 4. Review Public Package API

User prompt:

```text
Review a GAUSS package entry point that exposes fitModel(y, x, ctl) and helper procedures named with leading underscores.
```

What the assistant should do:

- Distinguish public entry points from internal helpers.
- Review argument validation for `y`, `x`, and `ctl`.
- Discuss control-structure defaults and package dependency clarity.
- Keep feedback GAUSS-specific and risk-based.

Risk or failure mode:

- Generic software advice that misses GAUSS procedure, package, and public API concerns.

Reference:

- Benchmark Prompt 5.1 in [benchmark prompts](../../evaluations/benchmark-prompts.md).
- Evaluation run [2026-06-30-code-assistant-manual-run-006.md](../../evaluations/runs/2026-06-30-code-assistant-manual-run-006.md).

## 5. Generate Matrix Standardization Tests

User prompt:

```text
Generate test cases for a GAUSS procedure that standardizes each matrix column.
```

What the assistant should do:

- Cover normal numeric matrices.
- Check that standardized columns have approximately zero mean and unit standard deviation when appropriate.
- Include constant-column, missing-value, single-row, and dimension edge cases.
- State expected outputs or invariants.
- Avoid non-GAUSS testing frameworks unless requested.

Risk or failure mode:

- Ignoring constant columns or missing values, inventing a test framework, or failing to state expected behavior.

Reference:

- Benchmark Prompt 9.1 in [benchmark prompts](../../evaluations/benchmark-prompts.md).
- Evaluation run [2026-07-01-code-assistant-manual-run-014.md](../../evaluations/runs/2026-07-01-code-assistant-manual-run-014.md).
