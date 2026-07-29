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
