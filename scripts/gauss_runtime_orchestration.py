"""Runtime orchestration controller (v0.31.0 Phase 2 skeleton, v0.32.0 Phase 3
Increment 1 adapter bridge, v0.33.0 Controlled Real Execution Integration).

This module implements the Phase 2 deliverable from
planning/v0.31.0-runtime-orchestration-design.md's Implementation Phases: a
small, internal orchestration layer that encodes the canonical execution
request, the 13-state runtime state machine, the confirmation lifecycle, and
the "exactly once per confirmed request" invocation invariant well enough for
deterministic unit testing -- entirely against an injected fake runner by
default.

Authoritative design sources (this module does not redefine their rules, only
implements them):

- planning/v0.31.0-canonical-execution-request-contract.md -- the 18-field
  canonical execution request contract, its canonicalization/hashing rules,
  and its confirmation contract.
- planning/v0.31.0-runtime-state-machine-contract.md -- the 13-state machine,
  its transition/guard/failure-routing tables, and its invariants.
- planning/v0.33.0-controlled-real-execution-integration.md -- the real
  execution path this module can now optionally drive via
  `build_production_adapter_runner(...)`, and the single, bounded,
  human-authorized real GAUSS smoke test verified through it.

This module is **mock-only by default, with an explicit, narrow real-path
factory that must be called by name to activate**:

- It never imports scripts/gauss_code_execution.py directly, and never calls
  execute_gauss_code(...) itself. The only import this module adds beyond
  the stdlib is scripts/gauss_execution_adapter.py -- which itself never
  imports the real helper at module import time either (see that module's
  own docstring and `load_real_helper()`).
- It never launches a subprocess, never constructs a shell command, and
  never detects a real GAUSS environment, anywhere in this module's own code.
- It never invokes gauss.exe or tgauss.exe directly; `build_production_adapter_runner(...)`
  is the one function whose *explicit* invocation, by name, results in a
  real-helper-backed `AdapterRunner` being constructed -- see that
  function's own docstring for the exact, narrow boundary this implies.
- All "execution" happens through an injected runner satisfying the
  FakeRunner Protocol -- either a fake/stub callable (every test in this
  module's own default test suite), or `AdapterRunner`, a thin bridge to a
  `gauss_execution_adapter.GaussExecutionAdapter` instance. `AdapterRunner`
  itself never selects a real helper; the adapter it wraps is constructed
  by its *caller* with an explicit helper callable -- fake in every default
  test, real only when `build_production_adapter_runner(...)` is called
  explicitly, by name, which no test in this module's default suite does.
- All state is in-memory only, scoped to one Python process, with no
  cross-process coordination, no database, no queue, and no file-based
  persistence -- unchanged by the real-path factory's existence.

Deliberately out of scope for this phase (see the module's Non-Goals in
planning/v0.31.0-runtime-orchestration-design.md):

- Real, actually-invoked Helper Adapter execution -- Increment 1 authorizes
  only the adapter's own interface and this bridge, both tested exclusively
  against fake helpers (planning/v0.32.0-real-helper-adapter-scope.md
  Section 24). No test in this module's own suite ever constructs a real
  helper or calls `gauss_execution_adapter.load_real_helper()`.
- Real execution-aware analysis / report-generation workflow integration
  (Phase 4) -- this module accepts injected fake hooks instead.
- Real file/session handling beyond what is needed to exercise the contract
  (Phase 5).
- A full Eligibility Evaluator / Safety Review rule engine -- this module
  consumes their *outcomes* (a pass/fail plus a failure category) rather
  than re-implementing the rules from workflows/real-execution-user-workflow.md.
  Tests simulate those outcomes directly via `block(...)`.
- Script-content fingerprinting -- script-path mode requests are refused
  outright in this phase (see ScriptIdentityUntrustedError and
  MockOrchestrationInstance.submit_for_review), per the canonical request
  contract's own documented, unresolved script-fingerprinting gap.
- User-facing workflow integration -- nothing here is wired into
  workflows/code-assistant-response.md or any agent.

Hash algorithm: SHA-256 (stdlib `hashlib`), applied to a deterministic
canonical JSON serialization of the hash-included fields. SHA-256 was chosen
because the canonical request contract's own Canonicalization Rules section
states that "any hash with acceptably low collision probability" satisfies
the design -- no adversarial-resistance property is actually required, only
determinism and stdlib availability. No third-party hashing library is used.
"""

from __future__ import annotations

import argparse
import enum
import hashlib
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# gauss_execution_adapter never imports scripts/gauss_code_execution.py at
# its own import time (see that module's docstring), so this import has no
# execution side effects: no helper import, no GAUSS detection, no
# subprocess launch, no code run.
import gauss_execution_adapter  # noqa: E402

# v0.36.0: gauss_orchestration_state_store never imports this module (the
# dependency direction is one-way: this module may depend on the store, the
# store never depends on this module), never imports the real helper, never
# launches a subprocess, and never touches GAUSS. Importing it has no
# execution side effects -- only OrchestrationStateStore.__init__ creates a
# directory or opens a database file, and this import does not construct one.
import gauss_orchestration_state_store as state_store_mod  # noqa: E402

# ---------------------------------------------------------------------------
# Small supporting value types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EnvironmentSummary:
    """Conceptual attributes of the frozen environment context (state-machine
    contract Section 6). Frozen once built into a CanonicalExecutionRequest."""

    executable_path: str
    gauss_version: str | None
    platform: str
    detection_provenance: str  # "direct" or "environment_check_result"


@dataclass(frozen=True)
class SafetyReviewItem:
    name: str
    passed: bool


@dataclass(frozen=True)
class SafetyReviewOutcome:
    """Mirrors workflows/real-execution-user-workflow.md's 14-item
    Pre-Execution Safety Review as a structured pass/fail outcome (canonical
    request contract Section 7 / state-machine contract Section 2's
    `safety_review` requirement)."""

    outcome: str  # "pass" or "fail"
    items: tuple[SafetyReviewItem, ...] = ()

    @property
    def passed(self) -> bool:
        return self.outcome == "pass"


# ---------------------------------------------------------------------------
# Canonical Execution Request (18-field contract)
# ---------------------------------------------------------------------------

_PLAN_FIELDS = frozenset(
    {
        "code",
        "script_path",
        "working_directory",
        "output_directory",
        "executable_path",
        "timeout_seconds",
        "expected_input_files",
        "expected_output_files",
        "required_packages",
        "allow_output_files",
        "execution_purpose",
        "environment_summary",
        "safety_review",
        "request_hash",
    }
)

# The 12 fields that contribute to request_hash, per the canonical request
# contract's Hash-Inclusion Matrix (Section 10). request_id, execution_purpose,
# user_confirmed, confirmation_scope, and confirmation_timestamp are
# deliberately excluded -- see that section for the rationale behind each.
_HASH_INCLUDED_FIELD_ORDER = (
    "code",
    "script_path",
    "working_directory",
    "output_directory",
    "executable_path",
    "timeout_seconds",
    "expected_input_files",
    "expected_output_files",
    "required_packages",
    "allow_output_files",
    "environment_summary",
    "safety_review",
)


class RequestFrozenError(Exception):
    """Raised when a plan field is mutated after the request has been frozen."""


class ConfirmationAlreadySetError(Exception):
    """Raised when attach_confirmation is called on an already-confirmed request.

    Confirmation is monotonic (state-machine contract Invariant 16): once
    accepted, it never reverts to an unconfirmed state on the same object.
    """


class ConfirmationScopeMismatchError(Exception):
    """Raised when confirmation_scope does not equal the current request_hash."""


class RequestValidationError(Exception):
    """Raised when a draft request fails structural or mode validation."""


