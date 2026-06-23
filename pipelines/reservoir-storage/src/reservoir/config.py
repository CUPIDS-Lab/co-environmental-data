"""Paths, HTTP defaults, and the SOURCES registry.

Non-secret per-source configuration (base URLs, endpoint templates, the
Northern Water ArcGIS service URL that still needs confirming) lives in
``data/lookups/sources.yaml`` so it is editable without touching code. Secrets
(API keys) come from the environment / ``.env`` and are never committed.
"""
from __future__ import annotations

import os
from pathlib import Path

from co_pipeline_core import config as _core

# ── paths ────────────────────────────────────────────────────────────────────
PKG_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PKG_DIR.parent.parent           # pipelines/reservoir-storage/
DATA = PROJECT_DIR / "data"
ORIGINAL = DATA / "original"
PROCESSED = DATA / "processed"
AUDIT = DATA / "audit"
LOOKUPS = DATA / "lookups"

CANONICAL_CSV = PROCESSED / "reservoir-storage.csv"
PROVENANCE_CSV = PROCESSED / "provenance.csv"
MANIFEST = ORIGINAL / "manifest.json"
SOURCES_YAML = LOOKUPS / "sources.yaml"
CONCEPTS_YAML = LOOKUPS / "concepts.yaml"

# ── HTTP defaults ────────────────────────────────────────────────────────────
USER_AGENT = _core.user_agent("reservoir-storage")
REQUEST_TIMEOUT = 60          # seconds
RATE_LIMIT_SECONDS = 0.5      # polite delay between requests
MAX_RETRIES = 4

# Secrets, read from the environment (set in a git-ignored .env). Optional —
# CDSS and NREL raise rate limits with a key but work without one.
CDSS_API_KEY = os.environ.get("CDSS_API_KEY", "")


def load_sources_config() -> dict:
    """Read ``data/lookups/sources.yaml`` (endpoints + per-source params)."""
    return _core.read_sources_yaml(SOURCES_YAML)


def get_sources() -> dict:
    """Instantiate the registered Source objects keyed by slug.

    Imported lazily to avoid a circular import (sources.py imports config).
    """
    from reservoir.sources import DwrCdss, ReclamationRise, NorthernWater

    return {
        s.name: s for s in (DwrCdss(), ReclamationRise(), NorthernWater())
    }
