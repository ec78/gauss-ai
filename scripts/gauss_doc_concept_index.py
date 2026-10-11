"""Documentation-derived concept index (v0.74.0).

Phase 2/3 of the v0.74.0 milestone ("Deterministic Pre-Execution Validation
& Grounding Coverage Expansion"): expands natural-language-to-symbol
resolution beyond `gauss_conversation_engine.py`'s own 5-entry hand-curated
`_CONCEPT_ALIAS_INDEX` (v0.73.0) by deriving candidate concepts directly
from the configured official GAUSS documentation itself -- each page's own
heading, "Purpose" section, and cross-referenced companion symbols (`:func:`
references / backtick-quoted names). This is a small, deterministic,
bag-of-keywords overlap index -- NOT a vector database, NOT a language
model, NOT web search, and NOT model-generated aliases.

Every derived candidate is only ever a PROPOSAL. `gauss_conversation_engine.
resolve_concepts(...)` re-verifies every candidate this module returns
against the caller's own `docs_root` via a real `command_doc_lookup.
lookup(...)` call before treating it as resolved -- exactly mirroring the
v0.73.0 curated-alias index's own re-verification discipline. This module
only ever narrows down WHICH real lookup to attempt next; it never
fabricates a symbol, and a caller's own documentation checkout not actually
containing a derived candidate produces no resolution at all.

Bounded: `build_documentation_concept_index(...)` scans at most
`MAX_INDEXED_DOC_FILES` `.rst` files under `docs_root`. The real docs
checkout this milestone was developed against has over 2,000 files, so the
resulting index is cached in-process per resolved `docs_root` path
(`get_documentation_concept_index(...)`), keyed by the directory's own
`stat().st_mtime` -- an edited/refreshed documentation checkout is
re-indexed rather than silently served a stale index for the life of one
process (a soft, best-effort invalidation: it does not detect a change to a
single nested file that does not also touch the root directory's own mtime,
which is an accepted, disclosed limitation for this version).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import command_doc_lookup as doc_lookup_mod

#: Conservative bound on how many `.rst` files one index build will scan --
#: the real docs checkout this milestone was developed against has ~2,063.
MAX_INDEXED_DOC_FILES = 4000

#: Keyword tokens shorter than this are dropped -- too generic to be useful
#: overlap signal ("of", "the", "for", ...). v0.74.0 live evaluation
#: (category 64.x) found the original bound of 4 excluded real, meaningful
#: short domain words (e.g. "sum", as in `sumc`'s own "sum of each column"
#: purpose text) -- lowered to 3, which still excludes every 1-2 letter
#: function word.
MIN_KEYWORD_LEN = 3

#: Bounds how many derived keywords are retained per index entry.
MAX_KEYWORDS_PER_ENTRY = 16

#: How many distinct keyword tokens must overlap between a phrase and an
#: index entry before that entry is proposed as a candidate. Deliberately
#: >1: a single shared generic-sounding word (e.g. "column") appears across
#: many unrelated documentation pages and is not, by itself, real evidence.
MIN_KEYWORD_OVERLAP = 2

#: Bounds how many companion-symbol names are retained per index entry.
MAX_COMPANIONS_PER_ENTRY = 8

_WORD_RE = re.compile(r"[A-Za-z]{%d,}" % MIN_KEYWORD_LEN)

#: Matches a call-shaped identifier immediately preceded by `=` or `::`
#: (case where documentation syntax reads like `y = meanc(x)` or
#: `.. function:: y = meanc(x)`) -- used to recover the REAL callable
#: symbol name(s) documented on a page, since a page's own file stem is not
#: always a real symbol name (e.g. `invinvpd.rst` documents both `inv` and
#: `invpd`; neither is literally its own stem).
_ASSIGN_CALL_RE = re.compile(r"(?:^|[=:]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)

#: Words that appear across a large fraction of GAUSS documentation pages
#: regardless of topic -- explicitly excluded so keyword overlap reflects
#: real topical similarity, not shared documentation-prose vocabulary. Small
#: and explicit, reviewable like every other fixed list in this codebase.
_GENERIC_DOC_WORDS = frozenset({
    "this", "that", "with", "from", "into", "will", "have", "when", "where",
    "which", "each", "used", "using", "value", "values", "data", "input",
    "inputs", "output", "outputs", "argument", "arguments", "parameter",
    "parameters", "scalar", "string", "result", "results", "computes",
    "compute", "computed", "computing", "returns", "returned", "return",
    "function", "functions", "procedure", "procedures", "matrix", "matrices",
    "purpose", "format", "example", "examples", "note", "notes", "default",
    "optional", "specifies", "specify", "specified", "following", "number",
    "elements", "element", "given", "instance", "structure", "vector",
    "vectors", "type", "types",
    # v0.74.0 live evaluation (category 64.x, scenario 64.1) found these
    # specific words are common enough across the REAL ~2,063-file
    # documentation corpus, in unrelated contexts, to produce false keyword
    # overlaps -- confirmed by direct document-frequency measurement
    # against that real corpus (see also `MAX_DOC_FREQUENCY_FRACTION`
    # below, the general-purpose safety net for words not anticipated
    # here). "gauss" is the product name and appears in incidental
    # boilerplate on many otherwise-unrelated pages.
    "gauss", "gaus", "dataset", "datasets", "write", "writes", "written",
    "writing", "code",
    # v0.75.0 live evaluation (category 65.x, scenario 65.1) found a real,
    # different false-ambiguity mechanism the document-frequency filter
    # below does NOT catch: an ordinary English pronoun/auxiliary-verb pair
    # ("can", "you") that is genuinely rare across the real corpus's own
    # heading+Purpose text (14 and 2 entries respectively out of 2,105 --
    # nowhere near `MAX_DOC_FREQUENCY_FRACTION`'s threshold) but still
    # carries zero real topical signal, purely because it is ordinary
    # conversational English, not GAUSS-domain vocabulary. A user's own
    # question ("What does invpd do, and can you show a quick example?")
    # naturally contains this kind of filler; two otherwise-unrelated pages
    # (`dbqueryisforwardonly.rst`, `dbsetdatabasename.rst`) coincidentally
    # both used "you"/"can" in their own second-person-styled Purpose text,
    # producing a spurious `AMBIGUOUS` derived-concept resolution for the
    # WHOLE question even though `invpd` had already resolved via a direct
    # literal match. Fixed by adding a small, fixed, general-English
    # stopword list here -- corpus-frequency-independent, unlike the words
    # above -- since a pronoun/auxiliary/modal verb is never meaningfully
    # GAUSS-domain content regardless of how rare it happens to be in this
    # particular corpus.
    "you", "your", "yours", "can", "could", "would", "should", "shall",
    "must", "may", "might", "we", "our", "they", "their", "does", "did",
})


def _normalize_word(word: str) -> str:
    """A single trailing "s" is stripped for plural/singular tolerance (e.g.
    "means" -> "mean", "columns" -> "column") -- a deliberately crude,
    inspectable heuristic, not a real stemmer; harmless if occasionally
    wrong, since it only affects internal overlap-scoring tokens, never
    anything shown to a user."""
    lowered = word.lower()
    if lowered.endswith("s") and len(lowered) > MIN_KEYWORD_LEN:
        return lowered[:-1]
    return lowered


def _keywords_from_text(*texts: str | None) -> tuple[str, ...]:
    seen: list[str] = []
    for text in texts:
        if not text:
            continue
        for word in _WORD_RE.findall(text):
            lowered = word.lower()
            if lowered in _GENERIC_DOC_WORDS:
                continue
            normalized = _normalize_word(word)
            if normalized in _GENERIC_DOC_WORDS or normalized in seen:
                continue
            seen.append(normalized)
            if len(seen) >= MAX_KEYWORDS_PER_ENTRY:
                break
    return tuple(seen)


@dataclass(frozen=True)
class DerivedConceptEntry:
    """One documentation-derived candidate. `evidence` and `source` make
    every entry traceable back to the real file it came from -- required by
    this milestone's own spec ("every derived entry must remain traceable to
    its documentation source")."""

    symbol: str
    #: docs_root-relative file path.
    source: str
    keywords: tuple[str, ...]
    #: Other symbol names this page references (`:func:`/backtick refs) --
    #: used by `gauss_pre_execution_validation.find_companion_hint(...)` to
    #: surface a documented companion for an unsupported generated symbol.
    companions: tuple[str, ...]
    #: Short quoted purpose/heading text, for display and manual review.
    evidence: str


