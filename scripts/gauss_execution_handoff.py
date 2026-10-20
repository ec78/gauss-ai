"""Controlled Execution Handoff (v0.78.0) -- the FIRST, deliberately narrow,
digest-bound, user-approved bridge between conversationally generated GAUSS
code and the EXISTING GAUSS execution adapter.

Full design rationale: planning/v0.78-controlled-execution-handoff.md.

This module is the entire trust boundary. It implements:

    ExecutionHandoffRequest    -- immutable, digest-bound proposed execution
    ExecutionHandoffApproval   -- immutable, single-request-digest-bound consent
    ExecutionHandoffApprovalStore -- process-local single-use consumption tracking
    ConversationalExecutionResult -- binds request + approval + ExecutionEvidence

Hard boundaries (structurally enforced and tested, see test_gauss_execution_
handoff.py's safety tests):

- This module never launches a subprocess itself, and never imports
  `gauss_code_execution` directly -- the only way it ever reaches the real
  GAUSS helper is via `gauss_execution_adapter.load_real_helper()`, exactly
  the same lazy, explicit factory `gauss_differential_harness.RealGaussRunner`
  (v0.77.0) already uses. All real execution routes through
  `gauss_execution_adapter.GaussExecutionAdapter.invoke(...)` -- no new
  process-launch code exists anywhere in this module.
- This module never imports `gauss_conversation_engine`, `gauss_chat_provider`,
  or `command_doc_lookup` -- it takes primitive values (code text, a
  readiness-state string, ...) from its caller, never an `AnswerResult` or a
  `ModelProvider`. The model/provider layer has no path into this module at
  all; nothing here can be reached by, or grant authority to, a model call.
- `create_execution_handoff_request(...)` is the ONLY way to build a request,
  and it refuses anything whose `readiness_state` is not exactly
  `gauss_pre_execution_validation.HandoffReadiness.HANDOFF_CANDIDATE.value` --
  this is a deterministic, pre-computed verdict this module only reads, never
  computes or overrides.
- `create_execution_handoff_approval(...)` is the ONLY way to build an
  approval, and it always binds `request_digest` directly from the
  `ExecutionHandoffRequest` object passed to it -- a caller cannot supply an
  arbitrary digest.
- Nothing in this module retries, repairs, edits code, extends a timeout, or
  changes a runner/executable after a failure. `execute_execution_handoff(...)`
  is called at most meaningfully once per approval (see consumption rule
  below) and returns; it never loops, never re-invokes itself, and never
  constructs a second request.
"""

from __future__ import annotations

import enum
import hashlib
import json
import tempfile
from dataclasses import dataclass
from typing import Any, Callable

import gauss_execution_adapter as adapter_mod
import gauss_execution_interpreter as interpreter_mod
import gauss_pre_execution_validation as validation_mod

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class HandoffNotEligibleError(Exception):
    """Raised by `create_execution_handoff_request(...)` when the supplied
    `readiness_state` is not `HandoffReadiness.HANDOFF_CANDIDATE.value`. The
    model can never override this by calling this function with a different
    state -- the readiness state itself is computed entirely upstream, by
    `gauss_pre_execution_validation.compute_handoff_readiness(...)`, which
    takes no model/provider argument of any kind."""


class HandoffRequestValidationError(Exception):
    """Raised for structurally invalid request inputs (empty code, a
    non-positive timeout, an unrecognized runner, or a `\"gauss\"` runner
    with no executable_path) -- never silently coerced to a default."""


class ApprovalRequestMismatchError(Exception):
    """Raised if a caller attempts to construct an approval whose decision
    is not one of `ApprovalDecision`'s values. `request_digest` itself is
    never independently supplied -- see `create_execution_handoff_approval`."""


# ---------------------------------------------------------------------------
# ExecutionHandoffRequest
# ---------------------------------------------------------------------------

#: The exact, fixed field order the digest is computed over. `request_id`
#: and `created_at` are deliberately excluded -- identity/display-only
#: fields whose change must never invalidate an otherwise-identical request
#: (mirrors gauss_runtime_orchestration.compute_request_hash's own exclusion
#: of request_id/confirmation fields from its hash).
_DIGEST_FIELD_ORDER = (
    "code",
    "runner",
    "executable_path",
    "gauss_version",
    "timeout_seconds",
    "workspace_parent",
    "readiness_state",
)

