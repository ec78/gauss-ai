# GAUSS Language Body of Knowledge

## Knowledge Domains

The GAUSS Language Expert is organized around the following domains.

## Domain 1 — Language Fundamentals

Language fundamentals define the baseline knowledge required to write valid, readable, and idiomatic GAUSS code.

This domain focuses on the core syntax, program structure, and language concepts that every GAUSS-focused agent must understand before writing, reviewing, translating, or debugging GAUSS code.

### 1.1 Core Mental Model

GAUSS is a matrix-oriented programming language designed for numerical, statistical, econometric, and scientific computing.

A GAUSS-focused agent should understand GAUSS as its own language, not as a variant of Python, R, MATLAB, or pseudocode.

Important principles:

* GAUSS is matrix-oriented.
* GAUSS code often works directly with matrices, vectors, scalars, strings, structures, arrays, DataFrames, and categorical variables.
* GAUSS supports both interactive exploration and reusable program development.
* GAUSS procedures use GAUSS syntax, not Python, R, MATLAB, or JavaScript syntax.
* GAUSS code should be written to match the user's goal: learning, analysis, debugging, package development, or production use.
* GAUSS agents should prefer valid, simple, readable code over clever but uncertain code.

Common failure modes:

* Treating GAUSS as MATLAB with slightly different syntax.
* Treating GAUSS as Python with matrices.
* Writing pseudocode that looks plausible but will not run.
* Ignoring GAUSS data structures and procedure rules.
* Inventing syntax from other languages.

### 1.2 Language Philosophy

GAUSS is especially strong for matrix operations, econometrics, statistics, optimization, simulation, and numerical programming.

A GAUSS solution should usually be:

* Explicit about inputs and outputs.
* Clear about matrix dimensions.
* Careful with missing values.
* Appropriate for the data structure.
* Readable enough for the intended user.
* Consistent with GAUSS idioms.

Agent guidance:

* Prefer matrix operations when they naturally express the computation.
* Do not force vectorization when a loop is clearer or necessary.
* Use DataFrames when labels, mixed types, dates, or categoricals matter.
* Use structures when named outputs make code easier to understand.
* Use procedures for reusable logic.
* Use scripts for simple demonstrations or one-off workflows.

Common failure modes:

* Assuming vectorization is always better.
* Using a DataFrame when a matrix is more appropriate for numerical computation.
* Using a matrix when labels and mixed types matter.
* Wrapping simple beginner examples in overly complex abstractions.

### 1.3 Source Files and Program Organization

GAUSS code may appear in scripts, procedure files, examples, packages, documentation examples, or interactive sessions.

Important concepts:

* A script is useful for one-off analysis, demonstrations, and tutorials.
* A procedure file is useful for reusable logic.
* A package organizes reusable functionality, documentation, examples, and tests.
* An example file should be runnable and focused.
* Public-facing code should be clearer and more documented than private exploratory code.

Agent guidance:

* Match the code format to the task.
* For quick examples, a script may be enough.
* For reusable code, write a procedure.
* For package functionality, consider public API design, tests, examples, and documentation.
* Keep examples self-contained when possible.

Common failure modes:

* Writing package-style code for a simple beginner question.
* Writing an unstructured script for code that should be reusable.
* Omitting setup steps required for an example to run.
* Mixing demonstration logic and reusable procedure logic without clear separation.

### 1.4 Variables and Naming

Variable names should make code easier to understand.

Important concepts:

* Names should reflect the role of the object.
* Names should avoid GAUSS reserved keywords.
* Names should avoid ambiguity.
* Names should be consistent across related examples and procedures.
* Short names are acceptable when conventional, such as `x`, `y`, `n`, `k`, or `i`.

Agent guidance:

* Use descriptive names for public procedures and important variables.
* Avoid `start` and `end` as variable names.
* Avoid overly generic names such as `data`, `result`, or `temp` when a more specific name is available.
* Use names that indicate structure when helpful, such as `x_mat`, `df`, `ctl`, or `results`.
* Do not import naming conventions from other languages if they reduce GAUSS clarity.

Common failure modes:

* Using reserved words as identifiers.
* Using unclear variable names.
* Using names that imply the wrong data structure.
* Changing variable names inconsistently across code and explanation.

### 1.5 Expressions and Assignment

Expressions are the building blocks of GAUSS code.

Important concepts:

* Assignment should make transformations clear.
* Matrix operations and element-by-element operations must be distinguished.
* Intermediate variables can improve readability.
* Complex expressions should be broken into steps when teaching or debugging.
* Expression behavior depends on data type and dimensions.

Agent guidance:

* Be explicit about matrix dimensions when writing matrix expressions.
* Use intermediate variables when they clarify the logic.
* Avoid overly dense one-line expressions in beginner-facing code.
* Check whether the intended operation is matrix algebra or element-wise computation.
* Do not assume that syntax from another language is valid GAUSS syntax.

Common failure modes:

* Confusing matrix multiplication with element-by-element multiplication.
* Ignoring row and column orientation.
* Writing compact expressions that are difficult to debug.
* Translating formulas from R, Python, or MATLAB without adapting syntax.

### 1.6 Operators

Operators must be used according to GAUSS syntax and semantics.

Important concepts:

* Operators may behave differently depending on whether objects are scalars, vectors, matrices, strings, or other data structures.
* Matrix algebra requires dimension compatibility.
* Logical expressions should be written clearly.
* Comparisons involving missing values require care.

Agent guidance:

* Verify matrix dimensions before writing matrix operations.
* Use clear logical expressions.
* Avoid unnecessary cleverness in conditional logic.
* Explain operator choices when they may not be obvious to the user.
* When translating from another language, check whether the operator has the same meaning in GAUSS.

Common failure modes:

* Assuming operators behave exactly like Python, R, or MATLAB.
* Writing dimensionally invalid matrix expressions.
* Using logical expressions that are hard to read.
* Ignoring missing values in comparisons.

### 1.7 Control Flow

Control flow determines how code branches or repeats.

Important concepts:

* Conditional logic should be simple and readable.
* Loops are appropriate when logic is sequential, stateful, or clearer than a vectorized alternative.
* Vectorization is useful, but not mandatory for every task.
* Beginner examples may benefit from explicit loops.
* Performance-sensitive code may require careful comparison between loops and vectorized alternatives.

Agent guidance:

* Use control flow when it improves clarity or is required by the algorithm.
* Prefer simple conditional logic.
* Avoid unnecessary nesting.
* Use loops when each step depends on the previous step.
* Do not claim loops are always bad.
* Do not force vectorization when it makes the code obscure.

Common failure modes:

* Replacing clear loops with confusing vectorized code.
* Using loops when a simple matrix operation would be clearer.
* Creating deeply nested control flow.
* Translating Python or MATLAB loop syntax directly into GAUSS.

### 1.8 Procedures

Procedures are the primary way to package reusable GAUSS logic.

Important concepts:

* GAUSS procedures should use valid `proc ... endp` structure.
* Procedures should have clear inputs and outputs.
* Local variables should be declared inside procedures.
* Procedures should avoid unnecessary dependence on global state.
* Reusable procedures should validate important assumptions.

Agent guidance:

* Use a procedure when the user needs reusable logic.
* Include expected input shapes and output descriptions when helpful.
* Keep procedures focused on one main responsibility.
* Return useful values instead of only printing output.
* Consider structures for multi-component outputs.
* Include a small usage example when writing a reusable procedure.

Common failure modes:

* Writing Python-style `def` functions.
* Forgetting `proc` and `endp`.
* Failing to declare local variables.
* Returning too many separate outputs.
* Printing results but not returning reusable values.
* Relying on hidden global variables.

### 1.9 Scope and Local Variables

Scope determines where variables are visible and how safely code can be reused.

Important concepts:

* Reusable procedures should avoid unintended dependence on external variables.
* Local variables make procedure behavior easier to reason about.
* Global state can make code harder to test and debug.
* Examples may use top-level variables, but reusable procedures should be more disciplined.

Agent guidance:

* Declare local variables inside procedures.
* Keep procedure inputs explicit.
* Avoid relying on variables that are not passed into the procedure.
* Use global state only when there is a clear reason.
* When debugging, check whether a variable is defined in the expected scope.

Common failure modes:

* Using variables inside a procedure that were not passed in or declared.
* Depending on workspace state from earlier examples.
* Accidentally overwriting variables.
* Making examples that only work because of hidden prior state.

### 1.10 Includes, Libraries, and Packages

GAUSS code may depend on built-in functionality, local source files, libraries, or packages.

Important concepts:

* Base GAUSS functionality should be distinguished from package-specific functionality.
* Package dependencies should be stated clearly.
* Example code should include required setup steps.
* Version compatibility matters when using newer features or package-specific procedures.
* Source files, libraries, and packages serve different roles in larger projects.

Agent guidance:

* State dependencies when using package-specific functions.
* Prefer base GAUSS when possible for simple examples.
* Use package-specific functionality when the package is part of the user's task.
* Do not invent package names or assume packages are installed.
* Retrieve official or approved sources when package behavior matters.

Common failure modes:

* Calling package procedures without setup instructions.
* Confusing base GAUSS functions with package functions.
* Inventing packages or libraries.
* Ignoring version compatibility.
* Assuming examples will run without required files or dependencies.

### 1.11 Compilation and Execution Context

GAUSS code may be written for interactive use, script execution, reusable procedure files, package development, or documentation examples.

Important concepts:

* Code that works interactively may need additional structure to be reusable.
* Documentation examples should be self-contained when possible.
* Package code should be written with maintainability and testing in mind.
* Execution context affects setup, file paths, dependencies, and expected outputs.

Agent guidance:

* Ask or infer whether the user needs a quick example, a reusable procedure, or package-quality code.
* Include setup steps when needed.
* Avoid relying on hidden interactive state.
* Make examples runnable from a clean session when possible.
* Separate exploratory code from reusable code.

Common failure modes:

* Writing code that only works after unstated prior commands.
* Omitting required data loading or package loading.
* Assuming the current working directory.
* Mixing exploratory and reusable code in confusing ways.

### 1.12 Comments and Explanation

Comments should clarify intent, assumptions, and non-obvious logic.

Important concepts:

* Comments are most useful when they explain why something is done.
* Beginner examples may need more comments.
* Production code should avoid noisy comments that restate obvious syntax.
* Explanations should match the user's experience level.

Agent guidance:

* Use comments to mark major steps.
* Comment assumptions about dimensions, missing values, or data structure.
* Keep comments concise.
* For teaching, explain key lines after the code.
* For advanced users, focus explanations on tradeoffs and edge cases.

Common failure modes:

* Over-commenting obvious syntax.
* Under-explaining important assumptions.
* Writing comments that do not match the code.
* Giving a dense block of code with no explanation for a beginner.

### 1.13 Language Fundamentals Checklist

Before generating GAUSS code, the agent should check:

* Is this valid GAUSS syntax?
* Is the code written for the right context: script, procedure, package, or example?
* Are variable names clear and safe?
* Are reserved keywords avoided?
* Are data structures appropriate?
* Are matrix dimensions considered?
* Are procedures written with valid `proc ... endp` structure?
* Are local variables handled properly?
* Are dependencies stated?
* Are setup steps included?
* Does the code rely on hidden interactive state?
* Is the explanation appropriate for the user's experience level?


## Domain 2 — Data Model

The GAUSS Data Model is central to writing correct and idiomatic GAUSS code. GAUSS is matrix-oriented, but modern GAUSS code may also use strings, arrays, structures, DataFrames, categorical variables, and dates. A GAUSS-focused agent must understand when each data structure is appropriate and how they interact.

### 2.1 Core Mental Model

GAUSS should be understood first as a matrix-oriented language.

Matrices are the default structure for numerical work. Many statistical, econometric, optimization, and linear algebra routines expect matrix inputs and return matrix outputs.

However, not all data should be treated as a matrix. Modern GAUSS workflows often use DataFrames for labeled, mixed-type, or imported data, structures for organized outputs and configuration, arrays for higher-dimensional data, and strings or categoricals for non-numeric information.

A GAUSS agent should not automatically force every problem into a matrix. It should choose the data structure based on the task.

### 2.2 Scalars, Vectors, and Matrices

Scalars, vectors, and matrices form the core numerical data model in GAUSS.

A scalar is a single value. A vector is a one-dimensional collection of values, usually represented as either a column vector or row vector. A matrix is a two-dimensional rectangular collection of values.

Important agent guidance:

- Use matrices for numerical computation.
- Pay close attention to row and column orientation.
- Check dimensions before matrix multiplication or concatenation.
- Avoid assuming that a vector’s orientation is unimportant.
- Prefer built-in matrix operations when they make the code clearer.
- Do not use Python, R, or MATLAB syntax unless it is valid GAUSS syntax.

Common failure modes:

- Confusing element-by-element operations with matrix operations.
- Ignoring dimension compatibility.
- Treating a row vector and column vector as interchangeable.
- Writing code that assumes a one-dimensional array model like Python or R.

### 2.3 Strings

Strings are used for text, variable names, labels, file paths, and user-facing messages.

Important agent guidance:

- Use `strlen` for string length.
- Use `strindx` for string search.
- Remember that `strindx` returns `0` when the substring is not found.
- Do not invent string functions based on Python, R, or MATLAB.
- Be careful when generating file paths or parsing text.

Common failure modes:

- Using `length` for string length.
- Inventing `substr`, `strpos`, or Python-style string methods.
- Forgetting that string search failures return `0`.
- Treating strings like arrays of characters in languages where that is common.

### 2.4 Arrays

Arrays are used for higher-dimensional data.

Important agent guidance:

- Do not assume `rows` and `cols` work on arrays.
- Use array-appropriate dimension tools.
- Be explicit about array shape and ordering.
- Avoid treating arrays as if they were ordinary matrices.

Common failure modes:

- Using matrix dimension functions on arrays.
- Assuming array indexing works like Python NumPy.
- Flattening arrays unnecessarily.
- Choosing an array when a structure or matrix would be clearer.

### 2.5 Structures

Structures are used to group related values under named fields.

They are especially useful for model results, configuration objects, procedure outputs, and organized return values.

Important agent guidance:

- Use structures when outputs need named components.
- Prefer structures over long lists of loosely related return values.
- Use structures to make APIs easier to understand.
- Be consistent with field names across related procedures.

Common failure modes:

- Returning too many separate outputs instead of a structured result.
- Using a structure when a simple matrix would be clearer.
- Inconsistent field naming across procedures.
- Treating GAUSS structures like Python dictionaries without checking syntax.

### 2.6 DataFrames

DataFrames are used for labeled, column-oriented data and are especially useful for imported datasets, mixed data types, categorical variables, and workflows where variable names matter.

Important agent guidance:

- Use DataFrames when working with imported data, named variables, or mixed data types.
- Use matrices when the task is primarily numerical computation.
- Convert or extract data intentionally when moving between DataFrame workflows and matrix-based procedures.
- Preserve variable names and metadata when useful to the user.
- Be careful with categorical and date columns.

Common failure modes:

- Treating a DataFrame exactly like a matrix.
- Losing variable names unnecessarily.
- Ignoring categorical variable behavior.
- Generating matrix-only code for a DataFrame task.
- Generating DataFrame code when a simple matrix is more appropriate.

### 2.7 Categorical Variables

Categorical variables represent discrete groups or labels.

Important agent guidance:

- Treat categorical variables differently from plain numeric variables.
- Be careful when converting categories to numeric codes.
- Preserve labels when they are meaningful.
- Use appropriate categorical tools rather than assuming manual string or numeric handling.

Common failure modes:

- Treating categories as ordinary strings without considering categorical behavior.
- Treating category codes as meaningful numeric values.
- Losing labels during conversion.
- Creating dummy variables without checking the intended modeling workflow.

### 2.8 Dates and Times

Dates and times often appear in time series, panel data, imported datasets, and reporting workflows.

Important agent guidance:

- Verify the date representation before performing date operations.
- Preserve date information when importing or transforming datasets.
- Be careful when sorting, merging, lagging, or differencing time-indexed data.
- For panel data, distinguish between group identifiers and time identifiers.

Common failure modes:

- Treating dates as plain strings.
- Sorting date strings incorrectly.
- Losing time index information in transformations.
- Confusing cross-sectional IDs with time variables.

### 2.9 Missing Values

Missing values are central to real-world statistical and econometric work.

Important agent guidance:

- Check how missing values affect numerical operations.
- Do not silently ignore missing values unless appropriate.
- Be explicit about whether rows with missing values should be dropped, imputed, flagged, or preserved.
- Explain missing-value handling decisions to the user.

Common failure modes:

- Failing to account for missing values before estimation.
- Accidentally propagating missing values through calculations.
- Dropping observations without telling the user.
- Treating missing values as zeros.

### 2.10 Data Structure Decision Rules

Use these rules when choosing a GAUSS data structure:

| Task | Prefer |
|---|---|
| Numerical linear algebra | Matrix |
| Regression inputs after cleaning | Matrix |
| Imported dataset with variable names | DataFrame |
| Mixed-type tabular data | DataFrame |
| Model results with named components | Structure |
| Configuration options | Structure |
| Higher-dimensional numerical data | Array |
| Text labels or file paths | String |
| Group labels | Categorical variable |
| Time-indexed data | DataFrame or matrix with explicit date handling |

### 2.11 Agent Checklist

Before generating GAUSS code involving data, the agent should ask:

- What data structure is the user starting with?
- Are variable names important?
- Are there mixed data types?
- Are there categorical variables?
- Are there dates or panel/time identifiers?
- Is the goal data cleaning, numerical computation, modeling, or reporting?
- Should the output preserve labels or metadata?
- Are dimensions compatible?
- Are missing values present?

## Domain 3 — Procedures and APIs

Procedures and APIs define how reusable GAUSS logic is packaged, called, documented, tested, and maintained.

This domain helps GAUSS-focused agents move beyond one-off scripts and generate reusable code that is clear, stable, testable, and appropriate for the user's level and goal.

### 3.1 Core Mental Model

A GAUSS procedure should package one clear unit of reusable logic.

A good procedure has:

* A clear purpose
* Explicit inputs
* Predictable outputs
* Local variables
* Minimal hidden state
* Appropriate input validation
* Useful error messages
* A small example showing how to call it

A GAUSS-focused agent should not write every answer as a procedure. It should choose a procedure when the user needs reusable logic, package code, tests, or a clean API.

Agent guidance:

* Use scripts for simple demonstrations or one-off workflows.
* Use procedures for reusable logic.
* Use packages when functionality needs organization, documentation, tests, examples, and distribution.
* Keep procedures focused on one main responsibility.
* Prefer clarity over cleverness.
* Document expected input shapes and output behavior.

Common failure modes:

* Writing a procedure when a simple script would be clearer.
* Writing a script when reusable logic is needed.
* Creating a procedure with too many responsibilities.
* Relying on hidden global state.
* Returning results that are hard to reuse.

### 3.2 Procedure Structure

GAUSS procedures should use valid GAUSS procedure syntax.

Core expectations:

* Use `proc ... endp` for reusable procedures.
* Declare local variables inside the procedure.
* Return outputs explicitly.
* Keep setup code outside the procedure unless it is part of the procedure's responsibility.
* Keep examples separate from procedure definitions when possible.

Agent guidance:

* Do not write Python-style `def` functions.
* Do not write R-style function definitions.
* Do not write MATLAB-style function files unless the syntax is valid GAUSS.
* Use GAUSS procedure syntax consistently.
* Include a usage example after the procedure when helpful.

Common failure modes:

* Forgetting `proc` or `endp`.
* Using invalid return syntax.
* Mixing example code inside reusable procedure definitions.
* Failing to declare local variables.
* Writing pseudocode instead of executable GAUSS.

### 3.3 Inputs

Procedure inputs should be explicit, understandable, and appropriate for the task.

Important considerations:

* Required inputs should be clearly named.
* Input order should be intuitive.
* Inputs should match expected GAUSS data structures.
* Matrix dimensions should be documented when important.
* Optional inputs should have clear defaults.
* Package-specific objects or structures should be identified.

Agent guidance:

