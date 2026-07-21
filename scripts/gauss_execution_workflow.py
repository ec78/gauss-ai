"""Conversational execution-workflow layer (v0.37.0 Conversational Execution
Workflow Integration).

Authoritative design source: `planning/v0.37.0-conversational-execution-
workflow-integration.md`. This module implements that plan's interaction
modes, intent-classification contract, eligibility/safety representation,
plan/confirmation contracts, durable-state relationship, and response
composition boundary -- it does not redefine them.

This module is the ONLY layer permitted to sit between a conversational
interaction and `scripts/gauss_runtime_orchestration.py`'s durable
controller. It enforces the required dependency direction:

    user-facing execution interaction
    -> execution-intent and mode decision (classify_interaction_mode)
    -> execution-plan builder (ExecutionWorkflow.propose_execution)
    -> canonical request (gauss_runtime_orchestration.build_canonical_request,
       invoked internally by the controller's own submit_for_review())
    -> durable orchestration controller (gauss_runtime_orchestration
       .MockOrchestrationInstance, built via build_durable_orchestration_
       instance -- always durable, never the bare in-memory constructor)
    -> Helper Adapter (gauss_execution_adapter, reached only through the
       controller's own invoke(runner) boundary)
    -> GAUSS execution helper (scripts/gauss_code_execution.py, reached only
       through gauss_execution_adapter.load_real_helper(), never imported or
       called by this module)

This module never imports `gauss_execution_adapter` or
`gauss_code_execution` directly, never launches a subprocess, and never
detects a real GAUSS environment. Every execution this module can drive
still passes through `MockOrchestrationInstance.invoke(runner)` -- the
`runner` is supplied by this module's OWN caller (in every test in this
module's default suite, a fake; in a bounded, separately authorized
real-verification harness, `gauss_runtime_orchestration
.build_production_adapter_runner(...)`, called by that harness, never by
this module).

Intent classification never parses natural language. `IntentSignal` accepts
only explicit, pre-classified booleans/enums -- the conversational agent is
expected to have already turned the user's words into these structured
facts, and this module independently re-derives the interaction mode from
them rather than trusting an agent-supplied mode hint at face value. Code
presence alone never authorizes execution; only the explicit
`execution_explicitly_requested=True` flag together with `code_present=True`
reaches `PREPARE_EXECUTION_PLAN`, and only a fully independently validated
`WorkflowConfirmationEvent` (bound to `request_hash` via `plan_digest`) can
ever reach `EXECUTE_AFTER_CONFIRMATION`.
"""

from __future__ import annotations

import argparse
import enum
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, NoReturn

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# Neither import below has any execution side effect: gauss_runtime_
# orchestration never imports the real helper at its own import time (only
# build_production_adapter_runner's explicit call does), and
# gauss_orchestration_state_store never imports GAUSS-adjacent code at all.
import gauss_runtime_orchestration as orchestration_mod  # noqa: E402
import gauss_orchestration_state_store as state_store_mod  # noqa: E402


# ---------------------------------------------------------------------------
# Interaction mode and intent classification
# ---------------------------------------------------------------------------


class InteractionMode(enum.Enum):
    ADVISORY = "advisory"
    EXPLAIN_CODE = "explain_code"
    REVIEW_CODE = "review_code"
    REVISE_CODE = "revise_code"
    PREPARE_EXECUTION_PLAN = "prepare_execution_plan"
    EXECUTE_AFTER_CONFIRMATION = "execute_after_confirmation"
    CANCEL_PENDING_EXECUTION = "cancel_pending_execution"
    INSPECT_PRIOR_RESULT = "inspect_prior_execution_result"
    REQUEST_RERUN = "request_rerun"


#: Modes that never execute regardless of any other signal -- passed through
#: from an agent-supplied hint only when no execution/cancel/inspect/rerun
#: signal is present (see classify_interaction_mode's precedence order).
_NON_EXECUTING_HINTS = frozenset(
    {InteractionMode.REVIEW_CODE, InteractionMode.EXPLAIN_CODE, InteractionMode.REVISE_CODE}
)


