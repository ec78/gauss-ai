# Grounding-Gated Generation

**Status: Alpha — added in `v0.73.0`, extending [conversational-code-generation.md](conversational-code-generation.md).**

`v0.72.0` disclosed whether a code-generation answer was grounded, but that disclosure was informational only — the model could still be asked to generate code for an entirely ungrounded request, and it sometimes fabricated a plausible-but-nonexistent GAUSS function when it did. `v0.73.0` turns grounding into an actual **generation gate**: a deterministic, provider-independent decision, computed before the model is ever consulted, that controls whether — and how much — GAUSS-specific code generation is permitted.

## Function/concept resolution

Before `v0.73.0`, grounding only matched the literal words in your question against documentation. Asking "calculate the column means" never even attempted to look up `meanc`, because the word "means" alone doesn't score as a confident documentation match. `resolve_concepts(...)` fixes this with a small, explicit, human-curated index mapping natural-language phrases to real GAUSS symbols:

| Phrase examples | Resolves to |
|---|---|
| "column means", "average each column", "compute column averages" | `meanc` |
| "column standard deviation", "standard deviation of each column" | `stdc` |
| "flatten a matrix", "turn a matrix into a vector", "vectorize a matrix" | `vec` |
| "invert a matrix", "matrix inverse" | `inv` |
| "panel regression", "panel data regression", "pooled time series cross section regression" | `tscsfit` |

Every entry was verified against real local GAUSS documentation before being added — the mapping is never guessed from memory, and it is never trusted by itself: every resolution is re-verified, at the moment you ask, against **your own configured `docs-root`**. If your documentation checkout doesn't actually contain the symbol, the alias produces no resolution at all, rather than a fabricated one.

This is a small, curated table — not a synonym dictionary, not a language model, not a vector database. It will not resolve every possible phrasing, and it does not try to.

## The generation gate

Every code-generation request now gets one of four policies, computed entirely from real retrieval evidence:

- **`FULL`** — every referenced GAUSS-specific topic was found. Generate normally.
- **`SUPPORTED_ONLY`** — some topics were found, some weren't. Only the supported portion is generated; the unsupported part is disclosed, never fabricated.
- **`CLARIFY`** — a phrase or token matched more than one similarly-scored documented candidate. `gauss-ai` asks which one you meant, naming the real candidates, instead of guessing.
- **`BLOCK`** — no authoritative documentation exists for the request at all. `gauss-ai` says so honestly and **never calls the model** for that turn.

The model is never given a chance to override this. For `BLOCK` and `CLARIFY`, the underlying provider (Ollama, Anthropic, or the fake/test provider) is not invoked at all — this has been confirmed live against a real, reachable Ollama service, observable directly from response latency (an instant reply, versus the real inference time every genuinely-answered request takes).

```
> Write GAUSS code for fooQuantumEstimator.
I don't have enough authoritative GAUSS documentation in the configured source to generate reliable
GAUSS code for this request. If you know the GAUSS procedure or function you want to use, tell me its
name and I can look it up.
```

## Post-generation symbol checking

Even with a `FULL` or `SUPPORTED_ONLY` gate, a model can still ignore its own instructions and introduce an unsupported function call. `check_generated_symbols(...)` is a conservative, best-effort pass over the generated code: it extracts call-shaped identifiers and flags any that are neither a grounded/resolved topic, a small set of verified GAUSS language constructs and common builtins, nor plausibly a name the user (or the model, on the user's behalf) defined locally in the same code. This is **not a compiler** and does not claim perfect static analysis — its purpose is narrow: catch an obvious hallucinated function call even when the model ignores its own prompt.

```
> Use reshape and colmean on my data.
[Partially grounded: reshape documented; `colmean` not found in the configured GAUSS documentation or verified error catalog]
[Warning: the generated code also calls `colmean`, which is not a documented function this session could
verify -- treat it as unverified, not authoritative GAUSS syntax.]
...
```

This check runs whenever the answer is code-shaped, regardless of how the question was classified — a real gap found during this milestone's own live evaluation was a question phrased without an explicit "write code" trigger, classified as plain Q&A, that still produced code containing a hallucinated symbol. The check now applies either way.

## What this does and doesn't fix

Grounding-gated generation makes it **structurally harder** for unsupported GAUSS syntax to reach you as if it were authoritative — both by refusing to ask the model at all when there's no evidence, and by flagging what slips through anyway. It does **not** make the underlying model reliable. This repository's own live evaluation of `qwen2.5-coder:7b` found:

- When grounding evidence for the right function was actually retrieved, the model used the real function correctly and consistently.
- When it wasn't, the model sometimes still fabricated a plausible name with no disclosed uncertainty (a real, disclosed limitation — not eliminated by this milestone).
- The post-generation checker caught this reliably in testing, including a subtle case (a made-up `tscsmtControl()` constructor where the real one is `tscsmtControlCreate()`) that would be easy to miss by eye.

**Treat all generated code as unverified until you check it yourself.** See [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md) for the complete, current list, and `planning/v0.73.0-grounding-gated-generation.md` for the full validation record.

## Ambiguity and clarification

If your request could plausibly refer to more than one documented function, `gauss-ai` asks rather than guesses:

```
> Write GAUSS code using alphafunc.
I want to make sure I use the right documented GAUSS function before generating code: "alphafunc" could
match more than one documented topic (alphafuncx, alphafuncy). Which one did you mean? If you already
know the exact function or procedure name, just tell me directly and I'll look it up.
```

This is fully deterministic — no model call is made to phrase or answer this question. Just name the function you meant, or provide more detail, and try again.

## Methodological questions remain separate from code generation

Asking "should I use OLS or a robust regression method?" is a methodological question, not a code-generation request — no code is generated merely because a related function name happens to be documented, and no documentation match is ever presented as validating a statistical or methodological choice. This distinction, established in `v0.70.0`'s own Econometrics-expert evaluations, is unchanged by this milestone.
