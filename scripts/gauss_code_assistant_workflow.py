"""GAUSS Code Assistant MVP workflow facade (v0.45.0 GAUSS Code Assistant
MVP Workflow).

Authoritative design source: `planning/v0.45.0-code-assistant-mvp.md`. This
module implements that plan's user journey, workflow-result model, and
user-experience templates -- it does not redefine them.

**This module orchestrates; it does not reimplement.** Every guarantee this
facade relies on -- eligibility/safety review, confirmation binding,
durable authorization, workspace containment, output provenance, explicit-
only file reading -- is enforced exactly where `v0.31.0`-`v0.44.0` already
put it: `gauss_execution_workflow.ExecutionWorkflow` and
`gauss_workspace.WorkspaceRegistry`. This module adds no new eligibility
rule, no new confirmation check, no new path-containment check, and no new
file-reading capability. Its own `MvpWorkflowSession.stage` tracking is a
reporting convenience, never a second, independent enforcement layer.

**Dependency direction.** This module depends on `gauss_execution_workflow`
and (transitively, for type references only) `gauss_workspace`/`gauss_
workspace_file_reader`. Nothing in this module imports `gauss_runtime_
orchestration`, `gauss_orchestration_state_store`, `gauss_execution_
adapter`, or `gauss_code_execution` directly -- it reaches them only
through `ExecutionWorkflow`'s own already-verified boundary. This module
never launches a subprocess and never touches GAUSS.

**Explicit non-goals, restated:** uploads, persistent storage, cloud
execution, multi-user support, binary file readers, PDF/image parsing,
autonomous execution, autonomous file reading, execution helper changes.
`read_file(...)` is only ever called explicitly by this facade's own
caller -- never invoked automatically by `execute(...)` or
`compose_response(...)`.
"""

from __future__ import annotations

import enum
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# gauss_execution_workflow has no import-time execution side effect (see its
# own module docstring); importing it here has none either.
import gauss_execution_workflow as wf  # noqa: E402
import gauss_workspace as workspace_mod  # noqa: E402
import gauss_workspace_file_reader as file_reader_mod  # noqa: E402


# ---------------------------------------------------------------------------
# Session stage tracking (reporting only -- see module docstring)
# ---------------------------------------------------------------------------


class CodeAssistantStage(enum.Enum):
    REQUEST_RECEIVED = "request_received"
    PLAN_PROPOSED = "plan_proposed"
    CONFIRMED = "confirmed"
    EXECUTED = "executed"
    RESPONDED = "responded"
    DECLINED = "declined"  # terminal: blocked proposal, rejected confirmation, or advisory-only


class MvpWorkflowStageError(Exception):
    """Raised when a facade method is called from a session stage that
    does not permit it. This is a reporting/sequencing guard local to this
    facade -- it never substitutes for the controller's or workspace
    registry's own real guards, which remain fully independent and are
    still separately enforced underneath."""


@dataclass
class MvpWorkflowSession:
    """Tracks one user journey through this facade. Mutated in place by
    each stage method; never itself durable (mirrors `ExecutionWorkflow`'s
    own process-local, in-memory-only convention)."""

    orchestration_instance_id: str | None = None
    workspace_id: str | None = None
    stage: CodeAssistantStage = CodeAssistantStage.REQUEST_RECEIVED
    intent_mode: "wf.InteractionMode | None" = None
    request_summary: str = ""
    proposal_outcome: "wf.ProposalOutcome | None" = None
    confirmation_outcome: "wf.ConfirmationOutcome | None" = None
    execution_result: "wf.ResponseReadyResult | None" = None
    file_reads: list["file_reader_mod.WorkspaceFileReadResult"] = field(default_factory=list)
    decline_reason: str | None = None


# ---------------------------------------------------------------------------
# Workflow result (Task 4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WorkflowResult:
    request_summary: str
    workspace_id: str | None
    execution_status: str | None
    execution_session_reference: str | None
    files_produced: tuple["wf.OutputFileSummary", ...]
    files_read: tuple["file_reader_mod.WorkspaceFileReadResult", ...]
    provenance: "wf.WorkspaceProvenance | None"
    analysis_status: str
    user_facing_summary: str


# ---------------------------------------------------------------------------
# User-experience summary templates (Task 5)
# ---------------------------------------------------------------------------

_METHODOLOGY_REMINDER = (
    "This does not prove code correctness or methodological/statistical validity."
)


