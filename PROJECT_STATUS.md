# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

**No milestone in progress.** v0.84.0 "One Lexical Statement Stream" was committed and tagged `v0.84.0` locally on 2026-10-13. **It is not pushed and has no GitHub release yet; confirm with the user first.** Its live evaluation `74.x` was not run before release (user decision). Plan and record: `planning/v0.84-lexical-statement-stream.md`:
- §1–§8: the plan, approved with every §8 recommendation;
- §9: deviations and the verdict diff;
- §10: testing;
- Appendix A: the 92 diff snippets verbatim.

**Next steps, waiting on the user:**
1. Push `main` and the `v0.84.0` tag, and create the GitHub release.
2. Optionally, live evaluation `74.x` (plan §7), in a fresh conversation after reinstall (see Handoff Notes).

**Recorded for a later search/grounding milestone** (item 4 was excluded, plan §2.5; also in `KNOWN_LIMITATIONS.md`):
- the 73.12 `sortc` and 73.13 "percentile" recall gaps;
- a false full grounding: "how do I compute the 95th percentile of a column" grounds `full` on `setColDateFormats`, whose derived keywords include `how` and `column`. Fixing it changes `_keywords_from_text`, and therefore the `ask()` gate.

**Still deferred:**
- category inference for elementwise expressions (72.3 finding 1; 73.5 is the same shape; needs its own design);
- the public release readiness track (below).

## Where Things Stand (v0.84.0, tagged 2026-10-13, not pushed)

Full detail is in CHANGELOG and `planning/v0.84-lexical-statement-stream.md`. v0.83.0 is released at https://github.com/ec78/gauss-ai/releases/tag/v0.83.0.

- **v0.84.0 additions:**
  - **One lexer** (`gauss_pre_execution_validation.py`), with each transition backed by a `tgauss.exe -b` spot check (strings before comments, `\` escapes, multi-line strings, nested `/* */`, `@ … @` comments):
    - `lex_gauss_source` → `code_view`/`masked_view`, length- and line-preserving;
    - `strip_comments`;
    - `source_statements`, the `;`-terminated stream with line/column.
  - **Shared consumers:**
    - `call_scan_view`;
    - `collect_user_defined_symbols` (statement-leading targets and `proc` names only; used by `validate_code` and `check_generated_symbols`);
    - `extract_generated_calls`, now across lines;
    - `_governing_assignment`, now over whole statements;
    - `validate_syntax`, which takes RAW code;
    - `check_system_statements`, which reads the masked lines.
  - **New INVALID rules:** `unterminated_block_comment` and `unterminated_at_comment`.
  - **New unknown constructs:** `multiline_string` and `undocumented_comment_form`.
  - **`coverage_gaps`** names undocumented calls (`call_undocumented`).
  - **Fixes:** the 73.10/73.14 defects, 73.x finding 5, and the pre-existing `dos`-behind-a-string handoff_candidate.
- **v0.83.0 additions:**
  - readiness reasons name their real cause;
  - `RoleUnknownCause` is recorded on every unknown role check;
  - `gauss_validate_code` returns `coverage` and `coverage_gaps`;
  - variadic `....`/`\.\.\.` spellings are normalized, a bare "numeric" type means `matrix`, and arguments align with `...`, so `sprintf` reaches candidacy;
  - `gauss_search_docs` lists labeled `candidates` via `search_candidates(...)`, which is never part of grounding. The `ask()` gate is byte-identical to v0.82.0 (and still is in v0.84.0).
- **MCP server** (`scripts/gauss_mcp_server.py`, stdio, optional `mcp` extra) has 9 base tools:
  - `gauss_session_start`/`close`, `gauss_search_docs`, `gauss_validate_code`, `gauss_execution_prepare(validation_id?)`, `gauss_execution_decide`, and `gauss_repair_start`/`command`/`close`;
  - opt-in strict-mode `gauss_chat_ask`/`gauss_chat_reset` (only when `chat-provider` ≠ `fake`).
- **Hybrid path:** the client writes the code, and `gauss_conversation_engine.validate_code(...)` computes the verdict. Execution happens only via a server-issued, single-use `validation_id`.
- **Validation chain:** one shared `validate_generated_code(...)`; a 213-entry `_SYSTEM_STATEMENT_REGISTRY` with categories file read/write, OS/process, source inclusion, directory, `network` and `database`. Code with no documented calls is `not_ready`.
- **Syntax layer** (`validate_syntax`, a bounded rule set, not a parser):
  - `_split_statements` (now a view of `source_statements`) + `_check_control_flow_blocks` validate `for … endfor` (nested included) with a body allowlist;
  - `if`/`do`/`proc`/thread blocks are unknown (`control_flow_block`) → at best `review_required`;
  - the INVALID rules include the four `for_*` rules, `let_statement_shape` and the two comment rules.
- **Tracing:**
  - `_governing_assignment` / `resolve_argument_category` trace a variable to its most recent prior top-level assignment, over whole `;`-terminated statements;
  - option B: indexed writes are looked through for category only, never for preconditions;
  - expressions are never evaluated.
- **Signatures:** nested optional groups are flattened, and `...` means no upper bound (`VARIADIC_MAX_ARGS`).
- **Evaluations:** the last category used is **73** (`73.1`-`73.15`, run 2026-10-12: 13 pass, 2 fail on real defects, both fixed in v0.84.0). The next category is `74`.
- **Tests:** 48 files, all passing; `check_release_readiness.py` passes. The `mcp` extra is installed in this machine's real Python, so the MCP tests actually run.

## Known Issues

- See the top paragraphs of `KNOWN_LIMITATIONS.md` (v0.84.0, v0.83.0, v0.82.0). The 73.x findings are fixed in v0.84.0, except the search recall gaps, which are listed there.
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

- **Windows reinstall** (see `CLAUDE.md`): stop any running `gauss-ai-mcp.exe` before `pip install -e ".[mcp]"`. Then reload the VS Code window (`Ctrl+Shift+P` → "Developer: Reload Window"). New MCP tools and changed behavior appear only in a fresh conversation, so a milestone's live evaluation (`74.x` next) must happen in a new conversation after the reinstall.
- **Machine config** (`C:\Users\Owner\.gauss-ai\config.json`): `chat_provider: ollama` (`qwen2.5-coder:7b`), `default_runner: gauss`, `gauss_executable: C:\gauss26\tgauss.exe`, `workspace_parent: C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`, `docs_root: C:/Users/Owner/.gauss-ai/docs` (the published copy). `GAUSS_AI_MCP_ALLOW_REAL_GAUSS` is **off**, so every MCP prepare on the `gauss` runner returns `real_gauss_not_allowed`, as designed.
- The `evaluations/differential_runs/2026-09-18-*` untracked directories are leftovers from v0.77.0, deliberately untouched; don't commit them.
