"""Tests for `gauss_mcp_server.py` (v0.79.0; hybrid path v0.80.0).

Run with:

    python scripts/test_gauss_mcp_server.py

Every test is deterministic and network-free, and never touches this
machine's own real `~/.gauss-ai/config.json`, real GAUSS executable, or real
Ollama/Anthropic endpoint -- every call explicitly pins `runner`/
`docs_root`/`workspace_parent` (argument precedence, which wins over this
machine's config file and environment), and strict-mode chat tests inject a
`FakeModelProvider`-backed engine directly. Requires the optional `mcp`
extra (`pip install -e ".[mcp]"`); skips cleanly if it is not installed.
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
    from mcp.server.mcpserver import MCPServer  # noqa: E402
except ImportError as exc:
    print(f"SKIPPED: the optional 'mcp' extra is not installed ({exc}).")
    print('Install it with: pip install -e ".[mcp]" to run this test file.')
    raise SystemExit(0)

import gauss_ai_config as config_mod  # noqa: E402
import gauss_chat_provider as provider_mod  # noqa: E402
import gauss_conversation_engine as engine_mod  # noqa: E402
import gauss_execution_handoff as handoff_mod  # noqa: E402

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


#: Same fixture shape `test_gauss_ai_chat.py` uses to reach a real,
#: broad-evidence `HANDOFF_CANDIDATE` deterministically (typed `x`).
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

CANDIDATE_CODE = "y = invpd({2 1, 1 2});\nprint y;"


def _fixture_docs_root(tmp: str) -> str:
    root = Path(tmp) / "docs"
    root.mkdir(exist_ok=True)
    (root / "invinvpd.rst").write_text(_TYPED_INV_RST, encoding="utf-8")
    return str(root)


def _start(tmp: str, **overrides) -> str:
    kwargs = dict(runner="fake", docs_root=_fixture_docs_root(tmp), workspace_parent=tmp)
    kwargs.update(overrides)
    resp = server_mod.gauss_session_start(**kwargs)
    return resp["session_id"]


def _with_chat_engine(session_id: str, docs_root: str, canned_answer: str | None = None) -> None:
    provider = provider_mod.FakeModelProvider(canned_answer=canned_answer) if canned_answer else provider_mod.FakeModelProvider()
    server_mod._sessions[session_id].engine = engine_mod.ConversationEngine(provider=provider, docs_root=docs_root)


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def test_01_base_tool_surface_and_opt_in_chat_registration() -> None:
    # v0.80.0: replaces v0.79.0's 9-tool set. gauss_chat_start/close became
    # gauss_session_start/close (a session now serves both paths), the
    # hybrid path added gauss_search_docs/gauss_validate_code, and the two
    # strict-mode chat tools are registered only on explicit opt-in.
    names = {t.name for t in asyncio.run(server_mod.server.list_tools())}
    base = {
        "gauss_session_start", "gauss_session_close", "gauss_search_docs", "gauss_validate_code",
        "gauss_execution_prepare", "gauss_execution_decide",
        "gauss_repair_start", "gauss_repair_command", "gauss_repair_close",
    }
    check("exactly the 9 base tools are registered at import", names == base)
    fresh = MCPServer("probe")
    server_mod._register_chat_tools(fresh)
    check("opt-in registers exactly the 2 chat tools", {t.name for t in asyncio.run(fresh.list_tools())} == {"gauss_chat_ask", "gauss_chat_reset"})


def test_02_chat_tools_enabled_only_for_a_real_provider() -> None:
    check("default (unset) is not enabled", not server_mod.chat_tools_enabled(config_mod.GaussAiConfig(), {}))
    check("explicit fake is not enabled", not server_mod.chat_tools_enabled(config_mod.GaussAiConfig(chat_provider="fake"), {}))
    check("ollama is enabled", server_mod.chat_tools_enabled(config_mod.GaussAiConfig(chat_provider="ollama"), {}))
    check("anthropic is enabled", server_mod.chat_tools_enabled(config_mod.GaussAiConfig(chat_provider="anthropic"), {}))


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


def test_03_session_start_close_and_unknown_session_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        check("session registered", sid in server_mod._sessions)
        check("close acknowledges", server_mod.gauss_session_close(sid) == {"session_id": sid, "closed": True})
        check("closing again is a no-op false", server_mod.gauss_session_close(sid)["closed"] is False)
    for fn, args in (
        (server_mod.gauss_validate_code, ("nope", "x = 1;")),
        (server_mod.gauss_execution_prepare, ("nope",)),
        (server_mod.gauss_execution_decide, ("nope", "yes")),
        (server_mod.gauss_chat_ask, ("nope", "hi")),
        (server_mod.gauss_chat_reset, ("nope",)),
    ):
        check(f"{fn.__name__} on unknown session is a structured error", fn(*args) == {"error": "unknown_session"})


def test_04_session_without_docs_root_reports_hint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        empty_cfg = Path(tmp) / "empty-config.json"
        saved_config = server_mod._config
        server_mod._config = config_mod.load_config(empty_cfg)  # no docs_root anywhere in config
        saved_env = os.environ.pop(config_mod.ENV_DOCS_ROOT, None)
        try:
            resp = server_mod.gauss_session_start(runner="fake", workspace_parent=tmp)
            check("not configured", resp["docs_root_configured"] is False)
            check("hint points to docs fetch", "gauss-ai docs fetch" in resp.get("hint", ""))
            result = server_mod.gauss_validate_code(resp["session_id"], CANDIDATE_CODE)
            check("validate refuses without docs", result.get("error") == "docs_root_not_configured")
        finally:
            server_mod._config = saved_config
            if saved_env is not None:
                os.environ[config_mod.ENV_DOCS_ROOT] = saved_env


# ---------------------------------------------------------------------------
# Hybrid path: search -> client-written code -> validate -> prepare -> decide
# ---------------------------------------------------------------------------


def test_05_search_docs_returns_grounded_excerpts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        resp = server_mod.gauss_search_docs("What does invpd do?", docs_root=_fixture_docs_root(tmp))
        check("grounded", resp["grounding_status"] == "grounded")
        check("invpd excerpt returned", any("invpd" in s["content"] for s in resp["sources"]))


def test_06_validated_candidate_round_trip_executes_with_fake_runner() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        validation = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)
        check("candidate", validation["handoff_readiness"]["state"] == "handoff_candidate")
        check("validation_id issued", isinstance(validation.get("validation_id"), str))
        check("code digest returned", len(validation.get("code_sha256", "")) == 64)
        prepared = server_mod.gauss_execution_prepare(sid, validation["validation_id"])
        check("prompt shows the exact validated code", "invpd({2 1, 1 2})" in prepared.get("rendered_prompt", ""))
        decided = server_mod.gauss_execution_decide(sid, "yes")
        check("success", decided.get("outcome") == handoff_mod.HandoffOutcome.SUCCESS.value)


def test_07_validation_id_is_single_use() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        vid = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"]
        server_mod.gauss_execution_prepare(sid, vid)
        check("reuse refused", server_mod.gauss_execution_prepare(sid, vid) == {"error": "unknown_or_used_validation_id"})
        check("made-up id refused", server_mod.gauss_execution_prepare(sid, "not-a-real-id") == {"error": "unknown_or_used_validation_id"})


def test_08_non_candidate_code_never_gets_a_validation_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        for code, why in (
            ("print colmean(x);", "hallucinated function"),
            ("print invpd({2 1, 3 2});", "violated documented precondition"),
            (CANDIDATE_CODE + '\ndos "dir";', "system-touching statement"),
            ("x = {1 2, 3 4};\nprint x;", "no documented calls"),
        ):
            resp = server_mod.gauss_validate_code(sid, code)
            check(f"{why}: not_ready", resp["handoff_readiness"]["state"] == "not_ready")
            check(f"{why}: no validation_id", "validation_id" not in resp and resp["execution_offer_eligible"] is False)
        dos = server_mod.gauss_validate_code(sid, CANDIDATE_CODE + '\ndos "dir";')
        check("system statement reported", [s["name"] for s in dos["system_statements"]] == ["dos"])


def test_09_structural_rejections_are_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        check("fenced code rejected", server_mod.gauss_validate_code(sid, "```gauss\nprint 1;\n```")["error"] == "fenced_code")
        check("empty code rejected", server_mod.gauss_validate_code(sid, "   ")["error"] == "empty_code")


def test_10_stale_validation_is_refused_at_prepare() -> None:
    """The docs changed between validate and prepare -- re-validation at
    prepare time must refuse rather than trust the stored verdict."""
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        vid = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"]
        (Path(tmp) / "docs" / "invinvpd.rst").unlink()
        (Path(tmp) / "docs" / "other.rst").write_text("other\n=====\n", encoding="utf-8")
        resp = server_mod.gauss_execution_prepare(sid, vid)
        check("stale refused", resp.get("error") == "validation_stale")


def test_11_outstanding_validation_ids_are_capped() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        ids = [server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"] for _ in range(server_mod.MAX_VALIDATIONS_PER_SESSION + 2)]
        stored = server_mod._sessions[sid].validated
        check("capped", len(stored) == server_mod.MAX_VALIDATIONS_PER_SESSION)
        check("oldest evicted", ids[0] not in stored and ids[-1] in stored)


def test_12_decline_and_unrecognized_on_validated_request() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        server_mod.gauss_execution_prepare(sid, server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"])
        check("unrecognized creates no approval", server_mod.gauss_execution_decide(sid, "sure")["outcome"] == "unrecognized"
              and len(server_mod._sessions[sid].approval_store) == 0)
        check("decline", server_mod.gauss_execution_decide(sid, "no")["outcome"] == "declined")
        check("nothing left pending", server_mod.gauss_execution_decide(sid, "yes") == {"error": "no_pending_request"})


# ---------------------------------------------------------------------------
# Strict mode (opt-in chat) and the two paths together
# ---------------------------------------------------------------------------


def test_13_chat_candidate_round_trip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs = _fixture_docs_root(tmp)
        sid = _start(tmp)
        _with_chat_engine(sid, docs, "```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```")
        ask = server_mod.gauss_chat_ask(sid, "Use invpd to invert this matrix.")
        check("offer eligible", ask["execution_offer_eligible"] is True)
        check("prepare without validation_id uses the chat answer", "digest" in server_mod.gauss_execution_prepare(sid))
        check("success", server_mod.gauss_execution_decide(sid, "yes")["outcome"] == handoff_mod.HandoffOutcome.SUCCESS.value)


def test_14_non_candidate_chat_answer_cannot_be_prepared() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        _with_chat_engine(sid, _fixture_docs_root(tmp))
        ask = server_mod.gauss_chat_ask(sid, "What is the meaning of life?")
        check("not eligible", ask["execution_offer_eligible"] is False)
        check("prepare refuses", server_mod.gauss_execution_prepare(sid) == {"error": "no_pending_handoff_candidate"})


def test_15_validated_execution_never_clears_a_pending_chat_offer() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs = _fixture_docs_root(tmp)
        sid = _start(tmp)
        _with_chat_engine(sid, docs, "```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```")
        server_mod.gauss_chat_ask(sid, "Use invpd to invert this matrix.")
        vid = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"]
        server_mod.gauss_execution_prepare(sid, vid)
        server_mod.gauss_execution_decide(sid, "yes")
        check("chat offer still pending", server_mod._sessions[sid].pending_code is not None)


def test_16_chat_reset_clears_offer() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        docs = _fixture_docs_root(tmp)
        sid = _start(tmp)
        _with_chat_engine(sid, docs, "```gauss\ny = invpd({2 1, 1 2});\nprint y;\n```")
        server_mod.gauss_chat_ask(sid, "Use invpd to invert this matrix.")
        check("reset acknowledges", server_mod.gauss_chat_reset(sid) == {"session_id": sid, "reset": True})
        check("offer cleared", server_mod.gauss_execution_prepare(sid) == {"error": "no_pending_handoff_candidate"})


# ---------------------------------------------------------------------------
# Server-operator real-GAUSS gate (GAUSS_AI_MCP_ALLOW_REAL_GAUSS)
# ---------------------------------------------------------------------------


def test_17_real_gauss_blocked_by_default() -> None:
    assert os.environ.get(server_mod.ENV_ALLOW_REAL_GAUSS) is None, "test environment must not pre-set this"
    with tempfile.TemporaryDirectory() as tmp:
        fake_exe = os.path.join(tmp, "does-not-exist-tgauss.exe")
        sid = _start(tmp, runner="gauss", gauss_executable=fake_exe)
        vid = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"]
        check("prepare blocked", server_mod.gauss_execution_prepare(sid, vid).get("error") == "real_gauss_not_allowed")
        repair = server_mod.gauss_repair_start(runner="gauss", gauss_executable=fake_exe, workspace_parent=tmp)
        check("repair blocked", repair.get("error") == "real_gauss_not_allowed")


def test_18_real_gauss_opt_in_still_requires_a_reachable_executable() -> None:
    """The opt-in removes only the server-side refusal, never the adapter's
    own environment probe -- a nonexistent executable never launches."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_exe = os.path.join(tmp, "does-not-exist-tgauss.exe")
        os.environ[server_mod.ENV_ALLOW_REAL_GAUSS] = "1"
        try:
            sid = _start(tmp, runner="gauss", gauss_executable=fake_exe)
            vid = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"]
            check("prepare allowed", "digest" in server_mod.gauss_execution_prepare(sid, vid))
            decided = server_mod.gauss_execution_decide(sid, "yes")
            check("never launched -- infrastructure_failure", decided["outcome"] == handoff_mod.HandoffOutcome.INFRASTRUCTURE_FAILURE.value)
        finally:
            del os.environ[server_mod.ENV_ALLOW_REAL_GAUSS]


