# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

**v0.88.0 "Search and Grounding Recall" was committed, tagged and pushed on 2026-10-21** (tag `v0.88.0`, commit `be3df16`; `main` pushed). GitHub release: https://github.com/ec78/gauss-ai/releases/tag/v0.88.0 (published 22:57 UTC). Plan and record: `planning/v0.88-search-and-grounding-recall.md` (§1-§8 approved with every recommendation: 1A, 2 yes, 3a, 4-8 yes, 9a, 10 defer, 11-12 yes; §9 deviations and diffs; §10 testing). The full gate diff is `planning/v0.88-gate-diff.md`. Baseline for every comparison: a `git archive` of `cf4434c`.
- Done:
  - `gauss_conversation_engine.py`:
    - derived keyword matches are search candidates only;
    - `_page_defines` (stem, heading symbol, or whole word in the syntax blocks) gates literal grounding, `validate_code` and `validate_generated_code`'s extra lookups;
    - statement pages ground only when the word is code-marked;
    - `index.rst` never grounds;
    - 12 curated aliases, matched on whole words;
    - one-word stopword queries and hyphenated page names;
    - excerpts keep Outputs;
    - `omitted_topics`, with tier 3 = the documented-symbol set;
    - `_lookup_command` and the alias check read the defining page;
    - `search_candidates` lists the new labeled origins.
  - `gauss_mcp_server.py`: `omitted_topics` + `omitted_note` in search, `omitted_topics` in chat output, and `REPLY_GUIDANCE` in the instructions and the decide description. `gauss_ai_chat.py`: the banner names omitted topics.
  - Tests: engine 159-170 and MCP 33-36 (16 new, all fail on `cf4434c`); `test_84`, `test_137` and four `test_138` rows updated with inline comments; `test_149` unchanged. 48 files and `check_release_readiness.py` pass.
  - Diffs:
    - baseline §2 numbers reproduced, all 915 HEAD rows equal the planning run (silent drops 74, not 72: two derived fifths);
    - gate: 787 tuples and 297 policies change; the 33 rows toward generation were reviewed individually, each on the page the question names;
    - verdicts: v0.87's 460 programs unchanged, only fn01-fn05/fn07 go review_required → not_ready, and nothing newly reaches handoff_candidate;
    - excerpts: 77 change (33 had no Outputs, 44 a cut Outputs), and 0 symbols now lose Outputs;
    - AST: `command_doc_lookup.py`, the gate, the validator and the execution core are identical.
  - Version 0.88.0. `README.md` (v0.87.0 prepended to the chain), `CHANGELOG.md`, `KNOWN_LIMITATIONS.md` (including the 78.x multi-session line and the deferred `.. include::` item) and `docs/mcp-server.md` are updated.
- **Deviations (plan §9.1):**
  1. `MAX_RESOLUTIONS` counts only resolved/ambiguous entries. Sentence words were pushing aliases out ("Save a matrix of results to a file", the logistic prompt, "Translate this Python idea"), so every unresolved word is now reported;
  2. alias list: `declare` dropped (its Purpose is global variables), `reorder columns` dropped, bare `structure` not a phrase, `gmmFit` added;
  3. whole-word alias matching;
  4. 77 excerpts change, not 33;
  5. §3.9 also applies in `validate_code`;
  6. pages already cited are not listed again as candidates.
