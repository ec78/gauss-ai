"""Focused unit tests for the v0.43.0 Workspace Integration with Execution
Workflow milestone -- i.e. `scripts/gauss_execution_workflow.py`'s new
`workspace_registry`/`workspace_id` integration with
`scripts/gauss_workspace.py`'s `WorkspaceRegistry`.

This repository has no pytest configuration anywhere; the established
convention (see scripts/test_gauss_execution_workflow.py's own docstring)
is a self-contained `check(name, condition)` harness runnable directly:

    python scripts/test_workspace_execution_integration.py

Every test in this file uses a fake runner and disposable temporary
directories for both the durable-store db and the workspace registry's
approved parent directory -- never the default repository-relative
locations, never a real GAUSS invocation. Tests are grouped to match the
authorizing task's own Task 7 coverage list: Workspace validation (1-4),
Path safety (5-7), Execution integration (8-10), Provenance (11-12),
Isolation (13).
"""

from __future__ import annotations

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
import gauss_workspace as gw  # noqa: E402

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


def _store(tmp: str) -> "store_mod.OrchestrationStateStore":
    s = store_mod.OrchestrationStateStore(Path(tmp) / "test.db")
    s.initialize()
    return s


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


def _make_output_runner(workspace_root: str, filename: str = "results.txt"):
    def runner(_: "orch.RunnerInput") -> dict[str, Any]:
        return {
            "executed": True, "execution_status": "completed", "exit_code": 0, "stdout": "ok", "stderr": "",
            "output_files": [
                {"path": str(Path(workspace_root) / filename), "size_bytes": 42, "file_type": "text/plain", "created_by_execution": "unknown"}
            ],
            "warnings": [], "errors": [],
        }

    return runner


def _propose(
    workflow: "wf.ExecutionWorkflow",
    *,
    session_id: str = "s1",
    request_id: str = "r1",
    code: str | None = "x = 2 + 2;\nprint x;",
    working_directory: str | None = None,
    output_directory: str | None = None,
    executable_path: str | None = "C:/example/gauss26/tgauss.exe",
    timeout_seconds: float | None = 30.0,
    workspace_id: str | None = None,
) -> "wf.ProposalOutcome":
    return workflow.propose_execution(
        session_id=session_id, request_id=request_id, execution_purpose="integration test",
        eligibility_declarations=wf.EligibilityDeclarations(execution_explicitly_requested=True),
        safety_input=_passing_safety(), code=code, working_directory=working_directory,
        output_directory=output_directory, executable_path=executable_path, gauss_version="GAUSS 26",
        timeout_seconds=timeout_seconds, workspace_id=workspace_id,
    )


def _confirm(workflow: "wf.ExecutionWorkflow", outcome: "wf.ProposalOutcome", *, session_id: str = "s1", request_id: str = "r1") -> "wf.ConfirmationOutcome":
    assert outcome.proposal is not None
    return workflow.confirm_execution(
        wf.WorkflowConfirmationEvent(
            session_id=session_id, orchestration_instance_id=outcome.orchestration_instance_id, request_id=request_id,
            request_hash=outcome.proposal.request_hash, decision="accepted", timestamp="t1",
            source_interaction_id="turn-1", plan_digest=outcome.proposal.plan_digest,
        )
    )


def _advance_workspace_to_ready(registry: "gw.WorkspaceRegistry", workspace_id: str) -> None:
    registry.update_workspace_status(workspace_id, to_status=gw.WorkspaceStatus.POPULATED)
    registry.update_workspace_status(workspace_id, to_status=gw.WorkspaceStatus.READY)


# ---------------------------------------------------------------------------
# Workspace validation (1-4)
# ---------------------------------------------------------------------------


def test_01_valid_workspace_accepted() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)

        outcome = _propose(workflow, workspace_id=workspace.workspace_id)
        check("a valid, ready workspace produces an unblocked proposal", not outcome.blocked)
        assert outcome.proposal is not None
        check("proposal records workspace_id", outcome.proposal.workspace_id == workspace.workspace_id)
        check(
            "working_directory auto-derived from the workspace root",
            outcome.proposal.working_directory == workspace.root_path,
        )
        store.close()


