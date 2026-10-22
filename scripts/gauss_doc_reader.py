"""Read-only, page-bounded reading of one documentation page, or one section
of it, verbatim (v0.89.0; planning v0.89 §3.6, live finding 79.x-1).

Why this exists: `gauss_search_docs` returns at most a 1,500-character
excerpt per source, built by `command_doc_lookup.extract_match(...)`. Live
evaluation 79.x needed content that never reaches that excerpt:
`dllcall.rst`'s Remarks (cut by the budget) and `sqpSolveMT`'s return codes
(`:0: normal convergence.` ... `:8: function complex.`), which extraction
itself drops -- `command_doc_lookup.py` skips every indented line starting
with `:` inside a function block (planning v0.89 §2.6; 512 pages have such
nested value lists). The 79.x client read those files from disk; a
stranger's client may have no disk access. A larger excerpt bound would not
have fixed the return codes, and changing extraction is a signature-parsing
change with its own all-pages diff, so this module serves the page's own
RST source instead, sliced by heading, without going through extraction.

Boundaries:

- Local and read-only: no network, no write, no model call.
- Nothing returned here is a grounding input. It cannot change a grounding
  status, the generation gate or any validation verdict, and no module on
  those paths imports this one.
- It reads only the user's own downloaded copy under `docs_root` (the same
  per-user posture as search excerpts; nothing is bundled or redistributed).
- `page` is untrusted input: it must pass `gauss_docs_fetch.
  safe_relative_path(...)` (the same rules the downloader applies to remote
  file names: relative, `.rst`, no `..`, no backslash or drive letter), and
  its resolved real path (symlinks followed) must stay inside the resolved
  docs root.
- Every answer is bounded: at most `READ_DOC_MAX_CHARS` characters per call,
  with `next_offset` to continue. `ge/api-reference.rst` (2.76 million
  characters) is read in pieces like any other page.

The heading scanner here is deliberately separate from
`command_doc_lookup.iter_headings`, which v0.88's decision 11 froze along
with the rest of the extraction code: sharing it would tie this reader to
extraction. Its rules are RST's own title forms -- a title line followed by
an underline of one repeated punctuation character, optionally with a
matching overline -- with title, underline and overline all unindented, so
an indented literal block or a `.. list-table::` row can never open a
section.
"""

from __future__ import annotations

import string
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gauss_docs_fetch as fetch_mod

#: The most characters one call returns. 8,000 covers the p99 section
#: (9,570 characters) in two calls and almost every section in one
#: (planning v0.89 §2.6).
READ_DOC_MAX_CHARS = 8000

#: `section="*"` reads the whole page, under the same bound and paging.
WHOLE_PAGE = "*"

_ADORNMENT_CHARS = frozenset(string.punctuation)


@dataclass(frozen=True)
class DocSection:
    """One heading of a page. `start`/`end` are character offsets into the
    page text: `start` is the heading's first line (its overline, if any),
    and `end` is where the next heading of the same or a higher level starts
    (or the end of the page), so a section includes its subsections.
    `segment_end` is where the very next heading of any level starts: the
    flat segments `[start, segment_end)` plus the preamble partition the page
    exactly."""

    heading: str
    level: int
    start: int
    end: int
    segment_end: int


@dataclass(frozen=True)
class DocOutline:
    title: str | None
    chars: int
    preamble_chars: int
    sections: tuple[DocSection, ...]


def _adornment(line: str) -> str | None:
    """The repeated punctuation character of an RST adornment line (at
    least 3 long, unindented, nothing else on the line), or None."""
    if line[:1].isspace():
        return None
    stripped = line.rstrip()
    if len(stripped) < 3 or stripped[0] not in _ADORNMENT_CHARS:
        return None
    char = stripped[0]
    return char if stripped == char * len(stripped) else None


