"""Cross-process concurrency and crash-simulation tests for
scripts/gauss_orchestration_state_store.py (v0.36.0 Durable Execution State
and Cross-Process Safety).

Uses the standard library `multiprocessing` module to launch genuinely
separate OS processes (not threads) that share one SQLite database file, to
verify this milestone's central claim: transactional duplicate-invocation
protection that holds across cooperating local processes, not just within
one process's own memory. All fake helpers only -- no GAUSS is run, invoked,
or referenced anywhere in this file.

Run directly:

    python scripts/test_gauss_orchestration_state_store_concurrency.py

See scripts/test_gauss_orchestration_state_store.py for single-process
schema/transaction/corruption tests (including all seven corruption
scenarios), and scripts/test_gauss_runtime_orchestration.py's v0.36.0
section for controller-level durable-store integration tests. This file
covers persistence-across-reopen, cross-process duplicate prevention,
concurrency (races, stale sequences, lock contention), and the four
crash-simulation scenarios specified in
planning/v0.36.0-durable-execution-state-and-cross-process-safety.md's
Crash-Recovery Model.
"""

from __future__ import annotations

import multiprocessing
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_orchestration_state_store as store_mod  # noqa: E402

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


def _seed_confirmed_record(
    db_path: str, instance_id: str, *, request_hash: str = "shared-hash", session_id: str = "s1", ttl: float = 1800.0
) -> int:
    """Drives a fresh record to 'confirmed' and returns the
    expected_transition_sequence_number a subsequent authorize_invocation
    call should use."""
    store = store_mod.OrchestrationStateStore(db_path, confirmation_ttl_seconds=ttl)
    store.initialize()
    store.create_record(orchestration_instance_id=instance_id, session_id=session_id)
    store.transition(instance_id, to_state="proposed", expected_transition_sequence_number=0, extra_fields={"request_hash": request_hash})
    store.transition(instance_id, to_state="awaiting_confirmation", expected_transition_sequence_number=1)
    store.record_confirmation(
        instance_id, scope=request_hash, timestamp="t1", session_id=session_id,
        expected_request_hash=request_hash, expected_transition_sequence_number=2,
    )
    store.close()
    return 3


# ---------------------------------------------------------------------------
# Multiprocessing worker functions -- must be top-level (picklable) for
# Windows' default "spawn" start method.
# ---------------------------------------------------------------------------


def _authorize_worker(db_path: str, instance_id: str, request_hash: str, session_id: str, invocation_id: str, expected_seq: int, result_queue: Any) -> None:
    store = store_mod.OrchestrationStateStore(db_path)
    store.initialize()
    try:
        store.authorize_invocation(
            instance_id, request_hash=request_hash, confirmation_scope=request_hash, session_id=session_id,
            invocation_id=invocation_id, expected_transition_sequence_number=expected_seq,
        )
        result_queue.put({"invocation_id": invocation_id, "success": True, "error": None})
    except store_mod.DurableStateError as exc:
        result_queue.put({"invocation_id": invocation_id, "success": False, "error": f"{type(exc).__name__}: {exc}"})


def _transition_worker(db_path: str, instance_id: str, to_state: str, expected_seq: int, result_queue: Any, label: str) -> None:
    store = store_mod.OrchestrationStateStore(db_path)
    store.initialize()
    try:
        store.transition(instance_id, to_state=to_state, expected_transition_sequence_number=expected_seq)
        result_queue.put({"label": label, "success": True, "error": None})
    except store_mod.DurableStateError as exc:
        result_queue.put({"label": label, "success": False, "error": f"{type(exc).__name__}: {exc}"})


def _hold_write_lock_then_release(db_path: str, hold_seconds: float, ready_event: Any) -> None:
    """Simulates real lock contention: opens its own raw connection, issues
    BEGIN IMMEDIATE (acquiring the write lock), signals readiness, holds it
    for hold_seconds, then commits and exits. Deliberately bypasses the
    public OrchestrationStateStore API to hold the lock for a controlled,
    precise duration."""
    import time as _time

    conn = sqlite3.connect(db_path, isolation_level=None, timeout=30.0)
    conn.execute("BEGIN IMMEDIATE")
    ready_event.set()
    _time.sleep(hold_seconds)
    conn.execute("COMMIT")
    conn.close()


