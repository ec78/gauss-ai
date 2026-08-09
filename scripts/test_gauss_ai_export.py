"""Tests for the `--export-session` diagnostic bundle (v0.68.0).

Run with:

    python scripts/test_gauss_ai_export.py

No test touches the real `~/.gauss-ai/config.json`; every bundle is built
and written to a real temp-directory path. No test launches GAUSS.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_ai_config as config_mod  # noqa: E402
import gauss_ai_export as export_mod  # noqa: E402
import gauss_ai_guided_repair as guided_mod  # noqa: E402
import gauss_code_assistant_cli as cli  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _new_adapter(tmp: str) -> "cli.InteractiveMvpAdapter":
    return cli.InteractiveMvpAdapter(workspace_parent=tmp, session_id="export-test", clock=lambda: 1000.0)


def _broken_gss(tmp: str) -> Path:
    p = Path(tmp) / "broken.gss"
    p.write_bytes(b"x = 2 + 2\nprint x;\n")
    return p


def _scripted(answers: list[str]):
    queue = list(answers)

    def _prompt(_question: str) -> str:
        if not queue:
            raise AssertionError("prompt_fn called more times than answers were scripted")
        return queue.pop(0)

    return _prompt


_HAPPY_PATH_ANSWERS = [
    "y", "y", "1", "1", "insert missing semicolon", "Add missing semicolon", "x = 2 + 2;",
    "y", "y", "y", "y", "accepted", "",
]


# ---------------------------------------------------------------------------
# build_diagnostic_bundle / write_diagnostic_bundle
# ---------------------------------------------------------------------------


def test_01_build_diagnostic_bundle_has_expected_keys() -> None:
    bundle = export_mod.build_diagnostic_bundle(
        transcript=["line 1", "line 2"], config=config_mod.GaussAiConfig(), runner_backend="fake",
        gauss_executable=None, workspace_id="ws-1", workspace_root="/tmp/ws-1",
    )
    expected_keys = {
        "gauss_ai_version", "python_version", "platform", "configuration", "runner_backend",
        "gauss_executable_used", "gauss_version_from_path", "workspace_id", "workspace_root", "session_transcript",
    }
    check("bundle has exactly the documented top-level keys", set(bundle.keys()) == expected_keys)
    check("configuration sub-dict has exactly the five config fields", set(bundle["configuration"].keys()) == {"gauss_executable", "default_runner", "workspace_parent", "default_timeout_seconds", "verbose"})
    check("session_transcript carries the real transcript", bundle["session_transcript"] == ["line 1", "line 2"])


def test_02_gauss_version_parsed_from_path_when_executable_given() -> None:
    bundle = export_mod.build_diagnostic_bundle(
        transcript=[], config=config_mod.GaussAiConfig(), runner_backend="gauss",
        gauss_executable="C:/gauss26/tgauss.exe", workspace_id=None, workspace_root=None,
    )
    check("version parsed from a real path string", bundle["gauss_version_from_path"] == "26")


def test_03_gauss_version_none_when_no_executable_configured() -> None:
    bundle = export_mod.build_diagnostic_bundle(
        transcript=[], config=config_mod.GaussAiConfig(), runner_backend="fake",
        gauss_executable=None, workspace_id=None, workspace_root=None,
    )
    check("no executable -> no version guess fabricated", bundle["gauss_version_from_path"] is None)


def test_04_bundle_never_contains_a_secret_shaped_field() -> None:
    bundle = export_mod.build_diagnostic_bundle(
        transcript=[], config=config_mod.GaussAiConfig(), runner_backend="fake",
        gauss_executable=None, workspace_id=None, workspace_root=None,
    )
    flattened = json.dumps(bundle).lower()
    for forbidden in ("password", "secret", "token", "license_key", "api_key", "credential"):
        check(f"bundle JSON never contains the substring {forbidden!r}", forbidden not in flattened)


def test_05_write_diagnostic_bundle_creates_file_and_parent_dirs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "nested" / "dir" / "bundle.json"
        bundle = export_mod.build_diagnostic_bundle(
            transcript=["a"], config=config_mod.GaussAiConfig(), runner_backend="fake",
            gauss_executable=None, workspace_id=None, workspace_root=None,
        )
        written = export_mod.write_diagnostic_bundle(bundle, target)
        check("returns the same path", written == target)
        check("file was actually created", target.is_file())
        reloaded = json.loads(target.read_text(encoding="utf-8"))
        check("written content round-trips as valid JSON matching the bundle", reloaded == bundle)


# ---------------------------------------------------------------------------
# Wiring through run_guided_repair -- real end-to-end
# ---------------------------------------------------------------------------


def test_06_export_session_writes_a_real_bundle_for_a_real_guided_run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        export_path = Path(tmp) / "export.json"
        guided_mod.run_guided_repair(
            source, adapter=adapter, prompt_fn=_scripted(_HAPPY_PATH_ANSWERS), print_fn=lambda *_: None,
            fake_result="failure", export_session=export_path,
        )
        check("the export file was created", export_path.is_file())
        bundle = json.loads(export_path.read_text(encoding="utf-8"))
        check("runner_backend reflects the real adapter", bundle["runner_backend"] == "fake")
        check("workspace_id matches the real active workspace", bundle["workspace_id"] == adapter.active_workspace_id)
        check("transcript is non-empty and contains real evidence", any("current_status: verification_reviewed:accepted" in line for line in bundle["session_transcript"]))
        adapter.close()


def test_07_no_export_session_writes_nothing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        before = set(Path(tmp).rglob("*"))
        guided_mod.run_guided_repair(
            source, adapter=adapter, prompt_fn=_scripted(_HAPPY_PATH_ANSWERS), print_fn=lambda *_: None,
            fake_result="failure",
        )
        after = set(Path(tmp).rglob("*"))
        new_json_files = [p for p in (after - before) if p.suffix == ".json"]
        check("no diagnostic bundle appears anywhere when --export-session was not requested", new_json_files == [])
        adapter.close()


def test_08_export_session_does_not_change_the_repair_outcome() -> None:
    """Read-only proof: the same scripted run produces the identical
    outcome whether or not export_session is requested."""
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        source1 = _broken_gss(tmp1)
        adapter1 = _new_adapter(tmp1)
        guided_mod.run_guided_repair(
            source1, adapter=adapter1, prompt_fn=_scripted(_HAPPY_PATH_ANSWERS), print_fn=lambda *_: None,
            fake_result="failure",
        )
        outcome_without_export = adapter1.last_application_result.outcome
        adapter1.close()

        source2 = _broken_gss(tmp2)
        adapter2 = _new_adapter(tmp2)
        guided_mod.run_guided_repair(
            source2, adapter=adapter2, prompt_fn=_scripted(_HAPPY_PATH_ANSWERS), print_fn=lambda *_: None,
            fake_result="failure", export_session=Path(tmp2) / "export.json",
        )
        outcome_with_export = adapter2.last_application_result.outcome
        adapter2.close()

        check("outcome is identical with and without --export-session", outcome_without_export == outcome_with_export == "applied")


def test_09_export_session_terminal_output_is_unaffected() -> None:
    """Recording for export must never alter what a real terminal user
    sees: every line the guided workflow prints during a single run must
    be forwarded to the real print_fn unchanged, plus exactly one extra
    confirmation line at the very end. Comparing across two SEPARATE
    adapter instances would be meaningless here (each generates its own
    random workspace/draft/application IDs independent of exporting), so
    this compares the recorded transcript against the print_fn calls
    actually observed within the SAME run."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _broken_gss(tmp)
        adapter = _new_adapter(tmp)
        export_path = Path(tmp) / "export.json"
        printed: list[str] = []
        guided_mod.run_guided_repair(
            source, adapter=adapter, prompt_fn=_scripted(_HAPPY_PATH_ANSWERS), print_fn=printed.append,
            fake_result="failure", export_session=export_path,
        )
        adapter.close()
        bundle = json.loads(export_path.read_text(encoding="utf-8"))
        transcript = bundle["session_transcript"]

        check("every recorded transcript line was also actually printed, in order", printed[: len(transcript)] == transcript)
        check("exactly one extra line (the export confirmation) was printed after the transcript", len(printed) == len(transcript) + 1)
        check("the extra line confirms the export and is NOT itself part of the recorded transcript", printed[-1].startswith("Diagnostic bundle written to") and printed[-1] not in transcript)