@dataclass(frozen=True)
class IntentSignal:
    """A structured, already-classified signal -- never raw natural-language
    text. The conversational agent supplies these explicit facts; this
    module independently re-derives the interaction mode from them rather
    than trusting `requested_mode_hint` alone."""

    requested_mode_hint: InteractionMode | None = None
    execution_explicitly_requested: bool = False
    code_present: bool = False
    confirmation_event_present: bool = False
    cancellation_requested: bool = False
    rerun_requested: bool = False
    inspect_instance_id: str | None = None


def classify_interaction_mode(signal: IntentSignal) -> InteractionMode:
    """Fails closed to ADVISORY for anything not unambiguous. See
    planning/v0.37.0-conversational-execution-workflow-integration.md's
    Intent-Classification Contract for the precedence rationale."""
    if signal.cancellation_requested:
        return InteractionMode.CANCEL_PENDING_EXECUTION
    if signal.rerun_requested:
        return InteractionMode.REQUEST_RERUN
    if signal.inspect_instance_id is not None:
        return InteractionMode.INSPECT_PRIOR_RESULT
    if signal.confirmation_event_present:
        # Classification alone never authorizes anything -- confirm_execution(...)
        # independently re-validates the full WorkflowConfirmationEvent.
        return InteractionMode.EXECUTE_AFTER_CONFIRMATION
    if signal.execution_explicitly_requested and signal.code_present:
        return InteractionMode.PREPARE_EXECUTION_PLAN
    if signal.requested_mode_hint in _NON_EXECUTING_HINTS:
        assert signal.requested_mode_hint is not None
        return signal.requested_mode_hint
    return InteractionMode.ADVISORY


# ---------------------------------------------------------------------------
# Eligibility (workflow-level, structural, non-inventive)
# ---------------------------------------------------------------------------

_SUPPORTED_EXECUTABLE_BASENAMES = frozenset({"tgauss", "tgauss.exe"})


@dataclass(frozen=True)
class EligibilityDeclarations:
    """Explicit, caller-supplied facts not derivable from the draft itself.
    A caller that cannot honestly determine one of these must supply the
    conservative (ineligible-leaning) value -- this module never infers any
    of them from free text."""

    execution_explicitly_requested: bool
    requires_package_install: bool = False
    requires_license_activation: bool = False
    requires_network_access: bool = False
    mutates_global_configuration: bool = False
    writes_outside_working_directory: bool = False
    data_or_files_missing: bool = False


@dataclass(frozen=True)
class EligibilityOutcome:
    eligible: bool
    reasons: tuple[str, ...] = ()


def evaluate_eligibility(
    draft: "orchestration_mod.RequestDraft", declarations: EligibilityDeclarations
) -> EligibilityOutcome:
    """Structurally encodes workflows/real-execution-user-workflow.md's
    Execution Eligibility Decision checklist. Adds no criteria beyond what
    that document already specifies."""
    reasons: list[str] = []
    if not declarations.execution_explicitly_requested:
        reasons.append("the user did not explicitly ask to run/test/execute/smoke-test code")
    if draft.script_path is not None:
        reasons.append(
            "script-path execution is not eligible: no trustworthy script-identity mechanism exists"
        )
    if not draft.code:
        reasons.append("code is missing")
    if not draft.working_directory:
        reasons.append("working_directory is missing or unknown")
    executable_name = Path(draft.executable_path).name.lower() if draft.executable_path else ""
    if executable_name not in _SUPPORTED_EXECUTABLE_BASENAMES:
        reasons.append(
            "executable must be the terminal tgauss/tgauss.exe executable, not a GUI executable or unset"
        )
    if draft.timeout_seconds is None or draft.timeout_seconds <= 0:
        reasons.append("timeout_seconds must be a positive number")
    if declarations.requires_package_install:
        reasons.append("code requires package installation, which is not eligible")
    if declarations.requires_license_activation:
        reasons.append("code requires license activation, which is not eligible")
    if declarations.requires_network_access:
        reasons.append("code requires network access, which is not eligible")
    if declarations.mutates_global_configuration:
        reasons.append("code mutates global configuration, which is not eligible")
    if declarations.writes_outside_working_directory:
        reasons.append("code writes outside the allowed working directory, which is not eligible")
    if declarations.data_or_files_missing:
        reasons.append("required data or files are missing")
    return EligibilityOutcome(eligible=not reasons, reasons=tuple(reasons))


