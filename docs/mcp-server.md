# MCP Server (v0.79.0)

`gauss-ai` can run as a local MCP (Model Context Protocol) server, so other MCP clients on the same machine — Claude Code, Claude Desktop — can call the conversational assistant and the guided repair pipeline as tools, instead of (or alongside) the interactive CLI. This is a transport layer only: every tool here is a thin wrapper around the same deterministic code the CLI already uses. Nothing described in this document changes any safety decision, approval flow, or execution boundary — see `docs/distribution-architecture.md` and `docs/controlled-execution-handoff.md` for those.

## Install

The base `gauss-ai` CLI has zero third-party runtime dependencies. The MCP server needs one additional package, installed via an optional extra:

```
pip install -e ".[mcp]"
```

Everything else (`gauss-ai version`, `gauss-ai chat`, `gauss-ai repair`, ...) works identically whether or not this extra is installed.

## Running it

Two equivalent entry points:

```
gauss-ai mcp          # subcommand on the main CLI
gauss-ai-mcp          # standalone console script (what the plugin's .mcp.json points at)
```

Both run the same server over stdio — the standard transport for a locally-spawned MCP server. There is no network/HTTP/port surface to configure or secure.

Add it to a client with, for example:

```
claude mcp add --transport stdio gauss-ai gauss-ai-mcp
```

## Tools

### Chat (conversational Q&A and code generation)

| Tool | Purpose |
| --- | --- |
| `gauss_chat_start` | Start a session. Optional `provider`/`model`/`docs_root`/`ollama_endpoint`/`runner`/`gauss_executable`/`workspace_parent`/`timeout_seconds`/`session_id`; anything omitted resolves the same way `gauss-ai chat` resolves it (environment variable, then `gauss-ai config`, then a safe default). Returns `session_id`. |
| `gauss_chat_ask` | Ask one question. Returns grounding status, any generated code, deterministic pre-execution validation evidence, and `execution_offer_eligible`. |
| `gauss_chat_reset` | Clear a session's history and any pending execution offer. |
| `gauss_chat_close` | End a session. |

Generated code is never executed, verified, or written to a file by these tools. See `docs/conversational-code-generation.md` and `docs/conversational-qa.md` for the underlying grounding/generation rules, unchanged here.

### Execution handoff (the real bridge)

| Tool | Purpose |
| --- | --- |
| `gauss_execution_prepare` | Usable only right after a `gauss_chat_ask` reply with `execution_offer_eligible: true`. Builds the exact request from that session's own last answer — never from a caller-supplied code string — and returns the code/runner/executable/timeout/digest for a human to review. Nothing is executed yet. |
| `gauss_execution_decide` | Takes the human's raw yes/no text. An unrecognized reply creates no approval. An approved reply immediately records the approval and invokes the existing GAUSS execution adapter exactly once — real execution, not advisory-only. |

This is the same two-step, digest-bound, single-use-approval flow `docs/controlled-execution-handoff.md` describes for the CLI chat, split across two tool calls instead of one terminal prompt.

**Real GAUSS execution requires an additional, server-operator-only gate.** Setting `runner="gauss"` on a session is not enough by itself: the `gauss-ai-mcp` process must also have been started with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1` in its own environment. Without it, `gauss_execution_prepare`/`gauss_repair_start` refuse with `real_gauss_not_allowed`. This is deliberate: an MCP client is one step further removed from the human at the keyboard than someone typing `--runner gauss` into a terminal, so this milestone adds one more opt-in, controlled only by whoever launches the server process — on top of, never instead of, the per-request approval above.

### Guided repair

| Tool | Purpose |
| --- | --- |
| `gauss_repair_start` | Start a repair session for one file's workflow (not bound to a specific file path yet — that happens via the `request` REPL command, same as `gauss-ai repl`). |
| `gauss_repair_command` | Send one REPL command line (`workspace create`, `request`, `plan`, `confirm <hash>`, `execute`, `diagnose`, `repair-plan`, `approve-repair <digest>` / `decline-repair <digest>`, `suggest-repair-draft`, `repair-draft`, `approve-repair-draft` / `decline-repair-draft`, `approve-repair-application` / `decline-repair-application`, `check-repair-application-gate`, `apply-repair`, `verify-repair`, `review-verification`, `show-repair-session`, `status`, `read`, `reset`, `exit`, ...). Every command behaves identically to `gauss-ai repl`; errors come back as plain output lines, never a crash. |
| `gauss_repair_close` | End a session without sending `exit`. |

Driving the pipeline this way — one command per tool call — lets a human approve or decline at every gate exactly as they would in a terminal, just relayed through whichever MCP client they're using.

## Session model

Chat and repair sessions are independent, in-memory, and process-local — nothing is persisted, and nothing survives a server restart. A client can hold several of each kind at once. There is no idle-session eviction in this version; call `gauss_chat_close`/`gauss_repair_close` when done, or restart the server. An abrupt disconnect still cleans up repair sessions' temporary workspaces via an `atexit` hook.

## Claude Code plugin

This repository also ships `.claude-plugin/plugin.json` + `.mcp.json` so it can be installed as a Claude Code plugin (`/plugin marketplace add` against this repo, then `/plugin install gauss-ai-mcp`). The plugin assumes `pip install -e ".[mcp]"` has already been run and `gauss-ai-mcp` is on `PATH` — installing the plugin does not run `pip` for you.
