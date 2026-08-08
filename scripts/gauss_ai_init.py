"""Idempotent first-run setup for the productized `gauss-ai` CLI (v0.67.0),
exposed as `gauss-ai init`.

Guides a new user through safe local setup: reviewing/confirming a
workspace-parent directory, discovering and confirming (never silently
choosing) a GAUSS executable, and setting a default runner. All interactive
I/O goes through injectable `prompt_fn`/`print_fn` parameters so this module
is fully testable without a real terminal.

It never activates a license, never installs GAUSS, never installs a
package, never modifies global GAUSS configuration, and never executes
GAUSS code. `gauss_environment_check.detect_environment(...)` is reused for
discovery -- this module defines no discovery logic of its own. When more
than one plausible terminal executable is found, the user must explicitly
choose one; none is ever picked automatically.

Idempotent: running `gauss-ai init` again reads the existing configuration
first and offers it as the default answer to every question (press Enter to
keep) -- it reviews and updates, it never corrupts or silently resets prior
configuration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import gauss_ai_config as config_mod
import gauss_environment_check as environment_check_mod


def _terminal_candidates(discovery_result: dict) -> list[dict]:
    candidates = discovery_result.get("executable_candidates", [])
    return [c for c in candidates if Path(c["path"]).name.lower() in {"tgauss", "tgauss.exe"}]


def run_init(
    *,
    prompt_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
    config_path: Path | None = None,
    discovery_fn: Callable[[], dict] | None = None,
) -> "config_mod.GaussAiConfig":
    """Runs the interactive setup flow and returns the saved config. Safe to
    call repeatedly -- see module docstring."""
    discovery_fn = discovery_fn or environment_check_mod.detect_environment
    existing = config_mod.load_config(config_path)

    print_fn("GAUSS AI Assistant -- first-run setup (safe to re-run at any time)")
    print_fn("")

    # -- workspace parent --------------------------------------------------
    print_fn(f"Approved workspace parent directory (current: {existing.workspace_parent or 'not set'})")
    answer = prompt_fn("  Enter a path to use, or press Enter to keep the current setting: ").strip()
    workspace_parent = existing.workspace_parent
    if answer:
        candidate = Path(answer).expanduser()
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".gauss-ai-init-write-check"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            workspace_parent = str(candidate)
            print_fn(f"  OK: {candidate} is writable.")
        except OSError as exc:
            print_fn(f"  WARNING: {candidate} is not writable ({exc}); keeping the previous setting.")

    # -- GAUSS executable ----------------------------------------------------
    print_fn("")
    print_fn(f"GAUSS executable (current: {existing.gauss_executable or 'not set'})")
    gauss_executable = existing.gauss_executable
    result = discovery_fn()
    candidates = _terminal_candidates(result)
    if len(candidates) == 1:
        path = candidates[0]["path"]
        answer = prompt_fn(f"  Found a candidate terminal executable: {path}\n  Use this? [y/N]: ").strip().lower()
        if answer == "y":
            ok, message = config_mod.validate_gauss_executable(path)
            if ok:
                gauss_executable = path
                print_fn(f"  OK: {message}")
            else:
                print_fn(f"  Not using it: {message}")
    elif len(candidates) > 1:
        print_fn("  Multiple candidate terminal executables were found -- none is chosen automatically:")
        for i, c in enumerate(candidates, start=1):
            print_fn(f"    [{i}] {c['path']}")
        answer = prompt_fn("  Enter a number to select one, or press Enter to skip: ").strip()
        if answer:
            try:
                index = int(answer) - 1
                if 0 <= index < len(candidates):
                    path = candidates[index]["path"]
                    ok, message = config_mod.validate_gauss_executable(path)
                    if ok:
                        gauss_executable = path
                        print_fn(f"  OK: {message}")
                    else:
                        print_fn(f"  Not using it: {message}")
                else:
                    print_fn("  Not a valid selection; keeping the previous setting.")
            except ValueError:
                print_fn("  Not a valid selection; keeping the previous setting.")
    else:
        print_fn("  No terminal GAUSS executable was auto-detected.")
        answer = prompt_fn(
            "  Enter a path manually, or press Enter to skip (fake-mode testing remains fully available): "
        ).strip()
        if answer:
            ok, message = config_mod.validate_gauss_executable(answer)
            if ok:
                gauss_executable = answer
                print_fn(f"  OK: {message}")
            else:
                print_fn(f"  Not using it: {message}")

    # -- default runner -------------------------------------------------
    print_fn("")
    default_runner = existing.default_runner
    answer = prompt_fn(f"  Default runner, 'fake' or 'gauss' (current: {default_runner or 'fake (default)'}): ").strip().lower()
    if answer in config_mod.VALID_RUNNERS:
        default_runner = answer
    elif answer:
        print_fn(f"  '{answer}' is not 'fake' or 'gauss'; keeping the previous setting.")

    new_config = config_mod.GaussAiConfig(
        gauss_executable=gauss_executable,
        default_runner=default_runner,
        workspace_parent=workspace_parent,
        default_timeout_seconds=existing.default_timeout_seconds,
        verbose=existing.verbose,
    )
    saved_path = config_mod.save_config(new_config, config_path)

    print_fn("")
    print_fn(f"Configuration saved to {saved_path}")
    print_fn("Next steps:")
    print_fn("  gauss-ai doctor           -- verify this configuration")
    print_fn("  gauss-ai repair <file.gss> -- guided repair of a specific file")
    print_fn("  gauss-ai                 -- the full interactive command set")
    return new_config
