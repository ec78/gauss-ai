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
