"""Tests for scripts/gauss_code_assistant_cli.py (v0.47.0 Interactive MVP
Adapter).

This repository uses self-contained test harnesses runnable directly:

    python scripts/test_gauss_code_assistant_cli.py

Every test uses disposable temporary directories, the adapter's deterministic
fake runner, and the real existing MVP workflow facade. No test runs GAUSS.
"""

from __future__ import annotations

import hashlib
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
            "stdout",
            "stderr",
            "interpret",
            "read fake-output.txt",
            "provenance",
            "status",
        ]:
            transcript.extend(_run(adapter, command))
        text = "\n".join(transcript)
        check("transcript exercises plan", "confirmation_required" in text)
        check("transcript exercises fake execute", "FAKE_RUNNER" in text)
        check("transcript exercises metadata listing", "CONTENT_DISCLOSURE" in text)
        check("transcript exercises explicit stdout", "stdout_begin" in text)
        check("transcript exercises explicit stderr", "stderr_begin" in text)
        check("transcript exercises interpretation", "Execution interpretation from existing evidence" in text)
        check("transcript exercises explicit read", "content_begin" in text)
        check("transcript exercises provenance", "provenance.execution_instance_id" in text)
        adapter.close()


def test_19_captured_streams_require_explicit_request() -> None:
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
        execute = _joined(_run(adapter, "execute"))
        check("execute reports stderr length", "stderr_chars:" in execute)
        check("execute does not print captured stderr content", "Undefined symbol" not in execute)
        stderr = _joined(_run(adapter, "stderr"))
        check("explicit stderr returns captured content", "Undefined symbol" in stderr)
        check("explicit stderr has boundaries", "stderr_begin" in stderr and "stderr_end" in stderr)
        adapter.close()


def test_20_interpret_before_execute() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_success(adapter)
        out = _run(adapter, "interpret")
        check("interpret before execute unavailable", "ERROR no_result" in _joined(out))
        adapter.close()


def test_21_interpret_fake_success() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "interpret"))
        check("interpret does not launch", "No GAUSS launch, no retry, no code edit" in out)
        check("interpret success", "completion_status: completed" in out)
        check("interpret safe continue", "safe_to_continue: true" in out)
        adapter.close()


def test_22_interpret_fake_syntax_error() -> None:
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
        _run(adapter, "execute")
        out = _joined(_run(adapter, "interpret"))
        check("interpret error code", "error_code: G0105" in out)
        check("interpret syntax failure", "failure_type: parse_syntax" in out)
        check("interpret diagnostic only", "next_step: Inspect" in out)
        adapter.close()


def test_23_completed_workspace_plan_rejected_with_guidance() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        check(
            "workspace reaches completed after its one execution",
            adapter.registry.get_workspace(adapter.active_workspace_id).status == gw.WorkspaceStatus.COMPLETED,
        )

        _run(adapter, "request --fake-success y = 9; print y;")
        out = _joined(_run(adapter, "plan"))
        check("second plan on a completed workspace is blocked", "propose -> blocked" in out)
        check("no execution occurred on the blocked second plan", "No execution occurred." in out)
        check("no new plan was created is stated explicitly", "No new plan was created." in out)
        check("single-shot exhaustion is flagged", "workspace_single_shot_exhausted: true" in out)
        check("guidance names 'workspace create' as the remedy", "workspace create" in out)
        assert adapter.mvp_session is not None
        check("no ExecutionProposal exists for the blocked second attempt", adapter.mvp_session.proposal_outcome.proposal is None)
        adapter.close()


def test_24_completed_workspace_state_unchanged_after_rejected_plan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        workspace_id = adapter.active_workspace_id
        manifest_before = adapter.registry.get_workspace_manifest(workspace_id).files

        _run(adapter, "request --fake-success y = 9; print y;")
        _run(adapter, "plan")

        check(
            "workspace status is untouched by the rejected second plan",
            adapter.registry.get_workspace(workspace_id).status == gw.WorkspaceStatus.COMPLETED,
        )
        check(
            "manifest is untouched by the rejected second plan",
            adapter.registry.get_workspace_manifest(workspace_id).files == manifest_before,
        )
        adapter.close()


def test_25_workspace_create_recovers_from_completed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        old_workspace_id = adapter.active_workspace_id

        _run(adapter, "request --fake-success y = 9; print y;")
        _run(adapter, "plan")  # blocked -- completed workspace

        _run(adapter, "workspace create")
        check("workspace create produced a different workspace id", adapter.active_workspace_id != old_workspace_id)
        request_hash2 = _plan_success(adapter)
        check("a normal plan on the fresh workspace succeeds", len(request_hash2) == 64)
        adapter.close()


def test_26_reset_then_request_plan_normal_flow_still_works() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_success(adapter)
        _run(adapter, "decline")
        _run(adapter, "reset")
        request_hash = _plan_success(adapter)
        check("reset allows a normal new request+plan on the same still-ready workspace", len(request_hash) == 64)
        check(
            "the workspace used for reset+replan is still ready (never entered execution)",
            adapter.registry.get_workspace(adapter.active_workspace_id).status == gw.WorkspaceStatus.READY,
        )
        adapter.close()


def test_27_interpretation_and_streams_remain_available_before_reset() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-failure x = ;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")

        first_interpret = _joined(_run(adapter, "interpret"))
        second_interpret = _joined(_run(adapter, "interpret"))
        check("interpret is repeatable without loss of evidence", "ERROR no_result" not in second_interpret)
        check("repeated interpretation is identical (deterministic, non-destructive)", first_interpret == second_interpret)

        first_stderr = _joined(_run(adapter, "stderr"))
        second_stderr = _joined(_run(adapter, "stderr"))
        check("stderr remains available on a second explicit request", "ERROR no_result" not in second_stderr)
        check("repeated stderr inspection is identical", first_stderr == second_stderr)

        provenance = _joined(_run(adapter, "provenance"))
        check("provenance remains available before reset", "ERROR no_result" not in provenance)

        _run(adapter, "reset")
        after_reset = _joined(_run(adapter, "interpret"))
        check("interpret is unavailable only after an explicit reset", "ERROR no_result" in after_reset)
        adapter.close()


def test_28_fake_timeout_through_cli() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-timeout x = 2 + 2; print x;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        execute_out = _joined(_run(adapter, "execute"))
        check("execute reports timed_out", "timed_out: true" in execute_out)
        out = _joined(_run(adapter, "interpret"))
        check("interpret classifies timeout", "execution_phase: timeout" in out)
        check("interpret does not retry", "No GAUSS launch, no retry, no code edit" in out)
        check("interpret recommends inspection only", "next_step: Inspect stdout and stderr" in out)
        adapter.close()


def test_29_fake_unknown_error_through_cli() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-unknown-error x = 2 + 2; print x;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "interpret"))
        check("interpret preserves the uncataloged code", "error_code: G9999" in out)
        check("interpret classifies it as unknown, not a guess", "failure_type: unknown" in out)
        check(
            "interpret states genericly that the code is uncataloged rather than inventing a meaning",
            "not yet in the local deterministic catalog" in out,
        )
        adapter.close()