* Name inputs based on their role, not just their type.
* For econometric procedures, common names like `y`, `x`, `p`, `lags`, or `ctl` may be appropriate.
* For DataFrame workflows, distinguish between the dataset and variable names.
* For reusable procedures, state expected input dimensions.
* Avoid requiring unnecessary inputs.
* Do not hide important inputs in global variables.

Common failure modes:

* Using vague input names.
* Assuming the input is a matrix when the user has a DataFrame.
* Ignoring row and column orientation.
* Failing to document required dimensions.
* Designing inputs that are difficult to remember or call correctly.

### 3.4 Outputs

Procedure outputs should be predictable and useful.

Important considerations:

* Return values should be reusable by downstream code.
* Printed output should not be the only output for reusable procedures.
* Multi-component outputs should be organized clearly.
* Output names and structure should be stable for public APIs.
* Outputs should preserve useful labels or metadata when appropriate.

Agent guidance:

* Return a matrix, scalar, string, structure, array, or DataFrame based on the task.
* Use structures for model results, diagnostics, configuration, or related outputs.
* Use clear field names in structures.
* If printing results, also consider returning the underlying values.
* Document what is returned.

Common failure modes:

* Printing results without returning them.
* Returning too many separate outputs.
* Returning an unlabeled matrix that is hard to interpret.
* Changing output shape unexpectedly.
* Losing useful metadata unnecessarily.

### 3.5 Local Variables and Scope

Procedures should be self-contained and avoid accidental dependence on outside state.

Important considerations:

* Local variables make procedure behavior easier to reason about.
* Inputs should be passed explicitly.
* Global state should be avoided unless there is a clear design reason.
* Temporary variables should not leak outside the procedure.
* Examples should not depend on hidden workspace state.

Agent guidance:

* Declare local variables inside procedures.
* Avoid using variables inside a procedure unless they are inputs or local variables.
* Keep procedure examples runnable from a clean session when possible.
* When debugging, check whether variables are defined in the expected scope.

Common failure modes:

* Failing to declare local variables.
* Using variables from the surrounding script without passing them in.
* Overwriting important variables.
* Writing examples that only work because of earlier hidden commands.

### 3.6 Optional Arguments and Defaults

Optional arguments make procedures flexible, but they should not make APIs confusing.

Important considerations:

* Defaults should be sensible and documented.
* Optional arguments should not change core behavior unexpectedly.
* Optional arguments should be validated.
* Too many optional arguments can make a procedure hard to use.
* Control structures can be useful when many settings are needed.

Agent guidance:

* Use optional arguments when they reduce burden on the user.
* Prefer simple defaults for beginner-facing examples.
* For many options, consider a control structure rather than a long argument list.
* Document defaults clearly.
* Avoid optional arguments that create ambiguous behavior.

Common failure modes:

* Adding too many optional arguments.
* Failing to document defaults.
* Using optional arguments to hide important assumptions.
* Changing behavior in surprising ways.
* Making examples hard to read because the call signature is too complex.

### 3.7 Keyword Arguments and Control Structures

Keyword arguments and control structures can improve readability when a procedure has multiple options.

Important considerations:

* Keyword arguments can make calls more self-documenting.
* Control structures are useful for grouped configuration.
* Defaults should be clear.
* Public APIs should be consistent across related procedures.
* Advanced configuration should not overwhelm basic users.

Agent guidance:

* Use keyword arguments when they improve call clarity.
* Use control structures when several related settings need to travel together.
* For beginner examples, keep configuration minimal.
* For package APIs, prefer consistent option names across procedures.
* Explain configuration choices briefly.

Common failure modes:

* Using long positional argument lists that are easy to misuse.
* Creating inconsistent option names across related procedures.
* Requiring a complex control structure for a simple task.
* Failing to show a minimal working example.

### 3.8 Input Validation

Reusable procedures should validate important assumptions before computation.

Validation may include:

* Required inputs are present.
* Matrix dimensions are compatible.
* Vectors have expected orientation.
* Inputs contain enough observations.
* Missing values are handled intentionally.
* Options are in an allowed range.
* DataFrames contain required variables.
* Package-specific structures contain required fields.

Agent guidance:

* Include validation when writing production or reusable code.
* Keep validation lighter in short teaching examples unless relevant.
* Provide clear error messages.
* Check dimensions before matrix multiplication, concatenation, or estimation.
* Do not silently drop or coerce data unless the behavior is stated.

Common failure modes:

* Letting dimension errors happen deep inside computation.
* Ignoring missing values.
* Assuming required DataFrame variables exist.
* Accepting invalid options without warning.
* Adding so much validation that a beginner example becomes hard to follow.

### 3.9 Error Handling

Error handling should help users understand and fix problems.

Good error handling should:

* Explain what went wrong.
* Explain what was expected.
* Mention relevant dimensions, variable names, or option values when helpful.
* Fail early when assumptions are violated.
* Avoid hiding real errors.

Agent guidance:

* For reusable procedures, prefer clear and specific error messages.
* For debugging answers, identify the likely source and suggest a concrete fix.
* When the exact cause is uncertain, provide a short checklist.
* Do not replace all errors with vague messages.

Common failure modes:

* Using generic messages like "invalid input."
* Failing late after several derived calculations.
* Masking the original problem.
* Treating all errors as syntax errors.

### 3.10 Public APIs

A public API is code that users are expected to call directly.

Public APIs should be:

* Stable
* Clearly named
* Documented
* Tested
* Consistent
* Backward-compatible when practical
* Designed around user needs rather than implementation details

Agent guidance:

* Treat public procedures more carefully than internal helpers.
* Use clear names and predictable outputs.
* Document required inputs, optional inputs, outputs, assumptions, and examples.
* Avoid exposing unnecessary implementation details.
* Consider how the API will evolve over time.

Common failure modes:

* Exposing too many small helper procedures.
* Changing public procedure signatures without a clear reason.
* Designing the API around internal implementation rather than user workflow.
* Providing no examples for public-facing functionality.

### 3.11 Internal Helper Procedures

Helper procedures support implementation but are not the main user-facing interface.

Good helper procedures should be:

* Focused
* Narrow
* Easy to test
* Named consistently
* Hidden or clearly marked as internal when appropriate
* Allowed to change more freely than public APIs

Agent guidance:

* Use helper procedures to reduce duplication or isolate complex logic.
* Do not expose helpers as public APIs unless users need them.
* Keep helper inputs close to the implementation need.
* Avoid over-documenting internal helpers as if they were public functions.
* Still keep helper code readable and testable.

Common failure modes:

* Making every helper public.
* Using helpers to hide unclear design.
* Creating too many tiny helpers that make code harder to follow.
* Leaving helper behavior untested.

### 3.12 Structures as API Outputs

Structures are often the best return type when a procedure produces multiple related results.

Use structures for:

* Model estimates
* Standard errors
* Diagnostics
* Settings
* Intermediate objects needed later
* Tables or named outputs
* Results that users will inspect repeatedly

Agent guidance:

* Use clear and stable field names.
* Keep related outputs grouped.
* Document structure fields.
* Use structures to make downstream code easier to read.
* Avoid returning a long sequence of loosely related outputs.

Common failure modes:

* Returning many separate objects instead of a structure.
* Using inconsistent field names across related procedures.
* Creating structures with unclear or undocumented fields.
* Using a structure when a single matrix or scalar would be simpler.

### 3.13 API Documentation Expectations

Reusable procedures should be documented according to their audience and use.

Documentation should usually include:

* Purpose
* Syntax or call pattern
* Required inputs
* Optional inputs and defaults
* Outputs
* Assumptions
* Package dependencies
* Example usage
* Notes about edge cases when relevant

Agent guidance:

* For public procedures, include formal documentation.
* For examples, include a minimal working call.
* For advanced APIs, document limitations and edge cases.
* Keep documentation aligned with actual behavior.
* Avoid documentation that only restates the procedure name.

Common failure modes:

* Missing input dimensions.
* Missing return descriptions.
* Missing examples.
* Outdated documentation after API changes.
* Failing to document package dependencies.

### 3.14 API Testing Expectations

Reusable APIs should have tests that protect expected behavior.

Useful tests include:

* Basic successful call
* Known-result example
* Dimension mismatch handling
* Missing value behavior
* Optional argument behavior
* Invalid option behavior
* Structure field presence
* Backward compatibility checks when relevant

Agent guidance:

* Suggest tests when generating reusable procedures.
* Use small data with known expected outputs when possible.
* Test both returned values and error behavior.
* For numerical procedures, use tolerance-based comparisons when appropriate.
* Keep examples and tests separate when possible.

Common failure modes:

* Only testing that the code runs.
* Ignoring error paths.
* Testing printed output instead of returned values.
* Failing to test optional arguments.
* Omitting regression tests for bug fixes.

### 3.15 Procedure and API Checklist

Before generating or reviewing a GAUSS procedure, the agent should check:

* Does this task need a procedure, or would a script be clearer?
* Does the procedure have one clear responsibility?
* Are inputs explicit and clearly named?
* Are expected input dimensions documented?
* Are local variables declared?
* Does the procedure avoid hidden global state?
* Are optional arguments and defaults clear?
* Is input validation appropriate for the use case?
* Are errors clear and actionable?
* Are outputs reusable?
* Should the output be a structure?
* Is the API public or internal?
* Are examples included?
* Are tests suggested or provided when appropriate?
* Are package dependencies stated?


## Domain 4 — Standard Library Awareness

Standard Library Awareness is the ability to recognize the major categories of built-in GAUSS functionality, choose appropriate built-in tools when available, and retrieve official documentation when exact syntax, arguments, return values, or version behavior matter.

This domain does not attempt to reproduce the GAUSS function reference. Instead, it defines how a GAUSS-focused agent should reason about built-in functionality.

### 4.1 Core Mental Model

A GAUSS-focused agent should prefer verified GAUSS functionality over invented code.

GAUSS includes extensive built-in functionality for matrix operations, statistics, optimization, strings, file I/O, graphics, random numbers, data management, and related numerical workflows. However, an agent should not guess function names or syntax from memory when precision matters.

Agent guidance:

* Prefer built-in GAUSS functionality when it is available and appropriate.
* Retrieve official documentation when function syntax, arguments, return values, or version-specific behavior matters.
* Distinguish base GAUSS functionality from package-specific functionality.
* Avoid inventing convenience functions.
* Prefer simple verified code over elegant unverified code.
* When uncertain, state the uncertainty and retrieve or recommend checking the authoritative source.

Common failure modes:

* Inventing a function because the name sounds plausible.
* Using Python, R, or MATLAB function names.
* Treating package-specific functions as built-in functions.
* Using the right function name with incorrect arguments.
* Ignoring version-specific behavior.

### 4.2 Linear Algebra

Linear algebra is a core strength of GAUSS.

Relevant task types include:

* Matrix multiplication
* Matrix decomposition
* Solving systems of equations
* Inversion or alternatives to inversion
* Eigenvalues and eigenvectors
* Rank and conditioning
* Least squares calculations
* Simulation and numerical algorithms

Agent guidance:

* Use built-in linear algebra routines when available.
* Check matrix dimensions before recommending operations.
* Avoid unnecessary matrix inversion when a more stable approach is appropriate.
* Explain row and column orientation when it matters.
* For numerical stability questions, consider conditioning and rank.

Common failure modes:

* Writing dimensionally invalid matrix expressions.
* Using matrix inversion unnecessarily.
* Translating linear algebra code mechanically from another language.
* Ignoring singular or ill-conditioned matrices.
* Confusing element-by-element operations with matrix operations.

### 4.3 Statistics

GAUSS includes functionality for statistical analysis, probability distributions, descriptive statistics, estimation, and related workflows.

Relevant task types include:

* Descriptive statistics
* Probability distributions
* Hypothesis testing
* Regression and model estimation
* Covariance and correlation
* Simulation
* Random sampling
* Diagnostics

Agent guidance:

* Prefer built-in statistical procedures when they match the task.
* For common statistical or econometric workflows, check for native GAUSS procedures before writing a custom matrix implementation.
* Prefer verified built-in procedures such as `olsmt` for standard OLS workflows when appropriate, verifying exact syntax against official documentation when needed.
* When recommending a native GAUSS procedure, provide a concrete example using that procedure when the syntax is known or retrievable from verified repository or official documentation.
* If exact procedure syntax is uncertain, state that retrieval or documentation verification is required before giving production-ready code.
* For common statistical translations, make the closest native GAUSS procedure the primary example when possible.
* Use manual matrix implementations for teaching, customization, diagnostics, and explaining mechanics, but do not present them as the default replacement for known built-in procedures.
* Retrieve documentation for procedure syntax and returned outputs.
* Check whether the function is part of base GAUSS or an application/package.
* Explain statistical assumptions separately from GAUSS syntax.
* Use small examples with known dimensions when teaching.

Common failure modes:

* Using statistically reasonable but invalid GAUSS code.
* Inventing modeling functions.
* Ignoring missing values before estimation.
* Using a procedure without understanding its expected input structure.
* Confusing returned results, printed output, and stored output.

### 4.4 Optimization

Optimization workflows often require careful setup, starting values, objective functions, constraints, and convergence interpretation.

Relevant task types include:

* Unconstrained optimization
* Constrained optimization
* Maximum likelihood estimation
* Nonlinear least squares
* Custom objective functions
* Starting value selection
* Convergence diagnostics

Agent guidance:

* Retrieve documentation for optimizer-specific syntax and control structures.
* Be explicit about objective function inputs and outputs.
* Distinguish optimization failure from syntax failure.
* Discuss starting values, scaling, and convergence when relevant.
* Keep simple examples small and runnable.

Common failure modes:

* Inventing optimizer call patterns.
* Omitting required control structures or setup.
* Treating convergence problems as syntax errors.
* Ignoring scaling or starting values.
* Providing an objective function that does not match the optimizer’s expected interface.

### 4.5 Time Series

Time series workflows require attention to ordering, lags, differencing, dates, and sample alignment.

Relevant task types include:

* Lagging
* Differencing
* Forecasting
* ARIMA and related models
* VAR models
* Unit root testing
* Date handling
* Sample alignment

Agent guidance:

* Verify that data are sorted correctly before lagging or differencing.
* Track sample size changes after transformations.
* Preserve or explain time indexes.
* Retrieve documentation for time series procedures and model objects.
* Distinguish time series logic from GAUSS implementation details.

Common failure modes:

* Lagging unsorted data.
* Misaligning dependent and independent variables.
* Ignoring missing values introduced by lags.
* Treating dates as plain strings.
* Using syntax from R, Python, or MATLAB time series libraries.

### 4.6 Machine Learning

Machine learning functionality may come from base GAUSS, applications, packages, or user-defined code.

Relevant task types include:

* Classification
* Regression
* Model evaluation
* Cross-validation
* Data preprocessing
* Feature engineering
* Prediction workflows
* Model comparison

Agent guidance:

* Verify whether requested functionality exists in base GAUSS, an application, or a package.
* State dependencies clearly.
* Keep data preprocessing explicit.
* Avoid importing Python scikit-learn syntax into GAUSS.
* Explain modeling workflow separately from implementation syntax.

Common failure modes:

* Inventing scikit-learn-style APIs.
* Assuming Python object-oriented method syntax.
* Omitting package dependencies.
* Ignoring train/test split or validation logic.
* Treating DataFrames and matrices interchangeably without conversion.

### 4.7 Strings

String functions are a common source of AI-generated mistakes.

Relevant task types include:

* String length
* String search
* Parsing labels
* File path construction
* Variable name handling
* Text cleanup
* User-facing messages

Known rules:

* Use `strlen` for string length.
* Use `strindx` for string search.
* Remember that `strindx` returns `0` when the substring is not found.

Agent guidance:

* Verify string function names before use.
* Do not use Python-style string methods.
* Do not invent R, MATLAB, or JavaScript string functions.
* Handle “not found” cases explicitly when using string search.
* Keep string parsing simple and testable.

Common failure modes:

* Using `length` for string length.
* Inventing `substr`, `strpos`, or similar names.
* Forgetting that `strindx` returns `0` when not found.
* Treating strings as arrays of characters without verifying the GAUSS approach.

### 4.8 File I/O

File I/O includes reading, writing, importing, exporting, and inspecting data.

Relevant task types include:

* Loading datasets
* Importing CSV or Excel files
* Saving output
* Reading text files
* Writing reports or intermediate results
* Handling paths
* Verifying imported data

Agent guidance:

* Include setup steps when examples depend on external files.
* Check the imported data before modeling.
* Be explicit about file paths and working directory assumptions.
* Consider platform-specific path differences.
* Preserve variable names and metadata when useful.
* Retrieve documentation when exact import/export syntax matters.

Common failure modes:

* Assuming the file is in the current working directory.
* Omitting required setup or import steps.
* Ignoring headers, delimiters, dates, or categorical columns.
* Proceeding directly to analysis without checking imported data.
* Confusing file I/O errors with modeling errors.

### 4.9 Graphics

Graphics functionality supports visualization, diagnostics, reporting, and teaching.

Relevant task types include:

* Scatter plots
* Line plots
* Histograms
* Diagnostic plots
* Forecast plots
* Model comparison plots
* Publication or blog figures

Agent guidance:

* Retrieve documentation for plotting syntax and options.
* Keep beginner plots simple.
* Include labels, titles, and legends when helpful.
* Separate data preparation from plotting.
* Avoid inventing plotting APIs based on Python, R, or MATLAB.
* Match plot complexity to the user’s purpose.

Common failure modes:

* Inventing plotting functions or options.
* Using ggplot-style syntax in GAUSS.
* Omitting setup needed for graph output.
* Plotting misaligned data.
* Creating visually complex plots when a simple diagnostic plot is better.

### 4.10 Dates and Times

Date and time handling appears in time series, panel data, imported datasets, reporting, and filtering.

Relevant task types include:

* Parsing dates
* Sorting by date
* Filtering date ranges
* Lagging or differencing time-indexed data
* Forecast horizons
* Time series plots
* Panel data time identifiers

Agent guidance:

* Verify date representation before operating on dates.
* Preserve date information during import and transformation.
* Sort by date before time-dependent operations.
* Distinguish date strings from date values.
* Retrieve documentation for exact date functions and formats when needed.

Common failure modes:

* Sorting date strings incorrectly.
* Treating dates as ordinary numeric values without checking representation.
* Losing date metadata during matrix conversion.
* Confusing time identifiers with group identifiers in panel data.

### 4.11 Random Numbers and Simulation

Random number generation and simulation require reproducibility, distribution choices, and careful storage of results.

Relevant task types include:

* Monte Carlo simulation
* Bootstrap workflows
* Random sampling
* Synthetic data generation
* Stochastic optimization
* Reproducible examples

Agent guidance:

* Set or discuss random seeds when reproducibility matters.
* Use appropriate distribution functions.
* Preallocate simulation results when size is known.
* Store only outputs needed for analysis.
* Use small simulations for teaching and larger simulations only when needed.
* Retrieve documentation for exact random number function syntax.

Common failure modes:

* Omitting seed control in reproducible examples.
* Generating random data with invalid function names.
* Storing excessive intermediate results.
* Failing to preallocate simulation output.
* Confusing distribution parameters.

### 4.12 Data Management

Data management includes cleaning, transforming, sorting, selecting, merging, reshaping, and preparing data for analysis.

Relevant task types include:

* Import inspection
* Variable selection
* Missing value handling
* Sorting
* Filtering
* Creating transformed variables
* Handling categorical variables
* Handling DataFrames
* Preparing model matrices

Agent guidance:

* Use DataFrames when labels, mixed types, dates, or categories matter.
* Use matrices when numerical computation is the goal.
* Make conversions between DataFrames and matrices explicit.
* Preserve metadata when useful.
* Handle missing values intentionally.
* Check dimensions after transformations.

Common failure modes:

* Treating DataFrames exactly like matrices.
* Dropping metadata unnecessarily.
* Ignoring missing values.
* Creating model inputs with mismatched rows.
* Performing time or panel transformations without sorting.

### 4.13 Utilities

Utility functions support common tasks such as dimensions, sorting, indexing, formatting, and inspection.

Agent guidance:

* Use utility functions when they make code clearer and safer.
* Verify function names before use.
* Check that dimension tools are appropriate for the data structure.
* Avoid using matrix-only utilities on arrays or DataFrames without verification.
* Prefer simple inspection steps when debugging.

