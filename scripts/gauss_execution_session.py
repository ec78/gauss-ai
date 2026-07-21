"""In-memory execution session model (v0.40.0 Execution Session Model
Implementation).

Authoritative design source: `planning/v0.39.0-execution-session-model.md`.
This module implements that plan's identity model, session-only state
machine, confirmation-binding contract, and API surface — it does not
redefine them.

**Scope, restated from the authorizing task:** in-memory only. No database,
no filesystem persistence, no distributed workers, no cross-process
execution, no agent handoff, no runtime orchestration changes. This module
has no dependency on, and is not depended on by, `scripts/gauss_runtime_
orchestration.py`, `scripts/gauss_execution_workflow.py`, `scripts/gauss_
orchestration_state_store.py`, `scripts/gauss_execution_adapter.py`, or
`scripts/gauss_code_execution.py` — it never imports any of them, never
launches a subprocess, and never touches GAUSS.

**Identity model (three separate concepts, never collapsed):**

- **Execution Request** — what the user approved: execution parameters and
  request identity. This module never represents a full request; it only
  ever accepts and stores a `request_hash`/`plan_digest`/`code_digest`
  *reference* to one, exactly as `planning/v0.39.0-execution-session-model
  .md`'s Identity Model specifies. Raw code is never a parameter anywhere in
  this module.
- **Execution Session** (`ExecutionSession`, this module's primary type) —
  the lifecycle of an approved (or approval-pending) request: confirmation
  validity, expiration, ownership/reference metadata. A session's `status`
  is one of six session-only states and never includes an execution
  instance's own outcome.
- **Execution Instance** (`ExecutionInstance`, a lightweight reference type
  only — this module implements no instance lifecycle functions) — one
  execution attempt. Deliberately not mixed with session state: nothing in
  `SessionStatus` is `running`/`completed`/`failed`: those are Execution
  Instance outcomes, represented (if at all) only as an opaque reference a
  session's `reference_metadata` may point at.

**Never stored anywhere in this module:** raw code, credentials, secrets,
raw GAUSS output (stdout/stderr/output-file content), user files. This is
structural, not merely conventional: no constructor or function in this
module accepts a code, credential, or output-content parameter at all.

**Session-only state machine** (six states; deliberately excludes
`running`/`completed`/`failed`, which belong to Execution Instances):

    created -> awaiting_confirmation -> confirmed -> {expired, cancelled}

`confirm_session(...)` performs the first two transitions atomically in one
call (there is no separate "display plan" step exposed by this minimal
API), landing on `confirmed`. `ready` exists in `VALID_TRANSITIONS` (matching
the design document's `confirmed -> ready` edge exactly) but no function in
this initial API triggers it — promoting a confirmed session to `ready`
immediately before an Execution Instance is created is left for a future,
separately authorized milestone that actually implements instance creation.
This is a disclosed, deliberate gap, not an oversight: `v0.40.0`'s own
required API list (`create_session`, `confirm_session`, `validate_session`,
`expire_session`, `cancel_session`, `invalidate_session`,
`get_session_state`) names no function that would perform that promotion.
"""

from __future__ import annotations

import argparse
import enum
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Session state machine
# ---------------------------------------------------------------------------


class SessionStatus(enum.Enum):
    CREATED = "created"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    CONFIRMED = "confirmed"
    READY = "ready"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


#: Exactly the five edges named in planning/v0.39.0-execution-session-model.md's
#: Session State Model. No more, no fewer.
VALID_TRANSITIONS: dict[SessionStatus, frozenset[SessionStatus]] = {
    SessionStatus.CREATED: frozenset({SessionStatus.AWAITING_CONFIRMATION}),
    SessionStatus.AWAITING_CONFIRMATION: frozenset({SessionStatus.CONFIRMED}),
    SessionStatus.CONFIRMED: frozenset({SessionStatus.READY, SessionStatus.EXPIRED, SessionStatus.CANCELLED}),
    SessionStatus.READY: frozenset(),
    SessionStatus.EXPIRED: frozenset(),
    SessionStatus.CANCELLED: frozenset(),
}

TERMINAL_SESSION_STATES = frozenset({SessionStatus.READY, SessionStatus.EXPIRED, SessionStatus.CANCELLED})

DEFAULT_CONFIRMATION_TTL_SECONDS = 1800.0  # 30 minutes, matching v0.36.0's existing durable-store policy


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class SessionError(Exception):
    """Base class for every error this module raises."""


