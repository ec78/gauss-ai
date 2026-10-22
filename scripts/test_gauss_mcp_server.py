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
    # v0.89.0 (planning v0.89 §3.6): gauss_read_doc joins the base set, so
    # the count is 10; nothing else was added or removed.
    base = {
        "gauss_session_start", "gauss_session_close", "gauss_search_docs", "gauss_read_doc", "gauss_validate_code",
        "gauss_execution_prepare", "gauss_execution_decide",
        "gauss_repair_start", "gauss_repair_command", "gauss_repair_close",
    }
    check("exactly the 10 base tools are registered at import", names == base)
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
        # v0.87.0 decision 2: decide is bound to the prompt's request_id (superseded: a bare reply).
        decided = server_mod.gauss_execution_decide(sid, "yes", request_id=prepared["request_id"])
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
        rid = server_mod.gauss_execution_prepare(
            sid, server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"],
        )["request_id"]
        # v0.87.0 decision 2: decide is bound to the prompt's request_id (superseded: a bare reply).
        check("unrecognized creates no approval",
              server_mod.gauss_execution_decide(sid, "sure", request_id=rid)["outcome"] == "unrecognized"
              and len(server_mod._sessions[sid].approval_store) == 0)
        check("decline", server_mod.gauss_execution_decide(sid, "no", request_id=rid)["outcome"] == "declined")
        check("nothing left pending",
              server_mod.gauss_execution_decide(sid, "yes", request_id=rid) == {"error": "no_pending_request"})


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
        prepared = server_mod.gauss_execution_prepare(sid)
        check("prepare without validation_id uses the chat answer", "digest" in prepared)
        # v0.87.0 decision 2: decide is bound to the prompt's request_id (superseded: a bare reply).
        decided = server_mod.gauss_execution_decide(sid, "yes", request_id=prepared["request_id"])
        check("success", decided["outcome"] == handoff_mod.HandoffOutcome.SUCCESS.value)


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
        rid = server_mod.gauss_execution_prepare(sid, vid)["request_id"]
        # v0.87.0 decision 2: decide is bound to the prompt's request_id (superseded: a bare reply).
        server_mod.gauss_execution_decide(sid, "yes", request_id=rid)
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
            prepared = server_mod.gauss_execution_prepare(sid, vid)
            check("prepare allowed", "digest" in prepared)
            # v0.87.0 decision 2: decide is bound to the prompt's request_id (superseded: a bare reply).
            decided = server_mod.gauss_execution_decide(sid, "yes", request_id=prepared["request_id"])
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


def test_25_v085_struct_procedure_header_is_not_a_syntax_violation() -> None:
    """Live finding 74.18: `proc (1) = myFunc(struct PV p);` (valid GAUSS,
    real tgauss.exe -b spot check s1) was a false syntax INVALID."""
    code = (
        "proc (1) = myFunc(struct PV p);\n    local b;\n    b = pvUnpack(p, \"b\");\n"
        "    retp((b[1] - 3)^2 + (b[2] + 1)^2);\nendp;\n\nb0 = { 0, 0 };\nstruct PV par1;\n"
        "par1 = pvCreate();\npar1 = pvPack(par1, b0, \"b\");\nstruct sqpSolveMTControl ctl;\n"
        "ctl = sqpSolveMTControlCreate();\nstruct sqpSolveMTout out;\nout = sqpSolveMT(&myFunc, par1, ctl);\n"
        "print \"estimated b = \" pvUnpack(out.par, \"b\")';"
    )
    pages = {
        "pvcreate.rst": ("pvCreate", "p = pvCreate()"),
        "pvpack.rst": ("pvPack", "p1 = pvPack(p1, x, nm)"),
        "pvunpack.rst": ("pvUnpack", "x = pvUnpack(p1, nm)"),
        "sqpsolvemtcontrolcreate.rst": ("sqpSolveMTControlCreate", "c = sqpSolveMTControlCreate()"),
        "sqpsolvemt.rst": ("sqpSolveMT", "out = sqpSolveMT(&fct, par1, c)"),
    }
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        for file_name, (title, function) in pages.items():
            (Path(tmp) / "docs" / file_name).write_text(
                f"{title}\n{'=' * len(title)}\n\nFormat\n------\n.. function:: {function}\n", encoding="utf-8",
            )
        resp = server_mod.gauss_validate_code(sid, code)
        check("syntax partial", resp["syntax"] == "partial")
        check("review_required (was not_ready)", resp["handoff_readiness"]["state"] == "review_required")
        check("no syntax reason", not any(r.startswith("syntax:") for r in resp["handoff_readiness"]["reasons"]))
        check("no validation_id", resp.get("validation_id") is None)
        bad = server_mod.gauss_validate_code(sid, code.replace("(struct PV p)", "(struct PV)"))
        check("h8: syntax invalid", bad["syntax"] == "invalid")