Common failure modes:

* Assuming `rows` and `cols` work on arrays.
* Inventing utility functions.
* Using utilities from other languages.
* Skipping inspection steps before debugging or modeling.

### 4.14 Retrieval Rules for Standard Library Questions

The agent should retrieve official or approved sources when:

* Exact function syntax matters.
* Argument names or optional arguments matter.
* Return values or output structures matter.
* Version-specific behavior matters.
* The agent is unsure whether a function exists.
* The function may belong to a package rather than base GAUSS.
* The user asks for documentation-quality accuracy.
* A hallucinated function would likely mislead the user.

The agent may answer without retrieval when:

* The concept is stable and general.
* The user asks for high-level explanation.
* The exact function call is not needed.
* The answer is clearly framed as conceptual.

### 4.15 Standard Library Checklist

Before using or recommending a GAUSS function, the agent should check:

* Is this a real GAUSS function?
* Is it base GAUSS or package-specific?
* Is the syntax verified?
* Are required inputs and dimensions clear?
* Are returned outputs understood?
* Are version assumptions relevant?
* Is there a simpler built-in approach?
* Is a custom implementation actually necessary?
* Does the code avoid Python, R, MATLAB, or pseudocode contamination?


## Domain 5 — Numerical Computing

Numerical computing is the practice of implementing mathematical, statistical, econometric, and simulation-based algorithms in a way that is accurate, stable, reproducible, and appropriate for the data.

This domain helps GAUSS-focused agents reason about matrix algebra, numerical precision, missing values, conditioning, simulation, and the difference between mathematically correct formulas and computationally reliable code.

### 5.1 Core Mental Model

GAUSS is designed for numerical and matrix-oriented computing. Many GAUSS workflows involve translating mathematical expressions into executable matrix code.

However, a formula that is correct on paper may still produce unreliable code if the implementation ignores dimensions, missing values, conditioning, precision, or data structure.

Agent guidance:

* Treat mathematical correctness and computational reliability as related but separate concerns.
* Check dimensions before matrix operations.
* Consider numerical stability before recommending matrix inversions or optimization routines.
* Consider missing values before estimation or simulation.
* Use reproducible examples when random numbers are involved.
* Prefer clear, verified numerical code over compact but fragile expressions.

Common failure modes:

* Translating formulas directly into invalid or unstable code.
* Ignoring singularity or ill-conditioning.
* Treating missing values as zeros.
* Ignoring row and column orientation.
* Producing statistically reasonable logic with invalid GAUSS syntax.
* Optimizing for compactness instead of reliability.

### 5.2 Matrix Algebra

Matrix algebra is central to GAUSS programming.

Common tasks include:

* Matrix multiplication
* Transposition
* Solving systems of equations
* Least squares calculations
* Covariance and correlation calculations
* Decompositions
* Eigenvalue problems
* Simulation storage and transformation

Agent guidance:

* Use matrix operations when they naturally express the computation.
* Verify dimension compatibility before matrix multiplication or concatenation.
* Explain matrix dimensions in educational examples.
* Prefer built-in numerical routines when available.
* Avoid unnecessary manual implementations of standard operations.
* Keep intermediate variables when they make the matrix logic easier to understand.

Common failure modes:

* Confusing matrix multiplication with element-by-element operations.
* Ignoring row vector vs column vector orientation.
* Creating dimension mismatches after lagging, differencing, or dropping missing values.
* Translating formulas without checking object shapes.
* Using loops for simple matrix operations when a clear matrix expression is available.

### 5.3 Numerical Precision

Numerical precision matters when calculations involve floating-point arithmetic, very large or very small numbers, subtraction of nearly equal values, or repeated transformations.

Agent guidance:

* Avoid implying exact equality for floating-point results unless appropriate.
* Use tolerance-based comparisons for numerical tests when needed.
* Be cautious with calculations that involve very small denominators.
* Explain that tiny numerical differences can be normal.
* Preserve enough precision in intermediate calculations.
* Avoid unnecessary rounding before final output.

Common failure modes:

* Comparing floating-point results using exact equality.
* Rounding intermediate results too early.
* Treating small numerical differences as errors.
* Ignoring scale differences across variables.
* Failing to use tolerances in tests.

### 5.4 Numerical Stability

Numerical stability refers to whether an algorithm produces reliable results under realistic data conditions.

Stability concerns arise with:

* Matrix inversion
* Nearly singular matrices
* Collinearity
* Optimization
* Recursive calculations
* Large or poorly scaled variables
* Ill-conditioned systems
* Repeated numerical transformations

Agent guidance:

* Avoid unnecessary matrix inversion when a more stable approach is available.
* Consider rank, conditioning, and collinearity when matrix operations fail.
* Distinguish syntax errors from numerical problems.
* Suggest diagnostics before changing model structure.
* Be careful when recommending custom implementations of numerical methods.
* Prefer tested built-in routines when they fit the problem.

Common failure modes:

* Treating singular matrix errors as syntax problems.
* Recommending arbitrary transformations without diagnosing the issue.
* Using inverse-based formulas when a solve/decomposition approach would be more appropriate.
* Ignoring scaling problems in optimization.
* Treating convergence failure as a package bug.

### 5.5 Conditioning and Singularity

Conditioning describes how sensitive numerical results are to small changes in inputs. Singularity means a matrix cannot be inverted.

Common causes include:

* Perfect or near-perfect multicollinearity
* Duplicate variables
* Too few observations
* Constant columns
* Poorly scaled variables
* Redundant constraints
* Missing-value filtering that changes the sample
* Insufficient variation in the data

Agent guidance:

* When matrix inversion or estimation fails, check for rank and collinearity issues.
* Check the number of observations relative to the number of variables.
* Check whether variables are constant or duplicated.
* Consider whether missing-value handling reduced the usable sample.
* Explain singularity in practical terms for beginners.
* Avoid simply adding small constants or arbitrary fixes unless justified.

Common failure modes:

* Applying a superficial transpose or reshape to fix a singularity problem.
* Ignoring data issues that create singular matrices.
* Treating collinearity as a coding typo.
* Suggesting a more complex model when the data do not support it.

### 5.6 Missing Values in Numerical Workflows

Missing values can affect matrix operations, descriptive statistics, estimation, forecasting, and simulations.

Agent guidance:

* Check for missing values before numerical computation.
* State how missing values are handled.
* Apply row filtering consistently across related variables.
* Track sample size changes after dropping missing values.
* Be careful when lagging or differencing introduces missing values.
* Do not treat missing values as zeros unless that is explicitly intended and justified.

Common failure modes:

* Silently dropping observations.
* Dropping rows from one variable but not another.
* Treating missing values as zeros.
* Ignoring missing values introduced by lags or differences.
* Comparing model results estimated on different samples without noting it.

### 5.7 Simulation

Simulation is common in GAUSS for Monte Carlo experiments, bootstrapping, synthetic data generation, forecasting exercises, and teaching examples.

Agent guidance:

* Set or discuss random seeds when reproducibility matters.
* Preallocate simulation output when the number of repetitions is known.
* Store only the outputs needed for the analysis.
* Use small simulation sizes in teaching examples.
* Use larger simulation sizes only when the task requires it.
* Clearly separate data-generating process, estimation, and summary steps.
* Check dimensions of simulated output.

Common failure modes:

* Omitting random seed control in reproducible examples.
* Growing result matrices repeatedly inside loops.
* Storing every intermediate draw unnecessarily.
* Mixing simulation logic and reporting logic in one unclear block.
* Confusing distribution parameters.
* Drawing conclusions from too few repetitions without caveat.

### 5.8 Reproducibility

Reproducibility means that results can be regenerated by another user or in a later session.

Important elements include:

* Random seed control
* Explicit data loading
* Clear dependencies
* Stated GAUSS or package version assumptions
* Stable input data
* Documented transformations
* Known expected outputs for examples or tests

Agent guidance:

* Include random seed setup when examples depend on random numbers.
* Include data import or data generation steps.
* State package dependencies.
* Avoid hidden workspace state.
* Keep examples runnable from a clean session when possible.
* For tests, use small examples with known expected results.

Common failure modes:

* Relying on variables defined earlier but not shown.
* Omitting package setup.
* Omitting random seed control.
* Assuming a local file path.
* Changing data in undocumented ways.
* Providing examples that cannot be run independently.

### 5.9 Optimization and Convergence

Numerical optimization requires careful attention to objective functions, starting values, scaling, constraints, and convergence.

Agent guidance:

* Verify the expected optimizer interface before generating code.
* Make objective function inputs and outputs explicit.
* Discuss starting values when they matter.
* Consider scaling when variables differ greatly in magnitude.
* Distinguish convergence problems from syntax problems.
* Explain convergence diagnostics in practical terms.
* Avoid inventing optimizer control options or call signatures.

Common failure modes:

* Writing an objective function that does not match the optimizer’s expected form.
* Omitting starting values.
* Treating non-convergence as a code syntax error.
* Ignoring scaling problems.
* Inventing control structures or option names.
* Failing to check whether the optimum is meaningful.

### 5.10 Forecasting and Time-Indexed Computation

Forecasting and time-indexed numerical work require special care with ordering, lag structure, sample alignment, and horizon management.

Agent guidance:

* Verify sorting before lagging or differencing.
* Track observations lost to lags, differences, or missing values.
* Keep forecast horizons explicit.
* Preserve date or time-index information when useful.
* Align actuals, fitted values, residuals, and forecasts carefully.
* Distinguish model logic from plotting or reporting logic.

Common failure modes:

* Lagging unsorted data.
* Misaligning dependent and independent variables.
* Ignoring missing values introduced by transformations.
* Plotting forecasts against the wrong dates.
* Mixing in-sample fitted values and out-of-sample forecasts without labeling them.

### 5.11 Panel and Grouped Computation

Panel and grouped workflows require attention to group identifiers, time identifiers, sorting, balancing, and within-group transformations.

Agent guidance:

* Identify group and time variables explicitly.
* Sort data appropriately before within-group operations.
* Distinguish cross-sectional identifiers from time identifiers.
* Check whether panel data are balanced or consecutive when it matters.
* Apply lags, differences, and filters within groups rather than across group boundaries.
* Preserve identifiers when converting between DataFrames and matrices.

Common failure modes:

* Lagging across group boundaries.
* Sorting only by time instead of group and time.
* Dropping identifiers too early.
* Assuming balanced panels.
* Treating panel data as an ordinary time series.

### 5.12 Numerical Testing

Numerical tests should verify both correctness and robustness.

Useful numerical tests include:

* Known-result calculations
* Dimension checks
* Tolerance-based comparisons
* Edge cases
* Missing-value behavior
* Singular or near-singular cases
* Reproducibility checks for random workflows
* Comparison against a simple manual calculation

Agent guidance:

* Use small known examples when possible.
* Use tolerance-based comparisons for floating-point results.
* Test dimensions and returned object structure.
* Test failure cases for reusable procedures.
* Separate numerical validity from formatting or printed output.
* Do not rely only on visual inspection.

Common failure modes:

* Testing only whether code runs.
* Comparing floating-point values exactly when a tolerance is needed.
* Ignoring edge cases.
* Ignoring missing values.
* Testing printed output instead of returned values.

## Domain 5 — Numerical Computing

Numerical computing is the practice of implementing mathematical, statistical, econometric, and simulation-based algorithms in a way that is accurate, stable, reproducible, and appropriate for the data.

This domain helps GAUSS-focused agents reason about matrix algebra, numerical precision, missing values, conditioning, simulation, and the difference between mathematically correct formulas and computationally reliable code.

### 5.1 Core Mental Model

GAUSS is designed for numerical and matrix-oriented computing. Many GAUSS workflows involve translating mathematical expressions into executable matrix code.

However, a formula that is correct on paper may still produce unreliable code if the implementation ignores dimensions, missing values, conditioning, precision, or data structure.

Agent guidance:

* Treat mathematical correctness and computational reliability as related but separate concerns.
* Check dimensions before matrix operations.
* Consider numerical stability before recommending matrix inversions or optimization routines.
* Consider missing values before estimation or simulation.
* Use reproducible examples when random numbers are involved.
* Prefer clear, verified numerical code over compact but fragile expressions.

Common failure modes:

* Translating formulas directly into invalid or unstable code.
* Ignoring singularity or ill-conditioning.
* Treating missing values as zeros.
* Ignoring row and column orientation.
* Producing statistically reasonable logic with invalid GAUSS syntax.
* Optimizing for compactness instead of reliability.

### 5.2 Matrix Algebra

Matrix algebra is central to GAUSS programming.

Common tasks include:

* Matrix multiplication
* Transposition
* Solving systems of equations
* Least squares calculations
* Covariance and correlation calculations
* Decompositions
* Eigenvalue problems
* Simulation storage and transformation

Agent guidance:

* Use matrix operations when they naturally express the computation.
* Verify dimension compatibility before matrix multiplication or concatenation.
* Explain matrix dimensions in educational examples.
* Prefer built-in numerical routines when available.
* Avoid unnecessary manual implementations of standard operations.
* Keep intermediate variables when they make the matrix logic easier to understand.

Common failure modes:

* Confusing matrix multiplication with element-by-element operations.
* Ignoring row vector vs column vector orientation.
* Creating dimension mismatches after lagging, differencing, or dropping missing values.
* Translating formulas without checking object shapes.
* Using loops for simple matrix operations when a clear matrix expression is available.

### 5.3 Numerical Precision

Numerical precision matters when calculations involve floating-point arithmetic, very large or very small numbers, subtraction of nearly equal values, or repeated transformations.

Agent guidance:

* Avoid implying exact equality for floating-point results unless appropriate.
* Use tolerance-based comparisons for numerical tests when needed.
* Be cautious with calculations that involve very small denominators.
* Explain that tiny numerical differences can be normal.
* Preserve enough precision in intermediate calculations.
* Avoid unnecessary rounding before final output.

Common failure modes:

* Comparing floating-point results using exact equality.
* Rounding intermediate results too early.
* Treating small numerical differences as errors.
* Ignoring scale differences across variables.
* Failing to use tolerances in tests.

### 5.4 Numerical Stability

Numerical stability refers to whether an algorithm produces reliable results under realistic data conditions.

Stability concerns arise with:

* Matrix inversion
* Nearly singular matrices
* Collinearity
* Optimization
* Recursive calculations
* Large or poorly scaled variables
* Ill-conditioned systems
* Repeated numerical transformations

Agent guidance:

* Avoid unnecessary matrix inversion when a more stable approach is available.
* Consider rank, conditioning, and collinearity when matrix operations fail.
* Distinguish syntax errors from numerical problems.
* Suggest diagnostics before changing model structure.
* Be careful when recommending custom implementations of numerical methods.
* Prefer tested built-in routines when they fit the problem.

Common failure modes:

* Treating singular matrix errors as syntax problems.
* Recommending arbitrary transformations without diagnosing the issue.
* Using inverse-based formulas when a solve/decomposition approach would be more appropriate.
* Ignoring scaling problems in optimization.
* Treating convergence failure as a package bug.

### 5.5 Conditioning and Singularity

Conditioning describes how sensitive numerical results are to small changes in inputs. Singularity means a matrix cannot be inverted.

Common causes include:

* Perfect or near-perfect multicollinearity
* Duplicate variables
* Too few observations
* Constant columns
* Poorly scaled variables
* Redundant constraints
* Missing-value filtering that changes the sample
* Insufficient variation in the data

Agent guidance:

* When matrix inversion or estimation fails, check for rank and collinearity issues.
* Check the number of observations relative to the number of variables.
* Check whether variables are constant or duplicated.
* Consider whether missing-value handling reduced the usable sample.
* Explain singularity in practical terms for beginners.
* Avoid simply adding small constants or arbitrary fixes unless justified.

Common failure modes:

* Applying a superficial transpose or reshape to fix a singularity problem.
* Ignoring data issues that create singular matrices.
* Treating collinearity as a coding typo.
* Suggesting a more complex model when the data do not support it.

### 5.6 Missing Values in Numerical Workflows

Missing values can affect matrix operations, descriptive statistics, estimation, forecasting, and simulations.

Agent guidance:

* Check for missing values before numerical computation.
* State how missing values are handled.
* Apply row filtering consistently across related variables.
* Track sample size changes after dropping missing values.
* Be careful when lagging or differencing introduces missing values.
* Do not treat missing values as zeros unless that is explicitly intended and justified.

Common failure modes:

* Silently dropping observations.
* Dropping rows from one variable but not another.
* Treating missing values as zeros.
* Ignoring missing values introduced by lags or differences.
* Comparing model results estimated on different samples without noting it.

### 5.7 Simulation

Simulation is common in GAUSS for Monte Carlo experiments, bootstrapping, synthetic data generation, forecasting exercises, and teaching examples.

Agent guidance:

* Set or discuss random seeds when reproducibility matters.
* Preallocate simulation output when the number of repetitions is known.
* Store only the outputs needed for the analysis.
* Use small simulation sizes in teaching examples.
* Use larger simulation sizes only when the task requires it.
* Clearly separate data-generating process, estimation, and summary steps.
* Check dimensions of simulated output.

Common failure modes:

* Omitting random seed control in reproducible examples.
* Growing result matrices repeatedly inside loops.
* Storing every intermediate draw unnecessarily.
* Mixing simulation logic and reporting logic in one unclear block.
* Confusing distribution parameters.
* Drawing conclusions from too few repetitions without caveat.

### 5.8 Reproducibility

Reproducibility means that results can be regenerated by another user or in a later session.

Important elements include:

* Random seed control
* Explicit data loading
* Clear dependencies
* Stated GAUSS or package version assumptions
* Stable input data
* Documented transformations
* Known expected outputs for examples or tests

Agent guidance:

* Include random seed setup when examples depend on random numbers.
* Include data import or data generation steps.
* State package dependencies.
* Avoid hidden workspace state.
* Keep examples runnable from a clean session when possible.
* For tests, use small examples with known expected results.

Common failure modes:

* Relying on variables defined earlier but not shown.
* Omitting package setup.
* Omitting random seed control.
* Assuming a local file path.
* Changing data in undocumented ways.
* Providing examples that cannot be run independently.

### 5.9 Optimization and Convergence

Numerical optimization requires careful attention to objective functions, starting values, scaling, constraints, and convergence.

Agent guidance:

* Verify the expected optimizer interface before generating code.
* Make objective function inputs and outputs explicit.
* Discuss starting values when they matter.
* Consider scaling when variables differ greatly in magnitude.
* Distinguish convergence problems from syntax problems.
* Explain convergence diagnostics in practical terms.
* Avoid inventing optimizer control options or call signatures.

Common failure modes:

* Writing an objective function that does not match the optimizer’s expected form.
* Omitting starting values.
* Treating non-convergence as a code syntax error.
* Ignoring scaling problems.
* Inventing control structures or option names.
* Failing to check whether the optimum is meaningful.

### 5.10 Forecasting and Time-Indexed Computation

Forecasting and time-indexed numerical work require special care with ordering, lag structure, sample alignment, and horizon management.

Agent guidance:

* Verify sorting before lagging or differencing.
* Track observations lost to lags, differences, or missing values.
* Keep forecast horizons explicit.
* Preserve date or time-index information when useful.
* Align actuals, fitted values, residuals, and forecasts carefully.
* Distinguish model logic from plotting or reporting logic.

Common failure modes:

* Lagging unsorted data.
* Misaligning dependent and independent variables.
* Ignoring missing values introduced by transformations.
* Plotting forecasts against the wrong dates.
* Mixing in-sample fitted values and out-of-sample forecasts without labeling them.

### 5.11 Panel and Grouped Computation

Panel and grouped workflows require attention to group identifiers, time identifiers, sorting, balancing, and within-group transformations.

Agent guidance:

* Identify group and time variables explicitly.
* Sort data appropriately before within-group operations.
* Distinguish cross-sectional identifiers from time identifiers.
* Check whether panel data are balanced or consecutive when it matters.
* Apply lags, differences, and filters within groups rather than across group boundaries.
* Preserve identifiers when converting between DataFrames and matrices.

Common failure modes:

* Lagging across group boundaries.
* Sorting only by time instead of group and time.
* Dropping identifiers too early.
* Assuming balanced panels.
* Treating panel data as an ordinary time series.

