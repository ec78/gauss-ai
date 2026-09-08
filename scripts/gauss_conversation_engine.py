"""Conversational GAUSS Q&A engine (v0.70.0).

Position relative to the rest of this repository: this module is the FIRST
genuine conversational capability in the project's history. Everything
before it ("Try The GAUSS Code Assistant" in `README.md`) meant a human
manually assembling `experts/`/`agents/`/`workflows/` markdown files into a
separate chat UI. This module programmatically assembles a small, fixed
system prompt plus real, structured grounding evidence, and calls a
`gauss_chat_provider.ModelProvider` -- but it still never executes GAUSS,
never repairs code, and never bypasses any existing approval layer; see the
"Boundary" section below.

Grounding (reused, never duplicated):

- A `G####`-shaped token in the question is looked up directly via
  `gauss_error_catalog.lookup_error(...)` -- the exact same verified
  catalog `interpret`/`diagnose`/`repair-plan` already consume. No error
  knowledge is redefined here.
- Otherwise, if a local documentation root is configured (`docs_root`,
  resolved by the caller via `gauss_ai_config.resolve_docs_root(...)`),
  candidate word tokens from the question are looked up via
  `command_doc_lookup.lookup(...)` -- the exact same local-docs retrieval
  tool `v0.6.0`-`v0.11.0` already built and evaluated. No parallel
  retrieval implementation exists here.
- If neither source produces a hit, the question is answered from the
  provider's own knowledge, and this is disclosed honestly -- never
  presented as documentation-grounded.

Boundary: this module has no import of, and no code path capable of
calling, `gauss_execution_workflow`, any `gauss_repair_*` module, or any
`gauss_verification_*` module -- verified structurally by a dedicated test,
not merely by convention. A bounded, explicit keyword heuristic detects an
execution-imperative question ("run this", "execute that") and returns a
fixed, honest redirect to `gauss-ai repair <file.gss>` WITHOUT ever calling
the model for that turn -- this is a UX nicety, not the actual safety
guarantee; the actual guarantee is the structural absence of any import
capable of executing or repairing anything. Any answer text that looks
code-shaped always receives a fixed, non-model-dependent "not executed in
this conversation" footer, appended by this module -- never left to the
model to remember to say.

Conversation state is process-local only (`ConversationState`), bounded to
`MAX_HISTORY_TURNS`, cleared by `reset()` or process exit -- no database, no
file, no cross-process sharing, exactly mirroring every other stage's own
process-local state in `gauss_code_assistant_cli.InteractiveMvpAdapter`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import command_doc_lookup as doc_lookup_mod
import gauss_chat_provider as provider_mod
import gauss_error_catalog as catalog

#: A conservative bound on retained turns (user+assistant combined, so 20
#: turns is 10 full exchanges) -- process-local only, never persisted.
#: Oldest turns are dropped first once the bound is exceeded.
MAX_HISTORY_TURNS = 20

#: How many distinct candidate word-tokens from a single question this
#: module will attempt a real documentation lookup for -- bounded so one
#: long, rambling question cannot trigger unbounded retrieval work.
MAX_TOKEN_LOOKUPS = 6

#: Below this confidence, `command_doc_lookup.lookup(...)`'s own result is
#: treated as "no real match" rather than grounding on a weak guess.
MIN_DOC_CONFIDENCE = 0.5

#: Retrieved documentation content is truncated to this many characters
#: before being included in a provider prompt -- bounded, not unbounded
#: prompt growth from a single large documentation page.
MAX_GROUNDING_CHARS = 4000

_ERROR_CODE_RE = re.compile(r"\bG\d{4}\b", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")

#: Common English/question words filtered out of token-lookup candidates --
#: a small, explicit, reviewable list, not a claim of real NLP.
_STOPWORDS = frozenset(
    {
        "what", "does", "how", "do", "the", "a", "an", "is", "are", "in", "for", "and", "that", "this",
        "difference", "between", "example", "show", "simple", "me", "give", "explain", "why", "would",
        "use", "using", "instead", "of", "to", "from", "with", "about", "can", "you", "your", "please",
        "gauss", "vs", "compare", "comparison", "concept", "mean", "means", "meaning", "error", "code",
    }
)

_EXECUTION_KEYWORDS = (
    "run this", "execute this", "run that", "execute that", "run it", "execute it",
    "run the example", "execute the example", "run the code", "execute the code",
    "apply this repair", "apply that repair", "run this script", "execute this script",
    # v0.71.0: live Ollama validation (Phase 11) surfaced a real repair-intent
    # phrasing ("fix my file ... and apply the change") that the original,
    # narrower "run/execute this" list did not catch -- added as the same
    # kind of fixed, literal phrase, not a general repair-intent parser.
    "fix my file", "fix this file", "fix that file", "repair my file", "repair this file",
    "repair that file", "apply the change", "apply this change", "apply that change",
    "apply the fix", "apply this fix", "apply that fix",
)

_CODE_FENCE_RE = re.compile(r"```")
#: A GAUSS statement terminator at end-of-line is a reasonable, bounded
#: signal of literal GAUSS code in free-form prose -- not a full parser.
_GAUSS_STATEMENT_RE = re.compile(r";\s*(?:\n|$)")

NOT_EXECUTED_FOOTER = "\n\n(This example has not been executed in this conversation.)"

EXECUTION_BOUNDARY_MESSAGE = (
    "Conversational execution isn't available yet in this version -- this chat can't run or apply "
    "anything. To actually execute or repair a GAUSS file, use the guided command: "
    "gauss-ai repair <file.gss>"
)

SYSTEM_PROMPT = (
    "You are the GAUSS AI conversational assistant. You answer questions specifically about the GAUSS "
    "programming language and Aptech's GAUSS product: syntax, built-in procedures and functions, "
    "matrices, data handling, and error messages. Be concise by default and expand only when asked. "
    "When a message below is explicitly labeled as retrieved from official documentation or this "
    "repository's verified error catalog, treat it as authoritative and prefer it over your own general "
    "knowledge, and say that it came from that source. When no such labeled information is provided, "
    "answer from your own knowledge, but do not claim the answer is documentation-verified. If you "
    "include GAUSS code as an example, do not claim it has been run or tested -- it has not been executed "
    "in this conversation. You do not execute code, apply repairs, or modify files yourself; if asked to "
    "run or execute something, say so honestly rather than pretending to."
)


@dataclass(frozen=True)
class ChatTurn:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class ConversationState:
    """Process-local only. Nothing here is ever written to disk."""

    turns: list[ChatTurn] = field(default_factory=list)
    #: The most recently grounded topic (an error code or a command name) --
    #: used only to resolve a simple pronoun-style follow-up ("show me an
    #: example", "what about that") when the new question itself contains
    #: no independently detectable topic.
    last_topic: str | None = None

    def add(self, role: str, content: str) -> None:
        self.turns.append(ChatTurn(role=role, content=content))
        if len(self.turns) > MAX_HISTORY_TURNS:
            del self.turns[: len(self.turns) - MAX_HISTORY_TURNS]

    def reset(self) -> None:
        self.turns.clear()
        self.last_topic = None

    def as_messages(self) -> tuple["provider_mod.ChatMessage", ...]:
        return tuple(provider_mod.ChatMessage(role=t.role, content=t.content) for t in self.turns)


@dataclass(frozen=True)
class KnowledgeLookupResult:
    hit: bool
    #: One of "error_catalog", "official_docs", "uncataloged_error_code", "none".
    source: str
    topic: str | None
    content: str
    citation: str | None


def _extract_error_code(question: str) -> str | None:
    match = _ERROR_CODE_RE.search(question)
    return catalog.normalize_error_code(match.group(0)) if match else None


def _candidate_tokens(question: str) -> list[str]:
    seen: list[str] = []
    for word in _TOKEN_RE.findall(question):
        lowered = word.lower()
        if lowered in _STOPWORDS or lowered in seen:
            continue
        seen.append(lowered)
        if len(seen) >= MAX_TOKEN_LOOKUPS:
            break
    return seen


def _format_doc_match(best_match: dict) -> str:
    parts: list[str] = []
    heading = best_match.get("heading")
    if heading:
        parts.append(str(heading))
    syntax_blocks = best_match.get("syntax_blocks") or []
    if syntax_blocks:
        parts.append("Syntax: " + "; ".join(syntax_blocks))
    inputs_section = best_match.get("inputs_section")
    if inputs_section:
        parts.append(f"Inputs:\n{inputs_section}")
    outputs_section = best_match.get("outputs_section") or best_match.get("returns_section")
    if outputs_section:
        parts.append(f"Outputs:\n{outputs_section}")
    examples = best_match.get("examples")
    if examples:
        parts.append(f"Examples:\n{examples}")
    notes = best_match.get("notes")
    if notes:
        parts.append(f"Notes:\n{notes}")
    text = "\n\n".join(parts)
    return text[:MAX_GROUNDING_CHARS]


def _resolve_docs_root(docs_root_str: str | None) -> Path | None:
    if not docs_root_str:
        return None
    path = Path(docs_root_str).expanduser()
    return path if path.exists() and path.is_dir() else None


def _lookup_command(token: str, docs_root: Path) -> KnowledgeLookupResult | None:
    result = doc_lookup_mod.lookup(token, docs_root, max_results=1)
    if result["status"] == "found" and result["best_match"] and result["confidence"] >= MIN_DOC_CONFIDENCE:
        best_match = result["best_match"]
        return KnowledgeLookupResult(
            hit=True, source="official_docs", topic=token,
            content=_format_doc_match(best_match), citation=best_match.get("file_path"),
        )
    return None


def ground(question: str, *, docs_root_str: str | None, last_topic: str | None = None) -> KnowledgeLookupResult:
    """Pure with respect to conversation state -- reads only the caller-
    supplied `docs_root_str`/`last_topic`, never mutates anything. Zero I/O
    beyond the real, bounded documentation-file reads `command_doc_lookup.
    lookup(...)` itself already performs when `docs_root_str` points at a
    real, existing directory."""
    error_code = _extract_error_code(question)
    if error_code is not None:
        entry = catalog.lookup_error(error_code)
        if entry is not None:
            content = f"{entry.title}: {entry.generic_explanation}"
            if entry.known_triggers:
                content += " Known possible triggers: " + "; ".join(entry.known_triggers) + "."
            return KnowledgeLookupResult(
                hit=True, source="error_catalog", topic=error_code, content=content,
                citation=f"gauss_error_catalog.py ({error_code})",
            )
        return KnowledgeLookupResult(hit=False, source="uncataloged_error_code", topic=error_code, content="", citation=None)

    docs_root = _resolve_docs_root(docs_root_str)
    if docs_root is not None:
        for token in _candidate_tokens(question):
            result = _lookup_command(token, docs_root)
            if result is not None:
                return result
        if last_topic:
            result = _lookup_command(last_topic, docs_root)
            if result is not None:
                return result

    return KnowledgeLookupResult(hit=False, source="none", topic=None, content="", citation=None)


def _looks_like_execution_request(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in _EXECUTION_KEYWORDS)


def _looks_code_shaped(text: str) -> bool:
    return bool(_CODE_FENCE_RE.search(text)) or bool(_GAUSS_STATEMENT_RE.search(text))


@dataclass(frozen=True)
class AnswerResult:
    text: str
    grounded: bool
    #: One of "error_catalog", "official_docs", "uncataloged_error_code", "none".
    grounding_source: str
    grounding_topic: str | None
    provider_name: str
    provider_model: str | None
    provider_success: bool
    provider_error: str | None


class ConversationEngine:
    """Orchestration only -- see module docstring for the full boundary.
    Owns exactly one `ConversationState` and one injected `ModelProvider`;
    constructs no execution/repair/application object of any kind."""

    def __init__(self, *, provider: "provider_mod.ModelProvider", docs_root: str | None = None) -> None:
        self.provider = provider
        self.docs_root = docs_root
        self.state = ConversationState()

    def reset(self) -> None:
        self.state.reset()

    def ask(self, question: str) -> AnswerResult:
        question = question.strip()

        if _looks_like_execution_request(question):
            self.state.add("user", question)
            self.state.add("assistant", EXECUTION_BOUNDARY_MESSAGE)
            return AnswerResult(
                text=EXECUTION_BOUNDARY_MESSAGE, grounded=False, grounding_source="none", grounding_topic=None,
                provider_name="none", provider_model=None, provider_success=True, provider_error=None,
            )

        grounding = ground(question, docs_root_str=self.docs_root, last_topic=self.state.last_topic)

        messages = [provider_mod.ChatMessage(role="system", content=SYSTEM_PROMPT)]
        messages.extend(self.state.as_messages())
        if grounding.hit:
            messages.append(provider_mod.ChatMessage(role="system", content=f"GROUNDING_CONTEXT: {grounding.content}"))
        messages.append(provider_mod.ChatMessage(role="user", content=question))

        result = self.provider.complete(tuple(messages))

        if not result.success:
            answer_text = f"The configured chat provider ({result.provider_name}) could not answer: {result.error_message}"
            self.state.add("user", question)
            self.state.add("assistant", answer_text)
            return AnswerResult(
                text=answer_text, grounded=grounding.hit, grounding_source=grounding.source,
                grounding_topic=grounding.topic, provider_name=result.provider_name, provider_model=result.model,
                provider_success=False, provider_error=result.error_message,
            )

        text = result.text or ""
        if _looks_code_shaped(text):
            text += NOT_EXECUTED_FOOTER

        self.state.add("user", question)
        self.state.add("assistant", text)
        if grounding.hit and grounding.topic:
            self.state.last_topic = grounding.topic

        return AnswerResult(
            text=text, grounded=grounding.hit, grounding_source=grounding.source, grounding_topic=grounding.topic,
            provider_name=result.provider_name, provider_model=result.model, provider_success=True, provider_error=None,
        )