def test_26_v086_structure_definitions_and_member_literals_are_not_syntax_violations() -> None:
    """Live findings 75.20 and 75.8: a structure definition (sc04) and a
    brace literal assigned to a member (sc01) were false syntax INVALIDs."""
    definition = (
        "struct regResults {\n    matrix b;\n    matrix se;\n    string label;\n};\nstruct regResults r;\n"
        "r.b = zeros(2, 1);\nr.label = \"OLS\";\nprint r.label;"
    )
    ds = (
        "proc (1) = dsMean(struct DS d);\n    retp(meanc(d.dataMatrix));\nendp;\nstruct DS myData;\n"
        "myData = dsCreate();\nmyData.dataMatrix = { 1  2,\n                      3  4 };\nm = dsMean(myData);"
    )
    pages = {
        "zeros.rst": ("zeros", "y = zeros(r, c)"),
        "meanc.rst": ("meanc", "y = meanc(x)"),
        "dscreate.rst": ("dsCreate", "d = dsCreate()"),
    }
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        for file_name, (title, function) in pages.items():
            (Path(tmp) / "docs" / file_name).write_text(
                f"{title}\n{'=' * len(title)}\n\nFormat\n------\n.. function:: {function}\n", encoding="utf-8",
            )
        resp = server_mod.gauss_validate_code(sid, definition)
        check("definition: syntax validated", resp["syntax"] == "validated")
        check("definition: no syntax reason", not any(r.startswith("syntax:") for r in resp["handoff_readiness"]["reasons"]))
        member = server_mod.gauss_validate_code(sid, ds)
        check("member literal: syntax partial (the proc block)", member["syntax"] == "partial")
        check("member literal: no syntax reason",
              not any(r.startswith("syntax:") for r in member["handoff_readiness"]["reasons"]))
        bad = server_mod.gauss_validate_code(sid, definition.replace("string label;", "vector label;"))
        check("d15 shape: syntax invalid", bad["syntax"] == "invalid")


# ---------------------------------------------------------------------------
# v0.87.0: handoff binding and refusals (live findings 77.x f2/f3, 76.x f2/f3;
# planning v0.87 §3.1-§3.4). Fake runner throughout.
# ---------------------------------------------------------------------------

#: A second candidate on the same fixture page, distinguishable from
#: CANDIDATE_CODE by its literal.
OTHER_CANDIDATE_CODE = "y = invpd({4 1, 1 4});\nprint y;"


class _SpyHelper:
    """Stands in for `select_helper(...)`: records each code text it runs,
    then behaves like the default fake helper."""

    def __init__(self) -> None:
        self.codes: list[str] = []

    def select(self, runner: str):
        def helper(**kwargs):
            self.codes.append(kwargs.get("code"))
            return handoff_mod.build_default_fake_helper()(**kwargs)
        return helper


def _with_spy(fn):
    spy = _SpyHelper()
    original = server_mod.handoff_mod.select_helper
    server_mod.handoff_mod.select_helper = spy.select
    try:
        fn(spy)
    finally:
        server_mod.handoff_mod.select_helper = original


