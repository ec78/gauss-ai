"""Validate all committed evidence examples and schema fixtures in one pass.

This script reuses the schema/warning-check logic from validate_lookup_evidence.py
so there is one source of truth for what "valid" means. It does not add any new
validation rules of its own; it only aggregates results across many files and
checks each file against its expected outcome (valid vs. intentionally invalid).

It intentionally does not validate GAUSS syntax or command semantics, does not
require GAUSS to be installed, and does not access the network.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_lookup_evidence as vle  # noqa: E402


DEFAULT_TARGET_DIRS = (
    "examples/retrieval/schema-aligned",
    "examples/retrieval/schema-fixtures",
)

INVALID_FIXTURE_PREFIX = "invalid-"


def repo_root() -> Path:
    return vle.repo_root()


def is_expected_invalid(path: Path) -> bool:
    """Files under schema-fixtures/ named invalid-*.json are expected to fail schema validation."""
    return path.parent.name == "schema-fixtures" and path.name.startswith(INVALID_FIXTURE_PREFIX)


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root())).replace("\\", "/")
    except ValueError:
        return str(path)


def collect_target_files(paths: list[str] | None) -> list[Path]:
    if paths:
        roots = [Path(p) for p in paths]
    else:
        roots = [repo_root() / d for d in DEFAULT_TARGET_DIRS]

    files: list[Path] = []
    for root in roots:
        if root.is_dir():
            files.extend(sorted(root.glob("*.json")))
        elif root.is_file():
            files.append(root)
        else:
            files.append(root)  # let it surface as a load error below

    # De-duplicate while preserving order, in case overlapping paths were given.
    seen: set[Path] = set()
    deduped: list[Path] = []
    for f in files:
        resolved = f.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(f)
    return deduped


def validate_one(path: Path, schema_path: Path, strict: bool) -> dict[str, Any]:
    dependency_error: str | None = None
    schema_errors: list[str] = []
    warnings: list[str] = []

    try:
        evidence = vle.load_json(path)
        schema = vle.load_json(schema_path)
    except Exception as exc:
        result = vle.build_result(path, schema_path, [f"Could not load JSON: {exc}"], [], None, strict)
        result["expected_invalid"] = is_expected_invalid(path)
        result["outcome_ok"] = False
        result["relpath"] = relpath(path)
        return result

    warnings = vle.warning_checks(evidence)
    try:
        schema_errors = vle.validate_with_jsonschema(evidence, schema)
    except RuntimeError as exc:
        dependency_error = str(exc)

    result = vle.build_result(path, schema_path, schema_errors, warnings, dependency_error, strict)
    result["relpath"] = relpath(path)

    expected_invalid = is_expected_invalid(path)
    result["expected_invalid"] = expected_invalid

    if dependency_error:
        outcome_ok = False
    elif expected_invalid:
        # Expected-invalid files must fail schema validation specifically,
        # not merely trip a --strict warning.
        outcome_ok = not result["schema_valid"]
    else:
        outcome_ok = result["passed"]

    result["outcome_ok"] = outcome_ok
    return result


def print_human(results: list[dict[str, Any]], strict: bool) -> None:
    for r in results:
        if r["dependency_error"]:
            status = "ERROR"
        elif r["expected_invalid"]:
            status = "OK (expected-invalid)" if r["outcome_ok"] else "UNEXPECTED-PASS"
        else:
            status = "PASS" if r["outcome_ok"] else "FAIL"

        warn_note = f" [{len(r['warnings'])} warning(s)]" if r["warnings"] else ""
        print(f"{status:<22} {r['relpath']}{warn_note}")

        if r["dependency_error"]:
            print(f"    {r['dependency_error']}")
        if not r["outcome_ok"]:
            for msg in r["schema_errors"]:
                print(f"    schema error: {msg}")
            for msg in r["warnings"]:
                print(f"    warning: {msg}")

    total = len(results)
    unexpected = [r for r in results if not r["outcome_ok"]]
    total_warnings = sum(len(r["warnings"]) for r in results)

    print()
    print(f"Checked {total} file(s): {total - len(unexpected)} as expected, {len(unexpected)} unexpected.")
    print(f"Total warnings across all files: {total_warnings}.")
    if strict and total_warnings and not unexpected:
        print("Strict mode: warnings did not cause an unexpected result for any file above, but were counted.")
    if unexpected:
        print("Unexpected files:")
        for r in unexpected:
            print(f"  - {r['relpath']}")
    else:
        print("Overall: PASS")


def build_summary(results: list[dict[str, Any]], strict: bool) -> dict[str, Any]:
    unexpected = [r for r in results if not r["outcome_ok"]]
    return {
        "strict": strict,
        "checked": len(results),
        "overall_pass": len(unexpected) == 0,
        "unexpected_count": len(unexpected),
        "total_warnings": sum(len(r["warnings"]) for r in results),
        "results": [
            {
                "path": r["relpath"],
                "expected_invalid": r["expected_invalid"],
                "schema_valid": r["schema_valid"],
                "passed": r["passed"],
                "outcome_ok": r["outcome_ok"],
                "warnings": r["warnings"],
                "schema_errors": r["schema_errors"],
                "dependency_error": r["dependency_error"],
            }
            for r in results
        ],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate all committed schema-aligned evidence examples and schema "
            "fixtures against schemas/command_lookup_evidence.schema.json."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help=(
            "Optional files or directories to validate instead of the defaults "
            "(examples/retrieval/schema-aligned/ and examples/retrieval/schema-fixtures/)."
        ),
    )
    parser.add_argument(
        "--schema",
        default=str(vle.default_schema_path()),
        help="Path to JSON Schema file. Defaults to schemas/command_lookup_evidence.schema.json.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as validation failures for expected-valid files (passed through to each file's validation).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary instead of human-readable output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    schema_path = Path(args.schema)

    files = collect_target_files(args.paths or None)
    if not files:
        print("No evidence files found to validate.")
        return 1

    results = [validate_one(f, schema_path, args.strict) for f in files]

    if args.json:
        print(json.dumps(build_summary(results, args.strict), indent=2))
    else:
        print_human(results, args.strict)

    return 0 if all(r["outcome_ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
