"""Model-provider abstraction for conversational GAUSS Q&A (v0.70.0; local
Ollama provider added in v0.71.0).

This is the ONLY module in this repository that ever constructs a request
to, or parses a response from, a real language-model API. The rest of the
application (`gauss_conversation_engine.py`, `gauss_ai_chat.py`, and every
existing module) sees only `ChatMessage`/`ProviderResult` -- provider-
specific request/response shapes never leak past this file.

Three providers exist:

- `FakeModelProvider` -- fully deterministic, no network, no randomness. It
  is NOT a claim of real conversational intelligence: it never synthesizes
  an answer, it only echoes back whatever grounding context it was given
  (or honestly says none was available) plus a fixed disclosure that it is
  a placeholder. This exists so the entire conversational system -- engine,
  CLI, grounding, bounded history, boundary checks -- is fully testable
  without network access or API charges, and so a tester with no configured
  real provider still gets an honest, working (if unsynthesized) chat
  session rather than a hard failure. `chat_provider` defaults to `"fake"`,
  mirroring `gauss_ai_config.py`'s own `default_runner`-defaults-to-`"fake"`
  precedent -- the safe default requires no credential and no network call.

- `AnthropicMessagesProvider` -- the one real provider this milestone adds,
  using only `urllib.request` (Python standard library) to call the
  Anthropic Messages API (`POST /v1/messages`). No third-party package is
  added as a dependency; this repository has had zero runtime dependencies
  through every prior milestone, and a single, small, stdlib-only HTTP call
  keeps that true. The API key is read from the `ANTHROPIC_API_KEY`
  environment variable INSIDE `complete(...)`, at call time only -- it is
  never accepted as a constructor argument, never stored as an instance
  attribute, never written to `gauss_ai_config.py`'s config file, and never
  logged. A missing key is reported as an honest `ProviderResult` failure
  (`error_kind="configuration"`), never a crash and never a silent fallback
  to the fake provider.

  IMPORTANT, stated once here rather than fabricated elsewhere: this
  adapter's own request/response/error-handling logic is fully unit-tested
  via an injected fake `transport` callable (see `test_gauss_chat_provider.
  py`), but no live network round trip against the real Anthropic API was
  performed during this milestone's development, because no
  `ANTHROPIC_API_KEY` is configured in this environment. The HTTP call path
  is real, standard, and has not been independently confirmed against the
  live API by this repository as of `v0.70.0`.

- `OllamaProvider` (v0.71.0) -- the local, zero-API-cost provider, calling a
  locally running Ollama service's own `POST /api/chat` endpoint, again via
  `urllib.request` only. No API key is required or accepted: local Ollama
  has no authentication for its default local-only listener. Request/
  response shapes are taken directly from Ollama's own authoritative
  documentation, verified before this was written (not from memory):
  https://docs.ollama.com/api/chat, https://docs.ollama.com/api/errors, and
  https://github.com/ollama/ollama/blob/main/docs/api.md. Unlike Anthropic,
  Ollama's `/api/chat` accepts `"system"`/`"user"`/`"assistant"` roles
  directly within its own `messages` array -- there is no separate top-
  level `system` field to assemble. A token cap is passed as
  `options.num_predict` (Ollama's own documented mechanism), and streaming
  is explicitly disabled (`"stream": false`) so exactly one JSON object is
  returned, matching this module's single-shot `complete(...)` contract.
  Ollama's own documented error shape is `{"error": "<string>"}` at the top
  level (never nested, unlike Anthropic's `{"error": {"message": ...}}`) --
  a 404 whose message contains "not found" is reported as the more specific
  `model_unavailable` error kind (with the exact `ollama pull <model>`
  command to fix it), never conflated with a generic HTTP error or a
  service-unreachable network error. `OllamaProvider` never falls back to
  any other provider on any failure -- an unreachable service, a missing
  model, or a malformed response are all reported as honest `ProviderResult`
  failures for the caller to display, exactly like `AnthropicMessagesProvider`
  already does.

  `check_ollama_service(...)` is a separate, explicitly read-only helper
  (`GET /api/tags`, Ollama's own documented model-listing endpoint) used by
  `gauss-ai doctor` and `gauss-ai init` to report service reachability and
  locally available models -- it never triggers a model pull or any
  generation, and is never called by `OllamaProvider.complete(...)` itself.
"""

from __future__ import annotations

import enum
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Protocol

