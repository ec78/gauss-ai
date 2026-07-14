"""Inspect which GAUSS packages/application modules appear available.

This is a read-only package inspection helper implementing the contract
defined in tools/gauss_package_inspection.md and validated against
schemas/gauss_package_inspection.schema.json.

It does not run user GAUSS code, does not execute statistical analysis, does
not install packages, does not activate Execution Mode, and does not
implement runtime orchestration -- an "installed: true" package result is
only context for a possible future execution decision (per
tools/gauss_package_inspection.md's Operating Mode Relationship section), not
proof that any code has run.

Package inspection depends on, but is separate from, GAUSS environment
detection (scripts/gauss_environment_check.py). Per
planning/v0.23.0-gauss-package-inspection-implementation.md's "Version-Specific
Package Context Rule", this helper always inherits the selected GAUSS version
and executable context rather than re-deciding it, and never mixes package
results across GAUSS versions.

Package/application-module directories are located using a small, explicitly
non-exhaustive heuristic (sibling "pkgs"/"packages" directories next to the
selected executable), the same conservative-starting-set discipline
scripts/gauss_environment_check.py already applies to
PLAUSIBLE_EXECUTABLE_NAMES and COMMON_LOCATION_TEMPLATES.

No safe, confirmed GAUSS package-metadata query command is documented in this
repository yet, so --allow-metadata-query does not actually invoke any
executable here; it is accepted for forward compatibility with the input
contract and currently only adds an explanatory warning. See
tools/gauss_package_inspection.md's "Optional metadata query" section.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

try:
    import gauss_environment_check as _env_check
except ImportError:  # pragma: no cover - defensive; keeps this script standalone
    _env_check = None

_ENV_STATUS_ENUM = {"found", "not_found", "ambiguous", "inaccessible", "error", "unknown"}

_SEPARATOR_RE = re.compile(r"[\s_\-]+")

_METADATA_QUERY_WARNING = (
    "Metadata query was requested but is not implemented because no safe GAUSS "
    "package metadata query has been confirmed."
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_schema_path() -> Path:
    return repo_root() / "schemas" / "gauss_package_inspection.schema.json"


def _normalize_name(name: str) -> str:
    """Case/separator-insensitive normalization only -- no alias inference.

    'tsmt', 'TSMT', 'ts-mt', and 'ts_mt' normalize to the same key, but
    'tscsfit' does NOT normalize to 'tsmt': tscsFit is one command within the
    TSMT package, not a synonym for the whole package (see
    planning/v0.23.0-gauss-package-inspection-implementation.md's Package
    Discovery Strategy).
    """
    return _SEPARATOR_RE.sub("", name.strip().lower())


def _derive_search_paths(executable_path: str | None) -> list[str]:
    """Conservative, documented-non-exhaustive sibling-directory heuristic.

    Looks for 'pkgs'/'packages' directories next to the selected GAUSS
    executable. This is a starting set, not a confirmed-exhaustive list of
    real GAUSS package directory layouts -- callers should supply
    package_search_paths directly for reliable results.
    """
    if not executable_path:
        return []
    parent = Path(executable_path).parent
    return [str(parent / "pkgs"), str(parent / "packages")]


def _default_accessible(path_str: str) -> Any:
    if _env_check is not None:
        return _env_check.check_accessible(path_str)
    try:
        p = Path(path_str)
        if not p.exists() or not p.is_file():
            return False
        if os.name == "nt":
            return True
        return os.access(str(p), os.X_OK)
    except OSError:
        return "unknown"


def _default_list_dir(path_str: str) -> Any:
    """Read-only directory listing.

    Returns a list of entry names, None if the path does not exist or is not
    a directory, or "unknown" if it exists but cannot be read (e.g.
    permissions). Never writes, executes, or imports anything found.
    """
    try:
        p = Path(path_str)
        if not p.exists() or not p.is_dir():
            return None
        return [entry.name for entry in p.iterdir()]
    except OSError:
        return "unknown"


def _default_env_detect_fn() -> Callable[..., dict[str, Any]] | None:
    if _env_check is None:
        return None

    def _fn(platform_hint: str | None = None) -> dict[str, Any]:
        return _env_check.detect_environment(platform_hint=platform_hint)

    return _fn


def _resolve_environment_context(
    *,
    environment_check_result: dict[str, Any] | None,
    executable_path: str | None,
    gauss_version: str | None,
    platform_hint: str | None,
    strict: bool,
    path_exists_fn: Callable[[str], bool],
    accessibility_fn: Callable[[str], Any],
    env_detect_fn: Callable[..., dict[str, Any]] | None,
) -> tuple[str, str | None, str | None, list[str]]:
    """Return (environment_status, executable_path, gauss_version, warnings).

    Precedence (see planning/v0.23.0-...md's Proposed CLI): explicit
    executable_path/gauss_version arguments, then environment_check_result,
    then environment detection (unless strict), then unavailable.
    """
    # Step 1: explicit executable path / GAUSS version -- highest priority.
    # Never combined with environment_check_result, so context is never mixed.
    if executable_path:
        if not path_exists_fn(executable_path):
            return (
                "not_found",
                None,
                None,
                ["The provided executable_path does not exist; it could not be used as package inspection context."],
            )
        accessible = accessibility_fn(executable_path)
        if accessible is not True:
            return (
                "inaccessible",
                None,
                None,
                ["The provided executable_path exists but could not be confirmed accessible."],
            )
        return "found", executable_path, gauss_version, []

    if gauss_version:
        # A version with no path: presence cannot be confirmed, so the
        # environment is not treated as "found", but the requested version is
        # still carried through for reporting rather than discarded.
        return (
            "unknown",
            None,
            gauss_version,
            [
                "A gauss_version was provided without an executable_path, so GAUSS presence could not be "
                "confirmed; package inspection could not proceed."
            ],
        )

    # Step 2: environment_check_result.
    if environment_check_result:
        detection_status = environment_check_result.get("detection_status", "unknown")
        if detection_status not in _ENV_STATUS_ENUM:
            detection_status = "unknown"
        if detection_status == "found":
            return (
                "found",
                environment_check_result.get("executable_path"),
                environment_check_result.get("version"),
                [],
            )
        return (
            detection_status,
            None,
            None,
            ["The supplied environment_check_result did not indicate a found GAUSS environment."],
        )

    # Step 3: strict mode with no context -- do not call environment detection.
    if strict:
        return (
            "unknown",
            None,
            None,
            [
                "strict mode was requested without environment_check_result or a direct executable_path/"
                "gauss_version, so no environment detection was attempted."
            ],
        )

    # Step 4: environment detection fallback, if feasible.
    detect_fn = env_detect_fn if env_detect_fn is not None else _default_env_detect_fn()
    if detect_fn is None:
        return (
            "unknown",
            None,
            None,
            ["No environment context was provided and GAUSS environment detection was not available to call."],
        )

    env_result = detect_fn(platform_hint=platform_hint)
    detection_status = env_result.get("detection_status", "unknown")
    if detection_status not in _ENV_STATUS_ENUM:
        detection_status = "unknown"
    if detection_status == "found":
        return (
            "found",
            env_result.get("executable_path"),
            env_result.get("version"),
            ["Environment context was obtained by calling GAUSS environment detection automatically."],
        )
    return (
        detection_status,
        None,
        None,
        ["GAUSS environment detection was attempted automatically but did not return a found environment."],
    )


def _inspect_found_environment(
    *,
    executable_path: str | None,
    gauss_version: str | None,
    requested: list[str],
    caller_paths: list[str],
    allow_metadata_query: bool,
    base_warnings: list[str],
    list_dir_fn: Callable[[str], Any],
) -> dict[str, Any]:
    warnings = list(base_warnings)

    # Caller-supplied paths are authoritative: checked unconditionally, and a
    # missing/inaccessible one reduces confidence (incomplete_scope).
    considered_paths: list[str] = []
    seen: set[str] = set()
    for p in caller_paths:
        if p not in seen:
            seen.add(p)
            considered_paths.append(p)

    scan_results: dict[str, Any] = {}
    for p in considered_paths:
        entries = list_dir_fn(p)
        if entries is None:
            scan_results[p] = "missing"
            warnings.append(f"Package search path '{p}' does not exist.")
        elif entries == "unknown":
            scan_results[p] = "inaccessible"
            warnings.append(f"Package search path '{p}' could not be accessed.")
        else:
            scan_results[p] = list(entries)

    # Derived heuristic paths are best-effort guesses, not confirmed real
    # package locations: silently skip ones that don't exist (no warning, no
    # effect on incomplete_scope), the same pattern
    # gauss_environment_check.py's discover_common_location_candidates uses
    # for its own common-location guesses.
    for p in _derive_search_paths(executable_path):
        if p in seen:
            continue
        seen.add(p)
        entries = list_dir_fn(p)
        if isinstance(entries, list):
            considered_paths.append(p)
            scan_results[p] = entries

    if not considered_paths:
        warnings.append("No package search paths were available to check.")

    accessible_paths = [p for p, v in scan_results.items() if isinstance(v, list)]
    incomplete_scope = any(v in ("missing", "inaccessible") for v in scan_results.values())

    # Flat candidate index: normalized name -> (raw_name, full_path, is_dir).
    candidate_index: dict[str, tuple[str, str, bool]] = {}
    for p in accessible_paths:
        for name in scan_results[p]:
            full_path = str(Path(p) / name)
            is_dir = Path(full_path).is_dir()
            candidate_index.setdefault(_normalize_name(name), (name, full_path, is_dir))

    packages: list[dict[str, Any]] = []
    missing_packages: list[str] = []
    unknown_packages: list[str] = []

    if requested:
        for req in requested:
            match = candidate_index.get(_normalize_name(req))
            if match:
                raw_name, full_path, is_dir = match
                packages.append(
                    {
                        "name": req,
                        "installed": True,
                        "version": None,
                        "version_known": False,
                        "source": "filesystem_scan",
                        "path": full_path,
                        "package_type": "application_module" if is_dir else "package",
                        "notes": [f"Matched directory entry '{raw_name}' in '{Path(full_path).parent}'."],
                    }
                )
            elif accessible_paths and not incomplete_scope:
                packages.append(
                    {
                        "name": req,
                        "installed": False,
                        "version": None,
                        "version_known": False,
                        "source": "filesystem_scan",
                        "path": None,
                        "package_type": "unknown",
                        "notes": [f"'{req}' was not found in any fully-scanned package search path."],
                    }
                )
                missing_packages.append(req)
            else:
                packages.append(
                    {
                        "name": req,
                        "installed": "unknown",
                        "version": None,
                        "version_known": False,
                        "source": "filesystem_scan" if accessible_paths else "requested_only",
                        "path": None,
                        "package_type": "unknown",
                        "notes": [
                            "Package search scope was incomplete or unavailable, so status could not be "
                            "conclusively determined."
                        ],
                    }
                )
                unknown_packages.append(req)

        status = "partial" if unknown_packages else "complete"
    else:
        # Conservative default: without requested_packages, broad discovery is
        # intentionally not performed (privacy-conscious, avoids overclaiming),
        # so status remains unknown rather than complete or partial.
        status = "unknown"
        warnings.append(
            "No requested_packages were supplied; broad package discovery is intentionally not performed, "
            "so package status remains unknown."
        )

    if allow_metadata_query:
        warnings.append(_METADATA_QUERY_WARNING)

    if status == "complete":
        if missing_packages:
            operating_mode = "verified_knowledge"
            can_assume: Any = False
            next_steps = [
                "Continue in Advisory Mode; commands depending on the missing package(s) should be treated "
                "as unavailable until confirmed otherwise.",
                "Verify whether the missing package(s) are actually required, and check licensing/"
                "installation status if so.",
                "Provide package_search_paths directly if a missing package is installed in a nonstandard "
                "location.",
            ]
        else:
            operating_mode = "execution_candidate"
            can_assume = True
            next_steps = [
                "Verify exact command syntax against GAUSS Language Expert evidence before treating any "
                "matched package's commands as confirmed usable.",
                "Confirm a future execution tool is available and the user permits execution before "
                "entering Execution Mode.",
            ]
    elif status == "partial":
        operating_mode = "verified_knowledge"
        can_assume = "unknown"
        next_steps = [
            "Provide additional package_search_paths to resolve the remaining unknown package(s).",
            "Inspect the unresolved package(s) manually if their availability is important before proceeding.",
        ]
    else:  # unknown
        operating_mode = "advisory"
        can_assume = "unknown"
        next_steps = [
            "Provide requested_packages and/or package_search_paths for a more conclusive result.",
            "Use official/verified GAUSS documentation to check package requirements while status remains "
            "unresolved.",
        ]

    inspection_method = "filesystem_scan" if considered_paths else ("requested_only" if requested else "not_checked")

    return _build_result(
        checked=True,
        environment_status="found",
        executable_path=executable_path,
        gauss_version=gauss_version,
        package_inspection_status=status,
        packages=packages,
        requested_packages=requested,
        missing_packages=missing_packages,
        unknown_packages=unknown_packages,
        package_search_paths=considered_paths,
        inspection_method=inspection_method,
        operating_mode_recommendation=operating_mode,
        can_assume_package_availability=can_assume,
        warnings=warnings,
        errors=[],
        next_steps=next_steps,
    )


def _build_result(
    *,
    checked: bool,
    environment_status: str,
    executable_path: str | None,
    gauss_version: str | None,
    package_inspection_status: str,
    packages: list[dict[str, Any]],
    requested_packages: list[str],
    missing_packages: list[str],
    unknown_packages: list[str],
    package_search_paths: list[str],
    inspection_method: str,
    operating_mode_recommendation: str,
    can_assume_package_availability: Any,
    warnings: list[str],
    errors: list[str],
    next_steps: list[str],
) -> dict[str, Any]:
    return {
        "checked": checked,
        "environment_status": environment_status,
        "executable_path": executable_path,
        "gauss_version": gauss_version,
        "package_inspection_status": package_inspection_status,
        "packages": packages,
        "requested_packages": requested_packages,
        "missing_packages": missing_packages,
        "unknown_packages": unknown_packages,
        "package_search_paths": package_search_paths,
        "inspection_method": inspection_method,
        "operating_mode_recommendation": operating_mode_recommendation,
        "can_assume_package_availability": can_assume_package_availability,
        "warnings": warnings,
        "errors": errors,
        "next_steps": next_steps,
    }


def inspect_packages(
    environment_check_result: dict[str, Any] | None = None,
    executable_path: str | None = None,
    gauss_version: str | None = None,
    platform_hint: str | None = None,
    requested_packages: list[str] | None = None,
    package_search_paths: list[str] | None = None,
    allow_metadata_query: bool = False,
    inspection_timeout_seconds: float | None = None,
    strict: bool = False,
    *,
    path_exists_fn: Callable[[str], bool] | None = None,
    accessibility_fn: Callable[[str], Any] | None = None,
    list_dir_fn: Callable[[str], Any] | None = None,
    env_detect_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run read-only GAUSS package inspection and return a schema-shaped result.

    `path_exists_fn`, `accessibility_fn`, `list_dir_fn`, and `env_detect_fn` are
    injectable for testing (see `_run_self_tests`) so inspection logic can be
    exercised without touching a real filesystem or depending on a real GAUSS
    installation. `inspection_timeout_seconds` is accepted for input-contract
    completeness but is not currently enforced (mirrors
    scripts/gauss_environment_check.py's `working_directory` precedent).
    """
    del inspection_timeout_seconds
    path_exists_fn = path_exists_fn or (lambda p: Path(p).exists())
    accessibility_fn = accessibility_fn or _default_accessible
    list_dir_fn = list_dir_fn or _default_list_dir

    requested = list(requested_packages) if requested_packages else []

    try:
        env_status, env_exec_path, env_version, env_warnings = _resolve_environment_context(
            environment_check_result=environment_check_result,
            executable_path=executable_path,
            gauss_version=gauss_version,
            platform_hint=platform_hint,
            strict=strict,
            path_exists_fn=path_exists_fn,
            accessibility_fn=accessibility_fn,
            env_detect_fn=env_detect_fn,
        )
    except Exception as exc:  # noqa: BLE001 -- inspection must never crash the caller
        return _build_result(
            checked=True,
            environment_status="error",
            executable_path=None,
            gauss_version=None,
            package_inspection_status="error",
            packages=[],
            requested_packages=requested,
            missing_packages=[],
            unknown_packages=[],
            package_search_paths=[],
            inspection_method="error",
            operating_mode_recommendation="advisory",
            can_assume_package_availability="unknown",
            warnings=[],
            errors=[f"Unexpected error resolving environment context: {exc}"],
            next_steps=[
                "Continue in Advisory Mode; this error does not block code writing, explanation, review, "
                "documentation, education, or product reasoning."
            ],
        )

    warnings = list(env_warnings)

    if env_status != "found":
        warnings.append("Package inspection could not be performed because the GAUSS environment is not confirmed found.")
        if allow_metadata_query:
            warnings.append(_METADATA_QUERY_WARNING)
        return _build_result(
            checked=True,
            environment_status=env_status,
            executable_path=None,
            gauss_version=None,
            package_inspection_status="unavailable",
            packages=[],
            requested_packages=requested,
            missing_packages=[],
            unknown_packages=list(requested),
            package_search_paths=[],
            inspection_method="not_checked",
            operating_mode_recommendation="advisory",
            can_assume_package_availability="unknown",
            warnings=warnings,
            errors=[],
            next_steps=[
                "Run GAUSS environment detection (gauss_environment_check) and confirm a found result before "
                "requesting package inspection.",
                "Provide executable_path directly if GAUSS is installed in a nonstandard location.",
                "Continue in Advisory Mode; code generation, explanation, and review remain fully available.",
            ],
        )

    caller_paths = list(package_search_paths) if package_search_paths else []
    try:
        return _inspect_found_environment(
            executable_path=env_exec_path,
            gauss_version=env_version,
            requested=requested,
            caller_paths=caller_paths,
            allow_metadata_query=allow_metadata_query,
            base_warnings=warnings,
            list_dir_fn=list_dir_fn,
        )
    except Exception as exc:  # noqa: BLE001 -- inspection must never crash the caller
        return _build_result(
            checked=True,
            environment_status=env_status,
            executable_path=env_exec_path,
            gauss_version=env_version,
            package_inspection_status="error",
            packages=[],
            requested_packages=requested,
            missing_packages=[],
            unknown_packages=[],
            package_search_paths=[],
            inspection_method="error",
            operating_mode_recommendation="advisory",
            can_assume_package_availability="unknown",
            warnings=warnings,
            errors=[f"Unexpected package inspection error: {exc}"],
            next_steps=[
                "Continue in Advisory Mode; this error does not block code writing, explanation, review, "
                "documentation, education, or product reasoning."
            ],
        )


def validate_against_schema(result: dict[str, Any], schema_path: Path) -> list[str]:
    """Validate a result dict against the schema. Returns jsonschema error messages.

    Returns a single explanatory item (not an exception) if jsonschema is not
    installed, so inspection results remain usable without the optional
    validation dependency.
    """
    try:
        from jsonschema import Draft202012Validator
    except ModuleNotFoundError:
        return [
            "jsonschema is not installed; skipped schema validation. "
            "Install with: python -m pip install jsonschema"
        ]

    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(result), key=lambda e: list(e.path))
    messages: list[str] = []
    for error in errors:
        path = "$"
        if error.path:
            path += "".join(f"[{part!r}]" for part in error.path)
        messages.append(f"{path}: {error.message}")
    return messages


