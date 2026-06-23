"""Parser for CO DWR / CDSS climate-station daily time series.

The CDSS REST API v2 ``climatedata/climatestationtsday`` returns (confirmed
against the live API)::

    {"ResultList": [
        {"stationNum": 18, "siteId": "USC00051342", "measType": "MaxTemp",
         "measDate": "1964-01-01T00:00:00-07:00", "value": 44.96,
         "flagA": null, "flagB": null, "flagC": "0", "flagD": "1700",
         "dataSource": "NOAA", "modified": "2013-03-29T15:42:35.24-06:00",
         "measUnit": "degF"}, ...],
     "ResultCount": 3}

``measType`` → canonical ``(variable, concept, unit)`` via ``schema.MEAS_MAP`` —
units differ by measure (``degF`` temps, ``in`` precip/snow/SWE/evap, ``mJ/m^2``
solar, ``kPa`` vapor pressure, ``KM`` wind run), so harmonization is per concept.
``flagA``..``flagD`` carry CDSS quality flags → ``qa_flag``.

Sentinel cleaning is **per variable**. A value ``<= -999`` is the missing/sentinel
encoding → NA for any measure. For non-negative-domain measures (precip, snow,
SWE, depth, evaporation, solar, wind run, vapor pressure) any negative is
impossible → NA. **Temperatures are left untouched** — sub-zero ``degF`` is real
Colorado winter data, not a sentinel.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from climate_stations import schema
from climate_stations.sources import Artifact

SENTINEL = -999.0  # CDSS missing/no-reading sentinel (also guards -9999 etc.)


def _clean_value(value, variable: str):
    """Map sentinels / impossible negatives to NA; preserve valid sub-zero temps."""
    if not isinstance(value, (int, float)):
        return None
    if value <= SENTINEL:                                  # universal missing sentinel
        return None
    if variable in schema.NON_NEGATIVE_VARS and value < 0:  # impossible for this measure
        return None
    return float(value)


def parse(path: Path, artifact: Artifact) -> pd.DataFrame:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):  # e.g. a stray "zero records" string sentinel
        return schema.normalize_long(pd.DataFrame(columns=schema.LONG_COLUMNS))
    rows = payload.get("ResultList", []) or []
    records = []
    for r in rows:
        meas = r.get("measType") or artifact.metadata.get("meas_type")
        variable, concept, unit = schema.MEAS_MAP.get(
            meas, (artifact.metadata.get("variable", "precip_in"),
                   "climate.precip_in", None))
        # Prefer the source-reported unit; fall back to the canonical unit for the
        # measure. (Confirmed identical for the sampled measTypes; this keeps a unit
        # variant from upstream visible rather than silently overwritten.)
        unit = r.get("measUnit") or unit
        flag = " ".join(
            str(r.get(k)).strip() for k in ("flagA", "flagB", "flagC", "flagD")
            if r.get(k) not in (None, "", "None")
        ).strip()
        station_num = r.get("stationNum")
        site_id = str(station_num) if station_num is not None else artifact.metadata.get("site_id")
        records.append({
            "source": "cdss_climate",
            "vintage": artifact.vintage,
            "site_id": site_id,
            "site_name": artifact.metadata.get("site_name"),
            "datetime": r.get("measDate") or r.get("measDateTime"),
            "variable": variable,
            "value": _clean_value(r.get("value"), variable),
            "unit": unit,
            "qa_flag": flag or pd.NA,
            "concept": concept,
        })
    df = pd.DataFrame.from_records(records, columns=schema.LONG_COLUMNS)
    return schema.normalize_long(df)
