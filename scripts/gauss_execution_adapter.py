"""Helper Adapter: the single controlled boundary between runtime orchestration
and the verified GAUSS code execution helper (v0.32.0 Phase 3, Increment 1).

Authoritative design sources (this module does not redefine their rules, only
implements them):

- planning/v0.32.0-real-helper-adapter-scope.md -- the full Phase 3 scope,
  helper interface audit (Section 5), request-to-helper projection (Section
  6), script-path policy (Section 7), environment binding (Section 8),
  pre-invocation validation (Section 9), status/failure mapping (Section 12),
  and the resolved decisions (Sections 22-24) this module implements.
- planning/v0.31.0-canonical-execution-request-contract.md -- the 18-field
  canonical execution request this module's AdapterRequest is a narrow
  projection of.

This module is scoped to Increment 1 ONLY, per
planning/v0.32.0-real-helper-adapter-scope.md's Section 24:

- It never imports scripts/gauss_code_execution.py at module import time.
  `load_real_helper()` performs that import lazily, inside its own function
  body, and is never called automatically -- only an explicit caller
  invocation constructs the real production path.
- It never launches a subprocess itself.
- It never detects a real GAUSS environment (no call to
  scripts/gauss_environment_check.py anywhere in this module).
- It never invokes gauss.exe or tgauss.exe, directly or indirectly --
  GaussExecutionAdapter.invoke(...) only ever calls the *injected* `helper`
  callable supplied by its caller (in practice, a test's fake helper; in a
  later, separately authorized increment, the real
  scripts.gauss_code_execution.execute_gauss_code via load_real_helper()).
- Script-path mode is unconditionally rejected before the injected helper is
  ever called (Section 7's resolved decision) -- this module implements no
  content-fingerprinting mechanism and does not treat a resolved path as
  proof of unchanged file contents.
- This module is not wired into scripts/gauss_runtime_orchestration.py by
  this revision (that is Increment 6, not authorized here).

Import direction, as resolved in the scope document's Section 23:
scripts/gauss_runtime_orchestration.py -> scripts/gauss_execution_adapter.py
-> scripts/gauss_code_execution.py. This module must never import the
controller (doing so would create the prohibited reverse/circular import).
"""

from __future__ import annotations

import argparse
import enum
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

# ---------------------------------------------------------------------------
# The verified helper interface (Protocol only -- no import of the real
# module here; see load_real_helper() below for the one, lazy, explicit
# import site).
# ---------------------------------------------------------------------------


class HelperCallable(Protocol):
    """Structural type matching execute_gauss_code(...)'s actual, verified
    signature (scripts/gauss_code_execution.py, confirmed by direct
    inspection -- see planning/v0.32.0-real-helper-adapter-scope.md Section
    5). A fake/stubbed callable satisfying this shape is used by every test
    in this module and in scripts/test_gauss_execution_adapter.py; the real
    execute_gauss_code function also satisfies it structurally, without this
    module ever importing it."""

    def __call__(
        self,
        environment_check_result: dict[str, Any] | None = None,
        package_inspection_result: dict[str, Any] | None = None,
        executable_path: str | None = None,
        gauss_version: str | None = None,
        code: str | None = None,
        script_path: str | None = None,
        working_directory: str | None = None,
        input_files: list[str] | None = None,
        output_directory: str | None = None,
        timeout_seconds: float | None = None,
        allow_file_write: bool = False,
        allow_output_files: bool = True,
        allow_network: bool = False,
        strict: bool = False,
        capture_stdout: bool = True,
        capture_stderr: bool = True,
        validate_schema: bool = False,
    ) -> dict[str, Any]: ...


