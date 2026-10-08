"""Tests for `gauss_pre_execution_validation.py` (v0.74.0).

Run with:

    python scripts/test_gauss_pre_execution_validation.py

Fully synthetic and network-free: no real GAUSS execution, no real
documentation checkout, no model provider of any kind.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_pre_execution_validation as validation_mod  # noqa: E402

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _best_match(*, syntax_blocks, related_links=(), file_path="fixture.rst"):
    return {"syntax_blocks": syntax_blocks, "related_links": related_links, "file_path": file_path}


# ---------------------------------------------------------------------------
# Phase 4 / 18: documented signature extraction
# ---------------------------------------------------------------------------


def test_01_valid_documented_signature_meanc() -> None:
    sig = validation_mod.extract_documented_signature("meanc", _best_match(syntax_blocks=[".. function:: y = meanc(x)"]))
    check("extracted", sig.extraction_status == validation_mod.SIGNATURE_EXTRACTED)
    check("min/max 1/1", sig.arg_ranges == ((1, 1),))
    check("parameter name x", sig.parameter_names == ("x",))


def test_02_optional_argument_signature_tscsfit() -> None:
    sig = validation_mod.extract_documented_signature(
        "tscsFit", _best_match(syntax_blocks=[".. function:: tso = tscsFit(y, x, grp[, tsc])"]),
    )
    check("extracted", sig.extraction_status == validation_mod.SIGNATURE_EXTRACTED)
    check("min 3 max 4", sig.arg_ranges == ((3, 4),))
    check("names include optional tsc", sig.parameter_names == ("y", "x", "grp", "tsc"))


def test_03_zero_argument_legacy_style_signature() -> None:
    sig = validation_mod.extract_documented_signature(
        "tscsmtControlCreate", _best_match(syntax_blocks=["tsc = tscsmtControlCreate( );"]),
    )
    check("extracted", sig.extraction_status == validation_mod.SIGNATURE_EXTRACTED)
    check("zero args", sig.arg_ranges == ((0, 0),))


def test_04_multiple_overloads_produce_multiple_ranges() -> None:
    sig = validation_mod.extract_documented_signature(
        "tscsFit",
        _best_match(syntax_blocks=[
            ".. function:: tso = tscsFit(y, x, grp[, tsc])",
            "tso = tscsFit(dataset, formula, grp[, tsc])",
        ]),
    )
    check("one merged range since both overloads share the same shape", sig.arg_ranges == ((3, 4),))


def test_05_unknown_signature_when_symbol_not_call_shaped_anywhere() -> None:
    sig = validation_mod.extract_documented_signature("olsmt", _best_match(syntax_blocks=["some unrelated prose"]))
    check("unknown", sig.extraction_status == validation_mod.SIGNATURE_UNKNOWN)
    check("empty ranges", sig.arg_ranges == ())


def test_06_malformed_or_empty_syntax_blocks_fail_closed() -> None:
    sig = validation_mod.extract_documented_signature("foo", _best_match(syntax_blocks=[]))
    check("unknown, not a crash", sig.extraction_status == validation_mod.SIGNATURE_UNKNOWN)


# ---------------------------------------------------------------------------
# Phase 5 / 18: generated-call extraction
# ---------------------------------------------------------------------------


def test_07_single_call_extracted() -> None:
    calls = validation_mod.extract_generated_calls("y = meanc(x);")
    check("one call", len(calls) == 1)
    check("symbol meanc, 1 arg", calls[0].symbol == "meanc" and calls[0].argument_count == 1)


def test_08_nested_call_extracts_both_outer_and_inner() -> None:
    calls = validation_mod.extract_generated_calls("z = f(g(x), y);")
    symbols = {c.symbol for c in calls}
    check("both f and g extracted", symbols == {"f", "g"})
    f_call = next(c for c in calls if c.symbol == "f")
    check("f has two top-level arguments", f_call.argument_count == 2)


def test_09_multiple_calls_on_separate_lines() -> None:
    code = "a = meanc(x);\nb = stdc(x);\n"
    calls = validation_mod.extract_generated_calls(code)
    check("two calls found", len(calls) == 2)
    check("line numbers recorded", {c.line_number for c in calls} == {1, 2})


def test_10_variable_names_are_not_treated_as_calls() -> None:
    calls = validation_mod.extract_generated_calls("x = 5;\ny = x + 1;\n")
    check("no calls extracted from plain assignments", calls == ())


def test_11_control_flow_lines_are_skipped() -> None:
    calls = validation_mod.extract_generated_calls("for i (1, 3, 1);\n  print i;\nendfor;\n")
    symbols = {c.symbol for c in calls}
    check("loop header not mistaken for a call", "i" not in symbols)


def test_12_malformed_code_with_unbalanced_parens_handled_conservatively() -> None:
    calls = validation_mod.extract_generated_calls("y = meanc(x;\n")
    check("no crash, no fabricated call for the unterminated paren", calls == ())


# ---------------------------------------------------------------------------
# Phase 6 / 18: signature compatibility validation
# ---------------------------------------------------------------------------


def test_13_compatible_call() -> None:
    call = validation_mod.GeneratedCall(symbol="meanc", argument_count=1, raw_arguments=("x",), line_number=1)
    sig = validation_mod.DocumentedSignature(
        symbol="meanc", arg_ranges=((1, 1),), parameter_names=("x",), source="meanc.rst",
        extraction_status=validation_mod.SIGNATURE_EXTRACTED,
    )
    result = validation_mod.validate_call(call, documented_signatures={"meanc": sig}, documented_symbols=frozenset({"meanc"}))
    check("compatible", result.argument_count_status == validation_mod.SignatureCompatibility.COMPATIBLE.value)


def test_14_incompatible_too_few_arguments() -> None:
    call = validation_mod.GeneratedCall(symbol="tscsFit", argument_count=2, raw_arguments=("y", "x"), line_number=1)
    sig = validation_mod.DocumentedSignature(
        symbol="tscsFit", arg_ranges=((3, 4),), parameter_names=("y", "x", "grp", "tsc"), source="tscsfit.rst",
        extraction_status=validation_mod.SIGNATURE_EXTRACTED,
    )
    result = validation_mod.validate_call(call, documented_signatures={"tscsfit": sig}, documented_symbols=frozenset({"tscsfit"}))
    check("incompatible", result.argument_count_status == validation_mod.SignatureCompatibility.INCOMPATIBLE.value)
    check("issue mentions passed count", "2" in result.issues[0])


def test_15_incompatible_too_many_arguments() -> None:
    call = validation_mod.GeneratedCall(symbol="meanc", argument_count=2, raw_arguments=("x", "y"), line_number=1)
    sig = validation_mod.DocumentedSignature(
        symbol="meanc", arg_ranges=((1, 1),), parameter_names=("x",), source="meanc.rst",
        extraction_status=validation_mod.SIGNATURE_EXTRACTED,
    )
    result = validation_mod.validate_call(call, documented_signatures={"meanc": sig}, documented_symbols=frozenset({"meanc"}))
    check("incompatible", result.argument_count_status == validation_mod.SignatureCompatibility.INCOMPATIBLE.value)


def test_16_unknown_signature_does_not_claim_incompatible() -> None:
    call = validation_mod.GeneratedCall(symbol="olsmt", argument_count=3, raw_arguments=("a", "b", "c"), line_number=1)
    unknown_sig = validation_mod.DocumentedSignature(
        symbol="olsmt", arg_ranges=(), parameter_names=(), source="olsmt.rst",
        extraction_status=validation_mod.SIGNATURE_UNKNOWN,
    )
    result = validation_mod.validate_call(call, documented_signatures={"olsmt": unknown_sig}, documented_symbols=frozenset({"olsmt"}))
    check("unknown, not incompatible", result.argument_count_status == validation_mod.SignatureCompatibility.UNKNOWN.value)
    check("still marked documented", result.documented is True)


def test_17_unknown_symbol_not_among_documented_topics() -> None:
    call = validation_mod.GeneratedCall(symbol="colmean", argument_count=1, raw_arguments=("x",), line_number=1)
    result = validation_mod.validate_call(call, documented_signatures={}, documented_symbols=frozenset({"meanc"}))
    check("not documented", result.documented is False)
    check("unknown status", result.argument_count_status == validation_mod.SignatureCompatibility.UNKNOWN.value)


# ---------------------------------------------------------------------------
# Phase 7: companion-function mismatch detection
# ---------------------------------------------------------------------------


def test_18_companion_hint_found_for_tscsmtcontrol() -> None:
    hint = validation_mod.find_companion_hint("tscsmtControl", companions=frozenset({"tscsmtControlCreate", "tscsFit"}))
    check("companion found", hint == "tscsmtControlCreate")


def test_19_no_companion_hint_when_nothing_relates() -> None:
    hint = validation_mod.find_companion_hint("colmean", companions=frozenset({"meanc", "stdc"}))
    check("no hint fabricated", hint is None)


# ---------------------------------------------------------------------------
# Phase 9 / 10 / 16: documented preconditions -- the invpd hard regression
# ---------------------------------------------------------------------------


def test_20_invpd_valid_symmetric_positive_definite_literal() -> None:
    call = validation_mod.GeneratedCall(symbol="invpd", argument_count=1, raw_arguments=("{2 1, 1 2}",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="y = invpd({2 1, 1 2});")
    check("one precondition checked", len(checks) == 1)
    check("satisfied", checks[0].status == validation_mod.PreconditionStatus.SATISFIED.value)


def test_21_invpd_non_symmetric_literal_is_violated() -> None:
    call = validation_mod.GeneratedCall(symbol="invpd", argument_count=1, raw_arguments=("{2 1, 3 2}",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="y = invpd({2 1, 3 2});")
    check("violated", checks[0].status == validation_mod.PreconditionStatus.VIOLATED.value)
    check("explanation names symmetry", "symmetric" in checks[0].explanation)


def test_22_invpd_symmetric_but_not_positive_definite_is_violated() -> None:
    # Symmetric (off-diagonals equal) but the leading 1x1 minor is negative.
    call = validation_mod.GeneratedCall(symbol="invpd", argument_count=1, raw_arguments=("{-1 0, 0 -1}",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="y = invpd({-1 0, 0 -1});")
    check("violated", checks[0].status == validation_mod.PreconditionStatus.VIOLATED.value)
    check("explanation names positive definiteness", "positive definite" in checks[0].explanation)


def test_23_invpd_runtime_variable_is_unverified() -> None:
    call = validation_mod.GeneratedCall(symbol="invpd", argument_count=1, raw_arguments=("x",), line_number=2)
    checks = validation_mod.check_preconditions(call, code="x = loadd(\"data.csv\");\ny = invpd(x);")
    check("unverified", checks[0].status == validation_mod.PreconditionStatus.UNVERIFIED.value)


def test_24_invpd_via_identifier_assigned_to_a_literal_earlier_is_checked() -> None:
    call = validation_mod.GeneratedCall(symbol="invpd", argument_count=1, raw_arguments=("m",), line_number=2)
    checks = validation_mod.check_preconditions(call, code="m = {2 1, 1 2};\ny = invpd(m);")
    check("satisfied via traced literal assignment", checks[0].status == validation_mod.PreconditionStatus.SATISFIED.value)


def test_25_invpd_expression_argument_like_x_transpose_x_is_unverified_not_guessed() -> None:
    """The real documented invpd(x'x) OLS example -- a matrix PRODUCT
    expression, not a literal or a simple variable. Must never be
    partially evaluated or guessed at."""
    call = validation_mod.GeneratedCall(symbol="invpd", argument_count=1, raw_arguments=("x'x",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="bols = invpd(x'x)*x'y;")
    check("unverified, never fabricated", checks[0].status == validation_mod.PreconditionStatus.UNVERIFIED.value)


def test_26_no_precondition_entry_for_a_symbol_with_none_curated() -> None:
    call = validation_mod.GeneratedCall(symbol="meanc", argument_count=1, raw_arguments=("x",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="y = meanc(x);")
    check("no preconditions curated for meanc", checks == ())


def test_27_inv_precondition_square_nonsingular_literal_is_satisfied() -> None:
    """v0.75.0 superseded v0.74.0's expectation here: `inv`'s precondition
    was curated but deliberately left `machine_checkable=False` in v0.74.0
    (no deterministic invertibility test existed yet). v0.75.0 adds one --
    an exact determinant computation reusing the same cofactor machinery
    `invpd`'s own check already uses -- so a literal, square, nonsingular
    matrix is now correctly reported SATISFIED rather than UNVERIFIED. See
    `_PRECONDITION_INDEX["inv"]`'s own updated description."""
    call = validation_mod.GeneratedCall(symbol="inv", argument_count=1, raw_arguments=("{2 1, 1 2}",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="y = inv({2 1, 1 2});")
    check("one precondition", len(checks) == 1)
    check("satisfied -- square with nonzero determinant", checks[0].status == validation_mod.PreconditionStatus.SATISFIED.value)


def test_27b_inv_precondition_singular_literal_is_violated() -> None:
    call = validation_mod.GeneratedCall(symbol="inv", argument_count=1, raw_arguments=("{1 2, 2 4}",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="y = inv({1 2, 2 4});")
    check("violated -- zero determinant", checks[0].status == validation_mod.PreconditionStatus.VIOLATED.value)
    check("explanation names determinant/singular", "determinant" in checks[0].explanation or "singular" in checks[0].explanation)


def test_27c_inv_precondition_non_square_literal_is_violated() -> None:
    call = validation_mod.GeneratedCall(symbol="inv", argument_count=1, raw_arguments=("{1 2 3, 4 5 6}",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="y = inv({1 2 3, 4 5 6});")
    check("violated -- not square", checks[0].status == validation_mod.PreconditionStatus.VIOLATED.value)


def test_27d_inv_precondition_runtime_variable_is_unverified() -> None:
    call = validation_mod.GeneratedCall(symbol="inv", argument_count=1, raw_arguments=("x",), line_number=2)
    checks = validation_mod.check_preconditions(call, code="x = loadd(\"data.csv\");\ny = inv(x);")
    check("unverified", checks[0].status == validation_mod.PreconditionStatus.UNVERIFIED.value)


# ---------------------------------------------------------------------------
# v0.75.0 Phase 7: new precondition families -- solpd, chol
# ---------------------------------------------------------------------------


def test_27e_solpd_valid_positive_definite_second_argument() -> None:
    call = validation_mod.GeneratedCall(symbol="solpd", argument_count=2, raw_arguments=("b", "{2 1, 1 2}"), line_number=1)
    checks = validation_mod.check_preconditions(call, code="x = solpd(b, {2 1, 1 2});")
    check("one precondition", len(checks) == 1)
    check("satisfied", checks[0].status == validation_mod.PreconditionStatus.SATISFIED.value)


def test_27f_solpd_invalid_not_positive_definite_second_argument() -> None:
    call = validation_mod.GeneratedCall(symbol="solpd", argument_count=2, raw_arguments=("b", "{-1 0, 0 -1}"), line_number=1)
    checks = validation_mod.check_preconditions(call, code="x = solpd(b, {-1 0, 0 -1});")
    check("violated", checks[0].status == validation_mod.PreconditionStatus.VIOLATED.value)


def test_27g_solpd_does_not_require_literal_symmetry_only_positive_definite_upper_triangle() -> None:
    """solpd.rst's own text: "solpd does not check to see that the matrix A
    is symmetric. solpd will look only at the upper half of the matrix
    including the principal diagonal." A non-symmetric literal whose UPPER
    triangle implies a positive-definite matrix must be SATISFIED, never
    VIOLATED merely for being non-symmetric (unlike invpd, which genuinely
    requires symmetry)."""
    # Upper-right entry is 1 (a genuinely positive-definite value once
    # reflected); lower-left is 999, deliberately different -- solpd's own
    # documented convention ignores the lower triangle entirely, so this
    # must be SATISFIED even though the raw literal is not symmetric.
    call = validation_mod.GeneratedCall(symbol="solpd", argument_count=2, raw_arguments=("b", "{2 1, 999 2}"), line_number=1)
    checks = validation_mod.check_preconditions(call, code="x = solpd(b, {2 1, 999 2});")
    check("satisfied via upper-triangle convention, not blocked by asymmetry", checks[0].status == validation_mod.PreconditionStatus.SATISFIED.value)


def test_27h_solpd_missing_second_argument_is_unverified() -> None:
    call = validation_mod.GeneratedCall(symbol="solpd", argument_count=1, raw_arguments=("b",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="x = solpd(b);")
    check("unverified -- documented A argument not found", checks[0].status == validation_mod.PreconditionStatus.UNVERIFIED.value)


def test_27i_chol_valid_positive_definite_literal() -> None:
    call = validation_mod.GeneratedCall(symbol="chol", argument_count=1, raw_arguments=("{2 1, 1 2}",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="u = chol({2 1, 1 2});")
    check("satisfied", checks[0].status == validation_mod.PreconditionStatus.SATISFIED.value)


def test_27j_chol_invalid_not_positive_definite_literal() -> None:
    call = validation_mod.GeneratedCall(symbol="chol", argument_count=1, raw_arguments=("{-1 0, 0 -1}",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="u = chol({-1 0, 0 -1});")
    check("violated", checks[0].status == validation_mod.PreconditionStatus.VIOLATED.value)


def test_28_no_check_ever_fabricates_satisfied_without_a_literal() -> None:
    for raw_arg in ("z", "compute(a, b)", "a + b"):
        call = validation_mod.GeneratedCall(symbol="invpd", argument_count=1, raw_arguments=(raw_arg,), line_number=1)
        checks = validation_mod.check_preconditions(call, code=f"y = invpd({raw_arg});")
        check(f"never satisfied for non-literal argument {raw_arg!r}", checks[0].status != validation_mod.PreconditionStatus.SATISFIED.value)


# ---------------------------------------------------------------------------
# Phase 12 / 13: execution eligibility
# ---------------------------------------------------------------------------


def _compatible(symbol: str) -> validation_mod.CallValidationResult:
    return validation_mod.CallValidationResult(
        symbol=symbol, documented=True, signature_known=True,
        argument_count_status=validation_mod.SignatureCompatibility.COMPATIBLE.value, issues=(), source="x.rst",
    )


def _incompatible(symbol: str) -> validation_mod.CallValidationResult:
    return validation_mod.CallValidationResult(
        symbol=symbol, documented=True, signature_known=True,
        argument_count_status=validation_mod.SignatureCompatibility.INCOMPATIBLE.value,
        issues=("wrong count",), source="x.rst",
    )


def test_29_unknown_symbol_makes_it_ineligible() -> None:
    eligibility, issues = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=("colmean",), ambiguous_topics=(),
        call_validations=(), preconditions=(), code_extraction_ok=True,
    )
    check("ineligible", eligibility == validation_mod.ExecutionEligibility.INELIGIBLE.value)
    check("issue names the symbol", any("colmean" in i for i in issues))


def test_30_incompatible_signature_makes_it_ineligible() -> None:
    eligibility, _ = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=(), ambiguous_topics=(),
        call_validations=(_incompatible("tscsFit"),), preconditions=(), code_extraction_ok=True,
    )
    check("ineligible", eligibility == validation_mod.ExecutionEligibility.INELIGIBLE.value)


def test_31_violated_precondition_makes_it_ineligible() -> None:
    precondition = validation_mod.DocumentedPrecondition(
        symbol="invpd", description="d", kind="property", source="s", machine_checkable=True,
    )
    violated = validation_mod.PreconditionCheck(precondition, validation_mod.PreconditionStatus.VIOLATED.value, "not symmetric")
    eligibility, issues = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=(), ambiguous_topics=(),
        call_validations=(_compatible("invpd"),), preconditions=(violated,), code_extraction_ok=True,
    )
    check("ineligible", eligibility == validation_mod.ExecutionEligibility.INELIGIBLE.value)
    check("issue names invpd", any("invpd" in i for i in issues))


def test_32_ambiguity_takes_priority_and_requires_clarification() -> None:
    eligibility, issues = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=("colmean",), ambiguous_topics=("olsmt/olsqr",),
        call_validations=(), preconditions=(), code_extraction_ok=True,
    )
    check("requires clarification, not ineligible", eligibility == validation_mod.ExecutionEligibility.REQUIRES_CLARIFICATION.value)


def test_33_fully_supported_example_is_eligible_for_validation() -> None:
    eligibility, issues = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=(), ambiguous_topics=(),
        call_validations=(_compatible("meanc"),), preconditions=(), code_extraction_ok=True,
    )
    check("eligible", eligibility == validation_mod.ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value)
    check("no issues", issues == ())


def test_34_unverified_precondition_does_not_block_eligibility() -> None:
    """Per this milestone's own Phase 13 rule: an UNVERIFIED precondition
    is a disclosed gap, not a violation -- it must not, by itself, prevent
    ELIGIBLE_FOR_VALIDATION."""
    precondition = validation_mod.DocumentedPrecondition(
        symbol="invpd", description="d", kind="property", source="s", machine_checkable=True,
    )
    unverified = validation_mod.PreconditionCheck(precondition, validation_mod.PreconditionStatus.UNVERIFIED.value, "runtime value")
    eligibility, issues = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=(), ambiguous_topics=(),
        call_validations=(_compatible("invpd"),), preconditions=(unverified,), code_extraction_ok=True,
    )
    check("still eligible", eligibility == validation_mod.ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value)


def test_35_unknown_signature_does_not_block_eligibility() -> None:
    unknown_sig_call = validation_mod.CallValidationResult(
        symbol="olsmt", documented=True, signature_known=False,
        argument_count_status=validation_mod.SignatureCompatibility.UNKNOWN.value,
        issues=("signature could not be extracted",), source=None,
    )
    eligibility, _ = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=(), ambiguous_topics=(),
        call_validations=(unknown_sig_call,), preconditions=(), code_extraction_ok=True,
    )
    check("still eligible", eligibility == validation_mod.ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value)


