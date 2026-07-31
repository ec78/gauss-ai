"""Deterministic, evidence-bound diagnostic reasoning over GAUSS execution
results.

Position in the reasoning pipeline:

    Execution evidence -> Interpretation -> Verified error knowledge -> Diagnosis -> (Repair, future, not implemented)

This module answers "what verified causes might explain this, what evidence
is still missing, and what should be inspected next" -- it never answers
"what exact code should replace the current code." See
`docs/gauss-diagnostic-reasoning.md` for the full boundary statement.

Pure and deterministic. This module never launches GAUSS, calls an execution
helper, mutates workspace state, edits source code, reads output files,
accesses the network, calls an LLM, performs a retry, constructs a repair,
or writes a new request/plan -- it has no import, and no code path, capable
of any of those things. It consumes only a `gauss_execution_interpreter.
ExecutionEvidence` object (the same one `interpret_execution(...)` consumes)
and, internally, that same function -- so evidence classification is never
duplicated or re-derived a second, possibly-inconsistent way.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import gauss_error_catalog as catalog
import gauss_execution_interpreter as interp


class DiagnosticConfidence(enum.Enum):
    """A deliberately small, bounded scale. Never "certain"/"guaranteed"/
    "proven" -- confidence reflects the strength of available evidence, not
    the severity of the error or the plausibility of a cause. A cataloged
    error code can support HIGH confidence about *what category* of problem
    was reported while every specific *cause* within that category still
    stays at LOW, since this engine has no source-code-content, variable-
    value, or matrix-shape evidence to distinguish between them."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class DiagnosticStatus(enum.Enum):
    NO_FAILURE_DETECTED = "no_failure_detected"
    DIAGNOSED = "diagnosed"
    UNKNOWN_ERROR = "unknown_error"
    TIMEOUT = "timeout"
    NOT_AVAILABLE = "not_available"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


#: A fixed, always-present disclosure -- never conditional, never reworded
#: per branch, so it cannot be accidentally omitted from any assessment.
REPAIR_BOUNDARY_STATEMENT = "Diagnosis does not modify or repair the program."

_BASE_LIMITATIONS: tuple[str, ...] = (
    "Diagnosis is bounded to this repository's verified GAUSS error catalog; it does not reason from "
    "general programming knowledge or infer beyond the supplied evidence.",
    "A cause's confidence reflects the strength of available evidence, not the severity of the error.",
)


@dataclass(frozen=True)
class DiagnosticCause:
    cause_id: str
    title: str
    description: str
    #: One of `DiagnosticConfidence`'s values. Every catalog-derived cause in
    #: this module is `low` -- see `DiagnosticConfidence`'s own docstring.
    confidence: str
    supporting_evidence: tuple[str, ...]
    #: What additional evidence would be needed to raise this cause's own
    #: confidence -- never a promise that this repository can currently
    #: collect that evidence automatically.
    required_evidence: tuple[str, ...]
    verification_source: str
    is_catalog_verified: bool


@dataclass(frozen=True)
class DiagnosticAssessment:
    diagnostic_status: str
    confidence: str
    summary: str
    possible_causes: tuple[DiagnosticCause, ...]
    #: Known facts, directly supported by the interpretation/evidence.
    supporting_evidence: tuple[str, ...]
    #: Reserved for a future evidence source capable of detecting an actual
    #: internal contradiction (e.g. two evidence fields disagreeing about
    #: the same fact) -- always empty in this version, since nothing this
    #: engine currently consumes can produce that signal. Present as a
    #: field, not silently omitted, so a future addition needs no schema
    #: change and a test can assert today's honest absence.
    contradicting_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    questions_to_ask: tuple[str, ...]
    recommended_diagnostic_steps: tuple[str, ...]
    limitations: tuple[str, ...]
    repair_boundary: str
    safe_to_continue: bool
    requires_user_input: bool
    source_error_code: str | None
    source_error_category: str | None
    #: `VerificationStatus` values (as strings) from the matched catalog
    #: entry, if any -- empty when no cataloged entry was matched.
    knowledge_verification: tuple[str, ...]


