"""Deterministic GAUSS execution-error catalog.

The catalog is intentionally small. It records only GAUSS error identifiers
this repository has verified evidence for -- reproduced against a real GAUSS
runtime, already present in this repository's own execution evidence, or
verified against official GAUSS/Aptech documentation -- and is designed so
new identifiers can be added without changing interpreter control flow.

Every entry carries its own `verification_status`/`verification_source` so a
caller (or a human reader of `docs/gauss-error-catalog.md`) can see exactly
why this repository trusts a given explanation, rather than treating every
cataloged code as equally certain. When documentation and observed runtime
text disagree, runtime evidence is treated as authoritative for `title`/
`generic_explanation`, and the disagreement is recorded in
`documentation_discrepancy` rather than silently discarded (see `G0036`).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class GaussErrorCategory(enum.Enum):
    PARSE_SYNTAX = "parse_syntax"
    RUNTIME_COMPUTATION = "runtime_computation"
    MATRIX_DIMENSION = "matrix_dimension"
    NUMERICAL = "numerical"
    FILE_IO = "file_io"
    PACKAGE_OR_LIBRARY = "package_or_library"
    STARTUP_OR_LICENSING = "startup_or_licensing"
    USER_INTERRUPTION = "user_interruption"
    TIMEOUT = "timeout"
    #: v0.55.0 -- an index/subscript value fell outside an object's valid
    #: bounds. Distinct from MATRIX_DIMENSION, which covers two operands
    #: disagreeing with each other, not a single index against one object.
    INDEXING_SUBSCRIPT = "indexing_subscript"
    #: v0.55.0 -- a procedure or built-in function call supplied an
    #: unexpected number of arguments, or an argument value outside a
    #: required range (e.g. a required-positive constraint). Covers both
    #: "procedure invocation" and "argument count or argument type" failure
    #: shapes named in this milestone's own scope.
    ARGUMENT_VALIDATION = "argument_validation"
    #: v0.55.0 -- an operation received an operand or argument of an
    #: unexpected type (e.g. a string where a numeric value was expected).
    TYPE_MISMATCH = "type_mismatch"
    UNKNOWN = "unknown"


class VerificationStatus(enum.Enum):
    """How a catalog entry's meaning was established. An entry may carry more
    than one status (e.g. both REAL_RUNTIME and OFFICIAL_DOCUMENTATION) when
    independently corroborated by more than one source."""

    REAL_RUNTIME = "real_runtime"
    OFFICIAL_DOCUMENTATION = "official_documentation"
    REPOSITORY_EVIDENCE = "repository_evidence"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class GaussErrorCatalogEntry:
    error_code: str
    category: GaussErrorCategory
    title: str
    generic_explanation: str
    execution_phase: str
    confidence: str
    recommended_next_step: str
    #: One or more sources this entry's meaning is grounded in. Never empty
    #: for a real catalog entry -- an entry with no verifiable source does
    #: not belong in this catalog at all.
    verification_status: tuple[VerificationStatus, ...]
    #: Human-readable citation(s) -- which planning/evaluation document, real
    #: invocation, or documentation URL this entry's wording is grounded in.
    verification_source: str
    #: Set only when official documentation and observed runtime evidence
    #: disagree. Runtime evidence still wins for `title`/`generic_explanation`
    #: above; this field records the disagreement rather than hiding it.
    documentation_discrepancy: str | None = None
    #: v0.54.0 -- verified diagnostic knowledge, consumed by
    #: `gauss_execution_diagnostics.py`. Each string is a short, evidence-
    #: grounded description of a situation known (from real runtime evidence
    #: or official documentation, same as this entry's own
    #: `verification_status`) to trigger this error code. These are
    #: *plausible causes*, never a confirmed diagnosis -- the diagnostic
    #: engine never ranks any of them above `low` confidence on its own,
    #: since none of them is distinguishable from the others without
    #: evidence this catalog does not carry (source code content, variable
    #: values, matrix shapes). Empty for an entry with no verified trigger
    #: knowledge yet -- never padded with a generic programming guess.
    known_triggers: tuple[str, ...] = ()
    #: Bounded, closed-ended questions a user could answer to help narrow
    #: down which of `known_triggers` applies. Never an open-ended "what
    #: does your code do?" -- always something answerable from the user's
    #: own knowledge of their script.
    diagnostic_questions: tuple[str, ...] = ()
    #: What evidence (beyond what the interpreter's `ExecutionEvidence`
    #: already carries) would be needed to raise cause-level confidence
    #: above `low` for this code -- e.g. source text, operand shapes. Never
    #: a promise that this repository can currently collect that evidence
    #: automatically.
    required_evidence_for_diagnosis: tuple[str, ...] = ()
    #: v0.56.0 -- verified repair-planning knowledge, consumed by
    #: `gauss_repair_planner.py`. Each string is a bounded, evidence-grounded
    #: *inspection strategy* -- never replacement code, never a specific edit,
    #: never an unverified GAUSS API. Distinct from `known_triggers`: a
    #: trigger explains a plausible *cause*; a repair strategy describes what
    #: a human should *inspect or decide* before any edit is made. Empty for
    #: an entry with no authored repair guidance yet.
    repair_strategies: tuple[str, ...] = ()
    #: What source context (beyond `ExecutionEvidence`) a human would need to
    #: supply before this entry's strategies could narrow toward a concrete
    #: edit -- e.g. source text, operand shapes, a file path. Never a promise
    #: that this repository can currently collect or apply that edit.
    repair_preconditions: tuple[str, ...] = ()
    #: How a human should confirm a future repair actually addressed this
    #: specific error code, once one is applied outside this repository's
    #: current scope. Never claims this repository performs the verification
    #: itself.
    repair_verification_steps: tuple[str, ...] = ()
    #: Generic, conservative cautions about this error code's repair space --
    #: never a claim that a specific fix is risky, since no specific fix is
    #: ever proposed by this catalog.
    repair_risks: tuple[str, ...] = ()


_ENTRIES: tuple[GaussErrorCatalogEntry, ...] = (
    GaussErrorCatalogEntry(
        error_code="G0105",
        category=GaussErrorCategory.PARSE_SYNTAX,
        title="Bad expression or missing arguments",
        generic_explanation=(
            "Execution stopped during parsing because GAUSS reported invalid syntax or a missing expression."
        ),
        execution_phase="parsing",
        confidence="high",
        recommended_next_step="Inspect the reported syntax near the parser diagnostic.",
        verification_status=(VerificationStatus.REAL_RUNTIME, VerificationStatus.OFFICIAL_DOCUMENTATION),
        verification_source=(
            "Real runtime: reproduced repeatedly via `tgauss.exe -b` (`planning/v0.28.0-real-gauss-invocation-"
            "research.md`; `v0.50.0`/`v0.52.0` real evaluations) using `x = ;`, consistently producing "
            "'error G0105 : Bad expression or missing arguments'. Official documentation: Aptech support "
            "content confirms the same title and describes the same general causes (missing semicolons, "
            "unloaded library statements, locale-related parsing issues)."
        ),
        known_triggers=(
            "a missing statement terminator (semicolon) on the reported line or the line before it",
            "a required `library` statement not included before a package procedure call",
            "an incomplete or malformed expression",
        ),
        diagnostic_questions=(
            "Does the reported line, or the line immediately before it, end with a semicolon?",
            "If this line calls a package procedure, is the corresponding `library` statement present earlier in the file?",
        ),
        required_evidence_for_diagnosis=(
            "the exact source text at and immediately before the reported parser location",
        ),
        repair_strategies=(
            "Inspect and complete or correct the invalid expression at the reported parser location before rerunning.",
        ),
        repair_preconditions=(
            "the exact source text at and immediately before the reported parser location",
        ),
        repair_verification_steps=(
            "Confirm the corrected script parses and executes without reproducing error G0105 at the same location.",
        ),
        repair_risks=(
            "A syntax-level fix does not confirm the surrounding logic is still correct; unrelated errors may "
            "surface only after this one is addressed.",
        ),
    ),
    GaussErrorCatalogEntry(
        error_code="G0063",
        category=GaussErrorCategory.PARSE_SYNTAX,
        title="Operator expected",
        generic_explanation=(
            "Execution stopped during parsing because GAUSS encountered a token where it expected an operator "
            "-- typically a bare, brace-less, `let`-less multi-token literal on an assignment's right-hand side."
        ),
        execution_phase="parsing",
        confidence="high",
        recommended_next_step="Enclose the right-hand side in `{...}` or prefix the statement with `let`.",
        verification_status=(VerificationStatus.REAL_RUNTIME,),
        verification_source=(
            "Real runtime: reproduced via `tgauss.exe -b` during v0.76.0 development (this repository's own "
            "session) using `x = -1 0;` (a real, live-found model output shape, category 66.x's own 66.4 "
            "prompt re-run through the installed `gauss-ai` CLI), consistently producing "
            "\"error G0063: Operator expected before '0'\". The identical literal prefixed with `let` "
            "(`let x = -1 0;`) was independently confirmed, same session, to execute successfully -- matching "
            "`let.rst`'s own documented Remarks (\"If curly braces are used, the `let` is optional\"; a bare "
            "multi-token list otherwise requires `let`). v0.77.0's own `gauss_pre_execution_validation."
            "bare_multi_token_literal_requires_let_or_braces` syntax rule is the deterministic detector for "
            "this exact shape."
        ),
        known_triggers=(
            "a bare assignment right-hand side listing two or more whitespace-separated numeric tokens with "
            "no enclosing `{...}` and no `let` keyword",
        ),
        diagnostic_questions=(
            "Does the reported right-hand side list more than one bare numeric token with no `{...}` and no `let`?",
        ),
        required_evidence_for_diagnosis=("the exact source text of the reported assignment statement",),
        repair_strategies=(
            "Enclose the right-hand side in curly braces, or prefix the statement with the `let` keyword.",
        ),
        repair_preconditions=("the exact source text of the reported assignment statement",),
        repair_verification_steps=(
            "Confirm the corrected script parses and executes without reproducing error G0063 at the same location.",
        ),
        repair_risks=(
            "A syntax-level fix does not confirm the surrounding logic is still correct; unrelated errors may "
            "surface only after this one is addressed.",
        ),
    ),
    GaussErrorCatalogEntry(
        error_code="G0036",
        category=GaussErrorCategory.MATRIX_DIMENSION,
        title="Matrix dimensions are incompatible",
        generic_explanation=(
            "Execution reached runtime before GAUSS reported an operation using incompatible matrix dimensions."
        ),
        execution_phase="runtime",
        confidence="high",
        recommended_next_step="Inspect stderr and verify matrix dimensions before the reported operation.",
        verification_status=(VerificationStatus.REAL_RUNTIME, VerificationStatus.OFFICIAL_DOCUMENTATION),
        verification_source=(
            "Real runtime: reproduced via `tgauss.exe -b` (`planning/v0.29.0-runtime-error-output-file-"
            "verification.md`; `v0.50.0`/`v0.52.0` real evaluations) using "
            "`x = ones(2,2); y = ones(3,1); z = x + y; print z;`, consistently producing "
            "'error G0036 : Matrix dimensions are incompatible'. Official documentation: an Aptech support "
            "page discusses this code (see `documentation_discrepancy`)."
        ),
        documentation_discrepancy=(
            "Official Aptech documentation (aptech.com/questions/g0036-matrices-are-not-conformable/) titles "
            "this error 'Matrices are not conformable', while every real runtime observation recorded in this "
            "repository shows the literal stderr text 'Matrix dimensions are incompatible'. Per this catalog's "
            "own verification policy, the runtime-observed text is used for `title`/`generic_explanation` above; "
            "the documentation wording is most likely a paraphrased page title rather than a literal runtime "
            "string, but that is not independently confirmed, so the disagreement is recorded rather than "
            "silently resolved."
        ),
        known_triggers=(
            "an arithmetic or Kronecker-product operation performed on operands whose dimensions do not conform",
            "operator precedence between the Kronecker-product operator (`.*.`) and standard matrix "
            "multiplication producing an unintended evaluation order",
        ),
        diagnostic_questions=(
            "What are the row/column dimensions of each operand in the reported operation?",
            "Does the expression mix the Kronecker-product operator (`.*.`) and matrix multiplication without explicit parentheses?",
        ),
        required_evidence_for_diagnosis=(
            "the row/column dimensions of the specific operands involved in the reported operation",
        ),
        repair_strategies=(
            "Inspect the dimensions and intended roles of both operands before deciding whether the operation, "
            "operand construction, or orientation needs adjustment.",
        ),
        repair_preconditions=(
            "the row/column dimensions of the specific operands involved in the reported operation",
        ),
        repair_verification_steps=(
            "Confirm the corrected operands produce a result with the intended dimensions before rerunning the "
            "full script.",
        ),
        repair_risks=(
            "Adjusting an operand's shape or orientation without understanding its statistical role can silently "
            "change what is being computed, not just whether it runs.",
        ),
    ),
    GaussErrorCatalogEntry(
        error_code="G0025",
        category=GaussErrorCategory.RUNTIME_COMPUTATION,
        title="Undefined symbol",
        generic_explanation="Execution reached runtime before GAUSS reported an undefined symbol.",
        execution_phase="runtime",
        confidence="high",
        recommended_next_step="Inspect stderr and the generated GAUSS script for the referenced symbol.",
        verification_status=(VerificationStatus.REAL_RUNTIME, VerificationStatus.OFFICIAL_DOCUMENTATION),
        verification_source=(
            "Real runtime: reproduced via `tgauss.exe -b` (`planning/v0.29.0-runtime-error-output-file-"
            "verification.md`) using `print undefinedvar;`, producing "
            "\"error G0025 : Undefined symbol: 'undefinedvar'\" with file/line info. Official documentation: "
            "Aptech support/blog content confirms an identical title and message format "
            "(example shown: \"G0025 : Undefined symbol: 'nobs' [estimate.gss, line 6]\"), and documents the "
            "same underlying cause (a symbol referenced before it is defined, an unloaded library, or a "
            "procedure GAUSS has not yet been told about)."
        ),
        known_triggers=(
            "a variable or procedure referenced before it was assigned or defined",
            "a required library or package not loaded",
            "a user-defined procedure not visible because the file defining it was not included, or the "
            "code was run line-by-line instead of as a complete file",
        ),
        diagnostic_questions=(
            "Is the referenced symbol assigned or defined earlier in the same run?",
            "Is the library or package that defines this symbol loaded (e.g. via a `library` statement)?",
            "Was the file run as a complete program rather than line-by-line?",
        ),
        required_evidence_for_diagnosis=(
            "the source location where the referenced symbol is expected to be assigned or defined",
        ),
        repair_strategies=(
            "Determine whether the missing symbol should be defined earlier in the script, supplied through "
            "scope, or loaded through an expected library or dependency.",
        ),
        repair_preconditions=(
            "the source location where the referenced symbol is expected to be assigned or defined",
        ),
        repair_verification_steps=(
            "Confirm the symbol resolves and the script no longer reports G0025 for this name before rerunning "
            "the full script.",
        ),
        repair_risks=(
            "Defining a symbol merely to silence the error, without understanding why it was missing, can mask "
            "a deeper scope or load-order problem.",
        ),
    ),
    GaussErrorCatalogEntry(
        error_code="G0014",
        category=GaussErrorCategory.FILE_IO,
        title="File not found",
        generic_explanation=(
            "GAUSS could not locate a file referenced by the script -- for example a data file, an included "
            "source file, or a script path argument."
        ),
        execution_phase="runtime",
        confidence="high",
        recommended_next_step=(
            "Confirm the referenced file exists and is reachable from GAUSS's current working directory or "
            "SRC_PATH, or supply an explicit full path."
        ),
        verification_status=(VerificationStatus.REAL_RUNTIME, VerificationStatus.OFFICIAL_DOCUMENTATION),
        verification_source=(
            "Real runtime: observed via `tgauss.exe -b` during `v0.28.0`'s non-interactive-invocation research "
            "(`planning/v0.28.0-real-gauss-invocation-research.md`) -- a `-e`-flag argument-parsing experiment "
            "was itself inconclusive about CLI argument handling, but as a side effect GAUSS genuinely produced "
            "\"error G0014 : File not found '1+1;', line 1\" when it tried to open a mis-parsed argument as a "
            "file. This was not an intentional file-not-found reproduction, but the error code and message text "
            "are real, unmodified GAUSS output, not a paraphrase. Official documentation: Aptech support content "
            "confirms G0014 as 'File not found', triggered when GAUSS cannot locate a referenced file in its "
            "current working directory or any directory in SRC_PATH."
        ),
        known_triggers=(
            "the referenced file is not present in GAUSS's current working directory or SRC_PATH",
            "a relative path was used from a different working directory than expected",
        ),
        diagnostic_questions=(
            "Does the referenced file exist at the expected location?",
            "What is GAUSS's current working directory for this run, and does it contain the file?",
        ),
        required_evidence_for_diagnosis=(
            "the file's expected location and GAUSS's actual current working directory for this run",
        ),
        repair_strategies=(
            "Validate the referenced path, current working directory, file existence, and permissions before "
            "changing the program.",
        ),
        repair_preconditions=(
            "the file's expected location and GAUSS's actual current working directory for this run",
        ),
        repair_verification_steps=(
            "Confirm the referenced file is reachable from the same working directory GAUSS will use before "
            "rerunning.",
        ),
        repair_risks=(
            "Hardcoding an absolute path as a workaround can break portability across machines or working "
            "directories.",
        ),
    ),
    GaussErrorCatalogEntry(
        error_code="G0290",
        category=GaussErrorCategory.PACKAGE_OR_LIBRARY,
        title="Library not found",
        generic_explanation=(
            "GAUSS could not find a required application/library file (an `.lcg` library), typically because "
            "the corresponding GAUSS application module is not installed, or is not present under the active "
            "GAUSSHOME directory."
        ),
        execution_phase="startup",
        confidence="high",
        recommended_next_step=(
            "Confirm the required GAUSS application/library is installed under GAUSSHOME for the active GAUSS "
            "version before rerunning."
        ),
        # v0.55.0: reproduced against a real GAUSS runtime -- upgraded from
        # documentation-only to dual-sourced. Runtime text and documentation
        # agree; no discrepancy to record.
        verification_status=(VerificationStatus.REAL_RUNTIME, VerificationStatus.OFFICIAL_DOCUMENTATION),
        verification_source=(
            "Real runtime: reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-"
            "expansion.md`) using `library optmum;` in an isolated scratch directory against this repository's "
            "real GAUSS 26.1.1 installation, whose `pkgs/` directory does not include `optmum` (confirmed "
            "installed modules: cmlmt, coint, comt, dccelib, gml, maxlikmt, optmt, pubtable, qardl, quaids, "
            "timeseries, tsmt, tspdlib), consistently producing \"error G0290 : Library not found "
            "'<path>\\optmum.lcg'\". Official documentation: Aptech support content documents G0290 as 'Library "
            "not found', occurring when a required application `.lcg` library file is missing from the active "
            "GAUSSHOME installation (e.g. an uninstalled application module such as `optmum`, `comt`, or "
            "`tsmt`) -- the runtime-observed title matches the documented title exactly; no discrepancy."
        ),
        known_triggers=(
            "the required GAUSS application/library module is not installed under the active GAUSSHOME",
        ),
        diagnostic_questions=(
            "Is the required application module (e.g. optmum, comt, tsmt) installed under GAUSSHOME for the active GAUSS version?",
        ),
        required_evidence_for_diagnosis=(
            "confirmation of which application module is required and whether it is installed under the active GAUSSHOME",
        ),
        repair_strategies=(
            "Confirm the required application module is installed under the active GAUSSHOME and correctly "
            "referenced before rerunning.",
        ),
        repair_preconditions=(
            "confirmation of which application module is required and whether it is installed under the active GAUSSHOME",
        ),
        repair_verification_steps=(
            "Confirm the `library` statement resolves without error before rerunning the full script.",
        ),
        repair_risks=(
            "Installing or modifying packages is outside this repository's automated scope; any installation "
            "must be performed by the user outside this workflow.",
        ),
    ),
    GaussErrorCatalogEntry(
        error_code="G0058",
        category=GaussErrorCategory.INDEXING_SUBSCRIPT,
        title="Index out of range",
        generic_explanation=(
            "Execution reached runtime before GAUSS reported that an index value fell outside the valid bounds "
            "of the object being indexed."
        ),
        execution_phase="runtime",
        confidence="high",
        recommended_next_step="Inspect the reported index value and the object's actual dimensions.",
        verification_status=(VerificationStatus.REAL_RUNTIME,),
        verification_source=(
            "Real runtime: reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-"
            "expansion.md`) using both `x = ones(2,2); print x[5,5];` and `x = ones(2,2); print x[-1,1];`, "
            "each consistently producing 'error G0058 : Index out of range'. Not yet independently corroborated "
            "against official Aptech documentation in this repository."
        ),
        known_triggers=(
            "an index value greater than the object's number of rows or columns",
            "an index value less than 1 (GAUSS uses 1-based indexing; a zero or negative index is out of range)",
        ),
        diagnostic_questions=(
            "What are the row/column dimensions of the object being indexed?",
            "Is the reported index value within the range 1 to the object's row/column count?",
        ),
        required_evidence_for_diagnosis=(
            "the dimensions of the object being indexed and the exact index value used at the reported location",
        ),
        repair_strategies=(
            "Inspect the object's actual dimensions and the reported index value before deciding whether the "
            "index, loop bound, or object construction needs adjustment.",
        ),
        repair_preconditions=(
            "the dimensions of the object being indexed and the exact index value used at the reported location",
        ),
        repair_verification_steps=(
            "Confirm the corrected index falls within the object's bounds and the script no longer reports "
            "G0058 at this location.",
        ),
        repair_risks=(
            "Widening an object's bounds to accommodate an index, rather than correcting the index itself, can "
            "silently change which elements are being read or written.",
        ),
    ),
    GaussErrorCatalogEntry(
        error_code="G0159",
        category=GaussErrorCategory.ARGUMENT_VALIDATION,
        title="Wrong number of parameters",
        generic_explanation=(
            "Execution reached runtime before GAUSS reported that a procedure was called with a different "
            "number of arguments than its own declaration accepts."
        ),
        execution_phase="runtime",
        confidence="high",
        recommended_next_step="Inspect the procedure's declared parameter list and the exact call site reported.",
        verification_status=(VerificationStatus.REAL_RUNTIME,),
        verification_source=(
            "Real runtime: reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-"
            "expansion.md`) using `proc(1) = myproc2(a, b); retp(a+b); endp; y = myproc2(1);`, consistently "
            "producing \"error G0159 : Wrong number of parameters ''myproc2' expected 2 arguments, received "
            "1'\". Not yet independently corroborated against official Aptech documentation in this repository."
        ),
        known_triggers=(
            "a procedure call supplying fewer arguments than the procedure's `proc` declaration requires",
            "a procedure call supplying more arguments than the procedure's `proc` declaration accepts",
        ),
        diagnostic_questions=(
            "How many parameters does the called procedure's `proc` statement declare?",
            "How many arguments does the reported call site actually supply?",
        ),
        required_evidence_for_diagnosis=(
            "the procedure's declared parameter count and the argument count actually supplied at the reported call site",
        ),
        repair_strategies=(
            "Compare the procedure's declared parameter list against the reported call site and determine "
            "whether the call or the declaration needs adjustment.",
        ),
        repair_preconditions=(
            "the procedure's declared parameter count and the argument count actually supplied at the reported call site",
        ),
        repair_verification_steps=(
            "Confirm the call site supplies exactly the declared number of arguments before rerunning the full script.",
        ),
        repair_risks=(
            "Adding placeholder arguments merely to match a count, without understanding their intended role, "
            "can silently change the procedure's behavior.",
        ),
    ),
    GaussErrorCatalogEntry(
        error_code="G0104",
        category=GaussErrorCategory.ARGUMENT_VALIDATION,
        title="Argument must be positive",
        generic_explanation=(
            "Execution reached runtime before GAUSS reported that a supplied argument did not satisfy a "
            "required strictly-positive-value constraint."
        ),
        execution_phase="runtime",
        confidence="high",
        recommended_next_step="Inspect the actual value of the reported argument at the point of the call.",
        verification_status=(VerificationStatus.REAL_RUNTIME,),
        verification_source=(
            "Real runtime: reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-"
            "expansion.md`) using `x = eye(-1);`, consistently producing 'error G0104 : Argument must be "
            "positive'. Not yet independently corroborated against official Aptech documentation in this "
            "repository."
        ),
        known_triggers=(
            "a zero or negative value supplied where a function or procedure requires a strictly positive "
            "value (e.g. a matrix-construction dimension such as `eye`'s size argument)",
        ),
        diagnostic_questions=(
            "What is the actual runtime value of the reported argument at the point of the call, and is it positive?",
        ),
        required_evidence_for_diagnosis=(
            "the runtime value of the specific argument identified by the error at the reported call site",
        ),
        repair_strategies=(
            "Inspect the runtime value of the reported argument and determine why it is zero, negative, or "
            "otherwise outside the required range.",
        ),
        repair_preconditions=(
            "the runtime value of the specific argument identified by the error at the reported call site",
        ),
        repair_verification_steps=(
            "Confirm the corrected argument value is positive and the script no longer reports G0104 at this "
            "call site.",
        ),
        repair_risks=(
            "Substituting an arbitrary positive placeholder value without understanding its statistical or "
            "computational role can produce a result that runs but is meaningless.",
        ),
    ),
    GaussErrorCatalogEntry(
        error_code="G0071",
        category=GaussErrorCategory.TYPE_MISMATCH,
        title="Type mismatch",
        generic_explanation=(
            "Execution reached runtime before GAUSS reported that an operation received an operand or argument "
            "of an unexpected type (for example a string where a numeric value was required)."
        ),
        execution_phase="runtime",
        confidence="high",
        recommended_next_step="Inspect the actual type of each operand or argument in the reported operation.",
        verification_status=(VerificationStatus.REAL_RUNTIME,),
        verification_source=(
            "Real runtime: reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-"
            "expansion.md`) using `x = sqrt(\"abc\");`, consistently producing 'error G0071 : Type mismatch'. "
            "Not yet independently corroborated against official Aptech documentation in this repository."
        ),
        known_triggers=(
            "a string value supplied where a numeric scalar or matrix argument was required",
        ),
        diagnostic_questions=(
            "What is the actual type (string, scalar, matrix) of each operand or argument in the reported operation?",
        ),
        required_evidence_for_diagnosis=(
            "the runtime type of each operand or argument involved in the reported operation",
        ),
        repair_strategies=(
            "Inspect the actual type of each operand or argument in the reported operation and determine which "
            "one does not match what the operation expects.",
        ),
        repair_preconditions=(
            "the runtime type of each operand or argument involved in the reported operation",
        ),
        repair_verification_steps=(
            "Confirm every operand or argument in the reported operation has a type the operation accepts "
            "before rerunning the full script.",
        ),
        repair_risks=(
            "Coercing a value to a different type without understanding why it had the wrong type can mask an "
            "upstream data-handling error.",
        ),
    ),
    GaussErrorCatalogEntry(
        error_code="G0048",
        category=GaussErrorCategory.NUMERICAL,
        title="Matrix singular",
        generic_explanation=(
            "Execution reached runtime before GAUSS reported that a matrix operation requiring inversion (or an "
            "equivalent operation) could not be completed because the supplied matrix is singular."
        ),
        execution_phase="runtime",
        confidence="high",
        recommended_next_step=(
            "Inspect the matrix supplied to the reported operation for linear dependence among its rows or columns."
        ),
        verification_status=(VerificationStatus.REAL_RUNTIME,),
        verification_source=(
            "Real runtime: reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-"
            "expansion.md`) using `x = ones(2,2); y = inv(x);`, consistently producing 'error G0048 : Matrix "
            "singular'. Not yet independently corroborated against official Aptech documentation in this "
            "repository."
        ),
        known_triggers=(
            "a matrix supplied to `inv` or an equivalent inversion-requiring operation has linearly dependent "
            "rows or columns (a zero, or near-zero, determinant)",
        ),
        diagnostic_questions=(
            "Does the matrix supplied to the reported operation have linearly dependent rows or columns?",
        ),
        required_evidence_for_diagnosis=(
            "the actual contents, determinant, or rank of the matrix supplied to the reported operation",
        ),
        repair_strategies=(
            "Inspect the matrix supplied to the reported operation for linear dependence among its rows or "
            "columns before deciding whether the data, model specification, or operation needs adjustment.",
        ),
        repair_preconditions=(
            "the actual contents, determinant, or rank of the matrix supplied to the reported operation",
        ),
        repair_verification_steps=(
            "Confirm the corrected matrix is non-singular (full rank) before rerunning the full script.",
        ),
        repair_risks=(
            "This repository does not assess whether a resulting non-singular matrix is statistically or "
            "methodologically appropriate for the intended model -- that judgment remains the user's.",
        ),
    ),
    GaussErrorCatalogEntry(
        error_code="G0047",
        category=GaussErrorCategory.MATRIX_DIMENSION,
        title="Rows don't match",
        generic_explanation=(
            "Execution reached runtime before GAUSS reported that a horizontal concatenation was attempted "
            "between operands with different numbers of rows."
        ),
        execution_phase="runtime",
        confidence="high",
        recommended_next_step=(
            "Inspect the row counts of each operand in the reported horizontal-concatenation operation."
        ),
        verification_status=(VerificationStatus.REAL_RUNTIME,),
        verification_source=(
            "Real runtime: reproduced via `tgauss.exe -b` (`planning/v0.55.0-verified-diagnostic-coverage-"
            "expansion.md`) using `x = ones(2,2); y = ones(3,3); z = x~y;`, consistently producing 'error G0047 "
            ": Rows don't match'. Not yet independently corroborated against official Aptech documentation in "
            "this repository. Distinct code from `G0036` (arithmetic/Kronecker dimension mismatch) -- this "
            "code is specific to the horizontal-concatenation (`~`) operator."
        ),
        known_triggers=(
            "a horizontal concatenation (`~`) attempted between operands with different numbers of rows",
        ),
        diagnostic_questions=(
            "What are the row counts of each operand in the reported horizontal-concatenation operation?",
        ),
        required_evidence_for_diagnosis=(
            "the row counts of the specific operands involved in the reported operation",
        ),
        repair_strategies=(
            "Inspect the row counts of each operand in the reported horizontal-concatenation operation before "
            "deciding whether the operands, the operation, or the intended orientation needs adjustment.",
        ),
        repair_preconditions=(
            "the row counts of the specific operands involved in the reported operation",
        ),
        repair_verification_steps=(
            "Confirm the corrected operands share the same row count before rerunning the full script.",
        ),
        repair_risks=(
            "Adjusting row counts (e.g. truncating or padding) without understanding why they differed can "
            "silently discard or misalign data.",
        ),
    ),
)


def _build_catalog(entries: tuple[GaussErrorCatalogEntry, ...]) -> dict[str, GaussErrorCatalogEntry]:
    """Builds the lookup dict from `_ENTRIES`, raising immediately on a
    duplicate `error_code` rather than silently letting a later entry
    overwrite an earlier one (which a plain dict literal would do)."""
    catalog: dict[str, GaussErrorCatalogEntry] = {}
    for entry in entries:
        code = normalize_error_code(entry.error_code)
        if code in catalog:
            raise ValueError(f"duplicate GAUSS error code in catalog: {code!r}")
        if not entry.verification_status:
            raise ValueError(f"catalog entry {code!r} declares no verification_status")
        catalog[code] = entry
    return catalog


def normalize_error_code(error_code: str) -> str:
    return error_code.strip().upper()


def lookup_error(error_code: str) -> GaussErrorCatalogEntry | None:
    return _CATALOG.get(normalize_error_code(error_code))


def known_error_codes() -> tuple[str, ...]:
    return tuple(sorted(_CATALOG))


def catalog_entries() -> tuple[GaussErrorCatalogEntry, ...]:
    return tuple(_CATALOG[code] for code in sorted(_CATALOG))


_CATALOG: dict[str, GaussErrorCatalogEntry] = _build_catalog(_ENTRIES)
