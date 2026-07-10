# Benchmark Prompts

This file evaluates the GAUSS Code Assistant against representative GAUSS programming tasks and known AI failure modes, including invalid syntax, cross-language contamination, hallucinated APIs, data-shape mistakes, and mismatched explanations.

Manual evaluation run files should reference the stable Prompt IDs assigned in this file.

When writing a new prompt's expected behavior, see `workflows/manual-evaluation.md`'s "Benchmark Authoring Guidance" section — in particular, avoid hardcoding volatile repository counts (prompt/coverage/run/index/warning counts) unless the benchmark is explicitly tied to a fixed repository state.

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

## Expert Routing

### Prompt 15.1: GAUSS code generation activates expert

The user asks for GAUSS code to load a dataset, run a simple regression, and explain the result. The response will include GAUSS code and command/procedure recommendations.

Expected behavior:
- Routes through the GAUSS Language Expert because the answer includes GAUSS code and command/procedure usage.
- Applies GAUSS Language Expert decision rules.
- Uses verified native GAUSS procedures when appropriate.
- Does not invent GAUSS syntax, commands, packages, or APIs.
- Distinguishes syntax claims from general explanation.
- Requires official-doc-backed evidence for exact command syntax/defaults/returns.
- Includes a validation suggestion.
- Does not literally need to print "GAUSS Language Expert activated."

### Prompt 15.2: R-to-GAUSS translation uses expert and evidence

The user provides R code using `lm(y ~ x1 + x2, data = df)` and asks for equivalent GAUSS code. The response recommends a native GAUSS procedure.

Expected behavior:
- Routes through the GAUSS Language Expert because this is translation into GAUSS.
- Identifies this as Code Translation with secondary Code Generation.
- Requires command evidence for the native GAUSS procedure before giving exact syntax.
- Prefers verified native GAUSS procedure usage over manual matrix OLS when appropriate.
- Does not silently substitute a manual implementation if verified native evidence exists.
- Includes a validation suggestion comparing GAUSS output with R output.
- Preserves uncertainty for any fields or defaults not verified.

### Prompt 15.3: Debugging cross-language string contamination

The user shows GAUSS-like code that uses a Python-style string `.find()` method and checks for `-1` when the substring is not found. They ask why it is not working.

Expected behavior:
- Routes through the GAUSS Language Expert because this is GAUSS debugging and cross-language contamination.
- Identifies `.find()` / `-1` as Python-style contamination, not GAUSS behavior.
- Requires or uses verified evidence for the relevant GAUSS string function behavior before giving exact return semantics.
- Corrects to real GAUSS behavior such as `strindx` returning `0` when not found, if verified evidence is available.
- Explains the fix without inventing methods or syntax.
- Includes a small validation check or test case.

### Prompt 15.4: Choosing between qnewtonmt and minimize

The user asks which GAUSS optimization command to use for a smooth bounded optimization problem and mentions both `qnewtonmt` and `minimize`.

Expected behavior:
- Routes through the GAUSS Language Expert because this is command selection and version-sensitive GAUSS behavior.
- Uses current, non-stale evidence for both commands if exact claims are made.
- Distinguishes `minimize` as current GAUSS 26 bound-constrained optimization coverage if supported by evidence.
- Preserves `qnewtonmt` as an established native optimization option unless evidence says otherwise.
- Does not claim deprecation or replacement without evidence.
- Does not pick one silently without stating criteria.
- States version assumptions and recommends verifying against current official docs if version matters.

### Prompt 15.5: DataFrame vs matrix design guidance

The user asks whether to use a GAUSS DataFrame or matrix for a workflow that imports labeled data, cleans missing values, then performs numerical modeling.

Expected behavior:
- Routes through the GAUSS Language Expert because this is a GAUSS data-structure decision.
- Uses BODY_OF_KNOWLEDGE-style language mechanics rather than command-specific retrieval unless exact command syntax is requested.
- Distinguishes DataFrame and matrix roles clearly.
- Recommends DataFrame for labeled/imported/mixed/date/categorical/cleaning context where appropriate.
- Recommends matrix for numerical computation/modeling where appropriate.
- Does not treat DataFrames and matrices as interchangeable.
- States assumptions and possible workflow transition points.

### Prompt 15.6: Ambiguous command evidence escalates

The user asks for exact syntax for a command, but the available evidence object has `retrieval_status: ambiguous` with multiple plausible command documentation matches.

Expected behavior:
- Routes through the GAUSS Language Expert because exact GAUSS command syntax is requested.
- Recognizes ambiguous evidence using the operational profile and retrieval-backed response pattern.
- Does not silently choose the top candidate.
- Does not invent syntax to resolve the ambiguity.
- Asks for disambiguating context or routes back to retrieval.
- Uses candidate matches only as candidates, not verified usage.
- Explains that schema-valid ambiguity is not the same as verified command usage.

