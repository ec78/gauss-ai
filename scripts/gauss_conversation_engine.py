"""Conversational GAUSS Q&A engine (v0.70.0; conversational GAUSS code
generation and multi-source grounding added in v0.72.0).

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

v0.72.0 additions -- conversational GAUSS code generation:

- `classify_intent(...)` deterministically labels a question as one of
  `Intent.QA`, `Intent.CODE_GENERATION`, `Intent.EXECUTION_REQUEST`, or
  `Intent.REPAIR_OR_APPLICATION_REQUEST` before any grounding or provider
  call happens. `Intent.CLI_INVOCATION` also exists on the enum for
  documentation/testing purposes, but the actual interception of
  `gauss-ai <subcommand>`-shaped chat input happens upstream in
  `gauss_ai_chat.py`, before `ConversationEngine.ask(...)` is ever called --
  this module has no CLI-shape awareness of its own and does not need any,
  since that boundary already exists and is already deterministic.
- `ground_multi(...)` replaces the effectively single-token grounding
  `ground(...)` performed (that legacy function is UNCHANGED and still used
  directly by its own tests) with a bounded, deterministic multi-source
  retrieval: every candidate token from the question is looked up (not just
  the first one that hits), up to `MAX_GROUNDING_SOURCES` distinct sources,
  producing a `GroundingBundle` whose `status` (`GROUNDED` /
  `PARTIALLY_GROUNDED` / `UNGROUNDED`) is computed from the evidence actually
  found -- never trusted from, or reported by, the model itself.
- Conversational code generation reuses this same grounding, the same
  execution/repair boundary, the same bounded conversation state, and the
  same `ModelProvider` interface -- this is an extension of the existing
  architecture, not a second one. Generated code is always advisory: it is
  never executed, never written to a file, and never treated as an approved
  repair draft. `AnswerResult.generated_code`/`.executed`/
  `.methodologically_validated` make this explicit and machine-readable
  rather than implicit in prose; `.executed` and `.methodologically_validated`
  are always `False` in this version -- there is no code path anywhere in
  this module capable of setting either to `True`.
"""

from __future__ import annotations

import enum
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
#: prompt growth from a single large documentation page. Used by the legacy,
#: single-source `ground(...)`/`_format_doc_match(...)` default.
MAX_GROUNDING_CHARS = 4000

#: v0.72.0: when multiple sources are bundled into one prompt (see
#: `ground_multi(...)`), each source's own content is truncated more
#: tightly than the single-source default above -- bounded total prompt
#: growth as more sources are found, not just per-source growth.
MAX_GROUNDING_CHARS_BUNDLED = 1500

#: v0.72.0: the maximum number of distinct documentation/catalog sources
#: `ground_multi(...)` will include in one `GroundingBundle` -- conservative
#: multi-source grounding, not a vector-database/full-RAG rewrite. Kept
#: within the 3-5 range this milestone's own spec suggested.
MAX_GROUNDING_SOURCES = 4

#: v0.72.0: how many recently grounded topics `ConversationState` retains
#: (most-recent-first, deduplicated) for a follow-up question with no
#: independently detectable topic of its own -- a bounded generalization of
#: the single `last_topic` fallback `ground(...)` already used, so a
#: multi-turn code-generation conversation ("show me reshape", "now use
#: meanc on the result") can still resolve context across more than one
#: recently discussed command.
MAX_RECENT_TOPICS = 5

