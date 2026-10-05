"""Tests for `gauss_mcp_server.py` (v0.79.0, local MCP server).

Run with:

    python scripts/test_gauss_mcp_server.py

Every test is deterministic and network-free, and never touches this
machine's own real `~/.gauss-ai/config.json`, real GAUSS executable, or real
Ollama/Anthropic endpoint -- every call below explicitly pins `provider`/
`runner`/`docs_root`/`workspace_parent` (CLI-argument precedence, which wins
over this machine's own config file and environment variables) rather than
relying on this module's config-resolution defaults, exactly the same
discipline `test_gauss_ai_chat.py`/`test_gauss_ai_guided_repair.py` already
use. Requires the optional `mcp` extra (`pip install -e ".[mcp]"`); skips
cleanly with a clear message if it is not installed.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

try:
    import gauss_mcp_server as server_mod  # noqa: E402
except ImportError as exc:
    print(f"SKIPPED: the optional 'mcp' extra is not installed ({exc}).")
    print('Install it with: pip install -e ".[mcp]" to run this test file.')
    raise SystemExit(0)

import gauss_execution_handoff as handoff_mod  # noqa: E402

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


#: Same fixture shape `test_gauss_ai_chat.py`'s own
#: `_fixture_docs_root_handoff_candidate`/`_TYPED_INV_RST` use to reach a
#: real, broad-evidence `HANDOFF_CANDIDATE` verdict deterministically.
_TYPED_INV_RST = """inv, invpd
==========

.. function:: xi = inv(x)
              xi = invpd(x)

Purpose
-------
inv returns the inverse of an invertible matrix. invpd returns the inverse of a symmetric, positive definite matrix.

Input
-----
    :param x: data
    :type x: NxN matrix
