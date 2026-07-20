"""Doubly-gated REAL GAUSS controller-path harness (v0.34.0 Confirmed
Controller Execution Path; extended in v0.35.0 Real Execution Reliability
and Output Verification with named, individually-selected reliability and
output-handling scenarios).

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

This harness drives the FULL runtime orchestration controller --
scripts/gauss_runtime_orchestration.py's MockOrchestrationInstance -- through
its complete, documented state sequence:

    collecting_inputs -> proposed -> awaiting_confirmation -> confirmed
    -> executing -> execution_completed (or execution_failed)
    -> analyzing -> report_generating -> completed

using `build_production_adapter_runner(...)` as the injected runner for the
one real `invoke()` call per process invocation of this script.

v0.35.0 change: exactly ONE named scenario is selected per explicit
invocation via --scenario (no default, and there is no "run everything" mode)
-- each real process invocation of this file performs at most one real GAUSS
call, for one caller-selected scenario, with a fresh CanonicalExecutionRequest,
a fresh MockOrchestrationInstance, and a fresh confirmation every time. An
explicit --invocation-number (1-5) must also be supplied when both gates are
present, purely as a caller-declared audit label printed in this run's own
evidence output -- it is NOT persisted anywhere and enforces nothing across
separate process invocations (this harness has no durable, cross-process
state, consistent with every prior milestone's stated limitations).

Verified inline code used by this harness (never invented, never
user-suppliable through this file):

- "success-basic" / "success-isolation" scenarios: "x = 2 + 2;\\nprint x;"
  -- byte-for-byte the script content real-verified as Test 3 ("Scalar
  calculation") in planning/v0.28.0-real-gauss-invocation-research.md,
  already reused by v0.33.0's and v0.34.0's own harnesses. The two scenario
  names exist to exercise the SAME verified code through two independent
  requests/instances, to demonstrate state isolation -- not to test two
  different code paths.
- "output-created" scenario: 'output file = gauss_output.txt reset;\\nprint
  "hello output test";\\noutput off;' -- byte-for-byte the idiom
  real-verified directly (Test 3) and at the helper level (Test 4) in
  planning/v0.29.0-runtime-error-output-file-verification.md, confirmed to
  create a file with exactly the expected content and to be correctly
  discovered (and the generated helper script correctly excluded) by
  scripts/gauss_code_execution.py's existing `_discover_output_files`.
- "output-missing" scenario: reuses the "success-basic" code unmodified,
  declaring `expected_output_files=("does_not_exist.txt",)` -- only the
  *declaration* is new here, not new GAUSS syntax; the script itself writes
  no output file, so the controller's existing, unmodified
  `_missing_expected_outputs(...)` is expected to flag the declared file as
  missing.
- "runtime-error" scenario: "x = ;" -- byte-for-byte the script content
  real-verified as Test 4 ("Intentional syntax error") in
  planning/v0.28.0-real-gauss-invocation-research.md: confirmed to exit
  non-interactively with exit_code 0, stdout "Program execute failed", and
  stderr containing "error G0105", never hanging or dropping into an
  interactive prompt.

`output_directory`, when supplied, is resolved by scripts/gauss_code_execution.py
(unmodified by this milestone) relative to `working_directory` via its own
existing containment check -- it is NOT the subprocess's current working
directory (that is always `working_directory` itself), so it only affects
where output-file *discovery* looks after execution, not where GAUSS's own
`output file = ...` statement actually writes. For the "output-created"
scenario this harness therefore expects --output-directory to be supplied as
the SAME directory as --working-directory (or a value that otherwise still
resolves to a location containing the real written file), consistent with
the actually-verified behavior recorded in
planning/v0.29.0-runtime-error-output-file-verification.md's Test 4 finding
that explicit --output-directory redirection of the *write* location was
never exercised or verified -- this harness does not invent that behavior.

Merely importing this module does nothing -- no gate is checked, no
directory is created, no helper is loaded, at import time. All gating and
preflight logic runs only inside main(), when explicitly invoked.

This module was created/extended, and its gating/preflight logic was tested,
WITHOUT ever supplying both gates simultaneously except for the explicitly
authorized, individually justified real invocations recorded in
planning/v0.35.0-implementation-report.md (and, for the two scenarios
carried over from v0.34.0, planning/v0.34.0-implementation-report.md).
"""

