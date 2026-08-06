"""Verification Execution workflow -- executes an already-applied repair's
resulting source through the existing, unmodified execution pipeline.

Position in the reasoning pipeline:

    ... -> Repair Application Transaction (gauss_repair_application.py, v0.62.0)
        -> Verification Execution (this module, v0.64.0)
        -> (Separate rerun approval / ordinary execution confirmation --
            already exists, unmodified: request/plan/confirm/execute)

**Repair knows nothing about execution. Execution knows nothing about
repair. Verification is only an adapter between them.** This is the ONLY
module in this repository that imports both `gauss_repair_application` and
`gauss_execution_workflow` -- and it does so only to translate an already-
successful `ApplicationResult` into inputs for the existing, completely
unmodified `ExecutionWorkflow`. It contains no execution logic of its own
(no runner, no invocation, no confirmation logic, no repair-specific
proposal/confirmation/session type) and no repair logic of its own (no
draft, no approval, no transaction).

This is not automatic repair validation, automatic repair acceptance,
autonomous retry, autonomous repair, or autonomous planning. It simply:

1. builds an immutable `VerificationExecutionRequest` from an already-
   successful `ApplicationResult` (never from a `RepairDraft` directly --
   structurally, there is no field anywhere in this module capable of
   holding one);
2. re-reads the repaired file (through the existing, reused
   `ExecutionWorkflow.read_workspace_file(...)`) and confirms its current
   hash still matches what the application transaction actually wrote --
   fails closed, never proceeds against stale content;
3. calls `ExecutionWorkflow.propose_execution(...)` -- the exact same
   method, with the exact same return type (`ProposalOutcome`), any
   ordinary execution proposal already uses;
4. leaves confirmation and execution entirely to the caller, via the
   existing, unmodified `ExecutionWorkflow.confirm_execution(...)`/
   `execute(...)` (or the MVP facade's own `confirm(...)`/`execute(...)`);
5. once both interpretations exist, compares them with a pure,
   evidence-only function that reports what happened -- never whether the
   repair is "correct," never a success probability, never a statistical
   claim.

Never implements: automatic retries, automatic repair acceptance, automatic
rollback, automatic planning, automatic code editing, repair scoring, LLM
repair loops, repair ranking, or autonomous execution.
"""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass
from typing import Callable

import gauss_execution_interpreter as interpreter_mod
import gauss_execution_workflow as wf
import gauss_repair_application as application_mod
import gauss_workspace_file_reader as file_reader_mod


class RepairNotAppliedError(Exception):
    """Raised by `build_verification_execution_request(...)` when the
    supplied `ApplicationResult.outcome` is not `"applied"` -- there is
    nothing to verify for a blocked or failed transaction."""


@dataclass(frozen=True)
class VerificationExecutionRequest:
    """Immutable. References only an already-successful `ApplicationResult`
    -- never a `RepairDraft` directly; structurally, there is no field here
    capable of holding one."""

    verification_execution_id: str
    #: Deliberately equal to `application_result_id` below -- this
    #: repository has no separate, independently-identified
    #: "RepairApplication" record distinct from the transaction's own
    #: `ApplicationResult`; both suggested field names are kept, pointing
    #: at the one real identifier that exists, rather than inventing a
    #: second, redundant ID.
    repair_application_id: str
    application_result_id: str
    workspace_id: str
    relative_path: str
    expected_post_repair_hash: str
    reason: str
    created_at: str


def build_verification_execution_request(
    application_result: "application_mod.ApplicationResult",
    *,
    reason: str,
    clock: Callable[[], float] = time.time,
    id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
) -> VerificationExecutionRequest:
    """The single sanctioned constructor. Raises `RepairNotAppliedError` if
    `application_result.outcome != "applied"`. Every field is read directly
    off `application_result` -- this function never accepts, inspects, or
    references a `RepairDraft` object at all."""
    if application_result.outcome != "applied":
        raise RepairNotAppliedError(
            f"application_result.outcome is {application_result.outcome!r}, not 'applied'; "
            "there is nothing to verify for a blocked or failed repair application."
        )
    if application_result.post_application_content_hash is None:
        raise RepairNotAppliedError(
            "application_result.post_application_content_hash is None; an applied result must carry one."
        )
    return VerificationExecutionRequest(
        verification_execution_id=id_factory(),
        repair_application_id=application_result.application_id,
        application_result_id=application_result.application_id,
        workspace_id=application_result.workspace_id,
        relative_path=application_result.relative_path,
        expected_post_repair_hash=application_result.post_application_content_hash,
        reason=reason,
        created_at=str(clock()),
    )