def _causes_from_entry(entry: "catalog.GaussErrorCatalogEntry") -> tuple[DiagnosticCause, ...]:
    """Every catalog-derived cause starts at LOW confidence -- deliberately
    uniform, since none of `known_triggers` is distinguishable from the
    others without source-code-content evidence this engine does not have.
    This keeps ranking simple, explainable, and free of opaque scoring."""
    return tuple(
        DiagnosticCause(
            cause_id=f"{entry.error_code}_cause_{index + 1}",
            title=trigger,
            description=trigger,
            confidence=DiagnosticConfidence.LOW.value,
            supporting_evidence=(),
            required_evidence=entry.required_evidence_for_diagnosis,
            verification_source=entry.verification_source,
            is_catalog_verified=True,
        )
        for index, trigger in enumerate(entry.known_triggers)
    )


def diagnose_execution(evidence: "interp.ExecutionEvidence") -> DiagnosticAssessment:
    """The single entry point. Internally calls `interpret_execution(evidence)`
    -- the same pure classification `interpret` already uses -- rather than
    re-deriving `execution_phase`/`failure_type`/etc. a second, possibly
    divergent way."""
    interpretation = interp.interpret_execution(evidence)
    limitations = list(_BASE_LIMITATIONS)

    if interpretation.execution_phase == "completed":
        return DiagnosticAssessment(
            diagnostic_status=DiagnosticStatus.NO_FAILURE_DETECTED.value,
            confidence=interpretation.confidence,
            summary="Execution completed with no detected error; there is nothing to diagnose.",
            possible_causes=(),
            supporting_evidence=(
                interpretation.user_explanation,
                f"launch_status: {interpretation.launch_status}",
            ),
            contradicting_evidence=(),
            missing_evidence=(),
            questions_to_ask=(),
            recommended_diagnostic_steps=(),
            limitations=tuple(
                limitations + ["A completed execution does not establish statistical or methodological correctness."]
            ),
            repair_boundary=REPAIR_BOUNDARY_STATEMENT,
            safe_to_continue=True,
            requires_user_input=False,
            source_error_code=None,
            source_error_category=None,
            knowledge_verification=(),
        )

    if interpretation.execution_phase == "pre_launch":
        return DiagnosticAssessment(
            diagnostic_status=DiagnosticStatus.NOT_AVAILABLE.value,
            confidence=DiagnosticConfidence.INSUFFICIENT_EVIDENCE.value,
            summary="Diagnosis is unavailable because no execution has launched or completed yet.",
            possible_causes=(),
            supporting_evidence=(),
            contradicting_evidence=(),
            missing_evidence=("a completed or failed execution attempt (run 'execute' first)",),
            questions_to_ask=(),
            recommended_diagnostic_steps=(
                "Review the prior planning, confirmation, runner-configuration, or workspace-state message.",
            ),
            limitations=tuple(limitations),
            repair_boundary=REPAIR_BOUNDARY_STATEMENT,
            safe_to_continue=False,
            requires_user_input=True,
            source_error_code=None,
            source_error_category=None,
            knowledge_verification=(),
        )

    if interpretation.execution_phase == "timeout":
        return DiagnosticAssessment(
            diagnostic_status=DiagnosticStatus.TIMEOUT.value,
            confidence=DiagnosticConfidence.INSUFFICIENT_EVIDENCE.value,
            summary=(
                "Execution timed out. This repository has no verified catalog knowledge about why GAUSS runs "
                "time out, so no specific cause is asserted."
            ),
            possible_causes=(),
            supporting_evidence=(interpretation.user_explanation,),
            contradicting_evidence=(),
            missing_evidence=("partial stdout/stderr output", "the generated GAUSS script"),
            questions_to_ask=(
                "Was this a real GAUSS launch, or simulated/injected timeout evidence?",
                "Does the script involve a loop, large data, or an operation expected to take longer than the "
                "configured timeout?",
            ),
            recommended_diagnostic_steps=(
                "Inspect stdout and stderr for partial output.",
                "Review the generated GAUSS script for unbounded loops or large data operations.",
            ),
            limitations=tuple(limitations + ["No automatic retry or timeout adjustment is performed by this diagnosis."]),
            repair_boundary=REPAIR_BOUNDARY_STATEMENT,
            safe_to_continue=False,
            requires_user_input=True,
            source_error_code=None,
            source_error_category=catalog.GaussErrorCategory.TIMEOUT.value,
            knowledge_verification=(),
        )

    entry = catalog.lookup_error(interpretation.error_code) if interpretation.error_code else None

    if entry is not None:
        causes = _causes_from_entry(entry)
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
        return DiagnosticAssessment(
            diagnostic_status=DiagnosticStatus.DIAGNOSED.value,
            confidence=(DiagnosticConfidence.LOW.value if causes else DiagnosticConfidence.INSUFFICIENT_EVIDENCE.value),
            summary=(
                f"GAUSS reported {entry.title} ({entry.error_code}). "
                f"{len(causes)} known, catalog-verified possible cause(s) are listed below; none is confirmed."
            ),
            possible_causes=causes,
            supporting_evidence=(interpretation.user_explanation, interpretation.technical_explanation),
            contradicting_evidence=(),
            missing_evidence=entry.required_evidence_for_diagnosis,
            questions_to_ask=entry.diagnostic_questions,
            recommended_diagnostic_steps=(entry.recommended_next_step,),
            limitations=tuple(entry_limitations),
            repair_boundary=REPAIR_BOUNDARY_STATEMENT,
            safe_to_continue=False,
            requires_user_input=bool(entry.diagnostic_questions),
            source_error_code=entry.error_code,
            source_error_category=entry.category.value,
            knowledge_verification=tuple(status.value for status in entry.verification_status),
        )

    if interpretation.error_code is not None:
        return DiagnosticAssessment(
            diagnostic_status=DiagnosticStatus.UNKNOWN_ERROR.value,
            confidence=DiagnosticConfidence.INSUFFICIENT_EVIDENCE.value,
            summary=(
                f"GAUSS reported an uncataloged error code ({interpretation.error_code}); no verified "
                "specialized diagnosis exists for it."
            ),
            possible_causes=(),
            supporting_evidence=(interpretation.technical_explanation,),
            contradicting_evidence=(),
            missing_evidence=(
                "independent verification of this error code (real runtime reproduction or official documentation)",
            ),
            questions_to_ask=(),
            recommended_diagnostic_steps=(
                "Inspect stderr for the full diagnostic text.",
                "Consider adding this code to the catalog only after independent verification.",
            ),
            limitations=tuple(
                limitations + ["This error code is not yet in the verified catalog; no cause is asserted for it."]
            ),
            repair_boundary=REPAIR_BOUNDARY_STATEMENT,
            safe_to_continue=False,
            requires_user_input=False,
            source_error_code=interpretation.error_code,
            source_error_category=catalog.GaussErrorCategory.UNKNOWN.value,
            knowledge_verification=(),
        )

    return DiagnosticAssessment(
        diagnostic_status=DiagnosticStatus.INSUFFICIENT_EVIDENCE.value,
        confidence=DiagnosticConfidence.INSUFFICIENT_EVIDENCE.value,
        summary=(
            "Execution did not complete successfully, and the supplied evidence is insufficient to diagnose a "
            "specific cause."
        ),
        possible_causes=(),
        supporting_evidence=(),
        contradicting_evidence=(),
        missing_evidence=tuple(interpretation.evidence_limitations) or ("captured stdout and/or stderr text",),
        questions_to_ask=(),
        recommended_diagnostic_steps=("Inspect stdout and stderr explicitly, then review the generated GAUSS script.",),
        limitations=tuple(limitations),
        repair_boundary=REPAIR_BOUNDARY_STATEMENT,
        safe_to_continue=False,
        requires_user_input=True,
        source_error_code=None,
        source_error_category=catalog.GaussErrorCategory.UNKNOWN.value,
        knowledge_verification=(),
    )