def test_27_v087_decide_is_bound_to_the_prompt_it_answers() -> None:
    """Probe P5 (v0.86 §12.6): before v0.87.0 a "yes" after two prepares ran
    the second request, whichever prompt the user answered."""
    def body(spy: _SpyHelper) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sid = _start(tmp)
            va = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"]
            vb = server_mod.gauss_validate_code(sid, OTHER_CANDIDATE_CODE)["validation_id"]
            pa = server_mod.gauss_execution_prepare(sid, va)
            check("27: a first prepare reports no replacement", "replaced_request_id" not in pa)
            pb = server_mod.gauss_execution_prepare(sid, vb)
            check("27: the second prepare reports the replaced request", pb.get("replaced_request_id") == pa["request_id"])
            check("27: ... with a notice naming it", pa["request_id"] in pb.get("notice", ""))
            try:
                stale = server_mod.gauss_execution_decide(sid, "yes", request_id=pa["request_id"])
            except TypeError:
                stale = {}
            check("27: a reply to the replaced prompt is refused", stale.get("error") == "request_superseded")
            check("27: ... naming the pending request", stale.get("pending_request_id") == pb["request_id"])
            check("27: ... and nothing ran or was approved",
                  spy.codes == [] and len(server_mod._sessions[sid].approval_store) == 0)
            check("27: the newer request is still pending",
                  server_mod._sessions[sid].pending_request is not None
                  and server_mod._sessions[sid].pending_request.request_id == pb["request_id"])
            try:
                ran = server_mod.gauss_execution_decide(sid, "yes", request_id=pb["request_id"])
            except TypeError:
                ran = {}
            check("27: the named request runs", ran.get("outcome") == handoff_mod.HandoffOutcome.SUCCESS.value)
            check("27: ... and it is the second program", spy.codes == [OTHER_CANDIDATE_CODE])
            check("27: decide echoes the request it acted on",
                  ran.get("request_id") == pb["request_id"] and ran.get("request_digest") == pb["digest"])
    _with_spy(body)


def test_28_v087_request_id_is_required_in_effect() -> None:
    def body(spy: _SpyHelper) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sid = _start(tmp)
            prepared = server_mod.gauss_execution_prepare(sid, server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"])
            rid = prepared["request_id"]
            bare = server_mod.gauss_execution_decide(sid, "yes")
            check("28: a bare reply is refused", bare.get("error") == "request_id_required")
            check("28: ... with an explanation naming request_id", "request_id" in bare.get("detail", ""))
            check("28: ... nothing approved, nothing ran, still pending",
                  len(server_mod._sessions[sid].approval_store) == 0 and spy.codes == []
                  and server_mod._sessions[sid].pending_request is not None)
            try:
                made_up = server_mod.gauss_execution_decide(sid, "yes", request_id="not-a-real-request")
                unrecognized = server_mod.gauss_execution_decide(sid, "Yes approve", request_id=rid)
                declined = server_mod.gauss_execution_decide(sid, "no", request_id=rid)
                again = server_mod.gauss_execution_decide(sid, "yes", request_id=rid)
            except TypeError:
                made_up = unrecognized = declined = again = {}
            check("28: an unknown request_id is refused", made_up.get("error") == "request_not_pending")
            check("28: unrecognized keeps the request pending and echoes it",
                  unrecognized.get("outcome") == "unrecognized" and unrecognized.get("request_id") == rid
                  and unrecognized.get("request_digest") == prepared["digest"])
            check("28: decline echoes the request",
                  declined.get("outcome") == "declined" and declined.get("request_id") == rid)
            check("28: a decided request is not pending", again == {"error": "no_pending_request"})
            check("28: nothing ran", spy.codes == [])
    _with_spy(body)


def test_29_v087_a_refused_prepare_does_not_spend_its_validation_id() -> None:
    """Live finding 76.x f3: the id used to be popped before every check,
    so a resubmission was told `unknown_or_used_validation_id`."""
    assert os.environ.get(server_mod.ENV_ALLOW_REAL_GAUSS) is None, "test environment must not pre-set this"
    with tempfile.TemporaryDirectory() as tmp:
        fake_exe = os.path.join(tmp, "does-not-exist-tgauss.exe")
        sid = _start(tmp, runner="gauss", gauss_executable=fake_exe)
        vid = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"]
        first = server_mod.gauss_execution_prepare(sid, vid).get("error")
        second = server_mod.gauss_execution_prepare(sid, vid).get("error")
        check("29: opt-in refusal repeats", first == second == "real_gauss_not_allowed")
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp)
        vid = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"]
        page = Path(tmp) / "docs" / "invinvpd.rst"
        page.rename(page.with_suffix(".bak"))
        stale = [server_mod.gauss_execution_prepare(sid, vid).get("error") for _ in range(2)]
        check("29: stale refusal repeats", stale == ["validation_stale", "validation_stale"])
        page.with_suffix(".bak").rename(page)
        check("29: once the docs are back, the same id prepares", "rendered_prompt" in server_mod.gauss_execution_prepare(sid, vid))
        check("29: a successful prepare spends it", server_mod.gauss_execution_prepare(sid, vid) == {"error": "unknown_or_used_validation_id"})
    with tempfile.TemporaryDirectory() as tmp:
        os.environ[server_mod.ENV_ALLOW_REAL_GAUSS] = "1"
        try:
            sid = _start(tmp, runner="gauss")
            server_mod._sessions[sid].executable_path = None  # no executable configured: request_rejected
            vid = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)["validation_id"]
            check("29: request_rejected", server_mod.gauss_execution_prepare(sid, vid).get("error") == "request_rejected")
            check("29: ... leaves the id usable", vid in server_mod._sessions[sid].validated)
        finally:
            del os.environ[server_mod.ENV_ALLOW_REAL_GAUSS]


