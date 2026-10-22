"""Detect whether GAUSS is installed or discoverable on this machine.

This is a read-only environment inspection helper implementing the contract
defined in tools/gauss_environment_check.md and validated against
schemas/gauss_environment_check.schema.json.

It does not run user GAUSS code, does not inspect installed GAUSS packages,
does not execute statistical analysis, does not generate reports, and does
not activate Execution Mode -- a "found" result is only an execution-candidate
signal (per tools/gauss_environment_check.md's Operating Mode Relationship
section), not proof that execution has occurred or is safe.

When multiple GAUSS installations are detected, this helper defaults to the
highest/newest detected version unless the caller provides a preferred
executable path, a preferred version, or requests strict mode -- see
planning/v0.21.0-gauss-environment-detection-implementation.md's "Default
Version Selection Rule".

No safe, confirmed GAUSS version-query command-line flag is documented in
this repository yet, so --allow-version-query does not actually invoke any
executable here; it is accepted for forward compatibility with the input
contract and currently only adds an explanatory warning. See
tools/gauss_environment_check.md's "Optional version query" section.

environment_overrides (from the tool spec's input contract) is deliberately
not implemented here -- it is deferred, since safely simulating an alternate
environment without risking a misleading result is nontrivial.
"""

from __future__ import annotations

import argparse
import json
import os
import platform as platform_module
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

PLAUSIBLE_EXECUTABLE_NAMES = [
    "tgauss",
    "tgauss.exe",
    "gauss",
    "gauss.exe",
    "wgauss",
    "wgauss.exe",
]
# These names are plausible candidates based on common GAUSS distributions,
# not a confirmed-exhaustive list. Real executable naming should be verified
# against actual installations as this helper matures.

VERSION_RE = re.compile(r"gauss[\s_-]?(\d{2}(?:\.\d+)?)", re.IGNORECASE)

COMMON_LOCATION_TEMPLATES: dict[str, list[str]] = {
    "windows": [
        r"C:\Program Files\GAUSS{version}\tgauss.exe",
        r"C:\Program Files\GAUSS\tgauss.exe",
        r"C:\gauss{version}\tgauss.exe",
    ],
    # v0.89.0 (planning v0.89 §9.3): Aptech's developers advise calling the
    # `tgauss` script in the user's GAUSS home folder on macOS, not the binary
    # inside the app bundle, because the script sets up the environment. The
    # earlier guesses (`/Applications/GAUSS{version}.app/Contents/MacOS/tgauss`)
    # pointed at exactly that binary, and the home folder's location is the
    # user's choice, so macOS now offers no guessed location: PATH lookup and
    # the `gauss-executable` setting are the only sources.
    "macos": [],
    "linux": [
        "/opt/gauss{version}/tgauss",
        "/usr/local/gauss{version}/tgauss",
        "/opt/gauss/tgauss",
    ],
}
COMMON_LOCATION_VERSIONS = ["26", "25", "24"]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_schema_path() -> Path:
    return repo_root() / "schemas" / "gauss_environment_check.schema.json"


def parse_gauss_version(text: str) -> str | None:
    """Extract a GAUSS version like '26' or '25.1' from a path or name string."""
    match = VERSION_RE.search(text)
    if not match:
        return None
    return match.group(1)


def version_sort_key(version: str | None) -> float:
    if version is None:
        return -1.0
    try:
        return float(version)
    except ValueError:
        return -1.0


def make_candidate(path: str, source: str, accessible: Any, notes: list[str]) -> dict[str, Any]:
    return {"path": path, "source": source, "accessible": accessible, "notes": notes}


def check_accessible(path_str: str) -> Any:
    """Read-only accessibility check: exists, is a file, and (on POSIX) executable."""
    try:
        p = Path(path_str)
        if not p.exists():
            return False
        if not p.is_file():
            return False
        if os.name == "nt":
            # Existence is the meaningful signal on Windows; the POSIX executable
            # bit does not apply.
            return True
        return os.access(str(p), os.X_OK)
    except OSError:
        return "unknown"


