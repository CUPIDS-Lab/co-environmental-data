"""Parser test for CO DWR/CDSS surface water — known-fixture-in, expected-frame-out.

The fixture is a real (trimmed) surfacewatertsday response for COLCAMCO — the DWR
station that re-serves USGS 09095500 (Colorado River near Cameo). Its values are
byte-identical to the USGS fixture, which is the point: DWR re-serves USGS.
"""
import json
from pathlib import Path

import pandas as pd

from streamflow.parsers import dwr_cdss
from streamflow.sources import Artifact


def _artifact(path: Path) -> Artifact:
    return Artifact(
        source="dwr_cdss", vintage="current", url="https://example/test",
        local_path=path,
        metadata={"site_id": "COLCAMCO", "site_name": "COLORADO RIVER NEAR CAMEO, CO.",
                  "variable": "discharge_cfs", "meas_type": "Streamflow"},
    )


def test_parses_canonical_schema(fixtures_dir):
    fx = fixtures_dir / "dwr_cdss_sample.json"
    df = dwr_cdss.parse(fx, _artifact(fx))
    assert len(df) == 3
    assert df["source"].unique().tolist() == ["dwr_cdss"]
    assert set(df["variable"]) == {"discharge_cfs"}
    assert df["unit"].unique().tolist() == ["cfs"]


def test_known_value(fixtures_dir):
    fx = fixtures_dir / "dwr_cdss_sample.json"
    df = dwr_cdss.parse(fx, _artifact(fx))
    latest = df.sort_values("datetime").iloc[-1]
    assert latest["value"] == 12400.0                 # value field (NOT measValue)
    assert latest["site_id"] == "COLCAMCO"            # parser reads abbrev from the response
    assert str(latest["datetime"].date()) == "2024-06-03"


def test_value_field_not_measvalue(fixtures_dir):
    """Regression guard: surface-water daily uses `value`, unlike the reservoir
    telemetry endpoint's `measValue`. A copy-paste of the reservoir parser would
    silently produce all-null values — assert they are populated."""
    fx = fixtures_dir / "dwr_cdss_sample.json"
    df = dwr_cdss.parse(fx, _artifact(fx))
    assert df["value"].notna().all()


def test_ice_sentinel_becomes_na(tmp_path):
    """CDSS encodes ice-affected days as the impossible discharge -999 (flag 'U Ice').
    The parser must map it to NA — not leave a negative discharge — while keeping the
    flag so the reason is still visible."""
    fx = tmp_path / "ice.json"
    fx.write_text(json.dumps({"ResultList": [
        {"abbrev": "YAMSTECO", "measType": "Streamflow", "measDate": "2026-02-04T00:00:00",
         "value": -999.0, "flagA": "U", "flagB": "Ice", "measUnit": "cfs"},
        {"abbrev": "YAMSTECO", "measType": "Streamflow", "measDate": "2026-02-05T00:00:00",
         "value": 120.0, "flagA": "A", "measUnit": "cfs"},
    ]}))
    df = dwr_cdss.parse(fx, _artifact(fx))
    assert (df["value"] < 0).sum() == 0                       # no impossible negatives
    ice = df[df["datetime"] == "2026-02-04"].iloc[0]
    assert pd.isna(ice["value"])                              # sentinel → NA
    assert "Ice" in str(ice["qa_flag"])                       # reason preserved