# ---------------------------------------------------------------------------
# Safety review (workflow-level; reuses the controller's own outcome type)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SafetyReviewInput:
    """Structurally encodes 13 of the 14 items in workflows/real-execution-
    user-workflow.md's Pre-Execution Safety Review checklist. The 14th item
    ("user confirmed this exact run") is deliberately NOT included here: this
    outcome is attached to the draft and hashed into request_hash *before*
    confirmation exists, so baking a not-yet-true confirmation fact into it
    would be both circular and dishonest. Confirmation is enforced as its
    own, later, independently-validated gate by confirm_execution(...)/
    MockOrchestrationInstance.confirm(...) instead."""

    code_shown_or_summarized: bool
    purpose_understood: bool
    does_not_delete_files: bool
    does_not_overwrite_unrelated_files: bool
    does_not_install_packages: bool
    does_not_activate_licenses: bool
    does_not_access_network: bool
    does_not_mutate_global_configuration: bool
    file_writes_relative_or_within_allowed_directory: bool
    working_directory_exists_and_safe: bool
    output_directory_within_allowed_scope: bool
    executable_is_terminal_gauss: bool
    timeout_is_set: bool


def evaluate_safety_review(inp: SafetyReviewInput) -> "orchestration_mod.SafetyReviewOutcome":
    items = (
        orchestration_mod.SafetyReviewItem("code_shown_or_summarized", inp.code_shown_or_summarized),
        orchestration_mod.SafetyReviewItem("purpose_understood", inp.purpose_understood),
        orchestration_mod.SafetyReviewItem("does_not_delete_files", inp.does_not_delete_files),
        orchestration_mod.SafetyReviewItem(
            "does_not_overwrite_unrelated_files", inp.does_not_overwrite_unrelated_files
        ),
        orchestration_mod.SafetyReviewItem("does_not_install_packages", inp.does_not_install_packages),
        orchestration_mod.SafetyReviewItem("does_not_activate_licenses", inp.does_not_activate_licenses),
        orchestration_mod.SafetyReviewItem("does_not_access_network", inp.does_not_access_network),
        orchestration_mod.SafetyReviewItem(
            "does_not_mutate_global_configuration", inp.does_not_mutate_global_configuration
        ),
        orchestration_mod.SafetyReviewItem(
            "file_writes_relative_or_within_allowed_directory",
            inp.file_writes_relative_or_within_allowed_directory,
        ),
        orchestration_mod.SafetyReviewItem(
            "working_directory_exists_and_safe", inp.working_directory_exists_and_safe
        ),
        orchestration_mod.SafetyReviewItem(
            "output_directory_within_allowed_scope", inp.output_directory_within_allowed_scope
        ),
        orchestration_mod.SafetyReviewItem("executable_is_terminal_gauss", inp.executable_is_terminal_gauss),
        orchestration_mod.SafetyReviewItem("timeout_is_set", inp.timeout_is_set),
    )
    outcome = "pass" if all(i.passed for i in items) else "fail"
    return orchestration_mod.SafetyReviewOutcome(outcome=outcome, items=items)


# ---------------------------------------------------------------------------
# Known limitations / methodology caveat (fixed, always disclosed)
# ---------------------------------------------------------------------------

KNOWN_LIMITATIONS: tuple[str, ...] = (
    "exit_code is not authoritative -- GAUSS has returned exit_code 0 for both successful "
    "execution and every observed failure type.",
    "output_files metadata lists files; it does not read or interpret their contents.",
    "Execution proves that a specific run occurred with a specific outcome, not methodology or "
    "statistical validity.",
    "Verified only on the observed Windows GAUSS 26.1.1 environment via tgauss.exe -b <script>; "
    "no cross-platform or cross-version claim is made.",
    "Cancellation during a synchronous in-progress invocation records intent only; it cannot "
    "interrupt an already-running call.",
    "A crash between durable invocation authorization and result persistence is disclosed as "
    "ambiguous, never silently resolved.",
)

