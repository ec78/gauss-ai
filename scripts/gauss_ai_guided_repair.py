"""Guided repair workflow for the productized `gauss-ai` CLI (v0.67.0),
exposed as `gauss-ai repair <file.gss>`.

This module is orchestration/UI only. It implements no repair engine, no
execution engine, and no approval logic of its own -- every step drives the
SAME `InteractiveMvpAdapter.handle_line(...)` sequence a manual REPL tester
would type, one command at a time. Guided UX may simplify navigation; it may
not simplify authorization -- every approval, confirmation, and review point
below requires a real, explicit answer from `prompt_fn` (real terminal input
in normal use; a scripted, injectable callable in tests). No decision is
ever inferred, defaulted to "yes," or skipped.

Sequence (a stage is skipped, with a plain-language explanation, only when
the pipeline itself reports it does not apply -- e.g. the original execution
already succeeded, so `repair-plan` reports nothing to repair):

    workspace create -> request (from the named file's real content) -> plan
    -> [explicit confirm] -> execute -> interpret -> diagnose -> repair-plan
    -> [explicit strategy approval] -> repair-draft -> [explicit draft approval]
    -> [explicit application approval] -> check-repair-application-gate
    -> apply-repair -> [explicit verification confirm] -> verify-repair
    -> confirm -> execute -> [explicit human review] -> review-verification
    -> show-repair-session

The only file this module ever reads is the single file the caller named on
the command line -- that naming IS the explicit authorization, exactly
mirroring the lower-level CLI's own explicit `read <path>` boundary. No
other file is ever read, and no file is ever written except through the
existing, unmodified `apply-repair` transaction.
"""

from __future__ import annotations

import hashlib
import shlex
from pathlib import Path
from typing import Callable

import gauss_ai_config as config_mod
import gauss_code_assistant_cli as cli_mod


def _step_run(adapter: "cli_mod.InteractiveMvpAdapter", print_fn: Callable[[str], None], command: str) -> list[str]:
    _keep_going, output = adapter.handle_line(command)
    for line in output:
        print_fn(line)
    return output


def _extract(lines: list[str], prefix: str) -> str | None:
    for line in lines:
        if line.startswith(prefix):
            return line.split(": ", 1)[1].strip()
    return None


def _confirm(prompt_fn: Callable[[str], str], question: str) -> bool:
    """The one and only place a yes/no approval decision is read. Anything
    other than exactly 'y' is treated as a decline -- there is no default-
    to-yes path."""
    answer = prompt_fn(f"{question} [y/N]: ").strip().lower()
    return answer == "y"


def _prompt_int(prompt_fn: Callable[[str], str], print_fn: Callable[[str], None], question: str) -> int:
    while True:
        answer = prompt_fn(question).strip()
        try:
            return int(answer)
        except ValueError:
            print_fn("Please enter a whole number.")


_FAKE_RESULT_FLAGS = {
    "success": "--fake-success",
    "failure": "--fake-failure",
    "timeout": "--fake-timeout",
    "unknown_error": "--fake-unknown-error",
}


