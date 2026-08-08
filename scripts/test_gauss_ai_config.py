"""Tests for the productized `gauss-ai` local configuration model (v0.67.0).

Run with:

    python scripts/test_gauss_ai_config.py

No test touches the real `~/.gauss-ai/config.json` -- every test uses a
temp-directory-backed path override. No test installs a package, executes
GAUSS, or accesses the network.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_ai_config as config_mod  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


# ---------------------------------------------------------------------------
# load/save roundtrip
# ---------------------------------------------------------------------------


def test_01_load_config_missing_file_returns_safe_defaults() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        config = config_mod.load_config(path)
        check("gauss_executable is None", config.gauss_executable is None)
        check("default_runner is None (not baked-in 'fake')", config.default_runner is None)
        check("workspace_parent is None", config.workspace_parent is None)
        check("default_timeout_seconds is None", config.default_timeout_seconds is None)
        check("verbose is False", config.verbose is False)


def test_02_save_then_load_roundtrips_exactly() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        original = config_mod.GaussAiConfig(
            gauss_executable="/opt/gauss26/tgauss", default_runner="gauss",
            workspace_parent="/home/user/workspaces", default_timeout_seconds=45.0, verbose=True,
        )
        saved_path = config_mod.save_config(original, path)
        check("save_config returns the same path", saved_path == path)
        loaded = config_mod.load_config(path)
        check("gauss_executable roundtrips", loaded.gauss_executable == original.gauss_executable)
        check("default_runner roundtrips", loaded.default_runner == original.default_runner)
        check("workspace_parent roundtrips", loaded.workspace_parent == original.workspace_parent)
        check("default_timeout_seconds roundtrips", loaded.default_timeout_seconds == original.default_timeout_seconds)
        check("verbose roundtrips", loaded.verbose == original.verbose)


def test_03_save_config_creates_parent_directory() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "nested" / "dir" / "config.json"
        config_mod.save_config(config_mod.GaussAiConfig(), path)
        check("nested parent directory was created", path.is_file())


def test_04_load_config_corrupt_json_returns_safe_defaults_not_a_crash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        path.write_text("{ this is not valid json", encoding="utf-8")
        config = config_mod.load_config(path)
        check("corrupt file does not raise, returns safe defaults", config.gauss_executable is None)


def test_05_load_config_non_object_json_returns_safe_defaults() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        config = config_mod.load_config(path)
        check("a JSON array (not object) is treated as no config", config.default_runner is None)


def test_06_config_dir_is_home_relative_never_hardcoded() -> None:
    check("config_dir is under Path.home()", str(config_mod.config_dir()).startswith(str(Path.home())))
    check("config file name is config.json", config_mod.config_path().name == "config.json")


# ---------------------------------------------------------------------------
# is_config_file_valid
# ---------------------------------------------------------------------------


def test_07_is_config_file_valid_missing_file_is_valid() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ok, message = config_mod.is_config_file_valid(Path(tmp) / "does-not-exist.json")
        check("missing file is reported valid (defaults apply)", ok is True)
        check("message mentions safe defaults", "default" in message.lower())


def test_08_is_config_file_valid_corrupt_file_is_invalid() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        path.write_text("not json at all {{{", encoding="utf-8")
        ok, message = config_mod.is_config_file_valid(path)
        check("corrupt file is reported invalid", ok is False)
        check("message explains why", "could not be parsed" in message)


def test_09_is_config_file_valid_well_formed_file_is_valid() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        config_mod.save_config(config_mod.GaussAiConfig(default_runner="fake"), path)
        ok, _message = config_mod.is_config_file_valid(path)
        check("well-formed file is valid", ok is True)


# ---------------------------------------------------------------------------
# validate_gauss_executable
# ---------------------------------------------------------------------------


def test_10_validate_gauss_executable_missing_path_is_invalid() -> None:
    ok, message = config_mod.validate_gauss_executable("/definitely/does/not/exist/tgauss.exe")
    check("missing path is invalid", ok is False)
    check("message says it does not exist", "does not exist" in message)


def test_11_validate_gauss_executable_directory_is_invalid() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ok, message = config_mod.validate_gauss_executable(tmp)
        check("a directory is invalid", ok is False)
        check("message says it is not a file", "not a file" in message)


def test_12_validate_gauss_executable_gui_executable_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "gauss.exe"
        p.write_bytes(b"")
        ok, message = config_mod.validate_gauss_executable(str(p))
        check("GUI gauss.exe is rejected", ok is False)
        check("message explains GUI executables cannot batch-run", "GUI" in message)


def test_13_validate_gauss_executable_terminal_executable_is_accepted() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "tgauss.exe"
        p.write_bytes(b"")
        ok, message = config_mod.validate_gauss_executable(str(p))
        check("terminal tgauss.exe is accepted", ok is True)
        check("message confirms validity", "valid terminal" in message)


def test_14_validate_gauss_executable_case_insensitive_basename() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "TGAUSS.EXE"
        p.write_bytes(b"")
        ok, _message = config_mod.validate_gauss_executable(str(p))
        check("basename check is case-insensitive", ok is True)


# ---------------------------------------------------------------------------
# precedence: CLI arg > env var > config file > default
# ---------------------------------------------------------------------------


def test_15_resolve_gauss_executable_cli_arg_wins_over_everything() -> None:
    config = config_mod.GaussAiConfig(gauss_executable="/config/tgauss")
    resolved = config_mod.resolve_gauss_executable(
        cli_value="/cli/tgauss", config=config, env={"GAUSS_EXECUTABLE": "/env/tgauss"}
    )
    check("CLI arg wins", resolved.value == "/cli/tgauss")
    check("source is cli_argument", resolved.source == "cli_argument")


def test_16_resolve_gauss_executable_env_var_wins_over_config_file() -> None:
    config = config_mod.GaussAiConfig(gauss_executable="/config/tgauss")
    resolved = config_mod.resolve_gauss_executable(cli_value=None, config=config, env={"GAUSS_EXECUTABLE": "/env/tgauss"})
    check("env var wins over config file", resolved.value == "/env/tgauss")
    check("source is environment_variable", resolved.source == "environment_variable")


def test_17_resolve_gauss_executable_config_file_wins_over_default() -> None:
    config = config_mod.GaussAiConfig(gauss_executable="/config/tgauss")
    resolved = config_mod.resolve_gauss_executable(cli_value=None, config=config, env={})
    check("config file wins over default", resolved.value == "/config/tgauss")
    check("source is config_file", resolved.source == "config_file")


def test_18_resolve_gauss_executable_default_when_nothing_set() -> None:
    resolved = config_mod.resolve_gauss_executable(cli_value=None, config=config_mod.GaussAiConfig(), env={})
    check("value is None by default", resolved.value is None)
    check("source is default", resolved.source == "default")


def test_19_resolve_default_runner_full_precedence_chain() -> None:
    config = config_mod.GaussAiConfig(default_runner="gauss")
    check(
        "cli arg wins",
        config_mod.resolve_default_runner(cli_value="fake", config=config, env={"GAUSS_AI_DEFAULT_RUNNER": "gauss"}).value
        == "fake",
    )
    check(
        "env var wins over config",
        config_mod.resolve_default_runner(cli_value=None, config=config, env={"GAUSS_AI_DEFAULT_RUNNER": "fake"}).value
        == "fake",
    )
    check(
        "config file wins over default",
        config_mod.resolve_default_runner(cli_value=None, config=config, env={}).value == "gauss",
    )
    check(
        "safe default ('fake') applies when nothing else is set",
        config_mod.resolve_default_runner(cli_value=None, config=config_mod.GaussAiConfig(), env={}).value == "fake",
    )


def test_20_resolve_default_runner_source_is_default_not_config_file_when_unset() -> None:
    """Regression test for the exact bug found during manual smoke testing:
    a freshly-defaulted config (no file on disk) must never be reported as
    'config_file' just because GaussAiConfig.default_runner happens to also
    equal the safe default value 'fake'."""
    resolved = config_mod.resolve_default_runner(cli_value=None, config=config_mod.GaussAiConfig(), env={})
    check("value is the safe default 'fake'", resolved.value == "fake")
    check("source is 'default', not 'config_file'", resolved.source == "default")


def test_21_resolve_workspace_parent_full_precedence_chain() -> None:
    config = config_mod.GaussAiConfig(workspace_parent="/config/workspaces")
    check(
        "cli arg wins",
        config_mod.resolve_workspace_parent(
            cli_value="/cli/workspaces", config=config, env={"GAUSS_AI_WORKSPACE_PARENT": "/env/workspaces"}
        ).value
        == "/cli/workspaces",
    )
    check(
        "env var wins over config",
        config_mod.resolve_workspace_parent(cli_value=None, config=config, env={"GAUSS_AI_WORKSPACE_PARENT": "/env/workspaces"}).value
        == "/env/workspaces",
    )
    check(
        "config file wins over default",
        config_mod.resolve_workspace_parent(cli_value=None, config=config, env={}).value == "/config/workspaces",
    )
    check(
        "default is None when nothing set",
        config_mod.resolve_workspace_parent(cli_value=None, config=config_mod.GaussAiConfig(), env={}).value is None,
    )


def test_22_resolve_default_timeout_seconds_full_precedence_chain() -> None:
    config = config_mod.GaussAiConfig(default_timeout_seconds=60.0)
    check(
        "cli arg wins",
        config_mod.resolve_default_timeout_seconds(cli_value=15.0, config=config, env={"GAUSS_AI_TIMEOUT_SECONDS": "45"}).value
        == 15.0,
    )
    check(
        "env var wins over config",
        config_mod.resolve_default_timeout_seconds(cli_value=None, config=config, env={"GAUSS_AI_TIMEOUT_SECONDS": "45"}).value
        == 45.0,
    )
    check(
        "config file wins over default",
        config_mod.resolve_default_timeout_seconds(cli_value=None, config=config, env={}).value == 60.0,
    )
    check(
        "safe default 30.0 applies when nothing else is set",
        config_mod.resolve_default_timeout_seconds(cli_value=None, config=config_mod.GaussAiConfig(), env={}).value == 30.0,
    )


def test_23_resolve_default_timeout_seconds_malformed_env_var_falls_through() -> None:
    resolved = config_mod.resolve_default_timeout_seconds(
        cli_value=None, config=config_mod.GaussAiConfig(), env={"GAUSS_AI_TIMEOUT_SECONDS": "not-a-number"}
    )
    check("malformed env var value falls through to default, does not raise", resolved.value == 30.0)
    check("source is default", resolved.source == "default")


def test_24_config_never_stores_secrets_or_arbitrary_keys() -> None:
    """Structural proof: GaussAiConfig has exactly five fields, none of
    which is secret-shaped, and save_config(...) serializes only those."""
    field_names = {f.name for f in __import__("dataclasses").fields(config_mod.GaussAiConfig)}
    check(
        "exactly the five documented fields exist",
        field_names == {"gauss_executable", "default_runner", "workspace_parent", "default_timeout_seconds", "verbose"},
    )
    for forbidden in ("password", "secret", "token", "license", "credential", "api_key"):
        check(f"no field name contains {forbidden!r}", not any(forbidden in name for name in field_names))


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
            _failures.append(f"{name} raised {type(exc).__name__}: {exc}")
        if len(_failures) == before:
            print(f"PASS  {name}")
        else:
            for failure in _failures[before:]:
                print(f"FAIL  {name}: {failure}")
    print(f"\n{len(tests)} test function(s) run, {len(_failures)} check failure(s).")
    if _failures:
        print("SOME CHECKS FAILED.")
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
