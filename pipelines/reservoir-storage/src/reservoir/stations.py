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
import re
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd

from reservoir import config

SEED_COLUMNS = ["source", "reservoir_id", "reservoir_name", "basin", "rise_item_ids",
                "latitude", "longitude", "elevation_ft", "county", "start_date",
                "end_date", "notes"]


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
        # RISE enumeration is two-step per reservoir: rise_location_search_url(name)
        # -> pick the Lake/Reservoir match -> rise_location_items_url(id) ->
        # parse_rise_location_items(). This is the search entry point.
        return rise_location_search_url("Reservoir", cfg["reclamation_rise"]["base_url"])
    if slug == "northern_water":
        # No storage service exists (hub = boundaries only) -> nothing to enumerate.
        svc = (cfg["northern_water"].get("feature_service_url") or "").rstrip("/")
        return f"{svc}/query?where=1%3D1&outFields=*&returnGeometry=false&f=json" if svc else ""
    raise ValueError(f"no enumeration url for source {slug!r}")


def parse_dwr_stations(path: Path) -> pd.DataFrame:
    """CDSS telemetrystation list → reservoir seed rows (with station metadata).

    Response shape: ``{"ResultList": [{"abbrev", "stationName", "waterDistrict",
    "latitude", "longitude", "county", "stationPorStart", "stationPorEnd", …}]}``.
    The telemetrystation record has no elevation — that stays blank for CDSS rows
    (reservoir pool elevation is a measured variable, not static station metadata;
    RISE-sourced rows do carry a fixed elevation).
    """
    payload = json.loads(Path(path).read_text())
    rows = []
    for r in payload.get("ResultList", []) or []:
        # The API's `parameter` query filter is unreliable; filter client-side to
        # the reservoir-storage stations.
        if (r.get("parameter") or "") != "STORAGE":
            continue
        rows.append({
            "source": "dwr_cdss",
            "reservoir_id": r.get("abbrev"),
            "reservoir_name": r.get("stationName"),
            "basin": r.get("waterDistrict") or r.get("division"),
            "rise_item_ids": "",
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "elevation_ft": None,
            "county": (r.get("county") or "").strip().title() or None,
            "start_date": (r.get("stationPorStart") or "")[:10] or None,
            "end_date": (r.get("stationPorEnd") or "")[:10] or None,
            "notes": "auto-enumerated (CDSS telemetrystation, STORAGE)",
        })
    return pd.DataFrame(rows, columns=SEED_COLUMNS)


# ── RISE enumeration (confirmed live) ────────────────────────────────────────
# RISE filtering by locationId/search is unreliable; the reliable path is the
# JSON:API relationship traversal: location (type Lake/Reservoir) ->
# catalogRecords -> catalogItems, fetched in one call with ?include=. Each item's
# parameterName maps to a canonical variable; the item id goes in rise_item_ids.
RISE_PARAM_MAP = {
    "Lake/Reservoir Storage": "storage_af",
    "Lake/Reservoir Elevation": "elevation_ft",
    "Lake/Reservoir Release - Total": "release_cfs",
}
RISE_API = "https://data.usbr.gov/rise/api"


def rise_location_search_url(name: str, base: str | None = None) -> str:
    """Text-search RISE locations. Caller picks the result whose
    ``locationTypeName`` is 'Lake/Reservoir' and whose name contains the keyword."""
    from urllib.parse import quote
    return f"{(base or RISE_API).rstrip('/')}/location?search={quote(name)}&itemsPerPage=25"


def rise_location_items_url(location_id: str | int, base: str | None = None) -> str:
    """One call returns the whole catalog tree (records -> items) for a location."""
    return f"{(base or RISE_API).rstrip('/')}/location/{location_id}?include=catalogRecords.catalogItems"


def parse_rise_location_items(payload: dict) -> dict:
    """From a ``location/<id>?include=catalogRecords.catalogItems`` response, return
    ``{canonical_variable: item_id}`` for storage/elevation/release. These ids go in
    ``reservoirs.csv:rise_item_ids`` and drive ``ReclamationRise.discover``."""
    out: dict[str, int] = {}
    for x in payload.get("included", []) or []:
        if "catalog-item" not in (x.get("id") or ""):
            continue
        var = RISE_PARAM_MAP.get(x.get("attributes", {}).get("parameterName") or "")
        m = re.search(r"/catalog-item/(\d+)", x.get("id", ""))
        if var and m and var not in out:
            out[var] = int(m.group(1))
    return out


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