def test_30_v087_session_start_reports_the_opt_in() -> None:
    assert os.environ.get(server_mod.ENV_ALLOW_REAL_GAUSS) is None, "test environment must not pre-set this"
    with tempfile.TemporaryDirectory() as tmp:
        docs = _fixture_docs_root(tmp)
        fake = server_mod.gauss_session_start(runner="fake", docs_root=docs)
        real = server_mod.gauss_session_start(runner="gauss", docs_root=docs)
        check("30: off, fake runner", fake.get("real_gauss_allowed") is False and "execution_hint" not in fake)
        check("30: off, gauss runner, with a hint",
              real.get("real_gauss_allowed") is False and server_mod.ENV_ALLOW_REAL_GAUSS in real.get("execution_hint", ""))
        os.environ[server_mod.ENV_ALLOW_REAL_GAUSS] = "1"
        try:
            on_fake = server_mod.gauss_session_start(runner="fake", docs_root=docs)
            on_real = server_mod.gauss_session_start(runner="gauss", docs_root=docs)
        finally:
            del os.environ[server_mod.ENV_ALLOW_REAL_GAUSS]
        check("30: on, both runners, no hint",
              on_fake.get("real_gauss_allowed") is True and on_real.get("real_gauss_allowed") is True
              and "execution_hint" not in on_real)


def test_31_v087_prompt_says_where_code_runs_and_digest_ignores_workspace() -> None:
    """Live finding 77.x f3: runs always execute in a deleted temp directory,
    so the configured workspace parent is neither shown nor digest-bound."""
    with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
        sid_a = _start(tmp_a, workspace_parent=tmp_a)
        sid_b = _start(tmp_b, workspace_parent=tmp_b)
        pa = server_mod.gauss_execution_prepare(sid_a, server_mod.gauss_validate_code(sid_a, CANDIDATE_CODE)["validation_id"])
        pb = server_mod.gauss_execution_prepare(sid_b, server_mod.gauss_validate_code(sid_b, CANDIDATE_CODE)["validation_id"])
        prompt = pa["rendered_prompt"]
        check("31: no Workspace parent line", "Workspace parent" not in prompt and tmp_a not in prompt)
        check("31: a Runs in line", "Runs in: a new temporary directory, deleted after the run" in prompt)
        check("31: the digest does not depend on the workspace parent", pa["digest"] == pb["digest"])
        check("31: the pending request carries none", server_mod._sessions[sid_a].pending_request.workspace_parent is None)


def test_32_v087_wording_names_request_id() -> None:
    import inspect
    params = inspect.signature(server_mod.gauss_execution_decide).parameters
    check("32: decide takes request_id, last and optional",
          list(params)[-1] == "request_id" and params["request_id"].default is None)
    check("32: decide's description names request_id", "request_id" in (server_mod.gauss_execution_decide.__doc__ or ""))
    check("32: prepare's description names the replacement", "replaced_request_id" in (server_mod.gauss_execution_prepare.__doc__ or ""))
    check("32: session start's description names the flag", "real_gauss_allowed" in (server_mod.gauss_session_start.__doc__ or ""))
    check("32: server instructions name request_id", "request_id" in (server_mod.server.instructions or ""))


# ---------------------------------------------------------------------------
# v0.88.0: search and grounding recall (planning v0.88 §6.1)
# ---------------------------------------------------------------------------


