"""Deterministic pre-execution validation for conversationally generated
GAUSS code (v0.74.0).

`v0.73.0`'s own live evidence proved symbol-level grounding is necessary but
not sufficient:

- **Finding 1**: a generated call can use only real, documented symbols and
  still be wrong -- wrong argument count, wrong argument order, or a
  violated documented precondition. Checking whether a symbol "appears
  supported" says nothing about any of that.
- **Finding 2** (the `tscsmtControl` regression, live scenario `63.5`): a
  `FULL`-gated request produced a real documented function (`tscsFit`) used
  correctly, alongside a hallucinated secondary symbol, `tscsmtControl()`,
  that is not a real callable at all -- it is the NAME OF A STRUCT TYPE
  documented in `tscsFit`'s own page, confused by the model for a
  constructor. The real constructor is `tscsmtControlCreate()`. `FULL`
  grounding did not, and structurally cannot, guarantee every symbol in the
  generated code is correct.
- **Finding 3** (the `invpd` regression, `evaluations/runs/2026-09-10-...-
  run-006.md`): a real, successful GAUSS execution of a generated `invpd`
  example did not prove the input satisfied `invpd`'s own documented
  precondition (a symmetric, positive-definite matrix) -- confirmed
  directly by `invinvpd.rst`'s own text: "If the input to invpd is not
  symmetric, it is possible that the function will (erroneously) appear to
  operate successfully." Execution success is independent evidence from
  documented-precondition satisfaction, and this module never conflates
  the two.

This module adds three deterministic, provider-independent layers on top of
`v0.73.0`'s grounding/gate/symbol-check pipeline in `gauss_conversation_
engine.py`:

1. Documented call-signature extraction and compatibility checking
   (`DocumentedSignature`, `extract_documented_signature`, `GeneratedCall`,
   `extract_generated_calls`, `CallValidationResult`, `validate_call`).
2. A small, hand-curated, doc-verified table of documented preconditions,
   with deterministic validators implemented ONLY for the small set this
   version can actually prove correct -- currently: square/symmetric/
   positive-definite checking of a LITERAL matrix argument to `invpd`
   (`DocumentedPrecondition`, `PreconditionCheck`, `check_preconditions`).
   A runtime-variable or expression argument (e.g. the real documented
   `invpd(x'x)` OLS example) is reported `UNVERIFIED`, never guessed.
3. An explicit, conservative execution-eligibility verdict
   (`ExecutionEligibility`, `compute_eligibility`) computed purely from the
   above plus `v0.73.0`'s own gate/symbol-check evidence. `ELIGIBLE_FOR_
   VALIDATION` means ONLY "deterministic checks found no known problem" --
   it is never presented, here or in any caller, as correct, safe,
   methodologically appropriate, or approved to run. This module contains
   no execution capability of any kind: no subprocess, no shell, no file
   write, no import of any `gauss_execution_*`/`gauss_repair_*`/
   `gauss_verification_*` module.

Deliberately duplicated, not imported, from `gauss_conversation_engine.py`:
the small, explicitly-verified control-flow-keyword list used to avoid
mistaking a loop header for a function call (see `_LANGUAGE_CONSTRUCT_
KEYWORDS` below). This module is imported BY `gauss_conversation_engine.py`,
so importing back from it would create a circular import; the list is small,
stable, and was verified via real GAUSS execution in `v0.73.0`'s own
development -- keep the two copies in sync if that list ever changes.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass

#: See module docstring's final paragraph for why this is duplicated rather
#: than imported.
_LANGUAGE_CONSTRUCT_KEYWORDS = frozenset({
    "if", "elseif", "else", "endif", "do", "while", "until", "endo", "for", "endfor",
    "proc", "endp", "retp", "local", "print", "struct",
})

_CALL_SHAPED_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _split_top_level_args(raw: str) -> list[str]:
    """Splits `raw` on top-level commas only -- commas nested inside
    `(...)`, `{...}`, or `[...]` do not split. Bounded, conservative: not a
    real expression parser, just enough to separate GAUSS call arguments
    and documented parameter lists."""
    raw = raw.strip()
    if not raw:
        return []
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in raw:
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return [p for p in parts if p]


def _find_matching_paren(line: str, open_idx: int) -> int | None:
    depth = 0
    for i in range(open_idx, len(line)):
        if line[i] == "(":
            depth += 1
        elif line[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return None


# ---------------------------------------------------------------------------
# Phase 4: documented call-signature extraction
# ---------------------------------------------------------------------------

SIGNATURE_EXTRACTED = "extracted"
SIGNATURE_UNKNOWN = "unknown"


@dataclass(frozen=True)
class DocumentedSignature:
    """`arg_ranges` holds one `(min_args, max_args)` pair per documented
    overload found for `symbol` -- a generated call is argument-count
    COMPATIBLE if its count falls in ANY of these ranges (real documented
    functions in this codebase's own docs, e.g. `tscsFit`, have more than
    one overload). `extraction_status == UNKNOWN` (with empty `arg_ranges`)
    means the documentation's own format did not support reliable
    extraction -- never a fabricated signature."""

    symbol: str
    arg_ranges: tuple[tuple[int, int], ...]
    parameter_names: tuple[str, ...]
    source: str | None
    extraction_status: str


def _parse_signature_occurrence(raw_args: str) -> tuple[int, int, tuple[str, ...]]:
    """`raw_args` is the text between one documented call's own parentheses,
    e.g. `"y, x, grp[, tsc]"` (the real, verified `tscsFit` documented
    form). A `[...]` group marks its own contents as optional, trailing
    arguments -- confirmed against real `tsmt/tscsfit.rst` text in this
    milestone's own development. Returns `(min_args, max_args, names)`."""
    bracket_idx = raw_args.find("[")
    if bracket_idx == -1:
        names = tuple(_split_top_level_args(raw_args))
        return len(names), len(names), names
    required_part = raw_args[:bracket_idx]
    optional_part = raw_args[bracket_idx:].strip()
    if optional_part.startswith("[") and optional_part.endswith("]"):
        optional_part = optional_part[1:-1]
    optional_part = optional_part.lstrip(",").strip()
    required_names = tuple(_split_top_level_args(required_part))
    optional_names = tuple(_split_top_level_args(optional_part))
    all_names = required_names + optional_names
    return len(required_names), len(all_names), all_names


