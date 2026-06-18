"""Parser for Northern Water ArcGIS FeatureServer query responses.

ArcGIS returns::

    {"features": [{"attributes": {"<date_field>": 1718582400000,
                                  "<storage_field>": 539122.0,
                                  "<name_field>": "Carter Lake"}}, ...]}

ArcGIS date fields are epoch milliseconds. The field names differ per service,
so the mapping lives in ``data/lookups/sources.yaml`` under
``northern_water.field_map`` (⚠️ confirm against the live service).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from reservoir import config, schema
from reservoir.sources import Artifact

CONCEPT = {
    "storage_af": "reservoir.storage_af",
    "pct_capacity": "reservoir.pct_capacity",
    "elevation_ft": "reservoir.elevation_ft",
    "release_cfs": "reservoir.release_cfs",
    "inflow_cfs": "reservoir.inflow_cfs",
}


def parse(path: Path, artifact: Artifact) -> pd.DataFrame:
    payload = json.loads(Path(path).read_text())
    fmap = config.load_sources_config()["northern_water"].get("field_map", {})
    date_f = fmap.get("datetime", "datetime")
    name_f = fmap.get("reservoir_name", "name")
    id_f = fmap.get("reservoir_id", "id")
    var_fields = fmap.get("variables", {"storage_af": "storage"})  # canonical → arcgis field

    records = []
    for feat in payload.get("features", []) or []:
        a = feat.get("attributes", {})
        raw_dt = a.get(date_f)
        # ArcGIS epoch-millis → timestamp; pass strings through.
        dt = pd.to_datetime(raw_dt, unit="ms") if isinstance(raw_dt, (int, float)) else raw_dt
        for variable, src_field in var_fields.items():
            if src_field not in a:
                continue
            records.append({
                "source": "northern_water",
                "vintage": artifact.vintage,
                "reservoir_id": str(a.get(id_f, artifact.metadata.get("reservoir_id", ""))),
                "reservoir_name": a.get(name_f),
                "datetime": dt,
                "variable": variable,
                "value": a.get(src_field),
                "unit": schema.VARIABLES.get(variable),
                "qa_flag": pd.NA,
                "concept": CONCEPT.get(variable),
            })
    df = pd.DataFrame.from_records(records, columns=schema.LONG_COLUMNS)
    return schema.normalize_long(df)
