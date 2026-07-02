#!/usr/bin/env python3
"""Lookup GAUSS command documentation in local official .rst docs.

This is a small, conservative prototype. It extracts only text found in the
matched documentation file and reports unresolved fields instead of guessing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SECTION_TITLES = {
    "syntax_blocks": ("syntax", "format", "formats", "usage"),
    "inputs_section": (
        "input",
        "inputs",
        "argument",
        "arguments",
        "parameter",
        "parameters",
    ),
    "outputs_section": (
        "output",
        "outputs",
        "return",
        "returns",
        "return value",
        "return values",
        "returned values",
    ),
    "examples": ("example", "examples"),
    "notes": ("note", "notes", "remark", "remarks", "description", "details"),
}

HEADING_CHARS = set("=-~^`:#*+")
MAX_SNIPPET_CHARS = 1400


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "", text.lower())


def is_heading_underline(line: str, title: str) -> bool:
    stripped = line.strip()
    return (
        bool(stripped)
        and len(stripped) >= max(3, len(title.strip()) // 2)
        and len(set(stripped)) == 1
        and stripped[0] in HEADING_CHARS
    )


def iter_headings(lines: list[str]) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for idx in range(len(lines) - 1):
        title = lines[idx].strip()
        if title and is_heading_underline(lines[idx + 1], title):
            headings.append({"title": title, "line": idx})
    return headings


def first_heading(lines: list[str]) -> str | None:
    headings = iter_headings(lines)
    return headings[0]["title"] if headings else None


def find_section_bounds(lines: list[str], heading_idx: int, headings: list[dict[str, Any]]) -> tuple[int, int]:
    start = headings[heading_idx]["line"]
    end = len(lines)
    if heading_idx + 1 < len(headings):
        end = headings[heading_idx + 1]["line"]
    return start, end


def compact_snippet(text: str, max_chars: int = MAX_SNIPPET_CHARS) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20].rstrip() + "\n...[truncated]"


def extract_named_sections(lines: list[str]) -> dict[str, str | None]:
    headings = iter_headings(lines)
    extracted: dict[str, str | None] = {key: None for key in SECTION_TITLES}

    for idx, heading in enumerate(headings):
        norm_title = heading["title"].strip().lower()
        for output_key, names in SECTION_TITLES.items():
            if extracted[output_key] is not None:
                continue
            if any(norm_title == name or norm_title.startswith(name + " ") for name in names):
                start, end = find_section_bounds(lines, idx, headings)
                extracted[output_key] = compact_snippet("\n".join(lines[start:end]))

    return extracted


def extract_literal_blocks_near_command(lines: list[str], command_name: str) -> list[str]:
    command_re = re.compile(rf"\b{re.escape(command_name)}\s*\(", re.IGNORECASE)
    blocks: list[str] = []
    current: list[str] = []
    in_block = False

    for line in lines:
        starts_literal = line.rstrip().endswith("::") or line.strip().startswith(".. code-block::")
        if starts_literal:
            if current:
                block = "\n".join(current).strip()
                if command_re.search(block):
                    blocks.append(compact_snippet(block))
                current = []
            in_block = True
            continue

        if in_block:
            if line.startswith((" ", "\t")) or not line.strip():
                current.append(line.rstrip())
                continue
            block = "\n".join(current).strip()
            if block and command_re.search(block):
                blocks.append(compact_snippet(block))
            current = []
            in_block = False

        if command_re.search(line):
            blocks.append(line.strip())

    if current:
        block = "\n".join(current).strip()
        if command_re.search(block):
            blocks.append(compact_snippet(block))

    deduped: list[str] = []
    for block in blocks:
        if block and block not in deduped:
            deduped.append(block)
    return deduped[:5]


def extract_function_directive_details(lines: list[str]) -> dict[str, list[str]]:
    syntax: list[str] = []
    params: list[str] = []
    returns: list[str] = []

    in_function = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(".. function::"):
            in_function = True
            syntax.append(stripped)
            continue

        if in_function:
            if stripped and not line.startswith((" ", "\t")) and not stripped.startswith(":"):
                in_function = False
                continue
            if stripped.startswith(":param") or stripped.startswith(":type"):
                params.append(stripped)
                continue
            if stripped.startswith(":return") or stripped.startswith(":rtype"):
                returns.append(stripped)
                continue
            if stripped.startswith(".. ") and not stripped.startswith(".. function::"):
                in_function = False
                continue
            if line.startswith((" ", "\t")) and stripped and not stripped.startswith(":"):
                if "(" in stripped and ")" in stripped and not stripped.startswith(("E.g", "If ", "=", "-")):
                    syntax.append(stripped)

    return {
        "syntax": [item for idx, item in enumerate(syntax) if item not in syntax[:idx]],
        "params": params,
        "returns": returns,
    }


def score_file(path: Path, lines: list[str], command_name: str) -> tuple[int, list[str]]:
    command_norm = normalize(command_name)
    stem_norm = normalize(path.stem)
    reasons: list[str] = []
    score = 0

    if stem_norm == command_norm:
        score += 100
        reasons.append("exact_file_name")
    elif command_norm in stem_norm:
        score += 45
        reasons.append("command_in_file_name")

    headings = iter_headings(lines)
    for heading in headings:
        heading_norm = normalize(heading["title"])
        if heading_norm == command_norm:
            score += 80
            reasons.append("exact_heading")
            break
        if command_norm in heading_norm:
            score += 35
            reasons.append("command_in_heading")
            break

    anchor_re = re.compile(rf"^\s*\.\.\s+_?{re.escape(command_name)}\s*:", re.IGNORECASE)
    if any(anchor_re.search(line) for line in lines):
        score += 70
        reasons.append("exact_anchor")

    command_call_re = re.compile(rf"\b{re.escape(command_name)}\s*\(", re.IGNORECASE)
    if any(command_call_re.search(line) for line in lines):
        score += 25
        reasons.append("command_call_text")

    doc_ref_re = re.compile(rf"`{re.escape(command_name)}`|:doc:`[^`]*{re.escape(command_name)}", re.IGNORECASE)
    if any(doc_ref_re.search(line) for line in lines):
        score += 15
        reasons.append("command_reference_text")

    return score, reasons


def extract_match(path: Path, docs_root: Path, command_name: str, score: int, reasons: list[str]) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    sections = extract_named_sections(lines)
    directive = extract_function_directive_details(lines)
    literal_blocks = extract_literal_blocks_near_command(lines, command_name)
    syntax_blocks = []
    if directive["syntax"]:
        syntax_blocks.extend(directive["syntax"])
    elif sections.get("syntax_blocks"):
        syntax_blocks.append(sections["syntax_blocks"])
    syntax_blocks = [block for idx, block in enumerate(syntax_blocks) if block and block not in syntax_blocks[:idx]]

    inputs_section = sections.get("inputs_section")
    outputs_section = sections.get("outputs_section")
    if not inputs_section and directive["params"]:
        inputs_section = compact_snippet("\n".join(directive["params"]))
    if not outputs_section and directive["returns"]:
        outputs_section = compact_snippet("\n".join(directive["returns"]))
    example_blocks = [block for block in literal_blocks if not block.strip().startswith(".. function::")]

    unresolved = []
    if not syntax_blocks:
        unresolved.append("verified syntax not found")
    if not inputs_section:
        unresolved.append("inputs/parameters section not found")
    if not outputs_section:
        unresolved.append("outputs/returns section not found")
    if not sections.get("examples"):
        unresolved.append("examples section not found")

    rel_path = path.resolve()
    try:
        rel_path = path.resolve().relative_to(docs_root.resolve())
    except ValueError:
        pass

    return {
        "file_path": str(rel_path).replace("\\", "/"),
        "source_type": "official_local_rst",
        "match_reason": reasons,
        "heading": first_heading(lines),
        "syntax_blocks": syntax_blocks,
        "inputs_section": inputs_section,
        "outputs_section": outputs_section,
        "examples": compact_snippet("\n\n".join(example_blocks)) if example_blocks else sections.get("examples"),
        "notes": sections.get("notes"),
        "confidence": min(score / 200, 1.0),
        "unresolved_questions": unresolved,
    }


def lookup(command_name: str, docs_root: Path, max_results: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "command_name": command_name,
        "docs_root": str(docs_root),
        "matches": [],
        "best_match": None,
        "status": "not_found",
        "confidence": 0.0,
        "unresolved_questions": [],
    }

    if not docs_root.exists() or not docs_root.is_dir():
        result["status"] = "error"
        result["unresolved_questions"] = ["docs_root does not exist or is not a directory"]
        return result

    candidates: list[tuple[int, Path, list[str]]] = []

    exact_name = f"{command_name}.rst"
    exact_paths = []
    direct_path = docs_root / exact_name
    if direct_path.exists():
        exact_paths.append(direct_path)
    else:
        exact_paths = [path for path in docs_root.rglob(exact_name)]

    search_paths = exact_paths if exact_paths else docs_root.rglob("*.rst")

    for path in search_paths:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        score, reasons = score_file(path, lines, command_name)
        if score > 0:
            candidates.append((score, path, reasons))

    candidates.sort(key=lambda item: (-item[0], str(item[1]).lower()))
    selected = candidates[:max_results]
    matches = [extract_match(path, docs_root, command_name, score, reasons) for score, path, reasons in selected]
    result["matches"] = matches

    if not matches:
        result["unresolved_questions"] = ["command-specific docs not found"]
        return result

    best_score = selected[0][0]
    second_score = selected[1][0] if len(selected) > 1 else 0
    best_match = matches[0]
    result["best_match"] = best_match
    result["confidence"] = best_match["confidence"]
    result["unresolved_questions"] = best_match["unresolved_questions"]

    if len(selected) > 1 and best_score - second_score < 25:
        result["status"] = "ambiguous"
        result["unresolved_questions"] = [
            "multiple plausible docs matches found",
            *best_match["unresolved_questions"],
        ]
    else:
        result["status"] = "found"

    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Lookup GAUSS command docs in local official .rst files.")
    parser.add_argument("command_name", help="GAUSS command or procedure name to look up.")
    parser.add_argument("--docs-root", required=True, help="Local root of official GAUSS documentation.")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum number of matches to return.")
    parser.add_argument(
        "--redact-docs-root",
        action="store_true",
        help="Replace docs_root in JSON output with a placeholder for shareable examples.",
    )
    args = parser.parse_args(argv)

    max_results = max(1, args.max_results)
    data = lookup(args.command_name, Path(args.docs_root), max_results)
    if args.redact_docs_root:
        data["docs_root"] = "<local official GAUSS docs root>"
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0 if data["status"] != "error" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
