# GAUSS Language Body of Knowledge

## Knowledge Domains

The GAUSS Language Expert is organized around the following domains.

### Domain 1 — Language Fundamentals

Core knowledge required to write valid GAUSS programs.

Topics:

- Language philosophy
- Matrix-oriented programming
- Source files
- Interactive execution
- Scripts and programs
- Variables
- Naming
- Reserved keywords
- Expressions
- Operators
- Control flow
- Procedures
- Scope
- Compilation
- Includes
- Libraries

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

### Domain 3 — Procedures and APIs

Core knowledge for writing reusable GAUSS procedures and public-facing APIs.

Topics:

- Procedure definitions
- Inputs
- Outputs
- Local variables
- Optional arguments
- Keyword arguments
- Return values
- Error handling
- Input validation
- API consistency
- Helper procedures
- Public vs internal procedures

### Domain 4 — Standard Library Awareness

Core knowledge about GAUSS built-in functionality and when to retrieve official documentation.

Topics:

- Linear algebra
- Statistics
- Optimization
- Time series
- Machine learning
- Strings
- File I/O
- Graphics
- Dates
- Random numbers
- Data management
- Utilities

### Domain 5 — Numerical Computing

Core knowledge for reliable numerical and statistical programming.

Topics:

- Matrix algebra
- Numerical precision
- Numerical stability
- Conditioning
- Missing values in numerical operations
- Performance tradeoffs
- Large datasets
- Simulation
- Reproducibility

### Domain 6 — Software Engineering

Core knowledge for building maintainable GAUSS projects.

Topics:

- Project organization
- Package architecture
- Public APIs
- Internal APIs
- Tests
- Examples
- Documentation
- Version compatibility
- Release process
- Code review

### Domain 7 — Debugging

Core knowledge for diagnosing and correcting GAUSS code.

Topics:

- Syntax errors
- Runtime errors
- Logic errors
- Dimension mismatches
- Type mismatches
- Missing value problems
- Package and library loading errors
- Performance debugging
- Numerical debugging

### Domain 8 — Performance Engineering

Core knowledge for writing efficient GAUSS code.

Topics:

- Vectorization
- Loops
- Preallocation
- Memory allocation
- Copies
- Views
- Matrix operations
- Benchmarking
- Readability vs performance

### Domain 9 — Package Ecosystem

Core knowledge about GAUSS packages and libraries.

Topics:

- Package manager
- Package structure
- Dependencies
- Library files
- Source files
- Examples
- Tests
- Documentation
- Versioning
- Distribution

### Domain 10 — Documentation and Examples

Core knowledge for explaining GAUSS code clearly.

Topics:

- API documentation
- Sphinx documentation
- `.rst` files
- Inline comments
- Examples
- Tutorials
- Blog-style explanations
- Beginner-friendly explanations
- Advanced reference material

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
- Use custom implementations for teaching, customization, or unsupported workflows.
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

### Domain 13 — Best Practices

Preferred patterns for GAUSS programming.

Topics:

- Naming conventions
- Readable code
- Reusable procedures
- Input validation
- Clear error messages
- Consistent outputs
- Testing philosophy
- Documentation standards
- Backward compatibility
- Package maintainability

### Domain 14 — Teaching and Support

Knowledge for helping users learn and troubleshoot GAUSS.

Topics:

- Explaining concepts progressively
- Diagnosing user misunderstandings
- Choosing simple examples
- Translating from other languages
- Helping beginners
- Supporting advanced users
- Connecting code to statistical intuition
- Avoiding overcomplicated answers

## Expertise Levels

Each topic may be classified by level:

| Level | Description |
|---|---|
| L100 | Beginner: basic concepts and simple usage |
| L200 | Intermediate: practical coding patterns |
| L300 | Advanced: reusable procedures, packages, and debugging |
| L400 | Expert: performance, design tradeoffs, and edge cases |
| L500 | Framework-level: language design, agent design, and expert judgment |