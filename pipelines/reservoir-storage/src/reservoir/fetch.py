"""Idempotent downloader: walk every Source.discover(), GET, save, hash.

Writes are the *only* path into ``data/original/`` (immutable thereafter). Uses
``requests-cache`` for HTTP-layer idempotence and ``tenacity`` for retries on
*transient* failures (connection/timeout), with a polite rate-limit and a
descriptive User-Agent.

**Errors are durable, not fatal.** Two source quirks make this essential:

- **CDSS (and RISE) return HTTP 404 for a query that matches zero records** — the
  body literally says "returns zero records from CDSS." A 404 therefore means
  *no data for this query*, not a broken pipeline; we skip it, we don't crash.
- A single bad artifact (a station with no series, a stale id, a 5xx) must not
  abort the whole retrieval. Each failure is logged to
  ``data/audit/fetch_errors.json`` and the run continues.

This module performs network I/O, only when a notebook calls it — never on import.
"""
from __future__ import annotations

import datetime as _dt
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
    """GET with retries on *transient* errors only; returns the Response as-is
    (including 404, which several of these APIs use to mean 'zero records')."""
    import requests
    from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                          wait_exponential)

    @retry(stop=stop_after_attempt(config.MAX_RETRIES),
           wait=wait_exponential(multiplier=1, min=1, max=30), reraise=True,
           retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)))
    def _do():
        return sess.get(url, timeout=config.REQUEST_TIMEOUT)

    return _do()


def fetch_artifact(sess, art: Artifact, *, force: bool = False) -> Path | None:
    """Download one artifact. Returns its path, or ``None`` when the source
    reports zero records (HTTP 404) — a non-error 'no data' outcome."""
    art.local_path.parent.mkdir(parents=True, exist_ok=True)
    if art.local_path.exists() and not force:
        return art.local_path
    resp = _get_with_retry(sess, art.url)
    if resp.status_code == 404:
        return None  # zero records — not an error (CDSS/RISE convention)
    resp.raise_for_status()  # other 4xx/5xx are real failures (caught by fetch_all)
    if art.metadata.get("paginate") == "jsonapi":
        _save_paginated(sess, art, resp)        # full history may span many pages
    else:
        art.local_path.write_bytes(resp.content)
        if not getattr(resp, "from_cache", False):
            time.sleep(config.RATE_LIMIT_SECONDS)
    return art.local_path


def _save_paginated(sess, art: Artifact, first_resp) -> None:
    """Follow JSON:API ``links.next`` and merge every page's ``data[]`` into one
    saved file. RISE caps a page at 10,000 rows, so a full reservoir history
    (e.g. Blue Mesa storage ≈ 22k daily values back to 1952) spans several pages.

    Uses a plain (non-cached) session for the page walk — the ``requests-cache``
    session returns an empty body for these large paginated responses.
    """
    import requests
    from urllib.parse import urljoin

    plain = requests.Session()
    plain.headers.update({"User-Agent": config.USER_AGENT})
    payload = first_resp.json()
    data = list(payload.get("data", []) or [])
    nxt = (payload.get("links") or {}).get("next")
    pages = 1
    while nxt and pages < 5000:
        time.sleep(config.RATE_LIMIT_SECONDS)
        resp = _get_with_retry(plain, urljoin(art.url, nxt))
        if resp.status_code != 200:
            break
        try:
            pj = resp.json()
        except ValueError:
            break
        rows = pj.get("data", []) or []
        if not rows:
            break
        data.extend(rows)
        nxt = (pj.get("links") or {}).get("next")
        pages += 1
    art.local_path.write_text(json.dumps({"data": data}))


PROGRESS_INTERVAL = 2.0  # seconds between throttled progress lines