def test_36_generation_policy_that_did_not_permit_generation_is_ineligible() -> None:
    eligibility, _ = validation_mod.compute_eligibility(
        generation_policy="block", unknown_symbols=(), ambiguous_topics=(),
        call_validations=(), preconditions=(), code_extraction_ok=True,
    )
    check("ineligible", eligibility == validation_mod.ExecutionEligibility.INELIGIBLE.value)


# ---------------------------------------------------------------------------
# Phase 20: rendering
# ---------------------------------------------------------------------------


def test_37_render_report_never_implies_execution_occurred() -> None:
    report = validation_mod.render_validation_report(
        eligibility=validation_mod.ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value,
        unresolved_issues=(), call_validations=(_compatible("meanc"),), preconditions=(), companion_hints=(),
    )
    for banned in ("executed successfully", "ran the code", "verified correct"):
        check(f"report does not claim {banned!r}", banned not in report.lower())
    check("eligibility line present", "eligible_for_validation" in report)


def test_38_render_report_shows_companion_hint() -> None:
    report = validation_mod.render_validation_report(
        eligibility=validation_mod.ExecutionEligibility.INELIGIBLE.value,
        unresolved_issues=("tscsmtControl unsupported",), call_validations=(),
        preconditions=(), companion_hints=(("tscsmtControl", "tscsmtControlCreate"),),
    )
    check("hint text present", "tscsmtControlCreate" in report and "tscsmtControl" in report)


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------


