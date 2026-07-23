"""Safe workspace-bound file reader (v0.44.0 Safe Workspace File Reading
Workflow).

Authoritative design source: `planning/v0.44.0-safe-file-reading-workflow.md`.
This module implements that plan's file-read request/result contract,
eligibility rules, size/encoding limits, and provenance model -- it does not
redefine them.

**Explicit-request only.** Nothing in this module reads a file on its own
initiative. `read_workspace_file(...)` is the single entry point, and it
always requires a caller-supplied `WorkspaceFileReadRequest` naming an exact
`workspace_id`/`relative_path` -- there is no scan, no directory listing, no
"read everything in the manifest" mode anywhere in this module.

**Dependency direction.** This module depends only on `scripts/gauss_
workspace.py` (for `WorkspaceRegistry`'s existing containment logic --
`get_workspace`, `validate_workspace`, `resolve_within_workspace`,
`get_workspace_manifest`). It has no dependency on `gauss_runtime_
orchestration.py`, `gauss_execution_adapter.py`, or `gauss_code_execution.py`,
never launches a subprocess, and never touches GAUSS.

**Supported formats.** Bounded text only: `.txt`, `.csv`, `.tsv`, `.out`,
`.log`, `.gss`, `.dat` -- and even these are rejected if their actual bytes
look binary (a NUL byte, or an excessive non-printable-byte ratio, in the
read sample), regardless of extension. No binary parsing, no spreadsheet
parsing, no image/PDF interpretation, no archive handling.

**Size/encoding are conservative and fail closed.** Every request is capped
by `ABSOLUTE_MAX_BYTES` regardless of what the caller asks for. Only UTF-8
is supported; any other requested encoding is rejected outright rather than
silently substituted. A file larger than the effective limit is rejected
outright unless the caller explicitly sets `allow_truncation=True`, in which
case `truncated=True` is set and `size_bytes`/`checksum` describe exactly
the bytes actually returned -- never the full file.

**No methodology conclusions.** `WorkspaceFileReadResult` has no field that
could hold one -- structurally, not merely by convention.
"""

from __future__ import annotations

import enum
import hashlib
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# gauss_workspace never mutates a real filesystem and never imports anything
# execution-adjacent (see its own module docstring) -- importing it here has
# no side effects.
import gauss_workspace as workspace_mod  # noqa: E402

# ---------------------------------------------------------------------------
# Limits and allowlist
# ---------------------------------------------------------------------------

DEFAULT_MAX_BYTES = 262_144  # 256 KiB -- conservative default for output-artifact-sized text
ABSOLUTE_MAX_BYTES = 5_242_880  # 5 MiB -- hard ceiling no request may exceed
SUPPORTED_ENCODING = "utf-8"

#: Extension allowlist. Every extension listed here is STILL subject to the
#: binary-content sniff below -- extension membership alone never authorizes
#: a read of content that actually looks binary.
ALLOWED_EXTENSIONS = frozenset({".txt", ".csv", ".tsv", ".out", ".log", ".gss", ".dat"})

_BINARY_SNIFF_SAMPLE_SIZE = 8192
_BINARY_NON_PRINTABLE_RATIO_THRESHOLD = 0.30
_PRINTABLE_BYTES = frozenset(
    {9, 10, 13} | set(range(0x20, 0x7F)) | set(range(0x80, 0x100))
)  # tab/LF/CR, ASCII printable, and high-bit bytes (may be valid UTF-8 continuation bytes)


def _looks_binary(sample: bytes) -> bool:
    """A NUL byte anywhere in the sample is treated as a definitive binary
    signal (the same heuristic git and many other tools use). Otherwise, an
    excessive proportion of non-printable, non-whitespace bytes is treated
    as binary too. Deliberately conservative -- false positives (rejecting
    genuinely-text content) are preferred over false negatives (accepting
    binary content as text)."""
    if not sample:
        return False
    if b"\x00" in sample:
        return True
    non_printable = sum(1 for b in sample if b not in _PRINTABLE_BYTES)
    return (non_printable / len(sample)) > _BINARY_NON_PRINTABLE_RATIO_THRESHOLD


# ---------------------------------------------------------------------------
# Request / result / provenance
# ---------------------------------------------------------------------------


class ReadStatus(enum.Enum):
    COMPLETED = "completed"
    REJECTED = "rejected"  # failed an eligibility/validation check before or during reading
    ERROR = "error"  # an unexpected OS-level fault during an otherwise-eligible read


@dataclass(frozen=True)
class WorkspaceFileReadRequest:
    workspace_id: str
    relative_path: str
    requested_purpose: str = ""
    expected_file_type: str | None = None
    max_bytes: int | None = None
    encoding: str = SUPPORTED_ENCODING
    allow_truncation: bool = False


