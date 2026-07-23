"""End-to-end unit tests for scripts/gauss_code_assistant_workflow.py
(v0.45.0 GAUSS Code Assistant MVP Workflow).

This repository has no pytest configuration anywhere; the established
convention is a self-contained `check(name, condition)` harness runnable
directly:

    python scripts/test_code_assistant_mvp_workflow.py

Every test uses fake runners, disposable temporary directories, and never
invokes GAUSS. This file tests *orchestration* -- that the facade correctly
sequences and reports on gauss_execution_workflow.py/gauss_workspace.py/
gauss_workspace_file_reader.py -- not those modules' own internal
correctness a second time (already exhaustively covered by their own test
suites).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_code_assistant_workflow as mvp  # noqa: E402
import gauss_execution_workflow as wf  # noqa: E402
import gauss_orchestration_state_store as store_mod  # noqa: E402
import gauss_runtime_orchestration as orch  # noqa: E402
import gauss_workspace as gw  # noqa: E402
import gauss_workspace_file_reader as file_reader_mod  # noqa: E402

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
# Fixtures
# ---------------------------------------------------------------------------


def _passing_safety() -> wf.SafetyReviewInput:
    return wf.SafetyReviewInput(
        code_shown_or_summarized=True, purpose_understood=True, does_not_delete_files=True,
        does_not_overwrite_unrelated_files=True, does_not_install_packages=True, does_not_activate_licenses=True,
        does_not_access_network=True, does_not_mutate_global_configuration=True,
        file_writes_relative_or_within_allowed_directory=True, working_directory_exists_and_safe=True,
        output_directory_within_allowed_scope=True, executable_is_terminal_gauss=True, timeout_is_set=True,
    )


def _fake_runner_completed(_: "orch.RunnerInput") -> dict[str, Any]:
    return {
        "executed": True, "execution_status": "completed", "exit_code": 0, "stdout": "4", "stderr": "",
        "output_files": [], "warnings": [], "errors": [],
    }


def _fake_runner_runtime_error(_: "orch.RunnerInput") -> dict[str, Any]:
    return {
        "executed": True, "execution_status": "failed", "exit_code": 0, "stdout": "Program execute failed\n",
        "stderr": "error G0105 : Undefined symbol\n", "output_files": [], "warnings": [],
        "errors": ["error G0105 : Undefined symbol"],
    }


def _make_output_runner(workspace_root: str, filename: str, content: bytes):
    def runner(_: "orch.RunnerInput") -> dict[str, Any]:
        path = Path(workspace_root) / filename
        path.write_bytes(content)
        return {
            "executed": True, "execution_status": "completed", "exit_code": 0, "stdout": "ok", "stderr": "",
            "output_files": [{"path": str(path), "size_bytes": len(content), "file_type": "text/plain", "created_by_execution": "unknown"}],
            "warnings": [], "errors": [],
        }

    return runner


class _Rig:
    """Bundles a facade + its own disposable temp directories for one test."""

    def __init__(self) -> None:
        self._ws_tmp = tempfile.TemporaryDirectory()
        self._db_tmp = tempfile.TemporaryDirectory()
        self.registry = gw.WorkspaceRegistry(approved_parent_directory=self._ws_tmp.name)
        self.store = store_mod.OrchestrationStateStore(Path(self._db_tmp.name) / "test.db")
        self.store.initialize()
        self.execution_workflow = wf.ExecutionWorkflow(state_store=self.store, workspace_registry=self.registry)
        self.facade = mvp.GaussCodeAssistantWorkflow(execution_workflow=self.execution_workflow, workspace_registry=self.registry)

    def new_ready_workspace(self) -> "gw.Workspace":
        workspace = self.registry.create_workspace()
        Path(workspace.root_path).mkdir(parents=True, exist_ok=True)
        self.registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.POPULATED)
        self.registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.READY)
        return workspace

    def propose(self, session: "mvp.MvpWorkflowSession", *, workspace_id: str, request_id: str = "r1", code: str | None = "x = 2 + 2;\nprint x;", eligibility: "wf.EligibilityDeclarations | None" = None, safety: "wf.SafetyReviewInput | None" = None) -> "wf.ProposalOutcome":
        return self.facade.propose(
            session, request_summary="test request", session_id="s1", request_id=request_id,
            execution_purpose="mvp test", eligibility_declarations=eligibility or wf.EligibilityDeclarations(execution_explicitly_requested=True),
            safety_input=safety or _passing_safety(), code=code, executable_path="C:/example/gauss26/tgauss.exe",
            gauss_version="GAUSS 26", timeout_seconds=30.0, workspace_id=workspace_id,
        )

    def confirm(self, session: "mvp.MvpWorkflowSession", *, decision: str = "accepted", request_id: str = "r1") -> "wf.ConfirmationOutcome":
        assert session.proposal_outcome is not None and session.proposal_outcome.proposal is not None
        proposal = session.proposal_outcome.proposal
        return self.facade.confirm(
            session,
            wf.WorkflowConfirmationEvent(
                session_id="s1", orchestration_instance_id=session.orchestration_instance_id, request_id=request_id,
                request_hash=proposal.request_hash, decision=decision, timestamp="t1",
                source_interaction_id="turn-1", plan_digest=proposal.plan_digest,
            ),
        )

    def close(self) -> None:
        self.store.close()
        self._ws_tmp.cleanup()
        self._db_tmp.cleanup()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_01_advisory_response_never_touches_execution() -> None:
    rig = _Rig()
    result = rig.facade.advisory_response(request_summary="explain this", mode=wf.InteractionMode.EXPLAIN_CODE)
    check("advisory result has no execution_status", result.execution_status is None)
    check("advisory result has no workspace_id", result.workspace_id is None)
    check("advisory summary mentions no code was run", "No code was run" in result.user_facing_summary)
    rig.close()


def test_02_full_happy_path_orchestration_and_stage_transitions() -> None:
    rig = _Rig()
    workspace = rig.new_ready_workspace()
    session = mvp.MvpWorkflowSession()
    check("session starts in REQUEST_RECEIVED", session.stage == mvp.CodeAssistantStage.REQUEST_RECEIVED)

    outcome = rig.propose(session, workspace_id=workspace.workspace_id)
    check("proposal is not blocked", not outcome.blocked)
    check("session reaches PLAN_PROPOSED", session.stage == mvp.CodeAssistantStage.PLAN_PROPOSED)

    rig.confirm(session)
    check("session reaches CONFIRMED", session.stage == mvp.CodeAssistantStage.CONFIRMED)

    rig.facade.execute(session, runner=_fake_runner_completed)
    check("session reaches EXECUTED", session.stage == mvp.CodeAssistantStage.EXECUTED)

    final = rig.facade.compose_response(session)
    check("session reaches RESPONDED", session.stage == mvp.CodeAssistantStage.RESPONDED)
    check("final result reports completed execution_status", final.execution_status == "completed")
    check("final result carries the execution_session_reference", final.execution_session_reference == session.orchestration_instance_id)
    check("final result carries the workspace_id", final.workspace_id == workspace.workspace_id)
    rig.close()


def test_03_blocked_proposal_reaches_declined_with_reason() -> None:
    rig = _Rig()
    workspace = rig.new_ready_workspace()
    session = mvp.MvpWorkflowSession()
    outcome = rig.propose(session, workspace_id=workspace.workspace_id, code=None)  # missing code -> ineligible
    check("proposal blocked", outcome.blocked)
    check("session reaches DECLINED", session.stage == mvp.CodeAssistantStage.DECLINED)

    final = rig.facade.compose_response(session)
    check("declined result has no execution_status", final.execution_status is None)
    check("declined summary explains the decline", "declined" in final.user_facing_summary.lower())
    rig.close()


def test_04_rejected_confirmation_reaches_declined() -> None:
    rig = _Rig()
    workspace = rig.new_ready_workspace()
    session = mvp.MvpWorkflowSession()
    rig.propose(session, workspace_id=workspace.workspace_id)
    rig.confirm(session, decision="rejected")
    check("session reaches DECLINED after rejection", session.stage == mvp.CodeAssistantStage.DECLINED)

    final = rig.facade.compose_response(session)
    check("rejected-confirmation summary is distinct", "not confirmed" in final.user_facing_summary.lower())
    rig.close()


def test_05_execution_runtime_error_still_reaches_executed() -> None:
    rig = _Rig()
    workspace = rig.new_ready_workspace()
    session = mvp.MvpWorkflowSession()
    rig.propose(session, workspace_id=workspace.workspace_id)
    rig.confirm(session)
    result = rig.facade.execute(session, runner=_fake_runner_runtime_error)
    check("a runtime error still reaches EXECUTED (a failure is a result, not a facade error)", session.stage == mvp.CodeAssistantStage.EXECUTED)
    check("execution result flags the runtime error", result.runtime_error_detected)

    final = rig.facade.compose_response(session)
    check("summary surfaces the runtime error distinctly", "runtime error" in final.user_facing_summary.lower())
    rig.close()


def test_06_explicit_file_read_appears_in_result() -> None:
    rig = _Rig()
    workspace = rig.new_ready_workspace()
    session = mvp.MvpWorkflowSession()
    rig.propose(session, workspace_id=workspace.workspace_id)
    rig.confirm(session)
    runner = _make_output_runner(workspace.root_path, "results.csv", b"a,b\n1,2\n")
    rig.facade.execute(session, runner=runner)

    read_result = rig.facade.read_file(
        session, file_reader_mod.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="results.csv")
    )
    check("explicit read succeeds", read_result.status == file_reader_mod.ReadStatus.COMPLETED.value)

    final = rig.facade.compose_response(session)
    check("final result includes the file read", len(final.files_read) == 1)
    check("summary mentions the read file", "results.csv" in final.user_facing_summary)
    rig.close()


def test_07_file_read_failure_reported_distinctly_from_execution_failure() -> None:
    rig = _Rig()
    workspace = rig.new_ready_workspace()
    session = mvp.MvpWorkflowSession()
    rig.propose(session, workspace_id=workspace.workspace_id)
    rig.confirm(session)
    rig.facade.execute(session, runner=_fake_runner_completed)

    read_result = rig.facade.read_file(
        session, file_reader_mod.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="never_written.csv")
    )
    check("read attempt fails on its own terms", read_result.status != file_reader_mod.ReadStatus.COMPLETED.value)
    check("execution itself remains reported as completed, unaffected by the read failure", session.execution_result is not None and session.execution_result.executed)
    rig.close()


def test_08_out_of_order_stage_calls_rejected() -> None:
    rig = _Rig()
    workspace = rig.new_ready_workspace()

    session_a = mvp.MvpWorkflowSession()
    check_raises(
        "execute() before propose()/confirm() is rejected",
        mvp.MvpWorkflowStageError, rig.facade.execute, session_a, runner=_fake_runner_completed,
    )

    session_b = mvp.MvpWorkflowSession()
    rig.propose(session_b, workspace_id=workspace.workspace_id)
    check_raises(
        "execute() before confirm() is rejected",
        mvp.MvpWorkflowStageError, rig.facade.execute, session_b, runner=_fake_runner_completed,
    )

    session_c = mvp.MvpWorkflowSession()
    rig.propose(session_c, workspace_id=workspace.workspace_id)
    check_raises(
        "proposing a second time on the same session is rejected",
        mvp.MvpWorkflowStageError, rig.propose, session_c, workspace_id=workspace.workspace_id, request_id="r2",
    )
    rig.close()


def test_09_read_file_rejects_workspace_mismatch() -> None:
    rig = _Rig()
    workspace_a = rig.new_ready_workspace()
    workspace_b = rig.new_ready_workspace()
    session = mvp.MvpWorkflowSession()
    rig.propose(session, workspace_id=workspace_a.workspace_id)
    rig.confirm(session)
    rig.facade.execute(session, runner=_fake_runner_completed)

    check_raises(
        "reading a file request targeting a different workspace than the session's own is rejected",
        ValueError, rig.facade.read_file, session,
        file_reader_mod.WorkspaceFileReadRequest(workspace_id=workspace_b.workspace_id, relative_path="anything.txt"),
    )
    rig.close()


def test_10_provenance_captured_in_workflow_result() -> None:
    rig = _Rig()
    workspace = rig.new_ready_workspace()
    session = mvp.MvpWorkflowSession()
    rig.propose(session, workspace_id=workspace.workspace_id)
    rig.confirm(session)
    runner = _make_output_runner(workspace.root_path, "out.log", b"log line\n")
    rig.facade.execute(session, runner=runner)

    final = rig.facade.compose_response(session)
    check("final result carries provenance", final.provenance is not None)
    assert final.provenance is not None
    check("provenance references the correct workspace", final.provenance.workspace_id == workspace.workspace_id)
    check("provenance has one artifact", len(final.provenance.artifacts) == 1)
    rig.close()


def test_11_two_workspaces_remain_isolated_across_sessions() -> None:
    rig = _Rig()
    workspace_a = rig.new_ready_workspace()
    workspace_b = rig.new_ready_workspace()

    session_a = mvp.MvpWorkflowSession()
    rig.propose(session_a, workspace_id=workspace_a.workspace_id, request_id="ra")
    rig.confirm(session_a, request_id="ra")
    rig.facade.execute(session_a, runner=_make_output_runner(workspace_a.root_path, "a.txt", b"only in A\n"))

    check(
        "workspace B remains untouched by workspace A's session",
        len(rig.registry.get_workspace_manifest(workspace_b.workspace_id).files) == 0,
    )
    check(
        "workspace A's manifest reflects only its own session's output",
        len(rig.registry.get_workspace_manifest(workspace_a.workspace_id).files) == 1,
    )
    rig.close()


def test_12_compose_response_before_execution_is_honest() -> None:
    rig = _Rig()
    workspace = rig.new_ready_workspace()
    session = mvp.MvpWorkflowSession()
    rig.propose(session, workspace_id=workspace.workspace_id)
    final = rig.facade.compose_response(session)
    check("no execution occurred yet is stated plainly", "no execution has occurred" in final.user_facing_summary.lower())
    check("execution_status remains None", final.execution_status is None)
    rig.close()


def test_13_workflow_result_has_no_methodology_conclusion_field() -> None:
    import dataclasses

    result_fields = {f.name for f in dataclasses.fields(mvp.WorkflowResult)}
    for forbidden in ("methodology", "conclusion", "valid", "verdict"):
        check(f"WorkflowResult has no {forbidden!r}-shaped field", forbidden not in result_fields)
    check("WorkflowResult does carry a user_facing_summary", "user_facing_summary" in result_fields)


def test_14_select_workspace_validates_without_creating() -> None:
    rig = _Rig()
    workspace = rig.new_ready_workspace()
    outcome = rig.facade.select_workspace(workspace.workspace_id)
    check("an existing, ready workspace validates", outcome.valid)

    missing_outcome = rig.facade.select_workspace("does-not-exist")
    check("a nonexistent workspace fails validation, never silently created", not missing_outcome.valid)
    check_raises(
        "select_workspace never creates a workspace as a side effect",
        gw.WorkspaceNotFoundError, rig.registry.get_workspace, "does-not-exist",
    )
    rig.close()


def test_15_module_never_runs_gauss() -> None:
    # gauss_execution_adapter legitimately ends up in sys.modules
    # transitively (gauss_runtime_orchestration imports it at module level,
    # matching every other test file's own convention) -- the real helper,
    # gauss_code_execution, is the thing that must never be imported by
    # default, and is not.
    check("gauss_code_execution is absent from sys.modules", "gauss_code_execution" not in sys.modules)


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