def test_39_module_has_no_execution_shell_or_file_write_capability() -> None:
    source = Path(validation_mod.__file__).read_text(encoding="utf-8")
    for token in ("write_text", "write_bytes", "os.system", "subprocess.", "eval(", "exec(", "shutil."):
        check(f"module source does not contain {token!r}", token not in source)


def test_40_model_cannot_override_eligibility() -> None:
    """`compute_eligibility(...)` takes no provider/model argument at all --
    structurally, no model output can influence its return value."""
    import inspect

    params = inspect.signature(validation_mod.compute_eligibility).parameters
    for name in params:
        check(f"parameter {name!r} is not model/provider-shaped", "model" not in name.lower() and "provider" not in name.lower())


# ---------------------------------------------------------------------------
# v0.75.0 Phase 4/18: richer documented parameter metadata
# ---------------------------------------------------------------------------


def test_41_classify_documented_type_scalar() -> None:
    categories, shape = validation_mod.classify_documented_type("scalar")
    check("scalar category", categories == (validation_mod.TypeClass.SCALAR.value,))
    check("unknown shape", shape == validation_mod.ShapeConstraint.UNKNOWN.value)


def test_42_classify_documented_type_string() -> None:
    categories, _ = validation_mod.classify_documented_type("string")
    check("string category", categories == (validation_mod.TypeClass.STRING.value,))


def test_43_classify_documented_type_square_matrix() -> None:
    categories, shape = validation_mod.classify_documented_type("NxN matrix")
    check("matrix category", validation_mod.TypeClass.MATRIX.value in categories)
    check("square shape", shape == validation_mod.ShapeConstraint.SQUARE.value)


def test_44_classify_documented_type_column_vector() -> None:
    categories, shape = validation_mod.classify_documented_type("Nx1 vector")
    check("vector category", validation_mod.TypeClass.VECTOR.value in categories)
    check("column vector shape", shape == validation_mod.ShapeConstraint.COLUMN_VECTOR.value)


def test_45_classify_documented_type_multi_category_enumeration() -> None:
    """Real documented text (`a: matrix, vector, or scalar`, seen across
    this session's own docs corpus) is a genuine enumeration -- every
    named category should be captured, not just the first."""
    categories, _ = validation_mod.classify_documented_type("matrix, vector, or scalar")
    check("all three captured", set(categories) == {
        validation_mod.TypeClass.MATRIX.value, validation_mod.TypeClass.VECTOR.value, validation_mod.TypeClass.SCALAR.value,
    })


def test_46_classify_documented_type_unknown_for_empty_or_unrecognized() -> None:
    categories, shape = validation_mod.classify_documented_type("")
    check("unknown category for empty text", categories == (validation_mod.TypeClass.UNKNOWN.value,))
    categories2, _ = validation_mod.classify_documented_type("opaque handle")
    check("unknown category for unrecognized text", categories2 == (validation_mod.TypeClass.UNKNOWN.value,))


def test_47_extract_documented_signature_populates_parameters_from_type_lines() -> None:
    best_match = _best_match(
        syntax_blocks=[".. function:: y = meanc(x)"],
    )
    best_match["inputs_section"] = ":param x: data\n:type x: NxK matrix"
    sig = validation_mod.extract_documented_signature("meanc", best_match)
    check("one parameter extracted", len(sig.parameters) == 1)
    param = sig.parameters[0]
    check("name x", param.name == "x")
    check("required", param.required is True)
    check("position 0", param.position == 0)
    check("matrix category", validation_mod.TypeClass.MATRIX.value in param.category)


def test_48_extract_documented_signature_no_type_lines_yields_unknown_parameters() -> None:
    sig = validation_mod.extract_documented_signature("meanc", _best_match(syntax_blocks=[".. function:: y = meanc(x)"]))
    check("one parameter", len(sig.parameters) == 1)
    check("unknown category when no :type line present", sig.parameters[0].category == (validation_mod.TypeClass.UNKNOWN.value,))


def test_49_optional_parameter_marked_not_required() -> None:
    best_match = _best_match(syntax_blocks=[".. function:: tso = tscsFit(y, x, grp[, tsc])"])
    best_match["inputs_section"] = (
        ":param y: dependent variable\n:type y: Nx1 vector\n\n"
        ":param x: regressors\n:type x: NxK matrix\n\n"
        ":param grp: group id\n:type grp: Nx1 vector\n\n"
        ":param tsc: control structure\n:type tsc: struct"
    )
    sig = validation_mod.extract_documented_signature("tscsFit", best_match)
    by_name = {p.name: p for p in sig.parameters}
    check("y required", by_name["y"].required is True)
    check("tsc optional", by_name["tsc"].required is False)
    check("tsc position 3", by_name["tsc"].position == 3)
    check("tsc control category", by_name["tsc"].category == (validation_mod.TypeClass.CONTROL.value,))


# ---------------------------------------------------------------------------
# v0.75.0 Phase 6/18: basic literal type/shape inference
# ---------------------------------------------------------------------------


def test_50_infer_literal_category_numeric_scalar() -> None:
    category, _ = validation_mod.infer_literal_category("5")
    check("scalar", category == validation_mod.TypeClass.SCALAR.value)


def test_51_infer_literal_category_string() -> None:
    category, _ = validation_mod.infer_literal_category('"hello"')
    check("string", category == validation_mod.TypeClass.STRING.value)


def test_52_infer_literal_category_literal_vector_column() -> None:
    category, shape = validation_mod.infer_literal_category("{1, 2, 3}")
    check("vector", category == validation_mod.TypeClass.VECTOR.value)
    check("column vector shape", shape == validation_mod.ShapeConstraint.COLUMN_VECTOR.value)


def test_53_infer_literal_category_literal_matrix_square() -> None:
    category, shape = validation_mod.infer_literal_category("{1 2, 3 4}")
    check("matrix", category == validation_mod.TypeClass.MATRIX.value)
    check("square", shape == validation_mod.ShapeConstraint.SQUARE.value)


def test_54_infer_literal_category_literal_matrix_non_square() -> None:
    category, shape = validation_mod.infer_literal_category("{1 2 3, 4 5 6}")
    check("matrix", category == validation_mod.TypeClass.MATRIX.value)
    check("shape not claimed square", shape != validation_mod.ShapeConstraint.SQUARE.value)


def test_55_infer_literal_category_runtime_variable_is_unknown() -> None:
    category, shape = validation_mod.infer_literal_category("x")
    check("unknown category for a runtime variable", category == validation_mod.TypeClass.UNKNOWN.value)
    check("unknown shape", shape == validation_mod.ShapeConstraint.UNKNOWN.value)


def _signature_with_params(*params: validation_mod.DocumentedParameter) -> validation_mod.DocumentedSignature:
    return validation_mod.DocumentedSignature(
        symbol="f", arg_ranges=((len(params), len(params)),), parameter_names=tuple(p.name for p in params),
        source="fixture.rst", extraction_status=validation_mod.SIGNATURE_EXTRACTED, parameters=tuple(params),
    )


def test_56_parameter_role_match_for_correct_literal_type() -> None:
    signature = _signature_with_params(
        validation_mod.DocumentedParameter(name="x", required=True, position=0, category=(validation_mod.TypeClass.MATRIX.value,), shape="unknown", source="matrix"),
    )
    call = validation_mod.GeneratedCall(symbol="f", argument_count=1, raw_arguments=("{1 2, 3 4}",), line_number=1)
    checks = validation_mod.check_parameter_roles(call, signature=signature)
    check("match", checks[0].status == validation_mod.ParameterRoleStatus.MATCH.value)


def test_57_parameter_role_mismatch_for_obvious_wrong_literal_type() -> None:
    signature = _signature_with_params(
        validation_mod.DocumentedParameter(name="x", required=True, position=0, category=(validation_mod.TypeClass.MATRIX.value,), shape="unknown", source="matrix"),
    )
    call = validation_mod.GeneratedCall(symbol="f", argument_count=1, raw_arguments=('"not a matrix"',), line_number=1)
    checks = validation_mod.check_parameter_roles(call, signature=signature)
    check("mismatch", checks[0].status == validation_mod.ParameterRoleStatus.MISMATCH.value)


def test_58_parameter_role_unknown_for_runtime_variable() -> None:
    signature = _signature_with_params(
        validation_mod.DocumentedParameter(name="x", required=True, position=0, category=(validation_mod.TypeClass.MATRIX.value,), shape="unknown", source="matrix"),
    )
    call = validation_mod.GeneratedCall(symbol="f", argument_count=1, raw_arguments=("x",), line_number=1)
    checks = validation_mod.check_parameter_roles(call, signature=signature)
    check("unknown, not mismatch, for a runtime variable", checks[0].status == validation_mod.ParameterRoleStatus.UNKNOWN.value)


def test_59_parameter_role_unknown_when_documented_category_unknown() -> None:
    signature = _signature_with_params(
        validation_mod.DocumentedParameter(name="x", required=True, position=0, category=(validation_mod.TypeClass.UNKNOWN.value,), shape="unknown", source=None),
    )
    call = validation_mod.GeneratedCall(symbol="f", argument_count=1, raw_arguments=("5",), line_number=1)
    checks = validation_mod.check_parameter_roles(call, signature=signature)
    check("unknown when doc category itself unknown", checks[0].status == validation_mod.ParameterRoleStatus.UNKNOWN.value)


def test_60_parameter_role_match_against_multi_category_enumeration() -> None:
    signature = _signature_with_params(
        validation_mod.DocumentedParameter(
            name="a", required=True, position=0,
            category=(validation_mod.TypeClass.MATRIX.value, validation_mod.TypeClass.VECTOR.value, validation_mod.TypeClass.SCALAR.value),
            shape="unknown", source="matrix, vector, or scalar",
        ),
    )
    call = validation_mod.GeneratedCall(symbol="f", argument_count=1, raw_arguments=("5",), line_number=1)
    checks = validation_mod.check_parameter_roles(call, signature=signature)
    check("scalar matches one of the enumerated categories", checks[0].status == validation_mod.ParameterRoleStatus.MATCH.value)


def test_61_parameter_role_empty_when_signature_has_no_parameters() -> None:
    signature = validation_mod.DocumentedSignature(
        symbol="f", arg_ranges=((1, 1),), parameter_names=(), source="fixture.rst",
        extraction_status=validation_mod.SIGNATURE_EXTRACTED, parameters=(),
    )
    call = validation_mod.GeneratedCall(symbol="f", argument_count=1, raw_arguments=("5",), line_number=1)
    check("no checks when no parameter metadata", validation_mod.check_parameter_roles(call, signature=signature) == ())
    check("no checks when signature is None", validation_mod.check_parameter_roles(call, signature=None) == ())


