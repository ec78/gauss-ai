"""Focused unit tests for scripts/gauss_runtime_orchestration.py (v0.31.0
Phase 2, extended in v0.32.0 Phase 3 Increment 1 with AdapterRunner
integration tests).

This repository has no pytest configuration anywhere (no pyproject.toml,
setup.py/cfg, pytest.ini, or conftest.py, and pytest is not installed in the
development environment used for this project). The established, actual
testing convention -- used consistently by scripts/gauss_code_execution.py,
scripts/gauss_environment_check.py, and scripts/gauss_package_inspection.py
-- is a self-contained `check(name, condition)` harness runnable directly as
a script, with no external test framework dependency. This file follows that
same convention, run directly:

    python scripts/test_gauss_runtime_orchestration.py

Tests 1-40 use only the mock/fake runner boundary directly. Tests 41-60
additionally exercise `orch.AdapterRunner` bridging a
`gauss_execution_adapter.GaussExecutionAdapter` -- but every one of those
still uses a fake helper callable, exactly like every other test in this
file. Tests 61-63 (v0.33.0) and 64-70/renumbered-87 (v0.34.0, extended
v0.35.0) structurally verify `build_production_adapter_runner(...)`'s
isolation and lock in real-observed evidence as fake-shaped regression
fixtures. Tests 71-86 (v0.35.0) cover reliability across repeated
independent requests, output-file creation/missing-output handling
(including a regression test for a real bug found and fixed during v0.35.0's
own real-invocation testing -- see `_missing_expected_outputs` in
gauss_runtime_orchestration.py), and duplicate-identity/state-isolation
guarantees. Nothing in this file imports scripts/gauss_code_execution.py,
calls gauss_execution_adapter.load_real_helper(), launches a subprocess, or
invokes GAUSS -- test_87 asserts this directly.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_execution_adapter as ga  # noqa: E402
import gauss_runtime_orchestration as orch  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _env(*, executable_path: str = "C:/example/gauss26/tgauss.exe") -> orch.EnvironmentSummary:
    return orch.EnvironmentSummary(
        executable_path=executable_path,
        gauss_version="GAUSS 26",
        platform="Windows",
        detection_provenance="direct",
    )


def _passing_safety() -> orch.SafetyReviewOutcome:
    return orch.SafetyReviewOutcome(
        outcome="pass",
        items=(
            orch.SafetyReviewItem("code_shown", True),
            orch.SafetyReviewItem("no_delete", True),
            orch.SafetyReviewItem("terminal_executable", True),
            orch.SafetyReviewItem("timeout_set", True),
        ),
    )


def _failing_safety() -> orch.SafetyReviewOutcome:
    return orch.SafetyReviewOutcome(
        outcome="fail",
        items=(orch.SafetyReviewItem("writes_outside_directory", False),),
    )


def _inline_draft(
    *,
    request_id: str = "req-1",
    code: str = "print 1+1;",
    working_directory: str = "C:/example/work",
    executable_path: str = "C:/example/gauss26/tgauss.exe",
    timeout_seconds: float = 30.0,
    expected_output_files: tuple[str, ...] = (),
    execution_purpose: str = "smoke test",
    safety_review: orch.SafetyReviewOutcome | None = None,
    environment_summary: orch.EnvironmentSummary | None = None,
) -> orch.RequestDraft:
    return orch.RequestDraft(
        request_id=request_id,
        code=code,
        working_directory=working_directory,
        executable_path=executable_path,
        timeout_seconds=timeout_seconds,
        expected_output_files=expected_output_files,
        execution_purpose=execution_purpose,
        environment_summary=environment_summary or _env(),
        safety_review=safety_review or _passing_safety(),
    )


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


def _fully_confirmed_instance(
    *, draft: orch.RequestDraft | None = None, session_id: str = "s1"
) -> orch.MockOrchestrationInstance:
    inst = orch.MockOrchestrationInstance(session_id=session_id, draft=draft or _inline_draft())
    inst.submit_for_review()
    inst.display_plan()
    assert inst.request is not None
    inst.confirm(
        orch.ConfirmationEvent(scope=inst.request.request_hash, timestamp="t1", session_id=session_id)
    )
    return inst


def _adapter_runner(
    inst: orch.MockOrchestrationInstance,
    helper: Any,
    *,
    environment_probe: Any = lambda _p: True,
) -> orch.AdapterRunner:
    """Builds a v0.32.0 Increment-1 AdapterRunner wrapping a fake helper --
    never the real scripts/gauss_code_execution.py -- bound to this
    instance's confirmed request_hash."""
    assert inst.request is not None
    adapter = ga.GaussExecutionAdapter(helper=helper, environment_probe=environment_probe)
    return orch.AdapterRunner(adapter, request_identity=inst.request.request_hash)


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def check_raises(name: str, exc_type: type[BaseException], fn, *args: Any, **kwargs: Any) -> None:
    try:
        fn(*args, **kwargs)
        _failures.append(f"{name} (expected {exc_type.__name__}, nothing was raised)")
    except exc_type:
        pass
    except Exception as exc:  # noqa: BLE001
        _failures.append(f"{name} (expected {exc_type.__name__}, got {type(exc).__name__}: {exc})")


# ---------------------------------------------------------------------------
# 1. Valid inline-code request normalization
# ---------------------------------------------------------------------------


def test_01_inline_code_normalization() -> None:
    draft_crlf = _inline_draft(code="print 1+1;\r\nprint 2+2;\r\n")
    draft_lf = _inline_draft(code="print 1+1;\nprint 2+2;\n")
    req_crlf = orch.build_canonical_request(draft_crlf)
    req_lf = orch.build_canonical_request(draft_lf)
    check("normalization: display text preserved verbatim", req_crlf.code == "print 1+1;\r\nprint 2+2;\r\n")
    check("normalization: CRLF/LF-only difference hashes identically", req_crlf.request_hash == req_lf.request_hash)


# ---------------------------------------------------------------------------
# 2. Deterministic hashing
# ---------------------------------------------------------------------------


def test_02_deterministic_hashing() -> None:
    req1 = orch.build_canonical_request(_inline_draft())
    req2 = orch.build_canonical_request(_inline_draft())
    check("same draft content hashes identically across builds", req1.request_hash == req2.request_hash)
    check("hash is a nonempty hex string", bool(req1.request_hash) and all(c in "0123456789abcdef" for c in req1.request_hash))


# ---------------------------------------------------------------------------
# 3. Hash changes when an included field changes
# ---------------------------------------------------------------------------


def test_03_hash_changes_for_included_field() -> None:
    req1 = orch.build_canonical_request(_inline_draft())
    req2 = orch.build_canonical_request(_inline_draft(working_directory="C:/example/other_work"))
    check("changed working_directory produces a different hash", req1.request_hash != req2.request_hash)

    req3 = orch.build_canonical_request(_inline_draft(timeout_seconds=60.0))
    check("changed timeout_seconds produces a different hash", req1.request_hash != req3.request_hash)


# ---------------------------------------------------------------------------
# 4. Hash does not change for presentation-only differences
# ---------------------------------------------------------------------------


def test_04_hash_stable_for_presentation_only_change() -> None:
    req1 = orch.build_canonical_request(_inline_draft(execution_purpose="quick test"))
    req2 = orch.build_canonical_request(_inline_draft(execution_purpose="a totally different label"))
    check("changed execution_purpose does not change the hash", req1.request_hash == req2.request_hash)

    # Reordering a hash-included collection must not change the hash either
    # (canonicalization sorts collections).
    draft_a = _inline_draft()
    draft_a.required_packages = ("pkg_b", "pkg_a")
    draft_b = _inline_draft()
    draft_b.required_packages = ("pkg_a", "pkg_b")
    req_a = orch.build_canonical_request(draft_a)
    req_b = orch.build_canonical_request(draft_b)
    check("reordering required_packages does not change the hash", req_a.request_hash == req_b.request_hash)


# ---------------------------------------------------------------------------
# 5 / 6. Mode exclusivity
# ---------------------------------------------------------------------------


def test_05_both_code_and_script_path_rejected() -> None:
    draft = _inline_draft()
    draft.script_path = "script.gss"
    check_raises("both code and script_path -> RequestValidationError", orch.RequestValidationError, orch.build_canonical_request, draft)


def test_06_neither_code_nor_script_path_rejected() -> None:
    draft = _inline_draft(code=None)
    check_raises("neither code nor script_path -> RequestValidationError", orch.RequestValidationError, orch.build_canonical_request, draft)


# ---------------------------------------------------------------------------
# 7. Script-path request fails closed
# ---------------------------------------------------------------------------


def test_07_script_path_fails_closed() -> None:
    draft = orch.RequestDraft(
        request_id="req-script",
        script_path="script.gss",
        working_directory="C:/example/work",
        executable_path="C:/example/gauss26/tgauss.exe",
        timeout_seconds=30.0,
        environment_summary=_env(),
        safety_review=_passing_safety(),
    )
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=draft)
    inst.submit_for_review()
    check("script-path request is blocked", inst.record.current_state == orch.OrchestrationState.BLOCKED)
    check(
        "script-path block uses SCRIPT_IDENTITY_UNTRUSTED category",
        inst.record.failure_category == orch.FailureCategory.SCRIPT_IDENTITY_UNTRUSTED,
    )


