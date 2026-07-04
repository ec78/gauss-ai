"""Validate GAUSS command lookup evidence JSON.

This script validates schema-aligned evidence objects against
schemas/command_lookup_evidence.schema.json and reports practical warnings for
risky evidence states. It intentionally does not validate GAUSS syntax or
command semantics.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


LOCAL_PATH_RE = re.compile(
    r"([A-Za-z]:[\\/][^\s\"']+)|(/Users/[^\s\"']+)|(/home/[^\s\"']+)"
)

VERIFIED_FIELD_NAMES = {
    "verified_syntax",
    "verified_inputs",
    "verified_outputs",
    "verified_defaults",
    "verified_examples",
    "syntax_blocks",
    "inputs_section",
    "outputs_section",
    "returns_section",
    "controls_section",
    "formula_section",
    "examples",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_schema_path() -> Path:
    return repo_root() / "schemas" / "command_lookup_evidence.schema.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def is_nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def iter_paths(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from iter_paths(child, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            yield from iter_paths(child, f"{path}[{idx}]")


def has_verified_content(obj: dict[str, Any]) -> bool:
    for key in VERIFIED_FIELD_NAMES:
        if is_nonempty(obj.get(key)):
            return True
    return False


def provenance_missing(obj: dict[str, Any]) -> bool:
    return not (
        is_nonempty(obj.get("file_path") or obj.get("source_path"))
        and is_nonempty(obj.get("source_type"))
        and is_nonempty(obj.get("source_authority"))
    )


def warning_checks(evidence: Any) -> list[str]:
    warnings: list[str] = []

    if not isinstance(evidence, dict):
        return ["Evidence root is not an object; practical warning checks skipped."]

    for path, value in iter_paths(evidence):
        if isinstance(value, str) and LOCAL_PATH_RE.search(value):
            warnings.append(f"Unredacted local absolute path found at {path}.")

    status = evidence.get("retrieval_status") or evidence.get("status")

    if status == "ambiguous":
        ambiguity = evidence.get("ambiguity")
        if not isinstance(ambiguity, dict) or ambiguity.get("is_ambiguous") is not True:
            warnings.append(
                "retrieval_status is ambiguous but ambiguity.is_ambiguous is missing or false."
            )

    if status == "conflict" and not evidence.get("conflicts"):
        warnings.append("retrieval_status is conflict but conflicts is missing or empty.")

    if status == "stale":
        stale = evidence.get("stale_evidence")
        if not isinstance(stale, dict) or stale.get("is_stale") is not True:
            warnings.append(
                "retrieval_status is stale but stale_evidence.is_stale is missing or false."
            )

    if isinstance(status, str) and status.startswith("found") and not evidence.get("matches"):
        warnings.append(f"retrieval_status is {status} but matches is empty.")

    if status == "found_incomplete":
        if not evidence.get("extraction_warnings") and not evidence.get("unresolved_questions"):
            warnings.append(
                "retrieval_status is found_incomplete but no extraction warnings or unresolved questions are present."
            )

    if evidence.get("source_authority") == "category_list":
        if any(is_nonempty(evidence.get(key)) for key in VERIFIED_FIELD_NAMES):
            warnings.append(
                "source_authority is category_list but top-level verified-looking fields are populated."
            )

    for idx, match in enumerate(evidence.get("matches") or []):
        if not isinstance(match, dict):
            continue
        prefix = f"matches[{idx}]"
        if match.get("source_authority") == "category_list" and has_verified_content(match):
            warnings.append(
                f"{prefix} has source_authority category_list but verified-looking sections are populated."
            )
        if has_verified_content(match) and provenance_missing(match):
            warnings.append(f"{prefix} has verified-looking sections but incomplete source provenance.")

    if has_verified_content(evidence) and provenance_missing(evidence):
        warnings.append("Top-level evidence has verified-looking sections but incomplete source provenance.")

    return warnings


def validate_with_jsonschema(evidence: Any, schema: Any) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "The 'jsonschema' package is required for schema validation. "
            "Install it with: python -m pip install jsonschema"
        ) from exc

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(evidence), key=lambda e: list(e.path))
    messages: list[str] = []
    for error in errors:
        path = "$"
        if error.path:
            path += "".join(f"[{part!r}]" for part in error.path)
        messages.append(f"{path}: {error.message}")
    return messages


def build_result(
    evidence_path: Path,
    schema_path: Path,
    schema_errors: list[str],
    warnings: list[str],
    dependency_error: str | None,
    strict: bool,
) -> dict[str, Any]:
    passed_schema = not schema_errors and dependency_error is None
    passed = passed_schema and (not strict or not warnings)
    return {
        "evidence_path": str(evidence_path),
        "schema_path": str(schema_path),
        "schema_valid": passed_schema,
        "passed": passed,
        "strict": strict,
        "schema_errors": schema_errors,
        "warnings": warnings,
        "dependency_error": dependency_error,
    }


def print_human(result: dict[str, Any]) -> None:
    print(f"Evidence: {result['evidence_path']}")
    print(f"Schema:   {result['schema_path']}")

    if result["dependency_error"]:
        print("Result:   ERROR")
        print(result["dependency_error"])
        return

    print(f"Result:   {'PASS' if result['passed'] else 'FAIL'}")
    print(f"Schema:   {'valid' if result['schema_valid'] else 'invalid'}")

    if result["schema_errors"]:
        print("\nSchema errors:")
        for msg in result["schema_errors"]:
            print(f"- {msg}")

    if result["warnings"]:
        print("\nWarnings:")
        for msg in result["warnings"]:
            print(f"- {msg}")

    if result["strict"] and result["warnings"]:
        print("\nStrict mode treats warnings as failures.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate GAUSS command lookup evidence JSON against the evidence schema."
    )
    parser.add_argument("evidence_json", help="Path to lookup/evidence JSON file.")
    parser.add_argument(
        "--schema",
        default=str(default_schema_path()),
        help="Path to JSON Schema file. Defaults to schemas/command_lookup_evidence.schema.json.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as validation failures.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON validation results.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    evidence_path = Path(args.evidence_json)
    schema_path = Path(args.schema)

    dependency_error: str | None = None
    schema_errors: list[str] = []
    warnings: list[str] = []

    try:
        evidence = load_json(evidence_path)
        schema = load_json(schema_path)
    except Exception as exc:
        result = build_result(
            evidence_path,
            schema_path,
            [f"Could not load JSON: {exc}"],
            [],
            None,
            args.strict,
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_human(result)
        return 1

    warnings = warning_checks(evidence)

    try:
        schema_errors = validate_with_jsonschema(evidence, schema)
    except RuntimeError as exc:
        dependency_error = str(exc)

    result = build_result(
        evidence_path,
        schema_path,
        schema_errors,
        warnings,
        dependency_error,
        args.strict,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human(result)

    if dependency_error:
        return 2
    if schema_errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
