# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

**No milestone in progress.** v0.85.0 "Procedure Headers, Defining Pages and Code-Loading Statements" was released on 2026-10-15: https://github.com/ec78/gauss-ai/releases/tag/v0.85.0 (tag `v0.85.0`, commit `f11505e`; `main` pushed). Plan and record: `planning/v0.85-proc-headers-and-defining-pages.md` (§1-§8 plan, §9 deviations and diffs, §10 testing, **§11 live evaluation 75.x**). v0.84.0's record, including live evaluation 74.x (17 pass, 2 fail on the two defects v0.85.0 fixes), is `planning/v0.84-lexical-statement-stream.md` §11.

**Live evaluation 75.x (2026-10-16; v0.85 plan §11; run files `2026-10-16-…-proc-headers-defining-pages-run-001.md` … `-021.md`):** 17 pass, 4 fail. v0.85.0's three changes all held live (v0.84.0 archive comparison: 4 state changes, all toward the evidence), including the user's GAUSS 26 `proc (struct T) = f(..., struct C c, w=0);` headers. **Recorded, uncommitted** (records only; no code change). The four fails come from three pre-existing, safe-direction validator defects, each located and spot-checked (`tgauss.exe -b` sc01-sc13):
1. `let_statement_shape` rejects `s.member = {…}` (valid GAUSS; its evidence covers indexed targets only);
2. `_CALL_SHAPED_RE` reads `.or (`, `.not (`, `or (` … as calls (false not_ready; INVALID inside call arguments);
3. `_check_matrix_literals` reads every `struct Name { … };` definition as a matrix literal.
Also: a false INCOMPATIBLE on `dftype(x, "category")` (string vs documented "vector"); reserved words (`lower`/`upper`, G0276) unchecked; new search items for v0.86 (English words such as `run`/`break`/`call`/`new` ground on command pages; "index" grounds full on the help landing page; `.. include::` unexpanded); upstream doc/library defects (tspdlib `adf_1break` omits `outlier`; `gmmFitIV` matrix input fails; `gmmControlCreate.rst` names a nonexistent struct). GAUSS 26 facts (spot-checked): a declaration is skippable only when the producing proc declares a `(struct T)` return type; `pvCreate()` undeclared fails (G0181/G0025); named defaulted arguments work in any order.

**v0.85.0 summary:**
- Done:
  - §3.1-§3.3: the new INVALID rule `proc_header_parameter`, header names skipped by `call_argument_missing_separator`, `_lookup_defining_page` at the three §2.2 sites, `library` (`source_inclusion`), and `dlibrary`/`dllcall` (`native_code`), so the registry has 216 entries;
  - the §6.1 tests (pre-exec 171-174, engine 143-149, MCP 25), each confirmed failing on HEAD;
  - the §6.2-§6.4 diffs, all as predicted except one extra 74.19 gap, which is pre-existing (§9.2 item 5).
  - 48 files pass, and so does `check_release_readiness.py`. The record is plan §9-§10.