"""


def _fixture_docs_root(tmp: str) -> str:
    root = Path(tmp) / "docs"
    root.mkdir()
    (root / "invinvpd.rst").write_text(_TYPED_INV_RST, encoding="utf-8")
    return str(root)


def _start_fake_chat_session(tmp: str, *, canned_answer: str | None = None) -> str:
    # `provider="fake"` and `runner="fake"` are CLI-argument-precedence
    # overrides -- they always win over this machine's own config file, so
    # these tests never depend on (or risk touching) this machine's real
    # chat-provider/runner/GAUSS-executable configuration.
    resp = server_mod.gauss_chat_start(
        provider="fake", runner="fake", docs_root=_fixture_docs_root(tmp), workspace_parent=tmp,
    )
    check("gauss_chat_start returns a session_id", "session_id" in resp)
    session_id = resp["session_id"]
    if canned_answer is not None:
        import gauss_chat_provider as provider_mod

        server_mod._chat_sessions[session_id].engine.provider = provider_mod.FakeModelProvider(
            canned_answer=canned_answer
        )
    return session_id


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def test_01_exactly_nine_tools_registered() -> None:
    tools = asyncio.run(server_mod.server.list_tools())
    names = {t.name for t in tools}
    expected = {
        "gauss_chat_start", "gauss_chat_ask", "gauss_chat_reset", "gauss_chat_close",
        "gauss_execution_prepare", "gauss_execution_decide",
        "gauss_repair_start", "gauss_repair_command", "gauss_repair_close",
    }
    check("exactly the expected 9 tools are registered", names == expected)


# ---------------------------------------------------------------------------
# Chat session lifecycle + isolation
# ---------------------------------------------------------------------------


def test_02_chat_start_ask_reset_close() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        session_id = _start_fake_chat_session(tmp)
        ask_resp = server_mod.gauss_chat_ask(session_id, "What does invpd do?")
        check("ask returns provider_success", ask_resp.get("provider_success") is True)
        check("ask returns text", isinstance(ask_resp.get("text"), str) and ask_resp["text"])
        reset_resp = server_mod.gauss_chat_reset(session_id)
        check("reset acknowledges", reset_resp == {"session_id": session_id, "reset": True})
        close_resp = server_mod.gauss_chat_close(session_id)
        check("close acknowledges", close_resp == {"session_id": session_id, "closed": True})
        check("session is gone after close", session_id not in server_mod._chat_sessions)


def test_03_unknown_chat_session_returns_structured_error_not_exception() -> None:
    check("ask on unknown session", server_mod.gauss_chat_ask("does-not-exist", "hi") == {"error": "unknown_session"})
    check("reset on unknown session", server_mod.gauss_chat_reset("does-not-exist") == {"error": "unknown_session"})
    check(
        "close on unknown session is a no-op false, not an error",
        server_mod.gauss_chat_close("does-not-exist") == {"session_id": "does-not-exist", "closed": False},
    )


def test_04_two_chat_sessions_are_isolated() -> None:
    with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
        sid_a = _start_fake_chat_session(tmp_a)
        sid_b = _start_fake_chat_session(tmp_b)
        check("distinct session ids", sid_a != sid_b)
        server_mod.gauss_chat_ask(sid_a, "What does invpd do?")
        check("session A has one turn", len(server_mod._chat_sessions[sid_a].engine.state.turns) == 2)
        check("session B is untouched", len(server_mod._chat_sessions[sid_b].engine.state.turns) == 0)
        server_mod.gauss_chat_reset(sid_a)
        check("resetting A does not affect B's turn count field existing", sid_b in server_mod._chat_sessions)


# ---------------------------------------------------------------------------
# Execution-offer gating -- the safety-relevant boundary this module must
# never re-derive itself (see module docstring).
# ---------------------------------------------------------------------------


def test_05_non_candidate_answer_is_not_offer_eligible_and_prepare_refuses() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        session_id = _start_fake_chat_session(tmp)
        ask_resp = server_mod.gauss_chat_ask(session_id, "What is the meaning of life?")
        check("plain QA answer is not execution-offer-eligible", ask_resp["execution_offer_eligible"] is False)
        prepare_resp = server_mod.gauss_execution_prepare(session_id)
        check(
            "prepare refuses with no pending candidate",
            prepare_resp == {"error": "no_pending_handoff_candidate"},
        )


def test_06_handoff_candidate_answer_is_offer_eligible() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        session_id = _start_fake_chat_session(tmp, canned_answer="```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```")
        ask_resp = server_mod.gauss_chat_ask(session_id, "Use invpd to invert this matrix.")
        check("HANDOFF_CANDIDATE answer is execution-offer-eligible", ask_resp["execution_offer_eligible"] is True)
        check(
            "handoff_readiness state is handoff_candidate",
            ask_resp["handoff_readiness"]["state"] == "handoff_candidate",
        )
        check("exactly one generated code block", len(ask_resp["generated_code"]) == 1)


# ---------------------------------------------------------------------------
# Full execution handoff: prepare -> decide
# ---------------------------------------------------------------------------


def test_07_prepare_then_approve_fake_runner_succeeds_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        session_id = _start_fake_chat_session(tmp, canned_answer="```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```")
        server_mod.gauss_chat_ask(session_id, "Use invpd to invert this matrix.")
        prepare_resp = server_mod.gauss_execution_prepare(session_id)
        check("prepare returns a digest", isinstance(prepare_resp.get("digest"), str) and prepare_resp["digest"])
        check("rendered prompt shows the exact code", "invpd({2 1, 1 2})" in prepare_resp["rendered_prompt"])

        decide_resp = server_mod.gauss_execution_decide(session_id, "yes")
        check("outcome is success", decide_resp["outcome"] == handoff_mod.HandoffOutcome.SUCCESS.value)
        check("launched is true", decide_resp["launched"] is True)
        check("evidence is present", decide_resp["evidence"] is not None)

        session = server_mod._chat_sessions[session_id]
        check("pending request cleared after decide", session.pending_request is None)
        check("approval store recorded exactly one approval", len(session.approval_store) == 1)


def test_08_decline_records_no_execution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        session_id = _start_fake_chat_session(tmp, canned_answer="```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```")
        server_mod.gauss_chat_ask(session_id, "Use invpd to invert this matrix.")
        server_mod.gauss_execution_prepare(session_id)
        decide_resp = server_mod.gauss_execution_decide(session_id, "no")
        check("outcome is declined", decide_resp["outcome"] == "declined")
        check("no 'launched'/'evidence' keys on a declined response", "evidence" not in decide_resp)


def test_09_unrecognized_response_creates_no_approval() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        session_id = _start_fake_chat_session(tmp, canned_answer="```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```")
        server_mod.gauss_chat_ask(session_id, "Use invpd to invert this matrix.")
        server_mod.gauss_execution_prepare(session_id)
        decide_resp = server_mod.gauss_execution_decide(session_id, "sure, go ahead")
        check("outcome is unrecognized", decide_resp["outcome"] == "unrecognized")
        session = server_mod._chat_sessions[session_id]
        check("no approval was recorded", len(session.approval_store) == 0)
        check("pending request is still set (not consumed by an unrecognized reply)", session.pending_request is not None)


def test_10_decide_with_no_pending_request_is_a_structured_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        session_id = _start_fake_chat_session(tmp)
        check(
            "decide with nothing prepared",
            server_mod.gauss_execution_decide(session_id, "yes") == {"error": "no_pending_request"},
        )


# ---------------------------------------------------------------------------
# Server-operator real-GAUSS gate (GAUSS_AI_MCP_ALLOW_REAL_GAUSS)
# ---------------------------------------------------------------------------


def test_11_real_gauss_blocked_by_default() -> None:
    assert os.environ.get(server_mod.ENV_ALLOW_REAL_GAUSS) is None, "test environment must not pre-set this"
    with tempfile.TemporaryDirectory() as tmp:
        fake_exe = os.path.join(tmp, "does-not-exist-tgauss.exe")
        session_id = _start_fake_chat_session(tmp, canned_answer="```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```")
        server_mod._chat_sessions[session_id].runner = "gauss"
        server_mod._chat_sessions[session_id].executable_path = fake_exe
        server_mod.gauss_chat_ask(session_id, "Use invpd to invert this matrix.")
        prepare_resp = server_mod.gauss_execution_prepare(session_id)
        check("real GAUSS blocked without the operator opt-in", prepare_resp.get("error") == "real_gauss_not_allowed")

        repair_resp = server_mod.gauss_repair_start(runner="gauss", gauss_executable=fake_exe, workspace_parent=tmp)
        check(
            "repair session construction also blocked without the operator opt-in",
            repair_resp.get("error") == "real_gauss_not_allowed",
        )


def test_12_real_gauss_opt_in_still_requires_a_real_reachable_executable() -> None:
    """Confirms the opt-in flag only REMOVES the server-side gate -- it does
    not bypass the existing adapter's own environment probe. A nonexistent
    executable path still safely fails at ENVIRONMENT_MISMATCH / `invoked ==
    False`, so this test never actually launches a subprocess."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_exe = os.path.join(tmp, "does-not-exist-tgauss.exe")
        os.environ[server_mod.ENV_ALLOW_REAL_GAUSS] = "1"
        try:
            session_id = _start_fake_chat_session(
                tmp, canned_answer="```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```"
            )
            server_mod._chat_sessions[session_id].runner = "gauss"
            server_mod._chat_sessions[session_id].executable_path = fake_exe
            server_mod.gauss_chat_ask(session_id, "Use invpd to invert this matrix.")
            prepare_resp = server_mod.gauss_execution_prepare(session_id)
            check("prepare now succeeds with the opt-in set", "digest" in prepare_resp)
            decide_resp = server_mod.gauss_execution_decide(session_id, "yes")
            check(
                "a nonexistent executable never actually launches -- infrastructure_failure, not success",
                decide_resp["outcome"] == handoff_mod.HandoffOutcome.INFRASTRUCTURE_FAILURE.value,
            )
        finally:
            del os.environ[server_mod.ENV_ALLOW_REAL_GAUSS]