def _v088_page(name: str, function: str) -> str:
    return (f"{name}\n{'=' * len(name)}\n\nPurpose\n-------\n\nA documented function.\n\nFormat\n------\n"
            f".. function:: {function}\n\n    :param x: input matrix\n    :type x: NxK matrix\n")


def _v088_docs_root(tmp: str) -> str:
    root = Path(_fixture_docs_root(tmp))
    pages = {
        "tspdlib/docs/tspdlib-landing.rst": "GAUSS Time-Series Panel Data (TSPDLIB)\n=====\n\nThe tspdlib library.\n",
        "for.rst": "for\n===\n\nPurpose\n----------------\n\nBegins a loop.\n\nFormat\n----------------\n\n::\n\n"
                   "    for i (start, stop, step);\n        ...\n    endfor;\n",
        "datalist.rst": "datalist\n========\n\nFormat\n------\n.. function:: datalist dataset [[var 1]]\n\n"
                        "Global Input\n------------\n\n.. data:: __range\n\n    the range of rows.\n",
        **{f"{n}.rst": _v088_page(n, f"y = {n}(x)") for n in ("meanc", "stdc", "rows", "cols", "diag")},
    }
    for name, text in pages.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8")
    return str(root)


def test_33_v088_search_opens_hyphenated_and_stopword_pages() -> None:
    """Findings 4-5 (74.x)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = _v088_docs_root(tmp)
        landing = server_mod.gauss_search_docs("tspdlib-landing", docs_root=root)
        check("33: tspdlib-landing returns its page", landing["grounding_status"] == "grounded"
              and [s["citation"] for s in landing["sources"]] == ["tspdlib/docs/tspdlib-landing.rst"])
        loop = server_mod.gauss_search_docs("for", docs_root=root)
        check("33: for is grounded", loop["grounding_status"] == "grounded"
              and [s["citation"] for s in loop["sources"]] == ["for.rst"])


def test_34_v088_search_reports_omitted_topics() -> None:
    """Finding 11 (76.5, 77.5, 78.11): a fifth named function was dropped."""
    with tempfile.TemporaryDirectory() as tmp:
        resp = server_mod.gauss_search_docs("meanc stdc rows cols diag", docs_root=_v088_docs_root(tmp))
        check("34: four sources", len(resp["sources"]) == 4)
        check("34: the fifth is named", len(resp.get("omitted_topics", [])) == 1
              and resp["omitted_topics"][0] not in [s["topic"] for s in resp["sources"]])
        check("34: with the fixed note", resp.get("omitted_note") == server_mod.OMITTED_TOPICS_NOTE
              and "search these names separately" in server_mod.OMITTED_TOPICS_NOTE)
        check("34: partially grounded", resp["grounding_status"] == "partially_grounded")
        four = server_mod.gauss_search_docs("meanc stdc rows cols", docs_root=_v088_docs_root(tmp))
        check("34: nothing omitted, no field", "omitted_topics" not in four and four["grounding_status"] == "grounded")


def test_35_v088_validate_code_invented_call_is_not_ready() -> None:
    """Finding 8 (re-plan §2.8): `data` used to ground on `datalist.rst`."""
    with tempfile.TemporaryDirectory() as tmp:
        sid = _start(tmp, docs_root=_v088_docs_root(tmp))
        resp = server_mod.gauss_validate_code(sid, "y = data(x);")
        check("35: not_ready", resp["handoff_readiness"]["state"] == "not_ready")
        check("35: data is unknown", resp["unknown_symbols"] == ["data"] and resp["grounding_sources"] == [])
        check("35: no validation_id", "validation_id" not in resp)
        search = server_mod.gauss_search_docs("data", docs_root=_v088_docs_root(tmp))
        check("35: search lists datalist as a non-defining candidate, not a source", search["sources"] == []
              and ("datalist.rst", "non_defining_page") in [(c["citation"], c["origin"]) for c in search.get("candidates", [])])


def test_36_v088_reply_guidance_in_decide_and_instructions() -> None:
    """78.x findings 1-2 (v0.87 plan §11.8)."""
    sentence = ("If several prompts are open, the user names the prompt in a separate message and replies with a "
                "bare yes or no; never ask the user to label a reply.")
    decide_doc = " ".join((server_mod.gauss_execution_decide.__doc__ or "").split())
    check("36: decide description", sentence in decide_doc)
    check("36: server instructions", sentence in (server_mod.server.instructions or ""))


# ---------------------------------------------------------------------------
# v0.89.0 (planning v0.89 §3.6, §3.8, §3.9)
# ---------------------------------------------------------------------------

#: The 79.x-1 shape: a return-code field list nested in the `out`
#: description, which extraction drops from the search excerpt, and a
#: Remarks section with a subsection.
_V089_PAGE = """zzsolve
=======

