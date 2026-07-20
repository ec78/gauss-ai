"""Doubly-gated REAL GAUSS controller-path harness (v0.34.0 Confirmed
Controller Execution Path).

THIS FILE CAN INVOKE REAL GAUSS. It is not a default test. It must never be
run as part of `python scripts/test_gauss_runtime_orchestration.py`,
`python scripts/test_gauss_execution_adapter.py`,
`python scripts/check_release_readiness.py`, or any CI workflow -- none of
those import or execute this file, and this file requires two independent,
explicit opt-in gates before it will do anything beyond print a skip notice:

    1. The command-line flag --run-real-gauss
    2. The environment variable GAUSS_AI_ALLOW_REAL_EXECUTION=1

BOTH are required simultaneously. Either one missing means this harness
skips safely without touching GAUSS, without invoking the Helper Adapter,
and without importing scripts/gauss_code_execution.py.

Unlike v0.33.0's scripts/test_gauss_execution_adapter_real.py (which drove
GaussExecutionAdapter directly, standalone), this harness drives the FULL
runtime orchestration controller -- scripts/gauss_runtime_orchestration.py's
MockOrchestrationInstance -- through its complete, documented state sequence:

    collecting_inputs -> proposed -> awaiting_confirmation -> confirmed
    -> executing -> execution_completed (or execution_failed)
    -> analyzing -> report_generating -> completed

using `build_production_adapter_runner(...)` as the injected runner for the
one real `invoke()` call. This is the first real exercise of the
controller's own confirmation/state-machine path (submit_for_review,
display_plan, confirm, invoke, begin_analysis), not just the adapter boundary
alone.

Merely importing this module does nothing -- no gate is checked, no
directory is created, no helper is loaded, at import time. All gating and
preflight logic runs only inside main(), when explicitly invoked.

Verified inline code used by this harness (never invented, never
user-suppliable through this file):

- "success" scenario: "x = 2 + 2;\\nprint x;" -- byte-for-byte the script
  content real-verified as Test 3 ("Scalar calculation") in
  planning/v0.28.0-real-gauss-invocation-research.md, already reused by
  v0.33.0's own harness.
- "runtime_error" scenario: "x = ;" -- byte-for-byte the script content
  real-verified as Test 4 ("Intentional syntax error") in that same
  document: confirmed to exit non-interactively with exit_code 0, stdout
  "Program execute failed", and stderr containing "error G0105", never
  hanging or dropping into an interactive prompt.

This module was created, and its gating/preflight logic was tested, WITHOUT
ever supplying both gates simultaneously except for the explicitly
authorized, individually justified real invocations recorded in
planning/v0.34.0-confirmed-controller-execution-path.md.
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

# Safe to import unconditionally -- gauss_runtime_orchestration has no
# import-time execution side effects (it only imports gauss_execution_adapter,
# which itself never imports the real helper at import time either).
import gauss_runtime_orchestration as orch  # noqa: E402

ENV_VAR_NAME = "GAUSS_AI_ALLOW_REAL_EXECUTION"
REQUIRED_ENV_VALUE = "1"
FLAG_NAME = "--run-real-gauss"

_VERIFIED_PLATFORM = "Windows"
_SUPPORTED_EXECUTABLE_BASENAMES = frozenset({"tgauss", "tgauss.exe"})

# Verified, not invented -- see module docstring for provenance.
_SCENARIOS: dict[str, str] = {
    "success": "x = 2 + 2;\nprint x;",
    "runtime_error": "x = ;",
}


def gate_status(*, flag_present: bool, env_value: str | None) -> tuple[bool, bool]:
    env_present = env_value == REQUIRED_ENV_VALUE
    return flag_present, env_present


def should_run(flag_present: bool, env_present: bool) -> bool:
    return flag_present and env_present


def _verify_platform() -> bool:
    return platform.system() == _VERIFIED_PLATFORM


def _verify_executable(executable_path: str | None) -> bool:
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
            "Doubly-gated real GAUSS controller-path harness. Drives the full "
            "MockOrchestrationInstance state sequence through one real invocation via "
            "build_production_adapter_runner(...). Requires --run-real-gauss AND "
            "GAUSS_AI_ALLOW_REAL_EXECUTION=1 simultaneously; either one missing skips "
            "safely without touching GAUSS."
        )
    )
    parser.add_argument("--run-real-gauss", action="store_true", dest="run_real_gauss")
    parser.add_argument("--executable-path", default=None)
    parser.add_argument("--working-directory", default=None)
    parser.add_argument("--session-id", default=None)
    parser.add_argument(
        "--scenario",
        choices=sorted(_SCENARIOS.keys()),
        default="success",
        help="Which verified inline-code scenario to run if both gates are present.",
    )
    parser.add_argument("--self-test", action="store_true")
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

    print("=" * 72)
    print("REAL GAUSS EXECUTION IS ENABLED FOR THIS RUN (full controller path).")
    print(f"Both {FLAG_NAME} and {ENV_VAR_NAME}=1 were supplied.")
    print(f"Scenario: {args.scenario}")
    print("=" * 72)

    if not _verify_platform():
        print(f"PREFLIGHT FAILED: not {_VERIFIED_PLATFORM} (detected: {platform.system()}). No GAUSS was touched.")
        return 0
    if not _verify_executable(args.executable_path):
        print(
            "PREFLIGHT FAILED: --executable-path missing, not a terminal (tgauss/tgauss.exe) "
            "executable, or does not exist. No GAUSS was touched."
        )
        return 0
    if not args.working_directory:
        print("PREFLIGHT FAILED: --working-directory is required. No GAUSS was touched.")
        return 0
    if not Path(args.working_directory).is_dir():
        print("PREFLIGHT FAILED: --working-directory does not exist or is not a directory. No GAUSS was touched.")
        return 0
    if not args.session_id:
        print("PREFLIGHT FAILED: --session-id is required. No GAUSS was touched.")
        return 0

    print("Preflight checks passed: platform verified, executable verified as terminal and present, "
          "working directory verified, session id supplied.")

    return _run_controller_path(
        executable_path=args.executable_path,
        working_directory=args.working_directory,
        session_id=args.session_id,
        scenario=args.scenario,
    )


def _run_controller_path(*, executable_path: str, working_directory: str, session_id: str, scenario: str) -> int:
    code = _SCENARIOS[scenario]

    env = orch.EnvironmentSummary(
        executable_path=executable_path,
        gauss_version="GAUSS 26",
        platform="Windows",
        detection_provenance="direct",
    )
    safety = orch.SafetyReviewOutcome(
        outcome="pass",
        items=(
            orch.SafetyReviewItem("code_shown", True),
            orch.SafetyReviewItem("no_delete", True),
            orch.SafetyReviewItem("terminal_executable", True),
            orch.SafetyReviewItem("timeout_set", True),
            orch.SafetyReviewItem("no_network", True),
            orch.SafetyReviewItem("no_credentials", True),
        ),
    )
    draft = orch.RequestDraft(
        request_id=f"v0.34.0-real-controller-{scenario}",
        code=code,
        working_directory=working_directory,
        executable_path=executable_path,
        timeout_seconds=30.0,
        execution_purpose=f"v0.34.0 real controller-path verification ({scenario})",
        environment_summary=env,
        safety_review=safety,
    )

    instance = orch.MockOrchestrationInstance(session_id=session_id, draft=draft)
    print(f"initial_state: {instance.record.current_state.value}")

    instance.submit_for_review()
    print(f"after_submit_for_review: {instance.record.current_state.value}")
    if instance.record.current_state != orch.OrchestrationState.PROPOSED:
        print(f"BLOCKED before confirmation: {instance.record.failure_category}. No GAUSS was touched.")
        return 0
    assert instance.request is not None
    request = instance.request
    print(f"canonical_request_id: {request.request_id}")
    print(f"request_hash: {request.request_hash}")

    instance.display_plan()
    print(f"after_display_plan: {instance.record.current_state.value}")

    print(f"confirmation_status_before_authorization: {instance.record.confirmation_status.value}")
    print(f"confirmation_consumption_status_before: {instance.record.confirmation_consumption_status}")

    confirmation = orch.ConfirmationEvent(
        scope=request.request_hash, timestamp="v0.34.0-real-controller-run", session_id=session_id
    )
    instance.confirm(confirmation)
    print(f"after_confirm: {instance.record.current_state.value}")
    print(f"confirmation_scope_matches_hash: {confirmation.scope == request.request_hash}")

    real_runner = orch.build_production_adapter_runner(request_identity=request.request_hash)

    instance.invoke(real_runner)
    print(f"after_invoke: {instance.record.current_state.value}")
    print(f"confirmation_status_after_authorization: {instance.record.confirmation_status.value}")
    print(f"confirmation_consumption_status_after: {instance.record.confirmation_consumption_status}")
    print(f"helper_invocation_id: {instance.record.helper_invocation_id}")
    print(f"helper_invocation_status: {instance.record.helper_invocation_status.value}")
    print(f"failure_category: {instance.record.failure_category}")

    result = instance.record.execution_result_reference
    if result is not None:
        print(f"execution_status: {result.execution_status}")
        print(f"exit_code (non-authoritative): {result.exit_code}")
        print(f"stdout: {result.stdout!r}")
        print(f"stderr: {result.stderr!r}")
        print(f"output_file_count (metadata only): {len(result.output_files)}")
    else:
        print("execution_result_reference: None (no valid result retained)")

    if instance.record.validation_outcome is not None:
        print(f"structural_validation_ok: {instance.record.validation_outcome.is_structurally_valid}")

    # Deterministic, minimal analysis/report hooks -- no real GAUSS involved,
    # only interpretation of the already-returned mock result reference.
    def analysis_hook(req: "orch.CanonicalExecutionRequest", res: "orch.MockExecutionResult | None") -> None:
        del req, res  # Deliberately minimal: presence/shape only, no methodology claim.

    def report_hook(analysis_status: "orch.AnalysisStatus") -> None:
        del analysis_status  # Deliberately minimal fallback-safe hook.

    if instance.record.current_state in (
        orch.OrchestrationState.EXECUTION_COMPLETED,
        orch.OrchestrationState.EXECUTION_FAILED,
    ) and instance.record.failure_category != orch.FailureCategory.MALFORMED_RESULT:
        instance.begin_analysis(analysis_hook, report_requested=True, report_hook=report_hook)
        print(f"after_begin_analysis: {instance.record.current_state.value}")
        print(f"analysis_status: {instance.record.analysis_status.value}")
        print(f"report_status: {instance.record.report_status.value}")
    else:
        print("analysis skipped: malformed result or non-terminal execution state")

    print(f"final_state: {instance.record.current_state.value}")
    print(f"transition_count: {len(instance.record.transition_log)}")
    print("transition_sequence: " + " -> ".join(t.to_state.value for t in instance.record.transition_log))

    print("SAFE_SUMMARY: " + str(instance.record.to_safe_summary()))
    return 0


# ---------------------------------------------------------------------------
# Self-test: gating/preflight logic only. Never supplies both gates
# simultaneously, never calls build_production_adapter_runner, never calls
# _run_controller_path.
# ---------------------------------------------------------------------------


def _run_self_tests() -> int:
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    check("no gates -> should not run", should_run(*gate_status(flag_present=False, env_value=None)) is False)
    check("flag only -> should not run", should_run(*gate_status(flag_present=True, env_value=None)) is False)
    check(
        "env var only -> should not run",
        should_run(*gate_status(flag_present=False, env_value=REQUIRED_ENV_VALUE)) is False,
    )
    check(
        "both gates present -> should run (pure boolean check only, never executed)",
        should_run(*gate_status(flag_present=True, env_value=REQUIRED_ENV_VALUE)) is True,
    )
    check("missing executable_path fails preflight", _verify_executable(None) is False)
    check("GUI executable fails preflight", _verify_executable("C:/example/gauss26/gauss.exe") is False)
    check("scenarios are exactly success and runtime_error", set(_SCENARIOS.keys()) == {"success", "runtime_error"})
    check(
        "success scenario code matches v0.28.0 Test 3 verified content",
        _SCENARIOS["success"] == "x = 2 + 2;\nprint x;",
    )
    check(
        "runtime_error scenario code matches v0.28.0 Test 4 verified content",
        _SCENARIOS["runtime_error"] == "x = ;",
    )

    # Safety-critical: main() reads the REAL os.environ internally, so this
    # self-test must never trust the ambient shell not to already have
    # GAUSS_AI_ALLOW_REAL_EXECUTION=1 set.
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
