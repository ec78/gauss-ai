"""Tests for `gauss_repair_draft_generation.py` (v0.69.0).

Run with:

    python scripts/test_gauss_repair_draft_generation.py

This file's primary purpose is proving the generator stays honestly bounded:
it must never fabricate a candidate for a code/pattern it has no verified
basis for, must never claim HIGH confidence, must always flag its
placeholder substitution as a placeholder, and must never produce
`suggested_operation`/`suggested_description` text containing a literal
code token that would trip `gauss_repair_draft.py`'s own `NO_GENERATED_CODE`
structural check.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_execution_interpreter as interp  # noqa: E402
import gauss_repair_draft as repair_draft_mod  # noqa: E402
import gauss_repair_draft_generation as gen  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _completed_evidence() -> interp.ExecutionEvidence:
    return interp.ExecutionEvidence(
        runner="FAKE", gauss_ran=False, executed=True, execution_status="completed", exit_code=0,
    )


def _pre_launch_evidence() -> interp.ExecutionEvidence:
    return interp.ExecutionEvidence(runner="FAKE", gauss_ran=False, executed=False, execution_status=None, exit_code=None)


def _timeout_evidence() -> interp.ExecutionEvidence:
    return interp.ExecutionEvidence(
        runner="FAKE", gauss_ran=False, executed=True, execution_status="timed_out", exit_code=None, timed_out=True,
    )


def _g0105_evidence() -> interp.ExecutionEvidence:
    return interp.ExecutionEvidence(
        runner="FAKE", gauss_ran=False, executed=True, execution_status="failed", exit_code=0,
        stderr_text="error G0105 : Bad expression or missing arguments",
    )


def _g0036_evidence() -> interp.ExecutionEvidence:
    return interp.ExecutionEvidence(
        runner="FAKE", gauss_ran=False, executed=True, execution_status="failed", exit_code=0,
        stderr_text="error G0036 : Matrix dimensions are incompatible",
    )


def _unknown_code_evidence() -> interp.ExecutionEvidence:
    return interp.ExecutionEvidence(
        runner="FAKE", gauss_ran=False, executed=True, execution_status="failed", exit_code=0,
        stderr_text="error G9999 : Not a real cataloged code",
    )


def _no_code_evidence() -> interp.ExecutionEvidence:
    return interp.ExecutionEvidence(
        runner="FAKE", gauss_ran=False, executed=True, execution_status="failed", exit_code=0, stderr_text="",
    )


# ---------------------------------------------------------------------------
# Not-applicable phases
# ---------------------------------------------------------------------------


def test_01_completed_execution_is_not_applicable() -> None:
    result = gen.generate_repair_draft_candidates(_completed_evidence(), "x = 1;")
    check("status is not_applicable", result.status == gen.GenerationStatus.NOT_APPLICABLE.value)
    check("no candidates", result.candidates == ())


def test_02_pre_launch_is_not_applicable() -> None:
    result = gen.generate_repair_draft_candidates(_pre_launch_evidence(), None)
    check("status is not_applicable", result.status == gen.GenerationStatus.NOT_APPLICABLE.value)
    check("no candidates", result.candidates == ())


def test_03_timeout_is_not_applicable() -> None:
    result = gen.generate_repair_draft_candidates(_timeout_evidence(), "x = 1;")
    check("status is not_applicable", result.status == gen.GenerationStatus.NOT_APPLICABLE.value)
    check("no candidates", result.candidates == ())


def test_04_uncataloged_error_code_is_not_applicable() -> None:
    result = gen.generate_repair_draft_candidates(_unknown_code_evidence(), "x = 1;")
    check("status is not_applicable", result.status == gen.GenerationStatus.NOT_APPLICABLE.value)
    check("no candidates", result.candidates == ())
    check("source_error_code is preserved even though uncataloged", result.source_error_code == "G9999")


def test_05_no_error_code_at_all_is_not_applicable() -> None:
    result = gen.generate_repair_draft_candidates(_no_code_evidence(), "x = 1;")
    check("status is not_applicable", result.status == gen.GenerationStatus.NOT_APPLICABLE.value)


# ---------------------------------------------------------------------------
# Honest "no candidate" cases -- never fabricates
# ---------------------------------------------------------------------------


def test_06_cataloged_code_with_no_generator_implemented_never_fabricates() -> None:
    """G0036 is a real, cataloged, high-confidence-classified error code, but
    this first version implements no candidate pattern for it -- the result
    must honestly say so, never invent a candidate."""
    result = gen.generate_repair_draft_candidates(_g0036_evidence(), "x = ones(2,2); y = ones(3,1); z = x + y;")
    check("status is no_candidate_available", result.status == gen.GenerationStatus.NO_CANDIDATE_AVAILABLE.value)
    check("no candidates", result.candidates == ())
    check("source_error_code is G0036", result.source_error_code == "G0036")
    check(
        "a limitation explicitly says no pattern is implemented yet",
        any("no deterministic candidate pattern" in item.lower() for item in result.limitations),
    )


def test_07_g0105_with_no_source_code_supplied_is_honest() -> None:
    result = gen.generate_repair_draft_candidates(_g0105_evidence(), None)
    check("status is no_candidate_available", result.status == gen.GenerationStatus.NO_CANDIDATE_AVAILABLE.value)
    check("no candidates", result.candidates == ())


def test_08_g0105_with_empty_string_source_is_honest() -> None:
    result = gen.generate_repair_draft_candidates(_g0105_evidence(), "   ")
    check("status is no_candidate_available", result.status == gen.GenerationStatus.NO_CANDIDATE_AVAILABLE.value)


def test_09_g0105_with_no_matching_line_is_honest() -> None:
    """A pattern IS implemented for G0105, but this source has no line
    matching it -- the result must say so, never guess a location."""
    result = gen.generate_repair_draft_candidates(_g0105_evidence(), "x = 2 + 2;\nprint x;\n")
    check("status is no_candidate_available", result.status == gen.GenerationStatus.NO_CANDIDATE_AVAILABLE.value)
    check("no candidates", result.candidates == ())
    check(
        "a limitation distinguishes 'pattern exists but no match' from 'no pattern at all'",
        any("no line in the supplied source matched" in item.lower() for item in result.limitations),
    )


# ---------------------------------------------------------------------------
# Real candidate generation: G0105 empty-assignment pattern
# ---------------------------------------------------------------------------


def test_10_g0105_single_match_produces_one_candidate() -> None:
    result = gen.generate_repair_draft_candidates(_g0105_evidence(), "x = ;\nprint x;\n")
    check("status is candidates_available", result.status == gen.GenerationStatus.CANDIDATES_AVAILABLE.value)
    check("exactly one candidate", len(result.candidates) == 1)
    c = result.candidates[0]
    check("line_start is 1", c.line_start == 1)
    check("line_end is 1", c.line_end == 1)
    check("affected_statement is the exact source line", c.affected_statement == "x = ;")
    check("proposed_replacement_text is x = 0;", c.proposed_replacement_text == "x = 0;")
    check("pattern_id is G0105_EMPTY_ASSIGNMENT_RHS", c.pattern_id == "G0105_EMPTY_ASSIGNMENT_RHS")
    check("error_code is G0105", c.error_code == "G0105")
    check("confidence is medium", c.confidence == gen.CandidateConfidence.MEDIUM.value)


def test_11_g0105_preserves_leading_indentation() -> None:
    result = gen.generate_repair_draft_candidates(_g0105_evidence(), "if (1);\n    x = ;\nendif;\n")
    check("exactly one candidate", len(result.candidates) == 1)
    c = result.candidates[0]
    check("line_start is 2", c.line_start == 2)
    check("indentation is preserved in the replacement", c.proposed_replacement_text == "    x = 0;")


def test_12_g0105_multiple_matches_produce_multiple_candidates() -> None:
    source = "x = ;\ny = 1;\nz = ;\n"
    result = gen.generate_repair_draft_candidates(_g0105_evidence(), source)
    check("two candidates", len(result.candidates) == 2)
    check("first candidate targets line 1", result.candidates[0].line_start == 1)
    check("second candidate targets line 3", result.candidates[1].line_start == 3)
    ids = {c.candidate_id for c in result.candidates}
    check("candidate IDs are unique", len(ids) == len(result.candidates))


def test_13_candidate_count_is_capped_at_max_candidates() -> None:
    source = "\n".join(f"v{i} = ;" for i in range(gen.MAX_CANDIDATES + 10))
    result = gen.generate_repair_draft_candidates(_g0105_evidence(), source)
    check(f"candidate count is capped at {gen.MAX_CANDIDATES}", len(result.candidates) == gen.MAX_CANDIDATES)


def test_14_different_variable_names_are_reflected_in_the_replacement() -> None:
    result = gen.generate_repair_draft_candidates(_g0105_evidence(), "myVariable123 = ;\n")
    check("exactly one candidate", len(result.candidates) == 1)
    check(
        "the replacement uses the same left-hand-side name",
        result.candidates[0].proposed_replacement_text == "myVariable123 = 0;",
    )


# ---------------------------------------------------------------------------
# Never fabricates certainty
# ---------------------------------------------------------------------------


def test_15_no_candidate_anywhere_ever_claims_high_confidence() -> None:
    check("CandidateConfidence has no HIGH member", not hasattr(gen.CandidateConfidence, "HIGH"))
    check(
        "no confidence value in the enum is the string 'high'",
        all(member.value != "high" for member in gen.CandidateConfidence),
    )


def test_16_reasoning_always_discloses_the_placeholder_nature_of_the_value() -> None:
    result = gen.generate_repair_draft_candidates(_g0105_evidence(), "x = ;\n")
    c = result.candidates[0]
    check("reasoning explicitly calls the value a placeholder", "placeholder" in c.reasoning.lower())
    check("reasoning explicitly disclaims guessing user intent", "not a guess" in c.reasoning.lower())


def test_17_generation_boundary_is_present_on_the_result_and_every_candidate() -> None:
    result = gen.generate_repair_draft_candidates(_g0105_evidence(), "x = ;\n")
    check("result carries the fixed boundary statement", result.generation_boundary == gen.GENERATION_BOUNDARY_STATEMENT)
    for c in result.candidates:
        check(
            f"{c.candidate_id} carries the fixed boundary statement",
            c.generation_boundary == gen.GENERATION_BOUNDARY_STATEMENT,
        )


# ---------------------------------------------------------------------------
# Compatibility with gauss_repair_draft.py's own structural constraints
# ---------------------------------------------------------------------------


def test_18_suggested_operation_and_description_contain_no_banned_code_tokens() -> None:
    """A candidate's operation/description text is meant to be passed
    straight through to repair-draft's own --operation/--description
    arguments -- it must never trip NO_GENERATED_CODE."""
    result = gen.generate_repair_draft_candidates(_g0105_evidence(), "x = ;\ny = ;\n")
    check("at least one candidate exists to check", len(result.candidates) > 0)
    for c in result.candidates:
        text = f"{c.suggested_operation} {c.suggested_description}"
        for token in repair_draft_mod._BANNED_CODE_TOKENS:  # noqa: SLF001
            check(f"{c.candidate_id} operation/description does not contain banned token {token!r}", token not in text)


# ---------------------------------------------------------------------------
# Determinism and purity
# ---------------------------------------------------------------------------


def test_19_generation_is_deterministic() -> None:
    r1 = gen.generate_repair_draft_candidates(_g0105_evidence(), "x = ;\n")
    r2 = gen.generate_repair_draft_candidates(_g0105_evidence(), "x = ;\n")
    check("repeated calls produce equal results", r1 == r2)


def test_20_module_defines_no_execution_repair_or_approval_engine_of_its_own() -> None:
    source = Path(gen.__file__).read_text(encoding="utf-8")
    forbidden = (
        "def execute(", "def apply_repair(", "def propose_execution(", "def evaluate_application_gate(",
        "def build_repair_draft(", "import subprocess", "import requests", "import urllib",
        "import gauss_code_execution",
    )
    for token in forbidden:
        check(f"module does not contain {token!r}", token not in source)


def test_21_generator_registry_is_deliberately_limited_to_g0105() -> None:
    """Locks in this milestone's own explicit scope boundary -- expanding
    pattern coverage in a future milestone must visibly update this test,
    never silently grow underneath it."""
    check("exactly one error code has a generator in this first version", tuple(gen._GENERATORS.keys()) == ("G0105",))  # noqa: SLF001


def run_tests() -> int:
    tests = [
        (name, fn)
        for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    for name, fn in tests:
        before = len(_failures)
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _failures.append(f"{name} raised {type(exc).__name__}: {exc}")
        if len(_failures) == before:
            print(f"PASS  {name}")
        else:
            for failure in _failures[before:]:
                print(f"FAIL  {name}: {failure}")
    print(f"\n{len(tests)} test function(s) run, {len(_failures)} check failure(s).")
    if _failures:
        print("SOME CHECKS FAILED.")
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