#: The only two supported runner literals -- matches this repository's
#: existing vocabulary exactly (gauss_ai_config.resolve_default_runner's
#: default "fake"; gauss_code_assistant_cli.REAL_GAUSS_BACKEND == "gauss").
#: Deliberately not "real"/"fake" or "true"/"false" -- reusing the existing
#: literal avoids a second, parallel runner vocabulary.
SUPPORTED_RUNNERS = frozenset({"fake", "gauss"})

#: Used ONLY as the mechanical `AdapterRequest.executable_path` value for a
#: `runner == "fake"` invocation, to satisfy the existing adapter's
#: unconditional executable-basename allowlist -- never stored on
#: `ExecutionHandoffRequest.executable_path` (which stays `None` for a fake
#: runner), never digest-bound, and never displayed to the user as a real
#: executable path.
_FAKE_RUNNER_EXECUTABLE_PLACEHOLDER = "tgauss.exe"


def _canonical_digest_payload(
    *,
    code: str,
    runner: str,
    executable_path: str | None,
    gauss_version: str | None,
    timeout_seconds: float,
    workspace_parent: str | None,
    readiness_state: str,
) -> dict[str, Any]:
    """Exact textual code binding -- deliberately NO newline/whitespace
    normalization of `code` (unlike gauss_runtime_orchestration._normalize_
    code_for_hash), per this milestone's explicit conservatism requirement
    (planning/v0.78-controlled-execution-handoff.md Section 1/7): a single
    changed character anywhere in the code must change the digest, with no
    exceptions."""
    values = {
        "code": code,
        "runner": runner,
        "executable_path": executable_path,
        "gauss_version": gauss_version,
        "timeout_seconds": float(timeout_seconds),
        "workspace_parent": workspace_parent,
        "readiness_state": readiness_state,
    }
    return {name: values[name] for name in _DIGEST_FIELD_ORDER}


