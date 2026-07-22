"""In-memory GAUSS workspace abstraction (v0.42.0 GAUSS Workspace Abstraction
Implementation).

Authoritative design source: `planning/v0.41.0-file-artifact-workflow-design.md`
(Workspace Model, Workspace Lifecycle, File Manifest Model, File Security
Boundaries sections). This module implements the first, minimal slice of
that design -- workspace identity, lifecycle, bounded filesystem location,
metadata, and a basic manifest -- it does not redefine those sections.

**Scope, restated from the authorizing task:** infrastructure only. No file
uploads, no automatic file reading, no artifact persistence, no cloud
storage, no multi-user permissions, no distributed workers, no runtime
orchestration changes, no automatic execution, no GAUSS execution changes.
This module has no dependency on, and is not depended on by,
`scripts/gauss_execution_workflow.py`, `scripts/gauss_execution_session.py`,
`scripts/gauss_runtime_orchestration.py`, `scripts/gauss_orchestration_
state_store.py`, `scripts/gauss_execution_adapter.py`, or `scripts/gauss_
code_execution.py` -- it never imports any of them, never launches a
subprocess, and never touches GAUSS.

**In-memory storage only.** `WorkspaceRegistry` is a plain Python object
holding a dict; nothing in this module writes to disk, a database, or the
network. Unlike `scripts/gauss_execution_session.py` (which has no backing
store at all -- callers hold the value themselves), this module DOES include
a small in-memory registry, because its own required API
(`get_workspace(workspace_id)`) needs a lookup-by-id capability a bare value
type cannot provide on its own. The registry is still never persisted
anywhere.

**No real filesystem mutation.** This module never creates, writes, reads,
or deletes a real file or directory. `root_path` and manifest
`relative_path` values are validated as *strings* (via `Path.resolve(strict
=False)`, which does not require the path to actually exist) -- never
opened, never scanned, never mkdir'd. Containment logic
(`_resolve_inside`) is deliberately a small, local, standalone
re-implementation of the same pattern already used by `scripts/gauss_code_
execution.py`'s own `_resolve_inside` -- duplicated, not imported, per this
codebase's established convention of small modules not reaching sideways
into the execution helper just to reuse a few lines (see `scripts/gauss_
orchestration_state_store.py`'s own docstring for the same rationale).

**Never stored anywhere in this module:** file contents, secrets,
credentials, raw execution output. Structural, not merely conventional: no
constructor or function in this module accepts file-content, credential, or
raw-stdout/stderr parameters at all. A manifest entry's `size`/`checksum`
are caller-asserted metadata values, never computed by reading the file
here.

**Workspace lifecycle** (seven states; this initial implementation supports
only the exact six-edge linear chain the authorizing task specifies -- no
branches, no shortcuts, no early-exit deletion):

    created -> populated -> ready -> executing -> completed -> archived -> deleted

`archive_workspace(...)` requires `status == completed`; `delete_workspace(
...)` requires `status == archived`. A future milestone may add additional
entry points (e.g. abandoning a still-`populated` workspace) if that need
is separately scoped and authorized -- this module does not add one on its
own.
"""

from __future__ import annotations

import argparse
import enum
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Workspace lifecycle
# ---------------------------------------------------------------------------


class WorkspaceStatus(enum.Enum):
    CREATED = "created"
    POPULATED = "populated"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


#: Exactly the six edges named in the authorizing task's Workspace States
#: section. No more, no fewer.
VALID_TRANSITIONS: dict[WorkspaceStatus, frozenset[WorkspaceStatus]] = {
    WorkspaceStatus.CREATED: frozenset({WorkspaceStatus.POPULATED}),
    WorkspaceStatus.POPULATED: frozenset({WorkspaceStatus.READY}),
    WorkspaceStatus.READY: frozenset({WorkspaceStatus.EXECUTING}),
    WorkspaceStatus.EXECUTING: frozenset({WorkspaceStatus.COMPLETED}),
    WorkspaceStatus.COMPLETED: frozenset({WorkspaceStatus.ARCHIVED}),
    WorkspaceStatus.ARCHIVED: frozenset({WorkspaceStatus.DELETED}),
    WorkspaceStatus.DELETED: frozenset(),
}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class WorkspaceError(Exception):
    """Base class for every error this module raises."""


