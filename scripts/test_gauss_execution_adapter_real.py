"""Doubly-gated REAL GAUSS smoke-test harness for the Helper Adapter
(v0.32.0 Phase 3, Increment 1 -- planning/v0.32.0-real-helper-adapter-scope.md
Section 16/22-23's resolved smoke-test enablement decision).

THIS FILE CAN INVOKE REAL GAUSS. It is not a default test. It must never be
run as part of `python scripts/test_gauss_execution_adapter.py`,
`python scripts/test_gauss_runtime_orchestration.py`,
`python scripts/check_release_readiness.py`, or any CI workflow -- none of
those import or execute this file, and this file requires two independent,
explicit opt-in gates before it will do anything beyond print a skip notice:

    1. The command-line flag --run-real-gauss
    2. The environment variable GAUSS_AI_ALLOW_REAL_EXECUTION=1

BOTH are required simultaneously. Either one missing means this harness
skips safely without touching GAUSS, without invoking the Helper Adapter,
and without importing scripts/gauss_code_execution.py.

Merely importing this module does nothing -- no gate is checked, no
directory is created, no helper is loaded, at import time. All gating and
preflight logic runs only inside main(), when explicitly invoked.

This module was created, and its gating/preflight logic was tested, WITHOUT
ever supplying both gates simultaneously, per
planning/v0.32.0-real-helper-adapter-scope.md's Increment 1 boundary: this
revision creates and tests only the gating and preflight behavior. No GAUSS
was run, no subprocess was launched, and the real helper was not invoked in
the production of this file.
"""

from __future__ import annotations

import argparse
import os
import platform
import sys
import tempfile
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# gauss_execution_adapter is safe to import unconditionally -- it has no
# import-time execution side effects (see its own docstring and
# scripts/test_gauss_execution_adapter.py's test_26). It is NOT imported
# lazily here because importing it never risks touching real GAUSS; only
# calling ga.load_real_helper() (invoked below, only after both gates pass)
# would import scripts/gauss_code_execution.py, and only actually calling
# the adapter's .invoke(...) (also only reached after both gates pass)
# would run a real subprocess.
import gauss_execution_adapter as ga  # noqa: E402

ENV_VAR_NAME = "GAUSS_AI_ALLOW_REAL_EXECUTION"
REQUIRED_ENV_VALUE = "1"
FLAG_NAME = "--run-real-gauss"

# The only environment this repository has ever verified real non-interactive
# GAUSS invocation against (v0.28.0/v0.29.0). This harness refuses to proceed
# on any other platform unless a future revision explicitly expands this set
# with its own new verification evidence -- not assumed here.
_VERIFIED_PLATFORM = "Windows"
_SUPPORTED_EXECUTABLE_BASENAMES = frozenset({"tgauss", "tgauss.exe"})

# Minimal, non-destructive, hardcoded inline code -- never user-suppliable
# through this harness, so no arbitrary code can reach a real GAUSS process
# through this file. This exact script (an assignment followed by print) is
# not invented -- it is byte-for-byte the script content real-verified as
# Test 3 ("Scalar calculation") in planning/v0.28.0-real-gauss-invocation-research.md:
# run via tgauss.exe -b calc.gss, confirmed exit code 0, confirmed stdout
# "       4.0000000". The previous placeholder here, "print 1+1;", was never
# itself verified as script-file content -- only the -e inline-expression
# form of that exact string was attempted, and that attempt was recorded as
# inconclusive/not confirmed working (v0.28.0 Test 6). This harness never
# uses -e; it always writes code to a generated script file and invokes it
# via the verified tgauss.exe -b <script_path> form, so this correction
# replaces an unverified string with a genuinely verified one.
_SMOKE_TEST_CODE = "x = 2 + 2;\nprint x;"


def gate_status(*, flag_present: bool, env_value: str | None) -> tuple[bool, bool]:
    """Pure function: computes (flag_present, env_present) from explicit
    inputs, so gating logic is testable without touching real argv/environ."""
    env_present = env_value == REQUIRED_ENV_VALUE
    return flag_present, env_present


def should_run(flag_present: bool, env_present: bool) -> bool:
    """Both gates are required. Either one missing means skip."""
    return flag_present and env_present


