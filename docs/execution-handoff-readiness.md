# Execution-Handoff Readiness

**Status: `v0.77.0`.** Extends [docs/pre-execution-validation.md](pre-execution-validation.md), [docs/gauss-syntax-validation.md](gauss-syntax-validation.md), and [docs/differential-syntax-validation.md](differential-syntax-validation.md). Read those first. `v0.77.0`'s own Phase 14 re-verification: `compute_handoff_readiness(...)`'s logic itself is **unchanged** from `v0.76.0` (the four rules below are byte-for-byte the same) — this milestone hardened the syntax validator feeding INTO it, not the readiness computation itself. Re-run live against the hardened validator: `INVALID` syntax still forces `NOT_READY` (confirmed live, `67.3`/`67.4` — the headline semicolon regression reproduced and caught again), `PARTIAL`/`UNKNOWN` syntax and an `UNVERIFIED` runtime-dependent precondition still force `REVIEW_REQUIRED` rather than either extreme (confirmed live, `67.8` — the first live exercise of a genuine runtime-variable precondition, `chol(x)` with `x` a real variable), and `HANDOFF_CANDIDATE` remains live-reachable and real-GAUSS-confirmed-accepted (`67.10`, independently cross-checked by the differential corpus run itself, item `D-025`).

## What this is — and what it is not

`HandoffReadiness` (`gauss_pre_execution_validation.compute_handoff_readiness(...)`) answers a different question than `ExecutionEligibility` does:

| | Question it answers |
|---|---|
| `ExecutionEligibility` | Is this code **structurally worth validating** (grounded, no unknown symbol, no known signature/precondition/parameter-role violation)? |
| `HandoffReadiness` | Is there **enough deterministic evidence** for a **future**, separate, user-approved execution-handoff workflow to even **consider** this code? |

**This milestone adds no execution capability of any kind.** `HANDOFF_CANDIDATE` is not "safe," not "correct," not "approved," and not "executed." No conversational path in this repository executes GAUSS, invokes a shell, writes a file, applies a repair, or bypasses the existing execution-approval workflow — that remains true regardless of what readiness state a turn computes. The model cannot set or influence this verdict: `compute_handoff_readiness(...)` takes no provider/model argument of any kind.

## The three states

- **`NOT_READY`** — a known violation exists (invalid syntax, an unresolved eligibility problem, an incompatible signature, a violated precondition, a mismatched parameter role, an unknown call symbol) or the underlying code failed eligibility/ambiguity checks outright.
- **`REVIEW_REQUIRED`** — no known violation, but a real evidence *gap* remains: syntax coverage is `PARTIAL`/`UNKNOWN`, a documented call's signature could not be extracted, a documented precondition is `UNVERIFIED` (typically because the input is a runtime value, not a literal), or overall validation coverage falls short of `BROAD`.
- **`HANDOFF_CANDIDATE`** — no known violation and no evidence gap: eligibility is `ELIGIBLE_FOR_VALIDATION`, syntax is `VALIDATED`, every documented signature/precondition/parameter-role check that ran found nothing wrong, and coverage is `BROAD`.

## The exact deterministic rules

1. `eligibility != ELIGIBLE_FOR_VALIDATION` → `NOT_READY` (covers both `INELIGIBLE` and `REQUIRES_CLARIFICATION` — nothing to consider yet).
2. `syntax.status == INVALID` → `NOT_READY`, quoting the syntax issue(s) directly.
3. Otherwise, any of the following → `REVIEW_REQUIRED`:
   - `syntax.status` is `PARTIAL` or `UNKNOWN`.
   - Any documented call has `signature_known == False` (the documentation exists, but this version couldn't reliably extract its call form).
   - Any documented precondition is `UNVERIFIED` (a real, disclosed, typically runtime-dependent gap).
   - The evidence profile is not `BROAD`.
4. Otherwise → `HANDOFF_CANDIDATE`.

This directly encodes a conservative default policy: an **unknown** signature or an **unverified** runtime-dependent precondition never silently becomes `HANDOFF_CANDIDATE` — they force human review — while a **known** violation is `NOT_READY`, never merely "needs review."

## Evidence-breadth categories (`EvidenceProfile`)

Computed from `ValidationCoverage`'s five non-orthogonal dimensions (symbol, signature, parameter-role, precondition, syntax — **not** predicted-output, which stays orthogonal, see below): `MINIMAL` / `PARTIAL` / `BROAD`. Never a numeric score, for the same reason nothing else in this module uses one — see `gauss_pre_execution_validation.py`'s own module docstring.

## Predicted output stays orthogonal

A model's own claimed output (`PredictedOutputClaim`) never affects readiness or coverage breadth in either direction — a correct prediction does not make code "more" handoff-ready, and a wrong one does not make otherwise-valid code less ready. Predicted-output correctness, syntax validity, and execution readiness are three different questions this module is careful never to collapse into one.

## Example

```
- Execution handoff readiness: review_required
  - runtime-dependent precondition(s) remain unverified for: invpd
  (This code has not been executed. This is not an approval to run it.)
```

## Known limitations

- Readiness is only ever computed from evidence this codebase can already produce deterministically — it inherits every limitation of syntax validation, signature extraction, precondition checking, and parameter-role checking documented on their own pages.
- `HANDOFF_CANDIDATE` is a claim about **evidence breadth**, not about correctness, safety, or methodological appropriateness — those remain outside this system's ability to verify, in this milestone or any prior one.
- No execution-handoff workflow exists yet. `HANDOFF_CANDIDATE` currently has no consumer beyond this advisory report — building that consumer, with its own explicit user-approval and safety-review steps, is future, unstarted work.
