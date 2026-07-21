"""Focused unit tests for scripts/gauss_execution_workflow.py (v0.37.0
Conversational Execution Workflow Integration).

This repository has no pytest configuration anywhere; the established
convention (see scripts/test_gauss_runtime_orchestration.py's own docstring)
is a self-contained `check(name, condition)` harness runnable directly:

    python scripts/test_gauss_execution_workflow.py

Every test in this file uses a fake runner and a disposable, temporary
SQLite database -- never the default repository-relative location, never
`gauss_execution_adapter.load_real_helper()`, never a real subprocess, never
real GAUSS. Tests are grouped to match the authorizing task's own Stage 4
coverage list: Intent and mode (1-8), Inputs and proposal (9-21),
Confirmation (22-33), Execution (34-49), Response composition (50-59).
"""

from __future__ import annotations

import multiprocessing
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_execution_workflow as wf  # noqa: E402
import gauss_orchestration_state_store as store_mod  # noqa: E402
import gauss_runtime_orchestration as orch  # noqa: E402


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
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _store(tmp: str, **kwargs: Any) -> "store_mod.OrchestrationStateStore":
    s = store_mod.OrchestrationStateStore(Path(tmp) / "test.db", **kwargs)
    s.initialize()
    return s


def _reopen_store_with_retry(db_path: Any, *, attempts: int = 40, delay: float = 0.25, **kwargs: Any) -> "store_mod.OrchestrationStateStore":
    """Windows occasionally holds a transient, non-application file lock on
    a just-closed SQLite file (e.g. antivirus real-time scanning) for a
    fraction of a second. This retry is a test-environment accommodation
    only -- gauss_orchestration_state_store.py itself performs no retry of
    any kind, per this milestone's own hard constraints."""
    import time

    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return store_mod.OrchestrationStateStore(db_path, **kwargs)
        except PermissionError as exc:
            last_exc = exc
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc


def _passing_safety() -> wf.SafetyReviewInput:
    return wf.SafetyReviewInput(
        code_shown_or_summarized=True,
        purpose_understood=True,
        does_not_delete_files=True,
        does_not_overwrite_unrelated_files=True,
        does_not_install_packages=True,
        does_not_activate_licenses=True,
        does_not_access_network=True,
        does_not_mutate_global_configuration=True,
        file_writes_relative_or_within_allowed_directory=True,
        working_directory_exists_and_safe=True,
        output_directory_within_allowed_scope=True,
        executable_is_terminal_gauss=True,
        timeout_is_set=True,
    )


def _failing_safety() -> wf.SafetyReviewInput:
    return wf.SafetyReviewInput(
        code_shown_or_summarized=True,
        purpose_understood=True,
        does_not_delete_files=True,
        does_not_overwrite_unrelated_files=False,  # the one failing item
        does_not_install_packages=True,
        does_not_activate_licenses=True,
        does_not_access_network=True,
        does_not_mutate_global_configuration=True,
        file_writes_relative_or_within_allowed_directory=True,
        working_directory_exists_and_safe=True,
        output_directory_within_allowed_scope=True,
        executable_is_terminal_gauss=True,
        timeout_is_set=True,
    )


def _eligible() -> wf.EligibilityDeclarations:
    return wf.EligibilityDeclarations(execution_explicitly_requested=True)


def _fake_runner_completed(_: "orch.RunnerInput") -> dict[str, Any]:
    return {
        "executed": True,
        "execution_status": "completed",
        "exit_code": 0,
        "stdout": "4",
        "stderr": "",
        "output_files": [],
        "warnings": [],
        "errors": [],
    }


def _fake_runner_runtime_error(_: "orch.RunnerInput") -> dict[str, Any]:
    return {
        "executed": True,
        "execution_status": "failed",
        "exit_code": 0,
        "stdout": "Program execute failed\n",
        "stderr": "error G0105 : Undefined symbol\n",
        "output_files": [],
        "warnings": [],
        "errors": ["error G0105 : Undefined symbol"],
    }


def _fake_runner_timed_out(_: "orch.RunnerInput") -> dict[str, Any]:
    return {
        "executed": True,
        "execution_status": "timed_out",
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "output_files": [],
        "warnings": [],
        "errors": [],
    }