def test_30_interpret_does_not_mutate_workspace_or_reexecute() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        workspace_status_before = adapter.registry.get_workspace(adapter.active_workspace_id).status
        stage_before = adapter.mvp_session.stage
        instance_id_before = adapter.mvp_session.orchestration_instance_id

        _run(adapter, "interpret")
        _run(adapter, "interpret")

        check("interpret never changes workspace status", adapter.registry.get_workspace(adapter.active_workspace_id).status == workspace_status_before)
        check("interpret never advances the session stage", adapter.mvp_session.stage == stage_before)
        check("interpret never creates a new orchestration instance", adapter.mvp_session.orchestration_instance_id == instance_id_before)
        adapter.close()


def test_31_interpret_never_auto_displays_streams_or_reads_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-failure x = ;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")

        out = _joined(_run(adapter, "interpret"))
        check("interpret output carries no stdout content-boundary marker", "stdout_begin" not in out)
        check("interpret output carries no stderr content-boundary marker", "stderr_begin" not in out)
        check("interpret output carries no file-read content-boundary marker", "content_begin" not in out)
        check("interpret alone never triggers a workspace file read", len(adapter.mvp_session.file_reads) == 0)
        adapter.close()


def test_32_interpret_surfaces_verification_metadata_through_cli() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-failure x = ;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "interpret"))
        check("CLI surfaces verification_status for a cataloged code", "verification_status: real_runtime, official_documentation" in out)
        check("CLI surfaces verification_source for a cataloged code", "verification_source:" in out)
        adapter.close()


def test_33_fake_timeout_wording_is_honestly_simulated_through_cli() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-timeout x = 2 + 2; print x;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "interpret"))
        check("simulated timeout is disclosed as simulated, not observed", "simulated" in out.lower() or "injected" in out.lower())
        check("simulated timeout does not claim gauss was launched", "launch_status: launched" not in out)
        adapter.close()


def test_34_diagnose_before_workspace_creation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        out = _joined(_run(adapter, "diagnose"))
        check("diagnose before any workspace reports no_result", "ERROR no_result" in out)
        adapter.close()


def test_35_diagnose_before_request() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        out = _joined(_run(adapter, "diagnose"))
        check("diagnose before request reports no_result", "ERROR no_result" in out)
        adapter.close()


def test_36_diagnose_before_execute() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_success(adapter)
        out = _joined(_run(adapter, "diagnose"))
        check("diagnose before execute reports no_result", "ERROR no_result" in out)
        adapter.close()


def test_37_diagnosis_after_success() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "diagnose"))
        check("diagnostic boundary disclosed", "DIAGNOSTIC_BOUNDARY" in out)
        check("no-failure status for a successful run", "diagnostic_status: no_failure_detected" in out)
        check("safe to continue", "safe_to_continue: true" in out)
        check("repair boundary disclosed", "Diagnosis does not modify or repair the program." in out)
        adapter.close()


def test_38_diagnosis_after_g0105() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-failure x = ;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "diagnose"))
        check("source_error_code G0105", "source_error_code: G0105" in out)
        check("at least one possible cause", "possible_cause_count: 0" not in out)
        check("questions posed", "questions_to_ask:" in out)
        adapter.close()


def test_39_diagnosis_after_g0036() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-failure x = ones(2,2); y = ones(3,1); z = x + y;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        # the deterministic --fake-failure fixture always reports G0105, not
        # G0036 -- exercised here purely to confirm the diagnose path works
        # end to end from a fresh request; the dedicated G0036 case is
        # covered directly against the engine in
        # test_gauss_execution_diagnostics.py, which does not depend on the
        # CLI's fake-failure fixture's fixed error code.
        out = _joined(_run(adapter, "diagnose"))
        check("diagnose completes without error", "ERROR" not in out.split("\n")[0])
        adapter.close()


def test_40_diagnosis_after_unknown_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-unknown-error x = 2 + 2; print x;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "diagnose"))
        check("unknown error status", "diagnostic_status: unknown_error" in out)
        check("code preserved", "source_error_code: G9999" in out)
        check("no possible causes for unknown code", "possible_cause_count: 0" in out)
        adapter.close()


def test_41_diagnosis_after_timeout_fixture() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-timeout x = 2 + 2; print x;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "diagnose"))
        check("timeout status", "diagnostic_status: timeout" in out)
        check("no asserted causes for timeout", "possible_cause_count: 0" in out)
        adapter.close()


def test_42_repeated_diagnose_is_deterministic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        first = _joined(_run(adapter, "diagnose"))
        second = _joined(_run(adapter, "diagnose"))
        check("repeated diagnose output is identical", first == second)
        adapter.close()


def test_43_interpretation_remains_available_after_diagnosis() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "diagnose")
        out = _joined(_run(adapter, "interpret"))
        check("interpret still works after diagnose", "ERROR no_result" not in out)
        adapter.close()


def test_44_streams_remain_explicitly_accessible_after_diagnosis() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-failure x = ;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        diagnose_out = _joined(_run(adapter, "diagnose"))
        check("diagnose does not auto-display stdout content", "stdout_begin" not in diagnose_out)
        check("diagnose does not auto-display stderr content", "stderr_begin" not in diagnose_out)
        stderr_out = _joined(_run(adapter, "stderr"))
        check("stderr remains explicitly accessible after diagnose", "stderr_begin" in stderr_out and "ERROR" not in stderr_out.split("\n")[0])
        adapter.close()


def test_45_completed_workspace_state_unchanged_by_diagnosis() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        status_before = adapter.registry.get_workspace(adapter.active_workspace_id).status
        _run(adapter, "diagnose")
        _run(adapter, "diagnose")
        check("workspace status unchanged by diagnose", adapter.registry.get_workspace(adapter.active_workspace_id).status == status_before)
        adapter.close()


def test_46_reset_clears_diagnostic_availability() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "diagnose")
        _run(adapter, "reset")
        out = _joined(_run(adapter, "diagnose"))
        check("diagnose unavailable after reset, consistent with interpret's own reset behavior", "ERROR no_result" in out)
        adapter.close()


def _failed_run_with_stderr(adapter: "cli.InteractiveMvpAdapter", stderr_text: str) -> None:
    """v0.55.0 helper: drives a real `request --fake-failure` / `plan` /
    `confirm` / `execute` sequence (so `execution_status` is genuinely
    'failed', exactly as the existing --fake-failure fixture already
    produces), then overrides only the captured stderr text so `interpret`/
    `diagnose` can be exercised against each new v0.55.0 catalog code through
    the adapter's real evidence-assembly path, without adding a dedicated
    fake-runner mode per code."""
    _run(adapter, "workspace create")
    _run(adapter, "request --fake-failure x = ;")
    _run(adapter, "plan")
    assert adapter.mvp_session is not None
    assert adapter.mvp_session.proposal_outcome is not None
    assert adapter.mvp_session.proposal_outcome.proposal is not None
    request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
    _run(adapter, f"confirm {request_hash}")
    _run(adapter, "execute")
    adapter.last_captured_output = cli.CapturedProcessOutput(stdout="Program execute failed\n", stderr=stderr_text)


