"""Installation/packaging tests for `gauss-ai` (v0.67.0).

Run with:

    python scripts/test_gauss_ai_packaging.py

Unlike every other `test_*.py` file in this repository, this one is slow
(it creates a real, disposable virtual environment and runs a real `pip
install -e .`) and is not part of the fast day-to-day regression loop --
run it explicitly as part of packaging validation. It never modifies the
user's global Python environment: every install happens inside a fresh
`tempfile.TemporaryDirectory()`-backed venv that is discarded when the test
finishes. No network access is required beyond what `pip` itself needs to
resolve `setuptools` (already satisfied from the local pip cache in every
environment this has been run in); `gauss-ai` itself declares zero runtime
dependencies.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import venv
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform.startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_entry_point(venv_dir: Path, name: str) -> Path:
    if sys.platform.startswith("win"):
        return venv_dir / "Scripts" / f"{name}.exe"
    return venv_dir / "bin" / name


def _run(args: list[str], *, cwd: Path | None = None, timeout: float = 180.0) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def test_01_editable_install_succeeds_in_a_disposable_venv() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        venv_dir = Path(tmp) / "venv"
        venv.create(venv_dir, with_pip=True)
        python = _venv_python(venv_dir)
        check("venv python was created", python.is_file())

        # No --no-build-isolation: Python 3.12's `venv` no longer bundles
        # setuptools by default, so pip's own build isolation (which fetches
        # the declared build backend, setuptools, into a throwaway build
        # env) is required here, not an optimization to skip.
        result = _run([str(python), "-m", "pip", "install", "-e", str(_REPO_ROOT)])
        check(f"pip install -e . succeeded (exit {result.returncode})", result.returncode == 0)
        if result.returncode != 0:
            _failures.append(f"pip install stderr tail: {result.stderr[-2000:]}")
            return

        entry_point = _venv_entry_point(venv_dir, "gauss-ai")
        check("the gauss-ai console-script entry point was created", entry_point.is_file())

        version_result = _run([str(entry_point), "version"])
        check("gauss-ai version exits 0 from the installed entry point", version_result.returncode == 0)
        check("gauss-ai version output includes 'gauss-ai version:'", "gauss-ai version:" in version_result.stdout)

        doctor_result = _run([str(entry_point), "doctor"])
        check(
            "gauss-ai doctor runs without GAUSS installed and exits 0 (WARN, not FAIL)",
            doctor_result.returncode == 0,
        )
        check("gauss-ai doctor output shows an Overall: line", "Overall:" in doctor_result.stdout)

        # cwd-independence: run the entry point from a directory that is
        # NOT the repository root and does not contain scripts/ at all.
        outside_dir = Path(tmp) / "somewhere-else-entirely"
        outside_dir.mkdir()
        outside_result = _run([str(entry_point), "version"], cwd=outside_dir)
        check(
            "gauss-ai version works from a cwd outside the repository entirely",
            outside_result.returncode == 0 and "gauss-ai version:" in outside_result.stdout,
        )

        # The user should never need to import a gauss_* module manually --
        # the installed module namespace should be reachable by the
        # entry point alone, from any cwd, with no PYTHONPATH manipulation.
        module_check = _run(
            [str(python), "-c", "import gauss_code_assistant_cli; print('OK')"], cwd=outside_dir
        )
        check(
            "core modules import directly after install, with no sys.path manipulation, from any cwd",
            module_check.returncode == 0 and "OK" in module_check.stdout,
        )


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
