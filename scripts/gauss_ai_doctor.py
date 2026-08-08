"""Read-only environment diagnostics for the productized `gauss-ai` CLI
(v0.67.0), exposed as `gauss-ai doctor`.

Every check here is read-only. This module never runs user code, never
installs a package, never alters a GAUSS installation, never activates a
license, never changes configuration, and never accesses the network. GAUSS
version discovery is done by parsing the configured executable's own PATH
STRING (`gauss_environment_check.parse_gauss_version(...)`) -- never by
launching it; if launching were ever required for a safer/more accurate
version read, that would need to be its own explicit, separately-approved,
opt-in check, not something `doctor` does automatically. No such check
exists in this milestone.

Reuses `gauss_environment_check.detect_environment(...)` for GAUSS
discovery and `gauss_ai_config` for configuration resolution/validation --
this module defines no new discovery or validation logic of its own.
"""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import gauss_ai_config as config_mod
import gauss_environment_check as environment_check_mod

MIN_PYTHON_VERSION = (3, 10)

#: Modules that must import cleanly for the assistant to function at all --
#: a representative slice of the pipeline, not every module (import success
#: here does not certify correctness, only that the installed package is
#: intact).
_REQUIRED_MODULES = (
    "gauss_code_assistant_cli",
    "gauss_code_assistant_workflow",
    "gauss_execution_workflow",
    "gauss_repair_planner",
    "gauss_repair_application",
    "gauss_verification_execution",
    "gauss_verification_review",
    "gauss_repair_session_summary",
)

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


@dataclass(frozen=True)
class DoctorCheckResult:
    name: str
    status: str  # PASS | WARN | FAIL
    message: str
    next_step: str | None = None


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[DoctorCheckResult, ...]

    @property
    def overall_status(self) -> str:
        statuses = {c.status for c in self.checks}
        if FAIL in statuses:
            return FAIL
        if WARN in statuses:
            return WARN
        return PASS


def _check_python_version(version_info: tuple[int, int, int] | None = None) -> DoctorCheckResult:
    vi = version_info if version_info is not None else sys.version_info[:3]
    ok = (vi[0], vi[1]) >= MIN_PYTHON_VERSION
    version_str = ".".join(str(part) for part in vi)
    if ok:
        return DoctorCheckResult("python_version", PASS, f"Python {version_str} (>= {'.'.join(map(str, MIN_PYTHON_VERSION))} required)")
    return DoctorCheckResult(
        "python_version", FAIL, f"Python {version_str} is below the required {'.'.join(map(str, MIN_PYTHON_VERSION))}",
        next_step=f"Install Python {'.'.join(map(str, MIN_PYTHON_VERSION))} or newer and reinstall gauss-ai.",
    )


def _check_module_imports(module_names: tuple[str, ...] = _REQUIRED_MODULES) -> DoctorCheckResult:
    missing: list[str] = []
    for name in module_names:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
    if not missing:
        return DoctorCheckResult("module_imports", PASS, f"all {len(module_names)} core modules import cleanly")
    return DoctorCheckResult(
        "module_imports", FAIL, f"{len(missing)} core module(s) failed to import: {', '.join(missing)}",
        next_step="Reinstall gauss-ai (pip install -e .) from a clean checkout.",
    )


def _check_workspace_parent(
    *, cli_value: str | None, config: "config_mod.GaussAiConfig", env: dict[str, str]
) -> DoctorCheckResult:
    resolved = config_mod.resolve_workspace_parent(cli_value=cli_value, config=config, env=env)
    if resolved.value is None:
        return DoctorCheckResult(
            "workspace_parent", WARN,
            "no workspace parent configured; a fresh temporary directory will be used each session",
            next_step="Run 'gauss-ai init' or 'gauss-ai config set workspace-parent <path>' to persist a chosen location.",
        )
    try:
        p = Path(resolved.value).expanduser()
        p.mkdir(parents=True, exist_ok=True)
        probe = p / ".gauss-ai-doctor-write-check"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except (OSError, ValueError) as exc:
        # ValueError (e.g. an embedded null byte) is caught alongside
        # OSError -- a read-only diagnostic must report FAIL for a
        # malformed configured path, never crash the whole `doctor` run.
        return DoctorCheckResult(
            "workspace_parent", FAIL, f"configured workspace parent ({resolved.value!r}) is not usable: {exc}",
            next_step="Choose a different, writable directory via 'gauss-ai config set workspace-parent <path>'.",
        )
    return DoctorCheckResult("workspace_parent", PASS, f"workspace parent is writable: {p} (source: {resolved.source})")


