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
