"""Tests for `gauss_docs_fetch.py` (v0.80.0).

Run with:

    python scripts/test_gauss_docs_fetch.py

Network-free: every test injects a fake transport, and every cache/config
path is a disposable temp directory -- never this machine's real
`~/.gauss-ai/` or the real docs.aptech.com site.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_ai_config as config_mod  # noqa: E402
import gauss_docs_fetch as fetch_mod  # noqa: E402

_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


BASE = "https://example.test/gauss/"


def _no_sleep(_seconds: float) -> None:
    """Retry backoff is real seconds in production; tests never wait."""


def _index(filenames: list[str]) -> bytes:
    payload = {"filenames": filenames, "envversion": {"sphinx": 61}, "docnames": [f[:-4] for f in filenames]}
    return f"Search.setIndex({json.dumps(payload)})".encode("utf-8")


def _site(pages: dict[str, bytes], *, index_names: list[str] | None = None, fail: set[str] = frozenset()):
    """A fake transport serving a tiny published site. Returns (transport, requested_urls)."""
    requested: list[str] = []
    names = index_names if index_names is not None else list(pages)

    def transport(request):
        url = request.full_url
        requested.append(url)
        if url == BASE + fetch_mod.SEARCH_INDEX_NAME:
            return 200, _index(names)
        for name, body in pages.items():
            if url == BASE + fetch_mod.SOURCES_PREFIX + name + ".txt":
                return (500, b"boom") if name in fail else (200, body)
        return 404, b"not found"

    return transport, requested


def test_01_parse_search_index_excludes_internal_pages() -> None:
    pages, env = fetch_mod.parse_search_index(_index(["meanc.rst", "_themes/x/README.rst", "tsmt/arimafit.rst"]))
    check("internal page excluded", pages == ("meanc.rst", "tsmt/arimafit.rst"))
    check("envversion kept", env == {"sphinx": 61})


def test_02_malformed_index_raises() -> None:
    for payload in (b"not javascript", b"Search.setIndex({bad json})", b'Search.setIndex({"docnames": []})'):
        try:
            fetch_mod.parse_search_index(payload)
            check(f"{payload!r} rejected", False)
        except fetch_mod.DocsFetchError:
            check(f"{payload!r} rejected", True)


def test_03_unsafe_paths_are_rejected() -> None:
    for bad in ("../evil.rst", "/abs.rst", "C:/x.rst", "a\\b.rst", "a/../b.rst", "notrst.txt", ""):
        check(f"{bad!r} unsafe", fetch_mod.safe_relative_path(bad) is None)
    check("nested ok", str(fetch_mod.safe_relative_path("tsmt/arimafit.rst")) == "tsmt/arimafit.rst")


def test_04_fetch_writes_rst_files_preserving_subdirectories_and_manifest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / "docs"
        transport, requested = _site({"meanc.rst": b"meanc\n=====\n", "tsmt/arimafit.rst": b"arimafit\n"})
        result = fetch_mod.fetch_docs(sleep_fn=_no_sleep, cache_dir=cache, transport=transport, base_url=BASE, clock_fn=lambda: "T0")
        check("two files", result.file_count == 2)
        check("saved as .rst (not .rst.txt)", (cache / "meanc.rst").read_bytes() == b"meanc\n=====\n")
        check("subdirectory preserved", (cache / "tsmt" / "arimafit.rst").is_file())
        manifest = fetch_mod.read_manifest(cache)
        check("manifest recorded", manifest is not None and manifest["file_count"] == 2 and manifest["fetched_at"] == "T0")
        check("no staging directory left behind", not any(p.name.startswith("docs.staging-") for p in Path(tmp).iterdir()))


def test_05_any_failed_page_aborts_and_keeps_the_previous_cache() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / "docs"
        cache.mkdir()
        (cache / "old.rst").write_text("old", encoding="utf-8")
        transport, _ = _site({"meanc.rst": b"x", "invpd.rst": b"y"}, fail={"invpd.rst"})
        try:
            fetch_mod.fetch_docs(sleep_fn=_no_sleep, cache_dir=cache, transport=transport, base_url=BASE, concurrency=1)
            check("failure raised", False)
        except fetch_mod.DocsFetchError:
            check("failure raised", True)
        check("old cache intact", (cache / "old.rst").read_text(encoding="utf-8") == "old")
        check("no partial new file in cache", not (cache / "meanc.rst").exists())
        check("staging cleaned up", not any(p.name.startswith("docs.staging-") for p in Path(tmp).iterdir()))


def test_06_unsafe_name_in_index_aborts_before_any_download() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        transport, requested = _site({"meanc.rst": b"x"}, index_names=["meanc.rst", "../../escape.rst"])
        try:
            fetch_mod.fetch_docs(sleep_fn=_no_sleep, cache_dir=Path(tmp) / "docs", transport=transport, base_url=BASE)
            check("unsafe index rejected", False)
        except fetch_mod.DocsFetchError:
            check("unsafe index rejected", True)
        # v0.89.0 (decision 7b): the site's robots.txt is read first, so it is
        # the one request before the index; still no page is downloaded.
        check("only robots.txt and the index were requested",
              requested == [fetch_mod.robots_url(BASE), BASE + fetch_mod.SEARCH_INDEX_NAME])
        check("nothing escaped", not (Path(tmp).parent / "escape.rst").exists())


def test_07_refetch_replaces_old_cache_contents() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / "docs"
        first, _ = _site({"old.rst": b"old"})
        fetch_mod.fetch_docs(sleep_fn=_no_sleep, cache_dir=cache, transport=first, base_url=BASE)
        second, _ = _site({"new.rst": b"new"})
        fetch_mod.fetch_docs(sleep_fn=_no_sleep, cache_dir=cache, transport=second, base_url=BASE)
        check("new content present", (cache / "new.rst").is_file())
        check("stale page removed", not (cache / "old.rst").exists())
        check("no .previous left behind", not (Path(tmp) / "docs.previous").exists())


def test_08_transient_error_is_retried_once() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        calls = {"n": 0}
        inner, _ = _site({"meanc.rst": b"x"})

        def flaky(request):
            if request.full_url.endswith("meanc.rst.txt"):
                calls["n"] += 1
                if calls["n"] == 1:
                    return 503, b"busy"
            return inner(request)

        result = fetch_mod.fetch_docs(sleep_fn=_no_sleep, cache_dir=Path(tmp) / "docs", transport=flaky, base_url=BASE)
        check("succeeded after one retry", result.file_count == 1 and calls["n"] == 2)


def test_09_config_is_pointed_at_cache_only_when_unset() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / "docs"
        cache.mkdir()
        cfg = Path(tmp) / "config.json"
        updated, _ = fetch_mod.point_config_at_cache(cache, config_path=cfg)
        check("unset docs_root is set", updated and config_mod.load_config(cfg).docs_root == str(cache))
        other = Path(tmp) / "my-own-docs"
        other.mkdir()
        config_mod.save_config(config_mod.GaussAiConfig(docs_root=str(other)), cfg)
        updated, message = fetch_mod.point_config_at_cache(cache, config_path=cfg)
        check("user-chosen docs_root is never overridden", not updated and config_mod.load_config(cfg).docs_root == str(other))
        check("message tells the user how to switch", "gauss-ai config set docs-root" in message)


def test_10_requests_carry_an_identifying_user_agent() -> None:
    seen: list[str] = []
    inner, _ = _site({"meanc.rst": b"x"})

    def recording(request):
        seen.append(request.get_header("User-agent") or "")
        return inner(request)

    with tempfile.TemporaryDirectory() as tmp:
        fetch_mod.fetch_docs(sleep_fn=_no_sleep, cache_dir=Path(tmp) / "docs", transport=recording, base_url=BASE)
    check("every request identifies gauss-ai", seen and all(ua.startswith("gauss-ai/") for ua in seen))


def test_11_rate_limit_403_is_retried_with_backoff_but_404_is_not() -> None:
    """The real v0.80.0 fetch hit a transient HTTP 403 (rate limiting) that
    cleared a moment later -- those must be retried with backoff, while a
    genuine 404 fails at once."""
    sleeps: list[float] = []
    calls = {"n": 0}
    inner, _ = _site({"meanc.rst": b"x"})

    def throttled(request):
        if request.full_url.endswith("meanc.rst.txt"):
            calls["n"] += 1
            if calls["n"] <= 2:
                return 403, b"rate limited"
        return inner(request)

    with tempfile.TemporaryDirectory() as tmp:
        result = fetch_mod.fetch_docs(sleep_fn=sleeps.append, cache_dir=Path(tmp) / "docs", transport=throttled, base_url=BASE)
    check("succeeded after two 403s", result.file_count == 1 and calls["n"] == 3)
    check("backed off between attempts", sleeps == list(fetch_mod.RETRY_BACKOFF_SECONDS[:2]))

    sleeps.clear()
    missing, _ = _site({"meanc.rst": b"x"}, index_names=["meanc.rst", "gone.rst"])
    with tempfile.TemporaryDirectory() as tmp:
        try:
            fetch_mod.fetch_docs(sleep_fn=sleeps.append, cache_dir=Path(tmp) / "docs", transport=missing, base_url=BASE, concurrency=1)
            check("404 fails", False)
        except fetch_mod.DocsFetchError as exc:
            check("404 fails", "HTTP 404" in str(exc))
    check("404 is never retried", sleeps == [])


def test_12_v089_content_signal_ai_input_no_refuses_the_fetch() -> None:
    """Decision 7b (planning v0.89): honor `Content-Signal: ai-input=no`."""
    cloudflare_preamble = "# As a condition of accessing this website ...\n# ai-input: inputting content into AI models\n"
    cases = {
        "no robots.txt": (None, True),
        "the real docs.aptech.com shape (preamble only, no directives)": (cloudflare_preamble, True),
        "ai-input=yes": ("User-agent: *\nContent-Signal: search=yes, ai-input=yes, ai-train=no\nAllow: /\n", True),
        "only ai-train=no": ("User-agent: *\nContent-Signal: ai-train=no\n", True),
        "ai-input=no for everyone": ("User-agent: *\nContent-Signal: search=yes, ai-input=no\nAllow: /\n", False),
        "ungrouped ai-input=no": ("Content-Signal: ai-input=no\nUser-agent: *\nAllow: /\n", False),
        "case and spacing": ("user-agent: *\ncontent-signal:  AI-Input = No \n", False),
        "ai-input=no for another crawler only": ("User-agent: SomeBot\nContent-Signal: ai-input=no\n\nUser-agent: *\nAllow: /\n", True),
        "a group named after a word in our URL is not ours": ("User-agent: github\nContent-Signal: ai-input=no\n\nUser-agent: *\nAllow: /\n", True),
        "a gauss-ai group wins over *": ("User-agent: gauss-ai\nContent-Signal: ai-input=yes\n\nUser-agent: *\nContent-Signal: ai-input=no\n", True),
        "and can refuse when * allows": ("User-agent: gauss-ai\nContent-Signal: ai-input=no\n\nUser-agent: *\nContent-Signal: ai-input=yes\n", False),
    }
    for label, (robots, allowed) in cases.items():
        with tempfile.TemporaryDirectory() as tmp:
            site, requested = _site({"meanc.rst": b"x"}, index_names=["meanc.rst"])

            def transport(request, site=site, robots=robots):
                if request.full_url == fetch_mod.robots_url(BASE):
                    return (404, b"") if robots is None else (200, robots.encode("utf-8"))
                return site(request)

            cache = Path(tmp) / "docs"
            try:
                fetch_mod.fetch_docs(sleep_fn=_no_sleep, cache_dir=cache, transport=transport, base_url=BASE)
                ok = True
            except fetch_mod.DocsFetchError as exc:
                ok = False
                check(f"{label}: the refusal names the signal", "ai-input=no" in str(exc))
            check(f"{label}: {'fetched' if allowed else 'refused'}", ok == allowed)
            if not allowed:
                check(f"{label}: nothing else was requested", requested == [] and not cache.exists())
    check("robots.txt is the site root's", fetch_mod.robots_url("https://docs.aptech.com/gauss/") == "https://docs.aptech.com/robots.txt")


def _run_all() -> int:
    test_fns = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
    for fn in test_fns:
        fn()
    if _failures:
        print(f"FAILED ({len(_failures)} issue(s)):")
        for f in _failures:
            print(f"  - {f}")
        return 1
    print(f"PASSED: {len(test_fns)} test functions, 0 failures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
