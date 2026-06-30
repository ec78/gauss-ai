# Benchmark Prompts

This file evaluates the GAUSS Code Assistant against representative GAUSS programming tasks and known AI failure modes, including invalid syntax, cross-language contamination, hallucinated APIs, data-shape mistakes, and mismatched explanations.

Manual evaluation run files should reference the stable Prompt IDs assigned in this file.

## Code Generation

### Prompt 1.1: Matrix summary procedure

Write a GAUSS procedure `summarizeCols(x)` that returns a matrix with each column's mean, standard deviation, minimum, and maximum.

Expected behavior:
- Uses valid GAUSS procedure syntax and matrix operations.
- Avoids Python, R, or MATLAB idioms such as `def`, `data.frame`, or `end`.
- Does not invent unsupported GAUSS helper functions.

### Prompt 1.2: String parser

Write a GAUSS procedure that takes a string like `"alpha=0.10"` and returns the text before and after the first equals sign.

Expected behavior:
- Uses GAUSS string functions, including `strlen` and `strindx`.
- Handles the case where `strindx` returns `0` when `"="` is not found.
- Avoids assuming string indexing behavior from Python or MATLAB.

### Prompt 1.3: DataFrame cleaning script

Draft a short GAUSS script that loads a dataset, drops rows with missing values in selected variables, and prints basic summaries.

Expected behavior:
- Distinguishes script-level code from reusable procedures.
- Handles missing values using GAUSS-appropriate operations.
- Does not hallucinate DataFrame methods from pandas, R, or MATLAB tables.

## Debugging

### Prompt 2.1: Array dimension error

Debug this GAUSS snippet:

```gauss
a = arrayinit(3|4|2, 0);
n = rows(a);
print n;
```

Expected behavior:
- Explains why `rows` is inappropriate for arrays.
- Recommends GAUSS array dimension inspection rather than matrix-only functions.
- Avoids converting the issue into a Python NumPy explanation.

### Prompt 2.2: String search bug

Explain why this condition fails when the pattern is absent:

```gauss
idx = strindx(name, "_");
if idx < 0;
    print "not found";
endif;
```

Expected behavior:
- States that `strindx` returns `0` when not found.
- Corrects the conditional logic.
- Mentions `strlen` only when useful, without forcing it into the answer.

### Prompt 2.3: Scope and package dependency

A user reports `Undefined symbol qardl` after copying a procedure call from package documentation. Diagnose likely causes.

Expected behavior:
- Checks whether the package is installed, loaded, and on the GAUSS path.
- Distinguishes public package APIs from internal helper procedures.
- Considers naming, scope, and procedure availability before rewriting code.

## Code Explanation

### Prompt 3.1: Beginner matrix explanation

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

### Prompt 3.2: Advanced structure explanation

Explain how a GAUSS control structure is used to pass options into a procedure, assuming the reader is an advanced GAUSS user.

Expected behavior:
- Describes structures as typed containers for configuration.
- Distinguishes structures from matrices, arrays, and DataFrames.
- Uses concise expert-level language without overexplaining basics.

## Code Translation

### Prompt 4.1: MATLAB to GAUSS

Translate this MATLAB-style logic into GAUSS:

```matlab
for i = 1:length(names)
    if contains(names{i}, "_")
        disp(names{i})
    end
end
```

Expected behavior:
- Avoids MATLAB cell-array syntax and `contains`.
- Uses GAUSS string-array handling and `strindx` correctly.
- Handles `strindx` returning `0` when no match exists.

### Prompt 4.2: Python to GAUSS

Translate this Python idea into GAUSS: compute column means for a numeric matrix, replace missing values with column means, and return the cleaned matrix.

Expected behavior:
- Avoids Python list comprehensions, `None`, `np.nan`, and pandas methods.
- Handles GAUSS missing values and matrix dimensions correctly.
- Produces GAUSS-shaped algorithm guidance or snippets only.

### Prompt 4.3: R to GAUSS regression setup

Translate this R-style workflow into GAUSS:

```r
model <- lm(y ~ x1 + x2, data = df)
summary(model)
```

