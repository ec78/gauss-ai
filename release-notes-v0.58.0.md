# v0.58.0 - Repair Application Safety Design

This release is design-only. It defines the complete safety architecture a future Repair Application stage would require, and implements none of it. `scripts/gauss_repair_planner.py` and `scripts/gauss_repair_approval.py` have zero diff. `safe_to_apply` and `safe_to_prepare_draft` remain exactly as structurally `False` as `v0.56.0`/`v0.57.0` left them.

## Added

- `planning/v0.58.0-repair-application-safety-design.md` — the full design: release goal, current-state audit, the core safety question, a four-layer approval separation, an 11-identity model, source-content-hash binding rules, stale-source detection rules, a `RepairDraft` data-model comparison and recommendation, allowed edit scope, the draft-generation boundary (including whether deterministic drafting is realistic vs. where LLM assistance would be needed and how it would be isolated), draft validation rules, human-review requirements, the application gate, the application transaction (with platform caveats), backup/rollback, audit/provenance, an invalidation-rules table, a persistence/durable-session recommendation with supporting threat-model reasoning, a failure taxonomy, an explicit repair/rerun separation, a 22-entry security threat table, a conceptual UX flow, a six-phase implementation roadmap, a proposed future benchmark category, non-goals, and readiness criteria.
- `docs/gauss-repair-application-safety.md` — the shorter, reference-style companion, mirroring `docs/gauss-repair-planning.md`/`docs/gauss-repair-approval.md`'s own format, explicitly marked "design, not implemented" throughout.

## Key Design Conclusions

- **Four approvals, never collapsible into one**: strategy approval (exists, `v0.57.0`), draft approval, application approval, and rerun approval (the last already exists conceptually as ordinary execution confirmation, unrelated to repair). A future implementation must keep each one separately displayed and separately confirmed, tied to its own digest.
- **Source-content-hash re-verification immediately before any write is the one rule everything else depends on.** Path, filename, and workspace ID are each individually insufficient; only a hash over bytes actually read at the moment they matter can detect staleness. A mismatch is always a hard stop — no rebasing, no merging, no best-effort apply.
- **Structured, bounded line-range edits are recommended over unified diffs or whole-file replacement** for the draft representation, specifically to avoid importing a patch-apply tool's own fuzzy-matching behavior into a safety-critical validation gate.
- **Persistence recommendation: a process-local prototype is sufficient for a first implementation.** Durable *approval* state is recommended against (losing it on crash is the safe, fail-closed outcome); durable *audit* is recommended starting at implementation Phase 5, because audit protects a different, asymmetric-risk property (forensic reconstruction after the fact) than session durability would. Durable execution sessions are not required by repair application itself.
- **A 22-entry threat table** covers stale-approval replay, draft/source substitution, path traversal, symlink escape, workspace swap, approval broadening, partial writes, failed rollback, process crash, untrusted LLM-generated diffs, and more — each marked mitigated-by-design or explicitly, honestly marked unresolved (symlink-escape TOCTOU, the validate-then-write race, and the crash-between-replace-and-audit-write gap are the three left partially open).

## Not Implemented

Patch generation, diff generation, file writes, repair application, rollback, automatic rerun, source inspection without explicit authorization, multi-file repair, binary repair, an atomic file-write utility, a `RepairDraft` type, an audit store — none of it. No test for application behavior exists, because no application behavior exists to test.

## Documentation Updates

`README.md`, `ROADMAP.md` (new `v0.58.0` section; the "Repair Application" future candidate updated from "not planned, scoped" to "designed, not authorized for implementation"), `KNOWN_LIMITATIONS.md`, `CHANGELOG.md`, `docs/gauss-repair-planning.md`, and `docs/gauss-repair-approval.md` were all updated to reference this design without changing any of their own claims about what is actually implemented today.

## Remaining Limitations

- This is a design, not a specification frozen against revision — a future implementation milestone may surface a gap this document didn't anticipate and should feel free to revise it.
- Three threats are documented as partially unresolved rather than falsely claimed as solved (see the planning document's own threat table).
- No implementation phase, timeline, or resourcing commitment is made — only phase ordering and dependencies.
- Everything Repair Application itself would require remains unimplemented: patch construction, file writes, backup/rollback, durable audit, and a separate rerun workflow.

## Next Recommended Milestone

Not this milestone's decision to make unilaterally — per the design's own readiness criteria (§26), implementation should not begin until this design has been explicitly reviewed and authorized. If authorized, Phase 1 (source identity and draft model, `planning/v0.58.0-repair-application-safety-design.md` §23) is the correct starting point; it depends on nothing beyond what already exists (`repair_plan_digest`, the file-reader's existing checksum precedent). Durable execution sessions remain a separate, still-unauthorized candidate, relevant only if a future workflow needs approval/application state to survive across conversation turns — no such workflow exists today.