FAKE_PROVIDER = "fake"
ANTHROPIC_PROVIDER = "anthropic"
OLLAMA_PROVIDER = "ollama"

#: Read at call time only -- see module docstring.
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"
DEFAULT_ANTHROPIC_BASE_URL = "https://api.anthropic.com"
DEFAULT_ANTHROPIC_API_VERSION = "2023-06-01"
DEFAULT_MAX_TOKENS = 1024
#: A conservative network timeout for the default transport -- never
#: unbounded, mirroring this repository's existing GAUSS-execution timeout
#: discipline (`gauss_code_execution.py`).
DEFAULT_TIMEOUT_SECONDS = 30.0

#: Ollama's own documented local default -- see module docstring for the
#: authoritative sources this was verified against. No API key of any kind
#: is required or accepted for a local Ollama service.
DEFAULT_OLLAMA_ENDPOINT = "http://localhost:11434"
#: See `docs/ollama-models.md` for the full recommendation policy and why
#: this specific model/size was chosen for private alpha (Apache-2.0
#: licensed, strong instruction-following and coding ability, practical on
#: 8GB+ RAM/VRAM consumer hardware). Never bundled with this repository --
#: the user must `ollama pull` it themselves.
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
OLLAMA_CHAT_PATH = "/api/chat"
OLLAMA_TAGS_PATH = "/api/tags"
#: A longer default timeout than the cloud providers' -- a local model
#: running on CPU can genuinely take longer than a cloud API round trip;
#: still explicit and bounded, never unbounded.
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 120.0


@dataclass(frozen=True)
class ChatMessage:
    """One turn's worth of content. `role` is `"system"`, `"user"`, or
    `"assistant"` -- this module does not enforce that as an enum, since
    both providers below already validate what they actually need from it,
    but callers should not invent a fourth role."""

    role: str
    content: str


class ProviderErrorKind(enum.Enum):
    #: A precondition the caller controls was not met -- e.g. a missing
    #: credential, or an unknown provider name. Never a network attempt.
    CONFIGURATION = "configuration"
    #: The request could not reach the provider at all (DNS, connection,
    #: timeout) -- distinct from a real, provider-returned HTTP error.
    NETWORK = "network"
    #: The provider was reached and responded with an HTTP error status.
    HTTP_ERROR = "http_error"
    #: The provider responded with HTTP success, but the response body did
    #: not have the shape this adapter expects.
    MALFORMED_RESPONSE = "malformed_response"
    #: The provider (currently: Ollama only) was reached, but the
    #: specifically configured model is not available there -- distinct
    #: from a generic HTTP error so callers (doctor, chat) can give an
    #: actionable "pull it first" message rather than a generic failure.
    MODEL_UNAVAILABLE = "model_unavailable"


@dataclass(frozen=True)
class ProviderResult:
    success: bool
    text: str | None
    provider_name: str
    model: str | None
    #: One of `ProviderErrorKind`'s values, or `None` on success.
    error_kind: str | None = None
    error_message: str | None = None


class ModelProvider(Protocol):
    """The entire interface the rest of this application depends on. Small
    and testable by design -- one method, plain dataclasses in and out, no
    provider SDK object anywhere in the signature."""

    def complete(self, messages: tuple[ChatMessage, ...], *, max_tokens: int = DEFAULT_MAX_TOKENS) -> ProviderResult: ...


@dataclass
class FakeModelProvider:
    """Deterministic, network-free provider -- see module docstring for why
    this is not, and must never be presented as, real conversational
    intelligence. `canned_answer`, if supplied, overrides the templated
    behavior entirely (used by tests that want a fixed, known response)."""

    canned_answer: str | None = None

    def complete(self, messages: tuple[ChatMessage, ...], *, max_tokens: int = DEFAULT_MAX_TOKENS) -> ProviderResult:
        del max_tokens
        if self.canned_answer is not None:
            return ProviderResult(
                success=True, text=self.canned_answer, provider_name=FAKE_PROVIDER, model="fake-deterministic-v1"
            )
        grounding = next(
            (m.content for m in reversed(messages) if m.role == "system" and m.content.startswith("GROUNDING_CONTEXT:")),
            None,
        )
        user_text = next((m.content for m in reversed(messages) if m.role == "user"), "")
        if grounding is not None:
            text = (
                "[fake/test provider -- template only, no synthesis performed]\n"
                f"Here is the retrieved information relevant to your question ({user_text!r}):\n\n"
                f"{grounding[len('GROUNDING_CONTEXT:'):].strip()}\n\n"
                "Configure a real provider (see docs/conversational-qa.md) for a synthesized, "
                "conversational answer instead of this raw retrieval echo."
            )
        else:
            text = (
                "[fake/test provider -- no real language understanding]\n"
                f"No local documentation or catalog match was found for your question ({user_text!r}), "
                "and this deterministic fallback provider cannot generate a general answer. Configure a "
                "real provider (see docs/conversational-qa.md) for a genuine conversational answer."
            )
        return ProviderResult(success=True, text=text, provider_name=FAKE_PROVIDER, model="fake-deterministic-v1")