@dataclass(frozen=True)
class FileReadProvenance:
    workspace_id: str
    relative_path: str
    size_bytes: int
    checksum: str
    read_at: float
    source_manifest_entry: "workspace_mod.ManifestFileEntry | None"
    complete: bool


@dataclass(frozen=True)
class WorkspaceFileReadResult:
    workspace_id: str
    relative_path: str
    status: str  # ReadStatus.value
    file_type: str | None
    size_bytes: int | None
    checksum: str | None
    encoding: str | None
    content: str | None
    truncated: bool
    provenance: FileReadProvenance | None
    error_code: str | None
    error_message: str | None


def _rejected(
    request: "WorkspaceFileReadRequest", *, error_code: str, error_message: str, status: ReadStatus = ReadStatus.REJECTED
) -> WorkspaceFileReadResult:
    return WorkspaceFileReadResult(
        workspace_id=request.workspace_id,
        relative_path=request.relative_path,
        status=status.value,
        file_type=None,
        size_bytes=None,
        checksum=None,
        encoding=None,
        content=None,
        truncated=False,
        provenance=None,
        error_code=error_code,
        error_message=error_message,
    )


def _file_type_of(relative_path: str) -> str:
    suffix = Path(relative_path).suffix.lower().lstrip(".")
    return suffix or "unknown"


def _find_manifest_entry(
    registry: "workspace_mod.WorkspaceRegistry", workspace_id: str, relative_path: str
) -> "workspace_mod.ManifestFileEntry | None":
    try:
        manifest = registry.get_workspace_manifest(workspace_id)
    except workspace_mod.WorkspaceNotFoundError:
        return None
    for entry in manifest.files:
        if entry.relative_path == relative_path:
            return entry
    return None


# ---------------------------------------------------------------------------
# The reader
# ---------------------------------------------------------------------------


def read_workspace_file(
    request: WorkspaceFileReadRequest,
    *,
    workspace_registry: "workspace_mod.WorkspaceRegistry",
    clock: Callable[[], float] = time.time,
) -> WorkspaceFileReadResult:
    """The single entry point. Always requires an explicit `request` and an
    explicit `workspace_registry` -- there is no default, no ambient
    workspace, and no scan. Every rejection is a structured result, never a
    raised exception, mirroring `gauss_execution_workflow.py`'s own
    established convention for eligibility-shaped failures."""

    # 1. Path must be relative.
    if Path(request.relative_path).is_absolute():
        return _rejected(request, error_code="path_not_relative", error_message="relative_path must not be absolute.")

    # 2. Encoding must be the one supported encoding.
    if request.encoding != SUPPORTED_ENCODING:
        return _rejected(
            request, error_code="unsupported_encoding",
            error_message=f"only {SUPPORTED_ENCODING!r} is supported; got {request.encoding!r}.",
        )

    # 3. Workspace must exist and pass general validity.
    try:
        workspace_registry.get_workspace(request.workspace_id)
    except workspace_mod.WorkspaceNotFoundError:
        return _rejected(
            request, error_code="workspace_not_found", error_message=f"no workspace exists for {request.workspace_id!r}."
        )
    workspace_outcome = workspace_registry.validate_workspace(request.workspace_id)
    if not workspace_outcome.valid:
        return _rejected(
            request,
            error_code=workspace_outcome.reason_category or "workspace_invalid",
            error_message=workspace_outcome.detail or "workspace failed validation.",
        )

    # 4. Path must resolve inside the workspace's own root (traversal and
    #    symlink-escape are both caught here, since Path.resolve() follows
    #    existing symlinks to their real target before the containment
    #    check is applied).
    resolved = workspace_registry.resolve_within_workspace(request.workspace_id, request.relative_path)
    if resolved is None:
        return _rejected(
            request, error_code="path_escapes_workspace",
            error_message="relative_path does not resolve inside this workspace's own root.",
        )

    # 5. File must exist and be a regular file.
    if not resolved.exists():
        return _rejected(request, error_code="file_not_found", error_message="the resolved path does not exist.")
    if not resolved.is_file():
        return _rejected(
            request, error_code="not_a_regular_file", error_message="the resolved path is not a regular file."
        )

    # 6. Extension allowlist.
    file_type = _file_type_of(request.relative_path)
    if resolved.suffix.lower() not in ALLOWED_EXTENSIONS:
        return _rejected(
            request, error_code="unsupported_file_type",
            error_message=f"extension {resolved.suffix!r} is not in the supported allowlist {sorted(ALLOWED_EXTENSIONS)}.",
        )
    if request.expected_file_type is not None and request.expected_file_type.lower() != file_type:
        return _rejected(
            request, error_code="file_type_mismatch",
            error_message=f"expected_file_type {request.expected_file_type!r} does not match actual type {file_type!r}.",
        )

    # 7. Size limit.
    try:
        actual_size = resolved.stat().st_size
    except OSError as exc:
        return _rejected(request, error_code="io_error", error_message=str(exc), status=ReadStatus.ERROR)
    effective_max = min(request.max_bytes or DEFAULT_MAX_BYTES, ABSOLUTE_MAX_BYTES)
    will_truncate = actual_size > effective_max
    if will_truncate and not request.allow_truncation:
        return _rejected(
            request, error_code="file_too_large",
            error_message=f"file is {actual_size} bytes, exceeding the effective limit of {effective_max} bytes.",
        )

    # 8. Read the bytes (bounded), sniff for binary content, decode.
    read_length = effective_max if will_truncate else actual_size
    try:
        with resolved.open("rb") as fh:
            raw = fh.read(read_length)
    except OSError as exc:
        return _rejected(request, error_code="io_error", error_message=str(exc), status=ReadStatus.ERROR)

    if _looks_binary(raw[:_BINARY_SNIFF_SAMPLE_SIZE]):
        return _rejected(
            request, error_code="binary_content_detected",
            error_message="the file's content does not look like text, regardless of its extension.",
        )

    truncated = will_truncate
    try:
        content = raw.decode(SUPPORTED_ENCODING, errors="strict")
    except UnicodeDecodeError:
        if truncated:
            # A truncation cut may legitimately land mid multi-byte
            # sequence -- tolerated only because truncated=True already
            # discloses that this content is not the full, exact file.
            content = raw.decode(SUPPORTED_ENCODING, errors="replace")
        else:
            return _rejected(
                request, error_code="decode_error",
                error_message="the file's bytes could not be decoded as UTF-8.",
            )

    checksum = hashlib.sha256(raw).hexdigest()
    now = clock()
    manifest_entry = _find_manifest_entry(workspace_registry, request.workspace_id, request.relative_path)
    provenance = FileReadProvenance(
        workspace_id=request.workspace_id,
        relative_path=request.relative_path,
        size_bytes=len(raw),
        checksum=checksum,
        read_at=now,
        source_manifest_entry=manifest_entry,
        complete=not truncated,
    )
    return WorkspaceFileReadResult(
        workspace_id=request.workspace_id,
        relative_path=request.relative_path,
        status=ReadStatus.COMPLETED.value,
        file_type=file_type,
        size_bytes=len(raw),
        checksum=checksum,
        encoding=SUPPORTED_ENCODING,
        content=content,
        truncated=truncated,
        provenance=provenance,
        error_code=None,
        error_message=None,
    )


