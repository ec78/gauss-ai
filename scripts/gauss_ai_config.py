"""Local configuration model for the productized `gauss-ai` CLI (v0.67.0;
conversational-chat settings added in v0.70.0).

Stores exactly seven settings and one display preference -- no secrets, no
license credentials, no passwords, no API keys, and no arbitrary key/value
execution mechanism of any kind:

    gauss_executable        -- path to a terminal (tgauss/tgauss.exe) executable
    default_runner           -- "fake" or "gauss"
    workspace_parent         -- approved parent directory for alpha workspaces
    default_timeout_seconds  -- default execution timeout
    chat_provider            -- "fake" or "anthropic" (v0.70.0)
    chat_model                -- model identifier string, provider-specific (v0.70.0)
    docs_root                -- local root of official GAUSS documentation, for
                                 conversational grounding only (v0.70.0)
    verbose                  -- whether to show raw digests/IDs by default

An API key/credential is never a field on this model and is never written to
the config file -- see `gauss_chat_provider.py`'s own module docstring for
where and how a real provider's credential is read (fresh from an
environment variable, at call time only, never persisted anywhere this
module touches).

File location: `~/.gauss-ai/config.json`, computed via `Path.home()` --
never a hard-coded, user-specific path. Every location this module touches
is either that fixed, home-relative file or a caller-supplied override
(for tests).

Precedence (most to least authoritative), applied identically for every
setting: explicit CLI argument -> environment variable -> local config file
-> safe default. This mirrors the precedence
`gauss_code_assistant_cli._resolve_real_executable(...)` already established
for `--gauss-executable`/`GAUSS_EXECUTABLE` (CLI arg, then env var, then
error) -- this module adds one more, lower-priority rung (the config file)
below those two, and extends the same shape to the three settings that
previously had no env-var or config-file layer at all.

This module never reads or writes any file other than the config file
itself, never executes anything, and never mutates configuration except
through `save_config(...)`, which is only ever called after explicit user
confirmation (see `gauss_ai_init.py`) or an explicit `gauss-ai config set`
invocation.
"""

from __future__ import annotations

import dataclasses
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gauss_code_execution as code_execution_mod

CONFIG_DIR_NAME = ".gauss-ai"
CONFIG_FILE_NAME = "config.json"

VALID_RUNNERS = ("fake", "gauss")
VALID_CHAT_PROVIDERS = ("fake", "anthropic")

ENV_GAUSS_EXECUTABLE = "GAUSS_EXECUTABLE"
ENV_DEFAULT_RUNNER = "GAUSS_AI_DEFAULT_RUNNER"
ENV_WORKSPACE_PARENT = "GAUSS_AI_WORKSPACE_PARENT"
ENV_TIMEOUT_SECONDS = "GAUSS_AI_TIMEOUT_SECONDS"
ENV_CHAT_PROVIDER = "GAUSS_AI_CHAT_PROVIDER"
ENV_CHAT_MODEL = "GAUSS_AI_CHAT_MODEL"
ENV_DOCS_ROOT = "GAUSS_AI_DOCS_ROOT"


def config_dir() -> Path:
    """Always `Path.home() / ".gauss-ai"` -- never hard-coded."""
    return Path.home() / CONFIG_DIR_NAME


def config_path() -> Path:
    return config_dir() / CONFIG_FILE_NAME


@dataclass(frozen=True)
class GaussAiConfig:
    """Every field except `verbose` defaults to `None` -- including
    `default_runner`/`default_timeout_seconds`, which otherwise have a
    usable non-None fallback ("fake"/30.0) applied only by the resolvers
    below, never baked into this dataclass. Symmetry matters here: if
    `default_runner` defaulted to `"fake"` directly on this type, a freshly
    constructed config (no file on disk at all) would be indistinguishable
    from one that explicitly wrote `default_runner: "fake"` to the file,
    and `resolve_default_runner(...)` would misreport its source as
    `config_file` instead of `default`."""

    gauss_executable: str | None = None
    default_runner: str | None = None
    workspace_parent: str | None = None
    default_timeout_seconds: float | None = None
    chat_provider: str | None = None
    chat_model: str | None = None
    docs_root: str | None = None
    verbose: bool = False