### 5.12 Numerical Testing

Numerical tests should verify both correctness and robustness.

Useful numerical tests include:

* Known-result calculations
* Dimension checks
* Tolerance-based comparisons
* Edge cases
* Missing-value behavior
* Singular or near-singular cases
* Reproducibility checks for random workflows
* Comparison against a simple manual calculation

Agent guidance:

* Use small known examples when possible.
* Use tolerance-based comparisons for floating-point results.
* Test dimensions and returned object structure.
* Test failure cases for reusable procedures.
* Separate numerical validity from formatting or printed output.
* Do not rely only on visual inspection.

Common failure modes:

* Testing only whether code runs.
* Comparing floating-point values exactly when a tolerance is needed.
* Ignoring edge cases.
* Ignoring missing values.
* Testing printed output instead of returned values.

### 5.13 Numerical Computing Checklist

Before generating or reviewing numerical GAUSS code, the agent should check:

* Are the data structures appropriate?
* Are matrix dimensions compatible?
* Are row and column orientations correct?
* Are missing values handled intentionally?
* Are numerical routines verified GAUSS functions?
* Is matrix inversion necessary, or is a more stable approach available?
* Are conditioning or singularity issues possible?
* Are random numbers reproducible when needed?
* Are simulations preallocated when appropriate?
* Are time series or panel operations properly sorted and aligned?
* Are results tested against a small known case?
* Are numerical comparisons tolerance-based when appropriate?
* Is the code clear enough to debug and maintain?


## Domain 6 — Software Engineering

Software engineering is the practice of organizing GAUSS code so it is maintainable, testable, documented, reusable, and safe to evolve over time.

This domain helps GAUSS-focused agents move beyond writing code that merely runs. It teaches agents to reason about project structure, public APIs, package architecture, documentation, tests, release processes, and long-term maintainability.

### 6.1 Core Mental Model

GAUSS code exists in different contexts:

* One-off analysis scripts
* Teaching examples
* Blog examples
* Reusable procedures
* Package source code
* Public APIs
* Tests
* Documentation examples
* Production workflows

Each context has different expectations.

A short tutorial script can prioritize clarity and simplicity. A package procedure should prioritize API stability, input validation, documentation, tests, and backward compatibility.

Agent guidance:

* Match engineering rigor to the context.
* Do not over-engineer simple examples.
* Do not under-engineer package-quality code.
* Separate exploratory analysis from reusable logic.
* Treat public APIs more carefully than private helpers.
* Consider tests and documentation when creating reusable code.

Common failure modes:

* Treating package code like a one-off script.
* Turning every small example into an overbuilt framework.
* Ignoring tests and documentation for reusable code.
* Mixing exploratory code, public APIs, and examples in one unclear file.

### 6.2 Project Organization

A well-organized GAUSS project should make it easy to find source code, examples, tests, documentation, and supporting data.

Preferred practices:

* Keep reusable source code separate from examples.
* Keep tests separate from examples.
* Keep documentation close enough to source code to stay current.
* Use predictable folder names.
* Include a clear README when the project is intended for others.
* Avoid hidden dependencies on a local working directory.

Agent guidance:

* For simple user examples, keep the project structure minimal.
* For reusable tools, suggest a clear project layout.
* For packages, distinguish source, examples, tests, and docs.
* Avoid recommending unnecessary structure for a small task.
* When file paths matter, make assumptions explicit.

Common failure modes:

* Placing all code in one large script.
* Mixing test data with production data without explanation.
* Assuming files exist in the current working directory.
* Creating a complex directory structure before the project needs it.

### 6.3 Package Architecture

Package architecture should support reuse, documentation, testing, versioning, and distribution.

A package should usually distinguish:

* Public procedures
* Internal helper procedures
* Examples
* Tests
* Documentation
* Package metadata
* Dependencies
* Release notes or changelog

Agent guidance:

* Recommend package structure when functionality will be reused or shared.
* Keep public APIs stable and documented.
* Keep internal helpers focused and implementation-oriented.
* Include examples that demonstrate realistic usage.
* Include tests for important behavior.
* Document package dependencies and version assumptions.

Common failure modes:

* Exposing too many helper procedures as public APIs.
* Creating public procedures without examples.
* Adding features without tests.
* Ignoring package metadata or dependency requirements.
* Treating package organization as an afterthought.

### 6.4 Public APIs

Public APIs are the procedures users are expected to call directly.

Public APIs should be:

* Clearly named
* Stable
* Documented
* Tested
* Predictable
* Consistent with related APIs
* Designed around user workflows

Agent guidance:

* Design APIs from the user's perspective.
* Keep call signatures understandable.
* Avoid long positional argument lists when options are better grouped.
* Use structures or control objects for complex configuration.
* Preserve backward compatibility when practical.
* Include examples for public-facing procedures.

Common failure modes:

* Designing APIs around internal implementation details.
* Requiring users to remember too many positional arguments.
* Changing public signatures unnecessarily.
* Returning outputs that are difficult to interpret.
* Failing to document assumptions and defaults.

### 6.5 Internal APIs and Helper Procedures

Internal helper procedures support implementation but are not the main user-facing interface.

Good helper procedures should be:

* Focused
* Narrow
* Easy to test
* Easy to replace
* Named consistently
* Clearly internal when appropriate

Agent guidance:

* Use helper procedures to reduce duplication.
* Avoid exposing helpers unnecessarily.
* Keep helper interfaces close to their implementation purpose.
* Do not document helpers as if they are public APIs unless users need them.
* Keep helpers testable when they contain important logic.

Common failure modes:

* Making every helper public.
* Creating many tiny helpers that obscure the main flow.
* Hiding important behavior in undocumented helpers.
* Letting helper procedures become inconsistent across a package.

### 6.6 Testing Strategy

Testing protects correctness and helps future developers change code safely.

Useful test categories include:

* Basic successful calls
* Known-result examples
* Edge cases
* Dimension mismatch behavior
* Missing value behavior
* Optional argument behavior
* Invalid input behavior
* Structure field checks
* Package loading checks
* Regression tests for fixed bugs

Agent guidance:

* Suggest tests when writing reusable or package code.
* Use small inputs with known expected results when possible.
* Test returned values, not just printed output.
* Test error paths for reusable APIs.
* For numerical code, use tolerance-based comparisons when appropriate.
* Keep tests focused and easy to run.

Common failure modes:

* Only testing that code runs.
* Testing examples but not edge cases.
* Ignoring missing values and dimension errors.
* Failing to test optional arguments.
* Treating visual inspection as the only validation.

### 6.7 Examples

Examples show users how to apply functionality.

Good examples should be:

* Runnable
* Focused
* Realistic enough to be useful
* Small enough to understand
* Clear about setup
* Clear about expected output
* Matched to the audience

Agent guidance:

* For beginners, keep examples simple and explicit.
* For advanced users, include realistic workflows and edge cases when useful.
* Avoid examples that depend on hidden state.
* Include data loading or setup steps when needed.
* Explain why each step matters when teaching.
* Keep examples separate from tests when possible.

Common failure modes:

* Providing examples that cannot run as written.
* Omitting package or data setup.
* Using overly complex examples for simple concepts.
* Using toy examples that fail to demonstrate the real workflow.
* Mixing example code directly into reusable procedure files.

### 6.8 Documentation

Documentation should explain purpose, usage, inputs, outputs, assumptions, and examples.

Documentation may include:

* README files
* API reference documentation
* Sphinx `.rst` files
* Inline comments
* Example walkthroughs
* Blog-style tutorials
* Changelogs
* Release notes

Agent guidance:

* Document public APIs more fully than internal helpers.
* Include input dimensions and expected data structures.
* Include output descriptions and structure fields.
* Include package dependencies.
* Include a runnable example.
* Keep documentation synchronized with code behavior.
* Adapt the level of explanation to the audience.

Common failure modes:

* Documenting what the function is called instead of what it does.
* Omitting input shapes.
* Omitting return descriptions.
* Letting documentation drift from implementation.
* Providing no example for public functionality.

### 6.9 Code Review

Code review should improve correctness, clarity, maintainability, and fit for purpose.

A GAUSS code review should check:

* Valid GAUSS syntax
* Valid function names and package dependencies
* Appropriate data structures
* Matrix dimensions
* Missing value handling
* Local variable declarations
* Scope and hidden state
* Public API design
* Output design
* Tests
* Documentation
* Examples
* Backward compatibility
* Readability for the intended audience

Agent guidance:

* Separate blocking correctness issues from style suggestions.
* Explain why a change matters.
* Suggest concrete fixes.
* Avoid overwhelming the user with too many minor comments.
* Prioritize code that will break, mislead users, or be hard to maintain.

Common failure modes:

* Focusing only on style.
* Missing invalid syntax or hallucinated functions.
* Ignoring tests and documentation.
* Suggesting broad rewrites when a focused fix is enough.
* Failing to consider the user's actual goal.

### 6.10 Version Compatibility

Version compatibility matters when code is distributed, documented, or used by customers on different GAUSS versions.

Important considerations:

* Target GAUSS version
* Package version
* Availability of newer language features
* Backward-compatible defaults
* Deprecations
* Documentation version
* Example reproducibility

Agent guidance:

* Ask or infer the target GAUSS version when compatibility matters.
* Prefer broadly supported approaches unless newer functionality is requested.
* Clearly state when code depends on a newer GAUSS version or package version.
* Avoid breaking public APIs without a clear reason.
* Document behavior changes.

Common failure modes:

* Assuming every user has the latest GAUSS version.
* Using newer syntax without warning.
* Breaking public APIs during refactoring.
* Mixing documentation from different versions.
* Ignoring package version dependencies.

### 6.11 Release Process

A release process helps ensure that package or framework changes are intentional, tested, documented, and communicated.

Release considerations may include:

* Version number
* Changelog entry
* Updated documentation
* Updated examples
* Passing tests
* Package metadata
* Backward compatibility notes
* Migration notes when needed

Agent guidance:

* For package changes, consider documentation and tests before release.
* Record notable changes in a changelog.
* Use versioning consistently.
* Separate experimental changes from stable releases.
* Communicate breaking changes clearly.

Common failure modes:

* Releasing code without updated documentation.
* Adding features without examples.
* Fixing bugs without regression tests.
* Failing to note breaking changes.
* Treating version numbers casually.

### 6.12 Maintainability

Maintainability means future developers can understand, modify, test, and extend the code safely.

Preferred practices:

* Keep procedures focused.
* Avoid unnecessary global state.
* Use clear names.
* Use consistent patterns.
* Avoid duplication when it creates maintenance risk.
* Keep public APIs stable.
* Include tests for important behavior.
* Keep documentation close to actual behavior.
* Prefer straightforward code over clever code.

Agent guidance:

* When refactoring, preserve behavior unless the user asks for behavior changes.
* Improve clarity without changing public APIs unnecessarily.
* Explain tradeoffs when suggesting larger structural changes.
* Suggest incremental improvements when code is fragile.
* Consider the likely future maintainer.

Common failure modes:

* Over-abstracting simple code.
* Under-structuring reusable code.
* Creating hidden dependencies.
* Making large rewrites without tests.
* Optimizing for elegance instead of maintainability.

### 6.13 Engineering Judgment

Good software engineering requires matching the solution to the situation.

A one-off script, a teaching example, a blog post, a package procedure, and a production workflow should not all be written the same way.

Agent guidance:

* Ask: who will use this code?
* Ask: will this code be reused?
* Ask: does this need tests?
* Ask: does this need documentation?
* Ask: does this need to remain backward-compatible?
* Ask: is this public API or internal implementation?
* Choose the simplest design that satisfies the real need.

Common failure modes:

* Applying package-level rigor to every small example.
* Giving tutorial-style code for production needs.
* Ignoring the long-term cost of public APIs.
* Treating maintainability as separate from correctness.

### 6.14 Software Engineering Checklist

Before generating or reviewing GAUSS code for reuse, the agent should check:

* Is this a script, procedure, package feature, example, or test?
* Is the code organized appropriately for that context?
* Are public APIs clearly separated from helpers?
* Are procedure inputs and outputs clear?
* Are dependencies stated?
* Are examples runnable?
* Are tests suggested or included when appropriate?
* Are documentation expectations clear?
* Are version compatibility concerns present?
* Are error messages helpful?
* Is the code maintainable by someone else?
* Is the solution over-engineered or under-engineered for the task?


## Domain 7 — Debugging

Debugging is the process of identifying, explaining, and correcting problems in GAUSS code.

This domain helps GAUSS-focused agents diagnose errors systematically instead of guessing from symptoms. A good debugging agent should distinguish between syntax errors, runtime errors, data problems, dimension problems, package issues, and logical mistakes.

### 7.1 Core Mental Model

Debugging GAUSS code requires separating several questions:

1. Is the code valid GAUSS syntax?
2. Are all functions available in base GAUSS or loaded packages?
3. Are the data structures appropriate?
4. Are matrix dimensions compatible?
5. Are inputs defined in the expected scope?
6. Are missing values affecting the result?
7. Is the code logically correct for the intended statistical or numerical task?

A GAUSS-focused agent should not jump immediately to rewriting code. It should first identify the likely failure type and then provide a targeted correction.

Agent guidance:

* Ask for the exact error message when it is not provided.
* Ask for or infer the relevant code block, not the entire project.
* Identify the likely class of error before proposing a fix.
* Explain why the error occurs.
* Provide the smallest useful correction first.
* When useful, provide a cleaned-up version of the code after explaining the minimal fix.

Common failure modes:

* Treating every error as a syntax error.
* Rewriting too much code instead of fixing the actual problem.
* Ignoring data shape and type.
* Ignoring missing values.
* Assuming a function exists without checking whether it is base GAUSS or package-specific.

### 7.2 Syntax Errors

Syntax errors occur when GAUSS cannot parse the code.

Common causes:

* Missing semicolons
* Missing or mismatched parentheses
* Missing or mismatched brackets
* Invalid procedure structure
* Missing `endp`
* Invalid control flow structure
* Reserved keyword used as a variable name
* Cross-language syntax from Python, R, MATLAB, or JavaScript

Agent guidance:

* Look for structural problems first.
* Check procedure boundaries.
* Check control flow boundaries.
* Check whether the code contains syntax from another language.
* Provide a corrected version with minimal changes.
* Explain the syntax rule involved.

Common failure modes:

* Correcting the wrong line because the actual syntax error appears earlier.
* Rewriting valid GAUSS into another invalid form.
* Missing a reserved keyword issue.
* Failing to notice copied Python, R, or MATLAB syntax.

### 7.3 Runtime Errors

Runtime errors occur when syntactically valid code fails during execution.

Common causes:

* Undefined variables
* Undefined procedures
* Missing package or library dependencies
* Invalid file paths
* Invalid input dimensions
* Invalid indexing
* Type mismatch
* Missing data problems
* Insufficient observations
* Singular or ill-conditioned matrices

Agent guidance:

* Identify which object or function is failing.
* Check whether required variables are defined.
* Check whether required packages are loaded.
* Check file paths and working directory assumptions.
* Check input dimensions and types.
* Explain the likely cause and provide a targeted fix.

Common failure modes:

* Assuming the runtime error is caused by the line where it appears, rather than an earlier setup issue.
* Ignoring missing package setup.
* Ignoring file path assumptions.
* Suggesting a statistical fix when the problem is a programming setup issue.

### 7.4 Dimension Mismatches

Dimension mismatches are among the most common GAUSS debugging problems because GAUSS code often relies on matrix operations.

Common causes:

* Matrix multiplication with incompatible dimensions
* Concatenation of objects with incompatible rows or columns
* Row vector vs column vector confusion
* Mismatched dependent and independent variable lengths
* Incorrect lagging, differencing, or trimming
* Missing values dropped from one variable but not another
* Incorrect reshaping or indexing

Agent guidance:

* Ask or compute `rows` and `cols` for relevant matrices when possible.
* Verify that dependent and independent variables have compatible numbers of observations.
* Check whether lagging or differencing reduced sample size.
* Check whether missing-value handling changed dimensions.
* Explain dimensions explicitly in the fix.
* Prefer simple dimension checks in reusable procedures.

Common failure modes:

* Assuming all vectors are interchangeable.
* Ignoring row vs column orientation.
* Dropping rows from one variable but not others.
* Fixing the symptom with transposes instead of correcting the data structure.

### 7.5 Type and Data Structure Errors

Type and data structure errors occur when code uses the wrong operation for the object.

Common causes:

* Treating a DataFrame as a matrix
* Treating an array as a matrix
* Treating a string as a numeric value
* Treating a categorical variable as a meaningful numeric code
* Passing a structure where a matrix is expected
* Using matrix dimension tools on arrays
* Using DataFrame code on plain matrices

Agent guidance:

* Identify the input object type before proposing a fix.
* Use matrix operations for numerical matrices.
* Use DataFrame-aware workflows when labels, mixed types, categoricals, or dates matter.
* Use array-appropriate dimension tools for arrays.
* Preserve metadata when it matters.
* Explain any conversion between data structures.

Common failure modes:

* Automatically converting everything to a matrix.
* Losing variable names unnecessarily.
* Treating categorical labels as numeric values.
* Using `rows` and `cols` on arrays.
* Assuming Python or R DataFrame methods exist in GAUSS.

### 7.6 Procedure and Scope Errors

Procedure and scope errors occur when reusable code relies on variables or behavior outside its intended context.

Common causes:

* Local variables not declared
* Variables used inside a procedure but not passed as inputs
* Hidden dependence on global state
* Conflicting variable names
* Procedure defined but not available in the current context
* Public and helper procedures mixed together unclearly
* Setup code placed inside or outside a procedure incorrectly

Agent guidance:

* Check whether each variable inside a procedure is an input, local variable, or intended global.
* Prefer explicit inputs over hidden dependencies.
* Declare local variables.
* Keep example code separate from procedure definitions.
* Check whether the procedure file is loaded or included.
* Explain scope issues clearly.

Common failure modes:

* Fixing scope issues by adding more global state.
* Ignoring missing local declarations.
* Assuming variables from a prior interactive session are available.
* Moving setup code into a procedure when it belongs in the example script.

### 7.7 Package and Library Loading Errors

Package and library errors occur when code depends on functionality that is unavailable in the current session.

Common causes:

* Package not installed
* Package not loaded
* Incorrect package name
* Function belongs to a package but is treated as base GAUSS
* Version mismatch
* Local source file not included
* Incorrect working directory
* Missing dependency

Agent guidance:

* Distinguish base GAUSS functions from package-specific functions.
* State package dependencies clearly.
* Ask or infer whether the package is installed.
* Check package examples or source when behavior matters.
* Avoid inventing package setup steps.
* Provide a base GAUSS alternative when reasonable.

Common failure modes:

* Assuming the user has a package installed.
* Treating package functions as built-in functions.
* Inventing package names or load commands.
* Ignoring version compatibility.
* Failing to mention required setup steps.

### 7.8 File I/O and Path Errors

File I/O errors occur when GAUSS cannot find, read, write, or parse a file as expected.

Common causes:

* Incorrect working directory
* Incorrect file path
* Platform-specific path separators
* Missing file extension
* File permissions
* File locked by another application
* Wrong delimiter or file format
* Variable names or headers not read as expected
* Date or categorical columns parsed unexpectedly

Agent guidance:

* Check the working directory and file path assumptions.
* Use clear, explicit paths in examples when possible.
* Explain platform-specific path concerns.
* Verify file format and delimiter.
* Check whether the data was imported as expected before modeling.
* Show a quick inspection step after import.

Common failure modes:

* Assuming the file is in the current working directory.
* Ignoring Windows vs Unix-style paths.
* Proceeding directly to analysis without checking imported data.
* Treating imported strings, dates, or categoricals incorrectly.

### 7.9 Missing Value Problems

Missing values can cause incorrect results, failed estimation, dimension changes, or unexpected output.

Common causes:

* Missing values in dependent or independent variables
* Missing values introduced by lagging or differencing
* Missing values ignored in one part of the workflow but not another
* Missing values treated as zeros
* Row deletion applied inconsistently
* Insufficient observations after cleaning

Agent guidance:

