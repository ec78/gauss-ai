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
        confidence="medium",
        recommended_next_step=(
            "Confirm the required GAUSS application/library is installed under GAUSSHOME for the active GAUSS "
            "version before rerunning."
        ),
        verification_status=(VerificationStatus.OFFICIAL_DOCUMENTATION,),
        verification_source=(
            "Official documentation only -- not yet reproduced against a real GAUSS runtime in this repository. "
            "Aptech support content documents G0290 as 'Library not found', occurring when a required "
            "application `.lcg` library file is missing from the active GAUSSHOME installation (e.g. an "
            "uninstalled application module such as `optmum`, `comt`, or `tsmt`)."
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