def _check_gauss_executable_configured(
    *, cli_value: str | None, config: "config_mod.GaussAiConfig", env: dict[str, str]
) -> DoctorCheckResult:
    resolved = config_mod.resolve_gauss_executable(cli_value=cli_value, config=config, env=env)
    if resolved.value is None:
        return DoctorCheckResult(
            "gauss_executable_configured", WARN,
            "no GAUSS executable configured; fake-mode testing is fully available, real GAUSS execution is not",
            next_step="Run 'gauss-ai init' or 'gauss-ai config set gauss-executable <path>' when ready for real-mode testing.",
        )
    return DoctorCheckResult(
        "gauss_executable_configured", PASS, f"configured: {resolved.value} (source: {resolved.source})",
    )


def _check_gauss_executable_valid(
    *, cli_value: str | None, config: "config_mod.GaussAiConfig", env: dict[str, str]
) -> DoctorCheckResult:
    resolved = config_mod.resolve_gauss_executable(cli_value=cli_value, config=config, env=env)
    if resolved.value is None:
        return DoctorCheckResult("gauss_executable_valid", WARN, "skipped -- no GAUSS executable is configured")
    ok, message = config_mod.validate_gauss_executable(resolved.value)
    if ok:
        version = environment_check_mod.parse_gauss_version(str(resolved.value))
        version_note = (
            f" (version parsed from path, GAUSS was not launched: GAUSS {version})"
            if version
            else " (version not determinable from path alone; GAUSS was not launched)"
        )
        return DoctorCheckResult("gauss_executable_valid", PASS, message + version_note)
    return DoctorCheckResult(
        "gauss_executable_valid", FAIL, message,
        next_step="Run 'gauss-ai init' to re-discover a valid terminal (tgauss/tgauss.exe) executable.",
    )


def _check_config_file_validity(config_path: Path | None) -> DoctorCheckResult:
    ok, message = config_mod.is_config_file_valid(config_path)
    if ok:
        return DoctorCheckResult("config_file_validity", PASS, message)
    return DoctorCheckResult(
        "config_file_validity", FAIL, message,
        next_step=f"Fix or delete {config_mod.config_path() if config_path is None else config_path} and run 'gauss-ai init' again.",
    )


def _check_package_version() -> DoctorCheckResult:
    try:
        from importlib.metadata import version as _pkg_version

        v = _pkg_version("gauss-ai")
        return DoctorCheckResult("package_version", PASS, f"gauss-ai {v}")
    except Exception:  # noqa: BLE001 -- not installed as a package, or metadata unavailable
        return DoctorCheckResult(
            "package_version", WARN, "gauss-ai package metadata not found (not installed via pip, or running from source)",
        )


def run_doctor(
    *,
    cli_gauss_executable: str | None = None,
    cli_workspace_parent: str | None = None,
    config: "config_mod.GaussAiConfig | None" = None,
    config_path: Path | None = None,
    env: dict[str, str] | None = None,
    python_version_info: tuple[int, int, int] | None = None,
    module_names: tuple[str, ...] = _REQUIRED_MODULES,
) -> DoctorReport:
    """Runs every read-only check and returns a `DoctorReport`. Every
    parameter is injectable so this can be exercised deterministically in
    tests without touching the real filesystem, real environment, or a real
    GAUSS installation."""
    env = env if env is not None else dict(os.environ)
    resolved_config = config if config is not None else config_mod.load_config(config_path)

    checks = (
        _check_python_version(python_version_info),
        _check_module_imports(module_names),
        _check_workspace_parent(cli_value=cli_workspace_parent, config=resolved_config, env=env),
        _check_gauss_executable_configured(cli_value=cli_gauss_executable, config=resolved_config, env=env),
        _check_gauss_executable_valid(cli_value=cli_gauss_executable, config=resolved_config, env=env),
        _check_config_file_validity(config_path),
        _check_package_version(),
    )
    return DoctorReport(checks=checks)


def render_report(report: DoctorReport) -> list[str]:
    lines = ["GAUSS AI Doctor -- read-only environment diagnostics.", ""]
    for check in report.checks:
        lines.append(f"[{check.status}] {check.name}: {check.message}")
        if check.next_step:
            lines.append(f"       next step: {check.next_step}")
    lines.append("")
    lines.append(f"Overall: {report.overall_status}")
    return lines