def _summarize_advisory(mode: "wf.InteractionMode", note: str) -> str:
    labels = {
        wf.InteractionMode.ADVISORY: "This was an advisory response.",
        wf.InteractionMode.EXPLAIN_CODE: "This was an explanation of the code.",
        wf.InteractionMode.REVIEW_CODE: "This was a code review.",
        wf.InteractionMode.REVISE_CODE: "This was a code revision.",
    }
    label = labels.get(mode, "This was an advisory response.")
    return f"{label} No code was run. {note}".strip()


def _summarize_blocked(reason: str | None) -> str:
    reason_text = reason or "eligibility or safety review did not pass"
    return (
        f"This request was declined before any code ran: {reason_text}. "
        "No execution occurred. Provide a revised request to try again."
    )


def _summarize_rejected_confirmation() -> str:
    return "The proposed execution plan was not confirmed, so nothing was run."


def _summarize_execution(result: "wf.ResponseReadyResult") -> str:
    if not result.executed:
        return (
            f"Execution did not complete (final state: {result.final_orchestration_state}). "
            f"{_METHODOLOGY_REMINDER}"
        )
    if result.runtime_error_detected:
        return (
            "The code ran, but GAUSS reported a runtime error. "
            "See the captured evidence for diagnosis; a fix requires a brand-new proposal and confirmation. "
            f"{_METHODOLOGY_REMINDER}"
        )
    if result.timed_out:
        return "The code ran but exceeded its timeout. " + _METHODOLOGY_REMINDER
    if result.missing_expected_output:
        return (
            "The code ran and completed, but a declared expected output file was not found. "
            f"{_METHODOLOGY_REMINDER}"
        )
    return "The code ran and completed. " + _METHODOLOGY_REMINDER


def _summarize_file_read(result: "file_reader_mod.WorkspaceFileReadResult") -> str:
    if result.status != file_reader_mod.ReadStatus.COMPLETED.value:
        return f"The requested file could not be read ({result.error_code}): {result.error_message}"
    truncation_note = " Note: this content was truncated and is not the complete file." if result.truncated else ""
    return (
        f"Read {result.size_bytes} bytes from {result.relative_path!r}.{truncation_note} "
        f"This is file-content evidence only -- {_METHODOLOGY_REMINDER}"
    )


# ---------------------------------------------------------------------------
# The facade
# ---------------------------------------------------------------------------