# ---------------------------------------------------------------------------
# 8 / 9. Transition validity
# ---------------------------------------------------------------------------


def test_08_valid_transition_sequence() -> None:
    inst = _fully_confirmed_instance()
    check("full pre-invocation sequence reaches confirmed", inst.record.current_state == orch.OrchestrationState.CONFIRMED)
    inst.invoke(lambda _: _completed_result())
    check("invoke reaches execution_completed", inst.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    inst.begin_analysis(lambda req, res: None)
    check("analysis with no report reaches completed", inst.record.current_state == orch.OrchestrationState.COMPLETED)
    seq = [e.sequence_number for e in inst.record.transition_log]
    check("transition_sequence_number is monotonic", seq == sorted(seq) and len(set(seq)) == len(seq))


def test_09_prohibited_transition_rejected() -> None:
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft())
    check_raises(
        "invoke() from collecting_inputs is rejected",
        orch.InvalidTransitionError,
        inst.invoke,
        lambda _: _completed_result(),
    )


# ---------------------------------------------------------------------------
# 10. Terminal instance cannot be resurrected
# ---------------------------------------------------------------------------


def test_10_terminal_instance_not_resurrected() -> None:
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft())
    inst.cancel()
    check("cancel from collecting_inputs reaches cancelled", inst.record.current_state == orch.OrchestrationState.CANCELLED)
    check_raises("submit_for_review on a cancelled instance is rejected", orch.InvalidTransitionError, inst.submit_for_review)
    check_raises("cancel() again on a terminal instance is rejected", orch.InvalidTransitionError, inst.cancel)


# ---------------------------------------------------------------------------
# 11 / 12. Confirmation scope and insufficiency of user_confirmed alone
# ---------------------------------------------------------------------------


def test_11_confirmation_scope_must_match_hash() -> None:
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft())
    inst.submit_for_review()
    inst.display_plan()
    check_raises(
        "confirm() with wrong scope is rejected",
        orch.ConfirmationScopeMismatchError,
        inst.confirm,
        orch.ConfirmationEvent(scope="not-the-real-hash", timestamp="t1", session_id="s1"),
    )
    check("mismatched confirm() does not accept the request", inst.record.current_state == orch.OrchestrationState.AWAITING_CONFIRMATION)


def test_12_user_confirmed_alone_is_insufficient() -> None:
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft())
    inst.submit_for_review()
    inst.display_plan()
    assert inst.request is not None
    # Bypass attach_confirmation entirely, simulating a hypothetical bug:
    # user_confirmed becomes True without a matching confirmation_scope.
    object.__setattr__(inst.request, "user_confirmed", True)
    inst._transition(orch.OrchestrationState.CONFIRMED, note="artificially forced for this test")
    check_raises(
        "invoke() with user_confirmed=true but no matching scope is rejected",
        orch.GuardFailedError,
        inst.invoke,
        lambda _: _completed_result(),
    )


# ---------------------------------------------------------------------------
# 13. Request change invalidates confirmation
# ---------------------------------------------------------------------------


def test_13_request_change_invalidates_confirmation() -> None:
    req1 = orch.build_canonical_request(_inline_draft(working_directory="C:/example/work"))
    req2 = orch.build_canonical_request(_inline_draft(working_directory="C:/example/different_work"))
    check("changed request has a different hash", req1.request_hash != req2.request_hash)
    check_raises(
        "confirming req2 with req1's hash as scope is rejected",
        orch.ConfirmationScopeMismatchError,
        req2.attach_confirmation,
        confirmation_scope=req1.request_hash,
        confirmation_timestamp="t1",
    )


# ---------------------------------------------------------------------------
# 14. Session mismatch invalidates confirmation
# ---------------------------------------------------------------------------


def test_14_session_mismatch_invalidates_confirmation() -> None:
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft())
    inst.submit_for_review()
    inst.display_plan()
    assert inst.request is not None
    check_raises(
        "confirm() from a different session is rejected",
        orch.SessionMismatchError,
        inst.confirm,
        orch.ConfirmationEvent(scope=inst.request.request_hash, timestamp="t1", session_id="s2"),
    )
    check("session-mismatched confirm() marks confirmation_status stale", inst.record.confirmation_status == orch.ConfirmationStatus.STALE)
    check("session-mismatched confirm() does not accept the request", inst.record.current_state == orch.OrchestrationState.AWAITING_CONFIRMATION)


# ---------------------------------------------------------------------------
# 15 / 16 / 17. Confirmation consumption
# ---------------------------------------------------------------------------


def test_15_confirmation_consumed_on_launch_authorization() -> None:
    inst = _fully_confirmed_instance()
    check("confirmation not yet consumed before invoke()", inst.record.confirmation_consumption_status is False)
    inst.invoke(lambda _: _completed_result())
    check("confirmation consumed after invoke()", inst.record.confirmation_consumption_status is True)
    check("confirmation_status becomes CONSUMED", inst.record.confirmation_status == orch.ConfirmationStatus.CONSUMED)


def test_16_launch_failure_still_consumes_confirmation() -> None:
    inst = _fully_confirmed_instance()

    def failing_runner(_: orch.RunnerInput) -> dict[str, Any]:
        raise RuntimeError("simulated: the process could not be launched")

    inst.invoke(failing_runner)
    check("launch failure still consumes confirmation", inst.record.confirmation_consumption_status is True)
    check("launch failure routes to execution_failed", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check("launch failure category is RUNNER_LAUNCH_FAILURE", inst.record.failure_category == orch.FailureCategory.RUNNER_LAUNCH_FAILURE)


def test_17_pre_invocation_guard_failure_does_not_consume_confirmation() -> None:
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft())
    inst.submit_for_review()
    inst.display_plan()
    assert inst.request is not None
    object.__setattr__(inst.request, "user_confirmed", True)
    inst._transition(orch.OrchestrationState.CONFIRMED, note="artificially forced for this test")
    try:
        inst.invoke(lambda _: _completed_result())
    except orch.GuardFailedError:
        pass
    check("pre-invocation guard failure does not consume confirmation", inst.record.confirmation_consumption_status is False)
    check("pre-invocation guard failure does not record an invocation id", inst.record.helper_invocation_id is None)


# ---------------------------------------------------------------------------
# 18 / 19. Exactly-once invocation
# ---------------------------------------------------------------------------


def test_18_fake_runner_called_exactly_once() -> None:
    calls: list[orch.RunnerInput] = []

    def counting_runner(runner_input: orch.RunnerInput) -> dict[str, Any]:
        calls.append(runner_input)
        return _completed_result()

    inst = _fully_confirmed_instance()
    inst.invoke(counting_runner)
    check("fake runner called exactly once", len(calls) == 1)


def test_19_duplicate_invocation_refused() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: _completed_result())
    # Natural path: the instance has moved on from `confirmed`, so a second
    # invoke() attempt is refused by the ordinary adjacency check.
    check_raises(
        "invoke() again after execution has already occurred is rejected",
        orch.InvalidTransitionError,
        inst.invoke,
        lambda _: _completed_result(),
    )

    # Defense-in-depth path: even if state were artificially reset to
    # `confirmed` (simulating a duplicate-delivery race), the explicit
    # invocation-identity check still refuses a second invocation for the
    # same request_hash.
    object.__setattr__(inst.record, "current_state", orch.OrchestrationState.CONFIRMED)
    check_raises(
        "invoke() refused via the explicit duplicate-invocation-id guard",
        orch.DuplicateInvocationError,
        inst.invoke,
        lambda _: _completed_result(),
    )


# ---------------------------------------------------------------------------
# 20. No automatic retry after failure
# ---------------------------------------------------------------------------


def test_20_no_automatic_retry_after_failure() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: {**_completed_result(), "execution_status": "failed", "exit_code": 1})
    check("failed execution routes to execution_failed", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check_raises(
        "invoke() cannot be called again on a failed instance (no automatic retry)",
        orch.InvalidTransitionError,
        inst.invoke,
        lambda _: _completed_result(),
    )
    check(
        "MockOrchestrationInstance exposes no rerun/retry method",
        not hasattr(inst, "rerun") and not hasattr(inst, "retry"),
    )


# ---------------------------------------------------------------------------
# 21-23. Distinct outcome routing
# ---------------------------------------------------------------------------


def test_21_completed_result_routes_through_analysis_and_reporting() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: _completed_result())
    reported: list[Any] = []
    inst.begin_analysis(lambda req, res: None, report_requested=True, report_hook=lambda status: reported.append(status))
    check("completed + report path reaches completed", inst.record.current_state == orch.OrchestrationState.COMPLETED)
    check("report hook was invoked", len(reported) == 1)
    check("report_status is completed", inst.record.report_status == orch.ReportStatus.COMPLETED)