class InvalidWorkspaceTransitionError(WorkspaceError):
    """Raised when a requested state transition is not present in
    VALID_TRANSITIONS for the workspace's current status."""


class WorkspacePathError(WorkspaceError):
    """Raised when a candidate path does not resolve safely inside its
    required containing directory (the approved parent directory for a
    workspace root, or a workspace's own root for a manifest entry)."""


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when no workspace exists for a given workspace_id."""


# ---------------------------------------------------------------------------
# Path containment (duplicated, not imported -- see module docstring)
# ---------------------------------------------------------------------------


def _resolve_inside(base_dir: Path, candidate: str | Path) -> Path | None:
    """Resolve `candidate` relative to `base_dir` and return it only if it
    stays inside `base_dir` -- rejects path traversal and absolute paths
    that point outside `base_dir`. Never touches the filesystem beyond
    `Path.resolve(strict=False)`, which does not require the path to
    actually exist."""
    try:
        candidate_path = Path(candidate)
        if not candidate_path.is_absolute():
            candidate_path = base_dir / candidate_path
        resolved = candidate_path.resolve(strict=False)
        base_resolved = base_dir.resolve(strict=False)
        resolved.relative_to(base_resolved)
        return resolved
    except (ValueError, OSError):
        return None


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------


@dataclass
class Workspace:
    """Never carries file contents, secrets, credentials, or raw execution
    output -- structurally impossible, since no field here accepts any of
    them. `root_path` is a validated, resolved path *string*, never a file
    handle or directory listing."""

    workspace_id: str
    root_path: str
    created_at: float
    status: WorkspaceStatus
    owner_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkspaceValidationOutcome:
    valid: bool
    reason_category: str | None = None
    detail: str | None = None


# ---------------------------------------------------------------------------
# Manifest (metadata only -- see module docstring)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ManifestFileEntry:
    """A caller-asserted metadata record. `size`/`checksum` are supplied by
    the caller -- this module never opens the file to compute them, and
    never reads or interprets its contents."""

    name: str
    relative_path: str
    source: str  # e.g. "user", "execution", "analysis" -- not enforced as an enum in this initial slice
    size: int | None = None
    checksum: str | None = None
    creation_state: str = "populated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "relative_path": self.relative_path,
            "size": self.size,
            "checksum": self.checksum,
            "source": self.source,
            "creation_state": self.creation_state,
        }


@dataclass(frozen=True)
class WorkspaceManifest:
    workspace_id: str
    files: tuple[ManifestFileEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"workspace_id": self.workspace_id, "files": [f.to_dict() for f in self.files]}


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------


class WorkspaceRegistry:
    """An in-memory-only collection of workspaces, each rooted somewhere
    inside one shared `approved_parent_directory`. Never writes to disk, a
    database, or the network -- `self._workspaces`/`self._manifests` are
    plain dicts, gone when the process exits.

    Multiple `WorkspaceRegistry` instances are fully isolated from one
    another (separate dicts) -- there is no hidden global/shared state
    anywhere in this module.
    """

    def __init__(
        self,
        *,
        approved_parent_directory: str | Path,
        clock: Callable[[], float] = time.time,
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self._approved_parent_directory = Path(approved_parent_directory).resolve(strict=False)
        self._clock = clock
        self._id_factory = id_factory
        self._workspaces: dict[str, Workspace] = {}
        self._manifests: dict[str, list[ManifestFileEntry]] = {}

    @property
    def approved_parent_directory(self) -> Path:
        return self._approved_parent_directory

    # -- creation -----------------------------------------------------------

    def create_workspace(
        self,
        *,
        root_path: str | None = None,
        owner_reference: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Workspace:
        """Creates a workspace in the `created` state. `root_path`, if
        supplied, must resolve inside `approved_parent_directory` (relative
        or absolute -- both are checked identically); if omitted, a fresh
        subdirectory named after the new `workspace_id` is used, which is
        always safe by construction. Never creates the directory on disk --
        only validates and records the path."""
        workspace_id = self._id_factory()
        candidate = root_path if root_path is not None else workspace_id
        resolved = _resolve_inside(self._approved_parent_directory, candidate)
        if resolved is None:
            raise WorkspacePathError(
                f"root_path {candidate!r} does not resolve inside the approved parent directory "
                f"{self._approved_parent_directory}; refusing to create a workspace outside its bounds."
            )
        workspace = Workspace(
            workspace_id=workspace_id,
            root_path=str(resolved),
            created_at=self._clock(),
            status=WorkspaceStatus.CREATED,
            owner_reference=owner_reference,
            metadata=dict(metadata or {}),
        )
        self._workspaces[workspace_id] = workspace
        self._manifests[workspace_id] = []
        return workspace

    # -- lookup -----------------------------------------------------------

    def get_workspace(self, workspace_id: str) -> Workspace:
        try:
            return self._workspaces[workspace_id]
        except KeyError:
            raise WorkspaceNotFoundError(f"no workspace exists for {workspace_id!r}.") from None

    def get_workspace_metadata(self, workspace_id: str) -> dict[str, Any]:
        return dict(self.get_workspace(workspace_id).metadata)

    # -- lifecycle -----------------------------------------------------------

    def update_workspace_status(self, workspace_id: str, *, to_status: WorkspaceStatus) -> Workspace:
        workspace = self.get_workspace(workspace_id)
        allowed = VALID_TRANSITIONS.get(workspace.status, frozenset())
        if to_status not in allowed:
            raise InvalidWorkspaceTransitionError(
                f"{workspace.status.value} -> {to_status.value} is not a valid workspace transition."
            )
        workspace.status = to_status
        return workspace

    def archive_workspace(self, workspace_id: str) -> Workspace:
        """Only valid from `completed`, matching VALID_TRANSITIONS exactly
        -- raises `InvalidWorkspaceTransitionError` from any other state,
        never silently no-ops."""
        return self.update_workspace_status(workspace_id, to_status=WorkspaceStatus.ARCHIVED)

    def delete_workspace(self, workspace_id: str) -> Workspace:
        """Only valid from `archived`, matching VALID_TRANSITIONS exactly.
        Never actually deletes a real file or directory -- only marks the
        tracked `Workspace` record `deleted`; a `deleted` workspace's
        record and manifest remain readable via `get_workspace(...)`/
        `get_workspace_manifest(...)` for audit purposes, matching this
        module's own no-real-filesystem-mutation scope."""
        return self.update_workspace_status(workspace_id, to_status=WorkspaceStatus.DELETED)

    # -- validation ------------------------------------------------------------

    def validate_workspace(
        self, workspace_id: str, *, expected_owner_reference: str | None = None
    ) -> WorkspaceValidationOutcome:
        """A read-only check (never mutates the workspace). Validates: the
        workspace exists, its status is not `deleted`, its `root_path`
        still resolves inside `approved_parent_directory` (defense in
        depth against a directly-mutated record), and -- when
        `expected_owner_reference` is supplied -- that it matches the
        workspace's own `owner_reference` (a named hook only; real
        ownership *rules* remain undesigned, per `planning/v0.41.0-file-
        artifact-workflow-design.md`'s own deferral)."""
        try:
            workspace = self.get_workspace(workspace_id)
        except WorkspaceNotFoundError:
            return WorkspaceValidationOutcome(False, "not_found", f"no workspace exists for {workspace_id!r}.")
        if workspace.status == WorkspaceStatus.DELETED:
            return WorkspaceValidationOutcome(False, "deleted", "this workspace has been deleted.")
        if _resolve_inside(self._approved_parent_directory, workspace.root_path) is None:
            return WorkspaceValidationOutcome(
                False, "path_escaped_root", "root_path no longer resolves inside the approved parent directory."
            )
        if expected_owner_reference is not None and workspace.owner_reference != expected_owner_reference:
            return WorkspaceValidationOutcome(
                False, "ownership_mismatch", "expected_owner_reference does not match this workspace's owner_reference."
            )
        return WorkspaceValidationOutcome(True)

    # -- manifest ------------------------------------------------------------

    def add_file_to_manifest(
        self,
        workspace_id: str,
        *,
        name: str,
        relative_path: str,
        source: str,
        size: int | None = None,
        checksum: str | None = None,
        creation_state: str = "populated",
    ) -> ManifestFileEntry:
        """Records caller-asserted file metadata only -- never opens,
        reads, or scans the file itself. `relative_path` must resolve
        inside this specific workspace's own `root_path` (a second,
        narrower containment check beyond the registry-wide approved
        parent directory)."""
        workspace = self.get_workspace(workspace_id)
        if _resolve_inside(Path(workspace.root_path), relative_path) is None:
            raise WorkspacePathError(
                f"relative_path {relative_path!r} does not resolve inside workspace "
                f"{workspace_id!r}'s own root_path {workspace.root_path!r}."
            )
        entry = ManifestFileEntry(
            name=name, relative_path=relative_path, source=source, size=size, checksum=checksum,
            creation_state=creation_state,
        )
        self._manifests[workspace_id].append(entry)
        return entry

    def get_workspace_manifest(self, workspace_id: str) -> WorkspaceManifest:
        self.get_workspace(workspace_id)  # raises WorkspaceNotFoundError if unknown
        return WorkspaceManifest(workspace_id=workspace_id, files=tuple(self._manifests.get(workspace_id, ())))

    # -- containment (public, for external callers -- e.g. v0.43.0's
    #    execution-workflow integration -- that need to check whether a
    #    path belongs to a specific workspace without duplicating this
    #    module's own _resolve_inside logic a second time) ----------------

    def resolve_within_workspace(self, workspace_id: str, candidate: str) -> Path | None:
        """Returns the resolved path if `candidate` (relative or absolute)
        resolves inside the given workspace's own `root_path`, else
        `None`. Read-only; never touches the filesystem beyond
        `Path.resolve(strict=False)`. Raises `WorkspaceNotFoundError` if
        `workspace_id` is unknown."""
        workspace = self.get_workspace(workspace_id)
        return _resolve_inside(Path(workspace.root_path), candidate)


