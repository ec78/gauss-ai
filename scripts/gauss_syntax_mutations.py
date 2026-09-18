"""Deterministic, reproducible mutation operators for GAUSS syntax corpus
family B (v0.77.0 -- see `planning/v0.77.0-differential-syntax-validation.md`
Phase 5).

Each operator is a pure function `(code: str) -> str | None`: given one
known-valid GAUSS snippet, it returns either a mutated snippet (one
structural change applied) or `None` when the operator's target shape is not
present in `code` at all (e.g. `remove_closing_brace` on a snippet with no
`{...}` literal). `None` means "inapplicable to this seed," never "the
mutation failed" -- callers skip inapplicable (operator, seed) pairs rather
than raising.

Deliberately NOT a claim that every mutation produces genuinely invalid
GAUSS: `build_differential_corpus.py` records each mutation's `operator`/
`description`/`original_valid_snippet` as *candidate* invalid evidence,
and the real `tgauss.exe` oracle (`gauss_differential_harness.py`) is what
actually determines ACCEPTED vs. REJECTED_SYNTAX_OR_PARSE/RUNTIME_ERROR for
each mutated snippet -- this module never asserts ground truth about GAUSS
grammar itself, only performs one explicit, named structural edit per
operator. No operator chains another operator's output; composing two
mutations is a decision left to an explicit caller, never done implicitly
here.

Each operator applies to the FIRST matching site it finds in `code` (leftmost
match for removals, or the first practical insertion point for additions) --
deterministic and reproducible: running the same operator on the same seed
twice always produces the same output.
"""

from __future__ import annotations

import re
from typing import Callable

MutationOperator = Callable[[str], "str | None"]


def _find_matching(text: str, open_idx: int, open_ch: str, close_ch: str) -> int | None:
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return i
    return None


def remove_closing_paren(code: str) -> str | None:
    idx = code.rfind(")")
    if idx == -1:
        return None
    return code[:idx] + code[idx + 1 :]


def remove_opening_paren(code: str) -> str | None:
    idx = code.find("(")
    if idx == -1:
        return None
    return code[:idx] + code[idx + 1 :]


def remove_closing_brace(code: str) -> str | None:
    idx = code.rfind("}")
    if idx == -1:
        return None
    return code[:idx] + code[idx + 1 :]


def remove_opening_brace(code: str) -> str | None:
    idx = code.find("{")
    if idx == -1:
        return None
    return code[:idx] + code[idx + 1 :]


_ASSIGNMENT_RHS_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*\s*=\s*)(.+?)(;)")


def remove_rhs_from_assignment(code: str) -> str | None:
    match = _ASSIGNMENT_RHS_RE.search(code)
    if not match or not match.group(2).strip():
        return None
    return code[: match.start(2)] + code[match.end(2) :]


#: Matches one arithmetic/comparison operator sitting between two token-shaped
#: neighbors -- deliberately excludes a leading `-` (unary-minus/negative
#: literal risk) by requiring a token character immediately before it.
_INTER_TOKEN_OPERATOR_RE = re.compile(r"(?<=[A-Za-z0-9_\)\]])\s*([+\-*/])\s*(?=[A-Za-z0-9_\(])")


def remove_operator_between_tokens(code: str) -> str | None:
    match = _INTER_TOKEN_OPERATOR_RE.search(code)
    if not match:
        return None
    return code[: match.start(1)] + code[match.end(1) :]


def matrix_literal_semicolon_row_separator(code: str) -> str | None:
    """Reproduces the exact v0.76.0-motivating shape: a `,`-separated
    literal's row separator replaced with `;`."""
    open_idx = code.find("{")
    if open_idx == -1:
        return None
    close_idx = _find_matching(code, open_idx, "{", "}")
    if close_idx is None:
        return None
    content = code[open_idx + 1 : close_idx]
    comma_idx = content.find(",")
    if comma_idx == -1:
        return None
    new_content = content[:comma_idx] + ";" + content[comma_idx + 1 :]
    return code[: open_idx + 1] + new_content + code[close_idx:]