### Prompt 15.7: Non-GAUSS task does not activate expert

The user asks for a short changelog entry or release note for the repository. The task mentions GAUSS AI but does not require GAUSS code, syntax, command behavior, or data-structure guidance.

Expected behavior:
- Does not route through the GAUSS Language Expert.
- Recognizes this as a non-activation case: release tracking, changelog drafting, or general writing.
- Does not impose GAUSS-specific evidence requirements unnecessarily.
- Does not ask for command documentation or retrieval evidence.
- Still produces a useful changelog/release-note response.
- Demonstrates that negative routing is part of correctness.

## Multi-Expert Routing

### Prompt 16.1: Econometrics-only activation

The user asks whether OLS is appropriate for estimating a causal effect in a conceptual scenario. They do not ask for GAUSS code, syntax, commands, or implementation.

Example prompt: "I have observational data on wages and education, and I want to estimate the causal effect of education on wages using OLS. Is OLS appropriate here, and what assumptions would I need?"

Expected behavior:
- Routes through the Econometrics Expert.
- Does not route through the GAUSS Language Expert.
- Identifies the task as methodology-focused, not implementation-focused.
- Explains that OLS can estimate associations but causal interpretation requires identification assumptions.
- Discusses omitted variable bias/endogeneity and possible design concerns.
- Recommends diagnostics, robustness checks, or alternative strategies where appropriate.
- Does not ask for GAUSS command documentation or official syntax evidence.
- Does not invent GAUSS syntax.
- Does not need a literal "Econometrics Expert activated" label.

### Prompt 16.2: GAUSS-only activation

The user asks for exact syntax or return fields for a GAUSS command, with no request for statistical interpretation.

Example prompt: "What is the exact GAUSS syntax for `strindx`, and what does it return if the substring is not found?"

Expected behavior:
- Routes through the GAUSS Language Expert.
- Does not route through the Econometrics Expert.
- Identifies the task as implementation-focused.
- Requires official-doc-backed evidence for exact syntax and return semantics.
- Correctly uses verified `strindx` behavior if evidence is available.
- Does not discuss model choice, assumptions, diagnostics, or statistical validity.
- Does not claim execution.
- Does not need a literal "GAUSS Language Expert activated" label.

### Prompt 16.3: Both experts activate for R-to-GAUSS regression translation

The user provides R code using `lm(y ~ education + experience, data = wages)` and asks for equivalent GAUSS code plus advice on whether the model is appropriate for interpreting education as causal.

Example prompt: "Can you translate this R code to GAUSS and tell me whether it supports a causal interpretation?

```r
model <- lm(wage ~ education + experience, data = wages)
summary(model)
coef(model)
```"

Expected behavior:
- Routes through both experts.
- GAUSS Language Expert handles implementation correctness and `olsmt` evidence.
- Econometrics Expert handles causal interpretation and assumptions.
- Uses official-doc-backed evidence for exact GAUSS command syntax.
- Does not treat `olsmt` availability as proof that the causal model is appropriate.
- Explains that causal interpretation requires identification assumptions beyond code translation.
- Provides validation suggestions for implementation and diagnostics/robustness suggestions for methodology.
- Keeps implementation and methodology claims distinct.
- Does not claim execution.

### Prompt 16.4: Both experts activate for panel-data method choice in GAUSS

The user asks which GAUSS approach to use for panel data where they have repeated observations by county over time and want to estimate an effect while controlling for county differences.

Example prompt: "I have county-level panel data over 10 years and want to estimate the effect of a policy while controlling for county-level differences. What model should I consider, and how should I think about implementing this in GAUSS?"

Expected behavior:
- Routes through both experts.
- Econometrics Expert handles panel methodology: unit/time structure, fixed effects vs random effects considerations, identification, clustering/serial correlation, diagnostics.
- GAUSS Language Expert handles implementation boundaries and notes that exact GAUSS command syntax requires evidence.
- Does not invent GAUSS panel command syntax.
- Separates methodological recommendation from implementation availability.
- Asks for or states assumptions about treatment timing, panel balance, policy variation, and clustering level.
- Provides next steps without overclaiming.

### Prompt 16.5: Methodologically bad request with valid GAUSS syntax

The user asks for GAUSS code to run a regression and interpret a statistically significant coefficient as causal, but the setup is observational and lacks identification support.

Example prompt: "I have observational customer data and want GAUSS code to regress purchase amount on whether someone saw an ad. If the ad coefficient is significant, can I say the ad caused higher purchases?"

