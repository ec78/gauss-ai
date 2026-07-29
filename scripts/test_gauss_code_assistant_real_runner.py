r"""Tests for opt-in real GAUSS execution in gauss_code_assistant_cli.py.

Default execution of this test file never launches GAUSS. The "real" runner
tests inject a helper callable that behaves like gauss_code_execution so the
adapter boundary can be validated without starting a subprocess.

Optional local smoke:

    python scripts/test_gauss_code_assistant_real_runner.py --run-gauss --gauss-executable C:\gauss26\tgauss.exe
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_code_assistant_cli as cli  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _joined(lines: list[str]) -> str:
    return "\n".join(lines)


def _run(adapter: "cli.InteractiveMvpAdapter", line: str) -> list[str]:
    keep_going, output = adapter.handle_line(line)
    check(f"{line!r} keeps session open", keep_going)
    return output


def _fake_tgauss(tmp: str, name: str = "tgauss.exe") -> str:
    path = Path(tmp) / name
    path.write_text("", encoding="utf-8")
    return str(path)


def _new_real_adapter(tmp: str, helper: Any) -> "cli.InteractiveMvpAdapter":
    return cli.InteractiveMvpAdapter(
        workspace_parent=tmp,
        session_id="real-runner-test",
        clock=lambda: 1000.0,
        runner_backend="gauss",
        gauss_executable=_fake_tgauss(tmp),
        real_helper=helper,
        env={},
    )


def _plan_confirm(adapter: "cli.InteractiveMvpAdapter") -> str:
    _run(adapter, "workspace create")
    _run(adapter, "request x = 2 + 2; print x;")
    plan = _joined(_run(adapter, "plan"))
    check("plan discloses real backend", "execution_backend: REAL_GAUSS" in plan)
    check("plan discloses real execution after confirmation", "real_gauss_will_run_after_confirm_execute: true" in plan)
    check("plan discloses generated script boundary", "script_path: inline code" in plan)
    assert adapter.mvp_session is not None
    assert adapter.mvp_session.proposal_outcome is not None
    assert adapter.mvp_session.proposal_outcome.proposal is not None
    return adapter.mvp_session.proposal_outcome.proposal.request_hash


class RecordingHelper:
    def __init__(self, status: str = "completed", *, executed: bool = True, exit_code: int | None = 0) -> None:
        self.calls: list[dict[str, Any]] = []
        self.status = status
        self.executed = executed
        self.exit_code = exit_code

    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        workdir = Path(kwargs["working_directory"])
        output_path = workdir / "real-helper-output.txt"
        if self.status == "completed":
            output_path.write_text("real helper output fixture\n", encoding="utf-8")
            output_files = [
                {
                    "path": str(output_path),
                    "size_bytes": output_path.stat().st_size,
                    "file_type": "text/plain",
                    "created_by_execution": "real_gauss_helper",
                }
            ]
        else:
            output_files = []

        return {
            "checked": True,
            "executed": self.executed,
            "execution_status": self.status,
            "operating_mode": "execution" if self.executed else "advisory",
            "executable_path": kwargs["executable_path"],
            "gauss_version": kwargs["gauss_version"],
            "working_directory": kwargs["working_directory"],
            "command": f"{kwargs['executable_path']} -b generated.gss" if self.executed else None,
            "code_source": "inline",
            "script_path": None,
            "timeout_seconds": kwargs["timeout_seconds"],
            "elapsed_seconds": 0.25 if self.executed else None,
            "exit_code": self.exit_code,
            "stdout": "stub stdout\n" if self.executed else None,
            "stderr": "stub stderr\n" if self.executed and self.status != "completed" else "",
            "output_files": output_files,
            "warnings": [],
            "errors": [] if self.status == "completed" else ["stub failure"],
            "next_steps": [],
            "raw_execution_details": {"generated_script_path": str(workdir / ".gauss_code_execution_generated" / "inline.gss")},
        }


def test_01_fake_default_still_does_not_import_real_helper() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = cli.InteractiveMvpAdapter(workspace_parent=tmp, session_id="fake-default", env={})
        status = _joined(_run(adapter, "status"))
        check("fake remains default backend", "execution_backend: FAKE" in status)
        check("fake status reports no GAUSS", "gauss_ran: false" in status)
        adapter.close()
    check("gauss_code_execution not imported in fake default", "gauss_code_execution" not in sys.modules)


def test_02_real_runner_requires_executable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            cli.InteractiveMvpAdapter(workspace_parent=tmp, runner_backend="gauss", env={})
        except ValueError as exc:
            check("missing executable blocks real runner", "--gauss-executable or GAUSS_EXECUTABLE" in str(exc))
            return
        check("missing executable raised", False)


def test_03_real_runner_rejects_gui_or_unknown_executable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        bad_path = _fake_tgauss(tmp, name="gauss.exe")
        try:
            cli.InteractiveMvpAdapter(workspace_parent=tmp, runner_backend="gauss", gauss_executable=bad_path, env={})
        except ValueError as exc:
            check("gui executable rejected", "terminal executable" in str(exc))
            return
        check("invalid executable raised", False)


def test_04_cli_arg_takes_precedence_over_environment() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cli_path = _fake_tgauss(tmp, name="tgauss.exe")
        env_path = _fake_tgauss(tmp, name="tgauss-env.exe")
        adapter = cli.InteractiveMvpAdapter(
            workspace_parent=tmp,
            runner_backend="gauss",
            gauss_executable=cli_path,
            real_helper=RecordingHelper(),
            env={"GAUSS_EXECUTABLE": env_path},
        )
        check("cli executable wins over env", adapter.real_gauss_executable == str(Path(cli_path).resolve(strict=False)))
        adapter.close()


def test_05_environment_executable_is_used_when_cli_arg_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env_path = _fake_tgauss(tmp)
        adapter = cli.InteractiveMvpAdapter(
            workspace_parent=tmp,
            runner_backend="gauss",
            real_helper=RecordingHelper(),
            env={"GAUSS_EXECUTABLE": env_path},
        )
        check("env executable selected", adapter.real_gauss_executable == str(Path(env_path).resolve(strict=False)))
        adapter.close()


def test_06_confirmation_required_before_real_helper_invocation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        helper = RecordingHelper()
        adapter = _new_real_adapter(tmp, helper)
        _plan_confirm(adapter)
        out = _joined(_run(adapter, "execute"))
        check("execute before confirm rejected", "MvpWorkflowStageError" in out)
        check("helper not called before confirmation", helper.calls == [])
        adapter.close()


def test_07_stale_confirmation_blocks_real_helper() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        helper = RecordingHelper()
        adapter = _new_real_adapter(tmp, helper)
        _plan_confirm(adapter)
        out = _joined(_run(adapter, "confirm stale"))
        check("stale confirmation rejected", "ConfirmationValidationError" in out)
        check("helper not called after stale confirmation", helper.calls == [])
        adapter.close()


def test_08_real_helper_receives_structured_safe_arguments() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        helper = RecordingHelper()
        adapter = _new_real_adapter(tmp, helper)
        request_hash = _plan_confirm(adapter)
        _run(adapter, f"confirm {request_hash}")
        out = _joined(_run(adapter, "execute"))
        check("real helper selected", "REAL_GAUSS_RUNNER" in out)
        check("GAUSS process reported as started", "gauss_ran: true" in out)
        check("helper called once", len(helper.calls) == 1)
        call = helper.calls[0]
        check("helper received code", call["code"] == "x = 2 + 2; print x;")
        check("helper received strict true", call["strict"] is True)
        check("helper received no network", call["allow_network"] is False)
        check("adapter did not pass shell flag", "shell" not in call)
        adapter.close()


def test_09_real_stdout_stderr_are_metadata_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        adapter = _new_real_adapter(tmp, RecordingHelper())
        request_hash = _plan_confirm(adapter)
        _run(adapter, f"confirm {request_hash}")
        out = _joined(_run(adapter, "execute"))
        check("stdout length reported", "stdout_chars: 12" in out)
        check("stderr length reported", "stderr_chars: 0" in out)
        check("stdout content not printed", "stub stdout" not in out)
        stdout = _joined(_run(adapter, "stdout"))
        check("explicit stdout returns content", "stub stdout" in stdout)
        outputs = _joined(_run(adapter, "outputs"))
        check("output metadata present", "real-helper-output.txt" in outputs)
        check("output content not printed", "real helper output fixture" not in outputs)
        read = _joined(_run(adapter, "read real-helper-output.txt"))
        check("explicit read returns content", "real helper output fixture" in read)
        adapter.close()


def test_10_nonzero_or_failed_result_does_not_fall_back_to_fake() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        helper = RecordingHelper(status="failed", executed=True, exit_code=1)
        adapter = _new_real_adapter(tmp, helper)
        request_hash = _plan_confirm(adapter)
        _run(adapter, f"confirm {request_hash}")
        out = _joined(_run(adapter, "execute"))
        check("failed status surfaced", "execution_status: failed" in out)
        check("exit code surfaced", "exit_code: 1" in out)
        check("still reports real process started", "gauss_ran: true" in out)
        check("no fake fallback", "FAKE_RUNNER" not in out)
        stderr = _joined(_run(adapter, "stderr"))
        check("explicit stderr returns failure content", "stub stderr" in stderr)
        adapter.close()


def test_11_prelaunch_block_reports_gauss_ran_false() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        helper = RecordingHelper(status="blocked", executed=False, exit_code=None)
        adapter = _new_real_adapter(tmp, helper)
        request_hash = _plan_confirm(adapter)
        _run(adapter, f"confirm {request_hash}")
        out = _joined(_run(adapter, "execute"))
        check("blocked status surfaced", "execution_status: blocked" in out)
        check("prelaunch block says gauss did not run", "gauss_ran: false" in out)
        adapter.close()


def test_12_timeout_metadata_and_provenance_are_visible() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        helper = RecordingHelper(status="timed_out", executed=True, exit_code=None)
        adapter = _new_real_adapter(tmp, helper)
        request_hash = _plan_confirm(adapter)
        _run(adapter, f"confirm {request_hash}")
        out = _joined(_run(adapter, "execute"))
        check("timeout surfaced", "timed_out: true" in out)
        provenance = _joined(_run(adapter, "provenance"))
        check("provenance includes real backend", "execution_backend: REAL_GAUSS" in provenance)
        check("provenance includes process started", "gauss_ran: true" in provenance)
        adapter.close()


def run_default_tests() -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        before = len(_failures)
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _failures.append(f"{name} raised an unexpected exception: {type(exc).__name__}: {exc}")
        if len(_failures) == before:
            print(f"PASS  {name}")
        else:
            for failure in _failures[before:]:
                print(f"FAIL  {name}: {failure}")


def run_real_smoke(gauss_executable: str) -> None:
    before = len(_failures)
    with tempfile.TemporaryDirectory() as tmp:
        adapter = cli.InteractiveMvpAdapter(
            workspace_parent=tmp,
            session_id="real-gauss-smoke",
            runner_backend="gauss",
            gauss_executable=gauss_executable,
            gauss_version="GAUSS real local smoke",
            env={},
        )
        request_hash = _plan_confirm(adapter)
        _run(adapter, f"confirm {request_hash}")
        out = _joined(_run(adapter, "execute"))
        check("real smoke invoked process", "gauss_ran: true" in out)
        check("real smoke completed", "execution_status: completed" in out)
        adapter.close()
    if len(_failures) == before:
        print("PASS  optional real GAUSS smoke test")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-gauss", action="store_true", help="Run one explicit local GAUSS smoke test.")
    parser.add_argument("--gauss-executable", default=None, help="Required with --run-gauss.")
    args = parser.parse_args(argv)

    run_default_tests()
    if args.run_gauss:
        if not args.gauss_executable:
            _failures.append("--run-gauss requires --gauss-executable")
        else:
            run_real_smoke(args.gauss_executable)
    else:
        print("SKIP  optional real GAUSS smoke test (--run-gauss not supplied)")

    print()
    print(f"{len(_failures)} check failure(s).")
    if _failures:
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
