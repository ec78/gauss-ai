"""Focused unit tests for scripts/gauss_execution_adapter.py (v0.32.0 Phase 3,
Increment 1).

This repository has no pytest configuration anywhere. Following the same
convention as scripts/test_gauss_runtime_orchestration.py and every other
scripts/*.py tool, this file uses a self-contained `check(name, condition)`
harness, run directly:

    python scripts/test_gauss_execution_adapter.py

Every test here uses a fake or stubbed helper callable -- nothing in this
file imports scripts/gauss_code_execution.py, calls load_real_helper(),
launches a subprocess, or invokes GAUSS.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_execution_adapter as ga  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _request(**overrides: Any) -> ga.AdapterRequest:
    defaults: dict[str, Any] = dict(
        request_identity="req-1",
        code="print 1+1;",
        script_path=None,
        working_directory="C:/example/work",
        output_directory=None,
        executable_path="C:/example/gauss26/tgauss.exe",
        gauss_version="GAUSS 26",
        timeout_seconds=30.0,
    )
    defaults.update(overrides)
    return ga.AdapterRequest(**defaults)


def _completed_result(**overrides: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "executed": True,
        "execution_status": "completed",
        "exit_code": 0,
        "stdout": "2",
        "stderr": "",
        "output_files": [],
        "warnings": [],
        "errors": [],
    }
    result.update(overrides)
    return result


def _always_matches(_path: str) -> bool:
    return True


def _never_matches(_path: str) -> bool:
    return False


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


# ---------------------------------------------------------------------------
# 1. Exact request-field projection
# ---------------------------------------------------------------------------


def test_01_exact_field_projection() -> None:
    captured: dict[str, Any] = {}

    def recording_helper(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return _completed_result()

    adapter = ga.GaussExecutionAdapter(helper=recording_helper, environment_probe=_always_matches)
    req = _request(
        working_directory="C:/example/work",
        output_directory="C:/example/work/out",
        executable_path="C:/example/gauss26/tgauss.exe",
        gauss_version="GAUSS 26",
        timeout_seconds=45.0,
        expected_input_files=("a.csv", "b.csv"),
        allow_output_files=False,
    )
    outcome = adapter.invoke(req)
    check("invocation succeeded", outcome.invoked and outcome.execution_status == "completed")
    check("code projected exactly", captured["code"] == "print 1+1;")
    check("script_path projected as None (inline mode)", captured["script_path"] is None)
    check("working_directory projected exactly", captured["working_directory"] == "C:/example/work")
    check("output_directory projected exactly", captured["output_directory"] == "C:/example/work/out")
    check("executable_path projected exactly", captured["executable_path"] == "C:/example/gauss26/tgauss.exe")
    check("gauss_version projected exactly", captured["gauss_version"] == "GAUSS 26")
    check("timeout_seconds projected exactly", captured["timeout_seconds"] == 45.0)
    check("input_files projected as a list", captured["input_files"] == ["a.csv", "b.csv"])
    check("allow_output_files projected exactly", captured["allow_output_files"] is False)


# ---------------------------------------------------------------------------
# 2. Explicit constants
# ---------------------------------------------------------------------------


def test_02_explicit_constants() -> None:
    captured: dict[str, Any] = {}

    def recording_helper(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return _completed_result()

    adapter = ga.GaussExecutionAdapter(helper=recording_helper, environment_probe=_always_matches)
    adapter.invoke(_request())
    check("strict=True always passed", captured["strict"] is True)
    check("allow_network=False always passed", captured["allow_network"] is False)
    check("allow_file_write=False always passed", captured["allow_file_write"] is False)
    check("environment_check_result never passed (explicit path/version used instead)", captured["environment_check_result"] is None)


# ---------------------------------------------------------------------------
# 3. Orchestration-only fields excluded
# ---------------------------------------------------------------------------


def test_03_orchestration_only_fields_excluded() -> None:
    # AdapterRequest structurally has no request_id / execution_purpose /
    # user_confirmed / confirmation_scope / confirmation_timestamp /
    # safety_review fields at all -- this is a static/structural guarantee,
    # not a runtime filter.
    field_names = set(ga.AdapterRequest.__dataclass_fields__.keys())
    excluded = {
        "execution_purpose",
        "user_confirmed",
        "confirmation_scope",
        "confirmation_timestamp",
        "safety_review",
    }
    check("AdapterRequest excludes every orchestration-only field", not (field_names & excluded))


# ---------------------------------------------------------------------------
# 4. Inline-code acceptance
# ---------------------------------------------------------------------------


def test_04_inline_code_accepted() -> None:
    adapter = ga.GaussExecutionAdapter(helper=lambda **_: _completed_result(), environment_probe=_always_matches)
    outcome = adapter.invoke(_request(code="print 42;"))
    check("inline code request is invoked", outcome.invoked)
    check("inline code request completes", outcome.execution_status == "completed")


# ---------------------------------------------------------------------------
# 5 / 6. Script-path rejection / no helper call on preflight rejection
# ---------------------------------------------------------------------------


def test_05_script_path_rejected_before_invocation() -> None:
    calls: list[Any] = []

    def counting_helper(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return _completed_result()

    adapter = ga.GaussExecutionAdapter(helper=counting_helper, environment_probe=_always_matches)
    outcome = adapter.invoke(_request(code=None, script_path="script.gss"))
    check("script-path request is not invoked", not outcome.invoked)
    check(
        "script-path rejection uses SCRIPT_PATH_UNSUPPORTED",
        outcome.failure_category == ga.AdapterFailureCategory.SCRIPT_PATH_UNSUPPORTED,
    )
    check("helper was never called for a script-path request", calls == [])


def test_06_missing_inline_code_rejected_before_invocation() -> None:
    calls: list[Any] = []

    def counting_helper(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return _completed_result()

    adapter = ga.GaussExecutionAdapter(helper=counting_helper, environment_probe=_always_matches)
    outcome = adapter.invoke(_request(code=None, script_path=None))
    check("missing-code request is not invoked", not outcome.invoked)
    check(
        "missing-code rejection uses MISSING_INLINE_CODE",
        outcome.failure_category == ga.AdapterFailureCategory.MISSING_INLINE_CODE,
    )
    check("helper was never called for a missing-code request", calls == [])


# ---------------------------------------------------------------------------
# 7. Environment mismatch
# ---------------------------------------------------------------------------


def test_07_environment_mismatch_blocks_invocation() -> None:
    calls: list[Any] = []

    def counting_helper(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return _completed_result()

    adapter = ga.GaussExecutionAdapter(helper=counting_helper, environment_probe=_never_matches)
    outcome = adapter.invoke(_request())
    check("environment mismatch is not invoked", not outcome.invoked)
    check(
        "environment mismatch uses ENVIRONMENT_MISMATCH",
        outcome.failure_category == ga.AdapterFailureCategory.ENVIRONMENT_MISMATCH,
    )
    check("helper was never called on environment mismatch", calls == [])


# ---------------------------------------------------------------------------
# 8. Executable mismatch (unsupported / GUI executable)
# ---------------------------------------------------------------------------


def test_08_unsupported_executable_rejected() -> None:
    calls: list[Any] = []

    def counting_helper(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return _completed_result()

    adapter = ga.GaussExecutionAdapter(helper=counting_helper, environment_probe=_always_matches)
    outcome = adapter.invoke(_request(executable_path="C:/example/gauss26/gauss.exe"))
    check("GUI executable request is not invoked", not outcome.invoked)
    check(
        "GUI executable rejection uses EXECUTABLE_UNSUPPORTED",
        outcome.failure_category == ga.AdapterFailureCategory.EXECUTABLE_UNSUPPORTED,
    )
    check("helper was never called for a GUI executable", calls == [])


# ---------------------------------------------------------------------------
# 9-15. Fake helper statuses (all seven verified values)
# ---------------------------------------------------------------------------


def test_09_fake_completed_result() -> None:
    adapter = ga.GaussExecutionAdapter(helper=lambda **_: _completed_result(), environment_probe=_always_matches)
    outcome = adapter.invoke(_request())
    check("completed status recognized", outcome.invoked and outcome.execution_status == "completed")
    check("completed result has no adapter-level failure category", outcome.failure_category is None)


def test_10_fake_failed_result() -> None:
    adapter = ga.GaussExecutionAdapter(
        helper=lambda **_: {**_completed_result(), "execution_status": "failed", "exit_code": 1},
        environment_probe=_always_matches,
    )
    outcome = adapter.invoke(_request())
    check("failed status recognized", outcome.invoked and outcome.execution_status == "failed")


def test_11_fake_timeout_result() -> None:
    adapter = ga.GaussExecutionAdapter(
        helper=lambda **_: {**_completed_result(), "execution_status": "timed_out", "exit_code": None},
        environment_probe=_always_matches,
    )
    outcome = adapter.invoke(_request())
    check("timed_out status recognized", outcome.invoked and outcome.execution_status == "timed_out")


def test_12_fake_skipped_result() -> None:
    adapter = ga.GaussExecutionAdapter(
        helper=lambda **_: {**_completed_result(), "execution_status": "skipped", "executed": False},
        environment_probe=_always_matches,
    )
    outcome = adapter.invoke(_request())
    check("skipped status recognized", outcome.invoked and outcome.execution_status == "skipped")


def test_13_fake_blocked_result() -> None:
    adapter = ga.GaussExecutionAdapter(
        helper=lambda **_: {**_completed_result(), "execution_status": "blocked", "executed": False},
        environment_probe=_always_matches,
    )
    outcome = adapter.invoke(_request())
    check("blocked status recognized", outcome.invoked and outcome.execution_status == "blocked")


def test_14_fake_error_result() -> None:
    adapter = ga.GaussExecutionAdapter(
        helper=lambda **_: {**_completed_result(), "execution_status": "error", "executed": False},
        environment_probe=_always_matches,
    )
    outcome = adapter.invoke(_request())
    check("error status recognized", outcome.invoked and outcome.execution_status == "error")


def test_15_fake_unknown_result() -> None:
    adapter = ga.GaussExecutionAdapter(
        helper=lambda **_: {**_completed_result(), "execution_status": "unknown", "executed": False},
        environment_probe=_always_matches,
    )
    outcome = adapter.invoke(_request())
    check("unknown status recognized (as a valid, known 'unknown' value)", outcome.invoked and outcome.execution_status == "unknown")


# ---------------------------------------------------------------------------
# 16. Malformed result
# ---------------------------------------------------------------------------


def test_16_malformed_result() -> None:
    adapter = ga.GaussExecutionAdapter(helper=lambda **_: {"executed": True}, environment_probe=_always_matches)
    outcome = adapter.invoke(_request())
    check("malformed result is invoked but not classified as a status", outcome.invoked and outcome.execution_status is None)
    check(
        "malformed result uses MALFORMED_RESULT",
        outcome.failure_category == ga.AdapterFailureCategory.MALFORMED_RESULT,
    )


# ---------------------------------------------------------------------------
# 17. Schema-validation failure (structural validation at the adapter's own
# boundary -- this module does not import the JSON schema; see
# _is_structurally_valid_result's docstring)
# ---------------------------------------------------------------------------


def test_17_structural_validation_failure_for_bad_output_files_shape() -> None:
    bad_result = {**_completed_result(), "output_files": "not-a-list"}
    adapter = ga.GaussExecutionAdapter(helper=lambda **_: bad_result, environment_probe=_always_matches)
    outcome = adapter.invoke(_request())
    check(
        "malformed output_files shape is flagged, not passed through",
        outcome.failure_category == ga.AdapterFailureCategory.MALFORMED_RESULT,
    )

    unknown_status_result = {**_completed_result(), "execution_status": "not_a_real_status"}
    adapter2 = ga.GaussExecutionAdapter(helper=lambda **_: unknown_status_result, environment_probe=_always_matches)
    outcome2 = adapter2.invoke(_request(request_identity="req-unknown-status"))
    check(
        "an invented/unrecognized status is flagged as UNKNOWN_HELPER_STATUS, not silently accepted",
        outcome2.failure_category == ga.AdapterFailureCategory.UNKNOWN_HELPER_STATUS,
    )


# ---------------------------------------------------------------------------
# 18. Output metadata retained as metadata only
# ---------------------------------------------------------------------------


def test_18_output_metadata_is_not_file_content() -> None:
    adapter = ga.GaussExecutionAdapter(
        helper=lambda **_: _completed_result(
            output_files=[{"path": "results.csv", "size_bytes": 42, "file_type": "text/csv"}]
        ),
        environment_probe=_always_matches,
    )
    outcome = adapter.invoke(_request())
    assert outcome.raw_result is not None
    entry = outcome.raw_result["output_files"][0]
    check("output metadata has no content key", "content" not in entry)

    result_with_content = _completed_result(output_files=[{"path": "x.csv", "content": "a,b\n1,2\n"}])
    adapter2 = ga.GaussExecutionAdapter(helper=lambda **_: result_with_content, environment_probe=_always_matches)
    outcome2 = adapter2.invoke(_request(request_identity="req-content-guard"))
    check(
        "a raw result carrying file content in output_files is flagged malformed",
        outcome2.failure_category == ga.AdapterFailureCategory.MALFORMED_RESULT,
    )


# ---------------------------------------------------------------------------
# 19 / 20. Helper called once / duplicate invocation refused
# ---------------------------------------------------------------------------


def test_19_helper_called_exactly_once() -> None:
    calls: list[Any] = []

    def counting_helper(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return _completed_result()

    adapter = ga.GaussExecutionAdapter(helper=counting_helper, environment_probe=_always_matches)
    adapter.invoke(_request())
    check("helper called exactly once", len(calls) == 1)


def test_20_duplicate_invocation_refused() -> None:
    calls: list[Any] = []

    def counting_helper(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return _completed_result()

    adapter = ga.GaussExecutionAdapter(helper=counting_helper, environment_probe=_always_matches)
    req = _request()
    adapter.invoke(req)
    second_outcome = adapter.invoke(req)
    check("second invocation for the same request_identity is refused", not second_outcome.invoked)
    check(
        "second invocation uses DUPLICATE_INVOCATION",
        second_outcome.failure_category == ga.AdapterFailureCategory.DUPLICATE_INVOCATION,
    )
    check("the helper itself was still only called once", len(calls) == 1)


# ---------------------------------------------------------------------------
# 21. No automatic retry
# ---------------------------------------------------------------------------


def test_21_no_automatic_retry() -> None:
    calls: list[Any] = []

    def failing_then_ok_helper(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {**_completed_result(), "execution_status": "failed", "exit_code": 1}

    adapter = ga.GaussExecutionAdapter(helper=failing_then_ok_helper, environment_probe=_always_matches)
    outcome = adapter.invoke(_request())
    check("failed result is returned, not retried", outcome.execution_status == "failed")
    check("helper called exactly once despite failure (no retry loop)", len(calls) == 1)
    check("GaussExecutionAdapter exposes no retry/rerun method", not hasattr(adapter, "retry") and not hasattr(adapter, "rerun"))


# ---------------------------------------------------------------------------
# 22. Helper exception mapped distinctly
# ---------------------------------------------------------------------------


def test_22_helper_exception_mapped_distinctly() -> None:
    def raising_helper(**kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("simulated: the process could not be launched")

    adapter = ga.GaussExecutionAdapter(helper=raising_helper, environment_probe=_always_matches)
    outcome = adapter.invoke(_request())
    check("a raised exception does not crash invoke()", outcome.invoked)
    check(
        "helper exception uses HELPER_LAUNCH_EXCEPTION, distinct from MALFORMED_RESULT",
        outcome.failure_category == ga.AdapterFailureCategory.HELPER_LAUNCH_EXCEPTION,
    )
    check(
        "HELPER_LAUNCH_EXCEPTION is a distinct enum member from MALFORMED_RESULT",
        ga.AdapterFailureCategory.HELPER_LAUNCH_EXCEPTION != ga.AdapterFailureCategory.MALFORMED_RESULT,
    )


# ---------------------------------------------------------------------------
# 23. Raw result preserved without rewriting it
# ---------------------------------------------------------------------------


def test_23_raw_result_preserved_unmodified() -> None:
    original = _completed_result(stdout="exact original text", output_files=[{"path": "a.csv", "size_bytes": 1}])
    adapter = ga.GaussExecutionAdapter(helper=lambda **_: original, environment_probe=_always_matches)
    outcome = adapter.invoke(_request())
    check("raw_result is the exact object the helper returned", outcome.raw_result is original)
    check("stdout is not rewritten", outcome.raw_result["stdout"] == "exact original text")


# ---------------------------------------------------------------------------
# 24. Safe summary excludes code and secrets
# ---------------------------------------------------------------------------


def test_24_safe_summary_excludes_code_and_secrets() -> None:
    adapter = ga.GaussExecutionAdapter(helper=lambda **_: _completed_result(), environment_probe=_always_matches)
    req = _request(code="print secret_password_value;")
    outcome = adapter.invoke(req)
    summary = ga.safe_summary(req, outcome)
    serialized = str(summary)
    check("safe summary excludes the inline code text", "secret_password_value" not in serialized)
    check("safe summary has no 'code' key", "code" not in summary)
    check(
        "safe summary has no 'secret'/'credential'/'password' keys",
        not any(k for k in summary if any(t in k.lower() for t in ("secret", "credential", "password"))),
    )


# ---------------------------------------------------------------------------
# 25. No methodology-validity claim anywhere in the data model (structural)
# ---------------------------------------------------------------------------


def test_25_no_methodology_validity_claim_in_data_model() -> None:
    request_fields = set(ga.AdapterRequest.__dataclass_fields__.keys())
    outcome_fields = set(ga.AdapterOutcome.__dataclass_fields__.keys())
    suspicious_terms = {"methodology", "statistically_valid", "correct", "trustworthy_result"}
    found = {f for f in request_fields | outcome_fields if any(t in f.lower() for t in suspicious_terms)}
    check("no methodology/validity-claiming field exists in the adapter's data model", not found)


# ---------------------------------------------------------------------------
# 26. Module import has no execution side effects (no real helper import)
# ---------------------------------------------------------------------------


def test_26_module_import_has_no_real_helper_side_effects() -> None:
    check(
        "gauss_code_execution is not imported as a module-level name in gauss_execution_adapter",
        "gauss_code_execution" not in dir(ga) or ga.__dict__.get("gauss_code_execution") is None,
    )
    check("load_real_helper exists as an explicit, separate factory", callable(ga.load_real_helper))


# ---------------------------------------------------------------------------
# 27. Missing package context fails closed
# ---------------------------------------------------------------------------


def test_27_missing_package_context_fails_closed() -> None:
    calls: list[Any] = []

    def counting_helper(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return _completed_result()

    adapter = ga.GaussExecutionAdapter(helper=counting_helper, environment_probe=_always_matches)
    outcome = adapter.invoke(_request(required_packages=("tsmt",), package_inspection_result=None))
    check("missing package context is not invoked", not outcome.invoked)
    check(
        "missing package context uses MISSING_PACKAGE_CONTEXT",
        outcome.failure_category == ga.AdapterFailureCategory.MISSING_PACKAGE_CONTEXT,
    )
    check("helper never called without package context", calls == [])


# ---------------------------------------------------------------------------
# Production-boundary tests (v0.32.0 Phase 3, Increment 3). These prove the
# production helper-loading path is explicit, honest on failure, and never
# auto-selected -- WITHOUT ever calling the real execute_gauss_code(...)
# that load_real_helper() resolves. Merely importing scripts/gauss_code_execution.py
# (which these tests do, exactly once, via the one sanctioned factory) is
# safe: that module defines functions at import time and does not run GAUSS,
# detect an environment, or launch a subprocess just by being imported --
# confirmed by direct inspection of its own module-level code (only
# `import gauss_environment_check` inside a try/except, itself also
# import-only). Calling the *returned* callable is what would run GAUSS,
# and none of these tests do that.
# ---------------------------------------------------------------------------


def test_28_load_real_helper_is_explicit_and_returns_the_real_callable() -> None:
    real_helper = ga.load_real_helper()
    check("load_real_helper() returns a callable", callable(real_helper))

    import gauss_code_execution as direct_import  # only to compare identity, never called

    check(
        "load_real_helper() returns the exact execute_gauss_code function object",
        real_helper is direct_import.execute_gauss_code,
    )
    check(
        "GaussExecutionAdapter's own construction never calls load_real_helper() itself",
        "load_real_helper" not in ga.GaussExecutionAdapter.__init__.__code__.co_names,
    )


def test_29_missing_helper_dependency_fails_honestly() -> None:
    sentinel_absent = object()
    previous = sys.modules.get("gauss_code_execution", sentinel_absent)
    # A None entry in sys.modules is Python's own documented mechanism for
    # "this module is known to be unimportable" -- simulating a missing
    # dependency without touching the real file on disk.
    sys.modules["gauss_code_execution"] = None  # type: ignore[assignment]
    try:
        raised = False
        try:
            ga.load_real_helper()
        except ImportError as exc:
            raised = True
            check(
                "the honest failure message names the missing dependency",
                "gauss_code_execution" in str(exc),
            )
        check("a missing helper dependency raises ImportError rather than failing silently", raised)
    finally:
        if previous is sentinel_absent:
            sys.modules.pop("gauss_code_execution", None)
        else:
            sys.modules["gauss_code_execution"] = previous


def test_30_no_implicit_fallback_to_a_real_helper() -> None:
    check_raises_typeerror = False
    try:
        ga.GaussExecutionAdapter()  # type: ignore[call-arg]
    except TypeError:
        check_raises_typeerror = True
    check(
        "constructing a GaussExecutionAdapter without an explicit helper is a TypeError "
        "(no default/implicit real-helper fallback exists)",
        check_raises_typeerror,
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


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
            _failures.append(f"{name} raised an unexpected exception: {type(exc).__name__}: {exc}")
        if len(_failures) == before:
            print(f"PASS  {name}")
        else:
            for f in _failures[before:]:
                print(f"FAIL  {name}: {f}")

    print()
    print(f"{len(tests)} test function(s) run, {len(_failures)} check failure(s).")
    if _failures:
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