# ---------------------------------------------------------------------------
# Guided repair sessions (unchanged from v0.79.0)
# ---------------------------------------------------------------------------


def test_19_repair_start_command_close() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sid = server_mod.gauss_repair_start(runner="fake", workspace_parent=tmp)["session_id"]
        resp = server_mod.gauss_repair_command(sid, "status")
        check("output list", isinstance(resp["output"], list) and resp["session_closed"] is False)
        check("close", server_mod.gauss_repair_close(sid) == {"session_id": sid, "closed": True})


def test_20_repair_exit_and_decline_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sid = server_mod.gauss_repair_start(runner="fake", workspace_parent=tmp)["session_id"]
        for cmd in ("decline-repair x", "decline-repair-draft x", "decline-repair-application x"):
            resp = server_mod.gauss_repair_command(sid, cmd)
            check(f"{cmd!r} returns output and keeps the session", isinstance(resp["output"], list) and not resp["session_closed"])
        check("exit closes", server_mod.gauss_repair_command(sid, "exit")["session_closed"] is True)
        check("command after exit is a structured error", server_mod.gauss_repair_command(sid, "status") == {"error": "unknown_session"})


# ---------------------------------------------------------------------------
# Structural guarantees: this module never reimplements safety logic
# ---------------------------------------------------------------------------