- **Observations disclosed:** `vector(x)` stays review_required (`vectordl.rst`'s heading names it); quoted prose words count as code ("continue"); `test`/`note` ambiguity forces `clarify` in 7 rows.
- **Live evaluation 79.x ran on 2026-10-21** (19:10-19:30 local, after the release), and is recorded: plan §11; run files `2026-10-21-code-assistant-mcp-search-grounding-recall-run-001.md` … `-013.md`; `INDEX.md`, `benchmark-prompts.md` category 79, `benchmark-coverage.md`. **13 pass.**
  - All 24 live responses (13 searches, 11 validations) are identical to a v0.88.0 archive re-run in every field. No verdict differs on v0.87.0. 9 of 13 search bundles do, all toward the evidence: `quantile` and `sortc` aliases, no `break.rst` for "structural break", `for`/`endfor` open, Outputs in `sqpSolveMT`'s excerpt, `omitted_topics: ['cols']` (v0.87.0 silently dropped `invpd`).
  - Two approved real-GAUSS runs (79.1, 79.2), byte-identical to direct `tgauss.exe -b`. Two correct blocks (`library`; `dlibrary`/`dllcall`). Every review_required snippet runs correctly in GAUSS. No decline; a post-run spent-id resubmission was refused (the recording session's own "yes" on a non-pending request is disclosed, plan §11.5).
  - The client followed the `adf_1break` candidate to its page and used `omitted_topics`. It read doc files from disk five times, three of them for content past the 1,500-character excerpt.
  - Findings (§11.6):
    1. No tool returns more than the excerpt (`sqpSolveMT` return codes, `dllcall` Remarks), and KL's "the full page is one search away" is wrong for that case. This matters for a stranger's client without disk access → v0.89.0;
    2. a `for t` loop makes an earlier `T` untraced wherever the loop is (pre-existing, safe-direction, not in KL);
    3. the client bypassed search for content search can reach (observation);
    4. upstream `logical-or.rst` names a nonexistent `dotor`;
    5. a probe: "return codes" grounds `return.rst` (already disclosed class).
  - Not exercised live: an invented name (a probe gives not_ready), `olsmt`, strict-mode `gauss_chat_ask`, opening a hyphenated candidate by name (the client bypassed the tool; a probe shows it works).
  - Recommendation (§11.8): v0.88.0 holds; carry findings 1-2 into v0.89.0; no re-run needed.
- **Next:** v0.89.0 (release readiness), with 79.x findings 1-2. Do not start it until the user asks.

**v0.87.0 "Handoff Binding and Precondition Coverage" was committed, tagged and pushed on 2026-10-20** (tag `v0.87.0`, commit `4103280`; `main` pushed). GitHub release: https://github.com/ec78/gauss-ai/releases/tag/v0.87.0. Plan and record: `planning/v0.87-handoff-binding-and-precondition-coverage.md` (§1-§8 approved on 2026-10-20 with every recommendation; §9 deviations and diffs; §10 testing; 42 `tgauss.exe -b` spot checks, dv/eg series). It fixes 77.x findings 1-3 and 76.x findings 2, 3 and 6.
- Done:
  - `gauss_mcp_server.py`: `gauss_execution_decide(..., request_id)` refuses a missing id (`request_id_required`), a replaced prompt (`request_superseded`) or any other id (`request_not_pending`) before parsing, and echoes `request_id`/`request_digest`; prepare reports `replaced_request_id`; a refused prepare no longer spends its `validation_id`; `gauss_session_start` reports `real_gauss_allowed` (+ `execution_hint`);
  - the prompt's "Workspace parent" line is now "Runs in: a new temporary directory, deleted after the run", and neither caller puts `workspace_parent` on the request (the only change in `gauss_execution_handoff.py`);
  - `gauss_pre_execution_validation.py`: `check_operator_preconditions` (a literal-divisor check for `/`: violated with a known matrix dividend, unverified with an unknown one, nothing for scalars or runtime divisors) and an `eigh`/`eighv` symmetry precondition (runtime input unverified);
  - tests: MCP 27-32, handoff 46, chat 49, pre-exec 180-183, engine 155-158 (14 of 16 fail on HEAD; 183 and 158 are invariance); MCP 06/12/13/15/18 now pass a `request_id`. 48 files and `check_release_readiness.py` pass;
  - the diffs: verdicts (460 programs; all 406 earlier snippets keep their state, the six `eigh` ones gain a satisfied precondition; nothing newly reaches handoff_candidate), the handoff surface (as predicted), AST (only the planned names) and gate (61 questions identical);
  - version 0.87.0; `README.md`, `CHANGELOG.md`, `KNOWN_LIMITATIONS.md`, `docs/mcp-server.md`, `docs/controlled-execution-handoff.md` and `CLAUDE.md` (decision 13) updated;
  - the search draft renamed to `planning/v0.88-search-and-grounding-recall.md` (v0.88.0; its live evaluation renumbered 79.x).
- One plan error corrected (§9.2): eg10 (`eigh(x')` of a non-symmetric literal) is violated, not satisfied.
- New pre-existing finding, disclosed (decision 11): `inv`'s absolute 1e-9 determinant bound flags `{1 0, 0 1e-10}`, which GAUSS inverts (dv10/dv11).
- **Live evaluation 78.x ran on 2026-10-20** and is recorded: plan §11; run files `2026-10-20-code-assistant-mcp-handoff-binding-run-001.md` … `-016.md`; `INDEX.md`, `benchmark-prompts.md` category 78, `benchmark-coverage.md`. **16 pass.**
  - Eight approved real-GAUSS runs, each byte-identical to direct GAUSS; every decide carried and echoed the prompt's request_id; three unrecognized replies ("ye", "A: yes", "Prompt B: yes") ran nothing; `save` blocked. All 21 live verdicts reproduced on the v0.87.0 archive; against v0.86.0, three change state, all toward the evidence (non-symmetric `eigh`, `eye(2) / A`, `eigh(vcx(x))`).
  - **Not exercised live:** the replacement path (the client opened one session per prompt, finding 1), and any decline (the user approved 78.3). Probe B1 (recording session, real stdio transport, fake runner) confirmed `replaced_request_id`, `request_superseded`, `request_id_required`, a decline with echo, a refused spent id and a repeated refusal.
  - Findings: (1) one pending prompt per session, but sessions multiply it, so with several open prompts the client alone maps a bare reply (disclose in KL); (2) the client suggested labelled replies ("A: yes") that the parser rejects (one sentence of guidance in the decide description); (3) `eigh` of a runtime value holds back correct covariance code and steers toward `eig` (decision 8's cost, observation); (4) the no-documented-call rule was met by an incidental `ones(2,2)` call (pre-existing, observation). Known items recurred: the 1e-9 bound, runtime `/` divisors, the fifth-symbol search drop, English-word grounding.
  - Client conduct: it grepped `KNOWN_LIMITATIONS.md` and this milestone's plan and read one source file during the tasks (plan §11.7).
  - Recommendation (§11.8): v0.87.0 stays released; no dedicated binding re-run; carry findings 1-2 into the next release's KL and tool text.
  - Recorded in commit `2071119` and pushed.
- **Next (superseded):** v0.88.0 was chosen, re-planned and approved on 2026-10-21 (above).

**v0.86.0 "Structure Members, Word Operators and Structure Definitions" was released on 2026-10-16** (https://github.com/ec78/gauss-ai/releases/tag/v0.86.0; tag `v0.86.0`, commit `5bb1eaa`): a validator-fix milestone for 75.x findings 1-3. Plan and record: `planning/v0.86-members-word-operators-struct-definitions.md` (§9-§10 implementation; §11 live evaluation 76.x; §12 live evaluation 77.x, both recorded and committed).

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

## Where Things Stand (v0.87.0, implemented 2026-10-20; v0.86.0 released 2026-10-16)

Full detail is in CHANGELOG and the planning docs (`planning/v0.86-*.md`, `planning/v0.85-*.md`, `planning/v0.84-*.md`).

- **v0.87.0 additions:** `gauss_execution_decide` bound to a `request_id` (refusals `request_id_required`/`request_superseded`/`request_not_pending`; outcomes echo `request_id`/`request_digest`); prepare reports `replaced_request_id` and spends a `validation_id` only when it returns a prompt; `gauss_session_start` reports `real_gauss_allowed`; the prompt says "Runs in: a new temporary directory, deleted after the run"; `check_operator_preconditions` (`/` literal divisor) and `eigh`/`eighv` symmetry preconditions.
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
  - `gauss_session_start`/`close`, `gauss_search_docs`, `gauss_validate_code`, `gauss_execution_prepare(validation_id?)`, `gauss_execution_decide(response_text, request_id)`, and `gauss_repair_start`/`command`/`close`;
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
- **Evaluations:** the last category used is **79** (`79.1`-`79.13`, v0.88.0, run 2026-10-21: 13 pass; v0.88 plan §11). The next category is `80`. Before that, **78** (`78.1`-`78.16`, v0.87.0, run 2026-10-20: 16 pass; plan §11). Before that, **77** (`77.1`-`77.20`, the execution re-evaluation run 2026-10-19: 20 pass; four approved real-GAUSS runs and one decline through MCP; v0.86 plan §12). 76.x (same day, plan §11) ran without the opt-in.
- **Tests:** 48 files, all passing; `check_release_readiness.py` passes. The `mcp` extra is installed in this machine's real Python, so the MCP tests actually run.

## Known Issues

- See the top paragraphs of `KNOWN_LIMITATIONS.md` (v0.86.0, v0.85.0, v0.84.0). v0.86.0's paragraph also holds 75.x findings 4-6 (deferred by decision) and the unmodelled structure-type errors (G0071/G0467/G0507). The 73.x findings are fixed in v0.84.0, except the search recall gaps, which are listed there.
- The 74.x findings that remain open (search items, the header grammar's unchecked shapes, the 8 still-ambiguous symbols, `.` literals, `keyword` names) are in `KNOWN_LIMITATIONS.md` (v0.85.0 paragraph).
- **Claude Code keeps stale tool descriptions** for MCP tools whose names didn't change across a server upgrade. This is cosmetic.
- **Pip debris:** `~auss_ai-0.79.0.dist-info` in `C:\Users\Owner\AppData\Local\Programs\Python\Python312\Lib\site-packages` causes a harmless "Ignoring invalid distribution" warning. The user can delete it at any time.

## Later

**Path to MVP (agreed with the user 2026-10-20).** The MVP is a publicly available MCP that a stranger can install, connect and use safely. The path:
1. v0.87.0: handoff binding plus small handoff/registry items (released 2026-10-20; 78.x: 16 pass);
2. v0.88.0: search/grounding recall (`planning/v0.88-search-and-grounding-recall.md`; released 2026-10-21; 79.x: 13 pass);
3. v0.89.0: release readiness (the decisions below, README quickstart, PyPI packaging, platform decision);
4. a round with one or two outside GAUSS testers on a clean install, then a public-alpha / v1.0 decision.

Open product question (needs the user's sign-off, since it touches a project-wide constraint): the run path is narrow. In 77.x only 6 of 22 snippets reached a run prompt, because expressions are never evaluated. The choice is to pitch the MVP as validation-first, or to widen what can run.

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

- **Windows reinstall** (see `CLAUDE.md`): stop any running `gauss-ai-mcp.exe` before `pip install -e ".[mcp]"`. Then reload the VS Code window (`Ctrl+Shift+P` → "Developer: Reload Window"). New MCP tools and changed behavior appear only in a fresh conversation, so a milestone's live evaluation (`80.x` next) must happen in a new conversation after the reinstall.
- **Machine config** (`C:\Users\Owner\.gauss-ai\config.json`): `chat_provider: ollama` (`qwen2.5-coder:7b`), `default_runner: gauss`, `gauss_executable: C:\gauss26\tgauss.exe`, `workspace_parent: C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`, `docs_root: C:/Users/Owner/.gauss-ai/docs` (the published copy). `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1` is set through a local-scope `gauss-ai` MCP override in Claude Code's `~/.claude.json`, now under **both** project keys, `c:/Users/eclow/Documents/GitHub/gauss-ai` and `C:/…` (checked 2026-10-19 after 77.x). In 76.x it existed only under `C:/…`, while the VS Code extension used `c:/…`, so prepare returned `real_gauss_not_allowed` (76.x finding 1); 77.x ran with it. Before an execution evaluation:
  1. make sure the override exists under the key the session actually uses;
  2. confirm it with one prepare on a trivial handoff candidate.

  With only the tracked `.mcp.json`, prepare returns `real_gauss_not_allowed`, as designed.
- The `evaluations/differential_runs/2026-09-18-*` untracked directories are leftovers from v0.77.0, deliberately untouched; don't commit them.