@dataclass(frozen=True)
class VerificationProposalResult:
    """Wraps the ordinary `wf.ProposalOutcome` this module's own
    `propose_verification_execution(...)` produces, plus two flags
    describing why a pre-proposal block occurred, if one did. Never a
    repair-specific proposal type -- `outcome.proposal`, when not blocked,
    is a genuine `wf.ExecutionProposal`, identical in type and construction
    to any ordinary execution's own proposal."""

    request: VerificationExecutionRequest
    outcome: "wf.ProposalOutcome"
    source_read_ok: bool
    source_hash_matches: bool


#: Fixed, always-present disclosures -- reused verbatim by every caller
#: (the CLI included) rather than re-worded per call site.
VERIFICATION_DISCLOSURE: tuple[str, ...] = (
    "This is an ordinary execution. It follows the standard execution workflow.",
    "The repaired file is simply the execution target.",
    "Repair success is NOT inferred from this proposal.",
    "Verification evidence will be collected once execution completes.",
)


def _verification_safety_input() -> "wf.SafetyReviewInput":
    """The repaired code has already passed every repair-layer safety gate
    (draft validation, application-gate re-verification, a bounded,
    single-file transaction); this reuses the same fixed, all-True
    declaration the interactive CLI already supplies for an ordinary,
    interactively-confirmed execution -- no new safety criteria are
    introduced or relaxed."""
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


def propose_verification_execution(
    request: VerificationExecutionRequest,
    *,
    execution_workflow: "wf.ExecutionWorkflow",
    workspace_root_path: str,
    session_id: str,
    request_id: str,
    executable_path: str,
    gauss_version: str | None = None,
    timeout_seconds: float = 30.0,
) -> VerificationProposalResult:
    """Reads the repaired file through the existing, reused
    `execution_workflow.read_workspace_file(...)`, confirms its hash still
    matches `request.expected_post_repair_hash`, and -- only if fresh --
    calls `execution_workflow.propose_execution(...)`, the exact same
    method any ordinary execution proposal already uses.

    `workspace_id` is deliberately never passed to that call: the workspace
    containing the repaired file already completed its one-shot lifecycle
    during the *original* failing execution, and `propose_execution`'s own
    existing workspace-completed check would unconditionally block a second
    workspace-bound proposal against it (v0.52.0's own, unmodified
    guarantee). The real repaired file is still executed, at its own real
    location, via `working_directory=workspace_root_path` -- an
    already-supported, pre-v0.43.0 code path (workspace-unaware execution),
    not a new capability. See `planning/v0.64.0-verification-execution-
    workflow.md` for the full reasoning."""
    read_result = execution_workflow.read_workspace_file(
        file_reader_mod.WorkspaceFileReadRequest(
            workspace_id=request.workspace_id, relative_path=request.relative_path
        )
    )
    if read_result.status != file_reader_mod.ReadStatus.COMPLETED.value:
        return VerificationProposalResult(
            request=request,
            outcome=wf.ProposalOutcome(
                orchestration_instance_id="",
                blocked=True,
                failure_category="verification_source_unreadable",
                failure_reason=f"{read_result.error_code}: {read_result.error_message}",
                proposal=None,
            ),
            source_read_ok=False,
            source_hash_matches=False,
        )

    hash_matches = read_result.checksum == request.expected_post_repair_hash
    if not hash_matches:
        return VerificationProposalResult(
            request=request,
            outcome=wf.ProposalOutcome(
                orchestration_instance_id="",
                blocked=True,
                failure_category="verification_source_stale",
                failure_reason=(
                    f"the repaired file's current content hash ({read_result.checksum}) no longer matches "
                    f"the hash recorded at application time ({request.expected_post_repair_hash}) -- the "
                    "file changed again after the repair was applied."
                ),
                proposal=None,
            ),
            source_read_ok=True,
            source_hash_matches=False,
        )

    outcome = execution_workflow.propose_execution(
        session_id=session_id,
        request_id=request_id,
        execution_purpose=f"Verification execution for repair application {request.repair_application_id}",
        eligibility_declarations=wf.EligibilityDeclarations(execution_explicitly_requested=True),
        safety_input=_verification_safety_input(),
        code=read_result.content,
        working_directory=workspace_root_path,
        executable_path=executable_path,
        gauss_version=gauss_version,
        timeout_seconds=timeout_seconds,
    )
    return VerificationProposalResult(request=request, outcome=outcome, source_read_ok=True, source_hash_matches=True)