def _fake_runner_output_created(_: "orch.RunnerInput") -> dict[str, Any]:
    return {
        "executed": True,
        "execution_status": "completed",
        "exit_code": 0,
        "stdout": "hello\n",
        "stderr": "",
        "output_files": [{"path": "C:/example/work/out.txt", "size_bytes": 5, "file_type": "text/plain", "created_by_execution": "unknown"}],
        "warnings": [],
        "errors": [],
    }


def _propose(
    workflow: "wf.ExecutionWorkflow",
    *,
    session_id: str = "s1",
    request_id: str = "r1",
    code: str | None = "x = 2 + 2;\nprint x;",
    script_path: str | None = None,
    working_directory: str | None = "C:/example/work",
    executable_path: str | None = "C:/example/gauss26/tgauss.exe",
    timeout_seconds: float | None = 30.0,
    expected_output_files: tuple[str, ...] = (),
    eligibility_declarations: "wf.EligibilityDeclarations | None" = None,
    safety_input: "wf.SafetyReviewInput | None" = None,
) -> "wf.ProposalOutcome":
    return workflow.propose_execution(
        session_id=session_id,
        request_id=request_id,
        execution_purpose="unit test",
        eligibility_declarations=eligibility_declarations or _eligible(),
        safety_input=safety_input or _passing_safety(),
        code=code,
        script_path=script_path,
        working_directory=working_directory,
        executable_path=executable_path,
        gauss_version="GAUSS 26",
        timeout_seconds=timeout_seconds,
        expected_output_files=expected_output_files,
    )


def _confirm(workflow: "wf.ExecutionWorkflow", outcome: "wf.ProposalOutcome", *, session_id: str = "s1", request_id: str = "r1") -> "wf.ConfirmationOutcome":
    assert outcome.proposal is not None
    return workflow.confirm_execution(
        wf.WorkflowConfirmationEvent(
            session_id=session_id,
            orchestration_instance_id=outcome.orchestration_instance_id,
            request_id=request_id,
            request_hash=outcome.proposal.request_hash,
            decision="accepted",
            timestamp="t1",
            source_interaction_id="turn-1",
            plan_digest=outcome.proposal.plan_digest,
        )
    )


# ---------------------------------------------------------------------------
# Intent and mode (1-8)
# ---------------------------------------------------------------------------


def test_01_advisory_request_stays_advisory() -> None:
    mode = wf.classify_interaction_mode(wf.IntentSignal())
    check("bare signal is advisory", mode == wf.InteractionMode.ADVISORY)


def test_02_explain_request_stays_non_executing() -> None:
    mode = wf.classify_interaction_mode(wf.IntentSignal(requested_mode_hint=wf.InteractionMode.EXPLAIN_CODE))
    check("explain hint passes through, never executes", mode == wf.InteractionMode.EXPLAIN_CODE)


def test_03_review_request_stays_non_executing() -> None:
    mode = wf.classify_interaction_mode(wf.IntentSignal(requested_mode_hint=wf.InteractionMode.REVIEW_CODE))
    check("review hint passes through, never executes", mode == wf.InteractionMode.REVIEW_CODE)


def test_04_revision_request_stays_non_executing() -> None:
    mode = wf.classify_interaction_mode(wf.IntentSignal(requested_mode_hint=wf.InteractionMode.REVISE_CODE))
    check("revise hint passes through, never executes", mode == wf.InteractionMode.REVISE_CODE)


def test_05_explicit_execution_request_prepares_a_plan() -> None:
    mode = wf.classify_interaction_mode(
        wf.IntentSignal(execution_explicitly_requested=True, code_present=True)
    )
    check("explicit request + code prepares a plan", mode == wf.InteractionMode.PREPARE_EXECUTION_PLAN)


def test_06_ambiguous_request_does_not_execute() -> None:
    mode = wf.classify_interaction_mode(
        wf.IntentSignal(execution_explicitly_requested=True, code_present=False)
    )
    check("explicit request without code fails closed to advisory", mode == wf.InteractionMode.ADVISORY)


def test_07_code_presence_alone_does_not_execute() -> None:
    mode = wf.classify_interaction_mode(wf.IntentSignal(code_present=True))
    check("code presence alone stays advisory", mode == wf.InteractionMode.ADVISORY)


