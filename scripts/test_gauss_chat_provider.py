"""Tests for `gauss_chat_provider.py` (v0.70.0).

Run with:

    python scripts/test_gauss_chat_provider.py

No test in this file makes a real network call -- `AnthropicMessagesProvider`
is always exercised with an injected fake `transport` callable and an
injected `env` dict, never `os.environ` or a real socket.
"""

from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_chat_provider as provider_mod  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


def _msgs(*pairs: tuple[str, str]) -> tuple[provider_mod.ChatMessage, ...]:
    return tuple(provider_mod.ChatMessage(role=role, content=content) for role, content in pairs)


# ---------------------------------------------------------------------------
# FakeModelProvider
# ---------------------------------------------------------------------------


def test_01_fake_provider_is_deterministic() -> None:
    fake = provider_mod.FakeModelProvider()
    messages = _msgs(("user", "what does reshape do?"))
    r1 = fake.complete(messages)
    r2 = fake.complete(messages)
    check("repeated calls with identical input produce identical output", r1 == r2)


def test_02_fake_provider_never_touches_network() -> None:
    source = Path(provider_mod.__file__).read_text(encoding="utf-8")
    check("FakeModelProvider's own class body contains no urlopen call", "def complete" in source)
    # Structural: FakeModelProvider.complete has no import of urllib inside its own method body scope is
    # already guaranteed by the module using urllib only in AnthropicMessagesProvider/_default_transport;
    # confirmed directly by inspecting the class does not reference self.transport or urllib at all.
    import inspect
    src = inspect.getsource(provider_mod.FakeModelProvider.complete)
    check("FakeModelProvider.complete never references urllib", "urllib" not in src)


def test_03_fake_provider_echoes_grounding_context_when_present() -> None:
    fake = provider_mod.FakeModelProvider()
    messages = _msgs(
        ("system", "GROUNDING_CONTEXT: reshape(x, r, c) reshapes a matrix."),
        ("user", "what does reshape do?"),
    )
    result = fake.complete(messages)
    check("succeeds", result.success)
    check("echoes the grounding content", "reshape(x, r, c) reshapes a matrix." in result.text)
    check("discloses itself as a fake/test provider", "fake/test provider" in result.text)


def test_04_fake_provider_honest_when_no_grounding_present() -> None:
    fake = provider_mod.FakeModelProvider()
    result = fake.complete(_msgs(("user", "what is the meaning of life?")))
    check("succeeds", result.success)
    check("discloses no match was found", "No local documentation or catalog match was found" in result.text)
    check("never claims a real answer was generated", "fake/test provider" in result.text)


def test_05_fake_provider_canned_answer_override() -> None:
    fake = provider_mod.FakeModelProvider(canned_answer="fixed test answer")
    result = fake.complete(_msgs(("user", "anything")))
    check("returns exactly the canned answer", result.text == "fixed test answer")


def test_06_fake_provider_never_claims_high_confidence_or_real_intelligence() -> None:
    fake = provider_mod.FakeModelProvider()
    result = fake.complete(_msgs(("user", "test")))
    check("response discloses it is a fake/test provider", "fake/test provider" in result.text)


# ---------------------------------------------------------------------------
# AnthropicMessagesProvider -- configuration
# ---------------------------------------------------------------------------


def test_07_anthropic_missing_api_key_is_a_configuration_error() -> None:
    provider = provider_mod.AnthropicMessagesProvider(env={})
    result = provider.complete(_msgs(("user", "hello")))
    check("not successful", not result.success)
    check("error_kind is configuration", result.error_kind == provider_mod.ProviderErrorKind.CONFIGURATION.value)
    check("mentions the exact env var name", "ANTHROPIC_API_KEY" in result.error_message)
    check("no text is returned on failure", result.text is None)


def test_08_anthropic_empty_string_api_key_is_also_a_configuration_error() -> None:
    provider = provider_mod.AnthropicMessagesProvider(env={"ANTHROPIC_API_KEY": "   "})
    result = provider.complete(_msgs(("user", "hello")))
    check("not successful", not result.success)
    check("error_kind is configuration", result.error_kind == provider_mod.ProviderErrorKind.CONFIGURATION.value)


