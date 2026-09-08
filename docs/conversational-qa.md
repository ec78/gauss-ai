# Conversational GAUSS Q&A

**Status: Alpha — first version, added in `v0.70.0`.**

`gauss-ai`, run with no subcommand, launches a conversational assistant you can ask GAUSS questions in plain language, with follow-up context retained across turns.

## How to launch chat

```
gauss-ai
```

is the default. The explicit, equivalent form is:

```
gauss-ai chat
```

Both accept the same optional flags: `--provider {fake|ollama|anthropic}`, `--model <name>`, `--docs-root <path>`, `--ollama-endpoint <url>` (only meaningful with `--provider ollama`).

## Supported capabilities

- Free-form questions about GAUSS syntax, built-in procedures/functions, and error messages.
- Multi-turn follow-up questions ("Show me a simple example.", "What's the difference between that and vec?") — a bounded amount of recent conversation is retained so simple references like "that"/"it" resolve to the most recently discussed topic.
- `help` — lists what the assistant can do.
- `reset` / `new` — clears the current conversation and starts fresh.
- `exit` / `quit` — leaves the assistant. Nothing about the conversation is saved anywhere when you do.

## Unsupported capabilities (by design, in this version)

- **No conversational execution.** Asking the assistant to "run this" or "execute that" gets an honest redirect to the real, existing guided command (`gauss-ai repair <file.gss>`) — it never silently executes anything to seem more capable.
- **No conversational code generation, repair, or file modification.** Incidental code examples in an answer are fine; turning a conversation directly into an executed script, a repair draft, or a written file is not implemented in this version.
- **No durable conversation history.** Nothing about a chat session is written to disk, a database, or shared across processes. Exiting (or `reset`) discards it completely.

## Provider configuration

Three providers exist behind a small, common interface (`gauss_chat_provider.ModelProvider`):

- **`fake`** (the default) — a fully deterministic, network-free provider. It never fabricates a synthesized answer; when real grounding evidence is available (see below) it echoes that evidence back, clearly labeled as a template, not a composed answer. It requires no credential and makes no network call, so the entire conversational system — including this alpha release itself — is usable and testable without an API key.
- **`ollama`** (added in `v0.71.0`) — talks to a locally running [Ollama](https://ollama.com) instance over HTTP (Python's standard library only). No API key, no cost, no data leaving your machine. You install Ollama and pull a model yourself; `gauss-ai` never installs or downloads either. Configure it with:
  ```
  gauss-ai config set chat-provider ollama
  gauss-ai config set chat-model qwen2.5-coder:7b   # optional; this is also the built-in default
  gauss-ai config set ollama-endpoint http://localhost:11434   # optional; this is also the built-in default
  ```
  See [ollama-models.md](ollama-models.md) for model recommendations, and run `gauss-ai doctor` to check whether Ollama is actually reachable and the configured model is actually pulled.

  **Validation status**: this provider has been validated against a real, locally running Ollama installation and a real model, in addition to its fully-tested fake-transport unit test suite — see the `v0.71.0` release notes for the specific scenarios exercised.
- **`anthropic`** — calls the real Anthropic Messages API over HTTPS (Python's standard library only; no extra package is installed for this). Configure it with:
  ```
  gauss-ai config set chat-provider anthropic
  gauss-ai config set chat-model claude-sonnet-5   # optional; a default is used if omitted
  ```
  and set the `ANTHROPIC_API_KEY` environment variable in your own shell/session before running `gauss-ai`. **`gauss-ai` never reads, stores, or writes this key anywhere in its own configuration file** — see "Privacy and credentials" below.

  **Alpha disclosure**: this provider's own request/response/error-handling logic is fully tested, but a live network round trip against the real Anthropic API has not been performed as part of this repository's own development or evaluation, because no API key is available in that environment. If you configure a real key and see something behave unexpectedly, please report it (see [reporting-bugs.md](reporting-bugs.md)).

Precedence for every chat setting is the same as every other `gauss-ai` setting: explicit CLI flag (`--provider`/`--model`/`--docs-root`/`--ollama-endpoint`) > environment variable (`GAUSS_AI_CHAT_PROVIDER`/`GAUSS_AI_CHAT_MODEL`/`GAUSS_AI_DOCS_ROOT`/`GAUSS_AI_OLLAMA_ENDPOINT`) > `gauss-ai config set chat-provider|chat-model|docs-root|ollama-endpoint <value>` > safe default.

See [distribution-architecture.md](distribution-architecture.md) for the ownership boundary between `gauss-ai` itself and whichever provider answers a question.

## Privacy and credential expectations

- No API key, token, or credential is ever a field in `gauss-ai`'s own config file (`~/.gauss-ai/config.json`).
- `ANTHROPIC_API_KEY` is read directly from your process environment at the moment a real answer is requested — never earlier, never cached, never logged, never included in any printed output.
- Nothing you type in a chat session is written to disk. There is no chat log file and no database.

## Grounding behavior

Before calling any provider, `gauss-ai` checks two existing, already-verified knowledge sources:

1. If your question names a `G####`-shaped GAUSS error code, the answer is looked up directly in this repository's own [verified error catalog](gauss-error-catalog.md) — no GAUSS launch required.
2. Otherwise, if you have configured `docs-root` to point at your own local checkout of official GAUSS documentation, the assistant looks for a real, matching command/procedure page.

Every answer explicitly discloses which of these applies:

- `[Grounded in this repository's verified error catalog: G0036]`
- `[Grounded in local official GAUSS documentation: reshape]`
- `[Not grounded in official documentation or the verified error catalog -- from the model's own general knowledge]`

This repository does not bundle a copy of official GAUSS documentation. If you don't configure `docs-root`, conversational answers about specific commands/procedures will not be documentation-grounded — set it to get real, cited retrieval instead of general-knowledge answers:

```
gauss-ai config set docs-root "C:\path\to\your\gauss-docs\checkout"
```

## Typing a `gauss-ai` command inside chat

If you type something that looks like a `gauss-ai` command (for example, `gauss-ai doctor` or `gauss-ai config show`) at the chat prompt, `gauss-ai` recognizes this deterministically and tells you to exit the chat and run it in your terminal instead — it is never sent to the model provider as a question, and it is never executed from inside the chat loop.

## Execution boundary

This chat never executes GAUSS code, never applies a repair, and never writes a file. If you show intent to run or execute something, you'll get an honest message pointing you to `gauss-ai repair <file.gss>` — the existing, fully supported, human-approved repair workflow. Any GAUSS code shown as part of an answer is always followed by a note that it has not been executed in the conversation, regardless of how the answer was produced.

## How to leave or reset a conversation

- `reset` or `new` clears the current conversation's history and starts over, in the same terminal session.
- `exit` or `quit` leaves the assistant entirely.
- Simply closing the terminal (or Ctrl+D / EOF) also leaves cleanly — nothing is left behind to clean up.

## What this is not

Not autonomous code generation, not a chatbot with memory across sessions, not a second execution path, and not a claim that any answer you receive has been tested unless you are told explicitly that it was. See [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md) for the complete, current limitations list.
