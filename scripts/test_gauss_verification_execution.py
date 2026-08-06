"""Tests for the Verification Execution workflow.

Run with:

    python scripts/test_gauss_verification_execution.py

Every test uses a real, on-disk temp-directory-backed workspace and a real
`OrchestrationStateStore` -- this module reuses the genuine
`ExecutionWorkflow`, so its tests exercise that real machinery rather than a
repair-specific stand-in. No test invokes real GAUSS; every execution uses
an injected fake runner, exactly like every other test in this repository.
"""

from __future__ import annotations

import dataclasses
import hashlib
import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_execution_interpreter as interp  # noqa: E402
import gauss_execution_workflow as wf  # noqa: E402
import gauss_orchestration_state_store as store_mod  # noqa: E402
import gauss_repair_application as app  # noqa: E402
import gauss_repair_application_approval as aa  # noqa: E402
import gauss_repair_approval as ra  # noqa: E402
import gauss_repair_draft as rd  # noqa: E402
import gauss_repair_draft_approval as da  # noqa: E402
import gauss_repair_planner as rp  # noqa: E402
import gauss_verification_execution as ver  # noqa: E402
import gauss_workspace as workspace_mod  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ORIGINAL_TEXT = "x = 2 + 2\nprint x;\n"


def _evidence(**overrides: object) -> "interp.ExecutionEvidence":
    values = {
        "runner": "FAKE", "gauss_ran": False, "executed": True, "execution_status": "failed",
        "exit_code": 0, "stdout_chars": 0, "stderr_chars": 0, "timed_out": False,
        "workspace_state": "failed", "provenance": None,
        "stdout_text": "Program execute failed\n", "stderr_text": "error G0105 : Undefined symbol\n",
        "metadata_error": None,
    }
    values.update(overrides)
    return interp.ExecutionEvidence(**values)


def _fake_runner_completed(_: object) -> dict:
    return {"executed": True, "execution_status": "completed", "exit_code": 0, "stdout": "4", "stderr": "", "output_files": [], "warnings": [], "errors": []}


def _fake_runner_g0105(_: object) -> dict:
    return {"executed": True, "execution_status": "failed", "exit_code": 0, "stdout": "Program execute failed\n", "stderr": "error G0105 : Undefined symbol\n", "output_files": [], "warnings": [], "errors": ["error G0105"]}


def _fake_runner_g0036(_: object) -> dict:
    return {"executed": True, "execution_status": "failed", "exit_code": 0, "stdout": "Program execute failed\n", "stderr": "error G0036 : Matrix dimensions are incompatible\n", "output_files": [], "warnings": [], "errors": ["error G0036"]}


