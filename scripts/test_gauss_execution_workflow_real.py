"""Doubly-gated REAL GAUSS conversational-workflow harness (v0.37.0
Conversational Execution Workflow Integration).

THIS FILE CAN INVOKE REAL GAUSS. It is not a default test. It must never be
run as part of `python scripts/test_gauss_execution_workflow.py`,
`python scripts/test_gauss_runtime_orchestration.py`,
`python scripts/check_release_readiness.py`, or any CI workflow -- none of
those import or execute this file, and this file requires two independent,
explicit opt-in gates before it will do anything beyond print a skip notice:

    1. The command-line flag --run-real-gauss
    2. The environment variable GAUSS_AI_ALLOW_REAL_EXECUTION=1

BOTH are required simultaneously. Either one missing means this harness
skips safely without touching GAUSS, without invoking the Helper Adapter,
and without importing scripts/gauss_code_execution.py.

Unlike scripts/test_gauss_runtime_orchestration_real.py (v0.34.0/v0.35.0),
which drives scripts/gauss_runtime_orchestration.py's MockOrchestrationInstance
directly, this harness drives the FULL conversational execution-workflow
layer added in v0.37.0 -- scripts/gauss_execution_workflow.py's
ExecutionWorkflow -- end to end:

    ExecutionWorkflow.propose_execution(...)   (eligibility + safety + exact plan)
    -> ExecutionWorkflow.confirm_execution(...) (request_hash-bound confirmation)
    -> ExecutionWorkflow.execute(..., runner=build_production_adapter_runner(...))
    -> ExecutionWorkflow.inspect(...)           (response-ready result readback)

using a disposable, temporary SQLite-backed OrchestrationStateStore (never
the default repository-relative `.gauss_orchestration_state/` location) and
`gauss_runtime_orchestration.build_production_adapter_runner(...)` as the one
injected real runner per process invocation.

Exactly ONE named scenario is selected per explicit invocation via
--scenario (no default, no "run everything" mode) -- each real process
invocation of this file performs at most one real GAUSS call, for one
caller-selected scenario, with a fresh proposal, a fresh confirmation, and a
fresh durable store every time. An explicit --invocation-number (1-3, this
milestone's own authorized budget) must also be supplied when both gates are
present, purely as a caller-declared audit label printed in this run's own
evidence output -- it is NOT persisted anywhere and enforces nothing across
separate process invocations.

Verified inline code used by this harness (never invented, never
user-suppliable through this file) -- byte-for-byte identical to the
scenarios already real-verified through the bare controller in v0.35.0
(scripts/test_gauss_runtime_orchestration_real.py), reused here to verify
the NEW conversational-workflow layer relays the same real, already-trusted
GAUSS behavior correctly end to end, not to test new GAUSS syntax:

- "success" scenario: "x = 2 + 2;\\nprint x;" -- byte-for-byte Test 3
  ("Scalar calculation") from planning/v0.28.0-real-gauss-invocation-research.md.
- "runtime-error" scenario: "x = ;" -- byte-for-byte Test 4 ("Intentional
  syntax error") from planning/v0.28.0-real-gauss-invocation-research.md:
  confirmed to exit non-interactively with exit_code 0, stdout "Program
  execute failed", and stderr containing "error G0105".
- "output-created" scenario: 'output file = gauss_output.txt reset;\\nprint
  "hello output test";\\noutput off;' -- byte-for-byte the idiom verified in
  planning/v0.29.0-runtime-error-output-file-verification.md and reused
  unmodified by v0.35.0's own "output-created" scenario. --output-directory
  must be supplied as the SAME directory as --working-directory, matching
  the actually-verified behavior that `output_directory` only affects
  post-execution discovery, never the subprocess's own working directory.

Merely importing this module does nothing -- no gate is checked, no
directory is created, no helper is loaded, at import time. All gating and
preflight logic runs only inside main(), when explicitly invoked.
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

# Safe to import unconditionally -- neither module has an import-time
# execution side effect (see each module's own docstring).
import gauss_execution_workflow as wf  # noqa: E402
import gauss_orchestration_state_store as store_mod  # noqa: E402
import gauss_runtime_orchestration as orch  # noqa: E402

ENV_VAR_NAME = "GAUSS_AI_ALLOW_REAL_EXECUTION"
REQUIRED_ENV_VALUE = "1"
FLAG_NAME = "--run-real-gauss"

_VERIFIED_PLATFORM = "Windows"
_SUPPORTED_EXECUTABLE_BASENAMES = frozenset({"tgauss", "tgauss.exe"})
_MAX_INVOCATION_NUMBER = 3  # this milestone's own authorized real-invocation budget

_SCENARIOS: dict[str, dict[str, Any]] = {
    "success": {
        "code": "x = 2 + 2;\nprint x;",
        "expected_output_files": (),
        "requires_output_directory": False,
    },
    "runtime-error": {
        "code": "x = ;",
        "expected_output_files": (),
        "requires_output_directory": False,
    },
    "output-created": {
        "code": 'output file = gauss_output.txt reset;\nprint "hello output test";\noutput off;',
        "expected_output_files": ("gauss_output.txt",),
        "requires_output_directory": True,
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
            "Doubly-gated real GAUSS conversational-workflow harness. Drives "
            "ExecutionWorkflow.propose_execution -> confirm_execution -> execute -> inspect "
            "through exactly one real invocation, for one explicitly selected scenario, via "
            "build_production_adapter_runner(...). Requires --run-real-gauss AND "
            "GAUSS_AI_ALLOW_REAL_EXECUTION=1 simultaneously; either one missing skips safely "
            "without touching GAUSS."
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
            "Caller-declared 1-3 audit label for this real invocation (this milestone's own "
            "authorized budget), printed in this run's evidence output. Not persisted; enforces "
            "nothing across separate process invocations."
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
    print("REAL GAUSS EXECUTION IS ENABLED FOR THIS RUN (full conversational workflow path).")
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

    return _run_workflow_path(
        executable_path=args.executable_path,
        working_directory=args.working_directory,
        output_directory=args.output_directory,
        session_id=args.session_id,
        scenario=args.scenario,
        invocation_number=args.invocation_number,
    )


def _passing_safety_input() -> "wf.SafetyReviewInput":
    return wf.SafetyReviewInput(
        code_shown_or_summarized=True,
        purpose_understood=True,
        does_not_delete_files=True,
        does_not_overwrite_unrelated_files=True,
        does_not_install_packages=True,
        does_not_activate_licenses=True,
        does_not_access_network=True,
        does_not_mutate_global_configuration=True,
        file_writes_relative_or_within_allowed_directory=True,
        working_directory_exists_and_safe=True,
        output_directory_within_allowed_scope=True,
        executable_is_terminal_gauss=True,
        timeout_is_set=True,
    )


def _run_workflow_path(
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

    with tempfile.TemporaryDirectory(prefix="gauss-ai-v037-state-") as state_dir:
        db_path = Path(state_dir) / "orchestration.db"
        print(f"disposable_state_db_path: {db_path}")
        store = store_mod.OrchestrationStateStore(db_path)
        store.initialize()
        workflow = wf.ExecutionWorkflow(state_store=store)

        request_id = f"v0.37.0-real-workflow-{scenario}-{invocation_number}"
        outcome = workflow.propose_execution(
            session_id=session_id,
            request_id=request_id,
            execution_purpose=f"v0.37.0 conversational execution workflow integration real verification ({scenario})",
            eligibility_declarations=wf.EligibilityDeclarations(execution_explicitly_requested=True),
            safety_input=_passing_safety_input(),
            code=code,
            working_directory=working_directory,
            output_directory=output_directory,
            executable_path=executable_path,
            gauss_version="GAUSS 26",
            timeout_seconds=30.0,
            expected_output_files=expected_output_files,
        )
        print(f"scenario: {scenario}")
        print(f"invocation_number: {invocation_number} of {_MAX_INVOCATION_NUMBER} (caller-declared, not persisted)")
        print(f"orchestration_instance_id: {outcome.orchestration_instance_id}")
        print(f"session_id: {session_id}")
        print(f"proposal_blocked: {outcome.blocked}")

        if outcome.blocked:
            print(f"BLOCKED before confirmation: {outcome.failure_category} -- {outcome.failure_reason}. No GAUSS was touched.")
            store.close()
            return 0

        proposal = outcome.proposal
        assert proposal is not None
        print(f"request_id (canonical): {proposal.request_id}")
        print(f"request_hash: {proposal.request_hash}")
        print(f"plan_digest: {proposal.plan_digest}")
        print(f"code_digest (not raw code): {proposal.code_digest}")
        print(f"expected_output_files: {list(proposal.expected_output_files)}")
        print(f"eligibility_passed: {proposal.eligibility_passed}")
        print(f"safety_review_outcome: {proposal.safety_review.outcome}")

        confirmation = workflow.confirm_execution(
            wf.WorkflowConfirmationEvent(
                session_id=session_id,
                orchestration_instance_id=outcome.orchestration_instance_id,
                request_id=request_id,
                request_hash=proposal.request_hash,
                decision="accepted",
                timestamp=f"v0.37.0-real-workflow-run-{invocation_number}",
                source_interaction_id=f"real-verification-turn-{invocation_number}",
                plan_digest=proposal.plan_digest,
            )
        )
        print(f"confirmation_current_state: {confirmation.current_state}")
        print(f"confirmation_accepted: {confirmation.accepted}")

        real_runner = orch.build_production_adapter_runner(request_identity=proposal.request_hash)

        result = workflow.execute(outcome.orchestration_instance_id, runner=real_runner)
        print(f"executed: {result.executed}")
        print(f"final_orchestration_state: {result.final_orchestration_state}")
        print(f"helper_invocation_status: {result.helper_invocation_status}")
        print(f"execution_status: {result.execution_status}")
        print(f"exit_code (non-authoritative, exit_code_is_authoritative={result.exit_code_is_authoritative}): {result.exit_code}")
        print(f"runtime_error_detected: {result.runtime_error_detected}")
        print(f"timed_out: {result.timed_out}")
        print(f"missing_expected_output: {result.missing_expected_output}")
        print(f"output_file_count (metadata only): {result.output_file_count}")
        for f in result.output_files:
            print(
                f"  output_file: path={f.path!r} size_bytes={f.size_bytes!r} "
                f"file_type={f.file_type!r} created_by_execution={f.created_by_execution!r}"
            )
        print(f"failure_category: {result.failure_category}")
        print(f"analysis_status: {result.analysis_status}")
        print(f"report_status: {result.report_status}")
        print(f"limitations: {list(result.limitations)}")
        print(f"methodology_caveat: {result.methodology_caveat}")
        print(f"rerun_requires_new_request: {result.rerun_requires_new_request}")

        inspected = workflow.inspect(outcome.orchestration_instance_id)
        print(f"inspect_matches_execute_execution_status: {inspected.execution_status == result.execution_status}")
        print(f"inspect_matches_execute_exit_code: {inspected.exit_code == result.exit_code}")

        print(f"durable_safe_summary: {store.safe_summary(outcome.orchestration_instance_id)}")
        store.close()
    return 0


# ---------------------------------------------------------------------------
# Self-test: gating/preflight logic only. Never supplies both gates
# simultaneously, never calls build_production_adapter_runner, never calls
# _run_workflow_path.
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
        "scenarios are exactly the three named v0.37.0 scenarios",
        set(_SCENARIOS.keys()) == {"success", "runtime-error", "output-created"},
    )
    check(
        "success scenario code matches v0.28.0 Test 3 verified content (reused from v0.35.0)",
        _SCENARIOS["success"]["code"] == "x = 2 + 2;\nprint x;",
    )
    check(
        "runtime-error scenario code matches v0.28.0 Test 4 verified content (reused from v0.35.0)",
        _SCENARIOS["runtime-error"]["code"] == "x = ;",
    )
    check(
        "output-created scenario code matches v0.29.0 verified content (reused from v0.35.0)",
        _SCENARIOS["output-created"]["code"]
        == 'output file = gauss_output.txt reset;\nprint "hello output test";\noutput off;',
    )
    check("missing scenario fails preflight", _verify_scenario(None) is False)
    check("unrecognized scenario fails preflight", _verify_scenario("not-a-real-scenario") is False)
    check("recognized scenario passes preflight", _verify_scenario("success") is True)
    check("missing invocation_number fails preflight", _verify_invocation_number(None) is False)
    check("invocation_number 0 fails preflight", _verify_invocation_number(0) is False)
    check("invocation_number 4 fails preflight (budget is 1-3)", _verify_invocation_number(4) is False)
    check("invocation_number 1 passes preflight", _verify_invocation_number(1) is True)
    check("invocation_number 3 passes preflight", _verify_invocation_number(3) is True)
    check(
        "output-created scenario requires an output directory",
        _verify_output_directory_if_required("output-created", None) is False,
    )
    check(
        "success scenario does not require an output directory",
        _verify_output_directory_if_required("success", None) is True,
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
