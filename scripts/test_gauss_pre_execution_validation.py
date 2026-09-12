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


def test_27_inv_precondition_present_but_not_machine_checkable_is_unverified() -> None:
    call = validation_mod.GeneratedCall(symbol="inv", argument_count=1, raw_arguments=("{2 1, 1 2}",), line_number=1)
    checks = validation_mod.check_preconditions(call, code="y = inv({2 1, 1 2});")
    check("one precondition", len(checks) == 1)
    check("unverified -- inv invertibility is not machine-checked in this version", checks[0].status == validation_mod.PreconditionStatus.UNVERIFIED.value)


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