class PreflightOutcome:
    SKIPPED_NO_GATES = "skipped_no_gates"
    SKIPPED_ONE_GATE = "skipped_one_gate"
    PREFLIGHT_FAILED_PLATFORM = "preflight_failed_platform"
    PREFLIGHT_FAILED_EXECUTABLE = "preflight_failed_executable"
    PREFLIGHT_PASSED = "preflight_passed"


def _verify_platform() -> bool:
    """Environment verification step 1: this harness only proceeds on the
    one platform this repository has ever verified real invocation against.
    Does not call scripts/gauss_environment_check.py -- this is a plain
    stdlib platform.system() check, not GAUSS detection."""
    return platform.system() == _VERIFIED_PLATFORM


def _verify_executable(executable_path: str | None) -> bool:
    """Environment verification step 2: an explicit, existing, terminal
    (non-GUI) executable path is required -- no auto-detection, no default,
    no fallback. GUI gauss.exe is rejected here, the same way
    scripts/gauss_execution_adapter.py's own GaussExecutionAdapter rejects
    it -- defense in depth, checked again below at the adapter boundary
    too."""
    if not executable_path:
        return False
    basename = Path(executable_path).name.lower()
    if basename not in _SUPPORTED_EXECUTABLE_BASENAMES:
        return False
    try:
        return Path(executable_path).exists()
    except OSError:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Doubly-gated real GAUSS smoke-test harness for the Helper Adapter. "
            "Requires --run-real-gauss AND GAUSS_AI_ALLOW_REAL_EXECUTION=1 "
            "simultaneously; either one missing skips safely without touching GAUSS."
        )
    )
    parser.add_argument(
        "--run-real-gauss",
        action="store_true",
        dest="run_real_gauss",
        help="First of two required gates. Does nothing by itself.",
    )
    parser.add_argument(
        "--executable-path",
        default=None,
        help=(
            "Required only if both gates are present: an explicit, existing terminal "
            "GAUSS executable path (tgauss/tgauss.exe). No auto-detection is performed."
        ),
    )
    parser.add_argument(
        "--working-directory",
        default=None,
        help=(
            "Optional explicit contained working directory to use if both gates are present. "
            "If omitted, a fresh disposable temporary directory is created and used."
        ),
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Test only the gating/preflight logic (never both gates at once) and exit.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.self_test:
        return _run_self_tests()

    flag_present, env_present = gate_status(
        flag_present=args.run_real_gauss, env_value=os.environ.get(ENV_VAR_NAME)
    )

    if not flag_present and not env_present:
        print(f"SKIPPED: neither {FLAG_NAME} nor {ENV_VAR_NAME}=1 was supplied. No GAUSS was touched.")
        return 0
    if flag_present and not env_present:
        print(
            f"SKIPPED: {FLAG_NAME} was supplied, but {ENV_VAR_NAME}=1 was not set. "
            "Both gates are required simultaneously. No GAUSS was touched."
        )
        return 0
    if env_present and not flag_present:
        print(
            f"SKIPPED: {ENV_VAR_NAME}=1 was set, but {FLAG_NAME} was not supplied. "
            "Both gates are required simultaneously. No GAUSS was touched."
        )
        return 0

    # Both gates are present. Print a prominent, unmissable notice before
    # doing anything else.
    print("=" * 72)
    print("REAL GAUSS EXECUTION IS ENABLED FOR THIS RUN.")
    print(f"Both {FLAG_NAME} and {ENV_VAR_NAME}=1 were supplied.")
    print("A real, minimal, non-destructive GAUSS process may be launched below.")
    print("=" * 72)

    if not _verify_platform():
        print(
            f"PREFLIGHT FAILED: this harness only proceeds on {_VERIFIED_PLATFORM} "
            f"(detected: {platform.system()}). No GAUSS was touched."
        )
        return 0

    if not _verify_executable(args.executable_path):
        print(
            "PREFLIGHT FAILED: --executable-path was missing, was not a terminal "
            "(tgauss/tgauss.exe) executable, or does not exist. GUI executables are never "
            "used. No GAUSS was touched."
        )
        return 0

    print("Preflight checks passed: platform verified, executable verified as terminal and present.")

    assert args.executable_path is not None
    real_helper = ga.load_real_helper()
    adapter = ga.GaussExecutionAdapter(helper=real_helper)

    if args.working_directory:
        return _invoke_once(adapter, args.executable_path, args.working_directory)

    with tempfile.TemporaryDirectory(prefix="gauss_ai_real_smoke_") as tmp_dir:
        return _invoke_once(adapter, args.executable_path, tmp_dir)


def _invoke_once(adapter: "ga.GaussExecutionAdapter", executable_path: str, working_directory: str) -> int:
    request = ga.AdapterRequest(
        request_identity="real-smoke-test-single-invocation",
        code=_SMOKE_TEST_CODE,
        script_path=None,
        working_directory=working_directory,
        output_directory=None,
        executable_path=executable_path,
        gauss_version=None,
        timeout_seconds=30.0,
        allow_output_files=True,
    )
    outcome = adapter.invoke(request)
    if not outcome.invoked:
        category = outcome.failure_category.value if outcome.failure_category else "unknown"
        print(f"BLOCKED before invocation: {category} -- {outcome.rejection_reason}")
        return 0

    print(f"execution_status: {outcome.execution_status}")
    raw = outcome.raw_result or {}
    print(f"exit_code (non-authoritative -- see scripts/gauss_code_execution.py's _detect_gauss_error): {raw.get('exit_code')}")
    print(f"elapsed_seconds: {raw.get('elapsed_seconds')}")
    print(f"stdout: {raw.get('stdout')!r}")
    print(f"stderr: {raw.get('stderr')!r}")
    print(f"warnings: {raw.get('warnings')}")
    print(f"errors: {raw.get('errors')}")
    print(f"output file count (metadata only, contents never read): {len(raw.get('output_files') or [])}")
    try:
        schema_errors = ga.validate_against_real_schema(raw)
        print(f"schema_validation_errors: {schema_errors if schema_errors else '[] (valid)'}")
    except ImportError as exc:
        print(f"schema_validation_errors: could not validate -- {exc}")
    return 0


# ---------------------------------------------------------------------------
# Self-test: gating/preflight logic only. Never supplies both gates
# simultaneously, never calls _invoke_once, never calls
# gauss_execution_adapter.load_real_helper().
# ---------------------------------------------------------------------------


def _run_self_tests() -> int:
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    check("no gates -> should not run", should_run(*gate_status(flag_present=False, env_value=None)) is False)
    check(
        "flag only -> should not run",
        should_run(*gate_status(flag_present=True, env_value=None)) is False,
    )
    check(
        "env var only -> should not run",
        should_run(*gate_status(flag_present=False, env_value=REQUIRED_ENV_VALUE)) is False,
    )
    check(
        "wrong env var value -> should not run",
        should_run(*gate_status(flag_present=True, env_value="true")) is False,
    )
    check(
        "both gates present -> should run (pure boolean check only, never executed)",
        should_run(*gate_status(flag_present=True, env_value=REQUIRED_ENV_VALUE)) is True,
    )

    check("platform verification is a plain stdlib check", _verify_platform() == (platform.system() == _VERIFIED_PLATFORM))
    check("missing executable_path fails preflight", _verify_executable(None) is False)
    check("GUI executable fails preflight", _verify_executable("C:/example/gauss26/gauss.exe") is False)
    check(
        "nonexistent terminal executable fails preflight",
        _verify_executable("C:/definitely/does/not/exist/tgauss.exe") is False,
    )

    # Exercise the actual CLI parsing / skip-path of main() with zero and one
    # gate -- both safe, both must return 0 without ever reaching invocation.
    # Safety-critical: main() reads the REAL os.environ internally, so this
    # self-test must never trust the ambient shell not to already have
    # GAUSS_AI_ALLOW_REAL_EXECUTION=1 set -- it explicitly clears it for the
    # duration of these two calls and restores whatever was there afterward,
    # regardless of outcome.
    sentinel_absent = object()
    previous_env_value = os.environ.get(ENV_VAR_NAME, sentinel_absent)
    if ENV_VAR_NAME in os.environ:
        del os.environ[ENV_VAR_NAME]
    try:
        check("main() with no args skips cleanly", main([]) == 0)
        check("main() with only the flag skips cleanly", main(["--run-real-gauss"]) == 0)
    finally:
        if previous_env_value is sentinel_absent:
            os.environ.pop(ENV_VAR_NAME, None)
        else:
            os.environ[ENV_VAR_NAME] = previous_env_value  # type: ignore[assignment]

    if failures:
        print(f"SELF-TEST FAILED ({len(failures)} issue(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SELF-TEST PASSED: gating and preflight logic verified; no GAUSS was touched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
