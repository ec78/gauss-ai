"""Interactive terminal adapter for the GAUSS Code Assistant MVP workflow.

This is the v0.47.0 Interactive MVP Adapter. It is intentionally thin:
terminal commands are translated into the existing
`GaussCodeAssistantWorkflow` facade and its underlying workspace/execution
components. The adapter owns no execution eligibility, confirmation,
workspace-boundary, file-reading, or provenance safety logic.

Default execution uses a deterministic fake runner. Real local GAUSS execution
is available only when the tester explicitly starts the adapter with
`--runner gauss`; that path lazily imports the existing `gauss_code_execution`
helper and never falls back to the fake runner.
"""

from __future__ import annotations

import argparse
import os
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
import gauss_execution_diagnostics as diagnostics  # noqa: E402
import gauss_execution_interpreter as interpreter  # noqa: E402
import gauss_execution_workflow as wf  # noqa: E402
import gauss_repair_application as application_transaction  # noqa: E402
import gauss_repair_application_approval as application_approval  # noqa: E402
import gauss_repair_application_gate as application_gate  # noqa: E402
import gauss_repair_approval as repair_approval  # noqa: E402
import gauss_repair_draft as repair_draft_mod  # noqa: E402
import gauss_repair_draft_approval as draft_approval  # noqa: E402
import gauss_repair_planner as repair_planner  # noqa: E402
import gauss_orchestration_state_store as store_mod  # noqa: E402
import gauss_workspace as workspace_mod  # noqa: E402
import gauss_workspace_file_reader as file_reader_mod  # noqa: E402


PROMPT = "gauss-mvp> "
DEFAULT_CODE = "x = 2 + 2;\nprint x;"
FAILURE_CODE = "x = ;"
DEFAULT_EXECUTABLE = "C:/example/gauss26/tgauss.exe"
FAKE_BACKEND = "fake"
REAL_GAUSS_BACKEND = "gauss"
DEFAULT_FAKE_GAUSS_VERSION = "GAUSS 26 (fake runner default; no GAUSS invocation)"
DEFAULT_REAL_GAUSS_VERSION = "GAUSS local terminal executable (explicit opt-in)"


@dataclass(frozen=True)
class PendingRequest:
    request_id: str
    summary: str
    code: str
    fake_result: str


@dataclass
class ExecutionProcessMetadata:
    backend: str
    executable_path: str | None = None
    gauss_ran: bool = False
    executed: bool = False
    execution_status: str | None = None
    exit_code: int | None = None
    timed_out: bool = False
    elapsed_seconds: float | None = None
    timeout_seconds: float | None = None
    stdout_chars: int = 0
    stderr_chars: int = 0
    generated_script_path: str | None = None
    command_preview: str | None = None
    error: str | None = None


@dataclass
class CapturedProcessOutput:
    stdout: str | None = None
    stderr: str | None = None


def _backend_label(backend: str) -> str:
    if backend == REAL_GAUSS_BACKEND:
        return "REAL_GAUSS"
    return "FAKE"


