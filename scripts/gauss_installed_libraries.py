"""v0.92.0 "Installed Libraries" (planning/v0.92-installed-libraries.md).

Read-only, deterministic knowledge of the GAUSS installation the user
configured: which library index `library <name>;` loads there, and which
symbols that index makes callable. Plus the docs-side half: which official
documentation pages belong to a package, so a package function is known as
one even when its page sits at the top level of the docs (GML).

Nothing here launches GAUSS, touches the network or writes a file. It reads
the executable's own `gauss.cfg`, the `.lcg` library index files that
configuration points at, and the `.rst` pages under `docs_root`. Every rule
below comes from a real `tgauss.exe -b` spot check (GAUSS 26.1.4,
2026-11-06, planning v0.92 §2, checks lb01-lb19); where GAUSS's behavior was
not measured, the code fails closed (no installation evidence) instead of
guessing.

Stdlib only, like the rest of the base CLI.
"""

from __future__ import annotations

import collections
import dataclasses
import functools
import glob
import hashlib
import os
import re
from pathlib import Path

#: The only `gauss.cfg` variables this module expands. GAUSS 26.1.4's own
#: `gauss.cfg` uses exactly these two in `lib_path`/`extra_lib_path`
#: (`$(GAUSSDIR)\lib`, `$(GAUSSDIR)\gaussplot\lib;$(PACKAGEDIR)\*\lib`). Any
#: other `$(...)` in those settings means the search order cannot be known
#: here, so the installation gives no evidence at all (fail closed).
_KNOWN_CFG_VARIABLES = ("GAUSSDIR", "PACKAGEDIR")
_CFG_VARIABLE_RE = re.compile(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)")

#: One symbol entry of an index: `    name    : kind : line`. Structures are
#: listed as `struct name : definition : line`. The kinds are every one seen
#: across this machine's 17 installed indexes (planning v0.92 §2.2); a line
#: of any other shape (headers, source-file lines, prose) is not an entry.
_INDEX_ENTRY_RE = re.compile(
    r"^\s+(?:struct\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(proc|fn|keyword|matrix|string|definition)\s*:",
    re.IGNORECASE,
)

#: A `library` line in a documentation page's own examples. Only bare names
#: count (`library gml;`, `library cmlmt, tsmt;`).
_DOC_LIBRARY_LINE_RE = re.compile(r"^\s*library\s+([A-Za-z_][\w ,]*?)\s*;", re.IGNORECASE | re.MULTILINE)

#: A page's own "Library" section (`xy.rst`: a "Library" heading, then
#: `pgraph`). Found in the v0.92.0 verdict diff (planning v0.92 §9): 38
#: top-level `pgraph` pages, 77 `tsmt/`, 47 `timeseries/` and 2 `bhatlib/`
#: pages name their library this way, so `xy(x, y);` without `library
#: pgraph;` was read as a core call and reached handoff_candidate, while
#: GAUSS 26.1.4 stops with G0025 (lb21).
_DOC_LIBRARY_SECTION_RE = re.compile(
    r"^Library[ \t]*\n[-=~^]+[ \t]*\n\s*([A-Za-z_][A-Za-z0-9_]*)[ \t]*$", re.MULTILINE,
)


@dataclasses.dataclass(frozen=True)
class LibraryIndex:
    """One resolved `.lcg` index file."""

    #: The name `library` was given, lower-cased (GAUSS names are
    #: case-insensitive: lb17 `library GML;` loads `gml.lcg`).
    name: str
    path: str
    sha256: str
    #: The `pkgs\\<dir>` directory holding the index, lower-cased, or `None`
    #: for an index outside the package directory (`lib\\pgraph.lcg`).
    #: `library tsmt;` resolves to `pkgs\\timeseries\\lib\\tsmt.lcg` (lb01), so
    #: its package directory is `timeseries`.
    package_dir: str | None
    #: Every symbol the index lists, lower-cased.
    symbols: frozenset[str]

    @property
    def lists_symbols(self) -> bool:
        """A paths-only index (`timeseries.lcg`: source file names, no
        entries) defines NOTHING in GAUSS 26.1.4: after `library
        timeseries;`, `garchFit` is G0025 and `struct garchResult` G0507
        (lb05, lb10)."""
        return bool(self.symbols)