def _default_transport(request: urllib.request.Request) -> tuple[int, bytes]:
    """The one, real, network-touching function in this module. Injectable
    on `AnthropicMessagesProvider` so every test can replace it with a fake
    callable and never touch a real socket."""
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _default_ollama_transport(request: urllib.request.Request) -> tuple[int, bytes]:
    """Identical to `_default_transport` except for a longer default
    timeout (`DEFAULT_OLLAMA_TIMEOUT_SECONDS`) -- a local model, especially
    on CPU, can genuinely take longer than a cloud API round trip. Kept as
    a separate function (rather than a parameterized one) because the
    `transport` field's own type on both provider dataclasses is a plain
    one-argument callable, matching `ModelProvider`'s minimal-surface
    convention -- not because the request-handling logic itself differs."""
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_OLLAMA_TIMEOUT_SECONDS) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _extract_ollama_error(raw_body: bytes) -> str | None:
    """Ollama's own documented error shape is `{"error": "<string>"}` at
    the top level -- verified against https://docs.ollama.com/api/errors,
    never nested the way Anthropic's `{"error": {"message": ...}}` is."""
    try:
        parsed = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(parsed, dict):
        return None
    error = parsed.get("error")
    return error if isinstance(error, str) and error else None


@dataclass
class AnthropicMessagesProvider:
    """See module docstring for the full credential/testing disclosure.
    `model`/`base_url`/`api_version`/`max_tokens` are all explicit,
    overridable constructor arguments -- nothing about a specific model
    version is hard-coded beyond a documented, overridable default."""

    model: str | None = None
    base_url: str = DEFAULT_ANTHROPIC_BASE_URL
    api_version: str = DEFAULT_ANTHROPIC_API_VERSION
    transport: Callable[[urllib.request.Request], tuple[int, bytes]] = _default_transport
    #: Injectable so tests never read a real environment variable either.
    env: dict[str, str] | None = None

    def complete(self, messages: tuple[ChatMessage, ...], *, max_tokens: int = DEFAULT_MAX_TOKENS) -> ProviderResult:
        env = self.env if self.env is not None else os.environ
        api_key = env.get(ANTHROPIC_API_KEY_ENV, "").strip()
        resolved_model = self.model or DEFAULT_ANTHROPIC_MODEL
        if not api_key:
            return ProviderResult(
                success=False,
                text=None,
                provider_name=ANTHROPIC_PROVIDER,
                model=resolved_model,
                error_kind=ProviderErrorKind.CONFIGURATION.value,
                error_message=(
                    f"{ANTHROPIC_API_KEY_ENV} is not set. Real conversational answers require a real API "
                    f"key in this environment variable; it is never read from, or written to, gauss-ai's "
                    "own config file."
                ),
            )

        system_text = "\n\n".join(m.content for m in messages if m.role == "system")
        conversation = [{"role": m.role, "content": m.content} for m in messages if m.role in {"user", "assistant"}]
        body = {"model": resolved_model, "max_tokens": max_tokens, "messages": conversation}
        if system_text:
            body["system"] = system_text

        request = urllib.request.Request(
            url=f"{self.base_url}/v1/messages",
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={
                "x-api-key": api_key,
                "anthropic-version": self.api_version,
                "content-type": "application/json",
            },
        )

        try:
            status, raw_body = self.transport(request)
        except urllib.error.URLError as exc:
            return ProviderResult(
                success=False, text=None, provider_name=ANTHROPIC_PROVIDER, model=resolved_model,
                error_kind=ProviderErrorKind.NETWORK.value, error_message=f"could not reach {self.base_url}: {exc}",
            )
        except OSError as exc:
            return ProviderResult(
                success=False, text=None, provider_name=ANTHROPIC_PROVIDER, model=resolved_model,
                error_kind=ProviderErrorKind.NETWORK.value, error_message=f"network error contacting {self.base_url}: {exc}",
            )

        if status >= 400:
            message = f"HTTP {status}"
            try:
                parsed_error = json.loads(raw_body.decode("utf-8"))
                inner = parsed_error.get("error", {})
                if isinstance(inner, dict) and inner.get("message"):
                    message = f"HTTP {status}: {inner['message']}"
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                pass
            return ProviderResult(
                success=False, text=None, provider_name=ANTHROPIC_PROVIDER, model=resolved_model,
                error_kind=ProviderErrorKind.HTTP_ERROR.value, error_message=message,
            )

        try:
            parsed = json.loads(raw_body.decode("utf-8"))
            content_blocks = parsed["content"]
            text = "".join(block["text"] for block in content_blocks if block.get("type") == "text")
            if not text:
                raise KeyError("no text content block in response")
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, IndexError) as exc:
            return ProviderResult(
                success=False, text=None, provider_name=ANTHROPIC_PROVIDER, model=resolved_model,
                error_kind=ProviderErrorKind.MALFORMED_RESPONSE.value,
                error_message=f"response did not have the expected shape: {exc}",
            )

        return ProviderResult(
            success=True, text=text, provider_name=ANTHROPIC_PROVIDER, model=parsed.get("model", resolved_model),
        )


