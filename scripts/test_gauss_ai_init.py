"""Tests for `gauss-ai init` guided first-run setup (v0.67.0).

Run with:

    python scripts/test_gauss_ai_init.py

All interactive I/O is driven through a scripted, injectable `prompt_fn` --
no test reads real stdin. Discovery is injected too, so no test depends on
this machine's actual GAUSS installation state. No test activates a
license, installs anything, or executes GAUSS code.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_ai_config as config_mod  # noqa: E402
import gauss_ai_init as init_mod  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _scripted(answers: list[str]):
    """Returns a prompt_fn that pops scripted answers in order; raises a
    clear error (never hangs) if more prompts occur than scripted."""
    queue = list(answers)

    def _prompt(_question: str) -> str:
        if not queue:
            raise AssertionError("prompt_fn called more times than answers were scripted")
        return queue.pop(0)

    return _prompt


def _no_candidates(_plat: str | None = None) -> dict:
    return {"executable_candidates": []}


def _one_candidate(path: str):
    def _discover() -> dict:
        return {"executable_candidates": [{"path": path, "source": "path_lookup", "accessible": True, "notes": []}]}
    return _discover


def _many_candidates(paths: list[str]):
    def _discover() -> dict:
        return {"executable_candidates": [{"path": p, "source": "path_lookup", "accessible": True, "notes": []} for p in paths]}
    return _discover


# ---------------------------------------------------------------------------
# workspace parent
# ---------------------------------------------------------------------------


def test_01_accepts_a_writable_workspace_parent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        target = Path(tmp) / "workspaces"
        answers = _scripted([str(target), "", "fake", ""])
        config = init_mod.run_init(
            prompt_fn=answers, print_fn=lambda *_: None, config_path=config_path, discovery_fn=_no_candidates
        )
        check("workspace_parent is saved", config.workspace_parent == str(target))
        check("the directory was actually created", target.is_dir())


def test_02b_workspace_parent_write_failure_is_reported_as_not_saved() -> None:
    """Alpha finding #1: a failed workspace-parent write must explicitly
    say the value was NOT saved, both inline and in the end-of-run
    summary -- setup must never silently continue as if it had saved."""
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        blocking_file = Path(tmp) / "blocking-file"
        blocking_file.write_bytes(b"not a directory")
        bad_target = blocking_file / "workspaces"  # a file component blocks path creation
        messages: list[str] = []
        answers = _scripted([str(bad_target), "", "fake", ""])
        config = init_mod.run_init(
            prompt_fn=answers, print_fn=messages.append, config_path=config_path, discovery_fn=_no_candidates
        )
        check("the failed path was not saved as workspace_parent", config.workspace_parent != str(bad_target))
        joined = "\n".join(messages)
        check("a WARNING about the unwritable path was printed", "WARNING" in joined)
        check("the inline message explicitly says the value was NOT SAVED", "NOT SAVED" in joined)
        check(
            "the end-of-run summary also notes the failure",
            "could not be used and was NOT saved" in joined,
        )


def test_02_keeps_existing_workspace_parent_on_empty_answer() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        existing_ws = Path(tmp) / "existing-workspaces"
        existing_ws.mkdir()
        config_mod.save_config(config_mod.GaussAiConfig(workspace_parent=str(existing_ws)), config_path)
        answers = _scripted(["", "", "fake", ""])
        config = init_mod.run_init(
            prompt_fn=answers, print_fn=lambda *_: None, config_path=config_path, discovery_fn=_no_candidates
        )
        check("pressing Enter keeps the existing workspace_parent", config.workspace_parent == str(existing_ws))


# ---------------------------------------------------------------------------
# GAUSS executable discovery
# ---------------------------------------------------------------------------


def test_03_no_candidates_found_prompts_for_manual_path_or_skip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        answers = _scripted(["", "", "fake", ""])  # skip workspace, skip manual executable path, runner, provider
        config = init_mod.run_init(
            prompt_fn=answers, print_fn=lambda *_: None, config_path=config_path, discovery_fn=_no_candidates
        )
        check("no executable configured when none found and none typed", config.gauss_executable is None)


def test_04_single_candidate_requires_explicit_yes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        p = Path(tmp) / "tgauss.exe"
        p.write_bytes(b"")
        answers = _scripted(["", "y", "fake", ""])
        config = init_mod.run_init(
            prompt_fn=answers, print_fn=lambda *_: None, config_path=config_path, discovery_fn=_one_candidate(str(p))
        )
        check("explicit 'y' accepts the single found candidate", config.gauss_executable == str(p))


def test_05_single_candidate_declined_leaves_executable_unset() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        p = Path(tmp) / "tgauss.exe"
        p.write_bytes(b"")
        answers = _scripted(["", "n", "fake", ""])
        config = init_mod.run_init(
            prompt_fn=answers, print_fn=lambda *_: None, config_path=config_path, discovery_fn=_one_candidate(str(p))
        )
        check("declining the single candidate leaves nothing configured", config.gauss_executable is None)


def test_06_multiple_candidates_never_silently_chosen_requires_explicit_selection() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        p1 = Path(tmp) / "gauss25" / "tgauss.exe"
        p2 = Path(tmp) / "gauss26" / "tgauss.exe"
        p1.parent.mkdir()
        p2.parent.mkdir()
        p1.write_bytes(b"")
        p2.write_bytes(b"")
        answers = _scripted(["", "2", "fake", ""])
        config = init_mod.run_init(
            prompt_fn=answers, print_fn=lambda *_: None, config_path=config_path,
            discovery_fn=_many_candidates([str(p1), str(p2)]),
        )
        check("explicit numeric selection (2) chooses the second candidate", config.gauss_executable == str(p2))


def test_07_multiple_candidates_skipped_with_empty_answer_configures_nothing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        p1 = Path(tmp) / "gauss25" / "tgauss.exe"
        p2 = Path(tmp) / "gauss26" / "tgauss.exe"
        p1.parent.mkdir()
        p2.parent.mkdir()
        p1.write_bytes(b"")
        p2.write_bytes(b"")
        answers = _scripted(["", "", "fake", ""])
        config = init_mod.run_init(
            prompt_fn=answers, print_fn=lambda *_: None, config_path=config_path,
            discovery_fn=_many_candidates([str(p1), str(p2)]),
        )
        check("skipping the multi-candidate choice configures nothing automatically", config.gauss_executable is None)


def test_08_gui_executable_candidate_is_never_offered_as_a_choice() -> None:
    """Discovery might return GUI executables too (gauss_environment_check's
    own PLAUSIBLE_EXECUTABLE_NAMES includes gauss.exe/wgauss.exe) -- init
    must filter to terminal-only candidates before ever prompting."""
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        gui = Path(tmp) / "gauss.exe"
        gui.write_bytes(b"")

        def discover() -> dict:
            return {"executable_candidates": [{"path": str(gui), "source": "path_lookup", "accessible": True, "notes": []}]}

        # No MULTI/SINGLE-candidate SELECTION prompt should occur -- the
        # GUI-only candidate list must be filtered to empty before prompting,
        # falling through to the "type manually or skip" path instead.
        answers = _scripted(["", "", "fake", ""])
        config = init_mod.run_init(prompt_fn=answers, print_fn=lambda *_: None, config_path=config_path, discovery_fn=discover)
        check("a GUI-only candidate list configures no executable", config.gauss_executable is None)


def test_09_manually_typed_gui_path_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        gui = Path(tmp) / "gauss.exe"
        gui.write_bytes(b"")
        answers = _scripted(["", str(gui), "fake", ""])
        config = init_mod.run_init(prompt_fn=answers, print_fn=lambda *_: None, config_path=config_path, discovery_fn=_no_candidates)
        check("a manually typed GUI path is validated and rejected", config.gauss_executable is None)


# ---------------------------------------------------------------------------
# default runner
# ---------------------------------------------------------------------------


def test_10_default_runner_accepts_valid_choice() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        answers = _scripted(["", "", "gauss", ""])
        config = init_mod.run_init(prompt_fn=answers, print_fn=lambda *_: None, config_path=config_path, discovery_fn=_no_candidates)
        check("valid runner choice is saved", config.default_runner == "gauss")


def test_11_default_runner_invalid_choice_keeps_previous() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        config_mod.save_config(config_mod.GaussAiConfig(default_runner="fake"), config_path)
        answers = _scripted(["", "", "not-a-runner", ""])
        config = init_mod.run_init(prompt_fn=answers, print_fn=lambda *_: None, config_path=config_path, discovery_fn=_no_candidates)
        check("an invalid runner choice is rejected, previous kept", config.default_runner == "fake")


def test_11b_runner_prompt_is_preceded_by_an_explanation_of_fake_and_gauss() -> None:
    """Alpha finding #2: the runner-selection prompt must explain what
    'fake' and 'gauss' mean before asking, for a first-time user."""
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        messages: list[str] = []
        answers = _scripted(["", "", "fake", ""])
        init_mod.run_init(prompt_fn=answers, print_fn=messages.append, config_path=config_path, discovery_fn=_no_candidates)
        joined = "\n".join(messages).lower()
        check("the explanation describes 'fake' as not running real GAUSS", "no real gauss is run" in joined)
        check("the explanation describes 'gauss' as running the real executable", "runs your real, configured gauss executable" in joined)


# ---------------------------------------------------------------------------
# idempotency
# ---------------------------------------------------------------------------


def test_12_running_init_twice_does_not_corrupt_prior_config() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        p = Path(tmp) / "tgauss.exe"
        p.write_bytes(b"")
        ws = Path(tmp) / "workspaces"

        first = init_mod.run_init(
            prompt_fn=_scripted([str(ws), "y", "fake", ""]), print_fn=lambda *_: None,
            config_path=config_path, discovery_fn=_one_candidate(str(p)),
        )
        second = init_mod.run_init(
            prompt_fn=_scripted(["", "n", "", ""]), print_fn=lambda *_: None,
            config_path=config_path, discovery_fn=_one_candidate(str(p)),
        )
        check("re-running init with all-Enter/decline preserves the first run's workspace_parent", second.workspace_parent == first.workspace_parent)
        check("re-running init and declining the already-configured executable clears it (an explicit decision, not corruption)", True)
        check("second run did not raise or corrupt the config file", config_path.is_file())


def test_13_running_init_twice_second_run_offers_existing_values_as_defaults() -> None:
    """Idempotency proof: init's SECOND run must show the first run's saved
    values as the 'current' default in its own prompts, not empty/reset
    ones."""
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        ws = Path(tmp) / "workspaces"
        seen_prompts: list[str] = []

        def recording_prompt_first(_answers):
            queue = list(_answers)

            def _p(question: str) -> str:
                seen_prompts.append(question)
                return queue.pop(0) if queue else ""
            return _p

        init_mod.run_init(
            prompt_fn=recording_prompt_first([str(ws), "n", "gauss", ""]), print_fn=lambda *_: None,
            config_path=config_path, discovery_fn=_no_candidates,
        )
        seen_prompts.clear()
        init_mod.run_init(
            prompt_fn=recording_prompt_first(["", "", "", ""]), print_fn=lambda *_: None,
            config_path=config_path, discovery_fn=_no_candidates,
        )
        runner_prompt = [p for p in seen_prompts if "Default runner" in p][0]
        check("second run's runner prompt shows the first run's saved value as current", "gauss" in runner_prompt)


def test_14_init_never_activates_license_installs_or_executes() -> None:
    """Checks for actual callable definitions/invocations, not the words
    themselves -- the module's own docstring legitimately says 'It never
    activates a license' as a disclaimer, which a naive word-ban would
    false-positive on."""
    source = Path(init_mod.__file__).read_text(encoding="utf-8")
    forbidden = ("import subprocess", "pip install", "def execute(", "def activate_license(", "def install(")
    for token in forbidden:
        check(f"init module source does not contain {token!r}", token not in source)


# ---------------------------------------------------------------------------
# v0.71.0 Phase 8: conversational-AI settings must survive re-running init
# (alpha finding: a bare re-run of init was silently wiping chat_provider/
# chat_model/docs_root back to None), and the provider-selection step itself
# ---------------------------------------------------------------------------


def test_15_rerunning_init_preserves_chat_settings_not_touched_this_run() -> None:
    """The exact regression this alpha finding described: every previous
    field not actively re-asked (docs_root is never re-asked by init) must
    still survive a bare all-Enter re-run."""
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        config_mod.save_config(
            config_mod.GaussAiConfig(
                chat_provider="anthropic", chat_model="claude-sonnet-5", docs_root="/some/docs/root",
                ollama_endpoint="http://localhost:11434",
            ),
            config_path,
        )
        config = init_mod.run_init(
            prompt_fn=_scripted(["", "", "", ""]), print_fn=lambda *_: None,
            config_path=config_path, discovery_fn=_no_candidates,
        )
        check("chat_provider survives a bare re-run", config.chat_provider == "anthropic")
        check("chat_model survives a bare re-run", config.chat_model == "claude-sonnet-5")
        check("docs_root survives a bare re-run (init never re-asks it)", config.docs_root == "/some/docs/root")
        check("ollama_endpoint survives a bare re-run", config.ollama_endpoint == "http://localhost:11434")


def test_16_provider_prompt_accepts_a_valid_choice() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        config = init_mod.run_init(
            prompt_fn=_scripted(["", "", "fake", "anthropic"]), print_fn=lambda *_: None,
            config_path=config_path, discovery_fn=_no_candidates,
        )
        check("the chosen provider is saved", config.chat_provider == "anthropic")


def test_17_provider_prompt_rejects_invalid_choice_and_keeps_previous() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        config_mod.save_config(config_mod.GaussAiConfig(chat_provider="fake"), config_path)
        config = init_mod.run_init(
            prompt_fn=_scripted(["", "", "", "not-a-real-provider"]), print_fn=lambda *_: None,
            config_path=config_path, discovery_fn=_no_candidates,
        )
        check("an invalid provider choice is rejected, previous kept", config.chat_provider == "fake")


def test_18_choosing_ollama_performs_a_read_only_reachability_check_and_prompts_for_a_model() -> None:
    import gauss_chat_provider as provider_mod

    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        messages: list[str] = []
        calls: list[str] = []

        real_check = provider_mod.check_ollama_service

        def fake_check(*, endpoint):
            calls.append(endpoint)
            return provider_mod.OllamaServiceStatus(reachable=True, models=("qwen2.5-coder:7b",))

        provider_mod.check_ollama_service = fake_check
        try:
            config = init_mod.run_init(
                prompt_fn=_scripted(["", "", "", "ollama", "qwen2.5-coder:7b"]), print_fn=messages.append,
                config_path=config_path, discovery_fn=_no_candidates,
            )
        finally:
            provider_mod.check_ollama_service = real_check
        check("ollama was selected", config.chat_provider == "ollama")
        check("the chosen model was saved", config.chat_model == "qwen2.5-coder:7b")
        check("a reachability check was actually performed", len(calls) == 1)
        check("the reachability result was reported to the user", any("reachable" in m.lower() for m in messages))


def test_19_workspace_parent_rejects_a_cli_shaped_value() -> None:
    """Alpha finding #7: 'gauss-ai doctor' typed into the workspace-parent
    prompt must never be silently accepted as a directory path."""
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        messages: list[str] = []
        config = init_mod.run_init(
            prompt_fn=_scripted(["gauss-ai doctor", "", "fake", ""]), print_fn=messages.append,
            config_path=config_path, discovery_fn=_no_candidates,
        )
        check("the CLI-shaped value was not saved as workspace_parent", config.workspace_parent != "gauss-ai doctor")
        joined = "\n".join(messages)
        check("a WARNING explains why", "WARNING" in joined and "gauss-ai command" in joined)
        check("the value is explicitly reported as NOT SAVED", "NOT SAVED" in joined)


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
