# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

**v0.86.0 "Structure Members, Word Operators and Structure Definitions" was released on 2026-10-16** (https://github.com/ec78/gauss-ai/releases/tag/v0.86.0; tag `v0.86.0`, commit `5bb1eaa`; `main` pushed at `5e63d58`): a validator-fix milestone for 75.x findings 1-3. Plan and record: `planning/v0.86-members-word-operators-struct-definitions.md` (§1-§8 approved with every recommendation; §9 deviations and diffs; §10 testing; 201 `tgauss.exe -b` spot checks, m/w/r/d series).
- Done:
  - the code, all in `gauss_pre_execution_validation.py`: member targets in `let_statement_shape` (plus the new `pp->x = {…}` INVALID), `_WORD_OPERATORS` blanked in `call_scan_view` and masked in the separator rule, and `_struct_definitions` with the new INVALID rule `struct_definition_shape`;
  - tests: pre-exec 175-179, engine 150-154 and MCP 26, each confirmed failing on HEAD; 48 files and `check_release_readiness.py` pass;
  - the diffs: docs syntax (79 blocks, exactly as predicted), verdicts (365 programs; all 125 earlier snippets unchanged), gate (61 questions identical), and AST (the engine is unchanged);
  - the version bump to 0.86.0; `README.md`, `CHANGELOG.md` and `KNOWN_LIMITATIONS.md` updated.
- One deviation (§9.2): an index earlier in the path (`d0[1].dataMatrix = {…}`, a structure-array element) is a member target. The all-docs diff found it, and spot checks m33-m38 confirmed it.
- **Live evaluation 76.x ran on 2026-10-19** and is recorded in commit `d67db5b`: plan §11; run files `2026-10-19-…-members-wordops-structs-run-001.md` … `-020.md`; `INDEX.md`, `benchmark-prompts.md` category 76, `benchmark-coverage.md`. Not pushed. `CLAUDE.md` now records the drive-letter keying of local-scope MCP overrides, and the rule to prove the opt-in with one prepare.
- **Live evaluation 77.x (the execution re-evaluation) ran on 2026-10-19** and is recorded: plan §12; run files `2026-10-19-code-assistant-mcp-execution-run-001.md` … `-020.md`; `INDEX.md`, `benchmark-prompts.md` category 77, `benchmark-coverage.md`. Committed, not pushed.
- **Next: scope the next milestone, at the user's choice** (§12.8). The candidates:
  - a small handoff/registry milestone. **77.x finding 2 first** (a reply should bind to the `request_id` the user saw). Then 77.x findings 1 (operator forms skip preconditions) and 3 (the unused "Workspace parent" prompt line), plus 76.x findings 2 (report `real_gauss_allowed` in `gauss_session_start`), 3 (a refused prepare spends its `validation_id`) and 6 (an `eigh` symmetry precondition);
  - the drafted v0.87.0 search/grounding milestone (`planning/v0.87-search-and-grounding-recall.md`, unapproved; add 76.x finding 5, the silent fifth-symbol drop, which recurred in 77.5);
  - or fold the handoff/registry items into v0.87.0.

  76.x finding 4 (`gmmfit.rst` `parEst`) and 75.x finding 8 (`gmmFitControl`, recurred in 77.4) are upstream. Do not start any milestone until the user chooses.

**Live evaluation 76.x (2026-10-19; v0.86 plan §11):** 19 pass, 1 fail (76.1, a client error: it told the user real execution was on).
- **v0.86.0 held live:** all 19 live verdicts reproduced on the v0.86.0 archive. Against v0.85.0, nine snippets go not_ready → review_required and four lose false reasons; none newly reaches handoff_candidate.
- **No code executed through MCP.** The server never received `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1` (finding 1):
  - the local-scope override is stored under the `~/.claude.json` project key `C:/Users/eclow/Documents/GitHub/gauss-ai`;
  - the VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai` (lowercase drive, `mcpServers: {}`), so the tracked `.mcp.json` was used;
  - all three prepares returned `real_gauss_not_allowed`. No prompt was rendered, no decide call was made, and the planned 76.11 decline never happened.
- **Other findings, all pre-existing and safe-direction:**
  - nothing in `gauss_session_start` reports the opt-in (2);
  - a refused prepare still spends its `validation_id`, because the id is popped before the opt-in check (3);
  - upstream, `gmmfit.rst` documents `gOut.parEst` but the member is `paramEst` (4; `G0504`);
  - `gauss_search_docs` silently drops a fifth symbol at `MAX_GROUNDING_SOURCES = 4` (5; for v0.87);
  - `eigh` has no registered symmetry precondition (6).
- **Spot checks:** e01-e08 (`G0071` for a literal into a `scalar` member; `gmmFitControl` undefined; `paramEst` runs).

**Live evaluation 77.x (2026-10-19; v0.86 plan §12): 20 pass, 0 fail.** The first live real-GAUSS execution through MCP.
- **The opt-in reached the server:** the override is now under both `~/.claude.json` keys (`c:/…` and `C:/…`), and a first prepare rendered a prompt (77.1).
- **The execution path held:**
  - four approved runs (77.9 `invpd`, 77.11 `eigh`, 77.16 `sortc`, 77.17 regression), each byte-identical to a direct `tgauss.exe -b` run;
  - one decline (77.10) that executed nothing;
  - one `unrecognized` reply ("Yes approve") that created no approval;
  - consumed ids refused on reuse;
  - `save` correctly `not_ready`.
- **v0.86.0 held:** all 22 live verdicts reproduced on the v0.86.0 archive. Against v0.85.0, 16 change toward the evidence; one, 77.17's restructured regression, goes not_ready → handoff_candidate (no I/O).
- **New findings, all small and pre-existing, none in `KNOWN_LIMITATIONS.md`:**
  1. operator forms (`eye(k) / xx`, `y / X`) skip the precondition registry. A literal singular matrix is not_ready via `inv` but handoff_candidate via `/`; GAUSS fails both loudly (`G0048`);
  2. `gauss_execution_decide` takes no `request_id`, and prepare silently replaces a pending request, so a reply approves whatever was prepared last;
  3. the prompt's "Workspace parent" line is never used: runs execute in a deleted temp directory.
- **Spot checks:** x01-x07; validator probes P1-P5.
- **Setup note:** two `gauss-ai-mcp` processes were running; which one served the session was not determined.

v0.85.0 "Procedure Headers, Defining Pages and Code-Loading Statements" was released on 2026-10-15: https://github.com/ec78/gauss-ai/releases/tag/v0.85.0 (tag `v0.85.0`, commit `f11505e`; `main` pushed). Plan and record: `planning/v0.85-proc-headers-and-defining-pages.md` (§1-§8 plan, §9 deviations and diffs, §10 testing, **§11 live evaluation 75.x**). v0.84.0's record, including live evaluation 74.x (17 pass, 2 fail on the two defects v0.85.0 fixes), is `planning/v0.84-lexical-statement-stream.md` §11.

**Live evaluation 75.x (2026-10-16; v0.85 plan §11; run files `2026-10-16-…-proc-headers-defining-pages-run-001.md` … `-021.md`):** 17 pass, 4 fail. v0.85.0's three changes all held live (v0.84.0 archive comparison: 4 state changes, all toward the evidence), including the user's GAUSS 26 `proc (struct T) = f(..., struct C c, w=0);` headers. Recorded and pushed (`abcf29a`, `163182d`). The four fails come from three pre-existing, safe-direction validator defects, each located and spot-checked (`tgauss.exe -b` sc01-sc13):
1. `let_statement_shape` rejects `s.member = {…}` (valid GAUSS; its evidence covers indexed targets only);
2. `_CALL_SHAPED_RE` reads `.or (`, `.not (`, `or (` … as calls (false not_ready; INVALID inside call arguments);
3. `_check_matrix_literals` reads every `struct Name { … };` definition as a matrix literal.
Also: a false INCOMPATIBLE on `dftype(x, "category")` (string vs documented "vector"); reserved words (`lower`/`upper`, G0276) unchecked; new search items for v0.87 (English words such as `run`/`break`/`call`/`new` ground on command pages; "index" grounds full on the help landing page; `.. include::` unexpanded); upstream doc/library defects (tspdlib `adf_1break` omits `outlier`; `gmmFitIV` matrix input fails; `gmmControlCreate.rst` names a nonexistent struct). GAUSS 26 facts (spot-checked): a declaration is skippable only when the producing proc declares a `(struct T)` return type; `pvCreate()` undeclared fails (G0181/G0025); named defaulted arguments work in any order.

**v0.85.0 summary:**
- Done:
  - §3.1-§3.3: the new INVALID rule `proc_header_parameter`, header names skipped by `call_argument_missing_separator`, `_lookup_defining_page` at the three §2.2 sites, `library` (`source_inclusion`), and `dlibrary`/`dllcall` (`native_code`), so the registry has 216 entries;
  - the §6.1 tests (pre-exec 171-174, engine 143-149, MCP 25), each confirmed failing on HEAD;
  - the §6.2-§6.4 diffs, all as predicted except one extra 74.19 gap, which is pre-existing (§9.2 item 5).
  - 48 files pass, and so does `check_release_readiness.py`. The record is plan §9-§10.
- Next: the user chose the validator milestone for 75.x findings 1-3 as v0.86.0 (implemented, above); the search milestone follows as v0.87.0 (`planning/v0.87-search-and-grounding-recall.md`; 75.x finding 7 feeds it).
- Unchanged: `&` parameters (v0.83.0's decision kept); trailing commas in headers are accepted.
- New pre-existing findings (§9.2 items 5-6): a matrix literal with `.` elements is "an expression" for role checks; a `keyword` definition's name is read as an undocumented call, so its snippet is not_ready.
- The 75.x records (21 run files, `INDEX.md`, `benchmark-prompts.md`, `benchmark-coverage.md`, v0.85 plan §11) are committed (`abcf29a`) and pushed. `planning/v0.87-search-and-grounding-recall.md` (formerly v0.86) is a separate untracked draft. Check with `git status` and `git log origin/main..main`.

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

## Where Things Stand (v0.86.0, released 2026-10-16)

Full detail is in CHANGELOG and the planning docs (`planning/v0.86-*.md`, `planning/v0.85-*.md`, `planning/v0.84-*.md`).

- **v0.86.0 additions** (all in `gauss_pre_execution_validation.py`; the engine is unchanged):
  - `let_statement_shape` accepts a brace literal on a member path (`s.x`, `s.a.b`, `d0[1].x`). A target ending in an index and whitespace around `.` stay INVALID, and `pp->x = {…}` is newly INVALID (spot checks m01-m38).
  - The 11 `_WORD_OPERATORS` (all reserved, G0276) are blanked in `call_scan_view` and masked as operators in `call_argument_missing_separator` (w and r series).
  - `_struct_definitions` and the new INVALID rule `struct_definition_shape` check each member: seven type phrases plus one name (d series). A valid definition is the validated construct `struct_definition`.

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
- **Evaluations:** the last category used is **77** (`77.1`-`77.20`, the execution re-evaluation run 2026-10-19: 20 pass; four approved real-GAUSS runs and one decline through MCP; v0.86 plan §12). 76.x (same day, plan §11) ran without the opt-in. The next category is `78`.
- **Tests:** 48 files, all passing; `check_release_readiness.py` passes. The `mcp` extra is installed in this machine's real Python, so the MCP tests actually run.

## Known Issues

- See the top paragraphs of `KNOWN_LIMITATIONS.md` (v0.86.0, v0.85.0, v0.84.0). v0.86.0's paragraph also holds 75.x findings 4-6 (deferred by decision) and the unmodelled structure-type errors (G0071/G0467/G0507). The 73.x findings are fixed in v0.84.0, except the search recall gaps, which are listed there.
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
- Idle-session eviction for long-running MCP servers.
- MCP sampling, so strict-mode chat could use the client's model. Blocked: Claude Code doesn't support sampling as a client (anthropics/claude-code#1785).

## Handoff Notes

- **Windows reinstall** (see `CLAUDE.md`): stop any running `gauss-ai-mcp.exe` before `pip install -e ".[mcp]"`. Then reload the VS Code window (`Ctrl+Shift+P` → "Developer: Reload Window"). New MCP tools and changed behavior appear only in a fresh conversation, so a milestone's live evaluation (`78.x` next) must happen in a new conversation after the reinstall.
- **Machine config** (`C:\Users\Owner\.gauss-ai\config.json`): `chat_provider: ollama` (`qwen2.5-coder:7b`), `default_runner: gauss`, `gauss_executable: C:\gauss26\tgauss.exe`, `workspace_parent: C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`, `docs_root: C:/Users/Owner/.gauss-ai/docs` (the published copy). `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1` is set through a local-scope `gauss-ai` MCP override in Claude Code's `~/.claude.json`, now under **both** project keys, `c:/Users/eclow/Documents/GitHub/gauss-ai` and `C:/…` (checked 2026-10-19 after 77.x). In 76.x it existed only under `C:/…`, while the VS Code extension used `c:/…`, so prepare returned `real_gauss_not_allowed` (76.x finding 1); 77.x ran with it. Before an execution evaluation:
  1. make sure the override exists under the key the session actually uses;
  2. confirm it with one prepare on a trivial handoff candidate.

  With only the tracked `.mcp.json`, prepare returns `real_gauss_not_allowed`, as designed.
- The `evaluations/differential_runs/2026-09-18-*` untracked directories are leftovers from v0.77.0, deliberately untouched; don't commit them.
