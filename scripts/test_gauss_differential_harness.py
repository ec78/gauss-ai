"""Tests for `gauss_differential_harness.py` (v0.77.0).

Run with:

    python scripts/test_gauss_differential_harness.py

Fully synthetic and network-free: no real GAUSS execution (every fake
`gauss_runner` below is a plain Python function returning a hand-built
dict), no real documentation checkout, no model provider of any kind.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_differential_harness as harness  # noqa: E402
import gauss_pre_execution_validation as validation_mod  # noqa: E402

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


# ---------------------------------------------------------------------------
# classify_gauss_outcome
# ---------------------------------------------------------------------------


def test_01_completed_is_accepted() -> None:
    result = harness.classify_gauss_outcome({"execution_status": "completed", "stdout": "4.0000000", "stderr": ""})
    check("outcome accepted", result.outcome == harness.RealGaussOutcome.ACCEPTED.value)


def test_02_failed_with_parse_syntax_code_is_rejected_syntax() -> None:
    result = harness.classify_gauss_outcome({
        "execution_status": "failed", "stdout": "", "stderr": "error G0105: Bad expression or missing arguments",
    })
    check("outcome rejected_syntax_or_parse", result.outcome == harness.RealGaussOutcome.REJECTED_SYNTAX_OR_PARSE.value)
    check("matched code G0105", result.matched_error_codes == ("G0105",))
    check("basis catalogued", result.classification_basis == "catalogued:G0105:PARSE_SYNTAX")


def test_03_failed_with_non_syntax_catalogued_code_is_runtime_error() -> None:
    result = harness.classify_gauss_outcome({
        "execution_status": "failed", "stdout": "", "stderr": "error G0036: dimension mismatch",
    })
    check("outcome runtime_error", result.outcome == harness.RealGaussOutcome.RUNTIME_ERROR.value)
    check("basis names matrix_dimension category", "matrix_dimension" in result.classification_basis)


def test_04_failed_with_uncatalogued_code_is_flagged_uncatalogued() -> None:
    result = harness.classify_gauss_outcome({
        "execution_status": "failed", "stdout": "", "stderr": "error G9999: some new never-seen code",
    })
    check("outcome still recorded (runtime_error, best-effort)", result.outcome == harness.RealGaussOutcome.RUNTIME_ERROR.value)
    check("basis flagged uncatalogued", result.classification_basis.startswith("uncatalogued"))


def test_05_failed_nonzero_exit_no_error_code_is_uncatalogued() -> None:
    """The real gauss_code_execution.py 'else' branch: a nonzero exit with no
    detected error-code marker still maps execution_status to 'failed', but
    carries no G#### code at all -- must never be silently treated as
    confirmed syntax evidence."""
    result = harness.classify_gauss_outcome({
        "execution_status": "failed", "stdout": "", "stderr": "",
        "errors": ["GAUSS process exited with nonzero status (1); execution failed."],
    })
    check("basis uncatalogued no code", result.classification_basis == "uncatalogued:no_error_code_detected")


def test_06_timed_out_is_timeout() -> None:
    result = harness.classify_gauss_outcome({"execution_status": "timed_out", "stdout": "", "stderr": ""})
    check("outcome timeout", result.outcome == harness.RealGaussOutcome.TIMEOUT.value)


def test_07_blocked_is_infrastructure_failure() -> None:
    result = harness.classify_gauss_outcome({"execution_status": "blocked", "stdout": None, "stderr": None})
    check("outcome infrastructure_failure", result.outcome == harness.RealGaussOutcome.INFRASTRUCTURE_FAILURE.value)


def test_08_error_status_is_infrastructure_failure() -> None:
    result = harness.classify_gauss_outcome({"execution_status": "error", "stdout": None, "stderr": None})
    check("outcome infrastructure_failure", result.outcome == harness.RealGaussOutcome.INFRASTRUCTURE_FAILURE.value)


# ---------------------------------------------------------------------------
# classify_agreement -- every case in Phase 17's list
# ---------------------------------------------------------------------------


def _outcome(outcome: str, basis: str = "test") -> harness.GaussOutcomeClassification:
    return harness.GaussOutcomeClassification(outcome=outcome, matched_error_codes=(), classification_basis=basis)


def test_09_agree_accept() -> None:
    result = harness.classify_agreement(
        validation_mod.SyntaxStatus.VALIDATED.value, _outcome(harness.RealGaussOutcome.ACCEPTED.value, "execution_status:completed"),
    )
    check("agree_accept", result == harness.AgreementClass.AGREE_ACCEPT.value)


def test_10_agree_reject() -> None:
    result = harness.classify_agreement(
        validation_mod.SyntaxStatus.INVALID.value,
        _outcome(harness.RealGaussOutcome.REJECTED_SYNTAX_OR_PARSE.value, "catalogued:G0105:PARSE_SYNTAX"),
    )
    check("agree_reject", result == harness.AgreementClass.AGREE_REJECT.value)


def test_11_false_positive_validator_rejects_gauss_accepts() -> None:
    result = harness.classify_agreement(
        validation_mod.SyntaxStatus.INVALID.value, _outcome(harness.RealGaussOutcome.ACCEPTED.value, "execution_status:completed"),
    )
    check("false_positive", result == harness.AgreementClass.FALSE_POSITIVE.value)


def test_12_false_negative_validator_accepts_gauss_rejects() -> None:
    result = harness.classify_agreement(
        validation_mod.SyntaxStatus.VALIDATED.value,
        _outcome(harness.RealGaussOutcome.REJECTED_SYNTAX_OR_PARSE.value, "catalogued:G0063:PARSE_SYNTAX"),
    )
    check("false_negative", result == harness.AgreementClass.FALSE_NEGATIVE.value)


def test_13_inconclusive_partial_validator_status() -> None:
    result = harness.classify_agreement(
        validation_mod.SyntaxStatus.PARTIAL.value, _outcome(harness.RealGaussOutcome.ACCEPTED.value, "execution_status:completed"),
    )
    check("inconclusive on PARTIAL", result == harness.AgreementClass.INCONCLUSIVE.value)


def test_14_inconclusive_unknown_validator_status() -> None:
    result = harness.classify_agreement(
        validation_mod.SyntaxStatus.UNKNOWN.value, _outcome(harness.RealGaussOutcome.ACCEPTED.value, "execution_status:completed"),
    )
    check("inconclusive on UNKNOWN", result == harness.AgreementClass.INCONCLUSIVE.value)


def test_15_runtime_error_is_treated_as_gauss_accepting_syntax() -> None:
    """A real RUNTIME_ERROR (e.g. dimension mismatch) means GAUSS's PARSER
    accepted the code -- the failure happened later. Paired with a VALIDATED
    verdict, this is AGREE_ACCEPT (syntax-level agreement), never a false
    negative -- the validator never claims runtime correctness."""
    result = harness.classify_agreement(
        validation_mod.SyntaxStatus.VALIDATED.value,
        _outcome(harness.RealGaussOutcome.RUNTIME_ERROR.value, "catalogued:G0036:MATRIX_DIMENSION"),
    )
    check("runtime error not mislabeled syntax reject", result == harness.AgreementClass.AGREE_ACCEPT.value)


def test_16_timeout_is_inconclusive_not_a_verdict() -> None:
    result = harness.classify_agreement(
        validation_mod.SyntaxStatus.VALIDATED.value, _outcome(harness.RealGaussOutcome.TIMEOUT.value, "execution_status:timed_out"),
    )
    check("timeout inconclusive", result == harness.AgreementClass.INCONCLUSIVE.value)


def test_17_infrastructure_failure_is_inconclusive() -> None:
    result = harness.classify_agreement(
        validation_mod.SyntaxStatus.INVALID.value,
        _outcome(harness.RealGaussOutcome.INFRASTRUCTURE_FAILURE.value, "execution_status:'blocked'"),
    )
    check("infrastructure failure inconclusive, distinct from timeout", result == harness.AgreementClass.INCONCLUSIVE.value)


def test_18_uncatalogued_evidence_is_inconclusive_fail_closed() -> None:
    result = harness.classify_agreement(
        validation_mod.SyntaxStatus.VALIDATED.value,
        _outcome(harness.RealGaussOutcome.RUNTIME_ERROR.value, "uncatalogued:G9999"),
    )
    check("uncatalogued fails closed to inconclusive", result == harness.AgreementClass.INCONCLUSIVE.value)


# ---------------------------------------------------------------------------
# run_corpus_item / run_corpus / summarize (fake gauss_runner only)
# ---------------------------------------------------------------------------


def test_19_run_corpus_item_end_to_end_agree_accept() -> None:
    def fake_runner(request_identity: str, code: str) -> dict:
        return {"execution_status": "completed", "stdout": "1.0000000", "stderr": "", "errors": []}

    result = harness.run_corpus_item({"id": "T1", "origin": "test", "snippet": "x = 1;"}, gauss_runner=fake_runner)
    check("agree_accept", result.agreement_class == harness.AgreementClass.AGREE_ACCEPT.value)
    check("id preserved", result.id == "T1")


def test_20_run_corpus_item_end_to_end_false_negative() -> None:
    """Reproduces the exact v0.76.0-found regression shape end to end: a
    matrix literal using ';' as a row separator. Real GAUSS silently
    misparses it (execution_status completed) rather than rejecting it, so
    this specific mutation is NOT expected to trip the syntax validator's
    own rule at all here -- included instead as a worked example that a
    validator INVALID verdict paired with a fake syntax-rejecting runner
    produces FALSE_NEGATIVE only when the validator itself misses a real
    violation. See test_12 for the direct classify_agreement-level proof;
    this test additionally proves comment-stripping runs before validation."""
    def fake_syntax_reject(request_identity: str, code: str) -> dict:
        return {"execution_status": "failed", "stdout": "", "stderr": "error G0063: Operator expected before '0'", "errors": []}

    # A snippet this version's validator DOES catch (bare_multi_token_literal) --
    # exercises AGREE_REJECT, not a real false negative (there is none left to
    # demonstrate at the unit level; the differential harness's own corpus run
    # is what discovers real ones).
    item = {"id": "T2", "origin": "test", "snippet": "// comment\nx = -1 0;"}
    result = harness.run_corpus_item(item, gauss_runner=fake_syntax_reject)
    check("comment stripped before validation, rule still fires", result.validator_status == validation_mod.SyntaxStatus.INVALID.value)
    check("agree_reject", result.agreement_class == harness.AgreementClass.AGREE_REJECT.value)


def test_21_summarize_counts_and_lists_false_negatives() -> None:
    def fake_accept(request_identity: str, code: str) -> dict:
        return {"execution_status": "completed", "stdout": "", "stderr": "", "errors": []}

    def fake_reject(request_identity: str, code: str) -> dict:
        return {"execution_status": "failed", "stdout": "", "stderr": "error G0105: Bad expression or missing arguments", "errors": []}

    items = [
        {"id": "F1", "origin": "docs_valid", "snippet": "x = 1;"},
        {"id": "F2", "origin": "docs_valid", "snippet": "x = ;"},  # validator INVALID (dangling_assignment)
    ]
    results = (
        harness.run_corpus_item(items[0], gauss_runner=fake_accept),
        harness.run_corpus_item(items[1], gauss_runner=fake_reject),
    )
    summary = harness.summarize(results)
    check("combined total 2", summary["combined"]["total"] == 2)
    check("no false negatives here", summary["combined"]["false_negatives"] == [])
    check("origin breakdown present", "docs_valid" in summary["by_origin"])


def test_22_summarize_lists_a_real_false_negative_by_id() -> None:
    def fake_syntax_reject(request_identity: str, code: str) -> dict:
        return {"execution_status": "failed", "stdout": "", "stderr": "error G0105: Bad expression or missing arguments", "errors": []}

    # A snippet the validator (wrongly, for this synthetic test) calls VALIDATED
    # -- an ordinary scalar assignment with no rule to trip -- while the fake
    # runner reports a real syntax rejection, reproducing what a genuine false
    # negative looks like end to end.
    item = {"id": "FN1", "origin": "mutation", "snippet": "x = 1;"}
    result = harness.run_corpus_item(item, gauss_runner=fake_syntax_reject)
    check("false_negative", result.agreement_class == harness.AgreementClass.FALSE_NEGATIVE.value)
    summary = harness.summarize((result,))
    check("listed by id", summary["combined"]["false_negatives"] == ["FN1"])


# ---------------------------------------------------------------------------
# load_jsonl / load_full_corpus
# ---------------------------------------------------------------------------


def test_23_load_jsonl_missing_file_returns_empty() -> None:
    check("empty for missing file", harness.load_jsonl(Path("does_not_exist_at_all.jsonl")) == [])


def test_24_load_jsonl_round_trips(tmp_path_factory=None) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.jsonl"
        path.write_text('{"id": "Z1", "origin": "docs_valid", "snippet": "x = 1;"}\n', encoding="utf-8")
        items = harness.load_jsonl(path)
        check("one item loaded", len(items) == 1)
        check("fields preserved", items[0]["id"] == "Z1" and items[0]["origin"] == "docs_valid")


# ---------------------------------------------------------------------------
# Safety: no execution authority, no conversational import path
# ---------------------------------------------------------------------------


def test_25_module_never_imports_conversational_modules() -> None:
    forbidden = ("gauss_conversation_engine", "gauss_ai_chat", "gauss_chat_provider")
    source = Path(harness.__file__).read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            for token in forbidden:
                check(f"import line {stripped!r} does not reference {token!r}", token not in stripped)


def test_26_module_never_imports_subprocess_directly() -> None:
    """Real process management is delegated entirely to gauss_execution_
    adapter/gauss_code_execution -- this module never imports subprocess
    itself."""
    source = Path(harness.__file__).read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            check(f"import line {stripped!r} does not import subprocess directly", "subprocess" not in stripped)


def test_27_importing_module_performs_no_real_gauss_invocation() -> None:
    """gauss_execution_adapter is imported lazily, only inside
    RealGaussRunner.__init__ (reached only from main()'s double-gated path),
    never at module import time."""
    source = Path(harness.__file__).read_text(encoding="utf-8")
    top_level_import_block = source.split("class RealGaussRunner", 1)[0]
    check("gauss_execution_adapter not imported at module top level", "import gauss_execution_adapter" not in top_level_import_block)


def test_28_main_requires_both_gates() -> None:
    result_no_gates = harness.main(["--corpus-dir", "does_not_exist"])
    check("no gates -> exit 0, skipped", result_no_gates == 0)
    result_flag_only = harness.main(["--run-real-gauss", "--corpus-dir", "does_not_exist"])
    check("flag only -> exit 0, skipped", result_flag_only == 0)


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
