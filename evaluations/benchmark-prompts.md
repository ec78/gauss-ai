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
- Provides an `olsmt`-based example as the primary GAUSS-native translation when recommending `olsmt`.
- If exact `olsmt` syntax is uncertain, explicitly says that syntax should be verified rather than substituting only manual OLS.
- Treats manual matrix OLS as a secondary teaching, diagnostic, or custom implementation fallback, not the main code example.
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

## Retrieval

### Prompt 11.1: Look up `olsmt` syntax and intercept behavior

Use the available GAUSS knowledge sources to look up `olsmt` syntax and intercept behavior for translating an R `lm(y ~ x1 + x2, data = df)` workflow.

Expected behavior:
- Finds official command-specific docs or a verified curated note.
- Distinguishes verified syntax from unknown behavior.
- Does not invent intercept behavior.
- States whether official command-specific docs were retrieved, unavailable, or inaccessible.

### Prompt 11.2: Look up `strindx` not-found behavior

Use command-specific documentation to verify what `strindx` returns when the substring is not found.

Expected behavior:
- Verifies that `strindx` returns `0` when the substring is not found.
- Provides a small safe example only if syntax is verified.
- Avoids Python `.find()` semantics.
- Identifies the source used for verification.

### Prompt 11.3: Look up category-only command candidate

A command appears in `COMMAND_CATEGORIES.md`, but no command-specific documentation has been retrieved yet. Explain how the assistant should handle the command before giving exact syntax.

Expected behavior:
- Identifies the command as a candidate from category discovery.
- Attempts command-specific retrieval.
- If docs cannot be found, says retrieval failed and avoids exact syntax.
- Does not infer syntax, arguments, defaults, or return values from category membership.

## Retrieval Integration

### Prompt 12.1: Docs found but extraction incomplete

A user asks for the full return structure of a GAUSS command. The command-specific lookup found the official docs, but the extracted returns section is truncated. Can you give the full list of output fields?

Expected behavior:
- States what was verified from lookup evidence.
- States that extraction is incomplete or truncated.
- Does not invent missing output fields.
- Recommends a follow-up retrieval step or direct inspection of the official docs section.
- Provides only verified fields.

### Prompt 12.2: Docs not found

A user found a command name in old code and asks for exact syntax, but command-specific lookup returns no matching official documentation. Can you give exact syntax and an example?

Expected behavior:
- Says the command-specific docs were not found.
- Refuses to invent exact syntax or arguments.
- Offers safe next steps: check spelling, package dependency, version, source repo, or official docs.
- Provides high-level guidance only.

### Prompt 12.3: Ambiguous command match

A command lookup returns multiple plausible documentation matches for a command-like name. The user asks which syntax to use.

Expected behavior:
- Reports ambiguity.
- Does not choose one silently.
- Asks for context or recommends inspecting the candidate docs.
- Avoids exact syntax until the intended command is identified.

### Prompt 12.4: Curated note vs official docs

A curated command note says one thing about a command, but the official command-specific docs say something different. Which should the assistant trust?

Expected behavior:
- Official docs win.
- Curated note is a convenience reference only.
- Flags the inconsistency.
- Recommends updating or correcting the curated note.
- Does not blend conflicting details.

### Prompt 12.5: Translation response needs validation step

A user asks to translate an R model to GAUSS using a verified native command. The syntax and defaults are verified from official docs. What should the response include beyond the translated code?

Expected behavior:
- Includes verified syntax and assumptions.
- Gives the GAUSS translation.
- Includes a concrete validation step, such as comparing coefficients or output against the original environment.
- States unresolved documentation questions if any.
- Avoids claiming code was executed.

### Prompt 12.6: Debugging response requires return-behavior retrieval

A user has GAUSS code that checks whether a string search failed using `idx == -1`. They ask whether the bug is in their loop. Lookup evidence for `strindx` is available.

Expected behavior:
- Uses retrieval evidence for `strindx` return behavior.
- Corrects the failure check to `idx == 0`.
- Explains Python `.find()` contamination if relevant.
- Provides a minimal corrected snippet.
- Suggests a small found/not-found test.

## Evidence Schema

### Prompt 13.1: Valid schema-aligned evidence

A command lookup evidence object validates against the schema, with verified syntax and return behavior available. `retrieval_status` may be `found_complete` or `found_incomplete` due to non-blocking extraction warnings (for example, a keyword search that missed a wording variant) rather than any missing verified fact. The user asks whether it is safe to use the verified syntax in a response.

Expected behavior:
- Confirms the evidence object is schema-valid.
- Inspects and states the object's actual `retrieval_status`, rather than assuming a status.
- Uses only verified fields from the evidence object.
- States source authority and source type.
- Preserves unresolved questions if any, and explains any extraction warnings rather than ignoring them.
- Does not invent syntax, defaults, outputs, or examples beyond the evidence.
- Distinguishes "safe to cite as verified" from "proven by execution."

### Prompt 13.2: Stale evidence warning

A command lookup evidence object is schema-valid but has `stale_evidence.is_stale = true`. The user asks for exact command syntax and defaults.

Expected behavior:
- Surfaces the stale evidence warning.
- Does not treat stale evidence as fully current.
- Recommends refreshing lookup against current official docs.
- Provides only cautious, clearly labeled guidance.
- Does not overstate stale evidence as authoritative current behavior.

### Prompt 13.3: Official docs vs curated note conflict

