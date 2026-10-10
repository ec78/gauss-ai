# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

**Next milestone chosen (2026-10-10): `v0.83.0 — Verdict Explanations and Search Recall`. Not started.** The user will start it in a fresh session with a handoff prompt. As usual, the first deliverable is a design doc, `planning/v0.83-verdict-explanations-and-search-recall.md`, for user approval before any implementation.

It addresses four of the five minor findings from live evaluation 72.x (`planning/v0.82-bounded-control-flow-syntax-coverage.md` §11.3; run files `evaluations/runs/2026-10-10-code-assistant-control-flow-syntax-coverage-run-0NN.md`):

1. **Misleading reason for code with no documented calls (72.6, 72.8).**
   - What happens: `validate_code` reports the reason as "generation policy does not permit code generation (block)". That is the `ask()` path's gate wording, but nothing was generated; only the attached note (`NO_DOCUMENTED_CALLS_NOTE`) explains the real cause.
   - What to keep: the `not_ready` verdict itself, which is v0.80.0 policy and correct.
2. **A partial verdict doesn't name its cause (72.3, 72.15).**
   - What happens: a role-check gap is reported only as "validation coverage is partial". In 72.x the client guessed the cause wrong twice.
   - Constraint on the fix: it must be deterministic, categorical text naming the symbol and parameter whose check stayed unknown, and it must not change any verdict.
   - Where to look: `compute_handoff_readiness` in `scripts/gauss_pre_execution_validation.py`, the MCP response in `gauss_validate_code`, and the `ValidationCoverage` and `ParameterRoleCheck` data.
3. **`sprintf.rst` names its variadic parameter `:param ....:` (four dots),** so the `:type` never attaches to the signature's `...`, and every variadic argument's role is unknown.
   - Constraint on the fix: normalize the `....` name (or attach the type some other way). This is a doc-extraction change, so it needs the CLAUDE.md all-pages before/after diff and a verdict diff against HEAD.
   - Open question: decide whether a documented "NxK numeric or string vectors" type should accept a scalar.
4. **`gauss_search_docs` returns nothing for a plain question (72.16).** "compute a covariance matrix" comes back `ungrounded` with no sources.
   - Diagnosed on 2026-10-10: `resolve_concepts` leaves the single word "covariance" unresolved. "variance-covariance matrix" is `ambiguous` across several equally scored pages (`robustse`, `vcx`, …), and an ambiguous resolution yields no sources at all.
   - So search already has concept resolution (through `ground_multi` → `resolve_concepts` → `gauss_doc_concept_index`). The gap is that weak or ambiguous matches produce nothing. An earlier note said "give search the resolution `ask()` has"; that was wrong.
   - Constraint on the fix: candidate pages must be clearly labeled as candidates, never as `grounded`.
   - Keep separate: `ground_multi` also feeds the `ask()` generation gate (`compute_generation_gate`). Any change must leave that gate's behavior unchanged, or change it only with explicit sign-off and tests, because the gate is safety-relevant.

Deliberately deferred:
- **finding 1 (72.3):** category inference for elementwise expressions (`v = 1 ./ seqa(...)` is untraceable). It changes tracing semantics, so it needs its own design;
- the public release readiness track (below).

Live evaluation for v0.83.0 is category `73.x`, in the usual live-client style (CLAUDE.md). It should re-ask 72.6 / 72.15 / 72.16-style tasks unsteered, and include plain-language search questions.

## Where Things Stand (v0.82.0, released 2026-10-10)

Released at https://github.com/ec78/gauss-ai/releases/tag/v0.82.0 (tag `v0.82.0`, commit `faa4d63`). Full detail is in CHANGELOG and the v0.82 planning doc.

- **MCP server** (`scripts/gauss_mcp_server.py`, stdio, optional `mcp` extra) has 9 base tools:
  - `gauss_session_start`/`close`, `gauss_search_docs`, `gauss_validate_code`, `gauss_execution_prepare(validation_id?)`, `gauss_execution_decide`, and `gauss_repair_start`/`command`/`close`;
  - opt-in strict-mode `gauss_chat_ask`/`gauss_chat_reset` (only when `chat-provider` ≠ `fake`).
