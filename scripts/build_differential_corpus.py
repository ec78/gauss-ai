"""One-off/rerunnable builder for the v0.77.0 differential syntax-validation
corpus (planning/v0.77.0-differential-syntax-validation.md Phases 4-6).

NOT part of the default test suite and NOT imported by any conversational or
execution module -- this script only ever reads local files (a real
documentation checkout and this repository's own `evaluations/runs/*.md`
transcripts) and writes static JSONL corpus files under
`evaluations/differential_corpus/`. It performs no GAUSS execution and no
model-provider call of any kind.

Produces three of the four corpus family files (the fourth,
`model_output_fresh.jsonl`, comes from a separate live-Ollama stress batch,
Phase 15, and is merged in the same schema by a different script):

- `docs_valid.jsonl`   (Family A -- Phase 4)
- `mutations.jsonl`    (Family B -- Phase 5, via `gauss_syntax_mutations.py`)
- `model_output_historical.jsonl` (Family C, historical half -- Phase 6)

Every corpus item is one JSON object per line with the common shape
`{"id", "origin", "snippet", "expected_class", "provenance": {...}}`.
`expected_class` is `"valid"` only for Family A (the documentation itself
asserts these are genuine examples) -- `null` for mutations (Phase 5:
"Do not assume the mutation is invalid merely because it looks invalid") and
for model output (never known a priori); the real `tgauss.exe` oracle in
`gauss_differential_harness.py` is what actually determines ground truth.

Family A extraction is deliberately restricted to `::`-introduced RST
literal blocks that fall under an "Examples" heading (before the next
top-level heading) -- NOT "Format" blocks (which contain placeholder tokens
like `...`/`constant_list`, never real runnable code) and NOT "Remarks"
blocks (which, in this real docs checkout, sometimes illustrate
DELIBERATELY ILLEGAL syntax as a negative example -- e.g. `let.rst`'s own
Remarks text: "expressions such as this: `let x[2, 1] = 3*a b` are
illegal"). Restricting to Examples sections avoids ever mislabeling a
docs-illustrated-illegal snippet as Family-A "valid" ground truth. This is a
real scoping tradeoff (a smaller Family A than scanning every `::` block
would produce) recorded here and in `docs/differential-syntax-validation.md`
rather than silently made.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_syntax_mutations as mut  # noqa: E402

_REPO_ROOT = _SCRIPT_DIR.parent
_CORPUS_DIR = _REPO_ROOT / "evaluations" / "differential_corpus"
_RUNS_DIR = _REPO_ROOT / "evaluations" / "runs"

#: Bounded, explicit file list -- see module docstring. Every path is
#: relative to the caller-supplied --docs-root. Chosen to cover Phase 4's
#: construct list (assignment, matrix/vector literal, function call, nested
#: call, indexing, print, strings, arithmetic, conditionals, loops,
#: procedures, local variables) using real pages confirmed present in this
#: session's own local docs checkout.
_FAMILY_A_FILES: tuple[str, ...] = (
    "let.rst", "meanc.rst", "invinvpd.rst", "chol.rst", "solpd.rst", "sumc.rst", "stdc.rst",
    "reshape.rst", "sprintf.rst", "cols.rst", "rows.rst", "ones.rst", "zeros.rst", "eye.rst",
    "print.rst", "if.rst", "for.rst", "dowhiledountil.rst", "local.rst", "proc.rst",
    "arrayindex.rst", "matrix-multiplication.rst", "matrix-division.rst",
)

_HEADING_UNDERLINE_CHARS = "=-~^\"'"


@dataclass(frozen=True)
class DocSnippet:
    snippet: str
    source_document: str
    line_start: int
    line_end: int


def _is_heading_underline(line: str, heading_text_len: int) -> bool:
    stripped = line.rstrip("\n")
    if not stripped:
        return False
    if len(set(stripped)) != 1:
        return False
    return stripped[0] in _HEADING_UNDERLINE_CHARS and len(stripped) >= max(3, heading_text_len - 2)


def _find_section(lines: list[str], heading: str) -> tuple[int, int] | None:
    """Returns `(start_line_idx, end_line_idx)` (end exclusive) of the body
    of the first top-level section whose heading text matches `heading`
    (case-insensitive, exact line text) -- body runs until the next line
    that is itself a heading (a text line immediately followed by a valid
    underline), or EOF."""
    start = None
    for i in range(len(lines) - 1):
        text = lines[i].strip()
        if text.lower() == heading.lower() and _is_heading_underline(lines[i + 1], len(text)):
            start = i + 2
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines) - 1):
        text = lines[j].strip()
        if text and _is_heading_underline(lines[j + 1], len(text)):
            end = j
            break
    return start, end


def _extract_literal_blocks(lines: list[str], start: int, end: int) -> list[tuple[str, int, int]]:
    """Finds every `::`-introduced RST literal block within `lines[start:end]`.
    Returns `(dedented_text, first_line_no, last_line_no)` triples, 1-indexed
    against the ORIGINAL file for provenance."""
    blocks: list[tuple[str, int, int]] = []
    i = start
    while i < end:
        if lines[i].strip() == "::":
            j = i + 1
            while j < end and not lines[j].strip():
                j += 1
            block_start = j
            block_lines: list[str] = []
            while j < end and (not lines[j].strip() or lines[j].startswith(("    ", "\t"))):
                block_lines.append(lines[j])
                j += 1
            while block_lines and not block_lines[-1].strip():
                block_lines.pop()
            if block_lines:
                dedented = "\n".join(line[4:] if line.startswith("    ") else line.rstrip("\n") for line in block_lines)
                blocks.append((dedented, block_start + 1, block_start + len(block_lines)))
            i = j
        else:
            i += 1
    return blocks


def extract_docs_valid_snippets(docs_root: Path, relative_path: str) -> list[DocSnippet]:
    file_path = docs_root / relative_path
    if not file_path.exists():
        return []
    lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    section = _find_section(lines, "Examples")
    if section is None:
        return []
    start, end = section
    snippets: list[DocSnippet] = []
    for text, line_start, line_end in _extract_literal_blocks(lines, start, end):
        if "..." in text:
            continue  # placeholder/ellipsis text, not real runnable code
        if ";" not in text:
            continue  # a result-display block, not a real GAUSS statement
        snippets.append(DocSnippet(snippet=text, source_document=relative_path, line_start=line_start, line_end=line_end))
    return snippets


def build_family_a(docs_root: Path) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    counter = 0
    for relative_path in _FAMILY_A_FILES:
        for doc_snippet in extract_docs_valid_snippets(docs_root, relative_path):
            if doc_snippet.snippet in seen:
                continue
            seen.add(doc_snippet.snippet)
            counter += 1
            items.append({
                "id": f"A-{counter:03d}",
                "origin": "docs_valid",
                "snippet": doc_snippet.snippet,
                "expected_class": "valid",
                "provenance": {
                    "source_document": doc_snippet.source_document,
                    "section": "Examples",
                    "line_start": doc_snippet.line_start,
                    "line_end": doc_snippet.line_end,
                    "extraction_method": (
                        "RST '::'-introduced literal block under an Examples heading, "
                        "filtered to contain ';' and no '...' placeholder"
                    ),
                },
            })
    return items


#: Phase 5: "Prefer breadth across mutation families over huge counts of
#: near-duplicates." With ~50 Family-A seeds and 17 operators, applying every
#: operator to every applicable seed produces 300-400+ items, most of which
#: are structurally near-identical (the same operator against very similar
#: `meanc`/`sumc`-shaped seeds). Capping per-operator count, sampling seeds
#: evenly spread across the whole seed list (not just the first N), keeps
#: every mutation family represented while staying inside the milestone's own
#: suggested 100-300 range and keeping the real-`tgauss.exe` baseline run
#: tractable.
MAX_MUTATIONS_PER_OPERATOR = 8


def build_family_b(family_a_items: list[dict]) -> list[dict]:
    by_operator: dict[str, list[tuple[dict, str]]] = {name: [] for name in mut.MUTATION_OPERATORS}
    for seed in family_a_items:
        for operator_name, mutated in mut.apply_all_mutations(seed["snippet"]).items():
            by_operator[operator_name].append((seed, mutated))

    items: list[dict] = []
    counter = 0
    for operator_name, candidates in by_operator.items():
        if not candidates:
            continue
        step = max(1, len(candidates) // MAX_MUTATIONS_PER_OPERATOR)
        sampled = candidates[::step][:MAX_MUTATIONS_PER_OPERATOR]
        for seed, mutated in sampled:
            counter += 1
            items.append({
                "id": f"B-{counter:03d}",
                "origin": "mutation",
                "snippet": mutated,
                "expected_class": None,
                "provenance": {
                    "seed_id": seed["id"],
                    "original_valid_snippet": seed["snippet"],
                    "mutation_operator": operator_name,
                    "mutation_description": mut.MUTATION_DESCRIPTIONS[operator_name],
                },
            })
    return items


_RUN_FILE_RE = re.compile(
    r"Prompt ID:\s*(?P<prompt_id>\S+).*?"
    r"```gauss\r?\n(?P<code>.*?)```\r?\n"
    r"(?:```\r?\n(?P<metadata>.*?)```\r?\n)?",
    re.DOTALL,
)
_METADATA_LINE_RE = re.compile(r"^(generation_policy|pre_execution_eligibility|syntax_validation|handoff_readiness)=(.+)$", re.MULTILINE)


def extract_model_output_from_run_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = _RUN_FILE_RE.search(text)
    if match is None or not match.group("code").strip():
        return None
    metadata_text = match.group("metadata") or ""
    metadata = {key: value.strip() for key, value in _METADATA_LINE_RE.findall(metadata_text)}
    return {
        "prompt_id": match.group("prompt_id"),
        "code": match.group("code").strip("\n"),
        "generation_policy": metadata.get("generation_policy"),
        "pre_execution_eligibility": metadata.get("pre_execution_eligibility"),
        "syntax_validation": metadata.get("syntax_validation"),
        "handoff_readiness": metadata.get("handoff_readiness"),
    }


def build_family_c_historical(runs_dir: Path, *, categories: tuple[str, ...]) -> list[dict]:
    items: list[dict] = []
    counter = 0
    for run_path in sorted(runs_dir.glob("2026-*-code-assistant-*.md")):
        extracted = extract_model_output_from_run_file(run_path)
        if extracted is None:
            continue
        prompt_id = extracted["prompt_id"] or ""
        major = prompt_id.split(".")[0]
        if major not in categories:
            continue
        counter += 1
        items.append({
            "id": f"C-{counter:03d}",
            "origin": "model_output_historical",
            "snippet": extracted["code"],
            "expected_class": None,
            "provenance": {
                "source_run": run_path.name,
                "prompt_id": prompt_id,
                "generation_policy": extracted["generation_policy"],
                "eligibility_at_time": extracted["pre_execution_eligibility"],
                "syntax_status_at_time": extracted["syntax_validation"],
                "readiness_at_time": extracted["handoff_readiness"],
            },
        })
    return items


def _write_jsonl(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for item in items:
            handle.write(json.dumps(item, ensure_ascii=False))
            handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-root", required=True, help="Path to a real local GAUSS documentation checkout.")
    parser.add_argument(
        "--historical-categories", default="61,62,63,64,65,66",
        help="Comma-separated benchmark-prompt major category numbers to pull Family C from.",
    )
    args = parser.parse_args(argv)

    docs_root = Path(args.docs_root)
    if not docs_root.exists():
        print(f"docs-root does not exist: {docs_root}", file=sys.stderr)
        return 1

    family_a = build_family_a(docs_root)
    family_b = build_family_b(family_a)
    categories = tuple(args.historical_categories.split(","))
    family_c = build_family_c_historical(_RUNS_DIR, categories=categories)

    _write_jsonl(_CORPUS_DIR / "docs_valid.jsonl", family_a)
    _write_jsonl(_CORPUS_DIR / "mutations.jsonl", family_b)
    _write_jsonl(_CORPUS_DIR / "model_output_historical.jsonl", family_c)

    print(f"Family A (docs_valid):            {len(family_a)} snippets -> {_CORPUS_DIR / 'docs_valid.jsonl'}")
    print(f"Family B (mutations):              {len(family_b)} snippets -> {_CORPUS_DIR / 'mutations.jsonl'}")
    print(f"Family C (model_output_historical): {len(family_c)} snippets -> {_CORPUS_DIR / 'model_output_historical.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