# ---------------------------------------------------------------------------
# Architectural: read-only, no engine of its own
# ---------------------------------------------------------------------------


def test_10_export_module_performs_no_execution_or_repair_logic() -> None:
    source = Path(export_mod.__file__).read_text(encoding="utf-8")
    forbidden = (
        "def execute(", "def apply_repair(", "def propose_execution(", "def evaluate_application_gate(",
        "def interpret_execution(", "def diagnose_execution(", "def plan_repair(", "subprocess",
    )
    for token in forbidden:
        check(f"export module does not define/call {token!r}", token not in source)


def test_11_export_module_never_reads_arbitrary_files() -> None:
    """Structural proof the export module only ever WRITES the bundle file
    itself -- it has no code path that reads any other file from disk."""
    source = Path(export_mod.__file__).read_text(encoding="utf-8")
    check("module contains no .read_text(/.read_bytes( call", ".read_text(" not in source and ".read_bytes(" not in source)


def run_tests() -> int:
    tests = [
        (name, fn)
        for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    for name, fn in tests:
        before = len(_failures)
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _failures.append(f"{name} raised {type(exc).__name__}: {exc}")
        if len(_failures) == before:
            print(f"PASS  {name}")
        else:
            for failure in _failures[before:]:
                print(f"FAIL  {name}: {failure}")
    print(f"\n{len(tests)} test function(s) run, {len(_failures)} check failure(s).")
    if _failures:
        print("SOME CHECKS FAILED.")
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