def _load_raw(path: str | Path | None = None) -> dict[str, Any]:
    """Returns exactly the keys present in the config file's own JSON --
    empty if the file is missing, unreadable, or malformed. Distinct from
    `load_config(...)`'s fully-defaulted `GaussAiConfig`: `default_runner`
    and `default_timeout_seconds` both have non-None dataclass defaults, so
    the resolvers below need to know whether a value was actually WRITTEN to
    the file, not merely whether the loaded dataclass happens to hold a
    truthy value -- otherwise a freshly-defaulted config (no file at all)
    would be indistinguishable from one that explicitly set
    `default_runner: "fake"`, misreporting its source as `config_file`."""
    p = Path(path) if path is not None else config_path()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def load_config(path: str | Path | None = None) -> GaussAiConfig:
    """Returns the safe-default config if the file is missing, unreadable,
    or malformed -- never raises. A corrupt config file is a `doctor` FAIL
    finding, not a crash."""
    data = _load_raw(path)
    raw_timeout = data.get("default_timeout_seconds")
    return GaussAiConfig(
        gauss_executable=data.get("gauss_executable") or None,
        default_runner=data.get("default_runner") or None,
        workspace_parent=data.get("workspace_parent") or None,
        default_timeout_seconds=(float(raw_timeout) if raw_timeout is not None else None),
        chat_provider=data.get("chat_provider") or None,
        chat_model=data.get("chat_model") or None,
        docs_root=data.get("docs_root") or None,
        verbose=bool(data.get("verbose", False)),
    )


def is_config_file_valid(path: str | Path | None = None) -> tuple[bool, str]:
    """Read-only validity check distinct from `load_config(...)`'s own
    fail-safe defaulting -- used by `doctor` to report a corrupt file as a
    FAIL rather than silently treating it as "no config"."""
    p = Path(path) if path is not None else config_path()
    if not p.is_file():
        return True, "no config file yet; safe defaults are in effect"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"config file exists but could not be parsed as JSON: {exc}"
    if not isinstance(data, dict):
        return False, "config file exists but its top-level JSON value is not an object"
    return True, f"config file is valid JSON: {p}"


def save_config(config: GaussAiConfig, path: str | Path | None = None) -> Path:
    """Writes the config file, creating `~/.gauss-ai/` if needed. Only ever
    called after explicit user confirmation (`gauss-ai init`) or an explicit
    `gauss-ai config set` command -- never automatically."""
    p = Path(path) if path is not None else config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = dataclasses.asdict(config)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p


def validate_gauss_executable(path_str: str) -> tuple[bool, str]:
    """Read-only validation, never executes the candidate. Rejects any
    basename other than the terminal `tgauss`/`tgauss.exe` -- reusing the
    exact same canonical set `gauss_code_execution.py`'s own real-runner
    command builder already uses, rather than redefining it."""
    p = Path(path_str).expanduser()
    if not p.exists():
        return False, f"path does not exist: {p}"
    if not p.is_file():
        return False, f"path is not a file: {p}"
    basename = p.name.lower()
    if basename not in code_execution_mod._TERMINAL_EXECUTABLE_BASENAMES:  # noqa: SLF001
        allowed = ", ".join(sorted(code_execution_mod._TERMINAL_EXECUTABLE_BASENAMES))  # noqa: SLF001
        return False, (
            f"{p.name!r} is not a supported terminal GAUSS executable ({allowed}); "
            "GUI executables such as gauss.exe cannot run in non-interactive batch mode."
        )
    return True, f"valid terminal GAUSS executable: {p}"


@dataclass(frozen=True)
class ResolvedValue:
    value: Any
    source: str  # "cli_argument" | "environment_variable" | "config_file" | "default"


def resolve_gauss_executable(
    *, cli_value: str | None = None, config: GaussAiConfig | None = None, env: dict[str, str] | None = None
) -> ResolvedValue:
    env = env if env is not None else os.environ
    if cli_value:
        return ResolvedValue(str(cli_value), "cli_argument")
    env_val = env.get(ENV_GAUSS_EXECUTABLE, "").strip()
    if env_val:
        return ResolvedValue(env_val, "environment_variable")
    config = config if config is not None else load_config()
    if config.gauss_executable:
        return ResolvedValue(config.gauss_executable, "config_file")
    return ResolvedValue(None, "default")


