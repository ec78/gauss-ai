# MCP Server

**Status: added in `v0.79.0`; hybrid validation path added in `v0.80.0`.**

`gauss-ai` can run as a local MCP (Model Context Protocol) server, so MCP clients on the same machine (Claude Code, Claude Desktop) can use it as a GAUSS toolkit:

- search the official documentation;
- deterministically validate GAUSS code;
- run validated code through a controlled, human-approved execution handoff;
- drive the guided repair pipeline.

This is a transport layer only. Every tool wraps the same deterministic code the CLI uses, and no safety decision is made by a model.

## Install and run

```
pip install -e ".[mcp]"      # the base CLI stays dependency-free; only the server needs this
gauss-ai docs fetch          # one-time download of the official docs (see gauss-documentation-setup.md)
```

Run the server with `gauss-ai mcp` or `gauss-ai-mcp`. Either one starts it over stdio, with no network port. Register it with a client, for example:

```
claude mcp add --transport stdio gauss-ai gauss-ai-mcp
```

This repository also ships a project-scoped `.mcp.json` and a Claude Code plugin manifest (`.claude-plugin/`).

## Two ways to get from a question to code

**Hybrid (always available, no extra model).** The client's own model (Claude, ChatGPT, ...) writes the GAUSS code, and `gauss-ai` judges it:

1. `gauss_session_start`
2. `gauss_search_docs` to look up the functions you need
3. write the code
4. `gauss_validate_code`
5. if eligible: `gauss_execution_prepare(validation_id)` → show the user the prompt → the user's own yes/no → `gauss_execution_decide(session_id, response_text, request_id)`, with the `request_id` prepare returned alongside that prompt

The code comes from the client; the readiness verdict is always computed by `gauss-ai`.

**Strict (opt-in).** `gauss_chat_ask` uses `gauss-ai`'s *own* configured model. The difference is that it can refuse to generate code at all for a topic it can't ground, while the hybrid path can only refuse to validate or execute code after it has been written. These tools exist only when `chat-provider` is set to `ollama` or `anthropic`. The default `fake` provider never enables them, and a running Ollama is never auto-detected.

## Tools

| Tool | Purpose |
| --- | --- |
| `gauss_session_start` | Starts a session. Optional `runner`, `gauss_executable`, `workspace_parent`, `timeout_seconds`, `docs_root`, `session_id`; anything omitted resolves like the CLI (environment variable, then `gauss-ai config`, then a safe default). Returns `real_gauss_allowed` (whether the server operator enabled real GAUSS; see below), plus an `execution_hint` when `runner` is `gauss` and it is not enabled. |
| `gauss_session_close` | Ends a session. |
| `gauss_search_docs` | Returns official-documentation excerpts (and verified error-catalog entries for codes like `G0025`) for a question or function names. A source is a page that documents a named symbol, a curated doc-verified phrase ("percentile" → `quantile`), an error code or a recent topic. It is never a keyword overlap, a page that only resembles the word (`data` → `datalist.rst`), a navigation `index.rst`, or a GAUSS statement page for an ordinary sentence word ("run a test" → `run.rst`); a statement grounds when the query is that word, puts it in backticks or quotes, or is a bare list of symbols. Pages examined but not grounded on are listed as labeled `candidates` (page, symbols, Purpose sentence, `origin`: `ambiguous_resolution`, `keyword_match`, `derived_from_docs`, `statement_page`, `non_defining_page` or `navigation_page`); a candidate is not a grounded answer, so search its name to read the page. At most 4 sources are returned: a documented name cut by that bound is listed in `omitted_topics` with an `omitted_note`, and the result is `partially_grounded`; search it separately. Local and read-only. |
| `gauss_validate_code` | Deterministic verdict on raw GAUSS code: documented call signatures, documented preconditions (e.g. `invpd` needs a symmetric positive-definite matrix), syntax, unknown (possibly hallucinated) functions, and system-touching statements. A call counts as documented only on a page that defines it, so an invented `solve(a, b)` is an unknown function even though `sqpsolvemt.rst` resembles it. Code that reaches `handoff_candidate` gets a single-use `validation_id`. Otherwise the reasons name the cause, and `coverage_gaps` lists each missing piece of evidence (symbol, argument, parameter, cause). |
| `gauss_execution_prepare` | Step 1 of execution. Takes a `validation_id` (hybrid) or nothing (strict: the last chat answer). Never accepts code directly. The stored code is re-validated first, and refused with `validation_stale` if the docs changed underneath it. Returns the exact code, a digest and a `request_id`. Preparing again while a request is pending replaces it and says so (`replaced_request_id`). A `validation_id` is spent only by a prepare that returns a prompt; a refusal (`real_gauss_not_allowed`, `validation_stale`, `request_rejected`) leaves it usable. |
| `gauss_execution_decide` | Step 2. Takes the human's own raw `yes`/`no` and the `request_id` of the prompt they answered. A missing `request_id` (`request_id_required`), a replaced prompt (`request_superseded`) or any other id (`request_not_pending`) approves nothing. Anything but yes/no is `unrecognized`, approves nothing and keeps the request pending. On approval, runs the existing GAUSS execution adapter exactly once. Every outcome echoes `request_id` and `request_digest`. If several prompts are open, the user names the prompt in a separate message and replies with a bare yes or no; never ask the user to label a reply (the parser rejects "A: yes"). |
| `gauss_repair_start` / `gauss_repair_command` / `gauss_repair_close` | Drive the guided repair pipeline one REPL command per call (`workspace create`, `request`, `plan`, `confirm <hash>`, `execute`, `diagnose`, `repair-plan`, `approve-repair <digest>`, ...), identical to `gauss-ai repl`. |
| `gauss_chat_ask` / `gauss_chat_reset` | Strict mode only (see above). |

## What can never be executed

Only `handoff_candidate` code can be offered for execution:

- grounded in the official documentation;
- no unknown functions;
- compatible documented signatures;
- no violated documented precondition;
- validated syntax;
- broad evidence.

In addition, **any system-touching statement always makes code `not_ready`**:

- OS commands: `dos`, `shell`
- programs or process control: `exec`, `execbg`, `system`
- other source files: `run`, `#include`
- directory changes: `chdir`, `changedir`
- any file read, write or delete: `load`/`loadd`, `save`/`saved`, `fopen`, `csvReadM`, `xlsWriteM`, `deleteFile`, `output file=`, ...

The handoff is for self-contained snippets that compute in memory. Work with real files belongs in the guided repair pipeline.

## Real GAUSS needs an extra opt-in

A `runner="gauss"` request is refused unless the server process itself was started with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. That gate is controlled only by whoever launches the server, and it comes on top of the per-request approval. It never bypasses the execution adapter's own checks: a nonexistent executable still never launches. `gauss_session_start` reports the opt-in as `real_gauss_allowed`; that says only that the operator enabled it, not that the executable runs.

## Session model

Sessions are in-memory and process-local. Nothing is persisted, and nothing survives a server restart. At most 8 `validation_id`s are outstanding per session; the oldest is evicted first, and each is single-use. There is no idle eviction: close sessions when done, or restart the server. An abrupt disconnect still cleans up repair workspaces.

## Updating on Windows

A running `gauss-ai-mcp.exe` (for example, one started by a Claude Code window) locks its executable. Stop it, or close the client, before `pip install -e ".[mcp]"`. Otherwise the reinstall fails partway and leaves `gauss-ai` uninstalled until you run it again.
