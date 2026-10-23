# CLAUDE.md

Durable, project-wide guidance for Claude Code sessions in this repository. For current work-in-progress, see `PROJECT_STATUS.md` instead — do not duplicate that material here.

**Context efficiency:** Read or inspect only the files needed for the current task unless broader repository review is necessary. Avoid dumping large file contents, logs, or test output into the conversation when a concise summary or targeted excerpt is sufficient.

## Project Purpose

**GAUSS AI** / **GAUSS Code Assistant**: a governed, human-in-the-loop CLI (`gauss-ai`) that helps diagnose and repair GAUSS-language code one file at a time, plus a conversational assistant (`gauss-ai`, no subcommand) that answers GAUSS questions and generates GAUSS code. Every safety-relevant decision (execution, file writes, repair application, generation gating, intent classification) is deterministic/rule-based — never inferred by a model. Currently in **Alpha**: public on PyPI as `gauss-ai` since 0.89.2 (2026-10-23).

## Architecture

- `scripts/` — all implementation and tests live here as flat Python modules (`gauss_*.py`) plus one `test_*.py` per module. `pyproject.toml` maps `scripts/` via `package-dir` and lists every module explicitly under `[tool.setuptools] py-modules`; **a new module must be added there or it will not be packaged/installed**.
- `gauss_ai_cli.py` — the `gauss-ai` console-script entry point (thin dispatcher).
- `gauss_ai_chat.py` + `gauss_conversation_engine.py` + `gauss_chat_provider.py` — the conversational layer: intent classification, grounding, generation gating, symbol checking, and the `ModelProvider` abstraction (`fake` / `ollama` / `anthropic`).
- `command_doc_lookup.py` — local retrieval over official-GAUSS `.rst` documentation under `docs_root` (user-configured; typically the copy `gauss-ai docs fetch` downloads into `~/.gauss-ai/docs/` via `gauss_docs_fetch.py`). Documentation is never bundled in or redistributed by this repo.
- Natural-language lookup: `gauss_search_docs` and `ask()` both ground through `gauss_conversation_engine.ground_multi(...)` → `resolve_concepts(...)`, which combines exact symbol tokens, the curated `_CONCEPT_ALIAS_INDEX` and the doc-derived `gauss_doc_concept_index.py`. `gauss_validate_code` instead grounds on the code's own called symbols, so search recall never affects a verdict.
- `gauss_mcp_server.py` — local MCP server (stdio; optional `mcp` extra). Hybrid path: the client model writes code, `gauss_conversation_engine.validate_code` computes the verdict deterministically, and execution is only possible via a server-issued, single-use `validation_id`. Strict-mode chat tools are opt-in (real `chat-provider` only).
- `gauss_error_catalog.py` — the verified GAUSS error-code knowledge base.
- The repair pipeline (`gauss_code_assistant_workflow.py`, `gauss_execution_*`, `gauss_repair_*`, `gauss_verification_*`) — the original governed execute→diagnose→repair→verify→review pipeline. The conversational layer has **no import path into any of these modules** (structurally enforced and tested).
- `planning/v{X}-*.md` — one design/readiness document per milestone, mirroring that milestone's required final-report structure.
- `evaluations/` — `benchmark-prompts.md`, `benchmark-coverage.md`, `runs/` (real transcripts), `runs/INDEX.md`.
- `docs/` — user/alpha-tester-facing documentation. `docs/development-history.md` carries a "Current Status" + chained "Previous milestone" history; `README.md` is the stranger's quickstart, and `docs/pypi-readme.md` is the PyPI description.
- `agents/`, `experts/`, `prompts/`, `tools/`, `workflows/`, `configs/` — a separate, mostly-aspirational multi-agent framework layer described in `ARCHITECTURE.md`; not the actively-developed `gauss-ai` product surface.

## Development Environment

- Python 3.10+, **zero third-party runtime dependencies** for the base CLI (stdlib only) — this is an intentional, long-standing constraint; don't add one without a strong reason. The only exception is the optional `mcp` extra (`pip install -e ".[mcp]"`), imported lazily so the base CLI never needs it.
- Install: `pip install -e .` — re-run this after every `git pull`/branch switch that touches `scripts/`, since a stale editable install can silently resolve to a different checkout. On Windows, a running `gauss-ai-mcp.exe` (e.g. spawned by a Claude Code window) locks its executable and makes the reinstall fail partway, leaving `gauss-ai` uninstalled — stop that process first, then reinstall.
- Verify install: `gauss-ai version`, `gauss-ai doctor`.
- Optional real backends used only for manual/live validation, never by automated tests: a local **Ollama** install (`chat-provider=ollama`, default model `qwen2.5-coder:7b`) and a real GAUSS installation (`tgauss.exe`, configured via `gauss-ai config set gauss-executable <path>`). The documentation under `docs-root` is also machine-specific (downloaded or cloned per user, never committed).
- The MCP server is registered for Claude Code in the repo's **tracked** `.mcp.json` (project scope, empty `env`). The operator opt-in that lets MCP execution run real GAUSS (`GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`) belongs only in a local-scope override (`claude mcp add gauss-ai --scope local -e GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1 -- gauss-ai-mcp`). Never put it in `.mcp.json`: that would turn real execution on for everyone who clones the repo.
  - **Claude Code keys local-scope servers by the exact project-path string, and the drive letter's case counts.** The VS Code extension opens this repo as `c:/…`, while a terminal usually gives `C:/…`. In 76.x the override existed only under `C:/…`, so the server ran without the opt-in. Keep it under both spellings (done for 77.x).
  - Check `~/.claude.json` for the key the session actually uses. More than one `gauss-ai-mcp` process can be running, one per Claude Code window (77.x had two). Then prove the opt-in before relying on it: `gauss_session_start` must report `real_gauss_allowed: true` (v0.87.0), and one `gauss_execution_prepare` on a trivial handoff candidate must return a `rendered_prompt`, not `real_gauss_not_allowed`. Neither proves the executable launches; only a run does.
  - Never tell a user that real execution is available on the strength of the config file alone (76.1).