class GaussCodeAssistantWorkflow:
    """Coordinates `ExecutionWorkflow` and `WorkspaceRegistry` into one
    MVP user journey. Owns no execution, workspace, or file-reading logic
    of its own -- every method below delegates to an existing module's
    already-verified entry point."""

    def __init__(
        self,
        *,
        execution_workflow: "wf.ExecutionWorkflow",
        workspace_registry: "workspace_mod.WorkspaceRegistry | None" = None,
    ) -> None:
        self._execution_workflow = execution_workflow
        self._workspace_registry = workspace_registry

    # -- stage 2: intent classification --------------------------------------

    @staticmethod
    def classify_intent(signal: "wf.IntentSignal") -> "wf.InteractionMode":
        """A direct pass-through to `gauss_execution_workflow.classify_
        interaction_mode(...)` -- this facade adds no second classifier."""
        return wf.classify_interaction_mode(signal)

    # -- stage 3: workspace selection -----------------------------------------

    def select_workspace(self, workspace_id: str) -> "workspace_mod.WorkspaceValidationOutcome":
        """Validates (never creates) a workspace. A workspace must already
        exist via `WorkspaceRegistry.create_workspace(...)`, performed
        outside this facade's own responsibility."""
        if self._workspace_registry is None:
            raise ValueError("select_workspace(...) requires a workspace_registry to be configured.")
        return self._workspace_registry.validate_workspace(workspace_id)

    # -- advisory (non-execution) path ------------------------------------------

    def advisory_response(
        self, *, request_summary: str, mode: "wf.InteractionMode", note: str = ""
    ) -> WorkflowResult:
        """For EXPLAIN_CODE/REVIEW_CODE/REVISE_CODE/ADVISORY intents --
        never touches the execution stack at all."""
        return WorkflowResult(
            request_summary=request_summary,
            workspace_id=None,
            execution_status=None,
            execution_session_reference=None,
            files_produced=(),
            files_read=(),
            provenance=None,
            analysis_status="not_started",
            user_facing_summary=_summarize_advisory(mode, note),
        )

    # -- stages 4-5: planning and confirmation -----------------------------------

    def propose(
        self,
        session: MvpWorkflowSession,
        *,
        request_summary: str,
        **propose_execution_kwargs: Any,
    ) -> "wf.ProposalOutcome":
        if session.stage != CodeAssistantStage.REQUEST_RECEIVED:
            raise MvpWorkflowStageError(f"propose(...) is only valid from REQUEST_RECEIVED, not {session.stage.value!r}.")
        session.request_summary = request_summary
        outcome = self._execution_workflow.propose_execution(**propose_execution_kwargs)
        session.orchestration_instance_id = outcome.orchestration_instance_id
        session.workspace_id = propose_execution_kwargs.get("workspace_id")
        session.proposal_outcome = outcome
        if outcome.blocked:
            session.stage = CodeAssistantStage.DECLINED
            session.decline_reason = outcome.failure_reason
        else:
            session.stage = CodeAssistantStage.PLAN_PROPOSED
        return outcome

    def confirm(self, session: MvpWorkflowSession, event: "wf.WorkflowConfirmationEvent") -> "wf.ConfirmationOutcome":
        if session.stage != CodeAssistantStage.PLAN_PROPOSED:
            raise MvpWorkflowStageError(f"confirm(...) is only valid from PLAN_PROPOSED, not {session.stage.value!r}.")
        outcome = self._execution_workflow.confirm_execution(event)
        session.confirmation_outcome = outcome
        if outcome.accepted:
            session.stage = CodeAssistantStage.CONFIRMED
        else:
            session.stage = CodeAssistantStage.DECLINED
            session.decline_reason = "confirmation rejected"
        return outcome

    # -- stages 6-7: execution + (automatic) output registration -----------------

    def execute(self, session: MvpWorkflowSession, *, runner: "wf.orchestration_mod.FakeRunner") -> "wf.ResponseReadyResult":
        if session.stage != CodeAssistantStage.CONFIRMED:
            raise MvpWorkflowStageError(f"execute(...) is only valid from CONFIRMED, not {session.stage.value!r}.")
        assert session.orchestration_instance_id is not None
        result = self._execution_workflow.execute(session.orchestration_instance_id, runner=runner)
        session.execution_result = result
        session.stage = CodeAssistantStage.EXECUTED
        return result

    # -- stage 8: optional, explicit-only file reading ----------------------------

    def read_file(
        self, session: MvpWorkflowSession, request: "file_reader_mod.WorkspaceFileReadRequest"
    ) -> "file_reader_mod.WorkspaceFileReadResult":
        """Always explicit -- never called by `execute(...)` or `compose_
        response(...)`. Requires `request.workspace_id` to match this
        session's own workspace, so a session can never read a different
        workspace's files through this facade."""
        if session.workspace_id is not None and request.workspace_id != session.workspace_id:
            raise ValueError(
                f"file-read request targets workspace {request.workspace_id!r}, but this session is "
                f"bound to workspace {session.workspace_id!r}."
            )
        result = self._execution_workflow.read_workspace_file(request)
        session.file_reads.append(result)
        return result

    # -- stages 9-10: analysis + final response ------------------------------

    def compose_response(self, session: MvpWorkflowSession) -> WorkflowResult:
        """Assembles the final `WorkflowResult`. Reachable from any stage
        -- a declined, executed, or still-mid-flow session all produce a
        structured, honest result, never a raw exception surfaced to the
        user."""
        result = session.execution_result

        if session.stage == CodeAssistantStage.DECLINED:
            if session.confirmation_outcome is not None and not session.confirmation_outcome.accepted:
                summary = _summarize_rejected_confirmation()
            else:
                summary = _summarize_blocked(session.decline_reason)
        elif result is not None:
            summary = _summarize_execution(result)
            if session.file_reads:
                summary += " " + " ".join(_summarize_file_read(r) for r in session.file_reads)
        else:
            summary = "No execution has occurred yet for this request."

        session.stage = CodeAssistantStage.RESPONDED if session.stage != CodeAssistantStage.DECLINED else session.stage

        return WorkflowResult(
            request_summary=session.request_summary,
            workspace_id=session.workspace_id,
            execution_status=(result.execution_status if result is not None else None),
            execution_session_reference=session.orchestration_instance_id,
            files_produced=(result.output_files if result is not None else ()),
            files_read=tuple(session.file_reads),
            provenance=(result.workspace_provenance if result is not None else None),
            analysis_status=(result.analysis_status if result is not None else "not_started"),
            user_facing_summary=summary,
        )


