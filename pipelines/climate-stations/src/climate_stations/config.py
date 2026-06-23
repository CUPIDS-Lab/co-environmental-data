"""Paths, HTTP defaults, and the SOURCES registry.

Non-secret per-source configuration (base URL, endpoint templates, the measType
list) lives in ``data/lookups/sources.yaml`` so it is editable without touching
code. The CDSS API key is a secret — it comes from the environment / ``.env`` or a
git-ignored ``dwr_api.json`` and is never committed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

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
USER_AGENT = (
    "co-environmental-data/climate-stations (CUPIDS Lab; "
    "https://github.com/CUPIDS-Lab/co-environmental-data; accounts@brianckeegan.com)"
)
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
def _load_cdss_api_key() -> str:
    env = os.environ.get("CDSS_API_KEY", "")
    if env:
        return env
    for candidate in (PROJECT_DIR / "dwr_api.json", PROJECT_DIR.parent.parent / "dwr_api.json"):
        try:
            if candidate.exists():
                data = json.loads(candidate.read_text())
                key = (data.get("CDSS_API_KEY") or data.get("api_key")
                       or data.get("apiKey") or data.get("key") or "")
                if key:
                    return key
        except Exception:
            pass  # malformed key file is non-fatal — fall through to keyless
    return ""


CDSS_API_KEY = _load_cdss_api_key()


def load_sources_config() -> dict:
    """Read ``data/lookups/sources.yaml`` (endpoints + per-source params)."""
    import yaml  # local import so `py_compile` works without the dep

    with open(SOURCES_YAML, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get_sources() -> dict:
    """Instantiate the registered Source objects keyed by slug.

    Imported lazily to avoid a circular import (sources.py imports config).
    """
    from climate_stations.sources import CdssClimate

    return {s.name: s for s in (CdssClimate(),)}
