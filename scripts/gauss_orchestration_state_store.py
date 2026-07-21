"""Durable orchestration state store (v0.36.0 Durable Execution State and
Cross-Process Safety).

Authoritative design source: `planning/v0.36.0-durable-execution-state-and-
cross-process-safety.md`. This module implements that plan's data model,
transaction boundaries, locking model, crash-recovery model, confirmation-
expiry policy, and corruption behavior -- it does not redefine them.

Storage technology: the Python standard library's `sqlite3` module only. No
third-party database or ORM is used or required.

**This module never imports, invokes, or knows about real GAUSS.** It has no
dependency on `scripts/gauss_code_execution.py`, `scripts/gauss_execution_
adapter.py`, or `scripts/gauss_runtime_orchestration.py` -- the dependency
direction is the reverse: the controller (`gauss_runtime_orchestration.py`)
may import this module, but this module never imports the controller, the
adapter, or the helper. This module never launches a subprocess and never
detects a GAUSS environment.

**Never persisted, by design** (mirroring the two existing "safe summary"
precedents already established elsewhere in this codebase -- neither
`OrchestrationRecord.to_safe_summary()` nor `gauss_execution_adapter.safe_
summary(...)` has ever included raw code or stdout/stderr text): raw inline
GAUSS code (only a SHA-256 digest is stored), stdout/stderr text, raw
output-file content, secrets or credentials, environment-variable values,
raw conversation text.

Support claim (see the planning document's own "Support Claim" section for
the full statement): one local machine, multiple cooperating Python
processes, one shared SQLite database file, transactional duplicate-
invocation protection scoped to one orchestration instance. This module does
NOT claim distributed exactly-once execution, multi-machine coordination,
protection across different database files, protection against manual
database tampering, or crash-safe knowledge of whether a real GAUSS process
actually launched near the invocation-authorization boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

SCHEMA_VERSION = 1
DEFAULT_CONFIRMATION_TTL_SECONDS = 1800.0  # 30 minutes; see planning doc's Confirmation-Expiry Policy
DEFAULT_BUSY_TIMEOUT_MS = 5000
DEFAULT_STATE_DIR_NAME = ".gauss_orchestration_state"
DEFAULT_DB_FILENAME = "orchestration.db"
_MAX_STORED_VALIDATION_PROBLEMS = 50

# Mirrors gauss_runtime_orchestration.OrchestrationState's .value strings.
# Deliberately duplicated here, not imported -- this module must never
# depend on the controller (see module docstring's stated import direction).
KNOWN_STATES = frozenset(
    {
        "advisory",
        "collecting_inputs",
        "proposed",
        "awaiting_confirmation",
        "confirmed",
        "executing",
        "execution_completed",
        "execution_failed",
        "analyzing",
        "report_generating",
        "completed",
        "cancelled",
        "blocked",
    }
)
TERMINAL_STATES = frozenset({"completed", "cancelled", "blocked"})
KNOWN_CONFIRMATION_STATUSES = frozenset(
    {"none", "requested", "accepted", "rejected", "stale", "invalidated", "consumed", "expired"}
)
KNOWN_INVOCATION_STATUSES = frozenset({"not_invoked", "in_progress", "returned", "failed_to_launch"})


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class DurableStateError(Exception):
    """Base class for every error this module raises. Every failure mode in
    this module fails closed: no method returns a success value while also
    leaving the database in a state inconsistent with that success."""


class SchemaVersionError(DurableStateError):
    """The database's own recorded schema_version does not match this
    module's SCHEMA_VERSION. Refuses to proceed rather than silently
    attempt an un-reviewed migration."""


class CorruptStateError(DurableStateError):
    """Stored data is internally inconsistent (malformed JSON, an impossible
    confirmation state, a transition-sequence gap/duplicate, an unrecognized
    state value). Never automatically repaired."""


class RecordNotFoundError(DurableStateError):
    """No durable record exists for the given orchestration_instance_id."""


class DuplicateRecordError(DurableStateError):
    """create_record was called for an orchestration_instance_id that
    already has a durable record."""


class StaleTransitionError(DurableStateError):
    """The caller's expected_transition_sequence_number did not match the
    durable record's own -- a lost-update guard. Another writer already
    advanced this record since the caller last read it."""


class LockContentionError(DurableStateError):
    """A transaction could not acquire the database's write lock within
    busy_timeout. The caller may retry with a new, explicit call -- this
    module never retries automatically."""


class AuthorizationFailedError(DurableStateError):
    """authorize_invocation's atomic preconditions were not all satisfied.

    `reason_category` is one of: "record_not_found", "wrong_state",
    "hash_mismatch", "session_mismatch", "confirmation_not_accepted",
    "confirmation_scope_mismatch", "confirmation_expired", "already_invoked".
    """

    def __init__(self, reason_category: str, detail: str) -> None:
        super().__init__(f"{reason_category}: {detail}")
        self.reason_category = reason_category
        self.detail = detail


# ---------------------------------------------------------------------------
# Durable record (read-only view)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DurableRecord:
    orchestration_instance_id: str
    session_id: str
    canonical_request_id: str | None
    request_hash: str | None
    code_digest: str | None
    current_state: str
    previous_state: str | None
    confirmation_status: str
    confirmation_scope: str | None
    confirmation_timestamp: str | None
    confirmation_consumed: bool
    confirmation_expires_at: float | None
    invocation_status: str
    invocation_id: str | None
    execution_status: str | None
    exit_code: int | None
    output_file_count: int | None
    validation_ok: bool | None
    validation_problems: tuple[str, ...]
    failure_category: str | None
    cancellation_status: str
    analysis_status: str
    report_status: str
    transition_sequence_number: int
    created_at: float
    last_transition_at: float
    schema_version: int

    def to_safe_summary(self) -> dict[str, Any]:
        """Excludes code, stdout/stderr, output-file content, secrets, and
        raw conversation text -- there is nothing to exclude here that was
        ever stored in the first place; this mirrors the exclusion set
        already established by `OrchestrationRecord.to_safe_summary()` and
        `gauss_execution_adapter.safe_summary(...)`."""
        return {
            "orchestration_instance_id": self.orchestration_instance_id,
            "session_id": self.session_id,
            "canonical_request_id": self.canonical_request_id,
            "request_hash": self.request_hash,
            "code_digest": self.code_digest,
            "current_state": self.current_state,
            "previous_state": self.previous_state,
            "confirmation_status": self.confirmation_status,
            "confirmation_consumed": self.confirmation_consumed,
            "confirmation_expires_at": self.confirmation_expires_at,
            "invocation_status": self.invocation_status,
            "invocation_id": self.invocation_id,
            "execution_status": self.execution_status,
            "exit_code": self.exit_code,
            "output_file_count": self.output_file_count,
            "validation_ok": self.validation_ok,
            "validation_problems": list(self.validation_problems),
            "failure_category": self.failure_category,
            "cancellation_status": self.cancellation_status,
            "analysis_status": self.analysis_status,
            "report_status": self.report_status,
            "transition_sequence_number": self.transition_sequence_number,
            "created_at": self.created_at,
            "last_transition_at": self.last_transition_at,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class TransitionEventRecord:
    sequence_number: int
    from_state: str
    to_state: str
    at: float
    note: str


def digest_code(code: str | None) -> str | None:
    """SHA-256 hex digest of inline code text -- never the code itself.
    Deterministic, matching the same hashlib already used (for a different
    purpose) in gauss_runtime_orchestration.py's request-hash computation."""
    if code is None:
        return None
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Default storage location
# ---------------------------------------------------------------------------