@dataclass
class CanonicalExecutionRequest:
    """The 18-field canonical execution request.

    Mutable only until frozen (mirrors the contract's lifecycle steps 3-6);
    the 14 "plan" fields (see _PLAN_FIELDS) become immutable once `freeze()`
    is called. The three confirmation fields may be set exactly once, after
    freezing, via `attach_confirmation(...)` -- never before, and never a
    second time.
    """

    request_id: str
    code: str | None
    script_path: str | None
    working_directory: str
    output_directory: str | None
    executable_path: str
    timeout_seconds: float
    expected_input_files: tuple[str, ...]
    expected_output_files: tuple[str, ...]
    required_packages: tuple[str, ...]
    allow_output_files: bool
    execution_purpose: str
    environment_summary: EnvironmentSummary
    safety_review: SafetyReviewOutcome
    request_hash: str
    user_confirmed: bool = False
    confirmation_scope: str | None = None
    confirmation_timestamp: str | None = None
    _frozen: bool = field(default=False, repr=False, compare=False)

    def __setattr__(self, name: str, value: Any) -> None:
        if name != "_frozen" and getattr(self, "_frozen", False) and name in _PLAN_FIELDS:
            raise RequestFrozenError(
                f"Cannot mutate '{name}' on a frozen CanonicalExecutionRequest; "
                "build a new request instead (per the immutability guarantee in "
                "planning/v0.31.0-canonical-execution-request-contract.md's lifecycle)."
            )
        object.__setattr__(self, name, value)

    def freeze(self) -> "CanonicalExecutionRequest":
        object.__setattr__(self, "_frozen", True)
        return self

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def attach_confirmation(self, *, confirmation_scope: str, confirmation_timestamp: str) -> None:
        if not self._frozen:
            raise RequestFrozenError("Cannot confirm a request that has not been frozen yet.")
        if self.user_confirmed:
            raise ConfirmationAlreadySetError(
                "Confirmation is monotonic; this request has already been confirmed once."
            )
        if confirmation_scope != self.request_hash:
            raise ConfirmationScopeMismatchError(
                "confirmation_scope must equal the current request_hash exactly; "
                "user_confirmed=true alone is never sufficient."
            )
        object.__setattr__(self, "user_confirmed", True)
        object.__setattr__(self, "confirmation_scope", confirmation_scope)
        object.__setattr__(self, "confirmation_timestamp", confirmation_timestamp)


@dataclass
class RequestDraft:
    """The mutable, pre-canonicalization draft a request is built from.

    Corresponds to the canonical request contract's lifecycle steps 3-5
    (draft assembled, eligibility reviewed, safety reviewed) -- freely
    mutable, no hash, no confirmation.
    """

    request_id: str
    code: str | None = None
    script_path: str | None = None
    working_directory: str | None = None
    output_directory: str | None = None
    executable_path: str | None = None
    timeout_seconds: float | None = None
    expected_input_files: tuple[str, ...] = ()
    expected_output_files: tuple[str, ...] = ()
    required_packages: tuple[str, ...] = ()
    allow_output_files: bool = True
    execution_purpose: str = ""
    environment_summary: EnvironmentSummary | None = None
    safety_review: SafetyReviewOutcome | None = None


def _normalize_code_for_hash(code: str) -> str:
    """Newline normalization for hashing only (canonical request contract
    Section 9) -- the original code text is never rewritten for display or
    for the runner; only this hash input is normalized."""
    return code.replace("\r\n", "\n").replace("\r", "\n")


def _canonical_environment_summary(e: EnvironmentSummary) -> dict[str, Any]:
    return {
        "executable_path": e.executable_path,
        "gauss_version": e.gauss_version,
        "platform": e.platform,
        "detection_provenance": e.detection_provenance,
    }


def _canonical_safety_review(s: SafetyReviewOutcome) -> dict[str, Any]:
    return {
        "outcome": s.outcome,
        "items": [
            {"name": i.name, "passed": i.passed}
            for i in sorted(s.items, key=lambda item: item.name)
        ],
    }