def _resolve_real_executable(
    *,
    runner_backend: str,
    gauss_executable: str | Path | None,
    env: dict[str, str] | None = None,
) -> str | None:
    if runner_backend != REAL_GAUSS_BACKEND:
        return None

    env_values = os.environ if env is None else env
    candidate = str(gauss_executable).strip() if gauss_executable is not None else ""
    if not candidate:
        candidate = env_values.get("GAUSS_EXECUTABLE", "").strip()
    if not candidate:
        raise ValueError("real GAUSS runner requires --gauss-executable or GAUSS_EXECUTABLE.")

    path = Path(candidate).expanduser().resolve(strict=False)
    if not path.exists() or not path.is_file():
        raise ValueError(f"real GAUSS executable was not found: {path}")
    if path.name.lower() not in {"tgauss", "tgauss.exe"}:
        raise ValueError(
            "real GAUSS runner requires a terminal executable named tgauss or tgauss.exe; "
            f"refusing {path.name!r}."
        )
    return str(path)


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
        runner_backend: str = FAKE_BACKEND,
        gauss_executable: str | Path | None = None,
        gauss_version: str | None = None,
        real_helper: Any | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        if runner_backend not in {FAKE_BACKEND, REAL_GAUSS_BACKEND}:
            raise ValueError("runner_backend must be 'fake' or 'gauss'.")
        self.adapter_session_id = session_id or f"adapter-{uuid.uuid4().hex}"
        self._clock = clock
        self.runner_backend = runner_backend
        self.backend_label = _backend_label(runner_backend)
        self.real_gauss_executable = _resolve_real_executable(
            runner_backend=runner_backend,
            gauss_executable=gauss_executable,
            env=env,
        )
        self.gauss_version = (
            gauss_version
            if gauss_version is not None
            else (DEFAULT_REAL_GAUSS_VERSION if runner_backend == REAL_GAUSS_BACKEND else DEFAULT_FAKE_GAUSS_VERSION)
        )
        self._real_helper = real_helper
        self.last_process_metadata = ExecutionProcessMetadata(backend=self.backend_label)
        self.last_captured_output = CapturedProcessOutput()
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
        # v0.57.0: the most recent repair plan this adapter session computed
        # (whatever `repair-plan`'s own args produced) -- `approve-repair`/
        # `decline-repair` operate against this exact plan, never a
        # recomputed one, since a caller's source-context flags are not
        # otherwise remembered between calls.
        self.last_repair_plan: repair_planner.RepairPlan | None = None
        self._repair_approval_store = repair_approval.RepairApprovalStore()
        # v0.59.0: the most recent repair draft this adapter session
        # constructed -- process-local only, exactly like last_repair_plan;
        # no draft is ever persisted, and no draft-approval mechanism reads
        # this field (drafting has no consumer yet).
        self.last_repair_draft: repair_draft_mod.RepairDraft | None = None
        self._draft_counter = 0
        # v0.60.0: process-local store of draft-approval decisions -- exactly
        # as durable (i.e. not) as _repair_approval_store already is.
        self._draft_approval_store = draft_approval.DraftApprovalStore()
        # v0.61.0: process-local store of application-approval decisions --
        # exactly as durable (i.e. not) as the other two approval stores.
        # Binds to the same draft digest draft approval itself binds to,
        # never a separately-computed "application digest" (see
        # gauss_repair_application_approval.py's own module docstring).
        self._application_approval_store = application_approval.ApplicationApprovalStore()
        # v0.62.0: the most recent repair-application transaction result --
        # process-local only, exactly like every other repair-layer field.
        # This adapter never writes to a file except through
        # gauss_repair_application.apply_repair(...); no other command
        # touches a source file's bytes.
        self.last_application_result: application_transaction.ApplicationResult | None = None
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
                ran_text = (
                    "GAUSS process started in this adapter session."
                    if self.last_process_metadata.gauss_ran
                    else "No GAUSS was run; no GAUSS process was started by this adapter session."
                )
                return False, [f"Exiting interactive MVP adapter. {ran_text}"]
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
            if command == "stdout":
                return True, self._captured_stream("stdout")
            if command == "stderr":
                return True, self._captured_stream("stderr")
            if command == "interpret":
                return True, self._interpret()
            if command == "diagnose":
                return True, self._diagnose()
            if command == "repair-plan":
                return True, self._repair_plan(args)
            if command == "approve-repair":
                return True, self._approve_repair(args)
            if command == "decline-repair":
                return True, self._decline_repair(args)
            if command == "repair-draft":
                return True, self._repair_draft(args)
            if command == "show-repair-draft":
                return True, self._show_repair_draft(args)
            if command == "approve-repair-draft":
                return True, self._approve_repair_draft(args)
            if command == "decline-repair-draft":
                return True, self._decline_repair_draft(args)
            if command == "show-repair-draft-approval":
                return True, self._show_repair_draft_approval(args)
            if command == "approve-repair-application":
                return True, self._approve_repair_application(args)
            if command == "decline-repair-application":
                return True, self._decline_repair_application(args)
            if command == "show-repair-application-approval":
                return True, self._show_repair_application_approval(args)
            if command == "check-repair-application-gate":
                return True, self._check_repair_application_gate(args)
            if command == "apply-repair":
                return True, self._apply_repair(args)
            if command == "show-application-result":
                return True, self._show_application_result(args)
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
            "GAUSS Code Assistant Interactive MVP Adapter (v0.62.0 alpha)",
            f"Execution backend: {self.backend_label}",
            "Commands:",
            "  help",
            "  workspace create",
            "  workspace status",
            "  request [--fake-success|--fake-failure|--fake-timeout|--fake-unknown-error] <GAUSS code or short request>",
            "  plan",
            "  confirm <request_hash>",
            "  decline",
            "  execute",
            "  outputs",
            "  stdout",
            "  stderr",
            "  interpret",
            "  diagnose",
            "  repair-plan [--source-text TEXT] [--matrix-shape NAME=RxC ...] [--path PATH ...]",
            "              [--procedure NAME] [--args SUMMARY] [--line-start N] [--line-end N]",
            "  approve-repair <plan_digest>",
            "  decline-repair <plan_digest>",
            "  repair-draft --path PATH --content-hash SHA256 --size N --line-start N --line-end N",
            "               --operation TEXT --description TEXT [--workspace-id ID] [--encoding utf-8]",
            "               [--procedure NAME] [--symbol NAME]",
            "  show-repair-draft",
            "  approve-repair-draft <draft_digest>",
            "  decline-repair-draft <draft_digest>",
            "  show-repair-draft-approval",
            "  approve-repair-application <draft_digest>",
            "  decline-repair-application <draft_digest>",
            "  show-repair-application-approval",
            "  check-repair-application-gate [--current-content-hash SHA256]",
            "  apply-repair <draft_digest> --replacement-text TEXT",
            "  show-application-result",
            "  read <relative-path>",
            "  provenance",
            "  status",
            "  reset",
            "  exit",
            "Default execution uses a deterministic fake runner.",
            "Real GAUSS execution is opt-in only with --runner gauss and a terminal tgauss executable.",
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
        elif remaining and remaining[0] == "--fake-timeout":
            # v0.52.0: a controlled, injected timeout result for benchmark
            # 43.4/evaluation use -- never an unbounded real GAUSS loop.
            fake_result = "timeout"
            remaining = remaining[1:]
        elif remaining and remaining[0] == "--fake-unknown-error":
            # v0.52.0: a deterministic uncataloged-error fixture (G9999 is
            # not, and must never become, a catalog entry) for benchmark
            # 43.9/evaluation use.
            fake_result = "unknown_error"
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
        self.last_process_metadata = ExecutionProcessMetadata(backend=self.backend_label)
        self.last_captured_output = CapturedProcessOutput()
        lines = [
            "ADAPTER: Stored request. No workflow execution occurred yet.",
            "ADAPTER_DISCLOSURE: Request interpretation is limited and adapter-driven.",
            f"request_id: {self.pending_request.request_id}",
            f"execution_backend: {self.backend_label}",
        ]
        if self.runner_backend == FAKE_BACKEND:
            # v0.52.0: only shown for the fake backend -- this field is
            # meaningless (and was confusingly echoed regardless of
            # backend before this fix) when --runner gauss is selected,
            # since real execution has no "fake_result" mode at all.
            lines.append(f"fake_runner_mode: {fake_result}")
        lines.append("next_step: run 'plan'")
        return lines

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
            executable_path=self.real_gauss_executable or DEFAULT_EXECUTABLE,
            gauss_version=self.gauss_version,
            timeout_seconds=30.0,
            workspace_id=self.active_workspace_id,
        )
        if outcome.blocked:
            lines = [
                "REAL_WORKFLOW: GaussCodeAssistantWorkflow.propose -> blocked.",
                f"adapter_session_id: {self.adapter_session_id}",
                f"orchestration_instance_id: {outcome.orchestration_instance_id}",
                f"failure_category: {outcome.failure_category}",
                f"failure_reason: {outcome.failure_reason}",
                "No execution occurred.",
                "No new plan was created.",
            ]
            reason = outcome.failure_reason or ""
            if "already completed its single allowed execution attempt" in reason:
                lines.extend(
                    [
                        "workspace_single_shot_exhausted: true",
                        "guidance: this workspace already completed its one allowed execution attempt; "
                        "its lifecycle does not permit a second plan or execution. Run 'workspace create' "
                        "to start a fresh workspace before requesting or planning again.",
                        "note: 'reset' alone clears the current request/plan/result state, but does not "
                        "change this workspace's own completed status -- 'workspace create' is required.",
                    ]
                )
            elif "is currently executing" in reason:
                lines.append(
                    "guidance: this workspace's prior execution attempt has not finished; wait for it to "
                    "conclude, or run 'workspace create' to start a fresh workspace."
                )
            return lines

        assert outcome.proposal is not None
        p = outcome.proposal
        return [
            "REAL_WORKFLOW: GaussCodeAssistantWorkflow.propose invoked.",
            "Execution plan (nothing has run):",
            f"execution_backend: {self.backend_label}",
            f"real_gauss_will_run_after_confirm_execute: {str(self.runner_backend == REAL_GAUSS_BACKEND).lower()}",
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
            "script_path: inline code; gauss_code_execution will generate a .gss script inside the workspace at execution time",
            f"timeout_seconds: {p.timeout_seconds}",
            "request_hash_confirmation: the request_hash above must be supplied exactly before execution.",
            "content_boundary: stdout/stderr and output files are not read automatically.",
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
        runner = (
            self._fake_runner(self.pending_request.fake_result)
            if self.runner_backend == FAKE_BACKEND
            else self._real_gauss_runner()
        )
        result = self.workflow.execute(self.mvp_session, runner=runner)
        final = self.workflow.compose_response(self.mvp_session)
        self.last_result = final
        metadata = self.last_process_metadata
        return [
            "REAL_WORKFLOW: GaussCodeAssistantWorkflow.execute invoked.",
            (
                "FAKE_RUNNER: deterministic fake runner used; GAUSS was not run."
                if self.runner_backend == FAKE_BACKEND
                else "REAL_GAUSS_RUNNER: existing gauss_code_execution helper selected; no fake fallback was used."
            ),
            f"execution_backend: {metadata.backend}",
            f"gauss_ran: {str(metadata.gauss_ran).lower()}",
            f"orchestration_instance_id: {result.orchestration_instance_id}",
            f"execution_status: {result.execution_status}",
            f"executed: {result.executed}",
            f"exit_code: {metadata.exit_code}",
            f"timed_out: {str(metadata.timed_out).lower()}",
            f"duration_seconds: {metadata.elapsed_seconds}",
            f"stdout_chars: {metadata.stdout_chars}",
            f"stderr_chars: {metadata.stderr_chars}",
            f"generated_script_path: {metadata.generated_script_path or 'none'}",
            f"runtime_error_detected: {result.runtime_error_detected}",
            f"output_file_count: {result.output_file_count}",
            f"analysis_status: {result.analysis_status}",
            "content_boundary: stdout/stderr contents and output file contents were not displayed automatically.",
            "next_debug_step: use 'stdout' or 'stderr' to inspect captured process text explicitly.",
            "next_interpretation_step: use 'interpret' to explain the execution result from captured evidence.",
            f"summary: {final.user_facing_summary}",
        ]

    def _outputs(self) -> list[str]:
        if self.last_result is None:
            return ["ERROR no_result: run 'execute' first."]
        lines = [
            "REAL_WORKFLOW: Reporting WorkflowResult.files_produced metadata only.",
            "CONTENT_DISCLOSURE: No file contents are read by 'outputs'. Use 'read <relative-path>'.",
            f"execution_backend: {self.last_process_metadata.backend}",
            f"file_count: {len(self.last_result.files_produced)}",
        ]
        for item in self.last_result.files_produced:
            lines.append(
                f"output: path={item.path} size_bytes={item.size_bytes} file_type={item.file_type} "
                f"created_by_execution={item.created_by_execution}"
            )
        return lines

    def _captured_stream(self, stream_name: str) -> list[str]:
        if self.last_result is None:
            return [f"ERROR no_result: run 'execute' before inspecting {stream_name}."]
        if stream_name == "stdout":
            content = self.last_captured_output.stdout
        else:
            content = self.last_captured_output.stderr
        if content is None:
            content = ""
        return [
            f"REAL_WORKFLOW: Reporting captured {stream_name} only after explicit request.",
            f"execution_backend: {self.last_process_metadata.backend}",
            f"gauss_ran: {str(self.last_process_metadata.gauss_ran).lower()}",
            f"{stream_name}_chars: {len(content)}",
            f"{stream_name}_begin",
            content,
            f"{stream_name}_end",
        ]

    def _build_execution_evidence(self) -> "interpreter.ExecutionEvidence":
        """Shared by `_interpret()` and `_diagnose()` so both operate on an
        identically-assembled evidence snapshot -- assembly only, no
        classification logic lives here (that stays in `interpret_execution`,
        called once by `interpret` and once, internally, by `diagnose`)."""
        metadata = self.last_process_metadata
        assert self.last_result is not None
        return interpreter.ExecutionEvidence(
            runner=metadata.backend,
            gauss_ran=metadata.gauss_ran,
            executed=metadata.executed or self.last_result.execution_status is not None,
            execution_status=self.last_result.execution_status or metadata.execution_status,
            exit_code=metadata.exit_code,
            stdout_chars=metadata.stdout_chars,
            stderr_chars=metadata.stderr_chars,
            timed_out=metadata.timed_out,
            workspace_state=self.last_result.execution_status,
            provenance=self.last_result.provenance,
            stdout_text=self.last_captured_output.stdout,
            stderr_text=self.last_captured_output.stderr,
            metadata_error=metadata.error,
        )

    def _interpret(self) -> list[str]:
        if self.last_result is None:
            return ["ERROR no_result: run 'execute' before interpreting execution evidence."]
        evidence = self._build_execution_evidence()
        result = interpreter.interpret_execution(evidence)
        lines = [
            "REAL_WORKFLOW: Execution interpretation from existing evidence only.",
            "INTERPRETER_BOUNDARY: No GAUSS launch, no retry, no code edit, no automatic file read.",
            f"execution_phase: {result.execution_phase}",
            f"launch_status: {result.launch_status}",
            f"completion_status: {result.completion_status}",
            f"failure_type: {result.failure_type}",
            f"error_code: {result.error_code}",
            f"error_category: {result.error_category}",
            f"confidence: {result.confidence}",
            f"requires_user_action: {str(result.requires_user_action).lower()}",
            f"safe_to_continue: {str(result.safe_to_continue).lower()}",
            f"summary: {result.summary}",
            f"user_explanation: {result.user_explanation}",
            f"technical_explanation: {result.technical_explanation}",
            f"likely_location: {result.likely_location}",
            f"next_step: {result.next_step}",
        ]
        for limitation in result.evidence_limitations:
            lines.append(f"evidence_limitation: {limitation}")
        if result.verification_status:
            lines.append(f"verification_status: {', '.join(result.verification_status)}")
            lines.append(f"verification_source: {result.verification_source}")
        if result.documentation_discrepancy:
            lines.append(f"documentation_discrepancy: {result.documentation_discrepancy}")
        return lines

    def _diagnose(self) -> list[str]:
        if self.last_result is None:
            return ["ERROR no_result: run 'execute' before diagnosing execution evidence."]
        evidence = self._build_execution_evidence()
        assessment = diagnostics.diagnose_execution(evidence)
        lines = [
            "REAL_WORKFLOW: Diagnostic reasoning from existing evidence and interpretation only.",
            "DIAGNOSTIC_BOUNDARY: No GAUSS launch, no execute, no plan, no retry, no code edit, no automatic file read, "
            "no workspace mutation.",
            f"diagnostic_status: {assessment.diagnostic_status}",
            f"confidence: {assessment.confidence}",
            f"summary: {assessment.summary}",
            f"safe_to_continue: {str(assessment.safe_to_continue).lower()}",
            f"requires_user_input: {str(assessment.requires_user_input).lower()}",
            f"source_error_code: {assessment.source_error_code}",
            f"source_error_category: {assessment.source_error_category}",
        ]
        if assessment.knowledge_verification:
            lines.append(f"knowledge_verification: {', '.join(assessment.knowledge_verification)}")
        lines.append("known_facts:")
        for fact in assessment.supporting_evidence:
            lines.append(f"  - {fact}")
        if assessment.contradicting_evidence:
            lines.append("contradicting_evidence:")
            for item in assessment.contradicting_evidence:
                lines.append(f"  - {item}")
        lines.append(f"possible_cause_count: {len(assessment.possible_causes)}")
        for cause in assessment.possible_causes:
            lines.append(f"  cause[{cause.cause_id}] (confidence={cause.confidence}, catalog_verified={cause.is_catalog_verified}): {cause.description}")
        if assessment.missing_evidence:
            lines.append("missing_evidence:")
            for item in assessment.missing_evidence:
                lines.append(f"  - {item}")
        if assessment.questions_to_ask:
            lines.append("questions_to_ask:")
            for question in assessment.questions_to_ask:
                lines.append(f"  - {question}")
        if assessment.recommended_diagnostic_steps:
            lines.append("recommended_diagnostic_steps:")
            for step in assessment.recommended_diagnostic_steps:
                lines.append(f"  - {step}")
        for limitation in assessment.limitations:
            lines.append(f"limitation: {limitation}")
        lines.append(f"repair_boundary: {assessment.repair_boundary}")
        return lines

    def _parse_source_context(self, args: list[str]) -> "repair_planner.SourceContext | str":
        """Parses a small, bounded set of explicit source-context flags.
        Returns a `SourceContext` on success, or an error message string on
        invalid input. Never reads a file or fetches anything -- every value
        comes directly from the flags the caller typed."""
        code_text: str | None = None
        line_start: int | None = None
        line_end: int | None = None
        matrix_shapes: list[str] = []
        referenced_paths: list[str] = []
        procedure_name: str | None = None
        argument_summary: str | None = None

        i = 0
        while i < len(args):
            token = args[i]
            if token == "--source-text" and i + 1 < len(args):
                code_text = args[i + 1]
                i += 2
            elif token == "--matrix-shape" and i + 1 < len(args):
                matrix_shapes.append(args[i + 1])
                i += 2
            elif token == "--path" and i + 1 < len(args):
                referenced_paths.append(args[i + 1])
                i += 2
            elif token == "--procedure" and i + 1 < len(args):
                procedure_name = args[i + 1]
                i += 2
            elif token == "--args" and i + 1 < len(args):
                argument_summary = args[i + 1]
                i += 2
            elif token == "--line-start" and i + 1 < len(args):
                try:
                    line_start = int(args[i + 1])
                except ValueError:
                    return f"ERROR usage: --line-start requires an integer, got {args[i + 1]!r}"
                i += 2
            elif token == "--line-end" and i + 1 < len(args):
                try:
                    line_end = int(args[i + 1])
                except ValueError:
                    return f"ERROR usage: --line-end requires an integer, got {args[i + 1]!r}"
                i += 2
            else:
                return f"ERROR usage: unrecognized repair-plan option {token!r}"

        return repair_planner.SourceContext(
            code_text=code_text,
            line_start=line_start,
            line_end=line_end,
            matrix_shapes=tuple(matrix_shapes),
            referenced_paths=tuple(referenced_paths),
            procedure_name=procedure_name,
            argument_summary=argument_summary,
        )

    def _repair_plan(self, args: list[str]) -> list[str]:
        if self.last_result is None:
            return ["ERROR no_result: run 'execute' before requesting a repair plan."]
        parsed = self._parse_source_context(args)
        if isinstance(parsed, str):
            return [parsed]
        source_context = parsed if not parsed.is_empty() else None
        evidence = self._build_execution_evidence()
        plan = repair_planner.plan_repair(evidence, source_context=source_context)
        # v0.57.0: this exact plan object (not a recomputed one) is what
        # approve-repair/decline-repair validate a supplied digest against.
        self.last_repair_plan = plan
        plan_digest = repair_planner.repair_plan_digest(plan)
        lines = [
            "REAL_WORKFLOW: Repair planning from existing evidence, interpretation, and diagnosis only.",
            "REPAIR_PLAN_BOUNDARY: No GAUSS launch, no execute, no plan, no retry, no code edit, no file write, "
            "no patch application, no new execution proposal, no workspace mutation.",
            f"repair_status: {plan.repair_status}",
            f"plan_digest: {plan_digest}",
            f"confidence: {plan.confidence}",
            f"summary: {plan.summary}",
            f"source_context_used: {str(plan.source_context_used).lower()}",
            f"source_error_code: {plan.source_error_code}",
            f"source_error_category: {plan.source_error_category}",
        ]
        if plan.knowledge_verification:
            lines.append(f"knowledge_verification: {', '.join(plan.knowledge_verification)}")
        lines.append("evidence_supporting_plan:")
        for item in plan.supporting_evidence:
            lines.append(f"  - {item}")
        if plan.repair_strategy:
            lines.append(f"proposed_repair_strategy: {plan.repair_strategy}")
        if plan.target_scope:
            lines.append(f"target_scope: {plan.target_scope}")
        lines.append(f"proposed_action_count: {len(plan.proposed_actions)}")
        for action in plan.proposed_actions:
            lines.append(
                f"  action[{action.action_id}] type={action.action_type} confidence={action.confidence} "
                f"is_concrete_edit={str(action.is_concrete_edit).lower()}: {action.description}"
            )
        if plan.assumptions:
            lines.append("assumptions:")
            for item in plan.assumptions:
                lines.append(f"  - {item}")
        if plan.missing_evidence:
            lines.append("missing_evidence:")
            for item in plan.missing_evidence:
                lines.append(f"  - {item}")
        if plan.risks:
            lines.append("risks:")
            for item in plan.risks:
                lines.append(f"  - {item}")
        if plan.verification_steps:
            lines.append("verification_steps:")
            for item in plan.verification_steps:
                lines.append(f"  - {item}")
        if plan.questions_to_answer:
            lines.append("questions_to_answer:")
            for item in plan.questions_to_answer:
                lines.append(f"  - {item}")
        lines.extend(
            [
                f"requires_user_input: {str(plan.requires_user_input).lower()}",
                f"requires_explicit_approval: {str(plan.requires_explicit_approval).lower()}",
                f"safe_to_prepare_draft: {str(plan.safe_to_prepare_draft).lower()}",
                f"safe_to_apply: {str(plan.safe_to_apply).lower()}",
                f"repair_boundary: {plan.repair_boundary}",
                "application_boundary: No patch was applied. No file was modified. GAUSS was not rerun.",
            ]
        )
        if plan.requires_explicit_approval:
            lines.append(
                f"next_step: run 'approve-repair {plan_digest}' or 'decline-repair {plan_digest}' to record an "
                "explicit decision (this records a decision only -- it does not apply anything)."
            )
        return lines

    def _record_repair_decision(self, args: list[str], *, decision: "repair_approval.ApprovalDecision", command_name: str) -> list[str]:
        if self.last_repair_plan is None:
            return ["ERROR no_repair_plan: run 'repair-plan' first."]
        if not args:
            return [f"ERROR usage: {command_name} <plan_digest>"]
        supplied_digest = args[0]
        actual_digest = repair_planner.repair_plan_digest(self.last_repair_plan)
        if supplied_digest != actual_digest:
            return [
                "ERROR stale_or_incorrect_digest: supplied plan_digest does not match the current repair plan.",
                f"current_plan_digest: {actual_digest}",
                "guidance: run 'repair-plan' again to see the current digest, or re-supply the exact digest shown there.",
            ]
        try:
            if decision == repair_approval.ApprovalDecision.APPROVED:
                record = self._repair_approval_store.approve(self.last_repair_plan, recorded_at=str(self._clock()))
            else:
                record = self._repair_approval_store.decline(self.last_repair_plan, recorded_at=str(self._clock()))
        except repair_approval.ApprovalConflictError as exc:
            return [f"ERROR approval_conflict: {exc}"]
        return [
            "REAL_WORKFLOW: Repair-plan approval recorded from the current repair plan only.",
            "APPROVAL_BOUNDARY: No code was modified. No file was written. No patch was applied. No draft was "
            "prepared. GAUSS was not rerun.",
            f"decision: {record.decision}",
            f"plan_digest: {record.plan_digest}",
            f"recorded_at: {record.recorded_at}",
            f"safe_to_apply: {str(record.safe_to_apply).lower()}",
            f"safe_to_prepare_draft: {str(record.safe_to_prepare_draft).lower()}",
            f"approval_boundary: {record.approval_boundary}",
        ]

    def _approve_repair(self, args: list[str]) -> list[str]:
        return self._record_repair_decision(args, decision=repair_approval.ApprovalDecision.APPROVED, command_name="approve-repair")

    def _decline_repair(self, args: list[str]) -> list[str]:
        return self._record_repair_decision(args, decision=repair_approval.ApprovalDecision.DECLINED, command_name="decline-repair")

    def _parse_repair_draft_args(self, args: list[str]) -> dict[str, object] | str:
        """Parses a small, bounded set of explicit repair-draft flags.
        Returns a field dict on success, or an error message string on
        invalid input. Never reads a file -- every value comes directly from
        the flags the caller typed; `content_hash`/`size` in particular must
        be supplied by the caller, since this module (and this CLI) perform
        no I/O of their own."""
        relative_path: str | None = None
        content_hash: str | None = None
        size: int | None = None
        line_start: int | None = None
        line_end: int | None = None
        operation: str | None = None
        description: str | None = None
        workspace_id: str | None = None
        encoding = "utf-8"
        procedure: str | None = None
        symbol: str | None = None

        i = 0
        while i < len(args):
            token = args[i]
            if token == "--path" and i + 1 < len(args):
                relative_path = args[i + 1]
                i += 2
            elif token == "--content-hash" and i + 1 < len(args):
                content_hash = args[i + 1]
                i += 2
            elif token == "--size" and i + 1 < len(args):
                try:
                    size = int(args[i + 1])
                except ValueError:
                    return f"ERROR usage: --size requires an integer, got {args[i + 1]!r}"
                i += 2
            elif token == "--line-start" and i + 1 < len(args):
                try:
                    line_start = int(args[i + 1])
                except ValueError:
                    return f"ERROR usage: --line-start requires an integer, got {args[i + 1]!r}"
                i += 2
            elif token == "--line-end" and i + 1 < len(args):
                try:
                    line_end = int(args[i + 1])
                except ValueError:
                    return f"ERROR usage: --line-end requires an integer, got {args[i + 1]!r}"
                i += 2
            elif token == "--operation" and i + 1 < len(args):
                operation = args[i + 1]
                i += 2
            elif token == "--description" and i + 1 < len(args):
                description = args[i + 1]
                i += 2
            elif token == "--workspace-id" and i + 1 < len(args):
                workspace_id = args[i + 1]
                i += 2
            elif token == "--encoding" and i + 1 < len(args):
                encoding = args[i + 1]
                i += 2
            elif token == "--procedure" and i + 1 < len(args):
                procedure = args[i + 1]
                i += 2
            elif token == "--symbol" and i + 1 < len(args):
                symbol = args[i + 1]
                i += 2
            else:
                return f"ERROR usage: unrecognized repair-draft option {token!r}"

        if workspace_id is None:
            workspace_id = self.active_workspace_id
        missing = [
            name
            for name, value in (
                ("--path", relative_path),
                ("--content-hash", content_hash),
                ("--size", size),
                ("--line-start", line_start),
                ("--line-end", line_end),
                ("--operation", operation),
                ("--description", description),
            )
            if value is None
        ]
        if workspace_id is None:
            missing.append("--workspace-id (no active workspace to default to)")
        if missing:
            return f"ERROR usage: missing required repair-draft option(s): {', '.join(missing)}"

        return {
            "workspace_id": workspace_id,
            "relative_path": relative_path,
            "content_hash": content_hash,
            "size": size,
            "encoding": encoding,
            "line_start": line_start,
            "line_end": line_end,
            "operation": operation,
            "description": description,
            "procedure": procedure,
            "symbol": symbol,
        }

    def _render_repair_draft(self, draft: "repair_draft_mod.RepairDraft") -> list[str]:
        digest = repair_draft_mod.repair_draft_digest(draft)
        validation = repair_draft_mod.validate_repair_draft(draft)
        lines = [
            "REAL_WORKFLOW: Repair-draft construction and structural validation only.",
            "DRAFT_BOUNDARY: No file was read or written. No patch exists. No code was generated. No approval "
            "to edit files exists.",
            f"repair_draft_id: {draft.repair_draft_id}",
            f"repair_plan_digest: {draft.repair_plan_digest}",
            f"draft_digest: {digest}",
            f"workspace_id: {draft.source_identity.artifact.workspace_id}",
            f"relative_path: {draft.source_identity.artifact.relative_path}",
            f"file_type: {draft.source_identity.artifact.file_type}",
            f"source_content_hash: {draft.source_identity.content_hash}",
            f"source_size: {draft.source_identity.size}",
            f"source_encoding: {draft.source_identity.encoding}",
            f"edit_line_range: [{draft.edit_scope.line_start}, {draft.edit_scope.line_end}]",
            f"target_procedure: {draft.edit_scope.target_procedure}",
            f"target_symbol: {draft.edit_scope.target_symbol}",
            f"intended_operation: {draft.edit_scope.intended_operation}",
            f"proposed_change_description: {draft.proposed_change_description}",
        ]
        lines.append("assumptions:")
        for item in draft.assumptions:
            lines.append(f"  - {item}")
        lines.append("risks:")
        for item in draft.risks:
            lines.append(f"  - {item}")
        lines.append("verification_steps:")
        for item in draft.verification_steps:
            lines.append(f"  - {item}")
        lines.extend(
            [
                f"generated_at: {draft.generated_at}",
                f"generated_by: {draft.generated_by}",
                f"approval_required: {str(draft.approval_required).lower()}",
                f"safe_to_prepare_draft: {str(draft.safe_to_prepare_draft).lower()}",
                f"safe_to_apply: {str(draft.safe_to_apply).lower()}",
                f"draft_boundary: {draft.draft_boundary}",
                f"validation_all_passed: {str(validation.all_passed).lower()}",
            ]
        )
        if validation.failed_checks:
            lines.append(f"validation_failed_checks: {', '.join(validation.failed_checks)}")
        lines.append("validation_checks:")
        for item in validation.checks:
            lines.append(f"  - {item.check}: {'pass' if item.passed else 'FAIL'} -- {item.detail}")
        lines.extend(
            [
                "disclosure: This is NOT an applied repair.",
                "disclosure: No files were modified.",
                "disclosure: No patch exists.",
                "disclosure: No code has been generated.",
                "disclosure: No approval to edit files exists.",
            ]
        )
        return lines

    def _repair_draft(self, args: list[str]) -> list[str]:
        if self.last_repair_plan is None:
            return ["ERROR no_repair_plan: run 'repair-plan' first."]
        parsed = self._parse_repair_draft_args(args)
        if isinstance(parsed, str):
            return [parsed]
        self._draft_counter += 1
        artifact = repair_draft_mod.SourceArtifact(
            workspace_id=str(parsed["workspace_id"]),
            relative_path=str(parsed["relative_path"]),
            file_type=Path(str(parsed["relative_path"])).suffix,
        )
        identity = repair_draft_mod.SourceIdentity(
            artifact=artifact,
            content_hash=str(parsed["content_hash"]),
            size=int(parsed["size"]),  # type: ignore[arg-type]
            encoding=str(parsed["encoding"]),
            observed_at=str(self._clock()),
        )
        scope = repair_draft_mod.EditScope(
            line_start=int(parsed["line_start"]),  # type: ignore[arg-type]
            line_end=int(parsed["line_end"]),  # type: ignore[arg-type]
            intended_operation=str(parsed["operation"]),
            target_procedure=parsed["procedure"] and str(parsed["procedure"]),
            target_symbol=parsed["symbol"] and str(parsed["symbol"]),
        )
        draft = repair_draft_mod.build_repair_draft(
            repair_draft_id=f"draft-{self._draft_counter}",
            repair_plan_digest=repair_planner.repair_plan_digest(self.last_repair_plan),
            source_identity=identity,
            edit_scope=scope,
            proposed_change_description=str(parsed["description"]),
            generated_at=str(self._clock()),
        )
        self.last_repair_draft = draft
        return self._render_repair_draft(draft)

    def _show_repair_draft(self, args: list[str]) -> list[str]:
        if self.last_repair_draft is None:
            return ["ERROR no_repair_draft: run 'repair-draft' first."]
        return self._render_repair_draft(self.last_repair_draft)

    def _render_draft_approval_record(self, record: "draft_approval.DraftApprovalRecord") -> list[str]:
        return [
            "REAL_WORKFLOW: Repair-draft approval recorded from the current repair draft only.",
            "DRAFT_APPROVAL_BOUNDARY: No code was modified. No file was written. No patch was applied. No "
            "execution occurred. Repair Application remains unavailable.",
            f"decision: {record.decision}",
            f"draft_digest: {record.draft_digest}",
            f"repair_draft_id: {record.repair_draft_id}",
            f"recorded_at: {record.recorded_at}",
            f"safe_to_apply: {str(record.safe_to_apply).lower()}",
            f"safe_to_prepare_draft: {str(record.safe_to_prepare_draft).lower()}",
            f"approval_boundary: {record.approval_boundary}",
        ]

    def _record_repair_draft_decision(
        self, args: list[str], *, decision: "draft_approval.DraftApprovalDecision", command_name: str
    ) -> list[str]:
        if self.last_repair_draft is None:
            return ["ERROR no_repair_draft: run 'repair-draft' first."]
        if not args:
            return [f"ERROR usage: {command_name} <draft_digest>"]
        supplied_digest = args[0]
        actual_digest = repair_draft_mod.repair_draft_digest(self.last_repair_draft)
        if supplied_digest != actual_digest:
            return [
                "ERROR stale_or_incorrect_digest: supplied draft_digest does not match the current repair draft.",
                f"current_draft_digest: {actual_digest}",
                "guidance: run 'repair-draft' or 'show-repair-draft' again to see the current digest, or "
                "re-supply the exact digest shown there.",
            ]
        try:
            if decision == draft_approval.DraftApprovalDecision.APPROVED:
                record = self._draft_approval_store.approve(self.last_repair_draft, recorded_at=str(self._clock()))
            else:
                record = self._draft_approval_store.decline(self.last_repair_draft, recorded_at=str(self._clock()))
        except draft_approval.DraftApprovalConflictError as exc:
            return [f"ERROR draft_approval_conflict: {exc}"]
        return self._render_draft_approval_record(record)

    def _approve_repair_draft(self, args: list[str]) -> list[str]:
        return self._record_repair_draft_decision(
            args, decision=draft_approval.DraftApprovalDecision.APPROVED, command_name="approve-repair-draft"
        )

    def _decline_repair_draft(self, args: list[str]) -> list[str]:
        return self._record_repair_draft_decision(
            args, decision=draft_approval.DraftApprovalDecision.DECLINED, command_name="decline-repair-draft"
        )

    def _show_repair_draft_approval(self, args: list[str]) -> list[str]:
        if self.last_repair_draft is None:
            return ["ERROR no_repair_draft: run 'repair-draft' first."]
        record = self._draft_approval_store.get_decision(self.last_repair_draft)
        if record is None:
            return ["ERROR no_draft_approval: run 'approve-repair-draft' or 'decline-repair-draft' first."]
        return self._render_draft_approval_record(record)

    def _render_application_approval_record(self, record: "application_approval.ApplicationApprovalRecord") -> list[str]:
        return [
            "REAL_WORKFLOW: Repair-application approval recorded from the current repair draft only.",
            "APPLICATION_APPROVAL_BOUNDARY: No code was modified. No file was written. No patch was applied. No "
            "execution occurred. The application transaction itself remains unimplemented.",
            f"decision: {record.decision}",
            f"draft_digest: {record.draft_digest}",
            f"repair_draft_id: {record.repair_draft_id}",
            f"recorded_at: {record.recorded_at}",
            f"safe_to_apply: {str(record.safe_to_apply).lower()}",
            f"safe_to_prepare_draft: {str(record.safe_to_prepare_draft).lower()}",
            f"approval_boundary: {record.approval_boundary}",
        ]

    def _record_repair_application_decision(
        self, args: list[str], *, decision: "application_approval.ApplicationApprovalDecision", command_name: str
    ) -> list[str]:
        if self.last_repair_draft is None:
            return ["ERROR no_repair_draft: run 'repair-draft' first."]
        if not args:
            return [f"ERROR usage: {command_name} <draft_digest>"]
        supplied_digest = args[0]
        actual_digest = repair_draft_mod.repair_draft_digest(self.last_repair_draft)
        if supplied_digest != actual_digest:
            return [
                "ERROR stale_or_incorrect_digest: supplied draft_digest does not match the current repair draft.",
                f"current_draft_digest: {actual_digest}",
                "guidance: run 'repair-draft' or 'show-repair-draft' again to see the current digest, or "
                "re-supply the exact digest shown there.",
            ]
        try:
            if decision == application_approval.ApplicationApprovalDecision.APPROVED:
                record = self._application_approval_store.approve(self.last_repair_draft, recorded_at=str(self._clock()))
            else:
                record = self._application_approval_store.decline(self.last_repair_draft, recorded_at=str(self._clock()))
        except application_approval.ApplicationApprovalConflictError as exc:
            return [f"ERROR application_approval_conflict: {exc}"]
        return self._render_application_approval_record(record)

    def _approve_repair_application(self, args: list[str]) -> list[str]:
        return self._record_repair_application_decision(
            args, decision=application_approval.ApplicationApprovalDecision.APPROVED, command_name="approve-repair-application"
        )

    def _decline_repair_application(self, args: list[str]) -> list[str]:
        return self._record_repair_application_decision(
            args, decision=application_approval.ApplicationApprovalDecision.DECLINED, command_name="decline-repair-application"
        )

    def _show_repair_application_approval(self, args: list[str]) -> list[str]:
        if self.last_repair_draft is None:
            return ["ERROR no_repair_draft: run 'repair-draft' first."]
        record = self._application_approval_store.get_decision(self.last_repair_draft)
        if record is None:
            return ["ERROR no_application_approval: run 'approve-repair-application' or 'decline-repair-application' first."]
        return self._render_application_approval_record(record)

    def _parse_gate_args(self, args: list[str]) -> dict[str, object] | str:
        """Parses the one optional gate flag. Returns a field dict on
        success, or an error message string on invalid input. Never reads a
        file -- a "current" content hash is only ever what the caller
        explicitly asserts, exactly like every other hash value in the
        repair-draft/approval layers."""
        current_content_hash: str | None = None
        i = 0
        while i < len(args):
            token = args[i]
            if token == "--current-content-hash" and i + 1 < len(args):
                current_content_hash = args[i + 1]
                i += 2
            else:
                return f"ERROR usage: unrecognized check-repair-application-gate option {token!r}"
        return {"current_content_hash": current_content_hash}

    def _check_repair_application_gate(self, args: list[str]) -> list[str]:
        if self.last_repair_plan is None:
            return ["ERROR no_repair_plan: run 'repair-plan' first."]
        if self.last_repair_draft is None:
            return ["ERROR no_repair_draft: run 'repair-draft' first."]
        parsed = self._parse_gate_args(args)
        if isinstance(parsed, str):
            return [parsed]
        current_content_hash = parsed["current_content_hash"]
        current_source_identity: "repair_draft_mod.SourceIdentity | None" = None
        if current_content_hash is not None:
            bound_identity = self.last_repair_draft.source_identity
            current_source_identity = repair_draft_mod.SourceIdentity(
                artifact=bound_identity.artifact,
                content_hash=current_content_hash,
                size=bound_identity.size,
                encoding=bound_identity.encoding,
                line_range=bound_identity.line_range,
                observed_at=str(self._clock()),
            )
        workspace_status: str | None = None
        if self.active_workspace_id is not None:
            workspace_status = self.registry.get_workspace(self.active_workspace_id).status.value
        strategy_record = self._repair_approval_store.get_decision(self.last_repair_plan)
        draft_record = self._draft_approval_store.get_decision(self.last_repair_draft)
        application_record = self._application_approval_store.get_decision(self.last_repair_draft)
        result = application_gate.evaluate_application_gate(
            repair_plan=self.last_repair_plan,
            repair_approval_record=strategy_record,
            repair_draft=self.last_repair_draft,
            draft_approval_record=draft_record,
            application_approval_record=application_record,
            current_source_identity=current_source_identity,
            workspace_status=workspace_status,
        )
        lines = [
            "REAL_WORKFLOW: Application-gate precondition re-verification only.",
            f"gate_boundary: {result.gate_boundary}",
            f"draft_digest: {result.draft_digest}",
            f"all_passed: {str(result.all_passed).lower()}",
        ]
        for c in result.checks:
            lines.append(f"  check[{c.check}]: {'pass' if c.passed else 'FAIL'} -- {c.detail}")
        if result.failed_checks:
            lines.append(f"failed_checks: {', '.join(result.failed_checks)}")
        lines.append(f"not_applicable_checks: {', '.join(result.not_applicable_checks)}")
        lines.append(
            "disclosure: A passing gate result does not authorize applying anything. No application "
            "transaction exists in this repository."
        )
        return lines

    def _parse_apply_repair_args(self, args: list[str]) -> "tuple[str, str] | str":
        """Parses `<draft_digest> --replacement-text TEXT`. Returns
        `(draft_digest, replacement_text)` on success, or an error message
        string on invalid input. The replacement text is never read from a
        file, generated, or inferred -- it must be supplied explicitly by
        the caller, exactly like every other content value in the
        repair-draft/approval layers."""
        if not args:
            return "ERROR usage: apply-repair <draft_digest> --replacement-text TEXT"
        draft_digest = args[0]
        remaining = args[1:]
        replacement_text: str | None = None
        i = 0
        while i < len(remaining):
            token = remaining[i]
            if token == "--replacement-text" and i + 1 < len(remaining):
                replacement_text = remaining[i + 1]
                i += 2
            else:
                return f"ERROR usage: unrecognized apply-repair option {token!r}"
        if replacement_text is None:
            return "ERROR usage: apply-repair <draft_digest> --replacement-text TEXT"
        return draft_digest, replacement_text

    def _render_application_result(self, result: "application_transaction.ApplicationResult") -> list[str]:
        lines = [
            "REAL_WORKFLOW: Repair application transaction executed against the real workspace filesystem.",
            f"application_boundary: {result.application_boundary}",
            f"application_id: {result.application_id}",
            f"draft_digest: {result.draft_digest}",
            f"workspace_id: {result.workspace_id}",
            f"relative_path: {result.relative_path}",
            f"outcome: {result.outcome}",
            f"reason: {result.reason}",
            f"pre_application_content_hash: {result.pre_application_content_hash}",
            f"post_application_content_hash: {result.post_application_content_hash}",
            f"applied_at: {result.applied_at}",
        ]
        if result.backup is not None:
            lines.extend(
                [
                    f"backup_relative_path: {result.backup.relative_path}",
                    f"backup_content_hash: {result.backup.content_hash}",
                    f"backup_size: {result.backup.size}",
                ]
            )
        else:
            lines.append("backup: none (blocked before any backup was created)")
        lines.append("checks:")
        for c in result.checks:
            lines.append(f"  - {c.check}: {'pass' if c.passed else 'FAIL'} -- {c.detail}")
        lines.extend(
            [
                f"file_modified: {str(result.outcome == 'applied').lower()}",
                f"backup_created: {str(result.backup is not None).lower()}",
                "rerun_performed: false",
                "next_step: a separate, explicit rerun confirmation (request/plan/confirm/execute) is required "
                "before executing the repaired code; this command never triggers one.",
            ]
        )
        return lines

    def _apply_repair(self, args: list[str]) -> list[str]:
        if self.last_repair_plan is None:
            return ["ERROR no_repair_plan: run 'repair-plan' first."]
        if self.last_repair_draft is None:
            return ["ERROR no_repair_draft: run 'repair-draft' first."]
        parsed = self._parse_apply_repair_args(args)
        if isinstance(parsed, str):
            return [parsed]
        supplied_digest, replacement_text = parsed
        actual_digest = repair_draft_mod.repair_draft_digest(self.last_repair_draft)
        if supplied_digest != actual_digest:
            return [
                "ERROR stale_or_incorrect_digest: supplied draft_digest does not match the current repair draft.",
                f"current_draft_digest: {actual_digest}",
                "guidance: run 'repair-draft' or 'show-repair-draft' again to see the current digest, or "
                "re-supply the exact digest shown there.",
            ]
        strategy_record = self._repair_approval_store.get_decision(self.last_repair_plan)
        draft_record = self._draft_approval_store.get_decision(self.last_repair_draft)
        application_record = self._application_approval_store.get_decision(self.last_repair_draft)
        result = application_transaction.apply_repair(
            repair_plan=self.last_repair_plan,
            repair_approval_record=strategy_record,
            repair_draft=self.last_repair_draft,
            draft_approval_record=draft_record,
            application_approval_record=application_record,
            replacement_text=replacement_text,
            workspace_registry=self.registry,
            clock=self._clock,
        )
        self.last_application_result = result
        return self._render_application_result(result)

    def _show_application_result(self, args: list[str]) -> list[str]:
        if self.last_application_result is None:
            return ["ERROR no_application_result: run 'apply-repair' first."]
        return self._render_application_result(self.last_application_result)

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
            f"execution_backend: {self.last_process_metadata.backend}",
            f"gauss_ran: {str(self.last_process_metadata.gauss_ran).lower()}",
            f"process_exit_code: {self.last_process_metadata.exit_code}",
            f"process_timed_out: {str(self.last_process_metadata.timed_out).lower()}",
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
            f"execution_backend: {self.backend_label}",
            f"fake_runner_default: {str(self.runner_backend == FAKE_BACKEND).lower()}",
            f"real_gauss_executable: {self.real_gauss_executable or 'none'}",
            f"gauss_ran: {str(self.last_process_metadata.gauss_ran).lower()}",
            f"last_exit_code: {self.last_process_metadata.exit_code}",
            f"last_timed_out: {str(self.last_process_metadata.timed_out).lower()}",
        ]

    def _reset(self) -> list[str]:
        self.mvp_session = None
        self.pending_request = None
        self.last_result = None
        self.last_process_metadata = ExecutionProcessMetadata(backend=self.backend_label)
        self.last_captured_output = CapturedProcessOutput()
        self.last_repair_plan = None
        self._repair_approval_store = repair_approval.RepairApprovalStore()
        self.last_repair_draft = None
        self._draft_approval_store = draft_approval.DraftApprovalStore()
        self._application_approval_store = application_approval.ApplicationApprovalStore()
        self.last_application_result = None
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
            if mode == "timeout":
                self.last_captured_output = CapturedProcessOutput(stdout="", stderr="")
                self.last_process_metadata = ExecutionProcessMetadata(
                    backend=self.backend_label,
                    executable_path=runner_input.executable_path,
                    gauss_ran=False,
                    executed=True,
                    execution_status="timed_out",
                    exit_code=None,
                    timed_out=True,
                    timeout_seconds=runner_input.timeout_seconds,
                    stdout_chars=0,
                    stderr_chars=0,
                )
                return {
                    "executed": True,
                    "execution_status": "timed_out",
                    "exit_code": None,
                    "stdout": "",
                    "stderr": "",
                    "output_files": [],
                    "warnings": ["fake runner result; GAUSS was not invoked"],
                    "errors": [],
                }
            if mode == "unknown_error":
                stdout_text = "Program execute failed\n"
                stderr_text = "error G9999 : Simulated uncataloged GAUSS error for benchmark 43.9\n"
                self.last_captured_output = CapturedProcessOutput(stdout=stdout_text, stderr=stderr_text)
                self.last_process_metadata = ExecutionProcessMetadata(
                    backend=self.backend_label,
                    executable_path=runner_input.executable_path,
                    gauss_ran=False,
                    executed=True,
                    execution_status="failed",
                    exit_code=0,
                    timed_out=False,
                    timeout_seconds=runner_input.timeout_seconds,
                    stdout_chars=len(stdout_text),
                    stderr_chars=len(stderr_text),
                )
                return {
                    "executed": True,
                    "execution_status": "failed",
                    "exit_code": 0,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "output_files": [],
                    "warnings": ["fake runner result; GAUSS was not invoked"],
                    "errors": ["error G9999 : Simulated uncataloged GAUSS error for benchmark 43.9"],
                }
            if mode == "failure":
                self.last_captured_output = CapturedProcessOutput(
                    stdout="Program execute failed\n",
                    stderr="error G0105 : Undefined symbol\n",
                )
                self.last_process_metadata = ExecutionProcessMetadata(
                    backend=self.backend_label,
                    executable_path=runner_input.executable_path,
                    gauss_ran=False,
                    executed=True,
                    execution_status="failed",
                    exit_code=0,
                    timed_out=False,
                    timeout_seconds=runner_input.timeout_seconds,
                    stdout_chars=len("Program execute failed\n"),
                    stderr_chars=len("error G0105 : Undefined symbol\n"),
                )
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
            self.last_captured_output = CapturedProcessOutput(stdout="fake runner completed\n", stderr="")
            self.last_process_metadata = ExecutionProcessMetadata(
                backend=self.backend_label,
                executable_path=runner_input.executable_path,
                gauss_ran=False,
                executed=True,
                execution_status="completed",
                exit_code=0,
                timed_out=False,
                timeout_seconds=runner_input.timeout_seconds,
                stdout_chars=len("fake runner completed\n"),
                stderr_chars=0,
            )
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

    # ------------------------------------------------------------------
    # opt-in real execution
    # ------------------------------------------------------------------

    def _load_real_helper(self) -> Any:
        if self._real_helper is not None:
            return self._real_helper
        import gauss_code_execution  # noqa: PLC0415

        self._real_helper = gauss_code_execution.execute_gauss_code
        return self._real_helper

    def _real_gauss_runner(self):
        def runner(runner_input: Any) -> dict[str, Any]:
            helper = self._load_real_helper()
            self.last_process_metadata = ExecutionProcessMetadata(
                backend=self.backend_label,
                executable_path=self.real_gauss_executable,
                gauss_ran=False,
                timeout_seconds=runner_input.timeout_seconds,
            )
            try:
                result = helper(
                    executable_path=self.real_gauss_executable,
                    gauss_version=self.gauss_version,
                    code=runner_input.code,
                    script_path=runner_input.script_path,
                    working_directory=runner_input.working_directory,
                    input_files=list(runner_input.expected_input_files),
                    output_directory=runner_input.output_directory,
                    timeout_seconds=runner_input.timeout_seconds,
                    allow_file_write=False,
                    allow_output_files=runner_input.allow_output_files,
                    allow_network=False,
                    strict=True,
                )
            except Exception as exc:  # noqa: BLE001
                self.last_process_metadata.error = str(exc)
                self.last_captured_output = CapturedProcessOutput()
                raise

            stdout_text = result.get("stdout") or ""
            stderr_text = result.get("stderr") or ""
            self.last_captured_output = CapturedProcessOutput(stdout=stdout_text, stderr=stderr_text)
            raw_details = result.get("raw_execution_details") or {}
            self.last_process_metadata = ExecutionProcessMetadata(
                backend=self.backend_label,
                executable_path=result.get("executable_path") or self.real_gauss_executable,
                gauss_ran=bool(result.get("executed")),
                executed=bool(result.get("executed")),
                execution_status=result.get("execution_status"),
                exit_code=result.get("exit_code"),
                timed_out=result.get("execution_status") == "timed_out",
                elapsed_seconds=result.get("elapsed_seconds"),
                timeout_seconds=result.get("timeout_seconds"),
                stdout_chars=len(stdout_text),
                stderr_chars=len(stderr_text),
                generated_script_path=raw_details.get("generated_script_path"),
                command_preview=result.get("command"),
            )
            return result

        return runner