def test_47_interpret_and_diagnose_handle_each_v0_55_0_new_code() -> None:
    new_codes = {
        "G0058": "error G0058 : Index out of range\n",
        "G0159": "error G0159 : Wrong number of parameters ''p' expected 2 arguments, received 1'\n",
        "G0104": "error G0104 : Argument must be positive\n",
        "G0071": "error G0071 : Type mismatch\n",
        "G0048": "error G0048 : Matrix singular\n",
        "G0047": "error G0047 : Rows don't match\n",
    }
    for code, stderr_text in new_codes.items():
        with tempfile.TemporaryDirectory() as tmp:
            adapter = _new_adapter(tmp)
            _failed_run_with_stderr(adapter, stderr_text)
            interpret_out = _joined(_run(adapter, "interpret"))
            check(f"interpret reports {code}", f"error_code: {code}" in interpret_out)
            diagnose_out = _joined(_run(adapter, "diagnose"))
            check(f"diagnose reports source_error_code {code}", f"source_error_code: {code}" in diagnose_out)
            check(f"diagnose for {code} finds at least one possible cause", "possible_cause_count: 0" not in diagnose_out)
            adapter.close()


def test_48_unknown_code_remains_generic_after_catalog_expansion() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _failed_run_with_stderr(adapter, "error G7777 : Never cataloged\n")
        out = _joined(_run(adapter, "diagnose"))
        check("uncataloged code after expansion is still unknown_error", "diagnostic_status: unknown_error" in out)
        check("no possible causes fabricated for an uncataloged code", "possible_cause_count: 0" in out)
        adapter.close()


def test_49_repair_plan_before_workspace_creation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        out = _joined(_run(adapter, "repair-plan"))
        check("repair-plan before any workspace reports no_result", "ERROR no_result" in out)
        adapter.close()


def test_50_repair_plan_before_request() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        out = _joined(_run(adapter, "repair-plan"))
        check("repair-plan before request reports no_result", "ERROR no_result" in out)
        adapter.close()


def test_51_repair_plan_before_execute() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_success(adapter)
        out = _joined(_run(adapter, "repair-plan"))
        check("repair-plan before execute reports no_result", "ERROR no_result" in out)
        adapter.close()


def test_52_repair_plan_after_successful_execution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "repair-plan"))
        check("boundary disclosed", "REPAIR_PLAN_BOUNDARY" in out)
        check("no-repair-needed status", "repair_status: successful_execution_no_repair_needed" in out)
        check("safe_to_apply false", "safe_to_apply: false" in out)
        check("application boundary disclosed", "No patch was applied. No file was modified. GAUSS was not rerun." in out)
        adapter.close()


def test_53_repair_plan_after_g0105() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-failure x = ;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "repair-plan"))
        check("source_error_code G0105", "source_error_code: G0105" in out)
        check("strategy_available status", "repair_status: strategy_available" in out)
        check("proposed strategy present", "proposed_repair_strategy:" in out)
        check("safe_to_apply false", "safe_to_apply: false" in out)
        adapter.close()


def test_54_repair_plan_after_each_new_code() -> None:
    codes = {
        "G0036": "error G0036 : Matrix dimensions are incompatible\n",
        "G0025": "error G0025 : Undefined symbol: 'x'\n",
        "G0014": "error G0014 : File not found 'x.txt'\n",
        "G0290": "error G0290 : Library not found\n",
    }
    for code, stderr_text in codes.items():
        with tempfile.TemporaryDirectory() as tmp:
            adapter = _new_adapter(tmp)
            _failed_run_with_stderr(adapter, stderr_text)
            out = _joined(_run(adapter, "repair-plan"))
            check(f"{code} repair-plan reports correct source_error_code", f"source_error_code: {code}" in out)
            check(f"{code} repair-plan has a proposed strategy", "proposed_repair_strategy:" in out)
            check(f"{code} repair-plan safe_to_apply false", "safe_to_apply: false" in out)
            adapter.close()


def test_55_repair_plan_after_unknown_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-unknown-error x = 2 + 2; print x;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "repair-plan"))
        check("unknown_error status", "repair_status: unknown_error" in out)
        check("code preserved", "source_error_code: G9999" in out)
        check("no proposed strategy for unknown code", "proposed_repair_strategy:" not in out)
        adapter.close()


def test_56_repair_plan_after_timeout_fixture() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-timeout x = 2 + 2; print x;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "repair-plan"))
        check("timeout status", "repair_status: timeout" in out)
        check(
            "does not assert an infinite loop as fact (only disclaims verifying one)",
            "does not verify whether the script contains an infinite loop" in out.lower(),
        )
        adapter.close()


def test_57_repeated_repair_plan_is_deterministic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        first = _joined(_run(adapter, "repair-plan"))
        second = _joined(_run(adapter, "repair-plan"))
        check("repeated repair-plan output is identical", first == second)
        adapter.close()


def test_58_diagnose_and_interpret_remain_available_after_repair_plan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        diagnose_out = _joined(_run(adapter, "diagnose"))
        interpret_out = _joined(_run(adapter, "interpret"))
        check("diagnose still works after repair-plan", "ERROR no_result" not in diagnose_out)
        check("interpret still works after repair-plan", "ERROR no_result" not in interpret_out)
        adapter.close()


def test_59_streams_remain_explicitly_accessible_after_repair_plan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _run(adapter, "workspace create")
        _run(adapter, "request --fake-failure x = ;")
        _run(adapter, "plan")
        assert adapter.mvp_session is not None
        request_hash = adapter.mvp_session.proposal_outcome.proposal.request_hash
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        repair_out = _joined(_run(adapter, "repair-plan"))
        check("repair-plan does not auto-display stdout content", "stdout_begin" not in repair_out)
        check("repair-plan does not auto-display stderr content", "stderr_begin" not in repair_out)
        stderr_out = _joined(_run(adapter, "stderr"))
        check("stderr remains explicitly accessible after repair-plan", "stderr_begin" in stderr_out and "ERROR" not in stderr_out.split("\n")[0])
        adapter.close()


def test_60_workspace_state_unchanged_by_repair_plan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        status_before = adapter.registry.get_workspace(adapter.active_workspace_id).status
        _run(adapter, "repair-plan")
        _run(adapter, "repair-plan --matrix-shape A=2x3 --matrix-shape B=4x5")
        check("workspace status unchanged by repair-plan", adapter.registry.get_workspace(adapter.active_workspace_id).status == status_before)
        adapter.close()


def test_61_reset_clears_repair_plan_availability() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        _run(adapter, "reset")
        out = _joined(_run(adapter, "repair-plan"))
        check("repair-plan unavailable after reset, consistent with diagnose/interpret's own reset behavior", "ERROR no_result" in out)
        adapter.close()


def test_62_repair_plan_source_context_flags_narrow_plan_without_applying() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _failed_run_with_stderr(adapter, "error G0036 : Matrix dimensions are incompatible\n")
        no_context = _joined(_run(adapter, "repair-plan"))
        with_context = _joined(_run(adapter, "repair-plan --matrix-shape A=2x3 --matrix-shape B=4x5"))
        check("no-context plan is strategy_available", "repair_status: strategy_available" in no_context)
        check("with-context plan is draft_possible_with_more_context", "repair_status: draft_possible_with_more_context" in with_context)
        check("with-context plan still reports safe_to_apply false", "safe_to_apply: false" in with_context)
        check("with-context plan still reports safe_to_prepare_draft false", "safe_to_prepare_draft: false" in with_context)
        check("with-context plan reports source_context_used true", "source_context_used: true" in with_context)
        adapter.close()


def test_63_repair_plan_rejects_unrecognized_option() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "repair-plan --not-a-real-flag"))
        check("unrecognized repair-plan option reports an error", "ERROR usage" in out)
        adapter.close()


