"""Tests for `gauss_syntax_mutations.py` (v0.77.0).

Run with:

    python scripts/test_gauss_syntax_mutations.py

Fully synthetic and network-free: no real GAUSS execution, no real
documentation checkout, no model provider of any kind.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_syntax_mutations as mut  # noqa: E402

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


# ---------------------------------------------------------------------------
# Registry / description completeness
# ---------------------------------------------------------------------------


def test_01_every_operator_has_a_description() -> None:
    for name in mut.MUTATION_OPERATORS:
        check(f"{name} has a description", name in mut.MUTATION_DESCRIPTIONS)
    for name in mut.MUTATION_DESCRIPTIONS:
        check(f"{name} is a registered operator", name in mut.MUTATION_OPERATORS)


def test_02_apply_mutation_unknown_name_raises() -> None:
    try:
        mut.apply_mutation("not_a_real_operator", "x = 1;")
        check("KeyError raised", False)
    except KeyError:
        check("KeyError raised", True)


# ---------------------------------------------------------------------------
# Per-operator: applies where expected, inapplicable (None) where not,
# deterministic (same input -> same output).
# ---------------------------------------------------------------------------


def test_03_remove_closing_paren() -> None:
    check("applies", mut.remove_closing_paren("y = meanc(x);") == "y = meanc(x;")
    check("inapplicable", mut.remove_closing_paren("x = 1;") is None)


def test_04_remove_opening_paren() -> None:
    check("applies", mut.remove_opening_paren("y = meanc(x);") == "y = meancx);")
    check("inapplicable", mut.remove_opening_paren("x = 1;") is None)


def test_05_remove_closing_brace() -> None:
    check("applies", mut.remove_closing_brace("x = { 1 2 };") == "x = { 1 2 ;")
    check("inapplicable", mut.remove_closing_brace("x = 1;") is None)


def test_06_remove_opening_brace() -> None:
    check("applies", mut.remove_opening_brace("x = { 1 2 };") == "x =  1 2 };")
    check("inapplicable", mut.remove_opening_brace("x = 1;") is None)


def test_07_remove_rhs_from_assignment() -> None:
    check("applies", mut.remove_rhs_from_assignment("x = 1 + 2;") == "x = ;")
    check("already empty is inapplicable", mut.remove_rhs_from_assignment("x = ;") is None)
    check("no assignment is inapplicable", mut.remove_rhs_from_assignment("print x;") is None)


def test_08_remove_operator_between_tokens() -> None:
    check("applies to +", mut.remove_operator_between_tokens("x = a + b;") == "x = a  b;")
    check("does not eat unary minus in a literal", mut.remove_operator_between_tokens("x = -1;") is None)


def test_09_matrix_literal_semicolon_row_separator() -> None:
    check(
        "applies",
        mut.matrix_literal_semicolon_row_separator("x = { 1 2, 3 4 };") == "x = { 1 2; 3 4 };",
    )
    check("no comma is inapplicable", mut.matrix_literal_semicolon_row_separator("x = { 1 2 };") is None)
    check("no literal is inapplicable", mut.matrix_literal_semicolon_row_separator("x = 1;") is None)


def test_10_remove_comma_between_arguments() -> None:
    check("applies", mut.remove_comma_between_arguments("y = meanc(a, b);") == "y = meanc(a b);")
    check("single-arg call is inapplicable", mut.remove_comma_between_arguments("y = meanc(a);") is None)
    check("no call is inapplicable", mut.remove_comma_between_arguments("x = 1;") is None)


def test_11_add_stray_comma_two_args() -> None:
    result = mut.add_stray_comma("y = meanc(a, b);")
    check("duplicates a comma", result == "y = meanc(a,, b);")


def test_12_add_stray_comma_single_arg() -> None:
    result = mut.add_stray_comma("y = meanc(a);")
    check("adds trailing comma", result == "y = meanc(a,);")


def test_13_add_stray_comma_zero_arg() -> None:
    check("zero-arg call is inapplicable", mut.add_stray_comma("y = f();") is None)


def test_14_add_duplicate_delimiter() -> None:
    check("applies", mut.add_duplicate_delimiter("y = meanc(x);") == "y = meanc(x));")
    check("no paren is inapplicable", mut.add_duplicate_delimiter("x = 1;") is None)


def test_15_break_quoted_string() -> None:
    check("applies", mut.break_quoted_string('s = "hello";') == 's = "hello;')
    check("no string is inapplicable", mut.break_quoted_string("x = 1;") is None)


def test_16_unmatched_quote() -> None:
    check("applies", mut.unmatched_quote("x = 1;") == 'x = 1 ";')
    check("no trailing semicolon is inapplicable", mut.unmatched_quote("x = 1") is None)


def test_17_malformed_indexing_delimiters() -> None:
    check("applies", mut.malformed_indexing_delimiters("y = x[1];") == "y = x[1;")
    check("no indexing is inapplicable", mut.malformed_indexing_delimiters("x = 1;") is None)


def test_18_malformed_nested_call() -> None:
    result = mut.malformed_nested_call("z = meanc(reshape(x, 2, 2));")
    check("removes a closing paren", result == "z = meanc(reshape(x, 2, 2);")
    check("no nested call is inapplicable", mut.malformed_nested_call("y = meanc(x);") is None)


def test_19_invalid_delimiter_nesting() -> None:
    check("applies", mut.invalid_delimiter_nesting("y = meanc(x);") == "y = meanc{x);")
    check("no paren is inapplicable", mut.invalid_delimiter_nesting("x = 1;") is None)


def test_20_bare_multi_token_literal() -> None:
    check("applies", mut.bare_multi_token_literal("x = { -1 0 };") == "x = -1 0;")
    check("single-token literal is inapplicable", mut.bare_multi_token_literal("x = { 5 };") is None)
    check("no literal is inapplicable", mut.bare_multi_token_literal("x = 1;") is None)


def test_21_duplicated_statement_delimiter() -> None:
    check("applies", mut.duplicated_statement_delimiter("x = 1;") == "x = 1;;")
    check("no trailing semicolon is inapplicable", mut.duplicated_statement_delimiter("x = 1") is None)


# ---------------------------------------------------------------------------
# Determinism and no implicit chaining
# ---------------------------------------------------------------------------


def test_22_operators_are_deterministic() -> None:
    seed = "z = meanc(reshape({1 2, 3 4}, 2, 2));"
    for name, operator in mut.MUTATION_OPERATORS.items():
        first = operator(seed)
        second = operator(seed)
        check(f"{name} deterministic", first == second)


def test_23_apply_all_mutations_never_chains() -> None:
    """Every value in apply_all_mutations(...)'s result is the ORIGINAL seed
    with exactly one operator applied -- never a mutation of a mutation."""
    seed = "y = meanc(a, b);"
    results = mut.apply_all_mutations(seed)
    check("at least one operator applies", len(results) > 0)
    for name, mutated in results.items():
        check(f"{name} matches direct single application", mutated == mut.apply_mutation(name, seed))


def test_24_apply_all_mutations_drops_unchanged_and_none() -> None:
    seed = "x = 1;"  # a minimal snippet most structural operators cannot touch
    results = mut.apply_all_mutations(seed)
    for name, mutated in results.items():
        check(f"{name} actually changed the snippet", mutated != seed)


def run_tests() -> int:
    tests = [
        (name, fn)
        for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    for name, fn in tests:
        before = len(_failures)
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _failures.append(f"{name} raised {type(exc).__name__}: {exc}")
        if len(_failures) == before:
            print(f"PASS  {name}")
        else:
            for failure in _failures[before:]:
                print(f"FAIL  {name}: {failure}")
    print(f"\n{len(tests)} test function(s) run, {len(_failures)} check failure(s).")
    if _failures:
        print("SOME CHECKS FAILED.")
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
