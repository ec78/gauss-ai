"""Tests for `gauss-ai doctor` read-only diagnostics (v0.67.0).

Run with:

    python scripts/test_gauss_ai_doctor.py

Every check is exercised with injected values (Python version, config,
environment, workspace path) -- no test depends on this machine's actual
GAUSS installation state, and no test executes anything, installs anything,
or touches the network.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_ai_config as config_mod  # noqa: E402
import gauss_ai_doctor as doctor_mod  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _get(report: "doctor_mod.DoctorReport", name: str) -> "doctor_mod.DoctorCheckResult":
    for c in report.checks:
        if c.name == name:
            return c
    raise AssertionError(f"no check named {name!r} in report")


# ---------------------------------------------------------------------------
# python_version
# ---------------------------------------------------------------------------


def test_01_python_version_pass_for_supported_version() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(config_path=Path(tmp) / "config.json", python_version_info=(3, 12, 0))
    check("supported Python version passes", _get(report, "python_version").status == doctor_mod.PASS)


def test_02_python_version_fail_for_unsupported_version() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(config_path=Path(tmp) / "config.json", python_version_info=(3, 8, 0))
    result = _get(report, "python_version")
    check("unsupported Python version fails", result.status == doctor_mod.FAIL)
    check("next_step is actionable", result.next_step is not None and "install" in result.next_step.lower())


# ---------------------------------------------------------------------------
# module_imports
# ---------------------------------------------------------------------------


def test_03_module_imports_pass_for_real_modules() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(config_path=Path(tmp) / "config.json")
    check("real, installed modules import cleanly", _get(report, "module_imports").status == doctor_mod.PASS)


def test_04_module_imports_fail_for_missing_module() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(
            config_path=Path(tmp) / "config.json", module_names=("gauss_code_assistant_cli", "this_module_does_not_exist_xyz")
        )
    result = _get(report, "module_imports")
    check("a genuinely missing module fails the check", result.status == doctor_mod.FAIL)
    check("failing module named in the message", "this_module_does_not_exist_xyz" in result.message)


# ---------------------------------------------------------------------------
# workspace_parent
# ---------------------------------------------------------------------------


def test_05_workspace_parent_warn_when_unconfigured() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(config=config_mod.GaussAiConfig(), config_path=Path(tmp) / "config.json", env={})
    check("unconfigured workspace parent is a WARN, not a FAIL", _get(report, "workspace_parent").status == doctor_mod.WARN)


def test_06_workspace_parent_pass_when_writable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(cli_workspace_parent=tmp, config_path=Path(tmp) / "config.json")
    check("a writable configured workspace parent passes", _get(report, "workspace_parent").status == doctor_mod.PASS)


def test_07_workspace_parent_fail_when_path_is_unusable() -> None:
    """A workspace parent path that collides with an existing FILE (not a
    directory) can never be mkdir'd -- doctor must report FAIL cleanly,
    never crash, regardless of the underlying OSError/ValueError shape."""
    with tempfile.TemporaryDirectory() as tmp:
        blocking_file = Path(tmp) / "blocked"
        blocking_file.write_text("this is a file, not a directory", encoding="utf-8")
        unusable_parent = blocking_file / "workspaces"
        report = doctor_mod.run_doctor(cli_workspace_parent=str(unusable_parent), config_path=Path(tmp) / "config.json")
    check("an unusable configured workspace parent fails cleanly, no crash", _get(report, "workspace_parent").status == doctor_mod.FAIL)


def test_07b_workspace_parent_never_crashes_on_malformed_path() -> None:
    """Regression test for a genuine doctor defect found during testing:
    _check_workspace_parent originally caught only OSError, so a malformed
    path raising ValueError (e.g. an embedded null byte) crashed run_doctor
    entirely instead of reporting a clean FAIL."""
    with tempfile.TemporaryDirectory() as tmp:
        malformed_parent = "\x00invalid-null-byte-path"
        report = doctor_mod.run_doctor(cli_workspace_parent=malformed_parent, config_path=Path(tmp) / "config.json")
    check("a malformed path is reported as FAIL, not a crash", _get(report, "workspace_parent").status == doctor_mod.FAIL)


# ---------------------------------------------------------------------------
# gauss_executable_configured / gauss_executable_valid
# ---------------------------------------------------------------------------


def test_08_gauss_executable_warn_when_unconfigured() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(config=config_mod.GaussAiConfig(), config_path=Path(tmp) / "config.json", env={})
    check("unconfigured executable is WARN, not FAIL", _get(report, "gauss_executable_configured").status == doctor_mod.WARN)
    check("gauss_executable_valid is skipped (WARN) when nothing is configured", _get(report, "gauss_executable_valid").status == doctor_mod.WARN)


def test_09_gauss_executable_valid_pass_for_real_terminal_executable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "tgauss.exe"
        p.write_bytes(b"")
        report = doctor_mod.run_doctor(cli_gauss_executable=str(p), config_path=Path(tmp) / "config.json")
    check("configured check passes", _get(report, "gauss_executable_configured").status == doctor_mod.PASS)
    check("valid check passes for a real terminal executable", _get(report, "gauss_executable_valid").status == doctor_mod.PASS)


def test_10_gauss_executable_valid_fail_for_gui_executable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "gauss.exe"
        p.write_bytes(b"")
        report = doctor_mod.run_doctor(cli_gauss_executable=str(p), config_path=Path(tmp) / "config.json")
    result = _get(report, "gauss_executable_valid")
    check("a configured GUI executable fails validity", result.status == doctor_mod.FAIL)
    check("message explains why", "GUI" in result.message)


def test_11_gauss_executable_valid_fail_for_missing_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(cli_gauss_executable="/does/not/exist/tgauss.exe", config_path=Path(tmp) / "config.json")
    check("a configured but missing executable fails validity", _get(report, "gauss_executable_valid").status == doctor_mod.FAIL)


def test_12_doctor_never_launches_the_configured_executable() -> None:
    """The configured executable is a zero-byte stub file -- if doctor tried
    to launch it, this would raise an OS-level exception (not a valid
    executable). A clean PASS with 'GAUSS was not launched' in the message
    is the structural proof doctor never invokes it."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "GAUSS26" / "tgauss.exe"
        p.parent.mkdir(parents=True)
        p.write_bytes(b"not a real executable")
        report = doctor_mod.run_doctor(cli_gauss_executable=str(p), config_path=Path(tmp) / "config.json")
    result = _get(report, "gauss_executable_valid")
    check("doctor completes without attempting to launch the stub executable", result.status == doctor_mod.PASS)
    check("message discloses GAUSS was not launched", "not launched" in result.message)
    check("version was parsed from the path string, not by execution", "26" in result.message)