def _plan_digest_from(out: list[str]) -> str:
    return [line.split(": ", 1)[1] for line in out if line.startswith("plan_digest:")][0]


def test_64_approve_repair_before_a_plan_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "approve-repair somehash"))
        check("approve-repair before a repair plan exists reports no_repair_plan", "ERROR no_repair_plan" in out)
        adapter.close()


def test_65_approve_repair_after_a_plan_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _failed_run_with_stderr(adapter, "error G0036 : Matrix dimensions are incompatible\n")
        plan_out = _run(adapter, "repair-plan")
        digest = _plan_digest_from(plan_out)
        out = _joined(_run(adapter, f"approve-repair {digest}"))
        check("approval recorded", "decision: approved" in out)
        check("plan_digest echoed back matches", f"plan_digest: {digest}" in out)
        check("safe_to_apply still false", "safe_to_apply: false" in out)
        check("safe_to_prepare_draft still false", "safe_to_prepare_draft: false" in out)
        check("approval boundary disclosed", "APPROVAL_BOUNDARY" in out)
        adapter.close()


def test_66_approve_repair_stale_digest_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _failed_run_with_stderr(adapter, "error G0036 : Matrix dimensions are incompatible\n")
        _run(adapter, "repair-plan")
        out = _joined(_run(adapter, "approve-repair 0000000000000000000000000000000000000000000000000000000000000000"))
        check("stale/incorrect digest rejected", "ERROR stale_or_incorrect_digest" in out)
        check("current_plan_digest disclosed for guidance", "current_plan_digest:" in out)
        adapter.close()


def test_67_approve_repair_stale_after_source_context_changes_plan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _failed_run_with_stderr(adapter, "error G0036 : Matrix dimensions are incompatible\n")
        first_out = _run(adapter, "repair-plan")
        first_digest = _plan_digest_from(first_out)
        _run(adapter, "repair-plan --matrix-shape A=2x3 --matrix-shape B=4x5")
        out = _joined(_run(adapter, f"approve-repair {first_digest}"))
        check("digest from a superseded plan is rejected as stale", "ERROR stale_or_incorrect_digest" in out)
        adapter.close()


def test_68_decline_repair_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _failed_run_with_stderr(adapter, "error G0025 : Undefined symbol: 'x'\n")
        plan_out = _run(adapter, "repair-plan")
        digest = _plan_digest_from(plan_out)
        out = _joined(_run(adapter, f"decline-repair {digest}"))
        check("decline recorded", "decision: declined" in out)
        check("safe_to_apply still false after decline", "safe_to_apply: false" in out)
        adapter.close()


def test_69_re_approve_without_revoke_reports_conflict() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _failed_run_with_stderr(adapter, "error G0014 : File not found 'x.txt'\n")
        plan_out = _run(adapter, "repair-plan")
        digest = _plan_digest_from(plan_out)
        _run(adapter, f"approve-repair {digest}")
        out = _joined(_run(adapter, f"approve-repair {digest}"))
        check("re-approving without revoke reports a conflict, not a silent overwrite", "ERROR approval_conflict" in out)
        adapter.close()


def test_70_approve_repair_missing_argument() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _failed_run_with_stderr(adapter, "error G0290 : Library not found\n")
        _run(adapter, "repair-plan")
        out = _joined(_run(adapter, "approve-repair"))
        check("approve-repair with no digest argument reports usage error", "ERROR usage" in out)
        adapter.close()


def test_71_reset_clears_repair_plan_and_approval_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _failed_run_with_stderr(adapter, "error G0036 : Matrix dimensions are incompatible\n")
        plan_out = _run(adapter, "repair-plan")
        digest = _plan_digest_from(plan_out)
        _run(adapter, f"approve-repair {digest}")
        _run(adapter, "reset")
        out = _joined(_run(adapter, f"approve-repair {digest}"))
        check("approve-repair after reset reports no_repair_plan, consistent with repair-plan's own reset behavior", "ERROR no_repair_plan" in out)
        adapter.close()


def test_72_repair_planning_regression_unaffected_by_approval_layer() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "repair-plan"))
        check("successful-execution repair-plan output unchanged by the new approval layer", "repair_status: successful_execution_no_repair_needed" in out)
        check("plan_digest still rendered even for a no-repair-needed plan", "plan_digest:" in out)
        adapter.close()


_DRAFT_ARGS = [
    "--path", "model.gss",
    "--content-hash", "a" * 64,
    "--size", "200",
    "--line-start", "5",
    "--line-end", "5",
    "--operation", "insert missing semicolon",
    "--description", "Insert a missing statement terminator at the reported line.",
]


def _repair_draft_from(adapter: "cli.InteractiveMvpAdapter") -> list[str]:
    return _run(adapter, "repair-draft " + " ".join(f'"{a}"' if " " in a else a for a in _DRAFT_ARGS))


def test_73_repair_draft_before_plan_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "repair-draft"))
        check("repair-draft before repair-plan reports no_repair_plan", "ERROR no_repair_plan" in out)
        adapter.close()


def test_74_show_repair_draft_before_draft_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        out = _joined(_run(adapter, "show-repair-draft"))
        check("show-repair-draft before repair-draft reports no_repair_draft", "ERROR no_repair_draft" in out)
        adapter.close()


def test_75_repair_draft_after_repair_plan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        out = _joined(_repair_draft_from(adapter))
        check("draft boundary disclosed", "DRAFT_BOUNDARY" in out)
        check("draft_digest present", "draft_digest:" in out)
        check("safe_to_apply false", "safe_to_apply: false" in out)
        check("safe_to_prepare_draft false", "safe_to_prepare_draft: false" in out)
        check("validation passed", "validation_all_passed: true" in out)
        for line in (
            "disclosure: This is NOT an applied repair.",
            "disclosure: No files were modified.",
            "disclosure: No patch exists.",
            "disclosure: No code has been generated.",
            "disclosure: No approval to edit files exists.",
        ):
            check(f"disclosure present: {line!r}", line in out)
        adapter.close()


def test_76_show_repair_draft_after_creation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        first = _joined(_repair_draft_from(adapter))
        second = _joined(_run(adapter, "show-repair-draft"))
        check("show-repair-draft matches the just-created draft's own output", first == second)
        adapter.close()


def test_77_repair_draft_uses_active_workspace_by_default() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        out = _joined(_repair_draft_from(adapter))
        check("workspace_id defaults to the active workspace", f"workspace_id: {adapter.active_workspace_id}" in out)
        adapter.close()


def test_78_repair_draft_missing_required_option() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        out = _joined(_run(adapter, "repair-draft --path model.gss"))
        check("missing required options reported", "ERROR usage: missing required repair-draft option" in out)
        adapter.close()


def test_79_repair_draft_rejects_unrecognized_option() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        out = _joined(_run(adapter, "repair-draft --not-a-real-flag"))
        check("unrecognized repair-draft option reports an error", "ERROR usage" in out)
        adapter.close()


def test_80_repeated_repair_draft_construction_same_inputs_same_digest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        out1 = _joined(_repair_draft_from(adapter))
        out2 = _joined(_repair_draft_from(adapter))
        digest1 = [line.split(": ", 1)[1] for line in out1.splitlines() if line.startswith("draft_digest:")][0]
        digest2 = [line.split(": ", 1)[1] for line in out2.splitlines() if line.startswith("draft_digest:")][0]
        check("repeated construction with identical inputs produces identical draft digests", digest1 == digest2)
        adapter.close()