def test_02_missing_workspace_rejected() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        outcome = _propose(workflow, workspace_id="does-not-exist")
        check("an unknown workspace_id blocks the proposal", outcome.blocked)
        store.close()


def test_03_deleted_workspace_rejected() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.EXECUTING)
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.COMPLETED)
        registry.archive_workspace(workspace.workspace_id)
        registry.delete_workspace(workspace.workspace_id)

        outcome = _propose(workflow, workspace_id=workspace.workspace_id)
        check("a deleted workspace blocks the proposal", outcome.blocked)
        store.close()


def test_04_archived_workspace_rejected() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.EXECUTING)
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.COMPLETED)
        registry.archive_workspace(workspace.workspace_id)

        outcome = _propose(workflow, workspace_id=workspace.workspace_id)
        check("an archived workspace blocks a new proposal", outcome.blocked)
        store.close()


# ---------------------------------------------------------------------------
# Path safety (5-7)
# ---------------------------------------------------------------------------


def test_05_script_inside_workspace_accepted() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)

        outcome = _propose(
            workflow, workspace_id=workspace.workspace_id,
            working_directory=str(Path(workspace.root_path) / "subdir"),
        )
        check("a working_directory inside the workspace root is accepted", not outcome.blocked)
        store.close()


def test_06_working_directory_outside_workspace_rejected() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as other_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)

        outcome = _propose(workflow, workspace_id=workspace.workspace_id, working_directory=other_tmp)
        check("a working_directory outside the workspace root is rejected", outcome.blocked)
        store.close()


def test_07_output_directory_outside_workspace_rejected() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as other_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)

        outcome = _propose(workflow, workspace_id=workspace.workspace_id, output_directory=other_tmp)
        check("an output_directory outside the workspace root is rejected", outcome.blocked)
        store.close()


# ---------------------------------------------------------------------------
# Execution integration (8-10)
# ---------------------------------------------------------------------------


def test_08_execution_request_carries_workspace_id() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)
        outcome = _propose(workflow, workspace_id=workspace.workspace_id)
        assert outcome.proposal is not None
        check("proposal.workspace_id matches the supplied workspace", outcome.proposal.workspace_id == workspace.workspace_id)
        store.close()


def test_09_controller_validates_workspace_before_invoking() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)
        outcome = _propose(workflow, workspace_id=workspace.workspace_id)
        _confirm(workflow, outcome)

        # Delete the workspace out from under the confirmed instance, between
        # confirmation and execution -- execute() must fail closed and never
        # touch the runner.
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.EXECUTING)
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.COMPLETED)
        registry.archive_workspace(workspace.workspace_id)
        registry.delete_workspace(workspace.workspace_id)

        calls = []

        def counting_runner(ri: "orch.RunnerInput") -> dict[str, Any]:
            calls.append(1)
            return _fake_runner_completed(ri)

        check_raises(
            "execute() refuses when the bound workspace no longer permits execution",
            wf.WorkspaceExecutionGuardError, workflow.execute, outcome.orchestration_instance_id, runner=counting_runner,
        )
        check("the runner was never called", len(calls) == 0)
        store.close()


def test_10_workspace_transitions_correctly_through_execution() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)
        check("workspace starts 'ready'", registry.get_workspace(workspace.workspace_id).status == gw.WorkspaceStatus.READY)

        outcome = _propose(workflow, workspace_id=workspace.workspace_id)
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("execution reports executed=True", result.executed)
        check(
            "workspace reaches 'completed' after a successful execution",
            registry.get_workspace(workspace.workspace_id).status == gw.WorkspaceStatus.COMPLETED,
        )
        store.close()


def test_10b_workspace_reaches_completed_even_after_a_runtime_error() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)

        outcome = _propose(workflow, workspace_id=workspace.workspace_id)
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_runtime_error)
        check("a GAUSS runtime error is still reported (execution genuinely ran)", result.runtime_error_detected)
        check(
            "workspace still reaches 'completed' after a failed (but attempted) execution -- "
            "per Task 5, workspace status never encodes success/failure",
            registry.get_workspace(workspace.workspace_id).status == gw.WorkspaceStatus.COMPLETED,
        )
        store.close()