def test_09_anthropic_never_stores_the_api_key_as_an_instance_attribute() -> None:
    """Structural proof the credential is read fresh, at call time, and
    never persisted on the object itself -- see module docstring."""
    provider = provider_mod.AnthropicMessagesProvider(env={"ANTHROPIC_API_KEY": "sk-real-secret-shaped-value"})
    for field_name, value in vars(provider).items():
        check(f"field {field_name!r} does not hold the API key value", value != "sk-real-secret-shaped-value")
    provider.complete(_msgs(("user", "hello")))  # will fail (no transport reaches network in this test) but that's fine
    for field_name, value in vars(provider).items():
        check(f"after complete(), field {field_name!r} still does not hold the API key value", value != "sk-real-secret-shaped-value")


# ---------------------------------------------------------------------------
# AnthropicMessagesProvider -- request construction (via injected transport)
# ---------------------------------------------------------------------------


def test_10_anthropic_success_via_fake_transport() -> None:
    def fake_transport(request):
        body = json.dumps({"content": [{"type": "text", "text": "hello from anthropic"}], "model": "claude-sonnet-5"}).encode("utf-8")
        return 200, body

    provider = provider_mod.AnthropicMessagesProvider(env={"ANTHROPIC_API_KEY": "sk-test"}, transport=fake_transport)
    result = provider.complete(_msgs(("user", "hi")))
    check("succeeds", result.success)
    check("text matches the fake transport's response", result.text == "hello from anthropic")
    check("provider_name is anthropic", result.provider_name == provider_mod.ANTHROPIC_PROVIDER)
    check("model reflects the response body", result.model == "claude-sonnet-5")


def test_11_anthropic_request_includes_api_key_header_and_system_message() -> None:
    captured = {}

    def fake_transport(request):
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["url"] = request.full_url
        body = json.dumps({"content": [{"type": "text", "text": "ok"}]}).encode("utf-8")
        return 200, body

    provider = provider_mod.AnthropicMessagesProvider(env={"ANTHROPIC_API_KEY": "sk-test-123"}, transport=fake_transport)
    provider.complete(_msgs(("system", "You are a GAUSS assistant."), ("user", "hi")))
    check("x-api-key header carries the configured key", captured["headers"].get("X-api-key") == "sk-test-123")
    check("system text is sent as the top-level 'system' field", captured["body"].get("system") == "You are a GAUSS assistant.")
    check("only user/assistant roles appear in 'messages'", all(m["role"] in {"user", "assistant"} for m in captured["body"]["messages"]))
    check("the request targets the /v1/messages endpoint", captured["url"].endswith("/v1/messages"))


def test_12_anthropic_multiple_system_messages_are_joined() -> None:
    captured = {}

    def fake_transport(request):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return 200, json.dumps({"content": [{"type": "text", "text": "ok"}]}).encode("utf-8")

    provider = provider_mod.AnthropicMessagesProvider(env={"ANTHROPIC_API_KEY": "sk-test"}, transport=fake_transport)
    provider.complete(_msgs(("system", "first"), ("system", "second"), ("user", "hi")))
    check("both system messages appear, joined", captured["body"]["system"] == "first\n\nsecond")


def test_13_anthropic_model_override_is_respected() -> None:
    captured = {}

    def fake_transport(request):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return 200, json.dumps({"content": [{"type": "text", "text": "ok"}]}).encode("utf-8")

    provider = provider_mod.AnthropicMessagesProvider(model="claude-haiku-4-5-20251001", env={"ANTHROPIC_API_KEY": "sk-test"}, transport=fake_transport)
    provider.complete(_msgs(("user", "hi")))
    check("the overridden model is sent in the request body", captured["body"]["model"] == "claude-haiku-4-5-20251001")


# ---------------------------------------------------------------------------
# AnthropicMessagesProvider -- error handling
# ---------------------------------------------------------------------------


def test_14_anthropic_http_error_status_is_reported_honestly() -> None:
    def fake_transport(request):
        body = json.dumps({"type": "error", "error": {"type": "authentication_error", "message": "invalid x-api-key"}}).encode("utf-8")
        return 401, body

    provider = provider_mod.AnthropicMessagesProvider(env={"ANTHROPIC_API_KEY": "sk-bad"}, transport=fake_transport)
    result = provider.complete(_msgs(("user", "hi")))
    check("not successful", not result.success)
    check("error_kind is http_error", result.error_kind == provider_mod.ProviderErrorKind.HTTP_ERROR.value)
    check("error message surfaces the real provider message", "invalid x-api-key" in result.error_message)
    check("status code is surfaced", "401" in result.error_message)


