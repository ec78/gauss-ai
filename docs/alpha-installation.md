# Alpha Installation Guide

**Status: Alpha — intended for controlled testing.**

This guide covers installing and configuring the productized `gauss-ai` CLI (`v0.67.0`). It supersedes nothing — the lower-level `python scripts/gauss_code_assistant_cli.py` REPL described in [docs/manual-alpha-testing-guide.md](manual-alpha-testing-guide.md) continues to work exactly as before and remains available for advanced/debugging use.

## Prerequisites

- **Python 3.10 or newer.** Verified on Python 3.12; the codebase uses no syntax requiring a newer version, but only 3.10+ has been exercised.
- **A clone of this repository.** `gauss-ai` is not published to a package index; installation is always from a local checkout (`pip install -e .` or `pip install .`).
- **GAUSS, optional.** Fake-mode testing (the default) requires no GAUSS installation at all. Real-mode testing requires a local, terminal (non-interactive) GAUSS installation — see "GAUSS Requirements" below.

## Supported Operating System

**Windows** is the only environment this repository's real-GAUSS execution path has been verified against (GAUSS 26.1.1, confirmed non-interactive batch invocation via `tgauss.exe -b`; see `planning/v0.28.0-real-gauss-invocation-research.md`). Fake-mode testing (packaging, CLI, the full guided workflow, doctor, init, config) has no OS-specific dependency and should work on any platform Python 3.10+ supports, but only Windows has been used to verify this milestone's own packaging and CLI behavior. Do not assume macOS/Linux real-GAUSS execution is supported — it is not yet verified.

## GAUSS Requirements

Real-mode execution requires the **terminal** GAUSS executable — `tgauss` or `tgauss.exe` — never the GUI `gauss`/`gauss.exe`/`wgauss`/`wgauss.exe` executables, which cannot run non-interactively. `gauss-ai config set gauss-executable <path>`, `gauss-ai init`, and `gauss-ai doctor` all validate this explicitly and reject a GUI executable with a clear error. This repository's own verified evidence covers **GAUSS 26.1.1**; other GAUSS 24/25/26 installations may work (the environment-detection logic supports them) but are not independently verified by this milestone.

## Installation

From the repository root:

```
pip install -e .
```

This is an **editable install** — the installed `gauss-ai` command continues to run the exact files in your cloned checkout; there is nothing to reinstall after pulling a new commit. A non-editable install also works if you prefer a fixed snapshot:

```
pip install .
```

Both install a single console-script entry point, `gauss-ai`, plus every existing `scripts/gauss_*.py` module as a directly importable top-level module (no dotted package namespace — this mirrors how the modules already import each other internally). No repository files are moved or restructured by installation.

**Using a virtual environment is recommended** but not required:

```
python -m venv .venv
.venv\Scripts\activate          (Windows)
source .venv/bin/activate       (macOS/Linux, untested for real-GAUSS execution)
pip install -e .
```

## Verify the install

```
gauss-ai version
```

Should print the `gauss-ai` version, your Python version, platform, and configured runner (`fake` by default) — with no GAUSS installation required.

If `gauss-ai` is not found on your `PATH` after installation, your virtual environment's `Scripts`/`bin` directory may not be activated, or your shell may need to be restarted. `python scripts/gauss_code_assistant_cli.py` (run from the repository root) always works as a fallback and requires no installation at all.

## Configuration

`gauss-ai` stores at most seven settings and one display preference in a single local file: `~/.gauss-ai/config.json` (i.e. `Path.home() / ".gauss-ai" / "config.json"` — never a hard-coded, user-specific path). No secrets, license credentials, API keys, or arbitrary key/value data are ever stored there.

Configuration precedence, most to least authoritative:

1. An explicit CLI argument (e.g. `--gauss-executable`, `--runner`, `--workspace-parent`, `--provider`, `--model`, `--docs-root`)
2. An environment variable (`GAUSS_EXECUTABLE`, `GAUSS_AI_DEFAULT_RUNNER`, `GAUSS_AI_WORKSPACE_PARENT`, `GAUSS_AI_TIMEOUT_SECONDS`, `GAUSS_AI_CHAT_PROVIDER`, `GAUSS_AI_CHAT_MODEL`, `GAUSS_AI_DOCS_ROOT`)
3. The local config file
4. A safe default (`default_runner=fake`, `default_timeout_seconds=30.0`, `chat_provider=fake`, no configured executable, workspace parent, chat model, or docs root)

Set values individually:

```
gauss-ai config show
gauss-ai config set gauss-executable C:\gauss26\tgauss.exe
gauss-ai config set workspace-parent C:\Users\you\gauss-ai-workspaces
gauss-ai config set default-runner fake
gauss-ai config set chat-provider fake
gauss-ai config set docs-root C:\path\to\your\gauss-docs\checkout
```

`gauss-ai config set gauss-executable <path>` validates the path exists and is a terminal executable before saving — an invalid or GUI path is rejected with a clear error, and nothing is written. See [docs/conversational-qa.md](conversational-qa.md) for the three chat-related settings (`chat-provider`, `chat-model`, `docs-root`) in full, including how a real provider's API key is configured (an environment variable, never a config setting).

## First-run setup

```
gauss-ai init
```

Guides you through reviewing/setting a workspace-parent directory, discovering (never silently choosing) a GAUSS executable, and setting a default runner. Safe to run again at any time — it reviews and updates existing configuration, it never resets or corrupts it. See [docs/alpha-quickstart.md](alpha-quickstart.md) for a full first-run walkthrough.

## Doctor

```
gauss-ai doctor
```

Read-only environment diagnostics: Python version, core module imports, workspace-parent writability, GAUSS executable configuration and validity, configuration-file validity, and installed package version. Reports `PASS`/`WARN`/`FAIL` per check with actionable next steps. Never runs GAUSS, never installs anything, never changes your configuration.

## Fake-mode testing

The default. No GAUSS installation is used or required:

```
gauss-ai repair examples/alpha-demo/broken.gss --fake-result failure
```

See [docs/alpha-quickstart.md](alpha-quickstart.md) for the full walkthrough and expected output.

## Real-mode testing

Requires a configured, valid terminal GAUSS executable (see "Configuration" above):

```
gauss-ai repair <your-file.gss> --runner gauss
```

Or set `default-runner gauss` in configuration to make it the default. Every execution still requires the exact same explicit `confirm`/`execute` sequence fake mode does — real mode changes only which runner ultimately executes the code, never how many approvals are required.

## Not Supported in This Milestone

macOS/Linux real-GAUSS execution, GAUSS versions other than what this repository has directly verified, cloud execution, multi-file repair, autonomous repair, and production deployment. See [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md) for the complete, current list.
