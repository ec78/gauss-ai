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

`v0.75.0` additions -- richer signature/parameter metadata, expanded
precondition coverage, and structured predicted-output claim handling. This
milestone's own real evaluation of `v0.74.0` surfaced a QA-intent
eligibility gap (a conversational answer not classified `CODE_GENERATION`
could still contain generated GAUSS code that never received an
eligibility verdict at all) and a real wrong-model-prediction finding (a
literal, valid `invpd({2 1, 1 2})` example: the code itself was correctly
`ELIGIBLE_FOR_VALIDATION`, but the model's own claimed numeric inverse,
`0.5 -0.5 / -0.5 0.5`, was wrong -- the real inverse, confirmed by
`tgauss.exe -b` execution, is `0.66666667 -0.33333333 / -0.33333333
0.66666667`; see `evaluations/runs/2026-09-12-code-assistant-pre-execution-
validation-run-004.md`). The universal-routing fix itself lives in
`gauss_conversation_engine.py` (see that module's own v0.75.0 docstring
section); this module adds the richer evidence that routing fix now always
computes:

- `DocumentedParameter`/`classify_documented_type` -- conservative
  per-parameter category (`SCALAR`/`VECTOR`/`MATRIX`/`STRING`/`CONTROL`/
  `DATASET`/`UNKNOWN`) and shape (`SQUARE`/`COLUMN_VECTOR`/`ROW_VECTOR`/
  `UNKNOWN`) extracted ONLY from a real `:type <name>: <text>` line in the
  documentation's own `.. function::` directive block (e.g. `meanc.rst`'s
  own `:type x: NxK matrix`) -- never inferred from a parameter name alone,
  never fabricated when the doc's own text does not support a confident
  category.
- `infer_literal_category`/`check_parameter_roles` -- a small, bounded
  literal-expression classifier (numeric scalar / string / literal
  matrix-or-vector, from a GAUSS `{...}` literal) compared positionally
  against the documented parameter category above, producing `MATCH`/
  `MISMATCH`/`UNKNOWN` (never fabricated agreement) per argument. A runtime
  variable or any non-literal expression is always `UNKNOWN` here -- this is
  not, and does not attempt to be, a type system or a GAUSS parser.
- Two new documented-precondition families beyond `invpd`, plus one
  upgrade of an EXISTING curated-but-previously-unimplemented entry, all
  selected because this session's own real, local GAUSS documentation
  checkout supports a genuinely deterministic literal check: `solpd`
  (`solpd.rst`: the *A* argument, its SECOND parameter, must be positive
  definite -- and `solpd.rst`'s own text says the function "does not check
  to see that the matrix *A* is symmetric... will look only at the upper
  half of the matrix including the principal diagonal", so this module's
  own check mirrors that exact documented convention rather than reusing
  `invpd`'s symmetry requirement verbatim); `chol` (`chol.rst`: the same
  upper-triangle-only positive-definiteness convention, on its one
  argument); and `inv` (`invinvpd.rst`: "if x is a matrix, it must be
  square and invertible" -- `v0.74.0` curated this entry but marked it
  `machine_checkable=False` because it had no deterministic invertibility
  test; `v0.75.0` adds one, an exact determinant computation via the same
  cofactor/leading-principal-minor machinery `invpd`'s own check already
  uses, bounded to the same `MAX_CHECKED_MATRIX_DIM`).
