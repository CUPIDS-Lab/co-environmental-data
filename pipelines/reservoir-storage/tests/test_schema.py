"""Schema-contract tests — catch drift before it reaches consumers."""
import pandas as pd
import pytest

from reservoir import schema


def _good_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "source": ["dwr_cdss"],
        "vintage": ["current"],
        "reservoir_id": ["GREEN MOUNTAIN"],
        "reservoir_name": ["Green Mountain Reservoir"],
        "datetime": ["2026-06-17T00:00:00"],
        "variable": ["storage_af"],
        "value": [138214.0],
        "unit": ["acre-ft"],
        "qa_flag": ["A"],
        "concept": ["reservoir.storage_af"],
    })


def test_good_frame_validates():
    out = schema.normalize_long(_good_frame())
    assert len(out) == 1
    assert out["source"].iloc[0] == "dwr_cdss"
    assert str(out["datetime"].dtype).startswith("datetime64")


def test_missing_required_column_raises():
    df = _good_frame().drop(columns=["variable"])
    with pytest.raises(Exception):
        schema.normalize_long(df)


def test_bad_variable_rejected():
    df = _good_frame()
    df["variable"] = "not_a_variable"
    with pytest.raises(Exception):
        schema.normalize_long(df)


def test_normalize_long_collapses_multiple_readings_per_day():
    # a day with two readings (sub-daily times / same-day revision) must not fail
    # the composite-key uniqueness check — keep the latest reading.
    early = _good_frame(); early["datetime"] = ["2026-06-17T00:00:00"]; early["value"] = [100.0]
    late = _good_frame(); late["datetime"] = ["2026-06-17T18:00:00"]; late["value"] = [200.0]
    out = schema.normalize_long(pd.concat([early, late], ignore_index=True))
    assert len(out) == 1                      # collapsed to one day
    assert out["value"].iloc[0] == 200.0      # kept the latest reading


def test_bad_source_rejected():
    df = _good_frame()
    df["source"] = "made_up_source"
    with pytest.raises(Exception):
        schema.normalize_long(df)
