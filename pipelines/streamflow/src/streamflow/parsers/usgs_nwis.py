"""Parser for USGS NWIS daily-values (``dv``) responses (WaterML-as-JSON).

The dv service returns (confirmed against the live API)::

    {"value": {"timeSeries": [
        {"sourceInfo": {"siteName": "COLORADO RIVER NEAR CAMEO, CO.",
                        "siteCode": [{"value": "09095500"}]},
         "variable": {"variableCode": [{"value": "00060"}],
                      "unit": {"unitCode": "ft3/s"}, "noDataValue": -999999.0},
         "values": [{"value": [
             {"value": "1310", "qualifiers": ["A", "e"],
              "dateTime": "2024-01-01T00:00:00.000"}, ...]}]},
        ...]}}

A site with no data in range returns an empty ``timeSeries`` list (HTTP 200) —
that yields an empty frame, not an error. ``qualifiers`` carry the approval state
(A=approved, P=provisional, e=estimated) → ``qa_flag``. Values equal to the
series' ``noDataValue`` sentinel are treated as missing.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from streamflow import schema
from streamflow.sources import Artifact

# USGS parameter code → (canonical variable, concept).
PARAM_MAP = {
    "00060": ("discharge_cfs", "streamflow.discharge_cfs"),
    "00065": ("gage_height_ft", "streamflow.gage_height_ft"),
}


def parse(path: Path, artifact: Artifact) -> pd.DataFrame:
    payload = json.loads(Path(path).read_text())
    series = (payload.get("value", {}) or {}).get("timeSeries", []) or []
    records = []
    for ts in series:
        info = ts.get("sourceInfo", {}) or {}
        codes = info.get("siteCode") or [{}]
        site_id = (codes[0].get("value") if codes else None) or artifact.metadata.get("site_id")
        site_name = info.get("siteName") or artifact.metadata.get("site_name")

        var = ts.get("variable", {}) or {}
        vcodes = var.get("variableCode") or [{}]
        param_cd = (vcodes[0].get("value") if vcodes else None) or artifact.metadata.get("param_cd")
        variable, concept = PARAM_MAP.get(
            param_cd, (artifact.metadata.get("variable", "discharge_cfs"),
                       "streamflow.discharge_cfs"))
        try:
            no_data = float(var.get("noDataValue"))
        except (TypeError, ValueError):
            no_data = None

        for block in ts.get("values", []) or []:
            for v in block.get("value", []) or []:
                raw = v.get("value")
                try:
                    val = float(raw)
                except (TypeError, ValueError):
                    val = None
                if val is not None and no_data is not None and val == no_data:
                    val = None  # USGS missing-data sentinel
                quals = v.get("qualifiers") or []
                flag = " ".join(str(q) for q in quals).strip()
                records.append({
                    "source": "usgs_nwis",
                    "vintage": artifact.vintage,
                    "site_id": site_id,
                    "site_name": site_name,
                    "datetime": v.get("dateTime"),
                    "variable": variable,
                    "value": val,
                    "unit": schema.VARIABLES.get(variable),
                    "qa_flag": flag or pd.NA,
                    "concept": concept,
                })
    df = pd.DataFrame.from_records(records, columns=schema.LONG_COLUMNS)
    return schema.normalize_long(df)