def test_62_parameter_role_mismatch_makes_eligibility_ineligible() -> None:
    mismatch = validation_mod.ParameterRoleCheck(
        symbol="f", position=0, parameter_name="x", documented_category=(validation_mod.TypeClass.MATRIX.value,),
        inferred_category=validation_mod.TypeClass.STRING.value, status=validation_mod.ParameterRoleStatus.MISMATCH.value,
        explanation="wrong type",
    )
    eligibility, issues = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=(), ambiguous_topics=(), call_validations=(),
        preconditions=(), code_extraction_ok=True, parameter_role_checks=(mismatch,),
    )
    check("ineligible", eligibility == validation_mod.ExecutionEligibility.INELIGIBLE.value)
    check("issue names f", any("f" in i for i in issues))


def test_63_parameter_role_unknown_does_not_block_eligibility() -> None:
    unknown = validation_mod.ParameterRoleCheck(
        symbol="f", position=0, parameter_name="x", documented_category=(validation_mod.TypeClass.MATRIX.value,),
        inferred_category=validation_mod.TypeClass.UNKNOWN.value, status=validation_mod.ParameterRoleStatus.UNKNOWN.value,
        explanation="unknown",
    )
    eligibility, _ = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=(), ambiguous_topics=(), call_validations=(),
        preconditions=(), code_extraction_ok=True, parameter_role_checks=(unknown,),
    )
    check("still eligible", eligibility == validation_mod.ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value)


# ---------------------------------------------------------------------------
# v0.75.0 Phase 9/10/11: predicted-output claim detection and verification
# ---------------------------------------------------------------------------


def test_64_no_output_claim_present() -> None:
    claim = validation_mod.analyze_predicted_output("Here is some GAUSS code that does X.", generated_code=("y = meanc(x);",))
    check("not present", claim.present is False)
    check("status not_present", claim.verification_status == validation_mod.OutputVerificationStatus.NOT_PRESENT.value)


def test_65_simple_correct_predicted_output_meanc_is_verified() -> None:
    text = "Expected output:\n4"
    claim = validation_mod.analyze_predicted_output(text, generated_code=("y = meanc({2, 4, 6});",))
    check("present", claim.present is True)
    check("verified", claim.verification_status == validation_mod.OutputVerificationStatus.VERIFIED.value)


def test_66_simple_incorrect_predicted_output_invpd_is_mismatch() -> None:
    """Reconstructs the exact v0.74.0 hard regression (evaluations/runs/
    2026-09-12-code-assistant-pre-execution-validation-run-004.md): a
    valid, literal, symmetric-positive-definite invpd({2 1, 1 2}) example
    whose model-claimed inverse (0.5 -0.5 / -0.5 0.5) is wrong -- the real
    inverse (confirmed via real tgauss.exe -b execution) is 0.66666667
    -0.33333333 / -0.33333333 0.66666667. Must never be marked VERIFIED."""
    text = "The expected output is:\n0.5 -0.5\n-0.5 0.5"
    claim = validation_mod.analyze_predicted_output(text, generated_code=("xi = invpd({2 1, 1 2});",))
    check("present", claim.present is True)
    check("mismatch, never verified", claim.verification_status == validation_mod.OutputVerificationStatus.MISMATCH.value)
    check("never silently rewritten to verified", claim.verification_status != validation_mod.OutputVerificationStatus.VERIFIED.value)


def test_67_correct_predicted_output_invpd_is_verified() -> None:
    text = "Expected output:\n0.66666667 -0.33333333\n-0.33333333 0.66666667"
    claim = validation_mod.analyze_predicted_output(text, generated_code=("xi = invpd({2 1, 1 2});",))
    check("verified", claim.verification_status == validation_mod.OutputVerificationStatus.VERIFIED.value)


def test_67b_predicted_output_in_its_own_markdown_bold_fenced_block_is_verified() -> None:
    """v0.75.0 live evaluation (category 65.x, scenario 65.10) found a real
    model puts its claimed output in its OWN separate fenced block right
    after a markdown-bold marker (`"**Expected output:**\\n```\\n4.0\\n5.0\\n
    6.0\\n```"`), not as bare text before the next fence. The original
    detector stopped at the FIRST ``` it saw -- the opening of that very
    fence -- capturing almost nothing. Must now correctly extract the
    fence's own numeric content."""
    text = (
        "Here is the code.\n\n"
        "**Expected output:**\n"
        "```\n"
        "     4.0\n"
        "     5.0\n"
        "     6.0\n"
        "```\n"
    )
    claim = validation_mod.analyze_predicted_output(text, generated_code=("y = meanc({1 2 3, 4 5 6, 7 8 9});",))
    check("present", claim.present is True)
    check("parseable", claim.parseable is True)
    check("verified against the real column means", claim.verification_status == validation_mod.OutputVerificationStatus.VERIFIED.value)


def test_67c_predicted_output_with_a_leading_text_label_line_is_still_parsed() -> None:
    """v0.75.0 live evaluation (category 65.x, scenario 65.9) found a real
    model labels its numeric block inside the same fenced output
    ("Inverted Matrix:\\n0.40000  -0.20000\\n-0.20000  0.40000") -- the
    label line has zero digits and must be skipped, not treated as making
    the whole claim unparseable. The claimed value here (0.4/-0.2/...) is
    also a real, live, WRONG model prediction (the correct inverse is
    0.6667/-0.3333/...) -- must be MISMATCH, never VERIFIED."""
    text = "The expected output is:\n```\nInverted Matrix:\n0.40000    -0.20000\n-0.20000     0.40000\n```"
    claim = validation_mod.analyze_predicted_output(text, generated_code=("xi = invpd({2 1, 1 2});",))
    check("present", claim.present is True)
    check("parseable despite the leading label line", claim.parseable is True)
    check("mismatch -- a real wrong model prediction", claim.verification_status == validation_mod.OutputVerificationStatus.MISMATCH.value)


def test_68_complex_code_with_no_recognized_pattern_is_unverified() -> None:
    text = "Expected output:\n42"
    claim = validation_mod.analyze_predicted_output(text, generated_code=("y = someUndocumentedFunction(x, z);",))
    check("unverified -- no deterministic checker applies", claim.verification_status == validation_mod.OutputVerificationStatus.UNVERIFIED.value)


def test_69_malformed_predicted_output_is_unparseable() -> None:
    text = "Expected output:\nthe matrix looks about right"
    claim = validation_mod.analyze_predicted_output(text, generated_code=("y = meanc(x);",))
    check("unparseable", claim.verification_status == validation_mod.OutputVerificationStatus.UNPARSEABLE.value)


def test_70_predicted_output_never_treated_as_execution_evidence() -> None:
    """Structural guarantee: `compute_eligibility(...)` takes no
    predicted-output argument at all, so a MISMATCH can never make
    otherwise-valid code ineligible, and a VERIFIED claim can never be
    mistaken for real execution -- eligibility and predicted-output
    verification are computed and reported entirely independently."""
    import inspect
    params = inspect.signature(validation_mod.compute_eligibility).parameters
    for name in params:
        check(f"parameter {name!r} is not an output/prediction-shaped input", "output" not in name.lower() and "predicted" not in name.lower())


# ---------------------------------------------------------------------------
# v0.75.0 Phase 13: validation coverage metadata
# ---------------------------------------------------------------------------


def test_71_coverage_not_applicable_when_no_code() -> None:
    coverage = validation_mod.compute_validation_coverage(
        has_code=False, call_validations=(), parameter_role_checks=(), preconditions=(),
        predicted_output=validation_mod.PredictedOutputClaim(present=False, raw_text=None, parseable=False, verification_status="not_present"),
    )
    check("all not_applicable", coverage.symbol_check == "not_applicable" and coverage.precondition_check == "not_applicable")


def test_72_coverage_complete_when_everything_resolved() -> None:
    predicted = validation_mod.PredictedOutputClaim(present=False, raw_text=None, parseable=False, verification_status="not_present")
    coverage = validation_mod.compute_validation_coverage(
        has_code=True, call_validations=(_compatible("meanc"),), parameter_role_checks=(), preconditions=(), predicted_output=predicted,
    )
    check("symbol complete", coverage.symbol_check == "complete")
    check("signature complete", coverage.signature_check == "complete")
    check("parameter role n/a with no role checks", coverage.parameter_role_check == "not_applicable")
    check("precondition n/a with no preconditions", coverage.precondition_check == "not_applicable")
    check("predicted output n/a with no claim", coverage.predicted_output_check == "not_applicable")


def test_73_coverage_partial_when_some_preconditions_unverified() -> None:
    precondition = validation_mod.DocumentedPrecondition(symbol="invpd", description="d", kind="property", source="s", machine_checkable=True)
    satisfied = validation_mod.PreconditionCheck(precondition, validation_mod.PreconditionStatus.SATISFIED.value, "ok")
    unverified = validation_mod.PreconditionCheck(precondition, validation_mod.PreconditionStatus.UNVERIFIED.value, "no validator")
    predicted = validation_mod.PredictedOutputClaim(present=False, raw_text=None, parseable=False, verification_status="not_present")
    coverage = validation_mod.compute_validation_coverage(
        has_code=True, call_validations=(), parameter_role_checks=(), preconditions=(satisfied, unverified), predicted_output=predicted,
    )
    check("partial", coverage.precondition_check == "partial")


# ---------------------------------------------------------------------------
# v0.76.0 Phases 2-7: deterministic GAUSS syntax validation
# ---------------------------------------------------------------------------


def test_74_valid_matrix_literal_is_validated() -> None:
    result = validation_mod.validate_syntax("x = {1 2, 3 4};\nprint x;\n")
    check("validated", result.status == validation_mod.SyntaxStatus.VALIDATED.value)
    check("no issues", result.issues == ())
    check("matrix_literal checked", "matrix_literal" in result.validated_constructs)