# ---------------------------------------------------------------------------
# Self-test harness (this repository's established convention -- no pytest
# is configured anywhere in this repository)
# ---------------------------------------------------------------------------


def _run_self_tests() -> int:
    """A lightweight built-in smoke test. The focused, comprehensive test
    suite lives in scripts/test_gauss_workspace.py -- this function only
    sanity-checks that the module's core entry points work at all. Never
    touches a real filesystem beyond a disposable temp directory used only
    as the approved parent (never written into)."""
    import tempfile

    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        registry = WorkspaceRegistry(approved_parent_directory=tmp)

        ws = registry.create_workspace(owner_reference="owner-1")
        check("workspace created in 'created' status", ws.status == WorkspaceStatus.CREATED)

        registry.update_workspace_status(ws.workspace_id, to_status=WorkspaceStatus.POPULATED)
        registry.add_file_to_manifest(
            ws.workspace_id, name="model.gss", relative_path="model.gss", source="user", size=1234
        )
        manifest = registry.get_workspace_manifest(ws.workspace_id)
        check("manifest has one entry", len(manifest.files) == 1)

        registry.update_workspace_status(ws.workspace_id, to_status=WorkspaceStatus.READY)
        registry.update_workspace_status(ws.workspace_id, to_status=WorkspaceStatus.EXECUTING)
        registry.update_workspace_status(ws.workspace_id, to_status=WorkspaceStatus.COMPLETED)

        outcome = registry.validate_workspace(ws.workspace_id)
        check("a completed, unarchived workspace still validates", outcome.valid)

        registry.archive_workspace(ws.workspace_id)
        registry.delete_workspace(ws.workspace_id)
        deleted_outcome = registry.validate_workspace(ws.workspace_id)
        check("a deleted workspace no longer validates", not deleted_outcome.valid)

        try:
            registry.create_workspace(root_path="../../escape-attempt")
            failures.append("a path-traversal root_path should have raised WorkspacePathError")
        except WorkspacePathError:
            pass

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
            "In-memory GAUSS workspace abstraction (v0.42.0). No real filesystem mutation, no "
            "database, no GAUSS invocation anywhere in this module."
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