def test_21_source_never_reimplements_safety_logic() -> None:
    source = Path(server_mod.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "def compute_handoff_readiness", "def create_execution_handoff_request", "def execute_execution_handoff",
        "class InteractiveMvpAdapter", "import gauss_pre_execution_validation", "def validate_code",
        "def check_system_statements",
    ):
        check(f"source has no {forbidden!r}", forbidden not in source)
    check(
        "reuses the canonical _execution_offer_eligible gate rather than duplicating it",
        "chat_mod._execution_offer_eligible" in source and "def _execution_offer_eligible" not in source,
    )
    check("prepare takes no code parameter", "code" not in server_mod.gauss_execution_prepare.__code__.co_varnames[:2])



# ---------------------------------------------------------------------------
# v0.83.0: verdict explanations and search candidates
# ---------------------------------------------------------------------------


def test_22_validate_code_reports_coverage_and_gaps() -> None:
    """Live findings 72.3/72.15: the response named no cause for a partial
    verdict, so the client guessed."""
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        clean = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)
        check("coverage reported", clean.get("coverage", {}).get("syntax_check") == "complete")
        check("no gaps for a candidate", clean.get("coverage_gaps") == [])
        partial = server_mod.gauss_validate_code(sid, "x = q * 2;\ny = inv(x);")
        check("review_required", partial["handoff_readiness"]["state"] == "review_required")
        check("gap names symbol, argument, parameter and cause", any(
            g["check"] == "parameter_role" and g["symbol"] == "inv" and g["argument"] == 1 and g["parameter"] == "x"
            and g["cause"] == "argument_assigned_from_expression" for g in partial["coverage_gaps"]
        ))
        no_calls = server_mod.gauss_validate_code(sid, "x = {1 2, 3 4};\nprint x;")
        check("no-calls reason is the real cause",
              no_calls["handoff_readiness"]["reasons"][0] == engine_mod.NO_DOCUMENTED_CALLS_ISSUE)
        check("existing keys unchanged", {"issues", "syntax", "preconditions", "notes", "eligibility"} <= set(no_calls))