* Ask whether missing values are present when results are unexpected.
* Explain how missing values affect the computation.
* Be explicit about whether missing values are dropped, flagged, imputed, or preserved.
* Apply missing-value handling consistently across related variables.
* Warn users when cleaning changes the sample size.

Common failure modes:

* Silently dropping observations.
* Treating missing values as zeros.
* Forgetting that transformations can introduce missing values.
* Comparing model results without noting different estimation samples.

### 7.10 Logical Errors

Logical errors occur when code runs but produces the wrong result.

Common causes:

* Wrong formula or model specification
* Incorrect ordering of observations
* Incorrect time or panel identifier
* Incorrect sorting before lagging or differencing
* Wrong variable selected from a DataFrame
* Incorrect condition in an `if` statement
* Incorrect loop bounds
* Incorrect interpretation of output
* Wrong assumptions about matrix orientation

Agent guidance:

* Verify the user's intended outcome.
* Check data ordering before time series or panel operations.
* Check selected variables and transformations.
* Check loop start and stop conditions.
* Compare against a simple known example when possible.
* Separate statistical logic from coding syntax.

Common failure modes:

* Declaring success because the code runs.
* Ignoring sorting requirements.
* Ignoring panel/time identifiers.
* Failing to test against a simple case with known output.
* Explaining the wrong statistical model.

### 7.11 Numerical Debugging

Numerical debugging is needed when code runs but results are unstable, implausible, or sensitive.

Common causes:

* Singular matrices
* Ill-conditioned matrices
* Collinearity
* Scaling problems
* Precision limitations
* Optimization convergence issues
* Poor starting values
* Outliers
* Near-zero denominators
* Random seed or reproducibility problems

Agent guidance:

* Check conditioning and rank-related issues when matrix inversion fails.
* Avoid assuming numerical failure means syntax failure.
* Suggest diagnostics before changing the model.
* Consider scaling or alternative formulations when appropriate.
* Set or document random seeds in simulation examples.
* Explain numerical issues in plain language when helping beginners.

Common failure modes:

* Recommending arbitrary code changes without diagnosing the numerical issue.
* Ignoring collinearity or singularity.
* Treating convergence problems as package bugs.
* Failing to distinguish statistical problems from programming errors.

### 7.12 Performance Debugging

Performance debugging is needed when code runs but is too slow or memory-intensive.

Common causes:

* Repeated memory allocation inside loops
* Unnecessary copying
* Inefficient string processing
* Inefficient DataFrame-to-matrix conversions
* Recomputing values unnecessarily
* Using overly complex code for simple matrix operations
* Very large intermediate objects

Agent guidance:

* Identify the slow section before optimizing.
* Prefer clarity until performance is actually a problem.
* Preallocate when repeated growth is causing slowdowns.
* Use vectorized or matrix operations when they naturally fit.
* Avoid forced vectorization that harms readability or correctness.
* Benchmark before and after major performance changes.

Common failure modes:

* Optimizing the wrong part of the code.
* Assuming all loops are bad.
* Creating unreadable vectorized code.
* Ignoring memory use.
* Improving speed while changing results.

### 7.13 Debugging Workflow

A GAUSS-focused agent should follow a structured debugging workflow.

Recommended workflow:

1. Identify the user's goal.
2. Capture the exact error message or unexpected behavior.
3. Identify the smallest relevant code block.
4. Classify the issue:

   * syntax
   * runtime
   * dimension
   * type/data structure
   * scope
   * package/library
   * file I/O
   * missing values
   * logical
   * numerical
   * performance
5. Check data structures and dimensions.
6. Check dependencies and execution context.
7. Provide a minimal fix.
8. Explain why the fix works.
9. Suggest a small validation step.
10. Offer a cleaner refactor only after the immediate issue is addressed.

Agent guidance:

* Prefer a minimal correction before a full rewrite.
* Make assumptions explicit.
* If information is missing, provide the most likely diagnosis and say what would confirm it.
* Avoid overwhelming the user with unrelated improvements.

### 7.14 Debugging Response Pattern

When helping a user debug GAUSS code, the agent should usually respond with:

1. Likely cause
2. Why it happens
3. Minimal fix
4. Corrected code
5. Optional improvement or validation check

Example response shape:

```text
The likely issue is a dimension mismatch between `y` and `x`.

This usually happens when one variable has been lagged or cleaned but the other has not, so they no longer have the same number of rows.

Minimal fix:
- Check `rows(y)` and `rows(x)`.
- Apply the same row filtering or trimming to both objects.

Corrected pattern:
...
```

Agent guidance:

* Keep the first answer focused.
* Give the user something actionable immediately.
* Save broader refactoring advice for after the bug is fixed.

### 7.15 Debugging Checklist

Before giving a debugging answer, the agent should check:

* What is the user's intended goal?
* What exact error or unexpected result occurred?
* Is the code valid GAUSS syntax?
* Are all functions real GAUSS functions or stated package functions?
* Are required packages loaded?
* Are required files available?
* Are variables defined in the expected scope?
* Are data structures appropriate?
* Are dimensions compatible?
* Are missing values present?
* Are dates, categoricals, or panel identifiers involved?
* Is the issue statistical, numerical, or purely syntactic?
* What is the smallest useful fix?
* Would a small validation check confirm the solution?


## Domain 8 — Performance Engineering

Performance engineering is the practice of writing GAUSS code that uses time and memory efficiently without sacrificing correctness, readability, or maintainability.

This domain helps GAUSS-focused agents make practical performance recommendations, especially for matrix operations, loops, simulations, large datasets, and package-quality code.

### 8.1 Core Mental Model

GAUSS is designed for efficient numerical and matrix-oriented computation. Performance often depends on choosing the right data structure, avoiding unnecessary copying, using matrix operations when appropriate, and keeping memory allocation under control.

However, performance should not be treated as the only goal. Code should first be correct, then clear, then optimized where it matters.

Agent guidance:

* Prefer clear, correct code before optimization.
* Optimize only the parts of code that are actually performance-sensitive.
* Use matrix operations when they naturally express the computation.
* Do not force vectorization when it makes code unclear or changes the logic.
* Consider memory use as well as execution time.
* Preserve numerical correctness when improving performance.

Common failure modes:

* Assuming loops are always bad.
* Assuming vectorized code is always better.
* Optimizing before understanding the bottleneck.
* Making code faster but less correct.
* Making code faster but much harder to debug.
* Ignoring memory allocation and copying.

### 8.2 Vectorization

Vectorization means using operations that apply to entire vectors or matrices rather than manually iterating over individual elements.

Vectorization is often useful when:

* The operation naturally applies to a full vector or matrix.
* Built-in matrix operations make the code shorter and clearer.
* The code performs repeated arithmetic over large data.
* A loop only exists to apply the same operation element-by-element.
* Performance matters and the vectorized form is readable.

Agent guidance:

* Prefer vectorization when it is natural and readable.
* Explain vectorized code when helping beginners.
* Use intermediate variables if they make the vectorized expression easier to understand.
* Avoid vectorized expressions that hide important logic.
* Do not vectorize sequential algorithms that depend on previous iterations.

Common failure modes:

* Replacing simple loops with obscure vectorized expressions.
* Vectorizing code that is logically sequential.
* Confusing element-by-element operations with matrix algebra.
* Ignoring dimension compatibility.
* Claiming vectorization is required when a loop is acceptable.

### 8.3 Loops

Loops are appropriate when the logic is sequential, conditional, stateful, or clearer than a vectorized alternative.

Loops are often appropriate for:

* Simulations with repeated draws
* Recursive calculations
* Time series algorithms
* Iterative optimization
* Conditional updates
* Accumulating results with state
* Teaching examples
* Code where clarity matters more than compactness

Agent guidance:

* Use loops when they fit the algorithm.
* Keep loop bodies focused and readable.
* Avoid unnecessary work inside loops.
* Preallocate storage when collecting results.
* Move repeated invariant calculations outside loops.
* Use clear loop bounds and indexing.

Common failure modes:

* Treating every loop as a performance problem.
* Growing matrices or arrays repeatedly inside a loop.
* Recomputing constants inside a loop.
* Using unclear loop bounds.
* Introducing off-by-one errors when translating from another language.

### 8.4 Preallocation

Preallocation means creating storage before a loop rather than repeatedly growing an object.

Preallocation is important when:

* A loop fills a vector, matrix, array, or structure field.
* The number of iterations is known.
* Intermediate results are stored repeatedly.
* Simulation results are collected.
* Performance or memory use matters.

Agent guidance:

* Preallocate result matrices, vectors, or arrays when size is known.
* Use meaningful dimensions when preallocating.
* Avoid repeatedly concatenating results inside a loop when preallocation is possible.
* Explain preallocation in beginner-friendly terms when relevant.
* Balance preallocation with clarity in small examples.

Common failure modes:

* Repeatedly growing a matrix inside a loop.
* Preallocating with the wrong shape.
* Preallocating too large an object unnecessarily.
* Ignoring memory constraints for large simulations.

### 8.5 Memory Allocation and Copying

Memory use matters when working with large matrices, arrays, DataFrames, simulations, or repeated transformations.

Important considerations:

* Large intermediate objects can slow code or exhaust memory.
* Unnecessary copies can make code inefficient.
* DataFrame-to-matrix conversions should be intentional.
* Repeated concatenation can create avoidable memory pressure.
* Storing every intermediate result may be unnecessary.

Agent guidance:

* Avoid unnecessary large intermediate objects.
* Avoid copying data when a smaller derived object is sufficient.
* Store only results that are needed later.
* Be careful when converting between DataFrames and matrices.
* Consider memory use when recommending arrays for high-dimensional results.
* For large simulations, consider whether summary statistics are enough.

Common failure modes:

* Creating multiple full-size copies of large data.
* Saving every intermediate object unnecessarily.
* Converting entire DataFrames to matrices when only a few columns are needed.
* Using arrays where a more compact representation would work.
* Ignoring memory use while focusing only on speed.

### 8.6 Matrix Operations

Matrix operations are central to GAUSS performance and readability.

Matrix operations are usually preferred when:

* The calculation is naturally linear algebra.
* The dimensions are clear.
* The operation maps directly to a mathematical expression.
* Built-in matrix routines are available.
* The result is easier to verify mathematically.

Agent guidance:

* Use matrix operations for linear algebra and numerical routines.
* Check dimensions before multiplication, inversion, concatenation, or decomposition.
* Prefer numerically appropriate routines over manual implementations.
* Avoid unnecessary matrix inversion when a more stable approach is available.
* Explain matrix dimensions when teaching or debugging.

Common failure modes:

* Writing loops for simple matrix operations.
* Using matrix operations without checking dimensions.
* Inverting matrices unnecessarily.
* Confusing row vectors and column vectors.
* Translating formulas directly without verifying dimensions.

### 8.7 DataFrames and Performance

DataFrames are useful for labeled, mixed-type, imported, or exploratory data, but they are not always the best structure for numerical computation.

Agent guidance:

* Use DataFrames for data cleaning, inspection, variable selection, labels, dates, categoricals, and mixed types.
* Use matrices for numerical computation after data is cleaned and selected.
* Convert or extract only the needed variables when moving to matrix-based computation.
* Avoid repeatedly converting between DataFrames and matrices in performance-sensitive code.
* Preserve metadata when it matters to the user.

Common failure modes:

* Treating DataFrames as the default structure for all computation.
* Converting an entire DataFrame when only selected variables are needed.
* Losing variable names unnecessarily.
* Repeating DataFrame extraction inside loops.
* Using matrix-only assumptions on mixed-type data.

### 8.8 Strings and Performance

String operations may become expensive when repeated many times or applied to large collections of text.

Agent guidance:

* Use valid GAUSS string functions.
* Avoid unnecessary repeated string parsing inside loops.
* Precompute repeated string search results when practical.
* Be careful with file path construction and repeated file operations.
* Keep string-heavy workflows simple and explicit.

Common failure modes:

* Inventing Python-style string methods.
* Repeatedly searching or parsing the same string.
* Mixing string processing with numerical loops unnecessarily.
* Ignoring platform differences in file paths.

### 8.9 File I/O Performance

File input and output can become a bottleneck when reading or writing repeatedly.

Agent guidance:

* Avoid reading the same file repeatedly inside loops.
* Load data once when practical.
* Inspect imported data before computation.
* Write output intentionally and avoid unnecessary repeated writes.
* Be explicit about file paths and formats.
* Keep data import separate from performance-sensitive numerical computation when possible.

Common failure modes:

* Loading data repeatedly inside a simulation or loop.
* Writing large output files repeatedly.
* Proceeding without verifying import results.
* Confusing file I/O problems with computational performance problems.

### 8.10 Benchmarking

Benchmarking helps verify whether a performance change actually improves code.

Agent guidance:

* Benchmark before and after optimization when performance matters.
* Use representative input sizes.
* Verify that optimized code returns the same results as the original.
* Avoid drawing conclusions from tiny examples if the real data is large.
* Consider both runtime and memory use.
* Keep benchmark code separate from production code when possible.

Common failure modes:

* Optimizing based on intuition only.
* Benchmarking unrealistic toy cases.
* Measuring speed without checking correctness.
* Improving one case while making common cases slower.
* Ignoring memory use.

### 8.11 Numerical Stability and Performance

Faster code is not better if it produces unstable or inaccurate numerical results.

Agent guidance:

* Prefer numerically stable methods over fragile shortcuts.
* Avoid unnecessary matrix inversion when a more stable approach exists.
* Watch for singular or ill-conditioned matrices.
* Consider scaling when optimization or linear algebra is unstable.
* Keep precision and convergence issues separate from syntax or performance issues.

Common failure modes:

* Replacing a stable method with a faster but less reliable one.
* Ignoring conditioning problems.
* Treating optimization failure as a speed issue.
* Comparing results without considering numerical tolerance.
* Sacrificing statistical correctness for compact code.

### 8.12 Readability vs Performance

Performance improvements should be weighed against readability and maintainability.

Agent guidance:

* For teaching, prefer clear code unless performance is the topic.
* For production or package code, optimize important bottlenecks while preserving structure.
* Explain tradeoffs when recommending a less readable but faster approach.
* Avoid clever code that future users cannot maintain.
* Document non-obvious performance choices.

Common failure modes:

* Giving highly optimized code to a beginner.
* Making code unreadable for a small speed gain.
* Refactoring for performance before confirming a bottleneck.
* Removing helpful intermediate variables that clarify the computation.

### 8.13 Performance Review Checklist

When reviewing GAUSS code for performance, the agent should check:

* Is the code correct first?
* Is there evidence of a real bottleneck?
* Are loops used appropriately?
* Are result objects preallocated when needed?
* Are large objects copied unnecessarily?
* Are repeated calculations moved outside loops?
* Are matrix operations used when natural?
* Are DataFrame-to-matrix conversions intentional?
* Is file I/O happening inside loops unnecessarily?
* Are string operations repeated unnecessarily?
* Are numerical methods stable?
* Has the optimized code been checked against the original output?
* Is the performance gain worth any added complexity?

### 8.14 Preferred Performance Defaults

When the user does not provide performance requirements, the agent should use these defaults:

| Situation                                 | Preferred Default                      |
| ----------------------------------------- | -------------------------------------- |
| Beginner example                          | Clear, readable code                   |
| Small one-off task                        | Simple implementation                  |
| Reusable procedure                        | Clear code with reasonable validation  |
| Simulation storing repeated results       | Preallocate result storage             |
| Large numerical computation               | Prefer matrix operations where natural |
| Data cleaning with labels and mixed types | Use DataFrame workflow                 |
| Estimation after cleaning                 | Use matrix inputs intentionally        |
| Unclear bottleneck                        | Diagnose before optimizing             |
| Performance-sensitive package code        | Benchmark and preserve correctness     |


## Domain 9 — Package Ecosystem

The GAUSS package ecosystem organizes reusable functionality into installable, documented, testable, and versioned components.

This domain helps GAUSS-focused agents distinguish between base GAUSS functionality, local source code, libraries, packages, examples, tests, and documentation. It also helps agents avoid inventing package behavior or assuming package-specific procedures are available in every GAUSS session.

### 9.1 Core Mental Model

A GAUSS package is more than a collection of procedures. It is a reusable software unit that may include source code, public APIs, internal helpers, examples, documentation, tests, metadata, dependencies, and release history.

A GAUSS-focused agent should understand package work as software engineering work, not merely code generation.

Agent guidance:

* Distinguish base GAUSS functionality from package-specific functionality.
* State package dependencies clearly.
* Check package source, examples, or documentation before using package-specific procedures.
* Treat public package APIs as stable user-facing interfaces.
* Treat internal helpers as implementation details unless the user specifically asks about them.
* Consider tests, examples, documentation, and version compatibility when changing package code.

Common failure modes:

* Calling package procedures as if they were base GAUSS functions.
* Inventing package names or setup steps.
* Ignoring package dependencies.
* Exposing internal helpers as public APIs.
* Adding package functionality without tests or documentation.
* Assuming the latest package version is installed.

### 9.2 Base GAUSS vs Package Functionality

Not every GAUSS function or procedure is available in every session.

Important distinctions:

* Base GAUSS functions are available without installing additional packages.
* Application or package procedures may require installation, loading, or setup.
* Local source files may require include paths, libraries, or project-specific setup.
* Documentation examples may depend on packages, data files, or version-specific features.

Agent guidance:

* Identify whether a function is base GAUSS or package-specific.
* Prefer base GAUSS for simple examples when possible.
* Use package functionality when the package is central to the user’s task.
* Clearly state when code requires a package.
* Provide setup guidance only when it is verified or already known from approved sources.

Common failure modes:

* Treating package functions as built-in functions.
* Omitting package installation or loading requirements.
* Mixing base and package functionality without explanation.
* Assuming package availability from the agent’s memory.
* Giving setup instructions copied from another language ecosystem.

### 9.3 Package Structure

A maintainable GAUSS package should have a predictable structure.

Package contents may include:

* Source files
* Public procedure definitions
* Internal helper procedures
* Library files
* Examples
* Tests
* Documentation
* Data files
* Metadata
* Changelog or release notes
* README or overview material

Agent guidance:

* Keep source code separate from examples and tests.
* Keep public APIs distinguishable from internal helpers.
* Include examples that demonstrate real user workflows.
* Include tests for important behavior.
* Keep documentation synchronized with code.
* Avoid recommending excessive structure for small experimental code.

Common failure modes:

* Putting all package logic into one large script.
* Mixing examples directly into source files.
* Omitting tests for public procedures.
* Omitting documentation for public APIs.
* Creating a complex package layout before the project needs it.

### 9.4 Public Package APIs

Public package APIs are the procedures users are expected to call directly.

Public package APIs should be:

* Stable
* Clearly named
* Documented
* Tested
* Consistent with related procedures
* Designed around user workflows
* Supported by examples

Agent guidance:

* Design public APIs from the user’s perspective.
* Keep required arguments clear and minimal.
* Use optional arguments or control structures when configuration grows.
* Return useful outputs, often as structures when results have named components.
* Preserve backward compatibility when practical.
* Document behavior changes when compatibility is broken.

Common failure modes:

* Designing APIs around internal implementation details.
* Exposing too many helper procedures.
* Changing public call signatures unnecessarily.
* Returning outputs that are hard to interpret.
* Providing no examples for public procedures.

### 9.5 Internal Helpers

Internal helpers support package implementation but are not the main user-facing interface.

Internal helpers may:

* Reduce duplication
* Encapsulate validation
* Isolate transformations
* Support public procedures
* Handle package-specific implementation details

Agent guidance:

* Keep internal helpers focused and narrow.
* Do not expose helpers publicly unless users need them.
* Use consistent naming and organization.
* Test helpers when they contain important logic.
* Avoid documenting helpers as public APIs unless they are intended for users.

Common failure modes:

* Turning every helper into a public procedure.
* Hiding important behavior in unclear helper code.
* Creating many small helpers that obscure the main workflow.
* Leaving helper behavior untested.

### 9.6 Dependencies

Packages may depend on base GAUSS functionality, other packages, data files, external files, or version-specific features.

Agent guidance:

* State package dependencies clearly.
* Check whether dependencies are required or optional.
* Mention version requirements when relevant.
* Avoid assuming dependencies are installed.
* Prefer graceful failure or clear error messages when dependencies are missing.
* Keep examples explicit about setup.

