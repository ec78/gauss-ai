"""Interactive terminal adapter for the GAUSS Code Assistant MVP workflow.

This is the v0.47.0 Interactive MVP Adapter. It is intentionally thin:
terminal commands are translated into the existing
`GaussCodeAssistantWorkflow` facade and its underlying workspace/execution
components. The adapter owns no execution eligibility, confirmation,
workspace-boundary, file-reading, or provenance safety logic.

Default execution uses a deterministic fake runner. This module never imports
`gauss_code_execution`, never launches GAUSS, and never constructs a real
helper runner.
"""

from __future__ import annotations

import argparse
import shlex
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_code_assistant_workflow as mvp  # noqa: E402
import gauss_execution_workflow as wf  # noqa: E402
import gauss_orchestration_state_store as store_mod  # noqa: E402
import gauss_workspace as workspace_mod  # noqa: E402
import gauss_workspace_file_reader as file_reader_mod  # noqa: E402


PROMPT = "gauss-mvp> "
DEFAULT_CODE = "x = 2 + 2;\nprint x;"
FAILURE_CODE = "x = ;"
DEFAULT_EXECUTABLE = "C:/example/gauss26/tgauss.exe"


@dataclass(frozen=True)
class PendingRequest:
    request_id: str
    summary: str
    code: str
    fake_result: str


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