def test_22_runtime_error_result_routes_distinctly() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: {**_completed_result(), "execution_status": "failed", "exit_code": 1, "stderr": "error G0025"})
    check("runtime error routes to execution_failed", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check("runtime error category is GAUSS_RUNTIME_ERROR", inst.record.failure_category == orch.FailureCategory.GAUSS_RUNTIME_ERROR)


def test_23_timeout_routes_distinctly() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: {**_completed_result(), "execution_status": "timed_out", "exit_code": None})
    check("timeout routes to execution_failed", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check("timeout category is TIMEOUT, distinct from GAUSS_RUNTIME_ERROR", inst.record.failure_category == orch.FailureCategory.TIMEOUT)
    check("TIMEOUT and GAUSS_RUNTIME_ERROR are distinct enum members", orch.FailureCategory.TIMEOUT != orch.FailureCategory.GAUSS_RUNTIME_ERROR)


# ---------------------------------------------------------------------------
# 24. Malformed result never enters normal analysis
# ---------------------------------------------------------------------------


def test_24_malformed_result_never_enters_analysis() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: {"executed": True})  # missing required keys -> malformed
    check("malformed result routes to execution_failed", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check("malformed result category is MALFORMED_RESULT", inst.record.failure_category == orch.FailureCategory.MALFORMED_RESULT)
    check("malformed result clears execution_result_reference", inst.record.execution_result_reference is None)
    check_raises(
        "begin_analysis() on a malformed result is rejected",
        orch.AnalysisNotAllowedError,
        inst.begin_analysis,
        lambda req, res: None,
    )


# ---------------------------------------------------------------------------
# 25. Missing expected output is identified
# ---------------------------------------------------------------------------


def test_25_missing_expected_output_identified() -> None:
    draft = _inline_draft(expected_output_files=("results.csv",))
    inst = _fully_confirmed_instance(draft=draft)
    inst.invoke(lambda _: _completed_result(output_files=[]))
    check("missing expected output still reaches execution_completed", inst.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check("missing expected output sets MISSING_EXPECTED_OUTPUT category", inst.record.failure_category == orch.FailureCategory.MISSING_EXPECTED_OUTPUT)


# ---------------------------------------------------------------------------
# 26. Output metadata is not treated as file content
# ---------------------------------------------------------------------------


def test_26_output_metadata_is_not_file_content() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(
        lambda _: _completed_result(
            output_files=[{"path": "results.csv", "size_bytes": 42, "file_type": "text/csv"}]
        )
    )
    assert inst.record.execution_result_reference is not None
    meta = inst.record.execution_result_reference.output_files[0]
    check("OutputFileMeta has no content attribute at all", not hasattr(meta, "content"))

    validation = orch.validate_fake_result(
        _completed_result(output_files=[{"path": "x.csv", "content": "a,b\n1,2\n"}])
    )
    check("a raw result with file content in output_files is flagged malformed", not validation.is_structurally_valid)


# ---------------------------------------------------------------------------
# 27 / 28. Cancellation
# ---------------------------------------------------------------------------


def test_27_cancellation_before_launch_prevents_invocation() -> None:
    inst = _fully_confirmed_instance()
    inst.cancel()
    check("cancel from confirmed reaches cancelled", inst.record.current_state == orch.OrchestrationState.CANCELLED)
    check_raises("invoke() after pre-launch cancellation is rejected", orch.InvalidTransitionError, inst.invoke, lambda _: _completed_result())


def test_28_cancellation_during_execution_is_disclosed_accurately() -> None:
    inst = _fully_confirmed_instance()

    def runner_that_gets_cancelled(_: orch.RunnerInput) -> dict[str, Any]:
        # Simulate a cancellation request arriving while the (synchronous)
        # call is "in flight" -- the call itself cannot be interrupted, and
        # it still returns a real result, which must be retained honestly.
        inst.cancel(note="user asked to cancel while waiting")
        return _completed_result()

    inst.invoke(runner_that_gets_cancelled)
    check(
        "cancellation during execution is recorded, not silently dropped",
        inst.record.cancellation_status == orch.CancellationStatus.CANCEL_REQUESTED_DURING_INVOCATION,
    )
    check(
        "the late result is still retained and processed (not discarded)",
        inst.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED,
    )
    check(
        "no claim of process termination is made anywhere in the record",
        "terminated" not in inst.record.cancellation_status.value,
    )


# ---------------------------------------------------------------------------
# 29 / 30. Downstream failures preserve evidence
# ---------------------------------------------------------------------------


def test_29_analysis_failure_preserves_execution_evidence() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: _completed_result())
    result_before = inst.record.execution_result_reference
    category_before = inst.record.failure_category

    def failing_analysis(req: Any, res: Any) -> None:
        raise RuntimeError("simulated analysis failure")

    inst.begin_analysis(failing_analysis)
    check("analysis_status is failed", inst.record.analysis_status == orch.AnalysisStatus.FAILED)
    check("execution_result_reference is untouched by analysis failure", inst.record.execution_result_reference is result_before)
    check("failure_category is untouched by analysis failure", inst.record.failure_category == category_before)
    check("instance still reaches completed despite analysis failure", inst.record.current_state == orch.OrchestrationState.COMPLETED)


def test_30_report_failure_preserves_execution_and_analysis_evidence() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: _completed_result())
    inst.begin_analysis(
        lambda req, res: None,
        report_requested=True,
        report_hook=lambda status: (_ for _ in ()).throw(RuntimeError("simulated report failure")),
    )
    check("report_status is failed", inst.record.report_status == orch.ReportStatus.FAILED)
    check("analysis_status remains completed despite report failure", inst.record.analysis_status == orch.AnalysisStatus.COMPLETED)
    check("execution_result_reference remains set despite report failure", inst.record.execution_result_reference is not None)
    check("instance still reaches completed with a fallback", inst.record.current_state == orch.OrchestrationState.COMPLETED)


# ---------------------------------------------------------------------------
# 31. Rerun requires a new request and confirmation
# ---------------------------------------------------------------------------


def test_31_rerun_requires_new_request_and_confirmation() -> None:
    inst1 = _fully_confirmed_instance(draft=_inline_draft(request_id="req-original"))
    inst1.invoke(lambda _: {**_completed_result(), "execution_status": "failed", "exit_code": 1})
    assert inst1.request is not None
    original_hash = inst1.request.request_hash

    # A "rerun" is a wholly new instance/request -- never a mutation of inst1.
    inst2 = _fully_confirmed_instance(draft=_inline_draft(request_id="req-rerun", code="print 1+1; print 3+3;"))
    assert inst2.request is not None
    check("rerun uses a different request_id", inst2.request.request_id != inst1.request.request_id)
    check("rerun uses a different request_hash", inst2.request.request_hash != original_hash)
    check("original instance's state is unaffected by the rerun", inst1.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check(
        "original instance's own object identity never becomes the rerun's request",
        inst1.request is not inst2.request,
    )


# ---------------------------------------------------------------------------
# 32. State loss / incomplete recovered state fails closed
# ---------------------------------------------------------------------------


def test_32_incomplete_recovered_state_fails_closed() -> None:
    # Simulate a "recovered" instance where current_state claims confirmed
    # but no canonical request was ever actually attached (e.g., process
    # restart mid-flow, per state-machine contract Section 15).
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft())
    object.__setattr__(inst.record, "current_state", orch.OrchestrationState.CONFIRMED)
    check("request is genuinely absent on the recovered instance", inst.request is None)
    check_raises(
        "invoke() on incomplete recovered state fails closed",
        orch.GuardFailedError,
        inst.invoke,
        lambda _: _completed_result(),
    )

    inst2 = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft())
    object.__setattr__(inst2.record, "current_state", orch.OrchestrationState.AWAITING_CONFIRMATION)
    check("request is genuinely absent on the second recovered instance", inst2.request is None)
    check_raises(
        "confirm() on incomplete recovered state fails closed",
        orch.GuardFailedError,
        inst2.confirm,
        orch.ConfirmationEvent(scope="anything", timestamp="t1", session_id="s1"),
    )


# ---------------------------------------------------------------------------
# Additional invariant-coverage tests
# ---------------------------------------------------------------------------


def test_33_confirmation_not_reusable_across_requests() -> None:
    """Invariant 7: confirmation cannot be reused across requests."""
    inst_a = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft(request_id="req-a"))
    inst_a.submit_for_review()
    inst_a.display_plan()
    assert inst_a.request is not None
    hash_a = inst_a.request.request_hash

    inst_b = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft(request_id="req-b", code="print 9+9;"))
    inst_b.submit_for_review()
    inst_b.display_plan()

    check_raises(
        "instance B cannot be confirmed using instance A's request_hash",
        orch.ConfirmationScopeMismatchError,
        inst_b.confirm,
        orch.ConfirmationEvent(scope=hash_a, timestamp="t1", session_id="s1"),
    )


def test_34_environment_mismatch_blocks_execution() -> None:
    """Invariant 12: environment mismatch blocks execution."""
    inst = _fully_confirmed_instance()
    inst.check_environment_before_invocation(still_matches=False)
    check("environment mismatch cancels the confirmed instance", inst.record.current_state == orch.OrchestrationState.CANCELLED)
    check("environment mismatch category recorded", inst.record.failure_category == orch.FailureCategory.ENVIRONMENT_MISMATCH)
    check_raises("invoke() after environment mismatch is rejected", orch.InvalidTransitionError, inst.invoke, lambda _: _completed_result())


def test_35_all_failure_categories_distinct() -> None:
    """Invariant 19: all failure categories route distinctly (structural check)."""
    all_categories = list(orch.FailureCategory)
    check("exactly 22 failure categories are defined", len(all_categories) == 22)
    check("all failure category values are unique", len(set(c.value for c in all_categories)) == len(all_categories))