def print_human(result: dict[str, Any]) -> None:
    print(f"Package inspection status:      {result['package_inspection_status']}")
    print(f"Operating mode recommendation:  {result['operating_mode_recommendation']}")
    print(f"Environment status:             {result['environment_status']}")
    print(f"Executable path / GAUSS version: {result['executable_path']} / {result['gauss_version']}")
    print(f"Can assume package availability: {result['can_assume_package_availability']}")
    print(f"Inspection method:              {result['inspection_method']}")

    if result["packages"]:
        print("\nPackages:")
        for pkg in result["packages"]:
            print(f"  - {pkg['name']}: installed={pkg['installed']} (source={pkg['source']}, path={pkg['path']})")

    if result["missing_packages"]:
        print(f"\nMissing packages: {', '.join(result['missing_packages'])}")

    if result["unknown_packages"]:
        print(f"Unknown packages: {', '.join(result['unknown_packages'])}")

    if result["package_search_paths"]:
        print("\nSearch paths considered:")
        for p in result["package_search_paths"]:
            print(f"  - {p}")

    if result["warnings"]:
        print("\nWarnings:")
        for w in result["warnings"]:
            print(f"  - {w}")

    if result["errors"]:
        print("\nErrors:")
        for e in result["errors"]:
            print(f"  - {e}")

    if result["next_steps"]:
        print("\nNext steps:")
        for n in result["next_steps"]:
            print(f"  - {n}")


