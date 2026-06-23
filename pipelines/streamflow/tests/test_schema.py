"""Schema contract + drift guards.

``LONG_COLUMNS`` / ``VARIABLES`` / ``SOURCE_SLUGS`` are the contract; changing
them is a migration (record it in the changelog). These tests fail loudly if the
contract drifts unintentionally, and exercise ``normalize_long``'s day-flooring +
same-key de-duplication.
"""
import pandas as pd
import pytest

from streamflow import schema


def test_contract_columns_stable():
    assert schema.LONG_COLUMNS == [
        "source", "vintage", "site_id", "site_name", "datetime",
        "variable", "value", "unit", "qa_flag", "concept",
    ]
    assert schema.SOURCE_SLUGS == ("usgs_nwis", "dwr_cdss")
    assert schema.VARIABLES["discharge_cfs"] == "cfs"


def test_normalize_floors_to_day_and_keeps_latest():
    """Two sub-daily readings on one (source, site, day, variable) collapse to the
    latest; the day key is then unique."""
    df = pd.DataFrame({
        "source": ["usgs_nwis", "usgs_nwis"],
        "vintage": ["current", "current"],
        "site_id": ["09095500", "09095500"],
        "site_name": ["Cameo", "Cameo"],
        "datetime": ["2024-06-01T06:00:00", "2024-06-01T18:00:00"],
        "variable": ["discharge_cfs", "discharge_cfs"],
        "value": [100.0, 110.0],
        "unit": ["cfs", "cfs"],
        "qa_flag": ["A", "A"],
        "concept": ["streamflow.discharge_cfs", "streamflow.discharge_cfs"],
    })
    out = schema.normalize_long(df)
    assert len(out) == 1
    assert out.iloc[0]["value"] == 110.0                       # latest reading kept
    assert str(out.iloc[0]["datetime"]) == "2024-06-01 00:00:00"  # floored to the day


def test_validate_rejects_unknown_variable():
    df = pd.DataFrame({
        "source": ["usgs_nwis"], "vintage": ["current"], "site_id": ["X"],
        "site_name": ["X"], "datetime": [pd.Timestamp("2024-01-01")],
        "variable": ["not_a_variable"], "value": [1.0], "unit": ["cfs"],
        "qa_flag": [pd.NA], "concept": [pd.NA],
    })
    with pytest.raises(Exception):
        schema.validate(df)
