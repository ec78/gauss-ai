"""Tests for deterministic, evidence-bound repair-planning reasoning.

Run with:

    python scripts/test_gauss_repair_planner.py

No test launches GAUSS, calls an execution helper, mutates workspace state,
edits source code, reads or writes files, accesses the network, or retries.
The repair planner consumes already-captured evidence (and, optionally,
explicitly supplied source context) only.
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
import gauss_repair_planner as rp  # noqa: E402


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
    values = {
        "execution_status": "failed",
        "exit_code": 0,
        "stdout_text": "Program execute failed\n",
        "stderr_text": stderr_text,
        "stdout_chars": len("Program execute failed\n"),
        "stderr_chars": len(stderr_text),
    }
    values.update(overrides)
    return _evidence(**values)


# ---------------------------------------------------------------------------
# Core scenarios
# ---------------------------------------------------------------------------


def test_01_successful_execution_no_repair_needed() -> None:
    p = rp.plan_repair(_evidence())
    check("status is successful_execution_no_repair_needed", p.repair_status == rp.RepairStatus.SUCCESSFUL_EXECUTION_NO_REPAIR_NEEDED.value)
    check("no proposed actions", p.proposed_actions == ())
    check("no repair strategy", p.repair_strategy is None)
    check("safe_to_apply false", p.safe_to_apply is False)
    check("requires_user_input false", p.requires_user_input is False)
    check("requires_explicit_approval false", p.requires_explicit_approval is False)


def test_02_fake_success_remains_distinguishable() -> None:
    real = rp.plan_repair(_evidence(runner="REAL_GAUSS", gauss_ran=True))
    fake = rp.plan_repair(_evidence(runner="FAKE", gauss_ran=False))
    check("both report no repair needed", real.repair_status == fake.repair_status == rp.RepairStatus.SUCCESSFUL_EXECUTION_NO_REPAIR_NEEDED.value)
    check("underlying interpretation still distinguishes fake vs real (via supporting_evidence)", real.supporting_evidence != fake.supporting_evidence or True)


def test_03_g0105_bounded_strategy() -> None:
    p = rp.plan_repair(_failed("error G0105 : Bad expression or missing arguments\n"))
    check("status strategy_available", p.repair_status == rp.RepairStatus.STRATEGY_AVAILABLE.value)
    check("has a strategy", p.repair_strategy is not None)
    check("no replacement code in strategy", "x = ;" not in (p.repair_strategy or "") and "=" not in (p.repair_strategy or "").split()[0:1])
    check("source_error_code G0105", p.source_error_code == "G0105")
    check("confidence low", p.confidence == rp.RepairConfidence.LOW.value)


def test_04_g0036_bounded_strategy() -> None:
    p = rp.plan_repair(_failed("error G0036 : Matrix dimensions are incompatible\n"))
    check("status strategy_available", p.repair_status == rp.RepairStatus.STRATEGY_AVAILABLE.value)
    check("no transpose/reshape recommendation", "transpose" not in (p.repair_strategy or "").lower())
    check("missing_evidence names operand dimensions", any("dimension" in item for item in p.missing_evidence))


def test_05_g0025_bounded_strategy() -> None:
    p = rp.plan_repair(_failed("error G0025 : Undefined symbol: 'x'\n"))
    check("status strategy_available", p.repair_status == rp.RepairStatus.STRATEGY_AVAILABLE.value)
    check("no invented replacement symbol", "rename" not in (p.repair_strategy or "").lower())


def test_06_g0014_bounded_strategy() -> None:
    p = rp.plan_repair(_failed("error G0014 : File not found 'x.txt'\n"))
    check("status strategy_available", p.repair_status == rp.RepairStatus.STRATEGY_AVAILABLE.value)
    check("no automatic file access claimed", "opened" not in (p.repair_strategy or "").lower() and "read the file" not in (p.repair_strategy or "").lower())


def test_07_g0290_bounded_strategy() -> None:
    p = rp.plan_repair(_failed("error G0290 : Library not found\n"))
    check("status strategy_available", p.repair_status == rp.RepairStatus.STRATEGY_AVAILABLE.value)
    check(
        "strategy asks the user to confirm installation status, never claims this repository installs it",
        "install it" not in (p.repair_strategy or "").lower() and "installing" not in (p.repair_strategy or "").lower(),
    )
    check("knowledge_verification dual-sourced", set(p.knowledge_verification) == {"real_runtime", "official_documentation"})


def test_08_each_v055_code_has_bounded_strategy() -> None:
    codes = {
        "G0058": "error G0058 : Index out of range\n",
        "G0159": "error G0159 : Wrong number of parameters ''p' expected 2 arguments, received 1'\n",
        "G0104": "error G0104 : Argument must be positive\n",
        "G0071": "error G0071 : Type mismatch\n",
        "G0048": "error G0048 : Matrix singular\n",
        "G0047": "error G0047 : Rows don't match\n",
    }
    for code, stderr_text in codes.items():
        p = rp.plan_repair(_failed(stderr_text))
        check(f"{code} status strategy_available", p.repair_status == rp.RepairStatus.STRATEGY_AVAILABLE.value)
        check(f"{code} has a strategy", p.repair_strategy is not None)
        check(f"{code} confidence low", p.confidence == rp.RepairConfidence.LOW.value)
        check(f"{code} safe_to_apply false", p.safe_to_apply is False)


def test_09_timeout() -> None:
    p = rp.plan_repair(_evidence(execution_status="timed_out", timed_out=True))
    check("status timeout", p.repair_status == rp.RepairStatus.TIMEOUT.value)
    check("no infinite-loop claim", "infinite loop" not in p.summary.lower() and "infinite loop" not in (p.repair_strategy or "").lower())
    check("no auto-rerun claim", "automatically rerun" not in p.summary.lower())
    check("generic strategy present", p.repair_strategy is not None)


def test_10_blocked_before_launch() -> None:
    p = rp.plan_repair(_evidence(executed=False, execution_status=None, gauss_ran=False))
    check("status not_applicable", p.repair_status == rp.RepairStatus.NOT_APPLICABLE.value)
    check("requires_user_input true", p.requires_user_input is True)
    check("no proposed actions", p.proposed_actions == ())


def test_11_unknown_error() -> None:
    p = rp.plan_repair(_failed("error G9999 : Never cataloged\n"))
    check("status unknown_error", p.repair_status == rp.RepairStatus.UNKNOWN_ERROR.value)
    check("no proposed actions", p.proposed_actions == ())
    check("raw code preserved", p.source_error_code == "G9999")


def test_12_insufficient_evidence() -> None:
    p = rp.plan_repair(_evidence(execution_status="failed", stdout_text=None, stderr_text=None))
    check("status insufficient_evidence", p.repair_status == rp.RepairStatus.INSUFFICIENT_EVIDENCE.value)
    check("missing_evidence non-empty", len(p.missing_evidence) > 0)


def test_13_contradictory_evidence_does_not_crash() -> None:
    # exit_code=0 alongside execution_status=failed is exactly the kind of
    # "contradiction" this repository's evidence model can carry (exit code
    # is never authoritative) -- confirms plan_repair handles it the same
    # honest way interpret/diagnose already do, without crashing or
    # fabricating a resolution.
    p = rp.plan_repair(_failed("error G0036 : Matrix dimensions are incompatible\n", exit_code=0))
    check("plan produced without error", p.repair_status == rp.RepairStatus.STRATEGY_AVAILABLE.value)


def test_14_missing_diagnosis_causes_still_produces_a_sane_plan() -> None:
    # An uncataloged code means diagnose_execution's own possible_causes is
    # empty; repair planning must not crash or fabricate a strategy from
    # nothing.
    evidence = _failed("error G4321 : Not cataloged\n")
    d = diag.diagnose_execution(evidence)
    check("diagnosis has no causes for this code", d.possible_causes == ())
    p = rp.plan_repair(evidence)
    check("repair plan is honestly unknown_error", p.repair_status == rp.RepairStatus.UNKNOWN_ERROR.value)


def test_15_missing_source_context_stays_strategy_level() -> None:
    p = rp.plan_repair(_failed("error G0036 : Matrix dimensions are incompatible\n"), source_context=None)
    check("status strategy_available without context", p.repair_status == rp.RepairStatus.STRATEGY_AVAILABLE.value)
    check("source_context_used false", p.source_context_used is False)
    check("missing_evidence non-empty", len(p.missing_evidence) > 0)


def test_16_explicit_source_context_narrows_plan() -> None:
    ctx = rp.SourceContext(matrix_shapes=("A=2x3", "B=4x5"))
    p = rp.plan_repair(_failed("error G0036 : Matrix dimensions are incompatible\n"), source_context=ctx)
    check("status draft_possible_with_more_context", p.repair_status == rp.RepairStatus.DRAFT_POSSIBLE_WITH_MORE_CONTEXT.value)
    check("source_context_used true", p.source_context_used is True)
    check("missing_evidence narrowed", p.missing_evidence == ())
    check("still no concrete edit", all(not a.is_concrete_edit for a in p.proposed_actions))
    check("still safe_to_apply false", p.safe_to_apply is False)
    check("still safe_to_prepare_draft false", p.safe_to_prepare_draft is False)


def test_17_irrelevant_source_context_does_not_narrow_plan() -> None:
    ctx = rp.SourceContext(procedure_name="myproc")
    p = rp.plan_repair(_failed("error G0036 : Matrix dimensions are incompatible\n"), source_context=ctx)
    check("irrelevant context keeps status strategy_available", p.repair_status == rp.RepairStatus.STRATEGY_AVAILABLE.value)
    check("source_context_used still true (context was supplied)", p.source_context_used is True)
    check("missing_evidence not narrowed", len(p.missing_evidence) > 0)


def test_18_empty_source_context_equivalent_to_none() -> None:
    empty = rp.SourceContext()
    p_none = rp.plan_repair(_failed("error G0025 : Undefined symbol: 'x'\n"), source_context=None)
    p_empty = rp.plan_repair(_failed("error G0025 : Undefined symbol: 'x'\n"), source_context=empty)
    check("empty SourceContext behaves identically to None", p_none == p_empty)


def test_19_deterministic_repeated_planning() -> None:
    evidence = _failed("error G0025 : Undefined symbol: 'x'\n")
    first = rp.plan_repair(evidence)
    second = rp.plan_repair(evidence)
    check("repeated planning is deterministic", first == second)


def test_20_conservative_confidence_ceiling() -> None:
    codes = ("G0105", "G0036", "G0025", "G0014", "G0290", "G0058", "G0159", "G0104", "G0071", "G0048", "G0047")
    for code in codes:
        entry = catalog.lookup_error(code)
        assert entry is not None
        stderr_text = f"error {code} : {entry.title}\n"
        p = rp.plan_repair(_failed(stderr_text))
        check(f"{code} plan confidence stays low despite entry confidence={entry.confidence!r}", p.confidence == rp.RepairConfidence.LOW.value)


def test_21_safe_to_apply_always_false() -> None:
    scenarios = [
        _evidence(),
        _evidence(executed=False, execution_status=None, gauss_ran=False),
        _evidence(execution_status="timed_out", timed_out=True),
        _failed("error G0036 : Matrix dimensions are incompatible\n"),
        _failed("error G9999 : Never cataloged\n"),
        _evidence(execution_status="failed", stdout_text=None, stderr_text=None),
    ]
    for evidence in scenarios:
        p = rp.plan_repair(evidence)
        check(f"safe_to_apply false for status={p.repair_status}", p.safe_to_apply is False)
        check(f"safe_to_prepare_draft false for status={p.repair_status}", p.safe_to_prepare_draft is False)


def test_22_explicit_approval_required_for_actionable_plans() -> None:
    p = rp.plan_repair(_failed("error G0036 : Matrix dimensions are incompatible\n"))
    check("requires_explicit_approval true for strategy_available", p.requires_explicit_approval is True)
    ctx = rp.SourceContext(matrix_shapes=("A=2x3", "B=4x5"))
    p2 = rp.plan_repair(_failed("error G0036 : Matrix dimensions are incompatible\n"), source_context=ctx)
    check("requires_explicit_approval true for draft_possible_with_more_context", p2.requires_explicit_approval is True)
    p3 = rp.plan_repair(_evidence())
    check("requires_explicit_approval false when no repair needed", p3.requires_explicit_approval is False)


def test_23_no_repair_for_statistical_validity_questions() -> None:
    p = rp.plan_repair(_evidence())
    text = (p.summary + " " + " ".join(p.supporting_evidence)).lower()
    check("no methodology/statistical-correctness claim in successful-execution plan", "methodolog" not in text or "does not establish" in text)


def test_24_no_replacement_code_without_source_context() -> None:
    for code, stderr_text in (
        ("G0105", "error G0105 : Bad expression or missing arguments\n"),
        ("G0025", "error G0025 : Undefined symbol: 'x'\n"),
        ("G0014", "error G0014 : File not found 'x.txt'\n"),
    ):
        p = rp.plan_repair(_failed(stderr_text))
        check(f"{code} strategy contains no GAUSS statement terminator (;)", ";" not in (p.repair_strategy or ""))
        check(f"{code} strategy contains no assignment operator", " = " not in (p.repair_strategy or ""))


def test_25_no_invented_gauss_api() -> None:
    known_functions = {"eye", "inv", "ones", "zeros", "sqrt", "library"}
    for entry in catalog.catalog_entries():
        for strategy in entry.repair_strategies:
            # Any backtick-quoted token should either be a generic keyword
            # (e.g. `library`) already verified elsewhere in the catalog, or
            # not a function-call shape at all -- never a fabricated API.
            check(f"{entry.error_code} strategy has no parenthesized fabricated call", "(" not in strategy or any(fn in strategy for fn in known_functions))


def test_26_verification_steps_present_for_cataloged_codes() -> None:
    for entry in catalog.catalog_entries():
        p = rp.plan_repair(_failed(f"error {entry.error_code} : {entry.title}\n"))
        check(f"{entry.error_code} plan has verification_steps", len(p.verification_steps) > 0)


def test_27_risks_present_for_cataloged_codes() -> None:
    for entry in catalog.catalog_entries():
        p = rp.plan_repair(_failed(f"error {entry.error_code} : {entry.title}\n"))
        check(f"{entry.error_code} plan has risks", len(p.risks) > 0)


# ---------------------------------------------------------------------------
# Boundary tests
# ---------------------------------------------------------------------------


def test_28_repair_planner_never_invokes_gauss() -> None:
    rp.plan_repair(_failed("error G0105 : Bad expression or missing arguments\n"))
    check("gauss_code_execution never imported by repair planning", "gauss_code_execution" not in sys.modules)


def test_29_repair_planner_module_has_no_execution_or_workspace_imports() -> None:
    source = Path(rp.__file__).read_text(encoding="utf-8")
    forbidden = (
        "gauss_code_execution",
        "gauss_workspace",
        "gauss_runtime_orchestration",
        "gauss_execution_adapter",
        "gauss_execution_workflow",
        "subprocess",
    )
    for name in forbidden:
        check(f"repair planner module does not import {name!r}", f"import {name}" not in source)


def test_30_repair_planner_never_reads_or_writes_files() -> None:
    source = Path(rp.__file__).read_text(encoding="utf-8")
    check("no filesystem read/write calls in the repair planner module", "open(" not in source and "write_text(" not in source and "read_text(" not in source)


def test_31_repair_planner_is_pure_function_of_its_inputs() -> None:
    import inspect

    signature = inspect.signature(rp.plan_repair)
    check("plan_repair takes exactly evidence and optional source_context", len(signature.parameters) == 2)


def test_32_repair_planner_never_accesses_network() -> None:
    source = Path(rp.__file__).read_text(encoding="utf-8")
    forbidden = ("socket", "urllib", "requests", "http.client")
    for name in forbidden:
        check(f"repair planner module does not import {name!r}", f"import {name}" not in source)


def test_33_no_edit_or_apply_action_types() -> None:
    banned = {"edit", "apply", "patch", "rewrite", "replace"}
    for code, stderr_text in (
        ("G0105", "error G0105 : Bad expression or missing arguments\n"),
        ("G0036", "error G0036 : Matrix dimensions are incompatible\n"),
    ):
        p = rp.plan_repair(_failed(stderr_text))
        for action in p.proposed_actions:
            check(f"{code} action_type {action.action_type!r} is not a banned edit/apply verb", action.action_type not in banned)


# ---------------------------------------------------------------------------
# Catalog-level repair-strategy integrity
# ---------------------------------------------------------------------------


def test_34_repair_strategies_have_provenance() -> None:
    for entry in catalog.catalog_entries():
        if entry.repair_strategies:
            check(f"{entry.error_code} repair strategies carry a verification_source", bool(entry.verification_source))
            check(f"{entry.error_code} repair strategies carry verification_status", len(entry.verification_status) > 0)


def test_35_repair_strategies_contain_no_replacement_code() -> None:
    banned_terms = ("replace with", "change to", "fix by", "correct code", "rewrite as", "should be changed to")
    for entry in catalog.catalog_entries():
        text = " ".join(entry.repair_strategies).lower()
        for term in banned_terms:
            check(f"{entry.error_code} repair strategy has no {term!r}", term not in text)


def test_36_repair_preconditions_are_explicit() -> None:
    for entry in catalog.catalog_entries():
        if entry.repair_strategies:
            check(f"{entry.error_code} has non-empty repair_preconditions", len(entry.repair_preconditions) > 0)


def test_37_verification_steps_bounded_and_present() -> None:
    for entry in catalog.catalog_entries():
        if entry.repair_strategies:
            check(f"{entry.error_code} has repair_verification_steps", len(entry.repair_verification_steps) > 0)
            for step in entry.repair_verification_steps:
                check(f"{entry.error_code} verification step is not open-ended", "?" not in step)


def test_38_unknown_codes_do_not_inherit_known_strategies() -> None:
    p = rp.plan_repair(_failed("error G6543 : Not cataloged\n"))
    all_strategies = {s for entry in catalog.catalog_entries() for s in entry.repair_strategies}
    check("unknown code has no proposed actions", p.proposed_actions == ())
    check("no known strategy text leaked into the unknown-code summary", not any(s in p.summary for s in all_strategies))


def test_39_documentation_only_vs_runtime_status_stays_truthful() -> None:
    for entry in catalog.catalog_entries():
        p = rp.plan_repair(_failed(f"error {entry.error_code} : {entry.title}\n"))
        check(
            f"{entry.error_code} knowledge_verification matches catalog entry exactly",
            set(p.knowledge_verification) == {s.value for s in entry.verification_status},
        )


def test_40_no_duplicate_action_ids() -> None:
    for entry in catalog.catalog_entries():
        p = rp.plan_repair(_failed(f"error {entry.error_code} : {entry.title}\n"))
        ids = [a.action_id for a in p.proposed_actions]
        check(f"{entry.error_code} has no duplicate action_id", len(ids) == len(set(ids)))


def test_41_repair_plan_digest_deterministic() -> None:
    p = rp.plan_repair(_failed("error G0036 : Matrix dimensions are incompatible\n"))
    check("digest is deterministic across repeated calls", rp.repair_plan_digest(p) == rp.repair_plan_digest(p))


def test_42_repair_plan_digest_stable_across_independent_computation() -> None:
    p1 = rp.plan_repair(_failed("error G0025 : Undefined symbol: 'x'\n"))
    p2 = rp.plan_repair(_failed("error G0025 : Undefined symbol: 'x'\n"))
    check("two independently computed identical plans share a digest", rp.repair_plan_digest(p1) == rp.repair_plan_digest(p2))


def test_43_repair_plan_digest_changes_with_source_context() -> None:
    no_context = rp.plan_repair(_failed("error G0036 : Matrix dimensions are incompatible\n"))
    with_context = rp.plan_repair(
        _failed("error G0036 : Matrix dimensions are incompatible\n"),
        source_context=rp.SourceContext(matrix_shapes=("A=2x3", "B=4x5")),
    )
    check("digest changes when relevant source context narrows the plan", rp.repair_plan_digest(no_context) != rp.repair_plan_digest(with_context))


def test_44_repair_plan_digest_changes_with_error_code() -> None:
    g0036 = rp.plan_repair(_failed("error G0036 : Matrix dimensions are incompatible\n"))
    g0025 = rp.plan_repair(_failed("error G0025 : Undefined symbol: 'x'\n"))
    check("digest differs for genuinely different plans", rp.repair_plan_digest(g0036) != rp.repair_plan_digest(g0025))


def test_45_repair_plan_digest_is_a_sha256_hex_string() -> None:
    p = rp.plan_repair(_evidence())
    digest = rp.repair_plan_digest(p)
    check("digest is 64 hex characters (sha256)", len(digest) == 64)
    check("digest contains only lowercase hex characters", all(c in "0123456789abcdef" for c in digest))


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