Common failure modes:

* Omitting dependency information.
* Assuming every user has the same local setup.
* Calling dependency functions without checking availability.
* Creating examples that fail in a clean session.
* Ignoring version-specific behavior.

### 9.7 Versioning

Versioning communicates stability, compatibility, and change history.

Important versioning concerns:

* GAUSS version compatibility
* Package version compatibility
* Public API changes
* Deprecations
* Bug fixes
* New features
* Documentation updates
* Example compatibility

Agent guidance:

* Ask or infer target GAUSS version when compatibility matters.
* Avoid using newer features without warning if users may be on older versions.
* Preserve public APIs when practical.
* Document breaking changes.
* Use changelog entries to summarize notable changes.
* Distinguish experimental work from stable releases.

Common failure modes:

* Assuming all users are on the newest GAUSS version.
* Breaking public APIs without noting it.
* Updating code but not documentation.
* Updating documentation but not examples.
* Treating package versioning casually.

### 9.8 Package Examples

Package examples show users how to apply package functionality.

Good examples should be:

* Runnable
* Focused
* Realistic
* Clear about setup
* Clear about required data
* Clear about expected output
* Aligned with documented APIs

Agent guidance:

* Include package loading or setup steps when needed.
* Use examples that match common user workflows.
* Keep beginner examples simple.
* Use more realistic examples for advanced workflows.
* Avoid relying on hidden workspace state.
* Keep examples separate from tests when possible.

Common failure modes:

* Providing examples that do not run.
* Omitting required package setup.
* Omitting required data setup.
* Using overly complex examples for simple functionality.
* Failing to update examples after API changes.

### 9.9 Package Tests

Package tests protect expected behavior and prevent regressions.

Useful package tests include:

* Basic successful calls
* Known-result checks
* Error handling
* Optional argument behavior
* Missing value behavior
* Dimension mismatch behavior
* Structure field presence
* Package loading behavior
* Regression tests for fixed bugs

Agent guidance:

* Suggest tests when adding or changing public package functionality.
* Test returned values, not just printed output.
* Use small known examples when possible.
* Use tolerance-based comparisons for numerical results.
* Add regression tests for bug fixes.
* Keep tests easy to run and understand.

Common failure modes:

* Testing only whether code runs.
* Ignoring error paths.
* Omitting tests for optional arguments.
* Ignoring missing values and dimension mismatches.
* Relying only on visual inspection of output.

### 9.10 Package Documentation

Package documentation explains how users should install, load, call, and interpret package functionality.

Documentation may include:

* README
* API reference
* Sphinx `.rst` files
* Tutorials
* Examples
* Changelog
* Release notes
* Migration notes

Agent guidance:

* Document public APIs thoroughly.
* Include required inputs, optional inputs, outputs, assumptions, and examples.
* Document structure fields when returning structures.
* Mention package dependencies.
* Keep documentation aligned with source code.
* Include migration notes for breaking changes when needed.

Common failure modes:

* Omitting input dimensions.
* Omitting output descriptions.
* Omitting examples.
* Letting documentation drift from source code.
* Failing to explain package setup.

### 9.11 Package Source Review

When reviewing package source code, the agent should consider more than syntax.

Review dimensions include:

* Valid GAUSS syntax
* Correct procedure structure
* Public vs internal API boundaries
* Input validation
* Output design
* Package dependencies
* Documentation
* Tests
* Examples
* Version compatibility
* Backward compatibility
* Maintainability

Agent guidance:

* Separate blocking correctness issues from maintainability suggestions.
* Check that public APIs are documented and tested.
* Check that examples still match current APIs.
* Check whether new functionality needs changelog notes.
* Avoid broad rewrites when focused changes are sufficient.

Common failure modes:

* Reviewing only the single edited procedure.
* Ignoring examples and tests.
* Missing dependency or version issues.
* Recommending public API changes without considering users.
* Failing to check documentation alignment.

### 9.12 Distribution and Release

Distribution makes package functionality available to users.

Release considerations include:

* Version number
* Passing tests
* Updated documentation
* Updated examples
* Updated changelog
* Compatibility notes
* Dependency notes
* Installation or update instructions

Agent guidance:

* Before release, check code, tests, examples, and documentation together.
* Document breaking changes clearly.
* Keep release notes focused on user-facing changes.
* Include migration guidance when behavior changes.
* Avoid releasing undocumented public APIs.

Common failure modes:

* Releasing code without tests.
* Releasing new APIs without examples.
* Forgetting to update changelog or documentation.
* Failing to mention breaking changes.
* Publishing behavior that depends on a local setup.

### 9.13 Package Ecosystem Retrieval Rules

The agent should retrieve package source, examples, or documentation when:

* The user asks about a package-specific procedure.
* The agent is unsure whether a procedure is base GAUSS or package-specific.
* Function syntax or return values matter.
* The task involves package internals.
* The task involves modifying package source.
* The task involves writing package documentation.
* The task involves debugging package loading or dependency issues.

The agent may answer conceptually without retrieval when:

* The user asks a high-level package design question.
* The question is about general software engineering tradeoffs.
* The exact package API is not needed.

### 9.14 Package Ecosystem Checklist

Before generating or reviewing package-related GAUSS code, the agent should check:

* Is this base GAUSS or package-specific functionality?
* Is the package installed or loaded?
* Are dependencies stated?
* Is the target GAUSS or package version relevant?
* Is this a public API or internal helper?
* Are examples needed?
* Are tests needed?
* Does documentation need to be updated?
* Are output structures stable and documented?
* Are backward compatibility concerns present?
* Should a changelog entry be added?
* Would the code run in a clean session?


## Domain 10 — Documentation and Examples

Documentation and examples help users understand what GAUSS code does, how to use it, what assumptions it makes, and how to adapt it safely.

This domain helps GAUSS-focused agents produce documentation and examples that are accurate, runnable, clear, audience-appropriate, and aligned with GAUSS conventions.

### 10.1 Core Mental Model

Good documentation answers four questions:

1. What does this do?
2. When should I use it?
3. How do I use it correctly?
4. What should I expect as output?

Good examples answer a related question:

> What does this look like in practice?

A GAUSS-focused agent should not treat documentation as filler text. Documentation is part of the user interface for GAUSS code.

Agent guidance:

* Write documentation for the intended audience.
* Include runnable examples when possible.
* State inputs, outputs, assumptions, and dependencies.
* Keep examples focused.
* Avoid examples that require hidden setup.
* Keep documentation synchronized with actual code behavior.
* Distinguish tutorial explanations from formal API reference.

Common failure modes:

* Writing documentation that only restates the procedure name.
* Omitting input dimensions.
* Omitting output descriptions.
* Providing examples that do not run.
* Failing to mention package dependencies.
* Letting documentation drift from code behavior.

### 10.2 Documentation Types

GAUSS documentation may serve different purposes.

Common documentation types include:

* API reference documentation
* Sphinx `.rst` files
* README files
* Package documentation
* Inline comments
* Tutorial walkthroughs
* Blog posts
* Example files
* Changelogs
* Release notes
* Migration notes
* Troubleshooting guides

Agent guidance:

* Match the documentation format to the user's goal.
* Use API reference for complete procedure behavior.
* Use tutorials for learning workflows.
* Use examples for practical application.
* Use changelogs and release notes for versioned changes.
* Use troubleshooting guides for recurring user problems.

Common failure modes:

* Using a tutorial style when formal reference is needed.
* Using terse reference style when the user needs teaching.
* Mixing release notes, examples, and API docs into one unclear document.
* Omitting migration guidance for breaking changes.

### 10.3 API Documentation

API documentation should describe public procedures clearly and completely.

API documentation should usually include:

* Purpose
* Syntax or call pattern
* Required inputs
* Optional inputs and defaults
* Keyword arguments or control structures
* Expected input types and dimensions
* Outputs
* Structure fields when structures are returned
* Assumptions
* Error conditions
* Package dependencies
* Example usage
* Related procedures when relevant

Agent guidance:

* Document public APIs more fully than internal helpers.
* Include input shape information when matrix dimensions matter.
* Document returned objects carefully.
* Include a minimal runnable example.
* Keep argument names and behavior aligned with the implementation.
* Mention version-specific behavior when relevant.

Common failure modes:

* Missing expected input dimensions.
* Missing optional argument defaults.
* Missing structure field descriptions.
* Documenting behavior that the code does not implement.
* Forgetting to update documentation after API changes.

### 10.4 Sphinx and `.rst` Documentation

Sphinx `.rst` documentation is useful for formal reference documentation and package documentation.

Agent guidance:

* Keep headings clear and hierarchical.
* Use consistent formatting for syntax, parameters, returns, examples, and notes.
* Make examples runnable when possible.
* Avoid overly long examples in formal reference pages.
* Cross-reference related procedures when useful.
* Keep `.rst` syntax valid.
* Preserve code block formatting.

Common failure modes:

* Producing invalid `.rst` syntax.
* Mixing Markdown syntax into `.rst` pages.
* Missing required reference sections.
* Using examples that are too long or too dependent on local files.
* Failing to document returned structures.

### 10.5 Inline Comments

Inline comments should clarify intent, assumptions, and non-obvious logic.

Good comments explain:

* Why a step is needed
* What assumption is being made
* Why a data structure was chosen
* Why dimensions are being changed
* Why missing values are handled a certain way
* Why a numerical or performance choice was made

Agent guidance:

* Use comments to mark major logical steps.
* Avoid comments that merely restate obvious syntax.
* Add more comments in beginner examples.
* Use fewer but more meaningful comments in advanced code.
* Keep comments synchronized with code.

Common failure modes:

* Over-commenting obvious lines.
* Under-commenting important assumptions.
* Leaving outdated comments after code changes.
* Writing comments that describe what the code used to do.

### 10.6 Examples

Examples should show users how to apply code correctly.

Good examples should be:

* Runnable
* Focused
* Minimal but meaningful
* Clear about setup
* Clear about inputs
* Clear about expected output
* Appropriate for the user’s level
* Easy to modify

Agent guidance:

* Use simple examples for beginners.
* Use realistic examples for applied workflows.
* Include data generation or data loading steps.
* Include package setup when required.
* Show expected output or interpretation when helpful.
* Keep examples separate from reusable procedure definitions when appropriate.
* Avoid hidden dependencies on prior workspace state.

Common failure modes:

* Providing examples that cannot run as written.
* Omitting setup steps.
* Using overly complex examples for simple concepts.
* Using toy examples that do not clarify the real workflow.
* Mixing example code with package source code.

### 10.7 Tutorials

Tutorials teach a workflow step by step.

Good tutorials should:

* Start with the user's goal
* Introduce concepts progressively
* Use small, concrete examples
* Explain key decisions
* Show intermediate outputs when useful
* End with a working result
* Mention next steps or extensions

Agent guidance:

* Optimize tutorials for learning, not just completeness.
* Avoid overwhelming users with too many options at once.
* Explain why each major step matters.
* Use progressive disclosure: start simple, then add complexity.
* Connect code to the statistical or analytical purpose when relevant.

Common failure modes:

* Starting with advanced abstractions too early.
* Skipping setup or data inspection.
* Providing code without explaining the workflow.
* Mixing several concepts in one example.
* Assuming the reader already understands GAUSS data structures.

### 10.8 Blog-Style Explanations

Blog-style explanations are useful for applied examples, feature introductions, and educational content.

Good blog examples should:

* Have a clear narrative
* Start from a practical problem
* Use approachable language
* Include runnable GAUSS code
* Explain outputs
* Connect code to user value
* Avoid unnecessary jargon
* Link to official documentation when useful

Agent guidance:

* Write blog examples with a teaching mindset.
* Keep code blocks focused.
* Explain the intuition before technical details when appropriate.
* Include enough context for mixed-experience readers.
* Avoid claiming more than the example demonstrates.
* Prefer practical examples over abstract demonstrations.

Common failure modes:

* Writing like a reference manual instead of a tutorial.
* Including too much code at once.
* Omitting interpretation of results.
* Using unsupported claims or vague benefits.
* Forgetting to link concepts back to GAUSS functionality.

### 10.9 Beginner-Friendly Explanations

Beginner-friendly explanations should reduce cognitive load.

Preferred practices:

* Explain one concept at a time.
* Use concrete examples.
* Avoid unnecessary abstraction.
* Define terminology.
* Show intermediate steps.
* Explain common mistakes.
* Use plain language.
* Connect syntax to purpose.

Agent guidance:

* Assume the user may be learning both GAUSS and the statistical workflow.
* Explain data structures explicitly.
* Avoid dense one-liners.
* Prefer scripts or small examples before package-style abstractions.
* Show how to inspect results.

Common failure modes:

* Giving expert-level code without explanation.
* Assuming the user understands matrices, DataFrames, or procedures.
* Using too many new concepts at once.
* Explaining syntax but not purpose.

### 10.10 Advanced Reference Material

Advanced reference material should be concise, complete, and precise.

Preferred practices:

* Focus on exact behavior.
* Document edge cases.
* Mention performance implications.
* Mention version compatibility.
* Clarify assumptions.
* Provide compact examples.
* Discuss tradeoffs where relevant.

Agent guidance:

* Do not overexplain basic syntax for expert users.
* Include design and edge-case considerations.
* Make return values and structures precise.
* Include relevant warnings or limitations.
* Keep examples realistic but not verbose.

Common failure modes:

* Being too vague for advanced users.
* Omitting edge cases.
* Omitting performance or compatibility implications.
* Providing beginner explanations when expert reference is needed.

### 10.11 Documentation for Returned Structures

When a procedure returns a structure, the documentation should describe the fields clearly.

Structure documentation should include:

* Structure name or role
* Field names
* Field types
* Field dimensions when relevant
* Meaning of each field
* Whether fields are always present
* How users should access fields
* Example inspection or usage

Agent guidance:

* Document structure fields for public APIs.
* Keep field names stable across related procedures.
* Use consistent naming patterns.
* Explain how structure outputs support downstream use.
* Include a short example accessing important fields.

Common failure modes:

* Returning structures without field documentation.
* Using unclear field names.
* Changing field names without noting it.
* Documenting only printed output while ignoring returned fields.

### 10.12 Documentation for DataFrames and Data Workflows

DataFrame workflows require documentation that preserves the user's understanding of variables, labels, dates, categoricals, and transformations.

Documentation should explain:

* Required columns
* Variable names
* Date or time identifiers
* Group identifiers
* Categorical variables
* Missing value handling
* Sorting requirements
* Transformations
* Conversion to matrices when needed

Agent guidance:

* State expected DataFrame structure.
* Preserve variable names in examples.
* Explain when data are converted to matrices.
* Document sorting requirements for panel or time series operations.
* Explain how missing values affect the workflow.

Common failure modes:

* Treating DataFrames as unlabeled matrices.
* Omitting required column names.
* Ignoring dates or categorical variables.
* Failing to explain matrix extraction before estimation.
* Losing metadata without explanation.

### 10.13 Documentation Review Checklist

When reviewing GAUSS documentation, the agent should check:

* Does it explain the purpose clearly?
* Does it identify the intended audience?
* Does it document inputs?
* Does it document input dimensions?
* Does it document optional arguments and defaults?
* Does it document outputs?
* Does it document returned structure fields?
* Does it state dependencies?
* Does it include a runnable example?
* Does the example match the documented API?
* Does it mention important assumptions?
* Does it handle version-specific behavior if relevant?
* Is the format appropriate: README, `.rst`, tutorial, blog, or inline comments?
* Is the documentation synchronized with the code?

### 10.14 Example Review Checklist

When reviewing GAUSS examples, the agent should check:

* Can the example run as written?
* Are setup steps included?
* Is required data available or generated?
* Are package dependencies stated?
* Is the example focused?
* Is the example appropriate for the audience?
* Are intermediate steps explained when useful?
* Are outputs labeled or interpreted?
* Does the example rely on hidden workspace state?
* Does it demonstrate the intended concept?
* Is it too simple, too complex, or just right for the purpose?

### 10.15 Preferred Documentation Defaults

When the user does not specify a documentation style, the agent should use these defaults:

| Situation                | Preferred Default                                        |
| ------------------------ | -------------------------------------------------------- |
| Public procedure         | API-style documentation with example                     |
| Beginner question        | Short explanation plus runnable example                  |
| Package feature          | Reference docs, example, and dependency notes            |
| Blog/tutorial            | Narrative explanation with step-by-step code             |
| Code review              | Focused comments tied to correctness and maintainability |
| Returned structure       | Field-by-field description                               |
| DataFrame workflow       | Required columns and transformation notes                |
| Version-specific feature | State version assumptions                                |


## Domain 11 — AI Failure Modes

AI assistants often generate incorrect GAUSS code because they rely on patterns from Python, R, MATLAB, JavaScript, or general pseudocode. The GAUSS Language Expert should help agents identify and avoid these failure modes before producing code.

This domain is not just a list of mistakes. It is a validation layer that every GAUSS-focused coding agent should consult when writing, reviewing, translating, or debugging GAUSS code.

### 11.1 Core Mental Model

Most GAUSS AI failures come from one of four sources:

1. The model invents a function name that sounds plausible.
2. The model imports syntax from another language.
3. The model misunderstands GAUSS data structures.
4. The model writes statistically reasonable logic using invalid GAUSS syntax.

A GAUSS-focused agent should treat generated code as suspicious until it has checked that the syntax, functions, data structures, and workflow are valid GAUSS.

### 11.2 Cross-Language Contamination

Cross-language contamination happens when an agent generates code that looks like Python, R, MATLAB, or JavaScript instead of GAUSS.

Common examples:

* Python-style methods such as `x.append()`, `df.drop()`, or `str.find()`.
* Python-style indexing or slicing.
* R-style formula syntax when the target GAUSS procedure does not support it.
* R-style data frame manipulation.
* MATLAB-style functions or indexing assumptions that are not valid in GAUSS.
* JavaScript-style object or callback syntax.
* Pseudocode written as if it were executable GAUSS.

Agent guidance:

* Do not assume a function exists in GAUSS because it exists in another language.
* Do not translate code mechanically line-by-line.
* Translate the intent of the code into idiomatic GAUSS.
* Verify function names and syntax against official or approved GAUSS sources.
* When translating from another language, explicitly identify language-specific constructs that need to be adapted.

### 11.3 Invented or Incorrect Function Names

AI assistants often invent GAUSS functions by analogy to other languages or by guessing from English descriptions.

Common examples:

* Inventing string functions.
* Inventing DataFrame methods.
* Inventing package manager functions.
* Inventing plotting functions.
* Inventing convenience wrappers that do not exist.
* Using function names from R, Python, MATLAB, or Stata.

Agent guidance:

* Do not invent GAUSS function names.
* Retrieve function names from official documentation, approved examples, or source code.
* If a function name is uncertain, state the uncertainty and provide a safe alternative.
* Prefer simple valid GAUSS code over elegant but unverified code.

### 11.4 String Handling Mistakes

String handling is a common source of AI-generated GAUSS errors.

Known rules:

* Use `strlen` for string length.
* Use `strindx` for string search.
* Remember that `strindx` returns `0` when the substring is not found.
* Do not use Python-style string methods.
* Do not assume R, MATLAB, or JavaScript string functions exist in GAUSS.

Common failure modes:

* Using `length` for string length.
* Inventing `substr`, `strpos`, or `findstr`.
* Treating strings as arrays of characters without verifying the correct GAUSS approach.
* Forgetting to handle the `0` return value from `strindx`.
* Writing file path logic without considering escaping, separators, or platform differences.

Agent checklist for string code:

* Is the function name valid GAUSS?
* Is the return value handled correctly?
* Does the code distinguish between "not found" and a valid position?
* Are file paths and labels handled safely?
* Is the code simpler if built-in GAUSS string utilities are used?

### 11.5 Matrix, Array, and DataFrame Confusion

GAUSS is matrix-oriented, but not every GAUSS data structure behaves like a matrix.

Common failure modes:

* Treating arrays as if `rows` and `cols` apply to them.
* Treating DataFrames exactly like matrices.
* Ignoring variable names and metadata in DataFrames.
* Assuming vectors have no orientation.
* Confusing element-by-element operations with matrix operations.
* Assuming Python NumPy-style indexing.
* Flattening arrays unnecessarily.
* Using matrix-only code for mixed-type tabular data.

