"""Tests for `gauss_doc_concept_index.py` (v0.74.0).

Run with:

    python scripts/test_gauss_doc_concept_index.py

Uses a small, disposable, synthetic `.rst` fixture tree -- never this
machine's own real local GAUSS documentation checkout.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_doc_concept_index as index_mod  # noqa: E402

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


_MEANC_RST = """meanc
=====

.. function:: y = meanc(x)

Purpose
-------
Computes the mean of every column of a matrix.
"""

_INV_RST = """inv, invpd
==========

.. function:: xi = inv(x)
              xi = invpd(x)

Purpose
-------
inv returns the inverse of an invertible matrix. invpd returns the inverse of a symmetric, positive definite matrix.
"""

_CORRX_RST = """corrx
=====

.. function:: y = corrx(x)

Purpose
-------
Computes the correlation matrix of the columns of a dataset. See :func:`meanc` for column means.
"""

_LEGACY_STYLE_RST = """tscsmtControlCreate
===================

Format
------
tsc = tscsmtControlCreate( );

Purpose
-------
Sets the members of a tscsmtControl structure to default values.
"""

#: Heading and body text use ONLY words already in `_GENERIC_DOC_WORDS` (or
#: too short to match `_WORD_RE`) and there is no "Purpose" section at all --
#: this must yield zero usable keywords, not a fabricated entry.
_EMPTY_RST = """Output
======

