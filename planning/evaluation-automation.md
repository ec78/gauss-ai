# Evaluation automation: snippet replay and a Codex test client

Status: proposal (2026-11-18). Not a milestone, and it does not start v0.95. Nothing here changes `gauss-ai` itself or relaxes a project-wide constraint.

## 1. Why

Live evaluations 70.x-86.x are run by hand. The user asks each task in a fresh Claude Code conversation, and afterwards the developing session does the following by hand:

- re-runs every snippet on a `git archive` of the previous release;
- diffs the verdicts;
- re-runs the approved programs with `tgauss.exe -b`;
- writes the run files.

86.x took about ten tasks of the user's time and most of a session for the replay (the scratchpad `rv86.py`, `tg86.py` and `bnd86.py`). Two parts can be automated without weakening what an evaluation proves:

1. **Snippet replay.** This needs no agent; it is deterministic (§2).
2. **The client side of tasks that never execute.** A Codex agent asks the tasks: search, read and validate (§3).

The user's own yes or no on a run prompt stays manual (§4).

## 2. Part A: snippet replay tool

`evaluations/tools/replay_snippets.py`.

It lives outside `scripts/`, so it is not packaged and `pyproject.toml`'s `py-modules` is untouched. It is a developer tool, not a product module.

**Input:**
- one or more client transcripts. It has an extractor for each format:
  - Claude Code `~/.claude/projects/<project>/*.jsonl`, taking `tool_use` blocks named `*gauss_validate_code`;
  - Codex `codex exec --json` event streams (§3).
- a baseline ref, for example `v0.94.1`. The tool makes `git archive -o` of the ref's `scripts/` into a temporary directory. This is the `tar` route that works on Windows.
- `--docs-root`, `--gauss-executable` and optionally `--input-dir`, for the analysis-folder file context.

**Per snippet,** it runs `validate_code` on HEAD and on the baseline, each in its own subprocess so the two module trees never mix. It records:
- the state and reasons;
- `pre_execution.coverage` gaps;
- `parameter_role_checks` (status, origin);
- the `system_statements` names.

**Output:** a JSON file and a Markdown table, ready to paste into a run file. The table rows are:

`n | task | baseline state | HEAD state | moved? | gap causes`

**`--run` (opt-in, manual only):**
- It writes each `handoff_candidate` snippet to a fresh scratch directory, copies in any declared `input/` files, and runs `tgauss.exe -b`.
- It records the exit status and the first error line (`G####`).
- Real GAUSS is touched only when the flag is given. It is never called from the automated test suite, which keeps "tests never read a real GAUSS install" intact.

**Guard:** a `--self-check` mode runs the extractors over a small synthetic transcript fixture. That fixture can be committed; the real transcripts never are.

This one tool replaces `rv86.py`, `tg86.py` and `bnd86.py`. It also makes the "re-run on the previous release" rule in `CLAUDE.md` cheap enough to apply to every evaluation.

## 3. Part B: a Codex test client for tasks that never execute

Codex CLI is installed (0.162.1). `codex exec` runs one non-interactive turn, so each task is a fresh conversation. Its useful flags are:

- `--json`, the JSONL event stream;
- `-o`, the final message;
- `--ephemeral`;
- `-C <dir>`;
- `-s <sandbox>`;
- `-p <profile>`;
- `--skip-git-repo-check`;
- `--ignore-user-config`.

A second vendor's model also tests something the Claude-only runs cannot: whether the server's tool descriptions and instructions are enough for a client that was not developed alongside them.