Expected behavior:
- Routes through both experts.
- GAUSS Language Expert may support implementation guidance if code is requested.
- Econometrics Expert flags the causal interpretation problem.
- Does not simply provide code and endorse the causal claim.
- Explains that statistical significance is not causal evidence without design support.
- Suggests design/robustness alternatives such as controls, matching, fixed effects, experiments, instruments, or sensitivity checks as appropriate.
- Does not invent GAUSS syntax unless command evidence is available.
- Keeps "can run this regression" separate from "can interpret it causally."

### Prompt 16.6: Correct command, wrong interpretation

The user has GAUSS regression output or describes output and misinterprets a p-value or coefficient.

Example prompt: "My GAUSS regression output shows the coefficient on price is -0.8 with p = 0.03. Does that mean price explains 3% of the variation in sales?"

Expected behavior:
- Routes through the Econometrics Expert.
- GAUSS Language Expert activates only if GAUSS output mechanics or command-specific fields are needed.
- Corrects the p-value misunderstanding.
- Explains what the coefficient means conditionally, subject to variable units and model specification.
- Distinguishes p-values from R-squared or explanatory power.
- States what additional context is needed for precise interpretation.
- Does not invent GAUSS output-field meanings.
- Does not overclaim causality.

### Prompt 16.7: Multi-expert uncertainty/conflict

The user asks for a GAUSS implementation of a model, but the methodological context is insufficient to know whether the model is appropriate.

Example prompt: "I want to run a logistic regression in GAUSS because my outcome is 0/1. Can you give me the command and tell me if this is the right model?"

Expected behavior:
- Routes through both experts.
- GAUSS Language Expert handles implementation only if evidence for the GAUSS command is available; otherwise routes to retrieval or states verification is needed.
- Econometrics Expert says binary outcome suggests logistic/probit may be candidates but appropriateness depends on goal, data structure, sampling, separation, repeated observations, and interpretation needs.
- Does not let implementation confidence mask methodological uncertainty.
- Does not let methodological plausibility invent exact GAUSS syntax.
- Asks focused clarifying questions or states assumptions.
- Separates "candidate method" from "verified GAUSS implementation."

### Prompt 16.8: Neither expert activates

The user asks for a general changelog or release note about v0.9.0 multi-expert routing. The task mentions GAUSS AI and Econometrics Expert but does not require GAUSS syntax, command behavior, statistical interpretation, or model advice.

Example prompt: "Write a short changelog entry saying we added multi-expert routing with the Econometrics Expert."

Expected behavior:
- Routes through neither operational expert.
- Recognizes this as release tracking/changelog/general writing.
- Does not impose GAUSS command evidence requirements.
- Does not impose econometric-methodology context requirements.
- Produces a useful changelog entry.
- Demonstrates correct negative routing despite expert-related terminology appearing in the request.

## Evidence Coverage and Tracking Guards

### Prompt 17.1: glm schema-aligned evidence exists and validates

The user asks whether local schema-aligned evidence now exists for GAUSS `glm` and whether it validates.

Expected behavior:
- Confirms `examples/retrieval/schema-aligned/glm.evidence.json` exists.
- Reports it was generated from local official `glm.rst`, not hand-written.
- Reports single-file validation passes.
- Reports validate-all default passes.
- Reports validate-all JSON mode passes.
- Notes strict mode fails only because reviewed HDF5 URI path-warning false positives are promoted to failures, now affecting both `glm` and `olsmt`.
- Does not claim schema validation proves GAUSS semantic correctness or execution.
- Mentions any extraction warnings/unresolved questions accurately.

### Prompt 17.2: Logistic regression response uses local glm evidence

The user asks how to run logistic regression in GAUSS and whether logistic regression is appropriate for a binary outcome.

Expected behavior:
- Uses local `glm.evidence.json`, not live docs.
- Routes through both GAUSS Language Expert and Econometrics Expert.
- Uses verified `glm` evidence for implementation facts:
  - `glm` call formats where extracted
  - `family` includes `"binomial"`
  - Binomial default link is `logit`
  - official logistic example if extracted
- Separates verified implementation from methodological appropriateness.
- States that binary outcome makes logistic/probit plausible but appropriateness depends on goal, sampling, repeated observations, separation, omitted variables, and interpretation needs.
- Does not let `glm` availability prove model appropriateness.
- Does not claim execution.

### Prompt 17.3: Panel estimation coverage audit does not invent support

The user asks whether GAUSS AI now has verified local evidence for a panel-estimation command and what the Code Assistant should say if asked for panel regression syntax.

Expected behavior:
- Uses the panel-estimation coverage audit.
- Accurately reports whether a verified general-purpose panel-estimation command was found.
- Distinguishes panel data-management/summary utilities from panel estimation.
- Distinguishes panel unit-root/stationarity tests from panel regression estimation.
- Does not invent panel-estimation command syntax.
- Explains that methodology guidance may still be given by the Econometrics Expert.
- Explains that exact implementation syntax requires verified GAUSS command evidence.
- Identifies follow-ups if coverage remains unresolved.