- **Hybrid path:** the client writes the code, and `gauss_conversation_engine.validate_code(...)` computes the verdict. Execution happens only via a server-issued, single-use `validation_id`.
- **Validation chain:** one shared `validate_generated_code(...)`; a 213-entry `_SYSTEM_STATEMENT_REGISTRY` with categories file read/write, OS/process, source inclusion, directory, `network` and `database`. Code with no documented calls is `not_ready`.
- **Syntax layer** (`validate_syntax`, a bounded rule set, not a parser):
  - `_split_statements` + `_check_control_flow_blocks` validate `for … endfor` (nested included) with a body allowlist;
  - `if`/`do`/`proc`/thread blocks are unknown (`control_flow_block`) → at best `review_required`;
  - the INVALID rules include the four `for_*` rules and `let_statement_shape`.
- **Tracing:**
  - `_governing_assignment` / `resolve_argument_category` trace a variable to its most recent prior top-level assignment;
  - option B: indexed writes are looked through for category only, never for preconditions;
  - expressions are never evaluated.
- **Signatures:** nested optional groups are flattened, and `...` means no upper bound (`VARIADIC_MAX_ARGS`).
- **Evaluations:** the last category used is **72** (`72.1`-`72.16`, all pass).
- **Tests:** 48 files, all passing; `check_release_readiness.py` passes. The `mcp` extra is installed in this machine's real Python, so the MCP tests actually run.

## Known Issues

- See the top paragraph of `KNOWN_LIMITATIONS.md` (v0.82.0), which includes the five 72.x findings.
- **Claude Code keeps stale tool descriptions** for MCP tools whose names didn't change across a server upgrade. This is cosmetic.
- **Pip debris:** `~auss_ai-0.79.0.dist-info` in `C:\Users\Owner\AppData\Local\Programs\Python\Python312\Lib\site-packages` causes a harmless "Ignoring invalid distribution" warning. The user can delete it at any time.

## Later

**Public release readiness** (the user's longer-term goal: a publicly available MCP). This is mostly a list of decisions:
- drop "Private Alpha"?
- publish to PyPI as `gauss-ai`?
- list in MCP directories (official registry, Claude Desktop extensions, Smithery)?
- cross-platform support (the `pyproject` classifiers declare Windows only)?
- a stranger-friendly README quickstart?
- optionally ask Aptech about the docs (the `aptech/docs` repo declares no license; the posture is per-user download, never redistribution).

**Smaller standalone items:**
- Live real-GAUSS evaluation through MCP. It needs `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1` in the user-scope MCP config; the user deferred it.
- Idle-session eviction for long-running MCP servers.
- MCP sampling, so strict-mode chat could use the client's model. Blocked: Claude Code doesn't support sampling as a client (anthropics/claude-code#1785).

## Handoff Notes

- **Windows reinstall** (see `CLAUDE.md`): stop any running `gauss-ai-mcp.exe` before `pip install -e ".[mcp]"`. Then reload the VS Code window (`Ctrl+Shift+P` → "Developer: Reload Window"). New MCP tools appear only in a fresh conversation, so live `73.x` must happen in a new conversation after the reinstall.
- **Machine config** (`C:\Users\Owner\.gauss-ai\config.json`): `chat_provider: ollama` (`qwen2.5-coder:7b`), `default_runner: gauss`, `gauss_executable: C:\gauss26\tgauss.exe`, `workspace_parent: C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`, `docs_root: C:/Users/Owner/.gauss-ai/docs` (the published copy). `GAUSS_AI_MCP_ALLOW_REAL_GAUSS` is **off**, so every MCP prepare on the `gauss` runner returns `real_gauss_not_allowed`, as designed.
- The `evaluations/differential_runs/2026-09-18-*` untracked directories are leftovers from v0.77.0, deliberately untouched; don't commit them.