@dataclasses.dataclass(frozen=True)
class Installation:
    """The library search of one GAUSS installation, read from its
    `gauss.cfg`. `search_path` is in GAUSS's own order, observed with
    `library;` (lb01): every `extra_lib_path` entry, then `lib_path`, each
    `*` expanded in case-insensitive alphabetical order. The first
    `<name>.lcg` found wins -- which is why `library tsmt;` loads the
    `timeseries` package's alias index and never `pkgs\\tsmt\\lib\\tsmt.lcg`
    (v0.91 §2.4's unexplained `adjRsq`/`chowfcst` G0025s)."""

    gauss_dir: str
    package_dir: str | None
    search_path: tuple[str, ...]

    def resolve(self, name: str) -> LibraryIndex | None:
        """Read fresh on every call (never cached), so a changed index is
        seen at `gauss_execution_prepare`'s re-check (planning v0.92 §3.5)."""
        return _resolve(self, name.lower())

    def always_loaded(self) -> tuple[LibraryIndex, ...]:
        """`user.lcg` and `gauss.lcg`, which GAUSS lists as active beside any
        named library (lb19)."""
        return tuple(index for index in (self.resolve("user"), self.resolve("gauss")) if index is not None)

    def reachable_library_names(self) -> tuple[str, ...]:
        """Every distinct `<name>` with a `<name>.lcg` on the search path, in
        first-found order -- what `library <name>;` could load here."""
        names: list[str] = []
        for directory in self.search_path:
            try:
                entries = sorted(os.listdir(directory), key=str.lower)
            except OSError:
                continue
            for entry in entries:
                stem, ext = os.path.splitext(entry)
                if ext.lower() == ".lcg" and stem.lower() not in names:
                    names.append(stem.lower())
        return tuple(names)


def _resolve(installation: Installation, name: str) -> LibraryIndex | None:
    for directory in installation.search_path:
        try:
            entries = os.listdir(directory)
        except OSError:
            continue
        for entry in entries:
            if entry.lower() == f"{name}.lcg":
                return _read_index(name, os.path.join(directory, entry), installation.package_dir)
    return None


def _read_index(name: str, path: str, package_root: str | None) -> LibraryIndex | None:
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    text = data.decode("utf-8", errors="replace")
    symbols = frozenset(m.group(1).lower() for m in map(_INDEX_ENTRY_RE.match, text.splitlines()) if m)
    package_dir: str | None = None
    if package_root is not None:
        try:
            relative = os.path.relpath(path, package_root)
        except ValueError:  # another drive on Windows
            relative = ""
        parts = Path(relative).parts
        if len(parts) >= 2 and parts[0] not in (os.pardir, os.curdir):
            package_dir = parts[0].lower()
    return LibraryIndex(
        name=name, path=path, sha256=hashlib.sha256(data).hexdigest(), package_dir=package_dir, symbols=symbols,
    )


def _cfg_setting(text: str, key: str) -> str | None:
    match = re.search(rf"^[ \t]*{re.escape(key)}[ \t]*=[ \t]*(.*?)[ \t]*$", text, re.MULTILINE | re.IGNORECASE)
    return match.group(1) if match else None


def load_installation(executable_path: str | None) -> Installation | None:
    """The installation of the configured `tgauss`/`gauss` executable, or
    `None` when there is no evidence: no executable configured, no
    `gauss.cfg` beside it, a setting missing, or a variable other than
    `$(GAUSSDIR)`/`$(PACKAGEDIR)`. `GAUSSDIR` is the executable's own
    directory, as for the GAUSS 26.1.4 install measured (`C:\\gauss26`)."""
    if not executable_path:
        return None
    gauss_dir = os.path.dirname(os.path.abspath(executable_path))
    try:
        cfg = Path(gauss_dir, "gauss.cfg").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    variables = {"GAUSSDIR": gauss_dir}
    package_setting = _cfg_setting(cfg, "PACKAGEDIR")
    if package_setting is not None:
        expanded = _expand(package_setting, variables)
        if expanded is None:
            return None
        variables["PACKAGEDIR"] = expanded
    lib_path = _cfg_setting(cfg, "lib_path")
    extra_lib_path = _cfg_setting(cfg, "extra_lib_path")
    if lib_path is None:
        return None
    search: list[str] = []
    for setting in (extra_lib_path or "", lib_path):
        expanded = _expand(setting, variables)
        if expanded is None:
            return None
        for part in expanded.split(";"):
            part = part.strip()
            if not part:
                continue
            if "*" in part:
                search.extend(sorted(glob.glob(part), key=str.lower))
            else:
                search.append(part)
    return Installation(
        gauss_dir=gauss_dir, package_dir=variables.get("PACKAGEDIR"), search_path=tuple(search),
    )


def _expand(value: str, variables: dict[str, str]) -> str | None:
    for name in _CFG_VARIABLE_RE.findall(value):
        if name.upper() not in variables:
            return None
    expanded = _CFG_VARIABLE_RE.sub(lambda m: variables[m.group(1).upper()], value)
    # The Windows `gauss.cfg` writes `\`; read either separator on any OS.
    return expanded.replace("\\", os.sep).replace("/", os.sep)


# ---------------------------------------------------------------------------
# The docs side: which pages belong to a package (planning v0.92 §8.1)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class DocsAttribution:
    """Which documented symbols are package functions, and of which
    libraries. A page is attributed to a library when its own examples load
    it (24 top-level GML pages say `library gml;`), or when it sits in a
    docs folder whose pages load that library most often (`mlmt/` ->
    `maxlikmt`, `timeseries/` -> `timeseries`, ...).

    `by_symbol` holds a symbol only when EVERY page named after it is
    attributed, so a symbol with a core page (`lagn.rst`, top level, no
    `library` line) is never a package function -- even if some installed
    package defines a procedure of that name (`coint`'s `lagn`)."""

    by_symbol: dict[str, frozenset[str]]

    def libraries_for(self, symbol: str) -> frozenset[str]:
        return self.by_symbol.get(symbol.lower(), frozenset())


