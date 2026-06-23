"""Paths, HTTP defaults, and the SOURCES registry.

Non-secret per-source configuration (base URL, endpoint templates, the measType
list) lives in ``data/lookups/sources.yaml`` so it is editable without touching
code. The CDSS API key is a secret — it comes from the environment / ``.env`` or a
git-ignored ``dwr_api.json`` and is never committed.
"""
from __future__ import annotations

import os
from pathlib import Path

from co_pipeline_core import config as _core

# ── paths ────────────────────────────────────────────────────────────────────
PKG_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PKG_DIR.parent.parent           # pipelines/climate-stations/
DATA = PROJECT_DIR / "data"
ORIGINAL = DATA / "original"
PROCESSED = DATA / "processed"
AUDIT = DATA / "audit"
LOOKUPS = DATA / "lookups"

CANONICAL_CSV = PROCESSED / "climate-stations.csv"
PROVENANCE_CSV = PROCESSED / "provenance.csv"
MANIFEST = ORIGINAL / "manifest.json"
SOURCES_YAML = LOOKUPS / "sources.yaml"
CONCEPTS_YAML = LOOKUPS / "concepts.yaml"
STATIONS_CSV = LOOKUPS / "stations.csv"

# ── HTTP defaults ────────────────────────────────────────────────────────────
USER_AGENT = _core.user_agent("climate-stations")
REQUEST_TIMEOUT = 120        # seconds — a full-POR daily response can be multi-MB
# Polite delay between requests + retry budget. Both are env-overridable because CDSS
# throttles a sustained burst of large full-history requests — raise CLIMATE_RATE_LIMIT
# (e.g. 1.0) and/or set CDSS_API_KEY for a clean full pull.
RATE_LIMIT_SECONDS = float(os.environ.get("CLIMATE_RATE_LIMIT", "0.5"))
MAX_RETRIES = int(os.environ.get("CLIMATE_MAX_RETRIES", "5"))

# Secrets. CDSS works without a key, but anonymous daily/row limits took effect
# 2025-12-10 — a key is required in practice (a keyless pull now returns
# "Error: Exceeded Daily Data Limit"). Resolution order: $CDSS_API_KEY, else a
# git-ignored ``dwr_api.json`` (pipeline root, then repo root) holding
# ``{"CDSS_API_KEY": "..."}``.
CDSS_API_KEY = _core.load_cdss_api_key(PROJECT_DIR)


def load_sources_config() -> dict:
    """Read ``data/lookups/sources.yaml`` (endpoints + per-source params)."""
    return _core.read_sources_yaml(SOURCES_YAML)


def get_sources() -> dict:
    """Instantiate the registered Source objects keyed by slug.

    Imported lazily to avoid a circular import (sources.py imports config).
    """
    from climate_stations.sources import CdssClimate

    return {s.name: s for s in (CdssClimate(),)}
