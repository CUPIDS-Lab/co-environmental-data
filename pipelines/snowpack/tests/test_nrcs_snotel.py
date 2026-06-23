"""SNOTEL parser — known-value assertions against a trimmed real AWDB response
(Park Cone, 680:CO:SNTL, 2020-02-01..04, elements WTEQ/SNWD/PREC) plus the
impossible-negative → NA regression on a constructed payload.
"""
import json

import pandas as pd

from snowpack.parsers import nrcs_snotel
from snowpack.schema import LONG_COLUMNS
from snowpack.sources import Artifact


def _art(path):
    return Artifact("nrcs_snotel", "current", "u", path,
                    {"site_id": "680:CO:SNTL", "site_name": "Park Cone", "date_field": "date"})


def test_parses_all_three_elements(fixtures_dir):
    fx = fixtures_dir / "nrcs_snotel_sample.json"
    df = nrcs_snotel.parse(fx, _art(fx))
    assert list(df.columns) == LONG_COLUMNS
    # 3 elements × 4 daily values
    assert len(df) == 12
    assert set(df["variable"]) == {"swe_in", "snow_depth_in", "precip_accum_in"}
    assert set(df["source"]) == {"nrcs_snotel"}
    assert (df["unit"] == "in").all()


def test_known_swe_value(fixtures_dir):
    fx = fixtures_dir / "nrcs_snotel_sample.json"
    df = nrcs_snotel.parse(fx, _art(fx))
    swe = df[df["variable"] == "swe_in"].set_index("datetime")["value"]
    assert swe[pd.Timestamp("2020-02-01")] == 6.7
    assert swe[pd.Timestamp("2020-02-03")] == 6.9


def test_flags_preserved(fixtures_dir):
    fx = fixtures_dir / "nrcs_snotel_sample.json"
    df = nrcs_snotel.parse(fx, _art(fx))
    # SNWD on 2020-02-01 carries qcFlag 'E' (edited), on 2020-02-03 'V' (valid)
    snwd = df[df["variable"] == "snow_depth_in"].set_index("datetime")["qa_flag"]
    assert snwd[pd.Timestamp("2020-02-01")] == "E"
    assert snwd[pd.Timestamp("2020-02-03")] == "V"


def test_negative_sentinel_becomes_na(tmp_path):
    """SWE/depth/precip cannot be negative; AWDB missing sentinels map to NA."""
    payload = [{"stationTriplet": "680:CO:SNTL", "data": [
        {"stationElement": {"elementCode": "WTEQ", "storedUnitCode": "in"},
         "values": [{"date": "2020-03-01", "value": -99.9, "qcFlag": "E"},
                    {"date": "2020-03-02", "value": 7.1, "qcFlag": "V"}]}]}]
    p = tmp_path / "neg.json"
    p.write_text(json.dumps(payload))
    df = nrcs_snotel.parse(p, _art(p))
    vals = df.set_index("datetime")["value"]
    assert pd.isna(vals[pd.Timestamp("2020-03-01")])     # -99.9 → NA
    assert vals[pd.Timestamp("2020-03-02")] == 7.1


def test_unknown_element_skipped(tmp_path):
    """An element we don't model must be skipped, not crash the parse."""
    payload = [{"stationTriplet": "680:CO:SNTL", "data": [
        {"stationElement": {"elementCode": "SMS", "storedUnitCode": "pct"},  # soil moisture — not modeled
         "values": [{"date": "2020-03-01", "value": 12.0}]},
        {"stationElement": {"elementCode": "WTEQ", "storedUnitCode": "in"},
         "values": [{"date": "2020-03-01", "value": 7.0, "qcFlag": "V"}]}]}]
    p = tmp_path / "mixed.json"
    p.write_text(json.dumps(payload))
    df = nrcs_snotel.parse(p, _art(p))
    assert len(df) == 1 and df.iloc[0]["variable"] == "swe_in"
