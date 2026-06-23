"""Parser test for CO DWR/CDSS climate daily — known-fixture-in, expected-frame-out.

Fixtures are real (trimmed) climatestationtsday responses: a Precip series (station
3, NOAA) and a Solar series (station 1886, CoAgMet — exercises the non-degF
``mJ/m^2`` unit). Sentinel / sub-zero behavior is tested inline so the intent is
explicit.
"""
import json
from pathlib import Path

import pandas as pd

from climate_stations.parsers import cdss_climate
from climate_stations.sources import Artifact


def _artifact(path: Path, meas_type: str, site_id="0", site_name="TEST") -> Artifact:
    variable = {"Precip": "precip_in", "Solar": "solar_rad_mj_m2",
                "MinTemp": "temp_min_f"}.get(meas_type, "precip_in")
    return Artifact("cdss_climate", "current", "https://example/test", path,
                    {"site_id": site_id, "site_name": site_name,
                     "variable": variable, "meas_type": meas_type})


def test_precip_parses_canonical_schema(fixtures_dir):
    fx = fixtures_dir / "cdss_climate_precip_sample.json"
    df = cdss_climate.parse(fx, _artifact(fx, "Precip"))
    assert len(df) == 3
    assert df["source"].unique().tolist() == ["cdss_climate"]
    assert set(df["variable"]) == {"precip_in"}
    assert df["unit"].unique().tolist() == ["in"]
    # site_id comes from the response stationNum, not the artifact metadata.
    assert df["site_id"].unique().tolist() == ["3"]


def test_precip_zero_is_preserved_not_nulled(fixtures_dir):
    """0.0 inches of precip is a real observation (dry day), NOT missing — it must
    survive as 0.0, never collapse to NA."""
    fx = fixtures_dir / "cdss_climate_precip_sample.json"
    df = cdss_climate.parse(fx, _artifact(fx, "Precip"))
    assert df["value"].notna().all()
    assert (df["value"] == 0.0).all()


def test_solar_known_value_and_nondegf_unit(fixtures_dir):
    """Solar exercises a per-measType unit that is NOT degF — the parser must carry
    the source-reported ``mJ/m^2``, mapping measType→variable correctly."""
    fx = fixtures_dir / "cdss_climate_solar_sample.json"
    df = cdss_climate.parse(fx, _artifact(fx, "Solar", site_id="1886"))
    assert set(df["variable"]) == {"solar_rad_mj_m2"}
    assert df["unit"].unique().tolist() == ["mJ/m^2"]
    first = df.sort_values("datetime").iloc[0]
    assert first["value"] == 27.45
    assert str(first["datetime"].date()) == "2024-06-01"


def test_subzero_temperature_is_preserved(tmp_path):
    """Sub-zero degF is real Colorado winter data — the parser must NOT null it
    (unlike the non-negative-domain measures). Only the -999 sentinel becomes NA."""
    fx = tmp_path / "mintemp.json"
    fx.write_text(json.dumps({"ResultList": [
        {"stationNum": 1886, "measType": "MinTemp", "measDate": "2024-01-09T00:00:00-07:00",
         "value": -6.736, "flagA": None, "dataSource": "CoAgMet", "measUnit": "degF"},
        {"stationNum": 1886, "measType": "MinTemp", "measDate": "2024-01-10T00:00:00-07:00",
         "value": -999.0, "flagA": "M", "dataSource": "CoAgMet", "measUnit": "degF"},
    ]}))
    df = cdss_climate.parse(fx, _artifact(fx, "MinTemp", site_id="1886"))
    jan9 = df[df["datetime"] == "2024-01-09"].iloc[0]
    assert jan9["value"] == -6.736                          # negative temp preserved
    jan10 = df[df["datetime"] == "2024-01-10"].iloc[0]
    assert pd.isna(jan10["value"])                          # -999 sentinel → NA
    assert "M" in str(jan10["qa_flag"])                     # reason preserved


def test_impossible_negative_for_nonnegative_measure_becomes_na(tmp_path):
    """A negative precip is physically impossible → NA. (Contrast with temperatures,
    which keep negatives.)"""
    fx = tmp_path / "precip.json"
    fx.write_text(json.dumps({"ResultList": [
        {"stationNum": 3, "measType": "Precip", "measDate": "2024-06-01T00:00:00-06:00",
         "value": -1.0, "flagA": "B", "dataSource": "NOAA", "measUnit": "in"},
    ]}))
    df = cdss_climate.parse(fx, _artifact(fx, "Precip", site_id="3"))
    assert pd.isna(df.iloc[0]["value"])
    assert "B" in str(df.iloc[0]["qa_flag"])                # flag still preserved


def test_qa_flags_joined(tmp_path):
    """flagA..flagD collapse into a single space-joined qa_flag; empty/None dropped."""
    fx = tmp_path / "flags.json"
    fx.write_text(json.dumps({"ResultList": [
        {"stationNum": 3, "measType": "Precip", "measDate": "2024-06-01T00:00:00-06:00",
         "value": 0.25, "flagA": "A", "flagB": None, "flagC": "0", "flagD": "1700",
         "dataSource": "NOAA", "measUnit": "in"},
    ]}))
    df = cdss_climate.parse(fx, _artifact(fx, "Precip", site_id="3"))
    assert df.iloc[0]["qa_flag"] == "A 0 1700"