def _is_title_line(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not line[:1].isspace() and _adornment(line) is None


def parse_sections(text: str) -> DocOutline:
    """Every RST title in `text`, in order, with levels numbered by first
    appearance of each adornment style (underline character, with or
    without overline), as docutils does."""
    lines = text.splitlines(keepends=True)
    offsets: list[int] = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line)
    found: list[tuple[str, tuple[str, bool], int]] = []
    styles: list[tuple[str, bool]] = []
    #: The last line a previous title used (its underline), so that line is
    #: never also read as the next title's overline.
    last_used_line = -1
    i = 0
    while i < len(lines) - 1:
        line, below = lines[i], lines[i + 1]
        underline = _adornment(below)
        if underline is not None and _is_title_line(line):
            overline = i - 1 > last_used_line and _adornment(lines[i - 1]) == underline
            start_line = i - 1 if overline else i
            style = (underline, overline)
            if style not in styles:
                styles.append(style)
            found.append((line.strip(), style, offsets[start_line]))
            last_used_line = i + 1
            i += 2
            continue
        i += 1
    total = len(text)
    sections: list[DocSection] = []
    for index, (heading, style, start) in enumerate(found):
        level = styles.index(style) + 1
        segment_end = found[index + 1][2] if index + 1 < len(found) else total
        end = total
        for later_heading, later_style, later_start in found[index + 1:]:
            if styles.index(later_style) + 1 <= level:
                end = later_start
                break
        sections.append(DocSection(heading=heading, level=level, start=start, end=end, segment_end=segment_end))
    preamble = sections[0].start if sections else total
    return DocOutline(
        title=sections[0].heading if sections else None, chars=total, preamble_chars=preamble,
        sections=tuple(sections),
    )


def docs_url(page: str) -> str | None:
    """The page's public address on docs.aptech.com, built from the citation
    alone (`sqpsolvemt.rst` -> `https://docs.aptech.com/gauss/sqpsolvemt.html`;
    nested pages keep their folders). No network access: Sphinx publishes
    each `<docname>.rst` as `<docname>.html`, the same docnames
    `gauss-ai docs fetch` reads from `searchindex.js`. v0.89.0: Aptech asked for
    a link back to the docs.aptech.com page with each result (planning v0.89
    §9.3). None for anything that is not a safe `.rst` citation."""
    relative = fetch_mod.safe_relative_path(page)
    if relative is None:
        return None
    return fetch_mod.DOCS_BASE_URL + relative.with_suffix(".html").as_posix()


def resolve_page(docs_root: str | Path, page: str) -> tuple[Path | None, str | None]:
    """`(path, None)` for a page that may be read, else `(None, reason)`.
    Reads nothing."""
    relative = fetch_mod.safe_relative_path(page)
    if relative is None:
        return None, "page must be a relative .rst citation as gauss_search_docs returns it, with no '..'"
    try:
        root = Path(docs_root).resolve(strict=True)
    except OSError:
        return None, "the configured docs root does not exist"
    candidate = root.joinpath(*relative.parts)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError:
        return None, "no such page under the docs root"
    if not resolved.is_relative_to(root):
        return None, "the page resolves outside the docs root"
    if not resolved.is_file():
        return None, "no such page under the docs root"
    return resolved, None


def read_page_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_doc(docs_root: str | Path, page: str, *, section: str | None = None, offset: int = 0) -> dict[str, Any]:
    """The whole read, as a JSON-safe dict. Without `section`, the page's
    outline. With `section` (a heading, matched case-insensitively, first
    match; or `"*"`), up to `READ_DOC_MAX_CHARS` characters of that
    section's raw source from `offset`, plus `next_offset` when more
    remains."""
    path, refusal = resolve_page(docs_root, page)
    if path is None:
        return {"error": "page_refused", "detail": refusal, "citation": page}
    text = read_page_text(path)
    outline = parse_sections(text)
    if section is None:
        return {
            "citation": page,
            "docs_url": docs_url(page),
            "title": outline.title,
            "chars": outline.chars,
            "sections": [
                {"heading": s.heading, "level": s.level, "chars": s.end - s.start} for s in outline.sections
            ],
            "max_chars_per_read": READ_DOC_MAX_CHARS,
        }
    if section.strip() == WHOLE_PAGE:
        heading, start, end = WHOLE_PAGE, 0, len(text)
    else:
        wanted = section.strip().casefold()
        match = next((s for s in outline.sections if s.heading.casefold() == wanted), None)
        if match is None:
            return {
                "error": "unknown_section",
                "detail": f"No section named {section!r} on this page; read one of these, or '*' for the whole page.",
                "citation": page,
                "available_sections": [s.heading for s in outline.sections],
            }
        heading, start, end = match.heading, match.start, match.end
    body = text[start:end]
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0 or offset > len(body):
        return {
            "error": "offset_out_of_range",
            "detail": f"offset must be an integer from 0 to {len(body)} for this section",
            "citation": page,
        }
    piece = body[offset:offset + READ_DOC_MAX_CHARS]
    next_offset = offset + len(piece)
    return {
        "citation": page,
        "docs_url": docs_url(page),
        "section": heading,
        "offset": offset,
        "chars_total": len(body),
        "content": piece,
        "next_offset": next_offset if next_offset < len(body) else None,
    }
