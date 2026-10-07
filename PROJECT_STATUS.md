# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

None active. `v0.80.0 — Hybrid MCP Validation, Docs Fetch, and Validation Hardening` is **complete, pushed, tagged, and released**: https://github.com/ec78/gauss-ai/releases/tag/v0.80.0 (tag `v0.80.0` → `b877af1`; `main` at `c541bad` or later). The next milestone has **not** been chosen or started. See "Next Milestone Handoff" below, and wait for the user's explicit go-ahead.

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

The user has **not** picked one yet. Present these, recommend one, and wait for an explicit decision. Per `CLAUDE.md`, plan it first (plan mode), give it its own `planning/v0.81-*.md`, and do not tag/push/release without confirmation.

### Recommended: v0.81.0 — Make idiomatic client-written code reach HANDOFF_CANDIDATE

**Why.** The hybrid path exists so a client model (Claude/ChatGPT) can write GAUSS code. But code written the way models naturally write it rarely reaches `handoff_candidate`. In live evaluations, candidacy only happened when the prompt coaxed a minimal, direct-literal form. Real evidence:
- **`70.6`:** `x = rndu(1e5, 4); y = meanc(x);` → `review_required`, because `rndu`'s signature can't be extracted from its docs and coverage was "partial".
- **`66.1` / `66.2` / `66.10` (v0.76.0):** assign-a-literal-then-call (`x = {...}; y = f(x);`) leaves the parameter-role check `UNKNOWN`. That check never traces a variable back to its literal, unlike the precondition checker, which does.
- **`69.1`/`70.x` setup:** `invpd` is only grounded at confidence 0.6, via the combined `invinvpd.rst` page.

**Likely scope** (verify in planning; all deterministic, no model calls):
1. Trace simple same-snippet literal assignments into `check_parameter_roles`, the same way `check_preconditions` already does.
2. Fill signature/parameter gaps for common builtins (`rndu`, `rndn`, `rows`, `cols`, `zeros`, `ones`, ...), every entry verified against the real published docs.
3. Re-baseline: run `gauss-ai docs fetch` on this machine (with the user's OK), consider switching `docs_root` (user's call), and re-run a representative set of earlier live categories against the published docs to see what changed.
4. Optionally, a real-GAUSS hybrid round trip through MCP: `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`, which needs the user to start the server that way. Only the fake runner has been exercised through MCP so far.

**Acceptance.**
- A new live category (`71.x`) where ordinary model-written snippets reach `handoff_candidate` without coaxing.
- Every existing NOT_READY protection still holds: hallucinated symbols, violated preconditions, system statements.
- Zero diff in core execution, repair and approval modules.

### Alternative: v0.81.0 — Public release readiness

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
