"""Source registry: the contract every reservoir-storage source obeys.

Three sources, multi-source from day one (issue #9):

- ``dwr_cdss``        — CO DWR / CDSS REST API v2 (statewide; state-controlled).
- ``reclamation_rise``— USBR Reclamation RISE API (Colorado River reservoirs).
- ``northern_water``  — Northern Water ArcGIS Hub FeatureServer (C-BT system).

The ``discover`` / ``ingest`` split (BoulderPublicData convention): ``discover``
is online — it asks "what time series are available?" and yields one
:class:`Artifact` per (reservoir × variable) request, with the fully-built API
URL. ``fetch.py`` performs the downloads. ``ingest`` is offline — it reads a
saved response from ``data/original/`` and dispatches to the matching parser.

⚠️ VERIFY-AGAINST-LIVE-API markers below flag the few endpoint/parameter details
that should be confirmed against the live service on the first real run. The
request *machinery* (paging, JSON shapes, hashing, provenance) is correct; the
exact catalog item IDs, parameter codes, and the Northern Water service URL are
the operator's first-run confirmation (tracked in ``docs/survey-notes.md``).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
from urllib.parse import urlencode

import pandas as pd

from reservoir import config


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
    def discover(self) -> Iterator[Artifact]:
        """Enumerate available artifacts upstream. Cheap; builds URLs, no downloads."""

    @abstractmethod
    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        """Read the local saved response and return a canonical-schema frame."""

    def enumeration_url(self) -> str:
        """Upstream catalog/station-list query that enumerates this source's
        reservoirs (see ``reservoir.stations``). Used to refresh the seed list."""
        from reservoir import stations
        return stations.station_list_url(self.name)

    # shared helper -----------------------------------------------------------
    def _stations(self) -> pd.DataFrame:
        """Starter reservoir list for this source, from the crosswalk seed.

        Replace/extend by running the full enumeration step documented in
        ``docs/survey-notes.md`` (each API exposes a catalog/stations endpoint).
        """
        seed = pd.read_csv(config.LOOKUPS / "reservoirs.csv", dtype=str)
        return seed[seed["source"] == self.name].copy()


# ─────────────────────────────────────────────────────────────────────────────
class DwrCdss(Source):
    name = "dwr_cdss"
    label = "Colorado DWR / CDSS (HydroBase REST API v2)"
    license = "Public / 'as-is' (Colorado DWR; no warranty, indemnification)"

    def discover(self) -> Iterator[Artifact]:
        cfg = config.load_sources_config()[self.name]
        base = cfg["base_url"].rstrip("/")
        endpoint = cfg["timeseries_endpoint"]           # telemetrystations/telemetrytimeseriesday/
        params_for = cfg["parameters"]                  # {"storage_af": "STORAGE", "elevation_ft": "ELEV"}
        # No startDate by default: CDSS returns zero records (HTTP 404) when
        # startDate predates a station's record, and a large pageSize returns the
        # full available history regardless. Set start_date in sources.yaml
        # (format MM/DD/YYYY) only to window a query.
        start = cfg.get("start_date") or ""
        for _, row in self._stations().iterrows():
            for _var, abbrev_param in params_for.items():
                q = {
                    "format": "json",
                    "abbrev": row["reservoir_id"],     # CDSS station abbreviation (e.g. GRERESCO)
                    "parameter": abbrev_param,         # STORAGE | ELEV (confirmed live)
                    "pageSize": 50000,
                }
                if start:
                    q["startDate"] = start
                if config.CDSS_API_KEY:
                    q["apiKey"] = config.CDSS_API_KEY
                url = f"{base}/{endpoint}?{urlencode(q)}"
                local = config.ORIGINAL / self.name / "current" / f"{row['reservoir_id']}_{abbrev_param}.json"
                yield Artifact(self.name, "current", url, local,
                               {"reservoir_id": row["reservoir_id"],
                                "reservoir_name": row["reservoir_name"], "param": abbrev_param})

    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        from reservoir.parsers import dwr_cdss
        return dwr_cdss.parse(artifact.local_path, artifact)


# ─────────────────────────────────────────────────────────────────────────────
class ReclamationRise(Source):
    name = "reclamation_rise"
    label = "USBR Reclamation RISE / HydroData (data.usbr.gov/rise/api)"
    license = "Public domain (U.S. federal)"

    def discover(self) -> Iterator[Artifact]:
        # Note: the human portal is rise.reclamation.gov; the API host is
        # data.usbr.gov/rise/api (JSON:API). Each reservoir variable is a RISE
        # "catalog item"; we pull its /result time series by itemId.
        cfg = config.load_sources_config()[self.name]
        base = cfg["base_url"].rstrip("/")
        start = cfg.get("start_date", "1900-01-01")
        for _, row in self._stations().iterrows():
            # reservoirs.csv carries the RISE catalog item id per variable in
            # the `rise_item_ids` JSON column (e.g. {"storage_af": 1234}).
            import json
            item_ids = json.loads(row.get("rise_item_ids") or "{}")  # ⚠️ VERIFY item IDs
            for _var, item_id in item_ids.items():
                if not item_id:
                    continue  # placeholder not yet filled — skip until the item id is confirmed
                q = {"itemId": item_id, "dateTime[after]": start, "page[size]": 10000}
                url = f"{base}/result?{urlencode(q)}"
                local = config.ORIGINAL / self.name / "current" / f"item_{item_id}.json"
                yield Artifact(self.name, "current", url, local,
                               {"reservoir_id": row["reservoir_id"],
                                "reservoir_name": row["reservoir_name"], "variable": _var})

    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        from reservoir.parsers import reclamation_rise
        return reclamation_rise.parse(artifact.local_path, artifact)


# ─────────────────────────────────────────────────────────────────────────────
class NorthernWater(Source):
    name = "northern_water"
    label = "Northern Water (ArcGIS Hub FeatureServer)"
    license = "Public (verify per dataset)"

    def discover(self) -> Iterator[Artifact]:
        # FINDING: Northern Water's ArcGIS Hub has boundaries only — no reservoir-
        # storage FeatureServer. With no service URL configured this yields nothing
        # (the C-BT reservoirs it operates are sourced from RISE). Kept so a real-time
        # service can be slotted in later by setting feature_service_url in sources.yaml.
        cfg = config.load_sources_config()[self.name]
        service = (cfg.get("feature_service_url") or "").rstrip("/")
        if not service:
            return
        q = {"where": "1=1", "outFields": "*", "f": "json", "resultRecordCount": 2000}
        url = f"{service}/query?{urlencode(q)}"
        local = config.ORIGINAL / self.name / "current" / "reservoirs_featureserver.json"
        yield Artifact(self.name, "current", url, local, {"service": service})

    def ingest(self, artifact: Artifact) -> pd.DataFrame:
        from reservoir.parsers import northern_water
        return northern_water.parse(artifact.local_path, artifact)


# The registry. ``config.get_sources()`` instantiates these.
SOURCES: dict[str, type[Source]] = {
    DwrCdss.name: DwrCdss,
    ReclamationRise.name: ReclamationRise,
    NorthernWater.name: NorthernWater,
}