# ---------------------------------------------------------------------------
# Post-execution comparison -- pure, evidence-only, no verdicts
# ---------------------------------------------------------------------------


class ComparisonOutcome(enum.Enum):
    SUCCEEDED_AFTER_FAILURE = "succeeded_after_failure"
    DIFFERENT_ERROR = "different_error"
    SAME_ERROR = "same_error"
    FAILED_AFTER_SUCCESS = "failed_after_success"
    BOTH_SUCCEEDED = "both_succeeded"


@dataclass(frozen=True)
class ComparisonSummary:
    """Evidence only. No `repair_correct`, `success_probability`, or
    `confidence_score` field exists anywhere on this type -- structurally,
    not merely by convention."""

    original_outcome: str
    verification_outcome: str
    same_outcome: bool
    comparison: str  # ComparisonOutcome value
    observation: str


def _outcome_label(interp: "interpreter_mod.ExecutionInterpretation") -> str:
    if interp.completion_status == "completed":
        return "Execution successful"
    if interp.error_code:
        return f"Runtime error {interp.error_code}"
    if interp.execution_phase == "timeout":
        return "Execution timed out"
    return f"Execution failed ({interp.failure_type or 'unknown'})"


def compare_execution_outcomes(
    original: "interpreter_mod.ExecutionInterpretation", verification: "interpreter_mod.ExecutionInterpretation"
) -> ComparisonSummary:
    """Pure. No I/O, no re-execution, no re-interpretation of raw evidence
    -- consumes two already-computed `ExecutionInterpretation` objects and
    reuses their own classification rather than re-deriving it. Reports
    only what happened; never concludes a repair is correct, assigns a
    success probability, or infers statistical correctness."""
    original_label = _outcome_label(original)
    verification_label = _outcome_label(verification)
    original_ok = original.completion_status == "completed"
    verification_ok = verification.completion_status == "completed"

    if not original_ok and verification_ok:
        comparison = ComparisonOutcome.SUCCEEDED_AFTER_FAILURE
        observation = (
            "The repaired code executed successfully whereas the original execution failed with "
            f"{original.error_code or original.failure_type or 'an error'}."
        )
    elif not original_ok and not verification_ok:
        if original.error_code is not None and original.error_code == verification.error_code:
            comparison = ComparisonOutcome.SAME_ERROR
            observation = "The repair did not change the observed execution outcome."
        else:
            comparison = ComparisonOutcome.DIFFERENT_ERROR
            observation = "The repair changed execution behavior, but a different runtime error occurred."
    elif original_ok and not verification_ok:
        comparison = ComparisonOutcome.FAILED_AFTER_SUCCESS
        observation = (
            f"The verification execution failed with {verification.error_code or verification.failure_type or 'an error'} "
            "even though the original execution succeeded."
        )
    else:
        comparison = ComparisonOutcome.BOTH_SUCCEEDED
        observation = "Both the original and verification executions completed successfully."

    same_outcome = original_ok == verification_ok and original.error_code == verification.error_code
    return ComparisonSummary(
        original_outcome=original_label,
        verification_outcome=verification_label,
        same_outcome=same_outcome,
        comparison=comparison.value,
        observation=observation,
    )