Expected behavior:
- Does not blindly use R formula syntax unless supported by a specific GAUSS procedure.
- Explains DataFrame-to-matrix preparation for dependent variable `y` and independent variables `x1` and `x2`.
- States assumptions about intercept handling.
- Mentions `olsmt` as the preferred native GAUSS OLS procedure when appropriate.
- Treats manual matrix OLS as a teaching fallback or custom implementation, not the only GAUSS-native option.
- Prefers verified built-in GAUSS procedures for common modeling workflows when available.
- Avoids inventing an `lm` clone, `summary` clone, or unsupported R-style API.

## Code Review

### Prompt 5.1: Review public API design

Review a proposed GAUSS package entry point that exposes `fitModel(y, x, ctl)` and several helper procedures named with leading underscores.

Expected behavior:
- Distinguishes public APIs from internal helper procedures.
- Checks argument validation, structure defaults, and package dependency clarity.
- Focuses on GAUSS maintainability rather than generic style advice.

### Prompt 5.2: Review matrix and array usage

Review code that mixes matrices and arrays and calls `rows()` and `cols()` on every object.

Expected behavior:
- Flags improper use of matrix dimension functions on arrays.
- Suggests GAUSS-appropriate dimension handling for each data type.
- Notes potential downstream dimension and indexing bugs.

## Refactoring

### Prompt 6.1: Procedure cleanup

Refactor a long GAUSS procedure that computes estimates, prints output, and writes files in one block.

Expected behavior:
- Separates computation, reporting, and file output concerns.
- Preserves behavior and public API compatibility.
- Avoids unnecessary abstractions or non-GAUSS design patterns.

### Prompt 6.2: Control structure defaults

Suggest a refactor for repeated option parsing code across several GAUSS procedures.

Expected behavior:
- Recommends a shared control-structure initialization pattern.
- Handles missing fields and defaults clearly.
- Keeps package public APIs stable.

## Optimization

### Prompt 7.1: Loop to matrix operation

Optimize GAUSS code that loops over rows to compute column sums for a large matrix.

Expected behavior:
- Recommends vectorized matrix operations where appropriate.
- Explains dimension assumptions and missing-value implications.
- Avoids premature optimization that changes results.

### Prompt 7.2: String processing efficiency

Improve a GAUSS routine that repeatedly calls `strlen` and `strindx` inside nested loops over many names.

Expected behavior:
- Identifies redundant string work and possible caching.
- Preserves correct `strindx == 0` not-found behavior.
- Does not propose unavailable regex or Python string APIs.

## Documentation

### Prompt 8.1: Procedure usage docs

Draft concise documentation for a GAUSS procedure `winsorizeDF(df, vars, limits)` that returns a cleaned DataFrame.

Expected behavior:
- Documents inputs, outputs, missing-value behavior, and examples.
- Uses GAUSS terminology for DataFrames and variables.
- Avoids promising unsupported methods or package features.

### Prompt 8.2: Package README section

Write a README section explaining how users should load a GAUSS package and call its public procedures.

Expected behavior:
- Distinguishes installation, loading, and API usage.
- Warns against calling internal helpers directly.
- Keeps documentation concise and practical.

## Test Generation

### Prompt 9.1: Matrix procedure tests

Generate test cases for a GAUSS procedure that standardizes each matrix column.

Expected behavior:
- Covers normal, constant-column, missing-value, and dimension edge cases.
- States expected outputs or invariants clearly.
- Avoids using non-GAUSS testing frameworks unless requested.

### Prompt 9.2: String utility tests

Generate tests for a GAUSS string utility that splits a name at the first underscore.

Expected behavior:
- Covers no underscore, leading underscore, trailing underscore, and multiple underscores.
- Checks `strindx` not-found behavior explicitly.
- Uses concise benchmark snippets without unrelated implementation code.

## Design Guidance

### Prompt 10.1: Choose data representation

Advise whether a GAUSS package should represent model results as a structure, matrix, DataFrame, or array.

Expected behavior:
- Compares tradeoffs for matrices, DataFrames, arrays, and structures.
- Considers public API stability and downstream reporting.
- Avoids one-size-fits-all recommendations.

### Prompt 10.2: Beginner vs advanced response

For the same GAUSS dimension mismatch error, explain how the assistant should respond to a beginner and to an advanced user.

Expected behavior:
- Adapts depth, terminology, and tone to each audience.
- Includes concrete GAUSS debugging steps for dimensions and scope.
- Avoids language contamination and hallucinated functions in both versions.
