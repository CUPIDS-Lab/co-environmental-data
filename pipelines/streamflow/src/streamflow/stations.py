"""Gage enumeration: build each source's station-catalog URL + parse it into the
seed (``data/lookups/sites.csv``).

The curated seed ships hand-picked major-river gages. These helpers are how you
*refresh* or *scale* it — e.g. swap the curated set for "all active CO discharge
gages." They build URLs and parse responses; the actual HTTP GET is the caller's
(keeps "no network on import" — see AGENTS.md). ``resolve_dwr_abbrev`` is also how
the seed's DWR rows are generated from a list of USGS site numbers (DWR re-serves
many USGS gages and exposes the cross-link via ``usgsSiteId``).
"""
from __future__ import annotations

import io

import pandas as pd

from streamflow import config

USGS_STATE_CO = "CO"


def usgs_site_list_url(state: str = USGS_STATE_CO, param_cd: str = "00060") -> str:
    """NWIS site service (RDB) — all stream gages in a state with daily values for
    a parameter. ``siteType=ST`` = stream; ``hasDataTypeCd=dv`` = has daily values."""
    cfg = config.load_sources_config()["usgs_nwis"]
    base = cfg["base_url"].rstrip("/")
    from urllib.parse import urlencode
    q = urlencode({"format": "rdb", "stateCd": state, "parameterCd": param_cd,
                   "siteType": "ST", "hasDataTypeCd": "dv", "siteStatus": "all"})
    return f"{base}/site/?{q}"


def parse_usgs_sites(rdb_text: str) -> pd.DataFrame:
    """Parse the NWIS site-service RDB (tab-separated, ``#`` comments, a type row
    under the header) into ``(source, site_id, site_name, usgs_site_no)``."""
    lines = [ln for ln in rdb_text.splitlines() if ln and not ln.startswith("#")]
    if len(lines) < 2:
        return pd.DataFrame(columns=["source", "site_id", "site_name", "usgs_site_no"])
    body = "\n".join([lines[0]] + lines[2:])  # drop the RDB type-definition row
    raw = pd.read_csv(io.StringIO(body), sep="\t", dtype=str)
    out = pd.DataFrame({
        "source": "usgs_nwis",
        "site_id": raw["site_no"],
        "site_name": raw["station_nm"],
        "usgs_site_no": raw["site_no"],
    })
    return out


def dwr_stations_url(water_district: str | None = None, county: str | None = None) -> str:
    """CDSS surface-water station catalog URL (optionally scoped)."""
    cfg = config.load_sources_config()["dwr_cdss"]
    base = cfg["base_url"].rstrip("/")
    from urllib.parse import urlencode
    q = {"format": "json", "pageSize": 50000}
    if water_district:
        q["waterDistrict"] = water_district
    if county:
        q["county"] = county
    return f"{base}/surfacewater/surfacewaterstations/?{urlencode(q)}"


def resolve_dwr_abbrev_url(usgs_site_no: str) -> str:
    """URL that resolves a USGS site number to its CDSS surface-water station
    (abbrev) — the cross-link that lets one curated USGS list seed both sources."""
    cfg = config.load_sources_config()["dwr_cdss"]
    base = cfg["base_url"].rstrip("/")
    from urllib.parse import urlencode
    return (f"{base}/surfacewater/surfacewaterstations/?"
            f"{urlencode({'format': 'json', 'usgsSiteId': usgs_site_no})}")


def parse_dwr_stations(payload: dict) -> pd.DataFrame:
    """Parse a CDSS surfacewaterstations response into
    ``(source, site_id, site_name, usgs_site_no)`` rows (site_id = abbrev)."""
    rows = payload.get("ResultList", []) or []
    recs = [{
        "source": "dwr_cdss",
        "site_id": r.get("abbrev"),
        "site_name": r.get("stationName"),
        "usgs_site_no": r.get("usgsSiteId") or None,
    } for r in rows if r.get("abbrev")]
    return pd.DataFrame(recs, columns=["source", "site_id", "site_name", "usgs_site_no"])


def merge_into_seed(frames: list[pd.DataFrame], basin_lookup: dict | None = None) -> pd.DataFrame:
    """Concatenate per-source station frames into the ``sites.csv`` shape, de-duped
    on ``(source, site_id)``. ``basin_lookup`` optionally maps site_id → basin."""
    cols = ["source", "site_id", "site_name", "basin", "usgs_site_no", "notes"]
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=cols)
    if "basin" not in df.columns:
        df["basin"] = ""
    if basin_lookup:
        df["basin"] = df["site_id"].map(basin_lookup).fillna(df["basin"])
    if "notes" not in df.columns:
        df["notes"] = ""
    df = df.drop_duplicates(["source", "site_id"]).reset_index(drop=True)
    return df[cols]