@dataclass(frozen=True)
class DocumentationConceptIndex:
    entries: tuple[DerivedConceptEntry, ...]
    docs_root: str
    files_scanned: int
    #: True if `MAX_INDEXED_DOC_FILES` was reached and some files were not
    #: scanned -- disclosed, never silently truncated.
    truncated: bool


def _extract_purpose_text(lines: list[str]) -> str | None:
    """GAUSS `.rst` documentation consistently uses a heading literally
    titled "Purpose" for a one-paragraph summary -- confirmed by direct
    reading of real `meanc.rst`/`invinvpd.rst` in this milestone's own
    development. `command_doc_lookup.SECTION_TITLES` does not recognize
    "purpose" as an alias for its own "notes" bucket, so this is extracted
    directly here rather than duplicating/widening that shared table."""
    headings = doc_lookup_mod.iter_headings(lines)
    for idx, heading in enumerate(headings):
        if heading["title"].strip().lower() == "purpose":
            start, end = doc_lookup_mod.find_section_bounds(lines, idx, headings)
            return doc_lookup_mod.compact_snippet("\n".join(lines[start:end]), 600)
    return None


def _extract_symbols_from_file(lines: list[str], stem: str) -> tuple[str, ...]:
    """Prefers the real callable name(s) parsed from documented call syntax
    over the file's own stem, since a page's stem is not always a real
    symbol (`invinvpd.rst` documents `inv` and `invpd`, neither of which is
    its own stem). Falls back to the stem only when no call-shaped syntax
    could be found at all -- never silently drops a file."""
    directive = doc_lookup_mod.extract_function_directive_details(lines)
    candidates: list[str] = []

    def _collect(text: str) -> None:
        for match in _ASSIGN_CALL_RE.finditer(text):
            name = match.group(1)
            if name.lower() not in (existing.lower() for existing in candidates):
                candidates.append(name)

    for syntax_line in directive.get("syntax", []):
        _collect(syntax_line)
    if candidates:
        return tuple(candidates)

    sections = doc_lookup_mod.extract_named_sections(lines)
    raw_syntax = sections.get("syntax_blocks")
    if raw_syntax:
        _collect(raw_syntax)
    if candidates:
        return tuple(candidates)

    return (stem,)


