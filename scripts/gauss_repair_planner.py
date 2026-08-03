"""Deterministic, evidence-bound repair-planning reasoning over GAUSS
execution results.

Position in the reasoning pipeline:

    Execution evidence -> Interpretation -> Verified error knowledge
        -> Diagnosis -> Repair Planning (this module)
        -> (Repair Application, future, not implemented)

This module answers "what bounded repair strategy should be considered, what
evidence and approval are needed before drafting or applying a change, and
how should a future repair be verified" -- it never answers "here is the
exact code to apply." See `docs/gauss-repair-planning.md` for the full
boundary statement.

Pure and deterministic. This module never launches GAUSS, calls an execution
helper, mutates workspace state, edits source code, reads or writes files,
accesses the network, calls an LLM, performs a retry, applies a patch, or
constructs a new execution proposal -- it has no import, and no code path,
capable of any of those things. It consumes only a
`gauss_execution_interpreter.ExecutionEvidence` object and an optional
`SourceContext` explicitly supplied by the caller; internally it reuses
`gauss_execution_interpreter.interpret_execution(...)` and
`gauss_execution_diagnostics.diagnose_execution(...)` -- the same pure
functions `interpret`/`diagnose` already use -- so evidence classification
and diagnostic reasoning are never duplicated or re-derived a second,
possibly-inconsistent way.

Confidence reuses `gauss_execution_diagnostics.DiagnosticConfidence` directly
rather than defining a parallel scale, per this project's own guidance to
avoid duplicating existing models.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import gauss_error_catalog as catalog
import gauss_execution_diagnostics as diag
import gauss_execution_interpreter as interp

#: Reused, not duplicated -- see module docstring.
RepairConfidence = diag.DiagnosticConfidence


class RepairStatus(enum.Enum):
    SUCCESSFUL_EXECUTION_NO_REPAIR_NEEDED = "successful_execution_no_repair_needed"
    NOT_APPLICABLE = "not_applicable"
    #: A real GAUSS launch was observed exceeding its configured timeout, or
    #: simulated/injected timeout evidence was supplied. Generic, code-
    #: independent inspection guidance only -- no catalog entry exists for
    #: "timeout" (it is not a GAUSS error code).
    TIMEOUT = "timeout"
    STRATEGY_AVAILABLE = "strategy_available"
    #: Explicit source context was supplied and is relevant to this error
    #: code's own repair preconditions -- narrower than STRATEGY_AVAILABLE,
    #: but still never a concrete edit or applied repair this milestone.
    DRAFT_POSSIBLE_WITH_MORE_CONTEXT = "draft_possible_with_more_context"
    #: A cataloged entry was matched, but it has no authored repair
    #: knowledge yet (`repair_strategies` empty) -- structurally supported,
    #: not expected to fire for any of the 11 codes cataloged as of v0.56.0.
    BLOCKED_BY_MISSING_SOURCE = "blocked_by_missing_source"
    UNKNOWN_ERROR = "unknown_error"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


#: A fixed, always-present disclosure -- never conditional, never reworded
#: per branch, so it cannot be accidentally omitted from any plan. Folds in
#: every disclosure this milestone's CLI integration requires.
REPAIR_BOUNDARY_STATEMENT = (
    "This is a repair plan, not an applied repair. No code was modified. GAUSS was not rerun. "
    "User approval would be required before any future repair application."
)

_BASE_LIMITATIONS: tuple[str, ...] = (
    "Repair planning is bounded to this repository's verified GAUSS error catalog and any source context "
    "explicitly supplied by the caller; it does not infer or reconstruct source code that was not provided.",
    "A repair strategy's confidence reflects the strength of available evidence, not a guarantee the strategy "
    "will resolve the error.",
)

#: A generic, code-independent risk appended to every catalog-derived plan --
#: never a claim about a specific fix, since no specific fix is ever proposed.
_GENERIC_REPAIR_RISK = (
    "Any code change carries some risk of introducing a different defect; this repository does not verify "
    "that risk automatically."
)

#: Generic, code-independent timeout guidance. Not catalog-derived (there is
#: no GAUSS error code for a timeout) -- see `gauss_execution_interpreter`'s
#: own timeout branch for why this is an interpreter/repair-level
#: classification, not a cataloged error.
_TIMEOUT_STRATEGY = (
    "Inspect runtime behavior, input size, convergence criteria, loop bounds, and environment factors that "
    "could explain the elapsed time before considering whether to rerun with a longer timeout."
)

#: Which `SourceContext` fields are considered relevant evidence for each
#: error category -- used only to decide whether supplied context narrows a
#: plan toward `DRAFT_POSSIBLE_WITH_MORE_CONTEXT`. A deliberately simple,
#: explainable lookup table, not an opaque scoring function.
_CATEGORY_RELEVANT_CONTEXT_FIELDS: dict[catalog.GaussErrorCategory, tuple[str, ...]] = {
    catalog.GaussErrorCategory.PARSE_SYNTAX: ("code_text",),
    catalog.GaussErrorCategory.MATRIX_DIMENSION: ("matrix_shapes", "code_text"),
    catalog.GaussErrorCategory.RUNTIME_COMPUTATION: ("code_text", "procedure_name"),
    catalog.GaussErrorCategory.FILE_IO: ("referenced_paths",),
    catalog.GaussErrorCategory.PACKAGE_OR_LIBRARY: ("referenced_paths", "procedure_name"),
    catalog.GaussErrorCategory.INDEXING_SUBSCRIPT: ("matrix_shapes", "code_text"),
    catalog.GaussErrorCategory.ARGUMENT_VALIDATION: ("procedure_name", "argument_summary"),
    catalog.GaussErrorCategory.TYPE_MISMATCH: ("code_text", "argument_summary"),
    catalog.GaussErrorCategory.NUMERICAL: ("matrix_shapes", "code_text"),
}


@dataclass(frozen=True)
class SourceContext:
    """Explicitly supplied source context only -- never populated by reading
    a file, inferring omitted code, or reconstructing anything the caller
    did not directly provide. Every field is optional; an empty
    `SourceContext` behaves identically to `source_context=None`."""

    code_text: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    matrix_shapes: tuple[str, ...] = ()
    referenced_paths: tuple[str, ...] = ()
    procedure_name: str | None = None
    argument_summary: str | None = None

    def is_empty(self) -> bool:
        return not (
            self.code_text
            or self.line_start is not None
            or self.line_end is not None
            or self.matrix_shapes
            or self.referenced_paths
            or self.procedure_name
            or self.argument_summary
        )


@dataclass(frozen=True)
class RepairAction:
    action_id: str
    #: Always an inspection/verification/clarification action -- never
    #: "edit" or "apply". Enforced by `test_no_edit_or_apply_action_types`.
    action_type: str
    description: str
    #: A descriptive area of attention (e.g. "matrix operand dimensions") --
    #: never a literal file path or line number unless the caller supplied
    #: one in `SourceContext`.
    target: str | None
    preconditions: tuple[str, ...]
    evidence_basis: str
    #: One of `RepairConfidence`'s values.
    confidence: str
    #: Always `False` in this milestone -- see module docstring.
    is_concrete_edit: bool
    requires_source_context: bool
    requires_user_approval: bool


@dataclass(frozen=True)
class RepairPlan:
    repair_status: str
    confidence: str
    summary: str
    #: Short label for the top-ranked strategy, or `None` if none applies.
    repair_strategy: str | None
    #: Ranked, top-first. Empty when no strategy applies.
    proposed_actions: tuple[RepairAction, ...]
    #: A descriptive area of attention; never a literal path/line unless the
    #: caller supplied one in `SourceContext`.
    target_scope: str | None
    source_context_used: bool
    supporting_evidence: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    risks: tuple[str, ...]
    verification_steps: tuple[str, ...]
    #: Reused directly from the diagnostic assessment's own
    #: `questions_to_ask` -- never re-derived a second way.
    questions_to_answer: tuple[str, ...]
    requires_user_input: bool
    requires_explicit_approval: bool
    #: Always `False` in this milestone -- no draft-generation capability
    #: exists yet, structurally, regardless of source context supplied.
    safe_to_prepare_draft: bool
    #: Always `False` -- this milestone implements planning only. Checked
    #: structurally by `test_safe_to_apply_always_false`.
    safe_to_apply: bool
    repair_boundary: str
    source_error_code: str | None
    source_error_category: str | None
    #: `VerificationStatus` values (as strings) from the matched catalog
    #: entry, if any -- empty when no cataloged entry was matched.
    knowledge_verification: tuple[str, ...]


def _context_relevant(entry: "catalog.GaussErrorCatalogEntry", source_context: SourceContext | None) -> bool:
    if source_context is None or source_context.is_empty():
        return False
    relevant_fields = _CATEGORY_RELEVANT_CONTEXT_FIELDS.get(entry.category, ())
    for field_name in relevant_fields:
        value = getattr(source_context, field_name)
        if value:
            return True
    return False


def _actions_from_entry(
    entry: "catalog.GaussErrorCatalogEntry", *, context_relevant: bool
) -> tuple[RepairAction, ...]:
    """Ranking note: every entry currently authors exactly one strategy, so
    declaration order is the only order -- this function still exists as a
    real, documented ranking point (not a no-op) so a future entry with more
    than one strategy has a place to rank without ambiguity. Nothing here
    ranks a strategy higher merely because it is common; ranking would be
    driven by precondition/context relevance once more than one strategy
    exists for a single code."""
    return tuple(
        RepairAction(
            action_id=f"{entry.error_code}_action_{index + 1}",
            action_type="inspect",
            description=strategy,
            target="; ".join(entry.repair_preconditions) or None,
            preconditions=entry.repair_preconditions,
            evidence_basis=entry.verification_source,
            confidence=RepairConfidence.LOW.value,
            is_concrete_edit=False,
            requires_source_context=bool(entry.repair_preconditions) and not context_relevant,
            requires_user_approval=True,
        )
        for index, strategy in enumerate(entry.repair_strategies)
    )


def plan_repair(
    evidence: "interp.ExecutionEvidence", source_context: SourceContext | None = None
) -> RepairPlan:
    """The single entry point. Internally calls `interpret_execution(evidence)`
    and `diagnose_execution(evidence)` -- the same pure functions `interpret`
    and `diagnose` already use -- rather than re-deriving classification or
    diagnostic reasoning a second, possibly divergent way."""
    interpretation = interp.interpret_execution(evidence)
    diagnosis = diag.diagnose_execution(evidence)
    limitations = list(_BASE_LIMITATIONS)
    context_used = source_context is not None and not source_context.is_empty()

    if interpretation.execution_phase == "completed":
        return RepairPlan(
            repair_status=RepairStatus.SUCCESSFUL_EXECUTION_NO_REPAIR_NEEDED.value,
            confidence=interpretation.confidence,
            summary="Execution completed with no detected error; there is nothing to repair.",
            repair_strategy=None,
            proposed_actions=(),
            target_scope=None,
            source_context_used=context_used,
            supporting_evidence=(interpretation.user_explanation,),
            assumptions=(),
            missing_evidence=(),
            risks=(),
            verification_steps=(),
            questions_to_answer=(),
            requires_user_input=False,
            requires_explicit_approval=False,
            safe_to_prepare_draft=False,
            safe_to_apply=False,
            repair_boundary=REPAIR_BOUNDARY_STATEMENT,
            source_error_code=None,
            source_error_category=None,
            knowledge_verification=(),
        )

    if interpretation.execution_phase == "pre_launch":
        return RepairPlan(
            repair_status=RepairStatus.NOT_APPLICABLE.value,
            confidence=RepairConfidence.INSUFFICIENT_EVIDENCE.value,
            summary="Repair planning is unavailable because no execution has launched or completed yet.",
            repair_strategy=None,
            proposed_actions=(),
            target_scope=None,
            source_context_used=context_used,
            supporting_evidence=(),
            assumptions=(),
            missing_evidence=("a completed or failed execution attempt (run 'execute' first)",),
            risks=(),
            verification_steps=(),
            questions_to_answer=(),
            requires_user_input=True,
            requires_explicit_approval=False,
            safe_to_prepare_draft=False,
            safe_to_apply=False,
            repair_boundary=REPAIR_BOUNDARY_STATEMENT,
            source_error_code=None,
            source_error_category=None,
            knowledge_verification=(),
        )

    if interpretation.execution_phase == "timeout":
        return RepairPlan(
            repair_status=RepairStatus.TIMEOUT.value,
            confidence=RepairConfidence.INSUFFICIENT_EVIDENCE.value,
            summary=(
                "Execution timed out. This repository has no verified catalog knowledge about why GAUSS runs "
                "time out, so only generic, code-independent inspection guidance is offered."
            ),
            repair_strategy=_TIMEOUT_STRATEGY,
            proposed_actions=(
                RepairAction(
                    action_id="timeout_action_1",
                    action_type="inspect",
                    description=_TIMEOUT_STRATEGY,
                    target=None,
                    preconditions=(),
                    evidence_basis=interpretation.technical_explanation,
                    confidence=RepairConfidence.INSUFFICIENT_EVIDENCE.value,
                    is_concrete_edit=False,
                    requires_source_context=False,
                    requires_user_approval=False,
                ),
            ),
            target_scope=None,
            source_context_used=context_used,
            supporting_evidence=(interpretation.user_explanation,),
            assumptions=(),
            missing_evidence=(
                "partial stdout/stderr output",
                "the generated GAUSS script",
                "whether this was an observed real timeout or simulated/injected timeout evidence",
            ),
            risks=(
                "This repository does not verify whether the script contains an infinite loop, an expensive "
                "computation, or a genuinely long-running valid operation -- do not assume any of these without "
                "inspection.",
            ),
            verification_steps=(
                "If the timeout is addressed by increasing the configured timeout, confirm the script still "
                "completes and produces the expected result rather than simply running longer before failing "
                "differently.",
            ),
            questions_to_answer=diagnosis.questions_to_ask,
            requires_user_input=True,
            requires_explicit_approval=False,
            safe_to_prepare_draft=False,
            safe_to_apply=False,
            repair_boundary=REPAIR_BOUNDARY_STATEMENT,
            source_error_code=None,
            source_error_category=catalog.GaussErrorCategory.TIMEOUT.value,
            knowledge_verification=(),
        )

    entry = catalog.lookup_error(interpretation.error_code) if interpretation.error_code else None

    if entry is not None:
        context_relevant = _context_relevant(entry, source_context)
        actions = _actions_from_entry(entry, context_relevant=context_relevant)
        entry_limitations = list(limitations)
        if entry.documentation_discrepancy:
            entry_limitations.append(
                f"Documentation/runtime discrepancy on record for {entry.error_code}: {entry.documentation_discrepancy}"
            )
        if catalog.VerificationStatus.REAL_RUNTIME not in entry.verification_status:
            entry_limitations.append(
                f"{entry.error_code}'s meaning is verified only against official documentation, not yet "
                "reproduced against a real GAUSS runtime in this repository."
            )

        if not actions:
            return RepairPlan(
                repair_status=RepairStatus.BLOCKED_BY_MISSING_SOURCE.value,
                confidence=RepairConfidence.INSUFFICIENT_EVIDENCE.value,
                summary=(
                    f"GAUSS reported {entry.title} ({entry.error_code}), but no repair guidance has been "
                    "authored for this code yet."
                ),
                repair_strategy=None,
                proposed_actions=(),
                target_scope=None,
                source_context_used=context_used,
                supporting_evidence=(interpretation.user_explanation, interpretation.technical_explanation),
                assumptions=(),
                missing_evidence=entry.repair_preconditions
                or ("verified repair-planning knowledge for this error code (not yet authored)",),
                risks=(),
                verification_steps=(),
                questions_to_answer=diagnosis.questions_to_ask,
                requires_user_input=True,
                requires_explicit_approval=False,
                safe_to_prepare_draft=False,
                safe_to_apply=False,
                repair_boundary=REPAIR_BOUNDARY_STATEMENT,
                source_error_code=entry.error_code,
                source_error_category=entry.category.value,
                knowledge_verification=tuple(status.value for status in entry.verification_status),
            )

        status = (
            RepairStatus.DRAFT_POSSIBLE_WITH_MORE_CONTEXT if context_relevant else RepairStatus.STRATEGY_AVAILABLE
        )
        missing = () if context_relevant else entry.repair_preconditions
        risks = tuple(entry.repair_risks) + (_GENERIC_REPAIR_RISK,)
        summary = (
            f"GAUSS reported {entry.title} ({entry.error_code}). "
            f"{len(actions)} catalog-verified inspection strategy(ies) are proposed below; none is applied "
            "or guaranteed to resolve the error."
        )
        if context_relevant:
            summary += " Supplied source context was used to sharpen the plan; no code was generated or applied."
        return RepairPlan(
            repair_status=status.value,
            confidence=RepairConfidence.LOW.value,
            summary=summary,
            repair_strategy=actions[0].description,
            proposed_actions=actions,
            target_scope=actions[0].target,
            source_context_used=context_used,
            supporting_evidence=(interpretation.user_explanation, interpretation.technical_explanation),
            assumptions=(
                "The reported error code accurately reflects the failure GAUSS encountered.",
                "No other undiagnosed error exists earlier in execution that would also need attention.",
            ),
            missing_evidence=missing,
            risks=risks,
            verification_steps=entry.repair_verification_steps,
            questions_to_answer=diagnosis.questions_to_ask,
            requires_user_input=bool(missing) or bool(diagnosis.questions_to_ask),
            requires_explicit_approval=True,
            safe_to_prepare_draft=False,
            safe_to_apply=False,
            repair_boundary=REPAIR_BOUNDARY_STATEMENT,
            source_error_code=entry.error_code,
            source_error_category=entry.category.value,
            knowledge_verification=tuple(status.value for status in entry.verification_status),
        )

    if interpretation.error_code is not None:
        return RepairPlan(
            repair_status=RepairStatus.UNKNOWN_ERROR.value,
            confidence=RepairConfidence.INSUFFICIENT_EVIDENCE.value,
            summary=(
                f"GAUSS reported an uncataloged error code ({interpretation.error_code}); no verified repair "
                "strategy exists for it."
            ),
            repair_strategy=None,
            proposed_actions=(),
            target_scope=None,
            source_context_used=context_used,
            supporting_evidence=(interpretation.technical_explanation,),
            assumptions=(),
            missing_evidence=(
                "independent verification of this error code (real runtime reproduction or official documentation)",
            ),
            risks=(),
            verification_steps=(),
            questions_to_answer=(),
            requires_user_input=False,
            requires_explicit_approval=False,
            safe_to_prepare_draft=False,
            safe_to_apply=False,
            repair_boundary=REPAIR_BOUNDARY_STATEMENT,
            source_error_code=interpretation.error_code,
            source_error_category=catalog.GaussErrorCategory.UNKNOWN.value,
            knowledge_verification=(),
        )

    return RepairPlan(
        repair_status=RepairStatus.INSUFFICIENT_EVIDENCE.value,
        confidence=RepairConfidence.INSUFFICIENT_EVIDENCE.value,
        summary=(
            "Execution did not complete successfully, and the supplied evidence is insufficient to plan a "
            "specific repair strategy."
        ),
        repair_strategy=None,
        proposed_actions=(),
        target_scope=None,
        source_context_used=context_used,
        supporting_evidence=(),
        assumptions=(),
        missing_evidence=tuple(interpretation.evidence_limitations) or ("captured stdout and/or stderr text",),
        risks=(),
        verification_steps=(),
        questions_to_answer=(),
        requires_user_input=True,
        requires_explicit_approval=False,
        safe_to_prepare_draft=False,
        safe_to_apply=False,
        repair_boundary=REPAIR_BOUNDARY_STATEMENT,
        source_error_code=None,
        source_error_category=catalog.GaussErrorCategory.UNKNOWN.value,
        knowledge_verification=(),
    )
