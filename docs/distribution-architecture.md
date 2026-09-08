# Distribution architecture: what GAUSS AI owns vs. what a model provider supplies

**Status: added in `v0.71.0`**, alongside first-class local Ollama support. This note exists so the boundary stays explicit as more providers are added.

## The boundary

GAUSS AI's own code — not any language model — owns every one of the following:

- Documentation grounding (local `.rst` lookup, see [gauss-documentation-setup.md](gauss-documentation-setup.md))
- Verified GAUSS error knowledge (the error catalog)
- The execution boundary (conversational chat never executes GAUSS code)
- Diagnostics (`gauss-ai doctor`)
- Repair planning, drafting, approval, application, and safety checks
- Verification of execution results
- Provenance/evidence tracking through the guided repair workflow
- Any future tool orchestration

A model provider — `fake`, `ollama`, or `anthropic` today — supplies exactly one thing: turning a grounded prompt into fluent natural-language text. `gauss_chat_provider.ModelProvider` is a narrow interface (`ChatMessage` in, `ProviderResult` out) specifically so that swapping which model answers a question changes nothing about any of the responsibilities above. No provider implementation is permitted to read or write arbitrary files, invoke GAUSS, invoke a shell command, or apply a repair — this is enforced by the interface itself, not by convention, and is covered by this repository's own structural tests.

## Currently supported providers

| Provider | Cost | Network | Credential | Notes |
|---|---|---|---|---|
| `fake` | Free | None | None | Deterministic, echoes retrieved evidence only. Always available; the safety net for testing and demos. |
| `ollama` | Free | Local only (`localhost` by default) | None | Requires you to install Ollama and pull a model yourself. See [ollama-models.md](ollama-models.md). |
| `anthropic` | Paid (your own API usage) | Real internet | `ANTHROPIC_API_KEY` (your own shell environment; never stored by `gauss-ai`) | Cloud-hosted, no local install. |

## Commitments

- **Ollama is optional.** `gauss-ai` does not require it to be installed, and no command fails simply because Ollama is absent, unless you have explicitly configured `chat-provider: ollama`.
- **No bundled model weights.** `gauss-ai`'s own package/repository never ships a model file of any kind. You obtain and manage models entirely through Ollama's own tooling (or Anthropic's own API, for that provider).
- **No permanent dependency on any one provider.** The `ModelProvider` interface exists so a future provider can be added without redesigning `ConversationEngine` or any downstream workflow.
- **Before any future bundled distribution** of a specific model (should that ever be considered), its license would need to be evaluated on its own terms — that has not happened, and is out of scope for this milestone.