Purpose
-------
Solves a fixture problem.

Format
------
.. function:: out = zzsolve(x)

    :param x: data
    :type x: scalar
    :return out: instance of a structure. Members:

        .. list-table::

            * - out.retcode
              - return code:

                  :0: normal convergence.
                  :1: forced exit.

    :rtype out: struct

Remarks
-------
Remarks text.

Details
+++++++
Nested detail.

Source
------
zzsolve.src
"""


def _v089_docs_root(tmp: str) -> str:
    root = Path(tmp) / "v089docs"
    (root / "sub").mkdir(parents=True, exist_ok=True)
    (root / "zzsolve.rst").write_text(_V089_PAGE, encoding="utf-8", newline="\n")
    (root / "zzlong.rst").write_text("zzlong\n======\n\nRemarks\n-------\n" + ("abcdefghij" * 2000) + "\n", encoding="utf-8", newline="\n")
    (root / "sub" / "zzinclude.rst").write_text("No heading at all, like an include page.\n", encoding="utf-8", newline="\n")
    (root / "notes.txt").write_text("not a page", encoding="utf-8")
    return str(root)


def test_37_v089_read_doc_outline_and_verbatim_sections() -> None:
    """79.x finding 1: the return codes and Remarks reach a client with no disk access."""
    with tempfile.TemporaryDirectory() as tmp:
        root = _v089_docs_root(tmp)
        outline = server_mod.gauss_read_doc("zzsolve.rst", docs_root=root)
        check("37: outline title", outline.get("title") == "zzsolve")
        check("37: outline headings and levels", [(s["heading"], s["level"]) for s in outline.get("sections", [])] == [
            ("zzsolve", 1), ("Purpose", 2), ("Format", 2), ("Remarks", 2), ("Details", 3), ("Source", 2)])
        check("37: outline has no content", "content" not in outline)
        check("37: every read links its docs.aptech.com page", outline.get("docs_url") == "https://docs.aptech.com/gauss/zzsolve.html"
              and server_mod.gauss_read_doc("sub/zzinclude.rst", section="*", docs_root=root).get("docs_url")
              == "https://docs.aptech.com/gauss/sub/zzinclude.html")
        fmt = server_mod.gauss_read_doc("zzsolve.rst", section="format", docs_root=root)
        start = _V089_PAGE.index("Format\n------")
        end = _V089_PAGE.index("Remarks\n-------")
        check("37: a section is the raw source, byte-for-byte", fmt.get("content") == _V089_PAGE[start:end])
        check("37: the nested return codes are there", ":0: normal convergence." in fmt.get("content", ""))
        check("37: one call, no continuation", fmt.get("next_offset") is None and fmt.get("offset") == 0)
        remarks = server_mod.gauss_read_doc("zzsolve.rst", section="Remarks", docs_root=root)
        check("37: a section includes its subsections", "Nested detail." in remarks.get("content", "")
              and "Source" not in remarks.get("content", ""))
        whole = server_mod.gauss_read_doc("zzsolve.rst", section="*", docs_root=root)
        check("37: '*' is the whole page", whole.get("content") == _V089_PAGE)
        missing = server_mod.gauss_read_doc("zzsolve.rst", section="Outputs", docs_root=root)
        check("37: an unknown section names the headings", missing.get("error") == "unknown_section"
              and "Remarks" in missing.get("available_sections", []))
        bare = server_mod.gauss_read_doc("sub/zzinclude.rst", docs_root=root)
        check("37: a page with no heading has an empty outline", bare.get("sections") == [] and bare.get("title") is None)
        check("37: and reads with '*'", server_mod.gauss_read_doc("sub/zzinclude.rst", section="*", docs_root=root).get("content")
              == "No heading at all, like an include page.\n")


def test_38_v089_read_doc_is_bounded_and_pages_exactly() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _v089_docs_root(tmp)
        expected = "Remarks\n-------\n" + ("abcdefghij" * 2000) + "\n"
        pieces, offset, calls = [], 0, 0
        while True:
            resp = server_mod.gauss_read_doc("zzlong.rst", section="Remarks", offset=offset, docs_root=root)
            calls += 1
            check("38: never more than the bound", len(resp.get("content", "")) <= 8000)
            check("38: total size reported", resp.get("chars_total") == len(expected))
            pieces.append(resp.get("content", ""))
            if resp.get("next_offset") is None or calls > 10:
                break
            offset = resp["next_offset"]
        check("38: three calls for 20,017 characters", calls == 3)
        check("38: the pieces reassemble the section exactly", "".join(pieces) == expected)
        bad = server_mod.gauss_read_doc("zzlong.rst", section="Remarks", offset=len(expected) + 1, docs_root=root)
        check("38: an offset past the end is refused", bad.get("error") == "offset_out_of_range")
        check("38: a negative offset is refused", server_mod.gauss_read_doc(
            "zzlong.rst", section="Remarks", offset=-1, docs_root=root).get("error") == "offset_out_of_range")


def test_39_v089_read_doc_refuses_paths_outside_the_docs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _v089_docs_root(tmp)
        (Path(tmp) / "secret.rst").write_text("outside\n", encoding="utf-8")
        for page in ("../secret.rst", str(Path(tmp) / "secret.rst"), "sub\\..\\..\\secret.rst", "C:/x.rst",
                     "notes.txt", "missing.rst", "sub/../zzsolve.rst", ""):
            resp = server_mod.gauss_read_doc(page, docs_root=root)
            check(f"39: refused {page!r}", resp.get("error") == "page_refused" and "content" not in resp
                  and "sections" not in resp)
        link = Path(root) / "link.rst"
        try:
            os.symlink(Path(tmp) / "secret.rst", link)
        except (OSError, NotImplementedError):
            link = None  # Creating symlinks needs a privilege on Windows; CI's Linux and macOS runs check this.
        if link is not None:
            check("39: a symlink out of the root is refused",
                  server_mod.gauss_read_doc("link.rst", section="*", docs_root=root).get("error") == "page_refused")
        no_root = server_mod.gauss_read_doc("zzsolve.rst", docs_root=str(Path(tmp) / "nowhere"))
        check("39: a missing docs root is refused", no_root.get("error") == "page_refused")


def test_40_v089_session_docs_root_and_read_hint() -> None:
    """§2.6 side finding: search ignored the session's docs_root."""
    with tempfile.TemporaryDirectory() as tmp:
        root = _v089_docs_root(tmp)
        sid = server_mod.gauss_session_start(runner="fake", docs_root=root, workspace_parent=tmp)["session_id"]
        resp = server_mod.gauss_search_docs("zzsolve", session_id=sid)
        check("40: search uses the session's docs root", resp["docs_root_configured"]
              and [s["citation"] for s in resp["sources"]] == ["zzsolve.rst"])
        check("40: a doc source carries the read hint", resp["sources"][0].get("read_hint") == server_mod.READ_DOC_HINT)
        check("40: and its docs.aptech.com page (§9.3)",
              resp["sources"][0].get("docs_url") == "https://docs.aptech.com/gauss/zzsolve.html")
        explicit = server_mod.gauss_search_docs("zzsolve", docs_root=root)
        check("40: otherwise identical to an explicit docs_root", explicit == resp)
        catalog = server_mod.gauss_search_docs("G0025", docs_root=root)
        check("40: an error-catalog source has no read hint or page link", catalog["sources"] and all(
            "read_hint" not in s and "docs_url" not in s for s in catalog["sources"]))
        read = server_mod.gauss_read_doc("zzsolve.rst", section="Source", session_id=sid)
        check("40: read uses the session's docs root", "zzsolve.src" in read.get("content", ""))
        check("40: an unknown session_id is an error", server_mod.gauss_search_docs("zzsolve", session_id="nope")
              == {"error": "unknown_session"})