# ---------------------------------------------------------------------------
# Guided repair sessions
# ---------------------------------------------------------------------------


def test_13_repair_start_command_close() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        start_resp = server_mod.gauss_repair_start(runner="fake", workspace_parent=tmp)
        check("repair start returns a session_id", "session_id" in start_resp)
        session_id = start_resp["session_id"]
        cmd_resp = server_mod.gauss_repair_command(session_id, "status")
        check("command returns an output list", isinstance(cmd_resp["output"], list))
        check("session stays open after an ordinary command", cmd_resp["session_closed"] is False)
        close_resp = server_mod.gauss_repair_close(session_id)
        check("close reports true", close_resp == {"session_id": session_id, "closed": True})
        check("session removed from registry", session_id not in server_mod._repair_sessions)


def test_14_repair_exit_command_closes_and_frees_the_session() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        start_resp = server_mod.gauss_repair_start(runner="fake", workspace_parent=tmp)
        session_id = start_resp["session_id"]
        cmd_resp = server_mod.gauss_repair_command(session_id, "exit")
        check("'exit' closes the session", cmd_resp["session_closed"] is True)
        check("session removed from registry after exit", session_id not in server_mod._repair_sessions)
        followup = server_mod.gauss_repair_command(session_id, "status")
        check("a command after exit is a structured error, not a crash", followup == {"error": "unknown_session"})