### Prompt 17.4: Tracking guard catches missing coverage row

The user asks what the evaluation tracking guard should report if a benchmark prompt exists in `evaluations/benchmark-prompts.md` but has no row in `evaluations/benchmark-coverage.md`.

Expected behavior:
- Uses `scripts/check_evaluation_tracking.py` behavior.
- Explains this is a structural error, not just a warning.
- States default mode should fail with nonzero exit.
- Explains why every Prompt ID needs a coverage row.
- Does not modify files during the explanation.
- Does not claim the current repo has this error unless the script actually reported it.

### Prompt 17.5: Tracking guard handles historical warnings

The user asks why `scripts/check_evaluation_tracking.py --strict` fails even though the default tracking check passes.

Expected behavior:
- Reports default mode passes with 0 errors and 2 warnings.
- Explains strict mode promotes warnings to failures.
- Names the two documented warnings:
  - historical 2.2 → run-001 internal Prompt ID 2.3 mismatch
  - unindexed v0.3.0 smoke-test file predating the Prompt ID tracking system
- Explains these are historical/documented states, not current blockers.
- Does not silently recommend rewriting old run files.
- Clearly distinguishes errors from warnings.

### Prompt 17.6: Tracking guard passes current evaluated categories

The user asks whether the current benchmark prompt, coverage, run-file, and index metadata are consistent after the latest evaluated categories.

Expected behavior:
- Runs or reports the current `scripts/check_evaluation_tracking.py` default result.
- Reports:
  - 59 prompt IDs
  - 59 coverage rows
  - 46 run files referenced
  - 51 index entries checked
  - 0 errors
  - 2 warnings
  - overall PASS
- Explains the two warnings as documented historical warnings.
- States strict mode would fail because warnings are promoted.
- Does not claim there are no warnings.
- Does not claim strict mode passes.

## Repository Hygiene and Evaluation Policy Cleanup

### Prompt 18.1: Stale Econometrics operational profile wording fixed

The user asks whether the Econometrics Expert operational profile still says multi-expert routing is not built.

Expected behavior:
- Inspects or references `experts/econometrics/OPERATIONAL_PROFILE.md`.
- Confirms stale wording was fixed.
- States that documented multi-expert routing now exists for GAUSS-only, Econometrics-only, both-experts, and neither-expert tasks.
- States that `v0.9.0` completed and evaluated this documented routing with `16.x` benchmarks.
- Confirms no expert behavior changed.
- Confirms runtime orchestration is still disclaimed.
- Does not imply all experts are operationalized.

### Prompt 18.2: Tracking guard historical warnings are policy-documented

The user asks why the tracking guard still reports two warnings and whether those warnings are blockers.

Expected behavior:
- Uses `evaluations/benchmark-coverage.md`'s Historical Tracking Exceptions section.
- Names both documented warnings:
  - historical `2.2` coverage row points to a run file whose internal Prompt ID is `2.3`
  - `v0.3.0` smoke-test file predates Prompt ID tracking and is intentionally not indexed
- Explains both are preserved as documented historical exceptions.
- Explains default mode may pass with documented warnings.
- Explains strict mode fails because warnings are promoted.
- Does not recommend silently rewriting historical files.
- States new undocumented inconsistencies should not be added under this policy.

### Prompt 18.3: Benchmark authoring avoids volatile hardcoded counts

The user asks what the benchmark-authoring guidance says about hardcoded counts in expected behavior.

Expected behavior:
- Uses `workflows/manual-evaluation.md`'s Benchmark Authoring Guidance section.
- Explains benchmarks should avoid hardcoding volatile repository counts unless tied to a fixed repository state.
- Explains expected behavior should usually require reporting live tool output accurately.
- Distinguishes stable facts from volatile counts.
- Mentions the `17.5`/`17.6` precedent.
- Explains baseline, mid-batch, and post-update states.
- Does not weaken evaluation expectations.

### Prompt 18.4: Econometrics knowledge.md disposition is clear

The user asks whether `experts/econometrics/knowledge.md` is still an active knowledge source.

Expected behavior:
- Inspects or references `experts/econometrics/knowledge.md`.
- Explains it is retained as a compatibility placeholder.
- States `experts/econometrics/BODY_OF_KNOWLEDGE.md` is the active authoritative knowledge source.
- States `knowledge.md` should not be treated as a separate or competing source.
- Notes no repo references depend on the old placeholder content, if supported by current documentation.
- Does not delete or modify files.

### Prompt 18.5: Official package source-type classification works

The user asks whether `command_doc_lookup.py` can now distinguish core official docs from official package docs.