- Next (not started; only if the user asks): commit the 75.x records; then the user chooses the next milestone: a small validator milestone for 75.x findings 1-3 (v0.85 plan §11.6), and/or the drafted search milestone `planning/v0.86-search-and-grounding-recall.md` (untracked draft, not approved; 75.x finding 7 feeds it).
- Unchanged: `&` parameters (v0.83.0's decision kept); trailing commas in headers are accepted.
- New pre-existing findings (§9.2 items 5-6): a matrix literal with `.` elements is "an expression" for role checks; a `keyword` definition's name is read as an undocumented call, so its snippet is not_ready.
- Uncommitted as of 2026-10-16: the 75.x records (21 run files, `INDEX.md`, `benchmark-prompts.md`, `benchmark-coverage.md`, v0.85 plan §11) and this status update. `planning/v0.86-search-and-grounding-recall.md` is a separate untracked draft. Check with `git status` and `git log origin/main..main`.

**Recorded for a later search/grounding milestone** (item 4 was excluded, plan §2.5; also in `KNOWN_LIMITATIONS.md`):
- the 73.12 `sortc` and 73.13 "percentile" recall gaps (both reproduced in 74.14/74.15);
- a false full grounding: "how do I compute the 95th percentile of a column" grounds `full` on `setColDateFormats`, whose derived keywords include `how` and `column`. Fixing it changes `_keywords_from_text`, and therefore the `ask()` gate. Still live on 2026-10-15;
- new in 74.x (§11.5 finding 5):
  - `for` is a question stopword, so the `for` page is unreachable;
  - a hyphenated candidate (`tspdlib-landing`) cannot be opened by searching its name;
  - long-page excerpts stop before Outputs (finding 6);
  - `command_doc_lookup.lookup` truncates to `max_results` before its tie check, so `max_results=1` callers never see a tie. v0.85 fixes only the validation path (plan v0.85 §4).

**Still deferred:**
- category inference for elementwise expressions (72.3 finding 1; 73.5 is the same shape; needs its own design);
- the public release readiness track (below).

## Where Things Stand (v0.85.0, released 2026-10-15)

Full detail is in CHANGELOG and the planning docs (`planning/v0.85-*.md`, `planning/v0.84-*.md`). v0.84.0 is released at https://github.com/ec78/gauss-ai/releases/tag/v0.84.0.

- **v0.85.0 additions:** the INVALID rule `proc_header_parameter` (`proc`/`keyword` header grammar from spot checks s1, s2, h1-h14; header names are no longer checked as calls); `_lookup_defining_page` (grounding excerpt and validator signatures come from the page grounding resolved); `library` → `source_inclusion`, `dlibrary`/`dllcall` → new category `native_code` (216 registry entries).
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
- **Validation chain:** one shared `validate_generated_code(...)`; a 216-entry `_SYSTEM_STATEMENT_REGISTRY` with categories file read/write, OS/process, source inclusion, directory, `network`, `database` and `native_code` (v0.85.0). Code with no documented calls is `not_ready`.
- **Syntax layer** (`validate_syntax`, a bounded rule set, not a parser):
  - `_split_statements` (now a view of `source_statements`) + `_check_control_flow_blocks` validate `for … endfor` (nested included) with a body allowlist;
  - `if`/`do`/`proc`/thread blocks are unknown (`control_flow_block`) → at best `review_required`;
  - the INVALID rules include the four `for_*` rules, `let_statement_shape` and the two comment rules.
- **Tracing:**
  - `_governing_assignment` / `resolve_argument_category` trace a variable to its most recent prior top-level assignment, over whole `;`-terminated statements;
  - option B: indexed writes are looked through for category only, never for preconditions;
  - expressions are never evaluated.
- **Signatures:** nested optional groups are flattened, and `...` means no upper bound (`VARIADIC_MAX_ARGS`).
- **Evaluations:** the last category used is **75** (`75.1`-`75.21`, run 2026-10-16 after the v0.85.0 release: 17 pass, 4 fail on three real pre-existing defects, v0.85 plan §11). The next category is `76`.
- **Tests:** 48 files, all passing; `check_release_readiness.py` passes. The `mcp` extra is installed in this machine's real Python, so the MCP tests actually run.

## Known Issues

- See the top paragraphs of `KNOWN_LIMITATIONS.md` (v0.84.0, v0.83.0, v0.82.0). The 73.x findings are fixed in v0.84.0, except the search recall gaps, which are listed there.
- The 74.x findings that remain open (search items, the header grammar's unchecked shapes, the 8 still-ambiguous symbols, `.` literals, `keyword` names) are in `KNOWN_LIMITATIONS.md` (v0.85.0 paragraph).
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

- **Windows reinstall** (see `CLAUDE.md`): stop any running `gauss-ai-mcp.exe` before `pip install -e ".[mcp]"`. Then reload the VS Code window (`Ctrl+Shift+P` → "Developer: Reload Window"). New MCP tools and changed behavior appear only in a fresh conversation, so a milestone's live evaluation (`75.x` next) must happen in a new conversation after the reinstall.
- **Machine config** (`C:\Users\Owner\.gauss-ai\config.json`): `chat_provider: ollama` (`qwen2.5-coder:7b`), `default_runner: gauss`, `gauss_executable: C:\gauss26\tgauss.exe`, `workspace_parent: C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`, `docs_root: C:/Users/Owner/.gauss-ai/docs` (the published copy). `GAUSS_AI_MCP_ALLOW_REAL_GAUSS` is **off**, so every MCP prepare on the `gauss` runner returns `real_gauss_not_allowed`, as designed.
- The `evaluations/differential_runs/2026-09-18-*` untracked directories are leftovers from v0.77.0, deliberately untouched; don't commit them.
