"""Station enumeration: build the AWDB station-catalog URL + parse it into the
seed (``data/lookups/sites.csv``), and derive each station's major river basin
from its HUC.

The committed seed ships ALL active CO SNOTEL + snow-course stations (a small,
enumerable universe — unlike the 12k-station CDSS climate catalog of #44), so the
default pull is full-state coverage, not a sample. These helpers are how you
*refresh* it or *scale* it to discontinued stations (``active_only=False`` for even
deeper history). They build URLs and parse responses; the actual HTTP GET is the
caller's (keeps "no network on import" — see AGENTS.md).
"""
from __future__ import annotations

from urllib.parse import urlencode

import pandas as pd

from snowpack import config

# source slug ↔ AWDB network code
NETWORK_TO_SOURCE = {"SNTL": "nrcs_snotel", "SNOW": "nrcs_snowcourse"}

SEED_COLUMNS = [
    "source", "site_id", "station_id", "site_name", "basin", "network",
    "huc", "elevation_ft", "latitude", "longitude", "county", "begin_date",
    "end_date", "notes",
]


def awdb_stations_url(network: str, state: str = "CO", active_only: bool = True) -> str:
    """AWDB station-catalog URL for one network in a state.

    ``network`` is the AWDB code (``SNTL`` SNOTEL, ``SNOW`` snow course). The
    ``stationTriplets`` wildcard ``*:CO:SNTL`` selects every station of that network
    in the state."""
    cfg = config.load_sources_config()
    # both sources share the AWDB base; pick whichever maps to this network
    src = NETWORK_TO_SOURCE.get(network, "nrcs_snotel")
    base = cfg[src]["base_url"].rstrip("/")
    endpoint = cfg[src]["stations_endpoint"]
    q = {"stationTriplets": f"*:{state}:{network}", "activeOnly": str(active_only).lower()}
    return f"{base}/{endpoint}?{urlencode(q)}"


def huc_to_basin(huc: str | None) -> str:
    """Map a USGS HUC to a Colorado major river basin (the % -of-normal grouping).

    Derived crosswalk keyed on HUC4, with a HUC8 refinement to split the
    White–Yampa region (HUC 1405). NRCS's own basin definitions are the authority;
    this is a documented approximation used for aggregation — see concepts.yaml.
    """
    h = str(huc or "")
    h4, h8 = h[:4], h[:8]
    if h4 == "1405":  # White–Yampa region: split White from Yampa/Green
        return "White" if h8 in {"14050005", "14050006", "14050007"} else "Yampa-Green"
    if h4 in ("1406", "1407"):  # Green tributaries
        return "Yampa-Green"
    return {
        "1401": "Colorado", "1402": "Gunnison", "1403": "Dolores-San Miguel",
        "1408": "San Juan", "1301": "Rio Grande", "1302": "Rio Grande",
        "1019": "South Platte", "1018": "North Platte",
        "1102": "Arkansas", "1103": "Arkansas",
    }.get(h4, "Other")


def parse_awdb_stations(payload: list) -> pd.DataFrame:
    """Parse an AWDB ``stations`` response (a JSON array) into the seed shape.

    ``source`` is derived from each station's ``networkCode``; ``basin`` from its
    ``huc``; ``site_id`` is the full station triplet (the AWDB data-endpoint key)."""
    rows = payload if isinstance(payload, list) else []
    recs = []
    for s in rows:
        if not isinstance(s, dict):
            continue
        net = s.get("networkCode")
        triplet = s.get("stationTriplet")
        if not triplet or net not in NETWORK_TO_SOURCE:
            continue
        recs.append({
            "source": NETWORK_TO_SOURCE[net],
            "site_id": triplet,
            "station_id": s.get("stationId"),
            "site_name": s.get("name"),
            "basin": huc_to_basin(s.get("huc")),
            "network": net,
            "huc": s.get("huc"),
            "elevation_ft": s.get("elevation"),
            "latitude": s.get("latitude"),
            "longitude": s.get("longitude"),
            "county": s.get("countyName"),
            "begin_date": (s.get("beginDate") or "")[:10] or None,
            "end_date": (s.get("endDate") or "")[:10] or None,
            "notes": f"{net} station",
        })
    return pd.DataFrame(recs, columns=SEED_COLUMNS)


def merge_into_seed(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate per-network station frames into the ``sites.csv`` shape,
    de-duped on ``(source, site_id)`` and sorted by basin then name."""
    df = (pd.concat(frames, ignore_index=True) if frames
          else pd.DataFrame(columns=SEED_COLUMNS))
    df = df.drop_duplicates(["source", "site_id"])
    df = df.sort_values(["source", "basin", "site_name"], na_position="last").reset_index(drop=True)
    return df[SEED_COLUMNS]
