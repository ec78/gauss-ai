"""Tests for `gauss_execution_handoff.py` (v0.78.0, Controlled Execution
Handoff).

Run with:

    python scripts/test_gauss_execution_handoff.py

Every test is deterministic and network-free. No test constructs a real
`gauss_execution_adapter.load_real_helper()` -- every helper here is a local
fake matching `gauss_execution_adapter.HelperCallable`'s structural shape.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_execution_handoff as handoff  # noqa: E402
import gauss_pre_execution_validation as validation_mod  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


HANDOFF_CANDIDATE = validation_mod.HandoffReadiness.HANDOFF_CANDIDATE.value
NOT_READY = validation_mod.HandoffReadiness.NOT_READY.value
REVIEW_REQUIRED = validation_mod.HandoffReadiness.REVIEW_REQUIRED.value


def _make_request(**overrides) -> "handoff.ExecutionHandoffRequest":
    defaults = dict(
        code="print 1+1;",
        readiness_state=HANDOFF_CANDIDATE,
        request_id="req-1",
        created_at="2026-09-19T00:00:00Z",
        runner="fake",
        executable_path=None,
        gauss_version=None,
        timeout_seconds=30.0,
        workspace_parent=None,
    )
    defaults.update(overrides)
    return handoff.create_execution_handoff_request(**defaults)


def _success_helper(**kwargs):
    return {
        "executed": True, "execution_status": "completed", "exit_code": 0,
        "stdout": "2", "stderr": "", "output_files": [], "warnings": [], "errors": [],
    }


def _gauss_error_helper(**kwargs):
    return {
        "executed": True, "execution_status": "failed", "exit_code": 1,
        "stdout": "", "stderr": "error G0001: syntax error", "output_files": [], "warnings": [], "errors": [],
    }


def _timeout_helper(**kwargs):
    return {
        "executed": False, "execution_status": "timed_out", "exit_code": None,
        "stdout": None, "stderr": None, "output_files": [], "warnings": [], "errors": [],
    }


# ---------------------------------------------------------------------------
# Request: eligibility gate
# ---------------------------------------------------------------------------


def test_01_handoff_candidate_required() -> None:
    for bad_state in (NOT_READY, REVIEW_REQUIRED, "not_a_real_state", ""):
        try:
            _make_request(readiness_state=bad_state)
            check(f"readiness_state={bad_state!r} raises HandoffNotEligibleError", False)
        except handoff.HandoffNotEligibleError:
            check(f"readiness_state={bad_state!r} raises HandoffNotEligibleError", True)


def test_02_handoff_candidate_succeeds() -> None:
    req = _make_request()
    check("request built for HANDOFF_CANDIDATE", req.readiness_state == HANDOFF_CANDIDATE)


def test_03_empty_code_rejected() -> None:
    for bad_code in ("", "   ", None):
        try:
            _make_request(code=bad_code)
            check(f"code={bad_code!r} raises HandoffRequestValidationError", False)
        except handoff.HandoffRequestValidationError:
            check(f"code={bad_code!r} raises HandoffRequestValidationError", True)


def test_04_invalid_timeout_rejected() -> None:
    for bad_timeout in (0, -1, -30.0):
        try:
            _make_request(timeout_seconds=bad_timeout)
            check(f"timeout={bad_timeout!r} rejected", False)
        except handoff.HandoffRequestValidationError:
            check(f"timeout={bad_timeout!r} rejected", True)


def test_05_unsupported_runner_rejected() -> None:
    try:
        _make_request(runner="subprocess")
        check("unsupported runner rejected", False)
    except handoff.HandoffRequestValidationError:
        check("unsupported runner rejected", True)


def test_06_gauss_runner_requires_executable() -> None:
    try:
        _make_request(runner="gauss", executable_path=None)
        check("gauss runner without executable_path rejected", False)
    except handoff.HandoffRequestValidationError:
        check("gauss runner without executable_path rejected", True)
    req = _make_request(runner="gauss", executable_path="C:/gauss26/tgauss.exe")
    check("gauss runner with executable_path accepted", req.executable_path == "C:/gauss26/tgauss.exe")


# ---------------------------------------------------------------------------
# Request: digest determinism and mutation sensitivity
# ---------------------------------------------------------------------------


def test_07_same_inputs_same_digest() -> None:
    a = _make_request(request_id="a", created_at="t1")
    b = _make_request(request_id="b", created_at="t2")
    check("identical execution-affecting fields -> identical digest", a.digest == b.digest)
    check("request_id difference does not affect digest", a.digest == b.digest)


def test_08_code_mutation_changes_digest() -> None:
    a = _make_request(code="print 1+1;")
    b = _make_request(code="print 1+2;")
    check("one-character code change -> different digest", a.digest != b.digest)


def test_09_runner_mutation_changes_digest() -> None:
    a = _make_request(runner="fake")
    b = _make_request(runner="gauss", executable_path="C:/gauss26/tgauss.exe")
    check("runner change -> different digest", a.digest != b.digest)


def test_10_executable_mutation_changes_digest() -> None:
    a = _make_request(runner="gauss", executable_path="C:/gauss26/tgauss.exe")
    b = _make_request(runner="gauss", executable_path="C:/other/tgauss.exe")
    check("executable_path change -> different digest", a.digest != b.digest)


def test_11_timeout_mutation_changes_digest() -> None:
    a = _make_request(timeout_seconds=30.0)
    b = _make_request(timeout_seconds=60.0)
    check("timeout change -> different digest", a.digest != b.digest)


def test_12_workspace_mutation_changes_digest() -> None:
    a = _make_request(workspace_parent=None)
    b = _make_request(workspace_parent="C:/workspaces")
    check("workspace_parent change -> different digest", a.digest != b.digest)


def test_13_gauss_version_mutation_changes_digest() -> None:
    a = _make_request(gauss_version=None)
    b = _make_request(gauss_version="GAUSS 26")
    check("gauss_version change -> different digest", a.digest != b.digest)


def test_14_request_is_immutable() -> None:
    req = _make_request()
    try:
        req.code = "print 999;"  # type: ignore[misc]
        check("mutating a frozen request raises", False)
    except Exception:
        check("mutating a frozen request raises", True)


def test_15_recompute_digest_matches() -> None:
    req = _make_request()
    check("recompute_digest matches recorded digest", req.recompute_digest() == req.digest)


def test_16_exact_textual_code_binding_no_normalization() -> None:
    a = _make_request(code="print 1+1;\r\n")
    b = _make_request(code="print 1+1;\n")
    check("CRLF vs LF code text is NOT normalized before hashing (exact binding)", a.digest != b.digest)


# ---------------------------------------------------------------------------
# Approval: binding and immutability
# ---------------------------------------------------------------------------


def test_17_approval_binds_exact_request_digest() -> None:
    req = _make_request()
    approval = handoff.create_execution_handoff_approval(
        req, decision="approved", approval_id="ap-1", decided_at="t"
    )
    check("approval.request_digest == request.digest", approval.request_digest == req.digest)


def test_18_approve_and_decline() -> None:
    req = _make_request()
    approved = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="ap-2", decided_at="t")
    declined = handoff.create_execution_handoff_approval(req, decision="declined", approval_id="ap-3", decided_at="t")
    check("approved decision recorded", approved.decision == "approved")
    check("declined decision recorded", declined.decision == "declined")


def test_19_approval_immutable() -> None:
    req = _make_request()
    approval = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="ap-4", decided_at="t")
    try:
        approval.decision = "declined"  # type: ignore[misc]
        check("mutating a frozen approval raises", False)
    except Exception:
        check("mutating a frozen approval raises", True)


def test_20_approval_for_a_cannot_authorize_b() -> None:
    req_a = _make_request(code="print 1+1;")
    req_b = _make_request(code="print 2+2;")
    approval_a = handoff.create_execution_handoff_approval(req_a, decision="approved", approval_id="ap-5", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval_a)
    result = handoff.execute_execution_handoff(req_b, approval_a, store=store, helper=_success_helper)
    check("approval for request A cannot authorize request B", not result.launched)
    check("mismatch classified as APPROVAL_MISMATCH", result.outcome == handoff.HandoffOutcome.APPROVAL_MISMATCH.value)


def test_21_invalid_decision_rejected() -> None:
    req = _make_request()
    try:
        handoff.create_execution_handoff_approval(req, decision="maybe", approval_id="ap-6", decided_at="t")
        check("invalid decision literal rejected", False)
    except handoff.ExecutionApprovalValidationError:
        check("invalid decision literal rejected", True)


# ---------------------------------------------------------------------------
# Pre-launch gate
# ---------------------------------------------------------------------------


def test_22_missing_approval_style_mismatch_blocks() -> None:
    # "Missing approval" is represented at the orchestration layer by simply
    # not calling execute_execution_handoff at all; here we prove the
    # analogous case of an approval that does not match blocks cleanly
    # (covered fully by test_20). This test proves a declined approval
    # blocks even when digests match exactly.
    req = _make_request()
    declined = handoff.create_execution_handoff_approval(req, decision="declined", approval_id="ap-7", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(declined)
    result = handoff.execute_execution_handoff(req, declined, store=store, helper=_success_helper)
    check("declined approval blocks execution", not result.launched)
    check("declined classified as DECLINED", result.outcome == handoff.HandoffOutcome.DECLINED.value)


def test_23_declined_cannot_become_approved_later() -> None:
    req = _make_request()
    declined = handoff.create_execution_handoff_approval(req, decision="declined", approval_id="ap-8", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(declined)
    # Attempting to execute the SAME declined approval object twice must
    # both times block -- there is no "upgrade" path.
    r1 = handoff.execute_execution_handoff(req, declined, store=store, helper=_success_helper)
    r2 = handoff.execute_execution_handoff(req, declined, store=store, helper=_success_helper)
    check("declined blocks first attempt", not r1.launched)
    check("declined blocks second attempt identically", not r2.launched and r2.outcome == handoff.HandoffOutcome.DECLINED.value)


def test_24_stale_request_blocked() -> None:
    req = _make_request()
    approval = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="ap-9", decided_at="t")
    # Simulate staleness by constructing a request-like object whose
    # recompute_digest() would differ -- achieved here by hand-building a
    # request with a mismatched stored digest via object.__setattr__,
    # exactly mirroring how frozen-dataclass staleness could only arise
    # from an external inconsistency, never from this module's own code.
    import dataclasses
    tampered = dataclasses.replace(req)
    object.__setattr__(tampered, "digest", "0" * 64)
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval)
    result = handoff.execute_execution_handoff(tampered, approval, store=store, helper=_success_helper)
    check("tampered/stale request blocks execution", not result.launched)
    # digest mismatch is detected as APPROVAL_MISMATCH first (approval was
    # bound to the original digest) -- both are fail-closed outcomes.
    check(
        "stale/mismatched request classified as a blocking outcome",
        result.outcome in {handoff.HandoffOutcome.APPROVAL_MISMATCH.value, handoff.HandoffOutcome.STALE_REQUEST.value},
    )


def test_25_not_eligible_request_object_blocks() -> None:
    # readiness_state is itself one of the seven digest-bound fields, so a
    # request whose readiness_state is not HANDOFF_CANDIDATE will normally
    # be caught one gate earlier, as a digest/approval mismatch (proven by
    # test_24). This test isolates the dedicated NOT_ELIGIBLE defense-in-
    # depth gate (planning doc Section 4, step 5) by constructing a
    # request+approval pair whose digests are internally *consistent* with
    # each other but whose readiness_state was tampered to a non-candidate
    # value after digest computation -- the one situation this module's own
    # code can never produce, but the gate still checks for explicitly.
    import dataclasses
    req = _make_request()
    tampered_digest = handoff.compute_execution_handoff_digest(
        code=req.code, runner=req.runner, executable_path=req.executable_path,
        gauss_version=req.gauss_version, timeout_seconds=req.timeout_seconds,
        workspace_parent=req.workspace_parent, readiness_state=NOT_READY,
    )
    downgraded = dataclasses.replace(req, readiness_state=NOT_READY)
    object.__setattr__(downgraded, "digest", tampered_digest)
    check("tampered request's digest recomputes consistently", downgraded.recompute_digest() == downgraded.digest)
    approval = handoff.create_execution_handoff_approval(
        downgraded, decision="approved", approval_id="ap-10", decided_at="t"
    )
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval)
    result = handoff.execute_execution_handoff(downgraded, approval, store=store, helper=_success_helper)
    check("non-HANDOFF_CANDIDATE request blocks even with self-consistent digest", not result.launched)
    check("classified as NOT_ELIGIBLE", result.outcome == handoff.HandoffOutcome.NOT_ELIGIBLE.value)


# ---------------------------------------------------------------------------
# Consumption / replay semantics
# ---------------------------------------------------------------------------


def test_26_fake_success_end_to_end() -> None:
    req = _make_request()
    approval = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="ap-11", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval)
    result = handoff.execute_execution_handoff(req, approval, store=store, helper=_success_helper)
    check("fake success launched", result.launched)
    check("fake success outcome SUCCESS", result.outcome == handoff.HandoffOutcome.SUCCESS.value)
    check("result binds request digest", result.request_digest == req.digest)
    check("result binds approval id", result.approval_id == approval.approval_id)
    check("evidence present", result.evidence is not None)


def test_27_replay_after_success_blocked() -> None:
    req = _make_request()
    approval = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="ap-12", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval)
    first = handoff.execute_execution_handoff(req, approval, store=store, helper=_success_helper)
    second = handoff.execute_execution_handoff(req, approval, store=store, helper=_success_helper)
    check("first execution launches", first.launched)
    check("replay after success is blocked", not second.launched)
    check("replay classified as ALREADY_CONSUMED", second.outcome == handoff.HandoffOutcome.ALREADY_CONSUMED.value)


def test_28_gauss_error_consumes_approval() -> None:
    req = _make_request()
    approval = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="ap-13", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval)
    first = handoff.execute_execution_handoff(req, approval, store=store, helper=_gauss_error_helper)
    check("GAUSS error still launches (executed the attempt)", first.launched)
    check("GAUSS error classified EXECUTION_FAILED", first.outcome == handoff.HandoffOutcome.EXECUTION_FAILED.value)
    replay = handoff.execute_execution_handoff(req, approval, store=store, helper=_success_helper)
    check("replay after GAUSS error is blocked (consumed)", not replay.launched)
    check("replay after failure classified ALREADY_CONSUMED", replay.outcome == handoff.HandoffOutcome.ALREADY_CONSUMED.value)


def test_29_timeout_consumes_approval() -> None:
    req = _make_request()
    approval = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="ap-14", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval)
    first = handoff.execute_execution_handoff(req, approval, store=store, helper=_timeout_helper)
    check("timeout still launches (attempt was made)", first.launched)
    check("timeout classified EXECUTION_TIMEOUT", first.outcome == handoff.HandoffOutcome.EXECUTION_TIMEOUT.value)
    replay = handoff.execute_execution_handoff(req, approval, store=store, helper=_success_helper)
    check("replay after timeout is blocked", not replay.launched)
    check("replay after timeout classified ALREADY_CONSUMED", replay.outcome == handoff.HandoffOutcome.ALREADY_CONSUMED.value)


def test_30_adapter_prelaunch_rejection_does_not_consume() -> None:
    # runner "gauss" with a bogus, non-tgauss executable name -> the
    # EXISTING adapter's own executable-allowlist guard rejects BEFORE
    # calling the helper at all (outcome.invoked is False) -- deterministically
    # provable non-launch, so this must NOT consume the approval.
    req = _make_request(runner="gauss", executable_path="C:/not_gauss/notepad.exe")
    approval = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="ap-15", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval)

    def _never_called(**kwargs):
        check("helper is never called when adapter rejects pre-invocation", False)
        return _success_helper(**kwargs)

    result = handoff.execute_execution_handoff(req, approval, store=store, helper=_never_called)
    check("adapter pre-invocation rejection is not launched", not result.launched)
    check("classified INFRASTRUCTURE_FAILURE", result.outcome == handoff.HandoffOutcome.INFRASTRUCTURE_FAILURE.value)
    check("approval NOT consumed after a proven non-launch", not store.is_consumed(approval.approval_id))

    # Because it was not consumed, a corrected request (e.g. a real
    # executable) could still legitimately use a FRESH approval later --
    # this does not happen automatically; it requires a brand new explicit
    # approval, proven here by simply using a fresh approval for a fresh,
    # corrected request rather than reusing this one.
    corrected_req = _make_request(runner="fake")
    corrected_approval = handoff.create_execution_handoff_approval(
        corrected_req, decision="approved", approval_id="ap-16", decided_at="t"
    )
    store.record(corrected_approval)
    corrected_result = handoff.execute_execution_handoff(
        corrected_req, corrected_approval, store=store, helper=_success_helper
    )
    check("a fresh request+approval after a non-launch succeeds normally", corrected_result.launched)


# ---------------------------------------------------------------------------
# Approval-response parsing (Phase 6)
# ---------------------------------------------------------------------------


def test_31_approval_parser_narrow_affirmative() -> None:
    for text in ("yes", "YES", " Yes ", "approve", "Approve"):
        check(f"{text!r} parses as approved", handoff.parse_execution_approval_response(text) == "approved")


def test_32_approval_parser_narrow_negative() -> None:
    for text in ("no", "NO", "decline", " Decline "):
        check(f"{text!r} parses as declined", handoff.parse_execution_approval_response(text) == "declined")


def test_33_approval_parser_rejects_ambiguous_phrases() -> None:
    for text in ("okay", "sure", "looks good", "go ahead", "probably", "I think so", "y", "yeah", ""):
        check(
            f"{text!r} is NOT treated as approval or decline",
            handoff.parse_execution_approval_response(text) == "unrecognized",
        )


def test_34_execution_trigger_phrase_detection() -> None:
    for text in ("run this", "Run This Code", "execute this", "EXECUTE THIS CODE"):
        check(f"{text!r} recognized as an execution trigger", handoff.looks_like_execution_request(text))
    for text in ("run", "please run this for me", "what does reshape do", ""):
        check(f"{text!r} NOT recognized as an execution trigger (narrow set only)", not handoff.looks_like_execution_request(text))


# ---------------------------------------------------------------------------
# select_helper / runner selection
# ---------------------------------------------------------------------------


def test_35_select_helper_fake() -> None:
    fake = handoff.select_helper("fake")
    result = fake(code="print 1;")
    check("fake helper returns a structurally valid dict", result.get("execution_status") == "completed")


def test_36_select_helper_rejects_unsupported() -> None:
    try:
        handoff.select_helper("subprocess")
        check("select_helper rejects unsupported runner", False)
    except handoff.HandoffRequestValidationError:
        check("select_helper rejects unsupported runner", True)


# ---------------------------------------------------------------------------
# Result digest chain
# ---------------------------------------------------------------------------


def test_37_result_digest_chain_consistency() -> None:
    req = _make_request()
    approval = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="ap-17", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval)
    result = handoff.execute_execution_handoff(req, approval, store=store, helper=_success_helper)
    check("request digest == approval request_digest", req.digest == approval.request_digest)
    check("result request_digest == request digest", result.request_digest == req.digest)
    check("result approval_id == approval approval_id", result.approval_id == approval.approval_id)
    check("result_digest is a 64-hex-char sha256", len(result.result_digest) == 64)


# ---------------------------------------------------------------------------
# Rendering (pure formatting, no I/O) -- shows exact code
# ---------------------------------------------------------------------------


def test_38_render_prompt_shows_exact_code() -> None:
    req = _make_request(code="x = 1;\ny = 2;")
    rendered = handoff.render_execution_handoff_prompt(req)
    check("rendered prompt contains exact code", "x = 1;\ny = 2;" in rendered)
    check("rendered prompt discloses not-yet-executed", "has not been executed" in rendered)
    check("rendered prompt discloses methodological-validity caveat", "methodological validity" in rendered)
    check("rendered prompt shows digest", req.digest in rendered)


def test_39_render_result_success_and_failure() -> None:
    req = _make_request()
    approval = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="ap-18", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval)
    success = handoff.execute_execution_handoff(req, approval, store=store, helper=_success_helper)
    rendered_success = handoff.render_conversational_execution_result(success)
    check("success rendering mentions completion", "completed" in rendered_success.lower())
    check("success rendering has methodological caveat", "methodological correctness" in rendered_success)

    req2 = _make_request(code="bad code")
    approval2 = handoff.create_execution_handoff_approval(req2, decision="approved", approval_id="ap-19", decided_at="t")
    store.record(approval2)
    failure = handoff.execute_execution_handoff(req2, approval2, store=store, helper=_gauss_error_helper)
    rendered_failure = handoff.render_conversational_execution_result(failure)
    check("failure rendering states no retry/repair", "No retry or repair was attempted" in rendered_failure)


# ---------------------------------------------------------------------------
# Structural safety: no subprocess, no conversational-module import path
# ---------------------------------------------------------------------------


def test_40_module_never_imports_subprocess() -> None:
    source = Path(handoff.__file__).read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            check(f"import line {stripped!r} does not import subprocess", "subprocess" not in stripped)


def test_41_module_never_imports_real_helper_module_directly() -> None:
    source = Path(handoff.__file__).read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            check(
                f"import line {stripped!r} does not import gauss_code_execution directly",
                "gauss_code_execution" not in stripped,
            )


def test_42_module_never_imports_conversational_modules() -> None:
    forbidden = ("gauss_conversation_engine", "gauss_ai_chat", "gauss_chat_provider", "command_doc_lookup")
    source = Path(handoff.__file__).read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            for token in forbidden:
                check(f"import line {stripped!r} does not reference {token!r}", token not in stripped)


def test_43_conversation_engine_never_imports_execution_modules() -> None:
    forbidden = ("gauss_execution_handoff", "gauss_execution_adapter", "gauss_code_execution", "subprocess")
    for module_file in ("gauss_conversation_engine.py", "gauss_chat_provider.py", "command_doc_lookup.py"):
        source = (Path(handoff.__file__).resolve().parent / module_file).read_text(encoding="utf-8")
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                for token in forbidden:
                    check(
                        f"{module_file}: import line {stripped!r} does not reference {token!r}",
                        token not in stripped,
                    )


def test_44_model_cannot_approve_or_reuse_consumed_approval() -> None:
    # There is no function in this module that accepts model/provider output
    # and returns an ExecutionHandoffApproval directly -- the only builder
    # (create_execution_handoff_approval) requires an explicit `decision`
    # string that must already be "approved"/"declined", themselves only
    # produced by parse_execution_approval_response(...) from a raw
    # user-typed string. This test proves the store also structurally
    # refuses to let a consumed approval be marked reusable.
    req = _make_request()
    approval = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="ap-20", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval)
    handoff.execute_execution_handoff(req, approval, store=store, helper=_success_helper)
    check("approval is consumed after one execution", store.is_consumed(approval.approval_id))
    # No API exists to "unconsume" -- confirmed by absence, not by call.
    check(
        "ExecutionHandoffApprovalStore exposes no un-consume/reset method",
        not hasattr(store, "unconsume") and not hasattr(store, "reset_consumption"),
    )


def test_45_duplicate_approval_id_rejected() -> None:
    req = _make_request()
    approval = handoff.create_execution_handoff_approval(req, decision="approved", approval_id="dup-1", decided_at="t")
    store = handoff.ExecutionHandoffApprovalStore()
    store.record(approval)
    try:
        store.record(approval)
        check("duplicate approval_id rejected", False)
    except handoff.ExecutionApprovalValidationError:
        check("duplicate approval_id rejected", True)



def test_46_v087_prompt_never_shows_workspace_parent_and_says_where_code_runs() -> None:
    """v0.87.0 (live finding 77.x f3): `execute_execution_handoff` always runs
    in a fresh `tempfile.TemporaryDirectory` and never reads
    `workspace_parent`, so the prompt no longer prints it, even for a request
    built with one, and always says where code runs. The field and its
    digest position are unchanged (test_06's mutation check still holds)."""
    with_parent = handoff.render_execution_handoff_prompt(_make_request(workspace_parent="C:/workspaces"))
    without = handoff.render_execution_handoff_prompt(_make_request())
    for label, rendered in (("with a workspace parent", with_parent), ("without", without)):
        check(f"{label}: no Workspace parent line", "Workspace parent" not in rendered and "C:/workspaces" not in rendered)
        check(f"{label}: Runs in line", f"Runs in: {handoff.HANDOFF_WORKING_DIRECTORY_DESCRIPTION}" in rendered)
    check("the description says the directory is temporary and deleted",
          handoff.HANDOFF_WORKING_DIRECTORY_DESCRIPTION == "a new temporary directory, deleted after the run")


def test_47_v092_libraries_are_bound_and_shown_only_when_present() -> None:
    """v0.92.0 (planning v0.92 §3.5): the active libraries enter the digest
    and the prompt, but only when there are any -- so every request without
    `library` keeps its pre-v0.92 digest and prompt exactly."""
    plain = _make_request()
    legacy_digest = handoff.compute_execution_handoff_digest(
        code=plain.code, runner=plain.runner, executable_path=plain.executable_path,
        gauss_version=plain.gauss_version, timeout_seconds=plain.timeout_seconds,
        workspace_parent=plain.workspace_parent, readiness_state=plain.readiness_state,
    )
    check("47: no libraries: the pre-v0.92 digest", plain.digest == legacy_digest)
    check("47: no libraries: no Library line", "Library:" not in handoff.render_execution_handoff_prompt(plain))
    entry = ("gml", "C:/gauss/pkgs/gml/lib/gml.lcg", "a" * 64)
    with_library = _make_request(libraries=(entry,))
    check("47: a library changes the digest", with_library.digest != plain.digest)
    check("47: ...and recomputes to itself", with_library.recompute_digest() == with_library.digest)
    changed = _make_request(libraries=((entry[0], entry[1], "b" * 64),))
    check("47: a changed index hash changes the digest", changed.digest != with_library.digest)
    check("47: the prompt names the library and its index",
          "Library: gml (C:/gauss/pkgs/gml/lib/gml.lcg)" in handoff.render_execution_handoff_prompt(with_library))


# ---------------------------------------------------------------------------
# v0.94.0: the files a run reads and keeps (planning v0.94 §3.3)
# ---------------------------------------------------------------------------


def _v094_plan(tmp: str, content: str = "y,x\n1,2\n") -> "tuple[handoff.HandoffFilePlan, str]":
    import os
    input_dir = os.path.join(tmp, "analysis", "input")
    output_dir = os.path.join(tmp, "analysis", "output")
    os.makedirs(input_dir)
    source = os.path.join(input_dir, "prices.csv")
    with open(source, "wb") as handle:
        handle.write(content.encode("utf-8"))
    accesses = (
        validation_mod.FileAccess("loadd", "read", "prices.csv", "input", 1, source),
        validation_mod.FileAccess("loadd", "read", "prices.csv", "input", 2, source),
        validation_mod.FileAccess("csvwritem", "write", "coef.csv", "output", 3),
        validation_mod.FileAccess("plotsave", "write", "fit.png", "output", 4),
    )
    plan = handoff.build_file_plan(
        accesses, analysis_folder=os.path.join(tmp, "analysis"), input_dir=input_dir, output_dir=output_dir,
    )
    return plan, source


def test_48_v094_file_plan_is_measured_bound_and_shown() -> None:
    import hashlib
    import tempfile
    check("48: no file access -> no plan", handoff.build_file_plan(
        (), analysis_folder="a", input_dir="a/input", output_dir="a/output") is None)
    with tempfile.TemporaryDirectory() as tmp:
        plan, source = _v094_plan(tmp)
        check("48: a read is measured once", len(plan.reads) == 1 and plan.reads[0].size == len("y,x\n1,2\n"))
        check("48: ...with its SHA-256", plan.reads[0].sha256 == hashlib.sha256(b"y,x\n1,2\n").hexdigest())
        check("48: writes keep their order", plan.writes == ("coef.csv", "fit.png"))
        plain = _make_request()
        with_files = _make_request(file_plan=plan)
        check("48: a plan changes the digest", with_files.digest != plain.digest)
        check("48: ...and recomputes to itself", with_files.recompute_digest() == with_files.digest)
        other = dataclasses_replace(plan, writes=("coef.csv",))
        check("48: a different kept name changes the digest", _make_request(file_plan=other).digest != with_files.digest)
        moved = dataclasses_replace(plan, output_parent=plan.output_parent + "2")
        check("48: a different output folder changes the digest",
              _make_request(file_plan=moved).digest != with_files.digest)
        prompt = handoff.render_execution_handoff_prompt(with_files)
        check("48: the prompt names the input folder and the file",
              f"Reads (copied from {plan.input_dir}" in prompt and "prices.csv (8 bytes, sha256 " in prompt)
        check("48: the prompt names what is kept and where",
              f"Keeps (copied to a new folder under {plan.output_parent}" in prompt and "coef.csv, fit.png" in prompt)
        check("48: a request without files has no file lines",
              "Reads" not in handoff.render_execution_handoff_prompt(plain))

        import os
        os.remove(source)
        try:
            _v094_plan_again = handoff.build_file_plan(
                (validation_mod.FileAccess("loadd", "read", "prices.csv", "input", 1, source),),
                analysis_folder="a", input_dir="a/input", output_dir="a/output",
            )
            check("48: a vanished input is refused", False)
        except handoff.HandoffRequestValidationError:
            check("48: a vanished input is refused", True)


def dataclasses_replace(obj, **changes):
    import dataclasses
    return dataclasses.replace(obj, **changes)


def test_49_v094_size_caps() -> None:
    import tempfile
    saved = handoff.MAX_INPUT_FILE_BYTES, handoff.MAX_RUN_INPUT_BYTES
    try:
        with tempfile.TemporaryDirectory() as tmp:
            handoff.MAX_INPUT_FILE_BYTES = 4
            try:
                _v094_plan(tmp)
                check("49: a file over the per-file cap is refused", False)
            except handoff.HandoffRequestValidationError as exc:
                check("49: a file over the per-file cap is refused", "at most 4 bytes per file" in str(exc))
    finally:
        handoff.MAX_INPUT_FILE_BYTES, handoff.MAX_RUN_INPUT_BYTES = saved


def test_50_v094_copy_in_copy_out() -> None:
    """The helper sees only copies; only named writes are kept, in a new
    folder; other new files are listed; the user's input is never changed;
    a changed input blocks before launch."""
    import os
    import tempfile
    seen: dict = {}

    def writing_helper(**kwargs):
        run_dir = kwargs["working_directory"]
        seen["files"] = sorted(os.listdir(run_dir))
        seen["run_dir"] = run_dir
        with open(os.path.join(run_dir, "prices.csv"), "a", encoding="utf-8") as handle:
            handle.write("appended by the run\n")
        with open(os.path.join(run_dir, "coef.csv"), "w", encoding="utf-8") as handle:
            handle.write("0.5\n")
        with open(os.path.join(run_dir, "xls.log"), "w", encoding="utf-8") as handle:
            handle.write("side\n")
        return _success_helper()

    with tempfile.TemporaryDirectory() as tmp:
        plan, source = _v094_plan(tmp)
        original = open(source, encoding="utf-8").read()
        request = _make_request(file_plan=plan)
        store = handoff.ExecutionHandoffApprovalStore()
        approval = handoff.create_execution_handoff_approval(
            request, decision="approved", approval_id="a-1", decided_at="2026-11-14T00:00:00Z")
        store.record(approval)
        result = handoff.execute_execution_handoff(request, approval, store=store, helper=writing_helper)
        check("50: success", result.outcome == "success" and result.launched)
        check("50: the helper saw only the copied input", seen["files"] == ["prices.csv"])
        check("50: the user's input is unchanged", open(source, encoding="utf-8").read() == original)
        check("50: one file kept", [name for name, _p, _s in result.files_kept] == ["coef.csv"])
        kept_path = result.files_kept[0][1]
        check("50: kept in a new folder under output", os.path.dirname(kept_path) == result.output_folder
              and os.path.dirname(result.output_folder) == plan.output_parent)
        check("50: kept content is the run's", open(kept_path, encoding="utf-8").read() == "0.5\n")
        check("50: a named write not created is listed", result.files_not_created == ("fit.png",))
        check("50: a side file is listed, not kept", result.files_not_kept == ("xls.log",))
        check("50: the run directory is gone", not os.path.exists(seen["run_dir"]))
        check("50: the result names the folder", f"Files kept in {result.output_folder}"
              in handoff.render_conversational_execution_result(result))

        # A second identical run never overwrites the first.
        request2 = _make_request(file_plan=plan, request_id="req-1")
        approval2 = handoff.create_execution_handoff_approval(
            request2, decision="approved", approval_id="a-2", decided_at="2026-11-14T00:00:01Z")
        store.record(approval2)
        second = handoff.execute_execution_handoff(request2, approval2, store=store, helper=writing_helper)
        check("50: a second run keeps into another folder", second.output_folder != result.output_folder
              and open(kept_path, encoding="utf-8").read() == "0.5\n")

        # The input changes after the prompt: blocked before launch.
        with open(source, "a", encoding="utf-8") as handle:
            handle.write("3,4\n")
        calls: list = []
        approval3 = handoff.create_execution_handoff_approval(
            request, decision="approved", approval_id="a-3", decided_at="2026-11-14T00:00:02Z")
        store.record(approval3)
        blocked = handoff.execute_execution_handoff(
            request, approval3, store=store, helper=lambda **kw: calls.append(kw) or _success_helper())
        check("50: a changed input blocks the run", blocked.outcome == "execution_blocked" and not blocked.launched)
        check("50: ...before the helper is called", calls == [])
        check("50: ...saying the file changed", "changed after the prompt was shown" in (blocked.blocked_reason or ""))
        check("50: ...and the approval is not consumed", not store.is_consumed("a-3"))


def _run_all() -> int:
    test_fns = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
    for fn in test_fns:
        fn()
    if _failures:
        print(f"FAILED ({len(_failures)} issue(s)):")
        for f in _failures:
            print(f"  - {f}")
        return 1
    print(f"PASSED: {len(test_fns)} test functions, 0 failures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