def load_real_helper() -> HelperCallable:
    """Explicit, lazy production-helper factory.

    Importing this module never calls this function -- it is only ever
    invoked by an explicit, separate caller action (not by
    GaussExecutionAdapter's own construction, and not by any default in this
    module). This is the ONE place in this module that may import
    scripts/gauss_code_execution.py, and it does so lazily (inside this
    function body, not at module top level), so merely importing
    gauss_execution_adapter has zero execution side effects: no helper
    import, no GAUSS detection, no subprocess launch, no code run.

    Per planning/v0.32.0-real-helper-adapter-scope.md's Section 23 (decision
    3): this is the only permitted route from orchestration to the helper --
    the controller must never import execute_gauss_code directly, and this
    factory must never be called automatically as part of constructing a
    GaussExecutionAdapter.
    """
    _script_dir = Path(__file__).resolve().parent
    if str(_script_dir) not in sys.path:
        sys.path.insert(0, str(_script_dir))
    try:
        import gauss_code_execution as _real_helper_module  # local import: see docstring above
    except ImportError as exc:
        raise ImportError(
            "load_real_helper() could not import scripts/gauss_code_execution.py: "
            f"{exc}. The real execution helper is unavailable in this environment; "
            "no production Helper Adapter can be constructed until this import succeeds."
        ) from exc

    return _real_helper_module.execute_gauss_code


# ---------------------------------------------------------------------------
# Narrow, self-contained request/result types (no import of orchestration
# types -- this module must not import scripts/gauss_runtime_orchestration.py,
# per the resolved import direction).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdapterRequest:
    """A narrow projection of the 18-field canonical execution request --
    exactly the fields this adapter needs to call the helper (Section 6's
    request-to-helper projection table). Deliberately excludes
    request_id/execution_purpose/user_confirmed/confirmation_scope/
    confirmation_timestamp/safety_review -- those are orchestration-only
    fields (Section 6) that never reach the helper.

    `request_identity` is an opaque identifier (in practice, the confirmed
    request's request_hash) used only for this adapter's own
    duplicate-invocation tracking -- not passed to the helper.
    """

    request_identity: str
    code: str | None
    script_path: str | None
    working_directory: str
    output_directory: str | None
    executable_path: str
    gauss_version: str | None
    timeout_seconds: float
    expected_input_files: tuple[str, ...] = ()
    expected_output_files: tuple[str, ...] = ()
    required_packages: tuple[str, ...] = ()
    allow_output_files: bool = True
    package_inspection_result: dict[str, Any] | None = None


class AdapterFailureCategory(enum.Enum):
    """Adapter-level pre-invocation and post-invocation failure categories.

    Distinct from, and narrower than, scripts/gauss_runtime_orchestration.py's
    22-member FailureCategory -- that enum classifies orchestration-level
    outcomes; this one classifies only what the adapter itself detects at
    its own boundary. A future Increment 6 controller integration maps these
    (and the helper's own execution_status values) into the orchestration
    FailureCategory, per Section 12's status/failure mapping table -- this
    module does not perform that mapping itself.
    """

    DUPLICATE_INVOCATION = "duplicate_invocation"
    SCRIPT_PATH_UNSUPPORTED = "script_path_unsupported"
    MISSING_INLINE_CODE = "missing_inline_code"
    INVALID_REQUEST = "invalid_request"
    EXECUTABLE_UNSUPPORTED = "executable_unsupported"
    ENVIRONMENT_MISMATCH = "environment_mismatch"
    MISSING_PACKAGE_CONTEXT = "missing_package_context"
    HELPER_UNAVAILABLE = "helper_dependency_unavailable"
    HELPER_LAUNCH_EXCEPTION = "helper_launch_exception"
    MALFORMED_RESULT = "malformed_result"
    UNKNOWN_HELPER_STATUS = "unknown_helper_status"


# The seven verified execution_status values, confirmed directly against
# schemas/gauss_code_execution.schema.json's enum -- no additional status is
# invented anywhere in this module.
VERIFIED_HELPER_STATUSES = frozenset(
    {"completed", "failed", "timed_out", "skipped", "blocked", "error", "unknown"}
)

# Only the terminal GAUSS executable has a verified, documented non-interactive
# batch-mode flag (-b) -- confirmed by direct inspection of
# scripts/gauss_code_execution.py's _TERMINAL_EXECUTABLE_BASENAMES. GUI
# executables (e.g. gauss.exe) are rejected by the adapter itself, in addition
# to (never instead of) the helper's own independent refusal -- defense in
# depth, per Section 8's "GUI substitution prohibition."
_SUPPORTED_EXECUTABLE_BASENAMES = frozenset({"tgauss", "tgauss.exe"})