# ---------------------------------------------------------------------------
# config_file_validity
# ---------------------------------------------------------------------------


def test_13_config_file_validity_pass_when_absent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(config_path=Path(tmp) / "no-such-file.json")
    check("absent config file is PASS (defaults apply)", _get(report, "config_file_validity").status == doctor_mod.PASS)


def test_14_config_file_validity_fail_when_corrupt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        path.write_text("not { valid json", encoding="utf-8")
        report = doctor_mod.run_doctor(config_path=path)
    check("corrupt config file fails validity", _get(report, "config_file_validity").status == doctor_mod.FAIL)


# ---------------------------------------------------------------------------
# overall_status and read-only guarantees
# ---------------------------------------------------------------------------


def test_15_overall_status_is_fail_if_any_check_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(cli_gauss_executable="/does/not/exist", config_path=Path(tmp) / "config.json")
    check("a single FAIL makes overall_status FAIL", report.overall_status == doctor_mod.FAIL)


def test_16_overall_status_is_warn_if_only_warnings() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(config=config_mod.GaussAiConfig(), config_path=Path(tmp) / "config.json", env={})
    check(
        "no FAIL, at least one WARN -> overall WARN",
        report.overall_status == doctor_mod.WARN and not any(c.status == doctor_mod.FAIL for c in report.checks),
    )


def test_17_overall_status_pass_when_fully_configured() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "tgauss.exe"
        p.write_bytes(b"")
        report = doctor_mod.run_doctor(cli_gauss_executable=str(p), cli_workspace_parent=tmp, config_path=Path(tmp) / "config.json")
    non_advisory = [c for c in report.checks if c.name != "package_version"]
    check("every non-metadata check passes when fully and correctly configured", all(c.status == doctor_mod.PASS for c in non_advisory))


def test_18_render_report_shows_status_and_next_steps() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = doctor_mod.run_doctor(config=config_mod.GaussAiConfig(), config_path=Path(tmp) / "config.json", env={})
    lines = doctor_mod.render_report(report)
    text = "\n".join(lines)
    check("rendered output includes [PASS]/[WARN]/[FAIL] markers", "[PASS]" in text or "[WARN]" in text or "[FAIL]" in text)
    check("rendered output includes an Overall: line", any(line.startswith("Overall:") for line in lines))
    check("a WARN's own next_step is rendered", "next step:" in text)


def test_19_doctor_module_defines_no_execution_install_or_mutation_callables() -> None:
    source = Path(doctor_mod.__file__).read_text(encoding="utf-8")
    forbidden = ("def execute(", "def apply_repair(", "def install(", "subprocess.", "def save_config(")
    for token in forbidden:
        check(f"doctor module does not define/call {token!r}", token not in source)


def test_20_doctor_never_imports_network_or_process_launch_modules() -> None:
    source = Path(doctor_mod.__file__).read_text(encoding="utf-8")
    forbidden = ("import subprocess", "import socket", "import urllib", "import requests")
    for token in forbidden:
        check(f"doctor module does not {token!r}", token not in source)


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
