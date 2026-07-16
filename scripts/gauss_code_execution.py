"""Execute explicitly provided GAUSS code or an explicit GAUSS script file, safely.

This is a controlled, read/write-limited code execution helper implementing the
contract defined in tools/gauss_code_execution.md and validated against
schemas/gauss_code_execution.schema.json.

It only ever executes explicitly supplied code (`code`) or an explicitly supplied
script file (`script_path`) -- never both, never neither, never an arbitrary
discovered file. It requires an explicit, existing, safe `working_directory` and
a timeout for every attempt. It never installs packages, never activates
licenses, never accesses the network, never mutates global GAUSS configuration,
and never writes outside `working_directory`.

The one deliberately unresolved risk this module does not paper over is real
GAUSS non-interactive invocation: the exact command-line form to run a `.gss`
script non-interactively may be platform/version dependent and is not confirmed
here (see `_default_command_builder`'s warning). To keep this risk isolated,
actual process invocation goes through an injectable *runner* abstraction
(`runner=`) and command construction goes through an injectable *command
builder* (`command_builder=`), so `--self-test` can exercise every branch of
this module's logic with a fake runner and never depend on a real GAUSS
installation. See planning/v0.25.0-gauss-code-execution-implementation.md's
"Runner Abstraction" and "Command Construction" sections.

Package inspection context (`package_inspection_result`) is advisory: a
non-empty `missing_packages` blocks execution with a clear error (this helper
never auto-installs), while `unknown_packages` only adds a warning.

No Code Assistant workflow integration, no runtime orchestration, no automatic
debugging/rerun loop, and no report generation exist here or anywhere in this
repository yet.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

try:
    import gauss_environment_check as _env_check
except ImportError:  # pragma: no cover - defensive; keeps this script standalone
    _env_check = None

_ENV_STATUS_ENUM = {"found", "not_found", "ambiguous", "inaccessible", "error", "unknown"}

_GENERATED_SCRIPT_DIRNAME = ".gauss_code_execution_generated"

# Conservative, documented defaults -- exact values are an implementation
# decision, not fixed by planning/v0.25.0-gauss-code-execution-implementation.md.
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_TIMEOUT_SECONDS = 300.0
MAX_CAPTURE_CHARS = 20000


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_schema_path() -> Path:
    return repo_root() / "schemas" / "gauss_code_execution.schema.json"


def _default_accessible(path_str: str) -> Any:
    if _env_check is not None:
        return _env_check.check_accessible(path_str)
    try:
        p = Path(path_str)
        if not p.exists() or not p.is_file():
            return False
        if os.name == "nt":
            return True
        return os.access(str(p), os.X_OK)
    except OSError:
        return "unknown"


def _default_env_detect_fn() -> Callable[..., dict[str, Any]] | None:
    if _env_check is None:
        return None

    def _fn(platform_hint: str | None = None) -> dict[str, Any]:
        return _env_check.detect_environment(platform_hint=platform_hint)

    return _fn


def _missing_version_warning() -> str:
    return (
        "GAUSS version is not known for the selected environment context; command construction "
        "cannot verify version-specific invocation behavior."
    )


def _resolve_environment_context(
    *,
    environment_check_result: dict[str, Any] | None,
    executable_path: str | None,
    gauss_version: str | None,
    strict: bool,
    path_exists_fn: Callable[[str], bool],
    accessibility_fn: Callable[[str], Any],
    env_detect_fn: Callable[..., dict[str, Any]] | None,
) -> tuple[str, str | None, str | None, list[str]]:
    """Return (environment_status, executable_path, gauss_version, warnings).

    Precedence: explicit executable_path/gauss_version arguments, then
    environment_check_result, then environment detection (unless strict), then
    unavailable -- the same precedence gauss_package_inspection.py already uses.
    """
    if executable_path:
        if not path_exists_fn(executable_path):
            return (
                "not_found",
                None,
                None,
                ["The provided executable_path does not exist; it could not be used as execution context."],
            )
        accessible = accessibility_fn(executable_path)
        if accessible is not True:
            return (
                "inaccessible",
                None,
                None,
                ["The provided executable_path exists but could not be confirmed accessible."],
            )
        warnings = [] if gauss_version else [_missing_version_warning()]
        return "found", executable_path, gauss_version, warnings

    if environment_check_result:
        detection_status = environment_check_result.get("detection_status", "unknown")
        if detection_status not in _ENV_STATUS_ENUM:
            detection_status = "unknown"
        if detection_status == "found":
            version = environment_check_result.get("version")
            warnings = [] if version else [_missing_version_warning()]
            return "found", environment_check_result.get("executable_path"), version, warnings
        return (
            detection_status,
            None,
            None,
            ["The supplied environment_check_result did not indicate a found GAUSS environment."],
        )

    if strict:
        return (
            "unknown",
            None,
            None,
            [
                "strict mode was requested without environment_check_result or a direct executable_path/"
                "gauss_version, so no environment detection was attempted."
            ],
        )

    detect_fn = env_detect_fn if env_detect_fn is not None else _default_env_detect_fn()
    if detect_fn is None:
        return (
            "unknown",
            None,
            None,
            ["No environment context was provided and GAUSS environment detection was not available to call."],
        )

    env_result = detect_fn(platform_hint=None)
    detection_status = env_result.get("detection_status", "unknown")
    if detection_status not in _ENV_STATUS_ENUM:
        detection_status = "unknown"
    if detection_status == "found":
        version = env_result.get("version")
        warnings = ["Environment context was obtained by calling GAUSS environment detection automatically."]
        if not version:
            warnings.append(_missing_version_warning())
        return "found", env_result.get("executable_path"), version, warnings
    return (
        detection_status,
        None,
        None,
        ["GAUSS environment detection was attempted automatically but did not return a found environment."],
    )


def _package_context_warnings_and_block(
    package_inspection_result: dict[str, Any] | None,
) -> tuple[list[str], str | None]:
    """Conservative default policy: block on any non-empty missing_packages, warn on unknown_packages."""
    if not package_inspection_result:
        return [], None
    missing = package_inspection_result.get("missing_packages") or []
    unknown = package_inspection_result.get("unknown_packages") or []
    warnings: list[str] = []
    if unknown:
        warnings.append(
            f"Package inspection reported unknown status for: {', '.join(unknown)}; execution proceeds, "
            "but package availability could not be confirmed."
        )
    if missing:
        error = (
            f"Execution was blocked because package inspection reported missing package(s): "
            f"{', '.join(missing)}. This helper does not install packages."
        )
        return warnings, error
    return warnings, None


def _resolve_inside(base_dir: Path, candidate: str) -> Path | None:
    """Resolve `candidate` relative to `base_dir` and return it only if it stays inside base_dir."""
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


def _validate_inputs(
    *,
    code: str | None,
    script_path: str | None,
    working_directory: str | None,
    output_directory: str | None,
    input_files: list[str],
    timeout_seconds: float | None,
    allow_network: bool,
    path_exists_fn: Callable[[str], bool],
    is_dir_fn: Callable[[str], bool],
) -> dict[str, Any]:
    warnings: list[str] = []
    if allow_network:
        warnings.append(
            "Network access was requested via allow_network, but this helper does not support network "
            "access; execution proceeds without network access."
        )

    if code and script_path:
        return {
            "status": "blocked",
            "code_source": "unknown",
            "script_path_out": None,
            "working_directory": working_directory,
            "output_directory": None,
            "timeout_seconds": None,
            "warnings": warnings,
            "errors": ["Both code and script_path were supplied; exactly one is required for execution."],
            "next_steps": [
                "Supply exactly one of code or script_path, not both.",
                "Continue in Advisory Mode; code generation, explanation, and review remain fully available.",
            ],
        }

    if not code and not script_path:
        return {
            "status": "skipped",
            "code_source": "none",
            "script_path_out": None,
            "working_directory": working_directory,
            "output_directory": None,
            "timeout_seconds": None,
            "warnings": warnings + ["No code or script_path was supplied; execution was not attempted."],
            "errors": [],
            "next_steps": [
                "Provide exactly one of code or script_path to request explicit execution.",
                "Continue in Advisory Mode; code generation, explanation, and review remain fully available.",
            ],
        }

    code_source = "inline" if code else "script_path"

    if not working_directory or not path_exists_fn(working_directory) or not is_dir_fn(working_directory):
        return {
            "status": "blocked",
            "code_source": code_source,
            "script_path_out": None,
            "working_directory": None,
            "output_directory": None,
            "timeout_seconds": None,
            "warnings": warnings,
            "errors": [
                "Execution was blocked because no safe working_directory was supplied; execution requires "
                "an explicit, existing working directory and cannot proceed without one."
            ],
            "next_steps": [
                "Provide an explicit, existing working_directory scoped to this execution request.",
                "Create a dedicated safe working directory if one does not already exist.",
                "Continue in Advisory Mode; code generation, explanation, and review remain fully available.",
            ],
        }

    working_dir_path = Path(working_directory)

    script_path_out: str | None = None
    if code_source == "script_path":
        resolved = _resolve_inside(working_dir_path, script_path)
        if resolved is None:
            return {
                "status": "blocked",
                "code_source": code_source,
                "script_path_out": None,
                "working_directory": str(working_dir_path),
                "output_directory": None,
                "timeout_seconds": None,
                "warnings": warnings,
                "errors": [
                    "Execution was blocked because script_path resolves outside the safe working_directory "
                    "via path traversal; this is not permitted."
                ],
                "next_steps": [
                    "Place the script file directly under the safe working_directory.",
                    "Provide a script_path that resolves inside working_directory without traversal.",
                    "Continue in Advisory Mode; code generation, explanation, and review remain fully available.",
                ],
            }
        script_path_out = str(resolved)

    resolved_output_dir = str(working_dir_path)
    if output_directory:
        resolved = _resolve_inside(working_dir_path, output_directory)
        if resolved is None:
            return {
                "status": "blocked",
                "code_source": code_source,
                "script_path_out": script_path_out,
                "working_directory": str(working_dir_path),
                "output_directory": None,
                "timeout_seconds": None,
                "warnings": warnings,
                "errors": [
                    "Execution was blocked because output_directory resolves outside the safe "
                    "working_directory via path traversal; this is not permitted."
                ],
                "next_steps": [
                    "Provide an output_directory that resolves inside working_directory without traversal.",
                    "Continue in Advisory Mode; code generation, explanation, and review remain fully available.",
                ],
            }
        resolved_output_dir = str(resolved)

    for f in input_files:
        resolved = _resolve_inside(working_dir_path, f)
        if resolved is None:
            return {
                "status": "blocked",
                "code_source": code_source,
                "script_path_out": script_path_out,
                "working_directory": str(working_dir_path),
                "output_directory": None,
                "timeout_seconds": None,
                "warnings": warnings,
                "errors": [
                    f"Execution was blocked because input file '{f}' resolves outside the safe "
                    "working_directory via path traversal; this is not permitted."
                ],
                "next_steps": [
                    "Provide input_files that resolve inside working_directory without traversal.",
                    "Continue in Advisory Mode; code generation, explanation, and review remain fully available.",
                ],
            }

    if timeout_seconds is None:
        timeout_final = DEFAULT_TIMEOUT_SECONDS
    elif timeout_seconds <= 0:
        return {
            "status": "blocked",
            "code_source": code_source,
            "script_path_out": script_path_out,
            "working_directory": str(working_dir_path),
            "output_directory": None,
            "timeout_seconds": None,
            "warnings": warnings,
            "errors": ["Execution was blocked because timeout_seconds must be positive."],
            "next_steps": [
                "Provide a positive timeout_seconds value, or omit it to use the default.",
                "Continue in Advisory Mode; code generation, explanation, and review remain fully available.",
            ],
        }
    elif timeout_seconds > MAX_TIMEOUT_SECONDS:
        timeout_final = MAX_TIMEOUT_SECONDS
        warnings.append(
            f"Requested timeout_seconds ({timeout_seconds}) exceeded the maximum of "
            f"{MAX_TIMEOUT_SECONDS}; capped to the maximum."
        )
    else:
        timeout_final = float(timeout_seconds)

    return {
        "status": "ok",
        "code_source": code_source,
        "script_path_out": script_path_out,
        "working_directory": str(working_dir_path),
        "output_directory": resolved_output_dir,
        "timeout_seconds": timeout_final,
        "warnings": warnings,
        "errors": [],
        "next_steps": [],
    }


def _prepare_code(
    *,
    code_source: str,
    code: str | None,
    script_path_for_command: str | None,
    working_directory: str,
    raw_details: dict[str, Any],
) -> tuple[str | None, list[str]]:
    """Return (script_path_to_execute, errors)."""
    if code_source == "script_path":
        return script_path_for_command, []
    if code_source != "inline":
        return None, []

    gen_dir = Path(working_directory) / _GENERATED_SCRIPT_DIRNAME
    try:
        gen_dir.mkdir(exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix="inline_", suffix=".gss", dir=str(gen_dir))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code or "")
    except OSError as exc:
        return None, [f"Failed to write inline code to a temporary script file: {exc}"]
    raw_details["generated_script_path"] = tmp_path
    return tmp_path, []


def _default_command_builder(*, executable_path: str, script_path: str) -> tuple[list[str], list[str]]:
    """Conservative, documented-best-effort command construction.

    No safe, confirmed non-interactive GAUSS invocation syntax is documented in
    this repository yet -- see this module's docstring and
    planning/v0.25.0-gauss-code-execution-implementation.md's "Command
    Construction" section. This is the single, clearly-labeled extension point
    a future implementation would revise once a confirmed form is known.
    """
    warnings = [
        "GAUSS non-interactive invocation syntax is a best-effort assumption ([executable_path, "
        "script_path]) and may be platform/version dependent; verify against the actual GAUSS "
        "installation before relying on this in production."
    ]
    return [executable_path, script_path], warnings


def _make_default_runner(monotonic_fn: Callable[[], float]) -> Callable[[list[str], str, float], dict[str, Any]]:
    """Default runner: subprocess.run with a timeout, no shell, cwd=working_directory."""

    def _runner(command: list[str], working_directory: str, timeout_seconds: float) -> dict[str, Any]:
        start = monotonic_fn()
        try:
            proc = subprocess.run(
                command,
                cwd=working_directory,
                timeout=timeout_seconds,
                capture_output=True,
                text=True,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = monotonic_fn() - start
            return {
                "executed": True,
                "timed_out": True,
                "exit_code": None,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "elapsed_seconds": elapsed,
                "raw_details": {},
            }
        except OSError as exc:
            elapsed = monotonic_fn() - start
            return {
                "executed": False,
                "timed_out": False,
                "exit_code": None,
                "stdout": "",
                "stderr": "",
                "elapsed_seconds": elapsed,
                "raw_details": {"os_error": str(exc)},
            }
        elapsed = monotonic_fn() - start
        return {
            "executed": True,
            "timed_out": False,
            "exit_code": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "elapsed_seconds": elapsed,
            "raw_details": {},
        }

    return _runner


def _truncate(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_CAPTURE_CHARS:
        return text, False
    return text[:MAX_CAPTURE_CHARS], True


def _discover_output_files(
    *,
    output_directory: str | None,
    working_directory: str | None,
    list_files_fn: Callable[[str], list[str]],
) -> tuple[list[dict[str, Any]], list[str]]:
    target_dir = output_directory or working_directory
    if not target_dir:
        return [], []
    try:
        names = list_files_fn(target_dir)
    except OSError:
        return [], [f"Output file discovery could not list files under '{target_dir}'."]

    files: list[dict[str, Any]] = []
    for name in names:
        if name == _GENERATED_SCRIPT_DIRNAME:
            continue
        full = Path(target_dir) / name
        if not full.is_file():
            continue
        try:
            size = full.stat().st_size
        except OSError:
            size = None
        file_type, _ = mimetypes.guess_type(str(full))
        files.append(
            {
                "path": str(full),
                "size_bytes": size,
                "file_type": file_type,
                "created_by_execution": "unknown",
                "notes": [
                    "Discovered via read-only directory listing after execution; created_by_execution "
                    "could not be reliably determined without a before/after comparison."
                ],
            }
        )
    return files, []


def _build_result(
    *,
    checked: bool,
    executed: bool,
    execution_status: str,
    operating_mode: str,
    executable_path: str | None,
    gauss_version: str | None,
    working_directory: str | None,
    command: str | None,
    code_source: str,
    script_path: str | None,
    timeout_seconds: float | None,
    elapsed_seconds: float | None,
    exit_code: int | None,
    stdout: str | None,
    stderr: str | None,
    output_files: list[dict[str, Any]],
    warnings: list[str],
    errors: list[str],
    next_steps: list[str],
    raw_execution_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "checked": checked,
        "executed": executed,
        "execution_status": execution_status,
        "operating_mode": operating_mode,
        "executable_path": executable_path,
        "gauss_version": gauss_version,
        "working_directory": working_directory,
        "command": command,
        "code_source": code_source,
        "script_path": script_path,
        "timeout_seconds": timeout_seconds,
        "elapsed_seconds": elapsed_seconds,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "output_files": output_files,
        "warnings": warnings,
        "errors": errors,
        "next_steps": next_steps,
    }
    if raw_execution_details:
        result["raw_execution_details"] = raw_execution_details
    return result


_GENERIC_ADVISORY_NEXT_STEP = (
    "Continue in Advisory Mode; this error does not block code writing, explanation, review, "
    "documentation, education, or product reasoning."
)


def execute_gauss_code(
    environment_check_result: dict[str, Any] | None = None,
    package_inspection_result: dict[str, Any] | None = None,
    executable_path: str | None = None,
    gauss_version: str | None = None,
    code: str | None = None,
    script_path: str | None = None,
    working_directory: str | None = None,
    input_files: list[str] | None = None,
    output_directory: str | None = None,
    timeout_seconds: float | None = None,
    allow_file_write: bool = False,
    allow_output_files: bool = True,
    allow_network: bool = False,
    strict: bool = False,
    capture_stdout: bool = True,
    capture_stderr: bool = True,
    validate_schema: bool = False,
    *,
    runner: Callable[[list[str], str, float], dict[str, Any]] | None = None,
    command_builder: Callable[..., tuple[list[str], list[str]]] | None = None,
    env_detect_fn: Callable[..., dict[str, Any]] | None = None,
    path_exists_fn: Callable[[str], bool] | None = None,
    is_dir_fn: Callable[[str], bool] | None = None,
    accessibility_fn: Callable[[str], Any] | None = None,
    list_files_fn: Callable[[str], list[str]] | None = None,
    monotonic_fn: Callable[[], float] | None = None,
) -> dict[str, Any]:
    """Run controlled, explicit GAUSS code/script execution and return a schema-shaped result.

    `runner`, `command_builder`, `env_detect_fn`, `path_exists_fn`, `is_dir_fn`,
    `accessibility_fn`, `list_files_fn`, and `monotonic_fn` are injectable for
    testing (see `_run_self_tests`) so this function can be exercised end-to-end
    -- including successful/failed/timed-out "executions" -- without ever
    invoking a real GAUSS subprocess.

    `validate_schema` is accepted for input-contract completeness; schema
    validation is performed by `validate_against_schema(...)`, invoked
    separately by the CLI. `capture_stdout`/`capture_stderr` are accepted for
    input-contract completeness -- capture is always attempted when the runner
    is actually invoked. `allow_file_write` is accepted for input-contract
    completeness -- this helper already confines every write (including the
    temporary script it generates for inline code) to `working_directory`
    unconditionally, so there is currently nothing additional for this flag to
    unlock.
    """
    del validate_schema, capture_stdout, capture_stderr, allow_file_write

    path_exists_fn = path_exists_fn or (lambda p: Path(p).exists())
    is_dir_fn = is_dir_fn or (lambda p: Path(p).is_dir())
    accessibility_fn = accessibility_fn or _default_accessible
    list_files_fn = list_files_fn or (lambda d: [p.name for p in Path(d).iterdir()])
    monotonic_fn = monotonic_fn or time.monotonic
    runner = runner or _make_default_runner(monotonic_fn)
    command_builder = command_builder or _default_command_builder

    requested_input_files = list(input_files) if input_files else []

    try:
        env_status, exec_path, gauss_ver, env_warnings = _resolve_environment_context(
            environment_check_result=environment_check_result,
            executable_path=executable_path,
            gauss_version=gauss_version,
            strict=strict,
            path_exists_fn=path_exists_fn,
            accessibility_fn=accessibility_fn,
            env_detect_fn=env_detect_fn,
        )
    except Exception as exc:  # noqa: BLE001 -- execution must never crash the caller
        return _build_result(
            checked=True,
            executed=False,
            execution_status="error",
            operating_mode="advisory",
            executable_path=None,
            gauss_version=None,
            working_directory=None,
            command=None,
            code_source="unknown",
            script_path=None,
            timeout_seconds=None,
            elapsed_seconds=None,
            exit_code=None,
            stdout=None,
            stderr=None,
            output_files=[],
            warnings=[],
            errors=[f"Unexpected error resolving environment context: {exc}"],
            next_steps=[_GENERIC_ADVISORY_NEXT_STEP],
        )

    warnings = list(env_warnings)

    if env_status != "found":
        warnings.append("Execution could not proceed because the GAUSS environment is not confirmed found.")
        return _build_result(
            checked=True,
            executed=False,
            execution_status="blocked",
            operating_mode="advisory",
            executable_path=None,
            gauss_version=None,
            working_directory=None,
            command=None,
            code_source="unknown",
            script_path=None,
            timeout_seconds=None,
            elapsed_seconds=None,
            exit_code=None,
            stdout=None,
            stderr=None,
            output_files=[],
            warnings=warnings,
            errors=["Execution was blocked because no usable GAUSS environment context was available."],
            next_steps=[
                "Run GAUSS environment detection (gauss_environment_check) and confirm a found result "
                "before requesting execution.",
                "Provide executable_path directly if GAUSS is installed in a nonstandard location.",
                "Continue in Advisory Mode; code generation, explanation, and review remain fully available.",
            ],
        )

    try:
        validation = _validate_inputs(
            code=code,
            script_path=script_path,
            working_directory=working_directory,
            output_directory=output_directory,
            input_files=requested_input_files,
            timeout_seconds=timeout_seconds,
            allow_network=allow_network,
            path_exists_fn=path_exists_fn,
            is_dir_fn=is_dir_fn,
        )
    except Exception as exc:  # noqa: BLE001
        return _build_result(
            checked=True,
            executed=False,
            execution_status="error",
            operating_mode="advisory",
            executable_path=exec_path,
            gauss_version=gauss_ver,
            working_directory=None,
            command=None,
            code_source="unknown",
            script_path=None,
            timeout_seconds=None,
            elapsed_seconds=None,
            exit_code=None,
            stdout=None,
            stderr=None,
            output_files=[],
            warnings=warnings,
            errors=[f"Unexpected error validating inputs: {exc}"],
            next_steps=[_GENERIC_ADVISORY_NEXT_STEP],
        )

    if validation["status"] in ("blocked", "skipped"):
        return _build_result(
            checked=True,
            executed=False,
            execution_status=validation["status"],
            operating_mode="advisory",
            executable_path=exec_path,
            gauss_version=gauss_ver,
            working_directory=validation["working_directory"],
            command=None,
            code_source=validation["code_source"],
            script_path=validation["script_path_out"],
            timeout_seconds=validation["timeout_seconds"],
            elapsed_seconds=None,
            exit_code=None,
            stdout=None,
            stderr=None,
            output_files=[],
            warnings=warnings + validation["warnings"],
            errors=validation["errors"],
            next_steps=validation["next_steps"],
        )

    pkg_warnings, pkg_block_error = _package_context_warnings_and_block(package_inspection_result)
    warnings = warnings + validation["warnings"] + pkg_warnings

    if pkg_block_error:
        return _build_result(
            checked=True,
            executed=False,
            execution_status="blocked",
            operating_mode="advisory",
            executable_path=exec_path,
            gauss_version=gauss_ver,
            working_directory=validation["working_directory"],
            command=None,
            code_source=validation["code_source"],
            script_path=validation["script_path_out"],
            timeout_seconds=validation["timeout_seconds"],
            elapsed_seconds=None,
            exit_code=None,
            stdout=None,
            stderr=None,
            output_files=[],
            warnings=warnings,
            errors=[pkg_block_error],
            next_steps=[
                "Install or enable the missing package outside this helper; the helper does not install "
                "packages.",
                "Choose an alternative approach that does not require the missing package.",
                "Continue in Advisory Mode; code generation, explanation, and review remain fully available.",
            ],
        )

    raw_details: dict[str, Any] = {}
    try:
        script_to_run, prep_errors = _prepare_code(
            code_source=validation["code_source"],
            code=code,
            script_path_for_command=validation["script_path_out"],
            working_directory=validation["working_directory"],
            raw_details=raw_details,
        )
    except Exception as exc:  # noqa: BLE001
        script_to_run, prep_errors = None, [f"Unexpected error preparing code for execution: {exc}"]

    if prep_errors:
        return _build_result(
            checked=True,
            executed=False,
            execution_status="error",
            operating_mode="advisory",
            executable_path=exec_path,
            gauss_version=gauss_ver,
            working_directory=validation["working_directory"],
            command=None,
            code_source=validation["code_source"],
            script_path=validation["script_path_out"],
            timeout_seconds=validation["timeout_seconds"],
            elapsed_seconds=None,
            exit_code=None,
            stdout=None,
            stderr=None,
            output_files=[],
            warnings=warnings,
            errors=prep_errors,
            next_steps=[_GENERIC_ADVISORY_NEXT_STEP],
        )

    command_list, command_warnings = command_builder(executable_path=exec_path, script_path=script_to_run)
    warnings = warnings + command_warnings
    command_str = " ".join(command_list)

    try:
        runner_result = runner(command_list, validation["working_directory"], validation["timeout_seconds"])
    except Exception as exc:  # noqa: BLE001
        return _build_result(
            checked=True,
            executed=False,
            execution_status="error",
            operating_mode="advisory",
            executable_path=exec_path,
            gauss_version=gauss_ver,
            working_directory=validation["working_directory"],
            command=command_str,
            code_source=validation["code_source"],
            script_path=validation["script_path_out"],
            timeout_seconds=validation["timeout_seconds"],
            elapsed_seconds=None,
            exit_code=None,
            stdout=None,
            stderr=None,
            output_files=[],
            warnings=warnings,
            errors=[f"Unexpected runner error: {exc}"],
            next_steps=[_GENERIC_ADVISORY_NEXT_STEP],
        )

    executed = bool(runner_result.get("executed"))
    elapsed = runner_result.get("elapsed_seconds")
    exit_code = runner_result.get("exit_code")
    stdout_text, stdout_truncated = _truncate(runner_result.get("stdout") or "")
    stderr_text, stderr_truncated = _truncate(runner_result.get("stderr") or "")
    if stdout_truncated:
        warnings.append("Captured stdout exceeded the capture limit and was truncated.")
    if stderr_truncated:
        warnings.append("Captured stderr exceeded the capture limit and was truncated.")

    if not executed:
        raw_error = (runner_result.get("raw_details") or {}).get("os_error")
        return _build_result(
            checked=True,
            executed=False,
            execution_status="error",
            operating_mode="advisory",
            executable_path=exec_path,
            gauss_version=gauss_ver,
            working_directory=validation["working_directory"],
            command=command_str,
            code_source=validation["code_source"],
            script_path=validation["script_path_out"],
            timeout_seconds=validation["timeout_seconds"],
            elapsed_seconds=elapsed,
            exit_code=None,
            stdout=stdout_text or None,
            stderr=stderr_text or None,
            output_files=[],
            warnings=warnings,
            errors=[raw_error or "The GAUSS executable could not be invoked."],
            next_steps=[_GENERIC_ADVISORY_NEXT_STEP],
        )

    if runner_result.get("timed_out"):
        warnings.append(
            f"Execution exceeded the timeout of {validation['timeout_seconds']} seconds and was terminated."
        )
        status = "timed_out"
        errors: list[str] = []
        next_steps = [
            "Review the script for unbounded loops or long-running operations.",
            "Reduce the runtime of the executed code if possible.",
            "Increase timeout_seconds only if a longer run is genuinely safe and expected.",
        ]
    elif exit_code == 0:
        status = "completed"
        errors = []
        next_steps = [
            "Interpret the results separately using the relevant expert (for example, the Econometrics "
            "Expert for methodology and diagnostics).",
            "Review methodology and diagnostics before treating any estimate as meaningful.",
        ]
    else:
        status = "failed"
        errors = [f"GAUSS process exited with nonzero status ({exit_code}); execution failed."]
        next_steps = [
            "Inspect stderr for the specific failure cause.",
            "Verify command syntax against GAUSS Language Expert evidence before retrying.",
            "Check whether a required package dependency is missing.",
        ]

    output_files: list[dict[str, Any]] = []
    if allow_output_files:
        output_files, discovery_warnings = _discover_output_files(
            output_directory=validation["output_directory"],
            working_directory=validation["working_directory"],
            list_files_fn=list_files_fn,
        )
        warnings.extend(discovery_warnings)

    return _build_result(
        checked=True,
        executed=True,
        execution_status=status,
        operating_mode="execution",
        executable_path=exec_path,
        gauss_version=gauss_ver,
        working_directory=validation["working_directory"],
        command=command_str,
        code_source=validation["code_source"],
        script_path=validation["script_path_out"],
        timeout_seconds=validation["timeout_seconds"],
        elapsed_seconds=elapsed,
        exit_code=exit_code,
        stdout=stdout_text,
        stderr=stderr_text,
        output_files=output_files,
        warnings=warnings,
        errors=errors,
        next_steps=next_steps,
        raw_execution_details=raw_details or None,
    )


def validate_against_schema(result: dict[str, Any], schema_path: Path) -> list[str]:
    """Validate a result dict against the schema. Returns jsonschema error messages.

    Returns a single explanatory item (not an exception) if jsonschema is not
    installed, so execution results remain usable without the optional
    validation dependency.
    """
    try:
        from jsonschema import Draft202012Validator
    except ModuleNotFoundError:
        return [
            "jsonschema is not installed; skipped schema validation. "
            "Install with: python -m pip install jsonschema"
        ]

    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(result), key=lambda e: list(e.path))
    messages: list[str] = []
    for error in errors:
        path = "$"
        if error.path:
            path += "".join(f"[{part!r}]" for part in error.path)
        messages.append(f"{path}: {error.message}")
    return messages


def print_human(result: dict[str, Any]) -> None:
    print(f"Execution status:                {result['execution_status']}")
    print(f"Operating mode:                  {result['operating_mode']}")
    print(f"Executed:                        {result['executed']}")
    print(f"Executable path / GAUSS version: {result['executable_path']} / {result['gauss_version']}")
    print(f"Working directory:               {result['working_directory']}")
    print(f"Code source / script path:       {result['code_source']} / {result['script_path']}")
    print(f"Command:                         {result['command']}")
    print(f"Timeout / elapsed (s):           {result['timeout_seconds']} / {result['elapsed_seconds']}")
    print(f"Exit code:                       {result['exit_code']}")

    if result["stdout"]:
        print("\nstdout:")
        print(result["stdout"])

    if result["stderr"]:
        print("\nstderr:")
        print(result["stderr"])

    if result["output_files"]:
        print("\nOutput files:")
        for f in result["output_files"]:
            print(f"  - {f['path']} ({f['size_bytes']} bytes, created_by_execution={f['created_by_execution']})")

    if result["warnings"]:
        print("\nWarnings:")
        for w in result["warnings"]:
            print(f"  - {w}")

    if result["errors"]:
        print("\nErrors:")
        for e in result["errors"]:
            print(f"  - {e}")

    if result["next_steps"]:
        print("\nNext steps:")
        for n in result["next_steps"]:
            print(f"  - {n}")


def _run_self_tests() -> int:
    """Lightweight built-in test suite using a fake runner and real disposable temp directories.

    No real GAUSS installation is required: every "execution" here is a fake
    runner call. Temp directories are real (via tempfile) so working-directory,
    path-safety, and output-file-discovery logic is exercised for real, safely,
    against disposable filesystem state.
    """
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    found_env = {"detection_status": "found", "executable_path": "/example/gauss26/tgauss", "version": "GAUSS 26"}

    def fake_runner_factory(
        exit_code: int = 0, stdout: str = "", stderr: str = "", timed_out: bool = False, executed: bool = True
    ) -> Callable[[list[str], str, float], dict[str, Any]]:
        def _runner(command: list[str], working_directory: str, timeout_seconds: float) -> dict[str, Any]:
            del command, working_directory, timeout_seconds
            return {
                "executed": executed,
                "timed_out": timed_out,
                "exit_code": None if timed_out else exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "elapsed_seconds": 0.1,
                "raw_details": {},
            }

        return _runner

    with tempfile.TemporaryDirectory(prefix="gauss_exec_selftest_") as tmp_dir:
        result = execute_gauss_code(
            environment_check_result={"detection_status": "not_found"}, code="print 1;", working_directory=tmp_dir
        )
        check("missing executable -> blocked", result["execution_status"] == "blocked" and result["executed"] is False)

        result = execute_gauss_code(
            environment_check_result={"detection_status": "ambiguous"}, code="print 1;", working_directory=tmp_dir
        )
        check("ambiguous environment -> blocked", result["execution_status"] == "blocked" and result["executed"] is False)

        result = execute_gauss_code(environment_check_result=found_env, working_directory=tmp_dir)
        check("no code or script -> skipped", result["execution_status"] == "skipped" and result["executed"] is False)

        result = execute_gauss_code(
            environment_check_result=found_env, code="print 1;", script_path="script.gss", working_directory=tmp_dir
        )
        check("both code and script -> blocked", result["execution_status"] == "blocked" and result["executed"] is False)

        result = execute_gauss_code(environment_check_result=found_env, code="print 1;", working_directory=None)
        check("missing working_directory (None) -> blocked", result["execution_status"] == "blocked")

        result = execute_gauss_code(
            environment_check_result=found_env,
            code="print 1;",
            working_directory=str(Path(tmp_dir) / "does_not_exist"),
        )
        check("missing working_directory (nonexistent) -> blocked", result["execution_status"] == "blocked")

        result = execute_gauss_code(
            environment_check_result=found_env,
            code='print "hello";',
            working_directory=tmp_dir,
            runner=fake_runner_factory(exit_code=0, stdout="hello", stderr=""),
        )
        check("successful fake execution -> completed", result["execution_status"] == "completed")
        check("completed -> executed true", result["executed"] is True)
        check("completed -> operating_mode execution", result["operating_mode"] == "execution")
        check("stdout captured", result["stdout"] == "hello")
        check("exit_code 0 maps to completed", result["execution_status"] == "completed")

        result = execute_gauss_code(
            environment_check_result=found_env,
            code="print 1;",
            working_directory=tmp_dir,
            runner=fake_runner_factory(exit_code=1, stdout="", stderr="boom"),
        )
        check("failed fake execution -> failed", result["execution_status"] == "failed")
        check("stderr captured", result["stderr"] == "boom")
        check("nonzero exit maps to failed", result["execution_status"] == "failed")

        result = execute_gauss_code(
            environment_check_result=found_env,
            code="print 1;",
            working_directory=tmp_dir,
            timeout_seconds=5,
            runner=fake_runner_factory(timed_out=True, stdout="partial"),
        )
        check("timeout fake execution -> timed_out", result["execution_status"] == "timed_out")
        check("timed_out has warnings or errors", len(result["warnings"]) + len(result["errors"]) >= 1)
        check("timed_out -> executed true", result["executed"] is True)

        big_output = "x" * (MAX_CAPTURE_CHARS + 500)
        result = execute_gauss_code(
            environment_check_result=found_env,
            code="print 1;",
            working_directory=tmp_dir,
            runner=fake_runner_factory(exit_code=0, stdout=big_output),
        )
        check("large stdout truncated", len(result["stdout"]) == MAX_CAPTURE_CHARS)
        check("truncation warning recorded", any("truncat" in w.lower() for w in result["warnings"]))

        with tempfile.TemporaryDirectory(prefix="gauss_exec_selftest_outputs_") as out_dir:
            Path(out_dir, "results.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            result = execute_gauss_code(
                environment_check_result=found_env,
                code="print 1;",
                working_directory=out_dir,
                runner=fake_runner_factory(exit_code=0),
                allow_output_files=True,
            )
            check(
                "output files limited to working_directory",
                len(result["output_files"]) == 1 and result["output_files"][0]["path"].endswith("results.csv"),
            )

        result = execute_gauss_code(
            environment_check_result=found_env, script_path="../outside.gss", working_directory=tmp_dir
        )
        check("path traversal rejected", result["execution_status"] == "blocked")

        result = execute_gauss_code(
            environment_check_result=found_env,
            code="print 1;",
            working_directory=tmp_dir,
            runner=fake_runner_factory(exit_code=0),
            allow_network=True,
        )
        check("allow_network warning present", any("network" in w.lower() for w in result["warnings"]))

        blocked_results = [
            execute_gauss_code(
                environment_check_result={"detection_status": "not_found"}, code="print 1;", working_directory=tmp_dir
            ),
            execute_gauss_code(environment_check_result=found_env, working_directory=tmp_dir),
        ]
        check(
            "executed false never reports completed",
            all(r["execution_status"] != "completed" for r in blocked_results if r["executed"] is False),
        )

        result = execute_gauss_code(
            environment_check_result=found_env,
            code="print 1;",
            working_directory=tmp_dir,
            package_inspection_result={"missing_packages": ["tsmt"], "unknown_packages": []},
            runner=fake_runner_factory(exit_code=0),
        )
        check(
            "missing package blocks execution",
            result["execution_status"] == "blocked" and result["executed"] is False,
        )
        check("missing package error mentions package", any("tsmt" in e for e in result["errors"]))

        result = execute_gauss_code(
            environment_check_result=found_env,
            code="print 1;",
            working_directory=tmp_dir,
            package_inspection_result={"missing_packages": [], "unknown_packages": ["foo"]},
            runner=fake_runner_factory(exit_code=0),
        )
        check(
            "unknown package warns but does not block",
            result["execution_status"] == "completed" and any("unknown" in w.lower() for w in result["warnings"]),
        )

        schema_path = default_schema_path()
        if schema_path.is_file():
            representative = {
                "blocked": execute_gauss_code(
                    environment_check_result={"detection_status": "not_found"},
                    code="print 1;",
                    working_directory=tmp_dir,
                ),
                "skipped": execute_gauss_code(environment_check_result=found_env, working_directory=tmp_dir),
                "completed": execute_gauss_code(
                    environment_check_result=found_env,
                    code="print 1;",
                    working_directory=tmp_dir,
                    runner=fake_runner_factory(exit_code=0, stdout="ok"),
                ),
                "failed": execute_gauss_code(
                    environment_check_result=found_env,
                    code="print 1;",
                    working_directory=tmp_dir,
                    runner=fake_runner_factory(exit_code=1, stderr="err"),
                ),
                "timed_out": execute_gauss_code(
                    environment_check_result=found_env,
                    code="print 1;",
                    working_directory=tmp_dir,
                    timeout_seconds=5,
                    runner=fake_runner_factory(timed_out=True),
                ),
            }
            for label, res in representative.items():
                errors = validate_against_schema(res, schema_path)
                missing_dependency = len(errors) == 1 and errors[0].startswith("jsonschema is not installed")
                if errors and not missing_dependency:
                    failures.append(f"schema validation failed for '{label}' result: {errors}")

    if failures:
        print(f"SELF-TEST FAILED ({len(failures)} issue(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("SELF-TEST PASSED: all checks succeeded.")
    return 0


def _load_json_file(path_str: str) -> dict[str, Any]:
    with open(path_str, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Execute explicitly supplied GAUSS code or an explicit GAUSS script file in a controlled, "
            "safety-constrained way. Requires an explicit safe working directory and timeout; never "
            "installs packages, activates licenses, mutates global configuration, or accesses the "
            "network. See tools/gauss_code_execution.md for the full contract."
        )
    )
    parser.add_argument(
        "--environment-result",
        default=None,
        help="Path to a JSON file containing a gauss_environment_check result to use as context.",
    )
    parser.add_argument(
        "--package-inspection-result",
        default=None,
        help="Path to a JSON file containing a gauss_package_inspection result to use as advisory context.",
    )
    parser.add_argument(
        "--executable-path", default=None, help="Directly select the GAUSS executable, bypassing --environment-result."
    )
    parser.add_argument("--gauss-version", default=None, help="Directly select the GAUSS version context.")
    parser.add_argument("--code", default=None, help="Explicit inline GAUSS code. Mutually exclusive with --script-path.")
    parser.add_argument(
        "--script-path", default=None, help="Explicit GAUSS script file to execute. Mutually exclusive with --code."
    )
    parser.add_argument(
        "--working-directory", default=None, help="Required. The safe, explicit working directory for execution."
    )
    parser.add_argument(
        "--input-file",
        action="append",
        default=[],
        dest="input_file",
        help="An explicit input file inside working-directory. May be repeated.",
    )
    parser.add_argument(
        "--output-directory",
        default=None,
        help="Where generated output may be discovered; must resolve inside working-directory.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=None)
    parser.add_argument(
        "--allow-file-write",
        action="store_true",
        help="Accepted for input-contract completeness; writes are always confined to working-directory.",
    )
    parser.add_argument(
        "--allow-output-files",
        action="store_true",
        default=True,
        help="Permit listing generated output files after execution (default: on).",
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Requests network access. Not supported; adds a warning and network access remains unavailable.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Do not fall back to automatic environment detection if no context is supplied.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full structured JSON result. Default output is a short human-readable summary.",
    )
    parser.add_argument(
        "--validate-schema",
        action="store_true",
        help="Validate the result against schemas/gauss_code_execution.schema.json before printing.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the built-in test suite (fake runner; no real GAUSS installation required) and exit.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.self_test:
        return _run_self_tests()

    environment_check_result = None
    if args.environment_result:
        try:
            environment_check_result = _load_json_file(args.environment_result)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Could not read --environment-result file '{args.environment_result}': {exc}", file=sys.stderr)
            return 2

    package_inspection_result = None
    if args.package_inspection_result:
        try:
            package_inspection_result = _load_json_file(args.package_inspection_result)
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"Could not read --package-inspection-result file '{args.package_inspection_result}': {exc}",
                file=sys.stderr,
            )
            return 2

    result = execute_gauss_code(
        environment_check_result=environment_check_result,
        package_inspection_result=package_inspection_result,
        executable_path=args.executable_path,
        gauss_version=args.gauss_version,
        code=args.code,
        script_path=args.script_path,
        working_directory=args.working_directory,
        input_files=args.input_file or None,
        output_directory=args.output_directory,
        timeout_seconds=args.timeout_seconds,
        allow_file_write=args.allow_file_write,
        allow_output_files=args.allow_output_files,
        allow_network=args.allow_network,
        strict=args.strict,
    )

    if args.validate_schema:
        schema_errors = validate_against_schema(result, default_schema_path())
        missing_dependency = len(schema_errors) == 1 and schema_errors[0].startswith("jsonschema is not installed")
        if schema_errors and missing_dependency:
            result["warnings"].append(schema_errors[0])
        elif schema_errors:
            if args.json:
                print(json.dumps({"result": result, "schema_errors": schema_errors}, indent=2))
            else:
                print("Schema validation FAILED:")
                for msg in schema_errors:
                    print(f"  - {msg}")
            return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
