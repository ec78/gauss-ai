"""Tests for the `gauss-ai` installed entry-point dispatcher (v0.67.0).

Run with:

    python scripts/test_gauss_ai_cli.py

`gauss_ai_config.config_path` is monkeypatched to a temp-directory path for
every test in this file, so no test ever reads or writes the real
`~/.gauss-ai/config.json`. `gauss_code_assistant_cli.main` and
`gauss_ai_guided_repair.run_guided_repair` are monkeypatched where a test
only needs to prove correct DISPATCH (argument forwarding), not re-run the
full underlying pipeline already covered by their own dedicated test files.
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_ai_chat as chat_mod  # noqa: E402
import gauss_ai_cli as ai_cli  # noqa: E402
import gauss_ai_config as config_mod  # noqa: E402
import gauss_ai_guided_repair as guided_mod  # noqa: E402
import gauss_code_assistant_cli as cli_mod  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


@contextlib.contextmanager
def _isolated_config():
    with tempfile.TemporaryDirectory() as tmp:
        fake_path = Path(tmp) / "config.json"
        original = config_mod.config_path
        config_mod.config_path = lambda: fake_path
        try:
            yield fake_path
        finally:
            config_mod.config_path = original


def _capture(fn, *args, **kwargs) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exit_code = fn(*args, **kwargs)
    return exit_code, buf.getvalue()


# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------


def test_01_version_shows_required_fields() -> None:
    with _isolated_config():
        exit_code, out = _capture(ai_cli.main, ["version"])
    check("exit code 0", exit_code == 0)
    check("shows gauss-ai version", "gauss-ai version:" in out)
    check("shows Python version", "Python:" in out)
    check("shows Platform", "Platform:" in out)
    check("shows configured runner", "Configured runner:" in out)
    check("shows GAUSS executable status", "GAUSS executable:" in out)


def test_02_version_never_launches_a_configured_executable() -> None:
    with _isolated_config() as config_path:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "tgauss.exe"
            p.write_bytes(b"not a real executable, would crash if launched")
            config_mod.save_config(config_mod.GaussAiConfig(gauss_executable=str(p)), config_path)
            exit_code, out = _capture(ai_cli.main, ["version"])
    check("exit code 0 -- completed without attempting to launch the stub", exit_code == 0)
    check("output discloses the version was parsed from the path only", "not launched" in out)


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------


def test_03_doctor_exit_code_reflects_overall_status() -> None:
    with _isolated_config():
        exit_code, out = _capture(ai_cli.main, ["doctor", "--gauss-executable", "/does/not/exist"])
    check("doctor exits 1 on a FAIL", exit_code == 1)
    check("output shows FAIL", "[FAIL]" in out)


def test_04_doctor_without_gauss_configured_still_exits_cleanly() -> None:
    with _isolated_config():
        exit_code, _out = _capture(ai_cli.main, ["doctor"])
    check("doctor without any GAUSS configuration exits 0 (WARN, not FAIL)", exit_code == 0)


# ---------------------------------------------------------------------------
# config show / set
# ---------------------------------------------------------------------------


def test_05_config_show_before_any_set_reports_defaults() -> None:
    with _isolated_config():
        exit_code, out = _capture(ai_cli.main, ["config", "show"])
    check("exit code 0", exit_code == 0)
    check("shows the default runner as fake (default)", "fake (default)" in out)
    check("shows gauss-executable as not set", "(not set)" in out)


def test_06_config_set_and_show_roundtrip() -> None:
    with _isolated_config():
        exit_code, _out = _capture(ai_cli.main, ["config", "set", "default-runner", "gauss"])
        check("set exits 0", exit_code == 0)
        _exit_code, out = _capture(ai_cli.main, ["config", "show"])
        check("subsequent show reflects the set value", "default-runner: gauss" in out)


def test_07_config_set_gauss_executable_rejects_gui_executable() -> None:
    with _isolated_config():
        with tempfile.TemporaryDirectory() as tmp:
            gui = Path(tmp) / "gauss.exe"
            gui.write_bytes(b"")
            exit_code, out = _capture(ai_cli.main, ["config", "set", "gauss-executable", str(gui)])
    check("setting a GUI executable exits nonzero", exit_code == 1)
    check("error message explains why", "ERROR" in out and "GUI" in out)


def test_08_config_set_gauss_executable_accepts_terminal_executable() -> None:
    with _isolated_config():
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "tgauss.exe"
            p.write_bytes(b"")
            exit_code, out = _capture(ai_cli.main, ["config", "set", "gauss-executable", str(p)])
    check("setting a valid terminal executable exits 0", exit_code == 0)
    check("confirms it was saved", "Saved gauss-executable" in out)


def test_09_config_set_invalid_default_runner_rejected() -> None:
    with _isolated_config():
        exit_code, out = _capture(ai_cli.main, ["config", "set", "default-runner", "not-a-runner"])
    check("an invalid runner value is rejected", exit_code == 1)
    check("error message present", "ERROR" in out)


def test_10_config_set_unknown_key_rejected() -> None:
    with _isolated_config():
        exit_code, out = _capture(ai_cli.main, ["config", "set", "not-a-real-key", "value"])
    check("an unknown config key is rejected", exit_code == 2)
    check("error message lists supported keys", "Supported:" in out)


def test_11_config_never_writes_secrets_key() -> None:
    with _isolated_config():
        exit_code, _out = _capture(ai_cli.main, ["config", "set", "password", "hunter2"])
    check("a 'password' key is rejected as unknown -- no secret-shaped key is supported", exit_code == 2)


# ---------------------------------------------------------------------------
# repair -- dispatch only (the full pipeline is covered by
# test_gauss_ai_guided_repair.py)
# ---------------------------------------------------------------------------


def test_12_repair_forwards_file_and_flags_to_the_guided_module() -> None:
    captured: dict[str, object] = {}
    original = guided_mod.run_guided_repair

    def fake_run_guided_repair(file_path, **kwargs):
        captured["file_path"] = file_path
        captured["kwargs"] = kwargs
        return object()

    guided_mod.run_guided_repair = fake_run_guided_repair
    try:
        with _isolated_config():
            exit_code, _out = _capture(
                ai_cli.main, ["repair", "myfile.gss", "--runner", "fake", "--fake-result", "failure"]
            )
    finally:
        guided_mod.run_guided_repair = original
    check("exit code 0 when run_guided_repair returns a non-None adapter", exit_code == 0)
    check("file path forwarded exactly", captured.get("file_path") == "myfile.gss")
    check("runner forwarded", captured["kwargs"].get("cli_runner") == "fake")
    check("fake_result forwarded", captured["kwargs"].get("fake_result") == "failure")


def test_13_repair_returns_nonzero_when_guided_repair_returns_none() -> None:
    original = guided_mod.run_guided_repair
    guided_mod.run_guided_repair = lambda file_path, **kwargs: None
    try:
        with _isolated_config():
            exit_code, _out = _capture(ai_cli.main, ["repair", "myfile.gss"])
    finally:
        guided_mod.run_guided_repair = original
    check("a None return (e.g. configuration error) is a nonzero exit", exit_code == 2)


# ---------------------------------------------------------------------------
# 'repl' subcommand -- config precedence applied, existing main() untouched
#
# v0.70.0 note: tests 14-16 previously drove this exact behavior through a
# BARE `ai_cli.main([])`/`ai_cli.main(["--workspace-parent", ...])` call,
# because bare invocation used to launch the command-by-command REPL
# directly. That expectation is now genuinely obsolete, not merely
# inconvenient: v0.70.0's whole purpose is to change the no-subcommand
# default to conversational chat (see test_20-test_24 below). The REPL
# itself is completely unchanged and fully preserved -- these three tests
# now drive it through the new, explicit `repl` subcommand instead, proving
# the exact same config-precedence and no-reimplementation guarantees as
# before, just reached by an explicit name rather than an implicit default.
# ---------------------------------------------------------------------------


def test_14_repl_subcommand_applies_resolved_config_when_no_explicit_flags() -> None:
    captured_argv: list[str] = []
    original = cli_mod.main
    cli_mod.main = lambda argv: (captured_argv.extend(argv), 0)[1]
    try:
        with _isolated_config() as config_path:
            config_mod.save_config(config_mod.GaussAiConfig(workspace_parent="/configured/workspaces"), config_path)
            ai_cli.main(["repl"])
    finally:
        cli_mod.main = original
    check("--workspace-parent was injected from the config file", "--workspace-parent" in captured_argv and "/configured/workspaces" in captured_argv)


def test_15_repl_subcommand_explicit_cli_flag_overrides_config_file() -> None:
    captured_argv: list[str] = []
    original = cli_mod.main
    cli_mod.main = lambda argv: (captured_argv.extend(argv), 0)[1]
    try:
        with _isolated_config() as config_path:
            config_mod.save_config(config_mod.GaussAiConfig(workspace_parent="/configured/workspaces"), config_path)
            ai_cli.main(["repl", "--workspace-parent", "/explicit/on/command/line"])
    finally:
        cli_mod.main = original
    check("explicit CLI arg is passed through unchanged, config value not injected", captured_argv.count("--workspace-parent") == 1)
    check("the explicit value wins", "/explicit/on/command/line" in captured_argv and "/configured/workspaces" not in captured_argv)


def test_16_repl_subcommand_is_the_real_unmodified_gauss_code_assistant_cli_main() -> None:
    """Structural proof this dispatcher never reimplements the REPL --
    _launch_repl's own source calls cli_mod.main(...), nothing else."""
    source = Path(ai_cli.__file__).read_text(encoding="utf-8")
    check("no second run_repl/InteractiveMvpAdapter construction exists in this module", "InteractiveMvpAdapter(" not in source)
    check("_launch_repl calls the existing cli_mod.main", "return cli_mod.main(final_argv)" in source)