- `PredictedOutputClaim`/`detect_predicted_output_claim`/
  `verify_predicted_output`/`analyze_predicted_output` -- a structured,
  never-model-self-labeled representation of a claimed predicted output
  (detected only from a small, explicit set of marker phrases, e.g.
  `"Expected output:"`/`"This should print:"`), with LIMITED deterministic
  verification for a handful of literal cases this module can already
  compute exactly without executing GAUSS: `meanc`/`sumc` of a literal
  matrix, and `inv`/`invpd` of a literal matrix (reusing the same cofactor-
  based inverse the upgraded `inv` precondition check above uses). Every
  other case is honestly `UNVERIFIED`, never guessed. A predicted-output
  verdict is ALWAYS kept structurally separate from `ExecutionEligibility`
  -- a wrong prediction never makes correctly-generated code itself
  ineligible, and a right-looking prediction is never treated as execution
  evidence (see `compute_eligibility(...)`'s own docstring).
- `ValidationCoverage`/`compute_validation_coverage` -- a small, explicit
  summary of which of the above passes actually ran to completion
  (`COMPLETE`/`PARTIAL`/`NOT_APPLICABLE`/`UNKNOWN`) for the current
  code-shaped answer, so a caller (and, eventually, a future controlled-
  execution-handoff milestone) can distinguish "eligible with broad
  evidence" from "eligible with many unknown gaps" -- never implying full
  static validation occurred when only part of it did.

`v0.75.0` deliberately keeps `ExecutionEligibility` a 3-state enum (see that
class's own docstring) rather than adding a fourth "eligible with caveats"
tier: `ValidationCoverage` above already gives a caller everything a fourth
tier would have provided, without proliferating eligibility states.

`v0.76.0` additions -- see `planning/v0.76.0-gauss-syntax-validation.md` for
the full gap analysis this section closes. Live `v0.75.0` evaluation
(scenario `65.8b`) found a real `chol` example whose generated matrix
literal used `;` as a row separator (`x = {-1 0; 0 -1};`) -- not valid GAUSS
syntax (`let.rst`'s own documented row-separator is `,`), but the existing
precondition checker could only, correctly and conservatively, report
`UNVERIFIED`, since it never guesses at an unparseable literal. Real
`tgauss.exe -b` execution (this milestone's own development session)
confirmed the gap is worse than a loud parse error: GAUSS does not reject
that literal -- it silently misparses it into one malformed row containing
a denormal/garbage element. This revealed a missing layer between
"documented call/precondition support" and "future execution eligibility":

- `SyntaxValidationResult`/`validate_syntax(...)` -- a small, bounded,
  provider-independent deterministic syntax checker (matrix-literal row
  separator/shape, balanced delimiters, dangling assignments, malformed
  call-argument separators, unterminated double-quoted strings), never a
  full GAUSS parser. Every rule's provenance (official documentation, real
  `tgauss.exe` execution, or a narrowly justified structural convention) is
  recorded in `_SYNTAX_RULE_REGISTRY`.
- `ValidationCoverage.syntax_check` and `EvidenceProfile`/
  `compute_evidence_profile(...)` -- coverage hardened into a categorical
  (`MINIMAL`/`PARTIAL`/`BROAD`) evidence-breadth judgment, never a numeric
  score, deliberately excluding predicted-output verification (orthogonal
  by design).
- `HandoffReadiness`/`ReadinessResult`/`compute_handoff_readiness(...)` -- a
  new, strictly-downstream-of-`ExecutionEligibility` verdict
  (`NOT_READY`/`REVIEW_REQUIRED`/`HANDOFF_CANDIDATE`) answering a different
  question than `ExecutionEligibility` does: not "is this worth
  validating" but "is there enough deterministic evidence for a FUTURE,
  user-approved, explicit execution-handoff workflow to even consider this
  code." `HANDOFF_CANDIDATE` never means correct, safe, approved, or
  executed -- it means every known-violation and evidence-gap check this
  module can run found nothing wrong and nothing missing. Computed purely
  from this module's own deterministic evidence; the model can never
  influence it, exactly like `ExecutionEligibility`. This milestone adds no
  execution capability of any kind -- no subprocess, no shell, no file
  write, no conversational execution handoff.
"""

from __future__ import annotations

import dataclasses
import enum
import re
from dataclasses import dataclass
from typing import Callable

#: See module docstring's final paragraph for why this is duplicated rather
#: than imported.
_LANGUAGE_CONSTRUCT_KEYWORDS = frozenset({
    "if", "elseif", "else", "endif", "do", "while", "until", "endo", "for", "endfor",
    "proc", "endp", "retp", "local", "print", "struct",
    # v0.82.0: with the counter blanked by `call_scan_text(...)`, a
    # `threadfor i (1, 5, 1);` header reads as `threadfor (...)` -- a header,
    # never a call to a function named `threadfor`.
    "threadfor",
})

_CALL_SHAPED_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _split_top_level_args(raw: str) -> list[str]:
    """Splits `raw` on top-level commas only -- commas nested inside
    `(...)`, `{...}`, or `[...]`, or inside a double-quoted string (v0.76.0
    Phase 6 -- a real comma-containing string argument, e.g.
    `sprintf("%s, %s", a, b)`, must never be mistaken for two arguments),
    do not split. Bounded, conservative: not a real expression parser, just
    enough to separate GAUSS call arguments and documented parameter
    lists."""
    raw = raw.strip()
    if not raw:
        return []
    parts: list[str] = []
    depth = 0
    in_string = False
    current: list[str] = []
    for ch in raw:
        if ch == '"' and not in_string:
            in_string = True
        elif ch == '"' and in_string:
            in_string = False
        if in_string:
            current.append(ch)
            continue
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


#: v0.80.0: the only lines skipped WHOLESALE when scanning for calls --
#: genuine declaration lines, whose `name(...)` text is a definition or a
#: declaration, never a call. Every other keyword-led line (`print`,
#: `retp`, `if`, `elseif`, `while`, `until`, `do while`, `for`) is scanned,
#: because it can legitimately contain real calls (`print invpd(x);`,
#: `retp(meanc(x));`, `if rows(x) > 1;`); the keyword itself is still
#: filtered out symbol-by-symbol wherever this is used.
_DECLARATION_LINE_KEYWORDS = frozenset({"proc", "endp", "local"})

#: v0.82.0: anchored at ANY statement start (line start or right after a
#: `;`), not only at the start of a line, and covers `threadfor` too. Found
#: during v0.82.0 planning: the one-line form real GAUSS accepts
#: (`v = zeros(5, 1); for i(1, 5, 1); v[i] = i^2; endfor;`, confirmed by
#: real `tgauss.exe -b`) left `i(` unblanked, so the loop counter was read
#: as a call to an undocumented function `i`.
_FOR_HEADER_LOOP_VAR_RE = re.compile(
    r"((?:^|;)\s*(?:thread)?for\s+)([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE,
)


def call_scan_text(line: str) -> str:
    """v0.80.0: the ONE shared definition of "which part of this line may
    contain a function call", used by both `extract_generated_calls(...)`
    here and `gauss_conversation_engine.check_generated_symbols(...)`, so the
    call extractor and the unknown-symbol checker can never disagree.

    Replaces a whole-line `startswith(keyword)` skip that had two real
    defects: it dropped every call on any keyword-led line (so a
    hallucinated `print colmean(x);` was neither extracted nor flagged
    unknown, and `print invpd({2 1, 3 2});` escaped its precondition check
    -- reproduced live in evaluation 69.1), and it had no word boundary (so
    `printfm(...)`, `format = ...`, `forecast = arima(...)` lines were
    dropped too -- the same class of defect v0.76.0 fixed for `formula`).

    Returns a string of the SAME LENGTH as `line` (so match offsets stay
    valid against the original text, from which argument text is still
    sliced), or `""` for a declaration line. Double-quoted string contents
    are masked, so `print "Inverse (2x2):";` is never read as a call to
    `Inverse`, and a `for` header's loop variable is blanked, so
    `for i (1, 3, 1);` is never read as a call to `i`."""
    stripped = line.strip().lower()
    if any(_starts_with_keyword(stripped, keyword) for keyword in _DECLARATION_LINE_KEYWORDS):
        return ""
    scan = _QUOTED_STRING_RE.sub(lambda m: "#" * len(m.group(0)), line)
    return _FOR_HEADER_LOOP_VAR_RE.sub(lambda m: m.group(1) + " " * len(m.group(2)), scan)


# ---------------------------------------------------------------------------
# Phase 4: documented call-signature extraction
# ---------------------------------------------------------------------------

SIGNATURE_EXTRACTED = "extracted"
SIGNATURE_UNKNOWN = "unknown"


class TypeClass(str, enum.Enum):
    """v0.75.0: a conservative, categorical classification of a documented
    parameter's (or a literal argument's) type -- NOT a real GAUSS type
    system, and deliberately coarse. `UNKNOWN` is the honest default: it is
    returned whenever the source text (documented or literal) does not
    clearly support one of the other categories, never guessed."""

    SCALAR = "scalar"
    VECTOR = "vector"
    MATRIX = "matrix"
    STRING = "string"
    CONTROL = "control"
    DATASET = "dataset"
    UNKNOWN = "unknown"


class ShapeConstraint(str, enum.Enum):
    """v0.75.0: a small, bounded set of shape constraints this module can
    actually recognize from a documented `NxN`/`Nx1`/`1xN`-style dimension
    string or a literal `{...}` matrix's own real dimensions. `CONFORMABLE`
    and `SPD` are provided for vocabulary completeness (per this
    milestone's own spec) but are not produced by any extractor in this
    version -- conformability/SPD-ness are precondition-level concerns
    (see `check_preconditions(...)`), not per-parameter shape metadata."""

    SQUARE = "square"
    COLUMN_VECTOR = "column_vector"
    ROW_VECTOR = "row_vector"
    CONFORMABLE = "conformable"
    SPD = "spd"
    UNKNOWN = "unknown"


#: v0.75.0: ordered only for deterministic iteration; every matching
#: keyword found in a documented `:type` string is collected (not just the
#: first), so a genuinely documented enumeration like "matrix, vector, or
#: scalar" (real text seen across this session's own docs corpus, e.g.
#: `addition.rst`-style operator pages) becomes a real multi-category
#: allowed set rather than an arbitrarily-picked single category -- see
#: `check_parameter_roles(...)`, which only flags `MISMATCH` when the
#: literal's inferred category is in NONE of the documented categories.
_TYPE_KEYWORDS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"\bstring\b", re.IGNORECASE), TypeClass.STRING.value),
    (re.compile(r"\bstruct\b", re.IGNORECASE), TypeClass.CONTROL.value),
    (re.compile(r"\bdata\s*frame\b", re.IGNORECASE), TypeClass.DATASET.value),
    (re.compile(r"\bmatrix\b", re.IGNORECASE), TypeClass.MATRIX.value),
    (re.compile(r"\barray\b", re.IGNORECASE), TypeClass.MATRIX.value),
    (re.compile(r"\bvector\b", re.IGNORECASE), TypeClass.VECTOR.value),
    (re.compile(r"\bscalar\b", re.IGNORECASE), TypeClass.SCALAR.value),
    (re.compile(r"\binteger\b", re.IGNORECASE), TypeClass.SCALAR.value),
)

#: `NxN`, `KxK`, etc. -- a backreference so only a REPEATED dimension label
#: counts as documented-square, never two merely-similar-looking labels.
_SQUARE_SHAPE_RE = re.compile(r"\b([A-Za-z])[xX]\1\b")
_COLUMN_VECTOR_SHAPE_RE = re.compile(r"\b[A-Za-z0-9]+[xX]1\b")
_ROW_VECTOR_SHAPE_RE = re.compile(r"\b1[xX][A-Za-z0-9]+\b")


def classify_documented_type(type_text: str | None) -> tuple[tuple[str, ...], str]:
    """Conservative, doc-text-only classification -- never infers a
    category from a parameter NAME, only from real documented type text
    (e.g. `meanc.rst`'s own `:type x: NxK matrix`). Returns
    `((TypeClass.UNKNOWN.value,), ShapeConstraint.UNKNOWN.value)` when
    `type_text` is empty or matches none of `_TYPE_KEYWORDS` -- an honest
    gap, never a guess."""
    if not type_text:
        return (TypeClass.UNKNOWN.value,), ShapeConstraint.UNKNOWN.value
    categories: list[str] = []
    for pattern, category in _TYPE_KEYWORDS:
        if pattern.search(type_text) and category not in categories:
            categories.append(category)
    if not categories:
        categories = [TypeClass.UNKNOWN.value]
    shape = ShapeConstraint.UNKNOWN.value
    if TypeClass.MATRIX.value in categories and _SQUARE_SHAPE_RE.search(type_text):
        shape = ShapeConstraint.SQUARE.value
    elif _COLUMN_VECTOR_SHAPE_RE.search(type_text) and not _ROW_VECTOR_SHAPE_RE.search(type_text):
        shape = ShapeConstraint.COLUMN_VECTOR.value
    elif _ROW_VECTOR_SHAPE_RE.search(type_text):
        shape = ShapeConstraint.ROW_VECTOR.value
    return tuple(categories), shape


@dataclass(frozen=True)
class DocumentedParameter:
    """v0.75.0: one documented parameter's own conservative metadata --
    `category`/`shape` are populated ONLY via `classify_documented_type(...)`
    from a real `:type <name>: ...` line found in the documentation's own
    `.. function::` directive block; `source` carries that raw text (or
    `None` when no `:type` line was found for this parameter at all, which
    is distinct from an unclassifiable one)."""

    name: str
    required: bool
    position: int
    category: tuple[str, ...]
    shape: str
    source: str | None


#: v0.75.0: matches a real `:type <name>: <text>` line from the same
#: `.. function::` directive block `extract_documented_signature(...)`
#: already reads `syntax_blocks` from -- `best_match["inputs_section"]`
#: joins each param's own `:param`/`:type` lines with real newlines (see
#: `command_doc_lookup.extract_match(...)`), so this is a genuine per-line
#: match, never a guess across an unrelated parameter's text. A leading
#: `&` (GAUSS's own struct-pointer sigil, e.g. `:type &myPlot: struct
#: pointer`) is stripped from the captured name so it still matches the
#: plain parameter name recorded in `parameter_names`.
_PARAM_TYPE_LINE_RE = re.compile(r":type\s+&?([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+)")


def _extract_documented_parameter_types(inputs_section: str | None) -> dict[str, str]:
    if not inputs_section:
        return {}
    type_by_name: dict[str, str] = {}
    for match in _PARAM_TYPE_LINE_RE.finditer(inputs_section):
        name, type_text = match.group(1), match.group(2).strip()
        if name not in type_by_name:
            type_by_name[name] = type_text
    return type_by_name


#: v0.81.0: the `:rtype` twin of `_PARAM_TYPE_LINE_RE`, read from
#: `best_match["outputs_section"]` (the same `.. function::` block's own
#: `:return`/`:rtype` lines -- see `command_doc_lookup.extract_match(...)`).
_RETURN_TYPE_LINE_RE = re.compile(r":rtype\s+&?([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+)")


def _extract_documented_return_categories(outputs_section: str | None) -> tuple[str, ...]:
    """Only the FIRST `:rtype` line counts: a single-target assignment
    `x = f(...)` receives a function's first return value, and a later
    return (e.g. `rndu`'s `newstate`, an "Opaque vector") never reaches it.
    An unclassifiable first return is `()`, never a guess."""
    if not outputs_section:
        return ()
    match = _RETURN_TYPE_LINE_RE.search(outputs_section)
    if not match:
        return ()
    categories, _shape = classify_documented_type(match.group(2).strip())
    if TypeClass.UNKNOWN.value in categories:
        return ()
    return categories


@dataclass(frozen=True)
class DocumentedSignature:
    """`arg_ranges` holds one `(min_args, max_args)` pair per documented
    overload found for `symbol` -- a generated call is argument-count
    COMPATIBLE if its count falls in ANY of these ranges (real documented
    functions in this codebase's own docs, e.g. `tscsFit`, have more than
    one overload). `extraction_status == UNKNOWN` (with empty `arg_ranges`)
    means the documentation's own format did not support reliable
    extraction -- never a fabricated signature. v0.75.0: `parameters` is a
    best-effort, SINGLE flattened parameter-metadata list (position/
    required/category/shape) built from `parameter_names` -- consistent
    with this module's existing overload-merging simplification (see
    `test_04_multiple_overloads_produce_multiple_ranges`), it does not
    track per-overload parameter metadata separately. Always `()` when
    `extraction_status == SIGNATURE_UNKNOWN`."""

    symbol: str
    arg_ranges: tuple[tuple[int, int], ...]
    parameter_names: tuple[str, ...]
    source: str | None
    extraction_status: str
    parameters: tuple[DocumentedParameter, ...] = ()
    #: v0.81.0: the categories `classify_documented_type(...)` gives the
    #: FIRST documented `:rtype` line in the same `.. function::` block
    #: (e.g. real `rndu.rst`: `:rtype y: RxC matrix` -> `("matrix",)`) --
    #: the value a single-target assignment `x = f(...)` receives in GAUSS.
    #: `()` when no `:rtype` line exists or it is unclassifiable; used only
    #: by `resolve_argument_category(...)` to trace a variable to the call
    #: that produced it, never to claim anything about the call itself.
    return_categories: tuple[str, ...] = ()


#: v0.82.0: a documented `...` (`fred_load(formula[, ...])`, `gmmFit(&fct, y,
#: ...[, gCtl])`) means "any number of further arguments" -- it was counted
#: as exactly one, so `fred_load`'s own documented key/value example (7
#: arguments) was a count mismatch, masked only by that example being
#: spliced in from parameter prose (live finding 71.5's extraction defect).
VARIADIC_MAX_ARGS = 10**6


def _bounded_max(names: tuple[str, ...]) -> int:
    return VARIADIC_MAX_ARGS if "..." in names else len(names)


def _parse_signature_occurrence(raw_args: str) -> tuple[int, int, tuple[str, ...]]:
    """`raw_args` is the text between one documented call's own parentheses,
    e.g. `"y, x, grp[, tsc]"` (the real, verified `tscsFit` documented
    form). A `[...]` group marks its own contents as optional, trailing
    arguments -- confirmed against real `tsmt/tscsfit.rst` text in this
    milestone's own development. Returns `(min_args, max_args, names)`."""
    bracket_idx = raw_args.find("[")
    if bracket_idx == -1:
        names = tuple(_split_top_level_args(raw_args))
        return len(names) - (1 if "..." in names else 0), _bounded_max(names), names
    required_part = raw_args[:bracket_idx]
    optional_part = raw_args[bracket_idx:].strip()
    if optional_part.startswith("[") and optional_part.endswith("]"):
        optional_part = optional_part[1:-1]
    optional_part = optional_part.lstrip(",").strip()
    required_names = tuple(_split_top_level_args(required_part))
    # v0.82.0: NESTED optional groups (`plotSave(filename[, size[, units[,
    # dpi]]])`, the real plotsave.rst form) are flattened before splitting.
    # `_split_top_level_args` treats `[` as nesting, so `size[, units[,
    # dpi]]` used to come back as ONE name (max 2 args). That was masked
    # until v0.82.0 by a 4-arg example spliced in from the `dpi` parameter's
    # prose (the same extraction defect as live finding 71.5); fixing that
    # alone would have made a valid 4-arg call a false count mismatch.
    optional_names = tuple(_split_top_level_args(optional_part.replace("[", "").replace("]", "")))
    all_names = required_names + optional_names
    return len(required_names) - (1 if "..." in required_names else 0), _bounded_max(all_names), all_names


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

    # v0.75.0: `:type` lines, when present, come from the SAME `.. function::`
    # directive block already parsed for syntax/names -- see
    # `_extract_documented_parameter_types(...)`'s own docstring for why this
    # is a real per-line match, never a guess.
    type_by_name = _extract_documented_parameter_types(best_match.get("inputs_section"))
    required_count = min(lo for lo, _hi in ranges)
    parameters = tuple(
        DocumentedParameter(
            name=name, required=position < required_count, position=position,
            category=classify_documented_type(type_by_name.get(name))[0],
            shape=classify_documented_type(type_by_name.get(name))[1],
            source=type_by_name.get(name),
        )
        for position, name in enumerate(names)
    )
    return DocumentedSignature(
        symbol=symbol, arg_ranges=tuple(ranges), parameter_names=tuple(names),
        source=best_match.get("file_path"), extraction_status=SIGNATURE_EXTRACTED,
        parameters=parameters,
        return_categories=_extract_documented_return_categories(best_match.get("outputs_section")),
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
    #: v0.81.0: 0-based offset of the call's name within its line, so a
    #: same-line assignment (`x = {1,2,3}; m = meanc(x);`, a form models
    #: write routinely) can be ordered before or after the call. `None`
    #: (hand-built calls) means "end of the line".
    column: int | None = None


def extract_generated_calls(code: str) -> tuple[GeneratedCall, ...]:
    """Conservative: shares `call_scan_text(...)` with
    `gauss_conversation_engine.check_generated_symbols(...)` -- not a GAUSS
    parser, no type inference, never interprets prose as code. Argument
    text is split at the top level only, so `f(g(x), y)` is extracted as a
    call to `f` with two top-level arguments (`g(x)` and `y`); `g` is
    separately extracted as its own nested call on the same line. Matches
    and paren-matching run against the masked scan text; argument text is
    sliced from the original line (same offsets), so a string-literal
    argument keeps its real content and quotes."""
    calls: list[GeneratedCall] = []
    for line_no, line in enumerate(code.splitlines(), start=1):
        scan = call_scan_text(line)
        if not scan:
            continue
        for match in _CALL_SHAPED_RE.finditer(scan):
            symbol = match.group(1)
            if symbol.lower() in _LANGUAGE_CONSTRUCT_KEYWORDS:
                continue
            close_idx = _find_matching_paren(scan, match.end() - 1)
            if close_idx is None:
                continue  # unterminated on this line -- skip rather than guess
            raw = line[match.end():close_idx]
            args = tuple(_split_top_level_args(raw))
            calls.append(GeneratedCall(
                symbol=symbol, argument_count=len(args), raw_arguments=args, line_number=line_no,
                column=match.start(),
            ))
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

    allowed = sorted({
        f"{lo}" if lo == hi else (f"{lo} or more" if hi >= VARIADIC_MAX_ARGS else f"{lo}-{hi}")
        for lo, hi in signature.arg_ranges
    })
    return CallValidationResult(
        symbol=call.symbol, documented=True, signature_known=True,
        argument_count_status=SignatureCompatibility.INCOMPATIBLE.value,
        issues=(f"documented form(s) accept {' or '.join(allowed)} argument(s); this call passed {call.argument_count}",),
        source=signature.source,
    )


# ---------------------------------------------------------------------------
# Phase 6 / 18 (v0.75.0): basic literal type/shape inference and
# parameter-role validation
# ---------------------------------------------------------------------------

#: v0.81.0: accepts exponent and leading-dot forms (`1e5`, `1.5E-3`, `.5`).
#: The real `meanc.rst` example is `meanc(rndu(1e5, 4))`, and models copy
#: it almost verbatim (runs 63.2, 70.6) -- `1e5` used to be UNKNOWN, which
#: alone kept `x = rndu(1e5, 4);` short of complete role coverage.
_NUMERIC_LITERAL_RE = re.compile(r"^-?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?$")
_STRING_LITERAL_RE = re.compile(r'^"(?:[^"\\]|\\.)*"$|^\'(?:[^\'\\]|\\.)*\'$')


def infer_literal_category(argument: str) -> tuple[str, str]:
    """Bounded, deterministic literal-expression classifier -- NOT arbitrary
    expression evaluation. Recognizes exactly three shapes of GAUSS literal:
    a bare numeric constant (`SCALAR`), a quoted string (`STRING`), and a
    `{...}` matrix/vector literal (parsed via the same `_parse_literal_matrix`
    logic the `invpd` precondition check already uses, so a 1x1 literal is
    `SCALAR`, a single-column or single-row literal is `VECTOR` with the
    corresponding shape, and anything else is `MATRIX`, `SQUARE` only when
    genuinely square). A runtime variable, a function call, or any other
    expression (e.g. the real documented `invpd(x'x)` OLS example) always
    returns `(TypeClass.UNKNOWN.value, ShapeConstraint.UNKNOWN.value)` --
    this function never partially evaluates a runtime expression."""
    argument = argument.strip()
    if _STRING_LITERAL_RE.match(argument):
        return TypeClass.STRING.value, ShapeConstraint.UNKNOWN.value
    if _NUMERIC_LITERAL_RE.match(argument):
        return TypeClass.SCALAR.value, ShapeConstraint.UNKNOWN.value
    if argument.startswith("{") and argument.endswith("}"):
        rows = _parse_literal_matrix(argument)
        if rows is None:
            return TypeClass.UNKNOWN.value, ShapeConstraint.UNKNOWN.value
        height, width = len(rows), len(rows[0])
        if height == 1 and width == 1:
            return TypeClass.SCALAR.value, ShapeConstraint.UNKNOWN.value
        if width == 1:
            return TypeClass.VECTOR.value, ShapeConstraint.COLUMN_VECTOR.value
        if height == 1:
            return TypeClass.VECTOR.value, ShapeConstraint.ROW_VECTOR.value
        if height == width:
            return TypeClass.MATRIX.value, ShapeConstraint.SQUARE.value
        return TypeClass.MATRIX.value, ShapeConstraint.UNKNOWN.value
    return TypeClass.UNKNOWN.value, ShapeConstraint.UNKNOWN.value


class ParameterRoleStatus(str, enum.Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ParameterRoleCheck:
    """One positional argument-vs-documented-parameter comparison.
    `MISMATCH` is produced ONLY when both the documented category and the
    argument's own inferred literal category are confidently known and they
    genuinely do not overlap -- e.g. a string literal passed where the
    documentation's own `:type` text names only `matrix`. Anything the
    literal inferrer or the documentation extractor could not confidently
    classify is `UNKNOWN`, never guessed into a `MISMATCH`."""

    symbol: str
    position: int
    parameter_name: str | None
    documented_category: tuple[str, ...]
    inferred_category: str
    status: str
    explanation: str
    #: v0.81.0: where `inferred_category` came from -- one of the
    #: `ArgumentOrigin` values. Defaulted so pre-v0.81.0 constructions of
    #: this type remain valid unchanged.
    origin: str = "literal"


#: v0.81.0: which literal categories a DOCUMENTED category accepts. Before
#: v0.81.0 the role check required an exact category match, so
#: `meanc({1,2,3})` and `meanc(5)` were MISMATCH -> NOT_READY, although both
#: are ordinary GAUSS: everything numeric in GAUSS is a matrix. The docs say
#: so themselves -- `stof.rst`: "x will be a 1x1 matrix equal to 3.14";
#: `between.rst`: `:type left: 1x1 matrix`; and `meanc.rst` documents its
#: own column-vector result as `:rtype y: Kx1 matrix`. So a documented
#: `matrix` accepts a vector or scalar, and a documented `vector` accepts a
#: scalar (a 1x1 vector). The reverse never holds: a `{1 2}` literal passed
#: where the docs name only `scalar` stays a MISMATCH, and `string`/
#: `control`/`dataset` remain distinct from every numeric category, so
#: `meanc("abc")` is still a MISMATCH.
_CATEGORY_ACCEPTS: dict[str, frozenset[str]] = {
    TypeClass.MATRIX.value: frozenset({TypeClass.MATRIX.value, TypeClass.VECTOR.value, TypeClass.SCALAR.value}),
    TypeClass.VECTOR.value: frozenset({TypeClass.VECTOR.value, TypeClass.SCALAR.value}),
}


def _category_accepted(inferred: str, documented: tuple[str, ...]) -> bool:
    return any(inferred in _CATEGORY_ACCEPTS.get(doc, frozenset({doc})) for doc in documented)


class ArgumentOrigin(str, enum.Enum):
    """v0.81.0: how `resolve_argument_category(...)` classified an argument.
    `TRACED_LITERAL` and `DOCUMENTED_RETURN` both require the variable's
    single governing assignment to be found by `_governing_assignment(...)`
    -- see that function for every case that is refused instead."""

    LITERAL = "literal"
    TRACED_LITERAL = "traced_literal"
    DOCUMENTED_RETURN = "documented_return"
    UNRESOLVED = "unresolved"


#: v0.82.0: the categories an indexed write provably leaves unchanged -- see
#: `resolve_argument_category(...)`.
_NUMERIC_CATEGORIES = frozenset({TypeClass.SCALAR.value, TypeClass.VECTOR.value, TypeClass.MATRIX.value})

#: A whole right-hand side that is exactly one call, `f(...)`, and nothing
#: else (no trailing transpose, operator, or index).
_SINGLE_CALL_RHS_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def resolve_argument_category(
    argument: str, *, code: str | None = None, line_number: int | None = None, column: int | None = None,
    signatures: "dict[str, DocumentedSignature] | None" = None,
) -> tuple[tuple[str, ...], str]:
    """v0.81.0: returns `(categories, origin)` for one call argument.

    1. A literal (`5`, `1e5`, `"s"`, `{1 2, 3 4}`) -> `infer_literal_category`.
    2. A simple identifier (optionally `x'`) whose governing assignment
       earlier in the SAME snippet (see `_governing_assignment(...)`) is
       `x = <literal>;` -> that literal's category (`TRACED_LITERAL`).
    3. ... or is `x = f(...);`, exactly one call to a symbol whose own docs
       give a classifiable first `:rtype` -> those categories
       (`DOCUMENTED_RETURN`, e.g. `x = rndu(100, 4);` -> `matrix`).

    Anything else -- an expression (`x'x`, `x*2`), an untraceable or
    ambiguously-written variable, a call with no `:rtype` -- is
    `((UNKNOWN,), UNRESOLVED)`. Nothing is ever evaluated."""
    category, _shape = infer_literal_category(argument)
    if category != TypeClass.UNKNOWN.value:
        return (category,), ArgumentOrigin.LITERAL.value
    unresolved = ((TypeClass.UNKNOWN.value,), ArgumentOrigin.UNRESOLVED.value)
    argument = argument.strip()
    if code is None or not _SIMPLE_IDENTIFIER_RE.fullmatch(argument):
        return unresolved
    name = argument.rstrip("'")
    rhs = _governing_assignment(name, code=code, line_number=line_number, column=column)
    numeric_only = False
    if rhs is None:
        # v0.82.0 (option B, user-approved): a second, category-only pass
        # that looks through indexed writes (`v[i] = i^2;`, typically inside
        # a preallocate-and-fill loop). Real `tgauss.exe -b` (GAUSS 26.1.4,
        # 2026-10-08) shows an indexed write cannot change a numeric
        # variable's shape: a write past the end is `G0058 Index out of
        # range` in 1-D and 2-D (GAUSS never grows the matrix), `v = {};
        # v[1] = 1;` is also `G0058`, and storing a string into an element
        # of a 3x1 numeric matrix leaves it a 3x1 matrix (`type` 6). It is
        # accepted only for a NUMERIC governing category: `s = "hello";
        # s[1] = 5;` is `G0071 Type mismatch`, so string targets keep
        # refusing. The precondition tracer never takes this path.
        rhs = _governing_assignment(
            name, code=code, line_number=line_number, column=column, allow_indexed_writes=True,
        )
        numeric_only = True
    if rhs is None:
        return unresolved
    categories: tuple[str, ...] | None = None
    origin = ArgumentOrigin.UNRESOLVED.value
    category, _shape = infer_literal_category(rhs)
    if category != TypeClass.UNKNOWN.value:
        categories, origin = (category,), ArgumentOrigin.TRACED_LITERAL.value
    else:
        call_match = _SINGLE_CALL_RHS_RE.match(rhs)
        if call_match and signatures:
            if _find_matching_paren(rhs, call_match.end() - 1) == len(rhs) - 1:
                signature = signatures.get(call_match.group(1).lower())
                if signature is not None and signature.return_categories:
                    categories, origin = signature.return_categories, ArgumentOrigin.DOCUMENTED_RETURN.value
    if categories is None:
        return unresolved
    if numeric_only and not all(c in _NUMERIC_CATEGORIES for c in categories):
        return unresolved
    return categories, origin


def check_parameter_roles(
    call: GeneratedCall, *, signature: DocumentedSignature | None, code: str | None = None,
    signatures: "dict[str, DocumentedSignature] | None" = None,
) -> tuple[ParameterRoleCheck, ...]:
    """Positional: argument `i` is compared against `signature.parameters[i]`.
    An extra argument beyond the documented parameter list is skipped here
    (argument-COUNT mismatches are already `validate_call(...)`'s own job,
    per `CallValidationResult`); this function never attempts to guess a
    role for a parameter with no reliable documented category. Returns `()`
    when `signature` is `None` or has no extracted parameter metadata at
    all -- an honest "nothing to check", not a fabricated pass.

    v0.81.0: given `code` (the comment-stripped snippet the call came from)
    and `signatures` (every documented signature known for this snippet),
    a variable argument is traced to its own assignment via
    `resolve_argument_category(...)`. Live evaluations 66.1/66.2/66.10/70.6
    found that the way models naturally write GAUSS -- assign, then call --
    always left this check UNKNOWN, so the evidence profile could never be
    BROAD. A `DOCUMENTED_RETURN` origin can produce MATCH or UNKNOWN but
    never MISMATCH: a documented "matrix" return may be 1x1 at run time
    (e.g. `sumc` of a column vector), so disagreement there is a gap, not a
    known violation."""
    if signature is None or not signature.parameters:
        return ()
    checks: list[ParameterRoleCheck] = []
    for position, argument in enumerate(call.raw_arguments):
        if position >= len(signature.parameters):
            break
        param = signature.parameters[position]
        inferred, origin = resolve_argument_category(
            argument, code=code, line_number=call.line_number, column=call.column, signatures=signatures,
        )
        inferred_label = "/".join(inferred)
        documented = param.category
        traced = {
            ArgumentOrigin.TRACED_LITERAL.value: f" (traced to its literal assignment `{argument.strip()} = ...`)",
            ArgumentOrigin.DOCUMENTED_RETURN.value: (
                f" (traced to `{argument.strip()} = ...`, a call whose documented return type is {inferred_label})"
            ),
        }.get(origin, "")
        if TypeClass.UNKNOWN.value in documented or TypeClass.UNKNOWN.value in inferred:
            status = ParameterRoleStatus.UNKNOWN.value
            explanation = (
                "the documented parameter type or this argument's own literal category could not be "
                "confidently determined"
            )
        elif all(_category_accepted(c, documented) for c in inferred):
            status = ParameterRoleStatus.MATCH.value
            explanation = f"the argument's category ({inferred_label}){traced} matches the documented parameter type"
        elif origin == ArgumentOrigin.DOCUMENTED_RETURN.value:
            status = ParameterRoleStatus.UNKNOWN.value
            explanation = (
                f"the argument{traced} may not fit the documented type for parameter {param.name!r} "
                f"({'/'.join(documented)}); a documented return type is not precise enough to call this a mismatch"
            )
        else:
            status = ParameterRoleStatus.MISMATCH.value
            explanation = (
                f"the argument's literal category ({inferred_label}){traced} does not match the documented type "
                f"for parameter {param.name!r} ({'/'.join(documented)})"
            )
        checks.append(ParameterRoleCheck(
            symbol=call.symbol, position=position, parameter_name=param.name,
            documented_category=documented, inferred_category=inferred_label,
            status=status, explanation=explanation, origin=origin,
        ))
    return tuple(checks)


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
    #: v0.75.0: which positional argument (0-indexed) of the call this
    #: precondition applies to -- `invpd`/`inv`/`chol` all constrain their
    #: ONE argument (position 0, the default), but `solpd(b, A)`'s
    #: documented precondition applies to its SECOND argument, `A`
    #: (position 1). Added rather than hardcoding position 0 everywhere so
    #: a genuinely different documented argument position is never silently
    #: mischecked.
    argument_index: int = 0


#: Hand-curated, doc-verified -- every entry's `description`/`source` was
#: checked in this milestone's own development session against the real,
#: local `invinvpd.rst`/`solpd.rst`/`chol.rst` cited (see module docstring's
#: Finding 3 and this module's own v0.75.0 docstring section). Small and
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
            symbol="inv", kind=PreconditionKind.PROPERTY.value, machine_checkable=True,
            source="invinvpd.rst",
            description=(
                'invinvpd.rst: "For inv, if x is a matrix, it must be square and invertible." '
                "v0.74.0 curated this entry but left it machine_checkable=False (no deterministic "
                "invertibility test existed yet). v0.75.0 upgrades it: for a literal matrix, "
                "squareness and a nonzero determinant (exact cofactor-expansion computation, the "
                "same machinery invpd's own leading-principal-minor check already uses) are both "
                "deterministically checkable without executing GAUSS -- see check_inv_precondition(...)."
            ),
        ),
    ),
    "solpd": (
        DocumentedPrecondition(
            symbol="solpd", kind=PreconditionKind.PROPERTY.value, machine_checkable=True, argument_index=1,
            source="solpd.rst",
            description=(
                'solpd.rst: "param A: NxN symmetric positive definite matrix..."; and, in its own '
                'Remarks: "solpd does not check to see that the matrix A is symmetric. solpd will '
                'look only at the upper half of the matrix including the principal diagonal." and '
                '"If the A matrix is not positive definite: trap 1 -> return scalar error code 30; '
                'trap 0 -> terminate with an error message." Checked on the SECOND argument (A), '
                "using solpd's own documented upper-triangle-only convention (see "
                "check_solpd_precondition(...)) rather than requiring literal symmetry the function "
                "itself does not require."
            ),
        ),
    ),
    "chol": (
        DocumentedPrecondition(
            symbol="chol", kind=PreconditionKind.PROPERTY.value, machine_checkable=True,
            source="chol.rst",
            description=(
                'chol.rst: "Computes the Cholesky decomposition of a symmetric, positive definite '
                'square matrix."; Remarks: "chol does not check to see that the matrix is symmetric. '
                'chol will look only at the upper half of the matrix including the principal '
                'diagonal... If the matrix x is symmetric but not positive definite... an error '
                '[is generated]." Checked the same upper-triangle-only way as solpd (see '
                "check_chol_precondition(...))."
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


#: v0.82.0: `threadfor`/`threadbegin` (and their closers) added -- found
#: during v0.82.0 planning to be invisible to every block-aware check, so a
#: write inside a parallel block was treated as a straight-line top-level
#: write. Fail-closed: a write inside one now makes the variable untraceable.
_BLOCK_OPEN_KEYWORDS = ("if", "for", "do", "proc", "keyword", "threadfor", "threadbegin")
_BLOCK_CLOSE_KEYWORDS = ("endif", "endfor", "endo", "endp", "threadendfor", "threadend")


def _masked_statements(code: str):
    """Yields `(line_number, start, end, masked, original)` for each
    `;`-separated statement, string contents masked (same `_QUOTED_STRING_RE`
    masking `call_scan_text(...)` uses) so a `;` or `=` inside a string is
    never read as code. `start`/`end` are column offsets within the line."""
    for line_no, line in enumerate(code.splitlines(), start=1):
        masked = _QUOTED_STRING_RE.sub(lambda m: "#" * len(m.group(0)), line)
        start = 0
        while start < len(masked):
            semi = masked.find(";", start)
            end = len(masked) if semi == -1 else semi
            if masked[start:end].strip():
                yield line_no, start, end, masked[start:end], line[start:end]
            start = end + 1


def _governing_assignment(
    name: str, *, code: str, line_number: int | None = None, column: int | None = None,
    allow_indexed_writes: bool = False,
) -> str | None:
    """v0.81.0: the ONE shared answer to "which assignment gives `name` its
    value at this call?", used by both the role check and the precondition
    tracer. Returns the right-hand-side text of the most recent plain
    top-level `name = <rhs>;` statement that ENDS before the call position
    `(line_number, column)` (`None` means end of line / end of code), or
    `None` when no such assignment exists or the answer would be a guess.

    Replaces the pre-v0.81.0 precondition tracer's whole-code `matches[-1]`,
    which had two defects: an assignment written AFTER the call drove the
    verdict (`x = {2 1, 1 2}; y = invpd(x); x = {-1 0, 0 -1};` was VIOLATED),
    and a literal followed by an operator (`x = {2 1, 1 2} * -1;`) was read
    as the bare literal. Refuses (returns `None`) whenever `name` is also
    written in any way this function does not model: inside a control-flow
    or `proc` block, as an indexed or member target (`x[1,1] = 5;`), as one
    of several targets (`{x, y} = f();`), as a `for` loop variable, or by
    `clear`. A refusal is always an honest gap, never a fabricated value.

    v0.82.0: `allow_indexed_writes=True` skips indexed writes (`x[i] = ...`,
    anywhere, including inside a block) instead of refusing on them. Only
    the role check's CATEGORY question may ask for this -- see
    `resolve_argument_category(...)` for the real `tgauss.exe -b` evidence
    that an indexed write cannot change a numeric variable's shape. The
    precondition tracer never does: an indexed write changes VALUES, so the
    governing literal is no longer evidence of what the call receives."""
    target = (
        line_number if line_number is not None else float("inf"),
        column if column is not None else float("inf"),
    )
    escaped = re.escape(name)
    plain_re = re.compile(rf"^\s*(?:let\s+)?{escaped}\s*=(?!=)", re.IGNORECASE)
    other_write_res = (
        re.compile(rf"^\s*{escaped}\s*\.[A-Za-z_]", re.IGNORECASE),
        re.compile(rf"^\s*\{{[^}}]*\b{escaped}\b[^}}]*\}}\s*=(?!=)", re.IGNORECASE),
        re.compile(rf"^\s*(?:thread)?for\s+{escaped}\b", re.IGNORECASE),
        re.compile(rf"^\s*clear(?:all)?\b.*\b{escaped}\b", re.IGNORECASE),
    )
    indexed_write_re = re.compile(rf"^\s*{escaped}\s*\[", re.IGNORECASE)
    depth = 0
    governing: str | None = None
    for line_no, _start, end, masked, original in _masked_statements(code):
        lowered = masked.strip().lower()
        if any(_starts_with_keyword(lowered, kw) for kw in _BLOCK_CLOSE_KEYWORDS):
            depth = max(0, depth - 1)
            continue
        if any(r.search(masked) for r in other_write_res):
            return None
        if indexed_write_re.search(masked):
            if allow_indexed_writes:
                continue
            return None
        plain = plain_re.search(masked)
        if plain is not None:
            if depth > 0:
                return None
            if (line_no, end) < target:
                governing = original[plain.end():].strip()
        if any(_starts_with_keyword(lowered, kw) for kw in _BLOCK_OPEN_KEYWORDS):
            depth += 1
    return governing


def _find_literal_matrix_for_argument(
    argument: str, *, code: str, line_number: int | None = None, column: int | None = None,
) -> list[list[float]] | None:
    """`argument` is the raw text of one call argument (e.g. `"x"` or
    `"{1 2, 2 1}"`). If it is itself a `{...}` literal, parses it directly.
    If it is a simple identifier (optionally transposed, `x'`), uses the
    right-hand side of its governing assignment (`_governing_assignment(
    ...)`, v0.81.0), but only when that whole right-hand side is a `{...}`
    literal. Any more complex expression (e.g. the real documented
    `invpd(x'x)` OLS example, a matrix product) is deliberately left
    unresolved -- this function never partially evaluates a runtime
    expression, and returns `None` (never a fabricated matrix) in that
    case."""
    argument = argument.strip()
    if "{" in argument:
        return _parse_literal_matrix(argument)
    if _SIMPLE_IDENTIFIER_RE.fullmatch(argument):
        rhs = _governing_assignment(argument.rstrip("'"), code=code, line_number=line_number, column=column)
        if rhs is not None and rhs.startswith("{") and rhs.endswith("}"):
            return _parse_literal_matrix(rhs)
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


def _reflect_upper_triangle_to_symmetric(rows: list[list[float]]) -> list[list[float]]:
    """v0.75.0: mirrors `solpd`/`chol`'s own documented behavior ("will look
    only at the upper half of the matrix including the principal diagonal")
    -- builds the symmetric matrix the function actually OPERATES ON from a
    (possibly non-symmetric) literal input, so this module's own
    positive-definiteness check tests exactly what the real function tests,
    never a stricter symmetry requirement the function itself does not
    impose. Callers must ensure `rows` is square first."""
    n = len(rows)
    reflected = [row[:] for row in rows]
    for i in range(n):
        for j in range(i):
            reflected[i][j] = reflected[j][i]
    return reflected


#: v0.75.0: exact tolerance for treating a literal-matrix determinant as
#: zero (singular) -- matches the `<= 0`/strict-positivity discipline
#: `_leading_principal_minors_positive` already uses for exact/rational
#: literal input.
_SINGULAR_DETERMINANT_TOLERANCE = 1e-9


def _cofactor(matrix: list[list[float]], row: int, col: int) -> float:
    minor = [r[:col] + r[col + 1:] for k, r in enumerate(matrix) if k != row]
    sign = 1.0 if (row + col) % 2 == 0 else -1.0
    return sign * _determinant(minor)


def _matrix_inverse(rows: list[list[float]]) -> list[list[float]] | None:
    """Exact adjugate/cofactor matrix inverse, bounded to
    `MAX_CHECKED_MATRIX_DIM` by every caller -- reuses `_determinant(...)`,
    the same machinery `_leading_principal_minors_positive(...)` already
    uses. Returns `None` for a singular (or non-square) matrix rather than
    raising or fabricating a result -- used both by the upgraded `inv`
    precondition check and by `verify_predicted_output(...)`'s own bounded
    deterministic output checker."""
    n = len(rows)
    if n == 0 or any(len(row) != n for row in rows):
        return None
    det = _determinant(rows)
    if abs(det) <= _SINGULAR_DETERMINANT_TOLERANCE:
        return None
    cofactors = [[_cofactor(rows, i, j) for j in range(n)] for i in range(n)]
    # Adjugate = transpose of the cofactor matrix.
    return [[cofactors[j][i] / det for j in range(n)] for i in range(n)]


def _literal_matrix_for_precondition_argument(
    call: GeneratedCall, *, argument_index: int, code: str,
) -> tuple[list[list[float]] | None, str | None]:
    """Shared bounds/lookup logic for every precondition checker below.
    Returns `(rows, unverified_reason)` -- exactly one is non-`None`. Never
    raises on a short argument list (e.g. `solpd(b)` missing its documented
    second argument)."""
    if argument_index >= len(call.raw_arguments):
        return None, "the documented argument this precondition applies to was not found in this call"
    rows = _find_literal_matrix_for_argument(
        call.raw_arguments[argument_index], code=code, line_number=call.line_number, column=call.column,
    )
    if rows is None:
        return None, (
            "the input is a runtime value or expression, not a literal matrix -- this cannot be checked "
            "without executing GAUSS, which this module never does"
        )
    if len(rows) > MAX_CHECKED_MATRIX_DIM or len(rows[0]) > MAX_CHECKED_MATRIX_DIM:
        return None, (
            f"the literal input matrix exceeds the {MAX_CHECKED_MATRIX_DIM}x{MAX_CHECKED_MATRIX_DIM} "
            "bound this version checks deterministically"
        )
    return rows, None


def check_invpd_precondition(call: GeneratedCall, *, code: str) -> PreconditionCheck:
    precondition = _PRECONDITION_INDEX["invpd"][0]
    rows, reason = _literal_matrix_for_precondition_argument(call, argument_index=precondition.argument_index, code=code)
    if rows is None:
        return PreconditionCheck(precondition, PreconditionStatus.UNVERIFIED.value, reason)
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


def check_inv_precondition(call: GeneratedCall, *, code: str) -> PreconditionCheck:
    """v0.75.0: upgraded from `machine_checkable=False` in v0.74.0 -- see
    `_PRECONDITION_INDEX["inv"]`'s own description for why this is now
    deterministically checkable for a literal matrix."""
    precondition = _PRECONDITION_INDEX["inv"][0]
    rows, reason = _literal_matrix_for_precondition_argument(call, argument_index=precondition.argument_index, code=code)
    if rows is None:
        return PreconditionCheck(precondition, PreconditionStatus.UNVERIFIED.value, reason)
    if not _is_square(rows):
        return PreconditionCheck(
            precondition, PreconditionStatus.VIOLATED.value,
            "the literal input matrix is not square, so it cannot be inverted by inv",
        )
    if abs(_determinant(rows)) <= _SINGULAR_DETERMINANT_TOLERANCE:
        return PreconditionCheck(
            precondition, PreconditionStatus.VIOLATED.value,
            "the literal input matrix has a zero determinant (singular), so it is not invertible",
        )
    return PreconditionCheck(
        precondition, PreconditionStatus.SATISFIED.value,
        "the literal input matrix is square with a nonzero determinant (verified by exact determinant computation)",
    )


def _check_upper_triangle_positive_definite(
    call: GeneratedCall, *, precondition: DocumentedPrecondition, code: str,
) -> PreconditionCheck:
    """Shared implementation for `solpd`/`chol`: both document that they
    "look only at the upper half of the matrix including the principal
    diagonal" rather than requiring literal symmetry -- see each entry's own
    `_PRECONDITION_INDEX` description for the exact quoted text."""
    rows, reason = _literal_matrix_for_precondition_argument(call, argument_index=precondition.argument_index, code=code)
    if rows is None:
        return PreconditionCheck(precondition, PreconditionStatus.UNVERIFIED.value, reason)
    if not _is_square(rows):
        return PreconditionCheck(
            precondition, PreconditionStatus.VIOLATED.value,
            f"the literal input matrix is not square, so it cannot be positive definite ({precondition.symbol} "
            "requires a square matrix)",
        )
    reflected = _reflect_upper_triangle_to_symmetric(rows)
    if not _leading_principal_minors_positive(reflected):
        return PreconditionCheck(
            precondition, PreconditionStatus.VIOLATED.value,
            f"the matrix implied by the literal input's own upper triangle (the convention {precondition.symbol} "
            "itself documents using) is not positive definite",
        )
    return PreconditionCheck(
        precondition, PreconditionStatus.SATISFIED.value,
        f"the matrix implied by the literal input's own upper triangle is positive definite (verified by "
        f"leading-principal-minor computation, following {precondition.symbol}'s own documented upper-triangle "
        "convention)",
    )


def check_solpd_precondition(call: GeneratedCall, *, code: str) -> PreconditionCheck:
    return _check_upper_triangle_positive_definite(call, precondition=_PRECONDITION_INDEX["solpd"][0], code=code)


def check_chol_precondition(call: GeneratedCall, *, code: str) -> PreconditionCheck:
    return _check_upper_triangle_positive_definite(call, precondition=_PRECONDITION_INDEX["chol"][0], code=code)


#: v0.75.0: dispatch from symbol to its deterministic checker -- every entry
#: here must have a matching `machine_checkable=True` entry in
#: `_PRECONDITION_INDEX`; `check_preconditions(...)` never calls a checker
#: for a precondition it does not itself mark `machine_checkable`.
_PRECONDITION_CHECKERS: dict[str, "Callable[[GeneratedCall], PreconditionCheck]"] = {
    "invpd": check_invpd_precondition,
    "inv": check_inv_precondition,
    "solpd": check_solpd_precondition,
    "chol": check_chol_precondition,
}


def check_preconditions(call: GeneratedCall, *, code: str) -> tuple[PreconditionCheck, ...]:
    """Never fabricates `SATISFIED` -- a precondition with no implemented
    deterministic validator is always reported `UNVERIFIED`, explicitly
    naming that no validator exists in this version, rather than being
    silently omitted."""
    checks: list[PreconditionCheck] = []
    checker = _PRECONDITION_CHECKERS.get(call.symbol.lower())
    for precondition in documented_preconditions(call.symbol):
        if precondition.machine_checkable and checker is not None:
            checks.append(checker(call, code=code))
        else:
            checks.append(PreconditionCheck(
                precondition, PreconditionStatus.UNVERIFIED.value,
                "no deterministic validator is implemented for this precondition in this version",
            ))
    return tuple(checks)


# ---------------------------------------------------------------------------
# Phases 2-7 (v0.76.0): deterministic GAUSS syntax validation
#
# See `planning/v0.76.0-gauss-syntax-validation.md` Section 3.2/3.3 for the
# full gap analysis and per-rule provenance table this section implements.
# The motivating regression: a real live `chol` scenario (evaluation 65.8b)
# produced a matrix literal using `;` as a row separator
# (`x = {-1 0; 0 -1};`). `_find_literal_matrix_for_argument` correctly
# declined to guess at it, reporting the `chol` precondition `UNVERIFIED` --
# safe, but silent about the fact that the literal itself is not well-formed
# GAUSS. Real `tgauss.exe -b` execution (this milestone's own development
# session) confirmed this is worse than a loud parse error: GAUSS does NOT
# reject a `;`-separated literal -- it silently misparses it into a single
# malformed row containing a denormal/garbage element. This section adds a
# dedicated deterministic layer that catches this class of problem directly,
# instead of leaving it to fall through as an uninformative UNVERIFIED
# precondition.
#
# Deliberately NOT a parser: every check below is a small, bounded, textual
# rule with its own documented/empirical provenance (see
# `_SYNTAX_RULE_REGISTRY`), operating on already comment-stripped code (the
# same convention every other check in this module already follows --
# callers pass `_strip_comments_for_analysis(block)`, never raw fenced-block
# text). A construct this version cannot check (e.g. a `do`/`if`/`proc`
# block body) is recorded in `unknown_constructs`, never silently ignored
# and never guessed at as passing.
# ---------------------------------------------------------------------------


class SyntaxStatus(str, enum.Enum):
    """`VALIDATED` means ONLY "no syntax violation was found within this
    version's implemented, deliberately bounded deterministic coverage" --
    it is never a claim of full GAUSS grammar correctness. `INVALID` means
    at least one deterministic rule below was actually violated. `PARTIAL`
    means some constructs in the code were checked (and passed), but at
    least one other construct present is outside this version's coverage
    (see `unknown_constructs`) -- never used when nothing was checked at
    all, which is `UNKNOWN` instead."""

    VALIDATED = "validated"
    INVALID = "invalid"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SyntaxRule:
    """Provenance record for one deterministic syntax rule -- every rule
    used by `validate_syntax(...)` has a matching entry in
    `_SYNTAX_RULE_REGISTRY` below, referenced by name from every
    `SyntaxIssue.rule` this module ever produces. Mirrors the same
    hand-curated-with-provenance discipline `_PRECONDITION_INDEX` already
    established for documented preconditions."""

    name: str
    description: str
    source: str
    applies_to: str


_SYNTAX_RULE_REGISTRY: dict[str, SyntaxRule] = {
    "matrix_literal_row_separator": SyntaxRule(
        name="matrix_literal_row_separator",
        description=(
            "A GAUSS matrix literal's rows are separated by `,`; elements within a row are separated by "
            "whitespace. `;` is not a valid row separator."
        ),
        source=(
            'let.rst (official docs): "let x = { 1 2 3, 4 5 6, 7 8 9 };" ... "If curly braces are used, '
            'the let is optional" (so the same literal syntax applies to a bare `x = {...}` assignment); '
            "confirmed by real `tgauss.exe -b` execution (v0.76.0 development session): a `;`-separated "
            "literal is NOT rejected by GAUSS -- it is silently misparsed into a single malformed row "
            "containing a denormal/garbage element, rather than raising an error. v0.77.0's differential "
            "baseline corpus run re-confirmed this exact silent misparse live (`x = { 1 2; 3 4 };\\nprint "
            'x;` produced stdout containing a literal `+DEN` denormal token) -- this rule is a DELIBERATE, '
            "evidence-justified exception to this milestone's own real-GAUSS-acceptance oracle: real GAUSS's "
            "process exits cleanly (no error), so the differential harness records this as a syntax "
            "'false positive' against raw process acceptance, but the rule is kept INVALID intentionally "
            "because raw acceptance here masks a dangerous silent misparse, not a correct parse -- see "
            "docs/differential-syntax-validation.md's 'intentional divergences' section."
        ),
        applies_to="matrix_literal",
    ),
    "matrix_literal_row_shape": SyntaxRule(
        name="matrix_literal_row_shape",
        description=(
            "Every row of a purely-numeric GAUSS matrix literal must have the same number of elements, "
            "and no row may be empty."
        ),
        source="let.rst (official docs): every documented literal example has conformable rows.",
        applies_to="matrix_literal",
    ),
    "balanced_delimiters": SyntaxRule(
        name="balanced_delimiters",
        description="`{`/`}`, `(`/`)`, and `[`/`]` must be balanced, and never closed with the wrong type.",
        source=(
            "Structural convention: every real GAUSS syntax example in this repository's own curated "
            "precondition/signature fixtures and documentation excerpts uses balanced delimiters throughout."
        ),
        applies_to="delimiters",
    ),
    "dangling_assignment": SyntaxRule(
        name="dangling_assignment",
        description="An assignment statement's right-hand side must not be empty (e.g. `x = ;`).",
        source=(
            "Real `tgauss.exe -b` execution (v0.76.0 development session): `x = ;` raises "
            '"error G0105: Bad expression or missing arguments".'
        ),
        applies_to="assignment",
    ),
    "call_argument_missing_separator": SyntaxRule(
        name="call_argument_missing_separator",
        description=(
            "Two adjacent tokens (identifiers, numeric literals, or a masked string) separated only by "
            "whitespace within one call argument, with no comma and no operator between them (e.g. "
            "`rndu(1e5 4)`, `reshape(5 3)`, `sprintf(\"...\" pi)`) -- GAUSS requires an explicit comma or "
            "operator between them."
        ),
        source=(
            "v0.77.0 differential baseline corpus run (this milestone's own real `tgauss.exe -b` "
            "execution, 2026-09-18): five independent mutated snippets sharing this exact shape "
            "(`meanc(rndu(1e5 4))`, `rndn(n n)`, `reshape(5 3)`, `sprintf(\"...\" pi)`, `ones(3 2)`) "
            "were all real syntax FALSE NEGATIVES under the pre-v0.77.0 validator (reported VALIDATED) "
            "-- real GAUSS rejects every one with \"error G0063: Operator expected\", the same code "
            "`bare_multi_token_literal_requires_let_or_braces` already catches for an assignment RHS. "
            "This rule generalizes that same grammar gap to call arguments. A second real false "
            "negative was found the same session by a fresh live-Ollama stress batch (Phase 15, "
            "scenario `D-007`): a real model wrote `print(\"Standard Deviation of x: \" std_dev);` -- "
            "the identical missing-separator shape, but inside a `print(...)` call, which the "
            "checker's own symbol-skip list (`_LANGUAGE_CONSTRUCT_KEYWORDS`, which includes `print` to "
            "avoid misreading GAUSS's bare `print x, y;` form as a call) exempted entirely. Real "
            "`tgauss.exe -b` confirmed `error G0063` for this exact snippet. Fixed by narrowing this "
            "check's own skip list to `_BLOCK_CONSTRUCT_KEYWORDS` (genuine loop/conditional/proc "
            "headers only), so a genuinely parenthesized, call-shaped `print(...)` is checked like any "
            "other call."
        ),
        applies_to="call",
    ),
    "unterminated_string": SyntaxRule(
        name="unterminated_string",
        description="A double-quoted string literal opened on a line must be closed on that same line.",
        source=(
            'let.rst (official docs): `let x = "dog""cat";` -- double quotes are GAUSS\'s unambiguous '
            "string delimiter. A single quote is deliberately NOT checked here: it is overwhelmingly used "
            "as the transpose operator (`x'`) in generated code, and treating it as a string delimiter "
            "would be a real false-positive risk this module's own fail-closed discipline requires avoiding."
        ),
        applies_to="string_literal",
    ),
    "bare_multi_token_literal_requires_let_or_braces": SyntaxRule(
        name="bare_multi_token_literal_requires_let_or_braces",
        description=(
            "A bare assignment of two or more whitespace-separated numeric tokens with no enclosing `{...}` "
            "and no `let` keyword (e.g. `x = -1 0;`) is not valid GAUSS -- it requires either `{...}` "
            "(`x = { -1 0 };`) or the `let` keyword (`let x = -1 0;`)."
        ),
        source=(
            "v0.76.0 live evaluation (a real CLI smoke-test scenario, category 66.x's own 66.4 prompt "
            're-run through the installed `gauss-ai` binary: a `chol` example whose real model output '
            "wrote `x = -1 0;` with no braces at all) + real `tgauss.exe -b` "
            "execution performed this session: `x = -1 0;` (no `let`, no `{}`) raises "
            '"error G0063: Operator expected before \'0\'"; the identical literal prefixed with `let` '
            "(`let x = -1 0;`) executes successfully, producing a column vector -- exactly matching "
            "`let.rst`'s own documented Format/Remarks (\"If curly braces are used, the let is optional\"; "
            'a bare multi-token list otherwise requires `let`).'
        ),
        applies_to="assignment",
    ),
    "for_block": SyntaxRule(
        name="for_block",
        description=(
            "VALIDATION rule (not a violation): a `for` block is reported as a validated construct only when "
            "its header is exactly `for NAME (start, stop, step);`, no header argument contains a `{...}` "
            "literal, a string, or a non-integer numeric literal start/step, it is closed by its own "
            "`endfor;`, and every statement in its body is a nested `for`/`endfor`, a plain or indexed "
            "assignment, a `print` statement, or empty. Any other body statement leaves the block an "
            "unknown construct (`control_flow_block`)."
        ),
        source=(
            "for.rst (official docs), Format: `for i (start, stop, step); ... endfor;`, with `start`, "
            "`stop` and `step` documented as scalars; user-guide/fundamentals/control-flow.rst \"Counted "
            "Loops: for\" (\"strictly local\" counter; nested-loop preallocate-and-fill example). Real "
            "`tgauss.exe -b` (GAUSS 26.1.4, v0.82.0 planning, 2026-10-08) ran the shapes this rule "
            "validates: no space before `(` (the live 71.3 form), the whole loop on one line, upper-case "
            "`FOR`/`ENDFOR`, an empty body, a negative step, zero iterations, doubly and triply nested loops "
            "with distinct counters, and bounds from `rows(x)` or a variable -- all ran. Two shapes run "
            "SILENTLY in a way the docs do not describe and are deliberately left unknown, not validated: a "
            "matrix-literal start (`for i ({1, 2}, 3, 1)`), and a fractional step with indexed writes "
            "(`for i (1, 3, 0.5)` truncates indices and overwrites elements)."
        ),
        applies_to="for_block",
    ),
    "for_header_shape": SyntaxRule(
        name="for_header_shape",
        description=(
            "A `for` header must be `for NAME (start, stop, step);` -- one counter name, then exactly three "
            "arguments in parentheses, then the end of the statement."
        ),
        source=(
            "for.rst (official docs), Format. Real `tgauss.exe -b` (GAUSS 26.1.4, 2026-10-08) rejects every "
            "deviation tried: `for i (1, 5);` and `for i (1, 5, 1, 1);` -> \"G0105 Bad expression or "
            "missing arguments\"; `for i = 1:3;` -> \"G0008 Syntax error '= 1:3'\"; C-style "
            "`for (i = 1; i <= 5; i++);` -> \"G0113 Unclosed (\"; a header with no `;` before the body -> "
            "\"G0063 Operator expected\"."
        ),
        applies_to="for_block",
    ),
    "for_block_balance": SyntaxRule(
        name="for_block_balance",
        description=(
            "Every `for` must be closed by its own `endfor;`: no `endfor` without an open `for`, no `for` "
            "left open at the end of the code, no `for` closed by another block's closer, no `endfor` "
            "closing another open block, and `endfor` must be a statement of its own."
        ),
        source=(
            "Real `tgauss.exe -b` (GAUSS 26.1.4, 2026-10-08): missing `endfor` -> \"G1001 found 'End of "
            "File' : Expected keyword 'ENDFOR'\"; a stray `endfor` -> \"G1001 found keyword 'ENDFOR' : "
            "Expected nothing\"; `for ... endo;` -> \"G1001 found keyword 'ENDO' : Expected keyword "
            "'ENDFOR'\"; `for ...; if ...; endfor; endif;` -> \"G1001 found keyword 'ENDFOR' : Expected "
            "keyword 'ENDIF'\"; `endfor` with no `;` before the next statement -> \"G0008 Syntax error\"."
        ),
        applies_to="for_block",
    ),
    "for_counter_reuse": SyntaxRule(
        name="for_counter_reuse",
        description="A nested `for` must not reuse the counter name of a `for` that encloses it.",
        source=(
            "Real `tgauss.exe -b` (GAUSS 26.1.4, 2026-10-08): `for i (1, 3, 1); for i (1, 3, 1); ... "
            "endfor; endfor;` -> \"G0736 Duplicate FOR loop counter name\"."
        ),
        applies_to="for_block",
    ),
    "for_counter_assignment": SyntaxRule(
        name="for_counter_assignment",
        description=(
            "A `for` body must not assign to the counter of any enclosing `for`, as a plain (`i = 2;`) or "
            "an indexed (`i[1] = 2;`) target."
        ),
        source=(
            "Real `tgauss.exe -b` (GAUSS 26.1.4, 2026-10-08): `i = 2;`, `i[1] = 2;`, and `i = 1;` inside an "
            "inner loop over `j` all -> \"G0541 Illegal assignment to FOR loop counter\"."
        ),
        applies_to="for_block",
    ),
    "let_statement_shape": SyntaxRule(
        name="let_statement_shape",
        description=(
            "An assignment whose right-hand side BEGINS with `{` is a `let` statement: its target must be "
            "a plain name (not indexed or a member), and nothing may follow the closing `}` "
            "(no transpose, operator, or concatenation)."
        ),
        source=(
            'let.rst (official docs): "If curly braces are used, the let is optional" -- `x = {...}` IS a '
            "`let`, whose right-hand side is a constant list. Real `tgauss.exe -b` (GAUSS 26.1.4, v0.82.0, "
            "2026-10-08) rejects every case this rule flags: `x = {1, 2, 3}';`, `let x = {1, 2}';`, "
            "`x = {1, 2} + 1;`, `x = {2 1, 1 2} * -1;`, `x = {1, 2} .* 3;`, `x = {1 2} ~ {3 4};`, "
            "`x = {1 2} | {3 4};`, `v[1:2] = {7, 8};`, `v[., 1] = {1, 2, 3};` -> \"G0008 Syntax error\"; "
            "`v[2] = {5};` -> \"G0047 Rows don't match\" + G0008. A literal that does not begin the "
            "right-hand side is unaffected and runs: `x = ({1, 2}) + 1;`, `x = 2 * {1, 2};`, "
            "`x = -{1, 2};`, `y = meanc({1, 2, 3}) + 1;`, `y = sumc({1, 2, 3}');`, and "
            "`v[., 1] = ones(3, 1);`. Before v0.82.0 every flagged case was reported VALIDATED."
        ),
        applies_to="assignment",
    ),
}


@dataclass(frozen=True)
class SyntaxIssue:
    rule: str
    message: str
    line_number: int | None
    construct: str


@dataclass(frozen=True)
class SyntaxValidationResult:
    """Immutable, provider-independent, contains no execution capability of
    any kind -- same discipline as every other result type in this module.
    `validated_constructs`/`unknown_constructs` are deduplicated, ordered
    tuples of construct names (e.g. `"matrix_literal"`, `"assignment"`,
    `"call"`, `"delimiters"`, `"string_literal"`, `"control_flow_block"`)."""

    status: str
    issues: tuple[SyntaxIssue, ...]
    validated_constructs: tuple[str, ...]
    unknown_constructs: tuple[str, ...]


_QUOTED_STRING_RE = re.compile(r'"[^"\n]*"')
#: Deliberately excludes newlines and backslash-escaping -- `let.rst`'s own
#: documented convention for embedding a literal quote is adjacent quoted
#: tokens (`"dog""cat"`), not backslash escaping, and a real GAUSS string
#: literal is not documented anywhere in this repository's own docs
#: checkout as spanning multiple lines.
_DANGLING_ASSIGNMENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*;")
#: A looser match than `_DANGLING_ASSIGNMENT_RE` -- used only to record that
#: SOME assignment construct is present (for `validated_constructs`
#: bookkeeping), matching both a normal and a dangling assignment alike.
#: `(?!=)` after the `=` excludes `==`/`!=`/`<=`/`>=` comparison operators.
_ASSIGNMENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\s*=(?!=)\s*\S")
#: v0.76.0: matches one non-`let`, non-brace-enclosed assignment statement's
#: own right-hand side -- see `bare_multi_token_literal_requires_let_or_
#: braces`'s own registry entry for the real live-found regression and real
#: `tgauss.exe -b` provenance. `(?P<let>\blet\s+)?` captures a `let` prefix
#: when present so the check below can skip it (`let.rst`'s own documented
#: exemption); `[^;{}]*` deliberately excludes `{`/`}` so this never
#: double-reports a real `{...}` matrix literal, which
#: `_check_matrix_literals(...)` already owns.
_BARE_ASSIGNMENT_RE = re.compile(
    r"(?P<let>\blet\s+)?\b[A-Za-z_][A-Za-z0-9_]*\s*=(?!=)\s*(?P<rhs>[^;{}]*);"
)


def _mask_quoted_strings(code: str) -> str:
    """Replaces each complete double-quoted string's content with `#` of the
    same length, so delimiter-balance/argument-separator/dangling-assignment
    scanning below never misreads a bracket or `=`/`;` character that
    happens to appear inside a string literal. Length-preserving, so byte
    offsets computed against the masked text remain valid against the
    original `code` for line-number reporting."""
    return _QUOTED_STRING_RE.sub(lambda m: "#" * len(m.group(0)), code)


def _find_matching_brace(text: str, open_idx: int) -> int | None:
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return None


def _check_balanced_delimiters(masked_code: str) -> tuple[list[SyntaxIssue], bool]:
    """A single unified stack-based scanner for `{}`/`()`/`[]` together --
    catches both a genuinely unmatched delimiter (e.g. the exact `meanc(`
    incomplete-call regression) and a wrong-type closer (e.g. `(1, 2}`).
    Returns `(issues, any_delimiter_found)`."""
    pairs = {"{": "}", "(": ")", "[": "]"}
    closers = {v: k for k, v in pairs.items()}
    issues: list[SyntaxIssue] = []
    stack: list[tuple[str, int]] = []
    found = False
    for i, ch in enumerate(masked_code):
        if ch in pairs:
            found = True
            stack.append((ch, i))
        elif ch in closers:
            found = True
            if stack and stack[-1][0] == closers[ch]:
                stack.pop()
            else:
                issues.append(SyntaxIssue(
                    rule="balanced_delimiters", message=f"unexpected `{ch}` with no matching opener",
                    line_number=masked_code.count("\n", 0, i) + 1, construct="delimiters",
                ))
    for opener, pos in stack:
        issues.append(SyntaxIssue(
            rule="balanced_delimiters", message=f"unmatched `{opener}` -- no closing `{pairs[opener]}` found",
            line_number=masked_code.count("\n", 0, pos) + 1, construct="delimiters",
        ))
    return issues, found


def _check_matrix_literals(code: str) -> tuple[list[SyntaxIssue], bool]:
    """Scans every top-level `{...}` occurrence in `code`. Does not attempt
    to validate a literal nested inside another literal -- no documented
    example in this repository's own docs checkout nests one matrix literal
    inside another. An unterminated `{` is deliberately left to
    `_check_balanced_delimiters(...)` rather than double-reported here."""
    issues: list[SyntaxIssue] = []
    found = False
    idx = 0
    while True:
        open_idx = code.find("{", idx)
        if open_idx == -1:
            break
        close_idx = _find_matching_brace(code, open_idx)
        if close_idx is None:
            break  # reported by _check_balanced_delimiters instead
        found = True
        content = code[open_idx + 1 : close_idx]
        line_no = code.count("\n", 0, open_idx) + 1
        if ";" in content:
            issues.append(SyntaxIssue(
                rule="matrix_literal_row_separator",
                message=(
                    "GAUSS matrix literal uses unsupported row separator `;` -- rows must be separated by "
                    "`,` (a `;`-separated literal is not rejected by GAUSS; it is silently misparsed into a "
                    "malformed single row instead)"
                ),
                line_number=line_no, construct="matrix_literal",
            ))
        elif content.strip():
            rows = content.split(",")
            if any(not row.strip() for row in rows):
                issues.append(SyntaxIssue(
                    rule="matrix_literal_row_shape",
                    message="matrix literal contains an empty row (a stray `,` with nothing between it and the next delimiter)",
                    line_number=line_no, construct="matrix_literal",
                ))
            else:
                numeric_row_widths: list[int] = []
                all_numeric = True
                for row in rows:
                    tokens = row.split()
                    if not all(_NUMERIC_LITERAL_RE.match(tok) for tok in tokens):
                        all_numeric = False
                        break
                    numeric_row_widths.append(len(tokens))
                if all_numeric and len(set(numeric_row_widths)) > 1:
                    issues.append(SyntaxIssue(
                        rule="matrix_literal_row_shape",
                        message="matrix literal rows have inconsistent element counts",
                        line_number=line_no, construct="matrix_literal",
                    ))
        idx = close_idx + 1
    return issues, found


def _check_unterminated_strings(code: str) -> list[SyntaxIssue]:
    issues: list[SyntaxIssue] = []
    offset = 0
    for line_no, line in enumerate(code.splitlines(keepends=True), start=1):
        remaining = _QUOTED_STRING_RE.sub("", line)
        if '"' in remaining:
            issues.append(SyntaxIssue(
                rule="unterminated_string", message="a double-quoted string on this line is not closed",
                line_number=line_no, construct="string_literal",
            ))
        offset += len(line)
    return issues


def _split_top_level_args_keep_empty(raw: str) -> list[str]:
    """Same top-level-comma splitting as `_split_top_level_args(...)`, but
    keeps empty slots (`""`) instead of dropping them -- needed to detect a
    stray/leading/trailing/duplicate comma, which `_split_top_level_args`'s
    own final filter would otherwise silently absorb."""
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
    parts.append("".join(current).strip())
    return parts


#: v0.77.0: an earlier version of this module flagged an empty slot between
#: commas in a call's argument list (`f(a,,b)`, `f(a,)`) as INVALID, on a
#: purely structural assumption ("no documented signature shows an empty
#: positional slot") with no real-runtime evidence behind it. This
#: milestone's own differential baseline corpus run (2026-09-18) directly
#: contradicted that assumption: real `tgauss.exe -b` execution of
#: `x = ones(3,, 2); print x;` and `x = meanc(rndu(1e5,, 4)); print rows(x);`
#: showed GAUSS silently and CORRECTLY collapses the doubled comma -- the
#: computed result is identical to the single-comma form, not a silent
#: misparse (contrast `matrix_literal_row_separator` above, which IS a
#: confirmed silent misparse and is deliberately kept). Per this milestone's
#: own Phase 10 ("prefer measurable disagreement over intuition-driven rule
#: expansion"), the check was removed entirely rather than patched --
#: `_check_call_argument_separators`/the `call_argument_separator` rule no
#: longer exist. See docs/differential-syntax-validation.md's "validator
#: hardening" section for the full evidence trail.


def _mask_bracketed_spans(text: str, *, open_ch: str, close_ch: str) -> str:
    """Replaces the INTERIOR of every top-level `open_ch...close_ch` span
    with `@` (same length, preserving line numbers) -- used so a call-
    argument-level check never mistakes legitimate whitespace-separated
    matrix-literal elements (`{2 1, 1 2}`) or indexing content (`x[1, 2]`)
    for a missing-separator violation. Length-preserving and does not touch
    the delimiter characters themselves."""
    result = list(text)
    idx = 0
    while True:
        open_idx = text.find(open_ch, idx)
        if open_idx == -1:
            break
        close_idx = _find_matching_brace(text, open_idx) if open_ch == "{" else _find_matching_bracket(text, open_idx)
        if close_idx is None:
            break
        for i in range(open_idx + 1, close_idx):
            if text[i] != "\n":
                result[i] = "@"
        idx = close_idx + 1
    return "".join(result)


def _find_matching_bracket(text: str, open_idx: int) -> int | None:
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return i
    return None


#: Matches a token-ending character directly followed by whitespace directly
#: followed by a token-starting character, with NOTHING else (no comma, no
#: operator, no delimiter) between them -- `#` is included because a masked
#: quoted string (see `_mask_quoted_strings`) is represented as a run of `#`.
_ADJACENT_BARE_TOKENS_RE = re.compile(r"[A-Za-z0-9_'#\)\]]\s+[A-Za-z0-9_#\(]")


def _check_call_argument_missing_separator(masked_code: str) -> list[SyntaxIssue]:
    """See `call_argument_missing_separator`'s own registry entry for the
    real `tgauss.exe -b`-verified regression cluster this closes. Operates
    on `masked_code` (comments/strings already masked by the caller) with
    matrix-literal and indexing spans additionally masked here, so a
    legitimate whitespace-separated matrix literal or index list passed as a
    call argument (e.g. `invpd({2 1, 1 2})`) is never mistaken for this
    violation.

    v0.77.0 (found by this milestone's own fresh live-Ollama stress batch,
    scenario `D-007`): skips only `_BLOCK_CONSTRUCT_KEYWORDS` (a genuine
    loop/conditional/proc HEADER), NOT the wider `_LANGUAGE_CONSTRUCT_
    KEYWORDS` `extract_generated_calls(...)` uses -- `print` is a member of
    the wider set (to avoid misreading GAUSS's own bare `print x, y;` form
    as a call), but a real model output `print("..." x);` (parenthesized,
    genuinely call-shaped) is real, confirmed-invalid GAUSS (`error G0063`)
    that this check must still be able to see. Skipping the wider set here
    silently exempted every `print(...)` call from this check entirely --
    the exact false negative `D-007` found."""
    scan_text = _mask_bracketed_spans(masked_code, open_ch="{", close_ch="}")
    scan_text = _mask_bracketed_spans(scan_text, open_ch="[", close_ch="]")
    issues: list[SyntaxIssue] = []
    for match in _CALL_SHAPED_RE.finditer(scan_text):
        symbol = match.group(1)
        if symbol.lower() in _BLOCK_CONSTRUCT_KEYWORDS:
            continue
        close_idx = _find_matching_paren(scan_text, match.end() - 1)
        if close_idx is None:
            continue  # reported by _check_balanced_delimiters instead
        raw = scan_text[match.end() : close_idx]
        if not raw.strip():
            continue  # a genuine zero-argument call, e.g. f()
        for arg in _split_top_level_args_keep_empty(raw):
            if _ADJACENT_BARE_TOKENS_RE.search(arg):
                issues.append(SyntaxIssue(
                    rule="call_argument_missing_separator",
                    message=(
                        f"call to `{symbol}` has an argument with adjacent tokens separated only by "
                        f"whitespace and no comma or operator between them (`{arg.strip()}`)"
                    ),
                    line_number=scan_text.count("\n", 0, match.start()) + 1, construct="call",
                ))
                break  # one issue per call is enough; avoid duplicate reports for the same call
    return issues


#: A narrower set than `_LANGUAGE_CONSTRUCT_KEYWORDS` above -- that set
#: exists to keep a loop/conditional HEADER from being misread as a call
#: (e.g. `if(x)`), and deliberately also includes simple single-statement
#: keywords (`print`, `local`, `retp`, `struct`) that are not block
#: constructs at all. Flagging `print`/`local` as an "unknown construct"
#: would make ordinary, fully-checkable generated code (which routinely
#: ends in a `print` statement) spuriously PARTIAL instead of VALIDATED --
#: only a genuine block-opening keyword belongs here.
_BLOCK_CONSTRUCT_KEYWORDS = frozenset({
    "if", "elseif", "else", "endif", "do", "while", "until", "endo", "for", "endfor", "proc", "endp",
    # v0.82.0: GAUSS's parallel constructs (threadfor.rst, threadbegin.rst,
    # threadstat.rst), found during v0.82.0 planning to be completely
    # invisible here -- `threadfor i(1, 5, 1); ... threadendfor;` was
    # reported VALIDATED with no unknown construct at all.
    "threadfor", "threadendfor", "threadbegin", "threadend", "threadstat",
})


#: v0.76.0 live evaluation (category 66.x, scenario 66.9) found a real
#: defect: a plain `startswith(keyword)` check matches `formula = ...` as
#: starting with the keyword `for` (a bare string-prefix match, not a real
#: word boundary), spuriously downgrading ordinary, fully-checkable code
#: from VALIDATED to PARTIAL. Requires the character immediately after the
#: keyword to be whitespace, `;`, or end-of-line -- a real word boundary,
#: never a guess at where an identifier happens to start with a keyword's
#: own letters.
def _starts_with_keyword(stripped_line: str, keyword: str) -> bool:
    if not stripped_line.startswith(keyword):
        return False
    remainder = stripped_line[len(keyword):]
    return remainder == "" or remainder[0] in " \t;("


def _check_bare_multi_token_literals(masked_code: str) -> list[SyntaxIssue]:
    """See `bare_multi_token_literal_requires_let_or_braces`'s own registry
    entry for the real live-found regression and real `tgauss.exe -b`
    provenance. Flags ONLY a right-hand side of two-or-more bare numeric
    tokens (each individually matching `_NUMERIC_LITERAL_RE`) with no `let`
    prefix and no `{...}` -- never a real expression (`x = a + b;`), a real
    call (`x = meanc(y);`), or a single scalar (`x = 5;`), which are all
    structurally excluded by the token-count/all-numeric requirement below."""
    issues: list[SyntaxIssue] = []
    for match in _BARE_ASSIGNMENT_RE.finditer(masked_code):
        if match.group("let") is not None:
            continue
        tokens = match.group("rhs").split()
        if len(tokens) < 2:
            continue
        if not all(_NUMERIC_LITERAL_RE.match(tok) for tok in tokens):
            continue
        issues.append(SyntaxIssue(
            rule="bare_multi_token_literal_requires_let_or_braces",
            message=(
                "a bare multi-value assignment with no `{...}` and no `let` keyword is not valid GAUSS "
                "-- use `{...}` (e.g. `x = { ... };`) or prefix with `let` (e.g. `let x = ...;`)"
            ),
            line_number=masked_code.count("\n", 0, match.start()) + 1, construct="assignment",
        ))
    return issues


@dataclass(frozen=True)
class _Statement:
    """v0.82.0: one `;`-terminated statement of string-masked code. `text`
    is stripped; `line_number` is the 1-based line its first character is
    on. `terminated` is False only for trailing text after the last `;`."""

    text: str
    line_number: int
    terminated: bool


def _split_statements(masked_code: str) -> list[_Statement]:
    """v0.82.0: splits WHOLE (already string-masked) code on `;`, across
    lines -- unlike `_masked_statements(...)`, which splits per line -- so a
    multi-line matrix literal or a statement continued onto the next line is
    one statement, and a block keyword that follows a `;` mid-line (the
    one-line loop form) starts its own statement. Empty statements (e.g. the
    second `;` of `print i;;`, documented in control-flow.rst) are dropped."""
    statements: list[_Statement] = []
    start = 0
    while start < len(masked_code):
        semi = masked_code.find(";", start)
        end = len(masked_code) if semi == -1 else semi
        raw = masked_code[start:end]
        text = raw.strip()
        if text:
            first = start + (len(raw) - len(raw.lstrip()))
            statements.append(_Statement(
                text=text, line_number=masked_code.count("\n", 0, first) + 1, terminated=semi != -1,
            ))
        start = end + 1
    return statements


def _first_keyword(statement_text: str) -> str | None:
    """The statement's leading word, lower-cased, when it is a block
    keyword at a real word boundary (`_starts_with_keyword(...)` -- so
    `formula = 1;` is never read as `for`); otherwise `None`."""
    word = _leading_word(statement_text)
    return word if word in _BLOCK_CONSTRUCT_KEYWORDS else None


def _leading_word(statement_text: str) -> str | None:
    """The statement's leading identifier, lower-cased. Unlike
    `_starts_with_keyword(...)`, any whitespace -- including a newline --
    ends the word, which matters for whole statements: `endfor` followed by
    a newline and no `;` (real G0008) must still be read as `endfor`."""
    match = _IDENTIFIER_AT_START_RE.match(statement_text)
    return match.group(0).lower() if match else None


#: v0.82.0: which non-`for` opener each closer ends. These blocks are never
#: modelled (they stay `control_flow_block`); pairing is tracked only so a
#: `for` closed by one of them, or an `endfor` that closes one of them, is
#: caught (`for_block_balance`, real G1001 evidence).
_CLOSER_FOR_OPENER = {
    "endif": ("if",), "endo": ("do",), "endp": ("proc", "keyword"),
    "threadendfor": ("threadfor",), "threadend": ("threadbegin",),
}
_UNMODELLED_OPENERS = frozenset({"if", "do", "proc", "keyword", "threadfor", "threadbegin"})
_IDENTIFIER_AT_START_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_FOR_HEADER_START_RE = re.compile(r"for\s+([A-Za-z_][A-Za-z0-9_]*)\s*", re.IGNORECASE)


@dataclass
class _ForFrame:
    kind: str
    counter: str | None
    line_number: int
    modelled: bool = True


def _non_integer_numeric_literal(text: str) -> bool:
    text = text.strip()
    if not _NUMERIC_LITERAL_RE.match(text):
        return False
    try:
        return not float(text).is_integer()
    except ValueError:
        return True


def _assignment_target(statement_text: str) -> tuple[str, bool] | None:
    """`(target_name, indexed)` for a plain `name = ...` / `let name = ...`
    or an indexed `name[...] = ...` assignment, else `None`. A member
    (`s.x = ...`) or multi-target (`{a, b} = ...`) write is `None` -- the
    `for` body allowlist does not model those."""
    text = statement_text
    if _leading_word(text) == "let":
        text = text[3:].lstrip()
    match = _IDENTIFIER_AT_START_RE.match(text)
    if match is None:
        return None
    rest = text[match.end():].lstrip()
    indexed = False
    if rest.startswith("["):
        close_idx = _find_matching_bracket(rest, 0)
        if close_idx is None:
            return None
        rest = rest[close_idx + 1:].lstrip()
        indexed = True
    if rest.startswith("=") and not rest.startswith("=="):
        return match.group(0), indexed
    return None


def _check_control_flow_blocks(masked_code: str) -> tuple[list[SyntaxIssue], bool, bool]:
    """v0.82.0: replaces the pre-v0.82.0 `_detect_unknown_syntax_constructs`,
    which flagged ANY line STARTING with a block keyword as
    `control_flow_block` -- so the 71.3 preallocate-and-fill loop capped
    syntax coverage at PARTIAL, while the same loop written on one line
    (`...; for i(1, 5, 1); ...`) was not seen at all and got VALIDATED.

    Walks `_split_statements(...)` with a stack of open blocks and returns
    `(issues, any_for_validated, any_unknown)`:

    - a `for` block is validated only under `for_block`'s registry
      conditions; its body allowlist is checked against the INNERMOST open
      block, so a statement inside an `if` inside a `for` is never treated
      as modelled (the `if` already makes the snippet unknown);
    - `for_header_shape`, `for_block_balance`, `for_counter_reuse` and
      `for_counter_assignment` are INVALID, each with real `tgauss.exe -b`
      provenance;
    - every non-`for` block keyword (`if`/`do`/`proc`/`thread*`/...) is
      unknown, exactly as before; pairing is tracked only to catch a
      `for`/`endfor` mismatch against one of them.

    Never a guess at well-formedness of anything it does not model: those
    only ever add to `any_unknown`."""
    issues: list[SyntaxIssue] = []
    stack: list[_ForFrame] = []
    any_for_validated = False
    any_unknown = False

    def issue(rule: str, message: str, line_number: int) -> None:
        issues.append(SyntaxIssue(rule=rule, message=message, line_number=line_number, construct="for_block"))

    def enclosing_counters() -> set[str]:
        return {f.counter.lower() for f in stack if f.kind == "for" and f.counter}

    def close_for(frame: _ForFrame) -> None:
        nonlocal any_for_validated, any_unknown
        if frame.modelled:
            any_for_validated = True
        else:
            any_unknown = True

    for statement in _split_statements(masked_code):
        text = statement.text
        line = statement.line_number
        keyword = _first_keyword(text)

        if keyword == "for":
            frame = _ForFrame(kind="for", counter=None, line_number=line)
            if stack and stack[-1].kind != "for":
                frame.modelled = False  # inside an unmodelled block
            header = _FOR_HEADER_START_RE.match(text)
            if header is None or not text[header.end():].startswith("("):
                issue("for_header_shape", "`for` header is not `for NAME (start, stop, step);`", line)
            else:
                frame.counter = header.group(1)
                open_idx = header.end()
                close_idx = _find_matching_paren(text, open_idx)
                if close_idx is None or text[close_idx + 1:].strip():
                    issue(
                        "for_header_shape",
                        "`for` header must end right after its `(start, stop, step)` list with `;`", line,
                    )
                else:
                    slots = _split_top_level_args_keep_empty(text[open_idx + 1:close_idx])
                    if any(not s for s in slots):
                        frame.modelled = False  # an empty slot: undocumented, not modelled
                    elif len(slots) != 3:
                        issue(
                            "for_header_shape",
                            f"`for` header has {len(slots)} argument(s); the documented form takes exactly "
                            "three (start, stop, step)", line,
                        )
                    elif any("{" in s or "#" in s for s in slots) or any(
                        _non_integer_numeric_literal(slots[i]) for i in (0, 2)
                    ):
                        frame.modelled = False
                if frame.counter and frame.counter.lower() in enclosing_counters():
                    issue(
                        "for_counter_reuse",
                        f"nested `for` reuses the enclosing loop's counter `{frame.counter}`", line,
                    )
            stack.append(frame)
            continue

        if keyword == "endfor":
            if text.lower() != "endfor":
                issue("for_block_balance", "`endfor` must be followed by `;` before the next statement", line)
            if not stack:
                issue("for_block_balance", "`endfor` with no open `for`", line)
                continue
            if stack[-1].kind != "for":
                issue("for_block_balance", f"`endfor` closes an open `{stack[-1].kind}` block", line)
                any_unknown = True
                for depth in range(len(stack) - 1, -1, -1):
                    if stack[depth].kind == "for":
                        del stack[depth:]
                        break
                continue
            close_for(stack.pop())
            continue

        if keyword in _CLOSER_FOR_OPENER:
            any_unknown = True
            if stack and stack[-1].kind == "for":
                issue("for_block_balance", f"`for` closed by `{keyword}` instead of `endfor`", line)
                stack.pop()
                continue
            if stack and stack[-1].kind in _CLOSER_FOR_OPENER[keyword]:
                stack.pop()
            continue

        if keyword in _UNMODELLED_OPENERS:
            any_unknown = True
            if stack and stack[-1].kind == "for":
                stack[-1].modelled = False
            stack.append(_ForFrame(kind=keyword, counter=None, line_number=line))
            continue

        if keyword is not None:
            # `else`/`elseif`/`while`/`until`/`threadstat`: never modelled.
            any_unknown = True
            if stack and stack[-1].kind == "for":
                stack[-1].modelled = False
            continue

        if not stack or stack[-1].kind != "for":
            continue  # top-level or inside an unmodelled block: unchanged behaviour

        # A statement directly inside a `for` body: the allowlist.
        frame = stack[-1]
        target = _assignment_target(text)
        if target is not None:
            if target[0].lower() in enclosing_counters():
                issue(
                    "for_counter_assignment",
                    f"assignment to the `for` loop counter `{target[0]}` inside its loop", line,
                )
            continue
        if _leading_word(text) == "print":
            continue
        frame.modelled = False

    for frame in stack:
        if frame.kind == "for":
            issue("for_block_balance", "`for` is never closed by `endfor`", frame.line_number)
    return issues, any_for_validated, any_unknown


#: v0.82.0: `[let] target = {` -- the start of a `let` statement (see
#: `let_statement_shape`'s registry entry). `target` may be indexed or a
#: member so the rule can flag it; a multi-target `{a, b} = ...` never
#: matches (it does not start with an identifier).
_LET_STATEMENT_RE = re.compile(
    r"^(?:let\s+)?(?P<target>[A-Za-z_][A-Za-z0-9_]*(?:\s*\[[^\]]*\]|\s*\.\s*[A-Za-z_][A-Za-z0-9_]*)*)"
    r"\s*=(?!=)\s*(?=\{)",
    re.IGNORECASE,
)


def _check_let_statements(masked_code: str) -> list[SyntaxIssue]:
    """v0.82.0: see `let_statement_shape`'s registry entry. Operates on
    whole statements, so a multi-line literal is handled; an unterminated
    `{` is left to `_check_balanced_delimiters(...)`."""
    issues: list[SyntaxIssue] = []
    for statement in _split_statements(masked_code):
        match = _LET_STATEMENT_RE.match(statement.text)
        if match is None:
            continue
        open_idx = match.end()
        close_idx = _find_matching_brace(statement.text, open_idx)
        if close_idx is None:
            continue
        target = match.group("target")
        trailing = statement.text[close_idx + 1:].strip()
        if "[" in target or "." in target:
            message = (
                f"`{target.strip()} = {{...}}` is a `let` statement, whose target must be a plain name -- "
                "assign the literal to a variable first, or use a call such as `ones(...)`"
            )
        elif trailing:
            message = (
                f"nothing may follow the `{{...}}` literal that begins a `let` right-hand side (found "
                f"`{trailing}`) -- assign the literal first, or wrap it in parentheses"
            )
        else:
            continue
        issues.append(SyntaxIssue(
            rule="let_statement_shape", message=message, line_number=statement.line_number,
            construct="assignment",
        ))
    return issues


def validate_syntax(code: str) -> SyntaxValidationResult:
    """The one entry point callers should use. `code` is expected to already
    have comments stripped by the caller, exactly like `check_preconditions(
    ...)`/`extract_generated_calls(...)` already expect -- this function
    never re-implements `gauss_conversation_engine._strip_comments_for_
    analysis(...)`, to avoid a third divergent copy of that regex."""
    masked = _mask_quoted_strings(code)
    issues: list[SyntaxIssue] = []

    delimiter_issues, delimiters_found = _check_balanced_delimiters(masked)
    issues.extend(delimiter_issues)

    matrix_issues, matrix_found = _check_matrix_literals(code)
    issues.extend(matrix_issues)

    issues.extend(_check_unterminated_strings(code))
    issues.extend(_check_bare_multi_token_literals(masked))
    issues.extend(_check_let_statements(masked))

    dangling_found = False
    for match in _DANGLING_ASSIGNMENT_RE.finditer(masked):
        dangling_found = True
        issues.append(SyntaxIssue(
            rule="dangling_assignment", message=f"assignment to `{match.group(1)}` has an empty right-hand side",
            line_number=masked.count("\n", 0, match.start()) + 1, construct="assignment",
        ))
    assignment_found = dangling_found or bool(_ASSIGNMENT_RE.search(masked))

    issues.extend(_check_call_argument_missing_separator(masked))
    call_found = bool(_CALL_SHAPED_RE.search(code))

    string_found = bool(_QUOTED_STRING_RE.search(code))

    validated: list[str] = []
    if delimiters_found:
        validated.append("delimiters")
    if matrix_found:
        validated.append("matrix_literal")
    if assignment_found:
        validated.append("assignment")
    if call_found:
        validated.append("call")
    if string_found:
        validated.append("string_literal")

    block_issues, for_validated, block_unknown = _check_control_flow_blocks(masked)
    issues.extend(block_issues)
    if for_validated:
        validated.append("for_block")
    unknown = ("control_flow_block",) if block_unknown else ()

    if issues:
        status = SyntaxStatus.INVALID.value
    elif validated and not unknown:
        status = SyntaxStatus.VALIDATED.value
    elif validated and unknown:
        status = SyntaxStatus.PARTIAL.value
    else:
        status = SyntaxStatus.UNKNOWN.value

    return SyntaxValidationResult(
        status=status, issues=tuple(issues), validated_constructs=tuple(validated), unknown_constructs=unknown,
    )


def merge_syntax_results(results: tuple[SyntaxValidationResult, ...]) -> SyntaxValidationResult | None:
    """Combines one `SyntaxValidationResult` per generated code block (a
    conversational answer can contain more than one fenced block) into a
    single result for the whole answer, re-deriving `status` from the
    combined evidence via the exact same rule `validate_syntax(...)` itself
    uses -- never a separate ranking scheme. Returns `None` for an empty
    input (no code blocks at all), distinct from a result computed from
    code that happened to have nothing checkable in it."""
    if not results:
        return None
    issues: list[SyntaxIssue] = []
    validated: list[str] = []
    unknown: list[str] = []
    for result in results:
        issues.extend(result.issues)
        for construct in result.validated_constructs:
            if construct not in validated:
                validated.append(construct)
        for construct in result.unknown_constructs:
            if construct not in unknown:
                unknown.append(construct)
    if issues:
        status = SyntaxStatus.INVALID.value
    elif validated and not unknown:
        status = SyntaxStatus.VALIDATED.value
    elif validated and unknown:
        status = SyntaxStatus.PARTIAL.value
    else:
        status = SyntaxStatus.UNKNOWN.value
    return SyntaxValidationResult(
        status=status, issues=tuple(issues), validated_constructs=tuple(validated), unknown_constructs=tuple(unknown),
    )


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
    immutability discipline as every other field here. v0.75.0 adds
    `parameter_role_checks`/`predicted_output`/`coverage` -- all optional/
    defaulted so this remains constructible exactly as before wherever it
    already was."""

    generation_policy: str | None
    unknown_symbols: tuple[str, ...]
    companion_hints: tuple[tuple[str, str], ...]
    call_validations: tuple[CallValidationResult, ...]
    preconditions: tuple[PreconditionCheck, ...]
    unresolved_issues: tuple[str, ...]
    eligibility: str
    parameter_role_checks: tuple[ParameterRoleCheck, ...] = ()
    predicted_output: "PredictedOutputClaim | None" = None
    coverage: "ValidationCoverage | None" = None
    #: v0.76.0 additions -- deterministic syntax validation and a future
    #: execution-handoff readiness verdict. `None` under the exact same
    #: condition as `coverage` above (no code-shaped content in the answer).
    syntax: "SyntaxValidationResult | None" = None
    readiness: "ReadinessResult | None" = None
    #: v0.80.0: any system-touching statement found (forces NOT_READY).
    system_statements: "tuple[SystemStatementFinding, ...]" = ()


def compute_eligibility(
    *, generation_policy: str | None, unknown_symbols: tuple[str, ...], ambiguous_topics: tuple[str, ...],
    call_validations: tuple[CallValidationResult, ...], preconditions: tuple[PreconditionCheck, ...],
    code_extraction_ok: bool, parameter_role_checks: tuple[ParameterRoleCheck, ...] = (),
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
      precondition does not block eligibility either, for the same reason);
    - v0.75.0: no documented parameter role/type is known to be MISMATCH
      (an UNKNOWN role check does not block eligibility, for the same
      reason UNKNOWN signatures/UNVERIFIED preconditions do not).

    `REQUIRES_CLARIFICATION` takes priority when genuine ambiguity remains
    (mirrors `v0.73.0`'s own `GenerationPolicy.CLARIFY` priority ordering).
    Any other failure yields `INELIGIBLE` with the specific reason(s)
    named in `unresolved_issues` -- never silently blocked with no
    explanation.

    v0.75.0: deliberately does NOT take a predicted-output verification
    argument at all -- a model's claimed predicted output (see
    `PredictedOutputClaim`/`analyze_predicted_output(...)`) is tracked as
    entirely separate evidence, never fed into this function, so a wrong
    prediction can never make correctly-generated code itself ineligible,
    and this function structurally cannot treat a predicted-output verdict
    as an execution-eligibility input even by future accident."""
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
    for role_check in parameter_role_checks:
        if role_check.status == ParameterRoleStatus.MISMATCH.value:
            issues.append(f"{role_check.symbol} (argument {role_check.position + 1}): {role_check.explanation}")

    if issues:
        return ExecutionEligibility.INELIGIBLE.value, tuple(issues)
    return ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value, ()


# ---------------------------------------------------------------------------
# Phase 9/10/11 (v0.75.0): predicted-output claim detection and limited
# deterministic verification
# ---------------------------------------------------------------------------


class OutputVerificationStatus(str, enum.Enum):
    """v0.75.0. Never self-assigned by the model -- `analyze_predicted_
    output(...)` is the only producer of this value, and it takes no
    provider/model argument of any kind (mirrors `compute_eligibility(...)`'s
    own structural guarantee)."""

    NOT_PRESENT = "not_present"
    VERIFIED = "verified"
    MISMATCH = "mismatch"
    UNVERIFIED = "unverified"
    UNPARSEABLE = "unparseable"


@dataclass(frozen=True)
class PredictedOutputClaim:
    """`expected_value`/`computed_value` are always a tuple-of-tuples (a
    single-cell tuple for a scalar) so a claimed matrix and a claimed
    scalar share one representation. `computed_value` is populated only
    when a deterministic checker in `verify_predicted_output(...)` actually
    ran (`verification_status` is `VERIFIED` or `MISMATCH`); it stays
    `None` for `UNVERIFIED`/`UNPARSEABLE`/`NOT_PRESENT` -- never guessed."""

    present: bool
    raw_text: str | None
    parseable: bool
    verification_status: str
    expected_value: tuple[tuple[float, ...], ...] | None = None
    computed_value: tuple[tuple[float, ...], ...] | None = None
    issues: tuple[str, ...] = ()


#: v0.75.0: a small, explicit set of marker phrases -- deliberately NOT a
#: general "any sentence describing output" detector, so ordinary
#: explanatory prose is never mistaken for a claimed result. Matches the
#: exact phrasing `CODE_GENERATION_SYSTEM_PROMPT_ADDENDUM` already asks the
#: model to use ("Expected output, not execution evidence:") plus a small
#: number of natural variants confirmed as real live-model phrasing in this
#: session's own v0.74.0 evaluation transcripts (e.g. "The expected output
#: is:", `evaluations/runs/2026-09-12-code-assistant-pre-execution-
#: validation-run-004.md`).
_OUTPUT_CLAIM_MARKERS: tuple[str, ...] = (
    "expected output, not execution evidence:",
    "expected output:",
    "the expected output is:",
    "this should print:",
    "this will print:",
    "this will return:",
    "the output will be:",
    "the result will be:",
)
_OUTPUT_CLAIM_MARKER_RE = re.compile(
    "(?:" + "|".join(re.escape(marker) for marker in _OUTPUT_CLAIM_MARKERS) + ")",
    re.IGNORECASE,
)
#: v0.75.0 live evaluation (category 65.x, scenario 65.10) found a real
#: detection gap: a real model frequently puts its claimed output in its
#: OWN separate fenced block immediately after the marker (often itself
#: inside markdown bold, e.g. "**Expected output:**\n```\n4.0\n5.0\n```"),
#: not as bare text before the next fence. The original single-regex
#: design stopped capturing at the first ``` it saw, which was the
#: OPENING of that very fence -- producing an empty/near-empty capture
#: (just the markdown "**" bold-close) instead of the real numeric
#: content inside it. `_extract_claim_text(...)` below fixes this: it
#: first tolerates markdown bold-close/whitespace right after the marker,
#: then explicitly prefers a fenced block's own CONTENT when one starts
#: there, falling back to the original "up to the next blank line/fence/
#: end" behavior only when no fence immediately follows.
_FENCED_BLOCK_RE = re.compile(r"```[A-Za-z0-9_+-]*[ \t]*\n(.*?)```", re.DOTALL)


def _extract_claim_text(remainder: str) -> str:
    stripped = remainder.lstrip()
    stripped = stripped.lstrip("*:").lstrip()  # tolerate "**...**"/stray ":" markdown right after the marker
    fence_match = _FENCED_BLOCK_RE.match(stripped)
    if fence_match:
        return fence_match.group(1).strip()
    stop_match = re.search(r"\n\s*\n|```", stripped)
    return (stripped[: stop_match.start()] if stop_match else stripped).strip()


def _parse_output_value(raw_text: str) -> tuple[tuple[float, ...], ...] | None:
    """Parses plain numeric text (one or more rows of whitespace/comma-
    separated numbers) -- the same conservative discipline as
    `_parse_literal_matrix(...)`, but without a `{...}` wrapper, since a
    model's own prose claim is never fenced that way. Returns `None`
    (never a partial/guessed parse) for anything containing non-numeric
    tokens.

    A small, bounded exception (v0.75.0 live evaluation, category 65.x,
    scenario 65.9): a real model commonly prefixes its numeric block with a
    plain text LABEL line inside the same fenced block (e.g. `"Inverted
    Matrix:\\n0.4  -0.2\\n-0.2  0.4"`). Any number of LEADING lines
    containing zero digit characters at all are skipped as a label/header
    -- never a line that has both digits and non-numeric tokens (e.g.
    `"Mean: 4.0"`), which still fails closed to `None` rather than being
    guessed at."""
    lines = [line.strip().strip(".") for line in raw_text.strip().splitlines()]
    lines = [line for line in lines if line]
    while lines and not any(ch.isdigit() for ch in lines[0]):
        lines.pop(0)  # a pure-text label/header line -- never partially numeric
    rows: list[tuple[float, ...]] = []
    for line in lines:
        tokens = line.replace(",", " ").split()
        if not tokens:
            continue
        try:
            rows.append(tuple(float(tok) for tok in tokens))
        except ValueError:
            return None
    if not rows:
        return None
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return None
    return tuple(rows)


def detect_predicted_output_claim(answer_text: str) -> PredictedOutputClaim:
    """Detection only -- never attempts deterministic verification itself
    (see `analyze_predicted_output(...)` for the combined entry point).
    Returns `NOT_PRESENT` when no marker phrase is found at all -- the
    common case for an answer with no output claim, and for prose-only
    QA (see `gauss_conversation_engine`'s own v0.75.0 universal-routing
    section)."""
    match = _OUTPUT_CLAIM_MARKER_RE.search(answer_text)
    if match is None:
        return PredictedOutputClaim(
            present=False, raw_text=None, parseable=False, verification_status=OutputVerificationStatus.NOT_PRESENT.value,
        )
    raw_text = _extract_claim_text(answer_text[match.end():])
    value = _parse_output_value(raw_text)
    if value is None:
        return PredictedOutputClaim(
            present=True, raw_text=raw_text, parseable=False, verification_status=OutputVerificationStatus.UNPARSEABLE.value,
            issues=("the claimed output text could not be parsed as a plain numeric value or matrix",),
        )
    return PredictedOutputClaim(
        present=True, raw_text=raw_text, parseable=True, verification_status=OutputVerificationStatus.UNVERIFIED.value,
        expected_value=value,
        issues=("no deterministic checker in this version recognized a computable pattern in the generated code",),
    )


def _flatten(rows: tuple[tuple[float, ...], ...]) -> tuple[float, ...]:
    return tuple(v for row in rows for v in row)


def _values_close(computed: tuple[tuple[float, ...], ...], expected: tuple[tuple[float, ...], ...], *, tol: float = 1e-3) -> bool:
    """Compares FLATTENED values only, deliberately ignoring row/column
    orientation -- a model may write a documented `Kx1` result as a single
    row of numbers instead of a column, and this checker's job is to catch
    a wrong VALUE, not to additionally re-validate shape/orientation (which
    is `check_parameter_roles(...)`'s job, not this one's)."""
    a, b = _flatten(computed), _flatten(expected)
    if len(a) != len(b):
        return False
    return all(abs(x - y) <= tol * max(1.0, abs(y)) for x, y in zip(a, b))


def verify_predicted_output(claim: PredictedOutputClaim, *, generated_code: str) -> PredictedOutputClaim:
    """Bounded, deterministic verification for a small, explicit set of
    recognized call patterns -- `meanc`/`sumc`/`inv`/`invpd` applied to a
    LITERAL matrix (traced the same way `check_preconditions(...)` already
    traces one), reusing `_matrix_inverse(...)` for `inv`/`invpd`. Every
    other generated-code pattern is deliberately left `UNVERIFIED` -- this
    function is not, and must never become, a general GAUSS interpreter.
    Never called when `claim.present` or `claim.parseable` is false.
    `generated_code` is expected to already have comments stripped by the
    caller (mirrors `check_preconditions(...)`'s own expectation -- this
    module never re-implements `gauss_conversation_engine._strip_comments_
    for_analysis(...)`, to avoid a third divergent copy of that regex)."""
    if not claim.present or not claim.parseable or claim.expected_value is None:
        return claim
    cleaned_code = generated_code
    for call in extract_generated_calls(cleaned_code):
        symbol = call.symbol.lower()
        if symbol not in ("meanc", "sumc", "inv", "invpd") or not call.raw_arguments:
            continue
        rows = _find_literal_matrix_for_argument(
            call.raw_arguments[0], code=cleaned_code, line_number=call.line_number, column=call.column,
        )
        if rows is None or len(rows) > MAX_CHECKED_MATRIX_DIM or len(rows[0]) > MAX_CHECKED_MATRIX_DIM:
            continue
        if symbol == "meanc":
            n = len(rows)
            computed = tuple((sum(rows[i][j] for i in range(n)) / n,) for j in range(len(rows[0])))
        elif symbol == "sumc":
            n = len(rows)
            computed = tuple((sum(rows[i][j] for i in range(n)),) for j in range(len(rows[0])))
        else:
            inverse = _matrix_inverse(rows)
            if inverse is None:
                continue
            computed = tuple(tuple(row) for row in inverse)
        if _values_close(computed, claim.expected_value):
            return dataclasses.replace(
                claim, computed_value=computed, verification_status=OutputVerificationStatus.VERIFIED.value, issues=(),
            )
        return dataclasses.replace(
            claim, computed_value=computed, verification_status=OutputVerificationStatus.MISMATCH.value,
            issues=(
                f"the deterministically computed result of {call.symbol}(...) does not match the claimed "
                "predicted output -- the claimed value is a model prediction, never execution evidence",
            ),
        )
    return claim


def analyze_predicted_output(answer_text: str, *, generated_code: tuple[str, ...]) -> PredictedOutputClaim:
    """The one combined entry point callers should use -- detects a claim in
    `answer_text`, then attempts limited deterministic verification against
    `generated_code`. `ExecutionEligibility`/`compute_eligibility(...)` never
    consume this result -- see that function's own v0.75.0 docstring
    paragraph for why."""
    claim = detect_predicted_output_claim(answer_text)
    if not claim.present or not claim.parseable:
        return claim
    return verify_predicted_output(claim, generated_code="\n".join(generated_code))


# ---------------------------------------------------------------------------
# Phase 13 (v0.75.0): validation completeness metadata
# ---------------------------------------------------------------------------


class CoverageStatus(str, enum.Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ValidationCoverage:
    """A summary of which validation passes actually ran to completion for
    the CURRENT code-shaped answer -- never a claim that the code itself is
    correct or safe. Distinguishes "eligible with broad evidence" from
    "eligible with many unknown gaps" without proliferating a second
    `ExecutionEligibility` tier (see this module's own top-of-file
    docstring for that explicit decision)."""

    symbol_check: str
    signature_check: str
    parameter_role_check: str
    precondition_check: str
    predicted_output_check: str
    #: v0.76.0 addition -- same four-state vocabulary, defaulted so every
    #: pre-v0.76.0 construction of this type remains valid unchanged.
    syntax_check: str = CoverageStatus.NOT_APPLICABLE.value


def compute_validation_coverage(
    *, has_code: bool, call_validations: tuple[CallValidationResult, ...],
    parameter_role_checks: tuple[ParameterRoleCheck, ...], preconditions: tuple[PreconditionCheck, ...],
    predicted_output: PredictedOutputClaim, syntax: "SyntaxValidationResult | None" = None,
) -> ValidationCoverage:
    if not has_code:
        na = CoverageStatus.NOT_APPLICABLE.value
        return ValidationCoverage(na, na, na, na, na, na)

    # `check_generated_symbols(...)` (gauss_conversation_engine.py) always
    # runs to completion whenever code is present -- there is no partial
    # state for it.
    symbol_check = CoverageStatus.COMPLETE.value

    if not call_validations:
        signature_check = CoverageStatus.NOT_APPLICABLE.value
    elif all(c.signature_known for c in call_validations):
        signature_check = CoverageStatus.COMPLETE.value
    elif any(c.signature_known for c in call_validations):
        signature_check = CoverageStatus.PARTIAL.value
    else:
        signature_check = CoverageStatus.UNKNOWN.value

    if not parameter_role_checks:
        parameter_role_check = CoverageStatus.NOT_APPLICABLE.value
    elif all(c.status != ParameterRoleStatus.UNKNOWN.value for c in parameter_role_checks):
        parameter_role_check = CoverageStatus.COMPLETE.value
    elif any(c.status != ParameterRoleStatus.UNKNOWN.value for c in parameter_role_checks):
        parameter_role_check = CoverageStatus.PARTIAL.value
    else:
        parameter_role_check = CoverageStatus.UNKNOWN.value

    if not preconditions:
        precondition_check = CoverageStatus.NOT_APPLICABLE.value
    elif all(c.status != PreconditionStatus.UNVERIFIED.value for c in preconditions):
        precondition_check = CoverageStatus.COMPLETE.value
    elif any(c.status != PreconditionStatus.UNVERIFIED.value for c in preconditions):
        precondition_check = CoverageStatus.PARTIAL.value
    else:
        precondition_check = CoverageStatus.UNKNOWN.value

    if predicted_output.verification_status == OutputVerificationStatus.NOT_PRESENT.value:
        predicted_output_check = CoverageStatus.NOT_APPLICABLE.value
    elif predicted_output.verification_status in (
        OutputVerificationStatus.VERIFIED.value, OutputVerificationStatus.MISMATCH.value,
    ):
        predicted_output_check = CoverageStatus.COMPLETE.value
    else:
        predicted_output_check = CoverageStatus.UNKNOWN.value

    # v0.76.0: `SyntaxStatus.INVALID` is still COMPLETE coverage -- a
    # definitive, deterministic finding, exactly like a VIOLATED
    # precondition above. Coverage measures whether real evidence was
    # obtained, not whether that evidence was favorable.
    if syntax is None:
        syntax_check = CoverageStatus.NOT_APPLICABLE.value
    elif syntax.status in (SyntaxStatus.VALIDATED.value, SyntaxStatus.INVALID.value):
        syntax_check = CoverageStatus.COMPLETE.value
    elif syntax.status == SyntaxStatus.PARTIAL.value:
        syntax_check = CoverageStatus.PARTIAL.value
    else:
        syntax_check = CoverageStatus.UNKNOWN.value

    return ValidationCoverage(
        symbol_check=symbol_check, signature_check=signature_check, parameter_role_check=parameter_role_check,
        precondition_check=precondition_check, predicted_output_check=predicted_output_check,
        syntax_check=syntax_check,
    )


# ---------------------------------------------------------------------------
# Phase 8 (v0.76.0): evidence-profile categorization
# ---------------------------------------------------------------------------


class EvidenceProfile(str, enum.Enum):
    """A categorical summary of how BROAD the validation evidence for the
    current code-shaped answer is, computed from `ValidationCoverage`'s five
    non-orthogonal dimensions (symbol/signature/parameter-role/precondition/
    syntax). Deliberately excludes `predicted_output_check` -- predicted-
    output verification is orthogonal evidence by design (see module
    docstring's Phase 17 discussion and `compute_eligibility(...)`'s own
    docstring), never folded into the evidence-breadth judgment a future
    handoff-readiness decision consumes. Deliberately not a numeric score --
    see module docstring's `v0.75.0` closing paragraph for why this module
    prefers categorical states throughout."""

    MINIMAL = "minimal"
    PARTIAL = "partial"
    BROAD = "broad"


def compute_evidence_profile(coverage: ValidationCoverage) -> str:
    dimensions = (
        coverage.symbol_check, coverage.signature_check, coverage.parameter_role_check,
        coverage.precondition_check, coverage.syntax_check,
    )
    unknown_count = sum(1 for d in dimensions if d == CoverageStatus.UNKNOWN.value)
    complete_or_na = all(d in (CoverageStatus.COMPLETE.value, CoverageStatus.NOT_APPLICABLE.value) for d in dimensions)
    if coverage.syntax_check == CoverageStatus.UNKNOWN.value or unknown_count >= 2:
        return EvidenceProfile.MINIMAL.value
    if coverage.syntax_check == CoverageStatus.COMPLETE.value and complete_or_na:
        return EvidenceProfile.BROAD.value
    return EvidenceProfile.PARTIAL.value


# ---------------------------------------------------------------------------
# v0.80.0: system-touching statements
# ---------------------------------------------------------------------------
#
# Found during v0.80.0 planning: nothing in the readiness chain looked at
# statements that reach outside GAUSS's own memory, so `y = invpd({2 1, 1 2});
# dos "...";` could reach HANDOFF_CANDIDATE -- and the execution helper does
# not sandbox GAUSS code (gauss_code_execution.py accepts `allow_file_write`
# only for input-contract completeness and discards it). The controlled
# execution handoff is for self-contained snippets that compute in memory
# (it already runs in an empty temp directory with no input files); any
# statement that runs OS commands, launches or ends processes, pulls in
# other source files, changes the working directory, or reads/writes/deletes
# files makes a snippet NOT_READY. File- and OS-level work belongs to the
# guided repair pipeline, which operates on real files with its own
# approvals. User decision (v0.80.0 plan): NOT_READY, not REVIEW_REQUIRED.


class SystemStatementCategory(str, enum.Enum):
    OS_COMMAND = "os_command"
    PROCESS_LAUNCH = "process_launch"
    PROCESS_CONTROL = "process_control"
    SOURCE_INCLUSION = "source_inclusion"
    DIRECTORY_CHANGE = "directory_change"
    FILE_DELETE = "file_delete"
    FILE_WRITE = "file_write"
    FILE_READ = "file_read"
    #: v0.82.0: functions that call a remote web API (FRED, DBnomics).
    #: `fred_load("GNPCA")` reached HANDOFF_CANDIDATE in v0.81.0 -- a
    #: network call from the controlled execution handoff, contrary to the
    #: project's "reaches outside GAUSS's own memory -> NOT_READY" rule.
    NETWORK = "network"
    #: v0.82.0: GAUSS's database interface (`dbAddDatabase`/`dbOpen`/
    #: `dbExecQuery`/...), which connects to a local or remote database.
    DATABASE = "database"


@dataclass(frozen=True)
class SystemStatementRule:
    """Provenance record, mirroring `SyntaxRule`: every entry was verified
    to exist as a real page in the official GAUSS documentation (aptech/docs,
    as published at docs.aptech.com/gauss) during v0.80.0 development, and
    `doc_page` names that page. Matching is by name only -- any statement-
    position use (`dos "..."`, `load x = f;`) or call-shaped use (`loadd(`)
    -- so a name never has to guess which syntactic form a caller chose."""

    name: str
    category: str
    doc_page: str


def _rules(category: SystemStatementCategory, *pairs: tuple[str, str]) -> tuple[SystemStatementRule, ...]:
    return tuple(SystemStatementRule(name=name, category=category.value, doc_page=page) for name, page in pairs)


_LOAD_PAGE = "loadloadfloadkloadmloadploads.rst"

_SYSTEM_STATEMENT_REGISTRY: tuple[SystemStatementRule, ...] = (
    *_rules(SystemStatementCategory.OS_COMMAND, ("dos", "dos.rst"), ("shell", "shell.rst")),
    *_rules(SystemStatementCategory.PROCESS_LAUNCH, ("exec", "exec.rst"), ("execbg", "execbg.rst")),
    *_rules(SystemStatementCategory.PROCESS_CONTROL, ("system", "system.rst")),
    *_rules(SystemStatementCategory.SOURCE_INCLUSION, ("run", "run.rst"), ("#include", "include.rst")),
    *_rules(SystemStatementCategory.DIRECTORY_CHANGE, ("chdir", "chdir.rst"), ("changedir", "changedir.rst")),
    *_rules(SystemStatementCategory.FILE_DELETE, ("deletefile", "deletefile.rst")),
    *_rules(
        SystemStatementCategory.FILE_WRITE,
        ("save", "save.rst"), ("saveall", "saveall.rst"), ("saved", "saved.rst"),
        ("savestruct", "savestruct.rst"), ("output", "output.rst"), ("create", "create.rst"),
        ("datacreate", "datacreate.rst"), ("writer", "writer.rst"), ("fputs", "fputs.rst"),
        ("fputst", "fputst.rst"), ("csvwritem", "csvwritem.rst"), ("xlswrite", "xlswrite.rst"),
        ("xlswritem", "xlswritem.rst"), ("xlswritesa", "xlswritesa.rst"), ("fopen", "fopen.rst"),
    ),
    *_rules(
        SystemStatementCategory.FILE_READ,
        ("load", _LOAD_PAGE), ("loadf", _LOAD_PAGE), ("loadk", _LOAD_PAGE), ("loadm", _LOAD_PAGE),
        ("loadp", _LOAD_PAGE), ("loads", _LOAD_PAGE), ("loadd", "loadd.rst"), ("loaddsa", "loaddsa.rst"),
        ("loadstruct", "loadstruct.rst"), ("loadarray", "loadarray.rst"), ("open", "open.rst"),
        ("dataopen", "dataopen.rst"), ("readr", "readr.rst"), ("getf", "getf.rst"),
        ("csvreadm", "csvreadm.rst"), ("csvreadsa", "csvreadsa.rst"), ("xlsreadm", "xlsreadm.rst"),
        ("xlsreadsa", "xlsreadsa.rst"), ("xlsgetsheetcount", "xlsgetsheetcount.rst"),
        ("fgets", "fgets.rst"), ("fgetsa", "fgetsa.rst"), ("fgetsat", "fgetsat.rst"), ("fgetst", "fgetst.rst"),
        ("filesa", "filesa.rst"), ("fileinfo", "fileinfo.rst"),
    ),
    # v0.82.0: a systematic audit of the published docs (2026-10-08, every
    # page's Purpose/Format text plus the db*/gda*/h5*/fred_*/dbnomics_*
    # families), prompted by v0.82.0's own signature-extraction fixes making
    # `plotSave("f.png", {800, 600});` -- a file write -- reach
    # HANDOFF_CANDIDATE, and by `fred_load(...)` (a web API call) already
    # reaching it in v0.81.0. Every name below was checked to appear on its
    # cited page. Deliberately NOT added (no effect outside GAUSS's memory):
    # `cdir`/`getGAUSSHome` (return a path string), `getnr`/`getnrmt`
    # (arithmetic), `xlsMakeRange` (builds a range string), `copyMetadata`
    # (in-memory dataframes), `fred_set`/`dbnomics_set` (build a parameter
    # map; only the load/search calls reach the network), `new`/`stop`.
    # A function that merely ACCEPTS a dataset filename as one of its
    # arguments (`ols("mydata", ...)`, `dstatmt`) is not covered here --
    # see KNOWN_LIMITATIONS.md.
    *_rules(
        SystemStatementCategory.FILE_WRITE,
        ("plotsave", "plotsave.rst"), ("putf", "putf.rst"), ("datasave", "datasave.rst"), ("datacreatecomplex",
        "datacreatecomplex.rst"), ("combinated", "combinated.rst"), ("null1", "null1.rst"), ("exctsmpl",
        "exctsmpl.rst"), ("mergeby", "mergeby.rst"), ("intrleav", "intrleav.rst"), ("sortd", "sortd.rst"),
        ("dataloop", "dataloopdataloop.rst"), ("renamefile", "renamefile.rst"), ("tempname", "tempname.rst"),
        ("comlog", "comlog.rst"), ("savewind", "savewind.rst"), ("graphprt", "graphprt.rst"), ("tkf2eps",
        "tkf2eps.rst"), ("tkf2ps", "tkf2ps.rst"), ("compile", "compile.rst"), ("lib", "lib.rst"), ("errorlog",
        "errorlog.rst"), ("errorlogat", "errorlogat.rst"), ("warninglog", "warninglog.rst"), ("warninglogat",
        "warninglogat.rst"), ("fflush", "fflush.rst"), ("gdacreate", "gdacreate.rst"), ("gdaappend",
        "gdaappend.rst"), ("gdapack", "gdapack.rst"), ("gdasave", "gdasave.rst"), ("gdaupdate",
        "gdaupdate.rst"), ("gdaupdateandpack", "gdaupdateandpack.rst"), ("gdawrite", "gdawrite.rst"),
        ("gdawrite32", "gdawrite32.rst"), ("gdawritesome", "gdawritesome.rst"), ("h5create", "h5create.rst"),
        ("h5write", "h5write.rst"), ("h5writeattribute", "h5writeattribute.rst"), ("spreadsheetwrite",
        "spreadsheetwrite.rst"),
    ),
    *_rules(
        SystemStatementCategory.FILE_READ,
        ("asciiload", "asciiload.rst"), ("dataload", "dataload.rst"), ("datalist", "datalist.rst"), ("momentd",
        "momentd.rst"), ("quantiled", "quantiled.rst"), ("setvars", "setvars.rst"), ("getname", "getname.rst"),
        ("getnamef", "getnamef.rst"), ("getheaders", "getheaders.rst"), ("iscplxf", "iscplxf.rst"), ("typef",
        "typef.rst"), ("vartypef", "vartypef.rst"), ("rowsf", "rowsf.rst"), ("colsf", "colsf.rst"), ("indices2",
        "indices2.rst"), ("rerun", "rerun.rst"), ("searchsourcepath", "searchsourcepath.rst"), ("seekr",
        "seekr.rst"), ("eof", "eof.rst"), ("fseek", "fseek.rst"), ("ftell", "ftell.rst"), ("fcheckerr",
        "fcheckerr.rst"), ("fclearerr", "fclearerr.rst"), ("fstrerror", "fstrerror.rst"), ("close",
        "close.rst"), ("closeall", "closeall.rst"), ("gdadstat", "gdadstat.rst"), ("gdadstatmat",
        "gdadstatmat.rst"), ("gdagetindex", "gdagetindex.rst"), ("gdagetname", "gdagetname.rst"),
        ("gdagetnames", "gdagetnames.rst"), ("gdagetorders", "gdagetorders.rst"), ("gdagettype",
        "gdagettype.rst"), ("gdagettypes", "gdagettypes.rst"), ("gdagetvarinfo", "gdagetvarinfo.rst"),
        ("gdaiscplx", "gdaiscplx.rst"), ("gdaload", "gdaload.rst"), ("gdaread", "gdaread.rst"),
        ("gdareadbyindex", "gdareadbyindex.rst"), ("gdareadsome", "gdareadsome.rst"), ("gdareadsparse",
        "gdareadsparse.rst"), ("gdareadstruct", "gdareadstruct.rst"), ("gdareportvarinfo",
        "gdareportvarinfo.rst"), ("gdavars", "gdavars.rst"), ("h5open", "h5open.rst"), ("h5read", "h5read.rst"),
        ("h5readattribute", "h5readattribute.rst"), ("spreadsheetreadm", "spreadsheetreadm.rst"),
        ("spreadsheetreadsa", "spreadsheetreadsa.rst"), ("xlsgetsheetsize", "xlsgetsheetsize.rst"),
        ("xlsgetsheettypes", "xlsgetsheettypes.rst"),
    ),
    *_rules(
        SystemStatementCategory.SOURCE_INCLUSION,
        ("use", "use.rst"), ("includedir", "includedir.rst"),
    ),
    *_rules(
        SystemStatementCategory.PROCESS_LAUNCH,
        ("edit", "edit.rst"),
    ),
    *_rules(
        SystemStatementCategory.NETWORK,
        ("fred_load", "fred_load.rst"), ("fred_search", "fred_search.rst"), ("dbnomics_search",
        "dbnomics_search.rst"), ("dbnomics_series", "dbnomics_series.rst"),
    ),
    *_rules(
        SystemStatementCategory.DATABASE,
        ("dbadddatabase", "dbadddatabase.rst"), ("dbclose", "dbclose.rst"), ("dbcommit", "dbcommit.rst"),
        ("dbcreatequery", "dbcreatequery.rst"), ("dbexecqueries", "dbexecqueries.rst"), ("dbexecquery",
        "dbexecquery.rst"), ("dbgetconnectoptions", "dbgetconnectoptions.rst"), ("dbgetdatabasename",
        "dbgetdatabasename.rst"), ("dbgetdrivername", "dbgetdrivername.rst"), ("dbgetdrivers",
        "dbgetdrivers.rst"), ("dbgethostname", "dbgethostname.rst"), ("dbgetlasterrornum",
        "dbgetlasterrornum.rst"), ("dbgetlasterrortext", "dbgetlasterrortext.rst"), ("dbgetnumericalprecpolicy",
        "dbgetnumericalprecpolicy.rst"), ("dbgetpassword", "dbgetpassword.rst"), ("dbgetport", "dbgetport.rst"),
        ("dbgetprimaryindex", "dbgetprimaryindex.rst"), ("dbgettableheaders", "dbgettableheaders.rst"),
        ("dbgettables", "dbgettables.rst"), ("dbgetusername", "dbgetusername.rst"), ("dbhasfeature",
        "dbhasfeature.rst"), ("dbisdriveravailable", "dbisdriveravailable.rst"), ("dbisopen", "dbisopen.rst"),
        ("dbisopenerror", "dbisopenerror.rst"), ("dbisvalid", "dbisvalid.rst"), ("dbopen", "dbopen.rst"),
        ("dbquerybindvalue", "dbquerybindvalue.rst"), ("dbqueryclear", "dbqueryclear.rst"), ("dbquerycols",
        "dbquerycols.rst"), ("dbqueryexecprepared", "dbqueryexecprepared.rst"), ("dbqueryfetchallm",
        "dbqueryfetchallm.rst"), ("dbqueryfetchallsa", "dbqueryfetchallsa.rst"), ("dbqueryfetchonem",
        "dbqueryfetchonem.rst"), ("dbqueryfetchonesa", "dbqueryfetchonesa.rst"), ("dbqueryfinish",
        "dbqueryfinish.rst"), ("dbquerygetboundvalue", "dbquerygetboundvalue.rst"), ("dbquerygetboundvalues",
        "dbquerygetboundvalues.rst"), ("dbquerygetfield", "dbquerygetfield.rst"), ("dbquerygetlasterrornum",
        "dbquerygetlasterrornum.rst"), ("dbquerygetlasterrortext", "dbquerygetlasterrortext.rst"),
        ("dbquerygetlastinsertid", "dbquerygetlastinsertid.rst"), ("dbquerygetlastquery",
        "dbquerygetlastquery.rst"), ("dbquerygetnumrowsaffected", "dbquerygetnumrowsaffected.rst"),
        ("dbquerygetposition", "dbquerygetposition.rst"), ("dbqueryisactive", "dbqueryisactive.rst"),
        ("dbqueryisforwardonly", "dbqueryisforwardonly.rst"), ("dbqueryisnull", "dbqueryisnull.rst"),
        ("dbqueryisselect", "dbqueryisselect.rst"), ("dbqueryisvalid", "dbqueryisvalid.rst"), ("dbqueryprepare",
        "dbqueryprepare.rst"), ("dbqueryrows", "dbqueryrows.rst"), ("dbqueryseek", "dbqueryseek.rst"),
        ("dbqueryseekfirst", "dbqueryseekfirst.rst"), ("dbqueryseeklast", "dbqueryseeklast.rst"),
        ("dbqueryseeknext", "dbqueryseeknext.rst"), ("dbqueryseekprevious", "dbqueryseekprevious.rst"),
        ("dbquerysetforwardonly", "dbquerysetforwardonly.rst"), ("dbremovedatabase", "dbremovedatabase.rst"),
        ("dbrollback", "dbrollback.rst"), ("dbsetconnectoptions", "dbsetconnectoptions.rst"),
        ("dbsetdatabasename", "dbsetdatabasename.rst"), ("dbsethostname", "dbsethostname.rst"),
        ("dbsetnumericalprecpolicy", "dbsetnumericalprecpolicy.rst"), ("dbsetpassword", "dbsetpassword.rst"),
        ("dbsetport", "dbsetport.rst"), ("dbsetusername", "dbsetusername.rst"), ("dbtransaction",
        "dbtransaction.rst"),
    ),
)

_SYSTEM_RULES_BY_NAME = {rule.name: rule for rule in _SYSTEM_STATEMENT_REGISTRY}
_SYSTEM_IDENTIFIER_NAMES = sorted((n for n in _SYSTEM_RULES_BY_NAME if not n.startswith("#")), key=len, reverse=True)
_SYSTEM_NAME_ALTERNATION = "|".join(re.escape(n) for n in _SYSTEM_IDENTIFIER_NAMES)
#: Statement position: at the start of a line or right after a `;`, and not
#: an assignment TO a variable that happens to share the name (`run = 5;`).
_SYSTEM_STATEMENT_RE = re.compile(
    r"(?:^|;)\s*(" + _SYSTEM_NAME_ALTERNATION + r")\b(?!\s*=(?!=))", re.IGNORECASE,
)
_SYSTEM_CALL_RE = re.compile(r"\b(" + _SYSTEM_NAME_ALTERNATION + r")\s*\(", re.IGNORECASE)
_INCLUDE_DIRECTIVE_RE = re.compile(r"^\s*#include\b", re.IGNORECASE)


@dataclass(frozen=True)
class SystemStatementFinding:
    name: str
    category: str
    line_number: int
    doc_page: str


def check_system_statements(code: str) -> tuple[SystemStatementFinding, ...]:
    """Deterministic, no I/O, no model input. Expects comment-stripped code
    (the engine strips comments before calling); masks double-quoted string
    contents first, so `print "dos is fine";` never matches. Fails closed: a
    match is never second-guessed as "probably harmless"."""
    findings: list[SystemStatementFinding] = []
    seen: set[tuple[str, int]] = set()
    for line_no, line in enumerate(code.splitlines(), start=1):
        masked = _QUOTED_STRING_RE.sub(lambda m: "#" * len(m.group(0)), line)
        names: list[str] = []
        if _INCLUDE_DIRECTIVE_RE.match(line):
            names.append("#include")
        names.extend(m.group(1).lower() for m in _SYSTEM_STATEMENT_RE.finditer(masked))
        names.extend(m.group(1).lower() for m in _SYSTEM_CALL_RE.finditer(masked))
        for name in names:
            if (name, line_no) in seen:
                continue
            seen.add((name, line_no))
            rule = _SYSTEM_RULES_BY_NAME[name]
            findings.append(SystemStatementFinding(
                name=name, category=rule.category, line_number=line_no, doc_page=rule.doc_page,
            ))
    return tuple(findings)


# ---------------------------------------------------------------------------
# Phase 9/10/11/16 (v0.76.0): future execution-handoff readiness
# ---------------------------------------------------------------------------


class HandoffReadiness(str, enum.Enum):
    """Distinct from, and strictly downstream of, `ExecutionEligibility`:
    `ELIGIBLE_FOR_VALIDATION` means "structurally worth validating";
    `HANDOFF_CANDIDATE` means "enough deterministic evidence exists to let a
    FUTURE, user-approved, explicit execution-handoff workflow consider
    it" -- still not executed, still not approved, still not semantically
    guaranteed correct, safe, or methodologically appropriate. This module
    contains no execution capability of any kind and this value is never
    consulted by, or capable of triggering, any execution path."""

    NOT_READY = "not_ready"
    REVIEW_REQUIRED = "review_required"
    HANDOFF_CANDIDATE = "handoff_candidate"


@dataclass(frozen=True)
class ReadinessResult:
    state: str
    reasons: tuple[str, ...]


def compute_handoff_readiness(
    *, eligibility: str, unresolved_issues: tuple[str, ...], syntax: SyntaxValidationResult | None,
    call_validations: tuple[CallValidationResult, ...], preconditions: tuple[PreconditionCheck, ...],
    evidence_profile: str, system_statements: tuple[SystemStatementFinding, ...] = (),
) -> ReadinessResult:
    """Deterministic, provider-independent: reads only its own arguments,
    calls no model, performs no I/O -- the model can never influence this
    verdict, exactly like `compute_eligibility(...)`. Conservative by
    design (Phase 10's own default policy):

    0. (v0.80.0) Any system-touching statement -> `NOT_READY`, checked
       first so its reason is always reported, whatever else is wrong.
    1. `eligibility != ELIGIBLE_FOR_VALIDATION` -> `NOT_READY` (both
       `INELIGIBLE` and `REQUIRES_CLARIFICATION` -- there is nothing yet
       for a future handoff workflow to consider).
    2. A KNOWN violation -- `syntax.status == INVALID` -- -> `NOT_READY`,
       reasons quote the syntax issues directly. (Every other known
       violation -- an incompatible signature, a violated precondition, a
       mismatched parameter role, an unknown call symbol -- already forces
       `eligibility != ELIGIBLE_FOR_VALIDATION` via `compute_eligibility(
       ...)`, so step 1 already covers those; this function does not
       re-derive them.)
    3. Otherwise, an evidence GAP (never a known violation) forces
       `REVIEW_REQUIRED`: syntax coverage itself is `PARTIAL`/`UNKNOWN`; a
       documented call's own signature could not be extracted
       (`signature_known == False`); a documented precondition remains
       `UNVERIFIED` (a real, runtime-dependent gap); or the overall
       evidence profile is not `BROAD`.
    4. No violation and no gap -> `HANDOFF_CANDIDATE`.
    """
    if system_statements:
        reasons = tuple(
            f"line {f.line_number}: `{f.name}` is a system-touching statement ({f.category}) -- controlled "
            "execution only runs self-contained snippets that compute in memory"
            for f in system_statements
        )
        return ReadinessResult(HandoffReadiness.NOT_READY.value, reasons)
    if eligibility == ExecutionEligibility.INELIGIBLE.value:
        reasons = unresolved_issues if unresolved_issues else ("code failed deterministic eligibility checks",)
        return ReadinessResult(HandoffReadiness.NOT_READY.value, tuple(reasons))
    if eligibility == ExecutionEligibility.REQUIRES_CLARIFICATION.value:
        reasons = unresolved_issues if unresolved_issues else (
            "unresolved topic ambiguity must be clarified before this code can be considered",
        )
        return ReadinessResult(HandoffReadiness.NOT_READY.value, tuple(reasons))

    if syntax is not None and syntax.status == SyntaxStatus.INVALID.value:
        reasons = tuple(f"syntax: {issue.message}" for issue in syntax.issues) or ("syntax validation found a violation",)
        return ReadinessResult(HandoffReadiness.NOT_READY.value, reasons)

    review_reasons: list[str] = []
    if syntax is None or syntax.status in (SyntaxStatus.PARTIAL.value, SyntaxStatus.UNKNOWN.value):
        status_label = syntax.status if syntax is not None else SyntaxStatus.UNKNOWN.value
        review_reasons.append(
            f"syntax validation coverage is {status_label} -- not all generated constructs could be "
            "deterministically checked"
        )
    unknown_signature_symbols = sorted({
        cv.symbol for cv in call_validations if cv.documented and not cv.signature_known
    })
    if unknown_signature_symbols:
        review_reasons.append(
            f"documented call signature could not be reliably extracted for: {', '.join(unknown_signature_symbols)}"
        )
    unverified_preconditions = [c for c in preconditions if c.status == PreconditionStatus.UNVERIFIED.value]
    if unverified_preconditions:
        symbols = ", ".join(sorted({c.precondition.symbol for c in unverified_preconditions}))
        review_reasons.append(f"runtime-dependent precondition(s) remain unverified for: {symbols}")
    if evidence_profile != EvidenceProfile.BROAD.value:
        review_reasons.append(
            f"validation coverage is {evidence_profile}, short of the broad evidence required for handoff candidacy"
        )

    if review_reasons:
        return ReadinessResult(HandoffReadiness.REVIEW_REQUIRED.value, tuple(review_reasons))

    return ReadinessResult(HandoffReadiness.HANDOFF_CANDIDATE.value, (
        "generated code is grounded and symbol-supported",
        "documented call signatures are compatible",
        "syntax was validated with no known violation",
        "no documented precondition is known to be violated",
        "validation coverage is broad",
    ))


# ---------------------------------------------------------------------------
# Phase 20/22: rendering
# ---------------------------------------------------------------------------


def render_validation_report(
    *, eligibility: str, unresolved_issues: tuple[str, ...], call_validations: tuple[CallValidationResult, ...],
    preconditions: tuple[PreconditionCheck, ...], companion_hints: tuple[tuple[str, str], ...],
    parameter_role_checks: tuple[ParameterRoleCheck, ...] = (), predicted_output: PredictedOutputClaim | None = None,
    coverage: ValidationCoverage | None = None, syntax: SyntaxValidationResult | None = None,
    readiness: ReadinessResult | None = None, system_statements: tuple[SystemStatementFinding, ...] = (),
) -> str:
    """Advisory, human-readable summary of this module's own evidence.
    Never implies real GAUSS execution occurred -- callers are expected to
    still append the existing, fixed "not executed in this conversation"
    footer (`gauss_conversation_engine.NOT_EXECUTED_FOOTER`) alongside this.
    v0.75.0's/v0.76.0's new optional parameters default to empty/`None` so
    every earlier call site remains valid unchanged."""
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

    if parameter_role_checks:
        lines.append("- Parameter checks:")
        for role_check in parameter_role_checks:
            label = role_check.parameter_name or f"argument {role_check.position + 1}"
            lines.append(f"  - {role_check.symbol} ({label}): {role_check.status} -- {role_check.explanation}")

    if predicted_output is not None and predicted_output.present:
        lines.append(f"- Predicted output: {predicted_output.verification_status}")
        if predicted_output.verification_status == OutputVerificationStatus.MISMATCH.value:
            lines.append(
                "  (The model's own claimed output does not match a deterministic recomputation -- this is a "
                "prediction-quality issue, separate from whether the code itself is eligible for validation.)"
            )
        elif predicted_output.verification_status == OutputVerificationStatus.VERIFIED.value:
            lines.append(
                "  (A deterministic recomputation matches the model's claimed output -- still not execution "
                "evidence: this code has not been run.)"
            )

    if syntax is not None:
        lines.append(f"- Syntax: {syntax.status}")
        for issue in syntax.issues:
            where = f" (line {issue.line_number})" if issue.line_number is not None else ""
            lines.append(f"  - {issue.message}{where}")
        if syntax.unknown_constructs:
            lines.append(
                "  - Not checked by this version: " + ", ".join(syntax.unknown_constructs)
            )

    if system_statements:
        lines.append("- System-touching statements (never run by controlled execution):")
        for finding in system_statements:
            lines.append(f"  - line {finding.line_number}: {finding.name} ({finding.category})")

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

    if coverage is not None:
        lines.append(
            "- Validation coverage: symbols={}, signature={}, parameter roles={}, preconditions={}, "
            "syntax={}, predicted output={}".format(
                coverage.symbol_check, coverage.signature_check, coverage.parameter_role_check,
                coverage.precondition_check, coverage.syntax_check, coverage.predicted_output_check,
            )
        )

    if readiness is not None:
        lines.append(f"- Execution handoff readiness: {readiness.state}")
        for reason in readiness.reasons:
            lines.append(f"  - {reason}")
        lines.append("  (This code has not been executed. This is not an approval to run it.)")

    return "\n".join(lines)
