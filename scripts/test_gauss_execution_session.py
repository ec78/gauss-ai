"""Focused unit tests for scripts/gauss_execution_session.py (v0.40.0
Execution Session Model Implementation).

This repository has no pytest configuration anywhere; the established
convention (see scripts/test_gauss_runtime_orchestration.py's own docstring)
is a self-contained `check(name, condition)` harness runnable directly:

    python scripts/test_gauss_execution_session.py

Every test in this file is purely in-memory. No database, no filesystem
persistence, no subprocess, and no GAUSS invocation occurs anywhere in this
file. Tests are grouped to match the authorizing task's own coverage list:
Creation (1-3), Confirmation (4-8), Expiration (9-11), Cancellation (12-14),
Security (15-18), Lifecycle (19-23).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_execution_session as ges  # noqa: E402

# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def check_raises(name: str, exc_type: type[BaseException], fn, *args: Any, **kwargs: Any) -> None:
    try:
        fn(*args, **kwargs)
        _failures.append(f"{name} (expected {exc_type.__name__}, nothing was raised)")
    except exc_type:
        pass
    except Exception as exc:  # noqa: BLE001
        _failures.append(f"{name} (expected {exc_type.__name__}, got {type(exc).__name__}: {exc})")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _fake_clock(value: list[float]):
    def clock() -> float:
        return value[0]

    return clock


def _new_session(*, request_hash: str = "h1", plan_digest: str | None = None, code_digest: str | None = "c1", **kwargs: Any) -> "ges.ExecutionSession":
    return ges.create_session(
        request_hash=request_hash, plan_digest=plan_digest if plan_digest is not None else request_hash,
        code_digest=code_digest, **kwargs,
    )


# ---------------------------------------------------------------------------
# Creation (1-3)
# ---------------------------------------------------------------------------


def test_01_session_created_correctly() -> None:
    session = _new_session()
    check("session starts in 'created' status", session.status == ges.SessionStatus.CREATED)
    check("session is not confirmed at creation", not session.confirmed)


def test_02_required_fields_populated() -> None:
    session = _new_session(request_hash="hash-a", code_digest="digest-a", owner="user-1")
    check("execution_session_id is populated", bool(session.execution_session_id))
    check("request_hash is populated", session.request_hash == "hash-a")
    check("plan_digest is populated", session.plan_digest == "hash-a")
    check("code_digest is populated", session.code_digest == "digest-a")
    check("created_at is populated", session.created_at > 0)
    check("owner is populated", session.owner == "user-1")
    check("expires_at starts unset", session.expires_at is None)


def test_03_missing_identity_fields_rejected() -> None:
    check_raises("missing request_hash is rejected", ValueError, ges.create_session, request_hash="", plan_digest="h1")
    check_raises("missing plan_digest is rejected", ValueError, ges.create_session, request_hash="h1", plan_digest="")


# ---------------------------------------------------------------------------
# Confirmation (4-8)
# ---------------------------------------------------------------------------


def test_04_valid_confirmation_accepted() -> None:
    session = _new_session()
    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1")
    check("confirmation reaches 'confirmed'", session.status == ges.SessionStatus.CONFIRMED)
    check("confirmed flag set", session.confirmed)
    check("confirmation_scope recorded", session.confirmation_scope == "h1")
    check("expires_at set after confirmation", session.expires_at is not None)


def test_05_invalid_digest_rejected() -> None:
    session = _new_session(request_hash="h1")
    check_raises(
        "a confirmation_scope not matching request_hash is rejected",
        ges.SessionValidationError, ges.confirm_session, session, confirmation_scope="wrong-hash", confirmed_at="t1",
    )
    check("session remains unconfirmed after rejection", not session.confirmed)
    check("session status unchanged after rejection", session.status == ges.SessionStatus.CREATED)


def test_06_confirmation_binds_to_plan_digest_too() -> None:
    # A session whose request_hash and plan_digest were built to differ
    # (representing a plan that changed after the request was hashed but
    # before the current confirmation attempt) must reject a scope that
    # matches only one of the two.
    session = ges.create_session(request_hash="h1", plan_digest="h1-different-plan")
    check_raises(
        "a scope matching request_hash but not plan_digest is rejected",
        ges.SessionValidationError, ges.confirm_session, session, confirmation_scope="h1", confirmed_at="t1",
    )


def test_07_confirmation_ttl_uses_store_clock_not_caller_timestamp() -> None:
    clock_value = [1000.0]
    session = _new_session()
    ges.confirm_session(
        session, confirmation_scope="h1", confirmed_at="not-a-real-timestamp", ttl_seconds=500.0, clock=_fake_clock(clock_value)
    )
    check("expires_at is computed from the store clock, not the caller label", session.expires_at == 1500.0)
    check("confirmed_at preserves the caller's own audit label verbatim", session.confirmed_at == "not-a-real-timestamp")


def test_08_confirmation_requires_created_or_awaiting_confirmation() -> None:
    session = _new_session()
    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1")
    check_raises(
        "confirming an already-confirmed session is refused",
        ges.InvalidSessionTransitionError, ges.confirm_session, session, confirmation_scope="h1", confirmed_at="t2",
    )


# ---------------------------------------------------------------------------
# Expiration (9-11)
# ---------------------------------------------------------------------------


def test_09_expired_session_rejected_by_validate() -> None:
    clock_value = [1000.0]
    session = _new_session()
    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1", ttl_seconds=10.0, clock=_fake_clock(clock_value))
    clock_value[0] += 20.0  # advance past the 10-second TTL
    outcome = ges.validate_session(session, expected_request_hash="h1", clock=_fake_clock(clock_value))
    check("an expired confirmation fails validation", not outcome.valid)
    check("expired confirmation reports 'expired'", outcome.reason_category == "expired")


def test_10_expire_session_transitions_when_actually_past_ttl() -> None:
    clock_value = [1000.0]
    session = _new_session()
    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1", ttl_seconds=10.0, clock=_fake_clock(clock_value))
    clock_value[0] += 20.0
    ges.expire_session(session, clock=_fake_clock(clock_value))
    check("expire_session transitions to 'expired' once actually past ttl", session.status == ges.SessionStatus.EXPIRED)


def test_11_expire_session_is_a_no_op_before_ttl_or_before_confirmation() -> None:
    clock_value = [1000.0]
    session = _new_session()
    ges.expire_session(session, clock=_fake_clock(clock_value))
    check("expire_session is a no-op on an unconfirmed session", session.status == ges.SessionStatus.CREATED)

    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1", ttl_seconds=1000.0, clock=_fake_clock(clock_value))
    ges.expire_session(session, clock=_fake_clock(clock_value))
    check("expire_session is a no-op before ttl has elapsed", session.status == ges.SessionStatus.CONFIRMED)


# ---------------------------------------------------------------------------
# Cancellation (12-14)
# ---------------------------------------------------------------------------


def test_12_cancelled_session_rejected_by_validate() -> None:
    session = _new_session()
    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1")
    ges.cancel_session(session, reason="user requested stop")
    check("cancellation reaches 'cancelled'", session.status == ges.SessionStatus.CANCELLED)
    outcome = ges.validate_session(session, expected_request_hash="h1")
    check("a cancelled session fails validation", not outcome.valid)
    check("cancelled session reports 'cancelled'", outcome.reason_category == "cancelled")


def test_13_cancel_session_requires_confirmed_state() -> None:
    session = _new_session()  # still 'created'
    check_raises(
        "cancel_session refuses a session that was never confirmed",
        ges.InvalidSessionTransitionError, ges.cancel_session, session,
    )


def test_14_cancelled_session_cannot_be_reconfirmed() -> None:
    session = _new_session()
    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1")
    ges.cancel_session(session)
    check_raises(
        "cancelled -> confirmed is forbidden",
        ges.InvalidSessionTransitionError, ges.confirm_session, session, confirmation_scope="h1", confirmed_at="t2",
    )


# ---------------------------------------------------------------------------
# Security (15-18)
# ---------------------------------------------------------------------------


def test_15_replay_attempt_rejected() -> None:
    session = _new_session()
    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1")
    check_raises(
        "replaying the same, otherwise-valid confirmation_scope a second time is rejected",
        ges.InvalidSessionTransitionError, ges.confirm_session, session, confirmation_scope="h1", confirmed_at="t1",
    )


def test_16_already_confirmed_defense_in_depth() -> None:
    # Directly exercises the SessionValidationError("already_confirmed", ...)
    # branch, unreachable through the public API alone (status always
    # leaves created/awaiting_confirmation in the same call that sets
    # confirmed=True) -- forced here the same way this codebase's other
    # test suites force defense-in-depth states directly.
    session = _new_session()
    session.confirmed = True  # force an otherwise-unreachable combination
    check_raises(
        "an already-confirmed session (even if forced back to a pre-confirmation status) refuses re-confirmation",
        ges.SessionValidationError, ges.confirm_session, session, confirmation_scope="h1", confirmed_at="t2",
    )


def test_17_changed_request_rejected() -> None:
    session = _new_session(request_hash="original-hash")
    # The request changed after the session was created (e.g. code edited)
    # -- confirmation_scope now reflects the NEW hash, which does not match
    # this session's own request_hash.
    check_raises(
        "a confirmation scoped to a changed request_hash is rejected",
        ges.SessionValidationError, ges.confirm_session, session, confirmation_scope="changed-hash", confirmed_at="t1",
    )


def test_18_changed_code_identity_detected_by_validate() -> None:
    session = _new_session(request_hash="h1", code_digest="original-code-digest")
    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1")
    outcome = ges.validate_session(session, expected_request_hash="h1", expected_code_digest="different-code-digest")
    check("a changed code_digest is detected", not outcome.valid)
    check("changed code_digest reports 'code_identity_mismatch'", outcome.reason_category == "code_identity_mismatch")


# ---------------------------------------------------------------------------
# Lifecycle (19-23)
# ---------------------------------------------------------------------------


def test_19_expired_to_confirmed_forbidden() -> None:
    clock_value = [1000.0]
    session = _new_session()
    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1", ttl_seconds=1.0, clock=_fake_clock(clock_value))
    clock_value[0] += 10.0
    ges.expire_session(session, clock=_fake_clock(clock_value))
    check("session reached 'expired'", session.status == ges.SessionStatus.EXPIRED)
    check_raises(
        "expired -> confirmed is forbidden",
        ges.InvalidSessionTransitionError, ges.confirm_session, session, confirmation_scope="h1", confirmed_at="t2",
    )


def test_20_invalid_transitions_rejected_directly() -> None:
    session = _new_session()
    check_raises(
        "created -> confirmed directly (skipping awaiting_confirmation) is rejected",
        ges.InvalidSessionTransitionError, ges._transition, session, ges.SessionStatus.CONFIRMED,
    )
    check_raises(
        "created -> ready is rejected",
        ges.InvalidSessionTransitionError, ges._transition, session, ges.SessionStatus.READY,
    )


def test_21_terminal_states_have_no_outgoing_transitions() -> None:
    for terminal in (ges.SessionStatus.READY, ges.SessionStatus.EXPIRED, ges.SessionStatus.CANCELLED):
        check(f"{terminal.value} has no outgoing transitions", ges.VALID_TRANSITIONS[terminal] == frozenset())


def test_22_invalidate_session_reaches_cancelled_from_any_non_terminal_state() -> None:
    for start_status in (ges.SessionStatus.CREATED, ges.SessionStatus.AWAITING_CONFIRMATION, ges.SessionStatus.CONFIRMED):
        session = _new_session()
        session.status = start_status  # simulate arriving from that state
        ges.invalidate_session(session, reason="request changed")
        check(f"invalidate_session from {start_status.value} reaches cancelled", session.status == ges.SessionStatus.CANCELLED)


def test_23_invalidate_session_is_a_no_op_on_already_terminal_sessions() -> None:
    session = _new_session()
    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1")
    ges.cancel_session(session)
    ges.invalidate_session(session, reason="redundant call")
    check("invalidate_session does not raise or change an already-cancelled session", session.status == ges.SessionStatus.CANCELLED)


# ---------------------------------------------------------------------------
# get_session_state / redaction (24-25)
# ---------------------------------------------------------------------------


def test_24_get_session_state_matches_serialization_model() -> None:
    session = _new_session(request_hash="h1", code_digest="c1", owner="owner-1")
    ges.confirm_session(session, confirmation_scope="h1", confirmed_at="t1")
    snapshot = ges.get_session_state(session)
    check("snapshot execution_session_id matches", snapshot.execution_session_id == session.execution_session_id)
    check("snapshot status is a string, not an enum", snapshot.status == "confirmed")
    check("snapshot confirmed flag matches", snapshot.confirmed is True)
    check("snapshot never mutates the underlying session", session.status == ges.SessionStatus.CONFIRMED)


def test_25_no_raw_code_or_secrets_field_exists_anywhere() -> None:
    import dataclasses

    session_fields = {f.name for f in dataclasses.fields(ges.ExecutionSession)}
    snapshot_fields = {f.name for f in dataclasses.fields(ges.SessionStateSnapshot)}
    for forbidden in ("code", "raw_code", "credentials", "secret", "secrets", "stdout", "stderr", "output_content"):
        check(f"ExecutionSession has no {forbidden!r} field", forbidden not in session_fields)
        check(f"SessionStateSnapshot has no {forbidden!r} field", forbidden not in snapshot_fields)


def test_26_module_never_runs_gauss() -> None:
    check("gauss_code_execution is absent from sys.modules", "gauss_code_execution" not in sys.modules)
    check("gauss_execution_adapter is absent from sys.modules", "gauss_execution_adapter" not in sys.modules)
    check("gauss_runtime_orchestration is absent from sys.modules", "gauss_runtime_orchestration" not in sys.modules)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


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