def detect_platform(platform_hint: str | None) -> str:
    if platform_hint:
        return platform_hint
    system = platform_module.system().lower()
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"
    if system == "linux":
        try:
            version_info = Path("/proc/version").read_text(encoding="utf-8", errors="ignore").lower()
            if "microsoft" in version_info:
                return "wsl"
        except OSError:
            pass
        return "linux"
    return "unknown"


def discover_path_lookup_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name in PLAUSIBLE_EXECUTABLE_NAMES:
        found = shutil.which(name)
        if found and found not in seen:
            seen.add(found)
            candidates.append(make_candidate(found, "path_lookup", check_accessible(found), []))
    return candidates


def discover_common_location_candidates(plat: str) -> list[dict[str, Any]]:
    if plat in ("wsl", "unknown") or plat not in COMMON_LOCATION_TEMPLATES:
        # Conservative: no confirmed common paths for WSL/containers/unsupported
        # platforms yet, so return nothing rather than guess.
        return []
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for template in COMMON_LOCATION_TEMPLATES[plat]:
        path_strs = (
            [template.format(version=v) for v in COMMON_LOCATION_VERSIONS]
            if "{version}" in template
            else [template]
        )
        for path_str in path_strs:
            if path_str in seen:
                continue
            if Path(path_str).exists():
                seen.add(path_str)
                candidates.append(make_candidate(path_str, "common_location_scan", check_accessible(path_str), []))
    return candidates


def default_discovery(plat: str) -> list[dict[str, Any]]:
    candidates = discover_path_lookup_candidates() + discover_common_location_candidates(plat)
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for c in candidates:
        if c["path"] not in seen:
            seen.add(c["path"])
            deduped.append(c)
    return deduped


def attempt_version_query(executable_path: str, timeout_seconds: float) -> tuple[str | None, list[str]]:
    """Optional minimal version query -- currently a documented no-op.

    No confirmed-safe GAUSS version-query flag exists in this repository yet,
    so this deliberately does not invoke the executable. It is the single,
    clearly-labeled extension point a future implementation would fill in
    once a safe flag is confirmed.
    """
    del executable_path, timeout_seconds  # unused until a safe flag is confirmed
    return None, [
        "Version query was requested via allow_version_query, but no safe GAUSS "
        "version-query flag is confirmed yet; the executable was not invoked."
    ]


def _build_result(
    *,
    checked: bool,
    installed: Any,
    accessible: Any,
    executable_path: str | None,
    executable_candidates: list[dict[str, Any]],
    version: str | None,
    version_known: bool,
    platform: str | None,
    detection_method: str,
    detection_status: str,
    operating_mode_recommendation: str,
    can_execute_gauss_code: Any,
    warnings: list[str],
    errors: list[str],
    next_steps: list[str],
) -> dict[str, Any]:
    return {
        "checked": checked,
        "installed": installed,
        "accessible": accessible,
        "executable_path": executable_path,
        "executable_candidates": executable_candidates,
        "version": version,
        "version_known": version_known,
        "platform": platform,
        "detection_method": detection_method,
        "detection_status": detection_status,
        "operating_mode_recommendation": operating_mode_recommendation,
        "can_execute_gauss_code": can_execute_gauss_code,
        "warnings": warnings,
        "errors": errors,
        "next_steps": next_steps,
    }


_NO_EXECUTION_WARNING = "No GAUSS code was executed by this detection result."
_NO_PACKAGE_WARNING = "Package availability was not checked by this detection result."
_FUTURE_STEPS = [
    "Run package inspection (not yet implemented) to determine which GAUSS packages are installed.",
    "Confirm a future execution tool is available and the user permits execution before entering Execution Mode.",
]


