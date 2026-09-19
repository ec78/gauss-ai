# Conversational GAUSS Code Generation

**Status: Alpha — added in `v0.72.0`, extending [conversational-qa.md](conversational-qa.md); grounding now actively controls generation (not just discloses it) as of `v0.73.0` — see [grounding-gated-generation.md](grounding-gated-generation.md); `v0.74.0` adds documented call-signature/precondition checking and an execution-eligibility verdict — see [pre-execution-validation.md](pre-execution-validation.md); `v0.75.0` makes that validation pass apply to ANY code-shaped answer, regardless of whether the question was classified as a code-generation request — see [universal-code-validation.md](universal-code-validation.md).**

In addition to answering questions, `gauss-ai` chat can now generate GAUSS code from a plain-language request. This is advisory by default: generated code is never written to a file and never treated as an approved repair. As of `v0.78.0`, code that reaches `HANDOFF_CANDIDATE` readiness (the strongest deterministic evidence level) can be executed through one narrow, explicit, single-use approval — see [docs/controlled-execution-handoff.md](controlled-execution-handoff.md) for the full consent contract; anything short of that readiness level is never executed, only ever discussed. It uses the exact same provider/grounding architecture as conversational Q&A — this is an extension, not a second system.

## What it can do

Ask for code the way you'd ask a colleague:

```
> Show me how to reshape a matrix to 4 columns.
> Write GAUSS code to estimate an OLS regression.
> Can you give me an example using reshape and meanc?
> How would I loop over columns in GAUSS?
```

Each answer shows, in order: a grounding-status disclosure, the generated code, an explanation, and a fixed reminder that the code has not been executed.

## Grounding status

