"""Run the default release-health guard suite in one command.

This is a thin wrapper around the existing, independently-runnable guard
scripts (scripts/validate_all_evidence.py, scripts/check_evaluation_tracking.py).
It does not implement new validation logic, does not change either script's
behavior, and does not suppress, hide, or reinterpret their warnings -- it
only runs them, prints each one's real output, and summarizes overall
pass/fail.

By default this runs only the two default (non-strict) checks, since those
are the release-health gates established by existing policy (see
scripts/README.md's strict-mode policy notes). Pass --strict to additionally
run both scripts in --strict mode as an informational, separate result --
strict-mode failure is currently expected (documented evidence and tracking
warnings) and is never folded into this script's own pass/fail exit code.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_CHECKS = ("validate_all_evidence.py", "check_evaluation_tracking.py")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_check(script: str, extra_args: list[str]) -> dict[str, Any]:
    cmd = [sys.executable, str(repo_root() / "scripts" / script), *extra_args]
    proc = subprocess.run(cmd, cwd=repo_root(), capture_output=True, text=True)
    return {
        "script": script,
        "args": extra_args,
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def print_check(check: dict[str, Any], label: str) -> None:
    print(f"\n$ {check['command']}")
    print(check["stdout"], end="")
    if check["stderr"]:
        print(check["stderr"], end="")
    print(f"[{label}: {'PASS' if check['passed'] else 'FAIL'}]")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the default release-health guard suite: scripts/validate_all_evidence.py "
            "and scripts/check_evaluation_tracking.py. This does not modify either script's "
            "behavior; it only runs them and summarizes the result."
        )
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Also run both checks in --strict mode, reported separately. Strict failure is "
            "currently expected (documented HDF5-URI evidence warnings and two historical "
            "tracking warnings) and does not affect this script's exit code."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary instead of human-readable output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    default_checks = [run_check(script, []) for script in DEFAULT_CHECKS]
    default_pass = all(c["passed"] for c in default_checks)

    strict_checks: list[dict[str, Any]] = []
    strict_pass: bool | None = None
    if args.strict:
        strict_checks = [run_check(script, ["--strict"]) for script in DEFAULT_CHECKS]
        strict_pass = all(c["passed"] for c in strict_checks)

    if args.json:
        summary: dict[str, Any] = {
            "default_checks": [
                {"script": c["script"], "passed": c["passed"], "returncode": c["returncode"]}
                for c in default_checks
            ],
            "default_pass": default_pass,
        }
        if args.strict:
            summary["strict_checks"] = [
                {"script": c["script"], "passed": c["passed"], "returncode": c["returncode"]}
                for c in strict_checks
            ]
            summary["strict_pass"] = strict_pass
            summary["strict_note"] = (
                "Strict failure is currently expected due to documented, reviewed warnings "
                "(see scripts/README.md's strict-mode policy notes). It is informational here "
                "and does not affect overall_pass."
            )
        summary["overall_pass"] = default_pass
        print(json.dumps(summary, indent=2))
    else:
        print("=== Release Readiness: Default Checks ===")
        for check, script in zip(default_checks, DEFAULT_CHECKS):
            print_check(check, script)
        print(f"\nDefault checks overall: {'PASS' if default_pass else 'FAIL'}")

        if args.strict:
            print("\n=== Release Readiness: Strict Checks (informational; failure is expected) ===")
            for check, script in zip(strict_checks, DEFAULT_CHECKS):
                print_check(check, f"{script} --strict")
            print(f"\nStrict checks overall: {'PASS' if strict_pass else 'FAIL'}")
            if not strict_pass:
                print(
                    "Strict failure is currently expected: glm/olsmt evidence HDF5-URI path "
                    "warnings and two documented historical tracking warnings remain. See "
                    "scripts/README.md's strict-mode policy notes. This does not affect the "
                    "overall release-readiness result above, which is based on default checks only."
                )

    return 0 if default_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