_METHODOLOGY_CAVEAT = (
    "Execution proves only that this specific run occurred with this specific outcome; it does "
    "not prove code correctness or methodological/statistical validity."
)


# ---------------------------------------------------------------------------
# Execution proposal / confirmation / response-ready result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionProposal:
    orchestration_instance_id: str
    request_id: str
    request_hash: str
    plan_digest: str
    execution_purpose: str
    code_digest: str | None
    script_path: str | None
    working_directory: str
    output_directory: str | None
    executable_path: str
    timeout_seconds: float
    expected_input_files: tuple[str, ...]
    expected_output_files: tuple[str, ...]
    required_packages: tuple[str, ...]
    environment_summary: "orchestration_mod.EnvironmentSummary"
    eligibility_passed: bool
    safety_review: "orchestration_mod.SafetyReviewOutcome"
    known_limitations: tuple[str, ...]


@dataclass(frozen=True)
class ProposalOutcome:
    orchestration_instance_id: str
    blocked: bool
    failure_category: str | None
    failure_reason: str | None
    proposal: ExecutionProposal | None


@dataclass(frozen=True)
class WorkflowConfirmationEvent:
    """`confirmed=True` alone is never sufficient anywhere in this module --
    only a full event with a `plan_digest` bound to `request_hash` is ever
    accepted."""

    session_id: str
    orchestration_instance_id: str
    request_id: str
    request_hash: str
    decision: str  # "accepted" or "rejected"
    timestamp: str
    source_interaction_id: str
    plan_digest: str


@dataclass(frozen=True)
class ConfirmationOutcome:
    orchestration_instance_id: str
    decision: str
    accepted: bool
    current_state: str


@dataclass(frozen=True)
class OutputFileSummary:
    """Metadata only -- no 'content' field, mirroring
    gauss_runtime_orchestration.OutputFileMeta."""

    path: str
    size_bytes: int | None
    file_type: str | None
    created_by_execution: Any


@dataclass(frozen=True)
class ResponseReadyResult:
    orchestration_instance_id: str
    executed: bool
    final_orchestration_state: str
    helper_invocation_status: str | None
    execution_status: str | None
    exit_code: int | None
    exit_code_is_authoritative: bool
    runtime_error_detected: bool
    timed_out: bool
    missing_expected_output: bool
    output_files: tuple[OutputFileSummary, ...]
    output_file_count: int
    output_file_details_available: bool
    analysis_status: str
    report_status: str
    failure_category: str | None
    limitations: tuple[str, ...]
    methodology_caveat: str
    rerun_requires_new_request: bool


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ConfirmationValidationError(Exception):
    """Raised when a WorkflowConfirmationEvent fails this module's own
    independent validation, before the controller is ever consulted."""


class UnknownInstanceError(Exception):
    """Raised when an orchestration_instance_id is not known to this
    workflow's cache and has no durable record either."""


class RerunRequiresNewRequestError(Exception):
    """Always raised by request_rerun(...) -- there is no in-place rerun
    path anywhere in this module."""


# ---------------------------------------------------------------------------
# Response composition helpers
# ---------------------------------------------------------------------------


