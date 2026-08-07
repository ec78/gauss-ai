# GAUSS Repair Session Summary

## Purpose

`scripts/gauss_repair_session_summary.py` (`v0.66.0`) is a read-only composition of evidence already produced by every prior milestone in the reasoning pipeline. It answers exactly one question: *what has happened in this repair session so far, in one place?* It introduces no new workflow, no new approval, no new repair capability, no execution, no planning, no rerun, no rollback, no persistence, no durable session, and no mutation of anything.

## What This Module Is Not

**Not a new workflow.** It computes nothing that did not already exist as a real object or a pure, already-established recomputation (interpretation, diagnosis, and the verification comparison are each recomputed the exact same way the CLI's own `interpret`/`diagnose`/`show-verification-request` commands already do — no new derivation logic).

**Not a new authority.** It owns none of the objects it displays. Every field on `RepairSessionSummary` holds a reference to an object constructed elsewhere, by the module that already owns that stage.

**Not a new approval.** Nothing about calling `show-repair-session` records, approves, declines, or reviews anything.

## The Architectural Exception

Every layer added since `v0.56.0` follows a strict, minimal-dependency rule: a layer imports only the one layer immediately below it. `gauss_repair_session_summary.py` is a deliberate, singular exception — its entire purpose is composition *across* the full pipeline, so it imports every stage's own module (`gauss_code_assistant_workflow`, `gauss_execution_interpreter`, `gauss_execution_diagnostics`, `gauss_repair_planner`, `gauss_repair_approval`, `gauss_repair_draft`, `gauss_repair_draft_approval`, `gauss_repair_application_approval`, `gauss_repair_application`, `gauss_verification_execution`, `gauss_verification_review`). Despite the wide import surface, it contains zero logic beyond composition: no I/O, no hashing, no clock access beyond a caller-supplied `generated_at`, and no code path capable of constructing, mutating, or reconstructing any of the imported types itself. Nothing else in the repository imports this module except the CLI.

## Position in the Reasoning Pipeline

```
Execution -> Interpretation -> Diagnosis -> Repair Plan -> Strategy Approval
    -> Repair Draft -> Draft Approval -> Application Approval
    -> (Application Gate -- checked separately, not composed here)
    -> Repair Application -> Verification Execution -> Comparison
    -> Verification Review
    -> Repair Session Summary (this module, v0.66.0)
```

## What Is Deliberately Excluded

**The Application Gate.** `evaluate_application_gate(...)` requires a freshly-supplied current source identity and workspace status — a genuine, external freshness check, not a cached record. A read-only summary has no sanctioned way to fabricate or silently re-derive that freshness, so the gate is not one of this summary's sections. The tester still runs `check-repair-application-gate` explicitly.

## RepairSessionSummary

Immutable. Twelve `Optional` reference fields (one per pipeline stage), plus `timeline`, `current_status`, `generated_at`, and a fixed `boundary`. Every populated field is the *exact same object* the caller passed in — proven by `is` identity checks throughout the test suite, never `==`.

### Timeline

Built in **fixed pipeline order**, never sorted by timestamp value. Only stages that both exist and carry a genuine timestamp field contribute an entry: strategy approval, repair draft, draft approval, application approval, application result, verification request, and verification review. Execution, interpretation, diagnosis, and the repair plan carry no timestamp anywhere in this architecture — an existing limitation, not something this module invents or works around. Timestamps are opaque, caller-supplied strings, frequently identical across stages under a fixed clock; a value-sort would be unstable, so pipeline order is used unconditionally.

### Current status

A single string naming the furthest stage actually reached, computed by walking the pipeline from its end backward. Because interpretation and diagnosis are always derivable, on demand, from an execution's own already-captured evidence (the same recomputation `interpret`/`diagnose` already perform), a session that only ran `execute` reports `current_status: diagnosed`, not merely `executed` — both are genuinely available evidence, not fabricated ones.

### Boundary

A single, fixed, session-state-invariant disclosure, present on every summary:

```
This is a read-only summary of evidence already produced by prior stages. It creates no new
approval, executes nothing, plans nothing, repairs nothing, and mutates no prior state. Any
missing stage below reflects that stage genuinely has not occurred in this session.
```

## CLI Usage

```
gauss-mvp> show-repair-session
This is a read-only summary of evidence already produced by prior stages. ...
generated_at: ...
current_status: application_applied
== original execution ==
execution_status: failed
...
== approvals ==
strategy_approval: approved
draft_approval: approved
application_approval: approved
== application ==
outcome: applied
backup_created: true
== verification execution ==
not yet occurred
== comparison ==
not available
== verification review ==
not yet recorded
== timeline ==
  1000.0  strategy_approval: Strategy approved
  1000.0  repair_draft: Repair draft generated
  ...
```

`show-repair-session` has no precondition — unlike every other command in this CLI, an empty session is not an error; it is honestly reported as `current_status: no_execution` with every section reading `not yet occurred`/`none`/`not available`/`not yet recorded` and an empty timeline.

## Limitations

- No Application Gate section — see above.
- No timestamp for execution, interpretation, diagnosis, or the repair plan — the timeline reflects only the seven stages that carry one.
- Process-local only, exactly like every other adapter session field — cleared by `reset`, not durable, not shared across processes.
- Summarizes exactly one adapter session's own current state — no aggregation across multiple sessions or multiple workspaces.