def test_08_try_this_without_confirmation_does_not_execute() -> None:
    # "try this" carries no explicit execution flag from the agent's own
    # structured classification -- this module never parses the phrase
    # itself, so an unset execution_explicitly_requested flag (even with a
    # PREPARE_EXECUTION_PLAN hint attached) must fail closed to advisory.
    mode = wf.classify_interaction_mode(
        wf.IntentSignal(requested_mode_hint=wf.InteractionMode.PREPARE_EXECUTION_PLAN, code_present=True)
    )
    check("a mode hint alone, without the explicit flag, fails closed to advisory", mode == wf.InteractionMode.ADVISORY)


# ---------------------------------------------------------------------------
# Inputs and proposal (9-21)
# ---------------------------------------------------------------------------


def test_09_missing_code() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow, code=None)
        check("missing code blocks the proposal", outcome.blocked)
        s.close()


def test_10_missing_environment() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow, executable_path=None)
        check("missing executable_path blocks the proposal", outcome.blocked)
        s.close()


def test_11_missing_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow, working_directory=None)
        check("missing working_directory blocks the proposal", outcome.blocked)
        s.close()


def test_12_unsafe_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(
            workflow,
            eligibility_declarations=wf.EligibilityDeclarations(
                execution_explicitly_requested=True, writes_outside_working_directory=True
            ),
        )
        check("writes-outside-directory blocks the proposal", outcome.blocked)
        check("blocked for ineligibility", outcome.failure_category == "ineligible_request")
        s.close()


def test_13_untrusted_script_path_request() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow, code=None, script_path="C:/example/work/script.gss")
        check("script-path request blocks the proposal", outcome.blocked)
        s.close()


def test_14_ineligible_request() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(
            workflow,
            eligibility_declarations=wf.EligibilityDeclarations(
                execution_explicitly_requested=True, requires_package_install=True
            ),
        )
        check("package-install requirement blocks the proposal", outcome.blocked)
        s.close()


def test_15_unsafe_request() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow, safety_input=_failing_safety())
        check("failing safety review blocks the proposal", outcome.blocked)
        check("blocked for unsafe_request", outcome.failure_category == "unsafe_request")
        s.close()


def test_16_valid_inline_code_proposal() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        check("valid proposal is not blocked", not outcome.blocked)
        assert outcome.proposal is not None
        check("proposal carries a code_digest, not raw code", outcome.proposal.code_digest is not None)
        check("proposal known_limitations is non-empty", len(outcome.proposal.known_limitations) > 0)
        s.close()


def test_17_stable_plan_rendering() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        assert outcome.proposal is not None
        check("plan_digest equals request_hash", outcome.proposal.plan_digest == outcome.proposal.request_hash)
        s.close()


def test_18_stable_request_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome_a = _propose(workflow, request_id="req-a")
        outcome_b = _propose(workflow, request_id="req-b")
        assert outcome_a.proposal is not None and outcome_b.proposal is not None
        check(
            "identical fields (differing only by request_id) produce the same request_hash",
            outcome_a.proposal.request_hash == outcome_b.proposal.request_hash,
        )
        check(
            "identical hashes still produce distinct orchestration instances",
            outcome_a.orchestration_instance_id != outcome_b.orchestration_instance_id,
        )
        s.close()


def test_19_changed_code_changes_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome_a = _propose(workflow, request_id="req-a", code="x = 1;")
        outcome_b = _propose(workflow, request_id="req-b", code="x = 2;")
        assert outcome_a.proposal is not None and outcome_b.proposal is not None
        check("changed code changes request_hash", outcome_a.proposal.request_hash != outcome_b.proposal.request_hash)
        s.close()


def test_20_changed_output_changes_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome_a = _propose(workflow, request_id="req-a", expected_output_files=())
        outcome_b = _propose(workflow, request_id="req-b", expected_output_files=("out.txt",))
        assert outcome_a.proposal is not None and outcome_b.proposal is not None
        check(
            "changed expected_output_files changes request_hash",
            outcome_a.proposal.request_hash != outcome_b.proposal.request_hash,
        )
        s.close()


def test_21_changed_timeout_changes_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome_a = _propose(workflow, request_id="req-a", timeout_seconds=30.0)
        outcome_b = _propose(workflow, request_id="req-b", timeout_seconds=60.0)
        assert outcome_a.proposal is not None and outcome_b.proposal is not None
        check("changed timeout changes request_hash", outcome_a.proposal.request_hash != outcome_b.proposal.request_hash)
        s.close()