def _crash_before_commit_worker(db_path: str, instance_id: str) -> None:
    """Simulates a process crashing mid-transaction: opens a raw connection,
    issues BEGIN IMMEDIATE, performs a partial UPDATE, then exits abruptly
    (os._exit, skipping COMMIT and any cleanup) -- SQLite's own rollback
    journal ensures this partial write is never visible to any other
    connection."""
    import os

    conn = sqlite3.connect(db_path, isolation_level=None, timeout=30.0)
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        "UPDATE orchestration_records SET invocation_id = 'PARTIAL-SHOULD-NEVER-BE-VISIBLE' "
        "WHERE orchestration_instance_id = ?",
        (instance_id,),
    )
    os._exit(1)  # no commit, no clean close -- simulates a hard crash


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def test_01_record_survives_store_reopen() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "persist.db")
        s1 = store_mod.OrchestrationStateStore(db_path)
        s1.initialize()
        s1.create_record(orchestration_instance_id="i1", session_id="s1")
        s1.close()

        s2 = store_mod.OrchestrationStateStore(db_path)
        s2.initialize()
        rec = s2.load_record("i1")
        check("record survives a fresh store instance re-opening the same file", rec.orchestration_instance_id == "i1")
        s2.close()


def test_02_confirmation_survives_restart_before_expiry() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "persist.db")
        _seed_confirmed_record(db_path, "i1", ttl=1800.0)
        s2 = store_mod.OrchestrationStateStore(db_path, confirmation_ttl_seconds=1800.0)
        s2.initialize()
        rec = s2.load_record("i1")
        check("confirmation status survives reopen", rec.confirmation_status == "accepted")
        check("confirmation not consumed", rec.confirmation_consumed is False)
        s2.authorize_invocation("i1", request_hash="shared-hash", confirmation_scope="shared-hash", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=3)
        check("authorization succeeds after reopen, before expiry", s2.load_record("i1").current_state == "executing")
        s2.close()


def test_03_consumed_confirmation_survives_restart() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "persist.db")
        _seed_confirmed_record(db_path, "i1")
        s1 = store_mod.OrchestrationStateStore(db_path)
        s1.initialize()
        s1.authorize_invocation("i1", request_hash="shared-hash", confirmation_scope="shared-hash", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=3)
        s1.close()

        s2 = store_mod.OrchestrationStateStore(db_path)
        s2.initialize()
        rec = s2.load_record("i1")
        check("confirmation remains consumed after reopen", rec.confirmation_consumed is True)
        check_raises(
            "a second authorization attempt after reopen is still refused",
            store_mod.AuthorizationFailedError,
            s2.authorize_invocation, "i1", request_hash="shared-hash", confirmation_scope="shared-hash", session_id="s1", invocation_id="inv2", expected_transition_sequence_number=rec.transition_sequence_number,
        )
        s2.close()


def test_04_execution_result_and_terminal_state_survive_restart() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "persist.db")
        _seed_confirmed_record(db_path, "i1")
        s1 = store_mod.OrchestrationStateStore(db_path)
        s1.initialize()
        s1.authorize_invocation("i1", request_hash="shared-hash", confirmation_scope="shared-hash", session_id="s1", invocation_id="inv1", expected_transition_sequence_number=3)
        s1.record_execution_result(
            "i1", to_state="execution_completed", execution_status="completed", exit_code=0,
            output_file_count=0, validation_ok=True, validation_problems=(), failure_category=None,
            expected_transition_sequence_number=4,
        )
        s1.close()

        s2 = store_mod.OrchestrationStateStore(db_path)
        s2.initialize()
        rec = s2.load_record("i1")
        check("execution_status survives reopen", rec.execution_status == "completed")
        check("state survives reopen", rec.current_state == "execution_completed")
        s2.close()


def test_05_transition_history_remains_ordered_across_reopen() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "persist.db")
        _seed_confirmed_record(db_path, "i1")
        s2 = store_mod.OrchestrationStateStore(db_path)
        s2.initialize()
        history = s2.get_transition_history("i1")
        check("three transitions present after reopen", len(history) == 3)
        check("history is ordered by sequence_number", [h.sequence_number for h in history] == sorted(h.sequence_number for h in history))
        s2.close()


# ---------------------------------------------------------------------------
# Duplicate prevention (genuine cross-process)
# ---------------------------------------------------------------------------


