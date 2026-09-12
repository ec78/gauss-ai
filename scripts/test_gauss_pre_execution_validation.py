"""Tests for `gauss_pre_execution_validation.py` (v0.74.0).

Run with:

    python scripts/test_gauss_pre_execution_validation.py

Fully synthetic and network-free: no real GAUSS execution, no real
documentation checkout, no model provider of any kind.
"""

from __future__ import annotations

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