def test_41_v089_idle_and_lru_eviction() -> None:
    real_clock, real_cap = server_mod._monotonic, server_mod.MAX_SESSIONS
    now = [real_clock()]
    server_mod._monotonic = lambda: now[0]
    try:
        with tempfile.TemporaryDirectory() as tmp:
            sid = _start(tmp)
            validation = server_mod.gauss_validate_code(sid, CANDIDATE_CODE)
            prepared = server_mod.gauss_execution_prepare(sid, validation["validation_id"])
            check("41: a prompt is pending", "request_id" in prepared)
            now[0] += server_mod.SESSION_IDLE_SECONDS - 1
            check("41: just under the bound, still alive", "error" not in server_mod.gauss_validate_code(sid, "x = 1;"))
            now[0] += server_mod.SESSION_IDLE_SECONDS + 1
            decided = server_mod.gauss_execution_decide(sid, "yes", request_id=prepared["request_id"])
            check("41: an idle session expires, and its pending prompt approves nothing",
                  decided.get("error") == "session_expired" and "outcome" not in decided and sid not in server_mod._sessions)
            check("41: any later call says expired", server_mod.gauss_validate_code(sid, "x = 1;").get("error") == "session_expired")

            repair = server_mod.gauss_repair_start(runner="fake", workspace_parent=tmp)
            rsid = repair["session_id"]
            closed = []
            adapter = server_mod._repair_sessions[rsid].adapter
            original_close = adapter.close
            adapter.close = lambda: (closed.append(rsid), original_close())
            now[0] += server_mod.SESSION_IDLE_SECONDS + 1
            server_mod.gauss_session_start(runner="fake", docs_root=_fixture_docs_root(tmp), workspace_parent=tmp)
            check("41: an idle repair session is closed through its own close path", closed == [rsid]
                  and rsid not in server_mod._repair_sessions)
            check("41: and reports expired", server_mod.gauss_repair_command(rsid, "help").get("error") == "session_expired")

            server_mod.MAX_SESSIONS = 3
            ids = []
            for _ in range(4):
                now[0] += 1
                ids.append(server_mod.gauss_session_start(
                    runner="fake", docs_root=_fixture_docs_root(tmp), workspace_parent=tmp)["session_id"])
            server_mod._sweep_sessions()
            check("41: the cap closes the least recently used", ids[0] not in server_mod._sessions
                  and all(i in server_mod._sessions for i in ids[1:]))
            # Every call pins docs_root, so this machine's own config never decides the result.
            reused = server_mod.gauss_session_start(
                runner="fake", docs_root=_fixture_docs_root(tmp), workspace_parent=tmp, session_id=sid)["session_id"]
            check("41: an expired id may be started again", reused == sid and sid in server_mod._sessions
                  and "error" not in server_mod.gauss_validate_code(sid, "x = 1;"))
    finally:
        server_mod._monotonic, server_mod.MAX_SESSIONS = real_clock, real_cap


