"""Integration: heterogeneous-measType outputs are mutually schema-compatible.

Parses two real fixtures with different measTypes and units (Precip in inches,
Solar in mJ/m^2), concatenates, and asserts the combined frame satisfies the
canonical contract — schema, composite-key uniqueness, controlled vocab. The point:
twelve measures with five different units coexist in one tidy long frame.
"""
from pathlib import Path

import pandas as pd

from climate_stations import schema
from climate_stations.parsers import cdss_climate
from climate_stations.sources import Artifact


def _build(fixtures_dir: Path) -> pd.DataFrame:
    a_precip = Artifact("cdss_climate", "current", "u",
                        fixtures_dir / "cdss_climate_precip_sample.json",
                        {"site_id": "3", "site_name": "BUCKHORN MTN 1 E",
                         "variable": "precip_in", "meas_type": "Precip"})
    a_solar = Artifact("cdss_climate", "current", "u",
                       fixtures_dir / "cdss_climate_solar_sample.json",
                       {"site_id": "1886", "site_name": "CENTER",
                        "variable": "solar_rad_mj_m2", "meas_type": "Solar"})
    return pd.concat([cdss_climate.parse(a_precip.local_path, a_precip),
                      cdss_climate.parse(a_solar.local_path, a_solar)], ignore_index=True)


def test_combined_frame_validates(fixtures_dir):
    combined = _build(fixtures_dir)
    validated = schema.validate(combined)                   # raises on any contract violation
    assert len(validated) == 3 + 2                          # precip + solar
    assert set(validated["variable"]) == {"precip_in", "solar_rad_mj_m2"}


def test_composite_key_unique(fixtures_dir):
    combined = _build(fixtures_dir)
    key = ["source", "site_id", "datetime", "variable"]
    assert not combined.duplicated(key).any()


def test_units_and_variables_in_vocabulary(fixtures_dir):
    combined = _build(fixtures_dir)
    assert set(combined["variable"]) <= set(schema.VARIABLES)
    assert set(combined["unit"].dropna()) <= set(schema.UNITS)
    # two distinct units coexist (inches + mJ/m^2) — harmonization is per concept.
    assert {"in", "mJ/m^2"} <= set(combined["unit"].dropna())