def _first_call_args_span(code: str) -> tuple[int, int] | None:
    """Returns `(open_idx, close_idx)` of the first top-level `(...)`
    immediately following a call-shaped identifier, or `None`."""
    match = re.search(r"[A-Za-z_][A-Za-z0-9_]*\s*\(", code)
    if not match:
        return None
    open_idx = match.end() - 1
    close_idx = _find_matching(code, open_idx, "(", ")")
    if close_idx is None:
        return None
    return open_idx, close_idx


def remove_comma_between_arguments(code: str) -> str | None:
    span = _first_call_args_span(code)
    if span is None:
        return None
    open_idx, close_idx = span
    args = code[open_idx + 1 : close_idx]
    comma_idx = args.find(",")
    if comma_idx == -1:
        return None
    new_args = args[:comma_idx] + args[comma_idx + 1 :]
    return code[: open_idx + 1] + new_args + code[close_idx:]


def add_stray_comma(code: str) -> str | None:
    span = _first_call_args_span(code)
    if span is None:
        return None
    open_idx, close_idx = span
    args = code[open_idx + 1 : close_idx]
    comma_idx = args.find(",")
    if comma_idx == -1:
        if not args.strip():
            return None
        # single-argument call: add a trailing stray comma, e.g. f(a) -> f(a,)
        new_args = args + ","
    else:
        # duplicate an existing comma, e.g. f(a, b) -> f(a, , b)
        new_args = args[: comma_idx + 1] + "," + args[comma_idx + 1 :]
    return code[: open_idx + 1] + new_args + code[close_idx:]


def add_duplicate_delimiter(code: str) -> str | None:
    idx = code.find(")")
    if idx == -1:
        return None
    return code[: idx + 1] + ")" + code[idx + 1 :]


_QUOTED_STRING_RE = re.compile(r'"[^"\n]*"')


def break_quoted_string(code: str) -> str | None:
    match = _QUOTED_STRING_RE.search(code)
    if not match:
        return None
    return code[: match.end() - 1] + code[match.end() :]


def unmatched_quote(code: str) -> str | None:
    """Inserts one stray, unpaired `"` immediately before the final `;`
    (independent of whether a real string already exists elsewhere)."""
    stripped = code.rstrip()
    if not stripped.endswith(";"):
        return None
    return stripped[:-1] + ' "' + ";"


_INDEXING_RE = re.compile(r"\[[^\[\]]*\]")


def malformed_indexing_delimiters(code: str) -> str | None:
    match = _INDEXING_RE.search(code)
    if not match:
        return None
    return code[: match.end() - 1] + code[match.end() :]


_NESTED_CALL_RE = re.compile(r"[A-Za-z_]\w*\s*\([^()]*[A-Za-z_]\w*\s*\([^()]*\)")


def malformed_nested_call(code: str) -> str | None:
    if not _NESTED_CALL_RE.search(code):
        return None
    return remove_closing_paren(code)


def invalid_delimiter_nesting(code: str) -> str | None:
    """Replaces the first `(` with `{` -- a real GAUSS call opener replaced
    with the wrong delimiter type, never a matched pair."""
    idx = code.find("(")
    if idx == -1:
        return None
    return code[:idx] + "{" + code[idx + 1 :]


_BARE_LITERAL_RE = re.compile(r"([A-Za-z_]\w*\s*=\s*)\{([^{}]*)\}(\s*;)")


def bare_multi_token_literal(code: str) -> str | None:
    """The exact v0.76.0 live-found regression shape: strips `{...}` from a
    multi-token numeric matrix literal, leaving a bare, brace-less,
    `let`-less right-hand side (`x = { -1 0 };` -> `x = -1 0;`)."""
    match = _BARE_LITERAL_RE.search(code)
    if not match:
        return None
    tokens = match.group(2).replace(",", " ").split()
    if len(tokens) < 2:
        return None
    return code[: match.start()] + match.group(1) + " ".join(tokens) + match.group(3)