#: v0.74.0 live-evaluation finding (category 64.x, scenario 64.1): against
#: the real ~2,063-file documentation checkout, the fixed `_GENERIC_DOC_
#: WORDS` list alone was NOT enough -- words like "gauss" (the product
#: name, normalized to "gaus", present in nearly every page's own
#: boilerplate) and "dataset"/"write" turned out to be common enough across
#: UNRELATED pages to produce false keyword overlaps (a query about
#: "correlation... of my dataset" spuriously matched `combinated`,
#: `getname`, `h5write`, `null1`, `writer` -- none of them about
#: correlation at all). A fixed word list cannot anticipate every corpus-
#: specific filler word. Fixed by adding a deterministic DOCUMENT-FREQUENCY
#: filter (pure counting, still not ML/a vector space): any candidate word
#: appearing in more than `MAX_DOC_FREQUENCY_FRACTION` of all scanned files
#: is corpus-generic and excluded, regardless of whether it is on the fixed
#: list. Only applied once at least `MIN_FILES_FOR_DOC_FREQUENCY_FILTER`
#: files were scanned -- with only a handful of documents (as in this
#: module's own small, synthetic tests), frequency statistics are not
#: meaningful, so behavior there is unchanged and governed by
#: `_GENERIC_DOC_WORDS` alone. Set high enough (real measurement: 5%) that
#: a legitimately useful, moderately-common domain word ("column", found
#: in ~4.2% of the real corpus) survives -- this filter is a secondary
#: safety net for corpus-generic words `_GENERIC_DOC_WORDS` did not
#: anticipate, not the primary defense (that role belongs to the explicit
#: list plus `MIN_KEYWORD_OVERLAP`).
MAX_DOC_FREQUENCY_FRACTION = 0.05
MIN_FILES_FOR_DOC_FREQUENCY_FILTER = 50