Expected behavior:
- Uses `scripts/command_doc_lookup.py`, `scripts/README.md`, and evidence examples.
- Explains the schema already supported official package source types.
- Explains the implementation now uses an `applications.rst`-derived package directory list.
- Confirms core docs such as `glm` remain `official_docs`/`official_local_rst`.
- Confirms package docs such as `tscsfit` now classify as `official_package_docs`/`official_package_rst`.
- Explains the remaining limitation: the package directory list is a hardcoded snapshot and should be refreshed if the Applications index changes.
- Does not claim live parsing exists if it does not.
- Does not overstate package classification as licensing verification.

### Prompt 18.6: Hygiene changes do not break existing guards

The user asks whether the `v0.11.0` cleanup changes broke evidence validation or evaluation tracking.

Expected behavior:
- Runs or reports:
  - `python scripts/validate_all_evidence.py`
  - `python scripts/validate_all_evidence.py --json`
  - `python scripts/check_evaluation_tracking.py`
  - `python scripts/check_evaluation_tracking.py --json`
- Reports default and JSON modes pass.
- Reports strict modes fail only for documented warning-promoted-to-failure cases:
  - evidence strict: `glm` and `olsmt` HDF5 URI false-positive warnings
  - tracking strict: two documented historical tracking warnings
- Clearly distinguishes default pass from "no warnings."
- Does not claim GAUSS semantic correctness or execution from evidence validation.

## GAUSS Language Knowledge Cleanup and CI Guard Prep

### Prompt 19.1: GAUSS Language knowledge.md disposition is clear

The user asks whether `experts/gauss-language/knowledge.md` is still an active knowledge source.

Expected behavior:
- Inspects or references `experts/gauss-language/knowledge.md`.
- Explains it is retained as a compatibility placeholder.
- States `experts/gauss-language/BODY_OF_KNOWLEDGE.md` is the active authoritative knowledge source.
- States `knowledge.md` should not be treated as a separate or competing source.
- Confirms no behavior change is implied.

### Prompt 19.2: Release readiness check uses default gates

The user asks how to check whether the repository is release-ready right now.

Expected behavior:
- References `scripts/check_release_readiness.py` (or the documented command sequence) as the release-check path.
- States default gates include `scripts/validate_all_evidence.py` and `scripts/check_evaluation_tracking.py`.
- States strict checks are not required for default release readiness.
- Does not suppress or hide any warning.

### Prompt 19.3: Strict-mode CI expectations are documented

The user asks why strict mode fails and what that means for a future CI setup.

Expected behavior:
- Explains strict mode currently fails for documented warning-promoted-to-failure cases.
- Names the evidence strict cases: `glm`/`olsmt` HDF5 URI warnings.
- Names the tracking strict cases: the two historical tracking warnings.
- States future CI should start with default checks unless strict warnings are resolved or explicitly allowlisted.
- Does not recommend hiding warnings to make CI pass.

### Prompt 19.4: Package directory refresh process is documented

The user asks how `PACKAGE_DOC_DIRECTORIES` should be kept up to date.

Expected behavior:
- Explains `PACKAGE_DOC_DIRECTORIES` is derived from the official Applications index (`applications.rst`).
- Explains it is a maintained snapshot, not live parsing.
- Explains the concrete refresh steps.
- Does not claim live parsing exists.
- Does not overstate the classification as licensing verification.

### Prompt 19.5: v0.12 cleanup does not break guards

The user asks whether the `v0.12.0` cleanup changes broke evidence validation or evaluation tracking.

Expected behavior:
- Runs or reports `python scripts/validate_all_evidence.py` and `python scripts/check_evaluation_tracking.py` (default modes).
- Reports both default checks pass.
- Reports strict failures remain limited to the same previously-documented warnings.
- Does not claim GAUSS execution or semantic correctness from evidence validation.

## Default CI Guard Integration

### Prompt 20.1: CI workflow runs default release-readiness check

The user asks whether the repository now has CI for the release-readiness gate and what command it runs.

Expected behavior:
- Confirms `.github/workflows/release-readiness.yml` exists.
- States the workflow runs on `push` and `pull_request`.
- States the workflow uses Python 3.11.
- States the workflow installs `jsonschema`.
- States the workflow runs `python scripts/check_release_readiness.py`.
- Explains this is the default release-readiness gate.
- Does not claim strict mode is run by CI.

### Prompt 20.2: CI does not enforce strict mode

The user asks whether CI will fail because strict mode currently fails.

Expected behavior:
- Explains CI does not run `--strict`.
- Explains CI runs only `python scripts/check_release_readiness.py`.
- Explains strict failures remain documented informational/future warning-free gates.
- Names the known strict failure categories:
  - evidence strict: `glm` and `olsmt` HDF5 URI warnings
  - tracking strict: two documented historical tracking warnings
- Explains CI should pass if default release-readiness passes.
- Does not suggest hiding or suppressing warnings.

### Prompt 20.3: CI documentation explains default vs strict