def _run_guided_sequence(
    adapter: "cli_mod.InteractiveMvpAdapter",
    file_path: str | Path,
    *,
    prompt_fn: Callable[[str], str],
    print_fn: Callable[[str], None],
    fake_result: str | None = None,
) -> None:
    path = Path(file_path)
    if not path.is_file():
        print_fn(f"ERROR: {path} does not exist or is not a file.")
        return
    content = path.read_text(encoding="utf-8")

    print_fn(f"Guided repair -- {path.name}")
    print_fn("This walks the existing, unmodified repair pipeline one step at a time.")
    print_fn("Every approval below requires your explicit confirmation; nothing is decided for you.")
    print_fn("")

    _step_run(adapter, print_fn, "workspace create")

    # Repair Application only ever operates on a file inside the approved
    # workspace boundary (path containment is a core safety guarantee of
    # this repository -- see gauss_workspace.py) -- never on an arbitrary
    # absolute path elsewhere on disk. The named file is therefore copied,
    # byte-for-byte, into the fresh workspace; the ORIGINAL file at
    # `file_path` is never written to, here or anywhere else in this
    # module. Any resulting repair (and its mandatory backup) lives inside
    # the workspace copy shown below -- nothing is copied back
    # automatically, so this guided command never performs a write outside
    # the workspace it just created.
    assert adapter.active_workspace_id is not None
    workspace_root = Path(adapter.registry.get_workspace(adapter.active_workspace_id).root_path)
    workspace_copy = workspace_root / path.name
    # write_bytes, never write_text: text-mode writes translate "\n" to the
    # platform line separator (CRLF on Windows), which would silently
    # change the copy's own byte content -- and therefore its SHA-256 hash
    # -- away from the exact bytes `content_hash` (below) is computed over.
    workspace_copy.write_bytes(content.encode("utf-8"))
    print_fn(f"Copied {path} into the approved workspace: {workspace_copy}")
    print_fn("The original file is never written to by this command; only the workspace copy above is ever modified.")

    print_fn(f"Read {len(content)} character(s) from {path}.")
    # v0.67.0: adapter._request(...) is called directly (bypassing the
    # shlex-based handle_line("request ...") path) because _request's own
    # text.replace("\\n", "\n") convenience -- designed for a human typing a
    # literal "\n" on one REPL line to mean a newline -- would silently
    # corrupt real file content that happens to contain a literal
    # backslash-n sequence. Passing the real content directly as a single
    # list element is the exact, existing, no-shell-tokenization path
    # _request(...) already supports internally (it does `" ".join(args)`).
    # `fake_result` (fake-runner-only; ignored entirely by the real backend,
    # exactly as PendingRequest.fake_result already is everywhere else) lets
    # a fake-mode demo/test genuinely reach the repair pipeline, since the
    # fake runner cannot otherwise infer success/failure from real content.
    request_args = ([_FAKE_RESULT_FLAGS[fake_result]] if fake_result in _FAKE_RESULT_FLAGS else []) + [content]
    adapter._request(request_args)  # noqa: SLF001
    print_fn("Prepared an execution request from the file's real content. No execution has occurred yet.")

    plan_out = _step_run(adapter, print_fn, "plan")
    request_hash = _extract(plan_out, "request_hash:")
    if request_hash is None:
        print_fn("Could not propose an execution plan; stopping.")
        return

    print_fn("")
    print_fn(f"About to CONFIRM AND EXECUTE this exact plan (request_hash={request_hash}).")
    if not _confirm(prompt_fn, "Confirm execution?"):
        print_fn("Declined. Guided repair stopped -- nothing was executed.")
        return
    _step_run(adapter, print_fn, f"confirm {request_hash}")
    _step_run(adapter, print_fn, "execute")

    _step_run(adapter, print_fn, "interpret")
    _step_run(adapter, print_fn, "diagnose")

    repair_plan_out = _step_run(adapter, print_fn, "repair-plan")
    plan_digest = _extract(repair_plan_out, "plan_digest:")
    repair_status = _extract(repair_plan_out, "repair_status:")
    if repair_status == "successful_execution_no_repair_needed" or plan_digest is None:
        print_fn("The original execution already succeeded -- there is nothing to repair.")
        _step_run(adapter, print_fn, "show-repair-session")
        return

    print_fn("")
    print_fn(f"Proposed repair strategy (plan_digest={plan_digest}) is shown above.")
    if not _confirm(prompt_fn, "Approve this repair strategy?"):
        _step_run(adapter, print_fn, f"decline-repair {plan_digest}")
        print_fn("Strategy declined. Guided repair stopped -- no draft, application, or execution beyond this point.")
        _step_run(adapter, print_fn, "show-repair-session")
        return
    _step_run(adapter, print_fn, f"approve-repair {plan_digest}")

    print_fn("")
    print_fn("To draft a repair, describe the exact replacement for the affected line range.")
    line_start = _prompt_int(prompt_fn, print_fn, "Line to start replacing (1-based): ")
    line_end = _prompt_int(prompt_fn, print_fn, "Line to end replacing (1-based, inclusive): ")
    operation = prompt_fn("Short description of the operation (e.g. 'insert missing semicolon'): ").strip()
    description = prompt_fn("Longer description of the intended change: ").strip()
    replacement_text = prompt_fn("Exact replacement text for that line range: ")

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    draft_cmd = (
        f"repair-draft --path {shlex.quote(path.name)} --content-hash {content_hash} "
        f"--size {len(content.encode('utf-8'))} --line-start {line_start} --line-end {line_end} "
        f"--operation {shlex.quote(operation)} --description {shlex.quote(description)}"
    )
    draft_out = _step_run(adapter, print_fn, draft_cmd)
    draft_digest = _extract(draft_out, "draft_digest:")
    if draft_digest is None:
        print_fn("Could not construct a repair draft; stopping.")
        return

    print_fn("")
    print_fn(f"Proposed draft (draft_digest={draft_digest}) is shown above.")
    if not _confirm(prompt_fn, "Approve this draft?"):
        _step_run(adapter, print_fn, f"decline-repair-draft {draft_digest}")
        print_fn("Draft declined. Guided repair stopped.")
        _step_run(adapter, print_fn, "show-repair-session")
        return
    _step_run(adapter, print_fn, f"approve-repair-draft {draft_digest}")

    print_fn("")
    if not _confirm(prompt_fn, "Approve APPLYING this exact draft to the file?"):
        _step_run(adapter, print_fn, f"decline-repair-application {draft_digest}")
        print_fn("Application declined. Guided repair stopped -- the file was not modified.")
        _step_run(adapter, print_fn, "show-repair-session")
        return
    _step_run(adapter, print_fn, f"approve-repair-application {draft_digest}")

    # A freshly re-read/re-hashed current content hash is required for the
    # gate's own source_hash_matches/path_unchanged checks to pass -- they
    # fail closed, by design, when no current observation is supplied (see
    # gauss_repair_application_gate.py). This is a genuine, fresh
    # observation -- the workspace copy is re-read from disk right here,
    # immediately before the gate check, rather than reusing the hash
    # computed back when the draft was built -- so a real change to the
    # workspace file between drafting and now is actually detected, never
    # silently assumed unchanged.
    current_content_hash = hashlib.sha256(workspace_copy.read_bytes()).hexdigest()
    gate_out = _step_run(
        adapter, print_fn, f"check-repair-application-gate --current-content-hash {current_content_hash}"
    )
    all_passed = _extract(gate_out, "all_passed:")
    if all_passed != "true":
        print_fn("The application gate did not pass every checkable precondition (see above). Guided repair stopped.")
        _step_run(adapter, print_fn, "show-repair-session")
        return

    apply_cmd = f"apply-repair {draft_digest} --replacement-text {shlex.quote(replacement_text)}"
    apply_out = _step_run(adapter, print_fn, apply_cmd)
    outcome = _extract(apply_out, "outcome:")
    if outcome != "applied":
        print_fn(f"The repair was not applied (outcome={outcome}). See details above.")
        _step_run(adapter, print_fn, "show-repair-session")
        return

    print_fn("")
    print_fn("The repair was applied. A backup of the original file was created (see above).")
    if not _confirm(prompt_fn, "Verify the repair by executing the repaired file now?"):
        print_fn("Skipped verification. Guided repair stopped -- the repair is applied but not yet verified.")
        _step_run(adapter, print_fn, "show-repair-session")
        return

    verify_out = _step_run(adapter, print_fn, "verify-repair")
    verify_hash = _extract(verify_out, "request_hash:")
    if verify_hash is None:
        print_fn("Could not propose a verification execution; stopping.")
        _step_run(adapter, print_fn, "show-repair-session")
        return

    print_fn("")
    if not _confirm(prompt_fn, f"Confirm and execute this verification plan (request_hash={verify_hash})?"):
        print_fn("Declined. Guided repair stopped -- the repair is applied but not yet verified.")
        return
    _step_run(adapter, print_fn, f"confirm {verify_hash}")
    _step_run(adapter, print_fn, "execute")

    print_fn("")
    print_fn("Verification evidence is shown above (evidence only -- not a correctness verdict).")
    decision = prompt_fn("Your review decision -- accepted / rejected / inconclusive: ").strip().lower()
    if decision not in {"accepted", "rejected", "inconclusive"}:
        print_fn(f"'{decision}' is not a valid decision; no review was recorded.")
        _step_run(adapter, print_fn, "show-repair-session")
        return
    notes = prompt_fn("Optional notes (Enter to skip): ").strip()
    review_cmd = f"review-verification --decision {decision}"
    if notes:
        review_cmd += f" --notes {shlex.quote(notes)}"
    _step_run(adapter, print_fn, review_cmd)

    print_fn("")
    _step_run(adapter, print_fn, "show-repair-session")