# ---------------------------------------------------------------------------
# Provenance (11-12)
# ---------------------------------------------------------------------------


def test_11_outputs_reference_workspace() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)

        outcome = _propose(workflow, workspace_id=workspace.workspace_id)
        _confirm(workflow, outcome)
        runner = _make_output_runner(workspace.root_path)
        result = workflow.execute(outcome.orchestration_instance_id, runner=runner)

        check("result carries workspace_provenance", result.workspace_provenance is not None)
        assert result.workspace_provenance is not None
        check("provenance references the correct workspace_id", result.workspace_provenance.workspace_id == workspace.workspace_id)
        check("provenance records exactly one artifact", len(result.workspace_provenance.artifacts) == 1)
        check("artifact source is 'execution'", result.workspace_provenance.artifacts[0].source == "execution")
        check("artifact relative_path is workspace-relative, not an absolute path", result.workspace_provenance.artifacts[0].relative_path == "results.txt")

        manifest = registry.get_workspace_manifest(workspace.workspace_id)
        check("the workspace manifest itself was updated with the output artifact", len(manifest.files) == 1)
        store.close()


def test_12_outputs_reference_execution_identifiers() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)

        outcome = _propose(workflow, workspace_id=workspace.workspace_id)
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)

        assert result.workspace_provenance is not None
        check(
            "provenance.execution_session_id matches the orchestration_instance_id",
            result.workspace_provenance.execution_session_id == outcome.orchestration_instance_id,
        )
        check("provenance.execution_instance_id is populated", result.workspace_provenance.execution_instance_id is not None)

        # Provenance also remains available via a later inspect() call.
        inspected = workflow.inspect(outcome.orchestration_instance_id)
        check("inspect() surfaces the same workspace_provenance", inspected.workspace_provenance == result.workspace_provenance)
        store.close()


def test_12b_no_content_field_anywhere_in_provenance() -> None:
    import dataclasses

    provenance_fields = {f.name for f in dataclasses.fields(wf.WorkspaceProvenance)}
    check("WorkspaceProvenance has no 'content' field", "content" not in provenance_fields)
    artifact_fields = {f.name for f in dataclasses.fields(gw.ManifestFileEntry)}
    for forbidden in ("content", "contents", "raw_content"):
        check(f"ManifestFileEntry (used as provenance.artifacts) has no {forbidden!r} field", forbidden not in artifact_fields)


# ---------------------------------------------------------------------------
# Isolation (13)
# ---------------------------------------------------------------------------


def test_13_two_workspaces_remain_independent_through_execution() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)

        workspace_a = registry.create_workspace()
        workspace_b = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace_a.workspace_id)
        _advance_workspace_to_ready(registry, workspace_b.workspace_id)

        outcome_a = _propose(workflow, request_id="req-a", workspace_id=workspace_a.workspace_id)
        _confirm(workflow, outcome_a, request_id="req-a")
        workflow.execute(outcome_a.orchestration_instance_id, runner=_make_output_runner(workspace_a.root_path, "a.txt"))

        check(
            "workspace B remains 'ready' while workspace A executed independently",
            registry.get_workspace(workspace_b.workspace_id).status == gw.WorkspaceStatus.READY,
        )
        check("workspace A's manifest has one entry", len(registry.get_workspace_manifest(workspace_a.workspace_id).files) == 1)
        check("workspace B's manifest remains empty", len(registry.get_workspace_manifest(workspace_b.workspace_id).files) == 0)
        store.close()


# ---------------------------------------------------------------------------
# Backward compatibility (14)
# ---------------------------------------------------------------------------


def test_14_workflow_without_workspace_registry_still_works() -> None:
    with tempfile.TemporaryDirectory() as db_tmp:
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store)  # no workspace_registry at all
        outcome = _propose(workflow, working_directory="C:/example/work")
        _confirm(workflow, outcome)
        result = workflow.execute(outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("execution without a workspace_registry still succeeds unchanged", result.executed)
        check("workspace_provenance is None when no workspace was used", result.workspace_provenance is None)
        store.close()


def test_15_workspace_id_without_a_configured_registry_raises() -> None:
    with tempfile.TemporaryDirectory() as db_tmp:
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store)  # no workspace_registry
        check_raises(
            "supplying workspace_id without a configured workspace_registry raises",
            ValueError, _propose, workflow, workspace_id="some-workspace",
        )
        store.close()