def test_81_repair_draft_does_not_mutate_workspace_or_filesystem() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        status_before = adapter.registry.get_workspace(adapter.active_workspace_id).status
        workspace_root = Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path)
        entries_before = set(workspace_root.rglob("*")) if workspace_root.exists() else set()
        _repair_draft_from(adapter)
        _run(adapter, "show-repair-draft")
        status_after = adapter.registry.get_workspace(adapter.active_workspace_id).status
        entries_after = set(workspace_root.rglob("*")) if workspace_root.exists() else set()
        check("workspace status unchanged by repair-draft/show-repair-draft", status_before == status_after)
        check("no new filesystem entries created by repair-draft/show-repair-draft", entries_before == entries_after)
        adapter.close()


def test_82_reset_clears_repair_draft_availability() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        _repair_draft_from(adapter)
        _run(adapter, "reset")
        out = _joined(_run(adapter, "show-repair-draft"))
        check("show-repair-draft unavailable after reset", "ERROR no_repair_draft" in out)
        adapter.close()


def test_83_repair_draft_never_calls_execute_or_mutates_approval_store() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        approval_len_before = len(adapter._repair_approval_store)  # noqa: SLF001
        _repair_draft_from(adapter)
        approval_len_after = len(adapter._repair_approval_store)  # noqa: SLF001
        check("repair-draft does not add any approval record", approval_len_before == approval_len_after)
        adapter.close()


def _draft_digest_from(out: list[str]) -> str:
    return [line.split(": ", 1)[1] for line in out if line.startswith("draft_digest:")][0]


def _plan_and_draft(adapter: "cli.InteractiveMvpAdapter") -> str:
    """Drives request -> plan -> confirm -> execute -> repair-plan ->
    repair-draft, returning the resulting draft's own digest."""
    request_hash = _plan_success(adapter)
    _run(adapter, f"confirm {request_hash}")
    _run(adapter, "execute")
    _run(adapter, "repair-plan")
    out = _repair_draft_from(adapter)
    return _draft_digest_from(out)


def test_84_approve_repair_draft_before_draft_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        out = _joined(_run(adapter, "approve-repair-draft somehash"))
        check("approve-repair-draft before a draft exists reports no_repair_draft", "ERROR no_repair_draft" in out)
        adapter.close()


def test_85_approve_repair_draft_after_draft_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_and_draft(adapter)
        out = _joined(_run(adapter, f"approve-repair-draft {digest}"))
        check("approval recorded", "decision: approved" in out)
        check("draft_digest echoed back matches", f"draft_digest: {digest}" in out)
        check("safe_to_apply still false", "safe_to_apply: false" in out)
        check("safe_to_prepare_draft still false", "safe_to_prepare_draft: false" in out)
        check("draft approval boundary disclosed", "DRAFT_APPROVAL_BOUNDARY" in out)
        check("approval_boundary states approved", "has been approved" in out)
        adapter.close()


def test_86_decline_repair_draft_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_and_draft(adapter)
        out = _joined(_run(adapter, f"decline-repair-draft {digest}"))
        check("decline recorded", "decision: declined" in out)
        check("decline boundary does not claim approval", "has been approved" not in out.split("approval_boundary:")[1])
        adapter.close()


def test_87_approve_repair_draft_stale_digest_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_and_draft(adapter)
        out = _joined(_run(adapter, "approve-repair-draft 0000000000000000000000000000000000000000000000000000000000000000"))
        check("stale/incorrect digest rejected", "ERROR stale_or_incorrect_digest" in out)
        check("current_draft_digest disclosed for guidance", "current_draft_digest:" in out)
        adapter.close()


def test_88_re_approve_repair_draft_without_revoke_reports_conflict() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_and_draft(adapter)
        _run(adapter, f"approve-repair-draft {digest}")
        out = _joined(_run(adapter, f"approve-repair-draft {digest}"))
        check("re-approving without revoke reports a conflict, not a silent overwrite", "ERROR draft_approval_conflict" in out)
        adapter.close()


def test_89_approve_repair_draft_missing_argument() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_and_draft(adapter)
        out = _joined(_run(adapter, "approve-repair-draft"))
        check("approve-repair-draft with no digest argument reports usage error", "ERROR usage" in out)
        adapter.close()


def test_90_show_repair_draft_approval_before_decision_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_and_draft(adapter)
        out = _joined(_run(adapter, "show-repair-draft-approval"))
        check("show-repair-draft-approval before any decision reports no_draft_approval", "ERROR no_draft_approval" in out)
        adapter.close()


def test_91_show_repair_draft_approval_after_decision() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_and_draft(adapter)
        _run(adapter, f"approve-repair-draft {digest}")
        first = _joined(_run(adapter, "show-repair-draft-approval"))
        second = _joined(_run(adapter, "show-repair-draft-approval"))
        check("repeated show-repair-draft-approval is deterministic", first == second)
        check("shows the approved decision", "decision: approved" in first)
        adapter.close()


def test_92_reset_clears_repair_draft_approval_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_and_draft(adapter)
        _run(adapter, f"approve-repair-draft {digest}")
        _run(adapter, "reset")
        out = _joined(_run(adapter, "approve-repair-draft " + digest))
        check("approve-repair-draft after reset reports no_repair_draft, consistent with repair-draft's own reset behavior", "ERROR no_repair_draft" in out)
        adapter.close()


def test_93_repair_draft_approval_does_not_mutate_workspace_or_filesystem() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_and_draft(adapter)
        status_before = adapter.registry.get_workspace(adapter.active_workspace_id).status
        workspace_root = Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path)
        entries_before = set(workspace_root.rglob("*")) if workspace_root.exists() else set()
        _run(adapter, f"approve-repair-draft {digest}")
        _run(adapter, "show-repair-draft-approval")
        status_after = adapter.registry.get_workspace(adapter.active_workspace_id).status
        entries_after = set(workspace_root.rglob("*")) if workspace_root.exists() else set()
        check("workspace status unchanged by draft-approval commands", status_before == status_after)
        check("no new filesystem entries created by draft-approval commands", entries_before == entries_after)
        adapter.close()


def test_94_repair_draft_approval_does_not_call_execute_or_mutate_strategy_approval() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_and_draft(adapter)
        strategy_len_before = len(adapter._repair_approval_store)  # noqa: SLF001
        _run(adapter, f"approve-repair-draft {digest}")
        strategy_len_after = len(adapter._repair_approval_store)  # noqa: SLF001
        check("approving a draft does not add a strategy-level approval record", strategy_len_before == strategy_len_after)
        adapter.close()


def test_95_repair_planning_and_approval_regression_unaffected_by_draft_approval_layer() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "repair-plan"))
        check("successful-execution repair-plan output unchanged by the new draft-approval layer", "repair_status: successful_execution_no_repair_needed" in out)
        adapter.close()


def _plan_draft_and_approve_draft(adapter: "cli.InteractiveMvpAdapter") -> str:
    """Drives request -> plan -> confirm -> execute -> repair-plan ->
    repair-draft -> approve-repair-draft, returning the draft's own digest."""
    digest = _plan_and_draft(adapter)
    _run(adapter, f"approve-repair-draft {digest}")
    return digest


