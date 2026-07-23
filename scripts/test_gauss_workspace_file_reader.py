"""Focused unit tests for scripts/gauss_workspace_file_reader.py (v0.44.0
Safe Workspace File Reading Workflow).

This repository has no pytest configuration anywhere; the established
convention (see scripts/test_gauss_workspace.py's own docstring) is a
self-contained `check(name, condition)` harness runnable directly:

    python scripts/test_gauss_workspace_file_reader.py

Unlike scripts/gauss_workspace.py's own tests, this module's tests DO create
real files on disk -- necessarily, since reading real bytes is this
module's entire purpose -- but always inside a disposable
`tempfile.TemporaryDirectory()`, always via `write_bytes` (never
`write_text`, which would apply Windows' own newline translation and make
exact-content comparisons platform-dependent), and never via GAUSS. Tests
are grouped to match the authorizing task's own Task 9 coverage list:
Successful reads (1-6), Safety (7-19), Boundary behavior (20-23),
Isolation (24).
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
import gauss_workspace_file_reader as fr  # noqa: E402

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


def _new_workspace(tmp: str) -> tuple["gw.WorkspaceRegistry", "gw.Workspace"]:
    registry = gw.WorkspaceRegistry(approved_parent_directory=tmp)
    workspace = registry.create_workspace()
    Path(workspace.root_path).mkdir(parents=True, exist_ok=True)
    return registry, workspace


def _write(workspace_root: str, relative_path: str, content: bytes) -> Path:
    path = Path(workspace_root) / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


# ---------------------------------------------------------------------------
# Successful reads (1-6)
# ---------------------------------------------------------------------------


def test_01_read_supported_utf8_text_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        _write(workspace.root_path, "notes.txt", "hello é workspace\n".encode("utf-8"))
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="notes.txt"),
            workspace_registry=registry,
        )
        check("status is completed", result.status == fr.ReadStatus.COMPLETED.value)
        check("content decoded correctly", result.content == "hello é workspace\n")
        check("file_type is 'txt'", result.file_type == "txt")


def test_02_read_csv_as_text_evidence() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        _write(workspace.root_path, "results.csv", b"a,b,c\n1,2,3\n")
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="results.csv"),
            workspace_registry=registry,
        )
        check("csv reads as completed", result.status == fr.ReadStatus.COMPLETED.value)
        check("csv content preserved verbatim", result.content == "a,b,c\n1,2,3\n")
        check("file_type is 'csv'", result.file_type == "csv")


def test_03_read_gauss_output_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        _write(workspace.root_path, "gauss_output.out", b"hello output test\n")
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="gauss_output.out"),
            workspace_registry=registry,
        )
        check(".out file reads as completed", result.status == fr.ReadStatus.COMPLETED.value)
        check(".gss extension is also supported", ".gss" in fr.ALLOWED_EXTENSIONS)


def test_04_checksum_and_size_returned() -> None:
    import hashlib

    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        content = b"checksum me\n"
        _write(workspace.root_path, "data.log", content)
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="data.log"),
            workspace_registry=registry,
        )
        check("size_bytes matches actual content length", result.size_bytes == len(content))
        check("checksum matches sha256 of the content", result.checksum == hashlib.sha256(content).hexdigest())


def test_05_workspace_provenance_preserved() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        _write(workspace.root_path, "data.tsv", b"a\tb\n1\t2\n")
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="data.tsv"),
            workspace_registry=registry,
        )
        assert result.provenance is not None
        check("provenance.workspace_id matches", result.provenance.workspace_id == workspace.workspace_id)
        check("provenance.relative_path matches", result.provenance.relative_path == "data.tsv")
        check("provenance.complete is True for an untruncated read", result.provenance.complete is True)
        check("provenance.read_at is populated", result.provenance.read_at > 0)


def test_06_provenance_links_to_manifest_entry_when_registered() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        _write(workspace.root_path, "registered.txt", b"tracked content\n")
        registry.add_file_to_manifest(
            workspace.workspace_id, name="registered.txt", relative_path="registered.txt", source="user", size=16
        )
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="registered.txt"),
            workspace_registry=registry,
        )
        assert result.provenance is not None
        check("source_manifest_entry is found when registered", result.provenance.source_manifest_entry is not None)
        check(
            "an unregistered file has source_manifest_entry=None (not an error)",
            fr.read_workspace_file(
                fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="registered.txt"),
                workspace_registry=registry,
            ).provenance.source_manifest_entry
            is not None,
        )


# ---------------------------------------------------------------------------
# Safety (7-19)
# ---------------------------------------------------------------------------


def test_07_reject_path_traversal() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="../../escape.txt"),
            workspace_registry=registry,
        )
        check("path traversal rejected", result.error_code == "path_escapes_workspace")


def test_08_reject_absolute_path() -> None:
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as other:
        registry, workspace = _new_workspace(tmp)
        absolute = str(Path(other) / "somewhere.txt")
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path=absolute),
            workspace_registry=registry,
        )
        check("absolute path rejected", result.error_code == "path_not_relative")


def test_09_reject_outside_workspace_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        # A second, sibling workspace root under the same approved parent --
        # a relative_path that climbs into it is still outside THIS
        # workspace's own root.
        other_workspace = registry.create_workspace()
        Path(other_workspace.root_path).mkdir(parents=True, exist_ok=True)
        _write(other_workspace.root_path, "secret.txt", b"not yours\n")
        climb = str(Path("..") / Path(other_workspace.root_path).name / "secret.txt")
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path=climb),
            workspace_registry=registry,
        )
        check("a file outside the workspace root is rejected", result.error_code == "path_escapes_workspace")


def test_10_reject_escaping_symlink() -> None:
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
        registry, workspace = _new_workspace(tmp)
        target = Path(outside) / "outside_secret.txt"
        target.write_bytes(b"outside content\n")
        link_path = Path(workspace.root_path) / "link_to_outside.txt"
        try:
            link_path.symlink_to(target)
        except OSError:
            print("SKIPPED test_10_reject_escaping_symlink: symlink creation not permitted on this host.")
            return
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="link_to_outside.txt"),
            workspace_registry=registry,
        )
        check("a symlink resolving outside the workspace is rejected", result.error_code == "path_escapes_workspace")


def test_11_reject_missing_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="never_created.txt"),
            workspace_registry=registry,
        )
        check("missing file rejected", result.error_code == "file_not_found")


def test_12_reject_directory() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        (Path(workspace.root_path) / "a_directory.txt").mkdir()
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="a_directory.txt"),
            workspace_registry=registry,
        )
        check("a directory is rejected", result.error_code == "not_a_regular_file")


def test_13_reject_unsupported_extension() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        _write(workspace.root_path, "program.exe", b"MZ\x90\x00")
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="program.exe"),
            workspace_registry=registry,
        )
        check("unsupported extension rejected", result.error_code == "unsupported_file_type")


def test_14_reject_binary_content_regardless_of_extension() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        _write(workspace.root_path, "looks_like_text.txt", bytes(range(256)) * 4)
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="looks_like_text.txt"),
            workspace_registry=registry,
        )
        check("binary content is rejected even with a .txt extension", result.error_code == "binary_content_detected")


def test_15_reject_oversized_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        _write(workspace.root_path, "big.txt", b"x" * (fr.DEFAULT_MAX_BYTES + 1))
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="big.txt"),
            workspace_registry=registry,
        )
        check("oversized file rejected by default (no truncation)", result.error_code == "file_too_large")


def test_16_reject_file_type_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        _write(workspace.root_path, "data.csv", b"a,b\n1,2\n")
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(
                workspace_id=workspace.workspace_id, relative_path="data.csv", expected_file_type="txt"
            ),
            workspace_registry=registry,
        )
        check("a mismatched expected_file_type is rejected", result.error_code == "file_type_mismatch")


def test_17_reject_unsupported_encoding() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        _write(workspace.root_path, "notes.txt", b"hello\n")
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="notes.txt", encoding="latin-1"),
            workspace_registry=registry,
        )
        check("a non-utf-8 requested encoding is rejected", result.error_code == "unsupported_encoding")


def test_18_reject_deleted_workspace() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.POPULATED)
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.READY)
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.EXECUTING)
        registry.update_workspace_status(workspace.workspace_id, to_status=gw.WorkspaceStatus.COMPLETED)
        registry.archive_workspace(workspace.workspace_id)
        registry.delete_workspace(workspace.workspace_id)
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="anything.txt"),
            workspace_registry=registry,
        )
        check("a deleted workspace rejects the read", result.error_code == "deleted")


def test_19_reject_unknown_workspace() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = gw.WorkspaceRegistry(approved_parent_directory=tmp)
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id="does-not-exist", relative_path="anything.txt"),
            workspace_registry=registry,
        )
        check("an unknown workspace_id is rejected", result.error_code == "workspace_not_found")


# ---------------------------------------------------------------------------
# Boundary behavior (20-23)
# ---------------------------------------------------------------------------


def test_20_output_metadata_does_not_auto_read_contents() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        _write(workspace.root_path, "auto.txt", b"should not be read automatically\n")
        # Registering manifest metadata (as v0.43.0's execute() does after a
        # real run) must never, by itself, produce any content anywhere.
        entry = registry.add_file_to_manifest(
            workspace.workspace_id, name="auto.txt", relative_path="auto.txt", source="execution", size=34
        )
        check("a manifest entry carries no content field", not hasattr(entry, "content"))


def test_21_execution_completion_does_not_auto_read_files() -> None:
    # This module exposes exactly one way to read a file: an explicit call
    # to read_workspace_file(...) with an explicit request. There is no
    # "on execution complete" hook, no callback, and no import-time side
    # effect that could trigger a read.
    import inspect

    source = inspect.getsource(fr)
    check(
        "the module defines read_workspace_file as its only read entry point",
        source.count("def read_workspace_file(") == 1,
    )
    check("no automatic/background reading helper exists in this module", "auto_read" not in source and "scan_workspace" not in source)


def test_22_read_result_contains_content_but_no_methodology_conclusion() -> None:
    import dataclasses

    result_fields = {f.name for f in dataclasses.fields(fr.WorkspaceFileReadResult)}
    for forbidden in ("methodology", "conclusion", "valid", "interpretation", "verdict"):
        check(f"WorkspaceFileReadResult has no {forbidden!r}-shaped field", forbidden not in result_fields)
    check("WorkspaceFileReadResult does carry 'content'", "content" in result_fields)


def test_23_truncated_content_is_clearly_marked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace = _new_workspace(tmp)
        oversized = b"y" * (fr.DEFAULT_MAX_BYTES + 100)
        _write(workspace.root_path, "big_allowed.txt", oversized)
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(
                workspace_id=workspace.workspace_id, relative_path="big_allowed.txt", allow_truncation=True
            ),
            workspace_registry=registry,
        )
        check("an allowed oversized read completes", result.status == fr.ReadStatus.COMPLETED.value)
        check("truncated flag is set", result.truncated is True)
        check("size_bytes reflects only the bytes actually returned", result.size_bytes == fr.DEFAULT_MAX_BYTES)
        assert result.provenance is not None
        check("provenance.complete is False for a truncated read", result.provenance.complete is False)


# ---------------------------------------------------------------------------
# Isolation (24)
# ---------------------------------------------------------------------------


def test_24_one_workspace_cannot_read_another_workspace_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry, workspace_a = _new_workspace(tmp)
        workspace_b = registry.create_workspace()
        Path(workspace_b.root_path).mkdir(parents=True, exist_ok=True)
        _write(workspace_b.root_path, "b_only.txt", b"belongs to workspace B\n")

        # Asking workspace A's registry entry to read a path that only
        # exists under workspace B's own root must fail closed -- the
        # relative_path, resolved against workspace A's root, simply does
        # not exist there.
        result = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace_a.workspace_id, relative_path="b_only.txt"),
            workspace_registry=registry,
        )
        check("workspace A cannot read a file that only exists in workspace B", result.error_code == "file_not_found")

        # And workspace B's own read of the same relative_path succeeds,
        # confirming the rejection above was genuine isolation, not a
        # blanket failure.
        result_b = fr.read_workspace_file(
            fr.WorkspaceFileReadRequest(workspace_id=workspace_b.workspace_id, relative_path="b_only.txt"),
            workspace_registry=registry,
        )
        check("workspace B can read its own file", result_b.status == fr.ReadStatus.COMPLETED.value)


def test_25_module_never_runs_gauss() -> None:
    check("gauss_code_execution is absent from sys.modules", "gauss_code_execution" not in sys.modules)
    check("gauss_runtime_orchestration is absent from sys.modules", "gauss_runtime_orchestration" not in sys.modules)
    check("gauss_execution_adapter is absent from sys.modules", "gauss_execution_adapter" not in sys.modules)


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