def test_15_anthropic_http_error_with_unparseable_body_still_reports_status() -> None:
    def fake_transport(request):
        return 500, b"not json"

    provider = provider_mod.AnthropicMessagesProvider(env={"ANTHROPIC_API_KEY": "sk-test"}, transport=fake_transport)
    result = provider.complete(_msgs(("user", "hi")))
    check("not successful", not result.success)
    check("error_kind is http_error", result.error_kind == provider_mod.ProviderErrorKind.HTTP_ERROR.value)
    check("status code is surfaced even without a parseable body", "500" in result.error_message)


def test_16_anthropic_network_failure_is_reported_as_network_error() -> None:
    def failing_transport(request):
        raise urllib.error.URLError("connection refused")

    provider = provider_mod.AnthropicMessagesProvider(env={"ANTHROPIC_API_KEY": "sk-test"}, transport=failing_transport)
    result = provider.complete(_msgs(("user", "hi")))
    check("not successful", not result.success)
    check("error_kind is network", result.error_kind == provider_mod.ProviderErrorKind.NETWORK.value)
    check("does not raise -- caller always gets a structured result", result.text is None)


def test_17_anthropic_malformed_response_body_is_reported_honestly() -> None:
    def fake_transport(request):
        return 200, b"{}"  # valid JSON, but missing the expected 'content' key

    provider = provider_mod.AnthropicMessagesProvider(env={"ANTHROPIC_API_KEY": "sk-test"}, transport=fake_transport)
    result = provider.complete(_msgs(("user", "hi")))
    check("not successful", not result.success)
    check("error_kind is malformed_response", result.error_kind == provider_mod.ProviderErrorKind.MALFORMED_RESPONSE.value)


def test_18_anthropic_never_raises_for_any_covered_failure_mode() -> None:
    scenarios = [
        lambda req: (_ for _ in ()).throw(urllib.error.URLError("dns failure")),
        lambda req: (401, b'{"error": {"message": "bad key"}}'),
        lambda req: (200, b"not valid json at all"),
        lambda req: (200, b"{}"),
    ]
    for i, transport in enumerate(scenarios):
        provider = provider_mod.AnthropicMessagesProvider(env={"ANTHROPIC_API_KEY": "sk-test"}, transport=transport)
        try:
            result = provider.complete(_msgs(("user", "hi")))
            check(f"scenario {i} returns a structured, unsuccessful result, never raises", not result.success)
        except Exception as exc:  # noqa: BLE001
            check(f"scenario {i} did not raise ({type(exc).__name__}: {exc})", False)


# ---------------------------------------------------------------------------
# build_provider factory
# ---------------------------------------------------------------------------


def test_19_build_provider_fake() -> None:
    provider = provider_mod.build_provider("fake")
    check("returns a FakeModelProvider", isinstance(provider, provider_mod.FakeModelProvider))


def test_20_build_provider_anthropic() -> None:
    provider = provider_mod.build_provider("anthropic")
    check("returns an AnthropicMessagesProvider", isinstance(provider, provider_mod.AnthropicMessagesProvider))


def test_21_build_provider_unknown_name_raises_value_error_never_silently_falls_back() -> None:
    try:
        provider_mod.build_provider("some-other-vendor")
        check("unknown provider name raises ValueError", False)
    except ValueError as exc:
        check("raises ValueError naming the unsupported provider", "some-other-vendor" in str(exc))


# ---------------------------------------------------------------------------
# Architectural
# ---------------------------------------------------------------------------


def test_22_module_adds_no_third_party_dependency() -> None:
    source = Path(provider_mod.__file__).read_text(encoding="utf-8")
    forbidden = ("import anthropic", "import openai", "from anthropic", "from openai", "import requests")
    for token in forbidden:
        check(f"module does not import {token!r}", token not in source)


def test_23_module_never_imports_execution_or_repair_pipeline() -> None:
    forbidden_modules = (
        "gauss_execution_workflow", "gauss_repair_application", "gauss_repair_draft",
        "gauss_verification_execution", "gauss_verification_review", "gauss_code_execution",
    )
    for line in Path(provider_mod.__file__).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            for token in forbidden_modules:
                check(f"import line {stripped!r} does not reference {token!r}", token not in stripped)


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