def test_15_repair_decline_paths_never_raise() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        start_resp = server_mod.gauss_repair_start(runner="fake", workspace_parent=tmp)
        session_id = start_resp["session_id"]
        for bad_command in (
            "decline-repair not-a-real-digest",
            "decline-repair-draft not-a-real-digest",
            "decline-repair-application not-a-real-digest",
        ):
            resp = server_mod.gauss_repair_command(session_id, bad_command)
            check(f"{bad_command!r} comes back as output, not an exception", isinstance(resp["output"], list))
            check(f"{bad_command!r} does not close the session", resp["session_closed"] is False)
        server_mod.gauss_repair_close(session_id)


def test_16_two_repair_sessions_get_independent_adapters() -> None:
    with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
        sid_a = server_mod.gauss_repair_start(runner="fake", workspace_parent=tmp_a)["session_id"]
        sid_b = server_mod.gauss_repair_start(runner="fake", workspace_parent=tmp_b)["session_id"]
        check("distinct repair session ids", sid_a != sid_b)
        check(
            "distinct adapter instances",
            server_mod._repair_sessions[sid_a].adapter is not server_mod._repair_sessions[sid_b].adapter,
        )
        server_mod.gauss_repair_close(sid_a)
        server_mod.gauss_repair_close(sid_b)


def test_17_unknown_repair_session_returns_structured_error() -> None:
    check(
        "command on unknown repair session",
        server_mod.gauss_repair_command("nope", "status") == {"error": "unknown_session"},
    )
    check(
        "close on unknown repair session is a no-op false",
        server_mod.gauss_repair_close("nope") == {"session_id": "nope", "closed": False},
    )


# ---------------------------------------------------------------------------
# Structural guarantees: this module must never reimplement safety logic
# (precedent: test_gauss_ai_cli.py's own unmodified-module source-scan checks)
# ---------------------------------------------------------------------------


def test_18_source_never_reimplements_safety_logic() -> None:
    source = Path(server_mod.__file__).read_text(encoding="utf-8")
    check("never redefines compute_handoff_readiness", "def compute_handoff_readiness" not in source)
    check("never redefines create_execution_handoff_request", "def create_execution_handoff_request" not in source)
    check("never redefines execute_execution_handoff", "def execute_execution_handoff" not in source)
    check("never redefines InteractiveMvpAdapter", "class InteractiveMvpAdapter" not in source)
    check("never imports gauss_pre_execution_validation directly", "import gauss_pre_execution_validation" not in source)
    check(
        "reuses the canonical _execution_offer_eligible gate rather than duplicating it",
        "chat_mod._execution_offer_eligible" in source and "def _execution_offer_eligible" not in source,
    )


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