Agent guidance:

* Identify the input data structure before writing code.
* Use matrices for numerical computation.
* Use DataFrames when variable names, mixed types, dates, or categoricals matter.
* Use structures for organized outputs and configuration.
* Use arrays for higher-dimensional data.
* Check dimensions before matrix operations.
* Do not assume matrix dimension functions work on arrays.

### 11.6 Procedure and Scope Mistakes

GAUSS procedures require valid procedure structure, local variable handling, and return behavior.

Common failure modes:

* Writing Python-style functions.
* Forgetting `proc` and `endp`.
* Using invalid return syntax.
* Failing to declare local variables.
* Accidentally relying on global state.
* Reusing reserved words as variable names.
* Using `start` or `end` as ordinary variable names.
* Mixing script-style code and reusable procedure code without clear boundaries.

Agent guidance:

* Use `proc ... endp` for procedures.
* Declare local variables inside procedures.
* Avoid reserved keywords and ambiguous names.
* Keep procedure inputs and outputs clear.
* Prefer reusable procedure design when the user asks for code they can adapt.
* Prefer scripts only for simple demonstrations or one-off examples.

### 11.7 Package and Library Mistakes

AI assistants may misunderstand how GAUSS packages, libraries, and source files are organized.

Common failure modes:

* Assuming a package is loaded when it is not.
* Inventing package names.
* Confusing source files, library files, and package manager behavior.
* Writing examples that depend on unavailable packages without saying so.
* Ignoring version compatibility.
* Calling procedures from packages without including required setup instructions.

Agent guidance:

* Clearly state package dependencies.
* Prefer base GAUSS when possible unless the user asks for package-specific code.
* When using package functionality, include the required setup or import steps.
* Distinguish between code that is part of GAUSS and code that comes from a package.
* Check package examples or source code before using package-specific functions.

### 11.8 Output and Printing Mistakes

GAUSS output should be clear, valid, and appropriate for the user's task.

Common failure modes:

* Using print syntax from another language.
* Producing unreadable matrix output.
* Failing to label results.
* Returning output in a format that is hard to use downstream.
* Confusing displayed output with returned values.

Agent guidance:

* Separate computation from presentation when appropriate.
* Label important outputs.
* Return reusable results from procedures.
* Use structures for model results or multi-component outputs.
* Keep beginner examples readable.

### 11.9 Statistical Code with Invalid GAUSS Syntax

A response can be statistically correct but still unusable if the GAUSS code is invalid.

Common failure modes:

* Correct econometric formula, invalid GAUSS implementation.
* Valid model idea, nonexistent GAUSS function.
* Correct matrix equation, wrong matrix dimensions.
* Appropriate statistical workflow, missing data handling ignored.
* Translation from R or Python that preserves statistical meaning but not GAUSS syntax.

Agent guidance:

* Validate the GAUSS implementation separately from the statistical logic.
* Check dimensions, data types, and missing values.
* Prefer explicit steps in educational examples.
* Use official examples when available.
* Do not hide uncertainty behind confident code.

### 11.10 Debugging Checklist for AI-Generated GAUSS Code

Before presenting GAUSS code, an agent should check:

* Are all functions valid GAUSS functions or clearly package-specific?
* Is the syntax GAUSS syntax rather than Python, R, MATLAB, or pseudocode?
* Are procedure definitions valid?
* Are local variables handled appropriately?
* Are reserved keywords avoided?
* Are data structures used correctly?
* Are matrix dimensions compatible?
* Are strings handled with valid GAUSS string functions?
* Are arrays handled with array-appropriate tools?
* Are DataFrames used appropriately when labels or mixed types matter?
* Are package dependencies stated?
* Are missing values considered?
* Is the output usable by the user?
* Would the code run as written, assuming the stated inputs and dependencies?

### 11.11 Recovery Strategy

When an agent detects a possible failure mode, it should recover by:

1. Identifying the questionable syntax, function, or assumption.
2. Checking the appropriate knowledge source.
3. Replacing the invalid pattern with valid GAUSS.
4. Explaining the correction briefly.
5. Adding a small test or usage example when helpful.

The agent should prefer a simpler verified solution over a sophisticated unverified one.


## Domain 12 — Decision Frameworks

Decision frameworks capture the judgment patterns an experienced GAUSS developer uses when choosing among valid approaches.

This domain is especially important for AI agents because many coding tasks do not have a single correct answer. A GAUSS-focused agent should not merely generate syntactically valid code. It should choose an approach that fits the user's goal, data structure, experience level, and likely next steps.

### 12.1 Core Mental Model

A good GAUSS solution should be:

- Correct
- Readable
- Idiomatic
- Appropriate for the user's data structure
- Appropriate for the user's experience level
- Easy to adapt
- Easy to debug
- No more complex than necessary

When multiple approaches are valid, the agent should explain the tradeoff briefly rather than pretending there is only one answer.

### 12.2 Matrix vs DataFrame

Use a matrix when the task is primarily numerical computation.

Prefer a matrix for:

- Linear algebra
- Estimation after data cleaning
- Simulation
- Optimization
- Numerical transformations
- Procedures that expect numeric arrays of values
- Performance-sensitive computation

Use a DataFrame when labels, mixed types, or data management matter.

Prefer a DataFrame for:

- Imported datasets
- Named variables
- Mixed numeric and string columns
- Categorical variables
- Date variables
- Data cleaning
- Exploratory data analysis
- Workflows where preserving variable names matters

Agent decision rule:

- If the user is cleaning, inspecting, importing, or selecting named variables, start with a DataFrame.
- If the user is estimating, optimizing, simulating, or doing matrix algebra, use matrices or extract matrix inputs intentionally.
- If both are needed, show the transition clearly.

Common mistake:

- Treating a DataFrame as if it were just a matrix with column names.

### 12.3 Array vs Matrix

Use a matrix for two-dimensional numerical data.

Use an array for higher-dimensional data.

Prefer a matrix for:

- Ordinary tabular numeric data
- Regression design matrices
- Time series vectors
- Linear algebra
- Most econometric model inputs

Prefer an array for:

- Multi-dimensional simulation results
- Collections of matrices with a shared shape
- Higher-dimensional numerical objects
- Repeated draws, panels, horizons, or scenarios that do not fit naturally into rows and columns

Agent decision rule:

- Do not use arrays just because the problem involves multiple objects.
- Use arrays when the dimensionality itself matters.
- Use structures when the objects are heterogeneous or named.
- Use matrices when the object is fundamentally rectangular and numeric.

Common mistake:

- Using arrays where a structure or matrix would be simpler and clearer.

### 12.4 Structure vs Multiple Return Values

Use a structure when output has named components that belong together.

Prefer a structure for:

- Model results
- Configuration settings
- Diagnostics
- Multiple related outputs
- Public-facing procedure results
- Outputs that users will inspect repeatedly

Prefer multiple return values only when:

- There are very few outputs
- The outputs are obvious and conventional
- The procedure is small or internal
- A structure would add unnecessary complexity

Agent decision rule:

- If a procedure returns more than two or three related outputs, consider a structure.
- If the output will be used by other procedures, prefer a structure with stable field names.
- If the output is instructional and simple, multiple returns may be acceptable.

Common mistake:

- Returning a long list of loosely named outputs that are hard to remember and easy to misuse.

### 12.5 Script vs Procedure

Use a script for a one-off workflow, demonstration, or tutorial.

Use a procedure for reusable logic.

Prefer a script for:

- Simple examples
- Blog demonstrations
- Step-by-step tutorials
- Reproducing an analysis
- Showing users how commands fit together

Prefer a procedure for:

- Repeated tasks
- Package functionality
- Shared utilities
- Testable logic
- Code that accepts inputs and returns outputs
- Anything likely to be reused

Agent decision rule:

- If the user asks "how do I do this once?", a script may be best.
- If the user asks "write a function/procedure", create a procedure.
- If the task may be reused, offer a procedure version.
- For teaching, it can be helpful to show a script first and then refactor into a procedure.

Common mistake:

- Wrapping everything in a procedure too early, making examples harder for beginners to follow.

### 12.6 Procedure vs Package

Use a standalone procedure for local or project-specific reuse.

Use a package when functionality needs to be organized, documented, tested, distributed, or shared.

Prefer a standalone procedure for:

- Small utilities
- Project-specific helpers
- Examples
- Experimental code
- One-file workflows

Prefer a package for:

- Reusable libraries
- Public APIs
- Multiple related procedures
- Documented functionality
- Code that needs examples, tests, and versioning
- Functionality shared across users or projects

Agent decision rule:

- Do not recommend a package structure for a small one-off helper.
- Do recommend package structure when the user is building a reusable tool or library.
- When package structure is recommended, separate public API design from internal helper implementation.

Common mistake:

- Treating every reusable procedure as if it needs to become a package.

### 12.7 Public API vs Helper Procedure

A public API is what users are expected to call directly.

A helper procedure supports implementation but is not the primary user-facing interface.

Public procedures should be:

- Stable
- Clearly named
- Documented
- Validated
- Consistent with related APIs
- Supported by examples and tests

Helper procedures may be:

- Narrower
- More implementation-specific
- Less user-friendly
- Subject to change
- Hidden or clearly marked as internal

Agent decision rule:

- If users are expected to call it, design it carefully.
- If it exists only to reduce duplication internally, keep it focused and avoid over-documenting it as public functionality.
- Avoid exposing implementation details unnecessarily.

Common mistake:

- Creating too many public procedures and making the API harder to learn.

### 12.8 Vectorization vs Loop

Vectorization is often preferred in GAUSS, but readability and correctness matter.

Prefer vectorization when:

- The operation naturally applies to full vectors or matrices
- Built-in matrix operations make the code shorter and clearer
- Performance matters
- The vectorized version is easy to understand

Prefer a loop when:

- The logic is sequential
- Each iteration depends on previous results
- The vectorized version would be obscure
- The code is instructional
- Debugging clarity matters
- The data structure does not fit a clean vectorized operation

Agent decision rule:

- Prefer clear vectorized code when it is natural.
- Do not force vectorization if it makes the code harder to understand.
- For beginners, clarity often matters more than compactness.
- For performance-sensitive code, consider both readability and benchmarking.

Common mistake:

- Assuming loops are always bad or that vectorization is always better.

### 12.9 Built-in Function vs Custom Implementation

Prefer built-in GAUSS functionality when it is available, appropriate, and clear.

Use a custom implementation when:

- No built-in function exists
- The user needs to learn the underlying method
- The workflow requires customization
- The built-in behavior does not match the user's needs
- The code is part of a package where a specialized implementation is justified

Agent decision rule:

- Search official or approved sources before assuming a function does not exist.
- Prefer built-ins for production code when they fit the task.
- For common statistical and econometric workflows, check for native GAUSS procedures before falling back to manual matrix implementations.
- For standard OLS workflows, consider verified built-ins such as `olsmt` when appropriate, and verify exact syntax against official documentation when needed.
- When a native procedure is recommended, provide a concrete example if the syntax is known or retrievable from verified repository or official documentation.
- If exact syntax is uncertain, say retrieval or documentation verification is required.
- Use custom implementations for teaching, customization, diagnostics, or unsupported workflows.
- Do not replace a recommended built-in procedure with only a manual implementation unless the user asks for the underlying mechanics.
- Do not invent a built-in function to avoid writing code.

Common mistake:

- Creating a custom implementation when a reliable built-in function already exists.

### 12.10 Example vs Formal Documentation

Examples and formal documentation serve different purposes.

Use examples when the user needs to understand how to apply something.

Use formal documentation when the user needs complete reference behavior.

Prefer examples for:

- Beginners
- Tutorials
- Blog posts
- Common workflows
- Demonstrating inputs and outputs
- Showing the "happy path"

Prefer formal documentation for:

- API definitions
- Argument descriptions
- Return values
- Edge cases
- Version-specific behavior
- Package reference material

Agent decision rule:

- If the user is learning, start with an example.
- If the user is implementing or debugging, include reference details.
- If writing documentation, include both formal reference and runnable examples when possible.

Common mistake:

- Giving only abstract reference material when the user needs a concrete example.

### 12.11 Beginner Explanation vs Expert Explanation

The agent should adapt explanations to the user's experience level.

For beginners:

- Use concrete examples
- Explain terminology
- Avoid unnecessary abstraction
- Prefer readable code
- Show intermediate outputs when helpful
- Explain why each step matters

For advanced users:

- Be concise
- Emphasize tradeoffs
- Mention edge cases
- Discuss performance or design implications
- Avoid overexplaining basic syntax

Agent decision rule:

- If the user appears new to GAUSS, optimize for clarity.
- If the user is building packages, documentation, or advanced econometric tools, include design considerations.
- When uncertain, provide a clear answer with optional deeper notes.

Common mistake:

- Giving expert-level code to a beginner without explaining the underlying structure.

### 12.12 Retrieval Decision Rules

A GAUSS-focused agent should know when to retrieve knowledge instead of relying on memory.

Retrieve official documentation when:

- Function syntax matters
- Argument names matter
- Return values matter
- Version-specific behavior matters
- The agent is unsure whether a function exists

Retrieve LLM reference material when:

- Avoiding common AI mistakes
- Checking language idioms
- Validating known failure-prone patterns
- Reviewing generated code for hallucinations

Retrieve blog examples when:

- The user needs an applied workflow
- A tutorial-style example would help
- The task resembles a published example
- The user is learning a concept

Retrieve package source when:

- The user asks about package internals
- A function belongs to a package
- Official documentation is insufficient
- Implementation behavior matters

Agent decision rule:

- Retrieval is required when the cost of being wrong is high.
- Retrieval is preferred when syntax or function availability is uncertain.
- Retrieval is optional when the task is conceptual or the answer is stable and simple.

Common mistake:

- Answering confidently from memory when the correct answer depends on exact GAUSS syntax.

### 12.13 Decision Checklist

Before choosing an implementation approach, the agent should ask:

- What is the user's goal?
- Is this a one-off task or reusable code?
- What data structure is the user starting with?
- Are variable names, labels, dates, or categories important?
- Is the user learning, debugging, optimizing, or building production code?
- Is there a reliable built-in function?
- Does this require package-specific functionality?
- Should the output be returned, printed, saved, or documented?
- Does the solution need to be beginner-friendly?
- Are there version-specific concerns?
- Should official documentation or source code be retrieved?

### 12.14 Preferred Default Choices

When the user does not provide enough detail, the agent should use conservative defaults:

| Situation | Preferred Default |
|---|---|
| Simple demonstration | Script |
| Reusable logic | Procedure |
| Numerical computation | Matrix |
| Imported mixed-type data | DataFrame |
| Multiple named outputs | Structure |
| Higher-dimensional numeric data | Array |
| Teaching task | Clear example first |
| Production task | Validated procedure with input checks |
| Uncertain function syntax | Retrieve documentation |
| Uncertain package behavior | Retrieve package source or examples |

## Domain 13 — Best Practices

Best practices capture the coding habits, design preferences, and maintenance standards that help GAUSS code remain readable, reliable, reusable, and teachable.

This domain should guide agents when writing new GAUSS code, reviewing user code, translating from other languages, or suggesting improvements.

### 13.1 Core Mental Model

Good GAUSS code should be:

- Correct
- Readable
- Explicit
- Reusable when appropriate
- Easy to test
- Easy to debug
- Consistent with GAUSS idioms
- Appropriate for the user's experience level
- Clear about assumptions, inputs, and outputs

A GAUSS-focused agent should prefer code that a user can understand, modify, and trust.

### 13.2 Naming Conventions

Names should make the purpose of variables, procedures, and structures clear.

Preferred practices:

- Use descriptive names for public procedures.
- Use short names only when they are conventional or local.
- Avoid names that conflict with GAUSS keywords.
- Avoid ambiguous names such as `data`, `temp`, or `result` when more specific names would be clearer.
- Use consistent naming patterns across related procedures.
- Use names that reflect the data structure when helpful, such as `y`, `x`, `x_mat`, `df`, `results`, or `ctl`.

Agent guidance:

- Prioritize clarity over cleverness.
- Avoid using `start` and `end` as variable names.
- Avoid names borrowed from another language's conventions if they make the GAUSS code less clear.
- Use procedure names that describe actions or returned results.

Common failure modes:

- Using reserved words as identifiers.
- Creating overly generic variable names.
- Using inconsistent names across examples.
- Using Python, R, or MATLAB naming assumptions without adapting them to GAUSS.

### 13.3 Readable Code

Readable code is easier to teach, debug, review, and maintain.

Preferred practices:

- Keep examples short when teaching.
- Separate logical steps with comments or whitespace.
- Avoid deeply nested logic when a simpler structure is possible.
- Use intermediate variables when they clarify intent.
- Prefer explicit data preparation steps before estimation or analysis.
- Keep computation and presentation separate when appropriate.

Agent guidance:

- For beginners, prioritize readability over compactness.
- For advanced users, still avoid unnecessary cleverness.
- When code is dense, explain the key lines.
- Do not over-comment obvious syntax, but do comment assumptions and non-obvious decisions.

Common failure modes:

- Producing overly compact code that is hard to modify.
- Hiding important data transformations.
- Combining data cleaning, estimation, and printing in one unclear block.
- Writing code that looks elegant but is difficult to debug.

### 13.4 Reusable Procedures

Reusable procedures should have clear inputs, outputs, and assumptions.

Preferred practices:

- Use `proc ... endp` for reusable logic.
- Declare local variables inside procedures.
- Validate important inputs.
- Return useful outputs rather than only printing results.
- Keep procedures focused on one main responsibility.
- Use helper procedures to reduce duplication when appropriate.
- Document expected input shapes and types.

Agent guidance:

- If code will be reused, write a procedure.
- If code is only a demonstration, a script may be better.
- When writing a procedure, include a small usage example.
- For multi-component results, consider returning a structure.

Common failure modes:

- Writing a procedure that depends on hidden global variables.
- Printing output but not returning values.
- Returning too many separate outputs.
- Failing to document expected input dimensions.
- Making one procedure responsible for too many tasks.

### 13.5 Input Validation

Input validation prevents confusing errors and makes code safer to reuse.

Preferred practices:

- Check dimensions before matrix operations.
- Check that required inputs are present.
- Check that inputs are the expected type or structure when possible.
- Validate optional inputs and defaults.
- Handle missing values intentionally.
- Provide clear error messages when assumptions are violated.

Agent guidance:

- Include validation for reusable or production-oriented code.
- Keep validation lighter in short teaching examples unless the validation itself is relevant.
- Explain what assumptions are being checked.
- Do not silently coerce data in ways that could surprise the user.

Common failure modes:

- Assuming matrix dimensions are compatible.
- Ignoring missing values.
- Letting low-level errors occur when a clearer input check would help.
- Overcomplicating beginner examples with too much validation.

### 13.6 Clear Error Messages

Error messages should help the user understand and fix the problem.

Preferred practices:

- State what went wrong.
- State what was expected.
- Include relevant dimensions, names, or input conditions when helpful.
- Avoid vague messages such as "invalid input" when a more specific message is possible.
- Keep messages concise.

Agent guidance:

- For reusable procedures, prefer informative error messages.
- For debugging help, explain the likely source of the error.
- When the exact cause is uncertain, identify the most likely causes and how to check them.

Common failure modes:

- Returning cryptic errors.
- Hiding the real cause of the problem.
- Failing to distinguish between syntax errors, dimension errors, and data problems.

### 13.7 Output Design

Outputs should be useful for both humans and downstream code.

Preferred practices:

- Return values that users can reuse.
- Use structures for named multi-component outputs.
- Label printed output clearly.
- Separate computation from display when appropriate.
- Preserve variable names or metadata when useful.
- Keep output formats consistent across related procedures.

Agent guidance:

- For analysis scripts, printed output may be appropriate.
- For reusable procedures, returned output is usually more important.
- For model results, consider a structure with named fields.
- When teaching, show both the returned object and how to inspect it.

Common failure modes:

- Printing results without returning them.
- Returning unlabeled matrices that are hard to interpret.
- Changing output structure across similar examples.
- Losing useful metadata unnecessarily.

### 13.8 Documentation Standards

