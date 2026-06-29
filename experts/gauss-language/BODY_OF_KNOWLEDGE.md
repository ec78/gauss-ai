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

### Domain 11 — AI Failure Modes

Common ways AI assistants generate incorrect GAUSS code.

Topics:

- Cross-language contamination
- Hallucinated functions
- Python syntax in GAUSS
- R syntax in GAUSS
- MATLAB syntax in GAUSS
- Incorrect string functions
- Incorrect assumptions about arrays
- Matrix/DataFrame confusion
- Invented packages
- Incorrect documentation references

### Domain 12 — Decision Frameworks

Judgment rules for choosing among valid GAUSS approaches.

Topics:

- Matrix vs DataFrame
- Array vs structure
- Script vs procedure
- Procedure vs package
- Public API vs helper function
- Vectorization vs loop
- Built-in function vs custom implementation
- Example vs formal documentation
- Beginner explanation vs expert explanation

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