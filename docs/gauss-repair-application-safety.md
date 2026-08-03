# GAUSS Repair Application Safety (Design, Not Implemented)

**Nothing described in this document exists in code.** No module in this repository implements any of it. This page documents the *design* produced by `v0.58.0` for a future Repair Application stage — the full rationale, data model, and threat analysis lives in `planning/v0.58.0-repair-application-safety-design.md`; this page is the shorter, reference-style companion, mirroring how `docs/gauss-repair-planning.md` and `docs/gauss-repair-approval.md` document their own (implemented) stages.

## Why This Document Exists Before The Code Does

Every implemented stage in this pipeline — interpretation, diagnosis, repair planning, repair approval — was designed to make illegitimate outcomes structurally impossible, not merely discouraged. Repair application is the first stage that can mutate a user's file. Writing the safety design *before* any code that could write a file exists is a deliberate continuation of that same discipline, not an extra step bolted on afterward.

## Position in the Reasoning Pipeline

```
Execution
  -> Evidence Collection      (gauss_execution_workflow.py / gauss_code_execution.py)
  -> Interpretation           (gauss_execution_interpreter.py, v0.51.0)
  -> Verified Knowledge       (gauss_error_catalog.py, v0.51.0-v0.56.0)
  -> Diagnosis                (gauss_execution_diagnostics.py, v0.54.0-v0.55.0)
  -> Repair Planning          (gauss_repair_planner.py, v0.56.0)
  -> Approval                 (gauss_repair_approval.py, v0.57.0)
  -> Repair Application       (design only, v0.58.0 -- no code)
```

| Stage | Answers | Implemented? |
|---|---|---|
| Repair Planning | What bounded strategy should be considered? | Yes (`v0.56.0`) |
| Approval | Did a human accept or decline this plan? | Yes (`v0.57.0`) |
| Repair Draft (future) | What specific, bounded edit is proposed against an exact source state? | No — data model designed only |
| Draft Approval (future) | Did a human accept this exact edit? | No |
| Application Approval (future) | Did a human authorize applying this exact edit to this exact current file? | No |
| Repair Application (future) | What change was actually written? | No |
| Rerun (future, separate) | Was the resulting code executed? | No — and never automatic |

## The Four Approvals

`v0.57.0` implemented exactly one of these — strategy approval. The other three are designed, not built:

1. **Strategy approval** *(exists)* — accepting a `RepairPlan`'s general direction. Authorizes nothing beyond recording that decision.
2. **Draft approval** *(designed, not built)* — accepting one specific, concrete edit against one specific, hash-verified source state.
3. **Application approval** *(designed, not built)* — authorizing that exact approved edit to be written to that exact, freshly-reverified file.
4. **Rerun approval** *(not repair-specific — this is the existing `request`/`plan`/`confirm`/`execute` path)* — authorizing execution of the result. Never implied by application.

No future implementation may collapse any two of these into one confirmation.

## The One Rule Everything Else Follows From

**A target file's content hash is re-verified immediately before any write, and any mismatch is a hard, unconditional stop.** No rebasing, no merging, no "best effort." This is the single design decision the rest of the safety model exists to support — see `planning/v0.58.0-repair-application-safety-design.md` §3 for the full reasoning and §21 for how it defends against the concrete threats it's meant to stop.

## What Would Be New

A future implementation would introduce a `RepairDraft` model — an immutable, digest-identified object binding a proposed structured edit (bounded line-range replacements, not a fuzzy-matched text patch — see the design doc §8 for why) to an exact `source_content_hash`, exact `workspace_id`/`relative_path`, and the `repair_plan_digest` it was derived from. Nothing in this repository computes any of that today.

## What Stays Exactly As It Is

- `scripts/gauss_repair_planner.py` — unchanged.
- `scripts/gauss_repair_approval.py` — unchanged. `RepairApprovalStore` remains process-local, digest-bound, conflict-protected, and unconnected to anything downstream.
- `safe_to_apply` and `safe_to_prepare_draft` — unchanged, still structurally `False` everywhere they appear.
- The existing execution confirmation path (`request`/`plan`/`confirm`/`execute`) — unchanged, and explicitly designed (§20 of the planning doc) to remain the *only* path to execution, never bypassed by a repair application.

## Safety Boundaries (Design Commitments for Any Future Implementation)

- A stale source hash always blocks application — never a silent merge.
- Every identity in the chain (plan → draft → application) is bound by digest, never by convenience fields like path or filename alone.
- No approval layer authorizes the next layer's action.
- No automatic rerun, ever, as a consequence of application.
- No multi-file edits, no binary files, no renames, no deletes, no new files, no whole-file replacement, in the initial scope.
- A backup is required before any write is attempted, and is never silently deleted — even if rollback itself later fails.
- No LLM call is trusted with application; if an LLM ever assists *drafting*, its output is untrusted input subject to the exact same deterministic validation gate as any other draft.

## Limitations of This Design (As a Design)

- It is a design, not a specification frozen against future revision — a future implementation milestone may surface a gap this document didn't anticipate, and should be free to revise this document rather than treat it as immutable.
- It recommends against durable approval/session state for a first implementation (§18 of the planning doc), which means an approval does not survive a process restart — this is treated as a safety feature (fail closed), not a gap, but it does mean a future workflow spanning multiple sessions would need a separate, explicitly authorized redesign.
- Several threats (symlink-escape TOCTOU, the validate-then-write race, the crash-between-replace-and-audit-write gap) are documented as **partially unresolved** rather than falsely claimed as fully mitigated — see the planning document's §21 threat table.
- No implementation phase, timeline, or resourcing commitment is made by this document — only phase *ordering and dependencies* (§23 of the planning doc).
