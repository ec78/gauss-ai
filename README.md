# GAUSS AI

<!-- mcp-name: io.github.ec78/gauss-ai -->

**GAUSS AI** helps an AI assistant work with the [GAUSS](https://www.aptech.com/) programming language without guessing. It runs on your machine as an MCP server (for Claude Code, Claude Desktop and other MCP clients) and as a command-line tool, `gauss-ai`.

- **Search the official GAUSS documentation**, downloaded once to your machine, and read any page or section in full.
- **Check GAUSS code deterministically**: documented call signatures, documented preconditions (for example, `invpd` needs a symmetric positive-definite matrix), syntax, unknown or invented functions, and statements that reach outside GAUSS. No model makes these decisions.
- **Run checked code in your own GAUSS**, optionally. Only after you approve the exact code, once, and only code that computes in memory.
- **Repair a GAUSS file**, one approved step at a time, through the guided repair pipeline (`gauss-ai repair`).

## Status

**Alpha.** Current milestone: `v0.89.0` - Release Readiness (package version `0.89.1`). gauss-ai is an unofficial, independent project, not affiliated with or endorsed by Aptech Systems, Inc. GAUSS is a trademark of Aptech Systems, Inc. The milestone history is in [docs/development-history.md](docs/development-history.md).

## Quickstart

You need Python 3.10 or newer. GAUSS itself is optional; without it, search and validation still work.

**1. Install**

```
pip install "gauss-ai[mcp]"
gauss-ai version
```

`pipx install "gauss-ai[mcp]"` or `uv tool install "gauss-ai[mcp]"` work too, and keep it out of your other Python environments. The `[mcp]` extra is needed only for the MCP server; the CLI alone has no third-party dependencies. To work on gauss-ai itself, see "Working on gauss-ai" below.

**2. Download the documentation (once)**

```
gauss-ai docs fetch
gauss-ai doctor
```

This downloads the published GAUSS documentation (about 8 MB) from docs.aptech.com into `~/.gauss-ai/docs/` and configures it. It runs only when you run it. See [docs/gauss-documentation-setup.md](docs/gauss-documentation-setup.md).

**3. Connect your MCP client**

Claude Code:

```
claude mcp add --transport stdio --scope user gauss-ai -- gauss-ai-mcp
```

Claude Desktop (Windows and macOS): add this to `claude_desktop_config.json` (Settings → Developer → Edit Config), then restart Claude Desktop. Desktop may not find `gauss-ai-mcp` on its own, so use the full path that `where gauss-ai-mcp` (Windows) or `which gauss-ai-mcp` (macOS) prints:

```json
{
  "mcpServers": {
    "gauss-ai": {
      "command": "C:\\full\\path\\to\\gauss-ai-mcp.exe",
      "args": []
    }
  }
}
```

In a new conversation, ask the assistant to start a gauss-ai session. It should report `docs_root_configured: true`. The tools are described in [docs/mcp-server.md](docs/mcp-server.md).

**4. Real GAUSS (optional)**

Point gauss-ai at your **terminal** GAUSS executable (`tgauss` or `tgauss.exe`, never the GUI), and make it the default runner. On Windows it is `tgauss.exe` in your GAUSS folder. On macOS, use the `tgauss` script in your GAUSS home folder, not the program inside the app, since the script sets up GAUSS's environment. On Linux, it is in the folder where you unpacked GAUSS and ran `./ginstall`.

```
gauss-ai config set gauss-executable "C:\gauss26\tgauss.exe"
gauss-ai config set default-runner gauss
```

Then give the server process your opt-in, `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Only whoever starts the server can set it, and every run still needs your own "yes":

- Claude Code: `claude mcp remove gauss-ai --scope user`, then
  `claude mcp add --transport stdio --scope user -e GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1 gauss-ai -- gauss-ai-mcp`
- Claude Desktop: add `"env": { "GAUSS_AI_MCP_ALLOW_REAL_GAUSS": "1" }` to the entry above, and restart.

Set it for yourself only. Never put it in a project's shared `.mcp.json` (this repository's own `.mcp.json` deliberately leaves it out), where it would turn real execution on for everyone who clones the project.

To check: in a new conversation, a new session must report `real_gauss_allowed: true`. That confirms the opt-in, not that GAUSS starts; the first approved run shows that.

**5. Upgrading**

Close your MCP client (on Windows a running server locks its files), run `pip install -U "gauss-ai[mcp]"`, then reopen the client and start a new conversation. If a session reports a `server_version` other than the one you installed, or a tool asks for an argument its description does not mention, restart the client again: some clients keep old tool descriptions.

## What it will and won't do

- Code from the assistant is **never run** unless gauss-ai's own checks rate it `handoff_candidate` and you approve that exact code. One approval runs it once, in a temporary directory that is deleted afterwards.
- Code that reaches outside GAUSS is **always blocked** from running: OS commands, other programs, `run`/`#include`, directory changes, any file read, write or delete, web data APIs and databases.
- A verdict is **evidence, not a guarantee** of correct results. Much real code is `review_required` (for example, most loops, or an argument computed by an expression, since expressions are never evaluated), and gauss-ai says exactly what it could not check.
- No telemetry. The only network access is `gauss-ai docs fetch`, run by you, and a model provider you explicitly enable for the optional built-in chat.

## Platforms

Search, validation and the MCP server are tested on Windows, Linux and macOS. Running real GAUSS has been verified on Windows (GAUSS 26.1) only; on Linux and macOS the `tgauss` path is implemented but not yet verified. Reports are welcome.

## The GAUSS documentation

gauss-ai never bundles, mirrors or redistributes the GAUSS documentation. Each user downloads Aptech's public documentation from docs.aptech.com with `gauss-ai docs fetch`. Searches run locally, and excerpts go only to your own MCP client.

## Safety Model

Every approval layer is independent, digest-bound, and never inferred: execution confirmation, strategy approval, draft approval, application approval, the application gate, explicit file reading, and human verification review. The guided `gauss-ai repair` command may simplify *navigation* through these steps, but it never simplifies *authorization* — see [docs/alpha-tester-guide.md](docs/alpha-tester-guide.md)'s "Current safety boundaries" for the complete list, and `planning/v0.67.0-productization-and-alpha-packaging.md` for the tests that prove the guided command cannot bypass any of them.

## Conversational GAUSS Q&A

```
gauss-ai
```

launches a chat you can ask GAUSS questions in plain language, with follow-up context retained ("What does reshape do?" → "Show me a simple example." → "What's the difference between that and vec?"). It answers from this repository's verified error catalog and, when you configure `docs-root`, real local GAUSS documentation — always disclosing whether an answer is grounded or not. It never applies a repair and never writes a file. As of `v0.78.0`, generated code that reaches `HANDOFF_CANDIDATE` readiness (the strongest deterministic evidence level) can be executed through one narrow, explicit, single-use, digest-bound approval — see [docs/controlled-execution-handoff.md](docs/controlled-execution-handoff.md); asking to "run this" for anything else still gets an honest redirect or a clear "nothing eligible right now" message, never a silent no-op. The prior command-by-command workflow REPL is unchanged and still available at `gauss-ai repl`. See [docs/conversational-qa.md](docs/conversational-qa.md) for the full guide, including how to configure a real model provider.

## What Happens to My Files?

Before you point this at your own code, here is exactly what it does and does not do to your files, in one place:

- **Your original source file is never modified directly.** `gauss-ai repair <file.gss>` copies the named file into a fresh, contained workspace and works there instead.
- **All repair work happens inside that workspace** — not in place, and not anywhere else on disk.
- **Explicit approval is required before every stage** — execution, repair strategy, repair draft, and application are each a separate, independent decision; nothing is inferred or defaulted to "yes."
- **Applying a repair always creates a mandatory, never-overwritten backup** before anything is written.
- **Verification is evidence-based, not assumed.** The repaired file is re-executed and compared against the original run; the result is a factual comparison, never a fabricated correctness claim.
- **You decide whether a repair is accepted.** The final verification review (`accepted` / `rejected` / `inconclusive`) is always your own recorded decision, never inferred automatically.

See "Safety Model" above and [docs/alpha-tester-guide.md](docs/alpha-tester-guide.md) for the complete list of safety boundaries this summarizes.

## Using the CLI

Everything above also works without an MCP client: `gauss-ai` (no subcommand) opens a conversational GAUSS assistant, and `gauss-ai repair <file.gss>` runs the guided repair pipeline.

## Repair quickstart (fake mode, no GAUSS required)

```
gauss-ai init
gauss-ai doctor
gauss-ai repair examples/alpha-demo/broken.gss --fake-result failure
```

Walks you through the entire pipeline — confirm execution, approve a repair strategy, describe and approve a draft, approve applying it, verify, and record your review — in well under 10 minutes. See [docs/alpha-quickstart.md](docs/alpha-quickstart.md) for the full walkthrough.

## Real GAUSS Mode

Once you have a configured, valid **terminal** GAUSS executable (`tgauss`/`tgauss.exe` — never the GUI `gauss.exe`):

```
gauss-ai config set gauss-executable C:\gauss26\tgauss.exe
gauss-ai repair <your-file.gss> --runner gauss
```

Every approval step is identical to fake mode; only the underlying runner changes. Verified against **GAUSS 26.1.1 on Windows** — see [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for the exact supported scope.

## Guided Repair Workflow

`gauss-ai repair <file.gss>` is orchestration/UI only over the exact same modules the lower-level command-by-command REPL uses (`python scripts/gauss_code_assistant_cli.py`, still fully supported — see the "Recommended reasoning sequence" section below for its full command reference). It hides internal identifiers by default and shows plain-language next steps; digests and trace IDs are still shown at every approval point, since they are what you are actually approving. As of `v0.69.0`, it also shows the evidence behind a repair immediately after strategy approval and, for a small, verified set of patterns, a candidate replacement you can accept, edit, or reject — never applied without your own decision, and never a substitute for the approval steps that follow.

## Expected Workflow

For a real repair, on your own file:

```
gauss-ai init
gauss-ai doctor
gauss-ai config set gauss-executable <path to your tgauss/tgauss.exe>
gauss-ai repair <your-file.gss> --runner gauss
```

You will be asked to explicitly confirm execution, approve a repair strategy, describe and approve a draft, approve applying it, and record a review of the verification evidence — every step is yours to decide. Add `--export-session <path>` to write a read-only diagnostic bundle (config, runner, workspace, full transcript, no secrets) you can attach to a bug report.

## How to Report Issues

See [docs/reporting-bugs.md](docs/reporting-bugs.md) for the process and [docs/alpha-feedback-template.md](docs/alpha-feedback-template.md) for the structured template. In short: run `gauss-ai doctor` first, gather a `--export-session` diagnostic bundle if possible, and report any apparent unauthorized approval/execution/read/write as Critical severity regardless of anything else.

## Documentation

- [docs/alpha-installation.md](docs/alpha-installation.md) — prerequisites, install, configuration, first-run setup.
- [docs/alpha-quickstart.md](docs/alpha-quickstart.md) — under 10 minutes to a successful fake-mode repair.
- [docs/alpha-troubleshooting.md](docs/alpha-troubleshooting.md) — common setup and workflow problems.
- [docs/alpha-tester-guide.md](docs/alpha-tester-guide.md) — what to test, safety boundaries, how to report issues.
- [docs/alpha-feedback-template.md](docs/alpha-feedback-template.md) — structured bug/feedback template.
- [docs/private-alpha-testing.md](docs/private-alpha-testing.md) — the private alpha entry point: what was validated, expected workflow, how to report issues.
- [docs/reporting-bugs.md](docs/reporting-bugs.md) — how to gather evidence (including `--export-session`) and where to report.
- [docs/known-alpha-limitations.md](docs/known-alpha-limitations.md) — tester-facing summary of current limitations.
- [docs/conversational-qa.md](docs/conversational-qa.md) — how to use conversational GAUSS Q&A, provider configuration, grounding, execution boundary.
- [docs/conversational-code-generation.md](docs/conversational-code-generation.md), [docs/grounding-gated-generation.md](docs/grounding-gated-generation.md), [docs/pre-execution-validation.md](docs/pre-execution-validation.md) — conversational GAUSS code generation, the deterministic generation gate, and documented call-signature/precondition checking with an execution-eligibility verdict.
- [examples/alpha-demo/](examples/alpha-demo/) — a small, ready-to-run demo scenario.
- [docs/mcp-server.md](docs/mcp-server.md) — the MCP server's tools, the hybrid and strict paths, the real-GAUSS opt-in and the session model.
- [docs/development-history.md](docs/development-history.md) — every milestone's summary, newest first, and the architecture notes.

## Known Limitations

See [docs/known-alpha-limitations.md](docs/known-alpha-limitations.md) for a tester-facing summary, or [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for the complete, per-milestone record. In short: much real code stops at `review_required`, since expressions are never evaluated; single-file repair only, no autonomous repair, no rerun/rollback beyond the one mandatory backup; no durable sessions; no telemetry; and real execution verified on Windows (GAUSS 26.1) only.

## Working on gauss-ai

From a checkout: `pip install -e ".[mcp]"`, re-run after every pull that touches `scripts/`. Each `scripts/test_*.py` is a standalone script (`python scripts/test_<module>.py`); `python scripts/check_release_readiness.py` runs the evidence and tracking checks. This repository's `.mcp.json` registers the server for Claude Code at project scope. `CLAUDE.md` holds the project's rules, `planning/` one design document per milestone, and `evaluations/` the benchmark prompts and live-evaluation records.