# ---------------------------------------------------------------------------
# Confirmation (22-33)
# ---------------------------------------------------------------------------


def test_22_accepted_exact_confirmation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        confirmation = _confirm(workflow, outcome)
        check("accepted confirmation reaches confirmed", confirmation.current_state == "confirmed")
        check("confirmation outcome reports accepted", confirmation.accepted)
        s.close()


def test_23_rejected_confirmation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        assert outcome.proposal is not None
        confirmation = workflow.confirm_execution(
            wf.WorkflowConfirmationEvent(
                session_id="s1", orchestration_instance_id=outcome.orchestration_instance_id, request_id="r1",
                request_hash=outcome.proposal.request_hash, decision="rejected", timestamp="t1",
                source_interaction_id="turn-1", plan_digest=outcome.proposal.plan_digest,
            )
        )
        check("rejected confirmation reaches cancelled", confirmation.current_state == "cancelled")
        check("confirmation outcome reports not accepted", not confirmation.accepted)
        s.close()


def test_24_missing_confirmation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        check_raises(
            "executing without any confirmation fails closed",
            orch.InvalidTransitionError,
            workflow.execute, outcome.orchestration_instance_id, runner=_fake_runner_completed,
        )
        s.close()


def test_25_stale_confirmation_plan_digest_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        assert outcome.proposal is not None
        check_raises(
            "a plan_digest not matching request_hash is refused before the controller is consulted",
            wf.ConfirmationValidationError,
            workflow.confirm_execution,
            wf.WorkflowConfirmationEvent(
                session_id="s1", orchestration_instance_id=outcome.orchestration_instance_id, request_id="r1",
                request_hash=outcome.proposal.request_hash, decision="accepted", timestamp="t1",
                source_interaction_id="turn-1", plan_digest="stale-digest-from-an-earlier-plan",
            ),
        )
        s.close()


def test_26_expired_confirmation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        clock_value = [1000.0]

        def clock() -> float:
            return clock_value[0]

        s = _store(tmp, clock=clock, confirmation_ttl_seconds=5.0)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        clock_value[0] += 10.0  # advance past the 5-second TTL
        check_raises(
            "an expired confirmation is refused at invocation time",
            orch.GuardFailedError,
            workflow.execute, outcome.orchestration_instance_id, runner=_fake_runner_completed,
        )
        s.close()


def test_27_wrong_session() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow, session_id="s1")
        assert outcome.proposal is not None
        check_raises(
            "a confirmation from the wrong session is refused",
            orch.SessionMismatchError,
            workflow.confirm_execution,
            wf.WorkflowConfirmationEvent(
                session_id="s-intruder", orchestration_instance_id=outcome.orchestration_instance_id, request_id="r1",
                request_hash=outcome.proposal.request_hash, decision="accepted", timestamp="t1",
                source_interaction_id="turn-1", plan_digest=outcome.proposal.plan_digest,
            ),
        )
        s.close()


def test_28_wrong_request_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow, request_id="r1")
        assert outcome.proposal is not None
        check_raises(
            "a confirmation naming the wrong request_id is refused",
            wf.ConfirmationValidationError,
            workflow.confirm_execution,
            wf.WorkflowConfirmationEvent(
                session_id="s1", orchestration_instance_id=outcome.orchestration_instance_id, request_id="r-wrong",
                request_hash=outcome.proposal.request_hash, decision="accepted", timestamp="t1",
                source_interaction_id="turn-1", plan_digest=outcome.proposal.plan_digest,
            ),
        )
        s.close()


def test_29_wrong_request_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        assert outcome.proposal is not None
        wrong_hash = "0" * 64
        check_raises(
            "a confirmation scoped to the wrong request_hash is refused by the controller",
            orch.ConfirmationScopeMismatchError,
            workflow.confirm_execution,
            wf.WorkflowConfirmationEvent(
                session_id="s1", orchestration_instance_id=outcome.orchestration_instance_id, request_id="r1",
                request_hash=wrong_hash, decision="accepted", timestamp="t1",
                source_interaction_id="turn-1", plan_digest=wrong_hash,
            ),
        )
        s.close()


