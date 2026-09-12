# Universal Code-Shaped Response Validation

**Status: `v0.75.0`.** Extends [docs/pre-execution-validation.md](pre-execution-validation.md) (`v0.74.0`), [docs/grounding-gated-generation.md](grounding-gated-generation.md) (`v0.73.0`), and [docs/conversational-code-generation.md](conversational-code-generation.md) (`v0.72.0`). Read those first — this page covers exactly one change: **what decides whether generated code gets validated.**

## The gap this closes

Before `v0.75.0`, whether a code-shaped answer received documented-signature/precondition/eligibility evidence depended on how the *original question* was classified:

- A question like "Write GAUSS code to invert this matrix" classifies as `CODE_GENERATION` — its answer was always validated.
- A question like "What does invpd do?" classifies as `QA` — even if the model's own answer happened to include a real, call-shaped GAUSS code example, that code never received a signature/precondition/eligibility verdict at all. `v0.74.0`'s own live evaluation found and disclosed this gap; it did not fix it (see `planning/v0.74.0-pre-execution-validation.md`, Section 13/15).

This meant `intent classification` (a bounded, deterministic, but necessarily approximate phrase-matcher) silently decided a safety-relevant question: *does this code get checked at all?* A user who asked a conceptual question and got a code example back as part of the answer had no guarantee that example was ever run through the same evidence a `CODE_GENERATION` request would get.

## The fix

`ConversationEngine.ask(...)` now computes the generation-gate (`compute_generation_gate(...)`) for every intent that reaches the provider call, not only `CODE_GENERATION` — but it still only uses that gate to block/clarify the provider call itself for `CODE_GENERATION` requests (prose-only QA is completely unaffected: the provider is still always called, and a plain-prose answer with no code still gets no validation section, exactly as before).

After the provider responds, the entry condition for the validation pass changed from:

```
if generated_code and gate is not None and gate.policy in (FULL, SUPPORTED_ONLY):
    validate(...)
```

to:

```
if generated_code:
    validate(...)
```

**The presence of code, not the original intent, now decides whether validation runs.** If the underlying grounding bundle was never `FULL`/`SUPPORTED_ONLY` (e.g. a `QA`-route hallucination with zero real evidence), `compute_eligibility(...)`'s own existing `generation_policy` check still correctly marks that code `INELIGIBLE` — nothing here silently passes an ungrounded answer just because it arrived via a different intent.

## What this looks like

A `QA`-classified question whose answer happens to include a real, correct example:

```
> What does invpd do?
[Grounded in local official GAUSS documentation: invpd]

invpd inverts a symmetric positive definite matrix, for example:

y = invpd({2 1, 1 2});

(This example has not been executed in this conversation.)
Validation:
- Function invpd: documented; signature: compatible
- Preconditions:
  - invpd: satisfied -- the literal input matrix is symmetric and positive definite (verified by leading-principal-minor computation)
- Execution eligibility: eligible_for_validation
  (This means only that deterministic checks found no known problem -- not that the code is correct, safe, methodologically appropriate, or approved to run.)
```

Before `v0.75.0`, this same answer would have shown no `Validation:` section at all.

A `QA`-classified question whose answer hallucinates a symbol:

```
> What does reshape do?
[Grounded in local official GAUSS documentation: reshape]
[Warning: the generated code also calls `colmean`, which is not a documented function this session could verify -- treat it as unverified, not authoritative GAUSS syntax.]

You can compute column averages like this:

x = colmean(y);

(This example has not been executed in this conversation.)
Validation:
- Execution eligibility: ineligible
  Cannot mark this code eligible for validation:
  - unresolved/unsupported call symbol(s): colmean
```

Before `v0.75.0`, `colmean` was still flagged as an unknown symbol (that post-generation check was already intent-independent, since `v0.73.0`) — but no eligibility verdict existed at all.

## What is unaffected

- **Prose-only QA.** A question with no code-shaped answer behaves exactly as before: no `Validation:` section, `pre_execution_eligibility` stays `None` (the repository-equivalent of "not applicable" — see `gauss_pre_execution_validation.py`'s own top-of-file docstring for why a fourth `ExecutionEligibility` state was deliberately not added instead of reusing this convention).
- **Execution/repair-request routing.** `EXECUTION_REQUEST`/`REPAIR_OR_APPLICATION_REQUEST` intents still return the fixed boundary message before the provider is ever called, unchanged.
- **CLI-invocation interception.** Still happens upstream in `gauss_ai_chat.py`, before `ConversationEngine.ask(...)` is ever reached, unchanged.
- **`CODE_GENERATION` requests.** Validated exactly once, exactly as before — the universal-routing change does not introduce a second, duplicate validation path; `_validate_pre_execution(...)` is still the single call site, now simply reached from a broader set of intents.

## Richer evidence now computed on every validated code block

Independent of the routing fix above, `v0.75.0` also broadened what the (now-universal) validation pass actually checks — see [docs/pre-execution-validation.md](pre-execution-validation.md#whats-new-in-v0750) for the full list: parameter-role/type checking beyond argument count, two new precondition families (`solpd`, `chol`) plus an upgraded `inv` check, structured predicted-output claim verification, and a validation-coverage summary.

## Known limitations

- Universal routing means a QA-route hallucination is now correctly flagged `INELIGIBLE` — but it does not make the underlying model any less likely to hallucinate in the first place. This is detection, not prevention.
- The routing fix does not add any new retrieval/grounding capability — a `QA`-classified answer's code is validated against whatever grounding evidence `ground_multi(...)` already found for that same turn (or, for a follow-up, the bounded `recent_topics` carryover `v0.72.0` already established). If that evidence is thin, the validation evidence built on top of it is correspondingly thin (surfaced honestly via `UNKNOWN`/`UNVERIFIED`, never inflated).
- No execution capability of any kind was added anywhere in this change — see this milestone's own final report (`planning/v0.75.0-*.md`) Section 10 for the explicit safety checklist.