def compute_execution_handoff_digest(
    *,
    code: str,
    runner: str,
    executable_path: str | None,
    gauss_version: str | None,
    timeout_seconds: float,
    workspace_parent: str | None,
    readiness_state: str,
) -> str:
    """Deterministic SHA-256 fingerprint over exactly the seven
    execution-affecting fields, in fixed field order. Same inputs always
    produce the same digest; changing any one of these seven fields always
    changes it (see test_gauss_execution_handoff.py's mutation-sensitivity
    tests, one per field)."""
    canonical = _canonical_digest_payload(
        code=code, runner=runner, executable_path=executable_path, gauss_version=gauss_version,
        timeout_seconds=timeout_seconds, workspace_parent=workspace_parent, readiness_state=readiness_state,
    )
    serialized = json.dumps(canonical, sort_keys=False, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExecutionHandoffRequest:
    """Immutable (frozen dataclass -- Python raises `FrozenInstanceError` on
    any attempted attribute assignment). Represents exactly one proposed
    execution of exactly this `code` text. Never constructed directly by
    calling code other than `create_execution_handoff_request(...)`."""

    request_id: str
    code: str
    readiness_state: str
    runner: str
    executable_path: str | None
    gauss_version: str | None
    timeout_seconds: float
    workspace_parent: str | None
    created_at: str
    digest: str

    def recompute_digest(self) -> str:
        """Recomputes the digest fresh from this request's own current field
        values -- used by the pre-launch gate to prove "same inputs, same
        digest" holds at launch time, not just at construction time (Phase 8
        of the milestone brief). Since this object is frozen, this can only
        ever equal `self.digest` unless the class's own field values were
        somehow altered outside its frozen contract."""
        return compute_execution_handoff_digest(
            code=self.code, runner=self.runner, executable_path=self.executable_path,
            gauss_version=self.gauss_version, timeout_seconds=self.timeout_seconds,
            workspace_parent=self.workspace_parent, readiness_state=self.readiness_state,
        )


def create_execution_handoff_request(
    *,
    code: str,
    readiness_state: str,
    request_id: str,
    created_at: str,
    runner: str = "fake",
    executable_path: str | None = None,
    gauss_version: str | None = None,
    timeout_seconds: float = 30.0,
    workspace_parent: str | None = None,
) -> ExecutionHandoffRequest:
    """The ONE pure builder for `ExecutionHandoffRequest`. No execution, no
    file write, no model call. Requires `readiness_state ==
    HandoffReadiness.HANDOFF_CANDIDATE.value` -- anything else (`not_ready`,
    `review_required`, or an unrecognized string) raises
    `HandoffNotEligibleError` before any other validation runs."""
    if readiness_state != validation_mod.HandoffReadiness.HANDOFF_CANDIDATE.value:
        raise HandoffNotEligibleError(
            f"readiness_state {readiness_state!r} is not "
            f"{validation_mod.HandoffReadiness.HANDOFF_CANDIDATE.value!r}; only code that has reached "
            "HANDOFF_CANDIDATE may become an ExecutionHandoffRequest."
        )
    if not code or not code.strip():
        raise HandoffRequestValidationError("code must be non-empty.")
    if runner not in SUPPORTED_RUNNERS:
        raise HandoffRequestValidationError(
            f"runner {runner!r} is not supported; must be one of {sorted(SUPPORTED_RUNNERS)!r}."
        )
    if timeout_seconds is None or timeout_seconds <= 0:
        raise HandoffRequestValidationError("timeout_seconds must be a positive number.")
    if runner == "gauss" and not executable_path:
        raise HandoffRequestValidationError("runner 'gauss' requires a non-empty executable_path.")

    digest = compute_execution_handoff_digest(
        code=code, runner=runner, executable_path=executable_path, gauss_version=gauss_version,
        timeout_seconds=timeout_seconds, workspace_parent=workspace_parent, readiness_state=readiness_state,
    )
    return ExecutionHandoffRequest(
        request_id=request_id, code=code, readiness_state=readiness_state, runner=runner,
        executable_path=executable_path, gauss_version=gauss_version, timeout_seconds=timeout_seconds,
        workspace_parent=workspace_parent, created_at=created_at, digest=digest,
    )


# ---------------------------------------------------------------------------
# ExecutionHandoffApproval
# ---------------------------------------------------------------------------


class ApprovalDecision(str, enum.Enum):
    APPROVED = "approved"
    DECLINED = "declined"


#: Fixed, always-present consent scope statement -- mirrors
#: gauss_repair_application_approval.APPLICATION_APPROVAL_BOUNDARY_STATEMENT's
#: discipline of a fixed, never-reworded-per-decision disclosure string.
APPROVED_CONSENT_STATEMENT = (
    "This approval authorizes exactly one execution of the exact code shown above, using the exact runner, "
    "executable, and timeout shown above, one time only. It does not approve methodological correctness, does "
    "not authorize a retry, does not authorize a repair, and does not authorize any different code or settings."
)

DECLINED_CONSENT_STATEMENT = (
    "This request was declined. No code was executed. Declining can never later be treated as approval -- a "
    "new explicit approval of a new request is required before any execution of this or any other code."
)


class ExecutionApprovalValidationError(Exception):
    """Raised for a structurally invalid approval construction request."""


@dataclass(frozen=True)
class ExecutionHandoffApproval:
    """Immutable. `request_digest` is always taken directly from the
    `ExecutionHandoffRequest` passed to `create_execution_handoff_approval`
    -- never independently supplied, so an approval object can never be
    constructed pointing at a digest the caller merely typed in."""

    approval_id: str
    request_digest: str
    decision: str
    decided_at: str
    consent_statement: str


def create_execution_handoff_approval(
    request: ExecutionHandoffRequest,
    *,
    decision: str,
    approval_id: str,
    decided_at: str,
) -> ExecutionHandoffApproval:
    """The ONE pure builder for `ExecutionHandoffApproval`. `decision` must
    be exactly one of `ApprovalDecision`'s values (`"approved"`/
    `"declined"`) -- this function performs no natural-language
    interpretation of a raw user response itself; see
    `parse_execution_approval_response(...)` for that, called by the
    orchestration layer BEFORE this function, never inside it."""
    if decision not in {d.value for d in ApprovalDecision}:
        raise ExecutionApprovalValidationError(
            f"decision {decision!r} must be one of {[d.value for d in ApprovalDecision]!r}."
        )
    statement = APPROVED_CONSENT_STATEMENT if decision == ApprovalDecision.APPROVED.value else DECLINED_CONSENT_STATEMENT
    return ExecutionHandoffApproval(
        approval_id=approval_id, request_digest=request.digest, decision=decision,
        decided_at=decided_at, consent_statement=statement,
    )


# ---------------------------------------------------------------------------
# Explicit approval-response parsing (Phase 6) -- deterministic, narrow,
# never a fuzzy/affirmative-sounding-phrase heuristic.
# ---------------------------------------------------------------------------

_AFFIRMATIVE_RESPONSES = frozenset({"yes", "approve"})
_NEGATIVE_RESPONSES = frozenset({"no", "decline"})


def parse_execution_approval_response(text: str) -> str:
    """Returns exactly one of `"approved"`, `"declined"`, `"unrecognized"`.
    Deliberately narrow -- see module docstring and planning doc Section 6.
    Never treats "okay"/"sure"/"looks good"/"go ahead" or any other
    affirmative-sounding phrase as approval."""
    normalized = (text or "").strip().lower()
    if normalized in _AFFIRMATIVE_RESPONSES:
        return "approved"
    if normalized in _NEGATIVE_RESPONSES:
        return "declined"
    return "unrecognized"


#: Small, fixed trigger-phrase set for recognizing an explicit conversational
#: execution request -- mirrors gauss_ai_config.looks_like_cli_invocation's
#: existing "small fixed detector, not a general classifier" convention.
_EXECUTION_TRIGGER_PHRASES = frozenset({"run this", "run this code", "execute this", "execute this code"})


def looks_like_execution_request(text: str) -> bool:
    return (text or "").strip().lower() in _EXECUTION_TRIGGER_PHRASES


# ---------------------------------------------------------------------------
# ExecutionHandoffApprovalStore -- process-local single-use tracking
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ApprovalRecord:
    approval: ExecutionHandoffApproval
    consumed: bool


class ExecutionHandoffApprovalStore:
    """In-memory only, one per process/session -- never persisted, never
    shared across processes (Phase 29 explicitly excludes a persistent
    approval database). Consumption is tracked here, per `approval_id`,
    rather than by mutating the frozen `ExecutionHandoffApproval` object
    itself."""

    def __init__(self) -> None:
        self._records: dict[str, _ApprovalRecord] = {}

    def record(self, approval: ExecutionHandoffApproval) -> None:
        if approval.approval_id in self._records:
            raise ExecutionApprovalValidationError(
                f"approval_id {approval.approval_id!r} is already recorded; approval_ids must be unique."
            )
        self._records[approval.approval_id] = _ApprovalRecord(approval=approval, consumed=False)

    def is_consumed(self, approval_id: str) -> bool:
        record = self._records.get(approval_id)
        return record is not None and record.consumed

    def mark_consumed(self, approval_id: str) -> None:
        record = self._records.get(approval_id)
        if record is None:
            raise ExecutionApprovalValidationError(f"no recorded approval for approval_id {approval_id!r}.")
        self._records[approval_id] = _ApprovalRecord(approval=record.approval, consumed=True)

    def get(self, approval_id: str) -> ExecutionHandoffApproval | None:
        record = self._records.get(approval_id)
        return record.approval if record is not None else None

    def __len__(self) -> int:
        return len(self._records)


# ---------------------------------------------------------------------------
# Failure taxonomy (Phase 25)
# ---------------------------------------------------------------------------


class HandoffOutcome(str, enum.Enum):
    NOT_ELIGIBLE = "not_eligible"
    DECLINED = "declined"
    APPROVAL_MISMATCH = "approval_mismatch"
    STALE_REQUEST = "stale_request"
    ALREADY_CONSUMED = "already_consumed"
    EXECUTION_BLOCKED = "execution_blocked"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_TIMEOUT = "execution_timeout"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    SUCCESS = "success"


# ---------------------------------------------------------------------------
# ConversationalExecutionResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConversationalExecutionResult:
    """Binds execution evidence back to the exact approved request. Composes
    `gauss_execution_interpreter.ExecutionEvidence` rather than re-defining
    execution evidence -- `evidence` is `None` only when nothing was
    actually launched (a pre-launch-gate block or an adapter-level
    pre-invocation rejection)."""

    request_digest: str
    approval_id: str
    launched: bool
    outcome: str
    evidence: "interpreter_mod.ExecutionEvidence | None"
    blocked_reason: str | None
    result_digest: str


def _compute_result_digest(
    *, request_digest: str, approval_id: str, launched: bool, outcome: str,
    evidence: "interpreter_mod.ExecutionEvidence | None",
) -> str:
    evidence_summary = None
    if evidence is not None:
        evidence_summary = {
            "execution_status": evidence.execution_status,
            "exit_code": evidence.exit_code,
            "timed_out": evidence.timed_out,
            "executed": evidence.executed,
        }
    payload = {
        "request_digest": request_digest,
        "approval_id": approval_id,
        "launched": launched,
        "outcome": outcome,
        "evidence_summary": evidence_summary,
    }
    serialized = json.dumps(payload, sort_keys=False, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _blocked_result(
    *, request_digest: str, approval_id: str, outcome: HandoffOutcome, reason: str,
) -> ConversationalExecutionResult:
    return ConversationalExecutionResult(
        request_digest=request_digest, approval_id=approval_id, launched=False, outcome=outcome.value,
        evidence=None, blocked_reason=reason,
        result_digest=_compute_result_digest(
            request_digest=request_digest, approval_id=approval_id, launched=False, outcome=outcome.value,
            evidence=None,
        ),
    )


def _prelaunch_check(
    request: ExecutionHandoffRequest, approval: ExecutionHandoffApproval, store: ExecutionHandoffApprovalStore,
) -> tuple[HandoffOutcome, str] | None:
    """Returns `(outcome, reason)` if execution must be blocked, `None` if
    every gate passes. Order matches planning doc Section 4 exactly."""
    if approval.decision == ApprovalDecision.DECLINED.value:
        return HandoffOutcome.DECLINED, "the approval on file for this request is a decline, not an approval."
    if approval.request_digest != request.digest:
        return (
            HandoffOutcome.APPROVAL_MISMATCH,
            f"approval.request_digest ({approval.request_digest!r}) does not match request.digest "
            f"({request.digest!r}); this approval does not authorize this request.",
        )
    if request.recompute_digest() != request.digest:
        return (
            HandoffOutcome.STALE_REQUEST,
            "the request's own fields no longer reproduce its recorded digest; this request is stale.",
        )
    if store.is_consumed(approval.approval_id):
        return (
            HandoffOutcome.ALREADY_CONSUMED,
            f"approval_id {approval.approval_id!r} has already been consumed by a prior execution attempt; "
            "a fresh explicit approval is required to execute again.",
        )
    if request.readiness_state != validation_mod.HandoffReadiness.HANDOFF_CANDIDATE.value:
        return (
            HandoffOutcome.NOT_ELIGIBLE,
            f"request.readiness_state {request.readiness_state!r} is no longer HANDOFF_CANDIDATE.",
        )
    return None


def build_default_fake_helper() -> Callable[..., dict[str, Any]]:
    """A small, deterministic canned fake helper matching
    `gauss_execution_adapter.HelperCallable`'s structural shape -- used only
    when `runner == \"fake\"` and the caller does not inject its own (tests
    always inject their own to exercise success/failure/timeout scenarios;
    this is only the interactive-chat default-mode fallback, exactly the
    same role `resolve_default_runner`'s `\"fake\"` default already plays
    for the guided-repair CLI when no real GAUSS is configured)."""

    def _fake_helper(**kwargs: Any) -> dict[str, Any]:
        return {
            "executed": True,
            "execution_status": "completed",
            "exit_code": 0,
            "stdout": "(fake runner: no real GAUSS was invoked)",
            "stderr": "",
            "output_files": [],
            "warnings": [],
            "errors": [],
        }

    return _fake_helper


def select_helper(runner: str) -> Callable[..., dict[str, Any]]:
    """The one explicit, narrow selection point between a fake helper and
    the real production helper. For `runner == \"gauss\"`, this calls
    `gauss_execution_adapter.load_real_helper()` -- the SAME lazy, explicit
    factory `gauss_differential_harness.RealGaussRunner` already uses;
    importing `gauss_code_execution` still only happens inside that
    function's own body, never here. Never called automatically by
    `execute_execution_handoff(...)` itself -- the caller (chat
    orchestration) must call this explicitly, exactly once, per request."""
    if runner == "gauss":
        return adapter_mod.load_real_helper()
    if runner == "fake":
        return build_default_fake_helper()
    raise HandoffRequestValidationError(f"runner {runner!r} is not supported.")


def execute_execution_handoff(
    request: ExecutionHandoffRequest,
    approval: ExecutionHandoffApproval,
    *,
    store: ExecutionHandoffApprovalStore,
    helper: Callable[..., dict[str, Any]],
) -> ConversationalExecutionResult:
    """The ONE orchestration function that may result in a real GAUSS
    invocation. Runs the full pre-launch gate first (Section 4); on any
    failure, returns a blocked result and calls the adapter zero times. On
    success, builds exactly one `gauss_execution_adapter.AdapterRequest`
    from `request`'s already-validated, digest-bound fields, invokes the
    EXISTING `gauss_execution_adapter.GaussExecutionAdapter` exactly once
    (a fresh instance, constructed here, wrapping the caller-selected
    `helper`), and returns a `ConversationalExecutionResult`.

    Never retries. Never repairs. Never changes `request` or `approval`.
    Never constructs a second request. The caller is responsible for
    calling this at most once per approval; this function itself also
    refuses via the `ALREADY_CONSUMED` gate if it is called again with an
    approval this same `store` has already marked consumed."""
    blocked = _prelaunch_check(request, approval, store)
    if blocked is not None:
        outcome, reason = blocked
        return _blocked_result(
            request_digest=request.digest, approval_id=approval.approval_id, outcome=outcome, reason=reason,
        )

    # The existing adapter's own executable-allowlist and environment-probe
    # guards apply unconditionally, even to a fake/test helper (mirrors
    # gauss_execution_adapter._run_self_tests's own fake-helper smoke test,
    # which passes a real environment_probe override for exactly this
    # reason). For runner=="fake" there is no real executable to bind, so a
    # fixed, allowlisted placeholder basename is used ONLY as the adapter's
    # own required argument -- it is never stored on the request, never
    # digest-bound, and never shown to the user as a real executable
    # (render_execution_handoff_prompt never prints an executable line when
    # request.executable_path is None).
    if request.runner == "gauss":
        adapter_executable_path = request.executable_path
        environment_probe = None  # real, default filesystem-existence probe
    else:
        adapter_executable_path = _FAKE_RUNNER_EXECUTABLE_PLACEHOLDER
        environment_probe = lambda _path: True  # noqa: E731 - fake runner never touches the real filesystem

    adapter = adapter_mod.GaussExecutionAdapter(helper=helper, environment_probe=environment_probe)
    with tempfile.TemporaryDirectory(prefix="gauss_ai_handoff_") as tmp_dir:
        adapter_request = adapter_mod.AdapterRequest(
            request_identity=approval.approval_id,
            code=request.code,
            script_path=None,
            working_directory=tmp_dir,
            output_directory=None,
            executable_path=adapter_executable_path,
            gauss_version=request.gauss_version,
            timeout_seconds=request.timeout_seconds,
            allow_output_files=False,
        )
        adapter_outcome = adapter.invoke(adapter_request)

        if not adapter_outcome.invoked:
            # Deterministically provable non-launch (planning doc Section 5)
            # -- the approval remains unconsumed. This is not an autonomous
            # retry: nothing here re-attempts anything; a human must issue a
            # brand new explicit "run this" turn to try again.
            category = adapter_outcome.failure_category.value if adapter_outcome.failure_category else "unknown"
            return _blocked_result(
                request_digest=request.digest, approval_id=approval.approval_id,
                outcome=HandoffOutcome.INFRASTRUCTURE_FAILURE,
                reason=f"adapter rejected before invocation ({category}): {adapter_outcome.rejection_reason}",
            )

        # The helper was actually called (or an attempt raised inside the
        # adapter) -- the approval is now consumed, regardless of outcome.
        store.mark_consumed(approval.approval_id)

        raw = adapter_outcome.raw_result or {}
        evidence = interpreter_mod.ExecutionEvidence(
            runner=request.runner,
            gauss_ran=(request.runner == "gauss"),
            executed=bool(raw.get("executed", False)),
            execution_status=adapter_outcome.execution_status,
            exit_code=raw.get("exit_code"),
            stdout_chars=len(raw["stdout"]) if raw.get("stdout") else None,
            stderr_chars=len(raw["stderr"]) if raw.get("stderr") else None,
            timed_out=(adapter_outcome.execution_status == "timed_out"),
            stdout_text=raw.get("stdout"),
            stderr_text=raw.get("stderr"),
        )

        if adapter_outcome.failure_category is not None:
            outcome = HandoffOutcome.INFRASTRUCTURE_FAILURE
            blocked_reason = adapter_outcome.rejection_reason
        elif adapter_outcome.execution_status == "completed":
            outcome = HandoffOutcome.SUCCESS
            blocked_reason = None
        elif adapter_outcome.execution_status == "timed_out":
            outcome = HandoffOutcome.EXECUTION_TIMEOUT
            blocked_reason = None
        else:
            outcome = HandoffOutcome.EXECUTION_FAILED
            blocked_reason = None

        return ConversationalExecutionResult(
            request_digest=request.digest, approval_id=approval.approval_id, launched=True,
            outcome=outcome.value, evidence=evidence, blocked_reason=blocked_reason,
            result_digest=_compute_result_digest(
                request_digest=request.digest, approval_id=approval.approval_id, launched=True,
                outcome=outcome.value, evidence=evidence,
            ),
        )


# ---------------------------------------------------------------------------
# Rendering helpers (pure string formatting -- no I/O)
# ---------------------------------------------------------------------------


#: v0.87.0: what the prompt's "Runs in" line says -- true of every run,
#: since `execute_execution_handoff` always uses a new
#: `tempfile.TemporaryDirectory(prefix="gauss_ai_handoff_")`.
HANDOFF_WORKING_DIRECTORY_DESCRIPTION = "a new temporary directory, deleted after the run"


def render_execution_handoff_prompt(request: ExecutionHandoffRequest) -> str:
    """Shows the exact code and exact execution details BEFORE approval is
    requested -- Phase 5/23 of the milestone brief. Never summarizes the
    code instead of showing it."""
    runner_label = "fake (no real GAUSS invocation)" if request.runner == "fake" else "GAUSS"
    lines = [
        "Ready for controlled execution.",
        "",
        "Code:",
        "```gauss",
        request.code,
        "```",
        "",
        f"Runner: {runner_label}",
    ]
    if request.executable_path:
        lines.append(f"Executable: {request.executable_path}")
    lines.append(f"Timeout: {request.timeout_seconds:g} seconds")
    # v0.87.0 (live finding 77.x f3): the prompt used to print "Workspace
    # parent: <path>" whenever the request carried one, but
    # `execute_execution_handoff` always runs in a fresh
    # `tempfile.TemporaryDirectory` (the v0.78.0 design) and never reads
    # `workspace_parent`. Every approved 77.x run executed somewhere other
    # than the directory the prompt named. The prompt now states where code
    # really runs; `workspace_parent` is never printed, and both callers stop
    # setting it (the field and its digest position are unchanged).
    lines.append(f"Runs in: {HANDOFF_WORKING_DIRECTORY_DESCRIPTION}")
    lines.append(f"Request digest: {request.digest}")
    lines.extend([
        "",
        "This code has not been executed.",
        "Execution success does not establish methodological validity.",
        "",
        f"Approve this exact execution using {runner_label} with a {request.timeout_seconds:g}-second "
        "timeout? [yes/no]",
    ])
    return "\n".join(lines)


def render_conversational_execution_result(result: ConversationalExecutionResult) -> str:
    if not result.launched:
        return (
            f"Execution was not performed ({result.outcome}). {result.blocked_reason or ''}".strip()
        )
    evidence = result.evidence
    lines: list[str] = []
    if result.outcome == HandoffOutcome.SUCCESS.value:
        lines.append("Execution completed.")
    elif result.outcome == HandoffOutcome.EXECUTION_TIMEOUT.value:
        lines.append("Execution timed out.")
    elif result.outcome == HandoffOutcome.INFRASTRUCTURE_FAILURE.value:
        lines.append("Execution could not be completed due to an infrastructure failure.")
    else:
        lines.append("GAUSS returned an execution error.")
    if evidence is not None:
        lines.append("")
        lines.append("stdout:")
        lines.append(evidence.stdout_text or "(none)")
        lines.append("")
        lines.append("stderr:")
        lines.append(evidence.stderr_text or "(none)")
        lines.append("")
        lines.append(f"GAUSS exit status: {evidence.exit_code if evidence.exit_code is not None else '(unknown)'}")
    lines.append("")
    if result.outcome == HandoffOutcome.SUCCESS.value:
        lines.append(
            "This confirms runtime execution only; it does not establish methodological correctness."
        )
    else:
        lines.append("No retry or repair was attempted.")
    return "\n".join(lines)