This value is the output of the function.
"""


def _fixture_root(tmp: str) -> Path:
    root = Path(tmp) / "docs"
    root.mkdir()
    (root / "meanc.rst").write_text(_MEANC_RST, encoding="utf-8")
    (root / "invinvpd.rst").write_text(_INV_RST, encoding="utf-8")
    (root / "corrx.rst").write_text(_CORRX_RST, encoding="utf-8")
    (root / "tscsmtcontrolcreate.rst").write_text(_LEGACY_STYLE_RST, encoding="utf-8")
    (root / "orphan.rst").write_text(_EMPTY_RST, encoding="utf-8")
    return root


def test_01_build_index_derives_real_symbols_from_directive_syntax() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _fixture_root(tmp)
        index = index_mod.build_documentation_concept_index(root)
        symbols = {e.symbol for e in index.entries}
        check("meanc derived", "meanc" in symbols)
        check("inv derived (not the file's own stem invinvpd)", "inv" in symbols)
        check("invpd derived (not the file's own stem invinvpd)", "invpd" in symbols)
        check("corrx derived", "corrx" in symbols)


def test_02_legacy_format_style_symbol_derived_without_a_function_directive() -> None:
    """`tscsmtControlCreate` uses the older plain Format-heading style
    (`tsc = tscsmtControlCreate( );`), not a `.. function::` directive --
    the fallback raw-syntax-block parsing path must still find it."""
    with tempfile.TemporaryDirectory() as tmp:
        root = _fixture_root(tmp)
        index = index_mod.build_documentation_concept_index(root)
        symbols = {e.symbol for e in index.entries}
        check("tscsmtControlCreate derived from legacy Format-heading style", "tscsmtControlCreate" in symbols)


def test_03_provenance_source_is_traceable_to_a_real_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _fixture_root(tmp)
        index = index_mod.build_documentation_concept_index(root)
        for entry in index.entries:
            check(f"{entry.symbol} source file exists", (root / entry.source).exists())


def test_04_orphan_file_with_no_purpose_and_no_syntax_yields_no_keywords_but_no_crash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _fixture_root(tmp)
        index = index_mod.build_documentation_concept_index(root)
        symbols = {e.symbol for e in index.entries}
        check("orphan (no usable keywords) contributes no entry", "orphan" not in symbols)


def test_05_companions_captured_from_func_references() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _fixture_root(tmp)
        index = index_mod.build_documentation_concept_index(root)
        corrx_entries = [e for e in index.entries if e.symbol == "corrx"]
        check("corrx entry present", len(corrx_entries) == 1)
        check("meanc captured as a companion via :func:`meanc`", "meanc" in corrx_entries[0].companions)
        check("a symbol never lists itself as its own companion", "corrx" not in corrx_entries[0].companions)


def test_06_resolve_derived_concepts_finds_corrx_for_a_related_phrase() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _fixture_root(tmp)
        index = index_mod.build_documentation_concept_index(root)
        matches = index_mod.resolve_derived_concepts("the correlation of the columns in my dataset", index)
        symbols = {m.symbol for m in matches}
        check("corrx proposed as a candidate", symbols == {"corrx"})
        check("overlap keywords are real, non-empty evidence", len(matches[0].overlap_keywords) >= 2)


def test_07_single_shared_generic_word_alone_is_not_enough_overlap() -> None:
    """A phrase sharing only ONE keyword with an entry (below
    MIN_KEYWORD_OVERLAP) must not propose a candidate -- this is the whole
    point of requiring more than one shared token."""
    with tempfile.TemporaryDirectory() as tmp:
        root = _fixture_root(tmp)
        index = index_mod.build_documentation_concept_index(root)
        matches = index_mod.resolve_derived_concepts("tell me about columns please", index)
        check("no candidate proposed from a single generic shared word", matches == ())


def test_08_no_matching_documentation_yields_no_resolution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "docs"
        root.mkdir()
        (root / "meanc.rst").write_text(_MEANC_RST, encoding="utf-8")
        index = index_mod.build_documentation_concept_index(root)
        matches = index_mod.resolve_derived_concepts("panel regression on time series cross section data", index)
        check("no fabricated candidate when nothing real matches", matches == ())


def test_09_two_distinct_equally_scored_symbols_is_reported_as_multiple_matches() -> None:
    """Genuine ambiguity: two DIFFERENT real symbols tie for the highest
    keyword overlap. The caller (`gauss_conversation_engine.resolve_
    concepts`) is responsible for turning this into an AMBIGUOUS
    resolution; this module's own contract is just to return every
    top-scoring match honestly, never silently pick one."""
    tie_a = "twin_a\n======\n\n.. function:: y = twin_a(x)\n\nPurpose\n-------\nComputes a shared special quantity from a data table.\n"
    tie_b = "twin_b\n======\n\n.. function:: y = twin_b(x)\n\nPurpose\n-------\nComputes a shared special quantity from a data table.\n"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "docs"
        root.mkdir()
        (root / "twin_a.rst").write_text(tie_a, encoding="utf-8")
        (root / "twin_b.rst").write_text(tie_b, encoding="utf-8")
        index = index_mod.build_documentation_concept_index(root)
        matches = index_mod.resolve_derived_concepts("compute the shared special quantity from my table", index)
        symbols = {m.symbol for m in matches}
        check("both tied candidates returned", symbols == {"twin_a", "twin_b"})


def test_10_index_build_is_bounded_by_max_indexed_doc_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "docs"
        root.mkdir()
        original_max = index_mod.MAX_INDEXED_DOC_FILES
        index_mod.MAX_INDEXED_DOC_FILES = 2
        try:
            for i in range(5):
                (root / f"f{i}.rst").write_text(f"f{i}\n===\n\nPurpose\n-------\nComputes a special value {i}.\n", encoding="utf-8")
            index = index_mod.build_documentation_concept_index(root)
            check("scan bounded to MAX_INDEXED_DOC_FILES", index.files_scanned == 2)
            check("truncation disclosed, not silent", index.truncated is True)
        finally:
            index_mod.MAX_INDEXED_DOC_FILES = original_max


def test_11_cached_index_returns_the_same_object_for_an_unchanged_docs_root() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _fixture_root(tmp)
        index_mod._INDEX_CACHE.clear()
        first = index_mod.get_documentation_concept_index(root)
        second = index_mod.get_documentation_concept_index(root)
        check("cache returns the identical object, not a rebuild", first is second)


def test_12_no_execution_or_file_write_capability() -> None:
    source = Path(index_mod.__file__).read_text(encoding="utf-8")
    for token in ("write_text", "write_bytes", "os.system", "subprocess.", "eval(", "exec("):
        check(f"module source does not contain {token!r}", token not in source)


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
