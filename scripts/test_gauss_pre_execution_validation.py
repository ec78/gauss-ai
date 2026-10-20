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
        # v0.82.0 (option B, user-approved): a NUMERIC variable's indexed
        # write no longer makes its CATEGORY untraceable -- real GAUSS shows
        # an indexed write cannot change its shape (see test_146). The v0.81.0
        # "indexed write" case here (`x = {1 2}; x[1] = 5;`) is superseded;
        # a string target, which GAUSS rejects (G0071), still refuses.
        "indexed write to a string": 'x = "ab";\nx[1] = 5;\ny = f(x);',
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


# ---------------------------------------------------------------------------
# v0.82.0: bounded control-flow syntax coverage (`for` blocks) and the `let`
# statement rule. Every expectation below is backed by the docs or a real
# `tgauss.exe -b` result recorded in `_SYNTAX_RULE_REGISTRY` and in
# planning/v0.82-bounded-control-flow-syntax-coverage.md §2.4.
# ---------------------------------------------------------------------------


def _syntax(code: str):
    return validation_mod.validate_syntax(code)


def _rules(code: str) -> set[str]:
    return {i.rule for i in _syntax(code).issues}


def test_137_simple_for_blocks_are_validated() -> None:
    snippets = {
        "71.3 live form": "v = zeros(5, 1);\nfor i(1, 5, 1);\n    v[i] = i^2;\nendfor;\nprint v;",
        "one line": "v = zeros(5, 1); for i(1, 5, 1); v[i] = i^2; endfor; print v;",
        "documented spacing": "for i (1, 4, 1);\n   print i;\nendfor;",
        "upper case": "v = zeros(3, 1);\nFOR i (1, 3, 1);\n    v[i] = i;\nENDFOR;",
        "empty body": "for i (1, 5, 1);\nendfor;\nprint 1;",
        "counting down": "v = zeros(5, 1);\nfor i (5, 1, -1);\n    v[i] = i;\nendfor;",
        "print with ;;": "for i (1, 10, 2);\n    print i;;\nendfor;",
        "bounds from calls and variables": "n = 4;\nx = zeros(n, 2);\nfor i (1, rows(x), 1);\n    x[i, 1] = i;\nendfor;",
        "doubly nested": "x = zeros(3, 4);\nfor i (1, rows(x), 1);\n    for j (1, cols(x), 1);\n        x[i,j] = i * j;\n    endfor;\nendfor;",
        "triply nested": "v = zeros(2, 2);\nfor i (1, 2, 1);\n for j (1, 2, 1);\n  for k (1, 2, 1);\n   v[i, j] = v[i, j] + k;\n  endfor;\n endfor;\nendfor;",
        "body plain assignment": "s = 0;\nfor i (1, 3, 1);\n    t = i * 2;\nendfor;",
        "multi-line literal body": "for i (1, 2, 1);\n    a = { 1 2,\n          3 4 };\nendfor;",
    }
    for name, code in snippets.items():
        result = _syntax(code)
        check(f"{name}: validated", result.status == validation_mod.SyntaxStatus.VALIDATED.value)
        check(f"{name}: for_block recorded", "for_block" in result.validated_constructs)
        check(f"{name}: nothing unknown", result.unknown_constructs == ())


def test_138_formula_like_identifiers_are_not_for_blocks() -> None:
    result = _syntax("formula = 1;\nforecast = 2;")
    check("no for_block", "for_block" not in result.validated_constructs)
    check("validated", result.status == validation_mod.SyntaxStatus.VALIDATED.value)