def compute_request_hash(request: "CanonicalExecutionRequest") -> str:
    """Deterministic SHA-256 fingerprint over exactly the 12 hash-included
    fields, in the fixed field order defined by
    _HASH_INCLUDED_FIELD_ORDER (canonical request contract Section 10)."""
    canonical: dict[str, Any] = {}
    for name in _HASH_INCLUDED_FIELD_ORDER:
        value = getattr(request, name)
        if name == "code":
            canonical[name] = _normalize_code_for_hash(value) if value is not None else None
        elif name == "timeout_seconds":
            canonical[name] = float(value)
        elif name == "expected_input_files":
            canonical[name] = sorted(value)
        elif name == "expected_output_files":
            canonical[name] = sorted(value)
        elif name == "required_packages":
            canonical[name] = sorted(value)
        elif name == "allow_output_files":
            canonical[name] = bool(value)
        elif name == "environment_summary":
            canonical[name] = _canonical_environment_summary(value)
        elif name == "safety_review":
            canonical[name] = _canonical_safety_review(value)
        else:
            canonical[name] = value

    # sort_keys=False: field order is already fixed by construction above,
    # matching the contract's "fixed field order" rule exactly (not
    # alphabetical). Nested dicts are built in fixed order too.
    serialized = json.dumps(canonical, sort_keys=False, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_canonical_request(draft: RequestDraft) -> CanonicalExecutionRequest:
    """Validate a draft (structural + mode-exclusivity checks only -- NOT
    eligibility/safety, which are the caller's responsibility per this
    module's scope), canonicalize it, compute its hash, and return a frozen
    CanonicalExecutionRequest.

    Raises RequestValidationError on any structural/mode failure. Fails
    closed: an incomplete or ambiguous draft is never silently accepted.
    """
    if bool(draft.code) and bool(draft.script_path):
        raise RequestValidationError(
            "Exactly one of code/script_path is required; both were supplied."
        )
    if not draft.code and not draft.script_path:
        raise RequestValidationError(
            "Exactly one of code/script_path is required; neither was supplied."
        )
    if not draft.working_directory:
        raise RequestValidationError("working_directory is required.")
    if not draft.executable_path:
        raise RequestValidationError("executable_path is required.")
    if draft.timeout_seconds is None or draft.timeout_seconds <= 0:
        raise RequestValidationError(
            "timeout_seconds must be a positive number, explicitly supplied "
            "(this module never relies on the real helper's own default)."
        )
    if draft.environment_summary is None:
        raise RequestValidationError("environment_summary is required before canonicalization.")
    if draft.safety_review is None:
        raise RequestValidationError("safety_review is required before canonicalization.")

    request = CanonicalExecutionRequest(
        request_id=draft.request_id,
        code=draft.code,
        script_path=draft.script_path,
        working_directory=draft.working_directory,
        output_directory=draft.output_directory,
        executable_path=draft.executable_path,
        timeout_seconds=float(draft.timeout_seconds),
        expected_input_files=tuple(draft.expected_input_files),
        expected_output_files=tuple(draft.expected_output_files),
        required_packages=tuple(draft.required_packages),
        allow_output_files=bool(draft.allow_output_files),
        execution_purpose=draft.execution_purpose,
        environment_summary=draft.environment_summary,
        safety_review=draft.safety_review,
        request_hash="",
    )
    request.request_hash = compute_request_hash(request)
    request.freeze()
    return request


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------


class OrchestrationState(enum.Enum):
    ADVISORY = "advisory"
    COLLECTING_INPUTS = "collecting_inputs"
    PROPOSED = "proposed"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    CONFIRMED = "confirmed"
    EXECUTING = "executing"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    ANALYZING = "analyzing"
    REPORT_GENERATING = "report_generating"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


TERMINAL_STATES = frozenset(
    {OrchestrationState.COMPLETED, OrchestrationState.CANCELLED, OrchestrationState.BLOCKED}
)

# The 18 valid intra-instance transitions. This corrects a discrepancy found
# during implementation: planning/v0.31.0-runtime-state-machine-contract.md's
# original transition inventory (17 transitions) omitted `confirmed ->
# cancelled` (needed for both pre-launch cancellation, Section 10, and
# session-boundary invalidation of an already-confirmed instance, Section
# 11's "Session boundary / expired confirmation" row) -- see this module's
# final report and the corresponding fix applied to that document.
VALID_TRANSITIONS: dict[OrchestrationState, frozenset[OrchestrationState]] = {
    OrchestrationState.ADVISORY: frozenset(
        {OrchestrationState.COLLECTING_INPUTS, OrchestrationState.PROPOSED}
    ),
    OrchestrationState.COLLECTING_INPUTS: frozenset(
        {OrchestrationState.PROPOSED, OrchestrationState.BLOCKED, OrchestrationState.CANCELLED}
    ),
    OrchestrationState.PROPOSED: frozenset({OrchestrationState.AWAITING_CONFIRMATION}),
    OrchestrationState.AWAITING_CONFIRMATION: frozenset(
        {
            OrchestrationState.CONFIRMED,
            OrchestrationState.CANCELLED,
            OrchestrationState.COLLECTING_INPUTS,
        }
    ),
    OrchestrationState.CONFIRMED: frozenset(
        {OrchestrationState.EXECUTING, OrchestrationState.CANCELLED}
    ),
    OrchestrationState.EXECUTING: frozenset(
        {OrchestrationState.EXECUTION_COMPLETED, OrchestrationState.EXECUTION_FAILED}
    ),
    OrchestrationState.EXECUTION_COMPLETED: frozenset({OrchestrationState.ANALYZING}),
    OrchestrationState.EXECUTION_FAILED: frozenset({OrchestrationState.ANALYZING}),
    OrchestrationState.ANALYZING: frozenset(
        {OrchestrationState.REPORT_GENERATING, OrchestrationState.COMPLETED}
    ),
    OrchestrationState.REPORT_GENERATING: frozenset({OrchestrationState.COMPLETED}),
    OrchestrationState.COMPLETED: frozenset(),
    OrchestrationState.CANCELLED: frozenset(),
    OrchestrationState.BLOCKED: frozenset(),
}


class InvalidTransitionError(Exception):
    """Raised when a transition is not present in VALID_TRANSITIONS for the
    current state -- a structural adjacency failure."""


class GuardFailedError(Exception):
    """Raised when a transition is structurally adjacent but a specific
    guard condition (state-machine contract Section 6) fails."""


class DuplicateInvocationError(Exception):
    """Raised when a second invocation is attempted for a request that has
    already authorized one (state-machine contract Section 8, Invariant 3)."""


class AnalysisNotAllowedError(Exception):
    """Raised when analysis is attempted on a malformed result (state-machine
    contract Section 12, Invariant 17)."""


class SessionMismatchError(Exception):
    """Raised when a confirmation event's session does not match this
    instance's session."""


# --- Confirmation, invocation, and outcome enums ---------------------------


class ConfirmationStatus(enum.Enum):
    NONE = "none"
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    STALE = "stale"
    INVALIDATED = "invalidated"
    CONSUMED = "consumed"
    EXPIRED = "expired"


class HelperInvocationStatus(enum.Enum):
    NOT_INVOKED = "not_invoked"
    IN_PROGRESS = "in_progress"
    RETURNED = "returned"
    FAILED_TO_LAUNCH = "failed_to_launch"


class CancellationStatus(enum.Enum):
    NOT_CANCELLED = "not_cancelled"
    CANCEL_REQUESTED_DURING_INVOCATION = "cancel_requested_during_invocation"
    CANCELLATION_ACKNOWLEDGED = "cancellation_acknowledged"


class AnalysisStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ReportStatus(enum.Enum):
    NOT_REQUESTED = "not_requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class FailureCategory(enum.Enum):
    """The 22 failure categories this mock controller can represent and
    route (planning/v0.31.0-runtime-orchestration-design.md's Failure
    Taxonomy, matched against the state-machine contract's Section 11)."""

    MISSING_INPUTS = "missing_inputs"
    INELIGIBLE_REQUEST = "ineligible_request"
    UNSAFE_REQUEST = "unsafe_request"
    CONFIRMATION_REJECTED = "confirmation_rejected"
    CONFIRMATION_MISSING = "confirmation_missing"
    CONFIRMATION_STALE = "confirmation_stale"
    CONFIRMATION_INVALIDATED = "confirmation_invalidated"
    CONFIRMATION_EXPIRED = "confirmation_expired"
    SESSION_MISMATCH = "session_mismatch"
    SCRIPT_IDENTITY_UNTRUSTED = "script_identity_untrusted"
    ENVIRONMENT_MISMATCH = "environment_mismatch"
    DUPLICATE_INVOCATION = "duplicate_invocation"
    RUNNER_UNAVAILABLE = "runner_unavailable"
    RUNNER_LAUNCH_FAILURE = "runner_launch_failure"
    TIMEOUT = "timeout"
    GAUSS_RUNTIME_ERROR = "gauss_runtime_error"
    MALFORMED_RESULT = "malformed_result"
    MISSING_EXPECTED_OUTPUT = "missing_expected_output"
    CANCELLATION_BEFORE_EXECUTION = "cancellation_before_execution"
    CANCELLATION_DURING_EXECUTION = "cancellation_during_execution"
    ANALYSIS_FAILURE = "analysis_failure"
    REPORT_GENERATION_FAILURE = "report_generation_failure"


# ---------------------------------------------------------------------------
# Fake result shape and validation (no real schema/helper import)
# ---------------------------------------------------------------------------

_VALID_EXECUTION_STATUSES = frozenset(
    {"completed", "failed", "timed_out", "blocked", "skipped", "error", "unknown"}
)


@dataclass(frozen=True)
class OutputFileMeta:
    """Metadata only -- deliberately has no 'content' field, so this type
    cannot be used to carry file content even by accident."""

    path: str
    size_bytes: int | None
    file_type: str | None
    created_by_execution: Any  # True / False / "unknown" tri-state
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class MockExecutionResult:
    executed: bool
    execution_status: str
    exit_code: int | None
    stdout: str
    stderr: str
    output_files: tuple[OutputFileMeta, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ResultValidation:
    is_structurally_valid: bool
    problems: tuple[str, ...] = ()


def validate_fake_result(raw: dict[str, Any]) -> ResultValidation:
    """Minimal structural validation distinguishing a structurally valid
    completed/failure/timeout result from a malformed one. Deliberately
    smaller than the full production schema (schemas/gauss_code_execution.schema.json,
    which is never imported here) -- only the subset of fields this mock
    controller's own routing logic depends on."""
    problems: list[str] = []
    required_keys = (
        "executed",
        "execution_status",
        "exit_code",
        "stdout",
        "stderr",
        "output_files",
        "warnings",
        "errors",
    )
    for key in required_keys:
        if key not in raw:
            problems.append(f"missing required key: {key}")

    if "executed" in raw and not isinstance(raw["executed"], bool):
        problems.append("'executed' must be a boolean")

    if "execution_status" in raw and raw["execution_status"] not in _VALID_EXECUTION_STATUSES:
        problems.append(
            f"'execution_status' value {raw.get('execution_status')!r} is not a recognized status"
        )

    if "output_files" in raw:
        if not isinstance(raw["output_files"], list):
            problems.append("'output_files' must be a list")
        else:
            for i, entry in enumerate(raw["output_files"]):
                if not isinstance(entry, dict) or "path" not in entry:
                    problems.append(f"output_files[{i}] must be an object with at least a 'path' key")
                elif "content" in entry:
                    # Structural guard: output metadata must never carry file
                    # content (Invariant 9).
                    problems.append(f"output_files[{i}] must not include file content")

    return ResultValidation(is_structurally_valid=not problems, problems=tuple(problems))


def _to_mock_result(raw: dict[str, Any]) -> MockExecutionResult:
    output_files = tuple(
        OutputFileMeta(
            path=f["path"],
            size_bytes=f.get("size_bytes"),
            file_type=f.get("file_type"),
            created_by_execution=f.get("created_by_execution", "unknown"),
            notes=tuple(f.get("notes", ())),
        )
        for f in raw.get("output_files", [])
    )
    return MockExecutionResult(
        executed=bool(raw["executed"]),
        execution_status=raw["execution_status"],
        exit_code=raw.get("exit_code"),
        stdout=raw.get("stdout") or "",
        stderr=raw.get("stderr") or "",
        output_files=output_files,
        warnings=tuple(raw.get("warnings", ())),
        errors=tuple(raw.get("errors", ())),
    )


def _missing_expected_outputs(
    request: CanonicalExecutionRequest, result: MockExecutionResult
) -> tuple[str, ...]:
    """Compare declared expected_output_files against the result's actual
    output_files by basename, not by exact string equality.

    expected_output_files is documented (canonical request contract, field 9)
    as "descriptive, not paths the helper validates" -- a free-form filename
    the user was told to expect, not a path the caller can be expected to
    predict exactly. The helper's own output-file discovery
    (scripts/gauss_code_execution.py's _discover_output_files) always returns
    absolute filesystem paths. A caller declaring the bare filename it was
    told to expect (e.g. "results.csv") must still be recognized as present
    when the actual result reports it at its real, absolute location (e.g.
    "C:\\...\\results.csv") -- v0.35.0 real-invocation testing found the
    prior exact-string comparison always misclassified a genuinely-created,
    correctly-discovered file as missing whenever expected_output_files used
    a bare filename, which is the documented, expected way to declare one.
    Basename comparison is tolerant of this without weakening detection: a
    truly absent file still has no discovered output whose basename matches.
    """
    actual_basenames = {Path(f.path).name for f in result.output_files}
    return tuple(f for f in request.expected_output_files if Path(f).name not in actual_basenames)


# ---------------------------------------------------------------------------
# Runner boundary (fake only)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunnerInput:
    """A narrow projection of the canonical request -- deliberately does not
    expose safety_review/confirmation internals to the runner boundary.

    `gauss_version`, `expected_input_files`, and `required_packages` were
    added in v0.32.0 Phase 3 (Increment 1) so this same projection can drive
    either a test fake runner (which may ignore them, as every pre-existing
    test already does) or `AdapterRunner`'s bridge to
    gauss_execution_adapter.AdapterRequest, without widening the runner
    boundary to expose safety_review/confirmation internals."""

    code: str | None
    script_path: str | None
    working_directory: str
    output_directory: str | None
    executable_path: str
    timeout_seconds: float
    allow_output_files: bool
    gauss_version: str | None = None
    expected_input_files: tuple[str, ...] = ()
    required_packages: tuple[str, ...] = ()


class FakeRunner(Protocol):
    """The injected runner boundary. A real implementation of this protocol
    is NEVER provided by this module -- callers (in practice, tests) supply
    one. This module never imports scripts/gauss_code_execution.py and never
    launches a subprocess itself."""

    def __call__(self, runner_input: RunnerInput) -> dict[str, Any]: ...


class AdapterRunner:
    """Bridges a `gauss_execution_adapter.GaussExecutionAdapter` into this
    controller's FakeRunner boundary (`MockOrchestrationInstance.invoke`'s
    `runner` parameter). Structurally satisfies FakeRunner -- it can be
    passed to `invoke(...)` exactly like a test's fake-runner lambda, with
    zero changes to `invoke`'s own logic.

    This class never selects, imports, or constructs a real helper itself --
    the `adapter` passed to `__init__` must already be fully constructed by
    the caller, with whatever helper callable the caller chose (a fake
    helper in every test in this repository as of this revision; a real one
    only via a future, separately authorized caller that explicitly invokes
    `gauss_execution_adapter.load_real_helper()` -- never automatically).

    Any adapter-level pre-invocation rejection (`AdapterOutcome.invoked` is
    `False` -- e.g. a race where the environment changed between this
    controller's own `check_environment_before_invocation()` call and the
    actual attempt) is raised here as an exception, which `invoke()` already
    treats as a `RUNNER_LAUNCH_FAILURE`. This is the correct classification,
    not a bug: by the time `invoke()` calls this bridge, confirmation has
    already been consumed (per the atomic-consumption rule) -- an
    adapter-level rejection discovered only at the moment of the attempted
    call is therefore a launch failure, not a pre-authorization guard
    failure. Callers are expected to have already run this controller's own
    script-path (`submit_for_review`) and environment-mismatch
    (`check_environment_before_invocation`) checks before ever reaching
    `invoke()` -- this bridge's own adapter-level checks are defense in
    depth for a race or a caller that skipped those steps, not the primary
    enforcement point.
    """

    def __init__(
        self, adapter: "gauss_execution_adapter.GaussExecutionAdapter", *, request_identity: str
    ) -> None:
        self._adapter = adapter
        self._request_identity = request_identity

    def __call__(self, runner_input: RunnerInput) -> dict[str, Any]:
        adapter_request = gauss_execution_adapter.AdapterRequest(
            request_identity=self._request_identity,
            code=runner_input.code,
            script_path=runner_input.script_path,
            working_directory=runner_input.working_directory,
            output_directory=runner_input.output_directory,
            executable_path=runner_input.executable_path,
            gauss_version=runner_input.gauss_version,
            timeout_seconds=runner_input.timeout_seconds,
            expected_input_files=runner_input.expected_input_files,
            required_packages=runner_input.required_packages,
            allow_output_files=runner_input.allow_output_files,
            package_inspection_result=None,
        )
        outcome = self._adapter.invoke(adapter_request)
        if not outcome.invoked:
            category = outcome.failure_category.value if outcome.failure_category else "unknown"
            raise RuntimeError(
                f"Helper Adapter rejected this invocation before calling the helper "
                f"({category}): {outcome.rejection_reason}"
            )
        assert outcome.raw_result is not None
        return outcome.raw_result


def build_production_adapter_runner(
    *,
    request_identity: str,
    environment_probe: Callable[[str], bool] | None = None,
) -> AdapterRunner:
    """The ONE narrow, explicit factory in this module that can result in a
    real GAUSS invocation (v0.33.0, Controlled Real Execution Integration).

    Calling this function is the only way this module's own code can reach
    the real helper -- it must be called explicitly, by name, by a caller
    that has already completed its own confirmation/eligibility/safety
    review. It is never called by `MockOrchestrationInstance`'s own
    construction, by `invoke(...)`'s default behavior, by any test in this
    repository's default suite, or merely because GAUSS happens to be
    installed on the current machine -- installed-ness is not consulted by
    this function at all; it only constructs the object graph.

    This function calls exactly two things: `gauss_execution_adapter.load_real_helper()`
    (the adapter's own lazy, explicit real-helper factory -- see that
    module's docstring) and `gauss_execution_adapter.GaussExecutionAdapter(...)`.
    It does not call `execute_gauss_code(...)` itself, does not launch a
    subprocess itself, and does not detect a GAUSS environment itself --
    every one of those remains the adapter's and the real helper's own
    responsibility, unchanged by this factory's existence.
    """
    real_helper = gauss_execution_adapter.load_real_helper()
    adapter = gauss_execution_adapter.GaussExecutionAdapter(
        helper=real_helper, environment_probe=environment_probe
    )
    return AdapterRunner(adapter, request_identity=request_identity)


# ---------------------------------------------------------------------------
# Confirmation event (explicit, no natural-language detection)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConfirmationEvent:
    """An explicit, already-classified confirmation event -- this module
    never attempts to parse or infer confirmation from natural language."""

    scope: str
    timestamp: str
    session_id: str


# ---------------------------------------------------------------------------
# Orchestration record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransitionEvent:
    sequence_number: int
    from_state: OrchestrationState
    to_state: OrchestrationState
    at: float
    note: str = ""


@dataclass
class OrchestrationRecord:
    """The state-owned data record (state-machine contract Section 3).
    Deliberately narrower than the full 19-item conceptual list: it omits an
    independent `session_identifier` *source* mechanism (a session_id string
    is accepted as given, per Open Decisions) and does not implement a
    separate durable `orchestration_instance_id` persistence layer -- both
    remain implementation-deferred per the contract's own Section 21.
    """

    orchestration_instance_id: str
    session_id: str
    current_state: OrchestrationState
    previous_state: OrchestrationState | None = None
    canonical_request_id: str | None = None
    request_hash: str | None = None
    confirmation_status: ConfirmationStatus = ConfirmationStatus.NONE
    confirmation_event_reference: str | None = None
    confirmation_consumption_status: bool = False
    helper_invocation_status: HelperInvocationStatus = HelperInvocationStatus.NOT_INVOKED
    helper_invocation_id: str | None = None
    execution_result_reference: MockExecutionResult | None = None
    validation_outcome: ResultValidation | None = None
    failure_category: FailureCategory | None = None
    cancellation_status: CancellationStatus = CancellationStatus.NOT_CANCELLED
    analysis_status: AnalysisStatus = AnalysisStatus.NOT_STARTED
    report_status: ReportStatus = ReportStatus.NOT_REQUESTED
    transition_sequence_number: int = 0
    created_at: float = 0.0
    last_transition_at: float = 0.0
    transition_log: list[TransitionEvent] = field(default_factory=list)

    def to_safe_summary(self) -> dict[str, Any]:
        """An audit-safe summary excluding code, secrets, credentials,
        environment-variable values, raw conversation text, and file
        contents -- only identifiers, hashes, and statuses."""
        return {
            "orchestration_instance_id": self.orchestration_instance_id,
            "session_id": self.session_id,
            "current_state": self.current_state.value,
            "previous_state": self.previous_state.value if self.previous_state else None,
            "canonical_request_id": self.canonical_request_id,
            "request_hash": self.request_hash,
            "confirmation_status": self.confirmation_status.value,
            "confirmation_consumption_status": self.confirmation_consumption_status,
            "helper_invocation_status": self.helper_invocation_status.value,
            "helper_invocation_id": self.helper_invocation_id,
            "validation_outcome": (
                {
                    "is_structurally_valid": self.validation_outcome.is_structurally_valid,
                    "problems": list(self.validation_outcome.problems),
                }
                if self.validation_outcome is not None
                else None
            ),
            "failure_category": self.failure_category.value if self.failure_category else None,
            "cancellation_status": self.cancellation_status.value,
            "analysis_status": self.analysis_status.value,
            "report_status": self.report_status.value,
            "transition_sequence_number": self.transition_sequence_number,
            "created_at": self.created_at,
            "last_transition_at": self.last_transition_at,
            "transition_count": len(self.transition_log),
        }


# ---------------------------------------------------------------------------
# Mock orchestration instance (one per canonical request)
# ---------------------------------------------------------------------------


class MockOrchestrationInstance:
    """A single, in-memory, mock-only orchestration instance governing
    exactly one Canonical Execution Request's lifecycle, per the state
    machine contract's Section 1 ("one orchestration instance corresponds to
    exactly one request" in this design).

    Never imports or calls scripts/gauss_code_execution.py. Never launches a
    subprocess. Never detects a real GAUSS environment.
    """

    def __init__(
        self,
        *,
        session_id: str,
        draft: RequestDraft,
        clock: Callable[[], float] = time.monotonic,
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
        state_store: "state_store_mod.OrchestrationStateStore | None" = None,
        orchestration_instance_id: str | None = None,
    ) -> None:
        """`state_store` is optional and defaults to None, preserving this
        class's original, fully in-memory-only behavior for every existing
        caller and test unchanged. When a store IS supplied, every state
        mutation this instance performs is also durably persisted through
        that one store -- see `build_durable_orchestration_instance(...)`
        for the explicit, named "production construction" entry point that
        requires a store (mirroring `build_production_adapter_runner(...)`'s
        own explicitness convention).

        `orchestration_instance_id` lets a caller supply a pre-existing ID
        (used by `reload_orchestration_instance(...)` to reconstruct an
        in-memory view of an already-durable record after a process
        restart); when omitted, a fresh ID is generated as before."""
        self._clock = clock
        self._id_factory = id_factory
        self._state_store = state_store
        self.draft = draft
        self.request: CanonicalExecutionRequest | None = None
        now = self._clock()
        self.record = OrchestrationRecord(
            orchestration_instance_id=orchestration_instance_id or id_factory(),
            session_id=session_id,
            current_state=OrchestrationState.COLLECTING_INPUTS,
            canonical_request_id=draft.request_id,
            created_at=now,
            last_transition_at=now,
        )
        if self._state_store is not None:
            self._state_store.create_record(
                orchestration_instance_id=self.record.orchestration_instance_id,
                session_id=session_id,
                canonical_request_id=draft.request_id,
                current_state=OrchestrationState.COLLECTING_INPUTS.value,
                created_at=now,
            )

    # -- internal transition primitive --------------------------------------

    def _transition(
        self,
        target: OrchestrationState,
        *,
        note: str = "",
        extra_fields: dict[str, Any] | None = None,
        sync_to_store: bool = True,
    ) -> None:
        current = self.record.current_state
        allowed = VALID_TRANSITIONS.get(current, frozenset())
        if target not in allowed:
            raise InvalidTransitionError(f"{current.value} -> {target.value} is not a valid transition.")
        expected_seq = self.record.transition_sequence_number
        now = self._clock()
        self.record.transition_log.append(
            TransitionEvent(
                sequence_number=expected_seq,
                from_state=current,
                to_state=target,
                at=now,
                note=note,
            )
        )
        self.record.transition_sequence_number += 1
        self.record.previous_state = current
        self.record.current_state = target
        self.record.last_transition_at = now
        if sync_to_store and self._state_store is not None:
            self._state_store.transition(
                self.record.orchestration_instance_id,
                to_state=target.value,
                note=note,
                expected_transition_sequence_number=expected_seq,
                extra_fields=extra_fields,
            )

    def _sync_extra(self, **fields: Any) -> None:
        """Pushes a non-transitioning field update (one that does not
        accompany a state change) to the durable store, when one is
        present. A no-op in the default, in-memory-only mode."""
        if self._state_store is not None and fields:
            self._state_store.update_fields(
                self.record.orchestration_instance_id,
                expected_transition_sequence_number=self.record.transition_sequence_number,
                **fields,
            )

    def _force_complete(self, *, note: str, extra_fields: dict[str, Any] | None = None) -> None:
        """A cancellation-only shortcut from a post-execution state directly
        to `completed`, bypassing the ordinary adjacency table -- this is a
        deliberate, distinct cancellation path (state-machine contract
        Section 10: "can only stop downstream work"), not a violation of the
        normal transition rules, which govern the non-cancellation flow."""
        expected_seq = self.record.transition_sequence_number
        now = self._clock()
        current = self.record.current_state
        self.record.transition_log.append(
            TransitionEvent(
                sequence_number=expected_seq,
                from_state=current,
                to_state=OrchestrationState.COMPLETED,
                at=now,
                note=f"cancellation shortcut: {note}",
            )
        )
        self.record.transition_sequence_number += 1
        self.record.previous_state = current
        self.record.current_state = OrchestrationState.COMPLETED
        self.record.last_transition_at = now
        if self._state_store is not None:
            self._state_store.transition(
                self.record.orchestration_instance_id,
                to_state="completed",
                note=f"cancellation shortcut: {note}",
                expected_transition_sequence_number=expected_seq,
                extra_fields=extra_fields,
            )

    # -- eligibility / safety / proposal --------------------------------------

    def block(self, category: FailureCategory, reason: str) -> None:
        """Record a blocking outcome and transition to `blocked`.

        This module does not implement the full Eligibility Evaluator /
        Safety Review rule engines from workflows/real-execution-user-workflow.md
        -- callers (tests) simulate their *outcome* by calling this directly,
        or indirectly via submit_for_review()'s own structural checks.
        """
        self.record.failure_category = category
        self._transition(OrchestrationState.BLOCKED, note=reason, extra_fields={"failure_category": category.value})

    def mark_runner_unavailable(self, reason: str) -> None:
        if self.record.current_state != OrchestrationState.COLLECTING_INPUTS:
            raise InvalidTransitionError("mark_runner_unavailable is only valid from collecting_inputs.")
        self.block(FailureCategory.RUNNER_UNAVAILABLE, reason)

    def submit_for_review(self) -> None:
        """Attempt collecting_inputs -> proposed for a (believed) complete
        draft. Fails closed to `blocked` for every ineligible/unsafe/
        incomplete case, per submit order: script-identity policy first
        (fail-closed regardless of other fields), then safety, then
        structural validation via build_canonical_request."""
        if self.record.current_state != OrchestrationState.COLLECTING_INPUTS:
            raise InvalidTransitionError("submit_for_review is only valid from collecting_inputs.")

        if self.draft.script_path is not None and not self.draft.code:
            # Fail-closed script-identity policy (Option 1, chosen in the
            # final report): script-path mode is never eligible for mock
            # execution in this phase -- there is no trustworthy mechanism
            # to confirm the on-disk script still matches what would be
            # shown at confirmation time (canonical request contract's
            # documented, unresolved script-fingerprinting gap).
            self.block(
                FailureCategory.SCRIPT_IDENTITY_UNTRUSTED,
                "script-path mode is not eligible for mock execution: no trustworthy "
                "script-identity mechanism exists in this phase.",
            )
            return

        if self.draft.safety_review is not None and not self.draft.safety_review.passed:
            self.block(FailureCategory.UNSAFE_REQUEST, "safety review did not pass")
            return

        try:
            candidate = build_canonical_request(self.draft)
        except RequestValidationError as exc:
            category = FailureCategory.MISSING_INPUTS
            if "Exactly one of code/script_path" in str(exc):
                category = FailureCategory.INELIGIBLE_REQUEST
            self.block(category, str(exc))
            return

        self.request = candidate
        self.record.request_hash = self.request.request_hash
        self._transition(
            OrchestrationState.PROPOSED,
            note="eligibility and safety review passed",
            extra_fields={
                "request_hash": self.request.request_hash,
                "code_digest": state_store_mod.digest_code(self.request.code),
            },
        )

    # -- confirmation ---------------------------------------------------------

    def display_plan(self) -> None:
        if self.record.current_state != OrchestrationState.PROPOSED:
            raise InvalidTransitionError("display_plan is only valid from proposed.")
        self.record.confirmation_status = ConfirmationStatus.REQUESTED
        self._transition(
            OrchestrationState.AWAITING_CONFIRMATION, note="plan displayed",
            extra_fields={"confirmation_status": "requested"},
        )

    def confirm(self, event: ConfirmationEvent) -> None:
        """user_confirmed=true alone is never sufficient: this also requires
        confirmation_scope == request_hash (checked inside
        CanonicalExecutionRequest.attach_confirmation) and a matching
        session_id (checked here). When a durable store is present, the
        store's own atomic `record_confirmation(...)` is the authoritative
        check and commit -- it happens first, and the in-memory mutation
        below only mirrors it (`sync_to_store=False` on the transition call
        below, avoiding a second, redundant durable write)."""
        if self.record.current_state != OrchestrationState.AWAITING_CONFIRMATION:
            raise InvalidTransitionError("confirm is only valid from awaiting_confirmation.")
        if self.request is None:
            # Fail closed: recovered/incomplete state must never be treated
            # as confirmable (state-machine contract Section 15).
            raise GuardFailedError("No canonical request is attached to this instance; cannot confirm.")

        if event.session_id != self.record.session_id:
            self.record.confirmation_status = ConfirmationStatus.STALE
            self.record.failure_category = FailureCategory.SESSION_MISMATCH
            raise SessionMismatchError("Confirmation session does not match this instance's session.")

        if event.scope != self.request.request_hash:
            self.record.confirmation_status = ConfirmationStatus.STALE
            self.record.failure_category = FailureCategory.CONFIRMATION_STALE
            raise ConfirmationScopeMismatchError(
                "Confirmation scope does not match the current request hash."
            )

        if self._state_store is not None:
            try:
                self._state_store.record_confirmation(
                    self.record.orchestration_instance_id,
                    scope=event.scope,
                    timestamp=event.timestamp,
                    session_id=event.session_id,
                    expected_request_hash=self.request.request_hash,
                    expected_transition_sequence_number=self.record.transition_sequence_number,
                )
            except state_store_mod.DurableStateError as exc:
                self.record.confirmation_status = ConfirmationStatus.STALE
                raise GuardFailedError(f"durable confirmation recording failed, refusing to confirm: {exc}") from exc

        self.request.attach_confirmation(
            confirmation_scope=event.scope, confirmation_timestamp=event.timestamp
        )
        self.record.confirmation_status = ConfirmationStatus.ACCEPTED
        self.record.confirmation_event_reference = event.timestamp
        self._transition(OrchestrationState.CONFIRMED, note="confirmation accepted", sync_to_store=False)

    def reject_confirmation(self) -> None:
        if self.record.current_state != OrchestrationState.AWAITING_CONFIRMATION:
            raise InvalidTransitionError("reject_confirmation is only valid from awaiting_confirmation.")
        self.record.confirmation_status = ConfirmationStatus.REJECTED
        self.record.failure_category = FailureCategory.CONFIRMATION_REJECTED
        self._transition(
            OrchestrationState.CANCELLED, note="user declined",
            extra_fields={"confirmation_status": "rejected", "failure_category": "confirmation_rejected"},
        )

    def edit_before_confirmation(self, **changes: Any) -> None:
        """A pre-confirmation edit -- same instance, per the state-machine
        contract's resolution that this differs from a post-confirmation
        change (which always requires a wholly new instance)."""
        if self.record.current_state != OrchestrationState.AWAITING_CONFIRMATION:
            raise InvalidTransitionError("edit_before_confirmation is only valid from awaiting_confirmation.")
        for key, value in changes.items():
            setattr(self.draft, key, value)
        self.request = None
        self.record.request_hash = None
        self.record.confirmation_status = ConfirmationStatus.INVALIDATED
        self._transition(
            OrchestrationState.COLLECTING_INPUTS, note="pre-confirmation edit",
            extra_fields={"confirmation_status": "invalidated", "request_hash": None},
        )

    def invalidate_for_session_boundary(self) -> None:
        """Represents a resumed session where prior confirmation state must
        not be trusted. From `awaiting_confirmation`, no confirmation was
        accepted yet, so the same instance may re-enter `collecting_inputs`.
        From `confirmed`, confirmation *was* accepted and is immutable
        (Section 7 of the state-machine contract) -- so this instance is
        abandoned (-> cancelled) instead, and a fresh cycle requires a new
        instance. See this module's final report for the contract
        inconsistency this resolves."""
        state = self.record.current_state
        if state == OrchestrationState.AWAITING_CONFIRMATION:
            self.record.confirmation_status = ConfirmationStatus.EXPIRED
            self._transition(
                OrchestrationState.COLLECTING_INPUTS,
                note="session boundary before confirmation; same instance, fresh cycle",
                extra_fields={"confirmation_status": "expired"},
            )
            return
        if state == OrchestrationState.CONFIRMED:
            self.record.confirmation_status = ConfirmationStatus.EXPIRED
            self.record.failure_category = FailureCategory.CONFIRMATION_EXPIRED
            self._transition(
                OrchestrationState.CANCELLED,
                note="session boundary after confirmation; instance abandoned, new request required",
                extra_fields={"confirmation_status": "expired", "failure_category": "confirmation_expired"},
            )
            return
        raise InvalidTransitionError(
            "invalidate_for_session_boundary is only valid from awaiting_confirmation/confirmed."
        )

    def check_environment_before_invocation(self, *, still_matches: bool) -> None:
        """Represents the pre-invocation `environment_still_matches` guard
        (state-machine contract Section 11, stage 11)."""
        if self.record.current_state != OrchestrationState.CONFIRMED:
            raise InvalidTransitionError("check_environment_before_invocation is only valid from confirmed.")
        if not still_matches:
            self.record.failure_category = FailureCategory.ENVIRONMENT_MISMATCH
            self._transition(
                OrchestrationState.CANCELLED,
                note="environment no longer matches the confirmed plan; fail closed",
                extra_fields={"failure_category": "environment_mismatch"},
            )

    # -- cancellation -----------------------------------------------------------

    def cancel(self, *, note: str = "") -> None:
        state = self.record.current_state
        if state in TERMINAL_STATES:
            raise InvalidTransitionError(f"Cannot cancel a terminal instance ({state.value}).")

        if state == OrchestrationState.EXECUTING:
            # The synchronous fake call cannot be interrupted -- this only
            # records intent; it does not stop or claim to stop the call.
            self.record.cancellation_status = CancellationStatus.CANCEL_REQUESTED_DURING_INVOCATION
            self.record.failure_category = FailureCategory.CANCELLATION_DURING_EXECUTION
            self._sync_extra(
                cancellation_status="cancel_requested_during_invocation",
                failure_category="cancellation_during_execution",
            )
            return

        if state in (
            OrchestrationState.EXECUTION_COMPLETED,
            OrchestrationState.EXECUTION_FAILED,
            OrchestrationState.ANALYZING,
            OrchestrationState.REPORT_GENERATING,
        ):
            self.record.cancellation_status = CancellationStatus.CANCELLATION_ACKNOWLEDGED
            extra_fields: dict[str, Any] = {"cancellation_status": "cancellation_acknowledged"}
            if self.record.analysis_status == AnalysisStatus.NOT_STARTED:
                self.record.analysis_status = AnalysisStatus.SKIPPED
                extra_fields["analysis_status"] = "skipped"
            self._force_complete(note=note or "cancelled downstream of execution", extra_fields=extra_fields)
            return

        # Pre-invocation cancellation: collecting_inputs / proposed /
        # awaiting_confirmation / confirmed (not yet launched).
        self.record.failure_category = FailureCategory.CANCELLATION_BEFORE_EXECUTION
        self.record.cancellation_status = CancellationStatus.CANCELLATION_ACKNOWLEDGED
        self._transition(
            OrchestrationState.CANCELLED, note=note or "user cancelled before execution",
            extra_fields={"failure_category": "cancellation_before_execution", "cancellation_status": "cancellation_acknowledged"},
        )

    # -- invocation (exactly once) ----------------------------------------------

    def invoke(self, runner: FakeRunner) -> None:
        """Authorize and perform exactly one fake invocation.

        Only valid from `confirmed`. Confirmation is consumed atomically
        with authorization -- before the runner is actually called, not
        merely "logically before" -- and a launch failure (the runner
        raising) still consumes it; a second call for the same request_hash
        is refused outright (DuplicateInvocationError) without touching the
        original invocation's state.

        When a durable store is present, `state_store.authorize_invocation(
        ...)` is called FIRST and must durably commit before this method
        does anything else -- in particular, before the runner is ever
        called. This is the one hard requirement this milestone exists to
        satisfy: the controller can never invoke first and persist
        afterward. If durable authorization fails for any reason (already
        invoked, expired confirmation, hash/session mismatch, a lost race
        with a concurrent writer, or lock contention), the corresponding
        in-memory exception is raised immediately and neither the in-memory
        state nor the runner is ever touched.
        """
        if self.record.current_state != OrchestrationState.CONFIRMED:
            raise InvalidTransitionError("invoke is only valid from confirmed.")
        if self.request is None:
            # Fail closed: recovered/incomplete state must never authorize
            # invocation (state-machine contract Section 15).
            raise GuardFailedError("No canonical request is attached to this instance; cannot invoke.")

        if not self.request.user_confirmed or self.request.confirmation_scope != self.request.request_hash:
            # Fail closed: user_confirmed=true alone is never sufficient.
            raise GuardFailedError(
                "genuine_confirmation_evidence guard failed: confirmation is not valid for this request."
            )

        if self.record.helper_invocation_id is not None:
            raise DuplicateInvocationError(
                f"Request {self.request.request_hash} has already authorized one invocation "
                f"({self.record.helper_invocation_id}); a second invocation is refused."
            )

        invocation_id = self._id_factory()

        if self._state_store is not None:
            try:
                self._state_store.authorize_invocation(
                    self.record.orchestration_instance_id,
                    request_hash=self.request.request_hash,
                    confirmation_scope=self.request.confirmation_scope,
                    session_id=self.record.session_id,
                    invocation_id=invocation_id,
                    expected_transition_sequence_number=self.record.transition_sequence_number,
                )
            except state_store_mod.AuthorizationFailedError as exc:
                if exc.reason_category == "already_invoked":
                    raise DuplicateInvocationError(f"durable authorization refused: {exc}") from exc
                if exc.reason_category == "session_mismatch":
                    raise SessionMismatchError(f"durable authorization refused: {exc}") from exc
                raise GuardFailedError(f"durable authorization refused: {exc}") from exc
            except state_store_mod.StaleTransitionError as exc:
                raise GuardFailedError(f"durable authorization refused (stale durable state): {exc}") from exc
            except state_store_mod.LockContentionError as exc:
                raise GuardFailedError(f"durable authorization could not acquire the write lock: {exc}") from exc

        # Atomic with authorization: record invocation identity and consume
        # confirmation together, immediately before transitioning/calling.
        # When a store is present, the durable commit above has ALREADY made
        # this exclusive -- this in-memory mutation only mirrors it.
        self.record.helper_invocation_id = invocation_id
        self.record.helper_invocation_status = HelperInvocationStatus.IN_PROGRESS
        self.record.confirmation_consumption_status = True
        self.record.confirmation_status = ConfirmationStatus.CONSUMED
        self._transition(OrchestrationState.EXECUTING, note="invocation authorized", sync_to_store=False)
        # Captured once, immediately after the EXECUTING transition -- this
        # is the transition_sequence_number the durable store is at right
        # now (matching authorize_invocation's own single commit), and is
        # reused below for whichever single record_execution_result call
        # ends up applying, regardless of how many further in-memory-only
        # transitions happen first.
        result_expected_seq = self.record.transition_sequence_number

        runner_input = RunnerInput(
            code=self.request.code,
            script_path=self.request.script_path,
            working_directory=self.request.working_directory,
            output_directory=self.request.output_directory,
            executable_path=self.request.executable_path,
            timeout_seconds=self.request.timeout_seconds,
            allow_output_files=self.request.allow_output_files,
            gauss_version=self.request.environment_summary.gauss_version,
            expected_input_files=self.request.expected_input_files,
            required_packages=self.request.required_packages,
        )

        try:
            raw_result = runner(runner_input)
        except Exception as exc:  # noqa: BLE001 - simulates a launch failure, never crashes the controller
            # Launch failure still consumed confirmation above (per the
            # atomic-consumption rule) -- a retry requires a new request.
            self.record.helper_invocation_status = HelperInvocationStatus.FAILED_TO_LAUNCH
            self.record.failure_category = FailureCategory.RUNNER_LAUNCH_FAILURE
            self._transition(OrchestrationState.EXECUTION_FAILED, note=f"runner launch failed: {exc}", sync_to_store=False)
            if self._state_store is not None:
                self._state_store.record_execution_result(
                    self.record.orchestration_instance_id, to_state="execution_failed", execution_status="unknown",
                    exit_code=None, output_file_count=None, validation_ok=None, validation_problems=(),
                    failure_category="runner_launch_failure",
                    expected_transition_sequence_number=result_expected_seq,
                )
            return

        self.record.helper_invocation_status = HelperInvocationStatus.RETURNED
        validation = validate_fake_result(raw_result)
        self.record.validation_outcome = validation

        if not validation.is_structurally_valid:
            # Malformed results are terminal for this instance and never
            # enter analysis as valid evidence (Invariant 17).
            self.record.failure_category = FailureCategory.MALFORMED_RESULT
            self.record.execution_result_reference = None
            self._transition(OrchestrationState.EXECUTION_FAILED, note="malformed result", sync_to_store=False)
            if self._state_store is not None:
                raw_status = raw_result.get("execution_status") if isinstance(raw_result, dict) else None
                self._state_store.record_execution_result(
                    self.record.orchestration_instance_id, to_state="execution_failed",
                    execution_status=str(raw_status) if raw_status is not None else "unknown",
                    exit_code=None, output_file_count=None, validation_ok=False, validation_problems=validation.problems,
                    failure_category="malformed_result",
                    expected_transition_sequence_number=result_expected_seq,
                )
            return

        result = _to_mock_result(raw_result)
        self.record.execution_result_reference = result

        db_failure_category: str | None
        if result.execution_status == "completed":
            missing = _missing_expected_outputs(self.request, result)
            if missing:
                self.record.failure_category = FailureCategory.MISSING_EXPECTED_OUTPUT
                db_failure_category = "missing_expected_output"
            else:
                db_failure_category = None
            self._transition(OrchestrationState.EXECUTION_COMPLETED, note="completed", sync_to_store=False)
        elif result.execution_status == "timed_out":
            self.record.failure_category = FailureCategory.TIMEOUT
            db_failure_category = "timeout"
            self._transition(OrchestrationState.EXECUTION_FAILED, note="timed out", sync_to_store=False)
        else:
            self.record.failure_category = FailureCategory.GAUSS_RUNTIME_ERROR
            db_failure_category = "gauss_runtime_error"
            self._transition(OrchestrationState.EXECUTION_FAILED, note=f"status={result.execution_status}", sync_to_store=False)

        if self._state_store is not None:
            self._state_store.record_execution_result(
                self.record.orchestration_instance_id,
                to_state=self.record.current_state.value,
                execution_status=result.execution_status,
                exit_code=result.exit_code,
                output_file_count=len(result.output_files),
                validation_ok=True,
                validation_problems=(),
                failure_category=db_failure_category,
                expected_transition_sequence_number=result_expected_seq,
            )

    # -- analysis / reporting ----------------------------------------------------

    def begin_analysis(
        self,
        analysis_hook: Callable[[CanonicalExecutionRequest, MockExecutionResult | None], Any],
        *,
        report_requested: bool = False,
        report_hook: Callable[[AnalysisStatus], Any] | None = None,
    ) -> None:
        """Route a completed/non-malformed-failed result through an injected
        fake analysis hook, then (if requested) an injected fake report
        hook. Neither hook's failure ever rewrites
        execution_result_reference / validation_outcome / failure_category
        (Invariant 8) -- their own failures are recorded only in
        analysis_status / report_status."""
        if self.record.current_state not in (
            OrchestrationState.EXECUTION_COMPLETED,
            OrchestrationState.EXECUTION_FAILED,
        ):
            raise InvalidTransitionError(
                "begin_analysis is only valid from execution_completed/execution_failed."
            )
        if self.record.failure_category == FailureCategory.MALFORMED_RESULT:
            raise AnalysisNotAllowedError(
                "Malformed results are never routed into analysis as valid execution evidence."
            )
        if self.request is None:
            # Fail closed: recovered/incomplete state must never enter analysis.
            raise GuardFailedError("No canonical request is attached to this instance; cannot analyze.")

        self._transition(OrchestrationState.ANALYZING, note="analysis started", extra_fields={"analysis_status": "in_progress"})
        self.record.analysis_status = AnalysisStatus.IN_PROGRESS
        try:
            analysis_hook(self.request, self.record.execution_result_reference)
            self.record.analysis_status = AnalysisStatus.COMPLETED
        except Exception:  # noqa: BLE001 - analysis failure must not crash or rewrite evidence
            self.record.analysis_status = AnalysisStatus.FAILED
        self._sync_extra(analysis_status=self.record.analysis_status.value)

        if report_requested:
            self._transition(
                OrchestrationState.REPORT_GENERATING, note="report requested",
                extra_fields={"report_status": "in_progress"},
            )
            self.record.report_status = ReportStatus.IN_PROGRESS
            try:
                assert report_hook is not None
                report_hook(self.record.analysis_status)
                self.record.report_status = ReportStatus.COMPLETED
            except Exception:  # noqa: BLE001 - report failure falls back, never erases evidence
                self.record.report_status = ReportStatus.FAILED
            self._sync_extra(report_status=self.record.report_status.value)
            self._transition(OrchestrationState.COMPLETED, note="report step concluded")
        else:
            self._transition(OrchestrationState.COMPLETED, note="no report requested")


# ---------------------------------------------------------------------------
# Durable construction / reload (v0.36.0 Durable Execution State and
# Cross-Process Safety)
# ---------------------------------------------------------------------------


def build_durable_orchestration_instance(
    *,
    session_id: str,
    draft: RequestDraft,
    state_store: "state_store_mod.OrchestrationStateStore",
    clock: Callable[[], float] = time.monotonic,
    id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
) -> MockOrchestrationInstance:
    """The explicit, named "production construction" entry point that
    requires a durable state store (mirrors `build_production_adapter_
    runner(...)`'s own explicitness convention). `MockOrchestrationInstance`
    itself still defaults to `state_store=None` for every existing caller
    and test -- this function exists only so production code paths have one
    unambiguous, named way to opt into durability, never an implicit
    default."""
    if state_store is None:
        raise ValueError("build_durable_orchestration_instance requires an explicit, non-None state_store.")
    return MockOrchestrationInstance(
        session_id=session_id, draft=draft, clock=clock, id_factory=id_factory, state_store=state_store,
    )


def reload_orchestration_instance(
    state_store: "state_store_mod.OrchestrationStateStore",
    orchestration_instance_id: str,
    *,
    clock: Callable[[], float] = time.monotonic,
) -> tuple[MockOrchestrationInstance, "state_store_mod.DurableRecord"]:
    """Reconstructs an in-memory view of an already-durable orchestration
    instance -- e.g. after a process restart, or in a second cooperating
    process. Returns (instance, durable_record).

    `instance.record` is reconstructed as faithfully as what was actually
    persisted allows: current_state, previous_state, confirmation status/
    consumption, invocation status/id, failure_category, cancellation/
    analysis/report status, the transition sequence number, and the full
    ordered transition history are all genuine, durably-sourced values.

    `instance.request` is always None after a reload -- inline code was
    deliberately never durably persisted (only a digest), so a full
    CanonicalExecutionRequest cannot be reconstructed. This means
    `begin_analysis()` and `invoke()` correctly refuse to proceed on a
    reloaded instance (both already fail closed when `self.request is
    None` -- an existing guard from `v0.31.0`, not something added here) --
    this reload path can never resurrect execution capability from
    incomplete state, satisfying this milestone's own stop condition.

    `instance.record.execution_result_reference` is always None after a
    reload -- raw stdout/stderr/output-file details/warnings/errors were
    never durably persisted, matching this codebase's existing "safe
    summary" precedent. The durable, safe execution facts that WERE
    persisted (execution_status, exit_code, output_file_count,
    validation_ok/problems) are available on the second return value,
    `durable_record`, rather than being fabricated into a full
    MockExecutionResult."""
    rec = state_store.load_record(orchestration_instance_id)
    placeholder_draft = RequestDraft(request_id=rec.canonical_request_id or orchestration_instance_id)
    instance = MockOrchestrationInstance(
        session_id=rec.session_id,
        draft=placeholder_draft,
        clock=clock,
        orchestration_instance_id=orchestration_instance_id,
        state_store=None,  # avoid __init__'s own create_record() call -- the record already exists
    )
    instance.record.current_state = OrchestrationState(rec.current_state)
    instance.record.previous_state = OrchestrationState(rec.previous_state) if rec.previous_state else None
    instance.record.canonical_request_id = rec.canonical_request_id
    instance.record.request_hash = rec.request_hash
    instance.record.confirmation_status = ConfirmationStatus(rec.confirmation_status)
    instance.record.confirmation_event_reference = rec.confirmation_timestamp
    instance.record.confirmation_consumption_status = rec.confirmation_consumed
    instance.record.helper_invocation_status = HelperInvocationStatus(rec.invocation_status)
    instance.record.helper_invocation_id = rec.invocation_id
    instance.record.failure_category = FailureCategory(rec.failure_category) if rec.failure_category else None
    instance.record.cancellation_status = CancellationStatus(rec.cancellation_status)
    instance.record.analysis_status = AnalysisStatus(rec.analysis_status)
    instance.record.report_status = ReportStatus(rec.report_status)
    instance.record.transition_sequence_number = rec.transition_sequence_number
    instance.record.created_at = rec.created_at
    instance.record.last_transition_at = rec.last_transition_at
    if rec.validation_ok is not None:
        instance.record.validation_outcome = ResultValidation(
            is_structurally_valid=rec.validation_ok, problems=rec.validation_problems
        )
    instance.record.transition_log = [
        TransitionEvent(
            sequence_number=event.sequence_number,
            from_state=OrchestrationState(event.from_state),
            to_state=OrchestrationState(event.to_state),
            at=event.at,
            note=event.note,
        )
        for event in state_store.get_transition_history(orchestration_instance_id)
    ]
    # Re-attach the store only now that reconstruction is complete, so any
    # FURTHER mutation of this reloaded instance is durable too.
    instance._state_store = state_store
    return instance, rec


# ---------------------------------------------------------------------------
# Self-test harness (this repository's established convention -- no pytest
# is configured anywhere in this repository; see the final report for why
# this module follows the same --self-test pattern as scripts/gauss_code_execution.py,
# scripts/gauss_environment_check.py, and scripts/gauss_package_inspection.py
# instead of introducing a new test framework)
# ---------------------------------------------------------------------------


def _run_self_tests() -> int:
    """A lightweight built-in smoke-test suite. The focused, comprehensive
    unit tests for this module live in scripts/test_gauss_runtime_orchestration.py
    (32+ cases) -- this function only sanity-checks that the module's core
    entry points work at all, mirroring the smoke-test role
    scripts/gauss_code_execution.py's own --self-test plays."""
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    env = EnvironmentSummary(
        executable_path="C:/example/gauss26/tgauss.exe",
        gauss_version="GAUSS 26",
        platform="Windows",
        detection_provenance="direct",
    )
    safety = SafetyReviewOutcome(outcome="pass", items=(SafetyReviewItem("code_shown", True),))
    draft = RequestDraft(
        request_id="req-1",
        code="print 1+1;",
        working_directory="C:/example/work",
        executable_path="C:/example/gauss26/tgauss.exe",
        timeout_seconds=30.0,
        environment_summary=env,
        safety_review=safety,
    )
    request = build_canonical_request(draft)
    check("request builds and freezes", request.is_frozen)
    check("hash is deterministic", request.request_hash == compute_request_hash(request))

    instance = MockOrchestrationInstance(session_id="s1", draft=draft)
    instance.submit_for_review()
    check("submit_for_review reaches proposed", instance.record.current_state == OrchestrationState.PROPOSED)
    instance.display_plan()
    check(
        "display_plan reaches awaiting_confirmation",
        instance.record.current_state == OrchestrationState.AWAITING_CONFIRMATION,
    )
    assert instance.request is not None
    instance.confirm(
        ConfirmationEvent(scope=instance.request.request_hash, timestamp="t1", session_id="s1")
    )
    check("confirm reaches confirmed", instance.record.current_state == OrchestrationState.CONFIRMED)

    def fake_runner(_: RunnerInput) -> dict[str, Any]:
        return {
            "executed": True,
            "execution_status": "completed",
            "exit_code": 0,
            "stdout": "2",
            "stderr": "",
            "output_files": [],
            "warnings": [],
            "errors": [],
        }

    instance.invoke(fake_runner)
    check(
        "invoke reaches execution_completed",
        instance.record.current_state == OrchestrationState.EXECUTION_COMPLETED,
    )
    check("invocation recorded exactly once", instance.record.helper_invocation_id is not None)

    try:
        instance.invoke(fake_runner)
        failures.append("duplicate invoke should have raised DuplicateInvocationError")
    except InvalidTransitionError:
        pass  # already past `confirmed`; also acceptable

    instance.begin_analysis(lambda req, res: None)
    check("analysis reaches completed", instance.record.current_state == OrchestrationState.COMPLETED)
    check("analysis marked completed", instance.record.analysis_status == AnalysisStatus.COMPLETED)

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
            "Mock-only, in-memory runtime orchestration controller skeleton "
            "(v0.31.0 Phase 2). Never imports scripts/gauss_code_execution.py, "
            "never launches a subprocess, never invokes GAUSS."
        )
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a lightweight built-in smoke test and exit.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if args.self_test:
        return _run_self_tests()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
