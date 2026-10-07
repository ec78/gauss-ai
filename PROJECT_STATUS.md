# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

`v0.80.0 — Hybrid MCP Validation, Docs Fetch, and Validation Hardening` is **implemented and committed locally (`a440c50`). It is not tagged, pushed, or released.** Pushing, tagging and releasing need a separate, explicit confirmation from the user.

The live MCP evaluation `70.1`-`70.6` **has been run and recorded**, after the user reloaded the VS Code window. All six scenarios passed. It found one client-side issue: Claude Code keeps stale descriptions for tools whose names didn't change. This is cosmetic, because the server accepted `validation_id` anyway.

## Completed Work

- **v0.79.0** (MCP server) was released. A live client evaluation, `69.1`, was recorded and pushed (`4fc4a2c`).
- **Hybrid MCP path:**
  - The client model writes code; `gauss_validate_code` → `gauss_conversation_engine.validate_code(...)` computes the verdict deterministically.
  - Execution only goes through a server-issued, single-use `validation_id`, re-validated at prepare time (`validation_stale`). Prepare never accepts code directly.
  - `gauss_chat_ask`/`gauss_chat_reset` are opt-in (registered only when `chat-provider` ≠ `fake`).
  - Tools were renamed: `gauss_chat_start`/`close` → `gauss_session_start`/`close`. `gauss_search_docs` was added.
- **Validation fixes (pre-existing gaps):**
  - A shared `call_scan_text(...)` fixes keyword-led lines (e.g. `print colmean(x);`) escaping extraction and the unknown-symbol check.
  - A 50-entry, doc-verified `_SYSTEM_STATEMENT_REGISTRY` forces `NOT_READY` for OS, process, include, directory and file I/O statements.
- **Refactor:** `_validate_pre_execution` + the inline unknown-symbol pass became `validate_generated_code(...)`. It was proven byte-identical via `AnswerResult` snapshots across 12 scenarios.
- **`gauss-ai docs fetch` / `docs status`** (`gauss_docs_fetch.py`) download the 1,826 published pages from docs.aptech.com into `~/.gauss-ai/docs/`.
  - The real fetch succeeded: 272s, with backoff after rate-limit 403s.
  - Doctor gained a `docs_root` check; init points to `docs fetch`.
- **`CLAUDE.md`:** the network rule was amended to allow the explicit docs fetch, with user sign-off.

## Decisions (user-approved)

- Hybrid plus opt-in strict mode, not either alone.
- Docs come from the **published site** (`_sources` via `searchindex.js`), not the GitHub archive.
- System-touching statements → **NOT_READY** (not REVIEW_REQUIRED). File reads are included.
- Deviation: `init` got a next-step pointer instead of an interactive download prompt. An extra prompt would break every scripted init test, and keeping init offline is preferable.

## Tests / Validation

- Full suite: 48 files, all passing; `check_release_readiness.py` passes.
- Zero diff since v0.79.0 in core execution/repair/verification/approval modules, `command_doc_lookup.py`, and `gauss_chat_provider.py`.
- 33 new tests (net).
- `mcp` is installed in the real Python env, so `test_gauss_mcp_server.py` runs (21 tests) rather than skipping.

## Known Issues

- See the top paragraph of `KNOWN_LIMITATIONS.md`.
- The user's local docs clone (`C:/Users/eclow/Documents/GitHub/docs`, `develop` branch, last updated 2026-06-02) is stale compared with the published site:
  - 146 published pages it lacks;
  - 383 unpublished drafts;
  - about 26% of shared pages differ.
  
  Their `docs_root` still points at that clone. `docs fetch` deliberately did not override it.
- Leftover pip debris `~auss_ai-0.79.0.dist-info` in site-packages (from the interrupted reinstall) causes a harmless "Ignoring invalid distribution" warning. The user was told how to remove it; it was not deleted automatically.

## Next Steps

1. Tag, push and release v0.80.0, but only on explicit user confirmation.

## Handoff Notes

- **Windows reinstall gotcha (now in `CLAUDE.md`):** a running `gauss-ai-mcp.exe` locks its executable, so `pip install -e ".[mcp]"` fails partway and leaves `gauss-ai` uninstalled. Stop the process first.
- The real-fetch copy used for verification is in this session's scratchpad (`realfetch/docs`), not committed.
- The `evaluations/differential_runs/2026-09-18-*` untracked directories are still deliberately untouched.
