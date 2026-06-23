"""Parser for CO DWR / CDSS surface-water daily time series.

The CDSS REST API v2 ``surfacewater/surfacewatertsday`` returns (confirmed
against the live API)::

    {"ResultList": [
        {"stationNum": 865, "abbrev": "CLAFORCO", "usgsSiteId": "06752260",
         "measType": "Streamflow", "measDate": "2024-06-01T00:00:00-06:00",
         "value": 160.0, "flagA": "A", "flagB": null, "flagC": null,
         "flagD": null, "dataSource": "USGS", "measUnit": "cfs"}, ...],
     "ResultCount": 5}

Two gotchas vs the reservoir telemetry parser: the value field is ``value`` (not
``measValue``), and ``measType`` is the spelled-out ``"Streamflow"``. ``flagA``..
``flagD`` carry CDSS quality flags → ``qa_flag``.

⚠️ ``dataSource`` is frequently ``"USGS"`` — DWR re-serves the federal gage. That
overlap is handled at the dataset level (the same gage also appears under
``usgs_nwis``, joinable via ``usgs_site_no`` in ``sites.csv``); see the concept
catalog caveats. We do NOT drop those rows here — ``source`` is in the key.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from streamflow import schema
from streamflow.sources import Artifact

# CDSS measType → (canonical variable, concept).
MEAS_MAP = {
    "Streamflow": ("discharge_cfs", "streamflow.discharge_cfs"),
    "DISCHRG": ("discharge_cfs", "streamflow.discharge_cfs"),  # legacy alias, defensive
}


def parse(path: Path, artifact: Artifact) -> pd.DataFrame:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):  # e.g. a stray "zero records" sentinel
        return schema.normalize_long(pd.DataFrame(columns=schema.LONG_COLUMNS))
    rows = payload.get("ResultList", []) or []
    records = []
    for r in rows:
        meas = r.get("measType")
        variable, concept = MEAS_MAP.get(
            meas, (artifact.metadata.get("variable", "discharge_cfs"),
                   "streamflow.discharge_cfs"))
        flag = " ".join(
            str(r.get(k)).strip() for k in ("flagA", "flagB", "flagC", "flagD")
            if r.get(k) not in (None, "", "None")
        ).strip()
        # Sentinel cleaning: CDSS encodes ice-affected / missing daily values as the
        # impossible discharge -999 (carrying a "U"/"Ice" flag). Discharge cannot be
        # negative, so map it to NA — harmonizing with USGS, which returns NA for the
        # same condition. The flag is preserved so the *reason* stays in qa_flag.
        value = r.get("value")
        if isinstance(value, (int, float)) and value < 0:
            value = None
        records.append({
            "source": "dwr_cdss",
            "vintage": artifact.vintage,
            "site_id": r.get("abbrev") or artifact.metadata.get("site_id"),
            "site_name": artifact.metadata.get("site_name"),
            "datetime": r.get("measDate") or r.get("measDateTime"),
            "variable": variable,
            "value": value,  # CDSS surface-water field is `value`, not measValue
            "unit": schema.VARIABLES.get(variable),
            "qa_flag": flag or pd.NA,
            "concept": concept,
        })
    df = pd.DataFrame.from_records(records, columns=schema.LONG_COLUMNS)
    return schema.normalize_long(df)