def test_36_no_methodology_validity_claim_anywhere_in_the_record() -> None:
    """Invariant 10 / 20: helper status determines orchestration state only;
    this module makes no methodology/validity claim anywhere in its data
    model (a structural absence check, since no Response Composer exists in
    this phase to make or refuse such a claim in prose)."""
    record_fields = set(orch.OrchestrationRecord.__dataclass_fields__.keys())
    result_fields = set(orch.MockExecutionResult.__dataclass_fields__.keys())
    # "validation_outcome" is a legitimate field (structural/schema
    # validation of the fake result, e.g. required keys present) -- it is
    # deliberately excluded from this check, which looks for a *different*
    # kind of field: one that would claim methodological/statistical
    # validity, which this data model must never contain.
    suspicious_terms = {"methodology", "statistically_valid", "correct", "trustworthy_result"}
    found = {f for f in record_fields | result_fields if any(t in f.lower() for t in suspicious_terms)}
    check("no methodology/validity-claiming field exists in the data model", not found)


def test_37_script_identity_untrusted_guard_is_conservative() -> None:
    """Invariant 13: ambiguous script identity blocks execution unless a
    later approved policy resolves it -- this module implements no such
    policy, so script-path mode is unconditionally blocked."""
    for script_path in ("script.gss", "C:/example/work/script.gss", "../escape.gss"):
        draft = orch.RequestDraft(
            request_id=f"req-{script_path}",
            script_path=script_path,
            working_directory="C:/example/work",
            executable_path="C:/example/gauss26/tgauss.exe",
            timeout_seconds=30.0,
            environment_summary=_env(),
            safety_review=_passing_safety(),
        )
        inst = orch.MockOrchestrationInstance(session_id="s1", draft=draft)
        inst.submit_for_review()
        check(
            f"script_path={script_path!r} is unconditionally blocked",
            inst.record.current_state == orch.OrchestrationState.BLOCKED
            and inst.record.failure_category == orch.FailureCategory.SCRIPT_IDENTITY_UNTRUSTED,
        )


def test_38_unsafe_request_blocked() -> None:
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft(safety_review=_failing_safety()))
    inst.submit_for_review()
    check("failing safety review blocks the request", inst.record.current_state == orch.OrchestrationState.BLOCKED)
    check("failing safety review category is UNSAFE_REQUEST", inst.record.failure_category == orch.FailureCategory.UNSAFE_REQUEST)


def test_39_execution_record_excludes_secrets_and_content() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: _completed_result(output_files=[{"path": "results.csv", "size_bytes": 10}]))
    summary = inst.record.to_safe_summary()
    serialized = str(summary)
    check("safe summary excludes the inline code text", "print 1+1" not in serialized)
    check("safe summary has no 'content' key anywhere", "content" not in summary)
    check("safe summary has no 'secret'/'credential'/'password' keys", not any(k for k in summary if any(t in k.lower() for t in ("secret", "credential", "password"))))


def test_40_confirmation_consumption_is_monotonic() -> None:
    """Invariant 16: once consumed, confirmation never reverts to valid."""
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: _completed_result())
    check("confirmation_status is consumed after invocation", inst.record.confirmation_status == orch.ConfirmationStatus.CONSUMED)
    # There is no public method anywhere on the instance that resets
    # confirmation_consumption_status back to False once True.
    check(
        "no public method exists to un-consume confirmation",
        not any(name.startswith("unconsume") or name.startswith("reset_confirmation") for name in dir(inst)),
    )


# ---------------------------------------------------------------------------
# Adapter-integration tests (v0.32.0 Phase 3, Increment 1). Every fake helper
# below is a plain Python function -- none of these tests import
# scripts/gauss_code_execution.py, call gauss_execution_adapter.load_real_helper(),
# launch a subprocess, or invoke GAUSS.
# ---------------------------------------------------------------------------


def _fake_completed_helper(**kwargs: Any) -> dict[str, Any]:
    return _completed_result()


