# Deterministic Pre-Execution Validation

**Status: `v0.74.0`.** Extends [docs/grounding-gated-generation.md](grounding-gated-generation.md) (`v0.73.0`) and [docs/conversational-code-generation.md](conversational-code-generation.md) (`v0.72.0`). Read those first — this page only covers what's new: checking whether generated code's *calls* and *documented preconditions* are actually consistent with real documentation, not just whether its *symbols* are.

## Why this exists

`v0.73.0`'s own live evaluation proved that symbol-level grounding is necessary but not sufficient:

- A `FULL`-gated request correctly used a real, documented function (`tscsFit`) — but also hallucinated an unrelated symbol, `tscsmtControl()`, that isn't a real callable at all (it's the name of a *struct type* mentioned in `tscsFit`'s own documentation; the real constructor is `tscsmtControlCreate()`).
- A real, successful GAUSS execution of a generated `invpd(...)` example did not prove the input actually satisfied `invpd`'s own documented requirement (a symmetric, positive-definite matrix) — `invpd`'s own documentation says as much: a non-symmetric input can sometimes "erroneously appear to operate successfully."

**Execution success, documented-precondition satisfaction, and syntax/signature validity are three different, independent kinds of evidence.** This module never conflates them.

## What's new

1. **A documentation-derived concept index** (`gauss_doc_concept_index.py`) supplements `v0.73.0`'s 5-entry curated alias table. It derives candidate symbols directly from each documentation page's own heading, "Purpose" section, and cross-references — a small, deterministic bag-of-keywords match, never a language model, never web search, never a vector database. Every candidate is still independently re-verified against your own configured documentation before being trusted, exactly like the curated table.
2. **Documented call-signature extraction and compatibility checking.** For each function actually grounded this turn, the assistant attempts to extract its documented argument count(s) from its own real "Format"/`.. function::` text, then checks whether the generated call's own argument count is compatible — `COMPATIBLE`, `INCOMPATIBLE`, or `UNKNOWN` (when extraction isn't reliable). This checks argument **count** only — never order, type, or semantic correctness.
3. **A small set of documented-precondition checks.** Currently implemented: whether a *literal* matrix argument to `invpd` is symmetric and positive definite (checked by real, deterministic linear algebra — no guessing). If the argument is a runtime variable or expression instead of a literal, the result is honestly `UNVERIFIED`, never assumed satisfied.
4. **An explicit execution-eligibility verdict**: `INELIGIBLE`, `REQUIRES_CLARIFICATION`, or `ELIGIBLE_FOR_VALIDATION`.

## What `ELIGIBLE_FOR_VALIDATION` means — and does not mean

> This code has enough deterministic support (documented symbols, compatible signatures, no known-violated preconditions) to be considered for a **future**, separate, controlled execution-validation workflow.

It does **not** mean:

- Correct
- Safe
- Methodologically appropriate for your problem
- Approved for execution
- Verified by you

Nothing in this milestone connects generated code to real execution. That remains true even for `ELIGIBLE_FOR_VALIDATION` code — it is still never executed, still never written to a file, still never applied as a repair.

## What you'll see

For a fully clean example:

```
[Grounded in official GAUSS documentation: meanc]

x = rndu(1000, 4);
column_means = meanc(x);

(This example has not been executed in this conversation.)
Validation:
- Function meanc: documented; signature: compatible
- Execution eligibility: eligible_for_validation
  (This means only that deterministic checks found no known problem -- not that the code is correct, safe, methodologically appropriate, or approved to run.)
```

For a documented-precondition violation:

```
Validation:
- Function invpd: documented; signature: compatible
- Preconditions:
  - invpd: violated -- the literal input matrix is not symmetric, which invpd's own documentation requires
- Execution eligibility: ineligible
  Cannot mark this code eligible for validation:
  - invpd: the literal input matrix is not symmetric, which invpd's own documentation requires
```

For a hallucinated symbol with a real documented companion:

```
[Warning: the generated code also calls `tscsmtControl`, which is not a documented function this session could verify -- treat it as unverified, not authoritative GAUSS syntax.]
Validation:
- `tscsmtControl` was not found, but `tscsmtControlCreate` is documented in the retrieved source.
- Execution eligibility: ineligible
```

Note what does *not* happen here: `tscsmtControl` is never silently rewritten to `tscsmtControlCreate`. A future, explicitly-authorized repair/editing milestone might make an accepted correction like that possible — this one only surfaces the diagnostic.

## The distinction chain

Five different things this page is careful never to collapse into one:

1. **Generated** — the model produced this text.
2. **Grounded** — real documentation evidence was retrieved for at least part of the request.
3. **Structurally validated** — the symbols used are documented, and call signatures are argument-count compatible (this milestone).
4. **Runtime tested** — actually executed against real GAUSS (never happens in chat, in any milestone so far).
5. **Semantically/methodologically appropriate** — the right approach for *your* actual problem (this system never claims to know that).

A result can be true at one level and false at another — the `invpd` example above (real GAUSS execution succeeded) whose input didn't actually satisfy the documented precondition is a real, observed instance of exactly that.

## Known limitations

- **Signature checking is argument-count only.** A call with the right number of arguments in the wrong order, or with an argument of the wrong shape/type, is not caught.
- **Precondition checking covers one function family (`invpd`) so far**, and only for literal matrix arguments — a real, disclosed, narrow start, not a claim of general semantic analysis.
- **The documentation-derived concept index can propose a topically-related but not-quite-right candidate** (bag-of-words overlap has no real understanding of synonyms) — when this happens, it either resolves to a real, verified, but imperfectly-matched symbol, or (more often) correctly reports genuine ambiguity and asks rather than guessing.
- **The new eligibility computation currently only runs for requests classified as code-generation intent.** A code-shaped answer to a plain question still gets `v0.73.0`'s older unsupported-symbol warning, but not the newer signature/precondition/eligibility evidence — a known, disclosed gap, not silently ignored.
- Every `v0.71.0`-`v0.73.0` limitation (no execution, no autonomous debugging, `docs-root` dependency, local-Ollama/hardware dependence) still applies unchanged.
