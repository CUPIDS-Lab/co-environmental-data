"""Source registry: the contract every streamflow source obeys.

Two sources, multi-source from day one (issue #10) — mirroring the
``reservoir-storage`` pipeline's state + federal split:

- ``usgs_nwis`` — USGS National Water Information System daily-values service
  (federal; the national streamflow record, deepest history).
- ``dwr_cdss`` — CO DWR / CDSS surface-water daily time series (state).

The ``discover`` / ``ingest`` split (BoulderPublicData convention): ``discover``
is online — it asks "what time series are available?" and yields one
:class:`Artifact` per (gage × variable) request, with the fully-built API URL.
``fetch.py`` performs the downloads. ``ingest`` is offline — it reads a saved
response from ``data/original/`` and dispatches to the matching parser.

⚠️ OVERLAP, not redundancy: DWR frequently re-serves the USGS gage (its
``dataSource`` is literally ``USGS``). The same physical gage therefore appears
under BOTH source slugs, joined by ``usgs_site_no`` in ``sites.csv``. ``source``
is in the composite key, so the two stay distinct rows; the concept catalog
caveats how to compare them (``data/lookups/concepts.yaml``).
"""
from __future__ import annotations

import datetime as _dt
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
from urllib.parse import urlencode

import pandas as pd

from streamflow import config


def _today_ymd() -> str:
    return _dt.date.today().strftime("%Y-%m-%d")


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
    def discover(self, sites: set[str] | None = None) -> Iterator[Artifact]:
        """Enumerate available artifacts upstream. Cheap; builds URLs, no downloads.

        ``sites`` optionally restricts to a subset of ``site_id`` values (the
        sampling hook — a handful of gages for a fast end-to-end run)."""

    @abstractmethod
    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        """Read the local saved response and return a canonical-schema frame."""

    # shared helper -----------------------------------------------------------
    def _stations(self, sites: set[str] | None = None) -> pd.DataFrame:
        """Starter gage list for this source, from the curated seed.

        Replace/extend by running the enumeration step in ``streamflow.stations``
        (each API exposes a station catalog). ``sites`` filters by ``site_id`` OR
        ``usgs_site_no`` — so a USGS site number selects BOTH that USGS gage and the
        DWR station that re-serves it (the two sources use different id namespaces:
        USGS numbers vs DWR abbrevs). That is what makes the cross-link usable as a
        single sampling key."""
        seed = pd.read_csv(config.SITES_CSV, dtype=str)
        sub = seed[seed["source"] == self.name].copy()
        if sites:
            keep = sub["site_id"].isin(sites) | sub["usgs_site_no"].isin(sites)
            sub = sub[keep].copy()
        return sub


# ─────────────────────────────────────────────────────────────────────────────
class UsgsNwis(Source):
    name = "usgs_nwis"
    label = "USGS National Water Information System (waterservices.usgs.gov)"
    license = "Public domain (U.S. federal — USGS)"

    def discover(self, sites: set[str] | None = None) -> Iterator[Artifact]:
        cfg = config.load_sources_config()[self.name]
        base = cfg["base_url"].rstrip("/")
        endpoint = cfg["dv_endpoint"]                    # dv/
        params_for = cfg["parameters"]                   # {"discharge_cfs": "00060"}
        stat_cd = cfg.get("stat_cd", "00003")            # daily mean
        start = cfg.get("start_date") or "1900-01-01"
        end = cfg.get("end_date") or _today_ymd()
        for _, row in self._stations(sites).iterrows():
            for variable, param_cd in params_for.items():
                q = {
                    "format": "json",
                    "sites": row["site_id"],             # USGS site number (e.g. 09095500)
                    "parameterCd": param_cd,             # 00060 = discharge
                    "statCd": stat_cd,                   # 00003 = daily mean
                    "startDT": start,                    # YYYY-MM-DD
                    "endDT": end,
                }
                url = f"{base}/{endpoint}?{urlencode(q)}"
                local = config.ORIGINAL / self.name / "current" / f"{row['site_id']}_{param_cd}.json"
                yield Artifact(self.name, "current", url, local,
                               {"site_id": row["site_id"], "site_name": row["site_name"],
                                "variable": variable, "param_cd": param_cd})

    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        from streamflow.parsers import usgs_nwis
        return usgs_nwis.parse(artifact.local_path, artifact)


# ─────────────────────────────────────────────────────────────────────────────
class DwrCdss(Source):
    name = "dwr_cdss"
    label = "Colorado DWR / CDSS surface water (HydroBase REST API v2)"
    license = "Public / 'as-is' (Colorado DWR; no warranty, indemnification)"

    def discover(self, sites: set[str] | None = None) -> Iterator[Artifact]:
        cfg = config.load_sources_config()[self.name]
        base = cfg["base_url"].rstrip("/")
        endpoint = cfg["timeseries_endpoint"]            # surfacewater/surfacewatertsday/
        params_for = cfg["parameters"]                   # {"discharge_cfs": "Streamflow"}
        page_size = cfg.get("page_size", 50000)
        # FULL HISTORY per gage. Surface-water daily uses min-measDate / max-measDate
        # (MM/DD/YYYY) — NOT startDate/endDate (that endpoint quirk differs from the
        # telemetry endpoint the reservoir pipeline used). CDSS clamps to each
        # station's period of record.
        start = cfg.get("start_date") or "01/01/1900"
        end = cfg.get("end_date") or _today_mmddyyyy()
        for _, row in self._stations(sites).iterrows():
            for variable, meas_type in params_for.items():
                q = {
                    "format": "json",
                    "abbrev": row["site_id"],            # CDSS station abbreviation (e.g. CLAFORCO)
                    "measType": meas_type,               # "Streamflow" (confirmed live)
                    "min-measDate": start,               # MM/DD/YYYY
                    "max-measDate": end,
                    "pageSize": page_size,
                }
                if config.CDSS_API_KEY:
                    q["apiKey"] = config.CDSS_API_KEY
                url = f"{base}/{endpoint}?{urlencode(q)}"
                local = config.ORIGINAL / self.name / "current" / f"{row['site_id']}_{meas_type}.json"
                yield Artifact(self.name, "current", url, local,
                               {"site_id": row["site_id"], "site_name": row["site_name"],
                                "variable": variable, "meas_type": meas_type})

    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        from streamflow.parsers import dwr_cdss
        return dwr_cdss.parse(artifact.local_path, artifact)


# The registry. ``config.get_sources()`` instantiates these.
SOURCES: dict[str, type[Source]] = {
    UsgsNwis.name: UsgsNwis,
    DwrCdss.name: DwrCdss,
}