def test_41_controller_to_adapter_projection() -> None:
    captured: dict[str, Any] = {}

    def recording_helper(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return _completed_result()

    inst = _fully_confirmed_instance()
    inst.invoke(_adapter_runner(inst, recording_helper))
    check("invocation via AdapterRunner reaches execution_completed", inst.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check("code projected through the adapter bridge", captured["code"] == "print 1+1;")
    check("working_directory projected through the adapter bridge", captured["working_directory"] == "C:/example/work")
    check("executable_path projected through the adapter bridge", captured["executable_path"] == "C:/example/gauss26/tgauss.exe")
    check("gauss_version projected through the adapter bridge", captured["gauss_version"] == "GAUSS 26")
    check("strict=True passed through the adapter bridge", captured["strict"] is True)
    check("allow_network=False passed through the adapter bridge", captured["allow_network"] is False)


def test_42_confirmation_consumed_before_adapter_invocation() -> None:
    inst = _fully_confirmed_instance()
    check("confirmation not yet consumed before invoke()", inst.record.confirmation_consumption_status is False)
    inst.invoke(_adapter_runner(inst, _fake_completed_helper))
    check("confirmation consumed after adapter-backed invoke()", inst.record.confirmation_consumption_status is True)


def test_43_preflight_failure_does_not_consume_confirmation() -> None:
    # Script-path refusal happens at submit_for_review(), long before any
    # adapter is ever constructed -- confirmation does not even exist yet.
    draft = orch.RequestDraft(
        request_id="req-preflight",
        script_path="script.gss",
        working_directory="C:/example/work",
        executable_path="C:/example/gauss26/tgauss.exe",
        timeout_seconds=30.0,
        environment_summary=_env(),
        safety_review=_passing_safety(),
    )
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=draft)
    inst.submit_for_review()
    check("script-path preflight failure blocks before any adapter involvement", inst.record.current_state == orch.OrchestrationState.BLOCKED)
    check("preflight failure never consumes confirmation", inst.record.confirmation_consumption_status is False)

    # Environment mismatch, detected by this controller's own pre-invocation
    # check, also never reaches invoke()/the adapter and never consumes
    # confirmation.
    inst2 = _fully_confirmed_instance(draft=_inline_draft(request_id="req-preflight-2"))
    inst2.check_environment_before_invocation(still_matches=False)
    check("environment-mismatch preflight failure reaches cancelled", inst2.record.current_state == orch.OrchestrationState.CANCELLED)
    check("environment-mismatch preflight failure never consumes confirmation", inst2.record.confirmation_consumption_status is False)


def test_44_adapter_launch_failure_consumes_confirmation() -> None:
    # A race: this controller's own environment check passed, but the
    # adapter's environment_probe (checked again, independently, immediately
    # before the call) reports a mismatch -- AdapterRunner raises, and
    # invoke() correctly classifies this as a launch failure, which DOES
    # consume confirmation (it was already consumed before the adapter was
    # ever called, per the atomic-consumption rule).
    inst = _fully_confirmed_instance()
    inst.check_environment_before_invocation(still_matches=True)
    runner = _adapter_runner(inst, _fake_completed_helper, environment_probe=lambda _p: False)
    inst.invoke(runner)
    check("adapter-level rejection still consumes confirmation", inst.record.confirmation_consumption_status is True)
    check("adapter-level rejection routes to execution_failed", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check("adapter-level rejection uses RUNNER_LAUNCH_FAILURE", inst.record.failure_category == orch.FailureCategory.RUNNER_LAUNCH_FAILURE)


def test_45_valid_completed_result_via_adapter() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(_adapter_runner(inst, _fake_completed_helper))
    check("adapter-backed completed result reaches execution_completed", inst.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    assert inst.record.execution_result_reference is not None
    check("adapter-backed result has no failure category", inst.record.failure_category is None)


def test_46_runtime_failure_result_via_adapter() -> None:
    inst = _fully_confirmed_instance()

    def failing_helper(**kwargs: Any) -> dict[str, Any]:
        return {**_completed_result(), "execution_status": "failed", "exit_code": 1, "stderr": "error G0025"}

    inst.invoke(_adapter_runner(inst, failing_helper))
    check("adapter-backed failed result reaches execution_failed", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check("adapter-backed failed result uses GAUSS_RUNTIME_ERROR", inst.record.failure_category == orch.FailureCategory.GAUSS_RUNTIME_ERROR)


def test_47_timeout_via_adapter() -> None:
    inst = _fully_confirmed_instance()

    def timeout_helper(**kwargs: Any) -> dict[str, Any]:
        return {**_completed_result(), "execution_status": "timed_out", "exit_code": None}

    inst.invoke(_adapter_runner(inst, timeout_helper))
    check("adapter-backed timeout reaches execution_failed", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check("adapter-backed timeout uses TIMEOUT, distinct from GAUSS_RUNTIME_ERROR", inst.record.failure_category == orch.FailureCategory.TIMEOUT)


def test_48_malformed_result_via_adapter() -> None:
    inst = _fully_confirmed_instance()

    def malformed_helper(**kwargs: Any) -> dict[str, Any]:
        return {"executed": True}  # missing required keys -> malformed

    inst.invoke(_adapter_runner(inst, malformed_helper))
    check("adapter-backed malformed result reaches execution_failed", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check("adapter-backed malformed result uses MALFORMED_RESULT", inst.record.failure_category == orch.FailureCategory.MALFORMED_RESULT)
    check_raises(
        "begin_analysis() on an adapter-backed malformed result is rejected",
        orch.AnalysisNotAllowedError,
        inst.begin_analysis,
        lambda req, res: None,
    )


def test_49_missing_expected_output_via_adapter() -> None:
    draft = _inline_draft(expected_output_files=("results.csv",))
    inst = _fully_confirmed_instance(draft=draft)

    def no_output_helper(**kwargs: Any) -> dict[str, Any]:
        return _completed_result(output_files=[])

    inst.invoke(_adapter_runner(inst, no_output_helper))
    check("adapter-backed missing-output result still reaches execution_completed", inst.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check("adapter-backed missing-output result uses MISSING_EXPECTED_OUTPUT", inst.record.failure_category == orch.FailureCategory.MISSING_EXPECTED_OUTPUT)


def test_50_environment_mismatch_blocks_adapter_path() -> None:
    inst = _fully_confirmed_instance()
    inst.check_environment_before_invocation(still_matches=False)
    check("environment mismatch cancels before any adapter is invoked", inst.record.current_state == orch.OrchestrationState.CANCELLED)
    check_raises(
        "invoke() after environment mismatch is rejected, adapter never reached",
        orch.InvalidTransitionError,
        inst.invoke,
        _adapter_runner(inst, _fake_completed_helper),
    )


def test_51_script_path_refused_before_any_adapter_exists() -> None:
    draft = orch.RequestDraft(
        request_id="req-script-adapter",
        script_path="script.gss",
        working_directory="C:/example/work",
        executable_path="C:/example/gauss26/tgauss.exe",
        timeout_seconds=30.0,
        environment_summary=_env(),
        safety_review=_passing_safety(),
    )
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=draft)
    inst.submit_for_review()
    check("script-path request never reaches a state where an adapter could be invoked", inst.record.current_state == orch.OrchestrationState.BLOCKED)
    check("script-path refusal uses SCRIPT_IDENTITY_UNTRUSTED", inst.record.failure_category == orch.FailureCategory.SCRIPT_IDENTITY_UNTRUSTED)


def test_52_duplicate_invocation_refused_with_adapter() -> None:
    calls: list[Any] = []

    def counting_helper(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return _completed_result()

    inst = _fully_confirmed_instance()
    runner = _adapter_runner(inst, counting_helper)
    inst.invoke(runner)
    check_raises(
        "second invoke() via the same adapter-backed runner is rejected by the controller",
        orch.InvalidTransitionError,
        inst.invoke,
        runner,
    )
    check("the adapter's own helper was called exactly once", len(calls) == 1)


def test_53_no_automatic_retry_with_adapter() -> None:
    inst = _fully_confirmed_instance()

    def failing_helper(**kwargs: Any) -> dict[str, Any]:
        return {**_completed_result(), "execution_status": "failed", "exit_code": 1}

    inst.invoke(_adapter_runner(inst, failing_helper))
    check("adapter-backed failure routes to execution_failed", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check_raises(
        "invoke() cannot be called again on an adapter-backed failed instance",
        orch.InvalidTransitionError,
        inst.invoke,
        _adapter_runner(inst, _fake_completed_helper),
    )


def test_54_rerun_requires_new_request_with_adapter() -> None:
    inst1 = _fully_confirmed_instance(draft=_inline_draft(request_id="req-adapter-original"))

    def failing_helper(**kwargs: Any) -> dict[str, Any]:
        return {**_completed_result(), "execution_status": "failed", "exit_code": 1}

    inst1.invoke(_adapter_runner(inst1, failing_helper))
    assert inst1.request is not None
    original_hash = inst1.request.request_hash

    inst2 = _fully_confirmed_instance(draft=_inline_draft(request_id="req-adapter-rerun", code="print 1+1; print 3+3;"))
    assert inst2.request is not None
    check("rerun via a fresh adapter-backed instance uses a different request_hash", inst2.request.request_hash != original_hash)
    inst2.invoke(_adapter_runner(inst2, _fake_completed_helper))
    check("rerun instance reaches execution_completed independently", inst2.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check("original instance is unaffected by the rerun", inst1.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)


def test_55_cancellation_before_authorization_with_adapter() -> None:
    calls: list[Any] = []

    def counting_helper(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return _completed_result()

    inst = _fully_confirmed_instance()
    inst.cancel()
    check("cancel from confirmed reaches cancelled before any adapter call", inst.record.current_state == orch.OrchestrationState.CANCELLED)
    check_raises(
        "invoke() after pre-launch cancellation is rejected, adapter never reached",
        orch.InvalidTransitionError,
        inst.invoke,
        _adapter_runner(inst, counting_helper),
    )
    check("the adapter's helper was never called", calls == [])


def test_56_cancellation_during_synchronous_adapter_call_and_late_result() -> None:
    inst = _fully_confirmed_instance()

    def helper_that_gets_cancelled(**kwargs: Any) -> dict[str, Any]:
        # Simulate a cancellation request arriving while the (synchronous)
        # adapter call is "in flight" -- the call cannot be interrupted, and
        # it still returns a real result, which must be retained honestly.
        inst.cancel(note="user asked to cancel while waiting")
        return _completed_result()

    inst.invoke(_adapter_runner(inst, helper_that_gets_cancelled))
    check(
        "cancellation during an adapter-backed call is recorded, not silently dropped",
        inst.record.cancellation_status == orch.CancellationStatus.CANCEL_REQUESTED_DURING_INVOCATION,
    )
    check(
        "the late adapter-backed result is still retained and processed",
        inst.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED,
    )
    check(
        "no claim of process termination is made anywhere in the record",
        "terminated" not in inst.record.cancellation_status.value,
    )


def test_57_analysis_failure_preserves_execution_result_with_adapter() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(_adapter_runner(inst, _fake_completed_helper))
    result_before = inst.record.execution_result_reference

    def failing_analysis(req: Any, res: Any) -> None:
        raise RuntimeError("simulated analysis failure")

    inst.begin_analysis(failing_analysis)
    check("analysis_status is failed after an adapter-backed execution", inst.record.analysis_status == orch.AnalysisStatus.FAILED)
    check("execution_result_reference untouched by analysis failure", inst.record.execution_result_reference is result_before)
    check("instance still reaches completed despite analysis failure", inst.record.current_state == orch.OrchestrationState.COMPLETED)


def test_58_report_failure_preserves_execution_and_analysis_with_adapter() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(_adapter_runner(inst, _fake_completed_helper))
    inst.begin_analysis(
        lambda req, res: None,
        report_requested=True,
        report_hook=lambda status: (_ for _ in ()).throw(RuntimeError("simulated report failure")),
    )
    check("report_status is failed after an adapter-backed execution", inst.record.report_status == orch.ReportStatus.FAILED)
    check("analysis_status remains completed despite report failure", inst.record.analysis_status == orch.AnalysisStatus.COMPLETED)
    check("execution_result_reference remains set despite report failure", inst.record.execution_result_reference is not None)


def test_59_session_mismatch_unaffected_by_adapter() -> None:
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft())
    inst.submit_for_review()
    inst.display_plan()
    assert inst.request is not None
    check_raises(
        "confirm() from a different session is rejected before any adapter could be involved",
        orch.SessionMismatchError,
        inst.confirm,
        orch.ConfirmationEvent(scope=inst.request.request_hash, timestamp="t1", session_id="s2"),
    )
    check("session-mismatched confirm() does not accept the request", inst.record.current_state == orch.OrchestrationState.AWAITING_CONFIRMATION)


def test_60_adapter_runner_never_imports_or_invokes_real_helper() -> None:
    """Static/structural proof that this module's own AdapterRunner path
    never touches the real helper: neither this module nor
    gauss_execution_adapter imports scripts/gauss_code_execution.py at
    module level, and load_real_helper() is never called anywhere in this
    test file."""
    check(
        "gauss_code_execution is not an imported module-level name in gauss_runtime_orchestration",
        "gauss_code_execution" not in dir(orch),
    )
    check(
        "gauss_code_execution is not an imported module-level name in gauss_execution_adapter",
        "gauss_code_execution" not in dir(ga),
    )
    import sys as _sys

    check("gauss_code_execution has not been imported into sys.modules by this test run", "gauss_code_execution" not in _sys.modules)


# ---------------------------------------------------------------------------
# v0.33.0 Controlled Real Execution Integration: production-path factory
# tests. These deliberately never CALL build_production_adapter_runner(...)
# -- doing so would import scripts/gauss_code_execution.py as a side effect
# of running this repository's default test suite, which would silently
# weaken the exact "default tests never touch the real helper" guarantee
# test_60 (and the adapter suite's own test_26) exist to protect. These
# tests instead verify the factory's existence, isolation, and non-automatic
# wiring structurally, without ever importing the real helper.
# ---------------------------------------------------------------------------


def test_61_production_adapter_factory_exists_and_is_isolated() -> None:
    check("build_production_adapter_runner exists and is callable", callable(orch.build_production_adapter_runner))
    check(
        "build_production_adapter_runner is not referenced inside MockOrchestrationInstance.__init__",
        "build_production_adapter_runner" not in orch.MockOrchestrationInstance.__init__.__code__.co_names,
    )
    check(
        "build_production_adapter_runner is not referenced inside MockOrchestrationInstance.invoke",
        "build_production_adapter_runner" not in orch.MockOrchestrationInstance.invoke.__code__.co_names,
    )
    check(
        "build_production_adapter_runner is not referenced inside AdapterRunner.__init__ or __call__",
        "build_production_adapter_runner" not in orch.AdapterRunner.__init__.__code__.co_names
        and "build_production_adapter_runner" not in orch.AdapterRunner.__call__.__code__.co_names,
    )


def test_62_production_adapter_factory_calls_only_the_sanctioned_real_path() -> None:
    """Structural proof that the factory's own bytecode calls nothing beyond
    the two sanctioned adapter entry points -- confirmed by name, not by
    actually calling the factory (which would import the real helper)."""
    names = orch.build_production_adapter_runner.__code__.co_names
    check("factory references gauss_execution_adapter", "gauss_execution_adapter" in names)
    check("factory does not reference execute_gauss_code directly", "execute_gauss_code" not in names)
    check("factory does not reference subprocess", "subprocess" not in names)


# ---------------------------------------------------------------------------
# v0.34.0 Confirmed Controller Execution Path: fake-helper regression tests
# capturing lessons from the two real controller-path invocations recorded
# in planning/v0.34.0-confirmed-controller-execution-path.md. Every fake
# result shape below is copied verbatim from that document's actual
# recorded stdout/stderr/exit_code -- not invented -- so these tests lock in
# regression protection against the exact real behavior observed, using
# fakes only. None of these tests import scripts/gauss_code_execution.py or
# call build_production_adapter_runner(...).
# ---------------------------------------------------------------------------


def _real_shaped_success_result() -> dict[str, Any]:
    """Verbatim shape of the real result observed in this milestone's
    invocation 1 (the "success" scenario, x = 2 + 2; print x;)."""
    return {
        "executed": True,
        "execution_status": "completed",
        "exit_code": 0,
        "stdout": "       4.0000000 \n",
        "stderr": (
            "\nGAUSS 26.1.1 (Apr 14 2026, 5516) 64-bit\n"
            "(C)Copyright 1984-2026 Aptech Systems, Inc.\nAll Rights Reserved Worldwide.\n\n\n"
            "Job: inline_gau_qf30.gss ( C:\\example\\work )\nSun Jul 19 19:47:00 2026\n\n\n"
        ),
        "output_files": [],
        "warnings": [],
        "errors": [],
    }


def _real_shaped_runtime_error_result() -> dict[str, Any]:
    """Verbatim shape of the real result observed in this milestone's
    invocation 2 (the "runtime_error" scenario, x = ;)."""
    return {
        "executed": True,
        "execution_status": "failed",
        "exit_code": 0,
        "stdout": "Program execute failed\n",
        "stderr": (
            "\nGAUSS 26.1.1 (Apr 14 2026, 5516) 64-bit\n"
            "(C)Copyright 1984-2026 Aptech Systems, Inc.\nAll Rights Reserved Worldwide.\n\n\n"
            "Job: inline_bt49tgfm.gss ( C:\\example\\work )\nSun Jul 19 19:48:23 2026\n\n\n"
            "error G0105 : Bad expression or missing arguments\n"
            "\tC:\\example\\work\\.gauss_code_execution_generated\\inline_bt49tgfm.gss, line 1\n"
        ),
        "output_files": [],
        "warnings": [],
        "errors": [],
    }


def test_64_full_sequence_matches_real_success_transition_log() -> None:
    """The exact 8-transition sequence observed in the real success
    invocation: proposed -> awaiting_confirmation -> confirmed -> executing
    -> execution_completed -> analyzing -> report_generating -> completed."""
    inst = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v034-success-shape"))
    inst.invoke(lambda _: _real_shaped_success_result())
    inst.begin_analysis(lambda req, res: None, report_requested=True, report_hook=lambda status: None)

    observed = [t.to_state.value for t in inst.record.transition_log]
    expected = [
        "proposed",
        "awaiting_confirmation",
        "confirmed",
        "executing",
        "execution_completed",
        "analyzing",
        "report_generating",
        "completed",
    ]
    check("fake-driven transition sequence matches the real success sequence exactly", observed == expected)
    check("final state is completed", inst.record.current_state == orch.OrchestrationState.COMPLETED)


def test_65_full_sequence_matches_real_runtime_error_transition_log() -> None:
    """The exact 8-transition sequence observed in the real runtime-error
    invocation: proposed -> awaiting_confirmation -> confirmed -> executing
    -> execution_failed -> analyzing -> report_generating -> completed."""
    inst = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v034-error-shape"))
    inst.invoke(lambda _: _real_shaped_runtime_error_result())
    inst.begin_analysis(lambda req, res: None, report_requested=True, report_hook=lambda status: None)

    observed = [t.to_state.value for t in inst.record.transition_log]
    expected = [
        "proposed",
        "awaiting_confirmation",
        "confirmed",
        "executing",
        "execution_failed",
        "analyzing",
        "report_generating",
        "completed",
    ]
    check("fake-driven transition sequence matches the real runtime-error sequence exactly", observed == expected)
    check("failure_category is GAUSS_RUNTIME_ERROR, matching the real observed classification", inst.record.failure_category == orch.FailureCategory.GAUSS_RUNTIME_ERROR)


def test_66_real_shaped_completed_result_routes_correctly() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: _real_shaped_success_result())
    check("real-shaped completed result reaches execution_completed", inst.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check("real-shaped completed result has no failure category", inst.record.failure_category is None)
    assert inst.record.execution_result_reference is not None
    check("stdout preserved unmodified", inst.record.execution_result_reference.stdout == "       4.0000000 \n")


def test_67_real_shaped_runtime_error_result_routes_correctly() -> None:
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: _real_shaped_runtime_error_result())
    check("real-shaped runtime-error result reaches execution_failed", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check("real-shaped runtime-error result uses GAUSS_RUNTIME_ERROR", inst.record.failure_category == orch.FailureCategory.GAUSS_RUNTIME_ERROR)
    check(
        "exit_code 0 despite failure is preserved, not silently corrected (exit_code remains non-authoritative)",
        inst.record.execution_result_reference is not None and inst.record.execution_result_reference.exit_code == 0,
    )


def test_68_request_and_confirmation_hash_match_end_to_end() -> None:
    """Re-verifies, across the full pre-invocation sequence in one pass
    (not just isolated pieces), that the confirmed request's confirmation_scope
    equals its own request_hash -- exactly what was observed live in both
    real invocations (confirmation_scope_matches_hash: True)."""
    inst = orch.MockOrchestrationInstance(session_id="s1", draft=_inline_draft(request_id="req-v034-hash-check"))
    inst.submit_for_review()
    inst.display_plan()
    assert inst.request is not None
    request_hash_before_confirm = inst.request.request_hash
    inst.confirm(orch.ConfirmationEvent(scope=inst.request.request_hash, timestamp="t1", session_id="s1"))
    check("confirmation_scope equals request_hash after confirm()", inst.request.confirmation_scope == request_hash_before_confirm)
    check("request_hash is unchanged by confirmation (frozen)", inst.request.request_hash == request_hash_before_confirm)


def test_69_safe_summary_excludes_code_after_full_real_shaped_sequence() -> None:
    inst = _fully_confirmed_instance(draft=_inline_draft(code="x = 2 + 2;\nprint x;"))
    inst.invoke(lambda _: _real_shaped_success_result())
    inst.begin_analysis(lambda req, res: None, report_requested=True, report_hook=lambda status: None)
    summary = inst.record.to_safe_summary()
    serialized = str(summary)
    check("safe summary excludes the real inline code text", "x = 2 + 2" not in serialized)
    check("safe summary has no 'code' key", "code" not in summary)
    check("safe summary reflects the completed terminal state", summary["current_state"] == "completed")


# ---------------------------------------------------------------------------
# v0.35.0 Real Execution Reliability and Output Verification: fake-helper
# regression tests capturing lessons from the five real controller-path
# invocations recorded in planning/v0.35.0-implementation-report.md.
#
# Invocation 3 ("output-created") surfaced a genuine controller bug during
# real testing: _missing_expected_outputs previously compared declared
# expected_output_files (documented, per the canonical request contract, as
# free-form/descriptive filenames -- never paths a caller is expected to
# predict exactly) against exact-string equality with the helper's *actual*
# output_files paths, which are always absolute filesystem paths. A
# genuinely-created, correctly-discovered file was therefore always
# misclassified as missing whenever expected_output_files declared a bare
# filename -- the documented, expected way to declare one. Fixed in
# _missing_expected_outputs (this file's own module) to compare by
# basename instead of exact string equality; scripts/gauss_code_execution.py
# and schemas/gauss_code_execution.schema.json were not touched. The two
# fixtures below reproduce the exact real result shapes observed in
# invocations 3 and 4 (paths generalized to a placeholder directory,
# consistent with this file's existing v0.34.0 fixtures), locking in
# regression protection for the fix using fakes only.
# ---------------------------------------------------------------------------


def _real_shaped_output_created_result() -> dict[str, Any]:
    """Verbatim shape of the real result observed in this milestone's
    invocation 3 (the "output-created" scenario, output file = gauss_output.txt
    reset; print "hello output test"; output off;), path generalized."""
    return {
        "executed": True,
        "execution_status": "completed",
        "exit_code": 0,
        "stdout": "hello output test\n",
        "stderr": (
            "\nGAUSS 26.1.1 (Apr 14 2026, 5516) 64-bit\n"
            "(C)Copyright 1984-2026 Aptech Systems, Inc.\nAll Rights Reserved Worldwide.\n\n\n"
            "Job: inline_rt_x1mol.gss ( C:\\example\\work )\nMon Jul 20 05:51:36 2026\n\n\n"
        ),
        "output_files": [
            {
                "path": "C:\\example\\work\\gauss_output.txt",
                "size_bytes": 19,
                "file_type": "text/plain",
                "created_by_execution": "unknown",
            }
        ],
        "warnings": [],
        "errors": [],
    }


def _real_shaped_output_missing_result() -> dict[str, Any]:
    """Verbatim shape of the real result observed in this milestone's
    invocation 4 (the "output-missing" scenario: the verified success-basic
    script, x = 2 + 2; print x;, with expected_output_files declaring a file
    the script never writes)."""
    return {
        "executed": True,
        "execution_status": "completed",
        "exit_code": 0,
        "stdout": "       4.0000000 \n",
        "stderr": (
            "\nGAUSS 26.1.1 (Apr 14 2026, 5516) 64-bit\n"
            "(C)Copyright 1984-2026 Aptech Systems, Inc.\nAll Rights Reserved Worldwide.\n\n\n"
            "Job: inline_q32pw3co.gss ( C:\\example\\work )\nMon Jul 20 05:54:07 2026\n\n\n"
        ),
        "output_files": [],
        "warnings": [],
        "errors": [],
    }


def test_71_two_independent_requests_each_execute_once() -> None:
    """Reproduces invocations 1-2 (success-basic / success-isolation): two
    separate, independently-confirmed requests, each invoked exactly once,
    with distinct helper_invocation_ids -- exactly as observed live. As in
    the real invocations (which used separate working directories per
    scenario), the drafts below differ in working_directory -- a
    hash-included field -- so their request_hashes differ too;
    request_hash is a pure content fingerprint over 12 hash-included fields
    (canonical request contract Section 10) and deliberately does NOT
    include request_id, so identical content with only request_id differing
    would legitimately hash identically -- see test_84 below."""
    inst_a = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-a", working_directory="C:/example/work-a"))
    inst_b = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-b", working_directory="C:/example/work-b"))

    inst_a.invoke(lambda _: _real_shaped_success_result())
    inst_b.invoke(lambda _: _real_shaped_success_result())

    check("instance A reaches execution_completed", inst_a.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check("instance B reaches execution_completed", inst_b.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check(
        "each instance has its own distinct helper_invocation_id",
        inst_a.record.helper_invocation_id != inst_b.record.helper_invocation_id,
    )
    check(
        "each instance has its own distinct request_hash (distinct working_directory)",
        inst_a.request is not None and inst_b.request is not None and inst_a.request.request_hash != inst_b.request.request_hash,
    )


def test_72_stale_state_does_not_cross_instances() -> None:
    """Instance A completes fully; a freshly constructed instance B must
    start from collecting_inputs with no execution result, no transitions,
    and no confirmation -- proving no module-level or shared state leaks
    between MockOrchestrationInstance objects."""
    inst_a = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-stale-a"))
    inst_a.invoke(lambda _: _real_shaped_success_result())
    inst_a.begin_analysis(lambda req, res: None, report_requested=True, report_hook=lambda status: None)
    check("instance A reached completed", inst_a.record.current_state == orch.OrchestrationState.COMPLETED)

    inst_b = orch.MockOrchestrationInstance(session_id="s-stale-b", draft=_inline_draft(request_id="req-v035-stale-b"))
    check("fresh instance B starts at collecting_inputs, unaffected by A", inst_b.record.current_state == orch.OrchestrationState.COLLECTING_INPUTS)
    check("fresh instance B has no execution result", inst_b.record.execution_result_reference is None)
    check("fresh instance B has no transitions yet", len(inst_b.record.transition_log) == 0)
    check("fresh instance B has no helper_invocation_id", inst_b.record.helper_invocation_id is None)
    check("fresh instance B's request is not yet built", inst_b.request is None)


def test_73_fresh_confirmation_required_per_instance() -> None:
    """A different, already-confirmed instance's confirmed status must never
    implicitly satisfy a second, distinct instance's own confirmation
    requirement -- each instance requires its own confirm() call, scoped to
    its own request_hash, every time."""
    inst_a = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-fresh-a"))
    check("instance A is confirmed", inst_a.request is not None and inst_a.request.user_confirmed)

    inst_b = orch.MockOrchestrationInstance(session_id="s-fresh-b", draft=_inline_draft(request_id="req-v035-fresh-b"))
    inst_b.submit_for_review()
    inst_b.display_plan()
    check("instance B is awaiting_confirmation, not implicitly confirmed by A", inst_b.record.current_state == orch.OrchestrationState.AWAITING_CONFIRMATION)
    check_raises(
        "invoking instance B before its own confirm() raises (state adjacency alone already refuses it), despite A being confirmed",
        orch.InvalidTransitionError,
        inst_b.invoke,
        lambda _: _real_shaped_success_result(),
    )


def test_74_real_shaped_output_created_result_now_matches_expected_output_post_fix() -> None:
    """Regression test for the real bug found in invocation 3: a genuinely
    created, correctly-discovered output file, declared by its bare
    filename in expected_output_files, must not be misclassified as
    missing."""
    draft = _inline_draft(request_id="req-v035-output-created", expected_output_files=("gauss_output.txt",))
    inst = _fully_confirmed_instance(draft=draft)
    inst.invoke(lambda _: _real_shaped_output_created_result())
    check("output-created result reaches execution_completed", inst.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check(
        "output-created result has NO failure category (fixed: was incorrectly MISSING_EXPECTED_OUTPUT before the basename fix)",
        inst.record.failure_category is None,
    )
    assert inst.record.execution_result_reference is not None
    check("exactly one output file recorded", len(inst.record.execution_result_reference.output_files) == 1)


def test_75_real_shaped_output_missing_result_still_correctly_flagged() -> None:
    """Regression test for invocation 4: a script that genuinely produces no
    output must still be correctly flagged as missing its declared expected
    output -- the basename fix must not cause false negatives."""
    draft = _inline_draft(request_id="req-v035-output-missing", expected_output_files=("does_not_exist.txt",))
    inst = _fully_confirmed_instance(draft=draft)
    inst.invoke(lambda _: _real_shaped_output_missing_result())
    check("output-missing result still reaches execution_completed", inst.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check("output-missing result correctly sets MISSING_EXPECTED_OUTPUT", inst.record.failure_category == orch.FailureCategory.MISSING_EXPECTED_OUTPUT)
    assert inst.record.execution_result_reference is not None
    check("zero output files recorded, matching the real observed evidence", len(inst.record.execution_result_reference.output_files) == 0)


def test_76_output_file_metadata_fields_retained_exactly() -> None:
    """The real output file's discovered metadata (path/size_bytes/file_type/
    created_by_execution) must survive into execution_result_reference
    unmodified -- this milestone never rewrites, summarizes, or filters it."""
    inst = _fully_confirmed_instance(draft=_inline_draft(expected_output_files=("gauss_output.txt",)))
    inst.invoke(lambda _: _real_shaped_output_created_result())
    assert inst.record.execution_result_reference is not None
    meta = inst.record.execution_result_reference.output_files[0]
    check("path preserved exactly", meta.path == "C:\\example\\work\\gauss_output.txt")
    check("size_bytes preserved exactly (19, matching the real file's actual size)", meta.size_bytes == 19)
    check("file_type preserved exactly", meta.file_type == "text/plain")
    check("created_by_execution preserved exactly", meta.created_by_execution == "unknown")


def test_77_output_metadata_never_carries_content() -> None:
    """OutputFileMeta has no 'content' field at all (structural guarantee),
    and a raw result whose output_files entry includes a 'content' key is
    rejected as malformed before it ever reaches execution_result_reference."""
    check("OutputFileMeta has no content field", not hasattr(orch.OutputFileMeta, "content") and "content" not in orch.OutputFileMeta.__dataclass_fields__)
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: _completed_result(output_files=[{"path": "results.csv", "content": "1,2,3"}]))
    check("a result whose output_files carries content is rejected as malformed", inst.record.failure_category == orch.FailureCategory.MALFORMED_RESULT)
    check("malformed content-carrying result never becomes an execution_result_reference", inst.record.execution_result_reference is None)


def test_78_blocked_execution_status_is_disclosed_not_silently_accepted() -> None:
    """An 'blocked' execution_status (the helper's own real, documented
    response to an output_directory/script_path that resolves outside safe
    containment, per scripts/gauss_code_execution.py, unmodified by this
    milestone) must never be silently treated as a successful completion --
    this locks in the controller's existing (not v0.35.0-introduced) routing
    of any non-completed/non-timed_out status to a disclosed failure."""
    inst = _fully_confirmed_instance()
    inst.invoke(lambda _: _completed_result(execution_status="blocked", executed=False))
    check("a blocked status never reaches execution_completed", inst.record.current_state != orch.OrchestrationState.EXECUTION_COMPLETED)
    check("a blocked status is disclosed as a failure, not silently accepted", inst.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)
    check("a blocked status is not falsely reported as having no failure category", inst.record.failure_category is not None)


def test_79_result_records_remain_distinct_across_instances() -> None:
    """Two instances' execution_result_reference objects must be distinct
    objects with independently correct content, never aliased or shared."""
    inst_a = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-distinct-a"))
    inst_b = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-distinct-b", expected_output_files=("gauss_output.txt",)))
    inst_a.invoke(lambda _: _real_shaped_success_result())
    inst_b.invoke(lambda _: _real_shaped_output_created_result())
    assert inst_a.record.execution_result_reference is not None
    assert inst_b.record.execution_result_reference is not None
    check("result objects are not the same object", inst_a.record.execution_result_reference is not inst_b.record.execution_result_reference)
    check("instance A's stdout is its own", inst_a.record.execution_result_reference.stdout == "       4.0000000 \n")
    check("instance B's stdout is its own, not overwritten by A", inst_b.record.execution_result_reference.stdout == "hello output test\n")


def test_80_prior_result_remains_immutable_after_a_second_unrelated_invocation() -> None:
    """Invoking a second, unrelated instance after the first has completed
    must never mutate the first instance's already-recorded evidence."""
    inst_a = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-immutable-a"))
    inst_a.invoke(lambda _: _real_shaped_success_result())
    stdout_before = inst_a.record.execution_result_reference.stdout  # type: ignore[union-attr]
    failure_before = inst_a.record.failure_category
    state_before = inst_a.record.current_state

    inst_b = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-immutable-b"))
    inst_b.invoke(lambda _: _real_shaped_runtime_error_result())

    check("instance A's stdout is unchanged after B's unrelated invocation", inst_a.record.execution_result_reference.stdout == stdout_before)  # type: ignore[union-attr]
    check("instance A's failure_category is unchanged", inst_a.record.failure_category == failure_before)
    check("instance A's state is unchanged", inst_a.record.current_state == state_before)


def test_81_runtime_error_and_missing_output_are_distinct_failure_categories() -> None:
    """Reproduces the observed distinction between invocation 4 (missing
    output, execution_completed) and invocation 5 (runtime error,
    execution_failed) -- these must never be conflated into one category."""
    inst_missing = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-cat-missing", expected_output_files=("does_not_exist.txt",)))
    inst_error = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-cat-error"))
    inst_missing.invoke(lambda _: _real_shaped_output_missing_result())
    inst_error.invoke(lambda _: _real_shaped_runtime_error_result())

    check("missing-output failure category differs from runtime-error failure category", inst_missing.record.failure_category != inst_error.record.failure_category)
    check("missing-output reaches execution_completed", inst_missing.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check("runtime-error reaches execution_failed", inst_error.record.current_state == orch.OrchestrationState.EXECUTION_FAILED)


def test_82_missing_expected_output_still_reaches_execution_completed() -> None:
    """Execution success and expected-output verification are two
    independently tracked outcomes -- a missing declared output must never
    downgrade an otherwise-completed execution to execution_failed."""
    inst = _fully_confirmed_instance(draft=_inline_draft(expected_output_files=("does_not_exist.txt",)))
    inst.invoke(lambda _: _real_shaped_output_missing_result())
    check("state is execution_completed, not execution_failed, despite the missing output", inst.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check("failure_category still discloses the missing output", inst.record.failure_category == orch.FailureCategory.MISSING_EXPECTED_OUTPUT)


def test_83_duplicate_request_identity_refused_even_via_reused_adapter() -> None:
    """Defense-in-depth: if a single GaussExecutionAdapter instance were
    ever reused across two invoke() attempts sharing the same
    request_identity (a caller-level mistake this controller's own
    single-invocation-per-instance guard already prevents in the normal
    case), the adapter's own independent duplicate-invocation tracking must
    still refuse the second attempt."""
    shared_identity = "req-v035-shared-identity"
    calls: list[int] = []

    def counting_helper(**kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return _completed_result()

    adapter = ga.GaussExecutionAdapter(helper=counting_helper, environment_probe=lambda _p: True)
    runner = orch.AdapterRunner(adapter, request_identity=shared_identity)

    inst_a = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-reused-adapter-a"))
    inst_a.invoke(runner)
    check("first invocation via the shared adapter succeeds", inst_a.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check("helper was called exactly once so far", len(calls) == 1)

    inst_b = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-reused-adapter-b"))
    inst_b.invoke(runner)  # same adapter, same request_identity as inst_a -- must be refused
    check(
        "second invocation via the same adapter/identity is refused as a launch failure",
        inst_b.record.current_state == orch.OrchestrationState.EXECUTION_FAILED
        and inst_b.record.failure_category == orch.FailureCategory.RUNNER_LAUNCH_FAILURE,
    )
    check("the helper itself was never called a second time", len(calls) == 1)


def test_84_same_code_with_new_request_identity_is_permitted_and_isolated() -> None:
    """Reproduces invocations 1-2's own design intent directly: identical
    code, submitted as two separate requests, must both be permitted and
    must never be refused as a false duplicate -- whether or not their
    request_hashes happen to match. request_hash is a pure content
    fingerprint (see test_71) that deliberately excludes request_id, so two
    requests with identical code AND identical working_directory/executable/
    timeout/etc. legitimately share one request_hash -- this is by design,
    not a collision bug, and duplicate-invocation refusal is scoped to one
    request_hash *reused within the same adapter instance* (test_83), never
    to two independent instances/adapters that happen to hash the same."""
    identical_code = "x = 2 + 2;\nprint x;"
    inst_a = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-same-code-a", code=identical_code))
    inst_b = _fully_confirmed_instance(draft=_inline_draft(request_id="req-v035-same-code-b", code=identical_code))
    inst_a.invoke(lambda _: _real_shaped_success_result())
    inst_b.invoke(lambda _: _real_shaped_success_result())
    check("both identical-code, distinct-instance requests succeed", inst_a.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED and inst_b.record.current_state == orch.OrchestrationState.EXECUTION_COMPLETED)
    check(
        "identical draft content legitimately produces the same request_hash (request_id is not hash-included)",
        inst_a.request is not None and inst_b.request is not None and inst_a.request.request_hash == inst_b.request.request_hash,
    )
    check(
        "yet each instance still has its own distinct helper_invocation_id",
        inst_a.record.helper_invocation_id != inst_b.record.helper_invocation_id,
    )


def test_85_safe_summary_omits_output_file_content_for_output_created_scenario() -> None:
    """The real output-created scenario's own literal file content
    ("hello output test") must never appear anywhere in the safe summary --
    only metadata (path/size/type) is legitimate execution evidence."""
    inst = _fully_confirmed_instance(draft=_inline_draft(expected_output_files=("gauss_output.txt",)))
    inst.invoke(lambda _: _real_shaped_output_created_result())
    inst.begin_analysis(lambda req, res: None, report_requested=True, report_hook=lambda status: None)
    summary = inst.record.to_safe_summary()
    serialized = str(summary)
    check("safe summary never includes the output file's literal content text", "hello output test" not in serialized)
    check("safe summary has no 'code' key", "code" not in summary)
    check("safe summary reflects the completed terminal state", summary["current_state"] == "completed")


def test_86_no_automatic_rerun_after_missing_expected_output() -> None:
    """A missing-expected-output classification must never trigger an
    automatic second invocation. Natural path: the instance has already
    moved on from `confirmed`, so a second invoke() attempt is refused by
    the ordinary state-adjacency check alone -- nothing in this codebase
    loops back to retry. Defense-in-depth path (mirroring test_19's own
    established pattern): even if state were artificially reset to
    `confirmed`, the explicit invocation-identity guard still refuses a
    second invocation for the same request_hash."""
    inst = _fully_confirmed_instance(draft=_inline_draft(expected_output_files=("does_not_exist.txt",)))
    inst.invoke(lambda _: _real_shaped_output_missing_result())
    check("helper_invocation_id was set exactly once", inst.record.helper_invocation_id is not None)
    check_raises(
        "a second invoke() is refused by ordinary state adjacency, not automatically retried",
        orch.InvalidTransitionError,
        inst.invoke,
        lambda _: _real_shaped_output_missing_result(),
    )

    object.__setattr__(inst.record, "current_state", orch.OrchestrationState.CONFIRMED)
    check_raises(
        "even with state artificially reset, the explicit duplicate-invocation-id guard still refuses a rerun",
        orch.DuplicateInvocationError,
        inst.invoke,
        lambda _: _real_shaped_output_missing_result(),
    )


def test_87_default_test_run_still_never_imports_the_real_helper() -> None:
    """Re-confirms, at the very end of this file's own test ordering, that
    nothing added for v0.33.0, v0.34.0, or v0.35.0 changed the
    default-test-suite guarantee: gauss_code_execution must still be absent
    from sys.modules after every test in this file (41-87) has run,
    including the new reliability/output-verification tests above, none of
    which call build_production_adapter_runner(...) or import the real
    helper."""
    import sys as _sys

    check(
        "gauss_code_execution remains absent from sys.modules after the full v0.33.0/v0.34.0/v0.35.0 test set",
        "gauss_code_execution" not in _sys.modules,
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
