"""One-time, user-invoked download of the official GAUSS documentation
(v0.80.0) into a local cache, so documentation grounding works without
cloning a git repository.

`gauss-ai docs fetch` (or the optional step in `gauss-ai init`) downloads
the raw `.rst` source of every page published at
https://docs.aptech.com/gauss/ -- a Sphinx site that publishes each page's
source at `_sources/<file>.txt` and lists every page in `searchindex.js`.
The published sources were verified byte-identical (apart from line
endings) to the `aptech/docs` repository's own `.rst` files. The result is
saved under `~/.gauss-ai/docs/` with the same relative layout, which is
exactly what `command_doc_lookup.py` and `gauss_doc_concept_index.py`
already expect from any `docs-root`: retrieval itself is unchanged and stays
entirely local.

Boundaries:

- This is the ONLY network access in gauss-ai besides a model provider the
  user explicitly enabled (see CLAUDE.md). It runs only when the user
  explicitly asks for it -- never automatically, never per question.
- Documentation is downloaded by each user, directly from Aptech's own
  public site, for local use. gauss-ai never bundles or redistributes it
  (the `aptech/docs` repository declares no license).
- Remote file names are untrusted input: anything absolute, containing
  `..`, or otherwise resolving outside the staging directory is rejected.
- The corpus is never left partial: the documentation-derived concept
  index's document-frequency filter depends on the full corpus, so any
  failed page aborts the whole fetch and the previous cache is kept intact.
"""

from __future__ import annotations

import concurrent.futures
import dataclasses
import json
import os
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable

import gauss_ai_config as config_mod

__version__ = "0.84.0"

DOCS_BASE_URL = "https://docs.aptech.com/gauss/"
SEARCH_INDEX_NAME = "searchindex.js"
SOURCES_PREFIX = "_sources/"
DOCS_CACHE_DIR_NAME = "docs"
MANIFEST_FILE_NAME = "docs-manifest.json"
#: v0.80.0 real-fetch finding: at 4 concurrent requests docs.aptech.com
#: began answering HTTP 403 partway through (the same URL returned 200 a
#: moment later) -- rate limiting. Kept deliberately polite: 2 workers, and
#: 403/429/5xx/network errors are retried with backoff.
DEFAULT_CONCURRENCY = 2
DEFAULT_TIMEOUT_SECONDS = 30
RETRY_BACKOFF_SECONDS = (2.0, 5.0, 15.0)
_RETRYABLE_STATUSES = frozenset({403, 429, 500, 502, 503, 504})
USER_AGENT = f"gauss-ai/{__version__} (+https://github.com/ec78/gauss-ai)"

Transport = Callable[[urllib.request.Request], tuple[int, bytes]]


class DocsFetchError(Exception):
    """Raised for any fetch failure. The previous cache is always left
    untouched when this is raised."""


def _default_transport(request: urllib.request.Request) -> tuple[int, bytes]:
    """The one network-touching function in this module; every test injects
    a fake instead."""
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def default_cache_dir() -> Path:
    return config_mod.config_dir() / DOCS_CACHE_DIR_NAME


def manifest_path(cache_dir: Path) -> Path:
    return cache_dir.parent / MANIFEST_FILE_NAME


def read_manifest(cache_dir: Path | None = None) -> dict[str, Any] | None:
    path = manifest_path(cache_dir or default_cache_dir())
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def parse_search_index(payload: bytes) -> tuple[tuple[str, ...], Any]:
    """Extracts the page list from Sphinx's `searchindex.js`
    (`Search.setIndex({...})`). Returns `(filenames, envversion)`, excluding
    `_`-prefixed entries (theme/internal pages, not GAUSS documentation)."""
    text = payload.decode("utf-8", errors="replace")
    start, end = text.find("("), text.rfind(")")
    if start == -1 or end <= start:
        raise DocsFetchError("search index has an unexpected format (no Search.setIndex(...) call found)")
    try:
        index = json.loads(text[start + 1:end])
    except json.JSONDecodeError as exc:
        raise DocsFetchError(f"search index is not valid JSON: {exc}") from exc
    filenames = index.get("filenames") if isinstance(index, dict) else None
    if not isinstance(filenames, list) or not all(isinstance(f, str) for f in filenames):
        raise DocsFetchError("search index has no usable 'filenames' list")
    pages = tuple(f for f in filenames if f.endswith(".rst") and not f.startswith("_"))
    return pages, index.get("envversion")


def safe_relative_path(filename: str) -> PurePosixPath | None:
    """Returns a safe relative `.rst` path, or `None` for anything that
    could escape the staging directory (absolute paths, drive letters,
    backslashes, `..`, empty segments)."""
    if not filename or "\\" in filename or ":" in filename or filename.startswith("/"):
        return None
    path = PurePosixPath(filename)
    if path.suffix != ".rst" or any(part in ("", ".", "..") for part in path.parts):
        return None
    return path