Before generating code, `gauss-ai` looks up every real GAUSS command/procedure name and error code it can identify in your request (bounded to a handful of candidates per question, `v0.72.0`'s multi-source grounding — see below), and computes one of three statuses:

- **`GROUNDED`** — every identified topic was found in your configured official documentation or the verified error catalog. Shown as `[Grounded in local official GAUSS documentation: reshape, meanc]`.
- **`PARTIALLY_GROUNDED`** — some topics were found, others were not. Shown as `[Partially grounded: reshape documented; `foo` not found in the configured GAUSS documentation or verified error catalog]`. The unsupported name is never silently presented as if it were documented.
- **`UNGROUNDED`** — nothing was found (often because `docs-root` isn't configured, or the request doesn't name a specific command). Shown with the same honest "from the model's own general knowledge" disclosure conversational Q&A already used.

This status is always computed from real retrieval evidence — never self-reported by the model, and never a numeric confidence score dressed up as certainty.

## Multi-source grounding (new in `v0.72.0`)

`v0.70.0`/`v0.71.0`'s grounding effectively resolved one topic per question. A request like "compare `reshape` and `vec`" would only ever surface the *last* of the two. `v0.72.0` looks up every distinct candidate token (bounded, currently up to 4 sources per question) so a genuinely multi-command request — "show me `reshape` and `meanc`" — can ground on both.

This is still a bounded, deterministic heuristic, not a language model or a vector database: it works well when your request names the actual GAUSS function (`meanc`), and it will not resolve a request phrased only in natural language ("column means") to the function that implements it — that gap is disclosed, not hidden (see Known Limitations below).

## Generated vs. executed — always distinct

Every code-shaped answer ends with:

```
(This example has not been executed in this conversation.)
```

This is appended by `gauss-ai`'s own code, unconditionally, regardless of what the model's own prose says. If you ask "what will this print?", the assistant is instructed to answer with an explicit prediction, not a claim of observed behavior — for example, "Expected output, not execution evidence: ...". This has been observed working correctly with a real local model in this repository's own live evaluation (see `evaluations/runs/2026-09-09-code-assistant-conversational-code-generation-run-001.md`), but it is a prompt-level instruction to the model, not a guarantee this repository's own code enforces line-by-line — a model can still phrase this imperfectly.

## Unsupported syntax

The system prompt instructs the model never to invent a GAUSS function name, and to say so plainly if it isn't confident one exists. **This alone has been observed to work inconsistently** in this repository's own live evaluation against a real local model — which is exactly why `v0.73.0` no longer relies on the model's own good behavior alone. As of `v0.73.0`, a deterministic generation gate decides whether generation is permitted at all before the model is consulted, and a post-generation check flags any unsupported function call that slips through anyway — see [grounding-gated-generation.md](grounding-gated-generation.md) for the full mechanism. As of `v0.74.0`, an unsupported symbol also gets a real documented-companion hint when one exists (e.g. a hallucinated `tscsmtControl` is paired with the real `tscsmtControlCreate`), and a real function that IS used correctly is additionally checked against its own documented call signature and, for a small set of functions, its own documented preconditions — see [pre-execution-validation.md](pre-execution-validation.md). Treat any generated function name you don't already recognize as unverified until you check it yourself.

## Multi-turn context

A follow-up in the same session can build on more than one recently discussed topic — not just the single most recent one. For example:

```
> Show me how to create a matrix.
> Now reshape it.
> Now compute column means of the reshaped matrix using meanc.
```

Each turn's grounding is computed fresh; naming `meanc` explicitly in the third turn lets it ground correctly even though earlier turns discussed different topics.

## Execution and repair boundaries are unchanged

Asking to run generated code, or to apply it to a file, is redirected to the existing, unchanged `gauss-ai repair <file.gss>` command — instantly, without the model ever being consulted for that turn:

```
> Can you run that for me?
Conversational execution isn't available yet in this version -- this chat can't run or apply anything.
To actually execute or repair a GAUSS file, use the guided command: gauss-ai repair <file.gss>
```

This holds regardless of what was generated earlier in the conversation. No code path in the conversational layer can execute GAUSS, invoke a shell command, write a file, or apply/approve a repair — this is a structural guarantee (verified by dedicated tests that scan the module's own imports and method surface), not merely good model behavior.

## Methodological questions are not code requests

Asking "should I use OLS or a robust regression method?" gets a direct methodological answer, not a code sample — and the answer never implies that a documented, grounded function name makes a statistical or methodological choice correct. Syntax correctness and methodological appropriateness are kept as separate claims, consistent with this repository's Econometrics-expert evaluations since `v0.16.0`.

## Known limitations (updated for `v0.74.0`)

- **Model hallucination is real and was directly observed, and is now mitigated but not eliminated.** In `v0.72.0`'s own live evaluation, `qwen2.5-coder:7b` invented a nonexistent `colmean` function (the real function is `meanc`) and separately fabricated an entire nonexistent panel-regression syntax pattern, both confirmed via real GAUSS execution. `v0.73.0`'s grounding-gated generation and function resolution fix both exact cases (see [grounding-gated-generation.md](grounding-gated-generation.md)), but a model can still occasionally introduce an unsupported symbol the post-generation checker is designed to catch — `v0.74.0`'s own live evaluation reproduced the exact `v0.73.0` `tscsmtControl` hallucination again, unprompted, confirming it is a real, repeatable failure mode this architecture is designed to catch, not eliminate. **Treat all generated code as unverified until you check it yourself** — this is the central reason conversational execution is not implemented in this version.
- **Natural-language phrasing resolves through a curated alias index plus a documentation-derived index (`v0.74.0`)**, not full language understanding. Coverage is now broader than the 5-entry curated table alone, but a phrasing with no real overlap to any real documentation will still not resolve, and is disclosed honestly rather than silently guessed.
- **Retrieval and resolution are bounded heuristics, not real language understanding.** A generic English word can occasionally match unrelated real documentation content (a retrieval-precision false positive; several were found and fixed live during `v0.73.0`'s and `v0.74.0`'s own development), and the post-generation symbol checker is a conservative, best-effort check, not a compiler.
- **Signature/precondition checking (`v0.74.0`) is argument-count only and covers one precondition family (`invpd`) so far** — see [pre-execution-validation.md](pre-execution-validation.md) for the full, honest scope.
- **No execution, no file writes, no automatic repair application** — by design, in this version. See [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md) for the complete, current list.

## Example conversation (real, from this milestone's own live evaluation)

```
> Show me a short reshape example.

[Grounded in local official GAUSS documentation: reshape]

Certainly! Here's a short example of using the `reshape` function in GAUSS:

```gauss
// Create a 3x1 vector of 5's
x = reshape(5, 3);
print x;
```

Expected output, not execution evidence:

```
      5
      5
      5
```

(This example has not been executed in this conversation.)
```

## Local model recommendation

See [ollama-models.md](ollama-models.md) for the current recommended local model. This milestone's own evaluation of `qwen2.5-coder:7b` for code generation specifically (not just Q&A) is summarized in `planning/v0.72.0-conversational-code-generation.md`.