The user asks where the repo documents the difference between default CI checks and strict checks.

Expected behavior:
- Uses `scripts/README.md` and `RELEASE_CHECKLIST.md`.
- Explains default checks are current release-health gates.
- Explains strict checks are informational/future warning-free gates.
- Explains CI starts with default checks only.
- Explains warnings remain visible and are not suppressed.
- Does not imply strict checks are passing.

### Prompt 20.4: CI workflow does not suppress warnings

The user asks whether the CI workflow hides warnings so the build can pass.

Expected behavior:
- Inspects or references `.github/workflows/release-readiness.yml`.
- Confirms the workflow runs the normal release-readiness command without redirecting or suppressing output.
- Explains warnings remain visible in logs.
- Explains default pass can still include documented warnings.
- Does not claim there are no warnings.
- Does not recommend suppressing warnings.

### Prompt 20.5: v0.13 CI integration does not break local guards

The user asks whether adding the CI workflow changed or broke local validation, tracking, or release-readiness checks.

Expected behavior:
- Runs or reports:
  - `python scripts/check_release_readiness.py`
  - `python scripts/check_release_readiness.py --json`
  - optionally the underlying default checks if needed:
    - `python scripts/validate_all_evidence.py`
    - `python scripts/check_evaluation_tracking.py`
- Reports default release-readiness passes.
- Reports JSON `overall_pass` is true.
- Explains strict mode remains informational and is not required for CI.
- Does not claim GAUSS semantic correctness or execution from evidence validation.

## Software Engineering Expert Foundation

Use Prompt IDs 21.1-21.8. These exercise the Software Engineering Expert (`experts/software-engineering/OPERATIONAL_PROFILE.md`) and the eight routing types documented in `workflows/expert-routing.md`, extending the two-expert coverage validated by `16.x` to three experts.

### Prompt 21.1: Software-engineering-only code review

The user asks for a maintainability review of generic pseudocode or non-GAUSS code with no econometric content.

Example prompt: "Can you review this generic pseudocode for maintainability? It loads data, cleans missing values, computes a few summary numbers, and prints a report, all in one long function. I am not asking about GAUSS syntax or statistics — just whether the structure is maintainable."

Expected behavior:
- Activates Software Engineering Expert only.
- Does not activate GAUSS Language Expert.
- Does not activate Econometrics Expert.
- Identifies maintainability issues such as one long function, mixed responsibilities, hidden assumptions, weak testability, and reporting coupled to data cleaning.
- Suggests refactoring into smaller responsibilities.
- Suggests tests or validation checks.
- Does not invent GAUSS syntax.
- Does not make statistical claims.

### Prompt 21.2: GAUSS + Software Engineering refactor

The user provides GAUSS-like code with repeated blocks and asks for a cleaner structure.

Example prompt: "I have GAUSS code with the same data-cleaning block copied before three different models. Can you help me refactor it into a cleaner structure without changing behavior?"

Expected behavior:
- Activates GAUSS Language Expert and Software Engineering Expert.
- GAUSS Language Expert owns GAUSS syntax and implementation validity.
- Software Engineering Expert owns refactor strategy, behavior preservation, duplication reduction, and testability.
- Recommends extracting repeated logic into a helper/procedure only with GAUSS-valid syntax or clearly labeled pseudocode.
- Explains behavior-preserving refactor principles.
- Suggests comparing old and new outputs.
- Does not claim tests were run.
- Does not invent unverified GAUSS syntax.

### Prompt 21.3: Econometrics + Software Engineering design review

The user describes an econometric workflow that mixes data cleaning, model fitting, diagnostics, and reporting in one script and asks how to improve it.

Example prompt: "I have an econometric analysis script that imports the data, cleans it, estimates the model, runs diagnostics, and writes final tables all in one long file. How should I organize this better so the analysis is easier to maintain and the diagnostics are not forgotten?"

Expected behavior:
- Activates Econometrics Expert and Software Engineering Expert.
- Does not require GAUSS Language Expert unless GAUSS-specific syntax is requested.
- Econometrics Expert owns diagnostics/modeling workflow concerns.
- Software Engineering Expert owns decomposition, maintainability, and workflow organization.
- Recommends separating data prep, model estimation, diagnostics, and reporting.
- Suggests validation/checkpoints.
- Does not invent GAUSS syntax.
- Does not claim causal/statistical validity from clean organization alone.

### Prompt 21.4: All three experts activate

The user asks for GAUSS code to estimate logistic regression, structure the code cleanly, and explain whether logistic regression is appropriate.

Example prompt: "Can you show me how to run a logistic regression in GAUSS for a binary outcome, structure the code cleanly so I can reuse it, and tell me whether logistic regression is automatically the right model?"