def test_42_v089_server_version_and_annotations() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        resp = server_mod.gauss_session_start(runner="fake", docs_root=_fixture_docs_root(tmp), workspace_parent=tmp)
        check("42: server_version", resp.get("server_version") == server_mod.__version__)
    tools = {t.name: t.annotations for t in asyncio.run(server_mod.server.list_tools())}
    read_only = {"gauss_session_start", "gauss_session_close", "gauss_search_docs", "gauss_read_doc",
                 "gauss_validate_code", "gauss_execution_prepare"}
    for name in read_only:
        check(f"42: {name} is read-only", tools[name] is not None and tools[name].read_only_hint is True
              and tools[name].open_world_hint is False)
    for name in ("gauss_execution_decide", "gauss_repair_start", "gauss_repair_command", "gauss_repair_close"):
        check(f"42: {name} is not read-only", tools[name] is not None and tools[name].read_only_hint is False)
    check("42: decide is marked destructive", tools["gauss_execution_decide"].destructive_hint is True)
    fresh = MCPServer("probe")
    server_mod._register_chat_tools(fresh)
    chat = {t.name: t.annotations for t in asyncio.run(fresh.list_tools())}
    check("42: chat_ask may reach a model provider", chat["gauss_chat_ask"].open_world_hint is True)
    check("42: chat_reset is read-only", chat["gauss_chat_reset"].read_only_hint is True)
    check("42: the read tool is named in the instructions", "gauss_read_doc" in (server_mod.server.instructions or ""))


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