# ---------------------------------------------------------------------------
# v0.70.0: bare invocation now launches conversational chat by default
# ---------------------------------------------------------------------------


def test_20_bare_invocation_launches_chat_not_the_repl() -> None:
    captured: dict[str, object] = {}
    original = chat_mod.run_chat

    def fake_run_chat(**kwargs):
        captured["kwargs"] = kwargs
        return object()

    chat_mod.run_chat = fake_run_chat
    try:
        with _isolated_config():
            exit_code, _out = _capture(ai_cli.main, [])
    finally:
        chat_mod.run_chat = original
    check("exit code 0", exit_code == 0)
    check("run_chat was called for bare invocation", "kwargs" in captured)


def test_21_bare_invocation_with_flags_still_reaches_chat_not_the_repl() -> None:
    """`gauss-ai --provider fake` (bare + flags) must reach chat, mirroring
    the pre-v0.70.0 convention that bare + flags fell through to whatever
    the no-subcommand default was."""
    captured: dict[str, object] = {}
    original = chat_mod.run_chat

    def fake_run_chat(**kwargs):
        captured["kwargs"] = kwargs
        return object()

    chat_mod.run_chat = fake_run_chat
    try:
        with _isolated_config():
            exit_code, _out = _capture(ai_cli.main, ["--provider", "fake"])
    finally:
        chat_mod.run_chat = original
    check("exit code 0", exit_code == 0)
    check("--provider was forwarded to run_chat", captured["kwargs"].get("cli_provider") == "fake")