## Important Commands

- Run one test module: `python scripts/test_<module>.py` (each is a standalone script using a small local `check(name, condition)` harness, not `unittest` — there is no pytest/tox/Makefile in this repo). Run the whole suite by looping over `scripts/test_*.py`. `test_gauss_mcp_server.py` skips cleanly (exit 0) unless the `mcp` extra is installed.
- Release-readiness check (also runs in CI on every push/PR): `python scripts/check_release_readiness.py`.
- CLI help: `gauss-ai --help`; conversational assistant: `gauss-ai` (no subcommand); guided repair: `gauss-ai repair <file.gss>`.

## Coding Conventions

- Docstrings and inline comments in this codebase are intentionally verbose and narrative — they record *why* (real evidence, a specific live-testing finding, a verified doc citation), not just *what*. Preserve this style in new/edited modules; don't strip it down to terse comments.
- Deterministic-by-design discipline: anything safety- or correctness-relevant (intent classification, grounding status, generation gates, symbol/signature checking) must be fixed logic or real-evidence lookups — never a model call, never a numeric confidence score presented as fact. Prefer categorical states over invented scores.
- Extend existing modules/abstractions rather than building parallel ones (e.g. code generation reused the existing `ConversationEngine`/`ModelProvider`, it did not create a second conversational system).
- Provider independence: no conversational logic may depend on which `ModelProvider` is active; prove this with a test provider that raises if called when it shouldn't be.
- Any scan of GAUSS source text must respect GAUSS's lexical structure:
  - a statement ends at `;`, not at a newline;
  - text inside a string literal is never code.

  Read source through `gauss_pre_execution_validation.lex_gauss_source(...)` (`masked_view`: comments blanked, strings masked, length- and line-preserving) and `source_statements(...)` (the `;`-terminated stream); never regex raw or per-line text, and never write a second string or comment regex. The lexer's rules (backslash escapes, multi-line strings, nested `/* */`, `@ … @` comments) come from real `tgauss.exe -b` spot checks. 73.10, 73.14 and the v0.84.0 `dos`-behind-a-string defect all came from scans that broke these rules; `test_170_v084_lexical_discipline_guard` enforces it.

## Testing Expectations

- Every `test_*.py` file is standalone, deterministic, and network-free by default — no test may require a running Ollama service or a real GAUSS install.
- Tests use small, synthetic, disposable fixtures (inline `.rst` strings, temp dirs) — **never** point a test at a real machine's own documentation checkout or GAUSS executable.
- Live/manual validation (real Ollama, real `tgauss.exe -b` spot checks) is a separate, explicitly-labeled evaluation procedure recorded under `evaluations/runs/`, not part of the automated suite. During development, `tgauss.exe -b` spot checks run from a scratch directory are the expected way to gather provenance for a new syntax rule; record the results in the rule's `_SYNTAX_RULE_REGISTRY` entry and the milestone's planning doc.
- Any change to documentation extraction or signature parsing (`command_doc_lookup.py`, `_parse_signature_occurrence`, `extract_documented_signature`) needs a before/after diff across all published doc pages, plus a verdict diff against HEAD on real docs. Small extraction changes have wide, sometimes masked effects (v0.82.0: one fix changed 131 signatures and exposed a registry gap).
- Any change to grounding (`resolve_concepts`, `ground_multi`, the alias or derived index, stopwords) needs a gate diff over a question corpus: every benchmark prompt's first paragraph (`evaluations/benchmark-prompts.md`), v0.85's 61 gate questions, and every `gauss_search_docs` query recorded in this project's Claude Code transcripts (`~/.claude/projects/<project>/*.jsonl`). v0.88 used 915 such questions. List every changed `(status, policy, matched, unmatched, ambiguous)` tuple, and review each row that moves toward generation individually.
- Before considering a milestone done: the full existing test suite must pass with zero unexplained diffs in core execution/repair/verification/approval modules. A genuinely obsolete test expectation may be updated, but only with an inline comment explaining why the old behavior was superseded.

## Project-Wide Constraints (do not relax without explicit user sign-off)