# ---------------------------------------------------------------------------
# Self-test harness (this repository's established convention -- no pytest
# is configured anywhere in this repository)
# ---------------------------------------------------------------------------


def _run_self_tests() -> int:
    """A lightweight built-in smoke test. The focused, comprehensive test
    suite lives in scripts/test_code_assistant_mvp_workflow.py. Never
    invokes GAUSS."""
    import tempfile

    import gauss_orchestration_state_store as store_mod
    import gauss_runtime_orchestration as orch

    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    def fake_runner(_: Any) -> dict[str, Any]:
        return {
            "executed": True, "execution_status": "completed", "exit_code": 0, "stdout": "4", "stderr": "",
            "output_files": [], "warnings": [], "errors": [],
        }

    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        registry = workspace_mod.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        store = store_mod.OrchestrationStateStore(Path(db_tmp) / "test.db")
        store.initialize()
        execution_workflow = wf.ExecutionWorkflow(state_store=store, workspace_registry=registry)
        facade = GaussCodeAssistantWorkflow(execution_workflow=execution_workflow, workspace_registry=registry)

        workspace = registry.create_workspace()
        Path(workspace.root_path).mkdir(parents=True, exist_ok=True)
        registry.update_workspace_status(workspace.workspace_id, to_status=workspace_mod.WorkspaceStatus.POPULATED)
        registry.update_workspace_status(workspace.workspace_id, to_status=workspace_mod.WorkspaceStatus.READY)

        advisory = facade.advisory_response(
            request_summary="explain this code", mode=wf.InteractionMode.EXPLAIN_CODE
        )
        check("advisory response never touches execution", advisory.execution_status is None)

        session = MvpWorkflowSession()
        safety = wf.SafetyReviewInput(
            code_shown_or_summarized=True, purpose_understood=True, does_not_delete_files=True,
            does_not_overwrite_unrelated_files=True, does_not_install_packages=True, does_not_activate_licenses=True,
            does_not_access_network=True, does_not_mutate_global_configuration=True,
            file_writes_relative_or_within_allowed_directory=True, working_directory_exists_and_safe=True,
            output_directory_within_allowed_scope=True, executable_is_terminal_gauss=True, timeout_is_set=True,
        )
        outcome = facade.propose(
            session, request_summary="run x = 2 + 2;", session_id="s1", request_id="r1",
            execution_purpose="self-test", eligibility_declarations=wf.EligibilityDeclarations(execution_explicitly_requested=True),
            safety_input=safety, code="x = 2 + 2;\nprint x;", executable_path="C:/example/gauss26/tgauss.exe",
            gauss_version="GAUSS 26", timeout_seconds=30.0, workspace_id=workspace.workspace_id,
        )
        check("proposal not blocked", not outcome.blocked)
        check("session reaches PLAN_PROPOSED", session.stage == CodeAssistantStage.PLAN_PROPOSED)

        assert outcome.proposal is not None
        facade.confirm(
            session,
            wf.WorkflowConfirmationEvent(
                session_id="s1", orchestration_instance_id=session.orchestration_instance_id, request_id="r1",
                request_hash=outcome.proposal.request_hash, decision="accepted", timestamp="t1",
                source_interaction_id="turn-1", plan_digest=outcome.proposal.plan_digest,
            ),
        )
        check("session reaches CONFIRMED", session.stage == CodeAssistantStage.CONFIRMED)

        facade.execute(session, runner=fake_runner)
        check("session reaches EXECUTED", session.stage == CodeAssistantStage.EXECUTED)

        final = facade.compose_response(session)
        check("final result reports executed status", final.execution_status == "completed")
        check("session reaches RESPONDED", session.stage == CodeAssistantStage.RESPONDED)

        try:
            facade.execute(session, runner=fake_runner)
            failures.append("calling execute() twice from RESPONDED should have raised MvpWorkflowStageError")
        except MvpWorkflowStageError:
            pass

        store.close()

    if failures:
        print(f"SELF-TEST FAILED ({len(failures)} issue(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SELF-TEST PASSED: all checks succeeded.")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "GAUSS Code Assistant MVP workflow facade (v0.45.0). Orchestrates existing "
            "execution/workspace/file-reader modules; implements no new execution, workspace, "
            "or file-reading logic of its own. Never invokes GAUSS."
        )
    )
    parser.add_argument("--self-test", action="store_true", help="Run a lightweight built-in smoke test and exit.")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if args.self_test:
        return _run_self_tests()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