def extract_documented_signature(symbol: str, best_match: dict) -> DocumentedSignature:
    """Conservative, best-effort extraction from `command_doc_lookup`'s own
    already-extracted `syntax_blocks` -- never guesses. Handles both real
    documentation styles confirmed present side by side in the real docs
    checkout this milestone was developed against: the `.. function::`
    directive style (one or more overload lines, e.g. `meanc`/`invpd`/
    `tscsFit`) and the older plain Format-heading text style with no
    directive at all (e.g. `tsc = tscsmtControlCreate( );`). If `symbol`
    cannot be found call-shaped in any syntax block, returns
    `extraction_status == UNKNOWN` rather than fabricating a signature."""
    call_re = re.compile(rf"\b{re.escape(symbol)}\s*\(([^()]*)\)", re.IGNORECASE)
    ranges: list[tuple[int, int]] = []
    names: list[str] = []
    for block in best_match.get("syntax_blocks") or ():
        for match in call_re.finditer(block):
            min_a, max_a, arg_names = _parse_signature_occurrence(match.group(1))
            if (min_a, max_a) not in ranges:
                ranges.append((min_a, max_a))
            for name in arg_names:
                if name and name not in names:
                    names.append(name)

    if not ranges:
        return DocumentedSignature(
            symbol=symbol, arg_ranges=(), parameter_names=(),
            source=best_match.get("file_path"), extraction_status=SIGNATURE_UNKNOWN,
        )
    return DocumentedSignature(
        symbol=symbol, arg_ranges=tuple(ranges), parameter_names=tuple(names),
        source=best_match.get("file_path"), extraction_status=SIGNATURE_EXTRACTED,
    )


