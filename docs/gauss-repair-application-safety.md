# GAUSS Repair Application Safety (Design, Application Transaction Not Implemented)

**Most of this document's design is now implemented; the application transaction itself (§14) is not.** As of `v0.61.0`, this repository implements source identity and the `RepairDraft` model (Phase 1, `v0.59.0`), deterministic draft validation (Phase 2, `v0.59.0`), draft-review and approval (Phase 3, `v0.60.0`), and application approval plus a pure application-gate precondition check (Phase 4.C and a pure-logic slice of §13, `v0.61.0`, `docs/gauss-repair-application-approval.md`). What remains unimplemented is exactly what this document's own §14 describes: the actual file-write transaction, backup/rollback (§15), audit (§16), and rerun (§20). The full rationale, data model, and threat analysis lives in `planning/v0.58.0-repair-application-safety-design.md`; this page is the shorter, reference-style companion, mirroring how `docs/gauss-repair-planning.md` and `docs/gauss-repair-approval.md` document their own (implemented) stages.

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
  -> Approval (strategy)      (gauss_repair_approval.py, v0.57.0)
  -> Repair Draft              (gauss_repair_draft.py, v0.59.0)
  -> Repair Draft Approval    (gauss_repair_draft_approval.py, v0.60.0)
  -> Repair Application Approval  (gauss_repair_application_approval.py, v0.61.0)
  -> Repair Application Gate       (gauss_repair_application_gate.py, v0.61.0 -- pure precondition check)
  -> Repair Application       (application transaction itself -- still no code)
```

| Stage | Answers | Implemented? |
|---|---|---|
| Repair Planning | What bounded strategy should be considered? | Yes (`v0.56.0`) |
| Approval (strategy) | Did a human accept or decline this plan? | Yes (`v0.57.0`) |
| Repair Draft | What specific, bounded edit is proposed against an exact source state? | Yes (`v0.59.0`) |
| Draft Approval | Did a human accept this exact edit? | Yes (`v0.60.0`) |
| Application Approval | Did a human authorize applying this exact edit to this exact current file? | Yes (`v0.61.0`) |
| Application Gate | Do every checkable precondition currently hold? | Yes, as pure logic (`v0.61.0`) — never itself an authorization |
| Repair Application (future) | What change was actually written? | No — the file-write transaction (§14) is not implemented |
| Rerun (future, separate) | Was the resulting code executed? | No — and never automatic |

## The Four Approvals

All four are now implemented:

1. **Strategy approval** *(implemented, `v0.57.0`)* — accepting a `RepairPlan`'s general direction. Authorizes nothing beyond recording that decision.
2. **Draft approval** *(implemented, `v0.60.0`)* — accepting one specific, concrete edit against one specific, hash-verified source state.
3. **Application approval** *(implemented, `v0.61.0`)* — authorizing that exact approved edit to be written to that exact, freshly-reverified file, once a transaction exists to carry it out. Approving does not itself write anything — no transaction consumes this decision yet.
4. **Rerun approval** *(not repair-specific — this is the existing `request`/`plan`/`confirm`/`execute` path)* — authorizing execution of the result. Never implied by application.

No implementation may collapse any two of these into one confirmation. See `docs/gauss-repair-application-approval.md` for layers 2 and 3's implementation, plus the pure Application Gate check.

## The One Rule Everything Else Follows From

**A target file's content hash is re-verified immediately before any write, and any mismatch is a hard, unconditional stop.** No rebasing, no merging, no "best effort." This is the single design decision the rest of the safety model exists to support — see `planning/v0.58.0-repair-application-safety-design.md` §3 for the full reasoning and §21 for how it defends against the concrete threats it's meant to stop.

## What Would Still Be New

A future implementation would introduce the application transaction itself (§14): reading and re-hashing the current file, creating and hash-verifying a backup, writing to a temporary file in the same directory, atomically replacing the target, and recording the result in an audit entry. Nothing in this repository writes to a file, creates a backup, or records an audit entry today — every module through `v0.61.0` remains read/reason-only.

## What Stays Exactly As It Is

- `scripts/gauss_repair_planner.py`, `scripts/gauss_repair_approval.py`, `scripts/gauss_repair_draft.py`, `scripts/gauss_repair_draft_approval.py` — unchanged since their own respective milestones.
- `safe_to_apply` and `safe_to_prepare_draft` — unchanged, still structurally `False` everywhere they appear; `ApplicationGateResult` (`v0.61.0`) does not even have a `safe_to_apply` field.
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
