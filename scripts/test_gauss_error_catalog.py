"""Tests for the deterministic GAUSS error catalog itself, independent of
the interpreter or diagnostic engine that consume it.

Run with:

    python scripts/test_gauss_error_catalog.py

No test launches GAUSS. This module only inspects `gauss_error_catalog.py`'s
own data.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_error_catalog as catalog  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def test_01_catalog_size_matches_v0_55_0() -> None:
    check("catalog has exactly 11 entries as of v0.55.0", len(catalog.known_error_codes()) == 11)


def test_02_every_entry_has_verification_metadata() -> None:
    for entry in catalog.catalog_entries():
        check(f"{entry.error_code} declares at least one verification_status", len(entry.verification_status) > 0)
        check(f"{entry.error_code} declares a verification_source", bool(entry.verification_source))


def test_03_every_entry_verification_status_values_are_valid() -> None:
    for entry in catalog.catalog_entries():
        for status in entry.verification_status:
            check(f"{entry.error_code} status {status!r} is a real VerificationStatus", isinstance(status, catalog.VerificationStatus))


def test_04_every_entry_category_is_valid() -> None:
    for entry in catalog.catalog_entries():
        check(f"{entry.error_code} category is a real GaussErrorCategory", isinstance(entry.category, catalog.GaussErrorCategory))


def test_05_no_duplicate_codes() -> None:
    codes = [entry.error_code for entry in catalog.catalog_entries()]
    check("no duplicate error codes in the catalog", len(codes) == len(set(codes)))


def test_06_duplicate_code_construction_raises() -> None:
    duplicate = catalog.GaussErrorCatalogEntry(
        error_code="G0105",
        category=catalog.GaussErrorCategory.PARSE_SYNTAX,
        title="dup",
        generic_explanation="dup",
        execution_phase="parsing",
        confidence="high",
        recommended_next_step="dup",
        verification_status=(catalog.VerificationStatus.REAL_RUNTIME,),
        verification_source="dup",
    )
    raised = False
    try:
        catalog._build_catalog((duplicate, duplicate))  # noqa: SLF001 - intentional internal-function test
    except ValueError:
        raised = True
    check("duplicate error_code raises ValueError", raised)


def test_07_missing_verification_status_raises() -> None:
    unverified = catalog.GaussErrorCatalogEntry(
        error_code="G0001",
        category=catalog.GaussErrorCategory.UNKNOWN,
        title="unverified",
        generic_explanation="unverified",
        execution_phase="runtime",
        confidence="low",
        recommended_next_step="n/a",
        verification_status=(),
        verification_source="none",
    )
    raised = False
    try:
        catalog._build_catalog((unverified,))  # noqa: SLF001
    except ValueError:
        raised = True
    check("empty verification_status raises ValueError", raised)


def test_08_documentation_discrepancy_retained_only_where_recorded() -> None:
    g0036 = catalog.lookup_error("G0036")
    assert g0036 is not None
    check("G0036 documentation_discrepancy is recorded", g0036.documentation_discrepancy is not None)
    for entry in catalog.catalog_entries():
        if entry.error_code != "G0036":
            check(f"{entry.error_code} has no fabricated documentation_discrepancy", entry.documentation_discrepancy is None)


def test_09_documentation_only_entries_remain_labeled_correctly() -> None:
    documentation_only = [
        entry
        for entry in catalog.catalog_entries()
        if entry.verification_status == (catalog.VerificationStatus.OFFICIAL_DOCUMENTATION,)
    ]
    # v0.55.0: G0290 was upgraded to dual-sourced this milestone, so as of
    # this release no entry remains documentation-only. This test asserts
    # today's actual state rather than a hardcoded historical expectation.
    check("no entry is documentation-only as of v0.55.0", documentation_only == [])


def test_10_dual_sourced_entries_show_both_sources() -> None:
    dual_sourced_codes = {"G0105", "G0036", "G0025", "G0014", "G0290"}
    for code in dual_sourced_codes:
        entry = catalog.lookup_error(code)
        assert entry is not None
        check(
            f"{code} is dual-sourced (real runtime + official documentation)",
            set(entry.verification_status) == {catalog.VerificationStatus.REAL_RUNTIME, catalog.VerificationStatus.OFFICIAL_DOCUMENTATION},
        )


def test_11_v0_55_0_new_codes_are_real_runtime_only() -> None:
    new_codes = {"G0058", "G0159", "G0104", "G0071", "G0048", "G0047"}
    for code in new_codes:
        entry = catalog.lookup_error(code)
        assert entry is not None
        check(
            f"{code} is real-runtime verified (not yet cross-checked against documentation)",
            entry.verification_status == (catalog.VerificationStatus.REAL_RUNTIME,),
        )


def test_12_lookup_unknown_codes_returns_none() -> None:
    check("G9999 is not cataloged", catalog.lookup_error("G9999") is None)
    check("G8888 is not cataloged", catalog.lookup_error("G8888") is None)
    check("G1111 is not cataloged", catalog.lookup_error("G1111") is None)


def test_13_lookup_case_and_whitespace_normalization() -> None:
    for form in ("g0058", "G0058", " G0058 ", "g0058\n"):
        entry = catalog.lookup_error(form)
        check(f"{form!r} resolves to G0058", entry is not None and entry.error_code == "G0058")


def test_14_known_error_codes_sorted_and_unique() -> None:
    codes = catalog.known_error_codes()
    check("known_error_codes is sorted", list(codes) == sorted(codes))
    check("known_error_codes has no duplicates", len(codes) == len(set(codes)))


def test_15_new_categories_are_populated() -> None:
    for category in (
        catalog.GaussErrorCategory.INDEXING_SUBSCRIPT,
        catalog.GaussErrorCategory.ARGUMENT_VALIDATION,
        catalog.GaussErrorCategory.TYPE_MISMATCH,
        catalog.GaussErrorCategory.NUMERICAL,
    ):
        matches = [entry for entry in catalog.catalog_entries() if entry.category == category]
        check(f"{category.value} category has at least one cataloged entry", len(matches) > 0)


def test_16_still_unused_categories_remain_honestly_empty() -> None:
    for category in (
        catalog.GaussErrorCategory.STARTUP_OR_LICENSING,
        catalog.GaussErrorCategory.USER_INTERRUPTION,
        catalog.GaussErrorCategory.TIMEOUT,
        catalog.GaussErrorCategory.UNKNOWN,
    ):
        matches = [entry for entry in catalog.catalog_entries() if entry.category == category]
        check(f"{category.value} category remains uncataloged (no speculative entry added)", matches == [])


def test_17_no_repair_instruction_appears_in_any_catalog_field() -> None:
    banned_terms = ("replace with", "change to", "fix by", "correct code", "rewrite as", "should be changed")
    for entry in catalog.catalog_entries():
        text = " ".join(
            [entry.title, entry.generic_explanation, entry.recommended_next_step]
            + list(entry.known_triggers)
            + list(entry.diagnostic_questions)
            + list(entry.required_evidence_for_diagnosis)
            + list(entry.repair_strategies)
            + list(entry.repair_preconditions)
            + list(entry.repair_verification_steps)
            + list(entry.repair_risks)
        ).lower()
        for term in banned_terms:
            check(f"{entry.error_code} has no repair instruction ({term!r})", term not in text)


def test_19_all_entries_have_repair_planning_knowledge_as_of_v0_56_0() -> None:
    for entry in catalog.catalog_entries():
        check(f"{entry.error_code} has repair_strategies", len(entry.repair_strategies) > 0)
        check(f"{entry.error_code} has repair_preconditions", len(entry.repair_preconditions) > 0)
        check(f"{entry.error_code} has repair_verification_steps", len(entry.repair_verification_steps) > 0)
        check(f"{entry.error_code} has repair_risks", len(entry.repair_risks) > 0)


def test_20_repair_strategies_distinct_from_diagnostic_triggers() -> None:
    for entry in catalog.catalog_entries():
        overlap = set(entry.repair_strategies) & set(entry.known_triggers)
        check(f"{entry.error_code} repair_strategies text is distinct from known_triggers text", overlap == set())


def test_18_matrix_dimension_category_has_two_distinct_codes() -> None:
    matches = [entry for entry in catalog.catalog_entries() if entry.category == catalog.GaussErrorCategory.MATRIX_DIMENSION]
    codes = {entry.error_code for entry in matches}
    check("matrix_dimension category has G0036 and G0047 as distinct codes", codes == {"G0036", "G0047"})


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
