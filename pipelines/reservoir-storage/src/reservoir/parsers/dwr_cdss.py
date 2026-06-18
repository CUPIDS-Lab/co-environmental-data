"""Parser for CO DWR / CDSS telemetry daily time series.

The CDSS REST API v2 ``telemetrytimeseriesday`` returns (confirmed against the
live API)::

    {"ResultList": [
        {"abbrev": "GRERESCO", "parameter": "STORAGE",
         "measDate": "2025-06-18T00:00:00", "measValue": 138214.0,
         "measUnit": "acft", "flagA": "", "flagB": "", "measCount": 1,
         "modified": "..."},
        ...],
     "ResultCount": 1234, "PageCount": 1}

The measurement is ``measValue`` (not ``value``); the date is ``measDate``. We
map the CDSS ``parameter`` code to a canonical ``variable`` and reshape to tidy
long. ``flagA``/``flagB`` carry CDSS quality flags → ``qa_flag``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from reservoir import schema
from reservoir.sources import Artifact

# CDSS parameter code → (canonical variable, concept). ⚠️ confirm codes live.
PARAM_MAP = {
    "STORAGE": ("storage_af", "reservoir.storage_af"),
    "ELEV": ("elevation_ft", "reservoir.elevation_ft"),
}


def parse(path: Path, artifact: Artifact) -> pd.DataFrame:
    payload = json.loads(Path(path).read_text())
    rows = payload.get("ResultList", []) or []
    records = []
    for r in rows:
        param = r.get("parameter") or artifact.metadata.get("param")
        if param not in PARAM_MAP:
            continue
        variable, concept = PARAM_MAP[param]
        flag = " ".join(str(r.get(k, "")).strip() for k in ("flagA", "flagB")).strip()
        records.append({
            "source": "dwr_cdss",
            "vintage": artifact.vintage,
            "reservoir_id": r.get("abbrev") or artifact.metadata.get("reservoir_id"),
            "reservoir_name": artifact.metadata.get("reservoir_name"),
            "datetime": r.get("measDate") or r.get("measDateTime"),
            "variable": variable,
            "value": r.get("measValue"),  # CDSS field is measValue, not value
            "unit": schema.VARIABLES[variable],
            "qa_flag": flag or pd.NA,
            "concept": concept,
        })
    df = pd.DataFrame.from_records(records, columns=schema.LONG_COLUMNS)
    return schema.normalize_long(df)
