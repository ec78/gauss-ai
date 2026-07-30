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
