# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

**`v0.82.0 — Bounded Control-Flow Syntax Coverage` was released on 2026-10-10** (https://github.com/ec78/gauss-ai/releases/tag/v0.82.0; commit `faa4d63`, tag pushed). No next milestone is chosen; do not start one until the user does. Design, implementation, deviations and live results are in `planning/v0.82-bounded-control-flow-syntax-coverage.md` (§9-§11).

v0.82.0 done:
- code and tests: `for … endfor` validation (nested included), four INVALID `for` rules, the `let_statement_shape` rule, option B category tracing, the vcx Syntax-line fix, nested-optional and variadic `...` signature fixes, and the system-statement registry audit (50 → 213, new `network`/`database`). 23 new tests; full suite (48 files) and `check_release_readiness.py` pass; zero diff in core execution/repair/verification modules.
- live category `72.1`-`72.16` (2026-10-10, real Claude Code client, uncoaxed, fresh conversation): all 16 pass, no wrong verdict.
  - The 71.3 shape now reaches handoff_candidate. So do a recurrence, a step-2 loop and loop-fill-then-`meanc` (option B).
  - All negative probes held: a hallucinated `colmedian`, an `invpd` VIOLATED through a variable, `csvWriteM`, `fred_load` (now `network`) and `filesa`.
  - Not exercised live (the client chose other shapes): a nested loop, a counting-down loop, an OS command, and review_required for an `if` body with a documented call.
  - Five minor findings, disclosed in KNOWN_LIMITATIONS (planning §11.3):
    1. `v = 1 ./ seqa(...)` is untraceable, which steered the client into a loop;
    2. the no-documented-calls reason reads "generation policy does not permit code generation (block)" on `validate_code`;
    3. `sprintf.rst`'s `:param ....:` gives variadic args no category;
    4. partial verdicts don't name the check that was partial (the client guessed wrong twice);
    5. `gauss_search_docs("compute a covariance matrix")` → ungrounded, no sources (reproduced).
- README, CHANGELOG, KNOWN_LIMITATIONS and evaluation tracking (benchmark-prompts, benchmark-coverage, `runs/INDEX.md` with its pattern paragraph) are all updated.

Next-milestone candidates (planning §11.4; do not start until the user chooses):
- a small "verdict explanation" patch: findings 2, 3 and 5;
- a larger milestone: expression category inference (finding 1) and/or search concept resolution (finding 4), or the public release readiness track below.

Earlier: `v0.81.0 — Idiomatic Handoff Candidacy` was released on 2026-10-08 (https://github.com/ec78/gauss-ai/releases/tag/v0.81.0).

v0.81.0 done:
- code and tests (48 files pass), version 0.81.0, README/CHANGELOG/KNOWN_LIMITATIONS;
- re-baseline against the published docs (identical verdicts; found the `vcx` fix, §3.5);
- live category `71.1`-`71.5` (real Claude Code client, uncoaxed code):
  - 3/5 reached handoff_candidate;
  - OLS stayed review_required by design;
  - **71.3 gap:** a preallocate-and-fill `for` loop stays review_required, because any block caps syntax coverage at partial;
  - minor `gauss_search_docs` noise in 71.5.

Follow-ups:
1. `docs_root` was switched to `C:/Users/Owner/.gauss-ai/docs` (the published copy) on 2026-10-08, at the user's request. `gauss-ai doctor` passes. The old clone at `C:/Users/eclow/Documents/GitHub/docs/docs` is no longer used.
2. `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1` stays **off**. The user deferred it, and the 71.3 follow-up doesn't need it (it is validator-only). Revisit only for a milestone that wants live real-GAUSS runs through MCP.
3. The planned 71.x negative probes (hallucinated symbol, SPD violation through a variable, system statement) were not run live. The v0.82.0 handoff folds them into `72.x`.

## Where Things Stand (v0.81.0; v0.82.0 changes are summarized above and in CHANGELOG)

- **MCP server** (`scripts/gauss_mcp_server.py`, stdio, optional `mcp` extra) has 9 base tools:
  - `gauss_session_start`/`close`, `gauss_search_docs`, `gauss_validate_code`, `gauss_execution_prepare(validation_id?)`, `gauss_execution_decide`, and `gauss_repair_start`/`command`/`close`;
  - opt-in strict-mode `gauss_chat_ask`/`gauss_chat_reset` (registered only when `chat-provider` ≠ `fake`).
- **Hybrid path:** the client model writes code, and `gauss_conversation_engine.validate_code(...)` computes the verdict. Execution happens only via a server-issued, single-use `validation_id` that is re-validated at prepare time.
- **Validation chain:** one shared `validate_generated_code(...)` (used by `ask()` and `validate_code()`); the 50-entry `_SYSTEM_STATEMENT_REGISTRY` forces NOT_READY.
- **v0.81.0 tracing:**
  - `_governing_assignment(...)` and `resolve_argument_category(...)` in `gauss_pre_execution_validation.py` trace a variable to its most recent prior top-level assignment;
  - `_CATEGORY_ACCEPTS` lets a vector or scalar stand in for a documented matrix;
  - `_resolve_ambiguous_by_definition(...)` in `gauss_conversation_engine.py` resolves combined doc pages.
- **Syntax layer:** `validate_syntax(...)` is a bounded rule set, not a parser. `_detect_unknown_syntax_constructs(...)` reports every `if`/`for`/`do`/`while`/`proc` block as unknown, which caps syntax coverage at PARTIAL. That cap is the 71.3 gap.
- **Evaluations:** live client evaluations `69.1`, `70.1`–`70.6` and `71.1`–`71.5` passed. The last category number used is **72** (`72.1`-`72.16`, v0.82.0).
- **Tests:** 48 files, all passing, and `check_release_readiness.py` passes. The `mcp` extra is installed in this machine's real Python, so the MCP tests actually run.

## Known Issues

- See the top paragraph of `KNOWN_LIMITATIONS.md` (v0.82.0), which includes the five 72.x findings. The 71.3 control-flow gap is closed for simple `for` loops.
- **Claude Code keeps stale tool descriptions** for MCP tools whose names didn't change across a server upgrade. This is cosmetic: the server still accepts new parameters.
- **Pip debris:** `~auss_ai-0.79.0.dist-info` in `C:\Users\Owner\AppData\Local\Programs\Python\Python312\Lib\site-packages` causes a harmless "Ignoring invalid distribution" warning. It is still present; the user can delete it at any time.

## Next Milestone Handoff

v0.82.0 (the milestone recommended here after v0.81.0) is done; see Current Objective. No next milestone is chosen yet. The candidates are in Current Objective (from planning §11.4) and below.

### Later: Public release readiness

The user's stated longer-term goal is a publicly available MCP. It is mostly decision-heavy:
- drop "Private Alpha"?
- publish to PyPI as `gauss-ai`?
- list in MCP directories (official registry, Claude Desktop extensions, Smithery)?
- cross-platform support (`pyproject` classifiers declare Windows only)?
- a stranger-friendly README quickstart?
- optionally ask Aptech about the docs (the `aptech/docs` repo declares no license; the current posture is per-user download, never redistribution).

### Smaller standalone items

- Live real-GAUSS evaluation through MCP. It needs `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1` in user-scope MCP config; the user deferred this.
- Idle-session eviction for long-running MCP servers.
- MCP sampling, so strict-mode chat could use the client's model instead of Ollama. Blocked: Claude Code doesn't support sampling as a client (anthropics/claude-code#1785).

## Handoff Notes

- **Windows reinstall gotcha (in `CLAUDE.md`):** stop any running `gauss-ai-mcp.exe` (spawned by the VS Code Claude Code window) before `pip install -e ".[mcp]"`, or the reinstall fails partway and leaves `gauss-ai` uninstalled. Stopping it disconnects the MCP tools until the user reloads the window (`Ctrl+Shift+P` → "Developer: Reload Window"). After a reload, new MCP tools appear only in a fresh conversation.
- **Machine config** (`C:\Users\Owner\.gauss-ai\config.json`): `chat_provider: ollama` (`qwen2.5-coder:7b`), `default_runner: gauss`, `gauss_executable: C:\gauss26\tgauss.exe`, `workspace_parent: C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`, `docs_root: C:/Users/Owner/.gauss-ai/docs` (the published copy, switched on 2026-10-08). The MCP server refuses `runner="gauss"` unless it was started with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`, which is currently off.
- **Live evaluations through MCP:** the user asks plain-language tasks one at a time in a fresh conversation, with no steering; the session writes the code itself. Don't put the test prompts into the kickoff message.
- The `evaluations/differential_runs/2026-09-18-*` untracked directories are leftovers from v0.77.0, deliberately untouched; don't commit them.
