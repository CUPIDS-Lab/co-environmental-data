"""Shared HTTP + progress plumbing for the fetch step.

The per-pipeline ``fetch.py`` keeps its own ``fetch_artifact`` (no-data
conventions; reservoir's JSON:API ``links.next`` pagination), its ``fetch_all``
orchestration (the ``discover()`` signature and progress wording differ), and its
``_progress_message`` (per-domain noun + label) — those details are load-bearing
and per-pipeline. The identical machinery lives here: the cached session, the
transient-retry wrapper, and the throttled progress emitter.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable


PROGRESS_INTERVAL = 2.0  # seconds between throttled progress lines


class RateLimited(Exception):
    """A transient response (per the caller's ``retry_codes``) worth retrying with backoff."""


def make_session(project_dir: Path, user_agent: str, *, allowable_codes=None):
    """A ``requests-cache`` session writing to ``<project_dir>/.requests-cache``.

    ``allowable_codes=(200,)`` (the CDSS/AWDB pipelines) caches only successes so a
    re-run re-hits a throttled/failed request; ``None`` keeps requests-cache's default.
    """
    import requests_cache

    kw = {"cache_name": str(Path(project_dir) / ".requests-cache"), "expire_after": 3600}
    if allowable_codes is not None:
        kw["allowable_codes"] = allowable_codes
    sess = requests_cache.CachedSession(**kw)
    sess.headers.update({"User-Agent": user_agent})
    return sess


def get_with_retry(sess, url: str, *, max_retries: int, timeout: int, retry_codes=()):
    """GET with retries on transient errors only — connection/timeout always, plus
    any status in ``retry_codes`` (e.g. the CDSS 403 throttle, or 5xx). Returns the
    Response as-is (incl. 404, which several of these APIs use to mean 'zero records')."""
    import requests
    from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                          wait_exponential)

    @retry(stop=stop_after_attempt(max_retries),
           wait=wait_exponential(multiplier=1, min=2, max=30), reraise=True,
           retry=retry_if_exception_type(
               (requests.ConnectionError, requests.Timeout, RateLimited)))
    def _do():
        resp = sess.get(url, timeout=timeout)
        if retry_codes and resp.status_code in retry_codes:
            raise RateLimited(f"HTTP {resp.status_code}")
        return resp

    return _do()


def make_emitter(progress, render: Callable[[dict], str]):
    """Resolve the ``progress`` argument into an ``emit(event)`` callable.

    ``True`` → throttled printer (notebook- and terminal-safe), formatting each event
    with the per-pipeline ``render``; ``False``/``None`` → silent; a callable →
    receives each raw event dict (for tqdm/structlog/tests).
    """
    if not progress:
        return lambda ev: None
    if callable(progress):
        return progress
    state = {"last": 0.0}

    def emit(ev):
        ph = ev.get("phase")
        if ph in ("start", "source", "done"):
            print(render(ev))
            state["last"] = time.monotonic()
        elif ph == "tick":
            now = time.monotonic()
            if now - state["last"] >= PROGRESS_INTERVAL:   # throttle: not every object
                state["last"] = now
                print(render(ev))

    return emit