def test_30_altered_plan_invalidates_confirmation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        original = _propose(workflow, request_id="r1", code="x = 1;")
        assert original.proposal is not None
        altered = _propose(workflow, request_id="r2", code="x = 999999;")
        assert altered.proposal is not None
        check("an altered plan produces a different request_hash", original.proposal.request_hash != altered.proposal.request_hash)
        check_raises(
            "confirming the original instance with the altered plan's digest is refused",
            wf.ConfirmationValidationError,
            workflow.confirm_execution,
            wf.WorkflowConfirmationEvent(
                session_id="s1", orchestration_instance_id=original.orchestration_instance_id, request_id="r1",
                request_hash=original.proposal.request_hash, decision="accepted", timestamp="t1",
                source_interaction_id="turn-1", plan_digest=altered.proposal.request_hash,
            ),
        )
        s.close()


def test_31_confirmation_already_consumed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        check_raises(
            "confirming an already-confirmed instance a second time is refused",
            orch.InvalidTransitionError,
            _confirm, workflow, outcome,
        )
        s.close()


def test_32_confirmation_after_restart() -> None:
    """Confirmation itself durably survives a simulated process restart --
    but actually INVOKING it from the restarted process does not, and must
    not, silently succeed: `reload_orchestration_instance(...)` always
    leaves `request=None` (raw code is never durably persisted, a
    deliberate v0.36.0 design choice this module inherits unchanged), so
    `execute()` against a reloaded instance always fails closed with
    `GuardFailedError`. Only the ORIGINAL process -- the one that built the
    proposal and still holds the live `CanonicalExecutionRequest` in memory
    -- can ever complete the invocation. This is a genuine, disclosed
    architectural boundary discovered while writing this test, not a bug:
    it trades cross-process resumability of an in-flight confirmed request
    for never storing raw GAUSS code."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "restart.db"
        s1 = store_mod.OrchestrationStateStore(db_path)
        s1.initialize()
        workflow1 = wf.ExecutionWorkflow(state_store=s1)
        outcome = _propose(workflow1)
        _confirm(workflow1, outcome)

        rec_before = s1.load_record(outcome.orchestration_instance_id)
        check("confirmation durably recorded before restart", rec_before.confirmation_status == "accepted")
        check("confirmation not yet consumed before restart", not rec_before.confirmation_consumed)
        s1.close()  # simulated process exit

        s2 = _reopen_store_with_retry(db_path)  # simulated fresh process
        rec_after = s2.load_record(outcome.orchestration_instance_id)
        check("confirmation status survives a simulated restart intact", rec_after.confirmation_status == "accepted")
        check("current_state survives a simulated restart intact", rec_after.current_state == "confirmed")
        assert outcome.proposal is not None
        check("request_hash survives a simulated restart intact", rec_after.request_hash == outcome.proposal.request_hash)

        workflow2 = wf.ExecutionWorkflow(state_store=s2)
        check_raises(
            "a restarted process without the live request cannot invoke it -- fails closed, never silently",
            orch.GuardFailedError,
            workflow2.execute, outcome.orchestration_instance_id, runner=_fake_runner_completed,
        )
        check(
            "confirmation remains unconsumed after the failed restart-based attempt",
            not s2.load_record(outcome.orchestration_instance_id).confirmation_consumed,
        )
        s2.close()

        # The ORIGINAL process still holds the live request and can still
        # complete the invocation once reattached to a fresh, open connection.
        s3 = _reopen_store_with_retry(db_path)
        workflow1._state_store = s3
        instance = workflow1._instances[outcome.orchestration_instance_id]
        instance._state_store = s3
        final_result = workflow1.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("the original request-holding process can still complete the invocation after restart", final_result.executed)
        s3.close()


def test_33_confirmation_cannot_transfer_to_a_rerun() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check_raises(
            "a completed instance always refuses request_rerun",
            wf.RerunRequiresNewRequestError,
            workflow.request_rerun, outcome.orchestration_instance_id,
        )
        check_raises(
            "a second invoke on the same instance is refused outright, confirming no transferred confirmation",
            orch.InvalidTransitionError,
            workflow.execute, outcome.orchestration_instance_id, runner=_fake_runner_completed,
        )
        s.close()


# ---------------------------------------------------------------------------
# Execution (34-49)
# ---------------------------------------------------------------------------


def test_34_durable_record_created() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        rec = s.load_record(outcome.orchestration_instance_id)
        check("a durable record exists immediately after proposal", rec.current_state == "awaiting_confirmation")
        s.close()


def test_35_durable_authorization_required() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        rec = s.load_record(outcome.orchestration_instance_id)
        check("durable confirmation was consumed by authorization", rec.confirmation_consumed)
        check("durable invocation_id was recorded", rec.invocation_id is not None)
        s.close()


def test_36_controller_invoked_once() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        calls = []

        def counting_runner(ri: "orch.RunnerInput") -> dict[str, Any]:
            calls.append(1)
            return _fake_runner_completed(ri)

        workflow.execute(outcome.orchestration_instance_id, runner=counting_runner)
        check_raises(
            "a second execute() attempt is refused",
            orch.InvalidTransitionError,
            workflow.execute, outcome.orchestration_instance_id, runner=counting_runner,
        )
        check("the runner was called exactly once", len(calls) == 1)
        s.close()


def test_37_direct_adapter_helper_path_absent() -> None:
    check(
        "the workflow module has no direct binding to gauss_execution_adapter",
        not hasattr(wf, "gauss_execution_adapter"),
    )
    check(
        "the workflow module has no direct binding to gauss_code_execution",
        not hasattr(wf, "gauss_code_execution"),
    )


def test_38_completed_result() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("completed result reports executed", result.executed)
        check("completed result reaches execution_completed", result.final_orchestration_state == "execution_completed")
        check("completed result reports no runtime error", not result.runtime_error_detected)
        s.close()


def test_39_runtime_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_runtime_error)
        check("runtime-error result still reports executed (the helper ran)", result.executed)
        check("runtime-error result flags runtime_error_detected", result.runtime_error_detected)
        check("runtime-error result reaches execution_failed", result.final_orchestration_state == "execution_failed")
        s.close()


def test_40_timeout() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_timed_out)
        check("timed-out result flags timed_out", result.timed_out)
        check("timed-out result does not flag a runtime error", not result.runtime_error_detected)
        s.close()


def test_41_missing_expected_output() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow, expected_output_files=("does_not_exist.txt",))
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("missing-output result flags missing_expected_output", result.missing_expected_output)
        check("missing-output result does not flag a runtime error", not result.runtime_error_detected)
        s.close()


def test_42_malformed_result() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)

        def malformed_runner(_: "orch.RunnerInput") -> dict[str, Any]:
            return {"executed": True}  # missing every other required key

        result = workflow.execute(outcome.orchestration_instance_id, runner=malformed_runner)
        check("malformed result reports executed=False (never treated as valid evidence)", not result.executed)
        check("malformed result is flagged as malformed_result", result.failure_category == "malformed_result")
        s.close()


def test_43_helper_unavailable_launch_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)

        def unavailable_runner(_: "orch.RunnerInput") -> dict[str, Any]:
            raise RuntimeError("the helper dependency is unavailable in this environment")

        result = workflow.execute(outcome.orchestration_instance_id, runner=unavailable_runner)
        check("launch failure reports executed=False", not result.executed)
        check("launch failure is flagged as runner_launch_failure", result.failure_category == "runner_launch_failure")
        s.close()


def test_44_environment_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        calls = []

        def counting_runner(ri: "orch.RunnerInput") -> dict[str, Any]:
            calls.append(1)
            return _fake_runner_completed(ri)

        result = workflow.execute(outcome.orchestration_instance_id, runner=counting_runner, environment_still_matches=False)
        check("environment mismatch cancels rather than executing", result.final_orchestration_state == "cancelled")
        check("environment mismatch is the recorded failure_category", result.failure_category == "environment_mismatch")
        check("the runner was never called", len(calls) == 0)
        s.close()


def test_45_cancellation_before_authorization() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        result = workflow.cancel(outcome.orchestration_instance_id)
        check("pre-invocation cancellation reaches cancelled", result.final_orchestration_state == "cancelled")
        check("pre-invocation cancellation records cancellation_before_execution", result.failure_category == "cancellation_before_execution")
        s.close()


def test_46_cancellation_during_synchronous_execution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        instance = workflow._instances[outcome.orchestration_instance_id]
        # Synchronous invocation cannot truly be interrupted mid-call -- this
        # mirrors gauss_runtime_orchestration's own established test pattern
        # (test_19-style) of forcing EXECUTING to exercise the
        # intent-only cancellation path honestly, without claiming
        # cooperative cancellation exists.
        object.__setattr__(instance.record, "current_state", orch.OrchestrationState.EXECUTING)
        instance.cancel(note="user requested stop mid-run")
        check(
            "cancellation during execution records intent only, without claiming interruption",
            instance.record.cancellation_status == orch.CancellationStatus.CANCEL_REQUESTED_DURING_INVOCATION,
        )
        s.close()


def test_47_state_loss_unknown_instance() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        check_raises(
            "inspecting an unknown instance fails closed",
            wf.UnknownInstanceError,
            workflow.inspect, "instance-that-was-never-created",
        )
        s.close()


def test_48_durable_corruption_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        workflow._instances.pop(outcome.orchestration_instance_id, None)  # force the durable-record path
        s._conn.execute(
            "UPDATE orchestration_records SET current_state = 'not_a_real_state' WHERE orchestration_instance_id = ?",
            (outcome.orchestration_instance_id,),
        )
        check_raises(
            "inspecting a corrupted record fails closed rather than silently returning something",
            store_mod.CorruptStateError,
            workflow.inspect, outcome.orchestration_instance_id,
        )
        s.close()


def _cross_process_execute_worker(db_path: str, instance_id: str, queue: "multiprocessing.Queue") -> None:
    import sys as _sys
    from pathlib import Path as _Path

    _script_dir = _Path(__file__).resolve().parent
    if str(_script_dir) not in _sys.path:
        _sys.path.insert(0, str(_script_dir))
    import gauss_execution_workflow as _wf
    import gauss_orchestration_state_store as _store_mod

    def _runner(_ri: Any) -> dict[str, Any]:
        return {
            "executed": True, "execution_status": "completed", "exit_code": 0, "stdout": "ok",
            "stderr": "", "output_files": [], "warnings": [], "errors": [],
        }

    store = _store_mod.OrchestrationStateStore(db_path)
    workflow = _wf.ExecutionWorkflow(state_store=store)
    try:
        workflow.execute(instance_id, runner=_runner)
        queue.put("success")
    except Exception as exc:  # noqa: BLE001
        queue.put(f"failure:{type(exc).__name__}")
    finally:
        store.close()


def test_49_cross_process_duplicate_attempt_blocked() -> None:
    """A reloaded instance's `request` is always `None` by design (durable
    state never stores raw code -- gauss_runtime_orchestration.
    reload_orchestration_instance's own documented behavior). This means
    `execute()` against a reloaded instance always fails closed with
    GuardFailedError, in any process that did not itself build the
    proposal -- cross-process duplicate *invocation* is not merely
    blocked by a race-losing error here; it is structurally impossible for
    any process other than the one holding the live, in-memory
    CanonicalExecutionRequest. This is verified below for three racing
    "cold" processes, none of which can invoke at all. Genuine cross-process
    authorize_invocation races AT THE DURABLE-STORE LAYER (the mechanism
    this fact ultimately rests on) were already verified directly in
    v0.36.0 (scripts/test_gauss_orchestration_state_store_concurrency.py)
    and are inherited unchanged; this test additionally confirms that none
    of the three failed attempts corrupted or silently advanced the durable
    record, and that the ORIGINAL request-holding process can still
    legitimately complete the invocation afterward."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "concurrency.db")
        s = store_mod.OrchestrationStateStore(db_path)
        s.initialize()
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        s.close()  # release before racing "cold" processes reopen it

        ctx = multiprocessing.get_context("spawn")
        queue: "multiprocessing.Queue" = ctx.Queue()
        procs = [
            ctx.Process(target=_cross_process_execute_worker, args=(db_path, outcome.orchestration_instance_id, queue))
            for _ in range(3)
        ]
        for p in procs:
            p.start()
        for p in procs:
            p.join(timeout=60)

        results = [queue.get(timeout=5) for _ in procs]
        check(
            f"every cold process without a live in-memory request fails closed (got {results})",
            all(r == "failure:GuardFailedError" for r in results),
        )

        s2 = _reopen_store_with_retry(db_path)
        rec = s2.load_record(outcome.orchestration_instance_id)
        check("the durable record was never advanced by any failed cross-process attempt", rec.current_state == "confirmed")
        s2.close()

        # This process still holds the live request in memory (it was never
        # reloaded) -- reattaching a fresh, open connection lets the
        # ORIGINAL holder complete the invocation the cold processes could
        # not, proving the confirmation was never wrongly consumed.
        s3 = _reopen_store_with_retry(db_path)
        workflow._state_store = s3
        instance = workflow._instances[outcome.orchestration_instance_id]
        instance._state_store = s3
        final_result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("the original request-holding process can still complete the invocation", final_result.executed)
        s3.close()


