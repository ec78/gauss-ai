"""Tests for scripts/gauss_code_assistant_cli.py (v0.47.0 Interactive MVP
Adapter).

This repository uses self-contained test harnesses runnable directly:

    python scripts/test_gauss_code_assistant_cli.py

Every test uses disposable temporary directories, the adapter's deterministic
fake runner, and the real existing MVP workflow facade. No test runs GAUSS.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_code_assistant_cli as cli  # noqa: E402
import gauss_workspace as gw  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _run(adapter: "cli.InteractiveMvpAdapter", line: str) -> list[str]:
    keep_going, output = adapter.handle_line(line)
    check(f"{line!r} keeps session open unless exit", keep_going)
    return output


def _joined(lines: list[str]) -> str:
    return "\n".join(lines)


def _new_adapter(tmp: str) -> "cli.InteractiveMvpAdapter":
    return cli.InteractiveMvpAdapter(workspace_parent=tmp, session_id="adapter-test", clock=lambda: 1000.0)


def _plan_success(adapter: "cli.InteractiveMvpAdapter") -> str:
    _run(adapter, "workspace create")
    _run(adapter, "request --fake-success x = 2 + 2; print x;")
    plan = _run(adapter, "plan")
    assert adapter.mvp_session is not None
    assert adapter.mvp_session.proposal_outcome is not None
    assert adapter.mvp_session.proposal_outcome.proposal is not None
    request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
    check("plan output displays request_hash", request_hash in _joined(plan))
    return request_hash


def test_01_startup_help_exit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        help_lines = _run(adapter, "help")
        check("help names the adapter", "Interactive MVP Adapter" in _joined(help_lines))
        keep_going, exit_lines = adapter.handle_line("exit")
        check("exit stops the loop", not keep_going)
        check("exit discloses no GAUSS run", "No GAUSS was run" in _joined(exit_lines))
        adapter.close()


def test_02_workspace_bootstrap() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        out = _run(adapter, "workspace create")
        check("workspace create invokes real registry", "REAL_WORKFLOW" in _joined(out))
        check("workspace id is active", adapter.active_workspace_id is not None)
        assert adapter.active_workspace_id is not None
        workspace = adapter.registry.get_workspace(adapter.active_workspace_id)
        check("workspace status is ready", workspace.status == gw.WorkspaceStatus.READY)
        check("workspace root exists", Path(workspace.root_path).exists())
        adapter.close()


def test_03_request_and_proposal() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        check("request hash was generated", len(request_hash) == 64)
        assert adapter.mvp_session is not None
        check("session reaches PLAN_PROPOSED", adapter.mvp_session.stage.value == "plan_proposed")
        adapter.close()


def test_04_explicit_confirmation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        out = _run(adapter, f"confirm {request_hash}")
        check("confirm invokes real workflow", "GaussCodeAssistantWorkflow.confirm" in _joined(out))
        check("confirm is accepted", "accepted: True" in _joined(out))
        assert adapter.mvp_session is not None
        check("session reaches confirmed", adapter.mvp_session.stage.value == "confirmed")
        adapter.close()


def test_05_decline_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_success(adapter)
        out = _run(adapter, "decline")
        check("decline uses confirmation path", "decision=rejected" in _joined(out))
        check("decline is not accepted", "accepted: False" in _joined(out))
        assert adapter.mvp_session is not None
        check("session reaches declined", adapter.mvp_session.stage.value == "declined")
        adapter.close()


def test_06_execute_blocked_before_confirmation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_success(adapter)
        out = _run(adapter, "execute")
        check("execute before confirmation is rejected", "MvpWorkflowStageError" in _joined(out))
        adapter.close()


def test_07_stale_or_mismatched_confirmation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_success(adapter)
        out = _run(adapter, "confirm stale-digest")
        check("stale digest is rejected by workflow validation", "ConfirmationValidationError" in _joined(out))
        adapter.close()


def test_08_deterministic_fake_success() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        out = _run(adapter, "execute")
        check("execute invokes real workflow", "GaussCodeAssistantWorkflow.execute" in _joined(out))
        check("fake runner is disclosed", "FAKE_RUNNER" in _joined(out))
        check("success completed", "execution_status: completed" in _joined(out))
        check("one output produced", "output_file_count: 1" in _joined(out))
        adapter.close()


def test_09_deterministic_fake_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-failure x = ;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        assert adapter.mvp_session.proposal_outcome is not None
        assert adapter.mvp_session.proposal_outcome.proposal is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        out = _run(adapter, "execute")
        check("failure is deterministic", "execution_status: failed" in _joined(out))
        check("runtime error is surfaced", "runtime_error_detected: True" in _joined(out))
        adapter.close()


def test_10_output_metadata_without_reading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _run(adapter, "outputs")
        check("outputs reports metadata only", "metadata only" in _joined(out))
        check("outputs lists fake-output", "fake-output.txt" in _joined(out))
        check("outputs does not print file content", "fake GAUSS Code Assistant MVP output" not in _joined(out))
        adapter.close()


def test_11_explicit_file_read() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _run(adapter, "read fake-output.txt")
        check("read invokes real file workflow", "read_workspace_file" in _joined(out))
        check("read completes", "read_status: completed" in _joined(out))
        check("read returns content only after explicit read", "fake GAUSS Code Assistant MVP output" in _joined(out))
        adapter.close()


def test_12_path_traversal_rejection() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _run(adapter, "read ../outside.txt")
        check("path traversal is rejected by file reader", "path_escapes_workspace" in _joined(out))
        adapter.close()


def test_13_cross_workspace_rejection() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        original_workspace = adapter.active_workspace_id
        other_workspace = adapter.registry.create_workspace()
        Path(other_workspace.root_path).mkdir(parents=True, exist_ok=True)
        adapter.registry.update_workspace_status(other_workspace.workspace_id, to_status=gw.WorkspaceStatus.POPULATED)
        adapter.registry.update_workspace_status(other_workspace.workspace_id, to_status=gw.WorkspaceStatus.READY)
        adapter.active_workspace_id = other_workspace.workspace_id
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _run(adapter, "read fake-output.txt")
        check("facade rejects read against different active workspace", "ValueError" in _joined(out))
        check("original workspace existed", original_workspace is not None)
        adapter.close()


def test_14_reset_behavior() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_success(adapter)
        out = _run(adapter, "reset")
        check("reset clears request state", "Cleared active request" in _joined(out))
        check("workspace retained", adapter.active_workspace_id is not None)
        check("session cleared", adapter.mvp_session is None)
        check("pending request cleared", adapter.pending_request is None)
        adapter.close()


def test_15_workflow_trace_disclosure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        plan_text = _joined(_run(adapter, "status"))
        check("status exposes adapter id", "adapter_session_id: adapter-test" in plan_text)
        check("status exposes orchestration id", "orchestration_instance_id:" in plan_text)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        provenance = _joined(_run(adapter, "provenance"))
        check("provenance discloses session reference caveat", "not a durable ExecutionSession ID" in provenance)
        check("provenance exposes execution instance id", "provenance.execution_instance_id:" in provenance)
        adapter.close()


def test_16_confirmation_required_again_after_changed_request() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        old_hash = _plan_success(adapter)
        _run(adapter, "request --fake-success y = 5; print y;")
        _run(adapter, "plan")
        out = _run(adapter, f"confirm {old_hash}")
        check("old hash cannot confirm changed proposal", "ConfirmationValidationError" in _joined(out))
        adapter.close()


def test_17_no_real_gauss_invocation() -> None:
    check("gauss_code_execution was never imported", "gauss_code_execution" not in sys.modules)


def test_18_complete_transcript_style_flow() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        transcript = []
        for command in [
            "help",
            "workspace create",
            "request --fake-success x = 2 + 2; print x;",
            "plan",
        ]:
            transcript.extend(_run(adapter, command))
        assert adapter.mvp_session is not None
        assert adapter.mvp_session.proposal_outcome is not None
        assert adapter.mvp_session.proposal_outcome.proposal is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        for command in [
            f"confirm {request_hash}",
            "execute",
            "outputs",
            "read fake-output.txt",
            "provenance",
            "status",
        ]:
            transcript.extend(_run(adapter, command))
        text = "\n".join(transcript)
        check("transcript exercises plan", "confirmation_required" in text)
        check("transcript exercises fake execute", "FAKE_RUNNER" in text)
        check("transcript exercises metadata listing", "CONTENT_DISCLOSURE" in text)
        check("transcript exercises explicit read", "content_begin" in text)
        check("transcript exercises provenance", "provenance.execution_instance_id" in text)
        adapter.close()


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
