"""Paths, HTTP defaults, and the SOURCES registry.

Non-secret per-source configuration (base URL, endpoint paths, element codes)
lives in ``data/lookups/sources.yaml`` so it is editable without touching code.

Unlike the streamflow/reservoir pipelines (which need a CDSS API key), the **NRCS
AWDB REST API requires no key** — it is open. The rate-limit / retry budget is
env-tunable for politeness, but there is no secret to load here.
"""
from __future__ import annotations

import os
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
PKG_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PKG_DIR.parent.parent           # pipelines/snowpack/
DATA = PROJECT_DIR / "data"
ORIGINAL = DATA / "original"
PROCESSED = DATA / "processed"
AUDIT = DATA / "audit"
LOOKUPS = DATA / "lookups"

CANONICAL_CSV = PROCESSED / "snowpack.csv"
PROVENANCE_CSV = PROCESSED / "provenance.csv"
MANIFEST = ORIGINAL / "manifest.json"
SOURCES_YAML = LOOKUPS / "sources.yaml"
CONCEPTS_YAML = LOOKUPS / "concepts.yaml"
SITES_CSV = LOOKUPS / "sites.csv"

# ── HTTP defaults ────────────────────────────────────────────────────────────
USER_AGENT = (
    "co-environmental-data/snowpack (CUPIDS Lab; "
    "https://github.com/CUPIDS-Lab/co-environmental-data; accounts@brianckeegan.com)"
)
REQUEST_TIMEOUT = 120        # seconds — a full-POR AWDB station response can be ~1 MB
# Polite delay between requests + retry budget, both env-overridable. AWDB has not
# been observed to throttle, but the back-off is cheap insurance for a full-state pull.
RATE_LIMIT_SECONDS = float(os.environ.get("SNOWPACK_RATE_LIMIT", "0.3"))
MAX_RETRIES = int(os.environ.get("SNOWPACK_MAX_RETRIES", "5"))


def load_sources_config() -> dict:
    """Read ``data/lookups/sources.yaml`` (endpoint + per-source params)."""
    import yaml  # local import so `py_compile` works without the dep

    with open(SOURCES_YAML, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get_sources() -> dict:
    """Instantiate the registered Source objects keyed by slug.

    Imported lazily to avoid a circular import (sources.py imports config).
    """
    from snowpack.sources import NrcsSnotel, NrcsSnowCourse

    return {s.name: s for s in (NrcsSnotel(), NrcsSnowCourse())}