def _to_response_ready_result(instance: "orchestration_mod.MockOrchestrationInstance") -> ResponseReadyResult:
    """Built from a live, same-process instance whose full evidence
    (instance.record.execution_result_reference) is still attached -- never
    guesses or fabricates a field the record does not actually carry."""
    record = instance.record
    result = record.execution_result_reference
    output_files = tuple(
        OutputFileSummary(
            path=f.path, size_bytes=f.size_bytes, file_type=f.file_type, created_by_execution=f.created_by_execution
        )
        for f in (result.output_files if result is not None else ())
    )
    return ResponseReadyResult(
        orchestration_instance_id=record.orchestration_instance_id,
        executed=(result.executed if result is not None else False),
        final_orchestration_state=record.current_state.value,
        helper_invocation_status=(
            record.helper_invocation_status.value if record.helper_invocation_status else None
        ),
        execution_status=(result.execution_status if result is not None else None),
        exit_code=(result.exit_code if result is not None else None),
        exit_code_is_authoritative=False,
        runtime_error_detected=(record.failure_category == orchestration_mod.FailureCategory.GAUSS_RUNTIME_ERROR),
        timed_out=(record.failure_category == orchestration_mod.FailureCategory.TIMEOUT),
        missing_expected_output=(
            record.failure_category == orchestration_mod.FailureCategory.MISSING_EXPECTED_OUTPUT
        ),
        output_files=output_files,
        output_file_count=len(output_files),
        output_file_details_available=True,
        analysis_status=record.analysis_status.value,
        report_status=record.report_status.value,
        failure_category=(record.failure_category.value if record.failure_category else None),
        limitations=KNOWN_LIMITATIONS,
        methodology_caveat=_METHODOLOGY_CAVEAT,
        rerun_requires_new_request=True,
    )


def _durable_record_to_response_ready_result(rec: "state_store_mod.DurableRecord") -> ResponseReadyResult:
    """Built from a durable-only view (a reloaded instance, or an instance
    never cached in this process). Per-file output metadata was never
    durably persisted -- only a count -- so `output_files` is always empty
    here and `output_file_details_available=False` discloses that honestly,
    rather than fabricating placeholder entries."""
    return ResponseReadyResult(
        orchestration_instance_id=rec.orchestration_instance_id,
        executed=(rec.execution_status is not None),
        final_orchestration_state=rec.current_state,
        helper_invocation_status=rec.invocation_status,
        execution_status=rec.execution_status,
        exit_code=rec.exit_code,
        exit_code_is_authoritative=False,
        runtime_error_detected=(rec.failure_category == "gauss_runtime_error"),
        timed_out=(rec.failure_category == "timeout"),
        missing_expected_output=(rec.failure_category == "missing_expected_output"),
        output_files=(),
        output_file_count=(rec.output_file_count or 0),
        output_file_details_available=False,
        analysis_status=rec.analysis_status,
        report_status=rec.report_status,
        failure_category=rec.failure_category,
        limitations=KNOWN_LIMITATIONS,
        methodology_caveat=_METHODOLOGY_CAVEAT,
        rerun_requires_new_request=True,
    )


# ---------------------------------------------------------------------------
# The workflow itself
# ---------------------------------------------------------------------------


