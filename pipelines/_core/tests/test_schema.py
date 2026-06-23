"""Tests for the shared normalize_long machinery."""
import pandas as pd

from co_pipeline_core import schema as core

LONG = ["source", "vintage", "site_id", "site_name", "datetime", "variable",
        "value", "unit", "qa_flag", "concept"]
VARS = {"swe_in": "in"}


def _identity(df):  # stand-in validator
    return df


def _row(**kw):
    base = dict(source="s", vintage="current", site_id="A", site_name="A name",
                datetime="2024-01-01T00:00:00", variable="swe_in", value=1.0,
                unit="in", qa_flag="V", concept="c")
    base.update(kw)
    return base


def test_fills_unit_and_optional_columns():
    df = pd.DataFrame([{k: _row()[k] for k in ("source", "vintage", "site_id", "datetime", "variable", "value")}])
    out = core.normalize_long(df, long_columns=LONG, variables=VARS, validate=_identity)
    assert out["unit"].iloc[0] == "in"            # filled from VARS
    assert pd.isna(out["qa_flag"].iloc[0]) and pd.isna(out["concept"].iloc[0])


def test_missing_required_column_raises():
    df = pd.DataFrame([{"source": "s", "vintage": "c", "site_id": "A"}])  # no datetime/variable/value
    try:
        core.normalize_long(df, long_columns=LONG, variables=VARS, validate=_identity)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "missing required columns" in str(e)


def test_utc_floor_dedups_to_latest_per_day():
    df = pd.DataFrame([_row(datetime="2024-03-01T06:00:00Z", value=1.0),
                       _row(datetime="2024-03-01T07:00:00Z", value=2.0)])
    out = core.normalize_long(df, long_columns=LONG, variables=VARS, validate=_identity)
    assert len(out) == 1 and out["value"].iloc[0] == 2.0          # latest wins
    assert out["datetime"].iloc[0] == pd.Timestamp("2024-03-01")  # floored, tz-naive


def test_local_date_keeps_local_calendar_date():
    # 2024-03-01T23:00-07:00 is still local 2024-03-01 (UTC would be the 2nd)
    df = pd.DataFrame([_row(datetime="2024-03-01T23:00:00-07:00")])
    out = core.normalize_long(df, long_columns=LONG, variables=VARS, validate=_identity,
                              datetime_mode="local_date")
    assert out["datetime"].iloc[0] == pd.Timestamp("2024-03-01")


def test_id_col_parameter():
    cols = [c if c != "site_id" else "reservoir_id" for c in LONG]
    cols = [c if c != "site_name" else "reservoir_name" for c in cols]
    df = pd.DataFrame([{**_row(), "reservoir_id": "R", "reservoir_name": "Res"}])
    out = core.normalize_long(df.drop(columns=["site_id", "site_name"]),
                              long_columns=cols, variables=VARS, validate=_identity,
                              id_col="reservoir_id", name_col="reservoir_name")
    assert list(out.columns) == cols and out["reservoir_id"].iloc[0] == "R"
