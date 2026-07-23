"""Focused unit tests for the v0.44.0 Safe Workspace File Reading Workflow
milestone's integration point -- `scripts/gauss_execution_workflow.py`'s
`ExecutionWorkflow.read_workspace_file(...)`, which delegates to
`scripts/gauss_workspace_file_reader.py`.

This repository has no pytest configuration anywhere; the established
convention is a self-contained `check(name, condition)` harness runnable
directly:

    python scripts/test_workspace_file_read_integration.py

Every test uses a fake execution runner, disposable temporary directories,
and never invokes GAUSS. This file focuses specifically on the
explicit-request-only boundary at the workflow layer and on keeping read
failures distinct from execution failures -- the lower-level reader
mechanics (path safety, size limits, binary detection, etc.) are already
exhaustively covered by scripts/test_gauss_workspace_file_reader.py and are
not re-tested here.
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


def _advance_workspace_to_ready(registry: "gw.WorkspaceRegistry", workspace_id: str) -> None:
    registry.update_workspace_status(workspace_id, to_status=gw.WorkspaceStatus.POPULATED)
    registry.update_workspace_status(workspace_id, to_status=gw.WorkspaceStatus.READY)


def _make_output_runner(workspace_root: str, filename: str, content: bytes):
    def runner(_: "orch.RunnerInput") -> dict[str, Any]:
        path = Path(workspace_root) / filename
        path.write_bytes(content)  # a real runner would have GAUSS write this; simulated here for the test
        return {
            "executed": True, "execution_status": "completed", "exit_code": 0, "stdout": "ok", "stderr": "",
            "output_files": [{"path": str(path), "size_bytes": len(content), "file_type": "text/plain", "created_by_execution": "unknown"}],
            "warnings": [], "errors": [],
        }

    return runner


def _propose_and_confirm(workflow: "wf.ExecutionWorkflow", *, workspace_id: str, request_id: str = "r1") -> str:
    outcome = workflow.propose_execution(
        session_id="s1", request_id=request_id, execution_purpose="integration test",
        eligibility_declarations=wf.EligibilityDeclarations(execution_explicitly_requested=True),
        safety_input=_passing_safety(), code="x = 2 + 2;\nprint x;", executable_path="C:/example/gauss26/tgauss.exe",
        gauss_version="GAUSS 26", timeout_seconds=30.0, workspace_id=workspace_id,
    )
    assert outcome.proposal is not None
    workflow.confirm_execution(
        wf.WorkflowConfirmationEvent(
            session_id="s1", orchestration_instance_id=outcome.orchestration_instance_id, request_id=request_id,
            request_hash=outcome.proposal.request_hash, decision="accepted", timestamp="t1",
            source_interaction_id="turn-1", plan_digest=outcome.proposal.plan_digest,
        )
    )
    return outcome.orchestration_instance_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_01_explicit_read_request_succeeds_after_execution() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        Path(workspace.root_path).mkdir(parents=True, exist_ok=True)
        _advance_workspace_to_ready(registry, workspace.workspace_id)
        instance_id = _propose_and_confirm(workflow, workspace_id=workspace.workspace_id)
        runner = _make_output_runner(workspace.root_path, "results.csv", b"a,b\n1,2\n")
        exec_result = workflow.execute(instance_id, runner=runner)
        check("execution completed", exec_result.executed)

        read_result = workflow.read_workspace_file(
            file_reader_mod.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="results.csv")
        )
        check("explicit read request succeeds", read_result.status == file_reader_mod.ReadStatus.COMPLETED.value)
        check("read content matches the real file", read_result.content == "a,b\n1,2\n")
        store.close()


def test_02_execution_completion_does_not_auto_read_the_file() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        Path(workspace.root_path).mkdir(parents=True, exist_ok=True)
        _advance_workspace_to_ready(registry, workspace.workspace_id)
        instance_id = _propose_and_confirm(workflow, workspace_id=workspace.workspace_id)
        runner = _make_output_runner(workspace.root_path, "auto_check.csv", b"never,read\nautomatically,here\n")
        exec_result = workflow.execute(instance_id, runner=runner)

        check("execution produced provenance metadata", exec_result.workspace_provenance is not None)
        assert exec_result.workspace_provenance is not None
        check("provenance artifacts carry no content field", not any(hasattr(a, "content") for a in exec_result.workspace_provenance.artifacts))
        # ResponseReadyResult itself has no field capable of holding file
        # content anywhere -- confirmed structurally.
        import dataclasses

        result_fields = {f.name for f in dataclasses.fields(wf.ResponseReadyResult)}
        check("ResponseReadyResult has no 'content' field", "content" not in result_fields)
        store.close()


def test_03_output_metadata_alone_does_not_trigger_a_read() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        Path(workspace.root_path).mkdir(parents=True, exist_ok=True)
        _advance_workspace_to_ready(registry, workspace.workspace_id)
        instance_id = _propose_and_confirm(workflow, workspace_id=workspace.workspace_id)
        runner = _make_output_runner(workspace.root_path, "metadata_only.log", b"log content nobody asked for\n")
        workflow.execute(instance_id, runner=runner)

        manifest = registry.get_workspace_manifest(workspace.workspace_id)
        check("the manifest records the output file's metadata", len(manifest.files) == 1)
        check("the manifest entry itself carries no content", not hasattr(manifest.files[0], "content"))
        store.close()


def test_04_read_failure_is_distinct_from_execution_failure() -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        workspace = registry.create_workspace()
        _advance_workspace_to_ready(registry, workspace.workspace_id)
        instance_id = _propose_and_confirm(workflow, workspace_id=workspace.workspace_id)

        def completed_runner(_: "orch.RunnerInput") -> dict[str, Any]:
            return {
                "executed": True, "execution_status": "completed", "exit_code": 0, "stdout": "ok", "stderr": "",
                "output_files": [], "warnings": [], "errors": [],
            }

        exec_result = workflow.execute(instance_id, runner=completed_runner)
        check("execution itself succeeded with no runtime error", exec_result.executed and not exec_result.runtime_error_detected)

        read_result = workflow.read_workspace_file(
            file_reader_mod.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="never_written.csv")
        )
        check("the read attempt fails on its own terms", read_result.status != file_reader_mod.ReadStatus.COMPLETED.value)
        check("a read failure does not retroactively mark execution as failed", exec_result.executed and not exec_result.runtime_error_detected)
        store.close()


def test_05_read_requires_a_configured_workspace_registry() -> None:
    with tempfile.TemporaryDirectory() as db_tmp:
        store = _store(db_tmp)
        workflow = wf.ExecutionWorkflow(state_store=store)  # no workspace_registry
        check_raises(
            "read_workspace_file without a configured workspace_registry raises",
            ValueError,
            workflow.read_workspace_file,
            file_reader_mod.WorkspaceFileReadRequest(workspace_id="anything", relative_path="anything.txt"),
        )
        store.close()


def test_06_module_never_runs_gauss() -> None:
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