def _page_libraries(text: str) -> frozenset[str]:
    names: set[str] = set()
    for match in _DOC_LIBRARY_LINE_RE.finditer(text):
        names.update(part.strip().lower() for part in match.group(1).split(",") if part.strip())
    names.update(match.group(1).lower() for match in _DOC_LIBRARY_SECTION_RE.finditer(text))
    return frozenset(names)


def docs_attribution(docs_root: str | None) -> DocsAttribution:
    """Deterministic over the `.rst` files under `docs_root`. Cached per
    root path and the root directory's modification time, so a `gauss-ai
    docs fetch` into the same root is seen by a long-running server."""
    if not docs_root:
        return DocsAttribution(by_symbol={})
    try:
        stamp = os.stat(docs_root).st_mtime_ns
    except OSError:
        return DocsAttribution(by_symbol={})
    return _docs_attribution_cached(os.path.abspath(docs_root), stamp)


@functools.lru_cache(maxsize=4)
def _docs_attribution_cached(docs_root: str, _stamp: int) -> DocsAttribution:
    pages: list[tuple[str | None, str, frozenset[str]]] = []
    folder_counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    root = Path(docs_root)
    for path in sorted(root.rglob("*.rst")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        relative = path.relative_to(root).parts
        folder = relative[0].lower() if len(relative) > 1 else None
        libraries = _page_libraries(text)
        pages.append((folder, path.stem.lower(), libraries))
        if folder is not None:
            folder_counts[folder].update(libraries)
    folder_library: dict[str, str] = {}
    for folder, counts in folder_counts.items():
        ranked = counts.most_common(2)
        # A tie names no library: the folder's pages do not say which one.
        if ranked and (len(ranked) == 1 or ranked[0][1] > ranked[1][1]):
            folder_library[folder] = ranked[0][0]
    attributed: dict[str, set[str]] = {}
    core: set[str] = set()
    for folder, stem, libraries in pages:
        page_libraries = set(libraries)
        if not page_libraries and folder in folder_library:
            page_libraries = {folder_library[folder]}
        if page_libraries:
            attributed.setdefault(stem, set()).update(page_libraries)
        else:
            core.add(stem)
    return DocsAttribution(by_symbol={
        stem: frozenset(libraries) for stem, libraries in attributed.items() if stem not in core
    })


def library_is_documented(index: LibraryIndex, attribution: DocsAttribution) -> bool:
    """Decision 1(b) as applied in planning v0.92 §8.1: the index defines at
    least one symbol whose docs pages are attributed to this library, or to
    the package directory holding the index (`tsmt` resolves into
    `pkgs\\timeseries`, whose pages say `library timeseries;`)."""
    owners = {index.name} | ({index.package_dir} if index.package_dir else set())
    return any(attribution.libraries_for(symbol) & owners for symbol in index.symbols)


def library_is_usable(index: LibraryIndex, attribution: DocsAttribution) -> bool:
    """Whether `library <index.name>;` may stand in a handoff candidate:
    the index lists symbols (a paths-only one defines nothing, lb05), sits
    under the installation's package directory, and is documented
    (`library_is_documented`).

    The package-directory rule came from the v0.92.0 verdict diff (planning
    v0.92 §9): the only documented index outside `pkgs/` is `lib/pgraph.lcg`,
    GAUSS's legacy graphics, and its examples (`xy`, `draw`, `bar`, `hist`,
    `scale`) each wrote `graphic.tkf` into the working directory under
    `tgauss.exe -b` -- a file write the system-statement registry does not
    list. Installed packages wrote no file in the same runs."""
    return index.lists_symbols and index.package_dir is not None and library_is_documented(index, attribution)


@dataclasses.dataclass(frozen=True)
class InstalledLibrariesReport:
    """For `gauss_session_start` and `gauss-ai doctor` (planning v0.92
    §3.6): every library name reachable on the search path, split into the
    ones `library` may name in a handoff candidate and the rest."""

    allowed: tuple[str, ...]
    not_allowed: tuple[str, ...]


def report_installed_libraries(
    installation: Installation | None, attribution: DocsAttribution,
) -> InstalledLibrariesReport | None:
    if installation is None:
        return None
    allowed: list[str] = []
    not_allowed: list[str] = []
    for name in installation.reachable_library_names():
        if name in ("gauss", "user"):
            continue  # always loaded; never named
        index = installation.resolve(name)
        if index is not None and library_is_usable(index, attribution):
            allowed.append(name)
        else:
            not_allowed.append(name)
    return InstalledLibrariesReport(allowed=tuple(allowed), not_allowed=tuple(not_allowed))