def detect_environment(
    preferred_executable_path: str | None = None,
    preferred_version: str | None = None,
    working_directory: str | None = None,
    platform_hint: str | None = None,
    allow_version_query: bool = False,
    detection_timeout_seconds: float = 5.0,
    strict: bool = False,
    *,
    path_exists_fn: Callable[[str], bool] | None = None,
    accessibility_fn: Callable[[str], Any] | None = None,
    discovery_fn: Callable[[str], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Run read-only GAUSS environment detection and return a schema-shaped result.

    `path_exists_fn`, `accessibility_fn`, and `discovery_fn` are injectable for
    testing (see `_run_self_tests`) so detection logic can be exercised without
    touching a real filesystem or depending on a real GAUSS installation.
    `working_directory` is accepted for input-contract completeness but is not
    currently used to alter detection.
    """
    del working_directory
    path_exists_fn = path_exists_fn or (lambda p: Path(p).exists())
    accessibility_fn = accessibility_fn or check_accessible
    discovery_fn = discovery_fn or default_discovery

    plat = detect_platform(platform_hint)

    try:
        # Step 1: user-provided executable path -- highest priority, never
        # silently falls back to another candidate on failure.
        if preferred_executable_path:
            if not path_exists_fn(preferred_executable_path):
                return _build_result(
                    checked=True,
                    installed=False,
                    accessible="unknown",
                    executable_path=None,
                    executable_candidates=[],
                    version=None,
                    version_known=False,
                    platform=plat,
                    detection_method="user_provided_path",
                    detection_status="not_found",
                    operating_mode_recommendation="advisory",
                    can_execute_gauss_code=False,
                    warnings=[],
                    errors=[],
                    next_steps=[
                        "Confirm the preferred_executable_path is correct.",
                        "Provide a different path, or omit preferred_executable_path to allow discovery.",
                    ],
                )

            accessible = accessibility_fn(preferred_executable_path)
            candidate = make_candidate(preferred_executable_path, "user_provided_path", accessible, [])

            if accessible is not True:
                return _build_result(
                    checked=True,
                    installed="unknown",
                    accessible=accessible if accessible in (False, "unknown") else "unknown",
                    executable_path=None,
                    executable_candidates=[candidate],
                    version=None,
                    version_known=False,
                    platform=plat,
                    detection_method="user_provided_path",
                    detection_status="inaccessible",
                    operating_mode_recommendation="advisory",
                    can_execute_gauss_code="unknown",
                    warnings=[
                        "A user-provided GAUSS executable path exists but could not be confirmed as accessible.",
                        _NO_EXECUTION_WARNING,
                    ],
                    errors=[],
                    next_steps=[
                        "Check file and directory permissions for the provided path.",
                        "Confirm a GAUSS license is active and reachable if permissions look correct.",
                    ],
                )

            version = parse_gauss_version(preferred_executable_path)
            version_known = version is not None
            version_warnings: list[str] = []
            if allow_version_query and not version_known:
                queried_version, query_warnings = attempt_version_query(
                    preferred_executable_path, detection_timeout_seconds
                )
                version_warnings.extend(query_warnings)
                if queried_version:
                    version = queried_version
                    version_known = True

            return _build_result(
                checked=True,
                installed=True,
                accessible=True,
                executable_path=preferred_executable_path,
                executable_candidates=[candidate],
                version=(f"GAUSS {version}" if version else None),
                version_known=version_known,
                platform=plat,
                detection_method="user_provided_path",
                detection_status="found",
                operating_mode_recommendation="execution_candidate",
                can_execute_gauss_code="unknown",
                warnings=[_NO_EXECUTION_WARNING, _NO_PACKAGE_WARNING, *version_warnings],
                errors=[],
                next_steps=list(_FUTURE_STEPS),
            )

        # Step 1b: strict mode with no preferred path -- do not fall back to
        # broader discovery, per tools/gauss_environment_check.md's `strict`
        # input semantics.
        if strict:
            return _build_result(
                checked=True,
                installed=False,
                accessible="unknown",
                executable_path=None,
                executable_candidates=[],
                version=None,
                version_known=False,
                platform=plat,
                detection_method="not_checked",
                detection_status="not_found",
                operating_mode_recommendation="advisory",
                can_execute_gauss_code=False,
                warnings=[
                    "strict mode was requested without a preferred_executable_path, "
                    "so no discovery was attempted."
                ],
                errors=[],
                next_steps=["Provide preferred_executable_path, or disable strict mode to allow discovery."],
            )

        # Step 2/3: PATH lookup + common installation-location scan.
        candidates = discovery_fn(plat)

        if not candidates:
            return _build_result(
                checked=True,
                installed=False,
                accessible="unknown",
                executable_path=None,
                executable_candidates=[],
                version=None,
                version_known=False,
                platform=plat,
                detection_method="mixed" if plat not in ("unknown", "wsl") else "not_checked",
                detection_status="not_found",
                operating_mode_recommendation="advisory",
                can_execute_gauss_code=False,
                warnings=[
                    "No plausible GAUSS executable was found on PATH or in the common "
                    "installation locations checked."
                ],
                errors=[],
                next_steps=[
                    "Provide preferred_executable_path if GAUSS is installed in a nonstandard location.",
                    "Continue in Advisory Mode; code generation, explanation, and review remain fully available.",
                ],
            )

        candidate_versions = {c["path"]: parse_gauss_version(c["path"]) for c in candidates}

        # Step 2b: user-specified preferred version overrides the newest-version default.
        if preferred_version:
            matching = [c for c in candidates if candidate_versions.get(c["path"]) == str(preferred_version)]
            if not matching:
                return _build_result(
                    checked=True,
                    installed="unknown",
                    accessible="unknown",
                    executable_path=None,
                    executable_candidates=candidates,
                    version=None,
                    version_known=False,
                    platform=plat,
                    detection_method="mixed",
                    detection_status="not_found",
                    operating_mode_recommendation="advisory",
                    can_execute_gauss_code="unknown",
                    warnings=[f"No detected candidate matched the requested GAUSS version {preferred_version}."],
                    errors=[],
                    next_steps=[
                        "Provide preferred_executable_path directly if the requested version "
                        "is installed in a nonstandard location.",
                        f"Confirm GAUSS {preferred_version} is actually installed.",
                    ],
                )

            accessible_matches = [c for c in matching if c["accessible"] is True]
            if not accessible_matches:
                return _build_result(
                    checked=True,
                    installed="unknown",
                    accessible=False,
                    executable_path=None,
                    executable_candidates=candidates,
                    version=None,
                    version_known=False,
                    platform=plat,
                    detection_method="mixed",
                    detection_status="inaccessible",
                    operating_mode_recommendation="advisory",
                    can_execute_gauss_code="unknown",
                    warnings=[
                        f"A candidate matching the requested GAUSS version {preferred_version} "
                        "was found but could not be confirmed as accessible."
                    ],
                    errors=[],
                    next_steps=[
                        "Check permissions for the matched candidate path.",
                        "Confirm a GAUSS license is active and reachable if permissions look correct.",
                    ],
                )

            chosen = accessible_matches[0]
            return _build_result(
                checked=True,
                installed=True,
                accessible=True,
                executable_path=chosen["path"],
                executable_candidates=candidates,
                version=f"GAUSS {candidate_versions[chosen['path']]}",
                version_known=True,
                platform=plat,
                detection_method="requested_version",
                detection_status="found",
                operating_mode_recommendation="execution_candidate",
                can_execute_gauss_code="unknown",
                warnings=[_NO_EXECUTION_WARNING, _NO_PACKAGE_WARNING],
                errors=[],
                next_steps=list(_FUTURE_STEPS),
            )

        # Step 3: newest-version default selection.
        versioned = [c for c in candidates if candidate_versions.get(c["path"]) is not None]

        if not versioned:
            if len(candidates) == 1:
                c = candidates[0]
                if c["accessible"] is True:
                    return _build_result(
                        checked=True,
                        installed=True,
                        accessible=True,
                        executable_path=c["path"],
                        executable_candidates=candidates,
                        version=None,
                        version_known=False,
                        platform=plat,
                        detection_method=c["source"],
                        detection_status="found",
                        operating_mode_recommendation="execution_candidate",
                        can_execute_gauss_code="unknown",
                        warnings=[
                            "Version could not be determined from the executable path.",
                            _NO_EXECUTION_WARNING,
                            _NO_PACKAGE_WARNING,
                        ],
                        errors=[],
                        next_steps=[
                            "Set allow_version_query to true if a version check is desired and considered safe.",
                            *_FUTURE_STEPS,
                        ],
                    )
                status = "inaccessible" if c["accessible"] is False else "unknown"
                return _build_result(
                    checked=True,
                    installed="unknown",
                    accessible=c["accessible"],
                    executable_path=None,
                    executable_candidates=candidates,
                    version=None,
                    version_known=False,
                    platform=plat,
                    detection_method=c["source"],
                    detection_status=status,
                    operating_mode_recommendation="advisory",
                    can_execute_gauss_code="unknown",
                    warnings=["A plausible GAUSS executable path was found but could not be confirmed as accessible."],
                    errors=[],
                    next_steps=["Check file and directory permissions for the candidate path."],
                )

            return _build_result(
                checked=True,
                installed="unknown",
                accessible="unknown",
                executable_path=None,
                executable_candidates=candidates,
                version=None,
                version_known=False,
                platform=plat,
                detection_method="mixed",
                detection_status="ambiguous",
                operating_mode_recommendation="advisory",
                can_execute_gauss_code="unknown",
                warnings=[
                    "Multiple plausible GAUSS executables were found and none could be "
                    "distinguished by version; the correct one could not be determined automatically."
                ],
                errors=[],
                next_steps=[
                    "Ask the user to choose one candidate or provide preferred_executable_path.",
                    "Continue in Advisory Mode until the ambiguity is resolved.",
                ],
            )

        versioned_sorted = sorted(
            versioned, key=lambda c: version_sort_key(candidate_versions[c["path"]]), reverse=True
        )
        highest_version = candidate_versions[versioned_sorted[0]["path"]]
        highest_candidates = [c for c in versioned_sorted if candidate_versions[c["path"]] == highest_version]
        accessible_highest = [c for c in highest_candidates if c["accessible"] is True]

        if accessible_highest:
            chosen = accessible_highest[0]
            return _build_result(
                checked=True,
                installed=True,
                accessible=True,
                executable_path=chosen["path"],
                executable_candidates=candidates,
                version=f"GAUSS {highest_version}",
                version_known=True,
                platform=plat,
                detection_method="version_sorting",
                detection_status="found",
                operating_mode_recommendation="execution_candidate",
                can_execute_gauss_code="unknown",
                warnings=[
                    f"Selected GAUSS {highest_version} as the highest detected version "
                    f"among {len(versioned)} versioned candidate(s).",
                    _NO_EXECUTION_WARNING,
                    _NO_PACKAGE_WARNING,
                ],
                errors=[],
                next_steps=list(_FUTURE_STEPS),
            )

        # Highest version detected but inaccessible -- never silently downgrade.
        older_accessible = [
            c for c in versioned_sorted if c["accessible"] is True and candidate_versions[c["path"]] != highest_version
        ]
        if older_accessible:
            return _build_result(
                checked=True,
                installed="unknown",
                accessible="unknown",
                executable_path=None,
                executable_candidates=candidates,
                version=None,
                version_known=False,
                platform=plat,
                detection_method="version_sorting",
                detection_status="ambiguous",
                operating_mode_recommendation="advisory",
                can_execute_gauss_code="unknown",
                warnings=[
                    f"The highest detected GAUSS version ({highest_version}) is inaccessible, "
                    "and at least one older version is accessible.",
                    "This tool does not silently select an older version when a newer one is "
                    "detected but inaccessible; user confirmation is required.",
                ],
                errors=[],
                next_steps=[
                    f"Confirm whether to use an older, accessible GAUSS version instead of "
                    f"the inaccessible GAUSS {highest_version}.",
                    "Check permissions/licensing for the inaccessible newest candidate.",
                    "Provide preferred_version or preferred_executable_path to make an explicit choice.",
                ],
            )

        return _build_result(
            checked=True,
            installed="unknown",
            accessible=False,
            executable_path=None,
            executable_candidates=candidates,
            version=None,
            version_known=False,
            platform=plat,
            detection_method="version_sorting",
            detection_status="inaccessible",
            operating_mode_recommendation="advisory",
            can_execute_gauss_code="unknown",
            warnings=[
                f"The highest detected GAUSS version ({highest_version}) is inaccessible, "
                "and no other versioned candidate is accessible."
            ],
            errors=[],
            next_steps=[
                "Check permissions and licensing for the detected candidate(s).",
                "Provide preferred_executable_path if a different, accessible installation exists.",
            ],
        )
    except Exception as exc:  # noqa: BLE001 -- detection must never crash the caller
        return _build_result(
            checked=True,
            installed="unknown",
            accessible="unknown",
            executable_path=None,
            executable_candidates=[],
            version=None,
            version_known=False,
            platform=plat,
            detection_method="error",
            detection_status="error",
            operating_mode_recommendation="advisory",
            can_execute_gauss_code="unknown",
            warnings=[],
            errors=[f"Unexpected detection error: {exc}"],
            next_steps=[
                "Continue in Advisory Mode; this error does not block code writing, explanation, "
                "review, documentation, education, or product reasoning."
            ],
        )


def validate_against_schema(result: dict[str, Any], schema_path: Path) -> list[str]:
    """Validate a result dict against the schema. Returns jsonschema error messages.

    Returns a single explanatory item (not an exception) if jsonschema is not
    installed, so detection results remain usable without the optional
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
    print(f"GAUSS detection status:          {result['detection_status']}")
    print(f"Operating mode recommendation:   {result['operating_mode_recommendation']}")
    print(f"Installed / Accessible:          {result['installed']} / {result['accessible']}")
    print(f"Executable path:                 {result['executable_path']}")
    print(f"Version (known):                 {result['version']} ({result['version_known']})")
    print(f"Platform / Detection method:     {result['platform']} / {result['detection_method']}")
    print(f"Can execute GAUSS code (future): {result['can_execute_gauss_code']}")

    if result["executable_candidates"]:
        print("\nCandidates:")
        for c in result["executable_candidates"]:
            print(f"  - {c['path']} (source={c['source']}, accessible={c['accessible']})")

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
    """Lightweight built-in test suite for the pure detection logic.

    No formal tests/ directory exists in this repository yet (see
    planning/v0.21.0-gauss-environment-detection-implementation.md's Testing
    Strategy), so this runs via `python scripts/gauss_environment_check.py
    --self-test`. Every case uses injected synthetic candidates; none depend
    on a real GAUSS installation.
    """
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    check("parse 'GAUSS 26' -> 26", parse_gauss_version("GAUSS 26") == "26")
    check(
        "parse path with GAUSS26 -> 26",
        parse_gauss_version("C:/Program Files/GAUSS26/tgauss.exe") == "26",
    )
    check("parse path with gauss25 -> 25", parse_gauss_version("/opt/gauss25/tgauss") == "25")
    check("parse 'GAUSS 25.1' -> 25.1", parse_gauss_version("GAUSS 25.1") == "25.1")
    check("parse no version -> None", parse_gauss_version("/usr/local/bin/tgauss") is None)

    def candidates_24_25_26(_plat: str) -> list[dict[str, Any]]:
        return [
            make_candidate("/example/gauss24/tgauss", "path_lookup", True, []),
            make_candidate("/example/gauss25/tgauss", "path_lookup", True, []),
            make_candidate("/example/gauss26/tgauss", "path_lookup", True, []),
        ]

    result = detect_environment(discovery_fn=candidates_24_25_26)
    check(
        "24/25/26 detected -> selects newest (26)",
        result["detection_status"] == "found" and result["version"] == "GAUSS 26",
    )

    result = detect_environment(preferred_version="25", discovery_fn=candidates_24_25_26)
    check(
        "preferred_version 25 overrides newest (26)",
        result["detection_status"] == "found" and result["version"] == "GAUSS 25",
    )

    def single_candidate(_plat: str) -> list[dict[str, Any]]:
        return [make_candidate("/example/gauss26/tgauss", "path_lookup", True, [])]

    result = detect_environment(
        preferred_executable_path="/preferred/gauss24/tgauss",
        path_exists_fn=lambda p: p == "/preferred/gauss24/tgauss",
        accessibility_fn=lambda p: True,
        discovery_fn=single_candidate,
    )
    check(
        "preferred_executable_path overrides discovery",
        result["detection_status"] == "found" and result["executable_path"] == "/preferred/gauss24/tgauss",
    )

    def unknown_version_candidates(_plat: str) -> list[dict[str, Any]]:
        return [
            make_candidate("/example/a/tgauss", "path_lookup", True, []),
            make_candidate("/example/b/tgauss", "path_lookup", True, []),
        ]

    result = detect_environment(discovery_fn=unknown_version_candidates)
    check("multiple unknown-version candidates -> ambiguous", result["detection_status"] == "ambiguous")

    def no_candidates(_plat: str) -> list[dict[str, Any]]:
        return []

    result = detect_environment(discovery_fn=no_candidates)
    check("no candidates -> not_found", result["detection_status"] == "not_found")

    result = detect_environment(
        preferred_executable_path="/preferred/gauss26/tgauss",
        path_exists_fn=lambda p: True,
        accessibility_fn=lambda p: False,
    )
    check("inaccessible preferred path -> inaccessible", result["detection_status"] == "inaccessible")

    def newest_inaccessible(_plat: str) -> list[dict[str, Any]]:
        return [
            make_candidate("/example/gauss24/tgauss", "path_lookup", True, []),
            make_candidate("/example/gauss26/tgauss", "path_lookup", False, []),
        ]

    result = detect_environment(discovery_fn=newest_inaccessible)
    check(
        "newest inaccessible with older accessible -> no silent downgrade (ambiguous)",
        result["detection_status"] == "ambiguous",
    )

    schema_path = default_schema_path()
    if schema_path.is_file():
        representative = {
            "found": detect_environment(discovery_fn=candidates_24_25_26),
            "not_found": detect_environment(discovery_fn=no_candidates),
            "ambiguous": detect_environment(discovery_fn=unknown_version_candidates),
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


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Detect whether GAUSS is installed or discoverable on this machine. "
            "Read-only: does not run user GAUSS code, does not inspect installed "
            "packages, and does not activate Execution Mode. See "
            "tools/gauss_environment_check.md for the full contract."
        )
    )
    parser.add_argument(
        "--preferred-executable-path",
        default=None,
        help="Highest-priority candidate. If given, no other candidate is silently substituted on failure.",
    )
    parser.add_argument(
        "--preferred-version",
        default=None,
        help="E.g. 25 or 26. Overrides the newest-version default when a matching, accessible candidate exists.",
    )
    parser.add_argument(
        "--working-directory",
        default=None,
        help="Accepted for input-contract completeness; not currently used to alter detection.",
    )
    parser.add_argument(
        "--platform-hint",
        default=None,
        choices=["windows", "macos", "linux", "wsl"],
        help="Override auto-detected platform.",
    )
    parser.add_argument(
        "--allow-version-query",
        action="store_true",
        help=(
            "Permit a minimal version query. No safe GAUSS version-query flag is "
            "confirmed yet, so this currently only adds an explanatory warning."
        ),
    )
    parser.add_argument("--detection-timeout-seconds", type=float, default=5.0)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use only --preferred-executable-path; do not fall back to broader discovery.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full structured JSON result. Default output is a short human-readable summary.",
    )
    parser.add_argument(
        "--validate-schema",
        action="store_true",
        help="Validate the result against schemas/gauss_environment_check.schema.json before printing.",
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

    result = detect_environment(
        preferred_executable_path=args.preferred_executable_path,
        preferred_version=args.preferred_version,
        working_directory=args.working_directory,
        platform_hint=args.platform_hint,
        allow_version_query=args.allow_version_query,
        detection_timeout_seconds=args.detection_timeout_seconds,
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
