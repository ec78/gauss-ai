"""Tests for `gauss_installed_libraries` (v0.92.0, planning
v0.92-installed-libraries.md): reading a GAUSS installation's library search
from its `gauss.cfg`, resolving `library <name>;` the way GAUSS does, and
attributing documentation pages to packages.

Run with:

    python scripts/test_gauss_installed_libraries.py

Fully synthetic: every test builds a fake GAUSS tree and a fake docs folder
in a temporary directory, modelled on the real shapes measured on GAUSS
26.1.4 (planning v0.92 §2; spot checks lb01-lb20). No test reads a real
GAUSS installation or a real documentation checkout, launches GAUSS, or
touches the network.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_installed_libraries as libraries_mod  # noqa: E402

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


_CFG = (
    "# a comment line\n"
    "PACKAGEDIR = $(GAUSSDIR)\\pkgs\n"
    "lib_path = $(GAUSSDIR)\\lib\n"
    "extra_lib_path = $(PACKAGEDIR)\\*\\lib\n"
)


def _index(*entries: str, header: str = "/*\n** fixture index\n*/\n\nsrc/file.src\n") -> str:
    return header + "".join(f"    {entry}\n" for entry in entries)


def build_fake_gauss(root: Path, *, cfg: str = _CFG) -> Path:
    """A fake installation shaped like `C:\\gauss26` (planning v0.92 §2.1-2.2):
    - `pkgs/alpha`: a package with a symbol index (like `gml`);
    - `pkgs/aardvark/lib/beta.lcg`: an alias that SHADOWS `pkgs/beta`'s own
      index, because `aardvark` sorts first (like `timeseries`'s `tsmt.lcg`);
    - `pkgs/gamma`: a paths-only index (like `timeseries.lcg`);
    - `pkgs/delta`: a package with no pages of its own (like `qardl`).
    Returns the fake executable's path."""
    gauss = root / "gauss"
    (gauss / "lib").mkdir(parents=True)
    (gauss / "tgauss.exe").write_bytes(b"")
    (gauss / "gauss.cfg").write_text(cfg, encoding="utf-8")
    (gauss / "lib" / "gauss.lcg").write_text(_index("gcore : proc : 1"), encoding="utf-8")
    (gauss / "lib" / "user.lcg").write_text("/*\n** user.lcg -- user library\n*/\n", encoding="utf-8")
    # Like `lib/pgraph.lcg`: documented, but not an installed package.
    (gauss / "lib" / "oldgfx.lcg").write_text(_index("gdraw : proc : 4"), encoding="utf-8")
    packages = {
        ("alpha", "alpha"): _index("pfit : proc : 10", "pPredict : proc : 40", "struct pModel : definition : 3"),
        ("aardvark", "beta"): _index("aliased : proc : 5"),
        ("beta", "beta"): _index("legacyonly : proc : 7"),
        ("gamma", "gamma"): "/*\n** paths only\n*/\n\nC:/gauss/pkgs/gamma/src/g.src\n",
        ("delta", "delta"): _index("dcoll : proc : 2"),
    }
    for (package, name), text in packages.items():
        (gauss / "pkgs" / package / "lib").mkdir(parents=True, exist_ok=True)
        (gauss / "pkgs" / package / "lib" / f"{name}.lcg").write_text(text, encoding="utf-8")
    return gauss / "tgauss.exe"


def build_fake_docs(root: Path) -> Path:
    """Pages attributed by their own `library` line (top level, like GML),
    by folder majority (like `tsmt/`), a core page, a folder tie, and a core
    page colliding with a package procedure name (like `lagn`/`coint`)."""
    docs = root / "docs"
    pages = {
        "meanc.rst": "meanc\n=====\n\nExamples\n--------\n\n::\n\n    print meanc(x);\n",
        "pfit.rst": "pfit\n====\n\nExamples\n--------\n\n::\n\n    library alpha;\n    m = pfit(y, x);\n",
        "beta/aliased.rst": "aliased\n=======\n\n::\n\n    library beta;\n    aliased(1);\n",
        "beta/legacyonly.rst": "legacyonly\n==========\n\nNo example here.\n",
        "dcoll.rst": "dcoll\n=====\n\nA core page with no library line.\n",
        "tie/one.rst": "one\n===\n\n::\n\n    library left;\n",
        "tie/two.rst": "two\n===\n\n::\n\n    library right;\n",
        "tie/three.rst": "three\n=====\n\nno line\n",
        "multi.rst": "multi\n=====\n\n::\n\n    library alpha, beta;\n",
        # Like `xy.rst`: the library named only in a "Library" section.
        "gdraw.rst": "gdraw\n=====\n\nPurpose\n-------\nDraws.\n\nLibrary\n-------\n\noldgfx\n\nFormat\n------\n",
    }
    for name, text in pages.items():
        path = docs / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return docs


def test_01_search_order_is_extra_lib_path_then_lib_path_alphabetically() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        exe = build_fake_gauss(Path(tmp))
        installation = libraries_mod.load_installation(str(exe))
        check("01: an installation is read", installation is not None)
        names = [Path(p).parent.name if Path(p).name == "lib" else Path(p).name for p in installation.search_path]
        check("01: packages alphabetically, then lib", names == ["aardvark", "alpha", "beta", "delta", "gamma", "gauss"])


def test_02_the_first_index_found_wins_shadowing_included() -> None:
    """lb01/lb02: `library tsmt;` loads `pkgs\\timeseries\\lib\\tsmt.lcg`,
    so a symbol only in `pkgs\\tsmt\\lib\\tsmt.lcg` is G0025."""
    with tempfile.TemporaryDirectory() as tmp:
        installation = libraries_mod.load_installation(str(build_fake_gauss(Path(tmp))))
        beta = installation.resolve("beta")
        check("02: beta resolves to the alias in aardvark", beta is not None and beta.package_dir == "aardvark")
        check("02: ...which lists the alias's symbol", "aliased" in beta.symbols)
        check("02: ...and not the shadowed index's", "legacyonly" not in beta.symbols)


def test_03_names_are_case_insensitive_and_symbols_lower_cased() -> None:
    """lb17: `library GML;` loads `gml.lcg`."""
    with tempfile.TemporaryDirectory() as tmp:
        installation = libraries_mod.load_installation(str(build_fake_gauss(Path(tmp))))
        alpha = installation.resolve("ALPHA")
        check("03: ALPHA resolves", alpha is not None and alpha.name == "alpha")
        check("03: symbols, structures included, lower-cased", alpha.symbols == {"pfit", "ppredict", "pmodel"})
        check("03: a SHA-256 of the file", len(alpha.sha256) == 64)


def test_04_a_paths_only_index_defines_nothing() -> None:
    """lb05/lb10: after `library timeseries;`, `garchFit` is G0025."""
    with tempfile.TemporaryDirectory() as tmp:
        installation = libraries_mod.load_installation(str(build_fake_gauss(Path(tmp))))
        gamma = installation.resolve("gamma")
        check("04: gamma resolves", gamma is not None)
        check("04: ...but lists no symbols", not gamma.lists_symbols)


def test_05_always_loaded_and_reachable_names() -> None:
    """lb19: `user.lcg` and `gauss.lcg` are always active."""
    with tempfile.TemporaryDirectory() as tmp:
        installation = libraries_mod.load_installation(str(build_fake_gauss(Path(tmp))))
        check("05: user and gauss always loaded", [i.name for i in installation.always_loaded()] == ["user", "gauss"])
        check("05: gauss.lcg's symbols", "gcore" in installation.always_loaded()[1].symbols)
        check("05: each reachable name once, first-found order",
              installation.reachable_library_names() == ("beta", "alpha", "delta", "gamma", "gauss", "oldgfx", "user"))
        check("05: an unknown name does not resolve", installation.resolve("nosuchlib") is None)


def test_06_no_evidence_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        check("06: no executable", libraries_mod.load_installation(None) is None)
        bare = Path(tmp) / "bare"
        bare.mkdir()
        (bare / "tgauss.exe").write_bytes(b"")
        check("06: no gauss.cfg", libraries_mod.load_installation(str(bare / "tgauss.exe")) is None)
        odd = build_fake_gauss(Path(tmp) / "odd", cfg="lib_path = $(SOMEWHERE)\\lib\n")
        check("06: an unknown variable", libraries_mod.load_installation(str(odd)) is None)
        nolib = build_fake_gauss(Path(tmp) / "nolib", cfg="extra_lib_path = $(GAUSSDIR)\\lib\n")
        check("06: no lib_path", libraries_mod.load_installation(str(nolib)) is None)


def test_07_docs_attribution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        attribution = libraries_mod.docs_attribution(str(build_fake_docs(Path(tmp))))
        check("07: a top-level page by its own library line", attribution.libraries_for("pfit") == {"alpha"})
        check("07: case-insensitive lookup", attribution.libraries_for("PFIT") == {"alpha"})
        check("07: a folder page by the folder's library", attribution.libraries_for("legacyonly") == {"beta"})
        check("07: a core page is never a package's", attribution.libraries_for("meanc") == frozenset())
        check("07: a page with no line in a tied folder is unattributed",
              attribution.libraries_for("three") == frozenset())
        check("07: several libraries on one page", attribution.libraries_for("multi") == {"alpha", "beta"})
        check("07: a Library section attributes the page (xy.rst, lb21)",
              attribution.libraries_for("gdraw") == {"oldgfx"})
        check("07: no docs root, no attribution", libraries_mod.docs_attribution(None).by_symbol == {})


def test_08_a_core_page_wins_over_a_package_page_of_the_same_name() -> None:
    """Planning v0.92 §8.1: `coint` defines `lagn`, which has a core page."""
    with tempfile.TemporaryDirectory() as tmp:
        docs = build_fake_docs(Path(tmp))
        (docs / "beta" / "dcoll.rst").write_text("dcoll\n=====\n\n::\n\n    library beta;\n", encoding="utf-8")
        attribution = libraries_mod.docs_attribution(str(docs))
        check("08: dcoll stays core", attribution.libraries_for("dcoll") == frozenset())


def test_09_which_libraries_are_documented() -> None:
    """Decision 1(b) as applied (§8.1): a page of the library's own, or of
    the package directory holding its index (the `tsmt` alias)."""
    with tempfile.TemporaryDirectory() as tmp:
        installation = libraries_mod.load_installation(str(build_fake_gauss(Path(tmp))))
        attribution = libraries_mod.docs_attribution(str(build_fake_docs(Path(tmp))))
        report = libraries_mod.report_installed_libraries(installation, attribution)
        check("09: alpha and beta are usable", report.allowed == ("beta", "alpha"))
        check("09: delta (no pages), gamma (paths only), oldgfx (not a package, like pgraph) are not",
              report.not_allowed == ("delta", "gamma", "oldgfx"))
        check("09: no installation, no report", libraries_mod.report_installed_libraries(None, attribution) is None)


def test_10_the_index_is_read_fresh_every_time() -> None:
    """Planning v0.92 §3.5: prepare must see an index changed after
    validation."""
    with tempfile.TemporaryDirectory() as tmp:
        exe = build_fake_gauss(Path(tmp))
        installation = libraries_mod.load_installation(str(exe))
        before = installation.resolve("alpha")
        index = Path(tmp) / "gauss" / "pkgs" / "alpha" / "lib" / "alpha.lcg"
        index.write_text(index.read_text(encoding="utf-8") + "    pnew : proc : 99\n", encoding="utf-8")
        after = installation.resolve("alpha")
        check("10: the new symbol is seen", "pnew" in after.symbols and "pnew" not in before.symbols)
        check("10: and the digest changes", after.sha256 != before.sha256)


def test_12_v0921_all_indexes_include_shadowed_ones() -> None:
    """v0.92.1 (live finding 83.7): the shadowed index is the only one that
    defines some structure types, so it must be visible to the check."""
    with tempfile.TemporaryDirectory() as tmp:
        installation = libraries_mod.load_installation(str(build_fake_gauss(Path(tmp))))
        paths = [Path(i.path).parent.parent.name + "/" + Path(i.path).name for i in installation.all_indexes()]
        check("12: both beta indexes are listed, the alias first", paths.index("aardvark/beta.lcg") < paths.index("beta/beta.lcg"))
        check("12: the shadowed one lists its own symbols",
              any("legacyonly" in i.symbols for i in installation.all_indexes()))


def test_11_module_reads_only() -> None:
    """The module never launches anything, writes anything or opens a
    network connection."""
    source = Path(libraries_mod.__file__).read_text(encoding="utf-8")
    for banned in ("subprocess", "socket", "urllib", "http.client", "os.system", "write_text", "write_bytes",
                   "open(", "shutil"):
        check(f"11: no {banned}", banned not in source)


def run_tests() -> int:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
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
