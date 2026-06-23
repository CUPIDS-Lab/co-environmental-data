"""Shared parser for NRCS AWDB ``data`` responses (SNOTEL + snow course).

The AWDB REST ``data`` endpoint returns (confirmed against the live API)::

    [{"stationTriplet": "713:CO:SNTL",
      "data": [
        {"stationElement": {"elementCode": "WTEQ", "storedUnitCode": "in",
                            "beginDate": "1979-10-01 00:00", ...},
         "values": [{"date": "2024-03-01", "value": 16.0,
                     "qcFlag": "V", "qaFlag": "P"}, ...]},
        {"stationElement": {"elementCode": "SNWD", ...}, "values": [...]},
        ...]}]

Snow courses use the SAME shape but each value is
``{"month", "monthPart", "year", "collectionDate", "value", ...}`` — the real
measurement date is ``collectionDate``, not ``date`` (the ``date_field`` argument
selects it). One response carries a station's FULL period of record across all
requested elements.

Cleaning at parse time:

- **Element → canonical variable** via :data:`ELEMENT_MAP`; unknown elements are
  skipped (never crash on an unexpected code).
- **Impossible negatives → NA.** SWE, snow depth, and precipitation accumulation
  cannot be negative; AWDB's missing sentinels (e.g. ``-99.9``) and any stray
  negative are mapped to NA, never silently kept or zero-filled.
- **Flags preserved.** ``qcFlag`` (quality control) and ``qaFlag`` (approval) are
  space-joined into ``qa_flag`` so the *reason* a value is what it is survives.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from snowpack import schema
from snowpack.sources import Artifact

# AWDB element code → (canonical variable, concept key).
ELEMENT_MAP = {
    "WTEQ": ("swe_in", "snowpack.swe_in"),
    "SNWD": ("snow_depth_in", "snowpack.snow_depth_in"),
    "PREC": ("precip_accum_in", "snowpack.precip_accum_in"),
    # Declared for extensibility — not requested in this build, mapped defensively.
    "SNDN": ("snow_density_pct", "snowpack.snow_density_pct"),
    "TOBS": ("air_temp_obs_f", "snowpack.air_temp_obs_f"),
}


def _flag(v: dict) -> str:
    return " ".join(
        str(v.get(k)).strip() for k in ("qcFlag", "qaFlag")
        if v.get(k) not in (None, "", "None")
    ).strip()


def parse_awdb(path: Path, artifact: Artifact, *, source: str, date_field: str) -> pd.DataFrame:
    """Parse one saved AWDB ``data`` response into the canonical tidy-long frame.

    ``source`` pins the registry slug (``nrcs_snotel`` / ``nrcs_snowcourse``);
    ``date_field`` is ``"date"`` for SNOTEL daily values, ``"collectionDate"`` for
    snow-course semimonthly values.
    """
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, list):  # defensive: an error body or sentinel
        return schema.normalize_long(pd.DataFrame(columns=schema.LONG_COLUMNS))

    records = []
    for station in payload:
        if not isinstance(station, dict):
            continue
        site_id = station.get("stationTriplet") or artifact.metadata.get("site_id")
        site_name = artifact.metadata.get("site_name")
        for block in station.get("data", []) or []:
            se = block.get("stationElement", {}) or {}
            code = se.get("elementCode")
            mapped = ELEMENT_MAP.get(code)
            if not mapped:
                continue  # element we didn't ask for / don't model — skip, don't crash
            variable, concept = mapped
            for v in block.get("values", []) or []:
                when = v.get(date_field) or v.get("date") or v.get("collectionDate")
                if not when:
                    continue
                raw = v.get("value")
                try:
                    val = float(raw)
                except (TypeError, ValueError):
                    val = None
                # Impossible negatives (missing sentinels) → NA. SWE / depth /
                # precip-accumulation are non-negative physical quantities.
                if val is not None and val < 0:
                    val = None
                flag = _flag(v)
                records.append({
                    "source": source,
                    "vintage": artifact.vintage,
                    "site_id": site_id,
                    "site_name": site_name,
                    "datetime": when,
                    "variable": variable,
                    "value": val,
                    "unit": schema.VARIABLES.get(variable),
                    "qa_flag": flag or pd.NA,
                    "concept": concept,
                })
    df = pd.DataFrame.from_records(records, columns=schema.LONG_COLUMNS)
    return schema.normalize_long(df)