class InteractiveMvpAdapter:
    """Small command handler for manual alpha testing.

    Tests call `handle_line(...)` directly; `run_repl(...)` below is only the
    terminal loop. All state is process-local and discarded when the adapter
    exits.
    """

    def __init__(
        self,
        *,
        workspace_parent: str | Path | None = None,
        session_id: str | None = None,
        clock: Any = time.time,
    ) -> None:
        self.adapter_session_id = session_id or f"adapter-{uuid.uuid4().hex}"
        self._clock = clock
        self._owns_parent_tmp = workspace_parent is None
        self._parent_tmp: tempfile.TemporaryDirectory[str] | None = None
        if workspace_parent is None:
            self._parent_tmp = tempfile.TemporaryDirectory(prefix="gauss-ai-alpha-")
            workspace_parent = self._parent_tmp.name

        self.workspace_parent = Path(workspace_parent).resolve(strict=False)
        self.workspace_parent.mkdir(parents=True, exist_ok=True)

        self._db_tmp = tempfile.TemporaryDirectory(prefix="gauss-ai-alpha-db-")
        self._store = store_mod.OrchestrationStateStore(Path(self._db_tmp.name) / "orchestration.db")
        self._store.initialize()
        self.registry = workspace_mod.WorkspaceRegistry(approved_parent_directory=self.workspace_parent)
        self.execution_workflow = wf.ExecutionWorkflow(state_store=self._store, workspace_registry=self.registry)
        self.workflow = mvp.GaussCodeAssistantWorkflow(
            execution_workflow=self.execution_workflow,
            workspace_registry=self.registry,
        )

        self.active_workspace_id: str | None = None
        self.mvp_session: mvp.MvpWorkflowSession | None = None
        self.pending_request: PendingRequest | None = None
        self.last_result: mvp.WorkflowResult | None = None
        self._turn_counter = 0

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._store.close()
        self._db_tmp.cleanup()
        if self._parent_tmp is not None:
            self._parent_tmp.cleanup()

    # ------------------------------------------------------------------
    # command dispatch
    # ------------------------------------------------------------------

    def handle_line(self, line: str) -> tuple[bool, list[str]]:
        stripped = line.strip()
        if not stripped:
            return True, []
        try:
            parts = shlex.split(stripped)
        except ValueError as exc:
            return True, [f"ERROR parse_error: {exc}"]
        if not parts:
            return True, []

        command = parts[0].lower()
        args = parts[1:]
        try:
            if command in {"help", "?"}:
                return True, self._help()
            if command in {"exit", "quit"}:
                return False, ["Exiting interactive MVP adapter. No GAUSS was run by this adapter."]
            if command == "workspace":
                return True, self._workspace(args)
            if command == "request":
                return True, self._request(args)
            if command == "plan":
                return True, self._plan()
            if command == "confirm":
                return True, self._confirm(args)
            if command == "decline":
                return True, self._decline()
            if command == "execute":
                return True, self._execute()
            if command == "outputs":
                return True, self._outputs()
            if command == "read":
                return True, self._read(args)
            if command == "provenance":
                return True, self._provenance()
            if command == "status":
                return True, self._status()
            if command == "reset":
                return True, self._reset()
            return True, [f"ERROR unknown_command: {command!r}. Type 'help' for commands."]
        except Exception as exc:  # noqa: BLE001
            return True, [f"ERROR {type(exc).__name__}: {exc}"]

    # ------------------------------------------------------------------
    # commands
    # ------------------------------------------------------------------

    def _help(self) -> list[str]:
        return [
            "GAUSS Code Assistant Interactive MVP Adapter (v0.47.0 alpha)",
            "Commands:",
            "  help",
            "  workspace create",
            "  workspace status",
            "  request [--fake-success|--fake-failure] <GAUSS code or short request>",
            "  plan",
            "  confirm <request_hash>",
            "  decline",
            "  execute",
            "  outputs",
            "  read <relative-path>",
            "  provenance",
            "  status",
            "  reset",
            "  exit",
            "Default execution uses a deterministic fake runner. GAUSS is never run by this adapter.",
        ]

    def _workspace(self, args: list[str]) -> list[str]:
        if not args:
            return ["ERROR usage: workspace create | workspace status"]
        sub = args[0].lower()
        if sub == "create":
            workspace = self.registry.create_workspace()
            Path(workspace.root_path).mkdir(parents=True, exist_ok=True)
            self.registry.update_workspace_status(workspace.workspace_id, to_status=workspace_mod.WorkspaceStatus.POPULATED)
            self.registry.update_workspace_status(workspace.workspace_id, to_status=workspace_mod.WorkspaceStatus.READY)
            self.active_workspace_id = workspace.workspace_id
            self.mvp_session = None
            self.pending_request = None
            self.last_result = None
            return [
                "REAL_WORKFLOW: WorkspaceRegistry.create_workspace + lifecycle ready.",
                f"adapter_session_id: {self.adapter_session_id}",
                f"workspace_id: {workspace.workspace_id}",
                f"workspace_root: {workspace.root_path}",
                "workspace_status: ready",
            ]
        if sub == "status":
            return self._workspace_status()
        return ["ERROR usage: workspace create | workspace status"]

    def _workspace_status(self) -> list[str]:
        if self.active_workspace_id is None:
            return ["workspace_status: none. Run 'workspace create' first."]
        workspace = self.registry.get_workspace(self.active_workspace_id)
        manifest = self.registry.get_workspace_manifest(self.active_workspace_id)
        return [
            "REAL_WORKFLOW: WorkspaceRegistry.get_workspace/get_workspace_manifest.",
            f"workspace_id: {workspace.workspace_id}",
            f"workspace_root: {workspace.root_path}",
            f"workspace_status: {workspace.status.value}",
            f"manifest_file_count: {len(manifest.files)}",
        ]

    def _request(self, args: list[str]) -> list[str]:
        fake_result = "success"
        remaining = list(args)
        if remaining and remaining[0] == "--fake-success":
            fake_result = "success"
            remaining = remaining[1:]
        elif remaining and remaining[0] == "--fake-failure":
            fake_result = "failure"
            remaining = remaining[1:]

        text = " ".join(remaining).strip()
        if not text:
            code = FAILURE_CODE if fake_result == "failure" else DEFAULT_CODE
            summary = f"Run default {fake_result} fixture"
        else:
            code = text.replace("\\n", "\n")
            summary = text if len(text) <= 120 else text[:117] + "..."

        self._turn_counter += 1
        self.pending_request = PendingRequest(
            request_id=f"req-{self._turn_counter}",
            summary=summary,
            code=code,
            fake_result=fake_result,
        )
        self.mvp_session = mvp.MvpWorkflowSession()
        self.last_result = None
        return [
            "ADAPTER: Stored request. No workflow execution occurred yet.",
            "ADAPTER_DISCLOSURE: Request interpretation is limited and adapter-driven.",
            f"request_id: {self.pending_request.request_id}",
            f"fake_runner_mode: {fake_result}",
            "next_step: run 'plan'",
        ]

    def _plan(self) -> list[str]:
        if self.active_workspace_id is None:
            return ["ERROR no_workspace: run 'workspace create' first."]
        if self.pending_request is None or self.mvp_session is None:
            return ["ERROR no_request: run 'request <code>' first."]

        outcome = self.workflow.propose(
            self.mvp_session,
            request_summary=self.pending_request.summary,
            session_id=self.adapter_session_id,
            request_id=self.pending_request.request_id,
            execution_purpose="manual interactive MVP alpha test",
            eligibility_declarations=wf.EligibilityDeclarations(execution_explicitly_requested=True),
            safety_input=_passing_safety(),
            code=self.pending_request.code,
            executable_path=DEFAULT_EXECUTABLE,
            gauss_version="GAUSS 26 (fake runner default; no GAUSS invocation)",
            timeout_seconds=30.0,
            workspace_id=self.active_workspace_id,
        )
        if outcome.blocked:
            return [
                "REAL_WORKFLOW: GaussCodeAssistantWorkflow.propose -> blocked.",
                f"adapter_session_id: {self.adapter_session_id}",
                f"orchestration_instance_id: {outcome.orchestration_instance_id}",
                f"failure_category: {outcome.failure_category}",
                f"failure_reason: {outcome.failure_reason}",
                "No execution occurred.",
            ]

        assert outcome.proposal is not None
        p = outcome.proposal
        return [
            "REAL_WORKFLOW: GaussCodeAssistantWorkflow.propose invoked.",
            "Execution plan (nothing has run):",
            f"adapter_session_id: {self.adapter_session_id}",
            f"workspace_id: {p.workspace_id}",
            f"request_id: {p.request_id}",
            f"orchestration_instance_id: {p.orchestration_instance_id}",
            "execution_session_reference_alias: orchestration_instance_id (not a durable ExecutionSession ID yet)",
            f"request_hash: {p.request_hash}",
            f"plan_digest: {p.plan_digest}",
            f"code_digest: {p.code_digest}",
            f"working_directory: {p.working_directory}",
            f"executable_path: {p.executable_path}",
            f"timeout_seconds: {p.timeout_seconds}",
            "confirmation_required: run 'confirm <request_hash>' to execute this exact plan.",
        ]

    def _confirm(self, args: list[str]) -> list[str]:
        if self.mvp_session is None or self.mvp_session.proposal_outcome is None:
            return ["ERROR no_plan: run 'plan' first."]
        if not args:
            return ["ERROR usage: confirm <request_hash>"]
        supplied_hash = args[0]
        proposal = self.mvp_session.proposal_outcome.proposal
        if proposal is None:
            return ["ERROR no_confirmable_plan: the proposal was blocked."]

        event = wf.WorkflowConfirmationEvent(
            session_id=self.adapter_session_id,
            orchestration_instance_id=proposal.orchestration_instance_id,
            request_id=proposal.request_id,
            request_hash=proposal.request_hash,
            decision="accepted",
            timestamp=str(self._clock()),
            source_interaction_id="terminal-confirm",
            plan_digest=supplied_hash,
        )
        outcome = self.workflow.confirm(self.mvp_session, event)
        return [
            "REAL_WORKFLOW: GaussCodeAssistantWorkflow.confirm invoked.",
            f"orchestration_instance_id: {outcome.orchestration_instance_id}",
            f"decision: {outcome.decision}",
            f"accepted: {outcome.accepted}",
            f"current_state: {outcome.current_state}",
            "next_step: run 'execute'",
        ]

    def _decline(self) -> list[str]:
        if self.mvp_session is None or self.mvp_session.proposal_outcome is None:
            return ["ERROR no_plan: run 'plan' first."]
        proposal = self.mvp_session.proposal_outcome.proposal
        if proposal is None:
            return ["ERROR no_confirmable_plan: the proposal was blocked."]
        event = wf.WorkflowConfirmationEvent(
            session_id=self.adapter_session_id,
            orchestration_instance_id=proposal.orchestration_instance_id,
            request_id=proposal.request_id,
            request_hash=proposal.request_hash,
            decision="rejected",
            timestamp=str(self._clock()),
            source_interaction_id="terminal-decline",
            plan_digest=proposal.plan_digest,
        )
        outcome = self.workflow.confirm(self.mvp_session, event)
        final = self.workflow.compose_response(self.mvp_session)
        self.last_result = final
        return [
            "REAL_WORKFLOW: GaussCodeAssistantWorkflow.confirm invoked with decision=rejected.",
            f"accepted: {outcome.accepted}",
            f"current_state: {outcome.current_state}",
            f"summary: {final.user_facing_summary}",
        ]

    def _execute(self) -> list[str]:
        if self.mvp_session is None:
            return ["ERROR no_session: run 'request' and 'plan' first."]
        if self.pending_request is None:
            return ["ERROR no_request: run 'request <code>' first."]
        result = self.workflow.execute(self.mvp_session, runner=self._fake_runner(self.pending_request.fake_result))
        final = self.workflow.compose_response(self.mvp_session)
        self.last_result = final
        return [
            "REAL_WORKFLOW: GaussCodeAssistantWorkflow.execute invoked.",
            "FAKE_RUNNER: deterministic fake runner used; GAUSS was not run.",
            f"orchestration_instance_id: {result.orchestration_instance_id}",
            f"execution_status: {result.execution_status}",
            f"executed: {result.executed}",
            f"runtime_error_detected: {result.runtime_error_detected}",
            f"output_file_count: {result.output_file_count}",
            f"analysis_status: {result.analysis_status}",
            f"summary: {final.user_facing_summary}",
        ]

    def _outputs(self) -> list[str]:
        if self.last_result is None:
            return ["ERROR no_result: run 'execute' first."]
        lines = [
            "REAL_WORKFLOW: Reporting WorkflowResult.files_produced metadata only.",
            "CONTENT_DISCLOSURE: No file contents are read by 'outputs'. Use 'read <relative-path>'.",
            f"file_count: {len(self.last_result.files_produced)}",
        ]
        for item in self.last_result.files_produced:
            lines.append(
                f"output: path={item.path} size_bytes={item.size_bytes} file_type={item.file_type} "
                f"created_by_execution={item.created_by_execution}"
            )
        return lines

    def _read(self, args: list[str]) -> list[str]:
        if self.active_workspace_id is None:
            return ["ERROR no_workspace: run 'workspace create' first."]
        if self.mvp_session is None:
            return ["ERROR no_session: run 'request', 'plan', and execute or inspect first."]
        if not args:
            return ["ERROR usage: read <relative-path>"]
        relative_path = args[0]
        result = self.workflow.read_file(
            self.mvp_session,
            file_reader_mod.WorkspaceFileReadRequest(
                workspace_id=self.active_workspace_id,
                relative_path=relative_path,
            ),
        )
        lines = [
            "REAL_WORKFLOW: GaussCodeAssistantWorkflow.read_file -> ExecutionWorkflow.read_workspace_file invoked.",
            f"workspace_id: {result.workspace_id}",
            f"relative_path: {result.relative_path}",
            f"read_status: {result.status}",
            f"error_code: {result.error_code}",
            f"size_bytes: {result.size_bytes}",
            f"truncated: {result.truncated}",
        ]
        if result.status == file_reader_mod.ReadStatus.COMPLETED.value:
            lines.extend(["content_begin", result.content or "", "content_end"])
        else:
            lines.append(f"error_message: {result.error_message}")
        return lines

    def _provenance(self) -> list[str]:
        if self.last_result is None:
            return ["ERROR no_result: run 'execute' first."]
        provenance = self.last_result.provenance
        lines = [
            "REAL_WORKFLOW: Reporting WorkflowResult.provenance.",
            f"adapter_session_id: {self.adapter_session_id}",
            f"workspace_id: {self.last_result.workspace_id}",
            f"execution_session_reference: {self.last_result.execution_session_reference}",
            "execution_session_reference_note: this is orchestration_instance_id, not a durable ExecutionSession ID yet.",
        ]
        if provenance is None:
            lines.append("provenance: none")
            return lines
        lines.extend(
            [
                f"provenance.workspace_id: {provenance.workspace_id}",
                f"provenance.execution_session_id: {provenance.execution_session_id}",
                f"provenance.execution_instance_id: {provenance.execution_instance_id}",
                f"provenance.artifact_count: {len(provenance.artifacts)}",
            ]
        )
        for artifact in provenance.artifacts:
            lines.append(
                f"artifact: relative_path={artifact.relative_path} source={artifact.source} "
                f"size={artifact.size} creation_state={artifact.creation_state}"
            )
        return lines

    def _status(self) -> list[str]:
        stage = self.mvp_session.stage.value if self.mvp_session is not None else "none"
        request_id = self.pending_request.request_id if self.pending_request is not None else "none"
        instance_id = self.mvp_session.orchestration_instance_id if self.mvp_session is not None else None
        return [
            "ADAPTER_STATUS:",
            f"adapter_session_id: {self.adapter_session_id}",
            f"workspace_id: {self.active_workspace_id or 'none'}",
            f"request_id: {request_id}",
            f"mvp_stage: {stage}",
            f"orchestration_instance_id: {instance_id or 'none'}",
            "fake_runner_default: true",
            "gauss_ran: false",
        ]

    def _reset(self) -> list[str]:
        self.mvp_session = None
        self.pending_request = None
        self.last_result = None
        return [
            "ADAPTER: Cleared active request, proposal, confirmation, and result.",
            "workspace_retained: true",
            f"workspace_id: {self.active_workspace_id or 'none'}",
            "If the retained workspace is completed, run 'workspace create' before another execution.",
        ]

    # ------------------------------------------------------------------
    # fake execution
    # ------------------------------------------------------------------

    def _fake_runner(self, mode: str):
        def runner(runner_input: Any) -> dict[str, Any]:
            workdir = Path(runner_input.working_directory)
            if mode == "failure":
                return {
                    "executed": True,
                    "execution_status": "failed",
                    "exit_code": 0,
                    "stdout": "Program execute failed\n",
                    "stderr": "error G0105 : Undefined symbol\n",
                    "output_files": [],
                    "warnings": ["fake runner result; GAUSS was not invoked"],
                    "errors": ["error G0105 : Undefined symbol"],
                }
            output_path = workdir / "fake-output.txt"
            content = (
                "fake GAUSS Code Assistant MVP output\n"
                f"adapter_session_id={self.adapter_session_id}\n"
                "gauss_ran=false\n"
            ).encode("utf-8")
            output_path.write_bytes(content)
            return {
                "executed": True,
                "execution_status": "completed",
                "exit_code": 0,
                "stdout": "fake runner completed\n",
                "stderr": "",
                "output_files": [
                    {
                        "path": str(output_path),
                        "size_bytes": len(content),
                        "file_type": "text/plain",
                        "created_by_execution": "deterministic_fake_runner",
                    }
                ],
                "warnings": ["fake runner result; GAUSS was not invoked"],
                "errors": [],
            }

        return runner


def run_repl(adapter: InteractiveMvpAdapter) -> int:
    print("GAUSS Code Assistant Interactive MVP Adapter (v0.47.0 alpha)")
    print("Type 'help' for commands. Default execution uses a deterministic fake runner; GAUSS is never run.")
    try:
        while True:
            try:
                line = input(PROMPT)
            except EOFError:
                print()
                break
            keep_going, output = adapter.handle_line(line)
            for item in output:
                print(item)
            if not keep_going:
                break
    finally:
        adapter.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Interactive terminal adapter for the GAUSS Code Assistant MVP workflow. "
            "Uses a deterministic fake runner by default and never runs GAUSS."
        )
    )
    parser.add_argument(
        "--workspace-parent",
        default=None,
        help="Approved parent directory for alpha workspaces. Defaults to a temporary directory.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    adapter = InteractiveMvpAdapter(workspace_parent=args.workspace_parent)
    return run_repl(adapter)


if __name__ == "__main__":
    raise SystemExit(main())