def _get(transport: Transport, url: str, *, sleep_fn: Callable[[float], None] = time.sleep) -> bytes:
    """Retries rate-limit/server/network failures with backoff, then fails
    closed. Any other status (e.g. 404: the page genuinely isn't there)
    fails immediately."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error = ""
    for attempt in range(len(RETRY_BACKOFF_SECONDS) + 1):
        if attempt:
            sleep_fn(RETRY_BACKOFF_SECONDS[attempt - 1])
        try:
            status, body = transport(request)
        except (urllib.error.URLError, OSError) as exc:
            last_error = str(exc)
            continue
        if status == 200:
            return body
        last_error = f"HTTP {status}"
        if status not in _RETRYABLE_STATUSES:
            break
    raise DocsFetchError(f"could not download {url}: {last_error}")


@dataclass(frozen=True)
class FetchResult:
    cache_dir: Path
    file_count: int
    fetched_at: str
    source_url: str


def fetch_docs(
    *,
    cache_dir: Path | None = None,
    transport: Transport = _default_transport,
    base_url: str = DOCS_BASE_URL,
    concurrency: int = DEFAULT_CONCURRENCY,
    progress_fn: Callable[[int, int], None] | None = None,
    clock_fn: Callable[[], str] = lambda: datetime.now(timezone.utc).isoformat(),
    sleep_fn: Callable[[float], None] = time.sleep,
) -> FetchResult:
    """Downloads every published page into a fresh staging directory, then
    swaps it in place of `cache_dir`. Raises `DocsFetchError` on any
    failure, leaving any existing cache exactly as it was."""
    cache_dir = (cache_dir or default_cache_dir()).resolve()
    pages, envversion = parse_search_index(_get(transport, base_url + SEARCH_INDEX_NAME, sleep_fn=sleep_fn))
    if not pages:
        raise DocsFetchError("the published search index listed no documentation pages")

    targets: list[tuple[str, PurePosixPath]] = []
    for filename in pages:
        rel = safe_relative_path(filename)
        if rel is None:
            raise DocsFetchError(f"refusing unsafe page path from the search index: {filename!r}")
        targets.append((filename, rel))

    cache_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = cache_dir.parent / f"{cache_dir.name}.staging-{uuid.uuid4().hex}"
    staging.mkdir()
    try:
        def _download(item: tuple[str, PurePosixPath]) -> None:
            filename, rel = item
            body = _get(
                transport, base_url + SOURCES_PREFIX + urllib.parse.quote(filename, safe="/") + ".txt", sleep_fn=sleep_fn,
            )
            destination = (staging / Path(*rel.parts)).resolve()
            if staging.resolve() not in destination.parents:
                raise DocsFetchError(f"refusing to write outside the staging directory: {filename!r}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(body)

        done = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
            futures = [pool.submit(_download, target) for target in targets]
            try:
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                    done += 1
                    if progress_fn is not None:
                        progress_fn(done, len(targets))
            except BaseException:
                for pending in futures:
                    pending.cancel()
                raise
        _swap_into_place(staging, cache_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    fetched_at = clock_fn()
    manifest = {
        "source_url": base_url,
        "fetched_at": fetched_at,
        "file_count": len(targets),
        "sphinx_envversion": envversion,
        "gauss_ai_version": __version__,
    }
    manifest_path(cache_dir).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return FetchResult(cache_dir=cache_dir, file_count=len(targets), fetched_at=fetched_at, source_url=base_url)


def _swap_into_place(staging: Path, cache_dir: Path) -> None:
    """Replaces `cache_dir` with `staging`. Renaming the directory also
    gives it a fresh mtime, which is what `gauss_doc_concept_index`'s own
    cache key watches, so the derived index is rebuilt for the new docs."""
    previous = cache_dir.parent / f"{cache_dir.name}.previous"
    if previous.exists():
        shutil.rmtree(previous)
    if cache_dir.exists():
        os.replace(cache_dir, previous)
    os.replace(staging, cache_dir)
    shutil.rmtree(previous, ignore_errors=True)


def point_config_at_cache(cache_dir: Path, *, config_path: Path | None = None) -> tuple[bool, str]:
    """Sets `docs_root` to the cache only if it is unset or already the
    cache -- never overrides a path the user chose themselves. Returns
    `(updated, message)`."""
    config = config_mod.load_config(config_path)
    current = config.docs_root
    if current and Path(current).expanduser().resolve() != cache_dir.resolve():
        return False, (
            f"docs-root is already set to {current} and was left unchanged. To use the downloaded docs instead: "
            f"gauss-ai config set docs-root {cache_dir}"
        )
    if current:
        return False, f"docs-root already points at {cache_dir}."
    config_mod.save_config(dataclasses.replace(config, docs_root=str(cache_dir)), config_path)
    return True, f"docs-root set to {cache_dir}."
