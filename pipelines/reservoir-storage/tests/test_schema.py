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


def test_bad_source_rejected():
    df = _good_frame()
    df["source"] = "made_up_source"
    with pytest.raises(Exception):
        schema.normalize_long(df)