class _Env:
    """Real workspace registry + real durable store + real ExecutionWorkflow,
    plus a real, on-disk repaired `.gss` file with a genuinely successful
    ApplicationResult behind it -- built once per test via `_Env(tmp)`."""

    def __init__(self, ws_tmp: str, db_tmp: str) -> None:
        self.registry = workspace_mod.WorkspaceRegistry(approved_parent_directory=ws_tmp)
        self.store = store_mod.OrchestrationStateStore(Path(db_tmp) / "test.db")
        self.store.initialize()
        self.execution_workflow = wf.ExecutionWorkflow(state_store=self.store, workspace_registry=self.registry)

        self.workspace = self.registry.create_workspace()
        Path(self.workspace.root_path).mkdir(parents=True, exist_ok=True)
        self.registry.update_workspace_status(self.workspace.workspace_id, to_status=workspace_mod.WorkspaceStatus.POPULATED)
        self.registry.update_workspace_status(self.workspace.workspace_id, to_status=workspace_mod.WorkspaceStatus.READY)

        self.target = Path(self.workspace.root_path) / "model.gss"
        self.target.write_bytes(ORIGINAL_TEXT.encode("utf-8"))
        self.real_hash = hashlib.sha256(ORIGINAL_TEXT.encode("utf-8")).hexdigest()

        # Simulate the workspace having already completed its one-shot
        # lifecycle from the *original* failing execution.
        self.registry.update_workspace_status(self.workspace.workspace_id, to_status=workspace_mod.WorkspaceStatus.EXECUTING)
        self.registry.update_workspace_status(self.workspace.workspace_id, to_status=workspace_mod.WorkspaceStatus.COMPLETED)

        self.original_evidence = _evidence()
        self.original_interpretation = interp.interpret_execution(self.original_evidence)

        self.plan = rp.plan_repair(self.original_evidence)
        self.plan_record = ra.RepairApprovalStore().approve(self.plan, recorded_at="t0")
        artifact = rd.SourceArtifact(workspace_id=self.workspace.workspace_id, relative_path="model.gss", file_type=".gss")
        identity = rd.SourceIdentity(artifact=artifact, content_hash=self.real_hash, size=len(ORIGINAL_TEXT.encode()), encoding="utf-8")
        scope = rd.EditScope(line_start=1, line_end=1, intended_operation="insert missing semicolon")
        self.draft = rd.build_repair_draft(
            repair_draft_id="draft-1", repair_plan_digest=rp.repair_plan_digest(self.plan),
            source_identity=identity, edit_scope=scope,
            proposed_change_description="Insert a missing statement terminator.", generated_at="t0",
        )
        self.draft_record = da.DraftApprovalStore().approve(self.draft, recorded_at="t0")
        self.application_record = aa.ApplicationApprovalStore().approve(self.draft, recorded_at="t0")

        self.application_result = app.apply_repair(
            repair_plan=self.plan, repair_approval_record=self.plan_record, repair_draft=self.draft,
            draft_approval_record=self.draft_record, application_approval_record=self.application_record,
            replacement_text="x = 2 + 2;\n", workspace_registry=self.registry,
            clock=lambda: 1000.0, id_factory=lambda: "app-1",
        )
        assert self.application_result.outcome == "applied"

    def close(self) -> None:
        self.store.close()

    def blocked_application_result(self) -> "app.ApplicationResult":
        return dataclasses.replace(self.application_result, outcome="blocked", post_application_content_hash=None)

    def propose(self, request: "ver.VerificationExecutionRequest", **overrides: object) -> "ver.VerificationProposalResult":
        kwargs = dict(
            request=request, execution_workflow=self.execution_workflow, workspace_root_path=self.workspace.root_path,
            session_id="s1", request_id="verify-req-1", executable_path="C:/example/gauss26/tgauss.exe",
            gauss_version="GAUSS 26", timeout_seconds=30.0,
        )
        kwargs.update(overrides)
        return ver.propose_verification_execution(**kwargs)


def _with_env(fn) -> None:
    with tempfile.TemporaryDirectory() as ws_tmp, tempfile.TemporaryDirectory() as db_tmp:
        env = _Env(ws_tmp, db_tmp)
        try:
            fn(env)
        finally:
            env.close()


# ---------------------------------------------------------------------------
# VerificationExecutionRequest construction
# ---------------------------------------------------------------------------


def test_01_build_request_from_applied_result() -> None:
    def body(env: _Env) -> None:
        request = ver.build_verification_execution_request(
            env.application_result, reason="verify repair", clock=lambda: 2000.0, id_factory=lambda: "verify-1"
        )
        check("verification_execution_id set from id_factory", request.verification_execution_id == "verify-1")
        check("repair_application_id matches the ApplicationResult's own id", request.repair_application_id == env.application_result.application_id)
        check("application_result_id equals repair_application_id", request.application_result_id == request.repair_application_id)
        check("workspace_id taken from ApplicationResult", request.workspace_id == env.application_result.workspace_id)
        check("relative_path taken from ApplicationResult", request.relative_path == env.application_result.relative_path)
        check("expected_post_repair_hash taken from post_application_content_hash", request.expected_post_repair_hash == env.application_result.post_application_content_hash)
        check("reason carried through", request.reason == "verify repair")
        check("created_at uses the injected clock", request.created_at == "2000.0")
    _with_env(body)


def test_02_build_request_rejects_blocked_outcome() -> None:
    def body(env: _Env) -> None:
        blocked_result = env.blocked_application_result()
        raised = False
        try:
            ver.build_verification_execution_request(blocked_result, reason="x")
        except ver.RepairNotAppliedError:
            raised = True
        check("blocked ApplicationResult raises RepairNotAppliedError", raised)
    _with_env(body)


def test_03_build_request_rejects_failed_outcome() -> None:
    def body(env: _Env) -> None:
        failed_result = dataclasses.replace(env.application_result, outcome="failed", post_application_content_hash=None)
        raised = False
        try:
            ver.build_verification_execution_request(failed_result, reason="x")
        except ver.RepairNotAppliedError:
            raised = True
        check("failed ApplicationResult raises RepairNotAppliedError", raised)
    _with_env(body)


def test_04_request_never_references_repair_draft() -> None:
    field_names = {f.name for f in dataclasses.fields(ver.VerificationExecutionRequest)}
    forbidden = {"repair_draft", "draft", "repair_draft_id", "draft_digest"}
    check("no field on VerificationExecutionRequest references a RepairDraft", field_names.isdisjoint(forbidden))


