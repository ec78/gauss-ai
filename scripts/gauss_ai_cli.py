"""Installed entry point for the productized `gauss-ai` CLI (v0.67.0;
`--export-session` added to `repair` in v0.68.0; `repair`'s guided draft
step gained AI-assisted repair-draft candidates in v0.69.0; the no-
subcommand default changed from the command-by-command REPL to
conversational Q&A in v0.70.0, with the prior REPL relocated, unmodified,
behind a new explicit `repl` subcommand).

`pip install -e .` exposes this module's `main()` as the `gauss-ai` console
script (see `pyproject.toml`). It is a thin dispatcher only -- it duplicates
no CLI implementation. `version`/`doctor`/`init`/`config`/`repair`/`chat`
each call a small, dedicated module (`gauss_ai_config`, `gauss_ai_doctor`,
`gauss_ai_init`, `gauss_ai_guided_repair`, `gauss_ai_chat`); `repl` (and the
bare/no-subcommand path before `v0.70.0`) calls the existing, completely
unmodified `gauss_code_assistant_cli.main(...)` -- `python scripts/
gauss_code_assistant_cli.py` continues to work exactly as before, unaffected
by anything in this module. As of `v0.70.0`, the no-subcommand default is
`chat`, not `repl` -- nothing that worked before is removed; it moved
behind an explicit, discoverable name.
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import platform as platform_module
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_ai_chat as chat_mod  # noqa: E402
import gauss_ai_config as config_mod  # noqa: E402
import gauss_ai_doctor as doctor_mod  # noqa: E402
import gauss_ai_guided_repair as guided_repair_mod  # noqa: E402
import gauss_ai_init as init_mod  # noqa: E402
import gauss_chat_provider as provider_mod  # noqa: E402
import gauss_code_assistant_cli as cli_mod  # noqa: E402
import gauss_environment_check as environment_check_mod  # noqa: E402

__version__ = "0.72.0"


def _cmd_version(args: list[str]) -> int:
    del args
    config = config_mod.load_config()
    env = os.environ
    runner = config_mod.resolve_default_runner(config=config, env=env)
    executable = config_mod.resolve_gauss_executable(config=config, env=env)

    print(f"gauss-ai version: {__version__}")
    print(f"Python: {platform_module.python_version()}")
    print(f"Platform: {platform_module.platform()}")
    print(f"Configured runner: {runner.value} (source: {runner.source})")
    if executable.value:
        version = environment_check_mod.parse_gauss_version(str(executable.value))
        print(f"GAUSS executable: {executable.value} (source: {executable.source})")
        print(f"Detected GAUSS version (parsed from path only; GAUSS was not launched): {version or 'unknown'}")
    else:
        print("GAUSS executable: not configured (run 'gauss-ai init' or 'gauss-ai config set gauss-executable <path>')")
    return 0


def _cmd_doctor(args: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="gauss-ai doctor", add_help=True, description="Read-only environment diagnostics.")
    parser.add_argument("--gauss-executable", default=None)
    parser.add_argument("--workspace-parent", default=None)
    parser.add_argument("--chat-provider", default=None, choices=list(config_mod.VALID_CHAT_PROVIDERS))
    parser.add_argument("--chat-model", default=None)
    parser.add_argument("--ollama-endpoint", default=None, help="Only meaningful when the chat provider is 'ollama'.")
    parsed = parser.parse_args(args)
    report = doctor_mod.run_doctor(
        cli_gauss_executable=parsed.gauss_executable,
        cli_workspace_parent=parsed.workspace_parent,
        cli_chat_provider=parsed.chat_provider,
        cli_chat_model=parsed.chat_model,
        cli_ollama_endpoint=parsed.ollama_endpoint,
    )
    for line in doctor_mod.render_report(report):
        print(line)
    return 0 if report.overall_status != doctor_mod.FAIL else 1


def _cmd_init(args: list[str]) -> int:
    del args
    init_mod.run_init()
    return 0


def _print_config_help() -> None:
    print("Usage: gauss-ai config show")
    print("       gauss-ai config set <key> <value>")
    print("")
    print("Keys:")
    print("  gauss-executable          Path to a terminal (tgauss/tgauss.exe) GAUSS executable")
    print("  workspace-parent          Approved parent directory for repair workspaces")
    print("  default-runner            'fake' or 'gauss' -- default execution backend for 'gauss-ai repair'")
    print("  default-timeout-seconds   Default execution timeout, in seconds")
    print("  chat-provider             'fake', 'ollama', or 'anthropic' -- which model answers conversational questions")
    print("  chat-model                Model name/identifier, meaning depends on chat-provider (see below)")
    print("  docs-root                 Local root of an official GAUSS documentation checkout, for grounding")
    print("  ollama-endpoint           Local Ollama service URL (default: http://localhost:11434)")
    print("  verbose                   'true' or 'false' -- show raw digests/IDs by default")
    print("")
    print("Chat providers, at a glance:")
    print("  fake       No real model, no network, no API key. Default. Echoes retrieved evidence only.")
    print("  ollama     A locally running Ollama model. No API key required. Requires Ollama installed and")
    print("             running (https://ollama.com), and a model pulled, e.g.: ollama pull qwen2.5-coder:7b")
    print("             gauss-ai config set chat-provider ollama")
    print("             gauss-ai config set chat-model qwen2.5-coder:7b")
    print("  anthropic  Anthropic's cloud API. Requires the ANTHROPIC_API_KEY environment variable to be set")
    print("             in your own shell -- gauss-ai never stores or reads it from any config file.")
    print("             gauss-ai config set chat-provider anthropic")
    print("")
    print("Documentation grounding (optional, all providers): without docs-root configured, conversational")
    print("answers about specific GAUSS commands are not grounded in official documentation. See")
    print("docs/conversational-qa.md and docs/gauss-documentation-setup.md for how to obtain and point at one.")
    print("")
    print("Run 'gauss-ai config show' to see your current configuration and its sources, and")
    print("'gauss-ai doctor' to check whether your configured provider is actually reachable.")


def _cmd_config(args: list[str]) -> int:
    if not args or args[0] in {"-h", "--help", "help"}:
        _print_config_help()
        return 0
    sub = args[0]
    if sub == "show":
        config = config_mod.load_config()
        print(f"Config file: {config_mod.config_path()}")
        print(f"  gauss-executable: {config.gauss_executable or '(not set)'}")
        print(f"  default-runner: {config.default_runner or 'fake (default)'}")
        print(f"  workspace-parent: {config.workspace_parent or '(not set)'}")
        print(f"  default-timeout-seconds: {config.default_timeout_seconds if config.default_timeout_seconds is not None else '30.0 (default)'}")
        print(f"  chat-provider: {config.chat_provider or 'fake (default)'}")
        print(f"  chat-model: {config.chat_model or '(provider default)'}")
        print(f"  docs-root: {config.docs_root or '(not set -- conversational answers will not be documentation-grounded)'}")
        print(f"  ollama-endpoint: {config.ollama_endpoint or f'{provider_mod.DEFAULT_OLLAMA_ENDPOINT} (default, only used when chat-provider is ollama)'}")
        print(f"  verbose: {config.verbose}")
        return 0
    if sub == "set":
        if len(args) < 3:
            print("Usage: gauss-ai config set <key> <value>")
            return 2
        key, value = args[1], " ".join(args[2:])
        config = config_mod.load_config()
        if key == "gauss-executable":
            ok, message = config_mod.validate_gauss_executable(value)
            if not ok:
                print(f"ERROR: {message}")
                return 1
            new_config = dataclasses.replace(config, gauss_executable=value)
        elif key == "workspace-parent":
            p = Path(value).expanduser()
            try:
                p.mkdir(parents=True, exist_ok=True)
                probe = p / ".gauss-ai-config-write-check"
                probe.write_text("ok", encoding="utf-8")
                probe.unlink()
            except OSError as exc:
                print(f"ERROR: {p} is not writable: {exc}")
                return 1
            new_config = dataclasses.replace(config, workspace_parent=str(p))
        elif key == "default-runner":
            if value not in config_mod.VALID_RUNNERS:
                print(f"ERROR: default-runner must be one of {config_mod.VALID_RUNNERS}")
                return 1
            new_config = dataclasses.replace(config, default_runner=value)
        elif key == "default-timeout-seconds":
            try:
                timeout = float(value)
            except ValueError:
                print("ERROR: default-timeout-seconds must be a number")
                return 1
            new_config = dataclasses.replace(config, default_timeout_seconds=timeout)
        elif key == "chat-provider":
            if value not in config_mod.VALID_CHAT_PROVIDERS:
                print(f"ERROR: chat-provider must be one of {config_mod.VALID_CHAT_PROVIDERS}")
                return 1
            new_config = dataclasses.replace(config, chat_provider=value)
        elif key == "chat-model":
            new_config = dataclasses.replace(config, chat_model=value)
        elif key == "docs-root":
            new_config = dataclasses.replace(config, docs_root=value)
        elif key == "ollama-endpoint":
            new_config = dataclasses.replace(config, ollama_endpoint=value)
        elif key == "verbose":
            if value.lower() not in {"true", "false"}:
                print("ERROR: verbose must be 'true' or 'false'")
                return 1
            new_config = dataclasses.replace(config, verbose=value.lower() == "true")
        else:
            print(
                f"ERROR: unknown config key {key!r}. Supported: gauss-executable, workspace-parent, "
                "default-runner, default-timeout-seconds, chat-provider, chat-model, docs-root, "
                "ollama-endpoint, verbose"
            )
            return 2
        saved_path = config_mod.save_config(new_config)
        print(f"Saved {key} to {saved_path}")
        return 0
    print(f"Unknown config subcommand: {sub!r}")
    return 2


def _cmd_repair(args: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="gauss-ai repair", add_help=True, description="Guided repair workflow for one .gss file.")
    parser.add_argument("file", help="Path to the .gss file to repair.")
    parser.add_argument("--gauss-executable", default=None)
    parser.add_argument("--runner", default=None, choices=list(config_mod.VALID_RUNNERS))
    parser.add_argument("--workspace-parent", default=None)
    parser.add_argument(
        "--fake-result",
        default=None,
        choices=["success", "failure", "timeout", "unknown_error"],
        help="Fake-runner-only (ignored by --runner gauss): forces the original execution's outcome, "
        "since the fake runner cannot infer success/failure from real file content. Use 'failure' to "
        "demonstrate the repair pipeline in fake mode.",
    )
    parser.add_argument(
        "--export-session",
        default=None,
        metavar="PATH",
        help="Write a read-only diagnostic bundle (config, runner, workspace, and the full session "
        "transcript -- no secrets) to PATH at the end of this run, for attaching to a bug report. "
        "Not a durable session -- written once, at the end of this same process.",
    )
    parsed = parser.parse_args(args)
    adapter = guided_repair_mod.run_guided_repair(
        parsed.file,
        cli_gauss_executable=parsed.gauss_executable,
        cli_runner=parsed.runner,
        cli_workspace_parent=parsed.workspace_parent,
        fake_result=parsed.fake_result,
        export_session=parsed.export_session,
    )
    return 0 if adapter is not None else 2


def _cmd_chat(args: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="gauss-ai",
        add_help=True,
        description="Conversational GAUSS Q&A and code generation (default when no subcommand is given). "
        "Ask a question or ask for GAUSS code -- generated code is always labeled with its documentation-"
        "grounding status and is never executed, verified, or written to a file; see "
        "docs/conversational-code-generation.md. Providers: fake (default, no network/API key), ollama "
        "(local, no API key), anthropic (cloud, needs ANTHROPIC_API_KEY). Run 'gauss-ai config --help' for "
        "the full provider/configuration reference.",
    )
    parser.add_argument("--provider", default=None, choices=list(config_mod.VALID_CHAT_PROVIDERS))
    parser.add_argument("--model", default=None)
    parser.add_argument("--docs-root", default=None)
    parser.add_argument("--ollama-endpoint", default=None, help="Only meaningful with --provider ollama.")
    parsed = parser.parse_args(args)
    engine = chat_mod.run_chat(
        cli_provider=parsed.provider, cli_model=parsed.model, cli_docs_root=parsed.docs_root,
        cli_ollama_endpoint=parsed.ollama_endpoint,
    )
    return 0 if engine is not None else 2


def _launch_repl(argv: list[str]) -> int:
    """Resolves gauss-ai's own configuration precedence (CLI arg > env var >
    config file > default) for the three settings the underlying REPL
    launcher accepts, then calls the EXISTING, unmodified
    `gauss_code_assistant_cli.main(...)` with the resolved values passed
    through as ordinary CLI arguments -- never a second implementation of
    argument parsing or adapter construction."""
    extractor = argparse.ArgumentParser(add_help=False)
    extractor.add_argument("--workspace-parent", default=None)
    extractor.add_argument("--runner", default=None)
    extractor.add_argument("--gauss-executable", default=None)
    known, _ = extractor.parse_known_args(argv)

    config = config_mod.load_config()
    env = os.environ
    resolved_runner = config_mod.resolve_default_runner(cli_value=known.runner, config=config, env=env)
    resolved_workspace = config_mod.resolve_workspace_parent(cli_value=known.workspace_parent, config=config, env=env)
    resolved_executable = config_mod.resolve_gauss_executable(cli_value=known.gauss_executable, config=config, env=env)

    final_argv = list(argv)
    if known.runner is None and resolved_runner.value:
        final_argv += ["--runner", str(resolved_runner.value)]
    if known.workspace_parent is None and resolved_workspace.value:
        final_argv += ["--workspace-parent", str(resolved_workspace.value)]
    if known.gauss_executable is None and resolved_executable.value:
        final_argv += ["--gauss-executable", str(resolved_executable.value)]
    return cli_mod.main(final_argv)


def _print_top_help() -> None:
    print("gauss-ai -- GAUSS Code Assistant alpha CLI")
    print("")
    print("Commands:")
    print("  gauss-ai                              Launch conversational GAUSS Q&A and code generation (default)")
    print("  gauss-ai chat [--provider ...] [--model ...] [--docs-root ...]   Same, explicit form")
    print("  gauss-ai version                     Show version and environment info")
    print("  gauss-ai doctor                       Read-only environment diagnostics")
    print("  gauss-ai init                         Guided first-run setup (idempotent)")
    print("  gauss-ai config show                  Show current configuration")
    print("  gauss-ai config set <key> <value>     Set one configuration value")
    print("  gauss-ai config --help                Full configuration and chat-provider reference")
    print("  gauss-ai repair <file.gss> [--export-session PATH]  Guided repair workflow for one file")
    print("  gauss-ai repl [--runner ...] [...]      Launch the full command-by-command workflow REPL (advanced)")
    print("")
    print("No API key? Try a local model: gauss-ai config set chat-provider ollama  (see 'gauss-ai config --help')")
    print(
        "Config keys: gauss-executable, workspace-parent, default-runner, default-timeout-seconds, "
        "chat-provider, chat-model, docs-root, ollama-endpoint, verbose"
    )
    print("Run 'python scripts/gauss_code_assistant_cli.py' directly for the exact same REPL without installing.")


def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    if argv and argv[0] in {"-h", "--help", "help"}:
        _print_top_help()
        return 0
    if argv and not argv[0].startswith("-"):
        command, rest = argv[0], argv[1:]
        if command == "version":
            return _cmd_version(rest)
        if command == "doctor":
            return _cmd_doctor(rest)
        if command == "init":
            return _cmd_init(rest)
        if command == "config":
            return _cmd_config(rest)
        if command == "repair":
            return _cmd_repair(rest)
        if command == "chat":
            return _cmd_chat(rest)
        if command == "repl":
            return _launch_repl(rest)
    return _cmd_chat(argv)


if __name__ == "__main__":
    raise SystemExit(main())