def test_06_two_processes_race_only_one_authorizes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "race.db")
        expected_seq = _seed_confirmed_record(db_path, "i-race")
        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        procs = [
            ctx.Process(target=_authorize_worker, args=(db_path, "i-race", "shared-hash", "s1", f"inv-{i}", expected_seq, q))
            for i in range(5)
        ]
        for p in procs:
            p.start()
        for p in procs:
            p.join(timeout=60)
        results = [q.get(timeout=10) for _ in procs]

        successes = [r for r in results if r["success"]]
        failures = [r for r in results if not r["success"]]
        check("exactly one of five racing processes succeeded", len(successes) == 1)
        check("the other four failed closed (DurableStateError)", len(failures) == 4)

        store = store_mod.OrchestrationStateStore(db_path)
        store.initialize()
        rec = store.load_record("i-race")
        check(
            "the durable record's invocation_id is exactly the winner's",
            successes and rec.invocation_id == successes[0]["invocation_id"],
        )
        store.close()


def test_07_repeated_event_delivery_does_not_reauthorize() -> None:
    """Simulates a duplicate-delivered message: the exact same
    invocation_id, submitted twice from two separate processes -- the
    second delivery must be refused, never silently treated as a no-op
    success."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "dup-event.db")
        expected_seq = _seed_confirmed_record(db_path, "i-dup")
        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        p1 = ctx.Process(target=_authorize_worker, args=(db_path, "i-dup", "shared-hash", "s1", "same-invocation-id", expected_seq, q))
        p1.start()
        p1.join(timeout=30)
        first = q.get(timeout=10)
        check("first delivery succeeds", first["success"] is True)

        store = store_mod.OrchestrationStateStore(db_path)
        store.initialize()
        seq_now = store.load_record("i-dup").transition_sequence_number
        store.close()

        p2 = ctx.Process(target=_authorize_worker, args=(db_path, "i-dup", "shared-hash", "s1", "same-invocation-id", seq_now, q))
        p2.start()
        p2.join(timeout=30)
        second = q.get(timeout=10)
        check("repeated delivery of the same invocation_id is refused, not silently accepted", second["success"] is False)


def test_08_process_restart_does_not_reset_duplicate_protection() -> None:
    """The first authorizing process exits completely (its Python process
    object is gone) before a second, brand-new process attempts the same
    instance -- duplicate protection must still hold, since it lives in the
    durable file, not in either process's memory."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "restart-dup.db")
        expected_seq = _seed_confirmed_record(db_path, "i-restart")
        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        p1 = ctx.Process(target=_authorize_worker, args=(db_path, "i-restart", "shared-hash", "s1", "inv-first-process", expected_seq, q))
        p1.start()
        p1.join(timeout=30)
        check("first process's authorization succeeded", q.get(timeout=10)["success"] is True)
        check("first process has fully exited", p1.is_alive() is False)

        store = store_mod.OrchestrationStateStore(db_path)
        store.initialize()
        seq_now = store.load_record("i-restart").transition_sequence_number
        store.close()

        p2 = ctx.Process(target=_authorize_worker, args=(db_path, "i-restart", "shared-hash", "s1", "inv-second-process", seq_now, q))
        p2.start()
        p2.join(timeout=30)
        check("a wholly new second process is still refused", q.get(timeout=10)["success"] is False)


def test_09_same_code_new_request_may_proceed_cross_process() -> None:
    """Two independent orchestration_instance_ids sharing one request_hash,
    each authorized by its OWN separate process, must both succeed -- exactly
    mirroring the single-process test_32 (Stage 2) but now genuinely
    cross-process."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "shared-hash-cross-process.db")
        seq_a = _seed_confirmed_record(db_path, "i-cp-a", request_hash="shared-hash-2")
        seq_b = _seed_confirmed_record(db_path, "i-cp-b", request_hash="shared-hash-2")
        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        pa = ctx.Process(target=_authorize_worker, args=(db_path, "i-cp-a", "shared-hash-2", "s1", "inv-a", seq_a, q))
        pb = ctx.Process(target=_authorize_worker, args=(db_path, "i-cp-b", "shared-hash-2", "s1", "inv-b", seq_b, q))
        pa.start()
        pb.start()
        pa.join(timeout=30)
        pb.join(timeout=30)
        results = {r["invocation_id"]: r["success"] for r in (q.get(timeout=10), q.get(timeout=10))}
        check("both independent, distinct-instance requests succeed", results.get("inv-a") is True and results.get("inv-b") is True)


# ---------------------------------------------------------------------------
# Concurrency: stale sequence, lock contention
# ---------------------------------------------------------------------------


def test_10_cross_process_stale_transition_sequence_fails() -> None:
    """Two processes both target the SAME starting transition_sequence_
    number for a non-authorization transition (submit_for_review's
    collecting_inputs -> proposed analogue) -- only one may win; the other
    must fail with StaleTransitionError specifically (this scenario, unlike
    authorize_invocation's richer precondition chain, isolates the raw
    optimistic-concurrency guard on its own)."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "stale.db")
        store = store_mod.OrchestrationStateStore(db_path)
        store.initialize()
        store.create_record(orchestration_instance_id="i-stale", session_id="s1")
        store.close()

        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        p1 = ctx.Process(target=_transition_worker, args=(db_path, "i-stale", "proposed", 0, q, "first"))
        p2 = ctx.Process(target=_transition_worker, args=(db_path, "i-stale", "blocked", 0, q, "second"))
        p1.start()
        p2.start()
        p1.join(timeout=30)
        p2.join(timeout=30)
        results = [q.get(timeout=10), q.get(timeout=10)]
        successes = [r for r in results if r["success"]]
        losers = [r for r in results if not r["success"]]
        check("exactly one of the two competing transitions succeeded", len(successes) == 1)
        check("the loser failed specifically due to a stale sequence number", losers and "StaleTransitionError" in losers[0]["error"])