@dataclass(frozen=True)
class _FileRecord:
    symbols: tuple[str, ...]
    source: str
    raw_keywords: tuple[str, ...]
    companions: tuple[str, ...]
    evidence: str


def build_documentation_concept_index(docs_root: Path) -> DocumentationConceptIndex:
    """Bounded, deterministic, real-file-based. Every entry can be traced
    back to `source` (a real, existing docs_root-relative file). Never
    invents a symbol, keyword, or companion that is not present in the
    scanned file's own text. Two passes: the first collects each file's own
    raw keyword candidates and builds a document-frequency count; the
    second drops any candidate that turned out to be corpus-generic (see
    `MAX_DOC_FREQUENCY_FRACTION` above) before finalizing each entry's
    keyword set."""
    all_paths = sorted(docs_root.rglob("*.rst"))
    truncated = len(all_paths) > MAX_INDEXED_DOC_FILES
    paths = all_paths[:MAX_INDEXED_DOC_FILES]

    records: list[_FileRecord] = []
    document_frequency: dict[str, int] = {}
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = text.splitlines()
        heading = doc_lookup_mod.first_heading(lines) or path.stem
        purpose = _extract_purpose_text(lines)
        raw_keywords = _keywords_from_text(heading, purpose)
        if not raw_keywords:
            continue  # nothing usable to index -- never guess at keywords

        for word in set(raw_keywords):
            document_frequency[word] = document_frequency.get(word, 0) + 1

        symbols = _extract_symbols_from_file(lines, path.stem)
        raw_companions = tuple(
            link for link in doc_lookup_mod.extract_related_links(lines)
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", link)
        )[:MAX_COMPANIONS_PER_ENTRY]
        try:
            rel_path = str(path.resolve().relative_to(docs_root.resolve())).replace("\\", "/")
        except ValueError:
            rel_path = str(path)

        records.append(_FileRecord(
            symbols=symbols, source=rel_path, raw_keywords=raw_keywords, companions=raw_companions, evidence=purpose or heading,
        ))

    files_scanned = len(paths)
    if files_scanned >= MIN_FILES_FOR_DOC_FREQUENCY_FILTER:
        doc_freq_threshold = max(2, int(files_scanned * MAX_DOC_FREQUENCY_FRACTION))
        corpus_generic_words = {word for word, count in document_frequency.items() if count > doc_freq_threshold}
    else:
        corpus_generic_words = set()

    entries: list[DerivedConceptEntry] = []
    for record in records:
        keywords = tuple(w for w in record.raw_keywords if w not in corpus_generic_words)[:MAX_KEYWORDS_PER_ENTRY]
        if not keywords:
            continue  # every candidate turned out to be corpus-generic -- never index on nothing real
        for symbol in record.symbols:
            entries.append(DerivedConceptEntry(
                symbol=symbol,
                source=record.source,
                keywords=keywords,
                companions=tuple(c for c in record.companions if c.lower() != symbol.lower()),
                evidence=record.evidence,
            ))

    return DocumentationConceptIndex(
        entries=tuple(entries), docs_root=str(docs_root), files_scanned=files_scanned, truncated=truncated,
    )