Expected behavior:
- Activates GAUSS Language Expert, Econometrics Expert, and Software Engineering Expert.
- Uses local `glm.evidence.json` (`examples/retrieval/schema-aligned/glm.evidence.json`) for GAUSS implementation facts.
- GAUSS Language Expert owns `glm` syntax/family/link implementation facts.
- Econometrics Expert explains binary outcome makes logistic regression plausible but not automatically right; appropriateness depends on goal, sampling, repeated observations, separation, omitted variables, and interpretation needs.
- Software Engineering Expert recommends reusable structure, separation of setup/modeling/output, and tests/checks.
- Keeps implementation, methodology, and maintainability claims separate.
- Does not claim execution.
- Does not let clean code imply model validity.

### Prompt 21.5: Software Engineering does not override GAUSS evidence

The user asks to refactor GAUSS code using Python-like constructs because they look cleaner.

Example prompt: "Can you refactor my GAUSS code to use Python-style list comprehensions and dictionary syntax? It would look cleaner that way."

Expected behavior:
- Activates GAUSS Language Expert and Software Engineering Expert.
- Software Engineering Expert may support the goal of cleaner structure.
- GAUSS Language Expert prevents invalid or unverified GAUSS syntax.
- Response prioritizes valid GAUSS over aesthetic Python-like constructs.
- Suggests GAUSS-appropriate or pseudocode-labeled alternatives.
- Does not invent GAUSS syntax.
- Does not claim Python-like constructs are valid GAUSS without evidence.

### Prompt 21.6: Software Engineering does not make causal claims

The user asks whether cleaner code organization makes regression results more causal or reliable.

Example prompt: "If I refactor my regression code and make it cleaner, does that make my results more causal or statistically reliable?"

Expected behavior:
- Activates Software Engineering Expert and Econometrics Expert.
- Software Engineering Expert explains cleaner code can improve reproducibility, reviewability, and reduce implementation mistakes.
- Econometrics Expert explains causal validity/statistical reliability depend on research design, assumptions, data quality, estimator choice, diagnostics, and identification, not code cleanliness alone.
- Does not overclaim.
- Does not require GAUSS Language Expert unless syntax is discussed.
- Separates maintainability/reproducibility from causal/statistical validity.

### Prompt 21.7: Testing and validation advice without execution claim

The user asks how to test a refactored GAUSS procedure.

Example prompt: "I refactored a GAUSS procedure into smaller helper procedures. How should I test that I did not change the behavior?"

Expected behavior:
- Activates Software Engineering Expert.
- Activates GAUSS Language Expert if GAUSS-specific testing or syntax advice is given.
- Suggests comparing old vs new outputs on representative inputs.
- Suggests edge cases, missing/empty data checks, dimension/shape checks, and regression checks.
- Suggests keeping expected outputs for known examples.
- Does not claim tests were run.
- Does not require new tooling unless clearly optional.
- Labels any unverified syntax or pseudocode clearly.

### Prompt 21.8: Neither expert activation for general writing task

The user asks for a short release-note blurb unrelated to code, GAUSS, or econometrics.

Example prompt: "Can you write a short release-note blurb saying this update improves the user experience and fixes several small issues?"

Expected behavior:
- Does not activate Software Engineering Expert.
- Does not activate GAUSS Language Expert.
- Does not activate Econometrics Expert.
- Gives normal writing help.
- Does not impose expert routing unnecessarily.
- Does not mention GAUSS, econometrics, code quality, or operational experts unless the user asks.

## Documentation Expert Foundation

Use Prompt IDs 22.1-22.8. These exercise the Documentation Expert (`experts/documentation/OPERATIONAL_PROFILE.md`) and the routing patterns added to `workflows/expert-routing.md` for the fourth operational expert, extending the three-expert coverage validated by `21.x` to four experts.

### Prompt 22.1: Documentation-only rewrite

The user asks to rewrite a confusing technical note into clearer user-facing documentation, with no GAUSS syntax or statistics involved.

Example prompt: "Can you rewrite this technical note into clearer user-facing documentation? Current note: 'The file loader takes the thing, checks what is missing, and makes the output available downstream. Users should make sure it worked before continuing.' I am not asking about GAUSS syntax, statistics, or code design — just documentation clarity."

Expected behavior:
- Activates Documentation Expert only.
- Does not activate GAUSS Language Expert.
- Does not activate Econometrics Expert.
- Does not activate Software Engineering Expert.
- Improves structure, clarity, assumptions, and reader guidance.
- Clarifies vague phrases such as "the thing" and "make sure it worked."
- Does not invent technical details beyond the source material.
- Does not turn this into curriculum design.

### Prompt 22.2: GAUSS + Documentation

The user asks to document a GAUSS procedure and include a usage example.

Example prompt: "Can you help me document a GAUSS procedure that calculates a z-score? I want a short description, inputs, outputs, and a usage example."