def test_11_lock_contention_produces_a_bounded_wait_or_lock_contention_error_never_corruption() -> None:
    """A holder process acquires and holds the write lock for a short,
    controlled duration via a raw BEGIN IMMEDIATE; a competitor process,
    configured with a deliberately short busy_timeout, attempts an
    authorization while the lock is held. It must either wait successfully
    (if it happens to acquire before its own timeout) or fail closed with
    LockContentionError -- never observe or write a corrupted intermediate
    state."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "contention.db")
        expected_seq = _seed_confirmed_record(db_path, "i-contend")

        ctx = multiprocessing.get_context("spawn")
        ready = ctx.Event()
        holder = ctx.Process(target=_hold_write_lock_then_release, args=(db_path, 1.5, ready))
        holder.start()
        ready.wait(timeout=10)

        store = store_mod.OrchestrationStateStore(db_path, busy_timeout_ms=200)
        outcome: dict[str, Any] = {}
        try:
            store.authorize_invocation(
                "i-contend", request_hash="shared-hash", confirmation_scope="shared-hash", session_id="s1",
                invocation_id="inv-contend", expected_transition_sequence_number=expected_seq,
            )
            outcome["kind"] = "succeeded"
        except store_mod.LockContentionError:
            outcome["kind"] = "lock_contention"
        except store_mod.DurableStateError as exc:
            outcome["kind"] = f"other_durable_error:{type(exc).__name__}"
        finally:
            store.close()
        holder.join(timeout=10)

        check(
            "a short busy_timeout under real contention either succeeds or fails closed with LockContentionError, never anything else",
            outcome["kind"] in ("succeeded", "lock_contention"),
        )

        store2 = store_mod.OrchestrationStateStore(db_path)
        store2.initialize()
        rec = store2.load_record("i-contend")
        check(
            "the record is never left in an inconsistent state regardless of the contention outcome",
            rec.current_state in ("confirmed", "executing"),
        )
        store2.close()


# ---------------------------------------------------------------------------
# Crash simulations (the four scenarios named in the planning document)
# ---------------------------------------------------------------------------


def test_12_crash_before_authorization_commit_leaves_no_trace() -> None:
    """Scenario 1: crash before the authorization commit. Expected: no
    invocation authorized; confirmation remains unconsumed."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "crash1.db")
        _seed_confirmed_record(db_path, "i-crash1")

        ctx = multiprocessing.get_context("spawn")
        p = ctx.Process(target=_crash_before_commit_worker, args=(db_path, "i-crash1"))
        p.start()
        p.join(timeout=30)
        check("the simulated-crash process actually exited", p.exitcode is not None)

        store = store_mod.OrchestrationStateStore(db_path)
        store.initialize()
        rec = store.load_record("i-crash1")
        check("no partial write is visible after the simulated crash", rec.invocation_id is None)
        check("confirmation remains unconsumed", rec.confirmation_consumed is False)
        check("state is still confirmed, not executing", rec.current_state == "confirmed")
        # A subsequent, real authorization must still succeed normally.
        store.authorize_invocation(
            "i-crash1", request_hash="shared-hash", confirmation_scope="shared-hash", session_id="s1",
            invocation_id="inv-after-crash1", expected_transition_sequence_number=rec.transition_sequence_number,
        )
        check("a fresh authorization after the simulated crash succeeds normally", store.load_record("i-crash1").current_state == "executing")
        store.close()


