# CLAUDE.md

Durable, project-wide guidance for Claude Code sessions in this repository. For current work-in-progress, see `PROJECT_STATUS.md` instead — do not duplicate that material here.

**Context efficiency:** Read or inspect only the files needed for the current task unless broader repository review is necessary. Avoid dumping large file contents, logs, or test output into the conversation when a concise summary or targeted excerpt is sufficient.

## Project Purpose

**GAUSS AI** / **GAUSS Code Assistant**: a governed, human-in-the-loop CLI (`gauss-ai`) that helps diagnose and repair GAUSS-language code one file at a time, plus a conversational assistant (`gauss-ai`, no subcommand) that answers GAUSS questions and generates GAUSS code. Every safety-relevant decision (execution, file writes, repair application, generation gating, intent classification) is deterministic/rule-based — never inferred by a model. Currently in **Private Alpha**.

## Architecture

- `scripts/` — all implementation and tests live here as flat Python modules (`gauss_*.py`) plus one `test_*.py` per module. `pyproject.toml` maps `scripts/` via `package-dir` and lists every module explicitly under `[tool.setuptools] py-modules`; **a new module must be added there or it will not be packaged/installed**.
- `gauss_ai_cli.py` — the `gauss-ai` console-script entry point (thin dispatcher).
- `gauss_ai_chat.py` + `gauss_conversation_engine.py` + `gauss_chat_provider.py` — the conversational layer: intent classification, grounding, generation gating, symbol checking, and the `ModelProvider` abstraction (`fake` / `ollama` / `anthropic`).
- `command_doc_lookup.py` — local retrieval over a real official-GAUSS `.rst` documentation checkout (`docs_root`, user-configured, not part of this repo).
- `gauss_error_catalog.py` — the verified GAUSS error-code knowledge base.
- The repair pipeline (`gauss_code_assistant_workflow.py`, `gauss_execution_*`, `gauss_repair_*`, `gauss_verification_*`) — the original governed execute→diagnose→repair→verify→review pipeline. The conversational layer has **no import path into any of these modules** (structurally enforced and tested).
- `planning/v{X}-*.md` — one design/readiness document per milestone, mirroring that milestone's required final-report structure.
- `evaluations/` — `benchmark-prompts.md`, `benchmark-coverage.md`, `runs/` (real transcripts), `runs/INDEX.md`.
- `docs/` — user/alpha-tester-facing documentation. `README.md` carries a "Current Status" + chained "Previous milestone" history.
- `agents/`, `experts/`, `prompts/`, `tools/`, `workflows/`, `configs/` — a separate, mostly-aspirational multi-agent framework layer described in `ARCHITECTURE.md`; not the actively-developed `gauss-ai` product surface.

## Development Environment

- Python 3.10+, **zero third-party runtime dependencies** (stdlib only) — this is an intentional, long-standing constraint; don't add one without a strong reason.
- Install: `pip install -e .` — re-run this after every `git pull`/branch switch that touches `scripts/`, since a stale editable install can silently resolve to a different checkout.
- Verify install: `gauss-ai version`, `gauss-ai doctor`.
- Optional real backends used only for manual/live validation, never by automated tests: a local **Ollama** install (`chat-provider=ollama`, default model `qwen2.5-coder:7b`) and a real GAUSS installation (`tgauss.exe`, configured via `gauss-ai config set gauss-executable <path>`). A real documentation checkout (`docs-root` config setting) is also machine-specific and gitignored.

## Important Commands

- Run one test module: `python scripts/test_<module>.py` (each is a standalone `unittest` script — there is no pytest/tox/Makefile in this repo).
- Release-readiness check (also runs in CI on every push/PR): `python scripts/check_release_readiness.py`.
- CLI help: `gauss-ai --help`; conversational assistant: `gauss-ai` (no subcommand); guided repair: `gauss-ai repair <file.gss>`.

## Coding Conventions

- Docstrings and inline comments in this codebase are intentionally verbose and narrative — they record *why* (real evidence, a specific live-testing finding, a verified doc citation), not just *what*. Preserve this style in new/edited modules; don't strip it down to terse comments.
- Deterministic-by-design discipline: anything safety- or correctness-relevant (intent classification, grounding status, generation gates, symbol/signature checking) must be fixed logic or real-evidence lookups — never a model call, never a numeric confidence score presented as fact. Prefer categorical states over invented scores.
- Extend existing modules/abstractions rather than building parallel ones (e.g. code generation reused the existing `ConversationEngine`/`ModelProvider`, it did not create a second conversational system).
- Provider independence: no conversational logic may depend on which `ModelProvider` is active; prove this with a test provider that raises if called when it shouldn't be.

## Testing Expectations

- Every `test_*.py` file is standalone, deterministic, and network-free by default — no test may require a running Ollama service or a real GAUSS install.
- Tests use small, synthetic, disposable fixtures (inline `.rst` strings, temp dirs) — **never** point a test at a real machine's own documentation checkout or GAUSS executable.
- Live/manual validation (real Ollama, real `tgauss.exe -b` spot checks) is a separate, explicitly-labeled evaluation procedure recorded under `evaluations/runs/`, not part of the automated suite.
- Before considering a milestone done: the full existing test suite must pass with zero unexplained diffs in core execution/repair/verification/approval modules. A genuinely obsolete test expectation may be updated, but only with an inline comment explaining why the old behavior was superseded.

## Project-Wide Constraints (do not relax without explicit user sign-off)

- Conversational code generation never executes, never writes a file, never applies a repair, and never bypasses any existing approval layer.
- The model can never override a deterministic safety decision (an execution/repair boundary, a generation gate, a validation/eligibility verdict) — these are computed and enforced entirely outside any provider call.
- No telemetry, no network calls except to a user-configured model provider the user explicitly enabled.

## Workflow Rules

- Work proceeds in versioned milestones (`vX.Y.0`), each typically specified as one large upfront brief. Each milestone gets its own `planning/v{X}-*.md` doc and typically ends with a mandatory multi-section final report — including an explicit recommendation on whether to proceed to the next milestone. **Do not auto-start the next milestone** unless the user asks.
- Release sequence: full test suite → update `README.md` ("Current Status" + prepend to the "Previous milestone" chain), `CHANGELOG.md` (`[Unreleased]`), `KNOWN_LIMITATIONS.md` → commit → tag `vX.Y.0` → **confirm with the user before pushing/creating a GitHub release**.
- New evaluation categories are numbered sequentially (e.g. `62.x`, `63.x`) in `evaluations/benchmark-prompts.md`, with matching dated files under `evaluations/runs/` and an `evaluations/runs/INDEX.md` entry. Score honestly — a correctly-blocked unsafe request is not a failure; a real defect found live is reported as a real defect, not smoothed over.