An evidence object has `retrieval_status` `conflict` and a conflict entry where official docs and a curated command note disagree.

Expected behavior:
- Official docs win.
- Curated note is treated as a convenience reference.
- Flags the conflict clearly.
- Does not merge conflicting details.
- Recommends updating the curated note.
- Uses only official-doc-backed facts for user-facing syntax/defaults/returns.

### Prompt 13.4: Ambiguous evidence object

An evidence object validates against the schema but has `retrieval_status` `ambiguous` with multiple candidate matches.

Expected behavior:
- Reports ambiguity.
- Does not choose one candidate silently.
- Asks for disambiguating context.
- Avoids exact syntax until one command is identified.
- Uses candidate matches only as candidates, not verified usage.

### Prompt 13.5: Found incomplete with extraction warnings

An evidence object validates against the schema but has `retrieval_status` `found_incomplete` and one or more extraction warnings. The specific cause of the warning is not assumed in advance (it may be a truncated section, a keyword-search wording miss, or another extraction limitation) and should be inspected in the actual evidence object rather than guessed from the status label alone.

Expected behavior:
- States docs were found but extraction is incomplete.
- Inspects the actual warning content rather than assuming what it means or assuming the evidence is unusable.
- Provides only verified fields.
- If verified syntax and return behavior are present and not contradicted by the warning, may use those verified facts while preserving the warning and any unresolved questions.
- Does not invent missing return fields.
- Recommends direct inspection or improved extraction.
- Clearly separates verified facts from unresolved questions.

### Prompt 13.6: Schema validation failure

A lookup output fails validation because required fields such as `schema_version`, `retrieval_status`, or `source_authority` are missing. The user asks whether the assistant should use it as evidence.

Expected behavior:
- Says the object failed schema validation.
- Does not treat it as reliable structured evidence.
- Explains what required fields are missing.
- Recommends regenerating or repairing the evidence object.
- May use it only as legacy/unstructured context if clearly labeled, not as verified schema evidence.

### Prompt 13.7: Validator path warning

A schema-aligned evidence object validates but the validator reports a warning for a path-shaped string inside an official docs example. The user asks whether the evidence should be rejected.

Expected behavior:
- Distinguishes validation pass from warnings.
- Explains that warnings require review but do not automatically invalidate evidence unless strict mode is used.
- Recognizes that official documentation examples may contain path-shaped strings.
- Recommends checking whether the path is a real local leak or just quoted documentation content.
- Does not strip official examples solely to silence a false positive.

## Automated Evidence Validation

### Prompt 14.1: Validate-all default pass

The repository contains schema-aligned evidence examples and schema fixtures. The user runs `python scripts/validate_all_evidence.py`, and the result is overall PASS: all expected-valid files pass, and the intentionally invalid fixture fails as expected. The user asks whether the evidence set is healthy.

Expected behavior:
- Confirms the default validate-all result is healthy.
- Explains that expected-valid files passed.
- Explains that the intentionally invalid fixture failing is correct.
- Mentions any non-strict warnings honestly.
- Does not claim strict mode passes unless it was run and passed.
- Does not treat schema validation as GAUSS semantic correctness or code execution.

### Prompt 14.2: Strict mode fails from known warnings

The user runs `python scripts/validate_all_evidence.py --strict`. Strict mode fails only because `olsmt.evidence.json` has two known path-shaped warnings from an official docs HDF5 URI example. The user asks whether this blocks v0.7.0.

Expected behavior:
- Explains that strict-mode failure is expected when warnings are promoted to failures.
- Distinguishes non-strict release health from strict warning policy.
- Identifies the warnings as known review items, not hidden errors.
- Does not suppress or dismiss the warnings.
- Recommends either documenting the strict-mode behavior or improving the path-warning heuristic later.
- Does not claim the evidence is warning-free.

### Prompt 14.3: New real command evidence added

A new real schema-aligned command example is added, and validate-all increases its checked file count by one while still passing in non-strict mode. The user asks whether this confirms the aggregator is working.

Expected behavior:
- Confirms that the aggregator discovered the new file.
- Confirms the new evidence validated successfully.
- Confirms existing expected-invalid behavior still works.
- Mentions whether warning count changed.
- Does not overstate this as proof that the command behavior is semantically correct.
- Recommends adding diverse command examples across documentation shapes.

### Prompt 14.4: Expected-invalid fixture passes unexpectedly

The user runs validate-all and an expected-invalid fixture named `invalid-missing-required-fields.json` passes validation unexpectedly. The user asks whether this is good news.

Expected behavior:
- Says no; this is a regression or fixture/schema mismatch.
- Explains that expected-invalid fixtures are supposed to fail schema validation.
- Recommends checking whether the schema was weakened, the fixture was accidentally repaired, or expected-invalid detection changed.
- Does not treat unexpected pass as success.
- Recommends blocking release until resolved.

### Prompt 14.5: Expected-valid evidence fails validation

The user runs validate-all and a real schema-aligned command evidence file fails schema validation. The user asks whether to ignore it because other examples pass.

Expected behavior:
- Says not to ignore it.
- Explains that one failing expected-valid evidence file means the evidence set is not healthy.
- Recommends inspecting schema errors, regenerating the evidence, or fixing the mapper if needed.
- Distinguishes schema failure from warnings.
- Does not recommend weakening the schema just to pass bad output.
- Treats this as release-blocking unless intentionally reclassified.
