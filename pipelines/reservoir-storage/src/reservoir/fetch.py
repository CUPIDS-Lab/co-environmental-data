"""Idempotent downloader: walk every Source.discover(), GET, save, hash.

Writes are the *only* path into ``data/original/`` (immutable thereafter). Uses
``requests-cache`` for HTTP-layer idempotence and ``tenacity`` for retries on
transient failures, with a polite rate-limit and a descriptive User-Agent.
Re-running is safe: an artifact already on disk is skipped unless ``force=True``.

This module performs network I/O. The notebooks call it explicitly so a live
pull is always a deliberate, visible step — never a side effect of import.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from reservoir import config, provenance
from reservoir.sources import Artifact


def _session():
    import requests_cache

    sess = requests_cache.CachedSession(
        cache_name=str(config.PROJECT_DIR / ".requests-cache"),
        expire_after=3600,
    )
    sess.headers.update({"User-Agent": config.USER_AGENT})
    return sess


def _get_with_retry(sess, url: str):
    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(stop=stop_after_attempt(config.MAX_RETRIES),
           wait=wait_exponential(multiplier=1, min=1, max=30), reraise=True)
    def _do():
        resp = sess.get(url, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp

    return _do()


def fetch_artifact(sess, art: Artifact, *, force: bool = False) -> Path:
    """Download one artifact to its local path; return the path."""
    art.local_path.parent.mkdir(parents=True, exist_ok=True)
    if art.local_path.exists() and not force:
        return art.local_path
    resp = _get_with_retry(sess, art.url)
    art.local_path.write_bytes(resp.content)
    if not getattr(resp, "from_cache", False):
        time.sleep(config.RATE_LIMIT_SECONDS)
    return art.local_path


def fetch_all(*, sources: list[str] | None = None, force: bool = False) -> list[Artifact]:
    """Discover + download every artifact; refresh the sha256 manifest.

    Returns the list of fetched Artifacts so the caller (notebook) can inspect
    counts and pass them to the cleaning step.
    """
    sess = _session()
    registry = config.get_sources()
    fetched: list[Artifact] = []
    manifest: dict[str, str] = {}
    for slug, src in registry.items():
        if sources and slug not in sources:
            continue
        for art in src.discover():
            path = fetch_artifact(sess, art, force=force)
            manifest[str(path.relative_to(config.ORIGINAL))] = provenance.sha256_file(path)
            fetched.append(art)
    config.MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    config.MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return fetched