def test_139_for_header_shape_is_invalid_for_every_tgauss_rejected_variant() -> None:
    cases = {
        "two args (G0105)": "v = zeros(5, 1);\nfor i (1, 5);\n    v[i] = i;\nendfor;",
        "four args (G0105)": "v = zeros(5, 1);\nfor i (1, 5, 1, 1);\n    v[i] = i;\nendfor;",
        "matlab form (G0008)": "v = zeros(3, 1);\nfor i = 1:3;\n    v[i] = i;\nendfor;",
        "c-style (G0113)": "v = zeros(5, 1);\nfor (i = 1; i <= 5; i++);\n    v[i] = i;\nendfor;",
        "header missing ; (G0063)": "v = zeros(3, 1);\nfor i (1, 3, 1)\n    v[i] = i;\nendfor;",
    }
    for name, code in cases.items():
        result = _syntax(code)
        check(f"{name}: invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
        check(f"{name}: names for_header_shape", "for_header_shape" in _rules(code))


def test_140_for_block_balance_is_invalid_for_every_tgauss_rejected_variant() -> None:
    cases = {
        "missing endfor": "v = zeros(5, 1);\nfor i (1, 5, 1);\n    v[i] = i;\nprint v;",
        "stray endfor": "v = zeros(3, 1);\nv[1] = 1;\nendfor;\nprint v;",
        "closed by endo": "v = zeros(5, 1);\nfor i (1, 5, 1);\n    v[i] = i;\nendo;",
        "crossed with if": "v = zeros(2, 2);\nfor i (1, 2, 1);\n  if i > 1;\n    v[i, 1] = 1;\nendfor;\n  endif;",
        "endfor missing ;": "v = zeros(3, 1);\nfor i (1, 3, 1);\n    v[i] = i;\nendfor\nprint v;",
    }
    for name, code in cases.items():
        result = _syntax(code)
        check(f"{name}: invalid", result.status == validation_mod.SyntaxStatus.INVALID.value)
        check(f"{name}: names for_block_balance", "for_block_balance" in _rules(code))


def test_141_counter_reuse_and_counter_assignment_are_invalid() -> None:
    reuse = "v = zeros(3, 3);\nfor i (1, 3, 1);\n  for i (1, 3, 1);\n    v[i, i] = i;\n  endfor;\nendfor;"
    check("reuse (G0736)", "for_counter_reuse" in _rules(reuse))
    for name, code in {
        "plain (G0541)": "v = zeros(5, 1);\nfor i (1, 5, 1);\n    i = 2;\n    v[i] = i;\nendfor;",
        "indexed (G0541)": "v = zeros(3, 1);\nfor i (1, 3, 1);\n    i[1] = 2;\nendfor;",
        "from an inner loop (G0541)": "v = zeros(2, 2);\nfor i (1, 2, 1);\n for j (1, 2, 1);\n  i = 1;\n endfor;\nendfor;",
    }.items():
        check(name, "for_counter_assignment" in _rules(code))
    sibling = "for i (1, 2, 1);\nendfor;\nfor i (1, 2, 1);\nendfor;"
    check("sequential loops may reuse a counter", _syntax(sibling).status == validation_mod.SyntaxStatus.VALIDATED.value)


def test_142_unmodelled_body_statements_leave_the_block_unknown() -> None:
    bodies = {
        "if": "if i > 2;\n        v[i] = i;\n    endif;",
        "break": "v[i] = i;\n    break;",
        "continue": "continue;",
        "do while": "do while 0;\n    endo;",
        "member write": "s.x = i;",
        "multi-target write": "{a, b} = f(i);",
        "bare expression statement": "f(i);",
        "format command": "format /rd 8,2;",
        "threadstat": "threadstat v[i] = i;",
    }
    for name, body in bodies.items():
        code = f"v = zeros(5, 1);\nfor i (1, 5, 1);\n    {body}\nendfor;\nprint v;"
        result = _syntax(code)
        check(f"{name}: partial", result.status == validation_mod.SyntaxStatus.PARTIAL.value)
        check(f"{name}: control_flow_block", "control_flow_block" in result.unknown_constructs)


def test_143_unmodelled_header_arguments_leave_the_block_unknown() -> None:
    headers = {
        "matrix-literal start (silently accepted by GAUSS)": "for i ({1, 2}, 3, 1);",
        "fractional step (silently truncates indices)": "for i (1, 3, 0.5);",
        "fractional start": "for i (1.5, 3, 1);",
        "string argument": 'for i ("a", 3, 1);',
        "empty slot": "for i (1, , 3, 1);",
    }
    for name, header in headers.items():
        code = f"v = zeros(5, 1);\n{header}\n    v[i] = 1;\nendfor;"
        result = _syntax(code)
        check(f"{name}: not validated", result.status == validation_mod.SyntaxStatus.PARTIAL.value)
    integral = "v = zeros(5, 1);\nfor i (1.0, 5, 1e0);\n    v[i] = 1;\nendfor;"
    check("integer-valued literals are fine", _syntax(integral).status == validation_mod.SyntaxStatus.VALIDATED.value)


def test_144_other_blocks_stay_unknown_including_previously_invisible_ones() -> None:
    cases = {
        "if": "x = 1;\nif x > 0;\n  print x;\nendif;",
        "do while": "i = 1;\ndo while i <= 3;\n  i = i + 1;\nendo;",
        "proc": "proc (1) = f(x);\n  retp(x);\nendp;",
        "threadfor (was VALIDATED pre-v0.82.0)": "v = zeros(5, 1);\nthreadfor i(1, 5, 1);\n v[i] = i;\nthreadendfor;",
        "threadbegin (was VALIDATED pre-v0.82.0)": "threadbegin;\n x = 1;\nthreadend;\nthreadjoin;",
        "for inside if": "x = 1;\nif x;\n  for i (1, 2, 1);\n    print i;\n  endfor;\nendif;",
    }
    for name, code in cases.items():
        result = _syntax(code)
        check(f"{name}: partial", result.status == validation_mod.SyntaxStatus.PARTIAL.value)
        check(f"{name}: control_flow_block", "control_flow_block" in result.unknown_constructs)


def test_145_let_statement_shape_flags_every_tgauss_rejected_case() -> None:
    rejected = (
        "x = {1, 2, 3}';", "let x = {1, 2}';", "x = {1, 2} + 1;", "x = {2 1, 1 2} * -1;", "x = {1, 2} .* 3;",
        "x = {1 2} ~ {3 4};", "x = {1 2} | {3 4};", "v = zeros(3, 1);\nv[1:2] = {7, 8};",
        "v = zeros(3, 2);\nv[., 1] = {1, 2, 3};", "v = zeros(3, 1);\nv[2] = {5};",
        "v = zeros(5, 1);\nfor i (1, 5, 1);\n    v[i] = {1};\nendfor;",
    )
    for code in rejected:
        result = _syntax(code)
        check(f"invalid: {code!r}", result.status == validation_mod.SyntaxStatus.INVALID.value)
        check(f"names let_statement_shape: {code!r}", "let_statement_shape" in _rules(code))
    accepted = (
        "x = ({1, 2}) + 1;", "x = 2 * {1, 2};", "x = -{1, 2};", "y = meanc({1, 2, 3}) + 1;",
        "y = sumc({1, 2, 3}');", "v = zeros(3, 2);\nv[., 1] = ones(3, 1);", "x = { 1 2,\n      3 4 };",
        "let x = {1 2, 3 4};", 'x = {"a" "b"};', "x = 5; y = {1, 2};",
    )
    for code in accepted:
        check(f"not flagged: {code!r}", "let_statement_shape" not in _rules(code))


def test_146_indexed_writes_keep_a_numeric_category_traceable_but_never_a_value() -> None:
    """Option B (user-approved): real GAUSS shows an indexed write cannot
    change a numeric variable's shape (G0058, no growth), so the role check
    looks through it; the precondition tracer never does."""
    code = "v = zeros(5, 1);\nfor i (1, 5, 1);\n    v[i] = i^2;\nendfor;\ny = f(v);"
    signatures = {"zeros": validation_mod.extract_documented_signature("zeros", {
        "syntax_blocks": [".. function:: y = zeros(r, c)"], "file_path": "zeros.rst",
        "inputs_section": ":param r: rows\n:type r: scalar\n:param c: cols\n:type c: scalar",
        "outputs_section": ":return y: zeros\n:rtype y: RxC matrix",
    })}
    check("documented return traced through indexed writes", _role_status(
        _matrix_param_signature(), "v", code=code, line=5, signatures=signatures,
    ) == validation_mod.ParameterRoleStatus.MATCH.value)
    check("literal traced through an indexed write", _role_status(
        _matrix_param_signature(), "x", code="x = {1 2, 3 4};\nx[1, 1] = 9;\ny = f(x);", line=3,
    ) == validation_mod.ParameterRoleStatus.MATCH.value)
    check("plain write inside the loop still refuses", _role_status(
        _matrix_param_signature(), "x", code="x = {1 2};\nfor i (1, 2, 1);\n  x = x + 1;\nendfor;\ny = f(x);", line=5,
    ) == validation_mod.ParameterRoleStatus.UNKNOWN.value)
    precondition_code = "x = {2 1, 1 2};\nx[1, 1] = -5;\ny = invpd(x);"
    call = validation_mod.extract_generated_calls(precondition_code)[0]
    checks = validation_mod.check_preconditions(call, code=precondition_code)
    check("precondition: unverified, never satisfied", checks[0].status == validation_mod.PreconditionStatus.UNVERIFIED.value)
    check("default resolver still refuses indexed writes",
          validation_mod._governing_assignment("x", code=precondition_code, line_number=3) is None)


def test_147_call_scan_blanks_mid_line_and_threadfor_counters() -> None:
    def _symbols(code: str) -> list[str]:
        return [c.symbol for c in validation_mod.extract_generated_calls(code)]
    check("one-line loop counter is not a call", _symbols("v = zeros(5, 1); for i(1, 5, 1); v[i] = i; endfor;") == ["zeros"])
    check("threadfor counter and keyword are not calls", _symbols("threadfor i(1, 5, 1);\n v[i] = i;\nthreadendfor;") == [])
    check("header calls are still extracted", _symbols("x = 1; for i (1, rows(x), 1); endfor;") == ["rows"])


def test_148_threaded_block_writes_make_a_variable_untraceable() -> None:
    code = "x = {2 1, 1 2};\nthreadfor i(1, 2, 1);\n  x = {-1 0, 0 -1};\nthreadendfor;\ny = invpd(x);"
    call = validation_mod.extract_generated_calls(code)[-1]
    checks = validation_mod.check_preconditions(call, code=code)
    check("unverified, not satisfied", checks[0].status == validation_mod.PreconditionStatus.UNVERIFIED.value)


def test_149_every_v082_rule_has_recorded_provenance() -> None:
    for name in ("for_block", "for_header_shape", "for_block_balance", "for_counter_reuse",
                 "for_counter_assignment", "let_statement_shape"):
        rule = validation_mod._SYNTAX_RULE_REGISTRY.get(name)
        check(f"{name} registered", rule is not None and rule.name == name)
        check(f"{name} has a source", rule is not None and len(rule.source) > 40)
    emitted: set[str] = set()
    for code in ("for i (1, 5);\nendfor;", "endfor;", "for i (1,2,1);\n for i (1,2,1);\n endfor;\nendfor;",
                 "for i (1,2,1);\n i = 1;\nendfor;", "x = {1}';"):
        emitted |= _rules(code)
    check("every emitted rule is registered", emitted <= set(validation_mod._SYNTAX_RULE_REGISTRY))


def test_150_nested_optional_groups_are_flattened() -> None:
    """v0.82.0: the real plotsave.rst form. `size[, units[, dpi]]` used to be
    one name, so a documented 4-argument call was a count mismatch."""
    check("plotSave", validation_mod._parse_signature_occurrence("filename[, size[, units[, dpi]]]")
          == (1, 4, ("filename", "size", "units", "dpi")))
    check("leading optional", validation_mod._parse_signature_occurrence("[myPlot, ]x, y")[1:] == (3, ("myPlot", "x", "y")))
    check("single optional unchanged", validation_mod._parse_signature_occurrence("y, x, grp[, tsc]") == (3, 4, ("y", "x", "grp", "tsc")))


def test_151_documented_variadic_has_no_upper_bound() -> None:
    lo, hi, _names = validation_mod._parse_signature_occurrence("fmt, ...")
    check("sprintf(fmt, ...): min 1", lo == 1)
    check("sprintf(fmt, ...): unbounded", hi == validation_mod.VARIADIC_MAX_ARGS)
    lo, hi, _names = validation_mod._parse_signature_occurrence("&fct, y, ...[, gCtl]")
    check("gmmFit: min 2, unbounded", (lo, hi) == (2, validation_mod.VARIADIC_MAX_ARGS))
    signature = validation_mod.extract_documented_signature(
        "sprintf", {"syntax_blocks": [".. function:: s = sprintf(fmt, ...)"], "file_path": "sprintf.rst"},
    )
    kwargs = {"documented_signatures": {"sprintf": signature}, "documented_symbols": frozenset({"sprintf"})}
    many = validation_mod.GeneratedCall(symbol="sprintf", argument_count=5, raw_arguments=('"%d"', "1", "2", "3", "4"), line_number=1)
    none = validation_mod.GeneratedCall(symbol="sprintf", argument_count=0, raw_arguments=(), line_number=1)
    check("5 args compatible", validation_mod.validate_call(many, **kwargs).argument_count_status
          == validation_mod.SignatureCompatibility.COMPATIBLE.value)
    too_few = validation_mod.validate_call(none, **kwargs)
    check("0 args still incompatible", too_few.argument_count_status == validation_mod.SignatureCompatibility.INCOMPATIBLE.value)
    check("message says 'or more'", any("1 or more" in i for i in too_few.issues))


def test_152_v082_registry_audit_covers_io_network_and_database_functions() -> None:
    cases = {
        'plotSave("f.png", {800, 600});': ("plotsave", "file_write"),
        'putf("a.txt", "hi", 1, 2, 0, 0);': ("putf", "file_write"),
        'call datasave("x.fmt", x);': ("datasave", "file_write"),
        'ret = h5write("f.h5", "/d", x);': ("h5write", "file_write"),
        'x = h5read("f.h5", "/d");': ("h5read", "file_read"),
        'x = spreadSheetReadM("a.xlsx", "A1", 1);': ("spreadsheetreadm", "file_read"),
        'x = gdaRead("a.gda", "x");': ("gdaread", "file_read"),
        'x = fred_load("GNPCA");': ("fred_load", "network"),
        'x = dbnomics_series("AMECO/ZUTN/EA19");': ("dbnomics_series", "network"),
        'id = dbAddDatabase("SQLITE");': ("dbadddatabase", "database"),
        'q = dbExecQuery(id, "select 1");': ("dbexecquery", "database"),
        "use mylib;": ("use", "source_inclusion"),
    }
    for code, (name, category) in cases.items():
        findings = validation_mod.check_system_statements(code)
        check(f"{name} found", any(f.name == name for f in findings))
        check(f"{name} is {category}", any(f.name == name and f.category == category for f in findings))
    for safe in ("close = 5;\nprint close;", "x = rows(y);", 'p = fred_set("limit", 10);', "s = xlsMakeRange(1, 1);"):
        check(f"not flagged: {safe!r}", validation_mod.check_system_statements(safe) == ())
    names = [rule.name for rule in validation_mod._SYSTEM_STATEMENT_REGISTRY]
    check("no duplicate names", len(names) == len(set(names)))


def test_153_registry_entry_inside_a_validated_loop_is_still_found() -> None:
    code = 'v = zeros(3, 1);\nfor i (1, 3, 1);\n    v[i] = i;\n    plotSave("f.png", {800, 600});\nendfor;'
    check("plotsave found on line 4", any(f.name == "plotsave" and f.line_number == 4 for f in validation_mod.check_system_statements(code)))



# ---------------------------------------------------------------------------
# v0.83.0: verdict explanations (live findings 72.3, 72.6, 72.8, 72.15)
# ---------------------------------------------------------------------------


def _signature(symbol: str, syntax: str, inputs: str, outputs: str = ""):
    return validation_mod.extract_documented_signature(symbol, {
        "syntax_blocks": [syntax], "inputs_section": inputs, "outputs_section": outputs, "file_path": f"{symbol}.rst",
    })


_SPRINTF_INPUTS = (
    ":param fmt: A sprintf style format string.\n:type fmt: string\n"
    ":param ....: One or more matrices or string arrays.\n:type ....: NxK numeric or string vectors"
)


def test_154_bare_numeric_type_text_means_matrix() -> None:
    """The real sprintf.rst `:type ....:` text. Without the bare-`numeric`
    rule it classified as `string` only, so a scalar was a false MISMATCH;
    real tgauss.exe -b runs scalar, vector, matrix and string arguments."""
    classify = validation_mod.classify_documented_type
    check("sprintf variadic type", classify("NxK numeric or string vectors")[0] == ("string", "matrix"))
    check("bare numeric alone", classify("numeric")[0] == ("matrix",))
    check("numeric vector unchanged", classify("Nx1 numeric vector")[0] == ("vector",))
    check("numeric matrix unchanged", classify("NxM numeric matrix")[0] == ("matrix",))
    check("plural stays unrecognized", classify("One or more matrices")[0] == ("unknown",))


def test_155_variadic_name_spellings_are_normalized() -> None:
    """The published docs spell a variadic `...`, `....` (sprintf.rst,
    eqsolvemt.rst, and maxlikmtProfileLimits's own signature) and, escaped,
    with backslashes (gmmfit.rst). Before v0.83.0 the four-dot signature had
    max 4 arguments and no `...` type line ever attached."""
    parse = validation_mod._parse_signature_occurrence
    check("four-dot signature is unbounded",
          parse("&logl, out0 [, ...., c1]") == (2, validation_mod.VARIADIC_MAX_ARGS, ("&logl", "out0", "...", "c1")))
    check("three-dot unchanged", parse("fmt, ...")[2] == ("fmt", "..."))
    types = validation_mod._extract_documented_parameter_types
    check("four-dot type attaches", types(":type ....: NxK numeric or string vectors") == {"...": "NxK numeric or string vectors"})
    check("three-dot type attaches (two spaces, as asdf.rst)", types(":type  ...: string") == {"...": "string"})
    check("escaped type attaches", types(":type \\.\\.\\.: any") == {"...": "any"})
    check("ordinary name unchanged", types(":type x: NxK matrix") == {"x": "NxK matrix"})
    sig = _signature("sprintf", ".. function:: s = sprintf(fmt, ...)", _SPRINTF_INPUTS)
    check("sprintf ... gets string/matrix", sig.parameters[1].category == ("string", "matrix"))


def test_156_arguments_align_with_a_documented_variadic() -> None:
    sig = _signature("sprintf", ".. function:: s = sprintf(fmt, ...)", _SPRINTF_INPUTS)
    call = validation_mod.GeneratedCall(
        symbol="sprintf", argument_count=5, raw_arguments=('"%d %d %s %d"', "3", "{1, 2}", '"x"', "{1 2, 3 4}"),
        line_number=1,
    )
    checks = validation_mod.check_parameter_roles(call, signature=sig)
    check("every argument checked (72.15's third argument was skipped)", len(checks) == 5)
    check("variadic arguments map to `...`", all(c.parameter_name == "..." for c in checks[1:]))
    check("scalar, vector, string and matrix all match", all(c.status == "match" for c in checks))

    mid = _signature("eqSolvemt", ".. function:: out = eqSolvemt(&fct, par, ..., c)",
                     ":type par: scalar\n:type c: struct")
    call = validation_mod.GeneratedCall(
        symbol="eqSolvemt", argument_count=5, raw_arguments=("&f", "1", "2", "3", "4"), line_number=1,
    )
    checks = validation_mod.check_parameter_roles(call, signature=mid)
    check("before the `...`: positional", checks[1].parameter_name == "par" and checks[1].status == "match")
    tail = checks[2:]
    check("at/after a mid-list `...`: unknown, not checked against `c`",
          all(c.status == "unknown" and c.unknown_cause == "variadic_position" and c.parameter_name is None for c in tail))
    check("no false MISMATCH against the struct `c` (pre-v0.83.0 behavior)", not any(c.status == "mismatch" for c in checks))


def test_157_every_unknown_role_check_names_its_cause() -> None:
    sig = _signature(
        "f", ".. function:: y = f(a, b, c, d)",
        ":type a: NxK matrix\n:type b: various\n:type d: NxK matrix",
    )
    g = _signature("g", ".. function:: y = g(x)", ":type x: scalar")  # no :rtype
    signatures = {"f": sig, "g": g}

    def roles(code: str):
        call = validation_mod.extract_generated_calls(code)[-1]
        return validation_mod.check_parameter_roles(call, signature=sig, code=code, signatures=signatures)

    cases = {
        "argument_expression": ("y = f(x'x, 1, 1, 1);", 0),
        "argument_untraced": ("y = f(q, 1, 1, 1);", 0),
        "argument_assigned_from_expression": ("v = 1 ./ w;\ny = f(v, 1, 1, 1);", 0),
        "return_type_undocumented": ("v = g(2);\ny = f(v, 1, 1, 1);", 0),
        "documented_type_unclassified": ("y = f(1, 1, 1, 1);", 1),
        "documented_type_missing": ("y = f(1, 1, 1, 1);", 2),
    }
    for cause, (code, position) in cases.items():
        found = roles(code)[position]
        check(f"{cause}: status unknown", found.status == "unknown")
        check(f"{cause}: cause recorded", found.unknown_cause == cause)
    detail = roles("v = 1 ./ w;\ny = f(v, 1, 1, 1);")[0].explanation
    check("explanation quotes the governing expression", "`v` is assigned from an expression (`1 ./ w`)" in detail)
    check("documented type text quoted", "(various)" in roles("y = f(1, 1, 1, 1);")[1].explanation)
    check("a MATCH carries no cause", roles("y = f(1, 1, 1, 1);")[3].unknown_cause is None)
    check("resolve_argument_category keeps its 2-tuple signature",
          validation_mod.resolve_argument_category("5") == (("scalar",), "literal"))


def test_158_no_evidence_issue_changes_text_never_eligibility() -> None:
    base = dict(unknown_symbols=(), ambiguous_topics=(), call_validations=(), preconditions=(), code_extraction_ok=True)
    plain = validation_mod.compute_eligibility(generation_policy="block", **base)
    worded = validation_mod.compute_eligibility(generation_policy="block", no_evidence_issue="no documented call", **base)
    check("same eligibility", plain[0] == worded[0] == "ineligible")
    check("ask() wording by default", plain[1] == ("generation policy does not permit code generation (block)",))
    check("validate_code wording when given", worded[1] == ("no documented call",))
    clarify = validation_mod.compute_eligibility(generation_policy="clarify", no_evidence_issue="x", **base)
    check("only `block` is reworded", "generation policy does not permit code generation (clarify)" in clarify[1])
    full = validation_mod.compute_eligibility(generation_policy="full", no_evidence_issue="x", **base)
    check("no issue when generation is permitted", full == ("eligible_for_validation", ()))


def _role(status: str, position: int = 0, cause: str | None = None):
    return validation_mod.ParameterRoleCheck(
        symbol="meanc", position=position, parameter_name="x", documented_category=("matrix",),
        inferred_category="unknown", status=status, explanation="`v` is assigned from an expression", origin="unresolved",
        unknown_cause=cause,
    )


def test_159_readiness_reasons_name_the_gap_and_never_change_the_state() -> None:
    """compute_handoff_readiness(...) reads `coverage`/`parameter_role_checks`
    only to word its reasons: every state is identical with and without them."""
    complete, na = "complete", "not_applicable"
    syntax_ok = validation_mod.SyntaxValidationResult("validated", (), ("assignment",), ())
    syntax_partial = validation_mod.SyntaxValidationResult("partial", (), ("assignment",), ("control_flow_block",))
    partial_roles = validation_mod.ValidationCoverage(complete, complete, "partial", na, na, complete)
    broad = validation_mod.ValidationCoverage(complete, complete, complete, na, na, complete)
    unknown_role = (_role("unknown", cause="argument_assigned_from_expression"),)
    table = [
        ("eligible_for_validation", (), syntax_ok, broad, ()),
        ("eligible_for_validation", (), syntax_ok, partial_roles, unknown_role),
        ("eligible_for_validation", (), syntax_partial, partial_roles, unknown_role),
        ("ineligible", ("x",), syntax_ok, partial_roles, unknown_role),
        ("requires_clarification", (), syntax_ok, partial_roles, unknown_role),
    ]
    for eligibility, issues, syntax, coverage, roles in table:
        common = dict(eligibility=eligibility, unresolved_issues=issues, syntax=syntax, call_validations=(),
                      preconditions=(), evidence_profile=validation_mod.compute_evidence_profile(coverage))
        before = validation_mod.compute_handoff_readiness(**common)
        after = validation_mod.compute_handoff_readiness(**common, coverage=coverage, parameter_role_checks=roles)
        check(f"same state: {eligibility}/{coverage.parameter_role_check}/{syntax.status}", before.state == after.state)

    reasons = validation_mod.compute_handoff_readiness(
        eligibility="eligible_for_validation", unresolved_issues=(), syntax=syntax_partial, call_validations=(),
        preconditions=(), evidence_profile="partial", coverage=partial_roles, parameter_role_checks=unknown_role,
    ).reasons
    check("syntax reason names the construct", any("unmodelled construct(s): control_flow_block" in r for r in reasons))
    check("profile reason names the dimension", any("(incomplete: parameter roles partial)" in r for r in reasons))
    check("role gap names symbol, argument and parameter",
          any("`meanc` argument 1 (parameter `x`): `v` is assigned from an expression" in r for r in reasons))

    many = tuple(_role("unknown", position=i, cause="argument_untraced") for i in range(8))
    capped = validation_mod._role_gap_reasons(many)
    check("capped at MAX_ROLE_GAP_REASONS plus a summary", len(capped) == validation_mod.MAX_ROLE_GAP_REASONS + 1)
    check("summary counts the rest", capped[-1] == "... and 3 more unknown parameter role check(s)")
    check("matches are never listed", validation_mod._role_gap_reasons((_role("match"),)) == [])


def test_160_coverage_gaps_list_only_gaps() -> None:
    syntax = validation_mod.SyntaxValidationResult("partial", (), (), ("control_flow_block",))
    calls = (
        validation_mod.CallValidationResult("f", True, False, "unknown", (), "f.rst"),
        validation_mod.CallValidationResult("meanc", True, True, "compatible", (), "meanc.rst"),
    )
    roles = (_role("unknown", cause="argument_untraced"), _role("unknown", cause="argument_untraced"), _role("match", 1))
    gaps = validation_mod.compute_coverage_gaps(
        call_validations=calls, parameter_role_checks=roles, preconditions=(), syntax=syntax,
    )
    check("one syntax, one signature, one (deduplicated) role gap",
          [g.check for g in gaps] == ["syntax", "signature", "parameter_role"])
    role_gap = gaps[2]
    check("role gap is structured", (role_gap.symbol, role_gap.argument, role_gap.parameter, role_gap.cause)
          == ("meanc", 1, "x", "argument_untraced"))
    check("no gaps for a clean result", validation_mod.compute_coverage_gaps(
        call_validations=calls[1:], parameter_role_checks=(_role("match"),), preconditions=(),
        syntax=validation_mod.SyntaxValidationResult("validated", (), (), ()),
    ) == ())


# ---------------------------------------------------------------------------
# v0.84.0: one lexer and statement stream (planning/v0.84-lexical-statement-
# stream.md). Each lexer case cites its real `tgauss.exe -b` spot check
# (GAUSS 26.1.4, 2026-10-12; IDs from the planning doc's §2.2).
# ---------------------------------------------------------------------------


def _strings(code: str) -> list[str]:
    lexed = validation_mod.lex_gauss_source(code)
    return [code[a:b] for a, b in lexed.string_spans]


def _comments(code: str) -> list[tuple[str, str]]:
    lexed = validation_mod.lex_gauss_source(code)
    return [(code[c.start:c.end], c.kind) for c in lexed.comment_spans]


def test_161_v084_lexer_follows_every_spot_checked_transition() -> None:
    # t1, t3, a2: comment openers inside a string are text
    check("t1 /* in a string", _strings('print "/*"; print "x"; print "*/";') == ['"/*"', '"x"', '"*/"'])
    check("t1 no comment", _comments('print "/*"; print "x"; print "*/";') == [])
    check("t3 // in a string", _comments('print "see https://docs.aptech.com";') == [])
    check("a2 @ in a string", _comments('print "x@y";') == [])
    # t2, a10, u4: a backslash consumes the next character
    check("t2 escaped quote", _strings('print "a\\"b"; dos dir; print "c\\"d";') == ['"a\\"b"', '"c\\"d"'])
    check("a10 escaped backslash ends the string",
          _strings('print "p\\\\"; print "q";') == ['"p\\\\"', '"q"'])
    check("u4 any escaped character", _strings('print "a\\qb";') == ['"a\\qb"'])
    # a5: a string may span lines
    check("a5 multi-line string", _strings('print "a\nb"; x = 1;') == ['"a\nb"'])
    # t6: block comments nest
    nested = '/* outer /* inner */ dos dir; */\nprint "END";'
    check("t6 nested", _comments(nested) == [("/* outer /* inner */ dos dir; */", "nested_block")])
    check("plain block", _comments("/* a */ x = 1;") == [("/* a */", "block")])
    # t7, a1, a9: @ comments, across lines and mid-statement
    check("t7 at comment", _comments('@ print "x"; @ y = 1;') == [('@ print "x"; @', "at")])
    check("a1 multi-line at", _comments('@ one\nprint "x";\n@\nz = 1;') == [('@ one\nprint "x";\n@', "at")])
    check("a9 mid-statement at", _comments("y = x @ 3 @ ;") == [("@ 3 @", "at")])
    # a3, a4, a6, a7, a8, u3: each comment form ignores the others and quotes
    check("a3 quote in a line comment", _strings('// say "hi\nprint "x";') == ['"x"'])
    check("a4 quote in a block comment", _strings('/* say "hi */ print "x";') == ['"x"'])
    check("a6 /* in a line comment", _comments("// /* \nx = 1;\n// */") == [("// /* ", "line"), ("// */", "line")])
    check("a7 // in an at comment", _comments('@ // @ print "x";') == [("@ // @", "at")])
    check("a8 @ in a block comment", _comments("/* @ */ x = 1;") == [("/* @ */", "block")])
    check("u3 // in a block comment", _comments('/* // */ print "x";') == [("/* // */", "block")])
    # u1, u2 and an open string: what stays open at end of input
    lex = validation_mod.lex_gauss_source
    check("u2 open block", lex('print "a";\n/* never closed\nx = 1;').unterminated == "block_comment")
    check("u1 open at", lex("y = x @ 3;").unterminated == "at_comment")
    check("open string", lex('print "abc;').unterminated == "string")
    check("closed", lex('print "abc";').unterminated is None)


def test_162_v084_lexer_views_keep_length_lines_and_are_idempotent() -> None:
    code = '/* one\ntwo */ x = "a;b"; // tail\n@ c @ y = meanc(x);'
    lexed = validation_mod.lex_gauss_source(code)
    check("code_view same length", len(lexed.code_view) == len(code))
    check("masked_view same length", len(lexed.masked_view) == len(code))
    check("newlines kept", lexed.code_view.count("\n") == code.count("\n") == lexed.masked_view.count("\n"))
    check("comments blanked", "one" not in lexed.code_view and "tail" not in lexed.code_view
          and "@" not in lexed.code_view)
    check("strings intact in code_view", '"a;b"' in lexed.code_view)
    check("strings masked in masked_view", '"' not in lexed.masked_view and ";b" not in lexed.masked_view)
    again = validation_mod.lex_gauss_source(lexed.code_view)
    check("idempotent on code_view", again.code_view == lexed.code_view and again.masked_view == lexed.masked_view)
    check("strip_comments is code_view", validation_mod.strip_comments(code) == lexed.code_view)
    offset = code.index("meanc")
    check("position after a multi-line comment", lexed.position(offset) == (3, offset - code.rindex("\n", 0, offset) - 1))


def test_163_v084_statement_stream_ends_at_semicolons_not_newlines() -> None:
    code = 'x = { 2 1 0,\n      1 2 1,\n      0 1 2 };\nprint "a;b"; /* c; d */ va = eigh(x);'
    statements = validation_mod.source_statements(code)
    check("three statements", [s.text.split()[0] for s in statements] == ["x", "print", "va"])
    first = statements[0]
    check("multi-line literal is one statement", first.text.endswith("0 1 2 }") and first.line == 1)
    check("its end is on line 3", (first.end_line, first.terminated) == (3, True))
    check("string text intact in text", statements[1].text == 'print "a;b"')
    check("masked hides the string", ";" not in statements[1].masked)
    check("comment never splits", statements[2].masked.strip().startswith("va"))
    check("trailing unterminated statement",
          validation_mod.source_statements("x = 1; y = 2")[-1].terminated is False)
    check("empty statements dropped", len(validation_mod.source_statements("print i;;")) == 1)
    check("_split_statements is a view of it", [s.line_number for s in validation_mod._split_statements(
        validation_mod._mask_quoted_strings(code))] == [s.line for s in statements])


def test_164_v084_calls_are_extracted_across_lines_and_strings() -> None:
    spanning = validation_mod.extract_generated_calls("x = {1 2, 2 1};\ny = invpd(\n  x);")
    check("a call spanning lines is extracted",
          [(c.symbol, c.argument_count, c.raw_arguments, c.line_number) for c in spanning]
          == [("invpd", 1, ("x",), 2)])
    escaped = validation_mod.extract_generated_calls('s = sprintf("a\\",%d", 3);')
    check("escaped quote and comma never split an argument",
          [c.raw_arguments for c in escaped] == [('"a\\",%d"', "3")])
    local_line = validation_mod.extract_generated_calls("local a; a = fakefn(x);")
    check("a declaration is skipped per statement, not per line", [c.symbol for c in local_line] == ["fakefn"])
    check("a proc header is still never a call",
          validation_mod.extract_generated_calls("proc (1) = f(x);\nretp(meanc(x));\nendp;")[0].symbol == "meanc")
    loop = validation_mod.extract_generated_calls("v = zeros(5, 1); for i(1, 5, 1); v[i] = i^2; endfor;")
    check("a one-line for header counter is never a call", [c.symbol for c in loop] == ["zeros"])
    labelled = validation_mod.extract_generated_calls('print "Inverse (2x2):";\n/* f(x) */ y = g(1);')
    check("strings and comments are never calls", [c.symbol for c in labelled] == ["g"])
    check("column within the line", labelled[0].column == len("/* f(x) */ y = "))


def test_165_v084_tracers_read_whole_multi_line_statements() -> None:
    code = "x = {1 2,\n2 1};\ny = invpd(x);"
    call = validation_mod.extract_generated_calls(code)[0]
    rhs = validation_mod._governing_assignment("x", code=code, line_number=call.line_number, column=call.column)
    check("the whole multi-line literal (73.10)", rhs == "{1 2,\n2 1}")
    pre = validation_mod.check_preconditions(call, code=code)
    check("two-line SPD violation is VIOLATED, as on one line", [p.status for p in pre] == ["violated"])
    categories, origin = validation_mod.resolve_argument_category(
        "x", code=code, line_number=call.line_number, column=call.column,
    )
    check("role tracer gets the literal", (categories, origin) == (("matrix",), "traced_literal"))
    later = "x = {2 1,\n1 2};\ny = invpd(x);\nx = {1 2,\n2 1};"
    call = validation_mod.extract_generated_calls(later)[0]
    check("an assignment ending after the call never governs it", validation_mod._governing_assignment(
        "x", code=later, line_number=call.line_number, column=call.column) == "{2 1,\n1 2}")
    blocked = "x = {2 1, 1 2};\nif rows(x) > 1;\n    x = {1 2,\n         2 1};\nendif;\ny = invpd(x);"
    call = [c for c in validation_mod.extract_generated_calls(blocked) if c.symbol == "invpd"][0]
    check("a multi-line write inside a block still refuses", validation_mod._governing_assignment(
        "x", code=blocked, line_number=call.line_number, column=call.column) is None)


def test_166_v084_syntax_reads_the_lexer() -> None:
    def status(code: str) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
        result = validation_mod.validate_syntax(code)
        return result.status, tuple(i.rule for i in result.issues), result.unknown_constructs

    check("`;` inside a string-array literal is not a row separator",
          status('s = { "a;b" };')[0] == "validated")
    check("a call-shaped string is not a call construct",
          "call" not in validation_mod.validate_syntax('print "f(x)";').validated_constructs)
    check("escaped quote is not unterminated", status('s = sprintf("a\\",%d", 3);')[0] == "validated")
    check("a URL string is fine", status('print "see https://docs.aptech.com";')[0] == "validated")
    check("an open string is still INVALID", status('print "hello;\n')[1] == ("unterminated_string",))
    check("a5 multi-line string is unknown, not invalid",
          status('print "a\nb";') == ("partial", (), ("multiline_string",)))
    check("u2 open block comment is INVALID",
          status("x = 1;\n/* never closed\ny = 2;")[1] == ("unterminated_block_comment",))
    check("u1 open at comment is INVALID", status("y = x @ 3;")[1] == ("unterminated_at_comment",))
    check("t7 at comment is an undocumented form",
          status("@ note @ x = {1 2};") == ("partial", (), ("undocumented_comment_form",)))
    check("t6 nested comment is an undocumented form",
          status("/* a /* b */ c */ x = {1 2};")[2] == ("undocumented_comment_form",))
    check("a plain comment is not", status("/* a */ x = {1 2}; // b")[0] == "validated")
    for rule in ("unterminated_block_comment", "unterminated_at_comment", "unterminated_string"):
        entry = validation_mod._SYNTAX_RULE_REGISTRY.get(rule)
        check(f"{rule} registered with provenance", entry is not None and "tgauss.exe -b" in entry.source)


def test_167_v084_system_scan_sees_through_strings_and_comments_correctly() -> None:
    def names(code: str) -> list[tuple[str, int]]:
        return [(f.name, f.line_number) for f in validation_mod.check_system_statements(code)]

    check("dos between /* and */ strings", names('print "/*"; dos dir; print "*/";') == [("dos", 1)])
    check("dos between escaped quotes", names('print "a\\"b"; dos dir; print "c\\"d";') == [("dos", 1)])
    check("dos in a string is text", names('print "dos dir";') == [])
    check("dos in a real comment is not run", names("/* dos dir; */ x = 1;") == [])
    check("dos in a multi-line string is text", names('print "a\ndos dir;\nb";') == [])
    check("line number after a multi-line comment", names("/* one\ntwo */\nx = 1;\ndos dir;") == [("dos", 4)])
    check("#include still found", names('#include foo.src\nx = 1;') == [("#include", 1)])


def test_168_v084_user_defined_names_are_statement_leading_targets() -> None:
    collect = validation_mod.collect_user_defined_symbols
    check("73.14: a string label is not an assignment", collect('d = det(x);\nprint "det = " d;') == {"d"})
    check("proc text in a string is not a definition", collect('print "proc fakefn(x)";') == frozenset())
    check("member write", collect("s.fakefn = 1;") == frozenset())
    check("indexed write", collect("x[1] = 2;") == frozenset())
    check("multi-target write", collect("{a, b} = f(x);") == frozenset())
    check("comparison in a condition", collect("if x == 1; endif;") == frozenset())
    check("assignment inside an at comment", collect("@ fakefn = 1; @ y = 2;") == {"y"})
    check("plain, let, typed and struct targets",
          collect('x = 1; let y = 1 2; string s = "a"; struct DS d = dsCreate();') == {"x", "y", "s", "d"})
    check("multi-line target", collect("x = {1 2,\n3 4};") == {"x"})
    check("proc definitions", collect("proc (1) = f(x);\nendp;\nproc g(y);\nendp;") == {"f", "g"})
    check("dot comparison is not assignment", collect("z = x .== y;") == {"z"})


def test_169_v084_undocumented_calls_are_named_gaps() -> None:
    calls = (
        validation_mod.CallValidationResult("fakeinverse", False, False, "unknown", (), None),
        validation_mod.CallValidationResult("det", True, True, "compatible", (), "det.rst"),
    )
    gaps = validation_mod.compute_coverage_gaps(call_validations=calls, parameter_role_checks=(), preconditions=(),
                                                syntax=validation_mod.SyntaxValidationResult("validated", (), (), ()))
    check("one call_undocumented gap", [(g.check, g.symbol, g.cause) for g in gaps]
          == [("signature", "fakeinverse", "call_undocumented")])
    complete, na = "complete", "not_applicable"
    syntax_ok = validation_mod.SyntaxValidationResult("validated", (), ("assignment",), ())
    coverage = validation_mod.ValidationCoverage(complete, "partial", na, na, na, complete)
    common = dict(eligibility="eligible_for_validation", unresolved_issues=(), syntax=syntax_ok, preconditions=(),
                  evidence_profile=validation_mod.compute_evidence_profile(coverage), coverage=coverage)
    with_call = validation_mod.compute_handoff_readiness(**common, call_validations=calls)
    without = validation_mod.compute_handoff_readiness(**common, call_validations=calls[1:])
    check("state unchanged by the wording", with_call.state == without.state == "review_required")
    check("reason names the undocumented call", any("`fakeinverse`" in r for r in with_call.reasons))


def test_170_v084_lexical_discipline_guard() -> None:
    """No scan of GAUSS source may bypass the shared lexer again. The only
    `splitlines()` calls left read documentation evidence or answer prose
    (planning v0.84 §2.3), and the retired regexes are gone."""
    import ast

    allowed_splitlines = {"_purpose_sentence", "_parse_output_value"}
    retired = {"_QUOTED_STRING_RE", "_ASSIGNMENT_TARGET_RE", "_PROC_DEFINITION_RE", "_LINE_COMMENT_RE",
               "_BLOCK_COMMENT_RE", "_masked_statements", "call_scan_text"}
    for module in ("gauss_conversation_engine.py", "gauss_pre_execution_validation.py"):
        tree = ast.parse((_SCRIPT_DIR / module).read_text(encoding="utf-8"))
        for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
            for node in ast.walk(fn):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "splitlines"):
                    check(f"{module}:{fn.name} splitlines allowed", fn.name in allowed_splitlines)
        used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
            n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
        } | {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        check(f"{module}: retired scanners gone", not (used & retired))


# ---------------------------------------------------------------------------
# v0.85.0: procedure headers (live finding 74.18) and code-loading statements
# (74.17). Every header below is a real `tgauss.exe -b` spot check (GAUSS
# 26.1.4, 2026-10-15; planning v0.85 §2.1), cited by its ID.
# ---------------------------------------------------------------------------

#: Headers real GAUSS runs. h12/h6/h10 already passed before v0.85.0 and are
#: invariance rows; the rest were false `call_argument_missing_separator`
#: INVALIDs.
_V085_VALID_HEADERS = {
    "s1": "proc (1) = myFunc(struct PV p);\n    retp(1);\nendp;",
    "h1": "proc (1) = f(struct PV p, struct DS d);\n    retp(1);\nendp;",
    "h2": "proc (1) = g(x, struct PV p, y);\n    retp(x + y);\nendp;",
    "h4b": "proc (0) = setb(struct box *pp);\n    pp->v = 7;\nendp;",
    "h7": "proc k(struct PV p);\n    retp(1);\nendp;",
    "h12": "proc (1) = apply(&g, x);\n    local g:proc;\n    retp(g(x));\nendp;",
    "h6": "keyword kw(str);\n    print str;\nendp;",
    "h10": "proc (1) = f(x,);\n    retp(x);\nendp;",  # decision 2 (a): GAUSS accepts the trailing comma
}

#: Headers real GAUSS rejects with `G0008 Syntax error`.
_V085_INVALID_HEADERS = {
    "h3": "proc (1) = h(a b);\n    retp(1);\nendp;",
    "h8": "proc (1) = f(struct PV);\n    retp(1);\nendp;",
    "h9": "proc (1) = f(string s);\n    retp(1);\nendp;",
    "h11": "proc (0) = setb(struct box * pp);\nendp;",
    # v0.85.0 implementation spot checks: three names, and a `keyword` header.
    "h13": "proc (1) = h(a b c);\n    retp(1);\nendp;",
    "h14": "keyword kw(a b);\n    print a;\nendp;",
}


def _rules_of(code: str) -> list[str]:
    return [issue.rule for issue in validation_mod.validate_syntax(code).issues]


def test_171_v085_proc_headers_follow_the_spot_checks() -> None:
    for spot, code in _V085_VALID_HEADERS.items():
        result = validation_mod.validate_syntax(code)
        check(f"{spot}: no issue", result.issues == ())
        check(f"{spot}: partial (the proc block is unmodelled)", result.status == validation_mod.SyntaxStatus.PARTIAL.value)
    for spot, code in _V085_INVALID_HEADERS.items():
        rules = _rules_of(code)
        check(f"{spot}: proc_header_parameter", rules == ["proc_header_parameter"])
    h3 = validation_mod.validate_syntax(_V085_INVALID_HEADERS["h3"]).issues[0]
    check("h3: names the header and the item", "`h`" in h3.message and "`a b`" in h3.message)
    check("h3: on the header's line", h3.line_number == 1)
    # h5: a CALL with a typed argument is still the call rule, never a header.
    check("h5: a call stays call_argument_missing_separator", _rules_of("y = f(struct PV p);") == ["call_argument_missing_separator"])
    # The header's own name is skipped, nothing else: a real call in the body is still checked.
    body = "proc (1) = f(struct PV p);\n    y = rndn(3 2);\n    retp(y);\nendp;"
    check("a call in the body is still checked", _rules_of(body) == ["call_argument_missing_separator"])
    check("upper-case PROC and STRUCT", validation_mod.validate_syntax(
        "PROC (1) = F(STRUCT PV p);\n    retp(1);\nENDP;").issues == ())
    # Shapes outside the four legal and four violating forms add no issue
    # (planning v0.85 §3.1); the proc block caps them at partial.
    for unknown in ("proc (1) = f(,x);\n    retp(x);\nendp;", "proc (1) = f(struct PV p q);\n    retp(1);\nendp;"):
        result = validation_mod.validate_syntax(unknown)
        check(f"no claim either way: {unknown!r}", result.issues == () and result.status == "partial")


def test_172_v085_header_skip_reads_statements_not_lines() -> None:
    split = "proc (1) =\n    myFunc(struct PV p);\n    retp(1);\nendp;"
    check("a header split across lines is a header", validation_mod.validate_syntax(split).issues == ())
    split_bad = "proc (1) =\n    myFunc(a b);\n    retp(1);\nendp;"
    bad = validation_mod.validate_syntax(split_bad).issues
    check("...and is checked as one", [i.rule for i in bad] == ["proc_header_parameter"])
    check("...reported on the header's first line", bool(bad) and bad[0].line_number == 1)
    same_line = "x = 1; proc (1) = myFunc(struct PV p);\n    retp(x);\nendp;"
    check("a header after a `;` on the same line", validation_mod.validate_syntax(same_line).issues == ())
    one_line = "proc (1) = f(struct PV p); retp(1); endp; y = g(a b);"
    check("a call after the one-line proc is still checked", _rules_of(one_line) == ["call_argument_missing_separator"])
    in_string = 'print "proc (1) = "; y = f(struct PV p);'
    check("`proc` inside a string never starts a header", _rules_of(in_string) == ["call_argument_missing_separator"])
    in_comment = "// proc (1) = f(struct PV p);\ny = f(a b);"
    check("`proc` inside a comment is not a header", _rules_of(in_comment) == ["call_argument_missing_separator"])
    not_leading = "y = proc_value(struct PV p);"
    check("a name starting with `proc` is not a header", _rules_of(not_leading) == ["call_argument_missing_separator"])


def test_173_v085_code_loading_statements_are_registered() -> None:
    cases = {
        "library tspdlib;": ("library", "source_inclusion"),
        "library pgraph, cmlmt;": ("library", "source_inclusion"),
        "library;": ("library", "source_inclusion"),  # planning v0.85 §5: fails closed like every entry
        "LIBRARY tspdlib;": ("library", "source_inclusion"),
        "x = 1; library tspdlib;": ("library", "source_inclusion"),
        "dlibrary -a mylib;": ("dlibrary", "native_code"),
        "dlibrary -d;": ("dlibrary", "native_code"),
        "dllcall -r myfunc(x);": ("dllcall", "native_code"),
        "dllcall myfunc;": ("dllcall", "native_code"),
    }
    for code, (name, category) in cases.items():
        findings = validation_mod.check_system_statements(code)
        check(f"{code!r}: {name} found", any(f.name == name for f in findings))
        check(f"{code!r}: {name} is {category}", any(f.name == name and f.category == category for f in findings))
    pages = {rule.name: rule.doc_page for rule in validation_mod._SYSTEM_STATEMENT_REGISTRY}
    check("library cites library.rst", pages.get("library") == "library.rst")
    check("dlibrary cites dlibrary.rst", pages.get("dlibrary") == "dlibrary.rst")
    check("dllcall cites dllcall.rst", pages.get("dllcall") == "dllcall.rst")
    check("native_code is a category", "native_code" in {c.value for c in validation_mod.SystemStatementCategory})
    for safe in ('print "library tspdlib";', "// library tspdlib;", "/* dlibrary -a mylib; */",
                 "library = 5;", "x = dllcall_count + 1;", "mylibrary = 2;"):
        check(f"not flagged: {safe!r}", validation_mod.check_system_statements(safe) == ())
    names = [rule.name for rule in validation_mod._SYSTEM_STATEMENT_REGISTRY]
    check("216 entries, no duplicates", len(names) == 216 and len(names) == len(set(names)))


def test_174_v085_header_rule_provenance() -> None:
    rule = validation_mod._SYNTAX_RULE_REGISTRY.get("proc_header_parameter")
    check("proc_header_parameter registered", rule is not None)
    if rule is not None:
        check("names itself", rule.name == "proc_header_parameter")
        check("cites real tgauss.exe -b", "tgauss.exe -b" in rule.source)
        check("cites every violation spot check", all(f"h{n}" in rule.source for n in (3, 8, 9, 11, 13, 14)))
        check("cites the legal-shape spot checks", all(s in rule.source for s in ("s1", "h4b", "h12", "h10")))
        check("the description gives the four legal shapes", all(
            shape in rule.description for shape in ("`name`", "`&name`", "`struct Type name`", "`struct Type *name`")
        ))
    separator = validation_mod._SYNTAX_RULE_REGISTRY["call_argument_missing_separator"]
    check("the call rule points headers at the header rule", "proc_header_parameter" in separator.description)


# ---------------------------------------------------------------------------
# v0.86.0: structure-member targets (live findings 75.8/75.18), word
# operators (75.19) and structure definitions (75.20). Every program below is
# a real `tgauss.exe -b` spot check (GAUSS 26.1.4, 2026-10-16; planning v0.86
# §2), cited by its ID.
# ---------------------------------------------------------------------------

_PT = "struct pt { matrix x; };\nstruct pt s;\n"

#: Brace literals assigned to member targets that real GAUSS runs.
_V086_VALID_MEMBER_TARGETS = {
    "m01": _PT + "s.x = {1 2};",
    "m02": _PT + "s.x = { 1 2,\n        3 4 };",
    "m03": "struct inner { matrix b; };\nstruct outer { struct inner a; };\nstruct outer s;\ns.a.b = {1};",
    "m08": _PT + "let s.x = {1 2};",
    "m10": _PT + "s.x = ({1, 2})';",
    "m11": "struct ps { string array sa; };\nstruct ps s;\ns.sa = {\"a\" \"b\"};",
    "m15": "struct DS d;\nd = dsCreate();\nd.dataMatrix = {1 ., 3 4};",
    "sc01": "struct DS d;\nd = dsCreate();\nd.dataMatrix = { 1 2, 3 4 };",
    "sc02": "struct gmmControl g;\ng = gmmControlCreate();\ng.bStart = { 0, 0 };",
    "m26": _PT + "struct pt *pp;\npp = &s;\npp->x = ({3 4});",
    "same line": _PT + "y = 1; s.x = {1 2};",
    "split": _PT + "s.x\n  = {1 2,\n 3 4};",
    # Found by the §6.3 all-docs diff (planning v0.86 §9.2): a member of a
    # structure-array element, as in cmlmtprofile.rst.
    "m33": _PT + "s = reshape(s, 2, 1);\ns[1].x = {1 2};",
    "m37": "struct DS d0;\nd0 = reshape(dsCreate, 2, 1);\nd0[1].dataMatrix = {8.3, 10.3, 19.0};",
}

#: Member (and plain indexed) targets real GAUSS rejects, or silently
#: misparses (m04, m18: the whole variable becomes the 1x1 literal).
_V086_INVALID_MEMBER_TARGETS = {
    "m04": _PT + "s.x = {1 2 3};\ns.x[1] = {5};",
    "m05": _PT + "s.x = {1 2 3};\ns.x[1:2] = {7 8};",
    "m17": _PT + "s.x = {1 2 3};\ns.x[2] = {5};",
    "m18": "v = {1 2 3};\nv[1] = {5};",
    "m20": _PT + "s.x = {1 2, 3 4};\ns.x[1, 2] = {9};",
    "m06": _PT + "s.x = {1, 2}';",
    "m07": _PT + "s.x = {1, 2} + 1;",
    "m13": _PT + "s.x = {1 2} ~ {3 4};",
    "m31": _PT + "let s.x = {1 2} + 1;",
    "m09": _PT + "s . x = {1 2};",
    "m28": _PT + "s .x = {1 2};",
    "m29": _PT + "s. x = {1 2};",
    "m24": _PT + "struct pt *pp;\npp = &s;\npp->x = {3 4};",
    "m25": _PT + "struct pt *pp;\npp = &s;\npp->x = {3};",
    "m34": _PT + "s = reshape(s, 2, 1);\ns[1].x = {1, 2}';",
    "m35": _PT + "s = reshape(s, 2, 1);\ns[1].x = {1 2 3};\ns[1].x[1] = {5};",
    "m38": _PT + "s = reshape(s, 2, 1);\ns[1] .x = {1 2};",
}


def test_175_v086_member_targets_follow_the_spot_checks() -> None:
    for spot, code in _V086_VALID_MEMBER_TARGETS.items():
        check(f"{spot}: no syntax issue", _rules_of(code) == [])
    for spot, code in _V086_INVALID_MEMBER_TARGETS.items():
        check(f"{spot}: let_statement_shape", _rules_of(code) == ["let_statement_shape"])
    messages = {
        spot: validation_mod.validate_syntax(_V086_INVALID_MEMBER_TARGETS[spot]).issues[0].message
        for spot in ("m04", "m06", "m09", "m24")
    }
    check("indexed message names the silent replacement", "indexed target" in messages["m04"]
          and "silently replaces" in messages["m04"])
    check("trailing message unchanged", "nothing may follow" in messages["m06"])
    check("whitespace message", "whitespace around the member" in messages["m09"])
    check("pointer message", "structure pointer" in messages["m24"])
    # Invariance: v0.82.0's plain-name evidence is unchanged.
    check("x = {1, 2, 3}'; still flagged", _rules_of("x = {1, 2, 3}';") == ["let_statement_shape"])
    check("v[., 1] = {1, 2, 3}; still flagged", _rules_of("v[., 1] = {1, 2, 3};") == ["let_statement_shape"])
    check("x = {1 2}; still clean", _rules_of("x = {1 2};") == [])
    # A non-literal pointer write was never matched and is not now (m23, m27).
    check("pp->x = 3; clean", _rules_of(_PT + "struct pt *pp;\npp = &s;\npp->x = 3;") == [])
    # Masked: a member-literal shape inside a string is never a statement.
    check("in a string", _rules_of('print "pp->x = {3 4};";') == [])


_A = "a = {1, 0, 1};\nb = {1, 1, 0};\n"
_S = "s = 1;\nt = 0;\n"


def _v086_word_operator_programs() -> dict[str, str]:
    """The §2.2 shapes that real GAUSS runs, one per spot-check program."""
    programs: dict[str, str] = {}
    for op in ("and", "or", "xor", "eqv"):
        programs[f"w_dot_{op}_paren"] = _A + f"y = (a) .{op} (b);"
        programs[f"w_dot_{op}_nospace"] = _A + f"y = (a).{op}(b);"
        programs[f"w_dot_{op}_incall"] = _A + f"y = sumc((a) .{op} (b));"
        programs[f"w_dot_{op}_incall_bare"] = _A + f"y = sumc(a .{op} b);"
        programs[f"w_{op}_paren"] = _S + f"y = (s) {op} (t);"
        programs[f"w_{op}_nospace"] = _S + f"y = (s){op}(t);"
        programs[f"w_{op}_incall"] = _S + f"y = maxc((s) {op} (t));"
        programs[f"w_{op}_incall_bare"] = _S + f"y = maxc(s {op} t);"
    for op in ("eq", "ne", "lt", "le", "gt", "ge"):
        programs[f"w_dot_{op}_paren"] = _A + f"y = (a) .{op} (1);"
        programs[f"w_dot_{op}_incall"] = _A + f"y = sumc((a) .{op} (1));"
        programs[f"w_{op}_paren"] = _S + f"y = (s) {op} (1);"
        programs[f"w_{op}_incall"] = _S + f"y = maxc((s) {op} (1));"
    programs.update({
        "w_dot_not_paren": _A + "y = .not (a);",
        "w_dot_not_nospace": _A + "y = .not(a);",
        "w_dot_not_incall": _A + "y = sumc(.not (a));",
        "w_dot_not_incall_bare": _A + "y = sumc(.not a);",
        "w_not_nospace": _S + "e = not(s);",
        "w_not_incall": _S + "y = maxc(not (s));",
        "w_dot_and_dot_not_incall": _A + "y = sumc(a .and .not b);",
        "w_upper_dot_or": _A + "y = (a) .OR (b);",
        "w_upper_or": _S + "y = maxc((s) OR (t));",
        "w_mixed_Or": _S + "y = (s) Or (t);",
        "w_selif_doc_example": "x = {1, 5, 9};\ny = selif(x, (x .> 1) .and (x .< 9));",
        "sc05": "x = {1, 5, 9};\ne = (x .< 2) .or (x .> 8);",
    })
    return programs


def test_176_v086_word_operators_are_never_adjacent_tokens() -> None:
    for spot, code in _v086_word_operator_programs().items():
        check(f"{spot}: no syntax issue", _rules_of(code) == [])
    # Real adjacency is still caught (G0063), and so is `not` used as a
    # binary operator (G0136).
    for spot, code in {
        "w_bad_adjacent_names": _A + "y = sumc(a .or b a);",
        "w_bad_not_binary": _S + "y = maxc(s not t);",
        "w_bad_dot_not_binary": _A + "y = sumc((a) .not (b));",
        "w_bad_adjacent_parens": _A + "y = sumc((a) (b));",
    }.items():
        check(f"{spot}: still call_argument_missing_separator", _rules_of(code) == ["call_argument_missing_separator"])
    # Identifiers that merely contain an operator's letters are still tokens.
    check("notes x adjacent", _rules_of("y = f(notes x);") == ["call_argument_missing_separator"])
    check("x order adjacent", _rules_of("y = f(x order);") == ["call_argument_missing_separator"])


def test_177_v086_word_operators_are_never_calls() -> None:
    for spot, code in _v086_word_operator_programs().items():
        symbols = {call.symbol.lower() for call in validation_mod.extract_generated_calls(code)}
        check(f"{spot}: no word operator extracted", not (symbols & validation_mod._WORD_OPERATORS))
    calls = validation_mod.extract_generated_calls("x = {1, 5, 9};\nm = meanc((x .< 2) .or (x .> 8));")
    check("meanc still extracted", [c.symbol for c in calls] == ["meanc"])
    if calls:
        check("argument text keeps the operator", calls[0].raw_arguments == ("(x .< 2) .or (x .> 8)",))
    # Whole identifiers only: these are still calls.
    names = [c.symbol for c in validation_mod.extract_generated_calls(
        "y = order(x); z = notes(x); w = ltrim(s); v = ne2(x); u = geta(x);"
    )]
    check("look-alike names are calls", names == ["order", "notes", "ltrim", "ne2", "geta"])
    # Lexical discipline: a string or comment is never touched (the view
    # is masked either way), and the view keeps its length and lines.
    code = 'print "a or (b)"; // or (c)\ny = (a) .or (b);'
    view = validation_mod.call_scan_view(code)
    check("same length", len(view) == len(code) and view.count("\n") == code.count("\n"))
    check("no call in string, comment or operator", validation_mod.extract_generated_calls(code) == ())
    check("the word set", validation_mod._WORD_OPERATORS == frozenset(
        {"and", "or", "not", "xor", "eqv", "eq", "ne", "lt", "le", "gt", "ge"}
    ))


#: Structure definitions real GAUSS runs (each program also declares an
#: instance and prints; only the definition matters here).
_V086_VALID_DEFINITIONS = {
    "sc04": "struct regResults {\n    matrix b;\n    matrix se;\n    string label;\n};\nstruct regResults r;",
    "d01": "struct my_struct {\n    scalar count;\n    matrix data;\n    string label;\n    string array names;\n};",
    "d02": "struct pt { matrix x; };",
    "d03": "struct pt { matrix x; };\nstruct box { array a; struct pt inner; matrix m; };",
    "d04": "struct sp { sparse matrix sm; };",
    "d10": "struct e { };",
    "d12": "struct pt { matrix x };",
    "d13": "struct pt { matrix x; } s;",
    "d14": "STRUCT PT { MATRIX X; };",
    "d23": "x = 1; struct pt { matrix x; }; struct pt s;",
    "d31": "struct w { struct DS d; struct PV p; };",
    "d32": "struct d { String Array n; };",
    "d33": "struct d { string\n   array n; };",
    "d36": "struct pt {\n  matrix x;  // the data\n  /* a */ string s;\n};",
    "d37": "struct d { matrix string; };",
    "d29": "struct pt { matrix x; };\nstruct pt { matrix x; };",
}

#: Member items real GAUSS rejects with G0008 (d34 also G0507), and d39's
#: nameless definition.
_V086_INVALID_DEFINITIONS = {
    "d05": "struct hp { struct pt *p; };",
    "d40": "struct hp { struct pt * p; };",
    "d06": "struct two { matrix a, b; };",
    "d07": "struct two { matrix a b; };",
    "d08": "struct nt { x; };",
    "d09": "struct ini { matrix x = 1; };",
    "d15": "struct ut { vector v; };",
    "d16": "struct lt { local v; };",
    "d17": "struct ml { matrix x; {1 2}; };",
    "d20": "struct sa { stringarray n; };",
    "d25": "struct d { matrix; };",
    "d26": "struct d { struct pt; };",
    "d27": "struct d { sparse x; };",
    "d28": "struct d { matrix x[2]; };",
    "d30": "struct d { matrix x; print 5; };",
    "d34": "struct o { struct i { matrix x; } ii; };",
    "d39": "struct { matrix x; };",
}


def test_178_v086_structure_definitions_follow_the_spot_checks() -> None:
    for spot, code in _V086_VALID_DEFINITIONS.items():
        result = validation_mod.validate_syntax(code)
        check(f"{spot}: no issue", result.issues == ())
        check(f"{spot}: struct_definition validated", "struct_definition" in result.validated_constructs)
        check(f"{spot}: no unknown", result.unknown_constructs == ())
    for spot, code in _V086_INVALID_DEFINITIONS.items():
        check(f"{spot}: struct_definition_shape", _rules_of(code) == ["struct_definition_shape"])
    issue = validation_mod.validate_syntax("struct pt {\n  matrix x;\n  vector v;\n};").issues
    check("reported on the item's line", len(issue) == 1 and issue[0].line_number == 3)
    check("message names the item", len(issue) == 1 and "`vector v`" in issue[0].message)
    # d11: no `;` after `}` -- the one failing observation, so unknown, not INVALID.
    d11 = validation_mod.validate_syntax("struct pt { matrix x; }\nstruct pt s;")
    check("d11: no issue", d11.issues == ())
    check("d11: unknown struct_definition", "struct_definition" in d11.unknown_constructs)
    check("d11: partial", d11.status == validation_mod.SyntaxStatus.PARTIAL.value)
    # Real matrix literals are still checked, right after a definition too (d24).
    check("d24 shape: a `;` literal after a definition", _rules_of(
        "struct pt { matrix x; };\nstruct pt s;\ns.x = {1 2; 3 4};"
    ) == ["matrix_literal_row_separator"])
    check("d24: a good literal after a definition", _rules_of("struct pt { matrix x; };\nstruct pt s;\ns.x = {1 2, 3 4};") == [])
    check("a declaration is not a definition", "struct_definition" not in
          validation_mod.validate_syntax("struct pt s;\nx = 1;").validated_constructs)
    # Masked: `struct` and braces in strings or comments are never a definition.
    check("in a string", _rules_of('s = "struct pt { matrix x; vector v; };";') == [])
    check("in a comment", _rules_of("// struct pt { vector v; };\nx = 1;") == [])
    check("a string member type name is masked", _rules_of('struct pt { matrix x; };\nprint "{;}";') == [])
    # The I/O rule: no statement can hide in a passing definition.
    check("dos inside a definition is INVALID", _rules_of("struct d { dos dir; };") == ["struct_definition_shape"])


def test_179_v086_rule_provenance() -> None:
    registry = validation_mod._SYNTAX_RULE_REGISTRY
    let_rule = registry["let_statement_shape"]
    check("let cites the member spot checks", all(
        f"m{n:02d}" in let_rule.source for n in (1, 3, 4, 5, 6, 8, 9, 18, 24, 25, 26, 33, 34, 35, 37, 38)
    ) and "sc01" in let_rule.source)
    check("let describes member paths", "member path" in let_rule.description)
    struct_rule = registry.get("struct_definition_shape")
    check("struct_definition_shape registered", struct_rule is not None)
    if struct_rule is not None:
        check("names itself", struct_rule.name == "struct_definition_shape")
        check("cites real tgauss.exe -b", "tgauss.exe -b" in struct_rule.source)
        check("cites every failing item", all(
            f"d{n:02d}" in struct_rule.source for n in (5, 6, 7, 8, 9, 15, 16, 17, 20, 25, 26, 27, 28, 30, 34, 39, 40)
        ))
        check("cites the docs", "structures.rst" in struct_rule.source and "declare.rst" in struct_rule.source)
        check("discloses the type-level gaps", all(code in struct_rule.description for code in ("G0071", "G0507", "G0467")))
    separator = registry["call_argument_missing_separator"]
    check("separator rule names word operators", "word operator" in separator.description
          and "G0276" in separator.source)
    literal = registry["matrix_literal_row_separator"]
    check("literal rule points at the definition rule", "struct_definition_shape" in literal.description)


# ---------------------------------------------------------------------------
# v0.87.0: the `/` operator (live finding 77.x f1) and `eigh`/`eighv`
# symmetry (76.x f6). Every program below is a real `tgauss.exe -b` spot
# check (GAUSS 26.1.4, 2026-10-20; planning v0.87 §2.5/§2.6), cited by its ID.
# ---------------------------------------------------------------------------

_SINGULAR = "a = {1 2, 2 4};\n"

#: ID -> (program, expected `/` statuses). GAUSS's own result is in the
#: comment: G0048/G0121 fail, "solves"/"element-wise" run.
_V087_DIVISION_ROWS = {
    "dv01": ("a = {1 2, 3 4};\nb = {5, 11};\nx = b / a;", ["satisfied"]),  # solves
    "dv02": (_SINGULAR + "b = {1, 2};\nx = b / a;", ["violated"]),  # G0048
    "dv03": (_SINGULAR + "x = eye(2) / a;", ["unverified"]),  # G0048; eye(2)'s shape not evaluated
    "dv04": (_SINGULAR + "x = 1 / a;", []),  # element-wise
    "dv05": (_SINGULAR + "x = a / 2;", []),  # element-wise
    "dv06": ("X = {1 2, 2 4, 3 6};\ny = {1, 2, 3};\nb = y / X;", ["violated"]),  # G0121
    "dv07": ("X = {1 1, 1 2, 1 3};\ny = {1, 2, 4};\nb = y / X;", ["satisfied"]),  # least squares
    "dv08": ("X = {1 2 3, 4 5 6};\ny = {1, 2};\nb = y / X;", ["violated"]),  # G0121
    "dv12": (_SINGULAR + "b = {1 2, 3 4};\nx = b / a;", ["violated"]),  # G0048
    "dv16": ("a = {1 2, 3 4};\nx = eye(2) / a';", []),  # solves; call dividend
    "dv19": (_SINGULAR + "x = eye(2) / a + 1;", ["unverified"]),  # G0048: `+` binds after `/`
    "dv20": ("X = {1 2, 2 4, 3 6};\ny = {1 2, 2 4, 3 6};\nb = y / X;", ["violated"]),  # G0121
    "dv22": ("x = eye(3) / {1 2 3, 4 5 6, 7 8 9};", ["unverified"]),  # G0048
    "dv23": ("x = eye(2) / {1 2, 2 4};", ["unverified"]),  # G0048
    "dv24": ("b = {1, 2};\nx = b / {1 2, 3 4};", ["satisfied"]),  # solves
    "dv25": ("s = 3;\n" + _SINGULAR + "x = s / a;", []),  # element-wise
    "dv26": (_SINGULAR + "x = eye(1) / a;", ["unverified"]),  # element-wise: eye(1) is a scalar
    "dv27": (_SINGULAR + "x = (eye(2)) / (a);", []),  # G0048, but a parenthesized divisor is unchecked
    "dv28": (_SINGULAR + "b = {1 2, 3 4};\nx = b / a[1:2, 1:2];", []),  # G0048, indexed: unchecked
    "dv31": ("b = {1 2, 2 4};\nx = eye(2) ./ b;", []),  # element-wise operator
    "dv32": ("X = {1 2, 2 4, 3 6};\ny = {1, 2, 3};\nb = y / X;\nprint \"after\";", ["violated"]),  # G0121
}


def test_180_v087_division_operator_follows_the_spot_checks() -> None:
    for spot_id, (code, expected) in _V087_DIVISION_ROWS.items():
        got = [c.status for c in validation_mod.check_operator_preconditions(code)]
        check(f"{spot_id}: {expected}", got == expected)
    lexical = {
        "string": 'x = "b / a";',
        "line comment": _SINGULAR + "x = 1; // b / a",
        "block comment": _SINGULAR + "x = 1; /* b / a */",
        "power binds first": _SINGULAR + "b = {1 2, 3 4};\nx = b / a ^ 2;",
        "a call is not a divisor": _SINGULAR + "b = {1 2, 3 4};\nx = b / inv(a);",
        "member is not a divisor": "x = eye(2) / s.a;",
    }
    for label, code in lexical.items():
        check(f"no `/` check: {label}", validation_mod.check_operator_preconditions(code) == ())
    check("`*` associates left (dv15)", [c.status for c in validation_mod.check_operator_preconditions(
        _SINGULAR + "b = {1 2, 3 4};\nx = b / a * a;")] == ["violated"])
    big = "a = {" + ", ".join(" ".join("1" if i == j else "0" for j in range(7)) for i in range(7)) + "};\n"
    check("a 7x7 divisor is beyond the checked bound", validation_mod.check_operator_preconditions(
        big + "b = a;\nx = b / a;") == ())
    check("a later reassignment is not the divisor's value", [c.status for c in validation_mod.check_operator_preconditions(
        _SINGULAR + "b = {1 2, 3 4};\nx = b / a;\na = {1 0, 0 1};")] == ["violated"])


_V087_EIGEN_ROWS = {
    "eg01": ("x = {4 1, 0 3};\nva = eigh(x);", "violated"),  # prints 3 4: the lower triangle's
    "eg02": ("x = {4 0, 1 3};\nva = eigh(x);", "violated"),  # = eg03's answer, silently
    "eg03": ("x = {4 1, 1 3};\nva = eigh(x);", "satisfied"),
    "eg04": ("x = {4 0, 0 3};\nva = eigh(x);", "satisfied"),
    "eg05": ("x = {4 1, 0 3};\n{va, ve} = eighv(x);", "violated"),
    "eg07": ("x = {1 2 3, 4 5 6};\nva = eigh(x);", "violated"),  # G0150 Matrix not square
    "eg08": ("x = {2 -1 0, 5 2 -1, 7 9 2};\nva = eigh(x);", "violated"),
    "eg09": ("x = {4 1, 1.0000000001 3};\nva = eigh(x);", "satisfied"),  # inside the 1e-9 tolerance
    # prints 2.38 4.62 (the transpose's lower triangle), not eig's 4 3:
    # the transposed literal is just as non-symmetric
    "eg10": ("x = {4 1, 0 3};\nva = eigh(x');", "violated"),
    "eg10 symmetric control": ("x = {4 1, 1 3};\nva = eigh(x');", "satisfied"),
}


def test_181_v087_eigh_and_eighv_symmetry() -> None:
    for spot_id, (code, expected) in _V087_EIGEN_ROWS.items():
        calls = [c for c in validation_mod.extract_generated_calls(code) if c.symbol.lower() in ("eigh", "eighv")]
        got = [p.status for c in calls for p in validation_mod.check_preconditions(c, code=code)]
        check(f"{spot_id}: {expected}", got == [expected])
    runtime = "x = rndn(4, 3);\nva = eigh(x'x);"
    call = [c for c in validation_mod.extract_generated_calls(runtime) if c.symbol == "eigh"][0]
    check("a runtime input is unverified (decision 8)",
          [p.status for p in validation_mod.check_preconditions(call, code=runtime)] == ["unverified"])
    lower = validation_mod.check_preconditions(validation_mod.extract_generated_calls(_V087_EIGEN_ROWS["eg01"][0])[0],
                                               code=_V087_EIGEN_ROWS["eg01"][0])
    check("the violation says why", "lower triangle" in lower[0].explanation)


def test_182_v087_precondition_provenance() -> None:
    division = validation_mod._OPERATOR_PRECONDITIONS["/"]
    check("`/` cites its pages", "operators.rst" in division.source and "matrix-division.rst" in division.source)
    check("`/` cites the dv series", all(f"dv{n:02d}" in division.description for n in (2, 3, 4, 6, 8, 12, 20, 22, 23, 25, 26, 32)))
    check("`/` records the QR contradiction", "QR" in division.description and "G0121" in division.description)
    for symbol, ids in (("eigh", ("eg01", "eg06", "eg07", "eg08")), ("eighv", ("eg05",))):
        entry = validation_mod.documented_preconditions(symbol)
        check(f"{symbol} registered", len(entry) == 1 and entry[0].machine_checkable)
        if entry:
            check(f"{symbol} cites its page", entry[0].source == f"{symbol}.rst")
            check(f"{symbol} cites its spot checks", all(i in entry[0].description for i in ids))
    for symbol in validation_mod._PRECONDITION_CHECKERS:
        entries = validation_mod.documented_preconditions(symbol)
        check(f"checker {symbol} has a machine_checkable entry", bool(entries) and entries[0].machine_checkable)
    check("`/` is not call-keyed", validation_mod.documented_preconditions("/") == ())


def test_183_v087_existing_checkers_unchanged() -> None:
    rows = {
        "inv singular": ("a = {1 2, 2 4};\nxi = inv(a);", "inv", "violated"),
        "inv regular": ("a = {2 1, 1 2};\nxi = inv(a);", "inv", "satisfied"),
        "invpd non-symmetric": ("a = {2 1, 0 2};\nxi = invpd(a);", "invpd", "violated"),
        "invpd spd": ("a = {2 1, 1 2};\nxi = invpd(a);", "invpd", "satisfied"),
        "solpd upper triangle": ("A = {2 1, 0 2};\nb = {1, 1};\nx = solpd(b, A);", "solpd", "satisfied"),
        "chol not pd": ("a = {1 2, 2 1};\nc = chol(a);", "chol", "violated"),
        "inv runtime": ("X = rndn(5, 2);\nxi = inv(X'X);", "inv", "unverified"),
        # Disclosed (planning v0.87 §2.5, decision 11): GAUSS inverts this
        # (dv10/dv11), but the absolute 1e-9 determinant bound is unchanged.
        "inv det 1e-10": ("a = {1 0, 0 1e-10};\nxi = inv(a);", "inv", "violated"),
    }
    for label, (code, symbol, expected) in rows.items():
        calls = [c for c in validation_mod.extract_generated_calls(code) if c.symbol == symbol]
        got = [p.status for c in calls for p in validation_mod.check_preconditions(c, code=code)]
        check(f"{label}: {expected}", got == [expected])


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