# ---------------------------------------------------------------------------
# Response composition (50-59)
# ---------------------------------------------------------------------------


def test_50_clear_statement_execution_occurred() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("executed is explicitly True", result.executed is True)
        s.close()


def test_51_clear_statement_when_execution_did_not_occur() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        result = workflow.inspect(outcome.orchestration_instance_id)
        check("executed is explicitly False before any invocation", result.executed is False)
        s.close()


def test_52_runtime_error_distinct_from_system_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)

        outcome_a = _propose(workflow, request_id="req-a")
        _confirm(workflow, outcome_a, request_id="req-a")
        runtime_error_result = workflow.execute(outcome_a.orchestration_instance_id, runner=_fake_runner_runtime_error)

        outcome_b = _propose(workflow, request_id="req-b")
        _confirm(workflow, outcome_b, request_id="req-b")

        def launch_failure_runner(_: "orch.RunnerInput") -> dict[str, Any]:
            raise RuntimeError("system-level launch failure")

        system_error_result = workflow.execute(outcome_b.orchestration_instance_id, runner=launch_failure_runner)

        check("a genuine GAUSS runtime error is flagged runtime_error_detected", runtime_error_result.runtime_error_detected)
        check("a launch/system failure is NOT flagged runtime_error_detected", not system_error_result.runtime_error_detected)
        check(
            "the two failure categories are distinct",
            runtime_error_result.failure_category != system_error_result.failure_category,
        )
        s.close()