#: In-process cache keyed by (resolved docs_root path, directory mtime) --
#: bounded to a small number of distinct docs roots so a long-running
#: process cannot grow this unboundedly.
_INDEX_CACHE: dict[tuple[str, float], DocumentationConceptIndex] = {}
_INDEX_CACHE_MAX_ENTRIES = 4


def get_documentation_concept_index(docs_root: Path) -> DocumentationConceptIndex:
    """Cached wrapper around `build_documentation_concept_index(...)` -- a
    real docs checkout can have thousands of files, and re-scanning all of
    them on every conversational turn would be real, unbounded-feeling
    latency for no benefit within one process's lifetime."""
    try:
        cache_key = (str(docs_root.resolve()), docs_root.stat().st_mtime)
    except OSError:
        return build_documentation_concept_index(docs_root)
    cached = _INDEX_CACHE.get(cache_key)
    if cached is not None:
        return cached
    index = build_documentation_concept_index(docs_root)
    if len(_INDEX_CACHE) >= _INDEX_CACHE_MAX_ENTRIES:
        _INDEX_CACHE.clear()
    _INDEX_CACHE[cache_key] = index
    return index


@dataclass(frozen=True)
class DerivedConceptMatch:
    symbol: str
    source: str
    overlap_keywords: tuple[str, ...]
    evidence: str


def resolve_derived_concepts(phrase: str, index: DocumentationConceptIndex) -> tuple[DerivedConceptMatch, ...]:
    """Deterministic bag-of-keywords overlap scoring over the WHOLE phrase
    (not per single token -- a lone generic-sounding word should not, by
    itself, propose a candidate). Returns every entry at the highest
    overlap count that meets `MIN_KEYWORD_OVERLAP`, ranked/tie-broken by
    symbol name for determinism; returns an empty tuple, never a
    low-confidence guess, when nothing meets the threshold. More than one
    DISTINCT symbol at the top score is genuine ambiguity for the caller to
    handle, exactly like `command_doc_lookup.lookup(...)`'s own tie logic."""
    phrase_words = {_normalize_word(w) for w in _WORD_RE.findall(phrase)}
    if not phrase_words:
        return ()

    scored: list[tuple[int, str, DerivedConceptEntry, tuple[str, ...]]] = []
    for entry in index.entries:
        overlap = tuple(sorted(phrase_words & set(entry.keywords)))
        if len(overlap) >= MIN_KEYWORD_OVERLAP:
            scored.append((len(overlap), entry.symbol.lower(), entry, overlap))

    if not scored:
        return ()

    scored.sort(key=lambda item: (-item[0], item[1]))
    best_count = scored[0][0]
    top = [item for item in scored if item[0] == best_count]
    return tuple(
        DerivedConceptMatch(symbol=entry.symbol, source=entry.source, overlap_keywords=overlap, evidence=entry.evidence)
        for _, _, entry, overlap in top
    )


def keyword_overlap_entries(
    phrase: str, index: DocumentationConceptIndex, *, min_overlap: int,
) -> tuple[tuple[DerivedConceptEntry, tuple[str, ...]], ...]:
    """v0.83.0: every index entry sharing at least `min_overlap` keywords with
    `phrase`, with the shared keywords, in index order. Used only by
    `gauss_conversation_engine.search_candidates(...)` to list labeled
    CANDIDATE pages for `gauss_search_docs` -- never to resolve or ground
    anything. `resolve_derived_concepts(...)` above, which does feed grounding
    (and so the `ask()` generation gate), keeps its own `MIN_KEYWORD_OVERLAP`
    and is not affected."""
    phrase_words = {_normalize_word(w) for w in _WORD_RE.findall(phrase)}
    if not phrase_words:
        return ()
    matches = []
    for entry in index.entries:
        overlap = tuple(sorted(phrase_words & set(entry.keywords)))
        if len(overlap) >= min_overlap:
            matches.append((entry, overlap))
    return tuple(matches)


def normalize_keyword(word: str) -> str:
    """v0.83.0: the public form of the keyword normalization the index uses,
    so a caller can compare other documentation text against `keywords`."""
    return _normalize_word(word)