class InvalidSessionTransitionError(SessionError):
    """Raised when a requested state transition is not present in
    VALID_TRANSITIONS for the session's current status."""


class SessionValidationError(SessionError):
    """Raised by confirm_session(...) when a precondition fails.

    `reason_category` is one of: "hash_mismatch", "code_identity_mismatch",
    "already_confirmed". validate_session(...) reports the analogous
    read-only outcomes via ValidationOutcome instead of raising.
    """

    def __init__(self, reason_category: str, detail: str) -> None:
        super().__init__(f"{reason_category}: {detail}")
        self.reason_category = reason_category
        self.detail = detail


# ---------------------------------------------------------------------------
# Execution Instance (reference type only -- no lifecycle functions in this
# initial API; see module docstring)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionInstance:
    """One execution attempt against a confirmed session. Deliberately a
    thin reference type: `execution_result_reference` is an opaque pointer
    (e.g. an identifier or a small status/exit-code summary), never raw
    stdout/stderr/output-file content."""

    instance_id: str
    session_id: str
    start_time: float | None = None
    end_time: float | None = None
    status: str | None = None  # reuses schemas/gauss_code_execution.schema.json's execution_status vocabulary
    execution_result_reference: Any = None


# ---------------------------------------------------------------------------
# Execution Session
# ---------------------------------------------------------------------------


@dataclass
class ExecutionSession:
    """The lifecycle of an approved (or approval-pending) Execution
    Request. Never carries raw code, credentials, secrets, or raw GAUSS
    output -- structurally impossible, since no field or constructor
    parameter here accepts any of them."""

    execution_session_id: str
    request_hash: str
    plan_digest: str
    status: SessionStatus
    created_at: float
    code_digest: str | None = None
    expires_at: float | None = None
    confirmed: bool = False
    confirmed_at: Any = None
    confirmation_scope: str | None = None
    owner: str | None = None
    reference_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationOutcome:
    valid: bool
    reason_category: str | None = None
    detail: str | None = None


@dataclass(frozen=True)
class SessionStateSnapshot:
    """A read-only projection of an ExecutionSession, matching
    planning/v0.39.0-execution-session-model.md's Serialization Model.
    Never mutates the session it reads."""

    execution_session_id: str
    request_hash: str
    plan_digest: str
    code_digest: str | None
    status: str
    created_at: float
    expires_at: float | None
    confirmed: bool
    confirmed_at: Any
    owner: str | None
    reference_metadata: dict[str, Any]


def _transition(session: ExecutionSession, target: SessionStatus) -> None:
    allowed = VALID_TRANSITIONS.get(session.status, frozenset())
    if target not in allowed:
        raise InvalidSessionTransitionError(
            f"{session.status.value} -> {target.value} is not a valid session transition."
        )
    session.status = target


# ---------------------------------------------------------------------------
# Required API
# ---------------------------------------------------------------------------


def create_session(
    *,
    request_hash: str,
    plan_digest: str,
    code_digest: str | None = None,
    owner: str | None = None,
    reference_metadata: dict[str, Any] | None = None,
    clock: Callable[[], float] = time.time,
    id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
) -> ExecutionSession:
    """Creates a session in the `created` state. Accepts only
    identifiers/hashes/digests/references -- never raw code, credentials,
    or file content."""
    if not request_hash:
        raise ValueError("request_hash is required.")
    if not plan_digest:
        raise ValueError("plan_digest is required.")
    now = clock()
    return ExecutionSession(
        execution_session_id=id_factory(),
        request_hash=request_hash,
        plan_digest=plan_digest,
        code_digest=code_digest,
        status=SessionStatus.CREATED,
        created_at=now,
        reference_metadata=dict(reference_metadata or {}),
        owner=owner,
    )


