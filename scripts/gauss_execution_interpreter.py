"""Evidence-only interpretation of GAUSS execution results.

This module never launches GAUSS, edits code, retries execution, or reads
workspace files. It turns already-captured execution metadata and optionally
supplied stdout/stderr text into a deterministic explanation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import gauss_error_catalog as catalog


_ERROR_RE = re.compile(r"error\s+(G\d{4})\s*:?\s*([^\r\n]*)", re.IGNORECASE)


@dataclass(frozen=True)
class ExecutionEvidence:
    runner: str | None
    gauss_ran: bool
    executed: bool
    execution_status: str | None
    exit_code: int | None
    stdout_chars: int | None = None
    stderr_chars: int | None = None
    timed_out: bool = False
    workspace_state: str | None = None
    provenance: Any | None = None
    stdout_text: str | None = None
    stderr_text: str | None = None
    metadata_error: str | None = None


@dataclass(frozen=True)
class ExecutionInterpretation:
    execution_phase: str
    launch_status: str
    completion_status: str
    failure_type: str | None
    confidence: str
    summary: str
    user_explanation: str
    technical_explanation: str
    likely_location: str | None
    next_step: str
    requires_user_action: bool
    safe_to_continue: bool
    error_code: str | None = None
    error_category: str | None = None
    evidence_limitations: tuple[str, ...] = ()


def _find_gauss_error(stdout_text: str | None, stderr_text: str | None) -> tuple[str | None, str | None]:
    for text in (stderr_text or "", stdout_text or ""):
        match = _ERROR_RE.search(text)
        if match:
            return catalog.normalize_error_code(match.group(1)), match.group(2).strip() or None
    return None, None


def _base_limitations(evidence: ExecutionEvidence) -> list[str]:
    limitations: list[str] = []
    if evidence.stdout_text is None:
        limitations.append("stdout text was not supplied; only stdout metadata is available.")
    if evidence.stderr_text is None:
        limitations.append("stderr text was not supplied; only stderr metadata is available.")
    if evidence.exit_code == 0 and evidence.execution_status in {"failed", "timed_out"}:
        limitations.append("exit code is not authoritative for GAUSS failure classification.")
    return limitations


def interpret_execution(evidence: ExecutionEvidence) -> ExecutionInterpretation:
    limitations = _base_limitations(evidence)
    runner = evidence.runner or "unknown"

    if evidence.timed_out or evidence.execution_status == "timed_out":
        return ExecutionInterpretation(
            execution_phase="timeout",
            launch_status="launched" if evidence.gauss_ran else "launch_unknown",
            completion_status="timed_out",
            failure_type=catalog.GaussErrorCategory.TIMEOUT.value,
            confidence="high" if evidence.executed else "medium",
            summary="Execution timed out before a completed result was available.",
            user_explanation="GAUSS execution did not complete within the configured timeout.",
            technical_explanation=(
                f"Runner {runner!r} reported execution_status='timed_out'. No retry was attempted."
            ),
            likely_location=None,
            next_step="Inspect stdout and stderr for partial output, then review the generated GAUSS script.",
            requires_user_action=True,
            safe_to_continue=False,
            error_category=catalog.GaussErrorCategory.TIMEOUT.value,
            evidence_limitations=tuple(limitations),
        )

    if not evidence.executed or evidence.execution_status in {None, "blocked", "skipped"}:
        reason = evidence.metadata_error or evidence.execution_status or "no execution result is available"
        return ExecutionInterpretation(
            execution_phase="pre_launch",
            launch_status="blocked_before_launch" if not evidence.gauss_ran else "launch_ambiguous",
            completion_status="not_completed",
            failure_type="blocked_before_launch",
            confidence="high" if not evidence.gauss_ran else "low",
            summary="Execution did not launch.",
            user_explanation=f"Interpretation is limited because {reason}.",
            technical_explanation=(
                f"Runner {runner!r} has executed={evidence.executed}, gauss_ran={evidence.gauss_ran}, "
                f"execution_status={evidence.execution_status!r}."
            ),
            likely_location=None,
            next_step="Review the prior planning, confirmation, runner-configuration, or workspace-state message.",
            requires_user_action=True,
            safe_to_continue=False,
            evidence_limitations=tuple(limitations),
        )

    error_code, diagnostic_text = _find_gauss_error(evidence.stdout_text, evidence.stderr_text)
    entry = catalog.lookup_error(error_code) if error_code is not None else None

    if evidence.execution_status == "completed" and error_code is None:
        return ExecutionInterpretation(
            execution_phase="completed",
            launch_status="launched" if evidence.gauss_ran else "fake_or_non_gauss_runner",
            completion_status="completed",
            failure_type=None,
            confidence="high" if evidence.gauss_ran or runner.upper() == "FAKE" else "medium",
            summary="Execution completed successfully.",
            user_explanation="No execution errors were detected in the supplied execution evidence.",
            technical_explanation=(
                f"Runner {runner!r} reported execution_status='completed' with exit_code={evidence.exit_code!r}."
            ),
            likely_location=None,
            next_step="Inspect stdout, output metadata, or explicitly requested output files if you need details.",
            requires_user_action=False,
            safe_to_continue=True,
            evidence_limitations=tuple(limitations),
        )

    if entry is not None:
        return ExecutionInterpretation(
            execution_phase=entry.execution_phase,
            launch_status="launched" if evidence.gauss_ran else "fake_or_non_gauss_runner",
            completion_status="failed",
            failure_type=entry.category.value,
            confidence=entry.confidence,
            summary=f"GAUSS reported {entry.title}.",
            user_explanation=entry.generic_explanation,
            technical_explanation=(
                f"Detected cataloged GAUSS error {entry.error_code}"
                + (f" with diagnostic text: {diagnostic_text}" if diagnostic_text else ".")
            ),
            likely_location="GAUSS diagnostic stream",
            next_step=entry.recommended_next_step,
            requires_user_action=True,
            safe_to_continue=False,
            error_code=entry.error_code,
            error_category=entry.category.value,
            evidence_limitations=tuple(limitations),
        )

    if error_code is not None:
        return ExecutionInterpretation(
            execution_phase="unknown",
            launch_status="launched" if evidence.gauss_ran else "fake_or_non_gauss_runner",
            completion_status="failed",
            failure_type=catalog.GaussErrorCategory.UNKNOWN.value,
            confidence="medium",
            summary=f"Execution failed with an uncataloged GAUSS error code: {error_code}.",
            user_explanation="GAUSS reported an error code that is not yet in the local deterministic catalog.",
            technical_explanation=(
                f"Preserved uncataloged GAUSS error {error_code}"
                + (f" with diagnostic text: {diagnostic_text}" if diagnostic_text else ".")
            ),
            likely_location="GAUSS diagnostic stream",
            next_step="Inspect stderr and consider adding this GAUSS error code to the catalog after verification.",
            requires_user_action=True,
            safe_to_continue=False,
            error_code=error_code,
            error_category=catalog.GaussErrorCategory.UNKNOWN.value,
            evidence_limitations=tuple(limitations),
        )

    return ExecutionInterpretation(
        execution_phase="unknown",
        launch_status="launched" if evidence.gauss_ran else "fake_or_non_gauss_runner",
        completion_status=evidence.execution_status or "unknown",
        failure_type=catalog.GaussErrorCategory.UNKNOWN.value,
        confidence="low",
        summary="Execution did not complete successfully, but the supplied evidence is insufficient to classify it.",
        user_explanation="The interpreter cannot determine a specific GAUSS failure category from the supplied evidence.",
        technical_explanation=(
            f"Runner {runner!r} reported execution_status={evidence.execution_status!r}, "
            f"exit_code={evidence.exit_code!r}, stdout_chars={evidence.stdout_chars!r}, "
            f"stderr_chars={evidence.stderr_chars!r}."
        ),
        likely_location=None,
        next_step="Inspect stdout and stderr, then review the generated GAUSS script.",
        requires_user_action=True,
        safe_to_continue=False,
        error_category=catalog.GaussErrorCategory.UNKNOWN.value,
        evidence_limitations=tuple(limitations),
    )
