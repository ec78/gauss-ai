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