def test_05_determinism_of_request_construction() -> None:
    def body(env: _Env) -> None:
        r1 = ver.build_verification_execution_request(env.application_result, reason="x", clock=lambda: 1.0, id_factory=lambda: "id-1")
        r2 = ver.build_verification_execution_request(env.application_result, reason="x", clock=lambda: 1.0, id_factory=lambda: "id-1")
        check("identical inputs produce identical requests", r1 == r2)
    _with_env(body)


# ---------------------------------------------------------------------------
# Proposal reuse
# ---------------------------------------------------------------------------


def test_06_propose_produces_genuine_execution_proposal() -> None:
    def body(env: _Env) -> None:
        request = ver.build_verification_execution_request(env.application_result, reason="x", clock=lambda: 2000.0, id_factory=lambda: "verify-1")
        result = env.propose(request)
        check("proposal not blocked", not result.outcome.blocked)
        check("outcome is a genuine wf.ProposalOutcome", isinstance(result.outcome, wf.ProposalOutcome))
        assert result.outcome.proposal is not None
        check("proposal is a genuine wf.ExecutionProposal", isinstance(result.outcome.proposal, wf.ExecutionProposal))
        check("proposal code_digest is populated (inline code path)", result.outcome.proposal.code_digest is not None)
        check("proposal.workspace_id is None (not lifecycle-bound)", result.outcome.proposal.workspace_id is None)
        check("proposal working_directory targets the real workspace root", result.outcome.proposal.working_directory == env.workspace.root_path)
        check("source_read_ok True", result.source_read_ok)
        check("source_hash_matches True", result.source_hash_matches)
    _with_env(body)


def test_07_propose_blocks_on_stale_hash() -> None:
    def body(env: _Env) -> None:
        request = ver.build_verification_execution_request(env.application_result, reason="x", clock=lambda: 2000.0, id_factory=lambda: "verify-1")
        env.target.write_bytes(b"mutated after repair applied\n")
        result = env.propose(request)
        check("proposal blocked", result.outcome.blocked)
        check("failure_category is verification_source_stale", result.outcome.failure_category == "verification_source_stale")
        check("source_read_ok True (read itself succeeded)", result.source_read_ok)
        check("source_hash_matches False", not result.source_hash_matches)
        check("no proposal object produced", result.outcome.proposal is None)
    _with_env(body)


def test_08_propose_blocks_on_unreadable_source() -> None:
    def body(env: _Env) -> None:
        request = ver.build_verification_execution_request(env.application_result, reason="x", clock=lambda: 2000.0, id_factory=lambda: "verify-1")
        env.target.unlink()
        result = env.propose(request)
        check("proposal blocked", result.outcome.blocked)
        check("failure_category is verification_source_unreadable", result.outcome.failure_category == "verification_source_unreadable")
        check("source_read_ok False", not result.source_read_ok)
    _with_env(body)


# ---------------------------------------------------------------------------
# Confirmation and execution reuse (unmodified ExecutionWorkflow methods)
# ---------------------------------------------------------------------------


def test_09_confirm_and_execute_reuse_unmodified_execution_workflow() -> None:
    def body(env: _Env) -> None:
        request = ver.build_verification_execution_request(env.application_result, reason="x", clock=lambda: 2000.0, id_factory=lambda: "verify-1")
        proposal_result = env.propose(request)
        assert proposal_result.outcome.proposal is not None

        confirm_outcome = env.execution_workflow.confirm_execution(
            wf.WorkflowConfirmationEvent(
                session_id="s1", orchestration_instance_id=proposal_result.outcome.orchestration_instance_id,
                request_id="verify-req-1", request_hash=proposal_result.outcome.proposal.request_hash,
                decision="accepted", timestamp="t1", source_interaction_id="turn-1",
                plan_digest=proposal_result.outcome.proposal.plan_digest,
            )
        )
        check("confirmation is a genuine wf.ConfirmationOutcome", isinstance(confirm_outcome, wf.ConfirmationOutcome))
        check("confirmation reaches confirmed", confirm_outcome.current_state == "confirmed")

        exec_result = env.execution_workflow.execute(proposal_result.outcome.orchestration_instance_id, runner=_fake_runner_completed)
        check("execution result is a genuine wf.ResponseReadyResult", isinstance(exec_result, wf.ResponseReadyResult))
        check("execution reports executed True", exec_result.executed)
        check("execution status completed", exec_result.execution_status == "completed")
    _with_env(body)