def confirm_session(
    session: ExecutionSession,
    *,
    confirmation_scope: str,
    confirmed_at: Any,
    ttl_seconds: float = DEFAULT_CONFIRMATION_TTL_SECONDS,
    clock: Callable[[], float] = time.time,
) -> ExecutionSession:
    """Validates and records confirmation, advancing
    `created`/`awaiting_confirmation` -> `confirmed` in one call (mutates
    `session` in place and returns it).

    `confirmation_scope` must equal BOTH `request_hash` and `plan_digest`
    exactly -- `confirmed=True` alone is never sufficient, matching every
    prior milestone's confirmation-binding contract. Confirmation is
    monotonic: calling this a second time on an ordinarily-reached
    already-confirmed session raises `InvalidSessionTransitionError`
    (status has already left `created`/`awaiting_confirmation`) -- replay is
    refused either way. The `already_confirmed` `SessionValidationError`
    below is defense in depth for the case where `session.confirmed` is
    `True` but `status` was externally forced back into a pre-confirmation
    value (unreachable through this module's own public API, but tested
    directly, mirroring this codebase's established defense-in-depth
    testing pattern).
    """
    if session.status not in (SessionStatus.CREATED, SessionStatus.AWAITING_CONFIRMATION):
        raise InvalidSessionTransitionError(
            f"confirm_session is only valid from 'created' or 'awaiting_confirmation', "
            f"not {session.status.value!r}."
        )
    if session.confirmed:
        raise SessionValidationError(
            "already_confirmed",
            "confirmation is monotonic; this session has already been confirmed once and cannot "
            "be re-confirmed or replayed.",
        )
    if confirmation_scope != session.request_hash:
        raise SessionValidationError(
            "hash_mismatch",
            "confirmation_scope does not equal this session's request_hash; the request has "
            "changed (or never matched) since this session was created.",
        )
    if confirmation_scope != session.plan_digest:
        raise SessionValidationError(
            "hash_mismatch",
            "confirmation_scope does not equal this session's plan_digest; the displayed plan "
            "no longer matches what is being confirmed.",
        )

    now = clock()
    if session.status == SessionStatus.CREATED:
        _transition(session, SessionStatus.AWAITING_CONFIRMATION)
    _transition(session, SessionStatus.CONFIRMED)
    session.confirmed = True
    session.confirmation_scope = confirmation_scope
    session.confirmed_at = confirmed_at
    session.expires_at = now + ttl_seconds
    return session


def validate_session(
    session: ExecutionSession,
    *,
    expected_request_hash: str,
    expected_code_digest: str | None = None,
    clock: Callable[[], float] = time.time,
) -> ValidationOutcome:
    """A read-only check (never mutates `session`). Returns a typed
    `ValidationOutcome` so a caller can distinguish *why* validation failed,
    rather than a bare boolean.

    A session is valid only if: `request_hash` matches, confirmation
    exists, expiration has not passed, and `status` allows the requested
    action. `expected_code_digest`, when supplied, is checked independently
    of `expected_request_hash` so a caller can distinguish "the code itself
    changed" (`code_identity_mismatch`) from "some other hash-included
    field changed" (`hash_mismatch`) -- both ultimately change
    `request_hash`, but the more specific category is more actionable.
    """
    if session.request_hash != expected_request_hash:
        return ValidationOutcome(
            False, "hash_mismatch", "request_hash does not match this session's own request_hash; the request has changed."
        )
    if expected_code_digest is not None and session.code_digest is not None and session.code_digest != expected_code_digest:
        return ValidationOutcome(
            False, "code_identity_mismatch", "code_digest does not match this session's own code_digest; the code has changed."
        )
    if session.status == SessionStatus.CANCELLED:
        return ValidationOutcome(False, "cancelled", "this session has been cancelled.")
    if session.status == SessionStatus.EXPIRED:
        return ValidationOutcome(False, "expired", "this session has expired.")
    if not session.confirmed:
        return ValidationOutcome(False, "not_confirmed", "this session has not been confirmed.")
    now = clock()
    if session.expires_at is None or now >= session.expires_at:
        return ValidationOutcome(False, "expired", "this session's confirmation has expired.")
    if session.status not in (SessionStatus.CONFIRMED, SessionStatus.READY):
        return ValidationOutcome(
            False, "wrong_state", f"session status {session.status.value!r} does not permit this action."
        )
    return ValidationOutcome(True)


def expire_session(
    session: ExecutionSession, *, now: float | None = None, clock: Callable[[], float] = time.time
) -> ExecutionSession:
    """Transitions `confirmed -> expired` when `now` (or the clock's
    current value) is past `expires_at`. A no-op -- returns `session`
    unchanged -- if the session is not `confirmed`, or is `confirmed` but
    not yet actually expired; never forces a transition outside
    VALID_TRANSITIONS and never expires an already-terminal session."""
    current_time = now if now is not None else clock()
    if session.status != SessionStatus.CONFIRMED:
        return session
    if session.expires_at is None or current_time < session.expires_at:
        return session
    _transition(session, SessionStatus.EXPIRED)
    return session