class ExecutionWorkflow:
    """The single, dedicated boundary between a conversational interaction
    and the durable orchestration controller.

    Never invokes the Helper Adapter or execution helper directly, never
    performs shell execution, never authorizes execution from conversational
    text alone, never infers confirmation, and never retries automatically.
    Every orchestration instance this class creates is durable from
    creation (built via `build_durable_orchestration_instance`, never the
    bare `MockOrchestrationInstance` constructor).
    """

    def __init__(
        self,
        *,
        state_store: "state_store_mod.OrchestrationStateStore",
        clock: Callable[[], float] = time.monotonic,
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self._state_store = state_store
        self._clock = clock
        self._id_factory = id_factory
        # Process-local convenience cache only -- never the source of truth.
        # inspect()/confirm_execution()/execute() all fall back to the
        # durable store (via reload_orchestration_instance) when an instance
        # is not present here, so cross-process/restart behavior is
        # inherited from v0.36.0, not reimplemented.
        self._instances: dict[str, "orchestration_mod.MockOrchestrationInstance"] = {}

    # -- proposal ------------------------------------------------------------

    def propose_execution(
        self,
        *,
        session_id: str,
        request_id: str,
        execution_purpose: str,
        eligibility_declarations: EligibilityDeclarations,
        safety_input: SafetyReviewInput,
        code: str | None = None,
        script_path: str | None = None,
        working_directory: str | None = None,
        output_directory: str | None = None,
        executable_path: str | None = None,
        gauss_version: str | None = None,
        platform: str = "Windows",
        detection_provenance: str = "direct",
        timeout_seconds: float | None = None,
        expected_input_files: tuple[str, ...] = (),
        expected_output_files: tuple[str, ...] = (),
        required_packages: tuple[str, ...] = (),
        allow_output_files: bool = True,
    ) -> ProposalOutcome:
        environment_summary = orchestration_mod.EnvironmentSummary(
            executable_path=executable_path or "",
            gauss_version=gauss_version,
            platform=platform,
            detection_provenance=detection_provenance,
        )
        safety_outcome = evaluate_safety_review(safety_input)
        draft = orchestration_mod.RequestDraft(
            request_id=request_id,
            code=code,
            script_path=script_path,
            working_directory=working_directory,
            output_directory=output_directory,
            executable_path=executable_path,
            timeout_seconds=timeout_seconds,
            expected_input_files=tuple(expected_input_files),
            expected_output_files=tuple(expected_output_files),
            required_packages=tuple(required_packages),
            allow_output_files=allow_output_files,
            execution_purpose=execution_purpose,
            environment_summary=environment_summary,
            safety_review=safety_outcome,
        )
        eligibility_outcome = evaluate_eligibility(draft, eligibility_declarations)

        instance = orchestration_mod.build_durable_orchestration_instance(
            session_id=session_id,
            draft=draft,
            state_store=self._state_store,
            clock=self._clock,
            id_factory=self._id_factory,
        )
        self._instances[instance.record.orchestration_instance_id] = instance

        if not eligibility_outcome.eligible:
            instance.block(
                orchestration_mod.FailureCategory.INELIGIBLE_REQUEST, "; ".join(eligibility_outcome.reasons)
            )
            return self._blocked_outcome(instance)

        instance.submit_for_review()
        if instance.record.current_state == orchestration_mod.OrchestrationState.BLOCKED:
            return self._blocked_outcome(instance)

        instance.display_plan()
        assert instance.request is not None
        proposal = ExecutionProposal(
            orchestration_instance_id=instance.record.orchestration_instance_id,
            request_id=instance.request.request_id,
            request_hash=instance.request.request_hash,
            plan_digest=instance.request.request_hash,
            execution_purpose=instance.request.execution_purpose,
            code_digest=state_store_mod.digest_code(instance.request.code),
            script_path=instance.request.script_path,
            working_directory=instance.request.working_directory,
            output_directory=instance.request.output_directory,
            executable_path=instance.request.executable_path,
            timeout_seconds=instance.request.timeout_seconds,
            expected_input_files=instance.request.expected_input_files,
            expected_output_files=instance.request.expected_output_files,
            required_packages=instance.request.required_packages,
            environment_summary=instance.request.environment_summary,
            eligibility_passed=True,
            safety_review=instance.request.safety_review,
            known_limitations=KNOWN_LIMITATIONS,
        )
        return ProposalOutcome(
            orchestration_instance_id=instance.record.orchestration_instance_id,
            blocked=False,
            failure_category=None,
            failure_reason=None,
            proposal=proposal,
        )

    def _blocked_outcome(self, instance: "orchestration_mod.MockOrchestrationInstance") -> ProposalOutcome:
        reason = instance.record.transition_log[-1].note if instance.record.transition_log else None
        return ProposalOutcome(
            orchestration_instance_id=instance.record.orchestration_instance_id,
            blocked=True,
            failure_category=(instance.record.failure_category.value if instance.record.failure_category else None),
            failure_reason=reason,
            proposal=None,
        )

    # -- instance resolution (cache, then durable fallback) -------------------

    def _resolve_instance(self, orchestration_instance_id: str) -> "orchestration_mod.MockOrchestrationInstance":
        instance = self._instances.get(orchestration_instance_id)
        if instance is not None:
            return instance
        try:
            instance, _rec = orchestration_mod.reload_orchestration_instance(
                self._state_store, orchestration_instance_id, clock=self._clock
            )
        except state_store_mod.RecordNotFoundError as exc:
            raise UnknownInstanceError(str(exc)) from exc
        self._instances[orchestration_instance_id] = instance
        return instance

    # -- confirmation ----------------------------------------------------------

    def confirm_execution(self, event: WorkflowConfirmationEvent) -> ConfirmationOutcome:
        if event.decision not in ("accepted", "rejected"):
            raise ConfirmationValidationError(f"decision must be 'accepted' or 'rejected', got {event.decision!r}")
        if event.plan_digest != event.request_hash:
            raise ConfirmationValidationError(
                "plan_digest does not match request_hash -- the plan shown to the user no longer "
                "matches this request; a changed plan can never reuse a stale confirmation digest."
            )
        instance = self._resolve_instance(event.orchestration_instance_id)
        if event.request_id != instance.record.canonical_request_id:
            raise ConfirmationValidationError(
                f"request_id {event.request_id!r} does not match this instance's own canonical "
                f"request_id {instance.record.canonical_request_id!r}."
            )

        if event.decision == "rejected":
            instance.reject_confirmation()
            return ConfirmationOutcome(
                orchestration_instance_id=event.orchestration_instance_id,
                decision="rejected",
                accepted=False,
                current_state=instance.record.current_state.value,
            )

        controller_event = orchestration_mod.ConfirmationEvent(
            scope=event.request_hash, timestamp=event.timestamp, session_id=event.session_id
        )
        instance.confirm(controller_event)
        return ConfirmationOutcome(
            orchestration_instance_id=event.orchestration_instance_id,
            decision="accepted",
            accepted=True,
            current_state=instance.record.current_state.value,
        )

    # -- execution ---------------------------------------------------------

    def execute(
        self,
        orchestration_instance_id: str,
        *,
        runner: "orchestration_mod.FakeRunner",
        environment_still_matches: bool = True,
    ) -> ResponseReadyResult:
        instance = self._resolve_instance(orchestration_instance_id)
        if instance.record.current_state == orchestration_mod.OrchestrationState.CONFIRMED:
            instance.check_environment_before_invocation(still_matches=environment_still_matches)
        if instance.record.current_state == orchestration_mod.OrchestrationState.CANCELLED:
            # Environment mismatch cancelled this instance above -- report
            # the honest, structured outcome rather than letting invoke()
            # raise a raw InvalidTransitionError for a state this method
            # itself just produced.
            return _to_response_ready_result(instance)
        instance.invoke(runner)
        return _to_response_ready_result(instance)

    # -- cancellation --------------------------------------------------------

    def cancel(self, orchestration_instance_id: str, *, note: str = "") -> ResponseReadyResult:
        instance = self._resolve_instance(orchestration_instance_id)
        instance.cancel(note=note)
        return _to_response_ready_result(instance)

    def invalidate_for_session_boundary(self, orchestration_instance_id: str) -> ResponseReadyResult:
        instance = self._resolve_instance(orchestration_instance_id)
        instance.invalidate_for_session_boundary()
        return _to_response_ready_result(instance)

    # -- inspection ------------------------------------------------------------

    def inspect(self, orchestration_instance_id: str) -> ResponseReadyResult:
        instance = self._instances.get(orchestration_instance_id)
        if instance is not None and instance.request is not None:
            return _to_response_ready_result(instance)
        try:
            rec = self._state_store.load_record(orchestration_instance_id)
        except state_store_mod.RecordNotFoundError as exc:
            raise UnknownInstanceError(str(exc)) from exc
        return _durable_record_to_response_ready_result(rec)

    # -- rerun -----------------------------------------------------------------

    def request_rerun(self, orchestration_instance_id: str) -> NoReturn:
        """Always refuses. A rerun is, structurally, nothing but a fresh
        call to propose_execution(...) with a new request_id -- there is no
        code path anywhere in this class that reuses a prior confirmation,
        prior request identity, or prior durable record to perform a second
        invocation."""
        prior = self.inspect(orchestration_instance_id)
        raise RerunRequiresNewRequestError(
            f"orchestration_instance_id {orchestration_instance_id!r} (final state "
            f"{prior.final_orchestration_state!r}) cannot be rerun in place; call "
            "propose_execution(...) again with a new request_id to build a fresh, "
            "independently confirmed request."
        )


# ---------------------------------------------------------------------------
# Self-test harness (this repository's established convention -- no pytest
# is configured anywhere in this repository)
# ---------------------------------------------------------------------------


def _run_self_tests() -> int:
    """A lightweight built-in smoke test. The focused, comprehensive test
    suite lives in scripts/test_gauss_execution_workflow.py -- this function
    only sanity-checks that the module's core entry points work at all,
    against a fake runner and a disposable temp-directory store. Never
    imports the real helper, never launches a subprocess, never invokes
    GAUSS."""
    import tempfile

    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    def fake_runner(_: "orchestration_mod.RunnerInput") -> dict[str, Any]:
        return {
            "executed": True,
            "execution_status": "completed",
            "exit_code": 0,
            "stdout": "4",
            "stderr": "",
            "output_files": [],
            "warnings": [],
            "errors": [],
        }

    with tempfile.TemporaryDirectory() as tmp:
        store = state_store_mod.OrchestrationStateStore(Path(tmp) / "self_test.db")
        try:
            store.initialize()
            workflow = ExecutionWorkflow(state_store=store)

            # Advisory: code presence alone never proposes execution.
            mode = classify_interaction_mode(IntentSignal(code_present=True))
            check("code presence alone stays advisory", mode == InteractionMode.ADVISORY)

            # Explicit execution request with code reaches PREPARE_EXECUTION_PLAN.
            mode = classify_interaction_mode(
                IntentSignal(execution_explicitly_requested=True, code_present=True)
            )
            check("explicit request + code prepares a plan", mode == InteractionMode.PREPARE_EXECUTION_PLAN)

            outcome = workflow.propose_execution(
                session_id="s1",
                request_id="r1",
                execution_purpose="self-test",
                eligibility_declarations=EligibilityDeclarations(execution_explicitly_requested=True),
                safety_input=SafetyReviewInput(
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
                ),
                code="x = 2 + 2;\nprint x;",
                working_directory="C:/example/work",
                executable_path="C:/example/gauss26/tgauss.exe",
                gauss_version="GAUSS 26",
                timeout_seconds=30.0,
            )
            check("proposal is not blocked", not outcome.blocked)
            assert outcome.proposal is not None
            instance_id = outcome.orchestration_instance_id

            confirmation = workflow.confirm_execution(
                WorkflowConfirmationEvent(
                    session_id="s1",
                    orchestration_instance_id=instance_id,
                    request_id="r1",
                    request_hash=outcome.proposal.request_hash,
                    decision="accepted",
                    timestamp="t1",
                    source_interaction_id="turn-1",
                    plan_digest=outcome.proposal.plan_digest,
                )
            )
            check("confirmation accepted reaches confirmed", confirmation.current_state == "confirmed")

            result = workflow.execute(instance_id, runner=fake_runner)
            check("execution reports executed=True", result.executed)
            check("execution reaches execution_completed", result.final_orchestration_state == "execution_completed")
            check("limitations disclosed", len(result.limitations) > 0)

            inspected = workflow.inspect(instance_id)
            check("inspect matches execute result", inspected.execution_status == "completed")

            try:
                workflow.request_rerun(instance_id)
                failures.append("request_rerun should always raise RerunRequiresNewRequestError")
            except RerunRequiresNewRequestError:
                pass
        finally:
            store.close()

    if failures:
        print(f"SELF-TEST FAILED ({len(failures)} issue(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SELF-TEST PASSED: all checks succeeded.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Conversational execution-workflow layer (v0.37.0). Never imports the Helper Adapter "
            "or execution helper directly, never launches a subprocess on import, never invokes "
            "GAUSS. Requires an injected runner (a fake in every default test) to execute anything."
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