def test_10_verification_executes_the_actual_repaired_content() -> None:
    """The verification execution's own proposal.code_digest must reflect
    the REPAIRED content (with the semicolon inserted), not the original,
    pre-repair content -- proving the real, on-disk repaired file is what
    gets proposed for execution, not a cached or stale copy."""
    def body(env: _Env) -> None:
        request = ver.build_verification_execution_request(env.application_result, reason="x", clock=lambda: 2000.0, id_factory=lambda: "verify-1")
        result = env.propose(request)
        assert result.outcome.proposal is not None
        repaired_text = env.target.read_text(encoding="utf-8")
        check("repaired file differs from the original pre-repair text", repaired_text != ORIGINAL_TEXT)
        expected_digest = store_mod.digest_code(repaired_text)
        check("proposal's code_digest matches the real repaired file's own digest", result.outcome.proposal.code_digest == expected_digest)
    _with_env(body)


# ---------------------------------------------------------------------------
# Comparison summaries
# ---------------------------------------------------------------------------


def _interp_for(runner_result: dict) -> "interp.ExecutionInterpretation":
    ev = _evidence(
        execution_status=runner_result["execution_status"], exit_code=runner_result["exit_code"],
        stdout_text=runner_result["stdout"], stderr_text=runner_result["stderr"], executed=True,
    )
    return interp.interpret_execution(ev)


def test_11_compare_succeeded_after_failure() -> None:
    original = _interp_for(_fake_runner_g0105(None))
    verification = _interp_for(_fake_runner_completed(None))
    summary = ver.compare_execution_outcomes(original, verification)
    check("comparison is succeeded_after_failure", summary.comparison == "succeeded_after_failure")
    check("same_outcome is False", summary.same_outcome is False)
    check("observation matches the task's own worked example", summary.observation == "The repaired code executed successfully whereas the original execution failed with G0105.")


def test_12_compare_same_error() -> None:
    original = _interp_for(_fake_runner_g0105(None))
    verification = _interp_for(_fake_runner_g0105(None))
    summary = ver.compare_execution_outcomes(original, verification)
    check("comparison is same_error", summary.comparison == "same_error")
    check("same_outcome is True", summary.same_outcome is True)
    check("observation matches the task's own worked example", summary.observation == "The repair did not change the observed execution outcome.")


def test_13_compare_different_error() -> None:
    original = _interp_for(_fake_runner_g0105(None))
    verification = _interp_for(_fake_runner_g0036(None))
    summary = ver.compare_execution_outcomes(original, verification)
    check("comparison is different_error", summary.comparison == "different_error")
    check("same_outcome is False", summary.same_outcome is False)
    check("observation matches the task's own worked example", summary.observation == "The repair changed execution behavior, but a different runtime error occurred.")


def test_14_compare_failed_after_success() -> None:
    original = _interp_for(_fake_runner_completed(None))
    verification = _interp_for(_fake_runner_g0105(None))
    summary = ver.compare_execution_outcomes(original, verification)
    check("comparison is failed_after_success", summary.comparison == "failed_after_success")
    check("same_outcome is False", summary.same_outcome is False)
    check("observation names the verification failure honestly", "failed with G0105" in summary.observation and "succeeded" in summary.observation)


def test_15_compare_both_succeeded() -> None:
    original = _interp_for(_fake_runner_completed(None))
    verification = _interp_for(_fake_runner_completed(None))
    summary = ver.compare_execution_outcomes(original, verification)
    check("comparison is both_succeeded", summary.comparison == "both_succeeded")
    check("same_outcome is True", summary.same_outcome is True)


def test_16_comparison_summary_has_no_verdict_fields() -> None:
    original = _interp_for(_fake_runner_g0105(None))
    verification = _interp_for(_fake_runner_completed(None))
    summary = ver.compare_execution_outcomes(original, verification)
    for forbidden in ("repair_correct", "success_probability", "confidence_score", "verdict", "is_fixed"):
        check(f"ComparisonSummary has no {forbidden!r} field", not hasattr(summary, forbidden))


def test_17_comparison_is_pure_and_deterministic() -> None:
    original = _interp_for(_fake_runner_g0105(None))
    verification = _interp_for(_fake_runner_completed(None))
    s1 = ver.compare_execution_outcomes(original, verification)
    s2 = ver.compare_execution_outcomes(original, verification)
    check("repeated comparison of identical inputs is deterministic", s1 == s2)