def _count_compatible(count: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(lo <= count <= hi for lo, hi in ranges)


# ---------------------------------------------------------------------------
# Phase 5: generated-call extraction
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GeneratedCall:
    symbol: str
    argument_count: int
    raw_arguments: tuple[str, ...]
    line_number: int


def extract_generated_calls(code: str) -> tuple[GeneratedCall, ...]:
    """Conservative: same call-shape/control-flow-line-skipping discipline
    as `gauss_conversation_engine.check_generated_symbols(...)` -- not a
    GAUSS parser, no type inference, never interprets prose as code.
    Argument text is split at the top level only, so `f(g(x), y)` is
    extracted as a call to `f` with two top-level arguments (`g(x)` and
    `y`); `g` is separately extracted as its own nested call on the same
    line."""
    calls: list[GeneratedCall] = []
    for line_no, line in enumerate(code.splitlines(), start=1):
        stripped = line.strip().lower()
        if any(stripped.startswith(keyword) for keyword in _LANGUAGE_CONSTRUCT_KEYWORDS):
            continue
        for match in _CALL_SHAPED_RE.finditer(line):
            symbol = match.group(1)
            if symbol.lower() in _LANGUAGE_CONSTRUCT_KEYWORDS:
                continue
            close_idx = _find_matching_paren(line, match.end() - 1)
            if close_idx is None:
                continue  # unterminated on this line -- skip rather than guess
            raw = line[match.end():close_idx]
            args = tuple(_split_top_level_args(raw))
            calls.append(GeneratedCall(symbol=symbol, argument_count=len(args), raw_arguments=args, line_number=line_no))
    return tuple(calls)


# ---------------------------------------------------------------------------
# Phase 6: signature compatibility validation
# ---------------------------------------------------------------------------


class SignatureCompatibility(str, enum.Enum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CallValidationResult:
    """Argument-COUNT compatibility only -- this never claims argument
    order, type, or shape correctness, and never claims the call is
    semantically correct merely because its argument count matches (see
    module docstring's Finding 1)."""

    symbol: str
    documented: bool
    signature_known: bool
    argument_count_status: str
    issues: tuple[str, ...]
    source: str | None


def validate_call(
    call: GeneratedCall, *, documented_signatures: dict[str, DocumentedSignature], documented_symbols: frozenset[str],
) -> CallValidationResult:
    lowered = call.symbol.lower()
    if lowered not in documented_symbols:
        return CallValidationResult(
            symbol=call.symbol, documented=False, signature_known=False,
            argument_count_status=SignatureCompatibility.UNKNOWN.value,
            issues=("symbol is not among the documented/resolved topics for this turn",), source=None,
        )

    signature = documented_signatures.get(lowered)
    if signature is None or signature.extraction_status == SIGNATURE_UNKNOWN or not signature.arg_ranges:
        return CallValidationResult(
            symbol=call.symbol, documented=True, signature_known=False,
            argument_count_status=SignatureCompatibility.UNKNOWN.value,
            issues=("a documented call signature could not be reliably extracted for this symbol",),
            source=signature.source if signature else None,
        )

    if _count_compatible(call.argument_count, signature.arg_ranges):
        return CallValidationResult(
            symbol=call.symbol, documented=True, signature_known=True,
            argument_count_status=SignatureCompatibility.COMPATIBLE.value, issues=(), source=signature.source,
        )

    allowed = sorted({f"{lo}" if lo == hi else f"{lo}-{hi}" for lo, hi in signature.arg_ranges})
    return CallValidationResult(
        symbol=call.symbol, documented=True, signature_known=True,
        argument_count_status=SignatureCompatibility.INCOMPATIBLE.value,
        issues=(f"documented form(s) accept {' or '.join(allowed)} argument(s); this call passed {call.argument_count}",),
        source=signature.source,
    )


# ---------------------------------------------------------------------------
# Phase 7: companion-function mismatch detection
# ---------------------------------------------------------------------------


def find_companion_hint(unknown_symbol: str, *, companions: frozenset[str]) -> str | None:
    """The exact `tscsmtControl`-vs-`tscsmtControlCreate` case (module
    docstring's Finding 2): a substring relationship between an unsupported
    generated symbol and a real documented companion is surfaced as a
    diagnostic hint, never used to silently rewrite the generated code --
    this module has no code-editing capability at all. Deterministic and
    conservative: only a direct substring relationship counts, never a
    fuzzy/edit-distance guess."""
    lowered = unknown_symbol.lower()
    candidates = sorted(
        c for c in companions
        if c.lower() != lowered and (lowered in c.lower() or c.lower() in lowered)
    )
    return candidates[0] if candidates else None


# ---------------------------------------------------------------------------
# Phase 8/9/10: documented preconditions and deterministic validators
# ---------------------------------------------------------------------------


class PreconditionKind(str, enum.Enum):
    SHAPE = "shape"
    DIMENSION = "dimension"
    PROPERTY = "property"
    TYPE = "type"
    RANGE = "range"
    REQUIRED_COMPANION = "required_companion"
    OTHER = "other"


class PreconditionStatus(str, enum.Enum):
    SATISFIED = "satisfied"
    VIOLATED = "violated"
    UNVERIFIED = "unverified"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class DocumentedPrecondition:
    symbol: str
    description: str
    kind: str
    source: str
    #: True only for the small set of preconditions this module actually
    #: implements a deterministic validator for below -- `machine_checkable`
    #: is a claim about what THIS VERSION can prove, not about whether the
    #: constraint is inherently checkable at all.
    machine_checkable: bool


#: Hand-curated, doc-verified -- every entry's `description`/`source` was
#: checked in this milestone's own development session against the real,
#: local `invinvpd.rst` cited (see module docstring's Finding 3). Small and
#: explicit, exactly like `gauss_conversation_engine._CONCEPT_ALIAS_INDEX`.
_PRECONDITION_INDEX: dict[str, tuple[DocumentedPrecondition, ...]] = {
    "invpd": (
        DocumentedPrecondition(
            symbol="invpd", kind=PreconditionKind.PROPERTY.value, machine_checkable=True,
            source="invinvpd.rst",
            description=(
                'invinvpd.rst: "For invpd, if x is a matrix, it must be symmetric and positive '
                'definite... If the input to invpd is not symmetric, it is possible that the '
                'function will (erroneously) appear to operate successfully."'
            ),
        ),
    ),
    "inv": (
        DocumentedPrecondition(
            symbol="inv", kind=PreconditionKind.PROPERTY.value, machine_checkable=False,
            source="invinvpd.rst",
            description=(
                'invinvpd.rst: "For inv, if x is a matrix, it must be square and invertible." '
                "(squareness is checkable for a literal matrix; general invertibility is not "
                "attempted deterministically in this version, so this entry is not marked "
                "machine-checkable -- see check_preconditions(...).)"
            ),
        ),
    ),
}


def documented_preconditions(symbol: str) -> tuple[DocumentedPrecondition, ...]:
    return _PRECONDITION_INDEX.get(symbol.lower(), ())


@dataclass(frozen=True)
class PreconditionCheck:
    precondition: DocumentedPrecondition
    status: str
    explanation: str


_LITERAL_MATRIX_RE = re.compile(r"\{([^{}]*)\}")
#: Deterministic linear algebra (leading-principal-minor computation) is
#: only attempted up to this size -- bounded, not a claim of general
#: numerical robustness.
MAX_CHECKED_MATRIX_DIM = 6
#: A single trailing GAUSS transpose quote is tolerated on an identifier
#: (`x'`); anything more complex (`x'x`, a function call, an expression) is
#: treated as a non-literal runtime value, never partially evaluated.
_SIMPLE_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*'?")


def _parse_literal_matrix(text: str) -> list[list[float]] | None:
    match = _LITERAL_MATRIX_RE.search(text)
    if not match:
        return None
    rows: list[list[float]] = []
    for row_str in (r.strip() for r in match.group(1).split(",")):
        if not row_str:
            continue
        try:
            rows.append([float(tok) for tok in row_str.split()])
        except ValueError:
            return None
    if not rows:
        return None
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return None
    return rows


def _find_literal_matrix_for_argument(argument: str, *, code: str) -> list[list[float]] | None:
    """`argument` is the raw text of one call argument (e.g. `"x"` or
    `"{1 2, 2 1}"`). If it is itself a `{...}` literal, parses it directly.
    If it is a simple identifier (optionally transposed, `x'`), looks for
    that identifier's own most recent `{...}` literal assignment earlier in
    the SAME code text. Any more complex expression (e.g. the real
    documented `invpd(x'x)` OLS example, a matrix product) is deliberately
    left unresolved -- this function never partially evaluates a runtime
    expression, and returns `None` (never a fabricated matrix) in that
    case."""
    argument = argument.strip()
    if "{" in argument:
        return _parse_literal_matrix(argument)
    if _SIMPLE_IDENTIFIER_RE.fullmatch(argument):
        base = argument.rstrip("'")
        assign_re = re.compile(rf"\b{re.escape(base)}\s*=\s*(\{{[^{{}}]*\}})")
        matches = assign_re.findall(code)
        if matches:
            return _parse_literal_matrix(matches[-1])
    return None


def _is_square(rows: list[list[float]]) -> bool:
    return len(rows) == len(rows[0])


def _is_symmetric(rows: list[list[float]], *, tol: float = 1e-9) -> bool:
    n = len(rows)
    return all(abs(rows[i][j] - rows[j][i]) <= tol for i in range(n) for j in range(n))


def _determinant(matrix: list[list[float]]) -> float:
    n = len(matrix)
    if n == 1:
        return matrix[0][0]
    if n == 2:
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    total = 0.0
    for col in range(n):
        minor = [row[:col] + row[col + 1:] for row in matrix[1:]]
        sign = 1.0 if col % 2 == 0 else -1.0
        total += sign * matrix[0][col] * _determinant(minor)
    return total


def _leading_principal_minors_positive(rows: list[list[float]]) -> bool:
    """Sylvester's criterion: a real symmetric matrix is positive definite
    iff every leading principal minor is strictly positive. Deterministic,
    exact (for literal/rational input), and requires no eigendecomposition
    or external numeric library."""
    n = len(rows)
    for k in range(1, n + 1):
        submatrix = [row[:k] for row in rows[:k]]
        if _determinant(submatrix) <= 0:
            return False
    return True


def check_invpd_precondition(call: GeneratedCall, *, code: str) -> PreconditionCheck:
    precondition = _PRECONDITION_INDEX["invpd"][0]
    if not call.raw_arguments:
        return PreconditionCheck(precondition, PreconditionStatus.UNVERIFIED.value, "no argument found to inspect")

    rows = _find_literal_matrix_for_argument(call.raw_arguments[0], code=code)
    if rows is None:
        return PreconditionCheck(
            precondition, PreconditionStatus.UNVERIFIED.value,
            "the input is a runtime value or expression, not a literal matrix -- symmetry/"
            "positive-definiteness cannot be checked without executing GAUSS, which this module "
            "never does",
        )
    if len(rows) > MAX_CHECKED_MATRIX_DIM or len(rows[0]) > MAX_CHECKED_MATRIX_DIM:
        return PreconditionCheck(
            precondition, PreconditionStatus.UNVERIFIED.value,
            f"the literal input matrix exceeds the {MAX_CHECKED_MATRIX_DIM}x{MAX_CHECKED_MATRIX_DIM} "
            "bound this version checks deterministically",
        )
    if not _is_square(rows):
        return PreconditionCheck(
            precondition, PreconditionStatus.VIOLATED.value,
            "the literal input matrix is not square, so it cannot be symmetric positive definite",
        )
    if not _is_symmetric(rows):
        return PreconditionCheck(
            precondition, PreconditionStatus.VIOLATED.value,
            "the literal input matrix is not symmetric, which invpd's own documentation requires",
        )
    if not _leading_principal_minors_positive(rows):
        return PreconditionCheck(
            precondition, PreconditionStatus.VIOLATED.value,
            "the literal input matrix is symmetric but not positive definite (a documented invpd requirement)",
        )
    return PreconditionCheck(
        precondition, PreconditionStatus.SATISFIED.value,
        "the literal input matrix is symmetric and positive definite (verified by leading-principal-minor computation)",
    )


def check_preconditions(call: GeneratedCall, *, code: str) -> tuple[PreconditionCheck, ...]:
    """Never fabricates `SATISFIED` -- a precondition with no implemented
    deterministic validator is always reported `UNVERIFIED`, explicitly
    naming that no validator exists in this version, rather than being
    silently omitted."""
    checks: list[PreconditionCheck] = []
    for precondition in documented_preconditions(call.symbol):
        if call.symbol.lower() == "invpd" and precondition.machine_checkable:
            checks.append(check_invpd_precondition(call, code=code))
        else:
            checks.append(PreconditionCheck(
                precondition, PreconditionStatus.UNVERIFIED.value,
                "no deterministic validator is implemented for this precondition in this version",
            ))
    return tuple(checks)


# ---------------------------------------------------------------------------
# Phase 11/12/13: pre-execution validation result and eligibility
# ---------------------------------------------------------------------------


class ExecutionEligibility(str, enum.Enum):
    """Deliberately not named/framed as "safe to run" -- see module
    docstring. `ELIGIBLE_FOR_VALIDATION` means only: this code has enough
    deterministic support to be considered for a FUTURE controlled
    execution-validation workflow. It does NOT mean correct, safe,
    methodologically appropriate, approved for execution, or user-approved.
    """

    INELIGIBLE = "ineligible"
    REQUIRES_CLARIFICATION = "requires_clarification"
    ELIGIBLE_FOR_VALIDATION = "eligible_for_validation"


@dataclass(frozen=True)
class PreExecutionValidationResult:
    """Immutable, provider-independent, contains no execution capability of
    any kind. `companion_hints` is a tuple of `(unknown_symbol,
    documented_companion)` pairs rather than a dict, for the same
    immutability discipline as every other field here."""

    generation_policy: str | None
    unknown_symbols: tuple[str, ...]
    companion_hints: tuple[tuple[str, str], ...]
    call_validations: tuple[CallValidationResult, ...]
    preconditions: tuple[PreconditionCheck, ...]
    unresolved_issues: tuple[str, ...]
    eligibility: str


def compute_eligibility(
    *, generation_policy: str | None, unknown_symbols: tuple[str, ...], ambiguous_topics: tuple[str, ...],
    call_validations: tuple[CallValidationResult, ...], preconditions: tuple[PreconditionCheck, ...],
    code_extraction_ok: bool,
) -> tuple[str, tuple[str, ...]]:
    """Deterministic: reads only its own arguments, calls no model, performs
    no I/O. Rule (deliberately conservative, exactly per this milestone's
    own Phase 13): `ELIGIBLE_FOR_VALIDATION` requires ALL of --

    - the generation policy actually permitted generation (`full`/
      `supported_only`);
    - no unresolved resolution ambiguity remains;
    - code extraction itself succeeded;
    - no unknown/unsupported call-shaped symbol remains;
    - no documented call signature is known to be INCOMPATIBLE (an UNKNOWN
      signature does not block eligibility -- it is a real, disclosed gap,
      not a violation);
    - no documented precondition is known to be VIOLATED (an UNVERIFIED
      precondition does not block eligibility either, for the same reason).

    `REQUIRES_CLARIFICATION` takes priority when genuine ambiguity remains
    (mirrors `v0.73.0`'s own `GenerationPolicy.CLARIFY` priority ordering).
    Any other failure yields `INELIGIBLE` with the specific reason(s)
    named in `unresolved_issues` -- never silently blocked with no
    explanation."""
    if ambiguous_topics:
        return (
            ExecutionEligibility.REQUIRES_CLARIFICATION.value,
            (f"ambiguous topic(s) remain unresolved: {', '.join(ambiguous_topics)}",),
        )

    issues: list[str] = []
    if not code_extraction_ok:
        issues.append("generated code could not be reliably parsed for call/argument extraction")
    if generation_policy not in ("full", "supported_only"):
        issues.append(f"generation policy does not permit code generation ({generation_policy})")
    if unknown_symbols:
        issues.append(f"unresolved/unsupported call symbol(s): {', '.join(unknown_symbols)}")
    for validation in call_validations:
        if validation.argument_count_status == SignatureCompatibility.INCOMPATIBLE.value:
            issues.append(f"{validation.symbol}: {'; '.join(validation.issues)}")
    for check in preconditions:
        if check.status == PreconditionStatus.VIOLATED.value:
            issues.append(f"{check.precondition.symbol}: {check.explanation}")

    if issues:
        return ExecutionEligibility.INELIGIBLE.value, tuple(issues)
    return ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value, ()


# ---------------------------------------------------------------------------
# Phase 20: rendering
# ---------------------------------------------------------------------------


def render_validation_report(
    *, eligibility: str, unresolved_issues: tuple[str, ...], call_validations: tuple[CallValidationResult, ...],
    preconditions: tuple[PreconditionCheck, ...], companion_hints: tuple[tuple[str, str], ...],
) -> str:
    """Advisory, human-readable summary of this module's own evidence.
    Never implies real GAUSS execution occurred -- callers are expected to
    still append the existing, fixed "not executed in this conversation"
    footer (`gauss_conversation_engine.NOT_EXECUTED_FOOTER`) alongside this."""
    lines = ["Validation:"]

    for validation in call_validations:
        status_bits = [
            "documented" if validation.documented else "not documented",
            f"signature: {validation.argument_count_status}",
        ]
        line = f"- Function {validation.symbol}: " + "; ".join(status_bits)
        if validation.issues:
            line += " (" + "; ".join(validation.issues) + ")"
        lines.append(line)

    for hint_symbol, companion in companion_hints:
        lines.append(f"- `{hint_symbol}` was not found, but `{companion}` is documented in the retrieved source.")

    if preconditions:
        lines.append("- Preconditions:")
        for check in preconditions:
            lines.append(f"  - {check.precondition.symbol}: {check.status} -- {check.explanation}")

    lines.append(f"- Execution eligibility: {eligibility}")
    if eligibility == ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value:
        lines.append(
            "  (This means only that deterministic checks found no known problem -- not that the "
            "code is correct, safe, methodologically appropriate, or approved to run.)"
        )
    elif unresolved_issues:
        lines.append("  Cannot mark this code eligible for validation:")
        for issue in unresolved_issues:
            lines.append(f"  - {issue}")

    return "\n".join(lines)
