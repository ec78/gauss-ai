# Conversational GAUSS Code Generation

**Status: Alpha — added in `v0.72.0`, extending [conversational-qa.md](conversational-qa.md).**

In addition to answering questions, `gauss-ai` chat can now generate GAUSS code from a plain-language request. This is still advisory only: generated code is never executed, never written to a file, and never treated as an approved repair. It uses the exact same provider/grounding architecture as conversational Q&A — this is an extension, not a second system.

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

The system prompt explicitly instructs the model never to invent a GAUSS function name, and to say so plainly if it isn't confident one exists, rather than generating a plausible guess. **This has been observed to work inconsistently in this repository's own live evaluation against a real local model** — see Known Limitations below. Treat any generated function name you don't already recognize as unverified until you check it yourself (`gauss-ai` chat's own documentation grounding, or the official GAUSS documentation directly).

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

## Known limitations (as validated in this milestone)

- **Model hallucination is real and was directly observed.** In this repository's own live evaluation, `qwen2.5-coder:7b` invented a nonexistent `colmean` function (the real function is `meanc`) when the relevant documentation wasn't retrieved, and separately fabricated an entire nonexistent panel-regression syntax pattern with no disclosed uncertainty. Both were confirmed as hallucinations via real GAUSS execution. **Treat all generated code as unverified until you check it yourself** — this is the central reason conversational execution is not implemented in this version.
- **Natural-language phrasing does not map to function names.** "Column means" will not automatically resolve to `meanc` unless you name the function; this is disclosed honestly (a partial-grounding gap), not silently papered over.
- **Retrieval is a bounded heuristic, not real language understanding.** A generic English word can occasionally match unrelated real documentation content (a retrieval-precision false positive), and clarification-asking behavior depends entirely on the model, not on any code enforcement.
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