def _plan_draft_approve_strategy_and_draft(adapter: "cli.InteractiveMvpAdapter") -> str:
    """Drives the full chain through strategy-level approval as well
    (request -> plan -> confirm -> execute -> repair-plan -> approve-repair
    -> repair-draft -> approve-repair-draft), returning the draft's own
    digest. Needed for gate tests where STRATEGY_APPROVAL_EXISTS must pass
    too, unlike `_plan_draft_and_approve_draft`, which leaves the
    strategy-level plan unapproved."""
    request_hash = _plan_success(adapter)
    _run(adapter, f"confirm {request_hash}")
    _run(adapter, "execute")
    plan_out = _joined(_run(adapter, "repair-plan"))
    plan_digest = [line.split(": ", 1)[1] for line in plan_out.splitlines() if line.startswith("plan_digest:")][0]
    _run(adapter, f"approve-repair {plan_digest}")
    draft_out = _repair_draft_from(adapter)
    digest = _draft_digest_from(draft_out)
    _run(adapter, f"approve-repair-draft {digest}")
    return digest


def test_96_approve_repair_application_before_draft_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        out = _joined(_run(adapter, "approve-repair-application somehash"))
        check("approve-repair-application before a draft exists reports no_repair_draft", "ERROR no_repair_draft" in out)
        adapter.close()


def test_97_approve_repair_application_after_draft_approved() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_draft_and_approve_draft(adapter)
        out = _joined(_run(adapter, f"approve-repair-application {digest}"))
        check("application approval recorded", "decision: approved" in out)
        check("draft_digest echoed back matches", f"draft_digest: {digest}" in out)
        check("safe_to_apply still false", "safe_to_apply: false" in out)
        check("safe_to_prepare_draft still false", "safe_to_prepare_draft: false" in out)
        check("application approval boundary disclosed", "APPLICATION_APPROVAL_BOUNDARY" in out)
        check("approval_boundary states approved", "has been approved" in out)
        check("approval_boundary discloses the transaction remains unimplemented", "remains unimplemented" in out)
        adapter.close()


def test_98_decline_repair_application_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_draft_and_approve_draft(adapter)
        out = _joined(_run(adapter, f"decline-repair-application {digest}"))
        check("decline recorded", "decision: declined" in out)
        check("decline boundary does not claim approval", "has been approved" not in out.split("approval_boundary:")[1])
        adapter.close()


def test_99_approve_repair_application_stale_digest_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_draft_and_approve_draft(adapter)
        out = _joined(_run(adapter, "approve-repair-application 0000000000000000000000000000000000000000000000000000000000000000"))
        check("stale/incorrect digest rejected", "ERROR stale_or_incorrect_digest" in out)
        check("current_draft_digest disclosed for guidance", "current_draft_digest:" in out)
        adapter.close()


def test_100_re_approve_repair_application_without_revoke_reports_conflict() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_draft_and_approve_draft(adapter)
        _run(adapter, f"approve-repair-application {digest}")
        out = _joined(_run(adapter, f"approve-repair-application {digest}"))
        check("re-approving without revoke reports a conflict, not a silent overwrite", "ERROR application_approval_conflict" in out)
        adapter.close()


def test_101_approve_repair_application_missing_argument() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_draft_and_approve_draft(adapter)
        out = _joined(_run(adapter, "approve-repair-application"))
        check("approve-repair-application with no digest argument reports usage error", "ERROR usage" in out)
        adapter.close()


def test_102_show_repair_application_approval_before_decision_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_draft_and_approve_draft(adapter)
        out = _joined(_run(adapter, "show-repair-application-approval"))
        check("show-repair-application-approval before any decision reports no_application_approval", "ERROR no_application_approval" in out)
        adapter.close()


def test_103_show_repair_application_approval_after_decision() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_draft_and_approve_draft(adapter)
        _run(adapter, f"approve-repair-application {digest}")
        first = _joined(_run(adapter, "show-repair-application-approval"))
        second = _joined(_run(adapter, "show-repair-application-approval"))
        check("repeated show-repair-application-approval is deterministic", first == second)
        check("shows the approved decision", "decision: approved" in first)
        adapter.close()


def test_104_check_repair_application_gate_before_repair_plan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        out = _joined(_run(adapter, "check-repair-application-gate"))
        check("check-repair-application-gate before repair-plan reports no_repair_plan", "ERROR no_repair_plan" in out)
        adapter.close()


def test_105_check_repair_application_gate_before_repair_draft() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        out = _joined(_run(adapter, "check-repair-application-gate"))
        check("check-repair-application-gate before repair-draft reports no_repair_draft", "ERROR no_repair_draft" in out)
        adapter.close()


def test_106_check_repair_application_gate_without_approvals_fails_every_approval_check() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_and_draft(adapter)
        out = _joined(_run(adapter, "check-repair-application-gate"))
        check("gate reports all_passed false with no draft/application approval recorded", "all_passed: false" in out)
        check("draft_approval_exists fails", "draft_approval_exists]: FAIL" in out)
        check("application_approval_exists fails", "application_approval_exists]: FAIL" in out)
        check("not_applicable_checks disclosed", "not_applicable_checks: backup_prepared" in out)
        check("gate never claims authorization", "does not authorize applying anything" in out)
        adapter.close()


def test_107_check_repair_application_gate_fully_approved_and_fresh_passes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_draft_approve_strategy_and_draft(adapter)
        _run(adapter, f"approve-repair-application {digest}")
        content_hash = "a" * 64
        out = _joined(_run(adapter, f"check-repair-application-gate --current-content-hash {content_hash}"))
        check("gate passes once every layer is approved and source hash is confirmed fresh", "all_passed: true" in out)
        check("no failed_checks line when all_passed is true", "failed_checks:" not in out)
        adapter.close()


def test_108_check_repair_application_gate_stale_source_hash_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_draft_approve_strategy_and_draft(adapter)
        _run(adapter, f"approve-repair-application {digest}")
        stale_hash = "b" * 64
        out = _joined(_run(adapter, f"check-repair-application-gate --current-content-hash {stale_hash}"))
        check("gate fails when the supplied current content hash no longer matches the draft", "all_passed: false" in out)
        check("source_hash_matches reported as FAIL", "source_hash_matches]: FAIL" in out)
        adapter.close()


def test_109_reset_clears_repair_application_approval_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_draft_and_approve_draft(adapter)
        _run(adapter, f"approve-repair-application {digest}")
        _run(adapter, "reset")
        out = _joined(_run(adapter, "approve-repair-application " + digest))
        check("approve-repair-application after reset reports no_repair_draft, consistent with repair-draft's own reset behavior", "ERROR no_repair_draft" in out)
        adapter.close()


def test_110_repair_application_approval_does_not_mutate_workspace_or_filesystem() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_draft_and_approve_draft(adapter)
        status_before = adapter.registry.get_workspace(adapter.active_workspace_id).status
        workspace_root = Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path)
        entries_before = set(workspace_root.rglob("*")) if workspace_root.exists() else set()
        _run(adapter, f"approve-repair-application {digest}")
        _run(adapter, "show-repair-application-approval")
        _run(adapter, "check-repair-application-gate")
        status_after = adapter.registry.get_workspace(adapter.active_workspace_id).status
        entries_after = set(workspace_root.rglob("*")) if workspace_root.exists() else set()
        check("workspace status unchanged by application-approval/gate commands", status_before == status_after)
        check("no new filesystem entries created by application-approval/gate commands", entries_before == entries_after)
        adapter.close()


