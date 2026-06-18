"""Reservoir enumeration — populate the full Colorado reservoir list from the
sources' own station/catalog endpoints, instead of hand-typing it.

``data/lookups/reservoirs.csv`` ships a curated *seed*; a live first run calls
:func:`station_list_url` per source, fetches the catalog, and
:func:`parse_dwr_stations` (etc.) turns it into reservoir rows that
:func:`merge_into_seed` folds back into the CSV. This is how the "full
enumeration" stays current without a maintainer retyping it.

DWR/CDSS is implemented and fixture-tested (it is the statewide source). RISE and
Northern Water enumeration URLs are built here too; their response parsers are
documented in ``docs/survey-notes.md`` and land once the ``⚠️ VERIFY`` endpoint
details are confirmed on the first live run.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd

from reservoir import config

SEED_COLUMNS = ["source", "reservoir_id", "reservoir_name", "basin", "rise_item_ids", "notes"]


def station_list_url(slug: str, cfg: dict | None = None) -> str:
    """Build the upstream enumeration query for a source (no network here)."""
    cfg = cfg or config.load_sources_config()
    if slug == "dwr_cdss":
        base = cfg["dwr_cdss"]["base_url"].rstrip("/")
        q = {"format": "json", "parameter": "STORAGE", "pageSize": 50000}  # reservoirs report STORAGE
        if config.CDSS_API_KEY:
            q["apiKey"] = config.CDSS_API_KEY
        return f"{base}/telemetrystations/telemetrystation/?{urlencode(q)}"
    if slug == "reclamation_rise":
        base = cfg["reclamation_rise"]["base_url"].rstrip("/")
        # RISE catalog items for the reservoir-storage parameter, Colorado. ⚠️ VERIFY filters.
        q = {"page[size]": 100, "itemStructureId": 1}
        return f"{base}/catalog-item?{urlencode(q)}"
    if slug == "northern_water":
        return cfg["northern_water"]["feature_service_url"].rstrip("/") + \
            "/query?where=1%3D1&outFields=*&returnGeometry=false&f=json"
    raise ValueError(f"no enumeration url for source {slug!r}")


def parse_dwr_stations(path: Path) -> pd.DataFrame:
    """CDSS telemetrystation list → reservoir seed rows.

    Response shape: ``{"ResultList": [{"abbrev", "stationName", "waterDistrict", …}]}``.
    """
    payload = json.loads(Path(path).read_text())
    rows = []
    for r in payload.get("ResultList", []) or []:
        rows.append({
            "source": "dwr_cdss",
            "reservoir_id": r.get("abbrev"),
            "reservoir_name": r.get("stationName"),
            "basin": r.get("waterDistrict") or r.get("division"),
            "rise_item_ids": "",
            "notes": "auto-enumerated (CDSS telemetrystation, parameter=STORAGE)",
        })
    return pd.DataFrame(rows, columns=SEED_COLUMNS)


def merge_into_seed(new_rows: pd.DataFrame, seed_path: Path | None = None,
                    write: bool = True) -> pd.DataFrame:
    """Union new reservoir rows into reservoirs.csv, de-duped on (source, reservoir_id)."""
    seed_path = seed_path or (config.LOOKUPS / "reservoirs.csv")
    existing = pd.read_csv(seed_path, dtype=str) if seed_path.exists() else pd.DataFrame(columns=SEED_COLUMNS)
    merged = (pd.concat([existing, new_rows.astype(str)], ignore_index=True)
              .drop_duplicates(["source", "reservoir_id"], keep="first")
              .sort_values(["source", "reservoir_id"]).reset_index(drop=True))
    if write:
        merged.to_csv(seed_path, index=False)
    return merged