def test_22_explicit_chat_subcommand_behaves_identically_to_bare_invocation() -> None:
    captured: dict[str, object] = {}
    original = chat_mod.run_chat

    def fake_run_chat(**kwargs):
        captured["kwargs"] = kwargs
        return object()

    chat_mod.run_chat = fake_run_chat
    try:
        with _isolated_config():
            exit_code, _out = _capture(ai_cli.main, ["chat", "--model", "some-model"])
    finally:
        chat_mod.run_chat = original
    check("exit code 0", exit_code == 0)
    check("--model was forwarded to run_chat", captured["kwargs"].get("cli_model") == "some-model")


def test_23_chat_returns_nonzero_when_run_chat_returns_none() -> None:
    original = chat_mod.run_chat
    chat_mod.run_chat = lambda **kwargs: None
    try:
        with _isolated_config():
            exit_code, _out = _capture(ai_cli.main, ["chat", "--provider", "anthropic"])
    finally:
        chat_mod.run_chat = original
    check("a None return (e.g. configuration error) is a nonzero exit", exit_code == 2)


def test_24_config_show_and_set_cover_the_new_chat_settings() -> None:
    with _isolated_config():
        exit_code, out = _capture(ai_cli.main, ["config", "show"])
        check("show exits 0", exit_code == 0)
        check("chat-provider default shown", "chat-provider: fake (default)" in out)
        check("docs-root not-set message shown", "docs-root:" in out and "not set" in out)

        exit_code, _out = _capture(ai_cli.main, ["config", "set", "chat-provider", "anthropic"])
        check("setting chat-provider exits 0", exit_code == 0)
        exit_code, out = _capture(ai_cli.main, ["config", "show"])
        check("show reflects the set chat-provider", "chat-provider: anthropic" in out)

        exit_code, _out = _capture(ai_cli.main, ["config", "set", "chat-provider", "not-a-real-provider"])
        check("an invalid chat-provider value is rejected", exit_code == 1)


# ---------------------------------------------------------------------------
# help / unknown command
# ---------------------------------------------------------------------------


def test_17_help_lists_all_commands() -> None:
    exit_code, out = _capture(ai_cli.main, ["--help"])
    check("exit code 0", exit_code == 0)
    for cmd in ("version", "doctor", "init", "config", "repair", "repl", "chat"):
        check(f"help mentions '{cmd}'", cmd in out)


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