@dataclass(frozen=True)
class AdapterOutcome:
    """The adapter's own classification of one invoke() call.

    `raw_result` preserves the helper's structured result completely
    unmodified when the helper was actually called and returned something
    -- this module never rewrites, summarizes, or filters it (Section 11).
    """

    invoked: bool
    execution_status: str | None
    failure_category: AdapterFailureCategory | None
    raw_result: dict[str, Any] | None
    rejection_reason: str | None = None


def _default_environment_probe(executable_path: str) -> bool:
    """Path-continuity check only -- NOT GAUSS detection.

    Confirms the previously-confirmed executable path still exists on disk,
    immediately before invocation (Section 8's `environment_still_matches`
    guard). This performs exactly the same kind of check
    scripts/gauss_code_execution.py's own `path_exists_fn` already performs
    internally -- a plain filesystem existence check, not a search for GAUSS
    installations, not a version query, and not a call into
    scripts/gauss_environment_check.py. It runs no code and detects no
    environment beyond "does this exact path still exist."
    """
    try:
        return Path(executable_path).exists()
    except OSError:
        return False


def _is_structurally_valid_result(raw: dict[str, Any]) -> bool:
    """Minimal structural check distinguishing a well-shaped helper result
    from a malformed one -- deliberately smaller than the full
    schemas/gauss_code_execution.schema.json (never imported here); only the
    subset this adapter's own routing depends on."""
    if not isinstance(raw, dict):
        return False
    if "execution_status" not in raw or "executed" not in raw:
        return False
    if not isinstance(raw["executed"], bool):
        return False
    if "output_files" in raw and raw["output_files"] is not None:
        if not isinstance(raw["output_files"], list):
            return False
        for entry in raw["output_files"]:
            if not isinstance(entry, dict) or "path" not in entry:
                return False
            if "content" in entry:
                # Structural guard: output metadata must never carry file
                # content, mirroring the controller's own equivalent check.
                return False
    return True


def safe_summary(request: AdapterRequest, outcome: AdapterOutcome) -> dict[str, Any]:
    """An audit-safe summary excluding code, script content, and any
    credential/secret-shaped data -- only identifiers, paths, statuses, and
    the helper's own disclosed evidence (stdout/stderr/exit_code/output
    metadata), which are legitimate execution evidence, not secrets."""
    raw = outcome.raw_result or {}
    return {
        "request_identity": request.request_identity,
        "working_directory": request.working_directory,
        "output_directory": request.output_directory,
        "executable_path": request.executable_path,
        "gauss_version": request.gauss_version,
        "timeout_seconds": request.timeout_seconds,
        "invoked": outcome.invoked,
        "execution_status": outcome.execution_status,
        "failure_category": outcome.failure_category.value if outcome.failure_category else None,
        "rejection_reason": outcome.rejection_reason,
        "exit_code": raw.get("exit_code"),
        "elapsed_seconds": raw.get("elapsed_seconds"),
        "output_file_count": len(raw.get("output_files") or []),
        "warning_count": len(raw.get("warnings") or []),
        "error_count": len(raw.get("errors") or []),
    }


# ---------------------------------------------------------------------------
# The adapter itself
# ---------------------------------------------------------------------------


