"""Focused unit tests for scripts/gauss_runtime_orchestration.py (v0.31.0 Phase 2).

This repository has no pytest configuration anywhere (no pyproject.toml,
setup.py/cfg, pytest.ini, or conftest.py, and pytest is not installed in the
development environment used for this project). The established, actual
testing convention -- used consistently by scripts/gauss_code_execution.py,
scripts/gauss_environment_check.py, and scripts/gauss_package_inspection.py
-- is a self-contained `check(name, condition)` harness runnable directly as
a script, with no external test framework dependency. This file follows that
same convention, run directly:

    python scripts/test_gauss_runtime_orchestration.py

Every test here is deterministic and uses only the mock/fake runner boundary
-- nothing in this file imports scripts/gauss_code_execution.py, launches a
subprocess, or invokes GAUSS.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

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