def test_111_repair_application_approval_does_not_mutate_other_approval_stores() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest = _plan_draft_and_approve_draft(adapter)
        strategy_len_before = len(adapter._repair_approval_store)  # noqa: SLF001
        draft_len_before = len(adapter._draft_approval_store)  # noqa: SLF001
        _run(adapter, f"approve-repair-application {digest}")
        strategy_len_after = len(adapter._repair_approval_store)  # noqa: SLF001
        draft_len_after = len(adapter._draft_approval_store)  # noqa: SLF001
        check("approving an application does not add a strategy-level approval record", strategy_len_before == strategy_len_after)
        check("approving an application does not add a draft-level approval record", draft_len_before == draft_len_after)
        adapter.close()


def test_112_repair_planning_and_prior_layers_regression_unaffected_by_application_layer() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "repair-plan"))
        check("successful-execution repair-plan output unchanged by the new application-approval layer", "repair_status: successful_execution_no_repair_needed" in out)
        adapter.close()


def _plan_draft_approve_all_with_real_file(
    adapter: "cli.InteractiveMvpAdapter", *, relative_path: str = "model.gss", text: str = "x = 2 + 2\nprint x;\n",
    line_start: int = 1, line_end: int = 1, approve_application: bool = True,
) -> "tuple[str, Path, str]":
    """Drives the full chain through strategy, draft, and application
    approval -- and, unlike every earlier repair-draft helper in this file,
    backs the draft's own `--content-hash` with a REAL file actually written
    into the workspace, since `apply-repair` genuinely reads and hashes the
    target. Returns (draft_digest, target_path, original_text)."""
    _run(adapter, "workspace create")
    assert adapter.active_workspace_id is not None
    workspace = adapter.registry.get_workspace(adapter.active_workspace_id)
    target = Path(workspace.root_path) / relative_path
    target.write_bytes(text.encode("utf-8"))
    real_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    _run(adapter, "request --fake-failure x = ;")
    plan = _run(adapter, "plan")
    request_hash = [line.split(": ", 1)[1] for line in plan if line.startswith("request_hash:")][0]
    _run(adapter, f"confirm {request_hash}")
    _run(adapter, "execute")
    plan_out = _joined(_run(adapter, "repair-plan"))
    plan_digest = [line.split(": ", 1)[1] for line in plan_out.splitlines() if line.startswith("plan_digest:")][0]
    _run(adapter, f"approve-repair {plan_digest}")

    draft_out = _run(
        adapter,
        f"repair-draft --path {relative_path} --content-hash {real_hash} "
        f'--size {len(text.encode("utf-8"))} --line-start {line_start} --line-end {line_end} '
        f'--operation "insert missing semicolon" --description "Insert a missing statement terminator."',
    )
    digest = _draft_digest_from(draft_out)
    _run(adapter, f"approve-repair-draft {digest}")
    if approve_application:
        _run(adapter, f"approve-repair-application {digest}")
    return digest, target, text


def test_113_apply_repair_before_draft_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        _run(adapter, "repair-plan")
        out = _joined(_run(adapter, 'apply-repair somehash --replacement-text "x;"'))
        check("apply-repair before a draft exists reports no_repair_draft", "ERROR no_repair_draft" in out)
        adapter.close()


def test_114_apply_repair_full_success_modifies_file_and_creates_backup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest, target, original_text = _plan_draft_approve_all_with_real_file(adapter)
        out = _joined(_run(adapter, f'apply-repair {digest} --replacement-text "x = 2 + 2;"'))
        check("outcome is applied", "outcome: applied" in out)
        check("file_modified is true", "file_modified: true" in out)
        check("backup_created is true", "backup_created: true" in out)
        check("rerun_performed is false", "rerun_performed: false" in out)
        check("target file was actually modified on disk", target.read_text(encoding="utf-8") == "x = 2 + 2;\nprint x;\n")
        check("application_boundary discloses backup preserved", "backup" in out.split("application_boundary:")[1].split("\n")[0].lower())
        adapter.close()


def test_115_apply_repair_stale_digest_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_draft_approve_all_with_real_file(adapter)
        out = _joined(_run(adapter, 'apply-repair 0000000000000000000000000000000000000000000000000000000000000000 --replacement-text "x;"'))
        check("stale/incorrect digest rejected", "ERROR stale_or_incorrect_digest" in out)
        check("current_draft_digest disclosed for guidance", "current_draft_digest:" in out)
        adapter.close()


def test_116_apply_repair_missing_replacement_text_argument() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest, _target, _text = _plan_draft_approve_all_with_real_file(adapter)
        out = _joined(_run(adapter, f"apply-repair {digest}"))
        check("apply-repair without --replacement-text reports usage error", "ERROR usage" in out)
        adapter.close()


def test_117_apply_repair_blocked_when_application_not_approved() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest, _target, _text = _plan_draft_approve_all_with_real_file(adapter, approve_application=False)
        out = _joined(_run(adapter, f'apply-repair {digest} --replacement-text "x;"'))
        check("outcome is blocked", "outcome: blocked" in out)
        check("reason names gate_failed", "gate_failed" in out)
        adapter.close()


def test_118_show_application_result_before_any_application() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _plan_draft_approve_all_with_real_file(adapter)
        out = _joined(_run(adapter, "show-application-result"))
        check("show-application-result before any apply-repair reports no_application_result", "ERROR no_application_result" in out)
        adapter.close()


def test_119_show_application_result_after_application_deterministic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest, _target, _text = _plan_draft_approve_all_with_real_file(adapter)
        _run(adapter, f'apply-repair {digest} --replacement-text "x = 2 + 2;"')
        first = _joined(_run(adapter, "show-application-result"))
        second = _joined(_run(adapter, "show-application-result"))
        check("repeated show-application-result is deterministic", first == second)
        check("shows the applied outcome", "outcome: applied" in first)
        adapter.close()


def test_120_reset_clears_application_result_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest, _target, _text = _plan_draft_approve_all_with_real_file(adapter)
        _run(adapter, f'apply-repair {digest} --replacement-text "x = 2 + 2;"')
        _run(adapter, "reset")
        out = _joined(_run(adapter, "show-application-result"))
        check("show-application-result after reset reports no_application_result", "ERROR no_application_result" in out)
        adapter.close()


def test_121_apply_repair_does_not_mutate_strategy_or_draft_approval_stores() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest, _target, _text = _plan_draft_approve_all_with_real_file(adapter)
        strategy_len_before = len(adapter._repair_approval_store)  # noqa: SLF001
        draft_len_before = len(adapter._draft_approval_store)  # noqa: SLF001
        application_len_before = len(adapter._application_approval_store)  # noqa: SLF001
        _run(adapter, f'apply-repair {digest} --replacement-text "x = 2 + 2;"')
        check("applying does not add a strategy-level approval record", strategy_len_before == len(adapter._repair_approval_store))  # noqa: SLF001
        check("applying does not add a draft-level approval record", draft_len_before == len(adapter._draft_approval_store))  # noqa: SLF001
        check("applying does not add an application-approval record", application_len_before == len(adapter._application_approval_store))  # noqa: SLF001
        adapter.close()