def test_13_crash_after_authorization_commit_before_helper_call_is_ambiguous() -> None:
    """Scenario 2: crash after the authorization commit but before the
    injected helper is ever called. Expected: invocation marked ambiguous
    (in_progress, no result); no automatic retry -- surfaced by the
    read-only inspection tooling as requiring manual review."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "crash2.db")
        expected_seq = _seed_confirmed_record(db_path, "i-crash2")
        store = store_mod.OrchestrationStateStore(db_path)
        store.initialize()
        store.authorize_invocation(
            "i-crash2", request_hash="shared-hash", confirmation_scope="shared-hash", session_id="s1",
            invocation_id="inv-crash2", expected_transition_sequence_number=expected_seq,
        )
        # Deliberately never call any "helper" and never call
        # record_execution_result -- simulating the process dying right here.
        store.close()

        store2 = store_mod.OrchestrationStateStore(db_path)
        store2.initialize()
        rec = store2.load_record("i-crash2")
        check("state is executing", rec.current_state == "executing")
        check("no execution_status was ever recorded", rec.execution_status is None)
        ambiguous = store2.list_ambiguous_invocations()
        check("this record is surfaced as ambiguous / requiring manual review", any(r.orchestration_instance_id == "i-crash2" for r in ambiguous))
        store2.close()


def test_14_crash_after_helper_call_before_result_persistence_is_also_ambiguous() -> None:
    """Scenario 3: crash after a (fake) helper call returns but before the
    result is durably persisted. This layer cannot distinguish this from
    scenario 2 without a helper/schema change (out of scope, a stop
    condition) -- the durable signature and the required disclosure are
    identical: ambiguous, never silently resolved either way."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "crash3.db")
        expected_seq = _seed_confirmed_record(db_path, "i-crash3")
        store = store_mod.OrchestrationStateStore(db_path)
        store.initialize()
        store.authorize_invocation(
            "i-crash3", request_hash="shared-hash", confirmation_scope="shared-hash", session_id="s1",
            invocation_id="inv-crash3", expected_transition_sequence_number=expected_seq,
        )
        # Simulate a fake helper call happening and returning -- but the
        # process "crashes" before record_execution_result is ever called.
        _fake_helper_result = {"executed": True, "execution_status": "completed", "exit_code": 0, "stdout": "4", "stderr": "", "output_files": [], "warnings": [], "errors": []}
        del _fake_helper_result  # the result exists locally but is never persisted -- exactly the point
        store.close()

        store2 = store_mod.OrchestrationStateStore(db_path)
        store2.initialize()
        rec = store2.load_record("i-crash3")
        check("same durable signature as scenario 2: executing, no execution_status", rec.current_state == "executing" and rec.execution_status is None)
        check("surfaced as ambiguous, identically to scenario 2", any(r.orchestration_instance_id == "i-crash3" for r in store2.list_ambiguous_invocations()))
        store2.close()


def test_15_crash_after_result_persistence_preserves_evidence_for_safe_continuation() -> None:
    """Scenario 4: crash after the result is durably persisted. Expected:
    reload returns the preserved result; terminal progression may continue
    safely (observed here as: the record is no longer ambiguous, and its
    safe evidence is fully intact for a reader)."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "crash4.db")
        expected_seq = _seed_confirmed_record(db_path, "i-crash4")
        store = store_mod.OrchestrationStateStore(db_path)
        store.initialize()
        store.authorize_invocation(
            "i-crash4", request_hash="shared-hash", confirmation_scope="shared-hash", session_id="s1",
            invocation_id="inv-crash4", expected_transition_sequence_number=expected_seq,
        )
        store.record_execution_result(
            "i-crash4", to_state="execution_completed", execution_status="completed", exit_code=0,
            output_file_count=1, validation_ok=True, validation_problems=(), failure_category=None,
            expected_transition_sequence_number=expected_seq + 1,
        )
        # Simulate the process crashing immediately after this commit.
        store.close()

        store2 = store_mod.OrchestrationStateStore(db_path)
        store2.initialize()
        rec = store2.load_record("i-crash4")
        check("execution_status preserved across the simulated crash", rec.execution_status == "completed")
        check("output_file_count preserved", rec.output_file_count == 1)
        check("no longer ambiguous", not any(r.orchestration_instance_id == "i-crash4" for r in store2.list_ambiguous_invocations()))
        check("state is execution_completed, safe for a caller to continue from", rec.current_state == "execution_completed")
        store2.close()


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