_ERROR_CODE_RE = re.compile(r"\bG\d{4}\b", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")

#: Common English/question words filtered out of token-lookup candidates --
#: a small, explicit, reviewable list, not a claim of real NLP.
_STOPWORDS = frozenset(
    {
        "what", "does", "how", "do", "the", "a", "an", "is", "are", "in", "for", "and", "that", "this",
        "difference", "between", "example", "show", "simple", "me", "give", "explain", "why", "would",
        "use", "using", "instead", "of", "to", "from", "with", "about", "can", "you", "your", "please",
        "gauss", "vs", "compare", "comparison", "concept", "mean", "meaning", "error", "code",
        # v0.72.0: "means" (plural, as in "column means") was previously
        # also stopworded, which caused a real live-Ollama-evaluation
        # finding (see the v0.72.0 evaluation category): a request to
        # "calculate the column means" silently reported full grounding on
        # `reshape` alone, giving no signal that `meanc` (the actual
        # relevant function) was never retrieved -- the real model then
        # invented a plausible-but-nonexistent `colmean` function instead,
        # confirmed as a real hallucination via real GAUSS execution
        # (`error G0025: Undefined symbol: 'colmean'`). Leaving "means"
        # unstopworded does not, by itself, teach the retrieval layer that
        # "means" refers to `meanc` -- there is no synonym map here, by
        # design -- but it does mean the word is now honestly surfaced as
        # an unmatched topic (`PARTIALLY_GROUNDED`) instead of being
        # silently dropped and reported as fully grounded on a
        # single, unrelated topic. "mean"/"meaning" remain stopworded --
        # they still serve v0.70.0's own "what does X mean" QA phrasing.
        # v0.72.0: code-generation-phrased questions introduce their own
        # common filler words that would otherwise become noisy, spurious
        # "unmatched topics" -- none of these are real GAUSS command names.
        "write", "generate", "create", "calculate", "compute", "column", "columns", "matrix", "matrices",
        "estimate", "estimation", "loop", "over", "some", "short", "long", "small", "single", "then",
        "after", "before", "into", "want", "need", "like", "script", "function", "syntax",
        # v0.72.0: common conversational connectives in multi-turn follow-ups
        # ("now show me X too") -- also not real GAUSS command names.
        "now", "as", "well", "too", "also", "next", "just", "again", "more", "another",
    }
)

#: A question asking the assistant to run/execute something it was just
#: shown or discussed -- checked BEFORE code-generation classification, so
#: an execution-imperative phrase is never misclassified as a request to
#: merely generate code.
_RUN_KEYWORDS = (
    "run this", "execute this", "run that", "execute that", "run it", "execute it",
    "run the example", "execute the example", "run the code", "execute the code",
    "run this script", "execute this script",
)

#: A repair/application-imperative phrase -- also checked before
#: code-generation classification. v0.71.0's live Ollama validation (Phase
#: 11) surfaced a real repair-intent phrasing ("fix my file ... and apply
#: the change") the original, narrower list did not catch; kept here as the
#: same kind of fixed, literal phrase, not a general repair-intent parser.
_REPAIR_KEYWORDS = (
    "apply this repair", "apply that repair", "fix my file", "fix this file", "fix that file",
    "repair my file", "repair this file", "repair that file", "apply the change", "apply this change",
    "apply that change", "apply the fix", "apply this fix", "apply that fix",
    # v0.72.0: live Ollama code-generation validation (Phase 19/Phase 27
    # release-readiness testing) surfaced a real gap the same way v0.71.0's
    # own Phase 11 did -- "Please apply that code to my myfile.gss file."
    # named "code" as the thing to apply, to a named file, and matched none
    # of the original "repair"/"change"/"fix" phrasing above. The model's
    # own answer was still safe (it has no file-write capability regardless
    # of routing), but the architectural interception itself should also
    # catch this phrasing family, exactly like the v0.71.0 precedent.
    "apply that code", "apply this code", "apply the code",
    "add that code to", "add this code to", "insert that code into", "insert this code into",
    "put that code in", "put this code in", "write that code to", "write this code to",
    "save that code to", "save this code to",
)

#: v0.72.0: a bounded, explicit phrase list for recognizing a request to
#: generate GAUSS code -- not a general intent classifier. Checked only
#: after `_RUN_KEYWORDS`/`_REPAIR_KEYWORDS` have already been ruled out, so
#: "run this code" and "fix this file" are never misclassified here.
_CODE_GENERATION_KEYWORDS = (
    "show me how", "show me an example", "show me a", "show me the code",
    "write gauss code", "write a gauss", "write an example", "write a function", "write a script",
    "write some code", "write code", "write me",
    "give me an example", "give me a code example", "give me sample code",
    "can you write", "can you give me an example", "can you give me code",
    "how would i", "example of", "example using", "code example",
)

_CODE_FENCE_RE = re.compile(r"```")
#: Recognizes a fenced code block, optionally labeled ```gauss, capturing
#: its body -- used by `extract_code_blocks(...)` (v0.72.0). Tolerant of a
#: generic (unlabeled) fence when the surrounding intent is code
#: generation; never interprets unfenced prose as code.
_CODE_BLOCK_RE = re.compile(r"```(?:[A-Za-z0-9_+-]*)?\s*\n(.*?)```", re.DOTALL)
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
    "You are the GAUSS AI conversational assistant, a specialized GAUSS coding assistant. You answer "
    "questions and generate code specifically about the GAUSS programming language and Aptech's GAUSS "
    "product: syntax, built-in procedures and functions, matrices, data handling, and error messages. "
    "Be concise by default and expand only when asked. When a message below is explicitly labeled as "
    "retrieved from official documentation or this repository's verified error catalog, treat it as "
    "authoritative and prefer it over your own general knowledge, and say that it came from that "
    "source. When no such labeled information is provided, answer from your own knowledge, but do not "
    "claim the answer is documentation-verified. If you include GAUSS code as an example, do not claim "
    "it has been run or tested -- it has not been executed in this conversation. You do not execute "
    "code, apply repairs, or modify files yourself; if asked to run or execute something, say so "
    "honestly rather than pretending to. If a question is entirely unrelated to GAUSS or this product, "
    "answer it briefly and honestly, then add one short sentence noting that you are a specialized "
    "GAUSS coding assistant -- never refuse a harmless off-topic question, and never add that reminder "
    "to an on-topic GAUSS question that simply lacks retrieval evidence."
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
    #: kept for backward compatibility (always equal to `recent_topics[0]`
    #: when non-empty); used directly by the legacy, single-source
    #: `ground(...)`.
    last_topic: str | None = None
    #: v0.72.0: most-recent-first, deduplicated, bounded to
    #: `MAX_RECENT_TOPICS` -- lets a multi-turn code-generation conversation
    #: ("show me reshape", "now use meanc on the result") resolve a
    #: follow-up against more than just the single most recent topic. Never
    #: persisted; cleared by `reset()` exactly like everything else here.
    recent_topics: list[str] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.turns.append(ChatTurn(role=role, content=content))
        if len(self.turns) > MAX_HISTORY_TURNS:
            del self.turns[: len(self.turns) - MAX_HISTORY_TURNS]

    def remember_topics(self, topics: tuple[str, ...]) -> None:
        """Moves each of `topics` to the front of `recent_topics` (most
        recent first), deduplicated, bounded to `MAX_RECENT_TOPICS`. Updates
        `last_topic` to match `recent_topics[0]` for backward compatibility."""
        for topic in topics:
            if topic in self.recent_topics:
                self.recent_topics.remove(topic)
            self.recent_topics.insert(0, topic)
        del self.recent_topics[MAX_RECENT_TOPICS:]
        if self.recent_topics:
            self.last_topic = self.recent_topics[0]

    def reset(self) -> None:
        self.turns.clear()
        self.last_topic = None
        self.recent_topics.clear()

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


def _format_doc_match(best_match: dict, *, max_chars: int = MAX_GROUNDING_CHARS) -> str:
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
    return text[:max_chars]


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


class Intent(str, enum.Enum):
    """v0.72.0: a deterministic label for what kind of request a question
    is, computed BEFORE any grounding or provider call. Execution, repair,
    and CLI-invocation classification are all safety-relevant boundaries and
    are deliberately kept as fixed, explicit phrase matching -- never
    model-based routing -- exactly continuing `v0.70.0`/`v0.71.0`'s own
    discipline. `CLI_INVOCATION` exists on this enum for completeness and
    testability, but `ConversationEngine`/`classify_intent(...)` never
    produce it: that interception happens upstream, in `gauss_ai_chat.py`'s
    own REPL loop via `gauss_ai_config.looks_like_cli_invocation(...)`,
    before a CLI-shaped line is ever passed to `ask(...)` at all."""

    QA = "qa"
    CODE_GENERATION = "code_generation"
    EXECUTION_REQUEST = "execution_request"
    REPAIR_OR_APPLICATION_REQUEST = "repair_or_application_request"
    CLI_INVOCATION = "cli_invocation"


def classify_intent(question: str) -> Intent:
    """Deterministic, bounded phrase matching -- not a language model, not a
    parser. Order matters: execution and repair/application phrasing are
    checked first, so a safety-boundary phrase is never misclassified as a
    mere code-generation request just because it also contains words like
    "code" or "this"."""
    lowered = question.lower()
    if any(keyword in lowered for keyword in _RUN_KEYWORDS):
        return Intent.EXECUTION_REQUEST
    if any(keyword in lowered for keyword in _REPAIR_KEYWORDS):
        return Intent.REPAIR_OR_APPLICATION_REQUEST
    if any(keyword in lowered for keyword in _CODE_GENERATION_KEYWORDS):
        return Intent.CODE_GENERATION
    return Intent.QA


def _looks_code_shaped(text: str) -> bool:
    return bool(_CODE_FENCE_RE.search(text)) or bool(_GAUSS_STATEMENT_RE.search(text))


def extract_code_blocks(text: str) -> tuple[str, ...]:
    """Conservative, structural extraction of fenced code blocks (```` ``` ````
    or ```` ```gauss ````) from a model's own response text -- never
    interprets unfenced prose as code, never executes anything, never writes
    anything to disk. Purely advisory metadata for `AnswerResult.
    generated_code`; multiple blocks are returned in the order they appear,
    each with trailing whitespace stripped, the original response text
    itself is left untouched by this function."""
    return tuple(match.group(1).rstrip() for match in _CODE_BLOCK_RE.finditer(text))


class GroundingStatus(str, enum.Enum):
    """v0.72.0: a categorical, deterministically COMPUTED grounding status
    -- never a numeric confidence score, and never self-reported by the
    model. `GroundingBundle.status` derives this purely from whether any
    real evidence was found and whether every referenced topic was covered,
    exactly mirroring how `KnowledgeLookupResult`/`ground(...)` already
    never trusted the model for whether a v0.70.0 answer was grounded."""

    GROUNDED = "grounded"
    PARTIALLY_GROUNDED = "partially_grounded"
    UNGROUNDED = "ungrounded"


@dataclass(frozen=True)
class GroundingSource:
    """One piece of real, structured evidence -- either a verified error
    catalog entry or a real local documentation match. Never fabricated;
    every field traces back to `gauss_error_catalog.py` or
    `command_doc_lookup.py`'s own real output."""

    #: "error_catalog" or "official_docs" -- the same vocabulary
    #: `KnowledgeLookupResult.source` already used.
    source: str
    topic: str
    content: str
    citation: str | None


@dataclass(frozen=True)
class GroundingBundle:
    """v0.72.0: the multi-source result of `ground_multi(...)`. Immutable,
    bounded (`len(sources) <= MAX_GROUNDING_SOURCES`), and never claims a
    topic was covered unless a `GroundingSource` for it is actually present
    in `sources`. `status` is a derived property, not a stored field, so it
    can never be constructed in an internally inconsistent state (e.g.
    `GROUNDED` with zero sources, or `UNGROUNDED` with sources present)."""

    sources: tuple[GroundingSource, ...]
    #: Topics (command names or error codes) that were referenced and
    #: successfully grounded -- `len(matched_topics) == len(sources)`.
    matched_topics: tuple[str, ...]
    #: Topics that looked like they might be specific GAUSS references but
    #: produced no confident match -- never silently dropped, always
    #: surfaced so an answer can honestly say what could not be grounded.
    unmatched_topics: tuple[str, ...]

    @property
    def status(self) -> GroundingStatus:
        if not self.sources:
            return GroundingStatus.UNGROUNDED
        if self.unmatched_topics:
            return GroundingStatus.PARTIALLY_GROUNDED
        return GroundingStatus.GROUNDED

    @property
    def hit(self) -> bool:
        return bool(self.sources)


def ground_multi(
    question: str, *, docs_root_str: str | None, recent_topics: tuple[str, ...] = ()
) -> GroundingBundle:
    """v0.72.0 multi-source grounding. Conservative and deterministic:
    every distinct candidate token from `question` is looked up (not just
    the first one that hits, unlike the legacy `ground(...)`), bounded to
    `MAX_GROUNDING_SOURCES` sources total. An error code, if present, is
    checked first and always included (as a source if cataloged, as an
    unmatched topic if not) -- exactly mirroring `ground(...)`'s own
    error-code priority. If the question itself produces zero sources of
    its own, `recent_topics` (most-recent-first) is tried, in order, as a
    fallback for a pronoun-style follow-up with no topic of its own -- a
    bounded generalization of `ground(...)`'s single `last_topic` fallback.
    Never fabricates a source, never fuzzy-matches below
    `MIN_DOC_CONFIDENCE`, never performs unbounded work."""
    sources: list[GroundingSource] = []
    matched_topics: list[str] = []
    unmatched_topics: list[str] = []
    seen_topics: set[str] = set()

    def _add_source(source: GroundingSource) -> None:
        if source.topic in seen_topics:
            return
        seen_topics.add(source.topic)
        sources.append(source)
        matched_topics.append(source.topic)

    def _add_unmatched(topic: str) -> None:
        if topic not in unmatched_topics:
            unmatched_topics.append(topic)

    error_code = _extract_error_code(question)
    if error_code is not None:
        entry = catalog.lookup_error(error_code)
        if entry is not None:
            content = f"{entry.title}: {entry.generic_explanation}"
            if entry.known_triggers:
                content += " Known possible triggers: " + "; ".join(entry.known_triggers) + "."
            _add_source(GroundingSource(
                source="error_catalog", topic=error_code, content=content,
                citation=f"gauss_error_catalog.py ({error_code})",
            ))
        else:
            _add_unmatched(error_code)

    docs_root = _resolve_docs_root(docs_root_str)
    if docs_root is not None:
        for token in _candidate_tokens(question):
            if len(sources) >= MAX_GROUNDING_SOURCES:
                break
            if error_code is not None and token == error_code.lower():
                continue  # already handled above -- avoid a redundant, doomed doc lookup
            result = doc_lookup_mod.lookup(token, docs_root, max_results=1)
            if result["status"] == "found" and result["best_match"] and result["confidence"] >= MIN_DOC_CONFIDENCE:
                best_match = result["best_match"]
                _add_source(GroundingSource(
                    source="official_docs", topic=token,
                    content=_format_doc_match(best_match, max_chars=MAX_GROUNDING_CHARS_BUNDLED),
                    citation=best_match.get("file_path"),
                ))
            else:
                _add_unmatched(token)

        if not sources:
            for topic in recent_topics:
                result = _lookup_command(topic, docs_root)
                if result is not None:
                    _add_source(GroundingSource(
                        source=result.source, topic=result.topic, content=result.content, citation=result.citation,
                    ))
                    break

    return GroundingBundle(
        sources=tuple(sources), matched_topics=tuple(matched_topics), unmatched_topics=tuple(unmatched_topics),
    )


def _format_grounding_context(bundle: GroundingBundle) -> str:
    """Combines every source in `bundle` into ONE system-message body,
    deliberately kept under a single `GROUNDING_CONTEXT:` prefix (rather
    than one message per source) so `FakeModelProvider`'s existing exact-
    prefix detection keeps working unchanged for both the single- and
    multi-source case. Each source is clearly labeled with its own kind and
    topic so a real model (and a human reading a transcript) can tell which
    claims are backed by which evidence."""
    parts = []
    for src in bundle.sources:
        label = "official docs" if src.source == "official_docs" else "verified error catalog"
        parts.append(f"[{label}: {src.topic}]\n{src.content}")
    return "\n\n".join(parts)


CODE_GENERATION_SYSTEM_PROMPT_ADDENDUM = (
    "The user is asking you to generate GAUSS code. Follow these rules strictly: "
    "Prefer syntax and function usage explicitly supported by any labeled documentation evidence "
    "provided below. Never invent a GAUSS function, procedure, or command name -- if you are not "
    "confident a function genuinely exists in GAUSS, say so explicitly instead of guessing at a "
    "plausible-sounding name. If the provided evidence does not cover part of what was requested, "
    "generate only the supported part and clearly state what could not be grounded, rather than "
    "fabricating the rest. Prefer minimal, correct code over clever or elaborate code. Do not claim "
    "the code has been executed, tested, or verified -- it has not. If asked what the code's output "
    "would be, say explicitly that this is a prediction, not observed execution evidence (for example: "
    "'Expected output, not execution evidence:'), and say so plainly if you cannot confidently predict "
    "it at all. Documented syntax correctness does not make a statistical or methodological choice "
    "correct -- if the user's request implies a specific method (e.g. a particular regression "
    "approach), you may generate the code they asked for, but do not claim that choice is the correct "
    "one for their data or question. Ask a clarifying question only when missing information would "
    "materially change the generated syntax, dimensions, data structure, or method -- do not ask "
    "unnecessary or trivial clarifying questions."
)

#: Prefix for the system message carrying `CODE_GENERATION_SYSTEM_PROMPT_ADDENDUM`,
#: added to the provider prompt only for `Intent.CODE_GENERATION` turns.
#: `FakeModelProvider` also recognizes this prefix (see `gauss_chat_provider.
#: py`) so its deterministic template can produce a fenced code block for
#: code-generation requests, fully testable without a real model.
CODE_GENERATION_MARKER_PREFIX = "CODE_GENERATION_MODE:"


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
    #: v0.72.0 additions -- all optional/defaulted so every pre-v0.72.0
    #: construction of this type (there are none outside this module, but
    #: keeping the contract explicit) remains valid.
    intent: str = Intent.QA.value
    #: One of `GroundingStatus`'s values, or `None` for a fixed
    #: execution/repair-boundary redirect, where grounding is not applicable.
    grounding_status: str | None = None
    grounding_sources: tuple[GroundingSource, ...] = ()
    #: Topics referenced (a command name or error code) that could not be
    #: grounded -- always empty when `grounding_status` is `GROUNDED` or `None`.
    unsupported_topics: tuple[str, ...] = ()
    #: Fenced GAUSS code blocks extracted from the answer text, in order.
    #: Always empty unless `intent == Intent.CODE_GENERATION.value`.
    generated_code: tuple[str, ...] = ()
    #: Always `False` in this version -- no code path in this module can
    #: execute anything, so this can never legitimately become `True` here.
    executed: bool = False
    #: Always `False` in this version, for the same reason: nothing in this
    #: module verifies GAUSS output, GAUSS execution success, or
    #: methodological/statistical appropriateness.
    methodologically_validated: bool = False


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
        intent = classify_intent(question)

        if intent in (Intent.EXECUTION_REQUEST, Intent.REPAIR_OR_APPLICATION_REQUEST):
            self.state.add("user", question)
            self.state.add("assistant", EXECUTION_BOUNDARY_MESSAGE)
            return AnswerResult(
                text=EXECUTION_BOUNDARY_MESSAGE, grounded=False, grounding_source="none", grounding_topic=None,
                provider_name="none", provider_model=None, provider_success=True, provider_error=None,
                intent=intent.value, grounding_status=None,
            )

        bundle = ground_multi(question, docs_root_str=self.docs_root, recent_topics=tuple(self.state.recent_topics))
        error_code = _extract_error_code(question)
        if not bundle.sources and error_code is not None and error_code in bundle.unmatched_topics:
            legacy_source, legacy_topic = "uncataloged_error_code", error_code
        elif bundle.sources:
            legacy_source, legacy_topic = bundle.sources[0].source, bundle.sources[0].topic
        else:
            legacy_source, legacy_topic = "none", None

        messages = [provider_mod.ChatMessage(role="system", content=SYSTEM_PROMPT)]
        messages.extend(self.state.as_messages())
        if intent == Intent.CODE_GENERATION:
            messages.append(provider_mod.ChatMessage(
                role="system", content=f"{CODE_GENERATION_MARKER_PREFIX} {CODE_GENERATION_SYSTEM_PROMPT_ADDENDUM}",
            ))
        if bundle.sources:
            messages.append(provider_mod.ChatMessage(
                role="system", content=f"GROUNDING_CONTEXT: {_format_grounding_context(bundle)}",
            ))
        messages.append(provider_mod.ChatMessage(role="user", content=question))

        result = self.provider.complete(tuple(messages))

        if not result.success:
            answer_text = f"The configured chat provider ({result.provider_name}) could not answer: {result.error_message}"
            self.state.add("user", question)
            self.state.add("assistant", answer_text)
            return AnswerResult(
                text=answer_text, grounded=bundle.hit, grounding_source=legacy_source,
                grounding_topic=legacy_topic, provider_name=result.provider_name, provider_model=result.model,
                provider_success=False, provider_error=result.error_message,
                intent=intent.value, grounding_status=bundle.status.value,
                grounding_sources=bundle.sources, unsupported_topics=bundle.unmatched_topics,
            )

        text = result.text or ""
        if _looks_code_shaped(text):
            text += NOT_EXECUTED_FOOTER
        generated_code = extract_code_blocks(text) if intent == Intent.CODE_GENERATION else ()

        self.state.add("user", question)
        self.state.add("assistant", text)
        if bundle.matched_topics:
            self.state.remember_topics(bundle.matched_topics)

        return AnswerResult(
            text=text, grounded=bundle.hit, grounding_source=legacy_source, grounding_topic=legacy_topic,
            provider_name=result.provider_name, provider_model=result.model, provider_success=True, provider_error=None,
            intent=intent.value, grounding_status=bundle.status.value,
            grounding_sources=bundle.sources, unsupported_topics=bundle.unmatched_topics,
            generated_code=generated_code, executed=False, methodologically_validated=False,
        )