def duplicated_statement_delimiter(code: str) -> str | None:
    stripped = code.rstrip()
    if not stripped.endswith(";"):
        return None
    return stripped + ";"


#: Name -> operator, in the same order as this milestone's Phase 5 list
#: (module docstring). Every entry here must be a pure function following the
#: `(code) -> str | None` contract documented above.
MUTATION_OPERATORS: dict[str, MutationOperator] = {
    "remove_closing_paren": remove_closing_paren,
    "remove_opening_paren": remove_opening_paren,
    "remove_closing_brace": remove_closing_brace,
    "remove_opening_brace": remove_opening_brace,
    "remove_rhs_from_assignment": remove_rhs_from_assignment,
    "remove_operator_between_tokens": remove_operator_between_tokens,
    "matrix_literal_semicolon_row_separator": matrix_literal_semicolon_row_separator,
    "remove_comma_between_arguments": remove_comma_between_arguments,
    "add_stray_comma": add_stray_comma,
    "add_duplicate_delimiter": add_duplicate_delimiter,
    "break_quoted_string": break_quoted_string,
    "unmatched_quote": unmatched_quote,
    "malformed_indexing_delimiters": malformed_indexing_delimiters,
    "malformed_nested_call": malformed_nested_call,
    "invalid_delimiter_nesting": invalid_delimiter_nesting,
    "bare_multi_token_literal": bare_multi_token_literal,
    "duplicated_statement_delimiter": duplicated_statement_delimiter,
}


#: Human-readable, one-line description per operator -- used by
#: `build_differential_corpus.py` to populate each mutation corpus item's
#: `mutation_description` field.
MUTATION_DESCRIPTIONS: dict[str, str] = {
    "remove_closing_paren": "removes the last `)` in the snippet",
    "remove_opening_paren": "removes the first `(` in the snippet",
    "remove_closing_brace": "removes the last `}` in the snippet",
    "remove_opening_brace": "removes the first `{` in the snippet",
    "remove_rhs_from_assignment": "empties an assignment's right-hand side (e.g. `x = ;`)",
    "remove_operator_between_tokens": "removes an arithmetic operator between two adjacent tokens",
    "matrix_literal_semicolon_row_separator": "replaces a matrix literal's `,` row separator with `;`",
    "remove_comma_between_arguments": "removes a comma between two call arguments",
    "add_stray_comma": "inserts a stray/duplicate comma into a call's argument list",
    "add_duplicate_delimiter": "duplicates a closing `)` immediately after itself",
    "break_quoted_string": "removes a double-quoted string's closing quote",
    "unmatched_quote": "inserts one stray, unpaired double quote before the final `;`",
    "malformed_indexing_delimiters": "removes the closing `]` from an indexing expression",
    "malformed_nested_call": "removes a closing `)` from a nested function call",
    "invalid_delimiter_nesting": "replaces an opening `(` with `{` (wrong delimiter type)",
    "bare_multi_token_literal": "strips `{...}` from a multi-token literal, leaving a bare brace-less RHS",
    "duplicated_statement_delimiter": "duplicates the trailing `;` statement delimiter",
}


def apply_mutation(name: str, code: str) -> str | None:
    """Looks up `name` in `MUTATION_OPERATORS` and applies it. Raises
    `KeyError` for an unregistered name -- never silently no-ops on a typo."""
    return MUTATION_OPERATORS[name](code)


def apply_all_mutations(code: str) -> dict[str, str]:
    """Applies every registered operator to `code`, returning only the
    mutations that actually produced a changed, non-`None` result (an
    operator returning `code` unchanged, or `None`, is dropped -- a
    mutation corpus item must be a real structural edit)."""
    results: dict[str, str] = {}
    for name, operator in MUTATION_OPERATORS.items():
        mutated = operator(code)
        if mutated is not None and mutated != code:
            results[name] = mutated
    return results