Expected behavior:
- Activates GAUSS Language Expert and Documentation Expert.
- GAUSS Language Expert owns GAUSS syntax and example validity.
- Documentation Expert owns explanation, structure, parameter descriptions, return/output descriptions, and usage clarity.
- Uses verified GAUSS syntax where possible or labels pseudocode clearly.
- Does not invent command behavior.
- Keeps syntax/evidence claims separate from documentation-quality claims.

### Prompt 22.3: Econometrics + Documentation

The user asks to document model assumptions and interpretation caveats for regression output.

Example prompt: "Can you help me write documentation that explains the assumptions and interpretation caveats for an OLS regression output?"

Expected behavior:
- Activates Econometrics Expert and Documentation Expert.
- Econometrics Expert owns assumptions and interpretation correctness.
- Documentation Expert owns clarity, caveats, audience fit, and reader-facing structure.
- Includes caveats about association vs causation unless identification supports causal claims.
- Does not overclaim causal validity.
- Does not require GAUSS Language Expert unless GAUSS-specific syntax is discussed.

### Prompt 22.4: Software Engineering + Documentation

The user asks to add comments/docstrings to a refactored helper function and explain its design intent.

Example prompt: "I refactored a helper function that validates input data before analysis. Can you help me write comments or a docstring that explain its purpose, inputs, outputs, assumptions, and design intent?"

Expected behavior:
- Activates Software Engineering Expert and Documentation Expert.
- Software Engineering Expert owns design intent, maintainability, and validation-purpose boundaries.
- Documentation Expert owns comment/docstring clarity, structure, and audience awareness.
- Comments explain intent and assumptions, not obvious mechanics.
- Does not claim tests were run.
- Does not claim documentation quality proves design quality.

### Prompt 22.5: All four experts activate

The user asks for GAUSS logistic regression code, clean reusable structure, model appropriateness explanation, and user-facing documentation.

Example prompt: "Can you show me how to run logistic regression in GAUSS for a binary outcome, structure the code so I can reuse it, explain whether logistic regression is automatically appropriate, and write a short user-facing documentation section for the workflow?"

Expected behavior:
- Activates GAUSS Language Expert, Econometrics Expert, Software Engineering Expert, and Documentation Expert.
- Uses local `glm` evidence (`examples/retrieval/schema-aligned/glm.evidence.json`) for implementation facts if available.
- GAUSS Language Expert owns `glm` syntax/family/link implementation facts.
- Econometrics Expert explains binary outcome makes logistic regression plausible but not automatically right.
- Software Engineering Expert recommends reusable structure, separation of setup/modeling/output, and validation checks.
- Documentation Expert writes or recommends a clear user-facing documentation section.
- Keeps implementation, methodology, maintainability, and documentation claims separate.
- Does not claim execution.
- Does not invent syntax.
- Does not let clear documentation imply model validity or maintainability.

### Prompt 22.6: Documentation Expert does not replace Education Expert

The user asks for a six-week curriculum to teach beginners econometrics in GAUSS.

Example prompt: "Can you build a six-week curriculum to teach beginners econometrics in GAUSS, with weekly learning objectives, exercises, and progression?"

Expected behavior:
- Recognizes this is primarily Education Expert territory, not Documentation Expert.
- Since the Education Expert is not operationalized, handles it as normal education/planning help or marks future Education routing without claiming Education Expert operationalization.
- Documentation Expert may be mentioned only as supporting reference-doc clarity, not owning curriculum design.
- Does not overclaim Documentation Expert scope.
- Does not overclaim Education Expert operationalization.
- Uses normal helpful response behavior.

### Prompt 22.7: Documentation Expert does not validate syntax

The user asks whether a beautifully written documentation page proves the GAUSS code example is valid.

Example prompt: "If a documentation page is clear and well written, does that mean the GAUSS code example in it is valid?"

Expected behavior:
- Activates Documentation Expert and GAUSS Language Expert.
- Documentation Expert explains clarity and structure do not prove syntax correctness.
- GAUSS Language Expert/evidence is required for GAUSS syntax validation.
- Does not validate syntax from prose quality.
- Explains that examples need verified syntax or must be labeled pseudocode/unverified.
- Does not claim execution.

### Prompt 22.8: Neither expert activation for nontechnical marketing blurb

The user asks for a nontechnical marketing sentence unrelated to docs, code, GAUSS, or econometrics.

Example prompt: "Can you write a friendly one-sentence marketing blurb saying our update makes the experience smoother and easier to use?"

Expected behavior:
- Does not activate Documentation Expert.
- Does not activate GAUSS Language Expert.
- Does not activate Econometrics Expert.
- Does not activate Software Engineering Expert.
- Gives normal writing help.
- Does not impose expert routing unnecessarily.
- Does not mention GAUSS, econometrics, code quality, documentation, or operational experts unless the user asks.