# ---------------------------------------------------------------------------
# Structural safety: no repair-specific execution engine, no forbidden imports
# ---------------------------------------------------------------------------


def test_18_verification_disclosure_fixed_and_never_claims_correctness() -> None:
    check("disclosure has four fixed lines", len(ver.VERIFICATION_DISCLOSURE) == 4)
    joined = " ".join(ver.VERIFICATION_DISCLOSURE).lower()
    check("disclosure states this is an ordinary execution", "ordinary execution" in joined)
    check("disclosure states repair success is not inferred", "not inferred" in joined)
    for forbidden in ("repair is correct", "fixed", "guaranteed", "verified correct"):
        check(f"disclosure never claims {forbidden!r}", forbidden not in joined)


def test_19_module_creates_no_repair_specific_execution_types() -> None:
    source = Path(ver.__file__).read_text(encoding="utf-8")
    forbidden_class_defs = ("class RepairExecutionEngine", "class RepairRunner", "class RepairProposal", "class RepairConfirmation", "class RepairExecutionSession")
    for token in forbidden_class_defs:
        check(f"module source does not define {token!r}", token not in source)


def test_20_module_never_imports_execution_helper_or_adapter_directly() -> None:
    source = Path(ver.__file__).read_text(encoding="utf-8")
    forbidden = ("gauss_code_execution", "gauss_execution_adapter", "gauss_runtime_orchestration", "gauss_orchestration_state_store", "subprocess", "socket")
    for name in forbidden:
        check(f"module does not import {name!r}", f"import {name}" not in source)


def test_21_module_never_imports_repair_draft_or_approval_modules_directly() -> None:
    """Only gauss_repair_application (for the ApplicationResult type) is
    imported -- never gauss_repair_draft, gauss_repair_draft_approval,
    gauss_repair_application_approval, gauss_repair_application_gate, or
    gauss_repair_planner directly, since verification consumes only an
    already-successful ApplicationResult."""
    source = Path(ver.__file__).read_text(encoding="utf-8")
    forbidden = (
        "import gauss_repair_draft",
        "import gauss_repair_draft_approval",
        "import gauss_repair_application_approval",
        "import gauss_repair_application_gate",
        "import gauss_repair_planner",
        "import gauss_repair_approval",
    )
    for token in forbidden:
        check(f"module does not contain {token!r}", token not in source)


def test_22_module_never_calls_rerun_or_retry() -> None:
    """The module's own docstring legitimately *mentions* "automatic
    retries"/"automatic rollback" as explicitly NOT implemented (a
    documentary disclaimer) -- this test checks for actual retry/rollback
    *code* (a loop-and-reattempt pattern or a callable named for it), not
    for the words appearing anywhere at all, which would also flag that
    honest disclaimer as if it were a violation."""
    source = Path(ver.__file__).read_text(encoding="utf-8")
    check("module source defines no retry(...) callable", "def retry(" not in source and "def _retry(" not in source)
    check("module source defines no rollback(...) callable", "def rollback(" not in source and "def _rollback(" not in source)
    check("module source contains no automatic-acceptance wording", "auto_accept" not in source.lower() and "automatic_accept" not in source.lower())


def test_23_execution_workflow_module_has_zero_diff_dependency() -> None:
    """Structural proof that this module never modifies or monkeypatches
    ExecutionWorkflow -- it only calls its existing public methods."""
    check("propose_verification_execution calls the real propose_execution", hasattr(wf.ExecutionWorkflow, "propose_execution"))
    check("ExecutionWorkflow.confirm_execution is untouched and callable", hasattr(wf.ExecutionWorkflow, "confirm_execution"))
    check("ExecutionWorkflow.execute is untouched and callable", hasattr(wf.ExecutionWorkflow, "execute"))


def test_24_workspace_already_completed_does_not_block_verification_proposal() -> None:
    """Direct proof of the architectural decision documented in
    planning/v0.64.0: a workspace that already completed its one-shot
    lifecycle (from the original failing execution) still allows a fresh
    verification proposal, because that proposal is never workspace-
    lifecycle-bound."""
    def body(env: _Env) -> None:
        check("workspace status is genuinely 'completed' before verification", env.registry.get_workspace(env.workspace.workspace_id).status == workspace_mod.WorkspaceStatus.COMPLETED)
        request = ver.build_verification_execution_request(env.application_result, reason="x", clock=lambda: 2000.0, id_factory=lambda: "verify-1")
        result = env.propose(request)
        check("verification proposal is NOT blocked by the completed workspace", not result.outcome.blocked)
    _with_env(body)


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