@dataclass
class OllamaProvider:
    """Local, zero-API-cost provider. See module docstring for the full
    endpoint/request/response/error-handling disclosure, verified against
    Ollama's own current documentation before this was written. `model`
    defaults to `DEFAULT_OLLAMA_MODEL` (see `docs/ollama-models.md` for the
    recommendation policy); `endpoint` defaults to Ollama's own documented
    local default and should only be overridden if Ollama itself has been
    configured to listen elsewhere. No API key field exists here at all --
    not merely unset -- because local Ollama has no concept of one."""

    model: str | None = None
    endpoint: str = DEFAULT_OLLAMA_ENDPOINT
    transport: Callable[[urllib.request.Request], tuple[int, bytes]] = _default_ollama_transport

    def complete(self, messages: tuple[ChatMessage, ...], *, max_tokens: int = DEFAULT_MAX_TOKENS) -> ProviderResult:
        resolved_model = self.model or DEFAULT_OLLAMA_MODEL
        # Ollama's /api/chat accepts "system"/"user"/"assistant" roles
        # directly within its own messages array -- confirmed against
        # https://docs.ollama.com/api/chat -- unlike Anthropic, there is no
        # separate top-level "system" field to assemble here.
        conversation = [{"role": m.role, "content": m.content} for m in messages]
        body = {
            "model": resolved_model,
            "messages": conversation,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        request = urllib.request.Request(
            url=f"{self.endpoint}{OLLAMA_CHAT_PATH}",
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={"content-type": "application/json"},
        )

        try:
            status, raw_body = self.transport(request)
        except urllib.error.URLError as exc:
            return ProviderResult(
                success=False, text=None, provider_name=OLLAMA_PROVIDER, model=resolved_model,
                error_kind=ProviderErrorKind.NETWORK.value,
                error_message=(
                    f"could not reach the local Ollama service at {self.endpoint}: {exc}. Is Ollama running? "
                    "Start it, or run 'gauss-ai doctor' for a diagnostic."
                ),
            )
        except OSError as exc:
            return ProviderResult(
                success=False, text=None, provider_name=OLLAMA_PROVIDER, model=resolved_model,
                error_kind=ProviderErrorKind.NETWORK.value,
                error_message=f"network error contacting {self.endpoint}: {exc}",
            )

        if status == 404:
            message = _extract_ollama_error(raw_body) or f"HTTP 404 from {self.endpoint}"
            if "not found" in message.lower():
                return ProviderResult(
                    success=False, text=None, provider_name=OLLAMA_PROVIDER, model=resolved_model,
                    error_kind=ProviderErrorKind.MODEL_UNAVAILABLE.value,
                    error_message=f"{message} -- pull it first with: ollama pull {resolved_model}",
                )
            return ProviderResult(
                success=False, text=None, provider_name=OLLAMA_PROVIDER, model=resolved_model,
                error_kind=ProviderErrorKind.HTTP_ERROR.value, error_message=message,
            )
        if status >= 400:
            message = _extract_ollama_error(raw_body) or f"HTTP {status} from {self.endpoint}"
            return ProviderResult(
                success=False, text=None, provider_name=OLLAMA_PROVIDER, model=resolved_model,
                error_kind=ProviderErrorKind.HTTP_ERROR.value, error_message=message,
            )

        try:
            parsed = json.loads(raw_body.decode("utf-8"))
            text = parsed["message"]["content"]
            if not isinstance(text, str) or not text:
                raise KeyError("no non-empty message.content in response")
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as exc:
            return ProviderResult(
                success=False, text=None, provider_name=OLLAMA_PROVIDER, model=resolved_model,
                error_kind=ProviderErrorKind.MALFORMED_RESPONSE.value,
                error_message=f"response did not have the expected shape: {exc}",
            )

        return ProviderResult(
            success=True, text=text, provider_name=OLLAMA_PROVIDER, model=parsed.get("model", resolved_model),
        )


@dataclass(frozen=True)
class OllamaServiceStatus:
    """Result of a read-only `GET /api/tags` probe -- never triggers a
    model pull or any generation."""

    reachable: bool
    #: Locally available model names exactly as Ollama reports them (e.g.
    #: "qwen2.5-coder:7b") -- empty if unreachable or the response was
    #: unparseable.
    models: tuple[str, ...]
    error_message: str | None = None


def check_ollama_service(
    *,
    endpoint: str = DEFAULT_OLLAMA_ENDPOINT,
    transport: Callable[[urllib.request.Request], tuple[int, bytes]] = _default_ollama_transport,
) -> OllamaServiceStatus:
    """Read-only reachability/model-listing probe, used by `gauss-ai
    doctor` and `gauss-ai init`. Calls Ollama's own documented `GET
    /api/tags` endpoint (https://docs.ollama.com/api/tags) -- never `/api/
    chat`, never `/api/pull`; nothing here can trigger generation or a
    download. Never raises; every failure mode is reported on the returned
    `OllamaServiceStatus`."""
    request = urllib.request.Request(url=f"{endpoint}{OLLAMA_TAGS_PATH}", method="GET")
    try:
        status, raw_body = transport(request)
    except (urllib.error.URLError, OSError) as exc:
        return OllamaServiceStatus(reachable=False, models=(), error_message=str(exc))
    if status >= 400:
        return OllamaServiceStatus(
            reachable=False, models=(), error_message=_extract_ollama_error(raw_body) or f"HTTP {status}"
        )
    try:
        parsed = json.loads(raw_body.decode("utf-8"))
        raw_models = parsed.get("models", []) if isinstance(parsed, dict) else []
        names = tuple(
            str(entry.get("name") or entry.get("model"))
            for entry in raw_models
            if isinstance(entry, dict) and (entry.get("name") or entry.get("model"))
        )
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
        return OllamaServiceStatus(reachable=True, models=(), error_message="response did not have the expected shape")
    return OllamaServiceStatus(reachable=True, models=names)


def ollama_model_matches(configured_model: str, available_models: tuple[str, ...]) -> bool:
    """Bounded, documented matching between a configured model name and
    Ollama's own reported local model names. Ollama model names are
    conventionally `<name>:<tag>` (default tag `latest`): an exact
    configured name (e.g. `qwen2.5-coder:7b`) must match exactly; a bare
    configured name with no tag (e.g. `llama3.1`) matches any installed
    tag of that same base name (e.g. `llama3.1:latest`). Never a fuzzy or
    partial-string match."""
    if configured_model in available_models:
        return True
    if ":" in configured_model:
        return False
    return any(name.split(":", 1)[0] == configured_model for name in available_models)


def build_provider(
    provider_name: str, *, model: str | None = None, endpoint: str | None = None
) -> "ModelProvider":
    """The one factory function callers should use. Raises `ValueError` for
    an unrecognized provider name -- never silently falls back to the fake
    provider, since that would be exactly the kind of quiet substitution
    this repository's own `v0.68.0` alpha validation work was built to
    prevent for the GAUSS runner backend. `endpoint` is meaningful only for
    `ollama` and is ignored for the other two providers."""
    if provider_name == FAKE_PROVIDER:
        return FakeModelProvider()
    if provider_name == ANTHROPIC_PROVIDER:
        return AnthropicMessagesProvider(model=model)
    if provider_name == OLLAMA_PROVIDER:
        return OllamaProvider(model=model, endpoint=endpoint or DEFAULT_OLLAMA_ENDPOINT)
    raise ValueError(
        f"unknown chat provider {provider_name!r}; supported: {FAKE_PROVIDER!r}, {ANTHROPIC_PROVIDER!r}, {OLLAMA_PROVIDER!r}"
    )
