"""Diagnostic bundle export for the guided repair workflow (v0.68.0),
exposed as `gauss-ai repair <file.gss> --export-session <path>`.

Not a durable session mechanism -- durable sessions remain explicitly out
of scope for this repository. The bundle is built and written entirely
within the same, single guided-repair process that already holds the real
session state; there is no later, separate command that reads it back, and
no persistence layer of any kind. This module is read-only with respect to
the repair pipeline: it only ever inspects already-existing adapter state
after a guided sequence completes, and never triggers, decides, or changes
anything about how a repair proceeds.

The bundle contains exactly the same fields `gauss-ai config show`/
`gauss-ai version` already disclose (no secrets are stored anywhere in this
repository's configuration model to begin with -- see
`gauss_ai_config.GaussAiConfig`), plus the session's own real evidence: the
runner backend actually used, the configured GAUSS executable and its
version (parsed from its own path string, never by launching it), the
active workspace's identity, and the complete, real, printed transcript of
every step the guided workflow took.
"""

from __future__ import annotations

import json
import platform as platform_module
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Any

import gauss_ai_config as config_mod
import gauss_environment_check as environment_check_mod


def _package_version() -> str:
    try:
        return _pkg_version("gauss-ai")
    except PackageNotFoundError:
        return "unknown (not installed via pip)"


def build_diagnostic_bundle(
    *,
    transcript: list[str],
    config: "config_mod.GaussAiConfig",
    runner_backend: str,
    gauss_executable: str | None,
    workspace_id: str | None,
    workspace_root: str | None,
) -> dict[str, Any]:
    """Pure composition of already-known values -- no I/O beyond what the
    caller already performed, no GAUSS invocation, no network access."""
    gauss_version = environment_check_mod.parse_gauss_version(gauss_executable) if gauss_executable else None
    return {
        "gauss_ai_version": _package_version(),
        "python_version": platform_module.python_version(),
        "platform": platform_module.platform(),
        "configuration": {
            "gauss_executable": config.gauss_executable,
            "default_runner": config.default_runner,
            "workspace_parent": config.workspace_parent,
            "default_timeout_seconds": config.default_timeout_seconds,
            "verbose": config.verbose,
        },
        "runner_backend": runner_backend,
        "gauss_executable_used": gauss_executable,
        "gauss_version_from_path": gauss_version,
        "workspace_id": workspace_id,
        "workspace_root": workspace_root,
        "session_transcript": transcript,
    }


def write_diagnostic_bundle(bundle: dict[str, Any], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p
