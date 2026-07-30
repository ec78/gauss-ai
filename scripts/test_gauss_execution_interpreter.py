"""Tests for deterministic execution-result interpretation.

Run with:

    python scripts/test_gauss_execution_interpreter.py

No test launches GAUSS, reads workspace files, edits code, or retries
execution. The interpreter consumes already-captured evidence only.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_error_catalog as catalog  # noqa: E402
import gauss_execution_interpreter as interp  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _evidence(**overrides: object) -> interp.ExecutionEvidence:
    values = {
        "runner": "REAL_GAUSS",
        "gauss_ran": True,
        "executed": True,
        "execution_status": "completed",
        "exit_code": 0,
        "stdout_chars": 10,
        "stderr_chars": 0,
        "timed_out": False,
        "stdout_text": "4.0000000\n",
        "stderr_text": "",
    }
    values.update(overrides)
    return interp.ExecutionEvidence(**values)


def test_01_catalog_lookup_known_error() -> None:
    entry = catalog.lookup_error("g0105")
    check("G0105 is cataloged", entry is not None)
    assert entry is not None
    check("G0105 is syntax category", entry.category == catalog.GaussErrorCategory.PARSE_SYNTAX)
    check("known codes include G0036", "G0036" in catalog.known_error_codes())


def test_02_successful_execution() -> None:
    result = interp.interpret_execution(_evidence())
    check("success completes", result.completion_status == "completed")
    check("success has no failure type", result.failure_type is None)
    check("success does not require action", not result.requires_user_action)
    check("success safe to continue", result.safe_to_continue)
    check("success does not validate methodology", "statistical" not in result.user_explanation.lower())


def test_03_syntax_error() -> None:
    result = interp.interpret_execution(
        _evidence(
            execution_status="failed",
            stdout_text="Program execute failed\n",
            stderr_text="error G0105 : Bad expression or missing arguments\n",
        )
    )
    check("syntax error code preserved", result.error_code == "G0105")
    check("syntax category", result.failure_type == catalog.GaussErrorCategory.PARSE_SYNTAX.value)
    check("syntax phase", result.execution_phase == "parsing")
    check("syntax explanation names parsing", "parsing" in result.user_explanation.lower())


def test_04_runtime_matrix_error() -> None:
    result = interp.interpret_execution(
        _evidence(
            execution_status="failed",
            stdout_text="Program execute failed\n",
            stderr_text="error G0036 : Matrix dimensions are incompatible\n",
        )
    )
    check("runtime code preserved", result.error_code == "G0036")
    check("runtime matrix category", result.failure_type == catalog.GaussErrorCategory.MATRIX_DIMENSION.value)
    check("runtime phase", result.execution_phase == "runtime")
    check("matrix explanation", "matrix dimensions" in result.user_explanation.lower())


def test_05_timeout() -> None:
    result = interp.interpret_execution(_evidence(execution_status="timed_out", timed_out=True))
    check("timeout phase", result.execution_phase == "timeout")
    check("timeout category", result.failure_type == catalog.GaussErrorCategory.TIMEOUT.value)
    check("timeout not safe", not result.safe_to_continue)


def test_06_blocked_execution() -> None:
    result = interp.interpret_execution(
        _evidence(
            runner="REAL_GAUSS",
            gauss_ran=False,
            executed=False,
            execution_status=None,
            exit_code=None,
            stdout_text=None,
            stderr_text=None,
            metadata_error="missing terminal executable",
        )
    )
    check("blocked pre launch", result.execution_phase == "pre_launch")
    check("blocked launch status", result.launch_status == "blocked_before_launch")
    check("blocked requires action", result.requires_user_action)


def test_07_unknown_failure_without_streams() -> None:
    result = interp.interpret_execution(
        _evidence(execution_status="failed", stdout_text=None, stderr_text=None, stderr_chars=100)
    )
    check("unknown failure low confidence", result.confidence == "low")
    check("unknown failure category", result.failure_type == catalog.GaussErrorCategory.UNKNOWN.value)
    check("missing stderr disclosed", any("stderr text was not supplied" in x for x in result.evidence_limitations))


def test_08_unknown_gauss_error_code() -> None:
    result = interp.interpret_execution(
        _evidence(execution_status="failed", stderr_text="error G9999 : Newly observed error\n")
    )
    check("unknown code preserved", result.error_code == "G9999")
    check("unknown code stays unknown", result.error_category == catalog.GaussErrorCategory.UNKNOWN.value)
    check("unknown avoids speculation", "not yet in the local deterministic catalog" in result.user_explanation)


def test_09_fake_execution_success() -> None:
    result = interp.interpret_execution(
        _evidence(runner="FAKE", gauss_ran=False, execution_status="completed", stdout_text="fake runner completed\n")
    )
    check("fake success classified completed", result.completion_status == "completed")
    check("fake launch label", result.launch_status == "fake_or_non_gauss_runner")


def test_10_truthfulness_no_repair_language() -> None:
    result = interp.interpret_execution(
        _evidence(execution_status="failed", stderr_text="error G0036 : Matrix dimensions are incompatible\n")
    )
    text = "\n".join(
        [
            result.summary,
            result.user_explanation,
            result.technical_explanation,
            result.next_step,
            result.likely_location or "",
        ]
    ).lower()
    check("does not claim a line", "line " not in text)
    check("does not propose code change", "rewrite" not in text and "change the code" not in text)
    check("does not infer model validity", "hypothesis" not in text and "methodology" not in text)


def test_11_catalog_entries_have_verification_metadata() -> None:
    for entry in catalog.catalog_entries():
        check(f"{entry.error_code} declares at least one verification_status", len(entry.verification_status) > 0)
        check(f"{entry.error_code} declares a non-empty verification_source", bool(entry.verification_source and entry.verification_source.strip()))


def test_12_duplicate_error_code_detected() -> None:
    duplicate = (
        catalog.lookup_error("G0105"),
        catalog.lookup_error("G0105"),
    )
    assert duplicate[0] is not None and duplicate[1] is not None
    try:
        catalog._build_catalog(duplicate)  # noqa: SLF001 - intentionally exercising the internal guard
        _failures.append("duplicate error codes should raise ValueError but did not")
    except ValueError as exc:
        check("duplicate detection names the offending code", "G0105" in str(exc))


def test_13_new_verified_codes_present() -> None:
    codes = catalog.known_error_codes()
    check("G0014 is cataloged", "G0014" in codes)
    check("G0290 is cataloged", "G0290" in codes)
    file_not_found = catalog.lookup_error("G0014")
    library_not_found = catalog.lookup_error("G0290")
    assert file_not_found is not None and library_not_found is not None
    check("G0014 is file_io category", file_not_found.category == catalog.GaussErrorCategory.FILE_IO)
    check("G0290 is package_or_library category", library_not_found.category == catalog.GaussErrorCategory.PACKAGE_OR_LIBRARY)


def test_14_verification_status_surfaced_through_interpreter() -> None:
    result = interp.interpret_execution(
        _evidence(execution_status="failed", stderr_text="error G0105 : Bad expression or missing arguments\n")
    )
    check("verification_status surfaced", len(result.verification_status) > 0)
    check("real_runtime present for G0105", "real_runtime" in result.verification_status)
    check("official_documentation present for G0105", "official_documentation" in result.verification_status)
    check("verification_source surfaced", result.verification_source is not None)


def test_15_documentation_discrepancy_surfaced_for_g0036() -> None:
    result = interp.interpret_execution(
        _evidence(execution_status="failed", stderr_text="error G0036 : Matrix dimensions are incompatible\n")
    )
    check("documentation_discrepancy is surfaced for G0036", result.documentation_discrepancy is not None)
    assert result.documentation_discrepancy is not None
    check("discrepancy names the documented wording", "not conformable" in result.documentation_discrepancy.lower())
    check(
        "runtime wording still used for the user-facing explanation",
        "incompatible" in result.user_explanation.lower(),
    )


def test_16_g0014_file_not_found_interpreted() -> None:
    result = interp.interpret_execution(
        _evidence(execution_status="failed", stderr_text="error G0014 : File not found 'data.txt', line 3\n")
    )
    check("G0014 code preserved", result.error_code == "G0014")
    check("G0014 category", result.failure_type == catalog.GaussErrorCategory.FILE_IO.value)
    check("G0014 does not claim a specific fix", "rename" not in result.next_step.lower())


def test_17_g0290_library_not_found_interpreted() -> None:
    result = interp.interpret_execution(
        _evidence(execution_status="failed", stderr_text="error G0290 : Library not found\n")
    )
    check("G0290 code preserved", result.error_code == "G0290")
    check("G0290 category", result.failure_type == catalog.GaussErrorCategory.PACKAGE_OR_LIBRARY.value)
    check("G0290 phase is startup", result.execution_phase == "startup")
    check("G0290 is documentation-only verified", result.verification_status == ("official_documentation",))


def test_18_timeout_wording_distinguishes_simulated_from_observed() -> None:
    observed = interp.interpret_execution(
        _evidence(runner="REAL_GAUSS", gauss_ran=True, execution_status="timed_out", timed_out=True)
    )
    simulated = interp.interpret_execution(
        _evidence(runner="FAKE", gauss_ran=False, execution_status="timed_out", timed_out=True)
    )
    check("observed timeout reports a real launch", observed.launch_status == "launched")
    check("observed timeout wording implies a real process", "gauss was launched" in observed.user_explanation.lower())
    check("simulated timeout does not claim a real launch", simulated.launch_status == "fake_or_non_gauss_runner")
    check(
        "simulated timeout wording explicitly disclaims a real launch",
        "simulated" in simulated.user_explanation.lower() or "injected" in simulated.user_explanation.lower(),
    )
    check("simulated timeout wording differs from observed timeout wording", simulated.user_explanation != observed.user_explanation)


def test_19_unknown_code_still_unknown_with_expanded_catalog() -> None:
    result = interp.interpret_execution(
        _evidence(execution_status="failed", stderr_text="error G9999 : Newly observed error\n")
    )
    check("G9999 remains uncataloged after catalog expansion", result.error_category == catalog.GaussErrorCategory.UNKNOWN.value)
    check("G9999 carries no verification metadata", result.verification_status == ())


def test_20_no_hardcoded_error_knowledge_outside_catalog() -> None:
    source = Path(interp.__file__).read_text(encoding="utf-8")
    check(
        "interpreter source contains no literal GAUSS error-code strings outside the catalog import",
        not any(code in source for code in catalog.known_error_codes()),
    )


def run_tests() -> int:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        before = len(_failures)
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _failures.append(f"{name} raised an unexpected exception: {type(exc).__name__}: {exc}")
        if len(_failures) == before:
            print(f"PASS  {name}")
        else:
            for failure in _failures[before:]:
                print(f"FAIL  {name}: {failure}")
    print()
    print(f"{len(tests)} test function(s) run, {len(_failures)} check failure(s).")
    if _failures:
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