**Setup (one-time, the user's machine):**
- A Codex profile `gauss-eval` registers `[mcp_servers.gauss-ai] command = "gauss-ai-mcp"` with **no** `GAUSS_AI_MCP_ALLOW_REAL_GAUSS`. With that variable unset, an attempted run stops at `real_gauss_not_allowed`.
- A clean test directory outside the repo, containing:
  - no `AGENTS.md`, `CLAUDE.md` or planning docs;
  - its own analysis folder with copies of the data files.

**Runner:** `evaluations/tools/run_codex_tasks.py <tasks.md> <out_dir>`.
- For each task it runs `codex exec --json --ephemeral --skip-git-repo-check -p gauss-eval -C <test_dir> -s <sandbox> -o <out>/taskNN-final.md "<task text>"`, sending stdout to `<out>/taskNN.jsonl`.
- It runs tasks one at a time and stops on the first infrastructure error, such as the MCP server failing to start. It never retries a task to get a better answer.
- `out_dir` is a scratch or inbox folder outside the repo. Raw transcripts contain local paths and are not committed, as with the Claude Code transcripts today.

**Grading** stays with the developing session and uses the existing rules:
- It reads the JSONL and lists the tool calls: search queries, which pages were read, and every validate call and its verdict.
- It lists every shell command Codex ran, so a `curl` or a read of `gauss-ai` source is disclosed.
- It runs the replay tool (§2), then writes the run files, the `INDEX.md` row, the coverage row and the benchmark category, as now.
- A Codex category is labelled as one, for example "(Codex client, automated)", with the model named. Its scores are never merged with a Claude-client category.

**Handoff to the developing session:** there is no message channel between Codex and Claude Code. The runner writes to `out_dir`, the user says "batch done", and the session reads the folder.

## 4. What stays manual, and why

- **Answering run prompts.**
  - A run is possible only through a server-issued, single-use `validation_id` and a `request_id` held in the MCP server's memory.
  - `codex exec` ends its MCP server when the turn ends, so a prompt prepared in one `exec` cannot be answered later. Batching approvals across processes would mean persisting that state, which weakens the boundary.
  - The rule is also the point of the test: the client never answers a run prompt itself.

  Execution tasks therefore stay interactive. The user runs them either in the Codex TUI with the local opt-in, or in Claude Code as now. The replay tool's `--run` covers the "does approved code run in GAUSS" half without an agent.
- **Writing the tasks and expected outcomes.** The developing session writes them into the planning doc before the run, as now. The Codex test directory never contains them.
- **Release, push and publish** decisions.

## 5. Decisions (taken 2026-11-18: the user accepted every recommendation below)

1. **Codex sandbox.** Options:
   - `read-only` with no network: the default proposal. It measures gauss-ai's own path.
   - `workspace-write` with network: this reproduces 86.5's `curl` route and measures how far an agent with a shell gets around the checks.

   Recommendation: `read-only` for the regular batches, and one deliberate `workspace-write` batch per data milestone.
2. **Codex model:** the profile's default, or a pinned model so categories are comparable over time. Recommendation: pin it, and name it in each run file.
3. **Where the tools live:** `evaluations/tools/`, as proposed, or `scripts/`. Putting them in `scripts/` would need `py-modules` entries and per-module tests.

## 6. Proposed first steps

1. Build §2 and use it to reproduce 86.x's replay table against `v0.94.1`. Done when the table matches §16 and §17 of `planning/v0.94-data-import-and-export.md`.
2. Build §3 and run the 86.x tasks through Codex, with the `read-only` sandbox and no opt-in. Every task stops at its verdict, or at `real_gauss_not_allowed`. 86.x has known results, so the first Codex category can be compared task by task with the Claude client, up to the run prompt.
3. Record that comparison as a new evaluation category. If it is useful, use automated batches for search and validate coverage in v0.95, and keep execution tasks manual.

## 7. Part A built (2026-11-18)

`evaluations/tools/replay_snippets.py`, as in §2. `--self-check` covers the extractors on synthetic Claude Code and Codex transcripts, including duplicate call ids, `item.started`/`item.completed` pairs, JSON-string arguments, command and meta records, and pipe escaping in the table. It passes.

**Acceptance: the 86.x transcript against `v0.94.1`**, with the 86x analysis folder and `--run`:
- 24 snippets were extracted.
- Per-snippet states match the hand replay exactly, on both versions. On `v0.94.1`: 10 `handoff_candidate`, 12 `review_required`, 2 `not_ready`. On HEAD: 11 `handoff_candidate`.
- The one state move is snippet 20, 86.6's `dstatmt` program, and it runs. Snippets 10 and 11, 86.4's `$|` renames, change reasons only. This is §17.3 of `planning/v0.94-data-import-and-export.md`.
- All 11 HEAD candidates exit 0 in `tgauss.exe -b`.

**The tool found a counting error in the 86.x record.** §16 there, `CHANGELOG.md`, `PROJECT_STATUS.md` and `evaluations/runs/INDEX.md` said "16 held back". The 24 snippets hold back 14 on `v0.94.1` (12 `review_required` and 2 `not_ready`), and all four were corrected.

**Known simplification:** the Claude Code extractor numbers a new task at every real user message, so a user's "yes" to a run prompt also starts a "task". The JSON keeps each task's text for mapping to the run files. The Codex runner writes one file per task, so it is unaffected.

## 8. Part B built, and a pilot on the 86.x tasks (2026-11-18)

**Tools:**
- `evaluations/tools/run_codex_tasks.py`, with `setup` and `run`.
- `evaluations/tools/summarize_codex_run.py`, which lists, per task, every gauss-ai call with its verdict and every shell command, flagging paths and URLs outside the work folder.
- `evaluations/tools/tasks-86x.md`, the 86.x user messages verbatim.
- `evaluations/tools/preamble-no-execution.md`.
- The eval folder is `C:\Users\Owner\Documents\gauss-ai-codex-eval`:
  - `home/` holds the eval's own gauss-ai config;
  - `data/input/` holds fresh copies of `fred_macro.csv` and `wage_returns.csv`;
  - `work/` is empty;
  - `inbox/` holds the transcripts.

**Model and settings found on setup:**
- `gpt-6.2-sol` and `gpt-6.2-astra` are in Codex's model list, but a ChatGPT-account login refuses both ("not supported when using Codex with a ChatGPT account"). The default is therefore `gpt-6.1-sol`, the newest model the account accepts.
- On this machine, `codex` on PATH is an npm shim, so the runner calls `node .../@openai/codex/bin/codex.js` directly. Going through `cmd.exe` would re-parse the TOML `-c` values.
- `--ignore-user-config` is needed. Without it, the user's own config adds browser and computer-use plugins, hooks and a second MCP server. Auth still loads.
- Codex's built-in web search is **not** covered by the read-only sandbox. Batch 1 showed this (below), and `-c web_search="disabled"` removes the tool, which is now passed on every run. One caveat: with the tool removed, a probe still answered FRED's latest GDP value with a citation marker, which may be model memory. The removal is confirmed by the tool list, not by that answer.

**Batch 1** (verbatim tasks, no preamble, web search on):
- Codex validated code in 5 of 10 tasks.
- Told by `gauss_session_start` that execution is off, it stopped before writing any code in 86.1, 86.3 and 86.6. In 86.4 it searched and then asked the user to attach the CSV. In 86.2 it told the user to restart the server with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`.
- **86.5 bypassed gauss-ai completely.** It opened `fred.stlouisfed.org/data/GDP.txt` through web search and reported "an OLS regression" (slope 84.578, R² 0.8464) that no code computed; the sandbox allowed no commands, and no gauss-ai call was made. These are unverifiable numbers presented as results: a client behaviour, not a gauss-ai defect, and the reason web search is now off.
- Each `gauss_execution_prepare` (86.7 and 86.9) returned `real_gauss_not_allowed`, as designed.

**Batch 2** (with the preamble, web search off):
- Codex validated code in 9 of 10 tasks. In 86.0 the MCP tools did not load: about 25k input tokens against the usual 80-90k, with nothing on stderr. Two reruns were normal, so the runner now warns on any task with no gauss-ai call and never retries it silently.
- There were 15 snippets in all (with the 86.0 rerun), replayed against `v0.94.1` with `--run --run-all`. No state moves.
  - **3 `handoff_candidate`:** 86.7, 86.8 and 86.9; all run.
  - **7 `review_required`:** five run cleanly, so they are false gaps (86.2, 86.3 ×2, 86.4, 86.9's first version). The two 86.1 versions stop in GAUSS with `G0472`, "column 'female' not found", so holding them back was right: a column picked by name is case-sensitive, a formula string is not (86.8's `"region + wage"` runs). This is the same unread form v0.94.2 deliberately left unread (plan v0.94 §17.2).
  - **5 `not_ready`, each by design:** `fred_load` ×2 (network), `output file = ...` (86.6, a file write outside the allowed-access registry), `errorlog` (86.2, documented as writing the error log file), and `print 2 + 2;` (no documented call).
- No shell command and no web search ran in any task.

**Compared with the Claude client in 86.x:**
- The Claude client iterated to a candidate in eight tasks, averaging 2.4 validations per task. Codex stopped after one or two validations and reported the verdict.
- Codex wrote its programs without seeing the data: no shell, and no gauss-ai tool shows an input file's columns. It guessed `female`, `region` and `wage`, and asked for the file in batch 1's 86.4.

**Candidate finding for gauss-ai (the user's decision, not started):** a client without its own file access cannot learn an input file's column names before execution. One option is for `gauss_session_start`'s analysis-folder report to give each listed CSV's header row. That is read-only and deterministic, and from files the server already digests.

**Not recorded as an evaluation category.** This was a pilot: batch 2 used a preamble, and the 86.x tasks' expected outcomes were written for an execution-enabled client. A scored Codex category should state its own expected outcomes for a no-execution client first, per the live-evaluation rules.