def test_122_apply_repair_never_touches_workspace_status_or_other_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        digest, target, _text = _plan_draft_approve_all_with_real_file(adapter)
        status_before = adapter.registry.get_workspace(adapter.active_workspace_id).status
        entries_before = set(Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path).rglob("*"))
        _run(adapter, f'apply-repair {digest} --replacement-text "x = 2 + 2;"')
        status_after = adapter.registry.get_workspace(adapter.active_workspace_id).status
        entries_after = set(Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path).rglob("*"))
        check("workspace status unchanged by apply-repair", status_before == status_after)
        new_entries = entries_after - entries_before
        check("exactly one new filesystem entry (the backup) was created", len(new_entries) == 1)
        if new_entries:
            check("the one new entry is a backup file, not a new directory", next(iter(new_entries)).is_file())
        adapter.close()


def test_123_repair_planning_and_prior_layers_regression_unaffected_by_application_transaction_layer() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        out = _joined(_run(adapter, "repair-plan"))
        check("successful-execution repair-plan output unchanged by the new application-transaction layer", "repair_status: successful_execution_no_repair_needed" in out)
        adapter.close()


# ---------------------------------------------------------------------------
# v0.64.0 Verification Execution Workflow
# ---------------------------------------------------------------------------


def _apply_repair_via_cli(
    adapter: "cli.InteractiveMvpAdapter", *, relative_path: str = "model.gss", text: str = "x = 2 + 2\nprint x;\n",
) -> "tuple[object, Path, str]":
    """Drives the full real chain through a successful apply-repair call
    (real file, real hashes, every approval layer) and returns
    (adapter.last_application_result, target_path, repaired_text)."""
    digest, target, _original_text = _plan_draft_approve_all_with_real_file(adapter, relative_path=relative_path, text=text)
    _run(adapter, f'apply-repair {digest} --replacement-text "x = 2 + 2;"')
    assert adapter.last_application_result is not None
    assert adapter.last_application_result.outcome == "applied"
    return adapter.last_application_result, target, target.read_text(encoding="utf-8")


def test_124_verify_repair_before_application_result_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        out = _joined(_run(adapter, "verify-repair"))
        check("verify-repair before any apply-repair reports no_application_result", "ERROR no_application_result" in out)
        adapter.close()


def test_125_verify_repair_full_success_and_comparison_succeeded_after_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _apply_repair_via_cli(adapter)
        verify_out = _joined(_run(adapter, "verify-repair --fake-success"))
        check("verify-repair discloses ordinary execution", "This is an ordinary execution." in verify_out)
        check("verify-repair discloses repair success is not inferred", "Repair success is NOT inferred" in verify_out)
        check("verify-repair proposal not blocked", "blocked: false" in verify_out)
        request_hash = [line.split(": ", 1)[1] for line in verify_out.splitlines() if line.startswith("request_hash:")][0]

        confirm_out = _joined(_run(adapter, f"confirm {request_hash}"))
        check("confirm (unmodified command) reaches confirmed", "current_state: confirmed" in confirm_out)
        execute_out = _joined(_run(adapter, "execute"))
        check("execute (unmodified command) reports completed", "execution_status: completed" in execute_out)

        show_out = _joined(_run(adapter, "show-verification-request"))
        check("comparison_available true", "comparison_available: true" in show_out)
        check("comparison is succeeded_after_failure", "comparison: succeeded_after_failure" in show_out)
        check(
            "observation matches the task's own worked example",
            "The repaired code executed successfully whereas the original execution failed with G0105." in show_out,
        )
        check("evidence-only disclosure present", "does not conclude the repair is correct" in show_out)
        adapter.close()


def test_126_verify_repair_same_error_comparison() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _apply_repair_via_cli(adapter)
        verify_out = _joined(_run(adapter, "verify-repair --fake-failure"))
        request_hash = [line.split(": ", 1)[1] for line in verify_out.splitlines() if line.startswith("request_hash:")][0]
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        show_out = _joined(_run(adapter, "show-verification-request"))
        check("comparison is same_error (fake-failure reproduces G0105 both times)", "comparison: same_error" in show_out)
        check("observation matches the task's own worked example", "The repair did not change the observed execution outcome." in show_out)
        adapter.close()


def test_127_verify_repair_different_error_comparison() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _apply_repair_via_cli(adapter)
        verify_out = _joined(_run(adapter, "verify-repair --fake-unknown-error"))
        request_hash = [line.split(": ", 1)[1] for line in verify_out.splitlines() if line.startswith("request_hash:")][0]
        _run(adapter, f"confirm {request_hash}")
        _run(adapter, "execute")
        show_out = _joined(_run(adapter, "show-verification-request"))
        check("comparison is different_error (G0105 originally, G9999 on verification)", "comparison: different_error" in show_out)
        check("observation matches the task's own worked example", "The repair changed execution behavior, but a different runtime error occurred." in show_out)
        adapter.close()


def test_128_show_verification_request_before_verify_repair() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        out = _joined(_run(adapter, "show-verification-request"))
        check("show-verification-request before verify-repair reports no_verification_request", "ERROR no_verification_request" in out)
        adapter.close()


def test_129_show_verification_request_before_execution_completes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _apply_repair_via_cli(adapter)
        _run(adapter, "verify-repair --fake-success")
        out = _joined(_run(adapter, "show-verification-request"))
        check("comparison_available is false before confirm/execute run", "comparison_available: false" in out)
        adapter.close()


def test_130_verify_repair_stale_source_blocks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _result, target, _text = _apply_repair_via_cli(adapter)
        target.write_bytes(b"mutated again after the repair was applied\n")
        out = _joined(_run(adapter, "verify-repair --fake-success"))
        check("verify-repair blocks on a stale post-repair hash", "blocked: true" in out)
        check("failure_category names verification_source_stale", "verification_source_stale" in out)
        adapter.close()


def test_131_verify_repair_does_not_mutate_approval_stores_or_repair_draft() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _apply_repair_via_cli(adapter)
        draft_before = adapter.last_repair_draft
        strategy_len_before = len(adapter._repair_approval_store)  # noqa: SLF001
        draft_len_before = len(adapter._draft_approval_store)  # noqa: SLF001
        application_len_before = len(adapter._application_approval_store)  # noqa: SLF001
        _run(adapter, "verify-repair --fake-success")
        check("last_repair_draft is the SAME object after verify-repair", adapter.last_repair_draft is draft_before)
        check("strategy approval store length unchanged", len(adapter._repair_approval_store) == strategy_len_before)  # noqa: SLF001
        check("draft approval store length unchanged", len(adapter._draft_approval_store) == draft_len_before)  # noqa: SLF001
        check("application approval store length unchanged", len(adapter._application_approval_store) == application_len_before)  # noqa: SLF001
        adapter.close()


def test_132_reset_clears_verification_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        _apply_repair_via_cli(adapter)
        _run(adapter, "verify-repair --fake-success")
        _run(adapter, "reset")
        out = _joined(_run(adapter, "show-verification-request"))
        check("show-verification-request after reset reports no_verification_request", "ERROR no_verification_request" in out)
        adapter.close()


def test_133_verify_repair_regression_ordinary_execution_unaffected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_adapter(tmp)
        request_hash = _plan_success(adapter)
        _run(adapter, f"confirm {request_hash}")
        out = _joined(_run(adapter, "execute"))
        check("ordinary execution output unaffected by the new verification-execution layer", "execution_status: completed" in out)
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