# ---------------------------------------------------------------------------
# Self-test harness (this repository's established convention -- no pytest
# is configured anywhere in this repository)
# ---------------------------------------------------------------------------


def _run_self_tests() -> int:
    """A lightweight built-in smoke test. The focused, comprehensive test
    suite lives in scripts/test_gauss_workspace_file_reader.py. Never
    touches a real filesystem beyond a disposable temp directory; never
    invokes GAUSS."""
    import tempfile

    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        registry = workspace_mod.WorkspaceRegistry(approved_parent_directory=tmp)
        workspace = registry.create_workspace()
        Path(workspace.root_path).mkdir(parents=True, exist_ok=True)
        # write_bytes (not write_text) so the exact bytes on disk are known
        # precisely -- text-mode writes translate '\n' on Windows, which
        # would make an exact content comparison platform-dependent.
        (Path(workspace.root_path) / "results.txt").write_bytes(b"hello workspace\n")

        request = WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="results.txt")
        result = read_workspace_file(request, workspace_registry=registry)
        check("a supported text file reads successfully", result.status == ReadStatus.COMPLETED.value)
        check("content matches what was written", result.content == "hello workspace\n")
        check("provenance is attached", result.provenance is not None)

        traversal_request = WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="../escape.txt")
        traversal_result = read_workspace_file(traversal_request, workspace_registry=registry)
        check("path traversal is rejected", traversal_result.error_code == "path_escapes_workspace")

        missing_request = WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="does_not_exist.txt")
        missing_result = read_workspace_file(missing_request, workspace_registry=registry)
        check("a missing file is rejected", missing_result.error_code == "file_not_found")

        (Path(workspace.root_path) / "binary.dat").write_bytes(b"\x00\x01\x02binary")
        binary_request = WorkspaceFileReadRequest(workspace_id=workspace.workspace_id, relative_path="binary.dat")
        binary_result = read_workspace_file(binary_request, workspace_registry=registry)
        check("binary content is rejected regardless of extension", binary_result.error_code == "binary_content_detected")

    if failures:
        print(f"SELF-TEST FAILED ({len(failures)} issue(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SELF-TEST PASSED: all checks succeeded.")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Safe workspace-bound file reader (v0.44.0). Explicit-request only, bounded text "
            "formats only, no GAUSS invocation anywhere in this module."
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
