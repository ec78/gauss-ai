# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

None active. **`v0.81.0 — Idiomatic Handoff Candidacy` was released on 2026-10-08:** https://github.com/ec78/gauss-ai/releases/tag/v0.81.0. The design and live results are in `planning/v0.81-idiomatic-handoff-candidacy.md` (§5.1). The next milestone has not been chosen; do not auto-start one.

Done:
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
3. The planned 71.x negative probes (hallucinated symbol, SPD violation through a variable, system statement) were not run live. They could be added as 71.6-71.8 if wanted.
4. Next-milestone candidate from 71.3: bounded syntax coverage for simple `for i(a,b,c); ... endfor;` blocks with plain-assignment bodies.

`v0.80.0` is released: https://github.com/ec78/gauss-ai/releases/tag/v0.80.0.

## Where Things Stand (v0.79.0 → v0.80.0)

- **MCP server** (`scripts/gauss_mcp_server.py`, stdio, optional `mcp` extra) has 9 base tools:
  - `gauss_session_start`/`close`, `gauss_search_docs`, `gauss_validate_code`, `gauss_execution_prepare(validation_id?)`, `gauss_execution_decide`, and `gauss_repair_start`/`command`/`close`;
  - opt-in strict-mode `gauss_chat_ask`/`gauss_chat_reset` (registered only when `chat-provider` ≠ `fake`).
- **Hybrid path:** the client model writes code, and `gauss_conversation_engine.validate_code(...)` computes the verdict. Execution happens only via a server-issued, single-use `validation_id` that is re-validated at prepare time.
- **Validation chain:** one shared function, `validate_generated_code(...)`, used by `ask()` and `validate_code()`.
  - Both scanners share `call_scan_text(...)`, which fixed the keyword-led-line gap.
  - The 50-entry `_SYSTEM_STATEMENT_REGISTRY` forces NOT_READY for OS, process, include, directory and file I/O statements.
- **`gauss-ai docs fetch` / `docs status`** (`scripts/gauss_docs_fetch.py`) download the 1,826 published pages from docs.aptech.com, all-or-nothing, with rate-limit backoff. `doctor` has a `docs_root` check.
- **Evaluations:** live client evaluations `69.1` (v0.79) and `70.1`–`70.6` (v0.80) passed. The last category number used is **70**.
- **Tests:** 48 files, all passing, and `check_release_readiness.py` passes. The `mcp` extra is installed in this machine's real Python, so the MCP tests actually run (21).

## Known Issues

- See the top paragraph of `KNOWN_LIMITATIONS.md` (v0.80.0).
- **The user's `docs_root` still points at a stale clone:** `C:/Users/eclow/Documents/GitHub/docs/docs`, `develop` branch, last updated 2026-06-02. Compared with the published site, it lacks 146 pages, has 383 unpublished drafts, and about 26% of shared pages differ. `~/.gauss-ai/docs` has not been downloaded on this machine yet. Every evaluation so far was grounded against the stale clone.
- **Claude Code keeps stale tool descriptions** for MCP tools whose names didn't change across a server upgrade. This is cosmetic: the server still accepts new parameters.
- **Pip debris:** `~auss_ai-0.79.0.dist-info` in `C:\Users\Owner\AppData\Local\Programs\Python\Python312\Lib\site-packages` causes a harmless "Ignoring invalid distribution" warning. The user was told how to remove it; it has not been removed.

## Next Milestone Handoff

The user chose the validation milestone as v0.81.0 (2026-10-07). After it ships, present the remaining options and wait for an explicit decision.

### In progress: v0.81.0 — see "Current Objective"

Planning corrected the old diagnosis. On the MCP path, `rndu` and the other builtins' signatures always extracted fine. The real causes were:
- the untraced variables in the role check;
- `1e5` literals;
- false vector/scalar-vs-matrix MISMATCHes;
- the precondition tracer reading assignments made after the call.

The "rndu signature unknown" message was real only on the `ask()` path. The planning doc has the details.

**71.x should cover:**
- ordinary uncoaxed tasks: column means of random data, OLS by hand (expect `review_required` for `invpd(x'x)`), zeros-then-fill, summary stats of a literal vector;
- negative probes: a hallucinated symbol, an SPD violation through a variable, a system statement.

### Next after v0.81.0: Public release readiness

The user's stated longer-term goal is a publicly available MCP. It is mostly decision-heavy:
- drop "Private Alpha"?
- publish to PyPI as `gauss-ai`?
- list in MCP directories (official registry, Claude Desktop extensions, Smithery)?
- cross-platform support (`pyproject` classifiers declare Windows only)?
- a stranger-friendly README quickstart?
- optionally ask Aptech about the docs (the `aptech/docs` repo declares no license; the current posture is per-user download, never redistribution).

Recommend doing this *after* the validation milestone above, so public users' first experience isn't constant `review_required`.

### Smaller standalone items, if the user prefers

- Live real-GAUSS evaluation through MCP (item 4 above, on its own).
- Idle-session eviction for long-running MCP servers.
- MCP sampling, so strict-mode chat could use the client's model instead of Ollama. Blocked: Claude Code doesn't support sampling as a client (anthropics/claude-code#1785).

## Handoff Notes

- **Windows reinstall gotcha (in `CLAUDE.md`):** stop any running `gauss-ai-mcp.exe` (spawned by the VS Code Claude Code window) before `pip install -e ".[mcp]"`, or the reinstall fails partway and leaves `gauss-ai` uninstalled. Stopping it disconnects the MCP tools until the user reloads the window (`Ctrl+Shift+P` → "Developer: Reload Window"). After a reload, new MCP tools appear only in a fresh conversation.
- **Machine config** (`C:\Users\Owner\.gauss-ai\config.json`): `chat_provider: ollama` (`qwen2.5-coder:7b`), `default_runner: gauss`, `gauss_executable: C:\gauss26\tgauss.exe`, `workspace_parent: C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`, `docs_root` = the stale clone above. Live MCP tests should pass `runner="fake"` unless real GAUSS is intended. The MCP server ignores `runner="gauss"` anyway unless it was started with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`.
- The `evaluations/differential_runs/2026-09-18-*` untracked directories are leftovers from v0.77.0, deliberately untouched; don't commit them.
