"""Bounded, deterministic, first-version AI-assisted repair-draft candidate
generation (v0.69.0).

Position in the reasoning pipeline:

    Execution evidence -> Interpretation -> Diagnosis
        -> Repair Planning (gauss_repair_planner.py, v0.56.0)
        -> Repair Draft Candidate Generation (this module, v0.69.0)
        -> Repair Draft (gauss_repair_draft.py, v0.59.0) -- via caller-supplied fields
        -> Repair Draft Approval -> Application Approval -> Application Gate
           -> Repair Application Transaction -> Verification -> Review
           (all unchanged, zero diff)

This is the first module in this repository capable of proposing literal
GAUSS replacement code -- but it never applies, approves, drafts, or writes
anything, and it never bypasses a single existing approval layer. A
generated candidate is only ever a PROPOSAL: `RepairDraftCandidate.
proposed_replacement_text` is surfaced to a human, who must explicitly
accept, edit, or reject it before it ever becomes the `--replacement-text`
argument to `apply-repair` (gauss_repair_application.py) -- exactly the
same argument a manual tester has always had to type by hand. This module
never calls `apply-repair`, `repair-draft`, any approval store, or GAUSS
itself, and defines no execution/application/approval logic of its own.

"AI-assisted" here means bounded, deterministic, catalog-and-pattern-driven
generation -- not a call to an external LLM API. This repository has no LLM
integration anywhere, and this module adds none; it is a first, narrow,
explainable version of draft generation, structured so a genuine LLM-backed
generator could be substituted behind the same `RepairDraftCandidate`
contract in a future, separately authorized milestone, without changing
anything downstream of this module.

Pattern coverage is DELIBERATELY narrow in this first version: exactly one
safe, unambiguous source pattern is recognized -- G0105's own verified
"incomplete or malformed expression" trigger, an assignment with an empty
right-hand side (e.g. `x = ;`), matching this repository's own catalog-
verified real-runtime reproduction trigger for G0105 exactly (see
`gauss_error_catalog.py`'s G0105 entry and
`planning/v0.28.0-real-gauss-invocation-research.md`). Every other
cataloged error code, and every G0105 occurrence that does not match this
exact pattern, returns an honest "no candidate available" result rather
than a fabricated guess -- exactly this repository's standing discipline
(see `gauss_repair_planner.py`'s own `BLOCKED_BY_MISSING_SOURCE` status)
applied one layer further, now to literal code instead of only inspection
strategies.

Every candidate's `proposed_replacement_text` is a clearly-flagged
placeholder substitution, never a claim about the user's actual intent --
`confidence` is capped at `medium`, never `high`, and `reasoning` always
states the placeholder is a placeholder that must be reviewed, not a guess
at what the user's code actually needs.

A candidate's `suggested_operation`/`suggested_description` are always
code-token-free descriptive text (no `;`, no ` = `), so they remain safe to
pass unchanged as `repair-draft`'s existing `--operation`/`--description`
arguments -- `gauss_repair_draft.py`'s own `NO_GENERATED_CODE` structural
check and its fixed "No code was generated" boundary statement remain true
of every `RepairDraft` this repository ever constructs, including one
seeded from a generated candidate.

Pure and deterministic given its inputs. Never launches GAUSS, calls an
execution helper, reads or writes a file (the affected source text is
caller-supplied, exactly like `gauss_repair_planner.SourceContext.
code_text` already is), mutates workspace state, accesses the network, or
calls an LLM -- it has no import, and no code path, capable of any of
those things.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Callable

import gauss_error_catalog as catalog
import gauss_execution_diagnostics as diag
import gauss_execution_interpreter as interp


class GenerationStatus(enum.Enum):
    CANDIDATES_AVAILABLE = "candidates_available"
    #: A cataloged error code was matched, or generation was attempted, but
    #: no candidate could be produced -- e.g. no pattern is implemented yet
    #: for this code, or no line in the supplied source matched it, or no
    #: source text was supplied at all.
    NO_CANDIDATE_AVAILABLE = "no_candidate_available"
    #: Generation does not apply at all -- no execution yet, execution
    #: succeeded, a timeout, or an uncataloged error code.
    NOT_APPLICABLE = "not_applicable"


class CandidateConfidence(enum.Enum):
    """Deliberately excludes HIGH -- no candidate this module ever produces
    is a confirmed fix; `MEDIUM` is the ceiling, reserved for a candidate
    whose *structural* pattern match is unambiguous even though the
    substituted value itself is only a placeholder."""

    MEDIUM = "medium"
    LOW = "low"


#: A fixed, always-present disclosure -- never conditional, never reworded
#: per candidate, so it cannot be accidentally omitted.
GENERATION_BOUNDARY_STATEMENT = (
    "This is a generated CANDIDATE only. It has not been approved, drafted, applied, or verified. Review it "
    "carefully -- accept, edit, or reject it -- before it can become part of a repair draft."
)

#: A conservative, explicit bound on how many candidates a single call can
#: return, mirroring `gauss_repair_draft.MAX_EDIT_RANGE_LINES`'s own
#: "cap it here, don't leave it to a future implementation to remember"
#: convention. Not user-configurable in this first version.
MAX_CANDIDATES = 5

_BASE_LIMITATIONS: tuple[str, ...] = (
    "Candidate generation is bounded to this repository's verified GAUSS error catalog and a small, explicit "
    "set of deterministic source patterns; it does not parse GAUSS syntax, verify semantic correctness, or "
    "reason about the program's intent.",
    "A candidate's confidence reflects the strength of the structural pattern match, not a guarantee the "
    "candidate will resolve the error or that its substituted value is what the code actually needs.",
)

#: Matches an assignment statement whose right-hand side is empty --
#: G0105's own catalog-verified "incomplete or malformed expression"
#: trigger, reproduced via `x = ;` (see gauss_error_catalog.py's G0105
#: entry). Captures leading indentation separately so it can be preserved
#: in the proposed replacement.
_EMPTY_ASSIGNMENT_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<lhs>[A-Za-z_]\w*)\s*=\s*;\s*$")


@dataclass(frozen=True)
class RepairDraftCandidate:
    candidate_id: str
    #: Which deterministic pattern produced this candidate -- e.g.
    #: "G0105_EMPTY_ASSIGNMENT_RHS". Never an opaque numeric score.
    pattern_id: str
    error_code: str
    line_start: int
    line_end: int
    #: The exact, unmodified source line(s) this candidate targets.
    affected_statement: str
    #: The candidate's literal proposed replacement text -- kept separate
    #: from every RepairDraft-facing field; see module docstring.
    proposed_replacement_text: str
    #: Code-token-free short label, safe to pass as repair-draft's
    #: --operation.
    suggested_operation: str
    #: Code-token-free longer description, safe to pass as repair-draft's
    #: --description.
    suggested_description: str
    reasoning: str
    #: One of `CandidateConfidence`'s values.
    confidence: str
    generation_boundary: str


@dataclass(frozen=True)
class RepairDraftGenerationResult:
    #: One of `GenerationStatus`'s values.
    status: str
    summary: str
    #: Ranked, top-first (currently: source order). Empty when no candidate
    #: could be produced.
    candidates: tuple[RepairDraftCandidate, ...]
    limitations: tuple[str, ...]
    generation_boundary: str
    source_error_code: str | None


def _result(
    status: GenerationStatus,
    summary: str,
    candidates: tuple[RepairDraftCandidate, ...],
    limitations: tuple[str, ...],
    source_error_code: str | None,
) -> RepairDraftGenerationResult:
    return RepairDraftGenerationResult(
        status=status.value,
        summary=summary,
        candidates=candidates,
        limitations=tuple(_BASE_LIMITATIONS) + limitations,
        generation_boundary=GENERATION_BOUNDARY_STATEMENT,
        source_error_code=source_error_code,
    )


def _generate_g0105_candidates(source_code: str) -> tuple[RepairDraftCandidate, ...]:
    candidates: list[RepairDraftCandidate] = []
    for index, line in enumerate(source_code.splitlines(), start=1):
        match = _EMPTY_ASSIGNMENT_RE.match(line)
        if not match:
            continue
        lhs = match.group("lhs")
        indent = match.group("indent")
        candidates.append(
            RepairDraftCandidate(
                candidate_id=f"candidate-g0105-{index}",
                pattern_id="G0105_EMPTY_ASSIGNMENT_RHS",
                error_code="G0105",
                line_start=index,
                line_end=index,
                affected_statement=line,
                proposed_replacement_text=f"{indent}{lhs} = 0;",
                suggested_operation="Fill in the missing expression on the assignment's right-hand side",
                suggested_description=(
                    "The assignment has no expression after its operator, which is a known G0105 trigger. A "
                    "neutral placeholder value has been substituted for review."
                ),
                reasoning=(
                    f"Line {index} assigns to '{lhs}' but supplies no expression before the statement "
                    "terminator, matching this repository's verified G0105 'incomplete or malformed "
                    "expression' trigger. A placeholder value (0) has been substituted so the statement "
                    "parses -- this is NOT a guess at the value your code actually needs; replace it with the "
                    "correct expression before accepting."
                ),
                confidence=CandidateConfidence.MEDIUM.value,
                generation_boundary=GENERATION_BOUNDARY_STATEMENT,
            )
        )
        if len(candidates) >= MAX_CANDIDATES:
            break
    return tuple(candidates)


#: Which cataloged error codes this first version can attempt pattern-based
#: generation for. Deliberately a single entry -- see module docstring.
#: A future milestone extending this dict is exactly the intended, narrow
#: extension point for broader coverage; nothing about the module's own
#: structure needs to change to add a second entry.
_GENERATORS: dict[str, Callable[[str], tuple[RepairDraftCandidate, ...]]] = {
    "G0105": _generate_g0105_candidates,
}


def generate_repair_draft_candidates(
    evidence: "interp.ExecutionEvidence", source_code: str | None
) -> RepairDraftGenerationResult:
    """The single entry point. Internally calls `interpret_execution(evidence)`
    and `diagnose_execution(evidence)` -- the same pure functions `interpret`/
    `diagnose` already use -- rather than re-deriving classification or
    diagnostic reasoning a second, possibly divergent way. `source_code`, if
    supplied, is the caller's own already-authorized source text (e.g. the
    adapter's `pending_request.code`) -- this function never reads a file."""
    interpretation = interp.interpret_execution(evidence)
    diagnosis = diag.diagnose_execution(evidence)

    if interpretation.execution_phase == "completed":
        return _result(
            GenerationStatus.NOT_APPLICABLE,
            "Execution completed with no detected error; there is nothing to generate a repair candidate for.",
            (),
            (),
            None,
        )

    if interpretation.execution_phase == "pre_launch":
        return _result(
            GenerationStatus.NOT_APPLICABLE,
            "Candidate generation is unavailable because no execution has launched or completed yet.",
            (),
            ("a completed or failed execution attempt (run 'execute' first)",),
            None,
        )

    if interpretation.execution_phase == "timeout":
        return _result(
            GenerationStatus.NOT_APPLICABLE,
            "Execution timed out. This repository has no cataloged GAUSS error code for a timeout, so no "
            "repair candidate can be generated.",
            (),
            (),
            None,
        )

    entry = catalog.lookup_error(interpretation.error_code) if interpretation.error_code else None

    if entry is None:
        if interpretation.error_code is not None:
            summary = (
                f"GAUSS reported an uncataloged error code ({interpretation.error_code}); no verified "
                "candidate pattern exists for it."
            )
        else:
            summary = (
                "The supplied evidence does not identify a cataloged GAUSS error code, so no repair candidate "
                "can be generated."
            )
        return _result(GenerationStatus.NOT_APPLICABLE, summary, (), (), interpretation.error_code)

    if not source_code or not source_code.strip():
        return _result(
            GenerationStatus.NO_CANDIDATE_AVAILABLE,
            f"GAUSS reported {entry.title} ({entry.error_code}), but no source code text is available to "
            "search for a candidate.",
            (),
            ("the affected source code text was not supplied",),
            entry.error_code,
        )

    generator = _GENERATORS.get(entry.error_code)
    candidates = generator(source_code) if generator is not None else ()

    if not candidates:
        limitations = [
            f"No deterministic candidate pattern is implemented yet for {entry.error_code} in this first "
            "version of AI-assisted draft generation; manual draft entry is required.",
        ]
        if generator is not None:
            limitations.append(
                "A candidate pattern exists for this error code, but no line in the supplied source matched it."
            )
        return _result(
            GenerationStatus.NO_CANDIDATE_AVAILABLE,
            f"GAUSS reported {entry.title} ({entry.error_code}). {diagnosis.summary} No automatic repair "
            "candidate could be generated; manual draft entry is required.",
            (),
            tuple(limitations),
            entry.error_code,
        )

    return _result(
        GenerationStatus.CANDIDATES_AVAILABLE,
        f"GAUSS reported {entry.title} ({entry.error_code}). {len(candidates)} candidate repair draft(s) "
        "generated from a bounded source pattern match; none is applied, approved, or guaranteed correct.",
        candidates,
        (),
        entry.error_code,
    )
