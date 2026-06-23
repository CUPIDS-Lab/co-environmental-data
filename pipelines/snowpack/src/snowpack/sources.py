"""Source registry: the contract every snowpack source obeys.

Two sources, multi-source from day one (issue #11) — but here BOTH come from the
SAME upstream, the **NRCS AWDB REST API**, differing only by network, duration,
and the per-value date field:

- ``nrcs_snotel`` — SNOTEL automated telemetry (network ``SNTL``); DAILY SWE,
  snow depth, and water-year precipitation accumulation; record since ~1980.
- ``nrcs_snowcourse`` — manual snow courses (network ``SNOW``); SEMIMONTHLY SWE
  and snow depth; the deep-history series (many CO courses back to the 1930s–40s).

The ``discover`` / ``ingest`` split (BoulderPublicData convention): ``discover``
is online — it asks "what series are available?" and yields ONE :class:`Artifact`
per station, requesting all of that source's elements at once (AWDB serves
multiple elements in a single response, so one request per station covers its
whole record). ``fetch.py`` performs the downloads. ``ingest`` is offline — it
reads a saved response from ``data/original/`` and dispatches to the parser.

⚠️ NOT a re-serve overlap: unlike streamflow's USGS↔DWR (same physical gage,
identical values), a SNOTEL and a snow course are NEARBY but DISTINCT sites. They
are complementary, not duplicate; the co-location reconciliation in ``audit.py``
treats their agreement as a (looser) accuracy check, not an identity.
"""
from __future__ import annotations

import datetime as _dt
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
from urllib.parse import urlencode

import pandas as pd

from snowpack import config


def _today_ymd() -> str:
    return _dt.date.today().strftime("%Y-%m-%d")


def _safe(triplet: str) -> str:
    """Filesystem-safe form of a station triplet (``713:CO:SNTL`` -> ``713_CO_SNTL``)."""
    return triplet.replace(":", "_")


@dataclass
class Artifact:
    """One downloadable unit from upstream (here: one station's full-POR response)."""

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
    def discover(self, sites: set[str] | None = None) -> Iterator[Artifact]:
        """Enumerate available artifacts upstream. Cheap; builds URLs, no downloads.

        ``sites`` optionally restricts to a subset of stations (the sampling hook —
        a handful of stations for a fast end-to-end run)."""

    @abstractmethod
    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        """Read the local saved response and return a canonical-schema frame."""

    # shared helpers ----------------------------------------------------------
    def _stations(self, sites: set[str] | None = None) -> pd.DataFrame:
        """Starter station list for this source, from the curated seed.

        Refresh/scale by re-running ``scripts/build_sites_seed.py`` (enumerates the
        AWDB station catalog). ``sites`` filters by ``site_id`` (the full triplet,
        e.g. ``713:CO:SNTL``) OR ``station_id`` (the bare id, e.g. ``713``) — so a
        short id is a convenient sampling key across both networks."""
        seed = pd.read_csv(config.SITES_CSV, dtype=str)
        sub = seed[seed["source"] == self.name].copy()
        if sites:
            keep = sub["site_id"].isin(sites) | sub["station_id"].isin(sites)
            sub = sub[keep].copy()
        return sub

    def _discover_awdb(self, sites: set[str] | None = None) -> Iterator[Artifact]:
        """Shared AWDB discovery: one Artifact per station, all elements at once."""
        cfg = config.load_sources_config()[self.name]
        base = cfg["base_url"].rstrip("/")
        endpoint = cfg["data_endpoint"]                   # data
        elements = ",".join(cfg["parameters"].values())  # e.g. WTEQ,SNWD,PREC
        duration = cfg["duration"]                        # DAILY | SEMIMONTHLY
        start = cfg.get("start_date") or "1900-01-01"
        end = cfg.get("end_date") or _today_ymd()
        for _, row in self._stations(sites).iterrows():
            triplet = row["site_id"]
            q = {
                "stationTriplets": triplet,
                "elements": elements,
                "duration": duration,
                "beginDate": start,                       # YYYY-MM-DD
                "endDate": end,
                "returnFlags": "true",                    # carry qcFlag + qaFlag
            }
            url = f"{base}/{endpoint}?{urlencode(q)}"
            local = config.ORIGINAL / self.name / "current" / f"{_safe(triplet)}.json"
            yield Artifact(self.name, "current", url, local,
                           {"site_id": triplet, "site_name": row.get("site_name"),
                            "duration": duration, "date_field": cfg["date_field"]})


# ─────────────────────────────────────────────────────────────────────────────
class NrcsSnotel(Source):
    name = "nrcs_snotel"
    label = "NRCS SNOTEL — automated snow telemetry (AWDB REST API)"
    license = "Public domain (U.S. federal — USDA NRCS)"

    def discover(self, sites: set[str] | None = None) -> Iterator[Artifact]:
        return self._discover_awdb(sites)

    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        from snowpack.parsers import nrcs_snotel
        return nrcs_snotel.parse(artifact.local_path, artifact)


# ─────────────────────────────────────────────────────────────────────────────
class NrcsSnowCourse(Source):
    name = "nrcs_snowcourse"
    label = "NRCS Snow Course / Aerial Marker — manual surveys (AWDB REST API)"
    license = "Public domain (U.S. federal — USDA NRCS)"

    def discover(self, sites: set[str] | None = None) -> Iterator[Artifact]:
        return self._discover_awdb(sites)

    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        from snowpack.parsers import nrcs_snowcourse
        return nrcs_snowcourse.parse(artifact.local_path, artifact)


# The registry. ``config.get_sources()`` instantiates these.
SOURCES: dict[str, type[Source]] = {
    NrcsSnotel.name: NrcsSnotel,
    NrcsSnowCourse.name: NrcsSnowCourse,
}