Documentation should help users understand purpose, inputs, outputs, assumptions, and examples.

Preferred practices:

- Start with what the code does and when to use it.
- Document inputs and expected dimensions.
- Document outputs and their interpretation.
- Include a simple runnable example.
- Mention package dependencies.
- Mention important assumptions.
- Keep examples realistic but not overly complex.

Agent guidance:

- For public procedures, include formal documentation.
- For examples, include enough explanation for the target audience.
- For advanced procedures, document edge cases and limitations.
- Avoid documentation that only restates the procedure name.

Common failure modes:

- Missing input shape information.
- Missing example usage.
- Failing to explain returned structures.
- Writing documentation that is too abstract for users to apply.

### 13.9 Testing Philosophy

Tests should protect correctness, prevent regressions, and clarify expected behavior.

Preferred practices:

- Test normal cases.
- Test edge cases.
- Test dimension mismatches when relevant.
- Test missing value behavior when relevant.
- Test optional arguments and defaults.
- Test error paths for reusable procedures.
- Use small examples with known expected results.

Agent guidance:

- When generating reusable code, suggest at least one basic test.
- For numerical code, include tolerance-based checks when appropriate.
- For package code, separate examples from tests.
- Use tests to document expected behavior.

Common failure modes:

- Only testing the happy path.
- Testing output visually instead of programmatically.
- Ignoring edge cases around empty inputs, missing values, or dimensions.
- Failing to test optional argument behavior.

### 13.10 Backward Compatibility

Backward compatibility matters when code is used by others or distributed in packages.

Preferred practices:

- Avoid breaking public APIs without a clear reason.
- Preserve existing argument names when practical.
- Add optional functionality without changing default behavior when possible.
- Document behavior changes.
- Consider version-specific GAUSS features before using them.
- Avoid relying on features unavailable to the target user base.

Agent guidance:

- Ask or infer the target GAUSS version when version compatibility matters.
- Prefer broadly supported syntax unless the user requests newer functionality.
- Clearly mark code that depends on a newer GAUSS version or package version.

Common failure modes:

- Changing procedure signatures unnecessarily.
- Using newer features without warning.
- Breaking examples or tests when refactoring.
- Assuming all users are on the latest GAUSS version.

### 13.11 Package Maintainability

Package code should be organized for long-term use, not just immediate execution.

Preferred practices:

- Keep public APIs stable and documented.
- Keep internal helpers focused.
- Organize examples separately from core source code.
- Include tests for important behavior.
- Document dependencies.
- Avoid unnecessary global state.
- Keep naming consistent across the package.
- Maintain a clear release process.

Agent guidance:

- For package-related tasks, think beyond the single procedure.
- Consider documentation, tests, examples, and API consistency.
- Avoid exposing internal helpers as public APIs unless necessary.
- Prefer incremental changes that are easy to review.

Common failure modes:

- Treating package code like a one-off script.
- Mixing examples and source logic.
- Creating public functions without documentation.
- Adding functionality without tests.

### 13.12 Beginner-Friendly Code

Beginner-friendly code should be simple, explicit, and easy to modify.

Preferred practices:

- Use concrete data examples.
- Show each step clearly.
- Avoid unnecessary abstraction.
- Explain key syntax.
- Keep procedure design simple.
- Prefer readable variable names.
- Show expected output when helpful.

Agent guidance:

- Do not optimize prematurely for beginners.
- Avoid dense one-liners.
- Explain why the data structure was chosen.
- Make assumptions visible.

Common failure modes:

- Giving advanced package-style code to a beginner.
- Overusing abstraction.
- Skipping setup steps.
- Assuming knowledge of matrix dimensions, DataFrames, or procedures.

### 13.13 Advanced Code

Advanced code should emphasize design tradeoffs, correctness, performance, and maintainability.

Preferred practices:

- Discuss API design.
- Consider performance and memory.
- Include validation and tests.
- Separate public and internal logic.
- Document assumptions and edge cases.
- Prefer robust design over clever code.

Agent guidance:

- Match the user's level and goal.
- If the user is building production or package code, include design considerations.
- Explain tradeoffs when there are multiple valid approaches.
- Include tests or review criteria.

Common failure modes:

- Providing simple tutorial code when the user needs package-ready code.
- Ignoring performance implications.
- Failing to discuss API stability.
- Omitting validation for reusable code.

### 13.14 Code Review Guidance

A GAUSS code review should check correctness, clarity, maintainability, and fit for purpose.

Review checklist:

- Does the code use valid GAUSS syntax?
- Are all functions valid GAUSS functions or stated package dependencies?
- Are data structures appropriate?
- Are dimensions handled correctly?
- Are missing values handled intentionally?
- Are procedure inputs and outputs clear?
- Are local variables declared?
- Are reserved words avoided?
- Is output reusable and clearly labeled?
- Are examples or tests included when needed?
- Is the code understandable for the intended audience?

Agent guidance:

- Prioritize correctness first.
- Separate blocking issues from style suggestions.
- Explain why a change matters.
- Suggest concrete fixes.
- Avoid overwhelming the user with too many minor comments at once.

### 13.15 Best Practice Checklist

Before producing GAUSS code, the agent should check:

- Is the chosen data structure appropriate?
- Is the code valid GAUSS rather than borrowed syntax?
- Are functions verified or clearly package-specific?
- Are inputs and outputs clear?
- Are dimensions and missing values considered?
- Is the code readable for the target audience?
- Is a script or procedure more appropriate?
- Should the output be a structure?
- Are package dependencies stated?
- Would a small example or test make the answer better?

## Domain 14 — Teaching and Support

Teaching and support are the practices of helping users understand GAUSS concepts, solve problems, correct misunderstandings, and become more independent over time.

This domain helps GAUSS-focused agents respond like experienced instructors and support engineers, not just code generators.

### 14.1 Core Mental Model

A good GAUSS teaching or support response should help the user make progress now while also improving their understanding for next time.

The agent should balance:

* Immediate usefulness
* Conceptual clarity
* Correct GAUSS syntax
* Appropriate detail level
* User confidence
* Long-term learning

Agent guidance:

* Start from the user’s goal.
* Identify what the user already understands.
* Explain the smallest concept needed to move forward.
* Provide runnable code when helpful.
* Avoid overwhelming the user with unnecessary theory.
* Correct misunderstandings directly but respectfully.
* Connect syntax to purpose.

Common failure modes:

* Giving only code with no explanation.
* Giving too much theory before solving the user’s problem.
* Assuming the user understands matrices, procedures, DataFrames, or packages.
* Correcting the user in a way that feels dismissive.
* Answering the literal question while missing the underlying confusion.

### 14.2 Explaining Concepts Progressively

Progressive explanation means starting simple and adding complexity only when needed.

Preferred pattern:

1. State the concept in plain language.
2. Show a small example.
3. Explain the key line or idea.
4. Connect it to the user’s task.
5. Mention advanced details only if useful.

Agent guidance:

* Use simple examples before abstract descriptions.
* Avoid introducing multiple new concepts at once.
* Use familiar data shapes when possible.
* Define terminology when the user may be new.
* Move from script examples to procedures only when reuse matters.

Common failure modes:

* Starting with expert-level abstractions.
* Explaining every edge case before the basic idea.
* Using examples that are too large.
* Introducing packages, structures, and advanced options before the user needs them.

### 14.3 Diagnosing User Misunderstandings

Users often ask about symptoms rather than root causes.

Common misunderstandings include:

* Thinking every table-like object should be a matrix.
* Confusing DataFrames and matrices.
* Confusing arrays and matrices.
* Treating categorical codes as meaningful numeric values.
* Ignoring row and column orientation.
* Assuming a procedure is available without loading a package.
* Interpreting a dimension mismatch as a statistical problem.
* Treating missing values as zeros.
* Assuming code that runs is statistically correct.
* Assuming output printed to screen is the same as reusable returned output.

Agent guidance:

* Look for the underlying misconception.
* Explain the misconception briefly.
* Show the corrected mental model.
* Provide a concrete fix.
* Avoid overwhelming the user with unrelated corrections.
* When useful, ask the user to check dimensions, types, or package setup.

Common failure modes:

* Fixing code without addressing the misunderstanding.
* Overcorrecting with a full rewrite.
* Treating the user’s misunderstanding as carelessness.
* Giving an answer that solves only the immediate symptom.

### 14.4 Choosing Examples

Examples should match the user’s goal, experience level, and context.

Good examples are:

* Small enough to understand
* Realistic enough to transfer
* Runnable
* Focused on one main idea
* Clear about inputs and outputs
* Free of hidden setup
* Easy to modify

Agent guidance:

* Use generated data for self-contained teaching examples.
* Use the user’s data structure when they provide one.
* Use DataFrames when teaching imported or labeled data workflows.
* Use matrices when teaching numerical computation.
* Keep beginner examples short.
* Use more realistic examples when teaching applied econometric workflows.

Common failure modes:

* Using toy examples that do not map to the user’s real task.
* Using complex examples that obscure the concept.
* Omitting setup steps.
* Giving examples that depend on unavailable files or packages.
* Changing the user’s data structure without explaining why.

### 14.5 Helping Beginners

Beginners need clarity, structure, and reassurance.

Preferred practices:

* Use plain language.
* Explain one thing at a time.
* Show complete runnable snippets.
* Avoid dense one-liners.
* Explain key syntax.
* Show how to inspect intermediate results.
* State assumptions clearly.
* Avoid unnecessary package or API complexity.

Agent guidance:

* Assume the user may not know matrix orientation.
* Explain why a DataFrame or matrix is being used.
* Show expected output when helpful.
* Use comments sparingly but meaningfully.
* Offer the next small step rather than a large roadmap.

Common failure modes:

* Providing production-style code for a beginner task.
* Assuming knowledge of procedures, structures, or packages.
* Using unexplained statistical notation.
* Skipping the setup or data inspection step.
* Giving too many alternatives at once.

### 14.6 Supporting Advanced Users

Advanced users often need precision, tradeoffs, and edge cases rather than basic explanation.

Preferred practices:

* Be concise.
* Focus on design choices.
* Discuss assumptions and limitations.
* Mention performance implications.
* Mention version or package compatibility when relevant.
* Provide tests or validation checks.
* Distinguish statistical logic from GAUSS implementation.

Agent guidance:

* Do not overexplain basic syntax.
* Provide specific recommendations.
* Discuss tradeoffs when multiple valid approaches exist.
* Include edge cases when they affect correctness.
* Respect the user’s existing expertise.

Common failure modes:

* Giving a beginner tutorial when the user needs API design.
* Ignoring performance or maintainability concerns.
* Failing to discuss edge cases.
* Giving generic advice instead of GAUSS-specific guidance.

### 14.7 Translating from Other Languages

Many users approach GAUSS from Python, R, MATLAB, Stata, or other statistical environments.

Teaching translation requires explaining both the code conversion and the conceptual shift.

Agent guidance:

* Translate the intent, not just the syntax.
* Identify language-specific patterns that do not carry over.
* Replace foreign idioms with GAUSS idioms.
* Explain differences in data structures.
* Watch for indexing, formula syntax, method calls, and package assumptions.
* Provide a GAUSS-native version rather than a line-by-line imitation when appropriate.

Common failure modes:

* Mechanical translation that produces invalid GAUSS.
* Carrying over Python methods, R formulas, or MATLAB functions.
* Ignoring DataFrame vs matrix differences.
* Failing to explain why the GAUSS version is structured differently.

### 14.8 Connecting Code to Statistical or Numerical Intuition

Many GAUSS users are solving statistical, econometric, or numerical problems.

Good explanations should connect implementation details to the analytical goal.

Agent guidance:

* Explain what the code is estimating, transforming, testing, or computing.
* Distinguish statistical model logic from programming syntax.
* Explain matrix dimensions in terms of observations and variables when helpful.
* Mention assumptions such as sorting, missing values, or sample alignment.
* Use statistical notation only when it helps the user.

Common failure modes:

* Providing code without explaining the statistical meaning.
* Explaining statistical theory while ignoring code correctness.
* Confusing model specification with implementation details.
* Ignoring sample alignment, missing values, or sorting.

### 14.9 Support Response Pattern

A support-oriented GAUSS response should usually follow this shape:

1. Identify the likely issue or goal.
2. Give the immediate fix or next step.
3. Explain why it works.
4. Provide corrected GAUSS code when useful.
5. Add one validation check.
6. Mention a related best practice only if it helps.

Agent guidance:

* Lead with the practical answer.
* Keep the first response focused.
* Avoid turning every support response into a tutorial.
* Save broad refactoring advice until after the immediate problem is solved.
* Be transparent about assumptions.

Common failure modes:

* Giving a long lecture before the fix.
* Providing many possible causes without prioritizing the likely one.
* Rewriting the user’s code unnecessarily.
* Omitting a validation step.

### 14.10 Teaching Response Pattern

A teaching-oriented GAUSS response should usually follow this shape:

1. State the concept simply.
2. Show a small runnable example.
3. Explain the example.
4. Connect it to the user’s task.
5. Mention a common mistake.
6. Suggest one next step.

Agent guidance:

* Use examples before abstractions.
* Keep explanations short and cumulative.
* Avoid introducing several concepts at once.
* Use the user’s context when available.
* Reinforce the correct mental model.

Common failure modes:

* Explaining too much at once.
* Using abstract examples with no connection to the user’s task.
* Skipping the common mistake that caused the confusion.
* Offering too many next steps.

### 14.11 Tone and User Experience

Support and teaching tone should be clear, respectful, and confidence-building.

Preferred tone:

* Direct
* Patient
* Practical
* Encouraging
* Honest about uncertainty
* Focused on the user’s goal

Agent guidance:

* Correct errors without making the user feel foolish.
* Avoid overconfidence when syntax or version behavior is uncertain.
* Say when documentation or source retrieval is needed.
* Explain assumptions.
* Keep answers proportional to the user’s question.

Common failure modes:

* Sounding condescending.
* Being overly verbose for a simple fix.
* Being too terse for a beginner.
* Hiding uncertainty.
* Making unsupported claims.

### 14.12 Escalation and Clarifying Questions

Sometimes the agent needs more information, but it should avoid unnecessary delays.

Ask for clarification when:

* The exact error message is needed.
* The data structure is unknown and affects the solution.
* GAUSS version matters.
* Package availability matters.
* The user’s goal is ambiguous.
* The code snippet is incomplete.

Proceed with assumptions when:

* A simple answer is possible.
* The likely issue is clear.
* The user needs immediate progress.
* The missing detail can be stated as an assumption.
* The agent can provide a safe general pattern.

Agent guidance:

* Ask one focused question when needed.
* Do not ask for information already provided.
* Provide a provisional answer when useful.
* State assumptions clearly.
* Explain what information would confirm the diagnosis.

Common failure modes:

* Asking too many questions before helping.
* Guessing when exact syntax or package behavior matters.
* Failing to state assumptions.
* Ignoring information already provided.

### 14.13 Teaching and Support Checklist

Before responding to a GAUSS teaching or support question, the agent should check:

* What is the user trying to accomplish?
* Is the user asking to learn, debug, translate, optimize, or build reusable code?
* What is the likely experience level?
* What data structure is involved?
* Is there a likely misconception?
* Does the response need code, explanation, or both?
* Should the code be a script or procedure?
* Are setup steps or package dependencies needed?
* Is a small example useful?
* Is a validation check useful?
* Should the response avoid unnecessary advanced detail?
* Is the tone clear, respectful, and practical?

### 14.14 Preferred Teaching and Support Defaults

When the user does not provide enough context, the agent should use these defaults:

| Situation                     | Preferred Default                                    |
| ----------------------------- | ---------------------------------------------------- |
| Beginner syntax question      | Plain explanation plus small example                 |
| Debugging question            | Likely cause, minimal fix, corrected code            |
| Translation question          | GAUSS-native translation plus differences            |
| Statistical workflow question | Code plus analytical explanation                     |
| Package question              | State dependency assumptions                         |
| Data structure confusion      | Explain matrix/DataFrame/array/structure distinction |
| Unclear experience level      | Start simple, add optional advanced note             |
| Unclear error                 | Ask for exact error but provide likely checks        |
| Reusable code request         | Procedure plus usage example                         |
| One-off task                  | Script or focused snippet                            |

## Using This Body of Knowledge

The GAUSS Language Body of Knowledge is not intended to be read as a linear manual. It is a reasoning map for GAUSS-focused agents.

Agents should use it to:

- Identify the relevant knowledge domain for a task.
- Select the right expert reasoning pattern.
- Avoid common GAUSS-specific mistakes.
- Decide when retrieval from official sources is required.
- Choose an appropriate implementation strategy.
- Match explanations to the user's experience level.
- Review generated code before presenting it.

### Task-to-Domain Routing

| User Task | Primary Domains |
|---|---|
| Write new GAUSS code | Domains 1, 2, 3, 12, 13 |
| Debug GAUSS code | Domains 7, 11, 2, 3 |
| Translate from Python/R/MATLAB | Domains 11, 1, 2, 12 |
| Write reusable procedure | Domains 3, 13, 6 |
| Review package code | Domains 6, 9, 13, 7 |
| Improve performance | Domains 8, 5, 2 |
| Explain a GAUSS concept | Domains 14, 1, 2 |
| Write documentation | Domains 10, 3, 13 |
| Work with numerical algorithms | Domains 5, 8, 4 |
| Work with packages | Domains 9, 6, 10 |
| Choose data structure | Domains 2, 12 |
| Avoid hallucinated syntax | Domains 11, 4 |

### Retrieval Triggers

Agents should retrieve from official or approved knowledge sources when:

- Exact function syntax matters.
- Argument names or return values matter.
- Version-specific behavior matters.
- A function might be package-specific.
- The agent is unsure whether a function exists.
- The user asks for documentation-quality accuracy.
- The generated code uses a failure-prone area such as strings, arrays, DataFrames, packages, or optimization.
- The task involves modifying package source code or public APIs.

### Validation Triggers

Agents should validate generated GAUSS code especially carefully when it includes:

- Procedure definitions
- Optional arguments or control structures
- Matrix multiplication or concatenation
- DataFrame-to-matrix conversion
- Array dimensions
- String functions
- Package-specific procedures
- Missing value handling
- Time series or panel transformations
- Numerical optimization
- Public API design

### Preferred Response Pattern

When generating GAUSS code, agents should usually follow this pattern:

1. State the approach.
2. Provide valid GAUSS code.
3. Explain important assumptions.
4. Explain key lines or design choices.
5. Include a small usage example or validation step when helpful.
6. Mention package or version dependencies when relevant.

### Preferred Review Pattern

When reviewing GAUSS code, agents should usually follow this pattern:

1. Identify blocking correctness issues.
2. Identify likely GAUSS syntax or function problems.
3. Check data structure and dimension assumptions.
4. Check package dependencies.
5. Suggest targeted fixes.
6. Mention maintainability, documentation, or tests only after correctness issues.

### Preferred Debugging Pattern

When debugging GAUSS code, agents should usually follow this pattern:

1. Identify the likely failure category.
2. Explain why the issue occurs.
3. Provide the smallest useful fix.
4. Provide corrected code.
5. Suggest one validation check.
6. Offer a cleaner refactor only if it helps.

### Preferred Teaching Pattern

When teaching GAUSS concepts, agents should usually follow this pattern:

1. Explain the concept in plain language.
2. Show a small runnable example.
3. Explain the example.
4. Mention one common mistake.
5. Suggest one next step.

### Maintenance Notes

This Body of Knowledge should be updated when:

- A recurring AI failure mode is discovered.
- A new GAUSS feature changes best practices.
- A package introduces a common workflow.
- User support questions reveal a repeated misunderstanding.
- Evaluations show a recurring agent weakness.
- Documentation or examples reveal a better pattern.

The Body of Knowledge should capture expert judgment, not duplicate official documentation.

## Expertise Levels

Each topic may be classified by level:

| Level | Description |
|---|---|
| L100 | Beginner: basic concepts and simple usage |
| L200 | Intermediate: practical coding patterns |
| L300 | Advanced: reusable procedures, packages, and debugging |
| L400 | Expert: performance, design tradeoffs, and edge cases |
| L500 | Framework-level: language design, agent design, and expert judgment |