class GaussExecutionAdapter:
    """The single controlled route from orchestration to the execution
    helper. Constructed with an injected `helper` callable -- never
    constructs or selects one itself, and never falls back to a real helper
    automatically (Section 3's "production helper selection must be
    explicit").

    Tracks invoked request_identity values in memory, per instance, to
    enforce "at most once per confirmed request" at the adapter's own
    boundary -- defense in depth alongside (never instead of) the
    controller's own equivalent guarantee (Increment 6, not implemented by
    this module).
    """

    def __init__(
        self,
        *,
        helper: HelperCallable,
        environment_probe: Callable[[str], bool] | None = None,
    ) -> None:
        self._helper = helper
        self._environment_probe = environment_probe or _default_environment_probe
        self._invoked_request_identities: set[str] = set()

    def _reject(
        self, category: AdapterFailureCategory, reason: str
    ) -> AdapterOutcome:
        return AdapterOutcome(
            invoked=False,
            execution_status=None,
            failure_category=category,
            raw_result=None,
            rejection_reason=reason,
        )

    def invoke(self, request: AdapterRequest) -> AdapterOutcome:
        """Validate, project, and call the injected helper at most once for
        this request_identity. Every rejection below occurs BEFORE the
        helper is ever called -- these are pre-invocation guard failures,
        distinct in kind from anything the helper itself might report."""

        # 1. Duplicate-invocation guard (defense in depth).
        if request.request_identity in self._invoked_request_identities:
            return self._reject(
                AdapterFailureCategory.DUPLICATE_INVOCATION,
                f"request_identity {request.request_identity!r} has already been invoked once; "
                "a second invocation is refused.",
            )

        # 2. Script-path policy: RESOLVED, unconditional (Section 7).
        if request.script_path is not None:
            return self._reject(
                AdapterFailureCategory.SCRIPT_PATH_UNSUPPORTED,
                "script-path execution is not supported in this phase: no trustworthy "
                "content-fingerprinting mechanism exists to confirm the on-disk script still "
                "matches what was shown at confirmation time. Inline-code execution is the only "
                "supported Phase 3 mode.",
            )

        # 3. Missing inline code.
        if not request.code:
            return self._reject(
                AdapterFailureCategory.MISSING_INLINE_CODE,
                "no inline code was supplied; inline-code execution is the only supported mode "
                "and requires non-empty code.",
            )

        # 4. Structural request validity.
        if not request.working_directory:
            return self._reject(
                AdapterFailureCategory.INVALID_REQUEST, "working_directory is required."
            )
        if request.timeout_seconds is None or request.timeout_seconds <= 0:
            return self._reject(
                AdapterFailureCategory.INVALID_REQUEST,
                "timeout_seconds must be a positive number, explicitly supplied.",
            )

        # 5. Executable support (GUI rejection is defense in depth: the
        #    helper itself also refuses a GUI executable, per Section 8).
        basename = Path(request.executable_path).name.lower()
        if basename not in _SUPPORTED_EXECUTABLE_BASENAMES:
            return self._reject(
                AdapterFailureCategory.EXECUTABLE_UNSUPPORTED,
                f"executable_path {request.executable_path!r} is not a supported terminal "
                "executable (tgauss/tgauss.exe); GUI executables are never used.",
            )

        # 6. Environment binding: the confirmed executable path must still
        #    exist immediately before invocation (Section 8).
        if not self._environment_probe(request.executable_path):
            return self._reject(
                AdapterFailureCategory.ENVIRONMENT_MISMATCH,
                f"executable_path {request.executable_path!r} no longer matches the confirmed "
                "environment (path no longer resolves); failing closed rather than silently "
                "re-detecting a different environment.",
            )

        # 7. Required-package context: fail closed rather than silently
        #    proceeding without knowing whether a required package is missing.
        if request.required_packages and request.package_inspection_result is None:
            return self._reject(
                AdapterFailureCategory.MISSING_PACKAGE_CONTEXT,
                f"required_packages {list(request.required_packages)!r} were declared, but no "
                "package_inspection_result was supplied to confirm availability.",
            )

        # All pre-invocation guards passed. This attempt now counts toward
        # "at most once", regardless of whether the call below succeeds,
        # returns a failure result, or raises.
        self._invoked_request_identities.add(request.request_identity)

        try:
            raw_result = self._helper(
                environment_check_result=None,
                package_inspection_result=request.package_inspection_result,
                executable_path=request.executable_path,
                gauss_version=request.gauss_version,
                code=request.code,
                script_path=None,
                working_directory=request.working_directory,
                input_files=list(request.expected_input_files) or None,
                output_directory=request.output_directory,
                timeout_seconds=request.timeout_seconds,
                allow_file_write=False,
                allow_output_files=request.allow_output_files,
                allow_network=False,
                strict=True,
                capture_stdout=True,
                capture_stderr=True,
                validate_schema=False,
            )
        except Exception as exc:  # noqa: BLE001 - a launch-time exception must not crash the caller
            return AdapterOutcome(
                invoked=True,
                execution_status=None,
                failure_category=AdapterFailureCategory.HELPER_LAUNCH_EXCEPTION,
                raw_result=None,
                rejection_reason=f"the injected helper raised: {type(exc).__name__}: {exc}",
            )

        if not _is_structurally_valid_result(raw_result):
            return AdapterOutcome(
                invoked=True,
                execution_status=None,
                failure_category=AdapterFailureCategory.MALFORMED_RESULT,
                raw_result=raw_result,
                rejection_reason="the helper's returned result failed structural validation.",
            )

        status = raw_result.get("execution_status")
        if status not in VERIFIED_HELPER_STATUSES:
            return AdapterOutcome(
                invoked=True,
                execution_status=None,
                failure_category=AdapterFailureCategory.UNKNOWN_HELPER_STATUS,
                raw_result=raw_result,
                rejection_reason=f"execution_status {status!r} is not one of the seven verified statuses.",
            )

        return AdapterOutcome(
            invoked=True,
            execution_status=status,
            failure_category=None,
            raw_result=raw_result,
            rejection_reason=None,
        )


