"""Tests for deterministic, evidence-bound diagnostic reasoning.

Run with:

    python scripts/test_gauss_execution_diagnostics.py

No test launches GAUSS, calls an execution helper, mutates workspace state,
edits source code, reads output files, accesses the network, or retries.
The diagnostic engine consumes already-captured evidence only.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_error_catalog as catalog  # noqa: E402
import gauss_execution_diagnostics as diag  # noqa: E402
import gauss_execution_interpreter as interp  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _evidence(**overrides: object) -> interp.ExecutionEvidence:
    values = {
        "runner": "REAL_GAUSS",
        "gauss_ran": True,
        "executed": True,
        "execution_status": "completed",
        "exit_code": 0,
        "stdout_chars": 10,
        "stderr_chars": 0,
        "timed_out": False,
        "stdout_text": "4.0000000\n",
        "stderr_text": "",
    }
    values.update(overrides)
    return interp.ExecutionEvidence(**values)


def _failed(stderr_text: str, **overrides: object) -> interp.ExecutionEvidence:
    base = {
        "execution_status": "failed",
        "stdout_text": "Program execute failed\n",
        "stderr_text": stderr_text,
    }
    base.update(overrides)
    return _evidence(**base)


# ---------------------------------------------------------------------------
# Core diagnostic engine
# ---------------------------------------------------------------------------


def test_01_successful_execution_produces_no_failure_diagnosis() -> None:
    a = diag.diagnose_execution(_evidence())
    check("no failure status", a.diagnostic_status == diag.DiagnosticStatus.NO_FAILURE_DETECTED.value)
    check("no possible causes", a.possible_causes == ())
    check("safe to continue", a.safe_to_continue)
    check("does not require user input", not a.requires_user_input)
    check("no source error code", a.source_error_code is None)
    check(
        "does not claim methodological correctness",
        any("does not establish" in limitation.lower() for limitation in a.limitations),
    )
    check("repair boundary always present", a.repair_boundary == diag.REPAIR_BOUNDARY_STATEMENT)


def test_02_fake_success_remains_distinguishable_from_real_success() -> None:
    real = diag.diagnose_execution(_evidence(runner="REAL_GAUSS", gauss_ran=True))
    fake = diag.diagnose_execution(_evidence(runner="FAKE", gauss_ran=False, stdout_text="fake runner completed\n"))
    check("real success names a real launch", any("launched" in fact for fact in real.supporting_evidence))
    check(
        "fake success names a fake/non-gauss launch",
        any("fake_or_non_gauss_runner" in fact for fact in fake.supporting_evidence),
    )
    check("real and fake success supporting_evidence differ", real.supporting_evidence != fake.supporting_evidence)


def test_03_g0105_bounded_diagnosis() -> None:
    a = diag.diagnose_execution(_failed("error G0105 : Bad expression or missing arguments\n"))
    check("status diagnosed", a.diagnostic_status == diag.DiagnosticStatus.DIAGNOSED.value)
    check("source code preserved", a.source_error_code == "G0105")
    check("category is parse_syntax", a.source_error_category == catalog.GaussErrorCategory.PARSE_SYNTAX.value)
    check("at least one cause", len(a.possible_causes) > 0)
    check("no cause claims corrected syntax", all("should be" not in c.description.lower() for c in a.possible_causes))


def test_04_g0036_bounded_diagnosis() -> None:
    a = diag.diagnose_execution(_failed("error G0036 : Matrix dimensions are incompatible\n"))
    check("category is matrix_dimension", a.source_error_category == catalog.GaussErrorCategory.MATRIX_DIMENSION.value)
    check("at least one cause", len(a.possible_causes) > 0)
    check(
        "no cause asserts a missing transpose as fact",
        all("missing transpose" not in c.description.lower() for c in a.possible_causes),
    )
    check(
        "missing evidence names operand dimensions",
        any("dimension" in item.lower() for item in a.missing_evidence),
    )


def test_05_g0025_bounded_diagnosis() -> None:
    a = diag.diagnose_execution(_failed("error G0025 : Undefined symbol: 'nobs'\n"))
    check("category is runtime_computation", a.source_error_category == catalog.GaussErrorCategory.RUNTIME_COMPUTATION.value)
    check("at least one cause", len(a.possible_causes) > 0)
    check(
        "does not invent the correct symbol",
        all("nobs" not in c.description for c in a.possible_causes),
    )


def test_06_g0014_bounded_diagnosis() -> None:
    a = diag.diagnose_execution(_failed("error G0014 : File not found 'data.txt', line 1\n"))
    check("category is file_io", a.source_error_category == catalog.GaussErrorCategory.FILE_IO.value)
    check("at least one cause", len(a.possible_causes) > 0)
    check(
        "does not claim to have located or read the file",
        all("located" not in c.description.lower() and "opened" not in c.description.lower() for c in a.possible_causes),
    )


def test_07_g0290_bounded_diagnosis() -> None:
    # v0.55.0: G0290 was reproduced against a real GAUSS runtime this
    # milestone and upgraded from documentation-only to dual-sourced; see
    # test_31_g0290_now_dual_sourced_after_v055_runtime_verification for the
    # dedicated regression test covering the transition itself.
    a = diag.diagnose_execution(_failed("error G0290 : Library not found\n"))
    check("category is package_or_library", a.source_error_category == catalog.GaussErrorCategory.PACKAGE_OR_LIBRARY.value)
    check("knowledge_verification is now dual-sourced", a.knowledge_verification == ("real_runtime", "official_documentation"))
    check(
        "limitations no longer disclose an unresolved runtime-confirmation gap for G0290",
        not any("not yet" in limitation.lower() and "runtime" in limitation.lower() for limitation in a.limitations),
    )


def test_08_unknown_gauss_code() -> None:
    a = diag.diagnose_execution(_failed("error G6543 : Some newly observed condition\n"))
    check("status unknown_error", a.diagnostic_status == diag.DiagnosticStatus.UNKNOWN_ERROR.value)
    check("code preserved", a.source_error_code == "G6543")
    check("no possible causes for an unknown code", a.possible_causes == ())
    check("confidence is insufficient_evidence", a.confidence == diag.DiagnosticConfidence.INSUFFICIENT_EVIDENCE.value)


def test_09_non_gauss_unknown_failure() -> None:
    a = diag.diagnose_execution(_failed("", stdout_text="Program execute failed\n"))
    check("no error code extracted", a.source_error_code is None)
    check("status insufficient_evidence", a.diagnostic_status == diag.DiagnosticStatus.INSUFFICIENT_EVIDENCE.value)
    check("no possible causes without a matched code", a.possible_causes == ())


def test_10_timeout_evidence() -> None:
    a = diag.diagnose_execution(_evidence(execution_status="timed_out", timed_out=True))
    check("status timeout", a.diagnostic_status == diag.DiagnosticStatus.TIMEOUT.value)
    check("no asserted causes for timeout", a.possible_causes == ())
    check("confidence insufficient", a.confidence == diag.DiagnosticConfidence.INSUFFICIENT_EVIDENCE.value)
    check("questions posed rather than causes asserted", len(a.questions_to_ask) > 0)


def test_11_blocked_before_launch_evidence() -> None:
    a = diag.diagnose_execution(
        _evidence(
            gauss_ran=False, executed=False, execution_status=None, exit_code=None,
            stdout_text=None, stderr_text=None, metadata_error="missing terminal executable",
        )
    )
    check("status not_available", a.diagnostic_status == diag.DiagnosticStatus.NOT_AVAILABLE.value)
    check("requires user input", a.requires_user_input)
    check("not safe to continue", not a.safe_to_continue)


def test_12_insufficient_evidence() -> None:
    a = diag.diagnose_execution(_evidence(execution_status="failed", stdout_text=None, stderr_text=None, stderr_chars=50))
    check("status insufficient_evidence", a.diagnostic_status == diag.DiagnosticStatus.INSUFFICIENT_EVIDENCE.value)
    check("missing evidence discloses missing stderr", any("stderr" in item.lower() for item in a.missing_evidence))


def test_13_contradictory_evidence() -> None:
    # exit_code 0 alongside a failed status is exactly the case this
    # repository has documented as unreliable -- the diagnostic assessment
    # must not silently ignore it (the interpreter's own limitation for
    # this is still surfaced through the supporting_evidence/technical text
    # this engine reuses, not a new contradiction detector).
    a = diag.diagnose_execution(_failed("error G0036 : Matrix dimensions are incompatible\n", exit_code=0))
    check("still classified via the catalog despite exit_code 0", a.source_error_code == "G0036")
    check(
        "contradicting_evidence remains honestly empty (no contradiction detector exists yet)",
        a.contradicting_evidence == (),
    )


def test_14_missing_stderr() -> None:
    a = diag.diagnose_execution(_evidence(execution_status="failed", stdout_text="Program execute failed\n", stderr_text=None))
    check("insufficient evidence without stderr", a.diagnostic_status == diag.DiagnosticStatus.INSUFFICIENT_EVIDENCE.value)


def test_15_missing_stdout() -> None:
    a = diag.diagnose_execution(_failed("error G0105 : Bad expression or missing arguments\n", stdout_text=None))
    check("still diagnoses from stderr alone", a.source_error_code == "G0105")


def test_16_deterministic_repeated_assessment() -> None:
    evidence = _failed("error G0036 : Matrix dimensions are incompatible\n")
    first = diag.diagnose_execution(evidence)
    second = diag.diagnose_execution(evidence)
    check("repeated assessment of identical evidence is identical", first == second)


def test_17_confidence_ceiling_behavior() -> None:
    for code, stderr in (
        ("G0105", "error G0105 : Bad expression or missing arguments\n"),
        ("G0036", "error G0036 : Matrix dimensions are incompatible\n"),
        ("G0025", "error G0025 : Undefined symbol: 'x'\n"),
        ("G0014", "error G0014 : File not found 'x.txt'\n"),
        ("G0290", "error G0290 : Library not found\n"),
    ):
        a = diag.diagnose_execution(_failed(stderr))
        for cause in a.possible_causes:
            check(f"{code} cause {cause.cause_id} confidence never exceeds low", cause.confidence == diag.DiagnosticConfidence.LOW.value)
        check(f"{code} overall diagnosis confidence is low, not high", a.confidence == diag.DiagnosticConfidence.LOW.value)


def test_18_catalog_verification_metadata_preserved() -> None:
    a = diag.diagnose_execution(_failed("error G0025 : Undefined symbol: 'x'\n"))
    check("knowledge_verification populated", len(a.knowledge_verification) > 0)
    check("real_runtime present for G0025", "real_runtime" in a.knowledge_verification)
    for cause in a.possible_causes:
        check(f"{cause.cause_id} marked catalog-verified", cause.is_catalog_verified)
        check(f"{cause.cause_id} carries a verification_source", bool(cause.verification_source))


def test_19_no_causes_when_no_verified_cause_exists() -> None:
    a = diag.diagnose_execution(_failed("error G6543 : Something new\n"))
    check("unknown code yields zero causes", a.possible_causes == ())


def test_20_missing_evidence_disclosed() -> None:
    a = diag.diagnose_execution(_failed("error G0036 : Matrix dimensions are incompatible\n"))
    check("missing_evidence is non-empty for a cataloged code", len(a.missing_evidence) > 0)


def test_21_no_code_repair_fields_or_repair_output() -> None:
    a = diag.diagnose_execution(_failed("error G0105 : Bad expression or missing arguments\n"))
    fields = set(a.__dataclass_fields__)
    check("no 'repair' field other than the fixed boundary statement", fields.isdisjoint({"repair", "replacement_code", "fix", "corrected_code"}))
    check("repair_boundary is the fixed disclosure string", a.repair_boundary == diag.REPAIR_BOUNDARY_STATEMENT)
    combined = " ".join(
        [a.summary]
        + list(a.recommended_diagnostic_steps)
        + [c.description for c in a.possible_causes]
    ).lower()
    check("no rewrite language anywhere in the assessment", "rewrite" not in combined and "replace it with" not in combined)


# ---------------------------------------------------------------------------
# Boundary tests
# ---------------------------------------------------------------------------


def test_22_diagnosis_never_invokes_gauss() -> None:
    diag.diagnose_execution(_failed("error G0105 : Bad expression or missing arguments\n"))
    check("gauss_code_execution never imported by diagnosis", "gauss_code_execution" not in sys.modules)


def test_23_diagnosis_module_has_no_execution_or_workspace_imports() -> None:
    source = Path(diag.__file__).read_text(encoding="utf-8")
    forbidden = ("gauss_code_execution", "gauss_workspace", "gauss_runtime_orchestration", "gauss_execution_adapter", "subprocess")
    for name in forbidden:
        check(f"diagnostics module does not import {name!r}", f"import {name}" not in source)


def test_24_diagnosis_is_a_pure_function_of_its_input() -> None:
    import inspect

    signature = inspect.signature(diag.diagnose_execution)
    check("diagnose_execution takes exactly one evidence parameter", len(signature.parameters) == 1)


def test_25_diagnosis_never_reads_files() -> None:
    source = Path(diag.__file__).read_text(encoding="utf-8")
    check("no filesystem read calls in the diagnostics module", "open(" not in source and "read_text(" not in source and "Path(" not in source)


# ---------------------------------------------------------------------------
# Catalog diagnostic-knowledge tests
# ---------------------------------------------------------------------------


def test_26_verified_diagnostic_knowledge_has_provenance() -> None:
    for entry in catalog.catalog_entries():
        if entry.known_triggers:
            check(f"{entry.error_code} known_triggers carry a verification_source", bool(entry.verification_source))
            check(f"{entry.error_code} known_triggers carry verification_status", len(entry.verification_status) > 0)


def test_27_no_duplicate_cause_identifiers() -> None:
    for entry in catalog.catalog_entries():
        causes = diag._causes_from_entry(entry)  # noqa: SLF001 - internal helper, intentional
        ids = [c.cause_id for c in causes]
        check(f"{entry.error_code} has no duplicate cause_id", len(ids) == len(set(ids)))


def test_28_no_cause_without_a_confidence_basis() -> None:
    for entry in catalog.catalog_entries():
        for cause in diag._causes_from_entry(entry):  # noqa: SLF001
            check(f"{cause.cause_id} has a non-empty confidence value", bool(cause.confidence))
            check(
                f"{cause.cause_id} confidence is a real DiagnosticConfidence value",
                cause.confidence in {c.value for c in diag.DiagnosticConfidence},
            )


def test_29_no_repair_instruction_in_catalog_entries() -> None:
    banned_terms = ("replace with", "change to", "fix by", "correct code", "rewrite as")
    for entry in catalog.catalog_entries():
        text = " ".join(entry.known_triggers + entry.diagnostic_questions + entry.required_evidence_for_diagnosis).lower()
        for term in banned_terms:
            check(f"{entry.error_code} diagnostic knowledge contains no {term!r}", term not in text)


def test_30_unknown_codes_do_not_inherit_known_code_causes() -> None:
    a = diag.diagnose_execution(_failed("error G1111 : Not in the catalog\n"))
    all_known_titles = {trigger for entry in catalog.catalog_entries() for trigger in entry.known_triggers}
    check("unknown code has no causes at all", a.possible_causes == ())
    check("no known-code trigger text leaked into an unknown-code assessment", not any(title in a.summary for title in all_known_titles))


def test_31_g0290_now_dual_sourced_after_v055_runtime_verification() -> None:
    # v0.55.0: G0290 was reproduced against a real GAUSS runtime this
    # milestone and upgraded from documentation-only to dual-sourced. This
    # intentionally supersedes v0.54.0's own documentation-only assertion --
    # see CHANGELOG.md / release-notes-v0.55.0.md for the exact reason.
    entry = catalog.lookup_error("G0290")
    assert entry is not None
    check(
        "G0290 verification_status is now dual-sourced",
        entry.verification_status == (catalog.VerificationStatus.REAL_RUNTIME, catalog.VerificationStatus.OFFICIAL_DOCUMENTATION),
    )
    a = diag.diagnose_execution(_failed("error G0290 : Library not found\n"))
    check("G0290 diagnosis now truthfully reports real_runtime verification", "real_runtime" in a.knowledge_verification)
    check(
        "G0290 no longer carries the pre-v0.55.0 'not yet reproduced' limitation wording",
        not any("not yet reproduced against a real GAUSS runtime" in item for item in a.limitations),
    )


# ---------------------------------------------------------------------------
# v0.55.0 -- new catalog codes
# ---------------------------------------------------------------------------


def test_32_g0058_index_out_of_range_bounded_diagnosis() -> None:
    a = diag.diagnose_execution(_failed("error G0058 : Index out of range\n"))
    check("G0058 diagnosed status", a.diagnostic_status == diag.DiagnosticStatus.DIAGNOSED.value)
    check("G0058 has possible causes", len(a.possible_causes) > 0)
    check("G0058 causes stay at low confidence", all(c.confidence == diag.DiagnosticConfidence.LOW.value for c in a.possible_causes))
    check("G0058 missing evidence disclosed", len(a.missing_evidence) > 0)
    check("G0058 diagnosis never proposes a corrected index", not any("change the index" in c.description.lower() for c in a.possible_causes))
    check("G0058 repair boundary present", a.repair_boundary == diag.REPAIR_BOUNDARY_STATEMENT)


def test_33_g0159_wrong_number_of_parameters_bounded_diagnosis() -> None:
    a = diag.diagnose_execution(
        _failed("error G0159 : Wrong number of parameters ''myproc2' expected 2 arguments, received 1'\n")
    )
    check("G0159 diagnosed status", a.diagnostic_status == diag.DiagnosticStatus.DIAGNOSED.value)
    check("G0159 has possible causes", len(a.possible_causes) > 0)
    check("G0159 causes stay at low confidence", all(c.confidence == diag.DiagnosticConfidence.LOW.value for c in a.possible_causes))
    check("G0159 questions_to_ask populated", len(a.questions_to_ask) > 0)


def test_34_g0104_argument_must_be_positive_bounded_diagnosis() -> None:
    a = diag.diagnose_execution(_failed("error G0104 : Argument must be positive\n"))
    check("G0104 diagnosed status", a.diagnostic_status == diag.DiagnosticStatus.DIAGNOSED.value)
    check("G0104 has possible causes", len(a.possible_causes) > 0)
    check("G0104 causes stay at low confidence", all(c.confidence == diag.DiagnosticConfidence.LOW.value for c in a.possible_causes))


def test_35_g0071_type_mismatch_bounded_diagnosis() -> None:
    a = diag.diagnose_execution(_failed("error G0071 : Type mismatch\n"))
    check("G0071 diagnosed status", a.diagnostic_status == diag.DiagnosticStatus.DIAGNOSED.value)
    check("G0071 has possible causes", len(a.possible_causes) > 0)
    check("G0071 causes stay at low confidence", all(c.confidence == diag.DiagnosticConfidence.LOW.value for c in a.possible_causes))


def test_36_g0048_matrix_singular_bounded_diagnosis() -> None:
    a = diag.diagnose_execution(_failed("error G0048 : Matrix singular\n"))
    check("G0048 diagnosed status", a.diagnostic_status == diag.DiagnosticStatus.DIAGNOSED.value)
    check("G0048 has possible causes", len(a.possible_causes) > 0)
    check("G0048 causes stay at low confidence", all(c.confidence == diag.DiagnosticConfidence.LOW.value for c in a.possible_causes))
    check("G0048 source_error_category is numerical", a.source_error_category == "numerical")


def test_37_g0047_rows_dont_match_bounded_diagnosis() -> None:
    a = diag.diagnose_execution(_failed("error G0047 : Rows don't match\n"))
    check("G0047 diagnosed status", a.diagnostic_status == diag.DiagnosticStatus.DIAGNOSED.value)
    check("G0047 has possible causes", len(a.possible_causes) > 0)
    check("G0047 causes stay at low confidence", all(c.confidence == diag.DiagnosticConfidence.LOW.value for c in a.possible_causes))


def test_38_all_new_entries_produce_no_repair_shaped_output() -> None:
    banned_terms = ("replace with", "change to", "fix by", "correct code", "rewrite as")
    for code, stderr_text in (
        ("G0058", "error G0058 : Index out of range\n"),
        ("G0159", "error G0159 : Wrong number of parameters ''p' expected 2 arguments, received 1'\n"),
        ("G0104", "error G0104 : Argument must be positive\n"),
        ("G0071", "error G0071 : Type mismatch\n"),
        ("G0048", "error G0048 : Matrix singular\n"),
        ("G0047", "error G0047 : Rows don't match\n"),
    ):
        a = diag.diagnose_execution(_failed(stderr_text))
        text = " ".join(
            [a.summary] + [c.description for c in a.possible_causes] + list(a.recommended_diagnostic_steps)
        ).lower()
        for term in banned_terms:
            check(f"{code} diagnosis contains no {term!r}", term not in text)


def test_39_existing_five_codes_diagnosis_does_not_regress() -> None:
    for code, stderr_text in (
        ("G0105", "error G0105 : Bad expression or missing arguments\n"),
        ("G0036", "error G0036 : Matrix dimensions are incompatible\n"),
        ("G0025", "error G0025 : Undefined symbol: 'x'\n"),
        ("G0014", "error G0014 : File not found 'x.txt'\n"),
    ):
        a = diag.diagnose_execution(_failed(stderr_text))
        check(f"{code} still diagnosed after expansion", a.diagnostic_status == diag.DiagnosticStatus.DIAGNOSED.value)
        check(f"{code} still produces catalog-verified causes", all(c.is_catalog_verified for c in a.possible_causes))


def test_40_unknown_code_still_unknown_after_catalog_expansion() -> None:
    a = diag.diagnose_execution(_failed("error G8888 : Not a real code\n"))
    check("synthetic G8888 remains unknown_error status", a.diagnostic_status == diag.DiagnosticStatus.UNKNOWN_ERROR.value)
    check("synthetic G8888 has no possible causes", a.possible_causes == ())


def run_tests() -> int:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        before = len(_failures)
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _failures.append(f"{name} raised an unexpected exception: {type(exc).__name__}: {exc}")
        if len(_failures) == before:
            print(f"PASS  {name}")
        else:
            for failure in _failures[before:]:
                print(f"FAIL  {name}: {failure}")
    print()
    print(f"{len(tests)} test function(s) run, {len(_failures)} check failure(s).")
    if _failures:
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
