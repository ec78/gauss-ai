"""Deterministic GAUSS execution-error catalog.

The catalog is intentionally small. It records only GAUSS error identifiers
that this repository has evidence for, and it is designed so new identifiers
can be added without changing interpreter control flow.
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


@dataclass(frozen=True)
class GaussErrorCatalogEntry:
    error_code: str
    category: GaussErrorCategory
    title: str
    generic_explanation: str
    execution_phase: str
    confidence: str
    recommended_next_step: str


_CATALOG: dict[str, GaussErrorCatalogEntry] = {
    "G0105": GaussErrorCatalogEntry(
        error_code="G0105",
        category=GaussErrorCategory.PARSE_SYNTAX,
        title="Bad expression or missing arguments",
        generic_explanation=(
            "Execution stopped during parsing because GAUSS reported invalid syntax or a missing expression."
        ),
        execution_phase="parsing",
        confidence="high",
        recommended_next_step="Inspect the reported syntax near the parser diagnostic.",
    ),
    "G0036": GaussErrorCatalogEntry(
        error_code="G0036",
        category=GaussErrorCategory.MATRIX_DIMENSION,
        title="Matrix dimensions are incompatible",
        generic_explanation=(
            "Execution reached runtime before GAUSS reported an operation using incompatible matrix dimensions."
        ),
        execution_phase="runtime",
        confidence="high",
        recommended_next_step="Inspect stderr and verify matrix dimensions before the reported operation.",
    ),
    "G0025": GaussErrorCatalogEntry(
        error_code="G0025",
        category=GaussErrorCategory.RUNTIME_COMPUTATION,
        title="Undefined symbol",
        generic_explanation="Execution reached runtime before GAUSS reported an undefined symbol.",
        execution_phase="runtime",
        confidence="medium",
        recommended_next_step="Inspect stderr and the generated GAUSS script for the referenced symbol.",
    ),
}


def normalize_error_code(error_code: str) -> str:
    return error_code.strip().upper()


def lookup_error(error_code: str) -> GaussErrorCatalogEntry | None:
    return _CATALOG.get(normalize_error_code(error_code))


def known_error_codes() -> tuple[str, ...]:
    return tuple(sorted(_CATALOG))


def catalog_entries() -> tuple[GaussErrorCatalogEntry, ...]:
    return tuple(_CATALOG[code] for code in sorted(_CATALOG))
