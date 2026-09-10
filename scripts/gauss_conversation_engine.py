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

v0.73.0 additions -- grounding-gated generation and function resolution:

- `resolve_concepts(...)` maps a natural-language phrase (e.g. "column
  means") to a real, documented GAUSS symbol (e.g. `meanc`) BEFORE the
  provider is ever called, using a small, explicit, doc-verified
  `_CONCEPT_ALIAS_INDEX` -- never a language model, never a synonym
  guessed from memory. Every entry's mapping was verified against this
  session's own real local GAUSS documentation checkout before being
  encoded (see each entry's `evidence` string), and every resolution is
  re-verified again at call time against the CALLER's own configured
  `docs_root` via `command_doc_lookup.lookup(...)` -- a hardcoded alias is
  a candidate to check, never treated as authoritative by itself. This is
  the direct fix for the exact v0.72.0 root cause: "calculate the column
  means" never even attempted a `meanc` lookup, so the model was left to
  invent `colmean` from its own unreliable general knowledge.
- `compute_generation_gate(...)` turns `GroundingBundle`'s status into a
  deterministic, provider-independent decision -- `GenerationPolicy.FULL`
  / `SUPPORTED_ONLY` / `CLARIFY` / `BLOCK` -- computed entirely from real
  retrieval evidence, exactly like `GroundingStatus` itself. The provider
  is not given a chance to override this: for `BLOCK` and `CLARIFY`, the
  provider is never called for code generation at all.
- `check_generated_symbols(...)` is a conservative, best-effort POST-
  generation check: it extracts call-shaped identifiers from generated
  code and flags any that are neither grounded/resolved symbols, a small
  explicitly-verified set of core GAUSS language constructs/common
  builtins, nor plausibly user-defined (assigned to, or declared via
  `proc`, in the same code). This is not a compiler and does not claim
  perfect static analysis -- it exists specifically to catch a future
  `colmean(...)`-shaped hallucination even if the model ignores its own
  prompt instructions, which `v0.72.0`'s own live evaluation proved can
  happen.

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
        # v0.73.0: common filler verbs in natural-language concept phrasing
        # ("get the mean of every column") -- not real GAUSS command names.
        "get", "getting", "find", "finding",
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
    "code" or "this". v0.73.0: a phrase that matches `_CONCEPT_ALIAS_INDEX`
    (e.g. "column means", "panel regression") is ALSO treated as a
    code-generation signal -- naming a specific GAUSS computation this
    concretely is itself evidence the user wants that computation done in
    GAUSS, even without an explicit "write code"/"show me" prefix. This is
    what makes this milestone's own canonical example, "Calculate the
    column means.", classify correctly with no other trigger phrase."""
    lowered = question.lower()
    if any(keyword in lowered for keyword in _RUN_KEYWORDS):
        return Intent.EXECUTION_REQUEST
    if any(keyword in lowered for keyword in _REPAIR_KEYWORDS):
        return Intent.REPAIR_OR_APPLICATION_REQUEST
    if any(keyword in lowered for keyword in _CODE_GENERATION_KEYWORDS):
        return Intent.CODE_GENERATION
    if any(phrase in lowered for entry in _CONCEPT_ALIAS_INDEX for phrase in entry.phrases):
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
    #: v0.73.0: where this source's TOPIC came from -- "literal" (the user
    #: named it directly), "recent_topic" (carried over from an earlier
    #: turn), or "resolved_concept" (found via `resolve_concepts(...)`'s
    #: natural-language alias index). Provenance only -- never affects
    #: whether the source counts as real grounding, which always requires
    #: the same real `command_doc_lookup`/error-catalog verification
    #: regardless of origin.
    origin: str = "literal"


class ResolutionStatus(str, enum.Enum):
    """v0.73.0: the outcome of attempting to resolve one phrase/token to a
    real, documented GAUSS symbol. Never a numeric confidence score --
    categorical, and always computed from real retrieval evidence."""

    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"


class MatchType(str, enum.Enum):
    """v0.73.0: how a resolution was found. `EXACT_SYMBOL` -- the user's
    own literal token matched a real documented symbol directly (the same
    mechanism `v0.72.0`'s `ground_multi(...)` already used).
    `ALIAS_OR_DESCRIPTION` -- a natural-language phrase matched a curated,
    doc-verified entry in `_CONCEPT_ALIAS_INDEX`, and the resulting symbol
    was independently re-verified against the caller's own `docs_root`.
    Neither match type is ever produced without a real, successful
    `command_doc_lookup.lookup(...)` (or error-catalog) call backing it."""

    EXACT_SYMBOL = "exact_symbol"
    ALIAS_OR_DESCRIPTION = "alias_or_description"


@dataclass(frozen=True)
class FunctionResolution:
    """v0.73.0: the result of attempting to resolve one phrase/token to a
    documented GAUSS symbol. `resolved_symbol`/`match_type`/`source`/
    `citation` are populated only when `status == RESOLVED`; `candidates`
    is populated only when `status == AMBIGUOUS`. Never fabricates a
    symbol -- an `UNRESOLVED` result means exactly that: no real evidence
    was found, not a low-confidence guess presented as a real answer."""

    user_phrase: str
    status: str
    resolved_symbol: str | None = None
    match_type: str | None = None
    #: "official_docs" or "error_catalog" -- the same vocabulary
    #: `GroundingSource.source` already uses. `None` when not RESOLVED.
    source: str | None = None
    citation: str | None = None
    #: A short, human-readable justification -- for `ALIAS_OR_DESCRIPTION`,
    #: quotes the curated index entry's own doc-verified justification and
    #: the real citation found at call time; for `AMBIGUOUS`, names why.
    evidence: str = ""
    #: Populated only when `status == AMBIGUOUS`: the plausible symbol
    #: names `command_doc_lookup.lookup(...)` itself could not confidently
    #: distinguish between.
    candidates: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConceptAliasEntry:
    """One curated, doc-verified natural-language-to-symbol mapping. See
    `_CONCEPT_ALIAS_INDEX`'s own module-level comment for the verification
    discipline every entry here was held to."""

    phrases: tuple[str, ...]
    symbol: str
    citation: str
    evidence: str


#: v0.73.0: a small, explicit, human-curated concept/alias index -- NOT a
#: vector database, NOT a language model, NOT a large synonym dictionary
#: assembled from memory. Every entry below was verified, in this
#: milestone's own development session, by directly reading the cited
#: real local GAUSS documentation file's own Purpose/Format section before
#: being encoded here -- the `evidence` string quotes that real content so
#: a future reviewer can check the claim without re-deriving it. Each
#: entry's `symbol` is STILL independently re-verified against the
#: CALLER's own configured `docs_root` at call time (see
#: `resolve_concepts(...)`) -- this index only ever proposes a candidate
#: to check, it is never trusted as authoritative by itself, and if a
#: user's own documentation checkout does not actually contain the symbol,
#: the alias produces no resolution at all rather than a fabricated one.
_CONCEPT_ALIAS_INDEX: tuple[ConceptAliasEntry, ...] = (
    ConceptAliasEntry(
        phrases=(
            "column means", "column mean", "average columns", "average each column",
            "column averages", "mean of every column", "mean of each column", "averages of each column",
        ),
        symbol="meanc",
        citation="meanc.rst",
        evidence='meanc.rst Purpose: "Computes the mean of every column of a matrix."',
    ),
    ConceptAliasEntry(
        phrases=(
            "column standard deviation", "standard deviation of each column", "column stdev",
            "std of each column", "standard deviation of every column",
        ),
        symbol="stdc",
        citation="stdc.rst",
        evidence='stdc.rst Purpose: "Computes the sample standard deviation of the elements in each column of a matrix."',
    ),
    ConceptAliasEntry(
        phrases=(
            "turn a matrix into a vector", "turn this matrix into a vector", "flatten a matrix",
            "flatten this matrix", "convert a matrix to a vector", "convert this matrix to a vector",
            "stack columns into a vector", "vectorize a matrix", "vectorize this matrix",
        ),
        symbol="vec",
        citation="vecvecr.rst",
        evidence='vecvecr.rst Purpose: "Creates a column vector by appending the columns/rows of a matrix to each other."',
    ),
    ConceptAliasEntry(
        phrases=("invert a matrix", "invert this matrix", "matrix inverse", "inverse of a matrix", "matrix inversion"),
        symbol="inv",
        citation="invinvpd.rst",
        evidence='invinvpd.rst Purpose: "inv returns the inverse of an invertible matrix."',
    ),
    ConceptAliasEntry(
        phrases=(
            "panel regression", "panel data regression", "time series cross section regression",
            "time series cross-section regression", "pooled time series cross section regression",
            "panel data model",
        ),
        symbol="tscsfit",
        citation="tsmt/tscsfit.rst",
        evidence='tsmt/tscsfit.rst Purpose: "Estimates the parameters of the pooled time-series cross-section regression model."',
    ),
)

#: v0.73.0: bounds how many `FunctionResolution` entries `resolve_concepts(...)`
#: returns -- same conservative-bound discipline as `MAX_GROUNDING_SOURCES`.
MAX_RESOLUTIONS = 4


def _iter_alias_matches(lowered_question: str):
    for entry in _CONCEPT_ALIAS_INDEX:
        for phrase in entry.phrases:
            if phrase in lowered_question:
                yield phrase, entry
                break  # one match per entry is enough; move to the next entry


def resolve_concepts(question: str, *, docs_root_str: str | None) -> tuple[FunctionResolution, ...]:
    """v0.73.0: resolves both literal command-name tokens (`MatchType.
    EXACT_SYMBOL`, the same retrieval `v0.72.0`'s `ground_multi(...)`
    already performed per-token) and curated natural-language phrases
    (`MatchType.ALIAS_OR_DESCRIPTION`, via `_CONCEPT_ALIAS_INDEX`) to real,
    doc-verified GAUSS symbols. Every resolution -- of either kind -- is
    backed by a real `command_doc_lookup.lookup(...)` call against the
    caller's OWN `docs_root`; nothing here is ever fabricated or trusted
    from a hardcoded table alone. Returns one entry per examined candidate
    token (`RESOLVED`/`AMBIGUOUS`/`UNRESOLVED` -- never silently omitted,
    so an unresolved phrase is honestly reported, not just absent), plus
    one entry per successfully-verified alias match; truncated to
    `MAX_RESOLUTIONS` only if that combined total is exceeded. Returns an
    empty tuple if `docs_root_str` does not resolve to a real, existing
    directory -- exactly like `ground_multi(...)`'s own behavior."""
    docs_root = _resolve_docs_root(docs_root_str)
    if docs_root is None:
        return ()

    resolutions: list[FunctionResolution] = []
    seen_symbols: set[str] = set()
    lowered = question.lower()
    error_code = _extract_error_code(question)

    for token in _candidate_tokens(question):
        if error_code is not None and token == error_code.lower():
            continue  # handled by the error catalog, not documentation lookup
        result = doc_lookup_mod.lookup(token, docs_root, max_results=3)
        if result["status"] == "found" and result["best_match"] and result["confidence"] >= MIN_DOC_CONFIDENCE:
            seen_symbols.add(token)
            best_match = result["best_match"]
            resolutions.append(FunctionResolution(
                user_phrase=token, status=ResolutionStatus.RESOLVED.value, resolved_symbol=token,
                match_type=MatchType.EXACT_SYMBOL.value, source="official_docs",
                citation=best_match.get("file_path"),
                evidence=f"literal token {token!r} matched {best_match.get('file_path')} directly",
            ))
        elif result["status"] == "ambiguous" and result["confidence"] >= MIN_DOC_CONFIDENCE and result["matches"]:
            candidates = tuple(
                dict.fromkeys(Path(m["file_path"]).stem for m in result["matches"] if m.get("file_path"))
            )
            if candidates:
                resolutions.append(FunctionResolution(
                    user_phrase=token, status=ResolutionStatus.AMBIGUOUS.value,
                    evidence=f"{token!r} matched more than one similarly-scored documentation page",
                    candidates=candidates,
                ))
        else:
            resolutions.append(FunctionResolution(
                user_phrase=token, status=ResolutionStatus.UNRESOLVED.value,
                evidence=f"no confident documentation match for {token!r}",
            ))

    for phrase, entry in _iter_alias_matches(lowered):
        if entry.symbol in seen_symbols:
            continue  # already resolved directly -- the alias would be redundant
        result = doc_lookup_mod.lookup(entry.symbol, docs_root, max_results=1)
        if result["status"] == "found" and result["best_match"] and result["confidence"] >= MIN_DOC_CONFIDENCE:
            seen_symbols.add(entry.symbol)
            best_match = result["best_match"]
            resolutions.append(FunctionResolution(
                user_phrase=phrase, status=ResolutionStatus.RESOLVED.value, resolved_symbol=entry.symbol,
                match_type=MatchType.ALIAS_OR_DESCRIPTION.value, source="official_docs",
                citation=best_match.get("file_path"),
                evidence=f"{entry.evidence} (re-verified against the configured docs-root: {best_match.get('file_path')})",
            ))
        # If verification fails against THIS caller's own docs_root, the
        # alias produces no resolution at all -- never a fabricated one.

    # Once a phrase like "column means" has successfully resolved via the
    # alias index, its own literal words (e.g. "means") should not ALSO be
    # reported as a separate, confusing UNRESOLVED token -- the concept it
    # expressed was resolved, even though the bare word is not itself a
    # GAUSS symbol. This does not hide anything: the ALIAS_OR_DESCRIPTION
    # resolution itself still names the full phrase and its real citation.
    resolved_alias_words: set[str] = set()
    for resolution in resolutions:
        if resolution.status == ResolutionStatus.RESOLVED.value and resolution.match_type == MatchType.ALIAS_OR_DESCRIPTION.value:
            resolved_alias_words.update(resolution.user_phrase.split())
    resolutions = [
        r for r in resolutions
        if not (r.status == ResolutionStatus.UNRESOLVED.value and r.user_phrase in resolved_alias_words)
    ]

    if len(resolutions) > MAX_RESOLUTIONS:
        return tuple(resolutions[:MAX_RESOLUTIONS])
    return tuple(resolutions)


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
    #: v0.73.0: phrases/tokens `resolve_concepts(...)` found genuinely
    #: ambiguous (multiple similarly-scored documented candidates) --
    #: tracked separately from `unmatched_topics` because "ambiguous" is a
    #: materially different situation from "not found at all" and drives a
    #: different generation-gate policy (`CLARIFY`, not `BLOCK`).
    ambiguous_topics: tuple[str, ...] = ()
    #: v0.73.0: every `FunctionResolution` this bundle was built from --
    #: full provenance for whichever topics ended up in `sources`,
    #: `unmatched_topics`, or `ambiguous_topics`.
    resolutions: tuple[FunctionResolution, ...] = ()

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
    """v0.72.0 multi-source grounding, extended in v0.73.0 to also resolve
    natural-language descriptions (e.g. "column means") to real documented
    symbols (e.g. `meanc`), not just literal command-name tokens -- see
    `resolve_concepts(...)`, which this function delegates ALL token/phrase
    resolution to (both the literal `EXACT_SYMBOL` matching `v0.72.0`
    performed inline here, and the new `ALIAS_OR_DESCRIPTION` matching), so
    there is exactly one place that logic lives. An error code, if present,
    is checked first and always included (as a source if cataloged, as an
    unmatched topic if not) -- exactly mirroring `ground(...)`'s own
    error-code priority, and is never re-examined by `resolve_concepts(...)`
    itself. Bounded to `MAX_GROUNDING_SOURCES` sources total. If the
    question itself produces zero sources of its own, `recent_topics`
    (most-recent-first) is tried, in order, as a fallback for a pronoun-
    style follow-up with no topic of its own -- a bounded generalization of
    `ground(...)`'s single `last_topic` fallback. Never fabricates a
    source, never fuzzy-matches below `MIN_DOC_CONFIDENCE`, never performs
    unbounded work."""
    sources: list[GroundingSource] = []
    matched_topics: list[str] = []
    unmatched_topics: list[str] = []
    ambiguous_topics: list[str] = []
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

    def _add_ambiguous(topic: str) -> None:
        if topic not in ambiguous_topics:
            ambiguous_topics.append(topic)

    error_code = _extract_error_code(question)
    if error_code is not None:
        entry = catalog.lookup_error(error_code)
        if entry is not None:
            content = f"{entry.title}: {entry.generic_explanation}"
            if entry.known_triggers:
                content += " Known possible triggers: " + "; ".join(entry.known_triggers) + "."
            _add_source(GroundingSource(
                source="error_catalog", topic=error_code, content=content,
                citation=f"gauss_error_catalog.py ({error_code})", origin="literal",
            ))
        else:
            _add_unmatched(error_code)

    docs_root = _resolve_docs_root(docs_root_str)
    resolutions = resolve_concepts(question, docs_root_str=docs_root_str) if docs_root is not None else ()

    for resolution in resolutions:
        if resolution.status == ResolutionStatus.RESOLVED.value:
            if len(sources) >= MAX_GROUNDING_SOURCES:
                continue  # still recorded in `resolutions` for provenance, just not promoted to a source
            # Re-fetches the full match rather than threading it through
            # `FunctionResolution` (which only carries a citation/evidence
            # summary) -- a second, real `command_doc_lookup.lookup(...)`
            # call, not a cached or trusted-from-memory value. A deliberate
            # simplicity-over-performance tradeoff: this module never
            # caches documentation content, and a handful of extra local
            # file reads per turn is a fine price for that discipline.
            result = doc_lookup_mod.lookup(resolution.resolved_symbol, docs_root, max_results=1)
            if result["status"] == "found" and result["best_match"]:
                best_match = result["best_match"]
                origin = "literal" if resolution.match_type == MatchType.EXACT_SYMBOL.value else "resolved_concept"
                _add_source(GroundingSource(
                    source=resolution.source, topic=resolution.resolved_symbol,
                    content=_format_doc_match(best_match, max_chars=MAX_GROUNDING_CHARS_BUNDLED),
                    citation=resolution.citation, origin=origin,
                ))
        elif resolution.status == ResolutionStatus.AMBIGUOUS.value:
            _add_ambiguous(resolution.user_phrase)
        else:
            _add_unmatched(resolution.user_phrase)

    if docs_root is not None and not sources:
        for topic in recent_topics:
            result = _lookup_command(topic, docs_root)
            if result is not None:
                _add_source(GroundingSource(
                    source=result.source, topic=result.topic, content=result.content, citation=result.citation,
                    origin="recent_topic",
                ))
                break

    return GroundingBundle(
        sources=tuple(sources), matched_topics=tuple(matched_topics), unmatched_topics=tuple(unmatched_topics),
        ambiguous_topics=tuple(ambiguous_topics), resolutions=resolutions,
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


class GenerationPolicy(str, enum.Enum):
    """v0.73.0: a deterministic, provider-independent decision about
    whether -- and how much -- GAUSS-specific code generation is
    permitted for a `CODE_GENERATION`-intent turn. Computed entirely from
    `GroundingBundle`'s own real retrieval evidence by
    `compute_generation_gate(...)` BEFORE the provider is ever called; the
    provider is never given a chance to override it."""

    #: Every referenced topic is grounded -- generate normally.
    FULL = "full"
    #: Some referenced topics are grounded, some are not -- generate only
    #: the supported portion; the unsupported portion is never fabricated.
    SUPPORTED_ONLY = "supported_only"
    #: A phrase/token resolved to more than one plausible documented
    #: symbol -- ask which one, rather than guessing or generating
    #: speculative code for either.
    CLARIFY = "clarify"
    #: No authoritative evidence exists for this request at all -- do not
    #: call the provider for GAUSS code generation; explain honestly.
    BLOCK = "block"


@dataclass(frozen=True)
class GenerationGateResult:
    """v0.73.0: the gate's own decision record -- deliberately explicit
    and inspectable rather than buried in `ConversationEngine.ask(...)`'s
    own conditionals (see module docstring)."""

    policy: str
    #: True only for `FULL`/`SUPPORTED_ONLY` -- the two policies that
    #: permit calling the provider for GAUSS code generation at all.
    allowed: bool
    grounding_status: str
    supported_topics: tuple[str, ...]
    unsupported_topics: tuple[str, ...]
    ambiguous_topics: tuple[str, ...]
    reason: str


def compute_generation_gate(bundle: GroundingBundle) -> GenerationGateResult:
    """Deterministic: reads only `bundle`'s own already-computed evidence,
    calls nothing, makes no network/file access of its own. `CLARIFY`
    takes priority over `SUPPORTED_ONLY`/`BLOCK` -- genuine ambiguity about
    which documented symbol was meant is a materially different situation
    from "some/no topics were found" and should not be silently folded
    into either."""
    if bundle.ambiguous_topics:
        return GenerationGateResult(
            policy=GenerationPolicy.CLARIFY.value, allowed=False, grounding_status=bundle.status.value,
            supported_topics=bundle.matched_topics, unsupported_topics=bundle.unmatched_topics,
            ambiguous_topics=bundle.ambiguous_topics,
            reason="the request could refer to more than one documented GAUSS symbol",
        )
    if bundle.status == GroundingStatus.GROUNDED:
        policy, reason = GenerationPolicy.FULL, (
            "every referenced GAUSS-specific topic was found in official documentation or the verified error catalog"
        )
    elif bundle.status == GroundingStatus.PARTIALLY_GROUNDED:
        policy, reason = GenerationPolicy.SUPPORTED_ONLY, (
            "some referenced topics are documented; unsupported topics will not be fabricated"
        )
    else:
        policy, reason = GenerationPolicy.BLOCK, (
            "no authoritative documentation or verified error-catalog evidence was found for this request"
        )
    return GenerationGateResult(
        policy=policy.value, allowed=policy in (GenerationPolicy.FULL, GenerationPolicy.SUPPORTED_ONLY),
        grounding_status=bundle.status.value, supported_topics=bundle.matched_topics,
        unsupported_topics=bundle.unmatched_topics, ambiguous_topics=bundle.ambiguous_topics, reason=reason,
    )


GENERATION_BLOCKED_MESSAGE = (
    "I don't have enough authoritative GAUSS documentation in the configured source to generate reliable "
    "GAUSS code for this request. If you know the GAUSS procedure or function you want to use, tell me its "
    "name and I can look it up."
)


def _render_clarify_message(bundle: GroundingBundle) -> str:
    parts = [
        f'"{r.user_phrase}" could match more than one documented topic ({", ".join(r.candidates)})'
        for r in bundle.resolutions
        if r.status == ResolutionStatus.AMBIGUOUS.value and r.candidates
    ]
    if not parts:
        parts.append("your request could refer to more than one documented GAUSS symbol")
    return (
        "I want to make sure I use the right documented GAUSS function before generating code: "
        + "; ".join(parts)
        + ". Which one did you mean? If you already know the exact function or procedure name, just tell me "
        "directly and I'll look it up."
    )


#: v0.73.0: a small, explicitly-verified set of real GAUSS language-level
#: statement keywords -- verified via real GAUSS execution in this
#: milestone's own development session (`tgauss.exe -b` on a script using
#: `proc`/`endp`/`retp`/`local`/`do while`/`endo`/`if`/`elseif`/`else`/
#: `endif`/`for`/`endfor`/`print`, which ran successfully end to end).
#: Deliberately small -- this is NOT an attempt to encode the full GAUSS
#: grammar, only enough of the common control-flow/declaration syntax that
#: `check_generated_symbols(...)` needs to avoid flagging a loop variable
#: or a language keyword as an unsupported function call.
_LANGUAGE_CONSTRUCT_KEYWORDS = frozenset({
    "if", "elseif", "else", "endif", "do", "while", "until", "endo", "for", "endfor",
    "proc", "endp", "retp", "local", "print", "struct",
})

#: v0.73.0: a small, explicitly-verified set of extremely common GAUSS
#: builtin functions -- verified via real GAUSS execution in this
#: milestone's own development session. Deliberately incomplete: this is
#: NOT a full builtin catalog, only enough to avoid flagging routine
#: matrix-construction/introspection calls as "unknown" merely because
#: they were not the specific subject of the current question's own
#: grounding bundle. `rndu`/`rndn` were added after this milestone's own
#: live Ollama evaluation (Phase 21) produced a real, genuine random-matrix
#: example using `rndu` and the checker flagged it as a false positive --
#: confirmed real via `tgauss.exe -b` before being added here.
_COMMON_BUILTIN_SYMBOLS = frozenset({"rows", "cols", "zeros", "ones", "rndu", "rndn"})

_CALL_SHAPED_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_ASSIGNMENT_TARGET_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)")
_PROC_DEFINITION_RE = re.compile(r"\bproc\b[^;]*?\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.IGNORECASE)


@dataclass(frozen=True)
class GeneratedSymbolCheck:
    """v0.73.0: a conservative, best-effort post-generation check -- NOT a
    compiler, NOT a claim of perfect static analysis. Exists specifically
    to catch a future `colmean(...)`-shaped hallucination even when the
    model ignores its own prompt instructions, which `v0.72.0`'s own live
    evaluation proved can happen."""

    #: Call-shaped symbols that matched a grounded/resolved topic.
    supported_symbols: tuple[str, ...]
    #: Call-shaped symbols that matched neither a grounded/resolved topic,
    #: a known language construct/common builtin, nor anything that looks
    #: locally user-defined -- the strongest signal of a hallucinated
    #: function name.
    unknown_call_symbols: tuple[str, ...]
    #: Call-shaped symbols that could plausibly be a user-defined `proc`
    #: or a variable also used in a call-like position -- never flagged as
    #: hallucinated, since GAUSS code may legitimately reference names the
    #: user (or the model, on the user's behalf) defines locally.
    user_defined_or_ambiguous_symbols: tuple[str, ...]


def _looks_like_control_flow_line(line: str) -> bool:
    stripped = line.strip().lower()
    return any(stripped.startswith(keyword) for keyword in _LANGUAGE_CONSTRUCT_KEYWORDS)


def check_generated_symbols(code: str, *, supported_symbols: tuple[str, ...]) -> GeneratedSymbolCheck:
    """Extracts call-shaped identifiers (`name(`) from `code`, skipping any
    line that begins with a known control-flow/declaration keyword (so a
    GAUSS `for`-loop's own header syntax, e.g. `for j (1, 3, 1);`, is never
    mistaken for a call to a function named `j`). `supported_symbols`
    should be the current turn's own grounded/resolved topics
    (case-insensitive). Deliberately conservative: a symbol is flagged as
    `unknown_call_symbols` only when it is neither supported, a known
    language construct/common builtin, nor plausibly assigned to or
    `proc`-defined elsewhere in the SAME code -- when the distinction
    cannot be made safely, this function classifies the symbol as
    ambiguous, never as hallucinated, per this module's own conservative-
    false-positive discipline."""
    supported = {s.lower() for s in supported_symbols} | _COMMON_BUILTIN_SYMBOLS
    assigned = {m.lower() for m in _ASSIGNMENT_TARGET_RE.findall(code)}
    proc_defined = {m.lower() for m in _PROC_DEFINITION_RE.findall(code)}

    known_supported: list[str] = []
    unknown: list[str] = []
    ambiguous: list[str] = []
    seen: set[str] = set()

    for line in code.splitlines():
        if _looks_like_control_flow_line(line):
            continue
        for match in _CALL_SHAPED_RE.finditer(line):
            symbol = match.group(1)
            lowered = symbol.lower()
            if lowered in seen or lowered in _LANGUAGE_CONSTRUCT_KEYWORDS:
                continue
            seen.add(lowered)
            if lowered in supported:
                known_supported.append(symbol)
            elif lowered in proc_defined or lowered in assigned:
                ambiguous.append(symbol)
            else:
                unknown.append(symbol)

    return GeneratedSymbolCheck(
        supported_symbols=tuple(known_supported), unknown_call_symbols=tuple(unknown),
        user_defined_or_ambiguous_symbols=tuple(ambiguous),
    )


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
    "unnecessary or trivial clarifying questions. Use ONLY the specific GAUSS functions/procedures named "
    "in the labeled documentation evidence below for anything GAUSS-syntax-specific -- if part of the "
    "request has no corresponding labeled evidence, explicitly say that part could not be generated "
    "reliably rather than filling the gap with an unverified guess."
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
    #: Populated whenever the answer text is code-shaped (v0.73.0: broadened
    #: from "only when `intent == CODE_GENERATION`" after live testing found
    #: a QA-classified question can still produce code-shaped prose the
    #: post-generation symbol check below should also cover).
    generated_code: tuple[str, ...] = ()
    #: Always `False` in this version -- no code path in this module can
    #: execute anything, so this can never legitimately become `True` here.
    executed: bool = False
    #: Always `False` in this version, for the same reason: nothing in this
    #: module verifies GAUSS output, GAUSS execution success, or
    #: methodological/statistical appropriateness.
    methodologically_validated: bool = False
    #: v0.73.0 additions -- grounding-gated generation.
    #: One of `GenerationPolicy`'s values, or `None` when the gate does not
    #: apply (every intent other than `CODE_GENERATION`).
    generation_policy: str | None = None
    #: Phrases/tokens `resolve_concepts(...)` found genuinely ambiguous
    #: (multiple similarly-scored documented candidates) -- always empty
    #: unless `generation_policy == GenerationPolicy.CLARIFY.value`.
    ambiguous_topics: tuple[str, ...] = ()
    #: Call-shaped symbols `check_generated_symbols(...)` found in the
    #: generated code that matched neither a grounded/resolved topic, a
    #: known language construct/common builtin, nor anything plausibly
    #: user-defined -- the strongest available post-generation signal of a
    #: hallucinated function name (e.g. a future `colmean(...)`). Always
    #: empty when `generated_code` is empty.
    unknown_symbols: tuple[str, ...] = ()


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

        # v0.73.0: for code-generation requests specifically, a deterministic
        # gate -- computed purely from `bundle`'s own real evidence -- decides
        # BEFORE the provider is ever consulted whether generation is
        # permitted at all. The provider is never given a chance to override
        # this: BLOCK and CLARIFY never reach `self.provider.complete(...)`.
        if intent == Intent.CODE_GENERATION:
            gate = compute_generation_gate(bundle)
            if gate.policy == GenerationPolicy.BLOCK.value:
                self.state.add("user", question)
                self.state.add("assistant", GENERATION_BLOCKED_MESSAGE)
                return AnswerResult(
                    text=GENERATION_BLOCKED_MESSAGE, grounded=bundle.hit, grounding_source=legacy_source,
                    grounding_topic=legacy_topic, provider_name="none", provider_model=None,
                    provider_success=True, provider_error=None, intent=intent.value,
                    grounding_status=bundle.status.value, grounding_sources=bundle.sources,
                    unsupported_topics=bundle.unmatched_topics, generation_policy=gate.policy,
                )
            if gate.policy == GenerationPolicy.CLARIFY.value:
                clarify_text = _render_clarify_message(bundle)
                self.state.add("user", question)
                self.state.add("assistant", clarify_text)
                return AnswerResult(
                    text=clarify_text, grounded=bundle.hit, grounding_source=legacy_source,
                    grounding_topic=legacy_topic, provider_name="none", provider_model=None,
                    provider_success=True, provider_error=None, intent=intent.value,
                    grounding_status=bundle.status.value, grounding_sources=bundle.sources,
                    unsupported_topics=bundle.unmatched_topics, generation_policy=gate.policy,
                    ambiguous_topics=bundle.ambiguous_topics,
                )
        else:
            gate = None

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
                generation_policy=gate.policy if gate is not None else None,
            )

        text = result.text or ""
        code_shaped = _looks_code_shaped(text)
        if code_shaped:
            text += NOT_EXECUTED_FOOTER
        # v0.73.0: broadened from "only when intent == CODE_GENERATION" --
        # this milestone's own live Ollama evaluation found a real question
        # ("Use reshape and colmean on my data.") that did not match any
        # code-generation trigger phrase (classified QA) but still produced
        # a code-shaped answer containing a hallucinated symbol. The
        # post-generation symbol check below is a pure safety net with no
        # user-facing behavior change other than an extra disclosure when
        # something looks wrong, so it should not be gated on intent
        # classification -- a hallucination is exactly as real in a QA
        # answer that happens to include example code as in an explicit
        # code-generation request.
        generated_code = extract_code_blocks(text) if code_shaped else ()

        # v0.73.0 Phase 8: a conservative, best-effort POST-generation check
        # -- catches a future `colmean(...)`-shaped hallucination even if the
        # model ignored its own prompt instructions, which is exactly what
        # v0.72.0's own live evaluation proved can happen. `supported_symbols`
        # includes not just each source's own topic name but every call-
        # shaped identifier appearing in that source's own retrieved content
        # -- live evaluation found `invinvpd.rst` (grounded topic `inv`)
        # legitimately documents `invpd` too, and the real model correctly
        # used it; since the CONTENT is real, retrieved documentation text,
        # never fabricated, treating names within it as supported carries no
        # fabrication risk.
        unknown_symbols: tuple[str, ...] = ()
        if generated_code:
            supported = set(bundle.matched_topics)
            for source in bundle.sources:
                supported.update(m.group(1) for m in _CALL_SHAPED_RE.finditer(source.content))
            all_unknown: list[str] = []
            for block in generated_code:
                block_check = check_generated_symbols(block, supported_symbols=tuple(supported))
                for symbol in block_check.unknown_call_symbols:
                    if symbol not in all_unknown:
                        all_unknown.append(symbol)
            unknown_symbols = tuple(all_unknown)

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
            generation_policy=gate.policy if gate is not None else None, unknown_symbols=unknown_symbols,
        )
