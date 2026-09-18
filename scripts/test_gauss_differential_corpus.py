"""Tests for the v0.77.0 differential syntax-validation corpus: the loader
(`gauss_differential_harness.load_jsonl`) against tiny synthetic fixtures,
plus minimum-size/provenance checks against the real, committed corpus files
under `evaluations/differential_corpus/` (built once, offline, by
`build_differential_corpus.py`).

Run with:

    python scripts/test_gauss_differential_corpus.py

Fully synthetic and network-free where it matters: the synthetic-fixture
tests below never touch a real documentation checkout or real GAUSS. The
"real committed corpus" tests read only STATIC files already checked into
this repository -- not a live docs_root, not tgauss.exe, not a model
provider -- so they remain safe to run in any environment/CI.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_differential_harness as harness  # noqa: E402

_REPO_ROOT = _SCRIPT_DIR.parent
_CORPUS_DIR = _REPO_ROOT / "evaluations" / "differential_corpus"

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


# ---------------------------------------------------------------------------
# Synthetic fixtures: one item per origin, provenance round-trips
# ---------------------------------------------------------------------------


def _write(tmp_dir: Path, name: str, items: list[dict]) -> Path:
    path = tmp_dir / name
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item))
            handle.write("\n")
    return path


def test_01_docs_valid_item_round_trips() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        item = {
            "id": "A-001", "origin": "docs_valid", "snippet": "x = 1;\n", "expected_class": "valid",
            "provenance": {"source_document": "fixture.rst", "section": "Examples", "line_start": 1, "line_end": 1},
        }
        path = _write(Path(tmp), "docs_valid.jsonl", [item])
        loaded = harness.load_jsonl(path)
        check("one item", len(loaded) == 1)
        check("origin preserved", loaded[0]["origin"] == "docs_valid")
        check("expected_class preserved", loaded[0]["expected_class"] == "valid")
        check("source_document provenance preserved", loaded[0]["provenance"]["source_document"] == "fixture.rst")


def test_02_mutation_item_round_trips() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        item = {
            "id": "B-001", "origin": "mutation", "snippet": "x = -1 0;\n", "expected_class": None,
            "provenance": {
                "seed_id": "A-001", "original_valid_snippet": "x = { -1 0 };\n",
                "mutation_operator": "bare_multi_token_literal", "mutation_description": "strips braces",
            },
        }
        path = _write(Path(tmp), "mutations.jsonl", [item])
        loaded = harness.load_jsonl(path)
        check("origin preserved", loaded[0]["origin"] == "mutation")
        check("expected_class is null (unknown a priori)", loaded[0]["expected_class"] is None)
        check("mutation_operator provenance preserved", loaded[0]["provenance"]["mutation_operator"] == "bare_multi_token_literal")
        check("original_valid_snippet provenance preserved", "original_valid_snippet" in loaded[0]["provenance"])


def test_03_model_output_item_round_trips() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        item = {
            "id": "C-001", "origin": "model_output_historical", "snippet": "y = meanc(x);\n", "expected_class": None,
            "provenance": {
                "source_run": "2026-01-01-fixture-run-001.md", "prompt_id": "61.1",
                "generation_policy": "full", "eligibility_at_time": "eligible_for_validation",
            },
        }
        path = _write(Path(tmp), "model_output_historical.jsonl", [item])
        loaded = harness.load_jsonl(path)
        check("origin preserved", loaded[0]["origin"] == "model_output_historical")
        check("source_run provenance preserved", loaded[0]["provenance"]["source_run"] == "2026-01-01-fixture-run-001.md")
        check("prompt_id provenance preserved", loaded[0]["provenance"]["prompt_id"] == "61.1")


def test_04_load_full_corpus_merges_all_families() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        _write(tmp_dir, "docs_valid.jsonl", [{"id": "A-001", "origin": "docs_valid", "snippet": "x = 1;"}])
        _write(tmp_dir, "mutations.jsonl", [{"id": "B-001", "origin": "mutation", "snippet": "x = ;"}])
        _write(tmp_dir, "model_output_historical.jsonl", [{"id": "C-001", "origin": "model_output_historical", "snippet": "y = f(x);"}])
        # model_output_fresh.jsonl deliberately absent -- must not error.
        items = harness.load_full_corpus(tmp_dir)
        check("three items merged", len(items) == 3)
        check("missing fresh-batch file tolerated", True)


# ---------------------------------------------------------------------------
# Real, committed corpus files: static repo content only
# ---------------------------------------------------------------------------


def test_05_docs_valid_corpus_meets_minimum_size() -> None:
    items = harness.load_jsonl(_CORPUS_DIR / "docs_valid.jsonl")
    check("at least 40 docs-valid snippets", len(items) >= 40)
    for item in items:
        check(f"{item['id']} has source_document provenance", "source_document" in item["provenance"])
        check(f"{item['id']} expected_class is valid", item["expected_class"] == "valid")


def test_06_mutation_corpus_meets_minimum_size() -> None:
    items = harness.load_jsonl(_CORPUS_DIR / "mutations.jsonl")
    check("at least 75 mutation snippets", len(items) >= 75)
    operators = {item["provenance"]["mutation_operator"] for item in items}
    check("at least 10 distinct mutation operators represented", len(operators) >= 10)
    for item in items:
        check(f"{item['id']} has original_valid_snippet provenance", "original_valid_snippet" in item["provenance"])


def test_07_model_output_historical_corpus_meets_minimum_size() -> None:
    items = harness.load_jsonl(_CORPUS_DIR / "model_output_historical.jsonl")
    check("at least 20 historical model-output snippets", len(items) >= 20)
    for item in items:
        check(f"{item['id']} has source_run provenance", "source_run" in item["provenance"])


def test_08_combined_corpus_meets_milestone_target() -> None:
    items = harness.load_full_corpus(_CORPUS_DIR)
    check("combined corpus has at least 150 items", len(items) >= 150)


def test_09_every_item_id_is_unique() -> None:
    items = harness.load_full_corpus(_CORPUS_DIR)
    ids = [item["id"] for item in items]
    check("no duplicate ids", len(ids) == len(set(ids)))


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