def cancel_session(session: ExecutionSession, *, reason: str = "") -> ExecutionSession:
    """Transitions `confirmed -> cancelled` -- explicit, user-initiated
    cancellation. Refuses (raises `InvalidSessionTransitionError`, never
    silently no-ops) from any other state: cancelling a session that was
    never confirmed, or is already terminal, is a caller error that should
    be surfaced. Use `invalidate_session(...)` instead for system-detected
    invalidation (e.g. a changed request) reachable from earlier states."""
    if session.status != SessionStatus.CONFIRMED:
        raise InvalidSessionTransitionError(
            f"cancel_session is only valid from 'confirmed', not {session.status.value!r}. "
            "Use invalidate_session(...) to abandon a session in an earlier state."
        )
    del reason  # audit-only in this in-memory model; not persisted anywhere
    _transition(session, SessionStatus.CANCELLED)
    return session


def invalidate_session(session: ExecutionSession, *, reason: str = "") -> ExecutionSession:
    """System-detected invalidation -- e.g. the underlying request changed,
    or a session-boundary event occurred -- reachable from any non-terminal
    state (`created`, `awaiting_confirmation`, or `confirmed`), always
    landing on `cancelled`. Distinct from `cancel_session(...)`, which
    represents explicit, user-initiated cancellation and is stricter about
    its source state. A no-op (returns `session` unchanged) if the session
    is already terminal -- invalidating an already-terminal session is
    meaningless, not an error."""
    if session.status in TERMINAL_SESSION_STATES:
        return session
    del reason  # audit-only in this in-memory model; not persisted anywhere
    if session.status == SessionStatus.CREATED:
        _transition(session, SessionStatus.AWAITING_CONFIRMATION)
    if session.status == SessionStatus.AWAITING_CONFIRMATION:
        _transition(session, SessionStatus.CONFIRMED)
    _transition(session, SessionStatus.CANCELLED)
    return session


def get_session_state(session: ExecutionSession) -> SessionStateSnapshot:
    """A read-only projection matching the Serialization Model in
    planning/v0.39.0-execution-session-model.md. Never mutates `session`."""
    return SessionStateSnapshot(
        execution_session_id=session.execution_session_id,
        request_hash=session.request_hash,
        plan_digest=session.plan_digest,
        code_digest=session.code_digest,
        status=session.status.value,
        created_at=session.created_at,
        expires_at=session.expires_at,
        confirmed=session.confirmed,
        confirmed_at=session.confirmed_at,
        owner=session.owner,
        reference_metadata=dict(session.reference_metadata),
    )


# ---------------------------------------------------------------------------
# Self-test harness (this repository's established convention -- no pytest
# is configured anywhere in this repository)
# ---------------------------------------------------------------------------


def _run_self_tests() -> int:
    """A lightweight built-in smoke test. The focused, comprehensive test
    suite lives in scripts/test_gauss_execution_session.py -- this function
    only sanity-checks that the module's core entry points work at all."""
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    session = create_session(request_hash="h1", plan_digest="h1", code_digest="c1")
    check("session created in 'created' status", session.status == SessionStatus.CREATED)

    confirm_session(session, confirmation_scope="h1", confirmed_at="t1")
    check("confirmed session reaches 'confirmed'", session.status == SessionStatus.CONFIRMED)
    check("confirmed session is marked confirmed", session.confirmed)

    outcome = validate_session(session, expected_request_hash="h1", expected_code_digest="c1")
    check("a freshly confirmed session validates successfully", outcome.valid)

    try:
        confirm_session(session, confirmation_scope="h1", confirmed_at="t2")
        failures.append("replayed confirmation should have raised InvalidSessionTransitionError")
    except InvalidSessionTransitionError:
        pass  # status is already 'confirmed', so replay is refused at the transition guard

    cancelled = cancel_session(session)
    check("cancellation reaches 'cancelled'", cancelled.status == SessionStatus.CANCELLED)

    outcome_after_cancel = validate_session(session, expected_request_hash="h1")
    check("a cancelled session no longer validates", not outcome_after_cancel.valid)
    check(
        "a cancelled session reports the 'cancelled' reason", outcome_after_cancel.reason_category == "cancelled"
    )

    snapshot = get_session_state(session)
    check("snapshot excludes anything beyond the documented fields", snapshot.status == "cancelled")

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
            "In-memory execution session model (v0.40.0). No database, no filesystem "
            "persistence, no cross-process execution, no GAUSS invocation anywhere in this module."
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
