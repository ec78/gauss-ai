"""Focused unit tests for scripts/gauss_orchestration_state_store.py (v0.36.0
Durable Execution State and Cross-Process Safety).

This repository has no pytest configuration anywhere. Following the
established convention, this file uses a self-contained
`check(name, condition)` harness, run directly:

    python scripts/test_gauss_orchestration_state_store.py

Every test here uses a disposable temporary SQLite database file -- never the
default repository location, never a shared file across tests. Nothing in
this file imports scripts/gauss_code_execution.py, scripts/gauss_execution_
adapter.py, or scripts/gauss_runtime_orchestration.py, and nothing here
invokes GAUSS. Single-process tests only -- see
scripts/test_gauss_orchestration_state_store_concurrency.py for
multiprocessing cross-process and crash-simulation tests.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_orchestration_state_store as store_mod  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures / helpers
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


class _FakeClock:
    """A controllable clock -- avoids any test depending on real wall-clock
    timing, and lets expiry be tested deterministically."""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self.value = start

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _new_store(tmp_path: Path, *, clock: Any = None, ttl: float = store_mod.DEFAULT_CONFIRMATION_TTL_SECONDS) -> store_mod.OrchestrationStateStore:
    db_path = tmp_path / "test.db"
    s = store_mod.OrchestrationStateStore(db_path, clock=clock or _FakeClock(), confirmation_ttl_seconds=ttl)
    s.initialize()
    return s


def _advance_to_confirmed(s: store_mod.OrchestrationStateStore, instance_id: str, *, session_id: str = "s1", request_hash: str = "hash-1") -> int:
    """Drives a fresh record through collecting_inputs -> confirmed, returning
    the expected_transition_sequence_number to use for the next write."""
    s.create_record(orchestration_instance_id=instance_id, session_id=session_id)
    s.transition(instance_id, to_state="proposed", expected_transition_sequence_number=0, extra_fields={"request_hash": request_hash})
    s.transition(instance_id, to_state="awaiting_confirmation", expected_transition_sequence_number=1)
    s.record_confirmation(
        instance_id, scope=request_hash, timestamp="t1", session_id=session_id,
        expected_request_hash=request_hash, expected_transition_sequence_number=2,
    )
    return 3


# ---------------------------------------------------------------------------
# 1-5: Initialization
# ---------------------------------------------------------------------------


def test_01_initialize_creates_schema() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        conn = sqlite3.connect(str(s.db_path))
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        s.close()
        check("orchestration_records table exists", "orchestration_records" in tables)
        check("transition_events table exists", "transition_events" in tables)
        check("invocation_attempts table exists", "invocation_attempts" in tables)
        check("schema_meta table exists", "schema_meta" in tables)


def test_02_initialize_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.initialize()
        s.initialize()
        s.close()
        check("idempotent initialize does not raise", True)


def test_03_unsupported_schema_version_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "bad.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE schema_meta (id INTEGER PRIMARY KEY CHECK (id=1), schema_version INTEGER NOT NULL, created_at REAL NOT NULL)")
        conn.execute("INSERT INTO schema_meta (id, schema_version, created_at) VALUES (1, 999, 0.0)")
        conn.commit()
        conn.close()
        s = store_mod.OrchestrationStateStore(db_path)
        check_raises("mismatched schema_version raises SchemaVersionError", store_mod.SchemaVersionError, s.initialize)
        s.close()


def test_04_default_db_path_is_not_a_temp_or_working_directory() -> None:
    p = store_mod.default_db_path()
    check("default path is under the repo's .gauss_orchestration_state directory", p.parent.name == store_mod.DEFAULT_STATE_DIR_NAME)
    check("default path is not inside evaluations/", "evaluations" not in p.parts)


def test_05_store_creates_parent_directory_deliberately() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        nested = Path(tmp) / "does" / "not" / "exist" / "yet" / "db.sqlite3"
        check("parent does not exist before construction", not nested.parent.exists())
        s = store_mod.OrchestrationStateStore(nested)
        check("parent created after construction", nested.parent.exists())
        s.close()


# ---------------------------------------------------------------------------
# 6-10: Record creation / retrieval
# ---------------------------------------------------------------------------


def test_06_create_and_load_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1", canonical_request_id="req-1")
        rec = s.load_record("i1")
        check("session_id persisted", rec.session_id == "s1")
        check("canonical_request_id persisted", rec.canonical_request_id == "req-1")
        check("initial state is collecting_inputs", rec.current_state == "collecting_inputs")
        check("transition_sequence_number starts at 0", rec.transition_sequence_number == 0)
        s.close()


def test_07_duplicate_create_record_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        check_raises("second create_record for the same id raises DuplicateRecordError", store_mod.DuplicateRecordError, s.create_record, orchestration_instance_id="i1", session_id="s1")
        s.close()


def test_08_load_missing_record_raises() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        check_raises("loading a nonexistent record raises RecordNotFoundError", store_mod.RecordNotFoundError, s.load_record, "does-not-exist")
        s.close()


def test_09_record_exists_helper() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        check("record_exists is False before creation", s.record_exists("i1") is False)
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        check("record_exists is True after creation", s.record_exists("i1") is True)
        s.close()


def test_10_code_digest_never_stores_raw_code() -> None:
    digest = store_mod.digest_code("x = 2 + 2;\nprint x;")
    check("digest is a 64-char hex string", len(digest) == 64 and all(c in "0123456789abcdef" for c in digest))
    check("digest does not contain the source text", "print" not in digest and "x" not in digest)
    check("digest is deterministic", digest == store_mod.digest_code("x = 2 + 2;\nprint x;"))
    check("digest of None is None", store_mod.digest_code(None) is None)


# ---------------------------------------------------------------------------
# 11-16: Transitions and optimistic concurrency
# ---------------------------------------------------------------------------


def test_11_transition_advances_state_and_sequence() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        s.transition("i1", to_state="proposed", expected_transition_sequence_number=0)
        rec = s.load_record("i1")
        check("state advanced to proposed", rec.current_state == "proposed")
        check("previous_state recorded", rec.previous_state == "collecting_inputs")
        check("sequence advanced to 1", rec.transition_sequence_number == 1)
        s.close()


def test_12_stale_transition_sequence_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        s.transition("i1", to_state="proposed", expected_transition_sequence_number=0)
        check_raises(
            "a stale expected_transition_sequence_number is rejected",
            store_mod.StaleTransitionError,
            s.transition, "i1", to_state="awaiting_confirmation", expected_transition_sequence_number=0,
        )
        s.close()


def test_13_transition_history_is_ordered_and_complete() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        history = s.get_transition_history("i1")
        check("three transitions recorded", len(history) == 3)
        check("sequence numbers are 0,1,2 in order", [t.sequence_number for t in history] == [0, 1, 2])
        check("final transition targets confirmed", history[-1].to_state == "confirmed")
        s.close()
        del seq


def test_14_unknown_state_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        check_raises("an unrecognized state name is rejected", ValueError, s.transition, "i1", to_state="not_a_real_state", expected_transition_sequence_number=0)
        s.close()


def test_15_update_fields_does_not_advance_sequence_or_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        s.update_fields("i1", expected_transition_sequence_number=0, cancellation_status="cancel_requested_during_invocation")
        rec = s.load_record("i1")
        check("state unchanged by update_fields", rec.current_state == "collecting_inputs")
        check("sequence unchanged by update_fields", rec.transition_sequence_number == 0)
        check("field updated", rec.cancellation_status == "cancel_requested_during_invocation")
        s.close()


def test_16_transition_on_missing_record_raises() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        check_raises("transition on a nonexistent record raises RecordNotFoundError", store_mod.RecordNotFoundError, s.transition, "ghost", to_state="proposed", expected_transition_sequence_number=0)
        s.close()


# ---------------------------------------------------------------------------
# 17-24: Confirmation and expiry
# ---------------------------------------------------------------------------


def test_17_record_confirmation_success() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        _advance_to_confirmed(s, "i1")
        rec = s.load_record("i1")
        check("state is confirmed", rec.current_state == "confirmed")
        check("confirmation_status is accepted", rec.confirmation_status == "accepted")
        check("confirmation not yet consumed", rec.confirmation_consumed is False)
        s.close()


def test_18_confirmation_session_mismatch_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        s.transition("i1", to_state="proposed", expected_transition_sequence_number=0, extra_fields={"request_hash": "h1"})
        s.transition("i1", to_state="awaiting_confirmation", expected_transition_sequence_number=1)
        exc_holder: list[Any] = []
        try:
            s.record_confirmation("i1", scope="h1", timestamp="t1", session_id="WRONG-SESSION", expected_request_hash="h1", expected_transition_sequence_number=2)
        except store_mod.AuthorizationFailedError as exc:
            exc_holder.append(exc)
        check("session mismatch raises AuthorizationFailedError", len(exc_holder) == 1)
        check("reason_category is session_mismatch", exc_holder and exc_holder[0].reason_category == "session_mismatch")
        s.close()


def test_19_confirmation_hash_mismatch_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        s.transition("i1", to_state="proposed", expected_transition_sequence_number=0, extra_fields={"request_hash": "h1"})
        s.transition("i1", to_state="awaiting_confirmation", expected_transition_sequence_number=1)
        check_raises(
            "confirmation targeting the wrong request_hash is rejected",
            store_mod.AuthorizationFailedError,
            s.record_confirmation, "i1", scope="h1", timestamp="t1", session_id="s1", expected_request_hash="DIFFERENT-HASH", expected_transition_sequence_number=2,
        )
        s.close()


def test_20_confirmation_scope_must_equal_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        s.transition("i1", to_state="proposed", expected_transition_sequence_number=0, extra_fields={"request_hash": "h1"})
        s.transition("i1", to_state="awaiting_confirmation", expected_transition_sequence_number=1)
        check_raises(
            "a confirmation scope not equal to the request hash is rejected",
            store_mod.AuthorizationFailedError,
            s.record_confirmation, "i1", scope="not-h1", timestamp="t1", session_id="s1", expected_request_hash="h1", expected_transition_sequence_number=2,
        )
        s.close()


def test_21_confirmation_not_expired_within_ttl() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        clock = _FakeClock()
        s = _new_store(Path(tmp), clock=clock, ttl=1800.0)
        seq = _advance_to_confirmed(s, "i1")
        clock.advance(1799.0)
        s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        rec = s.load_record("i1")
        check("authorization succeeds just before expiry", rec.current_state == "executing")
        s.close()


def test_22_confirmation_expires_correctly() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        clock = _FakeClock()
        s = _new_store(Path(tmp), clock=clock, ttl=1800.0)
        seq = _advance_to_confirmed(s, "i1")
        clock.advance(1800.1)
        exc_holder: list[Any] = []
        try:
            s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        except store_mod.AuthorizationFailedError as exc:
            exc_holder.append(exc)
        check("authorization fails after expiry", len(exc_holder) == 1)
        check("reason_category is confirmation_expired", exc_holder and exc_holder[0].reason_category == "confirmation_expired")
        rec = s.load_record("i1")
        check("confirmation was never consumed by the failed attempt", rec.confirmation_consumed is False)
        s.close()


def test_23_restart_does_not_extend_expiry() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "restart.db"
        clock = _FakeClock()
        s1 = store_mod.OrchestrationStateStore(db_path, clock=clock, confirmation_ttl_seconds=1800.0)
        s1.initialize()
        seq = _advance_to_confirmed(s1, "i1")
        rec_before = s1.load_record("i1")
        s1.close()

        clock2 = _FakeClock(start=clock.value + 2000.0)  # simulates a restart far in the future
        s2 = store_mod.OrchestrationStateStore(db_path, clock=clock2, confirmation_ttl_seconds=1800.0)
        s2.initialize()
        rec_after_restart = s2.load_record("i1")
        check("expires_at is unchanged across restart", rec_after_restart.confirmation_expires_at == rec_before.confirmation_expires_at)
        check_raises(
            "authorization after a simulated restart past expiry still fails closed",
            store_mod.AuthorizationFailedError,
            s2.authorize_invocation, "i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq,
        )
        s2.close()


def test_24_consumed_confirmation_never_becomes_reusable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        rec = s.load_record("i1")
        check("confirmation is consumed", rec.confirmation_consumed is True)
        check_raises(
            "a second authorization attempt is refused",
            store_mod.AuthorizationFailedError,
            s.authorize_invocation, "i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv2", expected_transition_sequence_number=rec.transition_sequence_number,
        )
        s.close()


# ---------------------------------------------------------------------------
# 25-32: Atomic invocation authorization
# ---------------------------------------------------------------------------


def test_25_authorize_invocation_success_commits_all_fields_atomically() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv-xyz", expected_transition_sequence_number=seq)
        rec = s.load_record("i1")
        check("state is executing", rec.current_state == "executing")
        check("invocation_status is in_progress", rec.invocation_status == "in_progress")
        check("invocation_id recorded", rec.invocation_id == "inv-xyz")
        check("confirmation_status is consumed", rec.confirmation_status == "consumed")
        s.close()


def test_26_authorize_invocation_wrong_state_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        exc_holder: list[Any] = []
        try:
            s.authorize_invocation("i1", request_hash="h1", confirmation_scope="h1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=0)
        except store_mod.AuthorizationFailedError as exc:
            exc_holder.append(exc)
        check("authorizing from collecting_inputs fails", len(exc_holder) == 1)
        check("reason_category is wrong_state", exc_holder and exc_holder[0].reason_category == "wrong_state")
        s.close()


def test_27_authorize_invocation_hash_mismatch_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        exc_holder: list[Any] = []
        try:
            s.authorize_invocation("i1", request_hash="WRONG-HASH", confirmation_scope="WRONG-HASH", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        except store_mod.AuthorizationFailedError as exc:
            exc_holder.append(exc)
        check("authorizing with the wrong request_hash fails", len(exc_holder) == 1)
        check("reason_category is hash_mismatch", exc_holder and exc_holder[0].reason_category == "hash_mismatch")
        s.close()


def test_28_authorize_invocation_session_mismatch_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        exc_holder: list[Any] = []
        try:
            s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="WRONG-SESSION", invocation_id="inv1", expected_transition_sequence_number=seq)
        except store_mod.AuthorizationFailedError as exc:
            exc_holder.append(exc)
        check("authorizing with the wrong session fails", len(exc_holder) == 1)
        check("reason_category is session_mismatch", exc_holder and exc_holder[0].reason_category == "session_mismatch")
        s.close()


def test_29_authorize_invocation_on_missing_record_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        exc_holder: list[Any] = []
        try:
            s.authorize_invocation("ghost", request_hash="h1", confirmation_scope="h1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=0)
        except store_mod.AuthorizationFailedError as exc:
            exc_holder.append(exc)
        check("authorizing a nonexistent instance fails", len(exc_holder) == 1)
        check("reason_category is record_not_found", exc_holder and exc_holder[0].reason_category == "record_not_found")
        s.close()


def test_30_authorize_invocation_no_partial_state_on_failure() -> None:
    """If any precondition fails, no field changes at all -- not even the
    ones checked before the failing precondition."""
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        before = s.load_record("i1")
        try:
            s.authorize_invocation("i1", request_hash="WRONG", confirmation_scope="WRONG", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        except store_mod.AuthorizationFailedError:
            pass
        after = s.load_record("i1")
        check("state unchanged after a failed authorization attempt", after.current_state == before.current_state == "confirmed")
        check("confirmation_consumed unchanged", after.confirmation_consumed == before.confirmation_consumed == False)
        check("invocation_id remains unset", after.invocation_id is None)
        check("transition_sequence_number unchanged", after.transition_sequence_number == before.transition_sequence_number)
        s.close()


def test_31_authorize_invocation_stale_sequence_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        check_raises(
            "authorizing with a stale expected sequence number fails",
            store_mod.StaleTransitionError,
            s.authorize_invocation, "i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq + 1,
        )
        s.close()


def test_32_same_code_new_request_may_proceed() -> None:
    """Two independent orchestration_instance_ids sharing the same
    request_hash (identical code/environment) must both be permitted to
    authorize and invoke once each -- duplicate protection is scoped per
    instance, never per content hash (mirrors v0.35.0's test_84 finding at
    the in-memory layer)."""
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq_a = _advance_to_confirmed(s, "i-a", session_id="s1", request_hash="shared-hash")
        seq_b = _advance_to_confirmed(s, "i-b", session_id="s1", request_hash="shared-hash")
        s.authorize_invocation("i-a", request_hash="shared-hash", confirmation_scope="shared-hash", session_id="s1", invocation_id="inv-a", expected_transition_sequence_number=seq_a)
        s.authorize_invocation("i-b", request_hash="shared-hash", confirmation_scope="shared-hash", session_id="s1", invocation_id="inv-b", expected_transition_sequence_number=seq_b)
        rec_a = s.load_record("i-a")
        rec_b = s.load_record("i-b")
        check("both instances reach executing", rec_a.current_state == "executing" and rec_b.current_state == "executing")
        check("each has its own distinct invocation_id", rec_a.invocation_id != rec_b.invocation_id)
        s.close()


# ---------------------------------------------------------------------------
# 33-37: Execution result recording
# ---------------------------------------------------------------------------


def test_33_record_execution_result_completed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        s.record_execution_result(
            "i1", to_state="execution_completed", execution_status="completed", exit_code=0,
            output_file_count=1, validation_ok=True, validation_problems=(), failure_category=None,
            expected_transition_sequence_number=seq + 1,
        )
        rec = s.load_record("i1")
        check("state is execution_completed", rec.current_state == "execution_completed")
        check("execution_status persisted", rec.execution_status == "completed")
        check("output_file_count persisted", rec.output_file_count == 1)
        s.close()


def test_34_record_execution_result_failed_with_failure_category() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        s.record_execution_result(
            "i1", to_state="execution_failed", execution_status="failed", exit_code=0,
            output_file_count=0, validation_ok=True, validation_problems=(), failure_category="gauss_runtime_error",
            expected_transition_sequence_number=seq + 1,
        )
        rec = s.load_record("i1")
        check("state is execution_failed", rec.current_state == "execution_failed")
        check("failure_category persisted", rec.failure_category == "gauss_runtime_error")
        s.close()


def test_35_record_result_requires_executing_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        check_raises(
            "recording a result before authorization is rejected",
            store_mod.AuthorizationFailedError,
            s.record_execution_result, "i1", to_state="execution_completed", execution_status="completed", exit_code=0,
            output_file_count=0, validation_ok=True, validation_problems=(), failure_category=None,
            expected_transition_sequence_number=seq,
        )
        s.close()


def test_36_validation_problems_are_bounded_and_json_encoded() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        many_problems = tuple(f"problem-{i}" for i in range(100))
        s.record_execution_result(
            "i1", to_state="execution_failed", execution_status="failed", exit_code=None,
            output_file_count=0, validation_ok=False, validation_problems=many_problems, failure_category="malformed_result",
            expected_transition_sequence_number=seq + 1,
        )
        rec = s.load_record("i1")
        check("validation_problems bounded to the configured maximum", len(rec.validation_problems) == store_mod._MAX_STORED_VALIDATION_PROBLEMS)
        s.close()


def test_37_ambiguous_invocation_listed_before_result_recorded() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        ambiguous = s.list_ambiguous_invocations()
        check("the authorized-but-not-yet-resulted instance is listed as ambiguous", any(r.orchestration_instance_id == "i1" for r in ambiguous))
        s.record_execution_result(
            "i1", to_state="execution_completed", execution_status="completed", exit_code=0,
            output_file_count=0, validation_ok=True, validation_problems=(), failure_category=None,
            expected_transition_sequence_number=seq + 1,
        )
        ambiguous_after = s.list_ambiguous_invocations()
        check("no longer ambiguous once a result is recorded", not any(r.orchestration_instance_id == "i1" for r in ambiguous_after))
        s.close()


# ---------------------------------------------------------------------------
# 38-44: Corruption detection
# ---------------------------------------------------------------------------


def test_38_malformed_validation_problems_json_detected_as_corrupt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        conn = sqlite3.connect(str(s.db_path))
        conn.execute("UPDATE orchestration_records SET validation_problems = ? WHERE orchestration_instance_id = ?", ("not valid json{{{", "i1"))
        conn.commit()
        conn.close()
        check_raises("malformed validation_problems JSON raises CorruptStateError on load", store_mod.CorruptStateError, s.load_record, "i1")
        check("check_integrity flags the same record", "i1" in s.check_integrity())
        s.close()


def test_39_unrecognized_state_detected_as_corrupt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        conn = sqlite3.connect(str(s.db_path))
        conn.execute("UPDATE orchestration_records SET current_state = ? WHERE orchestration_instance_id = ?", ("not_a_real_state", "i1"))
        conn.commit()
        conn.close()
        check_raises("an unrecognized state raises CorruptStateError on load", store_mod.CorruptStateError, s.load_record, "i1")
        s.close()


def test_40_impossible_confirmation_state_detected_as_corrupt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        conn = sqlite3.connect(str(s.db_path))
        conn.execute(
            "UPDATE orchestration_records SET confirmation_consumed = 1, confirmation_status = 'none' WHERE orchestration_instance_id = ?",
            ("i1",),
        )
        conn.commit()
        conn.close()
        check_raises(
            "confirmation_consumed=1 with confirmation_status='none' raises CorruptStateError",
            store_mod.CorruptStateError, s.load_record, "i1",
        )
        s.close()


def test_41_duplicate_invocation_attempt_row_blocked_by_unique_constraint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        conn = sqlite3.connect(str(s.db_path))
        raised = False
        try:
            conn.execute(
                "INSERT INTO invocation_attempts (orchestration_instance_id, invocation_id, request_hash, authorized_at) VALUES (?, ?, ?, ?)",
                ("i1", "inv-forged", "hash-1", 0.0),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raised = True
        conn.close()
        check("the UNIQUE constraint blocks a second invocation_attempts row for the same instance, even via raw SQL", raised)
        s.close()


def test_42_transition_sequence_gap_detected_as_corrupt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        s.transition("i1", to_state="proposed", expected_transition_sequence_number=0)
        conn = sqlite3.connect(str(s.db_path))
        conn.execute("DELETE FROM transition_events WHERE orchestration_instance_id = ? AND sequence_number = 0", ("i1",))
        conn.commit()
        conn.close()
        check("a deleted transition_events row is detected by check_integrity", "i1" in s.check_integrity())
        s.close()


def test_43_check_integrity_reports_nothing_for_healthy_records() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        _advance_to_confirmed(s, "i1")
        check("a healthy record is not flagged", s.check_integrity() == [])
        s.close()


def test_44_corrupt_record_excluded_from_authorization_not_silently_repaired() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        conn = sqlite3.connect(str(s.db_path))
        conn.execute("UPDATE orchestration_records SET current_state = ? WHERE orchestration_instance_id = ?", ("not_a_real_state", "i1"))
        conn.commit()
        conn.close()
        # authorize_invocation reads the raw row directly (not via
        # _row_to_record), so it will not raise CorruptStateError itself --
        # but it also cannot succeed, since the state is not 'confirmed'
        # (fail closed either way, never a silent repair).
        exc_holder: list[Any] = []
        try:
            s.authorize_invocation("i1", request_hash="h1", confirmation_scope="h1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=0)
        except store_mod.AuthorizationFailedError as exc:
            exc_holder.append(exc)
        check("authorization on a corrupt-state record fails closed rather than proceeding", len(exc_holder) == 1)
        s.close()


# ---------------------------------------------------------------------------
# 45-50: Read-only inspection, safe summaries, redaction
# ---------------------------------------------------------------------------


def test_45_safe_summary_excludes_code_and_output_text() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        summary = s.safe_summary("i1")
        check("no 'code' key", "code" not in summary)
        check("no 'stdout' key", "stdout" not in summary)
        check("no 'stderr' key", "stderr" not in summary)
        check("no 'output_files' full-content key", "output_files" not in summary)
        s.close()


def test_46_list_records_filters_by_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        s.create_record(orchestration_instance_id="i2", session_id="s1")
        s.transition("i2", to_state="proposed", expected_transition_sequence_number=0)
        all_records = s.list_records()
        proposed_only = s.list_records(state="proposed")
        check("list_records returns both records", len(all_records) == 2)
        check("filtered list returns only the proposed one", len(proposed_only) == 1 and proposed_only[0].orchestration_instance_id == "i2")
        s.close()


def test_47_list_terminal_finds_completed_cancelled_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        s.transition("i1", to_state="blocked", expected_transition_sequence_number=0, extra_fields={"failure_category": "unsafe_request"})
        terminal = s.list_terminal()
        check("blocked instance appears in list_terminal", any(r.orchestration_instance_id == "i1" for r in terminal))
        s.close()


def test_48_list_expired_confirmations() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        clock = _FakeClock()
        s = _new_store(Path(tmp), clock=clock, ttl=100.0)
        _advance_to_confirmed(s, "i1")
        check("not expired immediately", s.list_expired_confirmations() == [])
        clock.advance(101.0)
        expired = s.list_expired_confirmations()
        check("expired after the TTL elapses", any(r.orchestration_instance_id == "i1" for r in expired))
        s.close()


def test_49_list_needs_review_returns_two_lists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = _new_store(Path(tmp))
        seq = _advance_to_confirmed(s, "i1")
        s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        needs_review, corrupt_ids = s.list_needs_review()
        check("ambiguous instance appears in needs_review", any(r.orchestration_instance_id == "i1" for r in needs_review))
        check("no corrupt ids for a healthy database", corrupt_ids == [])
        s.close()


def test_50_cli_list_and_show_do_not_mutate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "cli.db"
        s = store_mod.OrchestrationStateStore(db_path)
        s.initialize()
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        before = s.load_record("i1").to_safe_summary()
        s.close()

        exit_code_list = store_mod.main(["--db-path", str(db_path), "--list"])
        exit_code_show = store_mod.main(["--db-path", str(db_path), "--show", "i1"])
        check("--list exits 0", exit_code_list == 0)
        check("--show exits 0", exit_code_show == 0)

        s2 = store_mod.OrchestrationStateStore(db_path)
        after = s2.load_record("i1").to_safe_summary()
        s2.close()
        check("CLI inspection commands never mutate the record", before == after)


def test_50b_cli_list_needs_review_and_check_integrity_do_not_mutate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "cli2.db"
        s = store_mod.OrchestrationStateStore(db_path)
        s.initialize()
        seq = _advance_to_confirmed(s, "i1")
        s.authorize_invocation("i1", request_hash="hash-1", confirmation_scope="hash-1", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=seq)
        before = s.load_record("i1").to_safe_summary()
        s.close()

        exit_needs_review = store_mod.main(["--db-path", str(db_path), "--list-needs-review"])
        exit_integrity = store_mod.main(["--db-path", str(db_path), "--check-integrity"])
        check("--list-needs-review exits 0", exit_needs_review == 0)
        check("--check-integrity exits 0", exit_integrity == 0)

        s2 = store_mod.OrchestrationStateStore(db_path)
        after = s2.load_record("i1").to_safe_summary()
        s2.close()
        check("--list-needs-review and --check-integrity never mutate the record", before == after)


# ---------------------------------------------------------------------------
# 51: static content scan for raw code / secrets
# ---------------------------------------------------------------------------


def test_51_database_file_never_contains_raw_code_text() -> None:
    """A whole-file byte scan of the produced .db file for a distinctive
    substring of inline code that was digested but never itself stored."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "scan.db"
        s = store_mod.OrchestrationStateStore(db_path)
        s.initialize()
        distinctive_code = "x_UNIQUE_MARKER_7f3a9c = 2 + 2; print x_UNIQUE_MARKER_7f3a9c;"
        s.create_record(orchestration_instance_id="i1", session_id="s1")
        s.transition(
            "i1", to_state="proposed", expected_transition_sequence_number=0,
            extra_fields={"request_hash": "h1", "code_digest": store_mod.digest_code(distinctive_code)},
        )
        s.close()
        raw_bytes = db_path.read_bytes()
        check("the distinctive marker from the inline code is never found in the database file", b"UNIQUE_MARKER_7f3a9c" not in raw_bytes)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_tests() -> int:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception as exc:  # noqa: BLE001
            _failures.append(f"{name} raised an unexpected exception: {type(exc).__name__}: {exc}")
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")

    print()
    if _failures:
        print(f"{len(tests)} test function(s) run, {len(_failures)} check failure(s).")
        for f in _failures:
            print(f"  - {f}")
        print("SOME CHECKS FAILED.")
        return 1
    print(f"{len(tests)} test function(s) run, 0 check failure(s).")
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
