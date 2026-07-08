"""Check consistency across benchmark prompts, benchmark coverage, the run index, and run files.

This script reuses the markdown files already maintained by the manual evaluation
workflow (evaluations/benchmark-prompts.md, evaluations/benchmark-coverage.md,
evaluations/runs/INDEX.md, evaluations/runs/*.md) as its only inputs. It does not
introduce a new metadata format, execute anything, require network access, or
replace the manual-evaluation workflow itself -- it only checks that the four
files stay consistent with each other.

It intentionally does not validate GAUSS syntax, evidence content, or response
quality -- that is the job of evaluations/scoring.md and manual review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

KNOWN_STATUSES = {"Not Run", "Passed", "Failed", "Blocked", "Accepted Exception"}
RUN_FILE_FIELDS = ("Prompt ID", "Prompt Category", "Overall Score", "Decision")

PROMPT_HEADING_RE = re.compile(r"^###\s*Prompt\s+(\d+\.\d+):", re.MULTILINE)
PROMPT_ID_RE = re.compile(r"^\d+\.\d+$")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def split_table_row(line: str) -> list[str] | None:
    line = line.strip()
    if not line.startswith("|"):
        return None
    cells = line.split("|")[1:-1] if line.endswith("|") else line.split("|")[1:]
    return [c.strip() for c in cells]


def extract_benchmark_prompt_ids(text: str) -> list[str]:
    return PROMPT_HEADING_RE.findall(text)


def extract_coverage_rows(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        cells = split_table_row(line)
        if not cells or len(cells) < 4:
            continue
        prompt_id = cells[0].strip()
        if not PROMPT_ID_RE.match(prompt_id):
            continue  # header/separator/non-data row
        status = cells[3].strip()
        latest_run_cell = cells[4].strip() if len(cells) > 4 else ""
        run_file = None
        link = LINK_RE.search(latest_run_cell)
        if link:
            run_file = Path(link.group(2)).name
        rows.append(
            {
                "prompt_id": prompt_id,
                "category": cells[1].strip() if len(cells) > 1 else "",
                "name": cells[2].strip() if len(cells) > 2 else "",
                "status": status,
                "run_file": run_file,
                "raw_latest_run": latest_run_cell,
                "score": cells[5].strip() if len(cells) > 5 else "",
                "notes": cells[6].strip() if len(cells) > 6 else "",
            }
        )
    return rows


def extract_index_entries(text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line in text.splitlines():
        cells = split_table_row(line)
        if not cells or len(cells) < 3:
            continue
        link = LINK_RE.search(cells[0])
        if not link:
            continue  # header/separator row
        run_file = Path(link.group(2)).name
        prompt_id = cells[2].strip() if len(cells) > 2 else ""
        if not PROMPT_ID_RE.match(prompt_id):
            continue
        entries.append({"run_file": run_file, "prompt_id": prompt_id})
    return entries


def find_all_linked_run_files(text: str) -> set[str]:
    files: set[str] = set()
    for match in LINK_RE.finditer(text):
        target = match.group(2)
        if target.endswith(".md"):
            files.add(Path(target).name)
    return files


def parse_run_file_fields(text: str) -> dict[str, str | None]:
    fields: dict[str, str | None] = {}
    for key in RUN_FILE_FIELDS:
        m = re.search(rf"^{re.escape(key)}:\s*(.*)$", text, re.MULTILINE)
        fields[key] = m.group(1).strip() if m and m.group(1).strip() else None
    return fields


def check(
    prompts_path: Path,
    coverage_path: Path,
    index_path: Path,
    runs_dir: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    prompts_text = read_text(prompts_path)
    coverage_text = read_text(coverage_path)
    index_text = read_text(index_path)

    if prompts_text is None:
        errors.append(f"Missing file: {prompts_path}")
    if coverage_text is None:
        errors.append(f"Missing file: {coverage_path}")
    if index_text is None:
        errors.append(f"Missing file: {index_path}")

    if prompts_text is None or coverage_text is None or index_text is None:
        return {
            "prompt_id_count": 0,
            "coverage_row_count": 0,
            "run_files_referenced": 0,
            "index_entry_count": 0,
            "errors": errors,
            "warnings": warnings,
            "overall_pass": False,
        }

    prompt_ids = extract_benchmark_prompt_ids(prompts_text)
    coverage_rows = extract_coverage_rows(coverage_text)
    index_entries = extract_index_entries(index_text)

    coverage_by_id: dict[str, list[dict[str, Any]]] = {}
    for row in coverage_rows:
        coverage_by_id.setdefault(row["prompt_id"], []).append(row)

    # Check 1: every benchmark prompt ID has a coverage row.
    for pid in prompt_ids:
        if pid not in coverage_by_id:
            errors.append(f"Prompt {pid} in benchmark-prompts.md has no row in benchmark-coverage.md.")

    # Orphaned coverage rows: a coverage row for a prompt ID no longer in benchmark-prompts.md.
    prompt_id_set = set(prompt_ids)
    for pid in coverage_by_id:
        if pid not in prompt_id_set:
            warnings.append(f"Coverage row for {pid} has no matching prompt heading in benchmark-prompts.md.")

    # Check 6a: duplicate prompt IDs in benchmark-coverage.md.
    for pid, rows in coverage_by_id.items():
        if len(rows) > 1:
            errors.append(f"Duplicate coverage rows for Prompt {pid} ({len(rows)} rows found).")

    run_file_to_prompt_ids: dict[str, list[str]] = {}
    for row in coverage_rows:
        # Check 2: recognized status values.
        if row["status"] not in KNOWN_STATUSES:
            errors.append(
                f"Prompt {row['prompt_id']}: unrecognized coverage status {row['status']!r} "
                f"(expected one of {sorted(KNOWN_STATUSES)})."
            )

        # Check 3: Passed/Failed rows must reference an existing run file.
        if row["status"] in ("Passed", "Failed"):
            if row["run_file"] is None:
                errors.append(
                    f"Prompt {row['prompt_id']} is {row['status']!r} but its Latest Run column "
                    f"has no run-file link ({row['raw_latest_run']!r})."
                )
            else:
                run_path = runs_dir / row["run_file"]
                if not run_path.is_file():
                    errors.append(
                        f"Prompt {row['prompt_id']} references run file {row['run_file']}, "
                        "which does not exist under evaluations/runs/."
                    )
                run_file_to_prompt_ids.setdefault(row["run_file"], []).append(row["prompt_id"])

    # Check 6b: duplicate run-file references across coverage rows.
    for run_file, pids in run_file_to_prompt_ids.items():
        if len(pids) > 1:
            errors.append(
                f"Run file {run_file} is referenced by multiple coverage rows: {', '.join(sorted(set(pids)))}."
            )

    # Check 4: run-file metadata fields, for every run file coverage actually references.
    referenced_run_files = set(run_file_to_prompt_ids.keys())
    run_file_fields: dict[str, dict[str, str | None]] = {}
    for run_file in sorted(referenced_run_files):
        run_path = runs_dir / run_file
        run_text = read_text(run_path)
        if run_text is None:
            continue  # already reported as missing above
        fields = parse_run_file_fields(run_text)
        run_file_fields[run_file] = fields
        missing = [key for key in RUN_FILE_FIELDS if not fields.get(key)]
        if missing:
            errors.append(f"Run file {run_file} is missing required field(s): {', '.join(missing)}.")

    # Check 5: every referenced run file appears in INDEX.md; every INDEX.md entry exists.
    index_by_file: dict[str, list[str]] = {}
    for entry in index_entries:
        index_by_file.setdefault(entry["run_file"], []).append(entry["prompt_id"])

    for run_file in sorted(referenced_run_files):
        if run_file not in index_by_file:
            errors.append(f"Run file {run_file} is referenced by benchmark-coverage.md but missing from runs/INDEX.md.")

    for entry in index_entries:
        run_path = runs_dir / entry["run_file"]
        if not run_path.is_file():
            errors.append(f"runs/INDEX.md references {entry['run_file']}, which does not exist.")

    # Cross-check: INDEX.md's recorded Prompt ID vs. the run file's own "Prompt ID:" field.
    # Both are authored together at evaluation time, so a mismatch here is a real error, not
    # a documented historical exception.
    for entry in index_entries:
        run_file = entry["run_file"]
        run_path = runs_dir / run_file
        run_text = read_text(run_path)
        if run_text is None:
            continue
        fields = run_file_fields.get(run_file) or parse_run_file_fields(run_text)
        own_prompt_id = fields.get("Prompt ID")
        if own_prompt_id and own_prompt_id != entry["prompt_id"]:
            errors.append(
                f"runs/INDEX.md lists {run_file} under Prompt ID {entry['prompt_id']}, "
                f"but the run file itself states Prompt ID {own_prompt_id}."
            )

    # Cross-check: benchmark-coverage.md's row Prompt ID vs. the linked run file's own
    # "Prompt ID:" field. Several early runs predate stable Prompt ID assignment and are
    # deliberately linked from a coverage row with a different ID than the run file itself
    # records (documented in benchmark-coverage.md's own notes and its "Completed Runs Not
    # Directly Covered By Current Stable Prompts" section). Treat this as a warning, not a
    # hard error, so known historical mismatches do not fail the default run; --strict
    # promotes it like any other warning.
    for row in coverage_rows:
        if row["run_file"] is None:
            continue
        fields = run_file_fields.get(row["run_file"])
        if fields is None:
            continue
        own_prompt_id = fields.get("Prompt ID")
        if own_prompt_id and own_prompt_id != row["prompt_id"]:
            warnings.append(
                f"benchmark-coverage.md links Prompt {row['prompt_id']} to {row['run_file']}, "
                f"but that run file states Prompt ID {own_prompt_id}. If this is a documented "
                "historical mismatch (see benchmark-coverage.md's notes for this row), no action "
                "is needed; otherwise, verify the correct run file is linked."
            )

    # Check 7a: run files on disk not referenced anywhere (coverage.md or INDEX.md).
    referenced_anywhere = find_all_linked_run_files(coverage_text) | find_all_linked_run_files(index_text)
    if runs_dir.is_dir():
        for run_path in sorted(runs_dir.glob("*.md")):
            if run_path.name in ("INDEX.md", "README.md"):
                continue  # tracking/documentation files, not evaluation run files
            if run_path.name not in referenced_anywhere:
                warnings.append(
                    f"Run file {run_path.name} exists under evaluations/runs/ but is not referenced "
                    "by benchmark-coverage.md or runs/INDEX.md."
                )

    # Check 7b: Not Run prompts in the current (highest-numbered) active category.
    def category_num(pid: str) -> int:
        return int(pid.split(".")[0])

    if prompt_ids:
        current_category = max(category_num(pid) for pid in prompt_ids)
        for row in coverage_rows:
            if category_num(row["prompt_id"]) == current_category and row["status"] == "Not Run":
                warnings.append(
                    f"Prompt {row['prompt_id']} ({row['category']}) is Not Run and belongs to the "
                    f"current active category ({current_category}.x)."
                )

    return {
        "prompt_id_count": len(prompt_ids),
        "coverage_row_count": len(coverage_rows),
        "run_files_referenced": len(referenced_run_files),
        "index_entry_count": len(index_entries),
        "errors": errors,
        "warnings": warnings,
        "overall_pass": not errors,
    }


def print_human(result: dict[str, Any], strict: bool) -> None:
    print(f"Benchmark prompt IDs found: {result['prompt_id_count']}")
    print(f"Coverage rows found:        {result['coverage_row_count']}")
    print(f"Run files referenced:       {result['run_files_referenced']}")
    print(f"Run index entries checked:  {result['index_entry_count']}")
    print()

    if result["errors"]:
        print(f"Errors ({len(result['errors'])}):")
        for msg in result["errors"]:
            print(f"  - {msg}")
    else:
        print("Errors: none")

    print()
    if result["warnings"]:
        print(f"Warnings ({len(result['warnings'])}):")
        for msg in result["warnings"]:
            print(f"  - {msg}")
    else:
        print("Warnings: none")

    print()
    overall_pass = result["overall_pass"] and not (strict and result["warnings"])
    if strict and result["warnings"] and not result["errors"]:
        print("Strict mode: warnings promoted to failures.")
    print(f"Overall: {'PASS' if overall_pass else 'FAIL'}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check that evaluations/benchmark-prompts.md, evaluations/benchmark-coverage.md, "
            "evaluations/runs/INDEX.md, and evaluations/runs/*.md stay consistent with each other."
        )
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary instead of human-readable output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = repo_root()
    prompts_path = root / "evaluations" / "benchmark-prompts.md"
    coverage_path = root / "evaluations" / "benchmark-coverage.md"
    index_path = root / "evaluations" / "runs" / "INDEX.md"
    runs_dir = root / "evaluations" / "runs"

    result = check(prompts_path, coverage_path, index_path, runs_dir)
    result["strict"] = args.strict
    overall_pass = result["overall_pass"] and not (args.strict and result["warnings"])
    result["overall_pass"] = overall_pass

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human(result, args.strict)

    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
