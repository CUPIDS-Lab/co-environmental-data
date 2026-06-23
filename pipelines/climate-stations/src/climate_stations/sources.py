"""Source registry: the contract the climate-station source obeys.

One API source — ``cdss_climate``, the CO DWR / CDSS Climate Station Time Series
(day) endpoint — but it federates **many observing networks** behind a single
contract: each row carries a ``dataSource`` (NOAA COOP/GHCN, CoCoRaHS citizen
observers, NRCS/SNOTEL, CoAgMet, NCWCD). The network is a *station* attribute,
recorded in ``data/lookups/stations.csv`` (the dimension table), not on every row.

The ``discover`` / ``ingest`` split (BoulderPublicData convention): ``discover``
is online-shaped — it asks "what daily series are available?" and yields one
:class:`Artifact` per **(station × measType)** request, with the fully-built API
URL. ``fetch.py`` performs the downloads. ``ingest`` is offline — it reads a saved
response from ``data/original/`` and dispatches to the parser.

The daily endpoint requires a station identifier (``stationNum`` or ``siteId``) —
a measType-only query is rejected (``Error: (stationNum or siteId) required``), so
enumeration is inherently per-station. One ``measType`` per request, so a station
with N requested measures costs N requests, each clamped server-side to that
station's period of record.
"""
from __future__ import annotations

import datetime as _dt
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
from urllib.parse import urlencode

import pandas as pd

from climate_stations import config, schema


def _today_mmddyyyy() -> str:
    return _dt.date.today().strftime("%m/%d/%Y")


@dataclass
class Artifact:
    """One downloadable unit from upstream (here: one API response)."""

    source: str
    vintage: str
    url: str
    local_path: Path
    metadata: dict = field(default_factory=dict)


class Source(ABC):
    name: str            # registry slug; matches data/original/<name>/
    label: str           # human-readable
    license: str         # source's own license (propagated to provenance)

    @abstractmethod
    def discover(self, sites: set[str] | None = None,
                 meas_types: set[str] | None = None) -> Iterator[Artifact]:
        """Enumerate available artifacts upstream. Cheap; builds URLs, no downloads.

        ``sites`` optionally restricts to a subset of ``site_id`` (stationNum)
        values — the sampling hook for a fast end-to-end run over a handful of
        stations. ``meas_types`` optionally restricts to a subset of CDSS measTypes
        (e.g. just the water-relevant ``Precip``/``SnowSWE``) for a cheaper pull."""

    @abstractmethod
    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        """Read the local saved response and return a canonical-schema frame."""

    # shared helper -----------------------------------------------------------
    def _stations(self, sites: set[str] | None = None) -> pd.DataFrame:
        """Starter station list for this source, from the curated seed.

        Replace/extend by running the enumeration step in ``climate_stations.stations``
        (the CDSS climate catalog has ~12,700 CO stations). ``sites`` filters by
        ``site_id`` (the CDSS stationNum)."""
        seed = pd.read_csv(config.STATIONS_CSV, dtype=str)
        sub = seed[seed["source"] == self.name].copy()
        if sites:
            sub = sub[sub["site_id"].isin(sites)].copy()
        return sub


# ─────────────────────────────────────────────────────────────────────────────
class CdssClimate(Source):
    name = "cdss_climate"
    label = "Colorado DWR / CDSS climate stations (HydroBase REST API v2)"
    license = "Public / 'as-is' (Colorado DWR; no warranty, indemnification)"

    def discover(self, sites: set[str] | None = None,
                 meas_types: set[str] | None = None) -> Iterator[Artifact]:
        cfg = config.load_sources_config()[self.name]
        base = cfg["base_url"].rstrip("/")
        endpoint = cfg["timeseries_endpoint"]            # climatedata/climatestationtsday/
        all_types = cfg.get("meas_types", list(schema.MEAS_MAP))
        types = [m for m in all_types if not meas_types or m in meas_types]
        page_size = cfg.get("page_size", 50000)
        # FULL HISTORY per station. The daily endpoint uses min-measDate / max-measDate
        # (MM/DD/YYYY) — NOT startDate/endDate. CDSS clamps to each station's period of
        # record, so an early start bound is harmless.
        start = cfg.get("start_date") or "01/01/1900"
        end = cfg.get("end_date") or _today_mmddyyyy()
        for _, row in self._stations(sites).iterrows():
            station_num = row["site_id"]                 # CDSS stationNum (stable id)
            for meas_type in types:
                variable, concept, _unit = schema.MEAS_MAP[meas_type]
                q = {
                    "format": "json",
                    "stationNum": station_num,
                    "measType": meas_type,               # one measType per request
                    "min-measDate": start,               # MM/DD/YYYY (NOT startDate)
                    "max-measDate": end,
                    "pageSize": page_size,
                }
                if config.CDSS_API_KEY:
                    q["apiKey"] = config.CDSS_API_KEY
                url = f"{base}/{endpoint}?{urlencode(q)}"
                local = config.ORIGINAL / self.name / "current" / f"{station_num}_{meas_type}.json"
                yield Artifact(self.name, "current", url, local,
                               {"site_id": station_num,
                                "site_name": row.get("site_name"),
                                "network": row.get("network"),
                                "variable": variable, "meas_type": meas_type})

    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        from climate_stations.parsers import cdss_climate
        return cdss_climate.parse(artifact.local_path, artifact)


# The registry. ``config.get_sources()`` instantiates these.
SOURCES: dict[str, type[Source]] = {
    CdssClimate.name: CdssClimate,
}
