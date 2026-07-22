"""Focused unit tests for scripts/gauss_workspace.py (v0.42.0 GAUSS
Workspace Abstraction Implementation).

This repository has no pytest configuration anywhere; the established
convention (see scripts/test_gauss_execution_session.py's own docstring) is
a self-contained `check(name, condition)` harness runnable directly:

    python scripts/test_gauss_workspace.py

Every test in this file is purely in-memory and uses a disposable temporary
directory only as the `approved_parent_directory` bound -- no real file is
ever created, read, or deleted by any test or by the module under test.
Tests are grouped to match the authorizing task's own coverage list:
Creation (1-3), Lifecycle (4-9), Security (10-15), Manifest (16-20),
Isolation (21-23).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_workspace as gw  # noqa: E402

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


def _registry(tmp: str) -> "gw.WorkspaceRegistry":
    return gw.WorkspaceRegistry(approved_parent_directory=tmp)


def _advance_to_completed(registry: "gw.WorkspaceRegistry", workspace_id: str) -> None:
    registry.update_workspace_status(workspace_id, to_status=gw.WorkspaceStatus.POPULATED)
    registry.update_workspace_status(workspace_id, to_status=gw.WorkspaceStatus.READY)
    registry.update_workspace_status(workspace_id, to_status=gw.WorkspaceStatus.EXECUTING)
    registry.update_workspace_status(workspace_id, to_status=gw.WorkspaceStatus.COMPLETED)


# ---------------------------------------------------------------------------
# Creation (1-3)
# ---------------------------------------------------------------------------


def test_01_workspace_created_successfully() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        check("workspace starts in 'created' status", ws.status == gw.WorkspaceStatus.CREATED)
        check("workspace has a root_path", bool(ws.root_path))
        check("root_path resolves inside the approved parent directory", ws.root_path.startswith(str(Path(tmp).resolve())))


def test_02_unique_workspace_ids_generated() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws_a = registry.create_workspace()
        ws_b = registry.create_workspace()
        check("two created workspaces have distinct ids", ws_a.workspace_id != ws_b.workspace_id)
        check("two created workspaces have distinct root_paths", ws_a.root_path != ws_b.root_path)


def test_03_metadata_stored() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace(owner_reference="owner-1", metadata={"purpose": "unit test"})
        check("owner_reference stored", ws.owner_reference == "owner-1")
        check("metadata stored", ws.metadata == {"purpose": "unit test"})
        check("get_workspace_metadata returns the same metadata", registry.get_workspace_metadata(ws.workspace_id) == {"purpose": "unit test"})


# ---------------------------------------------------------------------------
# Lifecycle (4-9)
# ---------------------------------------------------------------------------


def test_04_valid_transitions_accepted_full_chain() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        _advance_to_completed(registry, ws.workspace_id)
        check("workspace reaches 'completed' via the full valid chain", ws.status == gw.WorkspaceStatus.COMPLETED)
        registry.archive_workspace(ws.workspace_id)
        check("archive_workspace reaches 'archived'", ws.status == gw.WorkspaceStatus.ARCHIVED)
        registry.delete_workspace(ws.workspace_id)
        check("delete_workspace reaches 'deleted'", ws.status == gw.WorkspaceStatus.DELETED)


def test_05_invalid_transition_skip_ahead_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        check_raises(
            "created -> ready (skipping populated) is rejected",
            gw.InvalidWorkspaceTransitionError, registry.update_workspace_status, ws.workspace_id, to_status=gw.WorkspaceStatus.READY,
        )


def test_06_deleted_to_ready_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        _advance_to_completed(registry, ws.workspace_id)
        registry.archive_workspace(ws.workspace_id)
        registry.delete_workspace(ws.workspace_id)
        check_raises(
            "deleted -> ready is rejected",
            gw.InvalidWorkspaceTransitionError, registry.update_workspace_status, ws.workspace_id, to_status=gw.WorkspaceStatus.READY,
        )


def test_07_deleted_to_executing_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        _advance_to_completed(registry, ws.workspace_id)
        registry.archive_workspace(ws.workspace_id)
        registry.delete_workspace(ws.workspace_id)
        check_raises(
            "deleted -> executing is rejected",
            gw.InvalidWorkspaceTransitionError, registry.update_workspace_status, ws.workspace_id, to_status=gw.WorkspaceStatus.EXECUTING,
        )


def test_08_archive_requires_completed_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()  # still 'created'
        check_raises(
            "archive_workspace refuses a workspace that is not 'completed'",
            gw.InvalidWorkspaceTransitionError, registry.archive_workspace, ws.workspace_id,
        )


def test_09_delete_requires_archived_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        _advance_to_completed(registry, ws.workspace_id)  # 'completed', not yet archived
        check_raises(
            "delete_workspace refuses a workspace that is not 'archived'",
            gw.InvalidWorkspaceTransitionError, registry.delete_workspace, ws.workspace_id,
        )


# ---------------------------------------------------------------------------
# Security (10-15)
# ---------------------------------------------------------------------------


def test_10_path_traversal_root_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        check_raises(
            "a root_path escaping the approved parent via traversal is rejected",
            gw.WorkspacePathError, registry.create_workspace, root_path="../../escape-attempt",
        )


def test_11_outside_root_absolute_path_rejected() -> None:
    with tempfile.TemporaryDirectory() as other_tmp, tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        check_raises(
            "an absolute root_path pointing entirely outside the approved parent is rejected",
            gw.WorkspacePathError, registry.create_workspace, root_path=other_tmp,
        )


def test_12_deleted_workspace_cannot_reactivate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        _advance_to_completed(registry, ws.workspace_id)
        registry.archive_workspace(ws.workspace_id)
        registry.delete_workspace(ws.workspace_id)
        for target in (gw.WorkspaceStatus.CREATED, gw.WorkspaceStatus.POPULATED, gw.WorkspaceStatus.READY):
            check_raises(
                f"deleted -> {target.value} is rejected",
                gw.InvalidWorkspaceTransitionError, registry.update_workspace_status, ws.workspace_id, to_status=target,
            )
        outcome = registry.validate_workspace(ws.workspace_id)
        check("a deleted workspace fails validate_workspace", not outcome.valid)
        check("deleted workspace reports 'deleted'", outcome.reason_category == "deleted")


def test_13_manifest_relative_path_traversal_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        check_raises(
            "a manifest entry whose relative_path escapes the workspace root is rejected",
            gw.WorkspacePathError,
            lambda: registry.add_file_to_manifest(
                ws.workspace_id, name="escape.gss", relative_path="../../etc/passwd", source="user"
            ),
        )


def test_14_manifest_absolute_path_outside_workspace_rejected() -> None:
    with tempfile.TemporaryDirectory() as other_tmp, tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        check_raises(
            "a manifest entry with an absolute relative_path outside the workspace root is rejected",
            gw.WorkspacePathError,
            lambda: registry.add_file_to_manifest(
                ws.workspace_id, name="elsewhere.gss", relative_path=str(Path(other_tmp) / "elsewhere.gss"), source="user"
            ),
        )


def test_15_unauthorized_ownership_rejected_by_validate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace(owner_reference="real-owner")
        outcome = registry.validate_workspace(ws.workspace_id, expected_owner_reference="different-owner")
        check("an ownership mismatch fails validation", not outcome.valid)
        check("ownership mismatch reports 'ownership_mismatch'", outcome.reason_category == "ownership_mismatch")
        matching_outcome = registry.validate_workspace(ws.workspace_id, expected_owner_reference="real-owner")
        check("a matching owner_reference validates successfully", matching_outcome.valid)


# ---------------------------------------------------------------------------
# Manifest (16-20)
# ---------------------------------------------------------------------------


def test_16_manifest_metadata_captured_correctly() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        registry.add_file_to_manifest(
            ws.workspace_id, name="model.gss", relative_path="model.gss", source="user",
            size=1234, checksum="sha256:deadbeef", creation_state="populated",
        )
        manifest = registry.get_workspace_manifest(ws.workspace_id)
        check("manifest has exactly one entry", len(manifest.files) == 1)
        entry = manifest.files[0]
        check("entry name captured", entry.name == "model.gss")
        check("entry size captured", entry.size == 1234)
        check("entry checksum captured", entry.checksum == "sha256:deadbeef")
        check("entry source captured", entry.source == "user")
        check("entry creation_state captured", entry.creation_state == "populated")


def test_17_manifest_file_contents_not_read() -> None:
    import dataclasses

    entry_fields = {f.name for f in dataclasses.fields(gw.ManifestFileEntry)}
    for forbidden in ("content", "contents", "raw_content", "data", "bytes"):
        check(f"ManifestFileEntry has no {forbidden!r} field", forbidden not in entry_fields)


def test_18_manifest_relative_paths_preserved() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        registry.add_file_to_manifest(
            ws.workspace_id, name="data.csv", relative_path="inputs/data.csv", source="user", size=50000,
        )
        manifest = registry.get_workspace_manifest(ws.workspace_id)
        check("nested relative_path preserved verbatim", manifest.files[0].relative_path == "inputs/data.csv")


def test_19_manifest_for_unknown_workspace_raises() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        check_raises(
            "get_workspace_manifest for an unknown workspace_id raises",
            gw.WorkspaceNotFoundError, registry.get_workspace_manifest, "does-not-exist",
        )


def test_20_manifest_to_dict_matches_documented_shape() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws = registry.create_workspace()
        registry.add_file_to_manifest(ws.workspace_id, name="out.txt", relative_path="out.txt", source="execution", size=19)
        manifest_dict = registry.get_workspace_manifest(ws.workspace_id).to_dict()
        check("to_dict has workspace_id key", manifest_dict["workspace_id"] == ws.workspace_id)
        check("to_dict has files list", isinstance(manifest_dict["files"], list) and len(manifest_dict["files"]) == 1)
        check(
            "to_dict file entry has exactly the documented keys",
            set(manifest_dict["files"][0].keys()) == {"name", "relative_path", "size", "checksum", "source", "creation_state"},
        )


# ---------------------------------------------------------------------------
# Isolation (21-23)
# ---------------------------------------------------------------------------


def test_21_multiple_workspaces_remain_separate_in_one_registry() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = _registry(tmp)
        ws_a = registry.create_workspace(owner_reference="owner-a")
        ws_b = registry.create_workspace(owner_reference="owner-b")
        registry.update_workspace_status(ws_a.workspace_id, to_status=gw.WorkspaceStatus.POPULATED)
        check("advancing workspace A does not affect workspace B's status", registry.get_workspace(ws_b.workspace_id).status == gw.WorkspaceStatus.CREATED)
        registry.add_file_to_manifest(ws_a.workspace_id, name="a.gss", relative_path="a.gss", source="user")
        check("workspace B's manifest remains empty after adding a file to A", len(registry.get_workspace_manifest(ws_b.workspace_id).files) == 0)


def test_22_separate_registries_do_not_share_state() -> None:
    with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
        registry_a = _registry(tmp_a)
        registry_b = _registry(tmp_b)
        ws = registry_a.create_workspace()
        check_raises(
            "a workspace created in registry A is unknown to registry B",
            gw.WorkspaceNotFoundError, registry_b.get_workspace, ws.workspace_id,
        )


def test_23_each_registry_has_its_own_approved_parent_directory() -> None:
    with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
        registry_a = _registry(tmp_a)
        registry_b = _registry(tmp_b)
        check(
            "two registries pointed at different directories have different approved parents",
            registry_a.approved_parent_directory != registry_b.approved_parent_directory,
        )


# ---------------------------------------------------------------------------
# No-GAUSS-import confirmation (24)
# ---------------------------------------------------------------------------


def test_24_module_never_runs_gauss_or_touches_execution_stack() -> None:
    check("gauss_code_execution is absent from sys.modules", "gauss_code_execution" not in sys.modules)
    check("gauss_execution_adapter is absent from sys.modules", "gauss_execution_adapter" not in sys.modules)
    check("gauss_runtime_orchestration is absent from sys.modules", "gauss_runtime_orchestration" not in sys.modules)
    check("gauss_execution_workflow is absent from sys.modules", "gauss_execution_workflow" not in sys.modules)
    check("gauss_execution_session is absent from sys.modules", "gauss_execution_session" not in sys.modules)


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
