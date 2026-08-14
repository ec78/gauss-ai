# v0.70.0 - Conversational GAUSS Q&A Foundation

This milestone begins the transition from a guided GAUSS repair CLI toward a conversational GAUSS coding agent by implementing the first genuine conversational capability: general GAUSS Q&A with multi-turn follow-up context. It is not execution routing, not code generation, and not a redesign of any existing safety layer — the pipeline Execution → Interpretation → Diagnosis → Strategy → Draft → Application → Verification → Review is untouched, zero diff.

## CLI UX

`gauss-ai` (no subcommand) now launches conversational chat — the new preferred entry point. The prior bare-invocation behavior (the full command-by-command workflow REPL) is fully preserved, unchanged, behind a new explicit `gauss-ai repl` subcommand, so nothing that worked before is removed, only relocated to an explicit, discoverable name. `gauss-ai doctor`/`init`/`config`/`repair` are completely unaffected.

## Model-Provider Architecture

New module `scripts/gauss_chat_provider.py` defines a small, provider-agnostic `ModelProvider` interface (`ChatMessage` in, `ProviderResult` out) so the conversational system never depends on any single model vendor, and no provider-specific SDK object leaks past this one module. `FakeModelProvider` is fully deterministic and network-free — the safe default (mirroring `default_runner`'s own `"fake"`-first precedent) — so the entire system is testable without network access or API charges. `AnthropicMessagesProvider` is the one real provider added, built on Python's standard-library `urllib` only: no new third-party runtime dependency in a repository that has had zero through 69 prior milestones.

**Honest disclosure**: no live network round trip against the real Anthropic API was performed during this milestone's own development, because no `ANTHROPIC_API_KEY` is available in this environment. The adapter's own request construction, auth-header handling, response parsing, and every covered failure mode (missing credential, network failure, HTTP error, malformed response) are fully unit-tested via an injected fake transport callable — real, executed tests of real code, just not a genuine network call. Stated here explicitly rather than fabricated.

## Grounding

New module `scripts/gauss_conversation_engine.py` grounds questions by reusing, never duplicating, two existing knowledge sources. A `G####`-shaped question is looked up directly via `gauss_error_catalog.lookup_error(...)`. Otherwise, when a local documentation root is configured (`docs-root`), candidate word-tokens are looked up via `command_doc_lookup.lookup(...)` — the exact same local-docs retrieval tool `v0.6.0`-`v0.11.0` already built. Every answer explicitly discloses which source, if any, grounded it; an ungrounded answer is never presented as documentation-verified. Real local GAUSS documentation retrieval was genuinely exercised during this milestone's own evaluation.

## Conversation State

`ConversationState` is process-local only, capped at 20 turns (oldest dropped first), cleared by `reset`/`new` or process exit — no database, no file, no cross-process sharing. A `last_topic` field lets a simple pronoun-style follow-up ("show me an example") resolve against the previous turn's topic without requiring real model comprehension.

## Execution and Code-Generation Boundary

`gauss_conversation_engine.py` and `gauss_chat_provider.py` import nothing from `gauss_execution_workflow`, any `gauss_repair_*` module, or any `gauss_verification_*` module — verified by a dedicated test, not merely by convention. A bounded keyword heuristic detects an execution-imperative question ("run this", "execute that") and returns a fixed, honest redirect to `gauss-ai repair <file.gss>` without ever calling the model for that turn (proven by an intentionally-exploding test provider). Any answer text that looks code-shaped always receives a fixed, non-model-dependent "not executed in this conversation" footer.

## Configuration

New settings `chat-provider` (`fake`/`anthropic`, default `fake`), `chat-model`, `docs-root` — all following the identical CLI-arg > env-var > config-file > default precedence every existing setting already uses. No credential field was added anywhere; `ANTHROPIC_API_KEY` is read fresh from the environment at call time only, inside `complete(...)`, never stored on the provider instance and never written to `gauss-ai`'s own config file.

## Tests Added

74 new tests: `scripts/test_gauss_chat_provider.py` (23, including a structural proof the API key is never stored as an instance attribute and a proof no test ever touches the real network), `scripts/test_gauss_conversation_engine.py` (22, including real grounding against a disposable synthetic doc fixture and multi-turn follow-up proofs), `scripts/test_gauss_ai_chat.py` (19), plus 5 new dispatch tests in `test_gauss_ai_cli.py` and 5 new precedence tests in `test_gauss_ai_config.py`. Three pre-existing `test_gauss_ai_cli.py` tests were relocated (not deleted) from bare-invocation to the new `repl` subcommand, with the reason documented inline, since their previous expectation is genuinely obsolete now that bare invocation reaches chat instead.

## Full Regression Results

All 40 test files pass, zero regressions. Zero diff on every core pipeline/safety module: `gauss_execution_workflow.py`, every `gauss_repair_*`/`gauss_verification_*` module, `gauss_workspace.py`, `gauss_code_assistant_cli.py`, `gauss_code_assistant_workflow.py` — confirmed via `git diff --stat`.

## Packaging Verification

Verified through a fresh, disposable `pip install -e .` venv and the installed `gauss-ai` entry point: bare `gauss-ai chat` (and bare invocation) launches conversational mode with real documentation grounding against a real local GAUSS docs checkout; `gauss-ai repl` launches the unchanged workflow REPL; `gauss-ai doctor`/`repair` continue to work exactly as before; a real-provider selection with no API key configured honestly reports the missing credential rather than crashing or silently falling back.

## 60.x Benchmark Results

A new `60.x` Conversational GAUSS Q&A Foundation category (ten prompts) was fully evaluated using the deterministic `FakeModelProvider` — no `ANTHROPIC_API_KEY` is available in this development environment, so this evaluates grounding correctness, multi-turn context, and boundary enforcement, never real-LLM answer quality. Real local GAUSS documentation retrieval was genuinely exercised throughout. **10/10 Passed at 4.0.** One minor, disclosed limitation was found: a compound question containing both an invented word and a real GAUSS keyword can ground on the real keyword rather than staying ungrounded, since the bounded per-token detection heuristic has no real language understanding of user intent — documented, not fixed, since a genuine fix needs real intent parsing, out of scope.

## Evaluation Tracking

`check_evaluation_tracking.py --json` reports 564 prompt IDs, 564 coverage rows, 531 run files referenced, 536 index entries, 0 errors, and the same 3 pre-existing historical warnings carried from prior milestones — `overall_pass: true`.

## Release Readiness

`check_release_readiness.py` — PASS (`validate_all_evidence.py` PASS, `check_evaluation_tracking.py` PASS).

## Supported Alpha Environment

**Windows**, verified against **GAUSS 26.1.1** for real execution (unaffected by this milestone). Python 3.10+. Conversational Q&A itself makes no GAUSS calls and has no OS-specific dependency; the real `AnthropicMessagesProvider` has not been network-tested in this repository as of this milestone.

## Alpha Readiness Classification

**Private Alpha.** The first alpha-feedback cycle (five findings, `v0.69.0`) is complete and shipped — stated as addressed-in-implementation-and-verified-through-`v0.69.0`'s-own-evaluation, not as "all UX is now permanently solved." This milestone adds a genuinely new, additive capability without touching any existing safety-critical module; a second round of alpha testing, including of this new conversational assistant, is expected to surface further feedback, exactly as the first round did.

## Not Implemented

Conversational execution routing, conversational code generation/repair/application, automatic code-file creation, automatic draft creation from arbitrary conversation, autonomous code modification, a second real LLM provider, durable conversation history, multi-user sessions, and loading the full `experts/gauss-language/` corpus into the system prompt.

## Recommendation for the Next Milestone

The likely next step is conversational GAUSS code generation, but that recommendation should be weighed against real alpha feedback on this milestone's own conversational UX and grounding quality first — this milestone deliberately does not request or imply that authorization.