def _run_self_tests() -> int:
    """Lightweight built-in test suite for the pure inspection logic.

    No formal tests/ directory exists in this repository yet (matches
    scripts/gauss_environment_check.py's precedent), so this runs via
    `python scripts/gauss_package_inspection.py --self-test`. Every case uses
    injected synthetic fixtures; none depend on a real GAUSS installation.
    """
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    # 1. Environment not found -> unavailable, advisory.
    result = inspect_packages(environment_check_result={"detection_status": "not_found"})
    check(
        "environment not found -> unavailable/advisory",
        result["package_inspection_status"] == "unavailable" and result["operating_mode_recommendation"] == "advisory",
    )

    # 2. Strict with no context -> unavailable/advisory, detection never called.
    called = {"value": False}

    def _should_not_be_called(platform_hint: str | None = None) -> dict[str, Any]:
        called["value"] = True
        return {"detection_status": "found"}

    result = inspect_packages(strict=True, env_detect_fn=_should_not_be_called)
    check(
        "strict with no context -> unavailable/advisory, no detection call",
        result["package_inspection_status"] == "unavailable"
        and result["operating_mode_recommendation"] == "advisory"
        and not called["value"],
    )

    found_env = {"detection_status": "found", "executable_path": "/example/gauss26/tgauss", "version": "GAUSS 26"}

    def list_dir_tsmt_only(path_str: str) -> Any:
        if path_str == "/example/gauss26/pkgs":
            return ["tsmt"]
        return None

    # 3. Requested package found in synthetic package_search_path.
    result = inspect_packages(
        environment_check_result=found_env,
        requested_packages=["tsmt"],
        package_search_paths=["/example/gauss26/pkgs"],
        list_dir_fn=list_dir_tsmt_only,
    )
    check(
        "requested package found -> complete, installed true",
        result["package_inspection_status"] == "complete" and result["packages"][0]["installed"] is True,
    )
    check("found package -> execution_candidate", result["operating_mode_recommendation"] == "execution_candidate")

    # 4. Requested package missing when synthetic search scope is complete.
    def list_dir_empty(path_str: str) -> Any:
        if path_str == "/example/gauss26/pkgs":
            return []
        return None

    result = inspect_packages(
        environment_check_result=found_env,
        requested_packages=["tsmt"],
        package_search_paths=["/example/gauss26/pkgs"],
        list_dir_fn=list_dir_empty,
    )
    check(
        "requested package missing, complete scope -> complete, missing",
        result["package_inspection_status"] == "complete" and result["missing_packages"] == ["tsmt"],
    )
    check(
        "missing package does not imply GAUSS missing",
        result["environment_status"] == "found",
    )

    # 5. Requested package unknown when no reliable path exists.
    result = inspect_packages(
        environment_check_result={"detection_status": "found", "executable_path": None, "version": "GAUSS 26"},
        requested_packages=["tsmt"],
        list_dir_fn=list_dir_empty,
    )
    check(
        "no reliable search path -> unknown, partial",
        result["package_inspection_status"] == "partial" and result["unknown_packages"] == ["tsmt"],
    )

    # 6. Partial result when one supplied search path is missing/inaccessible.
    def list_dir_mixed(path_str: str) -> Any:
        if path_str == "/exists":
            return ["tsmt"]
        if path_str == "/missing":
            return None
        return None

    result = inspect_packages(
        environment_check_result=found_env,
        requested_packages=["tsmt", "other"],
        package_search_paths=["/exists", "/missing"],
        list_dir_fn=list_dir_mixed,
    )
    check(
        "one missing search path -> partial with matched + unknown package",
        result["package_inspection_status"] == "partial"
        and "tsmt" not in result["unknown_packages"]
        and result["unknown_packages"] == ["other"],
    )

    # 7. Selected GAUSS 26 context carried through by default.
    result = inspect_packages(environment_check_result=found_env, list_dir_fn=list_dir_empty)
    check("GAUSS 26 context carried through", result["gauss_version"] == "GAUSS 26")

    # 8. User-selected GAUSS 25 context carried through via direct args.
    result = inspect_packages(
        executable_path="/preferred/gauss25/tgauss",
        gauss_version="GAUSS 25",
        path_exists_fn=lambda p: p == "/preferred/gauss25/tgauss",
        accessibility_fn=lambda p: True,
        list_dir_fn=list_dir_empty,
    )
    check(
        "direct executable_path/gauss_version override carried through",
        result["gauss_version"] == "GAUSS 25" and result["executable_path"] == "/preferred/gauss25/tgauss",
    )

    # 9. No cross-version mixing: direct args take precedence, not merged with
    # a differing environment_check_result.
    result = inspect_packages(
        executable_path="/preferred/gauss24/tgauss",
        environment_check_result={"detection_status": "found", "executable_path": "/other/gauss26/tgauss", "version": "GAUSS 26"},
        path_exists_fn=lambda p: p == "/preferred/gauss24/tgauss",
        accessibility_fn=lambda p: True,
        list_dir_fn=list_dir_empty,
    )
    check(
        "explicit executable_path is not mixed with environment_check_result",
        result["executable_path"] == "/preferred/gauss24/tgauss" and result["gauss_version"] is None,
    )

    # 10. (covered above alongside case 4) missing package does not imply GAUSS missing.

    # 11. Installed package does not imply execution.
    result = inspect_packages(
        environment_check_result=found_env,
        requested_packages=["tsmt"],
        package_search_paths=["/example/gauss26/pkgs"],
        list_dir_fn=list_dir_tsmt_only,
    )
    check(
        "installed package result still requires future execution confirmation",
        any("execution tool" in step and "permit" in step for step in result["next_steps"]),
    )

    # 12. Metadata query flag accepted but does not invoke GAUSS.
    result = inspect_packages(
        environment_check_result=found_env,
        requested_packages=["tsmt"],
        package_search_paths=["/example/gauss26/pkgs"],
        list_dir_fn=list_dir_tsmt_only,
        allow_metadata_query=True,
    )
    check("metadata query warning present", _METADATA_QUERY_WARNING in result["warnings"])

    # 13. Representative outputs validate against schema when jsonschema is available.
    schema_path = default_schema_path()
    if schema_path.is_file():

        def list_dir_error(path_str: str) -> Any:
            raise ValueError("synthetic inspection failure")

        representative = {
            "complete": inspect_packages(
                environment_check_result=found_env,
                requested_packages=["tsmt"],
                package_search_paths=["/example/gauss26/pkgs"],
                list_dir_fn=list_dir_tsmt_only,
            ),
            "partial": inspect_packages(
                environment_check_result=found_env,
                requested_packages=["tsmt", "other"],
                package_search_paths=["/exists", "/missing"],
                list_dir_fn=list_dir_mixed,
            ),
            "unavailable": inspect_packages(environment_check_result={"detection_status": "not_found"}),
            "unknown": inspect_packages(environment_check_result=found_env, list_dir_fn=list_dir_empty),
            "error": inspect_packages(
                environment_check_result=found_env,
                requested_packages=["tsmt"],
                package_search_paths=["/example/gauss26/pkgs"],
                list_dir_fn=list_dir_error,
            ),
        }
        for label, res in representative.items():
            errors = validate_against_schema(res, schema_path)
            missing_dependency = len(errors) == 1 and errors[0].startswith("jsonschema is not installed")
            if errors and not missing_dependency:
                failures.append(f"schema validation failed for '{label}' result: {errors}")

    if failures:
        print(f"SELF-TEST FAILED ({len(failures)} issue(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("SELF-TEST PASSED: all checks succeeded.")
    return 0


def _split_comma_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect which GAUSS packages/application modules appear available in a "
            "detected GAUSS environment. Read-only: does not run user GAUSS code, does "
            "not install packages, and does not activate Execution Mode. See "
            "tools/gauss_package_inspection.md for the full contract."
        )
    )
    parser.add_argument(
        "--environment-result",
        default=None,
        help="Path to a JSON file containing a gauss_environment_check result to use as context.",
    )
    parser.add_argument(
        "--executable-path",
        default=None,
        help="Directly select the GAUSS executable/environment context, bypassing --environment-result.",
    )
    parser.add_argument(
        "--gauss-version",
        default=None,
        help="Directly select the GAUSS version context, e.g. 'GAUSS 25'.",
    )
    parser.add_argument(
        "--platform-hint",
        default=None,
        choices=["windows", "macos", "linux", "wsl"],
        help="Passed through to environment detection if it is called as a fallback.",
    )
    parser.add_argument(
        "--requested-package",
        action="append",
        default=[],
        dest="requested_package",
        help="A specific package/module name to inspect. May be repeated.",
    )
    parser.add_argument(
        "--requested-packages",
        default=None,
        help="Comma-separated package/module names to inspect.",
    )
    parser.add_argument(
        "--package-search-path",
        action="append",
        default=[],
        dest="package_search_path",
        help="A read-only directory to check for packages. May be repeated.",
    )
    parser.add_argument(
        "--allow-metadata-query",
        action="store_true",
        help=(
            "Permit a minimal package metadata query. No safe GAUSS metadata-query command "
            "is confirmed yet, so this currently only adds an explanatory warning."
        ),
    )
    parser.add_argument("--inspection-timeout-seconds", type=float, default=None)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Do not fall back to automatic environment detection if no context is supplied.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full structured JSON result. Default output is a short human-readable summary.",
    )
    parser.add_argument(
        "--validate-schema",
        action="store_true",
        help="Validate the result against schemas/gauss_package_inspection.schema.json before printing.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the built-in test suite (no real GAUSS installation required) and exit.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.self_test:
        return _run_self_tests()

    environment_check_result = None
    if args.environment_result:
        try:
            with open(args.environment_result, "r", encoding="utf-8") as f:
                environment_check_result = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Could not read --environment-result file '{args.environment_result}': {exc}", file=sys.stderr)
            return 2

    requested_packages: list[str] = list(args.requested_package)
    if args.requested_packages:
        for name in _split_comma_list(args.requested_packages):
            if name not in requested_packages:
                requested_packages.append(name)

    result = inspect_packages(
        environment_check_result=environment_check_result,
        executable_path=args.executable_path,
        gauss_version=args.gauss_version,
        platform_hint=args.platform_hint,
        requested_packages=requested_packages or None,
        package_search_paths=args.package_search_path or None,
        allow_metadata_query=args.allow_metadata_query,
        inspection_timeout_seconds=args.inspection_timeout_seconds,
        strict=args.strict,
    )

    if args.validate_schema:
        schema_errors = validate_against_schema(result, default_schema_path())
        missing_dependency = len(schema_errors) == 1 and schema_errors[0].startswith("jsonschema is not installed")
        if schema_errors and missing_dependency:
            result["warnings"].append(schema_errors[0])
        elif schema_errors:
            if args.json:
                print(json.dumps({"result": result, "schema_errors": schema_errors}, indent=2))
            else:
                print("Schema validation FAILED:")
                for msg in schema_errors:
                    print(f"  - {msg}")
            return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