def test_16_module_never_runs_gauss() -> None:
    check("gauss_code_execution is absent from sys.modules", "gauss_code_execution" not in sys.modules)


# ---------------------------------------------------------------------------
# Completed-workspace planning rejection (v0.52.0, 17-20)
# ---------------------------------------------------------------------------


def test_17_completed_workspace_rejects_new_proposal() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)

        first = _propose(workflow, request_id="req-1", workspace_id=workspace.workspace_id)
        _confirm(workflow, first, request_id="req-1")
        workflow.execute(first.orchestration_instance_id, runner=_fake_runner_completed)
        check(
            "workspace reaches completed after its one execution attempt",
            registry.get_workspace(workspace.workspace_id).status == gw.WorkspaceStatus.COMPLETED,
        )

        second = _propose(workflow, request_id="req-2", workspace_id=workspace.workspace_id)
        check("a completed workspace blocks a second proposal", second.blocked)
        check("no ExecutionProposal object is built for the blocked second attempt", second.proposal is None)
        assert second.failure_reason is not None
        check(
            "the block reason names the completed, single-shot nature of the workspace",
            "already completed its single allowed execution attempt" in second.failure_reason,
        )
        store.close()


def test_18_completed_workspace_rejection_leaves_state_unchanged() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)

        first = _propose(workflow, request_id="req-1", workspace_id=workspace.workspace_id)
        _confirm(workflow, first, request_id="req-1")
        workflow.execute(first.orchestration_instance_id, runner=_fake_runner_completed)
        manifest_before = registry.get_workspace_manifest(workspace.workspace_id).files

        _propose(workflow, request_id="req-2", workspace_id=workspace.workspace_id)

        check(
            "workspace status is untouched by the rejected second proposal",
            registry.get_workspace(workspace.workspace_id).status == gw.WorkspaceStatus.COMPLETED,
        )
        check(
            "manifest is untouched by the rejected second proposal",
            registry.get_workspace_manifest(workspace.workspace_id).files == manifest_before,
        )
        # The first execution's own result remains fully readable -- rejecting
        # a second plan must not discard prior evidence.
        inspected = workflow.inspect(first.orchestration_instance_id)
        check("the first execution's result remains inspectable after the rejected second attempt", inspected.executed)
        store.close()


def test_19_executing_workspace_rejects_new_proposal() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.EXECUTING)

        outcome = _propose(workflow, workspace_id=workspace.workspace_id)
        check("an in-flight (executing) workspace blocks a new proposal", outcome.blocked)
        check("no ExecutionProposal object is built while executing", outcome.proposal is None)
        store.close()


def test_20_lower_level_transition_still_blocked_if_propose_is_bypassed() -> None:
    """Defense in depth: even if a caller obtains a CONFIRMED instance bound
    to a workspace that only becomes COMPLETED afterward (e.g. a race, or a
    caller that skips this workflow's own propose_execution(...) checks by
    holding a stale confirmed instance), execute(...)'s own
    WorkspaceRegistry.update_workspace_status(...) call still refuses the
    COMPLETED -> EXECUTING transition. This is the same guard that existed
    before v0.52.0's earlier propose-time rejection -- it must remain
    intact, not be replaced by the earlier check."""
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)

        outcome = _propose(workflow, workspace_id=workspace.workspace_id)
        _confirm(workflow, outcome)

        # Simulate the workspace independently reaching 'completed' (e.g. via
        # a different orchestration instance) between confirmation and
        # execution of this instance.
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.EXECUTING)
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.COMPLETED)

        check_raises(
            "execute() still refuses completed -> executing at the workspace-lifecycle boundary",
            gw.InvalidWorkspaceTransitionError,
            workflow.execute,
            outcome.orchestration_instance_id,
            runner=_fake_runner_completed,
        )
        store.close()


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