# ---------------------------------------------------------------------------
# Self-test harness (this repository's established convention -- see
# scripts/gauss_runtime_orchestration.py's own docstring for why; no pytest
# is configured anywhere in this repository)
# ---------------------------------------------------------------------------


def _run_self_tests() -> int:
    """A lightweight built-in smoke test. The focused, comprehensive test
    suite lives in scripts/test_gauss_execution_adapter.py -- this function
    only sanity-checks that the module's core entry points work at all,
    using a fake helper. It never imports scripts/gauss_code_execution.py,
    never launches a subprocess, and never invokes GAUSS."""
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    def fake_helper(**kwargs: Any) -> dict[str, Any]:
        return {
            "executed": True,
            "execution_status": "completed",
            "exit_code": 0,
            "stdout": "2",
            "stderr": "",
            "output_files": [],
            "warnings": [],
            "errors": [],
        }

    adapter = GaussExecutionAdapter(helper=fake_helper, environment_probe=lambda _p: True)
    request = AdapterRequest(
        request_identity="req-1",
        code="print 1+1;",
        script_path=None,
        working_directory="C:/example/work",
        output_directory=None,
        executable_path="C:/example/gauss26/tgauss.exe",
        gauss_version="GAUSS 26",
        timeout_seconds=30.0,
    )
    outcome = adapter.invoke(request)
    check("fake completed invocation reports invoked", outcome.invoked)
    check("fake completed invocation reports completed status", outcome.execution_status == "completed")

    duplicate_outcome = adapter.invoke(request)
    check(
        "duplicate invocation is refused",
        not duplicate_outcome.invoked
        and duplicate_outcome.failure_category == AdapterFailureCategory.DUPLICATE_INVOCATION,
    )

    script_adapter = GaussExecutionAdapter(helper=fake_helper, environment_probe=lambda _p: True)
    script_request = AdapterRequest(
        request_identity="req-2",
        code=None,
        script_path="script.gss",
        working_directory="C:/example/work",
        output_directory=None,
        executable_path="C:/example/gauss26/tgauss.exe",
        gauss_version="GAUSS 26",
        timeout_seconds=30.0,
    )
    script_outcome = script_adapter.invoke(script_request)
    check(
        "script-path request is rejected before invocation",
        not script_outcome.invoked
        and script_outcome.failure_category == AdapterFailureCategory.SCRIPT_PATH_UNSUPPORTED,
    )

    summary = safe_summary(request, outcome)
    check("safe summary excludes code", "print 1+1" not in str(summary))

    if failures:
        print(f"SELF-TEST FAILED ({len(failures)} issue(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SELF-TEST PASSED: all checks succeeded.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "GAUSS Helper Adapter (v0.32.0 Phase 3, Increment 1). Never imports "
            "scripts/gauss_code_execution.py at import time, never launches a subprocess on "
            "import, never invokes GAUSS. Requires an injected helper callable to do anything."
        )
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a lightweight built-in smoke test (fake helper only) and exit.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if args.self_test:
        return _run_self_tests()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