def test_53_missing_output_distinct_from_runtime_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)

        outcome_a = _propose(workflow, request_id="req-a", expected_output_files=("missing.txt",))
        _confirm(workflow, outcome_a, request_id="req-a")
        missing_result = workflow.execute(outcome_a.orchestration_instance_id, runner=_fake_runner_completed)

        outcome_b = _propose(workflow, request_id="req-b")
        _confirm(workflow, outcome_b, request_id="req-b")
        error_result = workflow.execute(outcome_b.orchestration_instance_id, runner=_fake_runner_runtime_error)

        check("missing output does not also flag a runtime error", missing_result.missing_expected_output and not missing_result.runtime_error_detected)
        check("a runtime error does not also flag missing output", error_result.runtime_error_detected and not error_result.missing_expected_output)
        s.close()


def test_54_output_metadata_not_represented_as_content() -> None:
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(wf.OutputFileSummary)}
    check("OutputFileSummary has no 'content' field", "content" not in field_names)


def test_55_exit_code_described_as_non_authoritative() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("exit_code is always disclosed as non-authoritative", result.exit_code_is_authoritative is False)
        s.close()


def test_56_methodology_caveat_included() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("methodology_caveat is a non-empty string", isinstance(result.methodology_caveat, str) and len(result.methodology_caveat) > 0)
        s.close()


def test_57_limitations_included() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("limitations is non-empty on every response-ready result", len(result.limitations) > 0)
        s.close()


def test_58_new_request_required_for_rerun() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("rerun_requires_new_request is always True", result.rerun_requires_new_request is True)
        s.close()


def test_59_prior_result_remains_available() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        workflow = wf.ExecutionWorkflow(state_store=s)
        outcome = _propose(workflow)
        _confirm(workflow, outcome)
        executed_result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        inspected_result = workflow.inspect(outcome.orchestration_instance_id)
        check("a prior execution result remains available via inspect()", inspected_result.execution_status == executed_result.execution_status)
        check("a prior execution's exit_code remains available via inspect()", inspected_result.exit_code == executed_result.exit_code)
        s.close()


def test_60_module_never_imports_the_real_helper() -> None:
    check("gauss_code_execution remains absent from sys.modules", "gauss_code_execution" not in sys.modules)


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