- Generated code — whether written by gauss-ai's own provider or, on the MCP hybrid path, by the calling client's model — never executes except through the controlled execution handoff (deterministic `HANDOFF_CANDIDATE` verdict + explicit, digest-bound, single-use human approval), never writes a file, never applies a repair, and never bypasses any existing approval layer. Code may come from a caller; a readiness verdict never does.
- Code that reaches outside GAUSS's own memory (OS commands, processes, `#include`/`run`, directory changes, file reads/writes/deletes, web APIs such as FRED/DBnomics, databases — see `_SYSTEM_STATEMENT_REGISTRY`) is always `NOT_READY` for the handoff. When a change makes previously-blocked code reach `HANDOFF_CANDIDATE`, check that it isn't I/O that the registry simply doesn't list yet.
- The model can never override a deterministic safety decision (an execution/repair boundary, a generation gate, a validation/eligibility verdict) — these are computed and enforced entirely outside any provider call.
- No telemetry. Network calls are allowed only to (a) a model provider the user explicitly enabled, and (b) the explicit, user-invoked `gauss-ai docs fetch` download from docs.aptech.com — never automatic, never per-query.

## Workflow Rules

- Work proceeds in versioned milestones (`vX.Y.0`), each typically specified as one large upfront brief. Each milestone gets its own `planning/v{X}-*.md` doc and typically ends with a mandatory multi-section final report — including an explicit recommendation on whether to proceed to the next milestone. **Do not auto-start the next milestone** unless the user asks.
- Release sequence: full test suite → update `docs/development-history.md` ("Current Status" + prepend to the "Previous milestone" chain) and the README's one-line current milestone, `CHANGELOG.md` (`[Unreleased]`), `KNOWN_LIMITATIONS.md` → commit → tag `vX.Y.0` → **confirm with the user before pushing/creating a GitHub release**.
- New evaluation categories are numbered sequentially (e.g. `62.x`, `63.x`) in `evaluations/benchmark-prompts.md`, with matching dated files under `evaluations/runs/`, an `evaluations/runs/INDEX.md` entry and an `evaluations/benchmark-coverage.md` row. CI's `check_evaluation_tracking.py` fails without the coverage row. Score honestly — a correctly-blocked unsafe request is not a failure; a real defect found live is reported as a real defect, not smoothed over.
- Live MCP-client evaluations (`70.x` onward): the user asks plain-language tasks one at a time in a fresh conversation, and that session writes the code itself. The testing session does not read the milestone's planning doc or `PROJECT_STATUS.md` expectations until the tasks are done. Before recording why a verdict was `review_required`/partial, diagnose it by calling `validate_code(...)` directly and inspecting `pre_execution.coverage` and `parameter_role_checks`, because a client's in-conversation explanation can be a wrong guess (72.3, 72.15).

  When recording:
  - say whether the `coverage_gaps` the client saw agreed with that diagnosis;
  - for search tasks, say whether the client followed a candidate back to a grounded page, or whether its query was steered by prior knowledge;
  - disclose whether the client read source during the tasks, or deliberately shaped code around a known defect;
  - re-run every snippet on a `git archive` of the previous release, so the record separates what the milestone changed from pre-existing behavior (74.x);
  - for every run through the execution handoff, record the exact `gauss_execution_prepare` prompt, the user's own decision, and the result. Re-run approved code with `tgauss.exe -b` to compare, and confirm a declined run executed nothing. The client must never answer a run prompt itself, and passes the user's reply verbatim, even when the server will reject it (77.9);
  - a handoff run never touches `workspace_parent`: it executes in a temporary directory that is deleted afterwards (since v0.87.0 the prompt says so), so the filesystem cannot prove a decline. The evidence is the `declined` outcome, the decide code path, and a refused re-submission of the spent `validation_id` (77.10);
  - since v0.87.0, `gauss_execution_decide` acts only on the `request_id` it is given: the client passes the id of the prompt the user answered, with the reply verbatim. A second prepare supersedes a pending prompt (`replaced_request_id`; a reply to the old one is `request_superseded`), so avoid preparing while the user is answering, and if it happens, show the new prompt. Record the `request_id` passed for every run;
  - before calling a finding a new defect, check `KNOWN_LIMITATIONS.md` and earlier planning docs. Some gaps are disclosed on purpose (74.16 rediscovered v0.83.0's deliberately unfixed `&`-parameter gap).

  - `CLAUDE.md` and memory notes are auto-loaded into the testing client's own context, so they coach it: in 78.4 the client avoided the planned two-prompt binding test because this file described the single-slot rule. Keep an upcoming evaluation's expected behavior in the planning doc, not here, and record what the client could have learned from this file.

  An evaluation that includes execution starts by confirming the opt-in with one prepare, as described in Development Environment above. If the opt-in is missing, fix it before the tasks. Otherwise the run path goes untested, as in 76.x.

  Run files carry the date the tasks were actually run. A follow-up evaluation gets its own category and run-file slug; never reuse the slug of an existing category (77.x continues 76.x as a new category).
