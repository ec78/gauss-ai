# Known Alpha Limitations

**Status: Alpha — intended for controlled testing.** This is a tester-facing summary of what to expect right now. See [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md) at the repository root for the full, per-milestone historical record.

## Scope

- **Single-file repair only.** One `.gss` file per guided session. No multi-file repair exists or is planned for this phase.
- **No autonomous repair.** Every strategy approval, draft approval, application approval, and verification review requires your own explicit, real-time decision. Nothing is inferred on your behalf.
- **No rerun or rollback beyond one backup.** `apply-repair` always creates exactly one, never-overwritten backup before writing. There is no automated restore-from-backup, no automatic retry, and no rollback mechanism of any kind.
- **No durable sessions.** Each `gauss-ai` process is stateless once it exits. There is no way to resume a guided session across a process restart, and `--export-session` does not create one — it writes a one-time, read-only snapshot, not a resumable session. This includes conversational chat: nothing about a chat session is saved anywhere, and there is no way to resume one after exiting.

## Conversational Q&A and Code Generation (new in `v0.70.0`; local Ollama added in `v0.71.0`; code generation and multi-source grounding added in `v0.72.0`)

- **No conversational execution.** Asking the assistant to "run this" or "execute that" gets a fixed, honest redirect to `gauss-ai repair <file.gss>` — it never executes anything from a chat session, even immediately after generating code for you. Confirmed live against a real local Ollama model as well as the fake provider (see `evaluations/runs/2026-09-08-code-assistant-local-ollama-provider-run-006.md` and `evaluations/runs/2026-09-09-code-assistant-conversational-code-generation-run-008.md`).
- **No conversational repair or file modification.** `gauss-ai` chat can generate GAUSS code on request (see [docs/conversational-code-generation.md](conversational-code-generation.md)), but generated code is always advisory: turning a conversation directly into a written file or an applied repair is not implemented.
- **Generated code can be wrong, including confidently and without any disclosed uncertainty.** This repository's own live evaluation of `qwen2.5-coder:7b` found it invented a nonexistent `colmean` function in place of the real `meanc`, and separately fabricated an entire nonexistent panel-regression syntax pattern with no caveat at all -- both confirmed via real GAUSS execution. **Treat all generated code as unverified until you check it yourself.** See `evaluations/runs/2026-09-09-code-assistant-conversational-code-generation-run-002.md` and `-run-007.md`.
- **Multi-source grounding (`v0.72.0`) now grounds a question naming two or more real, documented commands together** (e.g. "what's the difference between reshape and vec") -- fixing the single-topic limitation `v0.71.0` disclosed. It does not, however, map natural-language phrasing to a function name: "column means" will not resolve to `meanc` unless you name the function.
- **Grounding requires you to configure `docs-root`.** This repository bundles no GAUSS documentation; without a configured local checkout, command/procedure questions are answered from the model's own knowledge (or, with the default fake provider, not answered at all), honestly disclosed as not documentation-grounded either way. See [docs/gauss-documentation-setup.md](gauss-documentation-setup.md).
- **A purely conceptual question with no real command name (e.g. "what's the difference between a matrix and a scalar") stays honestly ungrounded, even with a real model** -- the disclosure is honest either way, but this question shape has no command name for the retrieval layer to find (see `evaluations/runs/2026-09-08-code-assistant-local-ollama-provider-run-004.md`).
- **The default provider (`fake`) never synthesizes an answer.** It echoes back retrieved documentation/catalog text, clearly labeled as a template, or honestly says nothing was found.
- **A real, locally running Ollama model is now the recommended zero-cost way to get genuine synthesized answers** — no API key required. Run `gauss-ai config set chat-provider ollama` after installing [Ollama](https://ollama.com) and pulling a model (see [docs/ollama-models.md](ollama-models.md)); `gauss-ai doctor` will tell you whether it's reachable and the model is available. This has been validated live against a real local model as of `v0.71.0` — see `evaluations/runs/2026-09-08-code-assistant-local-ollama-provider-run-*.md`.
- **The cloud (`anthropic`) provider has still not been network-tested by this repository as of `v0.71.0`.** No API key is available in this repository's own development environment; the provider's request/response/error-handling logic is fully unit-tested, but a live round trip against the real API has not been independently confirmed. If you use it and see unexpected behavior, please report it.
- **Topic detection is a bounded heuristic, not real language understanding.** A question mixing an invented word with a real GAUSS keyword can occasionally ground on the real keyword instead of correctly staying ungrounded — a known, minor limitation, not a fabrication (see `evaluations/runs/2026-08-12-code-assistant-conversational-gauss-qa-foundation-run-005.md` for a documented example).

## Environment

- **Real GAUSS execution verified on Windows with GAUSS 26.1.1 only.** Other GAUSS 24/25/26 installations are supported by the discovery/execution logic but have not been independently verified by this repository's own testing. macOS/Linux real-GAUSS execution is not claimed or supported.
- **Fake-mode testing (packaging, CLI, guided workflow, doctor, init, config) has no OS-specific dependency**, but has only been exercised on Windows so far.
- **Python 3.10+ required.**

## Product behavior

- **`gauss-ai version`/`gauss-ai doctor` never launch GAUSS to report its version** — the version is parsed from the configured executable's own path string, and is reported as unknown when the path carries no parseable version number (e.g. a custom install directory name).
- **`gauss-ai init` never silently picks among multiple discovered GAUSS executables** — you must explicitly select one, type a path manually, or skip.
- **The Application Gate has no automated backup-restore, rollback-path-verification, application-consumer-authorization, or audit-record check** — these are explicitly disclosed as `not_applicable_checks` in gate output, not silently assumed satisfied.
- **A verification review cannot be revoked or corrected** once recorded — a mis-recorded decision requires a fresh `gauss-ai repair` session (a full `reset` in the lower-level REPL), not an edit-in-place.
- **No telemetry, analytics, or network reporting of any kind.** Nothing about your session is ever sent anywhere automatically.

## Known example-content history

`examples/alpha-demo/broken.gss` was corrected in `v0.68.0` after real-GAUSS validation found it reproduced a different, uncataloged error than the `G0105` it originally claimed (it had only ever been exercised in fake mode before). This is now fixed and re-verified against real GAUSS — noted here as a reminder that even this repository's own example content is only as trustworthy as its most recent real verification, exactly like any GAUSS script you bring yourself.

## If you hit something not listed here

It may be a genuine defect — see [docs/reporting-bugs.md](reporting-bugs.md).
