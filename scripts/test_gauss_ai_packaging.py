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


#: v0.89.0 (planning v0.89 §2.1, decision 13): developer tools that stay in
#: scripts/ and must never be installed as top-level modules.
_DEVELOPER_MODULES = frozenset({
    "build_differential_corpus", "check_evaluation_tracking", "check_release_readiness",
    "gauss_differential_harness", "gauss_syntax_mutations", "validate_all_evidence", "validate_lookup_evidence",
})


def _listed_py_modules() -> list[str] | None:
    try:
        import tomllib
    except ImportError:  # Python 3.10: no tomllib; CI runs this file on 3.12.
        return None
    with (_REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return list(tomllib.load(handle)["tool"]["setuptools"]["py-modules"])


def test_02_v089_wheel_holds_only_product_modules() -> None:
    """What `pip install gauss-ai` would put in site-packages (planning v0.89
    §3.1): the product modules, the two entry points, an SPDX license
    expression, and the MCP Registry ownership marker in the description."""
    import zipfile

    with tempfile.TemporaryDirectory() as tmp:
        result = _run([sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", tmp, str(_REPO_ROOT)], timeout=600.0)
        check(f"pip wheel succeeded (exit {result.returncode})", result.returncode == 0)
        wheels = list(Path(tmp).glob("gauss_ai-*.whl"))
        check("exactly one wheel", len(wheels) == 1)
        if result.returncode != 0 or len(wheels) != 1:
            _failures.append(f"pip wheel stderr tail: {result.stderr[-2000:]}")
            return
        with zipfile.ZipFile(wheels[0]) as wheel:
            names = wheel.namelist()
            metadata_name = next(n for n in names if n.endswith(".dist-info/METADATA"))
            metadata = wheel.read(metadata_name).decode("utf-8")
            entry_points = wheel.read(next(n for n in names if n.endswith(".dist-info/entry_points.txt"))).decode("utf-8")
        modules = {n[:-3] for n in names if n.endswith(".py") and "/" not in n}
        listed = _listed_py_modules()
        if listed is not None:
            check("the wheel's modules are exactly the listed py-modules", modules == set(listed))
        check("no developer module is installed", not (modules & _DEVELOPER_MODULES))
        check("no test module is installed", not any(m.startswith("test_") for m in modules))
        check("every top-level file is a module or dist-info", all(n.endswith(".py") or ".dist-info/" in n for n in names))
        check("the doc reader ships", "gauss_doc_reader" in modules)
        check("gauss-ai entry point", "gauss-ai = gauss_ai_cli:main" in entry_points)
        check("gauss-ai-mcp entry point", "gauss-ai-mcp = gauss_mcp_server:main" in entry_points)
        check("SPDX license expression", "License-Expression: MIT" in metadata)
        check("no license classifier", "License :: OSI Approved" not in metadata)
        check("the MCP Registry marker is in the description", "mcp-name: io.github.ec78/gauss-ai" in metadata)
        check("the mcp extra is declared and optional", "Provides-Extra: mcp" in metadata
              and "Requires-Dist: mcp>=2.3.0; extra == \"mcp\"" in metadata)
        check("no unconditional runtime dependency", not any(
            line.startswith("Requires-Dist:") and "extra ==" not in line for line in metadata.splitlines()))


def test_03_v089_versions_and_opt_in_declarations_agree() -> None:
    """Fast, no build: `.claude-plugin/plugin.json` said 0.82.0 at v0.88.0
    (planning v0.89 §2.1)."""
    import json
    import re

    pyproject = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE).group(1)
    plugin = json.loads((_REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    registry = json.loads((_REPO_ROOT / "server.json").read_text(encoding="utf-8"))
    check("plugin.json version matches pyproject", plugin.get("version") == version)
    check("server.json version matches pyproject", registry.get("version") == version)
    package = registry["packages"][0]
    check("server.json package version matches", package.get("version") == version and package.get("identifier") == "gauss-ai")
    check("server.json installs the mcp extra at this version",
          {"type": "named", "name": "--from", "value": f"gauss-ai[mcp]=={version}"} in package.get("runtimeArguments", []))
    opt_in = [v for v in package.get("environmentVariables", []) if v.get("name") == "GAUSS_AI_MCP_ALLOW_REAL_GAUSS"]
    check("server.json declares the opt-in as optional, with no value or default",
          len(opt_in) == 1 and opt_in[0].get("isRequired") is False and "value" not in opt_in[0] and "default" not in opt_in[0])
    mcp_json = json.loads((_REPO_ROOT / ".mcp.json").read_text(encoding="utf-8"))
    check("the tracked .mcp.json never sets the opt-in", mcp_json["mcpServers"]["gauss-ai"].get("env") == {})
    readme = (_REPO_ROOT / "docs" / "pypi-readme.md").read_text(encoding="utf-8")
    check("the PyPI README carries the registry name", f"mcp-name: {registry['name']}" in readme)
    check("the PyPI README links absolutely", "](docs/" not in readme and "](../" not in readme)
    # Aptech's request (planning v0.89 §9.3): unofficial, unaffiliated, and GAUSS is their trademark.
    disclaimer = "not affiliated with or endorsed by Aptech Systems, Inc. GAUSS is a trademark of Aptech Systems, Inc."
    for name, text in (("PyPI README", readme), ("README", (_REPO_ROOT / "README.md").read_text(encoding="utf-8"))):
        check(f"the {name} carries the unofficial/trademark line", "unofficial" in text and disclaimer in text)
    for module in ("gauss_ai_cli.py", "gauss_docs_fetch.py", "gauss_mcp_server.py"):
        text = (_REPO_ROOT / "scripts" / module).read_text(encoding="utf-8")
        check(f"{module} __version__ matches pyproject", f'__version__ = "{version}"' in text)


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
