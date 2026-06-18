"""Parser test for Northern Water (ArcGIS FeatureServer).

Exercises the epoch-millis date handling and the multi-variable fan-out
(one feature → one row per variable in the sources.yaml field_map).
"""
from pathlib import Path

import pandas as pd

from reservoir.parsers import northern_water
from reservoir.sources import Artifact


def _artifact(path: Path) -> Artifact:
    return Artifact(source="northern_water", vintage="current",
                    url="https://example/arcgis", local_path=path, metadata={})


def test_parses_canonical_schema(fixtures_dir):
    fx = fixtures_dir / "northern_water_sample.json"
    df = northern_water.parse(fx, _artifact(fx))
    # 2 reservoirs × 2 variables (STORAGE_AF, ELEV_FT) = 4 rows
    assert len(df) == 4
    assert df["source"].unique().tolist() == ["northern_water"]
    assert set(df["variable"]) == {"storage_af", "elevation_ft"}
    assert set(df["reservoir_id"]) == {"CARTER", "HORSETOOTH"}


def test_epoch_dates_parsed(fixtures_dir):
    fx = fixtures_dir / "northern_water_sample.json"
    df = northern_water.parse(fx, _artifact(fx))
    assert pd.api.types.is_datetime64_any_dtype(df["datetime"])
    assert df["datetime"].notna().all()


def test_known_value(fixtures_dir):
    fx = fixtures_dir / "northern_water_sample.json"
    df = northern_water.parse(fx, _artifact(fx))
    carter_storage = df.query("reservoir_id == 'CARTER' and variable == 'storage_af'")["value"]
    assert carter_storage.iloc[0] == 108900.0