def default_db_path() -> Path:
    """<repository_root>/.gauss_orchestration_state/orchestration.db.

    Never a system temp directory and never a user-provided working/output
    directory -- both would risk mixing application state with GAUSS
    execution sandboxes or colliding across unrelated invocations. The
    parent directory is NOT created here -- only OrchestrationStateStore.
    __init__ creates it, deliberately, only when a store is actually
    constructed."""
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / DEFAULT_STATE_DIR_NAME / DEFAULT_DB_FILENAME


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------


class OrchestrationStateStore:
    """A durable, SQLite-backed orchestration state store.

    Every write method is one atomic SQLite transaction (BEGIN IMMEDIATE ..
    COMMIT/ROLLBACK, explicit -- not relying on Python's sqlite3 implicit
    transaction defaults, which vary across Python versions). BEGIN
    IMMEDIATE acquires the write lock at the start of the transaction, so
    two concurrent writers targeting the same record serialize correctly:
    the second blocks (up to busy_timeout) until the first commits or rolls
    back, then observes the first's committed change and fails its own
    precondition checks accordingly -- no separate application-level lock
    is used or needed.
    """

    def __init__(
        self,
        db_path: str | Path,
        *,
        clock: Any = time.time,
        confirmation_ttl_seconds: float = DEFAULT_CONFIRMATION_TTL_SECONDS,
        busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    ) -> None:
        self.db_path = Path(db_path)
        self._clock = clock
        self._confirmation_ttl_seconds = confirmation_ttl_seconds
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), isolation_level=None, timeout=busy_timeout_ms / 1000.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
        self._conn.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "OrchestrationStateStore":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    # -- transaction helper --------------------------------------------------

    @contextmanager
    def _immediate_txn(self) -> Iterator[None]:
        try:
            self._conn.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower():
                raise LockContentionError(f"could not acquire the write lock: {exc}") from exc
            raise
        try:
            yield
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        else:
            self._conn.execute("COMMIT")

    # -- initialization --------------------------------------------------------

    def initialize(self) -> None:
        """Idempotent: safe to call every time a store is constructed. Fails
        closed with SchemaVersionError if the database already exists with a
        different schema_version than this module's SCHEMA_VERSION -- no
        automatic migration is attempted."""
        with self._immediate_txn():
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_meta ("
                "  id INTEGER PRIMARY KEY CHECK (id = 1),"
                "  schema_version INTEGER NOT NULL,"
                "  created_at REAL NOT NULL"
                ")"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS orchestration_records ("
                "  orchestration_instance_id TEXT PRIMARY KEY,"
                "  session_id TEXT NOT NULL,"
                "  canonical_request_id TEXT,"
                "  request_hash TEXT,"
                "  code_digest TEXT,"
                "  current_state TEXT NOT NULL,"
                "  previous_state TEXT,"
                "  confirmation_status TEXT NOT NULL DEFAULT 'none',"
                "  confirmation_scope TEXT,"
                "  confirmation_timestamp TEXT,"
                "  confirmation_consumed INTEGER NOT NULL DEFAULT 0 CHECK (confirmation_consumed IN (0,1)),"
                "  confirmation_expires_at REAL,"
                "  invocation_status TEXT NOT NULL DEFAULT 'not_invoked',"
                "  invocation_id TEXT,"
                "  execution_status TEXT,"
                "  exit_code INTEGER,"
                "  output_file_count INTEGER,"
                "  validation_ok INTEGER,"
                "  validation_problems TEXT NOT NULL DEFAULT '[]',"
                "  failure_category TEXT,"
                "  cancellation_status TEXT NOT NULL DEFAULT 'not_cancelled',"
                "  analysis_status TEXT NOT NULL DEFAULT 'not_started',"
                "  report_status TEXT NOT NULL DEFAULT 'not_requested',"
                "  transition_sequence_number INTEGER NOT NULL DEFAULT 0,"
                "  created_at REAL NOT NULL,"
                "  last_transition_at REAL NOT NULL,"
                "  schema_version INTEGER NOT NULL"
                ")"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS transition_events ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  orchestration_instance_id TEXT NOT NULL,"
                "  sequence_number INTEGER NOT NULL,"
                "  from_state TEXT NOT NULL,"
                "  to_state TEXT NOT NULL,"
                "  at REAL NOT NULL,"
                "  note TEXT NOT NULL DEFAULT '',"
                "  UNIQUE (orchestration_instance_id, sequence_number),"
                "  FOREIGN KEY (orchestration_instance_id) REFERENCES orchestration_records (orchestration_instance_id)"
                ")"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS invocation_attempts ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  orchestration_instance_id TEXT NOT NULL UNIQUE,"
                "  invocation_id TEXT NOT NULL,"
                "  request_hash TEXT NOT NULL,"
                "  authorized_at REAL NOT NULL,"
                "  FOREIGN KEY (orchestration_instance_id) REFERENCES orchestration_records (orchestration_instance_id)"
                ")"
            )
            row = self._conn.execute("SELECT schema_version FROM schema_meta WHERE id = 1").fetchone()
            if row is None:
                self._conn.execute(
                    "INSERT INTO schema_meta (id, schema_version, created_at) VALUES (1, ?, ?)",
                    (SCHEMA_VERSION, self._clock()),
                )
            elif row["schema_version"] != SCHEMA_VERSION:
                raise SchemaVersionError(
                    f"database schema_version {row['schema_version']} does not match this module's "
                    f"SCHEMA_VERSION {SCHEMA_VERSION}; refusing to proceed without an explicit, "
                    "reviewed migration."
                )

    # -- record creation / loading -------------------------------------------

    def create_record(
        self,
        *,
        orchestration_instance_id: str,
        session_id: str,
        canonical_request_id: str | None = None,
        current_state: str = "collecting_inputs",
        created_at: float | None = None,
    ) -> None:
        if current_state not in KNOWN_STATES:
            raise ValueError(f"unknown state {current_state!r}")
        now = created_at if created_at is not None else self._clock()
        try:
            with self._immediate_txn():
                self._conn.execute(
                    "INSERT INTO orchestration_records "
                    "(orchestration_instance_id, session_id, canonical_request_id, current_state, "
                    " created_at, last_transition_at, schema_version) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (orchestration_instance_id, session_id, canonical_request_id, current_state, now, now, SCHEMA_VERSION),
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicateRecordError(f"a durable record already exists for {orchestration_instance_id!r}") from exc

    def _row_to_record(self, row: sqlite3.Row) -> DurableRecord:
        try:
            problems = tuple(json.loads(row["validation_problems"]))
        except (json.JSONDecodeError, TypeError) as exc:
            raise CorruptStateError(
                f"validation_problems for {row['orchestration_instance_id']!r} is not valid JSON: {exc}"
            ) from exc
        if row["current_state"] not in KNOWN_STATES:
            raise CorruptStateError(
                f"{row['orchestration_instance_id']!r} has an unrecognized current_state {row['current_state']!r}"
            )
        if bool(row["confirmation_consumed"]) and row["confirmation_status"] != "consumed":
            raise CorruptStateError(
                f"{row['orchestration_instance_id']!r} has confirmation_consumed=1 but "
                f"confirmation_status={row['confirmation_status']!r} -- an impossible confirmation state."
            )
        return DurableRecord(
            orchestration_instance_id=row["orchestration_instance_id"],
            session_id=row["session_id"],
            canonical_request_id=row["canonical_request_id"],
            request_hash=row["request_hash"],
            code_digest=row["code_digest"],
            current_state=row["current_state"],
            previous_state=row["previous_state"],
            confirmation_status=row["confirmation_status"],
            confirmation_scope=row["confirmation_scope"],
            confirmation_timestamp=row["confirmation_timestamp"],
            confirmation_consumed=bool(row["confirmation_consumed"]),
            confirmation_expires_at=row["confirmation_expires_at"],
            invocation_status=row["invocation_status"],
            invocation_id=row["invocation_id"],
            execution_status=row["execution_status"],
            exit_code=row["exit_code"],
            output_file_count=row["output_file_count"],
            validation_ok=(bool(row["validation_ok"]) if row["validation_ok"] is not None else None),
            validation_problems=problems,
            failure_category=row["failure_category"],
            cancellation_status=row["cancellation_status"],
            analysis_status=row["analysis_status"],
            report_status=row["report_status"],
            transition_sequence_number=row["transition_sequence_number"],
            created_at=row["created_at"],
            last_transition_at=row["last_transition_at"],
            schema_version=row["schema_version"],
        )

    def load_record(self, orchestration_instance_id: str) -> DurableRecord:
        row = self._conn.execute(
            "SELECT * FROM orchestration_records WHERE orchestration_instance_id = ?",
            (orchestration_instance_id,),
        ).fetchone()
        if row is None:
            raise RecordNotFoundError(orchestration_instance_id)
        return self._row_to_record(row)

    def record_exists(self, orchestration_instance_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM orchestration_records WHERE orchestration_instance_id = ?",
            (orchestration_instance_id,),
        ).fetchone()
        return row is not None

    def _fetch_for_update(self, orchestration_instance_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM orchestration_records WHERE orchestration_instance_id = ?",
            (orchestration_instance_id,),
        ).fetchone()

    # -- generic transition (used for every transition except confirmation
    #    and invocation authorization, which have their own richer atomic
    #    operations below) -----------------------------------------------------

    def transition(
        self,
        orchestration_instance_id: str,
        *,
        to_state: str,
        note: str = "",
        expected_transition_sequence_number: int,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        if to_state not in KNOWN_STATES:
            raise ValueError(f"unknown state {to_state!r}")
        extra_fields = dict(extra_fields or {})
        now = self._clock()
        with self._immediate_txn():
            row = self._fetch_for_update(orchestration_instance_id)
            if row is None:
                raise RecordNotFoundError(orchestration_instance_id)
            if row["transition_sequence_number"] != expected_transition_sequence_number:
                raise StaleTransitionError(
                    f"expected transition_sequence_number {expected_transition_sequence_number} for "
                    f"{orchestration_instance_id!r}, but the durable record is at "
                    f"{row['transition_sequence_number']}; another writer already advanced it."
                )
            from_state = row["current_state"]
            set_clauses = [
                "current_state = ?",
                "previous_state = ?",
                "transition_sequence_number = transition_sequence_number + 1",
                "last_transition_at = ?",
            ]
            params: list[Any] = [to_state, from_state, now]
            for key, value in extra_fields.items():
                set_clauses.append(f"{key} = ?")
                params.append(value)
            params.extend([orchestration_instance_id, expected_transition_sequence_number])
            cur = self._conn.execute(
                f"UPDATE orchestration_records SET {', '.join(set_clauses)} "
                "WHERE orchestration_instance_id = ? AND transition_sequence_number = ?",
                params,
            )
            if cur.rowcount != 1:
                raise StaleTransitionError(
                    f"transition for {orchestration_instance_id!r} lost a race with a concurrent writer."
                )
            self._conn.execute(
                "INSERT INTO transition_events (orchestration_instance_id, sequence_number, from_state, "
                "to_state, at, note) VALUES (?, ?, ?, ?, ?, ?)",
                (orchestration_instance_id, expected_transition_sequence_number, from_state, to_state, now, note),
            )

    def update_fields(
        self,
        orchestration_instance_id: str,
        *,
        expected_transition_sequence_number: int,
        **fields: Any,
    ) -> None:
        """A non-transitioning field update (e.g. recording cancellation
        intent while EXECUTING, which does not itself change current_state).
        Still guarded by the same optimistic-concurrency check as every
        other write."""
        if not fields:
            return
        now = self._clock()
        with self._immediate_txn():
            row = self._fetch_for_update(orchestration_instance_id)
            if row is None:
                raise RecordNotFoundError(orchestration_instance_id)
            if row["transition_sequence_number"] != expected_transition_sequence_number:
                raise StaleTransitionError(
                    f"expected transition_sequence_number {expected_transition_sequence_number} for "
                    f"{orchestration_instance_id!r}, but the durable record is at "
                    f"{row['transition_sequence_number']}."
                )
            set_clauses = [f"{key} = ?" for key in fields] + ["last_transition_at = ?"]
            params = list(fields.values()) + [now, orchestration_instance_id, expected_transition_sequence_number]
            cur = self._conn.execute(
                f"UPDATE orchestration_records SET {', '.join(set_clauses)} "
                "WHERE orchestration_instance_id = ? AND transition_sequence_number = ?",
                params,
            )
            if cur.rowcount != 1:
                raise StaleTransitionError(
                    f"field update for {orchestration_instance_id!r} lost a race with a concurrent writer."
                )

    # -- confirmation ------------------------------------------------------

    def record_confirmation(
        self,
        orchestration_instance_id: str,
        *,
        scope: str,
        timestamp: str,
        session_id: str,
        expected_request_hash: str,
        expected_transition_sequence_number: int,
    ) -> None:
        """Atomically validates and records confirmation, and transitions
        awaiting_confirmation -> confirmed. confirmation_expires_at is
        computed from the store's own wall clock at this moment -- never
        from the caller-supplied, unparsed `timestamp` audit label."""
        now = self._clock()
        expires_at = now + self._confirmation_ttl_seconds
        with self._immediate_txn():
            row = self._fetch_for_update(orchestration_instance_id)
            if row is None:
                raise RecordNotFoundError(orchestration_instance_id)
            if row["session_id"] != session_id:
                raise AuthorizationFailedError(
                    "session_mismatch", "confirmation session does not match the record's own session"
                )
            if row["request_hash"] != expected_request_hash:
                raise AuthorizationFailedError(
                    "hash_mismatch", "confirmation targets a different request_hash than the durable record"
                )
            if scope != expected_request_hash:
                raise AuthorizationFailedError(
                    "confirmation_scope_mismatch", "confirmation scope does not equal the request hash"
                )
            if row["transition_sequence_number"] != expected_transition_sequence_number:
                raise StaleTransitionError(
                    f"expected transition_sequence_number {expected_transition_sequence_number} for "
                    f"{orchestration_instance_id!r}, but the durable record is at "
                    f"{row['transition_sequence_number']}."
                )
            from_state = row["current_state"]
            cur = self._conn.execute(
                "UPDATE orchestration_records SET confirmation_status='accepted', confirmation_scope=?, "
                "confirmation_timestamp=?, confirmation_expires_at=?, current_state='confirmed', "
                "previous_state=?, transition_sequence_number=transition_sequence_number+1, "
                "last_transition_at=? WHERE orchestration_instance_id=? AND transition_sequence_number=?",
                (scope, timestamp, expires_at, from_state, now, orchestration_instance_id, expected_transition_sequence_number),
            )
            if cur.rowcount != 1:
                raise StaleTransitionError(
                    f"confirmation for {orchestration_instance_id!r} lost a race with a concurrent writer."
                )
            self._conn.execute(
                "INSERT INTO transition_events (orchestration_instance_id, sequence_number, from_state, "
                "to_state, at, note) VALUES (?, ?, ?, 'confirmed', ?, ?)",
                (orchestration_instance_id, expected_transition_sequence_number, from_state, now, "confirmation accepted"),
            )

    # -- invocation authorization (the atomic operation) ---------------------

    def authorize_invocation(
        self,
        orchestration_instance_id: str,
        *,
        request_hash: str,
        confirmation_scope: str,
        session_id: str,
        invocation_id: str,
        expected_transition_sequence_number: int,
    ) -> None:
        """The one atomic transaction this milestone exists to provide.

        Verifies, in one transaction: (1) the record exists, (2) current_
        state is 'confirmed', (3) request_hash matches, (4) session_id
        matches, (5) confirmation_status is 'accepted', (6) confirmation_
        scope equals request_hash, (7) confirmation has not already been
        consumed, (8) no invocation_id already exists, (9) confirmation has
        not expired. Only if every condition holds does it, atomically:
        consume confirmation, record invocation_id, transition to
        'executing', and append the transition event -- all in one commit,
        BEFORE the caller may launch any helper. If any condition fails, no
        partial change is ever persisted (the whole transaction rolls back)."""
        now = self._clock()
        with self._immediate_txn():
            row = self._fetch_for_update(orchestration_instance_id)
            if row is None:
                raise AuthorizationFailedError("record_not_found", f"no durable record for {orchestration_instance_id!r}")
            if row["current_state"] != "confirmed":
                raise AuthorizationFailedError("wrong_state", f"current_state is {row['current_state']!r}, not 'confirmed'")
            if row["request_hash"] != request_hash:
                raise AuthorizationFailedError("hash_mismatch", "request_hash does not match the durable record")
            if row["session_id"] != session_id:
                raise AuthorizationFailedError("session_mismatch", "session_id does not match the durable record")
            if row["confirmation_status"] != "accepted":
                raise AuthorizationFailedError(
                    "confirmation_not_accepted", f"confirmation_status is {row['confirmation_status']!r}, not 'accepted'"
                )
            if row["confirmation_scope"] != confirmation_scope or confirmation_scope != request_hash:
                raise AuthorizationFailedError(
                    "confirmation_scope_mismatch", "confirmation scope does not match request_hash"
                )
            if bool(row["confirmation_consumed"]):
                raise AuthorizationFailedError("already_invoked", "confirmation has already been consumed")
            if row["invocation_id"] is not None:
                raise AuthorizationFailedError("already_invoked", "an invocation_id is already recorded for this instance")
            expires_at = row["confirmation_expires_at"]
            if expires_at is None or not isinstance(expires_at, (int, float)) or expires_at <= now:
                raise AuthorizationFailedError(
                    "confirmation_expired", "confirmation is missing, unparsable, or has expired -- failing closed"
                )
            if row["transition_sequence_number"] != expected_transition_sequence_number:
                raise StaleTransitionError(
                    f"expected transition_sequence_number {expected_transition_sequence_number} for "
                    f"{orchestration_instance_id!r}, but the durable record is at "
                    f"{row['transition_sequence_number']}."
                )

            from_state = row["current_state"]
            cur = self._conn.execute(
                "UPDATE orchestration_records SET current_state='executing', previous_state=?, "
                "confirmation_status='consumed', confirmation_consumed=1, invocation_status='in_progress', "
                "invocation_id=?, transition_sequence_number=transition_sequence_number+1, last_transition_at=? "
                "WHERE orchestration_instance_id=? AND transition_sequence_number=? AND current_state='confirmed' "
                "AND confirmation_consumed=0 AND invocation_id IS NULL",
                (from_state, invocation_id, now, orchestration_instance_id, expected_transition_sequence_number),
            )
            if cur.rowcount != 1:
                # Defense in depth: the pre-checks above should already have
                # caught every reachable failure mode, since BEGIN IMMEDIATE
                # holds the write lock for the whole transaction -- this
                # branch exists only as a safety net, never expected to be
                # the sole enforcement point.
                raise AuthorizationFailedError("already_invoked", "authorization lost a race with a concurrent writer")
            try:
                self._conn.execute(
                    "INSERT INTO invocation_attempts (orchestration_instance_id, invocation_id, request_hash, "
                    "authorized_at) VALUES (?, ?, ?, ?)",
                    (orchestration_instance_id, invocation_id, request_hash, now),
                )
            except sqlite3.IntegrityError as exc:
                raise AuthorizationFailedError(
                    "already_invoked", "invocation_attempts uniqueness guard rejected a second attempt"
                ) from exc
            self._conn.execute(
                "INSERT INTO transition_events (orchestration_instance_id, sequence_number, from_state, "
                "to_state, at, note) VALUES (?, ?, ?, 'executing', ?, ?)",
                (orchestration_instance_id, expected_transition_sequence_number, from_state, now, "invocation authorized"),
            )

    # -- post-invocation updates ---------------------------------------------

    def record_execution_result(
        self,
        orchestration_instance_id: str,
        *,
        to_state: str,
        execution_status: str,
        exit_code: int | None,
        output_file_count: int,
        validation_ok: bool,
        validation_problems: tuple[str, ...],
        failure_category: str | None,
        expected_transition_sequence_number: int,
    ) -> None:
        if to_state not in ("execution_completed", "execution_failed"):
            raise ValueError(f"to_state must be execution_completed or execution_failed, got {to_state!r}")
        problems_json = json.dumps(list(validation_problems)[:_MAX_STORED_VALIDATION_PROBLEMS])
        now = self._clock()
        with self._immediate_txn():
            row = self._fetch_for_update(orchestration_instance_id)
            if row is None:
                raise RecordNotFoundError(orchestration_instance_id)
            if row["current_state"] != "executing":
                raise AuthorizationFailedError(
                    "wrong_state", f"cannot record a result from state {row['current_state']!r}, expected 'executing'"
                )
            if row["transition_sequence_number"] != expected_transition_sequence_number:
                raise StaleTransitionError(
                    f"expected transition_sequence_number {expected_transition_sequence_number} for "
                    f"{orchestration_instance_id!r}, but the durable record is at "
                    f"{row['transition_sequence_number']}."
                )
            from_state = row["current_state"]
            cur = self._conn.execute(
                "UPDATE orchestration_records SET current_state=?, previous_state=?, invocation_status='returned', "
                "execution_status=?, exit_code=?, output_file_count=?, validation_ok=?, validation_problems=?, "
                "failure_category=?, transition_sequence_number=transition_sequence_number+1, last_transition_at=? "
                "WHERE orchestration_instance_id=? AND transition_sequence_number=?",
                (
                    to_state,
                    from_state,
                    execution_status,
                    exit_code,
                    output_file_count,
                    int(bool(validation_ok)),
                    problems_json,
                    failure_category,
                    now,
                    orchestration_instance_id,
                    expected_transition_sequence_number,
                ),
            )
            if cur.rowcount != 1:
                raise StaleTransitionError(
                    f"result recording for {orchestration_instance_id!r} lost a race with a concurrent writer."
                )
            self._conn.execute(
                "INSERT INTO transition_events (orchestration_instance_id, sequence_number, from_state, "
                "to_state, at, note) VALUES (?, ?, ?, ?, ?, ?)",
                (orchestration_instance_id, expected_transition_sequence_number, from_state, to_state, now, "execution result recorded"),
            )

    # -- inspection / recovery (read-only) -----------------------------------

    def get_transition_history(self, orchestration_instance_id: str) -> list[TransitionEventRecord]:
        rows = self._conn.execute(
            "SELECT sequence_number, from_state, to_state, at, note FROM transition_events "
            "WHERE orchestration_instance_id = ? ORDER BY sequence_number ASC",
            (orchestration_instance_id,),
        ).fetchall()
        return [
            TransitionEventRecord(
                sequence_number=r["sequence_number"], from_state=r["from_state"], to_state=r["to_state"],
                at=r["at"], note=r["note"],
            )
            for r in rows
        ]

    def list_records(self, *, state: str | None = None) -> list[DurableRecord]:
        if state is not None:
            rows = self._conn.execute(
                "SELECT * FROM orchestration_records WHERE current_state = ? ORDER BY created_at ASC", (state,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM orchestration_records ORDER BY created_at ASC").fetchall()
        return [self._row_to_record(r) for r in rows]

    def list_ambiguous_invocations(self) -> list[DurableRecord]:
        """Records stuck in 'executing' with an invocation_id already
        recorded but no execution result yet -- i.e. authorization
        committed, but this layer cannot know whether the (hypothetical)
        real helper was ever launched, ever returned, or its result was
        ever persisted. Always surfaced as requiring manual review; never
        auto-resolved."""
        rows = self._conn.execute(
            "SELECT * FROM orchestration_records WHERE current_state = 'executing' "
            "AND invocation_id IS NOT NULL AND execution_status IS NULL ORDER BY created_at ASC"
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def list_expired_confirmations(self) -> list[DurableRecord]:
        now = self._clock()
        rows = self._conn.execute(
            "SELECT * FROM orchestration_records WHERE confirmation_status = 'accepted' "
            "AND confirmation_consumed = 0 AND (confirmation_expires_at IS NULL OR confirmation_expires_at <= ?) "
            "ORDER BY created_at ASC",
            (now,),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def list_terminal(self) -> list[DurableRecord]:
        placeholders = ", ".join("?" for _ in TERMINAL_STATES)
        rows = self._conn.execute(
            f"SELECT * FROM orchestration_records WHERE current_state IN ({placeholders}) ORDER BY created_at ASC",
            tuple(TERMINAL_STATES),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def list_needs_review(self) -> tuple[list[DurableRecord], list[str]]:
        """Returns (ambiguous_or_expired_records, corrupt_instance_ids) --
        two separate lists, since a corrupt record cannot be safely loaded
        as a DurableRecord (loading one via `load_record`/`list_records`
        itself raises CorruptStateError; `check_integrity()` reports its ID
        only). Read-only -- reports; never repairs."""
        seen: dict[str, DurableRecord] = {}
        for rec in self.list_ambiguous_invocations():
            seen[rec.orchestration_instance_id] = rec
        for rec in self.list_expired_confirmations():
            seen.setdefault(rec.orchestration_instance_id, rec)
        return list(seen.values()), self.check_integrity()

    def check_integrity(self) -> list[str]:
        """Returns orchestration_instance_ids whose stored data is
        internally inconsistent (unrecognized state, impossible confirmation
        state, malformed validation_problems JSON, or a transition-sequence
        gap/duplicate). Read-only -- never repairs anything it finds."""
        corrupt: list[str] = []
        rows = self._conn.execute("SELECT * FROM orchestration_records").fetchall()
        for row in rows:
            try:
                self._row_to_record(row)
            except CorruptStateError:
                corrupt.append(row["orchestration_instance_id"])
                continue
            history = self.get_transition_history(row["orchestration_instance_id"])
            actual_seq = [t.sequence_number for t in history]
            expected_seq = list(range(len(actual_seq)))
            # transition_sequence_number always equals the count of recorded
            # transition_events for a healthy instance (each transition
            # increments the counter by exactly one and inserts exactly one
            # event) -- a mismatch here (including a deleted/missing event
            # row) is corruption even when the remaining rows happen to look
            # contiguous on their own.
            if actual_seq != expected_seq or len(history) != row["transition_sequence_number"]:
                corrupt.append(row["orchestration_instance_id"])
        return corrupt

    def safe_summary(self, orchestration_instance_id: str) -> dict[str, Any]:
        return self.load_record(orchestration_instance_id).to_safe_summary()


# ---------------------------------------------------------------------------
# Read-only CLI (Stage 5 operator tooling)
# ---------------------------------------------------------------------------


def _print_record(rec: DurableRecord) -> None:
    for key, value in rec.to_safe_summary().items():
        print(f"  {key}: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only inspection tool for the durable orchestration state store. "
            "Never mutates the database; never runs GAUSS."
        )
    )
    parser.add_argument("--db-path", default=str(default_db_path()), help="Path to the SQLite database file.")
    parser.add_argument("--init", action="store_true", help="Initialize the schema (idempotent) and exit.")
    parser.add_argument("--list", action="store_true", help="List all records (safe summaries).")
    parser.add_argument("--state", default=None, help="Filter --list by current_state.")
    parser.add_argument("--show", default=None, metavar="INSTANCE_ID", help="Show one record's safe summary.")
    parser.add_argument("--history", default=None, metavar="INSTANCE_ID", help="Show one record's transition history.")
    parser.add_argument("--list-ambiguous", action="store_true", help="List records requiring manual review (ambiguous invocation).")
    parser.add_argument("--list-expired", action="store_true", help="List records with an expired, unconsumed confirmation.")
    parser.add_argument("--list-terminal", action="store_true", help="List records in a terminal state.")
    parser.add_argument("--list-needs-review", action="store_true", help="List all records requiring manual review (ambiguous or expired) plus any detected corruption.")
    parser.add_argument("--check-integrity", action="store_true", help="List orchestration_instance_ids with detected corruption.")
    parser.add_argument("--self-test", action="store_true", help="Run a lightweight built-in smoke test and exit.")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.self_test:
        return _run_self_test()

    store = OrchestrationStateStore(args.db_path)
    try:
        store.initialize()
        if args.init:
            print(f"Initialized (schema_version={SCHEMA_VERSION}) at {args.db_path}")
            return 0
        if args.list:
            for rec in store.list_records(state=args.state):
                print(f"== {rec.orchestration_instance_id} ==")
                _print_record(rec)
            return 0
        if args.show:
            _print_record(store.load_record(args.show))
            return 0
        if args.history:
            for event in store.get_transition_history(args.history):
                print(f"  [{event.sequence_number}] {event.from_state} -> {event.to_state} at {event.at} ({event.note})")
            return 0
        if args.list_ambiguous:
            for rec in store.list_ambiguous_invocations():
                print(f"== AMBIGUOUS: {rec.orchestration_instance_id} ==")
                _print_record(rec)
            return 0
        if args.list_expired:
            for rec in store.list_expired_confirmations():
                print(f"== EXPIRED CONFIRMATION: {rec.orchestration_instance_id} ==")
                _print_record(rec)
            return 0
        if args.list_terminal:
            for rec in store.list_terminal():
                print(f"== TERMINAL: {rec.orchestration_instance_id} ==")
                _print_record(rec)
            return 0
        if args.check_integrity:
            corrupt = store.check_integrity()
            if corrupt:
                print("CORRUPT records detected (fail-closed, not repaired):")
                for instance_id in corrupt:
                    print(f"  {instance_id}")
            else:
                print("No corruption detected.")
            return 0
        if args.list_needs_review:
            needs_review, corrupt_ids = store.list_needs_review()
            if not needs_review and not corrupt_ids:
                print("Nothing requires manual review.")
                return 0
            for rec in needs_review:
                print(f"== NEEDS REVIEW: {rec.orchestration_instance_id} ==")
                _print_record(rec)
            for instance_id in corrupt_ids:
                print(f"== NEEDS REVIEW (CORRUPT, not loadable): {instance_id} ==")
            return 0
        parser.print_help()
        return 0
    finally:
        store.close()


def _run_self_test() -> int:
    import tempfile

    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "self_test.db"
        clock_value = [1000.0]

        def clock() -> float:
            return clock_value[0]

        store = OrchestrationStateStore(db_path, clock=clock, confirmation_ttl_seconds=1800.0)
        try:
            store.initialize()
            store.initialize()  # idempotent
            store.create_record(orchestration_instance_id="i1", session_id="s1")
            rec = store.load_record("i1")
            check("record created with collecting_inputs", rec.current_state == "collecting_inputs")

            store.transition("i1", to_state="proposed", expected_transition_sequence_number=0, extra_fields={"request_hash": "h1"})
            store.transition("i1", to_state="awaiting_confirmation", expected_transition_sequence_number=1)
            store.record_confirmation(
                "i1", scope="h1", timestamp="t1", session_id="s1", expected_request_hash="h1", expected_transition_sequence_number=2
            )
            rec = store.load_record("i1")
            check("confirmed after record_confirmation", rec.current_state == "confirmed")
            check("confirmation expires_at set", rec.confirmation_expires_at == 1000.0 + 1800.0)

            store.authorize_invocation(
                "i1", request_hash="h1", confirmation_scope="h1", session_id="s1", invocation_id="inv1",
                expected_transition_sequence_number=3,
            )
            rec = store.load_record("i1")
            check("authorized reaches executing", rec.current_state == "executing")
            check("confirmation consumed", rec.confirmation_consumed is True)

            try:
                store.authorize_invocation(
                    "i1", request_hash="h1", confirmation_scope="h1", session_id="s1", invocation_id="inv2",
                    expected_transition_sequence_number=4,
                )
                failures.append("second authorize_invocation should have raised AuthorizationFailedError")
            except AuthorizationFailedError as exc:
                check(
                    "second authorization fails closed (already past 'confirmed')",
                    exc.reason_category in ("already_invoked", "wrong_state"),
                )

            store.record_execution_result(
                "i1", to_state="execution_completed", execution_status="completed", exit_code=0,
                output_file_count=0, validation_ok=True, validation_problems=(), failure_category=None,
                expected_transition_sequence_number=4,
            )
            rec = store.load_record("i1")
            check("result recorded reaches execution_completed", rec.current_state == "execution_completed")
            check("execution_status persisted", rec.execution_status == "completed")

            history = store.get_transition_history("i1")
            check("transition history has 5 events", len(history) == 5)
        finally:
            store.close()

    if failures:
        print(f"SELF-TEST FAILED ({len(failures)} issue(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SELF-TEST PASSED: all checks succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