from __future__ import annotations

import argparse
import os
import platform
import sys
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
_MAX_INVOCATION_NUMBER = 5

# Verified, not invented -- see module docstring for provenance of each
# scenario's code and expected_output_files.
_SCENARIOS: dict[str, dict[str, Any]] = {
    "success-basic": {
        "code": "x = 2 + 2;\nprint x;",
        "expected_output_files": (),
        "requires_output_directory": False,
    },
    "success-isolation": {
        "code": "x = 2 + 2;\nprint x;",
        "expected_output_files": (),
        "requires_output_directory": False,
    },
    "output-created": {
        "code": 'output file = gauss_output.txt reset;\nprint "hello output test";\noutput off;',
        "expected_output_files": ("gauss_output.txt",),
        "requires_output_directory": True,
    },
    "output-missing": {
        "code": "x = 2 + 2;\nprint x;",
        "expected_output_files": ("does_not_exist.txt",),
        "requires_output_directory": False,
    },
    "runtime-error": {
        "code": "x = ;",
        "expected_output_files": (),
        "requires_output_directory": False,
    },
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


def _verify_scenario(scenario: str | None) -> bool:
    return scenario is not None and scenario in _SCENARIOS


def _verify_invocation_number(invocation_number: int | None) -> bool:
    return invocation_number is not None and 1 <= invocation_number <= _MAX_INVOCATION_NUMBER


def _verify_output_directory_if_required(scenario: str, output_directory: str | None) -> bool:
    if not _SCENARIOS[scenario]["requires_output_directory"]:
        return True
    if not output_directory:
        return False
    try:
        return Path(output_directory).is_dir()
    except OSError:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Doubly-gated real GAUSS controller-path harness. Drives the full "
            "MockOrchestrationInstance state sequence through exactly one real invocation, "
            "for one explicitly selected scenario, via build_production_adapter_runner(...). "
            "Requires --run-real-gauss AND GAUSS_AI_ALLOW_REAL_EXECUTION=1 simultaneously; "
            "either one missing skips safely without touching GAUSS."
        )
    )
    parser.add_argument("--run-real-gauss", action="store_true", dest="run_real_gauss")
    parser.add_argument("--executable-path", default=None)
    parser.add_argument("--working-directory", default=None)
    parser.add_argument("--output-directory", default=None)
    parser.add_argument("--session-id", default=None)
    parser.add_argument(
        "--scenario",
        choices=sorted(_SCENARIOS.keys()),
        default=None,
        help="Which verified, named scenario to run if both gates are present. Required; no default.",
    )
    parser.add_argument(
        "--invocation-number",
        type=int,
        default=None,
        help=(
            "Caller-declared 1-5 audit label for this real invocation, printed in this run's "
            "evidence output. Not persisted; enforces nothing across separate process invocations."
        ),
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
    print(f"Scenario requested: {args.scenario!r}")
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
    if not _verify_scenario(args.scenario):
        print(
            f"PREFLIGHT FAILED: --scenario is required and must be one of {sorted(_SCENARIOS.keys())}. "
            "No GAUSS was touched."
        )
        return 0
    if not _verify_invocation_number(args.invocation_number):
        print(
            f"PREFLIGHT FAILED: --invocation-number is required and must be an integer from 1 to "
            f"{_MAX_INVOCATION_NUMBER} (caller-declared audit label only). No GAUSS was touched."
        )
        return 0
    if not _verify_output_directory_if_required(args.scenario, args.output_directory):
        print(
            f"PREFLIGHT FAILED: scenario {args.scenario!r} requires --output-directory to be an "
            "existing directory. No GAUSS was touched."
        )
        return 0

    print(
        "Preflight checks passed: platform verified, executable verified as terminal and present, "
        "working directory verified, session id supplied, scenario recognized, invocation number "
        f"in range, output-directory requirement satisfied. invocation_number: "
        f"{args.invocation_number} of {_MAX_INVOCATION_NUMBER} (caller-declared, not persisted)."
    )

    return _run_controller_path(
        executable_path=args.executable_path,
        working_directory=args.working_directory,
        output_directory=args.output_directory,
        session_id=args.session_id,
        scenario=args.scenario,
        invocation_number=args.invocation_number,
    )


def _run_controller_path(
    *,
    executable_path: str,
    working_directory: str,
    output_directory: str | None,
    session_id: str,
    scenario: str,
    invocation_number: int,
) -> int:
    spec = _SCENARIOS[scenario]
    code = spec["code"]
    expected_output_files = spec["expected_output_files"]

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
        request_id=f"v0.35.0-real-controller-{scenario}-{invocation_number}",
        code=code,
        working_directory=working_directory,
        output_directory=output_directory,
        executable_path=executable_path,
        timeout_seconds=30.0,
        expected_output_files=expected_output_files,
        execution_purpose=f"v0.35.0 real execution reliability/output verification ({scenario})",
        environment_summary=env,
        safety_review=safety,
    )

    instance = orch.MockOrchestrationInstance(session_id=session_id, draft=draft)
    print(f"scenario: {scenario}")
    print(f"invocation_number: {invocation_number} of {_MAX_INVOCATION_NUMBER} (caller-declared, not persisted)")
    print(f"orchestration_instance_id: {instance.record.orchestration_instance_id}")
    print(f"session_id: {session_id}")
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
    print(f"expected_output_files: {list(request.expected_output_files)}")

    instance.display_plan()
    print(f"after_display_plan: {instance.record.current_state.value}")

    print(f"confirmation_status_before_authorization: {instance.record.confirmation_status.value}")
    print(f"confirmation_consumption_status_before: {instance.record.confirmation_consumption_status}")

    confirmation = orch.ConfirmationEvent(
        scope=request.request_hash,
        timestamp=f"v0.35.0-real-controller-run-{invocation_number}",
        session_id=session_id,
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
        for f in result.output_files:
            print(
                f"  output_file: path={f.path!r} size_bytes={f.size_bytes!r} "
                f"file_type={f.file_type!r} created_by_execution={f.created_by_execution!r}"
            )
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
    check(
        "scenarios are exactly the five named v0.35.0 scenarios",
        set(_SCENARIOS.keys())
        == {"success-basic", "success-isolation", "output-created", "output-missing", "runtime-error"},
    )
    check(
        "success-basic scenario code matches v0.28.0 Test 3 verified content",
        _SCENARIOS["success-basic"]["code"] == "x = 2 + 2;\nprint x;",
    )
    check(
        "success-isolation scenario code matches v0.28.0 Test 3 verified content (same code, distinct request)",
        _SCENARIOS["success-isolation"]["code"] == "x = 2 + 2;\nprint x;",
    )
    check(
        "output-created scenario code matches v0.29.0 Test 3/4 verified content",
        _SCENARIOS["output-created"]["code"]
        == 'output file = gauss_output.txt reset;\nprint "hello output test";\noutput off;',
    )
    check(
        "output-created scenario declares its own real filename as expected output",
        _SCENARIOS["output-created"]["expected_output_files"] == ("gauss_output.txt",),
    )
    check(
        "output-missing scenario reuses success-basic's verified code",
        _SCENARIOS["output-missing"]["code"] == _SCENARIOS["success-basic"]["code"],
    )
    check(
        "output-missing scenario declares a file the script never creates",
        _SCENARIOS["output-missing"]["expected_output_files"] == ("does_not_exist.txt",),
    )
    check(
        "runtime-error scenario code matches v0.28.0 Test 4 verified content",
        _SCENARIOS["runtime-error"]["code"] == "x = ;",
    )
    check("missing scenario fails preflight", _verify_scenario(None) is False)
    check("unrecognized scenario fails preflight", _verify_scenario("not-a-real-scenario") is False)
    check("recognized scenario passes preflight", _verify_scenario("success-basic") is True)
    check("missing invocation_number fails preflight", _verify_invocation_number(None) is False)
    check("invocation_number 0 fails preflight", _verify_invocation_number(0) is False)
    check("invocation_number 6 fails preflight", _verify_invocation_number(6) is False)
    check("invocation_number 1 passes preflight", _verify_invocation_number(1) is True)
    check("invocation_number 5 passes preflight", _verify_invocation_number(5) is True)
    check(
        "output-created scenario requires an output directory",
        _verify_output_directory_if_required("output-created", None) is False,
    )
    check(
        "success-basic scenario does not require an output directory",
        _verify_output_directory_if_required("success-basic", None) is True,
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
    print("SELF-TEST PASSED: gating, scenario, and preflight logic verified; no GAUSS was touched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