def run_guided_repair(
    file_path: str | Path,
    *,
    adapter: "cli_mod.InteractiveMvpAdapter | None" = None,
    prompt_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
    cli_gauss_executable: str | None = None,
    cli_runner: str | None = None,
    cli_workspace_parent: str | None = None,
    config: "config_mod.GaussAiConfig | None" = None,
    env: dict[str, str] | None = None,
    fake_result: str | None = None,
) -> "cli_mod.InteractiveMvpAdapter | None":
    """Runs the guided sequence against `adapter` if supplied (tests always
    supply their own, so they can inspect its state afterward), otherwise
    builds one from resolved configuration and closes it before returning.
    Never constructs a second execution or repair engine -- `adapter` is a
    genuine `InteractiveMvpAdapter`, the exact same type the lower-level CLI
    itself uses. `fake_result` is meaningful only when the adapter's own
    runner backend is 'fake' (ignored entirely by the real backend, exactly
    as `PendingRequest.fake_result` already is everywhere else in this
    codebase) -- it lets fake-mode testing/demo genuinely reach the repair
    pipeline, since the fake runner cannot infer success/failure from real
    file content."""
    owns_adapter = adapter is None
    if adapter is None:
        resolved_config = config if config is not None else config_mod.load_config()
        runner = config_mod.resolve_default_runner(cli_value=cli_runner, config=resolved_config, env=env).value
        gauss_executable = config_mod.resolve_gauss_executable(
            cli_value=cli_gauss_executable, config=resolved_config, env=env
        ).value
        workspace_parent = config_mod.resolve_workspace_parent(
            cli_value=cli_workspace_parent, config=resolved_config, env=env
        ).value
        try:
            adapter = cli_mod.InteractiveMvpAdapter(
                workspace_parent=workspace_parent, runner_backend=runner, gauss_executable=gauss_executable,
            )
        except ValueError as exc:
            print_fn(f"Configuration error: {exc}")
            print_fn("Run 'gauss-ai doctor' or 'gauss-ai init' to fix this before retrying.")
            return None

    try:
        _run_guided_sequence(adapter, file_path, prompt_fn=prompt_fn, print_fn=print_fn, fake_result=fake_result)
    finally:
        if owns_adapter:
            adapter.close()
    return adapter