def test_75_semicolon_row_separator_matrix_literal_is_invalid() -> None:
    """The exact v0.75.0 live regression (evaluation 65.8b): a `chol`
    example whose generated matrix literal used `;` as a row separator."""
    result = validation_mod.validate_syntax("x = {-1 0; 0 -1};\nu = chol(x);\n")
    check("invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
    check("names the separator", any("row separator" in i.message and "`;`" in i.message for i in result.issues))
    check("rule provenance recorded", any(i.rule == "matrix_literal_row_separator" for i in result.issues))


def test_76_correctly_formatted_gauss_equivalent_of_the_semicolon_case_is_validated() -> None:
    """Phase 12: the correctly formatted equivalent of the semicolon-matrix
    regression must NOT be flagged."""
    result = validation_mod.validate_syntax("x = {-1 0, 0 -1};\nu = chol(x);\n")
    check("validated", result.status == validation_mod.SyntaxStatus.VALIDATED.value)


def test_77_ragged_numeric_matrix_rows_are_invalid() -> None:
    result = validation_mod.validate_syntax("x = {1 2 3, 4 5};\n")
    check("invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
    check("names inconsistent counts", any("inconsistent element counts" in i.message for i in result.issues))


def test_78_empty_matrix_literal_row_is_invalid() -> None:
    result = validation_mod.validate_syntax("x = {1 2, , 3 4};\n")
    check("invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
    check("names empty row", any("empty row" in i.message for i in result.issues))


def test_79_unbalanced_brace_is_invalid() -> None:
    result = validation_mod.validate_syntax("x = {1 2, 3 4;\nprint x;\n")
    check("invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
    check("names unmatched brace", any("unmatched `{`" in i.message for i in result.issues))


def test_80_unbalanced_parenthesis_from_incomplete_call_is_invalid() -> None:
    """Phase 5's exact example: `meanc(` with nothing to close it."""
    result = validation_mod.validate_syntax("y = meanc(\n")
    check("invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
    check("names unmatched paren", any("unmatched `(`" in i.message for i in result.issues))


def test_81_dangling_assignment_is_invalid() -> None:
    """Phase 13's exact example: `x = ;`, confirmed against real
    `tgauss.exe -b` execution (error G0105) in this milestone's own
    development session."""
    result = validation_mod.validate_syntax("x = ;\nprint x;\n")
    check("invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
    check("names dangling assignment", any("empty right-hand side" in i.message for i in result.issues))


def test_82_ordinary_valid_assignment_is_validated() -> None:
    result = validation_mod.validate_syntax("x = 5;\nprint x;\n")
    check("validated", result.status == validation_mod.SyntaxStatus.VALIDATED.value)
    check("assignment checked", "assignment" in result.validated_constructs)


def test_83_quoted_string_containing_a_comma_is_not_mistaken_for_an_argument_boundary() -> None:
    result = validation_mod.validate_syntax('print "hello, world";\n')
    check("validated", result.status == validation_mod.SyntaxStatus.VALIDATED.value)
    check("string_literal checked", "string_literal" in result.validated_constructs)


def test_84_unterminated_quoted_string_is_invalid() -> None:
    result = validation_mod.validate_syntax('print "hello;\n')
    check("invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
    check("names unterminated string", any("not closed" in i.message for i in result.issues))


def test_85_nested_call_is_validated() -> None:
    """Phase 14's exact example: `meanc(reshape(x, 2, 3))`."""
    result = validation_mod.validate_syntax("y = meanc(reshape(x, 2, 3));\n")
    check("validated", result.status == validation_mod.SyntaxStatus.VALIDATED.value)


def test_86_multiple_code_blocks_merge_conservatively() -> None:
    block_a = validation_mod.validate_syntax("x = {1 2, 3 4};\n")
    block_b = validation_mod.validate_syntax("y = {-1 0; 0 -1};\n")
    merged = validation_mod.merge_syntax_results((block_a, block_b))
    check("invalid overall", merged.status == validation_mod.SyntaxStatus.INVALID.value)
    check("carries both blocks' evidence", "matrix_literal" in merged.validated_constructs)
    check("names the second block's violation", any("row separator" in i.message for i in merged.issues))


def test_86b_merge_of_no_blocks_is_none() -> None:
    check("none", validation_mod.merge_syntax_results(()) is None)


# v0.77.0: test_86c/test_86d previously asserted a stray/trailing comma
# between call arguments is INVALID, on a purely structural assumption with
# no real-runtime evidence. This milestone's own differential baseline
# corpus run (2026-09-18) directly contradicted that assumption via real
# `tgauss.exe -b` execution -- see `call_argument_missing_separator`'s
# registry entry and the removed `call_argument_separator` rule's own
# comment in gauss_pre_execution_validation.py for the full evidence trail.
# The old behavior is superseded, not merely relaxed: GAUSS genuinely,
# correctly tolerates a doubled/trailing comma (confirmed by a real printed
# result identical to the single-comma form), so the validator must not
# flag it at all.
def test_86c_stray_comma_in_call_arguments_is_not_flagged_invalid() -> None:
    result = validation_mod.validate_syntax("y = meanc(x,,y);\n")
    check("not invalid -- real GAUSS accepts and correctly collapses the doubled comma", result.status != validation_mod.SyntaxStatus.INVALID.value)


def test_86d_trailing_comma_in_call_arguments_is_not_flagged_invalid() -> None:
    result = validation_mod.validate_syntax("y = meanc(x,);\n")
    check("not invalid -- real GAUSS accepts a trailing comma", result.status != validation_mod.SyntaxStatus.INVALID.value)


def test_86e_control_flow_block_is_partial_not_invalid() -> None:
    code = "i = 1;\ndo while i <= 3;\n  print i;\n  i = i + 1;\nendo;\n"
    result = validation_mod.validate_syntax(code)
    check("partial, not invalid", result.status == validation_mod.SyntaxStatus.PARTIAL.value)
    check("unknown construct named", "control_flow_block" in result.unknown_constructs)


def test_86f_empty_code_is_unknown() -> None:
    result = validation_mod.validate_syntax("")
    check("unknown", result.status == validation_mod.SyntaxStatus.UNKNOWN.value)
    check("nothing validated", result.validated_constructs == ())


def test_86g_ordinary_print_statement_is_not_treated_as_an_unknown_construct() -> None:
    """Regression guard: `print`/`local`/`retp` are simple statements, not
    block constructs -- they must never spuriously downgrade otherwise fully
    checkable code from VALIDATED to PARTIAL (see `_BLOCK_CONSTRUCT_
    KEYWORDS`'s own docstring)."""
    result = validation_mod.validate_syntax("x = {2 1, 1 2};\nu = chol(x);\nprint u;\n")
    check("validated, not partial", result.status == validation_mod.SyntaxStatus.VALIDATED.value)
    check("no unknown constructs", result.unknown_constructs == ())


def test_86h_matrix_literal_with_character_elements_is_not_falsely_flagged_invalid() -> None:
    """A documented, valid literal this checker cannot deeply validate
    (character elements, not numeric) must never be guessed at as INVALID --
    only the two structural rules (row separator, empty row) that apply
    regardless of element type are checked."""
    result = validation_mod.validate_syntax("x = { dog cat };\n")
    check("not invalid", result.status != validation_mod.SyntaxStatus.INVALID.value)


def test_86i_rule_registry_has_provenance_for_every_rule_a_check_can_produce() -> None:
    produced_rules = {
        "matrix_literal_row_separator", "matrix_literal_row_shape", "balanced_delimiters",
        "dangling_assignment", "call_argument_missing_separator", "unterminated_string",
    }
    for rule_name in produced_rules:
        rule = validation_mod._SYNTAX_RULE_REGISTRY.get(rule_name)
        check(f"{rule_name} has a registry entry", rule is not None)
        if rule is not None:
            check(f"{rule_name} has a non-empty source", bool(rule.source))


# ---------------------------------------------------------------------------
# v0.76.0 Phase 6: call-expression parsing hardening
# ---------------------------------------------------------------------------


def test_86j_bare_multi_token_literal_without_let_or_braces_is_invalid() -> None:
    """v0.76.0 live finding: a real CLI smoke test of the `66.4` prompt
    against the real Ollama model produced `x = -1 0;` -- a bare, brace-less,
    non-`let` multi-token literal, which real `tgauss.exe -b` execution
    confirms is invalid GAUSS (`error G0063: Operator expected before '0'`).
    Regression guard."""
    result = validation_mod.validate_syntax("x = -1 0;\nu = chol(x);\n")
    check("invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
    check("names the rule", any(i.rule == "bare_multi_token_literal_requires_let_or_braces" for i in result.issues))


def test_86k_let_prefixed_multi_token_literal_is_validated() -> None:
    """The same literal, `let`-prefixed, is real, documented, valid GAUSS
    (`let.rst`) and must not be flagged."""
    result = validation_mod.validate_syntax("let x = -1 0;\nprint x;\n")
    check("validated", result.status == validation_mod.SyntaxStatus.VALIDATED.value)


def test_86l_braced_multi_token_literal_is_unaffected_by_the_new_rule() -> None:
    result = validation_mod.validate_syntax("x = {-1 0, 0 -1};\nprint x;\n")
    check("validated", result.status == validation_mod.SyntaxStatus.VALIDATED.value)


def test_86m_ordinary_expressions_and_calls_are_not_falsely_flagged() -> None:
    for code in ("x = a + b;\nprint x;\n", "y = meanc(x);\nprint y;\n", "y = reshape(x, 2, 3);\nprint y;\n", "x = 5;\nprint x;\n"):
        r = validation_mod.validate_syntax(code)
        check(f"{code!r} is not flagged bare_multi_token_literal", not any(
            i.rule == "bare_multi_token_literal_requires_let_or_braces" for i in r.issues
        ))


def test_87_nested_call_extraction_preserves_both_symbols_and_argument_boundaries() -> None:
    calls = validation_mod.extract_generated_calls("y = meanc(reshape(x, 2, 3));\n")
    symbols = {c.symbol for c in calls}
    check("both calls extracted", symbols == {"meanc", "reshape"})
    outer = next(c for c in calls if c.symbol == "meanc")
    inner = next(c for c in calls if c.symbol == "reshape")
    check("outer call has exactly one top-level argument", outer.argument_count == 1)
    check("outer argument boundary preserves the nested call whole", outer.raw_arguments == ("reshape(x, 2, 3)",))
    check("inner call has three arguments", inner.argument_count == 3)


def test_88_matrix_literal_as_a_call_argument_is_a_single_argument() -> None:
    calls = validation_mod.extract_generated_calls("u = chol({2 1, 1 2});\n")
    check("one call", len(calls) == 1)
    check("one argument, the whole literal", calls[0].raw_arguments == ("{2 1, 1 2}",))


def test_89_string_argument_containing_a_comma_is_a_single_argument() -> None:
    calls = validation_mod.extract_generated_calls('sprintf("%s, %s", a, b);\n')
    call = calls[0]
    check("three top-level arguments, not four", call.argument_count == 3)
    check("the string argument is kept whole", call.raw_arguments[0] == '"%s, %s"')


def test_90_multiple_nesting_levels_are_each_extracted() -> None:
    calls = validation_mod.extract_generated_calls("y = meanc(sumc(reshape(x, 2, 3)));\n")
    symbols = {c.symbol for c in calls}
    check("all three calls extracted", symbols == {"meanc", "sumc", "reshape"})


def test_91_malformed_unterminated_call_fails_closed_never_guessed() -> None:
    calls = validation_mod.extract_generated_calls("y = meanc(\n")
    check("no call fabricated for an unterminated call", calls == ())


# ---------------------------------------------------------------------------
# v0.76.0 Phase 8: coverage/evidence-profile hardening
# ---------------------------------------------------------------------------


def _no_predicted_output() -> "validation_mod.PredictedOutputClaim":
    return validation_mod.PredictedOutputClaim(present=False, raw_text=None, parseable=False, verification_status="not_present")


def test_92_broad_evidence_profile_when_everything_resolved() -> None:
    validated_syntax = validation_mod.validate_syntax("x = {1 2, 3 4};\nu = chol(x);\n")
    coverage = validation_mod.compute_validation_coverage(
        has_code=True, call_validations=(_compatible("chol"),), parameter_role_checks=(), preconditions=(),
        predicted_output=_no_predicted_output(), syntax=validated_syntax,
    )
    check("syntax complete", coverage.syntax_check == "complete")
    check("broad", validation_mod.compute_evidence_profile(coverage) == validation_mod.EvidenceProfile.BROAD.value)


def test_93_partial_evidence_profile_when_signature_unknown() -> None:
    unknown_sig = validation_mod.CallValidationResult(
        symbol="chol", documented=True, signature_known=False,
        argument_count_status=validation_mod.SignatureCompatibility.UNKNOWN.value,
        issues=("signature could not be extracted",), source=None,
    )
    validated_syntax = validation_mod.validate_syntax("x = {1 2, 3 4};\nu = chol(x);\n")
    coverage = validation_mod.compute_validation_coverage(
        has_code=True, call_validations=(unknown_sig,), parameter_role_checks=(), preconditions=(),
        predicted_output=_no_predicted_output(), syntax=validated_syntax,
    )
    check("signature unknown", coverage.signature_check == "unknown")
    check("partial", validation_mod.compute_evidence_profile(coverage) == validation_mod.EvidenceProfile.PARTIAL.value)


def test_94_minimal_evidence_profile_when_syntax_unknown() -> None:
    unknown_syntax = validation_mod.validate_syntax("")
    coverage = validation_mod.compute_validation_coverage(
        has_code=True, call_validations=(), parameter_role_checks=(), preconditions=(),
        predicted_output=_no_predicted_output(), syntax=unknown_syntax,
    )
    check("syntax unknown", coverage.syntax_check == "unknown")
    check("minimal", validation_mod.compute_evidence_profile(coverage) == validation_mod.EvidenceProfile.MINIMAL.value)


def test_95_unverified_precondition_keeps_evidence_profile_below_broad() -> None:
    precondition = validation_mod.DocumentedPrecondition(
        symbol="invpd", description="d", kind="property", source="s", machine_checkable=True,
    )
    unverified = validation_mod.PreconditionCheck(precondition, validation_mod.PreconditionStatus.UNVERIFIED.value, "runtime value")
    validated_syntax = validation_mod.validate_syntax("y = invpd(x);\n")
    coverage = validation_mod.compute_validation_coverage(
        has_code=True, call_validations=(_compatible("invpd"),), parameter_role_checks=(), preconditions=(unverified,),
        predicted_output=_no_predicted_output(), syntax=validated_syntax,
    )
    check("precondition unknown-coverage", coverage.precondition_check == "unknown")
    check("not broad", validation_mod.compute_evidence_profile(coverage) != validation_mod.EvidenceProfile.BROAD.value)


def test_96_predicted_output_never_affects_evidence_profile() -> None:
    """Phase 17: predicted-output verification is orthogonal -- a MISMATCH
    must never change the evidence-profile category."""
    validated_syntax = validation_mod.validate_syntax("x = {1 2, 3 4};\nu = chol(x);\n")
    mismatch = validation_mod.PredictedOutputClaim(
        present=True, raw_text="9 9", parseable=True, verification_status="mismatch",
        expected_value=((9.0, 9.0),), computed_value=((1.0, 1.0),), issues=("wrong",),
    )
    coverage_with_mismatch = validation_mod.compute_validation_coverage(
        has_code=True, call_validations=(_compatible("chol"),), parameter_role_checks=(), preconditions=(),
        predicted_output=mismatch, syntax=validated_syntax,
    )
    coverage_without_claim = validation_mod.compute_validation_coverage(
        has_code=True, call_validations=(_compatible("chol"),), parameter_role_checks=(), preconditions=(),
        predicted_output=_no_predicted_output(), syntax=validated_syntax,
    )
    check(
        "evidence profile identical regardless of predicted-output verdict",
        validation_mod.compute_evidence_profile(coverage_with_mismatch)
        == validation_mod.compute_evidence_profile(coverage_without_claim),
    )


# ---------------------------------------------------------------------------
# v0.76.0 Phases 9-11, 16: execution-handoff readiness
# ---------------------------------------------------------------------------


def test_97_fully_supported_code_is_a_handoff_candidate() -> None:
    validated_syntax = validation_mod.validate_syntax("x = {1 2, 3 4};\nu = chol(x);\n")
    coverage = validation_mod.compute_validation_coverage(
        has_code=True, call_validations=(_compatible("chol"),), parameter_role_checks=(), preconditions=(),
        predicted_output=_no_predicted_output(), syntax=validated_syntax,
    )
    profile = validation_mod.compute_evidence_profile(coverage)
    readiness = validation_mod.compute_handoff_readiness(
        eligibility=validation_mod.ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value, unresolved_issues=(),
        syntax=validated_syntax, call_validations=(_compatible("chol"),), preconditions=(), evidence_profile=profile,
    )
    check("handoff candidate", readiness.state == validation_mod.HandoffReadiness.HANDOFF_CANDIDATE.value)
    check("has positive reasons", len(readiness.reasons) > 0)


def test_98_ineligible_from_unknown_symbol_is_not_ready() -> None:
    readiness = validation_mod.compute_handoff_readiness(
        eligibility=validation_mod.ExecutionEligibility.INELIGIBLE.value,
        unresolved_issues=("unresolved/unsupported call symbol(s): colmean",),
        syntax=None, call_validations=(), preconditions=(), evidence_profile=validation_mod.EvidenceProfile.MINIMAL.value,
    )
    check("not ready", readiness.state == validation_mod.HandoffReadiness.NOT_READY.value)
    check("names the symbol", any("colmean" in r for r in readiness.reasons))


def test_99_incompatible_signature_is_not_ready() -> None:
    eligibility, issues = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=(), ambiguous_topics=(),
        call_validations=(_incompatible("meanc"),), preconditions=(), code_extraction_ok=True,
    )
    readiness = validation_mod.compute_handoff_readiness(
        eligibility=eligibility, unresolved_issues=issues, syntax=validation_mod.validate_syntax("y = meanc(1, 2);\n"),
        call_validations=(_incompatible("meanc"),), preconditions=(), evidence_profile=validation_mod.EvidenceProfile.BROAD.value,
    )
    check("not ready", readiness.state == validation_mod.HandoffReadiness.NOT_READY.value)


def test_100_parameter_role_mismatch_is_not_ready() -> None:
    mismatch = validation_mod.ParameterRoleCheck(
        symbol="meanc", position=0, parameter_name="x", documented_category=("matrix",),
        inferred_category="string", status=validation_mod.ParameterRoleStatus.MISMATCH.value, explanation="wrong type",
    )
    eligibility, issues = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=(), ambiguous_topics=(),
        call_validations=(_compatible("meanc"),), preconditions=(), code_extraction_ok=True,
        parameter_role_checks=(mismatch,),
    )
    readiness = validation_mod.compute_handoff_readiness(
        eligibility=eligibility, unresolved_issues=issues, syntax=validation_mod.validate_syntax('y = meanc("x");\n'),
        call_validations=(_compatible("meanc"),), preconditions=(), evidence_profile=validation_mod.EvidenceProfile.BROAD.value,
    )
    check("not ready", readiness.state == validation_mod.HandoffReadiness.NOT_READY.value)


def test_101_known_precondition_violation_is_not_ready() -> None:
    call = validation_mod.GeneratedCall(symbol="invpd", argument_count=1, raw_arguments=("{1 2, 3 4}",), line_number=1)
    check_result = validation_mod.check_invpd_precondition(call, code="x = {1 2, 3 4};\ny = invpd(x);\n")
    check("sanity: precondition actually violated", check_result.status == validation_mod.PreconditionStatus.VIOLATED.value)
    eligibility, issues = validation_mod.compute_eligibility(
        generation_policy="full", unknown_symbols=(), ambiguous_topics=(),
        call_validations=(_compatible("invpd"),), preconditions=(check_result,), code_extraction_ok=True,
    )
    readiness = validation_mod.compute_handoff_readiness(
        eligibility=eligibility, unresolved_issues=issues, syntax=validation_mod.validate_syntax("y = invpd(x);\n"),
        call_validations=(_compatible("invpd"),), preconditions=(check_result,),
        evidence_profile=validation_mod.EvidenceProfile.BROAD.value,
    )
    check("not ready", readiness.state == validation_mod.HandoffReadiness.NOT_READY.value)


def test_102_invalid_syntax_is_not_ready_even_when_otherwise_eligible() -> None:
    """The exact Phase 12 requirement: invalid syntax must never become a
    handoff candidate, regardless of what the eligibility verdict says."""
    invalid_syntax = validation_mod.validate_syntax("x = {-1 0; 0 -1};\nu = chol(x);\n")
    readiness = validation_mod.compute_handoff_readiness(
        eligibility=validation_mod.ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value, unresolved_issues=(),
        syntax=invalid_syntax, call_validations=(_compatible("chol"),), preconditions=(),
        evidence_profile=validation_mod.EvidenceProfile.BROAD.value,
    )
    check("not ready", readiness.state == validation_mod.HandoffReadiness.NOT_READY.value)
    check("reasons cite the syntax problem", any("row separator" in r for r in readiness.reasons))


def test_103_unresolved_ambiguity_is_not_ready() -> None:
    readiness = validation_mod.compute_handoff_readiness(
        eligibility=validation_mod.ExecutionEligibility.REQUIRES_CLARIFICATION.value,
        unresolved_issues=("ambiguous topic(s) remain unresolved: inv",),
        syntax=None, call_validations=(), preconditions=(), evidence_profile=validation_mod.EvidenceProfile.MINIMAL.value,
    )
    check("not ready", readiness.state == validation_mod.HandoffReadiness.NOT_READY.value)


def test_104_runtime_dependent_unverified_precondition_is_review_required() -> None:
    """This milestone's documented policy (planning doc Section 3.5): an
    UNVERIFIED runtime-dependent precondition is a real, disclosed gap, not
    a known violation -- it forces REVIEW_REQUIRED, never silently
    HANDOFF_CANDIDATE and never punitively NOT_READY."""
    precondition = validation_mod.DocumentedPrecondition(
        symbol="invpd", description="d", kind="property", source="s", machine_checkable=True,
    )
    unverified = validation_mod.PreconditionCheck(precondition, validation_mod.PreconditionStatus.UNVERIFIED.value, "runtime value, not literal")
    validated_syntax = validation_mod.validate_syntax("y = invpd(x);\n")
    readiness = validation_mod.compute_handoff_readiness(
        eligibility=validation_mod.ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value, unresolved_issues=(),
        syntax=validated_syntax, call_validations=(_compatible("invpd"),), preconditions=(unverified,),
        evidence_profile=validation_mod.EvidenceProfile.PARTIAL.value,
    )
    check("review required, not handoff candidate", readiness.state == validation_mod.HandoffReadiness.REVIEW_REQUIRED.value)
    check("not ready is never used for a mere evidence gap", readiness.state != validation_mod.HandoffReadiness.NOT_READY.value)
    check("names the unverified precondition", any("unverified" in r for r in readiness.reasons))


def test_105_unknown_signature_forces_review_required_not_handoff_candidate() -> None:
    unknown_sig = validation_mod.CallValidationResult(
        symbol="tscsFit", documented=True, signature_known=False,
        argument_count_status=validation_mod.SignatureCompatibility.UNKNOWN.value,
        issues=("a documented call signature could not be reliably extracted for this symbol",), source=None,
    )
    validated_syntax = validation_mod.validate_syntax("m = tscsFit(y, x, grp);\n")
    readiness = validation_mod.compute_handoff_readiness(
        eligibility=validation_mod.ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value, unresolved_issues=(),
        syntax=validated_syntax, call_validations=(unknown_sig,), preconditions=(),
        evidence_profile=validation_mod.EvidenceProfile.PARTIAL.value,
    )
    check("review required", readiness.state == validation_mod.HandoffReadiness.REVIEW_REQUIRED.value)


def test_106_model_cannot_set_readiness() -> None:
    """Structural proof: `compute_handoff_readiness` takes no provider/model
    argument of any kind -- it cannot even accidentally consult one."""
    import inspect

    sig = inspect.signature(validation_mod.compute_handoff_readiness)
    for param_name in sig.parameters:
        check(f"{param_name!r} is not a provider/model parameter", "provider" not in param_name.lower() and "model" not in param_name.lower())


# ---------------------------------------------------------------------------
# v0.76.0 Phase 19: safety -- no execution capability of any kind
# ---------------------------------------------------------------------------


def test_106b_identifier_starting_with_a_block_keyword_is_not_a_false_positive() -> None:
    """v0.76.0 live evaluation (category 66.x, scenario 66.9) found a real
    defect: a real model-generated identifier, `formula`, was spuriously
    treated as starting with the block keyword `for` (a bare string-prefix
    match, not a real word boundary), downgrading otherwise fully-checkable
    code from VALIDATED to PARTIAL. Fixed by requiring a real word boundary
    (`_starts_with_keyword`). Regression guard."""
    result = validation_mod.validate_syntax('formula = "y ~ X1 + X2 + X3";\nprint formula;\n')
    check("validated, not spuriously partial", result.status == validation_mod.SyntaxStatus.VALIDATED.value)
    check("no false unknown construct", result.unknown_constructs == ())

    # A handful of other real identifiers that share a keyword's own prefix.
    for code in ("dogcount = 5;\nprint dogcount;\n", "ifx = 1;\nprint ifx;\n", "doubled = x + x;\nprint doubled;\n"):
        r = validation_mod.validate_syntax(code)
        check(f"{code!r} is not falsely flagged", r.unknown_constructs == ())


def test_107_syntax_and_readiness_functions_have_no_execution_shell_or_file_write_capability() -> None:
    import inspect

    forbidden = ("subprocess", "os.system", "open(", "write_text", "write_bytes", "eval(", "exec(", "shell=")
    for fn in (
        validation_mod.validate_syntax, validation_mod.merge_syntax_results, validation_mod.compute_evidence_profile,
        validation_mod.compute_handoff_readiness,
    ):
        source = inspect.getsource(fn)
        for token in forbidden:
            check(f"{fn.__name__} source does not contain {token!r}", token not in source)


# ---------------------------------------------------------------------------
# v0.77.0: call_argument_missing_separator -- closes a real, five-item false-
# negative cluster found by the differential baseline corpus run
# (2026-09-18). See that rule's own _SYNTAX_RULE_REGISTRY entry for the
# real tgauss.exe -b provenance.
# ---------------------------------------------------------------------------


def test_108_missing_separator_in_single_arg_call_is_invalid() -> None:
    """Real regression B-057/B-059/B-063 shape: two bare numeric tokens with
    only whitespace between them, inside a call's sole argument."""
    for snippet in ("x = reshape(5 3);\n", "x = ones(3 2);\n", "y = meanc(rndu(1e5 4));\n"):
        result = validation_mod.validate_syntax(snippet)
        check(f"{snippet!r} invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
        check(f"{snippet!r} names call_argument_missing_separator", any(i.rule == "call_argument_missing_separator" for i in result.issues))


def test_109_missing_separator_between_identifiers_is_invalid() -> None:
    """Real regression B-058 shape: two bare identifiers, no comma."""
    result = validation_mod.validate_syntax("A = rndn(n n);\n")
    check("invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
    check("names rule", any(i.rule == "call_argument_missing_separator" for i in result.issues))


def test_110_missing_separator_after_masked_string_is_invalid() -> None:
    """Real regression B-061 shape: a quoted-string argument immediately
    followed by a bare identifier with no comma -- must fire even though the
    preceding token is a string, not a bare number/identifier."""
    result = validation_mod.validate_syntax('s1 = sprintf("Pi is equal to %.4f" pi);\n')
    check("invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
    check("names rule", any(i.rule == "call_argument_missing_separator" for i in result.issues))


def test_111_matrix_literal_argument_is_not_falsely_flagged_missing_separator() -> None:
    """A literal matrix passed directly as a call argument (whitespace-
    separated elements within a row) must never be mistaken for a missing
    call-argument separator."""
    result = validation_mod.validate_syntax("y = invpd({2 1, 1 2});\n")
    check("not invalid", result.status != validation_mod.SyntaxStatus.INVALID.value)


def test_112_indexing_argument_is_not_falsely_flagged_missing_separator() -> None:
    result = validation_mod.validate_syntax("y = meanc(x[1, 2]);\n")
    check("not invalid", result.status != validation_mod.SyntaxStatus.INVALID.value)


def test_113_real_expression_argument_with_operator_is_not_flagged() -> None:
    """An operator between two tokens (already valid GAUSS) must never be
    mistaken for a missing separator -- only a BARE whitespace gap with no
    operator/comma at all is a violation."""
    result = validation_mod.validate_syntax("y = meanc(x + z);\n")
    check("not invalid", result.status != validation_mod.SyntaxStatus.INVALID.value)


def test_114_nested_call_argument_is_not_falsely_flagged() -> None:
    result = validation_mod.validate_syntax("z = meanc(reshape(x, 2, 2));\n")
    check("not invalid", result.status != validation_mod.SyntaxStatus.INVALID.value)


def test_115_missing_separator_inside_print_call_is_invalid() -> None:
    """Real regression D-007 (found by v0.77.0's own fresh live-Ollama stress
    batch, Phase 15): a real model wrote `print("..." std_dev);` -- the same
    missing-separator shape as test_110, but inside a parenthesized `print(
    ...)` call. Real `tgauss.exe -b` confirms `error G0063`. Before the fix,
    `print` was skipped entirely (it is a member of the wider
    `_LANGUAGE_CONSTRUCT_KEYWORDS` this check used to reference), so this was
    a genuine, confirmed false negative."""
    result = validation_mod.validate_syntax('print("Standard Deviation of x: " std_dev);\n')
    check("invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
    check("names rule", any(i.rule == "call_argument_missing_separator" for i in result.issues))


def test_116_bare_print_statement_without_parens_is_unaffected() -> None:
    """GAUSS's own documented bare `print x, y;` form (no parens at all) must
    never be mistaken for a call with a missing separator -- there is no
    `print(` call-shape for `_CALL_SHAPED_RE` to even match here."""
    result = validation_mod.validate_syntax("print x, y;\n")
    check("not invalid", result.status != validation_mod.SyntaxStatus.INVALID.value)


def test_117_well_formed_print_call_with_parens_is_not_flagged() -> None:
    result = validation_mod.validate_syntax('print("Standard Deviation of x: ", std_dev);\n')
    check("not invalid", result.status != validation_mod.SyntaxStatus.INVALID.value)


# ---------------------------------------------------------------------------
# v0.80.0: shared call_scan_text(...) -- keyword-led lines are scanned, not
# skipped (the bare-`print` gap reproduced live in evaluation 69.1), with
# real word boundaries (the `printfm`/`format`/`forecast` prefix gap).
# ---------------------------------------------------------------------------


def _symbols(code: str) -> list[tuple[str, int]]:
    return [(c.symbol, c.argument_count) for c in validation_mod.extract_generated_calls(code)]


def test_118_keyword_prefixed_identifiers_are_no_longer_skipped() -> None:
    check("printfm extracted", _symbols("printfm(x, 1, mask);") == [("printfm", 3)])
    check("format = line scanned", _symbols('format = sprintf("%d", 1);') == [("sprintf", 2)])
    check("forecast = line scanned", _symbols("forecast = arima(y, 1);") == [("arima", 2)])
    check("dotfeq (starts with 'do') extracted", _symbols("dotfeq(a, b);") == [("dotfeq", 2)])
    check("iff = line (starts with 'if') scanned", _symbols("iff = invpd(x);") == [("invpd", 1)])
    check("localx = line (starts with 'local') scanned", _symbols("localx = f(y);") == [("f", 1)])


def test_119_calls_on_keyword_led_lines_are_extracted() -> None:
    check("print f(...) extracted", _symbols("print invpd({2 1, 1 2});") == [("invpd", 1)])
    check("uppercase PRINT", _symbols("PRINT meanc(x);") == [("meanc", 1)])
    check("retp(f(x)) yields f only", _symbols("retp(f(x));") == [("f", 1)])
    check("if f(x) > 0 yields f", _symbols("if f(x) > 0;") == [("f", 1)])
    check("do while header call extracted", _symbols("do while i <= rows(x);") == [("rows", 1)])
    check("struct initializer call extracted", _symbols("struct DS d = dsCreate();") == [("dsCreate", 0)])
    check("keyword-as-call still filtered", _symbols("print(y);") == [] and _symbols("retp(a+b);") == [])


def test_120_declarations_loop_headers_and_strings_never_yield_calls() -> None:
    check("for-header loop variable is not a call", _symbols("for i (1, 3, 1);") == [])
    check("for-header still exposes real calls", _symbols("for i (1, rows(x), 1);") == [("rows", 1)])
    check("proc header skipped", _symbols("proc (1) = myf(x);") == [])
    check("local declaration skipped", _symbols("local a, b;") == [])
    check("parens inside a string are not calls", _symbols('print "Inverse (2x2):";') == [])
    calls = validation_mod.extract_generated_calls('s = sprintf("%d, %d", a, b);')
    check("string argument text and quotes preserved", calls[0].raw_arguments == ('"%d, %d"', "a", "b"))


def test_121_print_wrapped_precondition_violation_is_now_caught() -> None:
    """The exact 69.1 shape: a `print`-wrapped call was never extracted, so
    its documented precondition was never checked."""
    code = "print invpd({2 1, 3 2});"
    calls = validation_mod.extract_generated_calls(code)
    checks = [pc for call in calls for pc in validation_mod.check_preconditions(call, code=code)]
    check("invpd precondition evaluated", len(checks) > 0)
    check("non-symmetric literal is VIOLATED", any(pc.status == validation_mod.PreconditionStatus.VIOLATED.value for pc in checks))


# ---------------------------------------------------------------------------
# v0.80.0: system-touching statement gate
# ---------------------------------------------------------------------------


def _system_names(code: str) -> list[tuple[str, str]]:
    return [(f.name, f.category) for f in validation_mod.check_system_statements(code)]


def test_122_system_statements_detected_in_every_category() -> None:
    cases = {
        'y = 1; dos "dir";': ("dos", "os_command"),
        "shell ^cmd;": ("shell", "os_command"),
        'r = EXEC("x.exe", "");': ("exec", "process_launch"),
        "system;": ("system", "process_control"),
        "run myprog.gss;": ("run", "source_inclusion"),
        '#include "helpers.src"': ("#include", "source_inclusion"),
        'changeDir("C:/");': ("changedir", "directory_change"),
        'ret = deleteFile("a.txt");': ("deletefile", "file_delete"),
        "output file=out.txt on;": ("output", "file_write"),
        'ret = saveStruct(s, "f");': ("savestruct", "file_write"),
        'x = loadd("auto2.dta");': ("loadd", "file_read"),
        "load x = mydata;": ("load", "file_read"),
        "open fh = mydata;": ("open", "file_read"),
    }
    for code, expected in cases.items():
        check(f"{code!r} -> {expected}", _system_names(code) == [expected])


def test_123_system_statement_gate_ignores_strings_and_same_named_variables() -> None:
    for code in ('print "dos is fine";', "run = 5;", "output = x * 2;", "saveresults = meanc(x);",
                 'print "Use loadd(file) to read data";', "loaded = 1;", "x = rndn(3, 3); print x;"):
        check(f"{code!r} has no findings", _system_names(code) == [])


def test_124_system_statement_forces_not_ready_ahead_of_everything_else() -> None:
    finding = validation_mod.check_system_statements('dos "dir";')
    readiness = validation_mod.compute_handoff_readiness(
        eligibility=validation_mod.ExecutionEligibility.ELIGIBLE_FOR_VALIDATION.value, unresolved_issues=(),
        syntax=None, call_validations=(), preconditions=(),
        evidence_profile=validation_mod.EvidenceProfile.BROAD.value, system_statements=finding,
    )
    check("NOT_READY", readiness.state == validation_mod.HandoffReadiness.NOT_READY.value)
    check("reason names the statement", any("`dos`" in r for r in readiness.reasons))


def test_125_every_registry_entry_has_doc_provenance_and_unique_name() -> None:
    names = [rule.name for rule in validation_mod._SYSTEM_STATEMENT_REGISTRY]
    check("names unique", len(names) == len(set(names)))
    check("every rule cites a doc page", all(rule.doc_page.endswith(".rst") for rule in validation_mod._SYSTEM_STATEMENT_REGISTRY))
    valid = {c.value for c in validation_mod.SystemStatementCategory}
    check("every category valid", all(rule.category in valid for rule in validation_mod._SYSTEM_STATEMENT_REGISTRY))


# ---------------------------------------------------------------------------
# v0.81.0: GAUSS category compatibility, exponent literals, and same-snippet
# variable tracing (`_governing_assignment` / `resolve_argument_category`)
# ---------------------------------------------------------------------------


def _matrix_param_signature() -> validation_mod.DocumentedSignature:
    return _signature_with_params(validation_mod.DocumentedParameter(
        name="x", required=True, position=0, category=(validation_mod.TypeClass.MATRIX.value,), shape="unknown",
        source="NxK matrix",
    ))


def _scalar_param_signature() -> validation_mod.DocumentedSignature:
    return _signature_with_params(validation_mod.DocumentedParameter(
        name="r", required=True, position=0, category=(validation_mod.TypeClass.SCALAR.value,), shape="unknown",
        source="scalar",
    ))


def _role_status(signature, argument: str, *, code: str | None = None, line: int = 1, signatures=None) -> str:
    call = validation_mod.GeneratedCall(symbol="f", argument_count=1, raw_arguments=(argument,), line_number=line)
    return validation_mod.check_parameter_roles(call, signature=signature, code=code, signatures=signatures)[0].status


def test_126_vector_and_scalar_literals_are_accepted_where_matrix_is_documented() -> None:
    match = validation_mod.ParameterRoleStatus.MATCH.value
    mismatch = validation_mod.ParameterRoleStatus.MISMATCH.value
    check("column vector -> matrix", _role_status(_matrix_param_signature(), "{1,2,3}") == match)
    check("row vector -> matrix", _role_status(_matrix_param_signature(), "{1 2 3}") == match)
    check("scalar -> matrix", _role_status(_matrix_param_signature(), "5") == match)
    check("string -> matrix still mismatch", _role_status(_matrix_param_signature(), '"abc"') == mismatch)
    check("vector -> scalar still mismatch", _role_status(_scalar_param_signature(), "{1 2}") == mismatch)
    check("matrix -> scalar still mismatch", _role_status(_scalar_param_signature(), "{1 2, 3 4}") == mismatch)


def test_127_exponent_and_leading_dot_numerals_are_scalars() -> None:
    for literal in ("1e5", "1.5E-3", ".5", "-2e+3", "3."):
        check(f"{literal} scalar", validation_mod.infer_literal_category(literal)[0] == validation_mod.TypeClass.SCALAR.value)
    for not_literal in ("e5", "1e", "1.2.3", "x1"):
        check(f"{not_literal} not scalar", validation_mod.infer_literal_category(not_literal)[0] == validation_mod.TypeClass.UNKNOWN.value)


def test_128_variable_traced_to_literal_or_scalar_assignment() -> None:
    match = validation_mod.ParameterRoleStatus.MATCH.value
    check("matrix literal", _role_status(_matrix_param_signature(), "x", code="x = {1 2, 3 4};\ny = f(x);", line=2) == match)
    check("scalar", _role_status(_scalar_param_signature(), "n", code="n = 5;\ny = f(n);", line=2) == match)
    check("transposed", _role_status(_matrix_param_signature(), "x'", code="x = {1 2 3};\ny = f(x');", line=2) == match)
    check("case-insensitive name", _role_status(_matrix_param_signature(), "X", code="x = {1 2};\ny = f(X);", line=2) == match)
    check("let form", _role_status(_matrix_param_signature(), "x", code="let x = {1 2};\ny = f(x);", line=2) == match)
    check("traced literal can still mismatch", _role_status(
        _scalar_param_signature(), "v", code="v = {1 2};\ny = f(v);", line=2,
    ) == validation_mod.ParameterRoleStatus.MISMATCH.value)


def test_129_same_line_assignment_ordering_uses_call_column() -> None:
    code = "x = {1,2,3}; m = meanc(x);"
    call = validation_mod.extract_generated_calls(code)[0]
    check("column recorded", call.column == code.index("meanc"))
    check("prior same-line assignment governs", validation_mod._governing_assignment(
        "x", code=code, line_number=1, column=call.column,
    ) == "{1,2,3}")
    later = "m = meanc(x); x = {1,2,3};"
    later_call = validation_mod.extract_generated_calls(later)[0]
    check("later same-line assignment does not", validation_mod._governing_assignment(
        "x", code=later, line_number=1, column=later_call.column,
    ) is None)
    inside = "x = {1,2}; x = sumc(x);"
    inside_call = validation_mod.extract_generated_calls(inside)[0]
    check("the call's own statement never governs its argument", validation_mod._governing_assignment(
        "x", code=inside, line_number=1, column=inside_call.column,
    ) == "{1,2}")


def test_130_variable_traced_to_documented_return_type() -> None:
    rndu = validation_mod.DocumentedSignature(
        symbol="rndu", arg_ranges=((2, 2),), parameter_names=("r", "c"), source="rndu.rst",
        extraction_status=validation_mod.SIGNATURE_EXTRACTED, return_categories=(validation_mod.TypeClass.MATRIX.value,),
    )
    signatures = {"rndu": rndu}
    code = "x = rndu(100, 4);\ny = f(x);"
    check("matrix return -> matrix param matches", _role_status(
        _matrix_param_signature(), "x", code=code, line=2, signatures=signatures,
    ) == validation_mod.ParameterRoleStatus.MATCH.value)
    check("matrix return -> scalar param is a gap, never a mismatch", _role_status(
        _scalar_param_signature(), "x", code=code, line=2, signatures=signatures,
    ) == validation_mod.ParameterRoleStatus.UNKNOWN.value)
    check("trailing operator after the call is not traced", _role_status(
        _matrix_param_signature(), "x", code="x = rndu(100, 4)';\ny = f(x);", line=2, signatures=signatures,
    ) == validation_mod.ParameterRoleStatus.UNKNOWN.value)
    no_rtype = {"rndu": dataclasses.replace(rndu, return_categories=())}
    check("no documented rtype -> unknown", _role_status(
        _matrix_param_signature(), "x", code=code, line=2, signatures=no_rtype,
    ) == validation_mod.ParameterRoleStatus.UNKNOWN.value)


def test_131_untraceable_writes_make_the_variable_unresolved() -> None:
    cases = {
        "reassigned inside a block": "x = {1 2};\nif 1;\n  x = {3 4};\nendif;\ny = f(x);",
        "indexed write": "x = {1 2};\nx[1] = 5;\ny = f(x);",
        "multi-target": "x = {1 2};\n{x, z} = g(1);\ny = f(x);",
        "loop variable": "x = 1;\nfor x(1, 3, 1);\nendfor;\ny = f(x);",
        "cleared": "x = {1 2};\nclear x;\ny = f(x);",
        "expression rhs": "x = {1 2} * 2;\ny = f(x);",
        "assigned only after the call": "y = f(x);\nx = {1 2};",
        "x'x expression argument": "x = {1 2};\ny = f(x'x);",
    }
    for name, code in cases.items():
        argument = "x'x" if "x'x" in name else "x"
        line = next(i for i, l in enumerate(code.splitlines(), start=1) if "f(" in l)
        check(name, _role_status(_matrix_param_signature(), argument, code=code, line=line) == validation_mod.ParameterRoleStatus.UNKNOWN.value)


def test_132_string_contents_are_never_read_as_assignments() -> None:
    code = 'print "x = {1 2}; done";\ny = f(x);'
    check("masked", validation_mod._governing_assignment("x", code=code, line_number=2) is None)


def test_133_precondition_tracer_ignores_assignments_after_the_call() -> None:
    """Pre-v0.81.0 the tracer took the LAST `{...}` assignment anywhere in
    the code, so a reassignment written after `invpd(x)` falsely drove a
    VIOLATED verdict."""
    code = "x = {2 1, 1 2};\ny = invpd(x);\nx = {-1 0, 0 -1};"
    call = validation_mod.extract_generated_calls(code)[0]
    checks = validation_mod.check_preconditions(call, code=code)
    check("satisfied by the governing assignment", checks[0].status == validation_mod.PreconditionStatus.SATISFIED.value)


def test_134_precondition_tracer_still_catches_a_violating_reassignment_before_the_call() -> None:
    code = "x = {2 1, 1 2};\nx = {-1 0, 0 -1};\ny = invpd(x);"
    call = validation_mod.extract_generated_calls(code)[0]
    checks = validation_mod.check_preconditions(call, code=code)
    check("violated", checks[0].status == validation_mod.PreconditionStatus.VIOLATED.value)


def test_135_precondition_tracer_never_reads_a_literal_followed_by_an_operator() -> None:
    code = "x = {2 1, 1 2} * -1;\ny = invpd(x);"
    call = validation_mod.extract_generated_calls(code)[0]
    checks = validation_mod.check_preconditions(call, code=code)
    check("unverified, not satisfied", checks[0].status == validation_mod.PreconditionStatus.UNVERIFIED.value)


def test_136_documented_return_categories_use_the_first_rtype_only() -> None:
    best_match = {
        "syntax_blocks": [".. function:: y = rndu(r, c)"], "file_path": "rndu.rst",
        "inputs_section": ":param r: rows\n:type r: scalar\n:param c: cols\n:type c: scalar",
        "outputs_section": ":return y: numbers\n:rtype y: RxC matrix\n\n:return newstate: state\n:rtype newstate: Opaque vector",
    }
    signature = validation_mod.extract_documented_signature("rndu", best_match)
    check("first rtype only", signature.return_categories == (validation_mod.TypeClass.MATRIX.value,))
    no_outputs = validation_mod.extract_documented_signature("rndu", {**best_match, "outputs_section": None})
    check("absent -> ()", no_outputs.return_categories == ())


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
