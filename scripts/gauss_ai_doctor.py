"""Read-only environment diagnostics for the productized `gauss-ai` CLI
(v0.67.0), exposed as `gauss-ai doctor`. Ollama diagnostics added in
`v0.71.0`.

Every check here is read-only. This module never runs user code, never
installs a package, never alters a GAUSS installation, never activates a
license, and never changes configuration. GAUSS version discovery is done
by parsing the configured executable's own PATH STRING
(`gauss_environment_check.parse_gauss_version(...)`) -- never by launching
it; if launching were ever required for a safer/more accurate version read,
that would need to be its own explicit, separately-approved, opt-in check,
not something `doctor` does automatically. No such check exists in this
milestone.

`v0.71.0` narrow exception to "never accesses the network": when, and only
when, `chat_provider` resolves to `"ollama"`, this module makes one
read-only, local-loopback `GET /api/tags` probe (via `gauss_chat_provider.
check_ollama_service(...)`) to report whether the local Ollama service is
reachable and which models it has available -- never a POST, never
`/api/chat`, never `/api/pull`, and never any request to an external host.
This is a local health check, not "accessing the network" in the sense
every other check in this module still avoids; it is bounded by an explicit
timeout and is skipped entirely for every other provider. If Ollama is not
the selected provider, its absence is never reported as a failure of an
otherwise-valid installation.

Reuses `gauss_environment_check.detect_environment(...)` for GAUSS
discovery, `gauss_ai_config` for configuration resolution/validation, and
`gauss_chat_provider.check_ollama_service(...)`/`ollama_model_matches(...)`
for Ollama diagnostics -- this module defines no new discovery, validation,
or Ollama-request logic of its own.
"""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import gauss_ai_config as config_mod
import gauss_chat_provider as provider_mod
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


def _check_chat_provider(*, config: "config_mod.GaussAiConfig", env: dict[str, str]) -> DoctorCheckResult:
    resolved = config_mod.resolve_chat_provider(config=config, env=env)
    return DoctorCheckResult("chat_provider", PASS, f"{resolved.value} (source: {resolved.source})")


def _check_ollama_service(
    *,
    config: "config_mod.GaussAiConfig",
    env: dict[str, str],
    cli_endpoint: str | None,
    service_checker: "Callable[..., provider_mod.OllamaServiceStatus] | None" = None,
) -> DoctorCheckResult:
    """Only meaningful, and only ever called, when `chat_provider` resolves
    to `"ollama"` -- see module docstring for the narrow, explicit,
    local-loopback-only network exception this represents."""
    endpoint = config_mod.resolve_ollama_endpoint(cli_value=cli_endpoint, config=config, env=env).value
    endpoint = endpoint or provider_mod.DEFAULT_OLLAMA_ENDPOINT
    checker = service_checker or provider_mod.check_ollama_service
    status = checker(endpoint=endpoint)
    if not status.reachable:
        return DoctorCheckResult(
            "ollama_service", FAIL, f"could not reach {endpoint}: {status.error_message}",
            next_step="Start Ollama (it normally runs as a background service after installation), then re-run 'gauss-ai doctor'.",
        )
    return DoctorCheckResult("ollama_service", PASS, f"reachable at {endpoint} ({len(status.models)} model(s) installed)")


def _check_ollama_model(
    *,
    config: "config_mod.GaussAiConfig",
    env: dict[str, str],
    cli_model: str | None,
    cli_endpoint: str | None,
    service_checker: "Callable[..., provider_mod.OllamaServiceStatus] | None" = None,
) -> DoctorCheckResult:
    """Depends on the service actually being reachable -- if it is not,
    this check honestly reports that it could not be evaluated, rather than
    reporting a misleading FAIL for a precondition that already failed
    elsewhere."""
    resolved_model = config_mod.resolve_chat_model(cli_value=cli_model, config=config, env=env).value
    resolved_model = resolved_model or provider_mod.DEFAULT_OLLAMA_MODEL
    endpoint = config_mod.resolve_ollama_endpoint(cli_value=cli_endpoint, config=config, env=env).value
    endpoint = endpoint or provider_mod.DEFAULT_OLLAMA_ENDPOINT
    checker = service_checker or provider_mod.check_ollama_service
    status = checker(endpoint=endpoint)
    if not status.reachable:
        return DoctorCheckResult(
            "ollama_model", WARN, f"skipped -- Ollama service at {endpoint} is not reachable (see ollama_service above)",
        )
    if provider_mod.ollama_model_matches(resolved_model, status.models):
        return DoctorCheckResult("ollama_model", PASS, f"{resolved_model} is available")
    return DoctorCheckResult(
        "ollama_model", FAIL, f"{resolved_model} is not installed locally (installed: {', '.join(status.models) or 'none'})",
        next_step=f"Run 'ollama pull {resolved_model}' (this is never done automatically by gauss-ai).",
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
    cli_chat_provider: str | None = None,
    cli_chat_model: str | None = None,
    cli_ollama_endpoint: str | None = None,
    config: "config_mod.GaussAiConfig | None" = None,
    config_path: Path | None = None,
    env: dict[str, str] | None = None,
    python_version_info: tuple[int, int, int] | None = None,
    module_names: tuple[str, ...] = _REQUIRED_MODULES,
    ollama_service_checker: "Callable[..., provider_mod.OllamaServiceStatus] | None" = None,
) -> DoctorReport:
    """Runs every read-only check and returns a `DoctorReport`. Every
    parameter is injectable so this can be exercised deterministically in
    tests without touching the real filesystem, real environment, or a real
    GAUSS/Ollama installation. `ollama_service_checker` is injected in
    tests so no test ever makes a real network call, even a local one."""
    env = env if env is not None else dict(os.environ)
    resolved_config = config if config is not None else config_mod.load_config(config_path)

    checks = [
        _check_python_version(python_version_info),
        _check_module_imports(module_names),
        _check_workspace_parent(cli_value=cli_workspace_parent, config=resolved_config, env=env),
        _check_gauss_executable_configured(cli_value=cli_gauss_executable, config=resolved_config, env=env),
        _check_gauss_executable_valid(cli_value=cli_gauss_executable, config=resolved_config, env=env),
        _check_chat_provider(config=resolved_config, env=env),
        _check_config_file_validity(config_path),
        _check_package_version(),
    ]

    resolved_provider = config_mod.resolve_chat_provider(cli_value=cli_chat_provider, config=resolved_config, env=env).value
    if resolved_provider == "ollama":
        checks.append(
            _check_ollama_service(
                config=resolved_config, env=env, cli_endpoint=cli_ollama_endpoint, service_checker=ollama_service_checker,
            )
        )
        checks.append(
            _check_ollama_model(
                config=resolved_config, env=env, cli_model=cli_chat_model, cli_endpoint=cli_ollama_endpoint,
                service_checker=ollama_service_checker,
            )
        )
    return DoctorReport(checks=tuple(checks))


def render_report(report: DoctorReport) -> list[str]:
    lines = ["GAUSS AI Doctor -- read-only environment diagnostics.", ""]
    for check in report.checks:
        lines.append(f"[{check.status}] {check.name}: {check.message}")
        if check.next_step:
            lines.append(f"       next step: {check.next_step}")
    lines.append("")
    lines.append(f"Overall: {report.overall_status}")
    return lines