def test_23_search_docs_lists_labeled_candidates_without_changing_grounding() -> None:
    """Live finding 72.16."""
    with tempfile.TemporaryDirectory() as tmp:
        root = _fixture_docs_root(tmp)
        (Path(root) / "vcmvcx.rst").write_text(
            "vcm, vcx\n========\n\nPurpose\n-------\n\nComputes an estimate of a variance-covariance matrix.\n\n"
            ".. function:: vc = vcx(x)\n\n    :param x: data\n    :type x: NxK matrix\n\n"
            "    :return vc: KxK variance-covariance matrix.\n",
            encoding="utf-8",
        )
        resp = server_mod.gauss_search_docs("covariance", docs_root=root)
        check("grounding status untouched", resp["grounding_status"] == "ungrounded" and resp["sources"] == [])
        check("candidate listed", [c["citation"] for c in resp.get("candidates", [])] == ["vcmvcx.rst"])
        check("labeled", resp["candidates"][0]["status"] == "candidate")
        check("note explains candidates", resp.get("candidate_note") == engine_mod.SEARCH_CANDIDATE_NOTE)
        check("truncation flag present", resp.get("candidates_truncated") is False)
        grounded = server_mod.gauss_search_docs("What does invpd do?", docs_root=root)
        check("no candidate keys when grounded", "candidates" not in grounded and "candidate_note" not in grounded)


def test_24_v084_undocumented_calls_are_named_gaps_and_labels_hide_nothing() -> None:
    """Live finding 73.14: a `"fakeinverse = "` label hid a hallucinated call,
    and the partial signature check left `coverage_gaps` empty."""
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        labelled = server_mod.gauss_validate_code(
            sid, 'x = {2 1, 1 2};\ny = inv(x);\nf = fakeinverse(x);\nprint "fakeinverse = " f;',
        )
        check("label hides nothing: not_ready", labelled["handoff_readiness"]["state"] == "not_ready")
        check("call_undocumented gap", any(
            g["check"] == "signature" and g["symbol"] == "fakeinverse" and g["cause"] == "call_undocumented"
            for g in labelled["coverage_gaps"]
        ))
        own_proc = server_mod.gauss_validate_code(
            sid, "proc (1) = g(x);\n    retp(x);\nendp;\ny = inv(g({2 1, 1 2}));",
        )
        check("a snippet's own proc: review_required", own_proc["handoff_readiness"]["state"] == "review_required")
        check("its call is a named gap, so the partial verdict has a cause", any(
            g["symbol"] == "g" and g["cause"] == "call_undocumented" for g in own_proc["coverage_gaps"]
        ))


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
