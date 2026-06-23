"""Paths, HTTP defaults, and the SOURCES registry.

Non-secret per-source configuration (base URLs, endpoint templates, parameter
codes) lives in ``data/lookups/sources.yaml`` so it is editable without touching
code. Secrets (the optional CDSS API key) come from the environment / ``.env``
and are never committed.
"""
from __future__ import annotations

import os
from pathlib import Path

from co_pipeline_core import config as _core

# ── paths ────────────────────────────────────────────────────────────────────
PKG_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PKG_DIR.parent.parent           # pipelines/streamflow/
DATA = PROJECT_DIR / "data"
ORIGINAL = DATA / "original"
PROCESSED = DATA / "processed"
AUDIT = DATA / "audit"
LOOKUPS = DATA / "lookups"

CANONICAL_CSV = PROCESSED / "streamflow.csv"
PROVENANCE_CSV = PROCESSED / "provenance.csv"
MANIFEST = ORIGINAL / "manifest.json"
SOURCES_YAML = LOOKUPS / "sources.yaml"
CONCEPTS_YAML = LOOKUPS / "concepts.yaml"
SITES_CSV = LOOKUPS / "sites.csv"

# ── HTTP defaults ────────────────────────────────────────────────────────────
USER_AGENT = _core.user_agent("streamflow")
REQUEST_TIMEOUT = 120        # seconds — USGS full-POR daily responses can be multi-MB
# Polite delay between requests + retry budget. Both are env-overridable because CDSS
# throttles a sustained burst of large full-history requests with HTTP 403 — raise
# STREAMFLOW_RATE_LIMIT (e.g. 3) and/or set CDSS_API_KEY for a clean full DWR pull.
RATE_LIMIT_SECONDS = float(os.environ.get("STREAMFLOW_RATE_LIMIT", "0.5"))
MAX_RETRIES = int(os.environ.get("STREAMFLOW_MAX_RETRIES", "5"))

# Secrets. CDSS works without a key, but a key RAISES its rate limits — required in
# practice for a full DWR pull (a keyless full-history burst trips a 403 IP throttle).
# Resolution order: $CDSS_API_KEY, else a git-ignored ``dwr_api.json`` (pipeline root,
# then repo root) holding ``{"CDSS_API_KEY": "..."}``. USGS needs no key.
CDSS_API_KEY = _core.load_cdss_api_key(PROJECT_DIR)


def load_sources_config() -> dict:
    """Read ``data/lookups/sources.yaml`` (endpoints + per-source params)."""
    return _core.read_sources_yaml(SOURCES_YAML)


def get_sources() -> dict:
    """Instantiate the registered Source objects keyed by slug.

    Imported lazily to avoid a circular import (sources.py imports config).
    """
    from streamflow.sources import UsgsNwis, DwrCdss

    return {s.name: s for s in (UsgsNwis(), DwrCdss())}
