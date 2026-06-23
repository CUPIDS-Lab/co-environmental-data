"""Idempotent downloader: walk every Source.discover(), GET, save, hash.

Writes are the *only* path into ``data/original/`` (immutable thereafter). Uses
``requests-cache`` for HTTP-layer idempotence and ``tenacity`` for retries on
*transient* failures (connection/timeout/5xx), with a polite rate-limit and a
descriptive User-Agent.

**Errors are durable, not fatal.** Two behaviors matter here:

- **AWDB signals "no data" in the body, not the status.** A valid request for a
  station/element with no observations returns HTTP 200 with an empty ``values``
  list (or an empty ``data`` array). That is a non-error no-data outcome the
  parser turns into an empty frame — we still save the response. (A truly invalid
  station triplet can 404; we treat that as no-data too.)
- A single bad artifact (a 5xx, a connection drop) must not abort the whole
  retrieval. Each failure is logged to ``data/audit/fetch_errors.json`` and the
  run continues.

AWDB returns each station's full period of record in one (≈1 MB) JSON — not
paginated — so there is no ``links.next`` walk. This module performs network I/O
only when a notebook/CLI calls it — never on import.
"""
from __future__ import annotations

import datetime as _dt
import json
import time
from pathlib import Path

from snowpack import config, provenance
from snowpack.sources import Artifact

from co_pipeline_core import fetch as _corefetch


def _session():
    return _corefetch.make_session(config.PROJECT_DIR, config.USER_AGENT, allowable_codes=(200,))




def fetch_artifact(sess, art: Artifact, *, force: bool = False) -> Path | None:
    """Download one artifact. Returns its path, or ``None`` when the station is
    unknown upstream (HTTP 404) — a non-error 'no data' outcome. An empty-but-200
    body IS saved (the parser yields an empty frame from it)."""
    art.local_path.parent.mkdir(parents=True, exist_ok=True)
    if art.local_path.exists() and not force:
        return art.local_path
    resp = _corefetch.get_with_retry(sess, art.url, max_retries=config.MAX_RETRIES, timeout=config.REQUEST_TIMEOUT, retry_codes=(429, 502, 503, 504))
    if resp.status_code == 404:
        return None  # unknown station — treat as no data, not an error
    resp.raise_for_status()  # other 4xx/5xx are real failures (caught by fetch_all)
    art.local_path.write_bytes(resp.content)
    if not getattr(resp, "from_cache", False):
        time.sleep(config.RATE_LIMIT_SECONDS)
    return art.local_path




def _progress_message(ev: dict) -> str:
    """Render one progress event as a human line (pure; unit-tested)."""
    ph = ev.get("phase")
    if ph == "start":
        srcs = ", ".join(ev["sources"])
        return f"⏳ fetching ~{ev['total']} stations from {len(ev['sources'])} source(s): {srcs}"
    if ph == "source":
        return f"  → {ev['source']}: {ev['count']} stations"
    if ph == "tick":
        pct = 100 * ev["done"] // max(1, ev["total"])
        site = ev.get("site") or ""
        return (f"    {ev['done']}/{ev['total']} ({pct}%) · {ev['fetched']} ok · "
                f"{ev['no_data']} no-data · {ev['errors']} err  {site}").rstrip()
    if ph == "done":
        return (f"✓ fetched {ev['fetched']} · {ev['no_data']} no-data · "
                f"{ev['errors']} errors (see data/audit/fetch_errors.json)")
    return ""


def _make_emitter(progress):
    """Throttled printer over this pipeline's _progress_message (shared)."""
    return _corefetch.make_emitter(progress, _progress_message)


def fetch_all(*, sources: list[str] | None = None, sites: set[str] | None = None,
              force: bool = False, progress=True) -> list[Artifact]:
    """Discover + download every artifact; refresh the sha256 manifest.

    Never raises on a single bad artifact: a 404 (no data) is skipped silently,
    any other error is logged to ``data/audit/fetch_errors.json`` and the run
    continues. Returns the list of artifacts that actually produced a file.

    ``sites`` restricts to a subset of stations — the sampling hook for a fast
    end-to-end run. ``progress`` reports how far along the run is; pass ``False``
    to silence or a callable for raw events.
    """
    sess = _session()
    registry = config.get_sources()
    emit = _make_emitter(progress)

    # discover() is cheap (builds URLs, no I/O) — materialize it so we have a
    # denominator for "X/Y" without it being a hard promise about timing.
    plan = [(slug, src, list(src.discover(sites=sites)))
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
                  "site": art.metadata.get("site_name")})
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