def run_repl(adapter: InteractiveMvpAdapter) -> int:
    print("GAUSS Code Assistant Interactive MVP Adapter (v0.62.0 alpha)")
    print(f"Execution backend: {adapter.backend_label}")
    if adapter.runner_backend == REAL_GAUSS_BACKEND:
        print("Real GAUSS execution is enabled only after hash-bound confirm + execute.")
        print(f"GAUSS executable: {adapter.real_gauss_executable}")
    else:
        print("Type 'help' for commands. Default execution uses a deterministic fake runner; GAUSS is not run.")
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
            "Uses a deterministic fake runner by default; real GAUSS execution is opt-in."
        )
    )
    parser.add_argument(
        "--workspace-parent",
        default=None,
        help="Approved parent directory for alpha workspaces. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--runner",
        choices=[FAKE_BACKEND, REAL_GAUSS_BACKEND],
        default=FAKE_BACKEND,
        help="Execution backend. Default: fake. Use 'gauss' only for explicit local GAUSS alpha testing.",
    )
    parser.add_argument(
        "--gauss-executable",
        default=None,
        help="Path to terminal GAUSS executable (tgauss or tgauss.exe). Required for --runner gauss unless GAUSS_EXECUTABLE is set.",
    )
    parser.add_argument(
        "--gauss-version",
        default=None,
        help="Optional descriptive GAUSS version label recorded in the execution plan.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    try:
        adapter = InteractiveMvpAdapter(
            workspace_parent=args.workspace_parent,
            runner_backend=args.runner,
            gauss_executable=args.gauss_executable,
            gauss_version=args.gauss_version,
        )
    except ValueError as exc:
        print(f"ERROR runner_configuration: {exc}", file=sys.stderr)
        return 2
    return run_repl(adapter)


if __name__ == "__main__":
    raise SystemExit(main())
