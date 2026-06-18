"""Parser for USBR Reclamation RISE ``/result`` time series (JSON:API).

RISE returns JSON:API::

    {"data": [
        {"type": "Result",
         "attributes": {"dateTime": "2026-06-17T00:00:00", "result": 539122.0}},
        ...]}

The canonical ``variable`` for the pull is carried on the artifact metadata
(set in ``ReclamationRise.discover`` from the ``rise_item_ids`` map).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from reservoir import schema
from reservoir.sources import Artifact

CONCEPT = {
    "storage_af": "reservoir.storage_af",
    "elevation_ft": "reservoir.elevation_ft",
    "release_cfs": "reservoir.release_cfs",
}


def parse(path: Path, artifact: Artifact) -> pd.DataFrame:
    payload = json.loads(Path(path).read_text())
    variable = artifact.metadata.get("variable", "storage_af")
    records = []
    for item in payload.get("data", []) or []:
        attrs = item.get("attributes", item)
        records.append({
            "source": "reclamation_rise",
            "vintage": artifact.vintage,
            "reservoir_id": artifact.metadata.get("reservoir_id"),
            "reservoir_name": artifact.metadata.get("reservoir_name"),
            "datetime": attrs.get("dateTime") or attrs.get("datetime"),
            "variable": variable,
            "value": attrs.get("result") or attrs.get("value"),
            "unit": schema.VARIABLES.get(variable),
            "qa_flag": attrs.get("flag") or pd.NA,
            "concept": CONCEPT.get(variable),
        })
    df = pd.DataFrame.from_records(records, columns=schema.LONG_COLUMNS)
    return schema.normalize_long(df)
