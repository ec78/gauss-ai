"""Repair Session Summary -- a read-only composition of evidence already
produced by every prior milestone in the reasoning pipeline.

Position in the reasoning pipeline:

    Execution -> Interpretation -> Diagnosis -> Repair Plan -> Strategy Approval
        -> Repair Draft -> Draft Approval -> Application Approval
        -> (Application Gate -- checked separately, not composed here)
        -> Repair Application -> Verification Execution -> Comparison
        -> Verification Review
        -> Repair Session Summary (this module, v0.66.0)

This introduces no new workflow, no new approval, no new repair capability,
no execution, no planning, no rerun, no rollback, no persistence, no durable
session, and no mutation of anything. It owns none of the objects it
displays -- it only holds references to them and presents them together, in
one place, for a human to read.

Every other layer added since v0.56.0 follows a strict, minimal-dependency
rule: a layer imports only the one layer immediately below it. This module
deliberately breaks that pattern, and it is a conscious, singular exception:
its entire purpose is composition ACROSS the full pipeline, so it needs type
visibility into every stage that can appear in a session. Despite the wide
import surface, it contains zero logic beyond composition -- no I/O, no
clock access beyond a caller-supplied `generated_at`, no hashing, no
re-derivation of any field already present on the objects it references, and
no code path capable of constructing, mutating, or reconstructing any of the
imported types itself (it only ever receives already-built instances as
parameters).

The Application Gate is deliberately NOT part of this summary.
`evaluate_application_gate(...)` requires a freshly-supplied current source
identity and workspace status -- a genuine, external freshness check, not a
cached record. Fabricating a gate result inside a read-only summary (or
silently re-reading the file to produce one) would be new capability this
milestone does not authorize. The tester still runs
`check-repair-application-gate` explicitly for that.

Never implements: new approvals, new execution, new planning, rerun, repair,
rollback, persistence, durable sessions, or mutation of any kind.
"""

from __future__ import annotations

from dataclasses import dataclass

import gauss_code_assistant_workflow as mvp
import gauss_execution_diagnostics as diagnostics_mod
import gauss_execution_interpreter as interpreter_mod
import gauss_repair_application as application_mod
import gauss_repair_application_approval as application_approval_mod
import gauss_repair_approval as repair_approval_mod
import gauss_repair_draft as repair_draft_mod
import gauss_repair_draft_approval as draft_approval_mod
import gauss_repair_planner as repair_planner_mod
import gauss_verification_execution as verification_mod
import gauss_verification_review as review_mod


#: Fixed, always-present -- never reworded per session state.
REPAIR_SESSION_SUMMARY_BOUNDARY = (
    "This is a read-only summary of evidence already produced by prior stages. It creates no new "
    "approval, executes nothing, plans nothing, repairs nothing, and mutates no prior state. Any "
    "missing stage below reflects that stage genuinely has not occurred in this session."
)


@dataclass(frozen=True)
class TimelineEntry:
    stage: str
    timestamp: str
    description: str


@dataclass(frozen=True)
class RepairSessionSummary:
    """Immutable. Every field holds a reference to an already-constructed
    object -- never a copy, never a re-derived value. `None` means that
    stage genuinely has not occurred in this session; it is never inferred
    or fabricated from a later stage's presence."""

    original_execution: "mvp.WorkflowResult | None"
    interpretation: "interpreter_mod.ExecutionInterpretation | None"
    diagnosis: "diagnostics_mod.DiagnosticAssessment | None"
    repair_plan: "repair_planner_mod.RepairPlan | None"
    strategy_approval: "repair_approval_mod.ApprovalRecord | None"
    repair_draft: "repair_draft_mod.RepairDraft | None"
    draft_approval: "draft_approval_mod.DraftApprovalRecord | None"
    application_approval: "application_approval_mod.ApplicationApprovalRecord | None"
    application_result: "application_mod.ApplicationResult | None"
    verification_request: "verification_mod.VerificationExecutionRequest | None"
    comparison_summary: "verification_mod.ComparisonSummary | None"
    verification_review: "review_mod.VerificationReview | None"
    timeline: tuple[TimelineEntry, ...]
    current_status: str
    generated_at: str
    boundary: str


def _build_timeline(
    *,
    strategy_approval: "repair_approval_mod.ApprovalRecord | None",
    repair_draft: "repair_draft_mod.RepairDraft | None",
    draft_approval: "draft_approval_mod.DraftApprovalRecord | None",
    application_approval: "application_approval_mod.ApplicationApprovalRecord | None",
    application_result: "application_mod.ApplicationResult | None",
    verification_request: "verification_mod.VerificationExecutionRequest | None",
    verification_review: "review_mod.VerificationReview | None",
) -> tuple[TimelineEntry, ...]:
    """Fixed pipeline order, never sorted by timestamp value -- timestamps
    here are opaque, caller-supplied strings (frequently identical across
    stages under a fixed test clock), so a value-sort would be unstable.
    Only stages whose object exists AND carries a genuine timestamp field
    contribute an entry; execution/interpretation/diagnosis/repair-plan
    carry no timestamp anywhere in this architecture and are never listed
    here (an existing limitation this module does not fabricate around)."""
    entries: list[TimelineEntry] = []
    if strategy_approval is not None:
        entries.append(
            TimelineEntry("strategy_approval", strategy_approval.recorded_at, f"Strategy {strategy_approval.decision}")
        )
    if repair_draft is not None:
        entries.append(TimelineEntry("repair_draft", repair_draft.generated_at, "Repair draft generated"))
    if draft_approval is not None:
        entries.append(TimelineEntry("draft_approval", draft_approval.recorded_at, f"Draft {draft_approval.decision}"))
    if application_approval is not None:
        entries.append(
            TimelineEntry("application_approval", application_approval.recorded_at, f"Application {application_approval.decision}")
        )
    if application_result is not None:
        entries.append(
            TimelineEntry("application_result", application_result.applied_at, f"Application {application_result.outcome}")
        )
    if verification_request is not None:
        entries.append(
            TimelineEntry("verification_request", verification_request.created_at, "Verification execution requested")
        )
    if verification_review is not None:
        entries.append(
            TimelineEntry("verification_review", verification_review.reviewed_at, f"Review recorded: {verification_review.decision}")
        )
    return tuple(entries)