def _progress_message(ev: dict) -> str:
    """Render one progress event as a human line (pure; unit-tested)."""
    ph = ev.get("phase")
    if ph == "start":
        srcs = ", ".join(ev["sources"])
        return f"⏳ fetching ~{ev['total']} series from {len(ev['sources'])} source(s): {srcs}"
    if ph == "source":
        return f"  → {ev['source']}: {ev['count']} series"
    if ph == "tick":
        pct = 100 * ev["done"] // max(1, ev["total"])
        res = ev.get("reservoir") or ""
        return (f"    {ev['done']}/{ev['total']} ({pct}%) · {ev['fetched']} ok · "
                f"{ev['no_data']} no-data · {ev['errors']} err  {res}").rstrip()
    if ph == "done":
        return (f"✓ fetched {ev['fetched']} · {ev['no_data']} no-data (404) · "
                f"{ev['errors']} errors (see data/audit/fetch_errors.json)")
    return ""


def _make_emitter(progress):
    """Resolve the ``progress`` argument into an emit(event) callable.

    ``True`` → throttled printer (notebook- and terminal-safe); ``False``/``None``
    → silent; a callable → receives each raw event dict (for tqdm/structlog/tests).
    """
    if not progress:
        return lambda ev: None
    if callable(progress):
        return progress
    state = {"last": 0.0}

    def emit(ev):
        ph = ev.get("phase")
        if ph in ("start", "source", "done"):
            print(_progress_message(ev))
            state["last"] = time.monotonic()
        elif ph == "tick":
            now = time.monotonic()
            if now - state["last"] >= PROGRESS_INTERVAL:   # throttle: not every object
                state["last"] = now
                print(_progress_message(ev))

    return emit


def fetch_all(*, sources: list[str] | None = None, force: bool = False,
              progress=True) -> list[Artifact]:
    """Discover + download every artifact; refresh the sha256 manifest.

    Never raises on a single bad artifact: a 404 (no data) is skipped silently,
    any other error is logged to ``data/audit/fetch_errors.json`` and the run
    continues. Returns the list of artifacts that actually produced a file.

    ``progress`` reports how far along the run is — important because a full live
    pull fans out to hundreds of series and RISE histories paginate. It is *not* a
    deterministic bar: lines are throttled to ~one every few seconds and name the
    current source/reservoir + running counts. Pass ``progress=False`` to silence,
    or a callable to receive raw event dicts (e.g. drive a tqdm bar).
    """
    sess = _session()
    registry = config.get_sources()
    emit = _make_emitter(progress)

    # discover() is cheap (builds URLs, no I/O) — materialize it so we have a
    # denominator for "X/Y" without it being a hard promise about timing.
    plan = [(slug, src, list(src.discover()))
            for slug, src in registry.items()
            if not sources or slug in sources]
    total = sum(len(arts) for _, _, arts in plan)
    emit({"phase": "start", "total": total, "sources": [s for s, _, _ in plan]})

    fetched: list[Artifact] = []
    manifest: dict[str, str] = {}
    errors: list[dict] = []
    no_data = 0
    done = 0

    for slug, src, arts in plan:
        emit({"phase": "source", "source": slug, "count": len(arts)})
        for art in arts:
            emit({"phase": "tick", "done": done, "total": total, "fetched": len(fetched),
                  "no_data": no_data, "errors": len(errors),
                  "reservoir": art.metadata.get("reservoir_name")})
            try:
                path = fetch_artifact(sess, art, force=force)
            except Exception as err:  # durable, not fatal
                errors.append({"source": slug, "url": art.url,
                               "error": f"{type(err).__name__}: {err}",
                               "at": _dt.datetime.utcnow().isoformat() + "Z"})
                path = None
            else:
                if path is None:
                    no_data += 1
                else:
                    manifest[str(path.relative_to(config.ORIGINAL))] = provenance.sha256_file(path)
                    fetched.append(art)
            done += 1

    config.MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    config.MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    config.AUDIT.mkdir(parents=True, exist_ok=True)
    (config.AUDIT / "fetch_errors.json").write_text(json.dumps(errors, indent=2))
    emit({"phase": "done", "fetched": len(fetched), "no_data": no_data, "errors": len(errors)})
    return fetched