def resolve_default_runner(
    *, cli_value: str | None = None, config: GaussAiConfig | None = None, env: dict[str, str] | None = None
) -> ResolvedValue:
    env = env if env is not None else os.environ
    if cli_value:
        return ResolvedValue(cli_value, "cli_argument")
    env_val = env.get(ENV_DEFAULT_RUNNER, "").strip()
    if env_val:
        return ResolvedValue(env_val, "environment_variable")
    config = config if config is not None else load_config()
    if config.default_runner:
        return ResolvedValue(config.default_runner, "config_file")
    return ResolvedValue("fake", "default")


def resolve_workspace_parent(
    *, cli_value: str | None = None, config: GaussAiConfig | None = None, env: dict[str, str] | None = None
) -> ResolvedValue:
    env = env if env is not None else os.environ
    if cli_value:
        return ResolvedValue(cli_value, "cli_argument")
    env_val = env.get(ENV_WORKSPACE_PARENT, "").strip()
    if env_val:
        return ResolvedValue(env_val, "environment_variable")
    config = config if config is not None else load_config()
    if config.workspace_parent:
        return ResolvedValue(config.workspace_parent, "config_file")
    return ResolvedValue(None, "default")


def resolve_default_timeout_seconds(
    *, cli_value: float | None = None, config: GaussAiConfig | None = None, env: dict[str, str] | None = None
) -> ResolvedValue:
    env = env if env is not None else os.environ
    if cli_value is not None:
        return ResolvedValue(float(cli_value), "cli_argument")
    env_val = env.get(ENV_TIMEOUT_SECONDS, "").strip()
    if env_val:
        try:
            return ResolvedValue(float(env_val), "environment_variable")
        except ValueError:
            pass
    config = config if config is not None else load_config()
    if config.default_timeout_seconds is not None:
        return ResolvedValue(config.default_timeout_seconds, "config_file")
    return ResolvedValue(30.0, "default")


def resolve_chat_provider(
    *, cli_value: str | None = None, config: GaussAiConfig | None = None, env: dict[str, str] | None = None
) -> ResolvedValue:
    """Mirrors `resolve_default_runner(...)` exactly: `"fake"` is the safe
    default, requiring no network access, no credential, and no external
    dependency -- identical in spirit to `default_runner` defaulting to
    `"fake"` rather than `"gauss"`."""
    env = env if env is not None else os.environ
    if cli_value:
        return ResolvedValue(cli_value, "cli_argument")
    env_val = env.get(ENV_CHAT_PROVIDER, "").strip()
    if env_val:
        return ResolvedValue(env_val, "environment_variable")
    config = config if config is not None else load_config()
    if config.chat_provider:
        return ResolvedValue(config.chat_provider, "config_file")
    return ResolvedValue("fake", "default")


def resolve_chat_model(
    *, cli_value: str | None = None, config: GaussAiConfig | None = None, env: dict[str, str] | None = None
) -> ResolvedValue:
    """No default model is asserted -- an unset value (`None`) is a valid,
    honest outcome; `gauss_chat_provider.AnthropicMessagesProvider` applies
    its own explicit, documented default only if this resolves to `None`."""
    env = env if env is not None else os.environ
    if cli_value:
        return ResolvedValue(cli_value, "cli_argument")
    env_val = env.get(ENV_CHAT_MODEL, "").strip()
    if env_val:
        return ResolvedValue(env_val, "environment_variable")
    config = config if config is not None else load_config()
    if config.chat_model:
        return ResolvedValue(config.chat_model, "config_file")
    return ResolvedValue(None, "default")


def resolve_docs_root(
    *, cli_value: str | None = None, config: GaussAiConfig | None = None, env: dict[str, str] | None = None
) -> ResolvedValue:
    """No default path is asserted -- this repository bundles no GAUSS
    documentation; an unset value means conversational grounding against
    local official documentation is unavailable, honestly, not silently
    assumed."""
    env = env if env is not None else os.environ
    if cli_value:
        return ResolvedValue(cli_value, "cli_argument")
    env_val = env.get(ENV_DOCS_ROOT, "").strip()
    if env_val:
        return ResolvedValue(env_val, "environment_variable")
    config = config if config is not None else load_config()
    if config.docs_root:
        return ResolvedValue(config.docs_root, "config_file")
    return ResolvedValue(None, "default")
