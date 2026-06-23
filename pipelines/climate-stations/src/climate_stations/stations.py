"""Station enumeration: build the CDSS climate-station catalog URL + parse it into
the seed (``data/lookups/stations.csv``).

The curated seed ships a manageable, **active** cross-section of stations across
networks and water divisions. These helpers are how you *refresh* or *scale* it —
e.g. swap the curated set for "all ~12,700 CO climate stations." They build URLs
and parse responses; the actual HTTP GET is the caller's (keeps "no network on
import" — see AGENTS.md).

``site_id`` is the CDSS ``stationNum`` (a stable integer id). ``network`` is the
``dataSource`` (NOAA / CoCoRaHS / NRCS / CoAgMet / NCWCD); ``site_id_network`` is
the network-native id (GHCN ``siteId``), the join key for the SNOTEL / GHCN
crosswalk (relates to snowpack issue #11).
"""
from __future__ import annotations

from urllib.parse import urlencode

import pandas as pd

from climate_stations import config

STATION_COLUMNS = [
    "source", "site_id", "site_name", "network", "site_id_network",
    "division", "water_district", "county", "latitude", "longitude",
    "start_date", "end_date", "notes",
]


def climate_stations_url(county: str | None = None, water_district: str | None = None,
                         division: str | None = None, page_size: int = 50000,
                         page_index: int = 1) -> str:
    """CDSS climate-station catalog URL (optionally scoped by county / district /
    division). The key is appended when configured (anonymous limits apply)."""
    cfg = config.load_sources_config()["cdss_climate"]
    base = cfg["base_url"].rstrip("/")
    q = {"format": "json", "pageSize": page_size, "pageIndex": page_index}
    if county:
        q["county"] = county
    if water_district:
        q["waterDistrict"] = water_district
    if division:
        q["division"] = division
    if config.CDSS_API_KEY:
        q["apiKey"] = config.CDSS_API_KEY
    return f"{base}/climatedata/climatestations/?{urlencode(q)}"


def parse_climate_stations(payload: dict) -> pd.DataFrame:
    """Parse a CDSS ``climatestations`` response into the ``stations.csv`` shape."""
    rows = payload.get("ResultList", []) or []
    recs = []
    for r in rows:
        if r.get("stationNum") is None:
            continue
        recs.append({
            "source": "cdss_climate",
            "site_id": str(r.get("stationNum")),
            "site_name": (r.get("stationName") or "").strip(),
            "network": (r.get("dataSource") or "").strip(),
            "site_id_network": r.get("siteId") or "",
            "division": r.get("division"),
            "water_district": r.get("waterDistrict"),
            "county": (r.get("county") or "").strip(),
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "start_date": (r.get("startDate") or "")[:10],
            "end_date": (r.get("endDate") or "")[:10],
            "notes": "",
        })
    return pd.DataFrame(recs, columns=STATION_COLUMNS)


def select_active(df: pd.DataFrame, since: str = "2024-01-01") -> pd.DataFrame:
    """Keep stations whose period of record extends to/after ``since`` — the default
    pull is the active subset; full history is still retrieved per retained station."""
    return df[df["end_date"].fillna("") >= since].copy()


def curate_seed(df: pd.DataFrame, per_network: int = 8,
                since: str = "2024-01-01") -> pd.DataFrame:
    """Down-select an *active* cross-section: up to ``per_network`` stations from
    each network, spread across water divisions, for a committed seed that exercises
    every network and unit without pulling all ~12,700 stations. Deterministic
    (sorts by division then site_id; no randomness)."""
    active = select_active(df, since=since)
    picks = []
    for _network, grp in active.groupby("network", dropna=False):
        grp = grp.sort_values(["division", "site_id"])
        # spread across divisions: round-robin one per division until we hit the cap
        by_div = [g for _, g in grp.groupby("division", dropna=False)]
        i, taken = 0, []
        while len(taken) < min(per_network, len(grp)) and by_div:
            g = by_div[i % len(by_div)]
            if len(g):
                taken.append(g.iloc[0])
                by_div[i % len(by_div)] = g.iloc[1:]
            by_div = [g for g in by_div if len(g)]
            if not by_div:
                break
            i += 1
        picks.extend(taken)
    out = pd.DataFrame(picks, columns=STATION_COLUMNS) if picks else pd.DataFrame(columns=STATION_COLUMNS)
    return out.drop_duplicates(["source", "site_id"]).reset_index(drop=True)


def merge_into_seed(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate per-scope station frames into the ``stations.csv`` shape, de-duped
    on ``(source, site_id)``."""
    df = (pd.concat(frames, ignore_index=True) if frames
          else pd.DataFrame(columns=STATION_COLUMNS))
    return df.drop_duplicates(["source", "site_id"]).reset_index(drop=True)[STATION_COLUMNS]