def _determine_current_status(
    *,
    original_execution: "mvp.WorkflowResult | None",
    interpretation: "interpreter_mod.ExecutionInterpretation | None",
    diagnosis: "diagnostics_mod.DiagnosticAssessment | None",
    repair_plan: "repair_planner_mod.RepairPlan | None",
    strategy_approval: "repair_approval_mod.ApprovalRecord | None",
    repair_draft: "repair_draft_mod.RepairDraft | None",
    draft_approval: "draft_approval_mod.DraftApprovalRecord | None",
    application_approval: "application_approval_mod.ApplicationApprovalRecord | None",
    application_result: "application_mod.ApplicationResult | None",
    verification_request: "verification_mod.VerificationExecutionRequest | None",
    comparison_summary: "verification_mod.ComparisonSummary | None",
    verification_review: "review_mod.VerificationReview | None",
) -> str:
    """Pure, deterministic. Walks the pipeline from its end backward and
    returns the label of the first (i.e. furthest) populated stage found."""
    if verification_review is not None:
        return f"verification_reviewed:{verification_review.decision}"
    if comparison_summary is not None:
        return "verification_completed"
    if verification_request is not None:
        return "verification_requested"
    if application_result is not None:
        return f"application_{application_result.outcome}"
    if application_approval is not None:
        return f"application_{application_approval.decision}"
    if draft_approval is not None:
        return f"draft_{draft_approval.decision}"
    if repair_draft is not None:
        return "draft_created"
    if strategy_approval is not None:
        return f"strategy_{strategy_approval.decision}"
    if repair_plan is not None:
        return "planned"
    if diagnosis is not None:
        return "diagnosed"
    if interpretation is not None:
        return "interpreted"
    if original_execution is not None:
        return "executed"
    return "no_execution"


def build_repair_session_summary(
    *,
    original_execution: "mvp.WorkflowResult | None" = None,
    interpretation: "interpreter_mod.ExecutionInterpretation | None" = None,
    diagnosis: "diagnostics_mod.DiagnosticAssessment | None" = None,
    repair_plan: "repair_planner_mod.RepairPlan | None" = None,
    strategy_approval: "repair_approval_mod.ApprovalRecord | None" = None,
    repair_draft: "repair_draft_mod.RepairDraft | None" = None,
    draft_approval: "draft_approval_mod.DraftApprovalRecord | None" = None,
    application_approval: "application_approval_mod.ApplicationApprovalRecord | None" = None,
    application_result: "application_mod.ApplicationResult | None" = None,
    verification_request: "verification_mod.VerificationExecutionRequest | None" = None,
    comparison_summary: "verification_mod.ComparisonSummary | None" = None,
    verification_review: "review_mod.VerificationReview | None" = None,
    generated_at: str,
) -> RepairSessionSummary:
    """The single sanctioned constructor. Every domain parameter defaults to
    `None` -- a session need not have reached every stage. `generated_at` is
    required and caller-supplied, matching every other layer's own
    clock-injection convention. Performs no I/O, no mutation, and
    constructs no object other than the summary and its own timeline."""
    timeline = _build_timeline(
        strategy_approval=strategy_approval,
        repair_draft=repair_draft,
        draft_approval=draft_approval,
        application_approval=application_approval,
        application_result=application_result,
        verification_request=verification_request,
        verification_review=verification_review,
    )
    current_status = _determine_current_status(
        original_execution=original_execution,
        interpretation=interpretation,
        diagnosis=diagnosis,
        repair_plan=repair_plan,
        strategy_approval=strategy_approval,
        repair_draft=repair_draft,
        draft_approval=draft_approval,
        application_approval=application_approval,
        application_result=application_result,
        verification_request=verification_request,
        comparison_summary=comparison_summary,
        verification_review=verification_review,
    )
    return RepairSessionSummary(
        original_execution=original_execution,
        interpretation=interpretation,
        diagnosis=diagnosis,
        repair_plan=repair_plan,
        strategy_approval=strategy_approval,
        repair_draft=repair_draft,
        draft_approval=draft_approval,
        application_approval=application_approval,
        application_result=application_result,
        verification_request=verification_request,
        comparison_summary=comparison_summary,
        verification_review=verification_review,
        timeline=timeline,
        current_status=current_status,
        generated_at=generated_at,
        boundary=REPAIR_SESSION_SUMMARY_BOUNDARY,
    )
