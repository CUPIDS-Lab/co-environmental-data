"""Schema contract + drift guards.

``LONG_COLUMNS`` / ``VARIABLES`` / ``MEAS_MAP`` / ``SOURCE_SLUGS`` are the contract;
changing them is a migration (record it in the changelog). These tests fail loudly
if the contract drifts unintentionally, and exercise ``normalize_long``'s
day-flooring + same-key de-duplication.
"""
import pandas as pd
import pytest

from climate_stations import schema


def test_contract_columns_stable():
    assert schema.LONG_COLUMNS == [
        "source", "vintage", "site_id", "site_name", "datetime",
        "variable", "value", "unit", "qa_flag", "concept",
    ]
    assert schema.SOURCE_SLUGS == ("cdss_climate",)


def test_twelve_meastypes_mapped_with_confirmed_units():
    # All 12 CDSS daily measTypes are mapped, and the live-confirmed units hold.
    assert len(schema.MEAS_MAP) == 12
    assert schema.VARIABLES["precip_in"] == "in"
    assert schema.VARIABLES["temp_min_f"] == "degF"
    assert schema.VARIABLES["solar_rad_mj_m2"] == "mJ/m^2"
    assert schema.VARIABLES["vapor_pressure_kpa"] == "kPa"
    assert schema.VARIABLES["wind_run_km"] == "KM"
    assert schema.VARIABLES["frost_date"] is None          # unconfirmed → no canonical unit
    assert schema.UNITS == ["KM", "degF", "in", "kPa", "mJ/m^2"]


def test_temps_excluded_from_nonnegative_cleaning():
    # Sub-zero degF is real — temps must NOT be in the non-negative-domain set.
    assert "temp_min_f" not in schema.NON_NEGATIVE_VARS
    assert "temp_max_f" not in schema.NON_NEGATIVE_VARS
    assert "precip_in" in schema.NON_NEGATIVE_VARS
    assert "swe_in" in schema.NON_NEGATIVE_VARS


def test_normalize_floors_to_day_and_keeps_latest():
    """Two sub-daily readings on one (source, site, day, variable) collapse to the
    latest; the day key is then unique."""
    df = pd.DataFrame({
        "source": ["cdss_climate", "cdss_climate"],
        "vintage": ["current", "current"],
        "site_id": ["3", "3"],
        "site_name": ["Buckhorn", "Buckhorn"],
        "datetime": ["2024-06-01T06:00:00-06:00", "2024-06-01T18:00:00-06:00"],
        "variable": ["precip_in", "precip_in"],
        "value": [0.1, 0.2],
        "unit": ["in", "in"],
        "qa_flag": ["A", "A"],
        "concept": ["climate.precip_in", "climate.precip_in"],
    })
    out = schema.normalize_long(df)
    assert len(out) == 1
    assert out.iloc[0]["value"] == 0.2                          # latest reading kept
    assert str(out.iloc[0]["datetime"]) == "2024-06-01 00:00:00"  # floored to the day


def test_subzero_temperature_passes_schema():
    """A negative degF must validate — the schema places no lower bound on value."""
    df = pd.DataFrame({
        "source": ["cdss_climate"], "vintage": ["current"], "site_id": ["1886"],
        "site_name": ["Center"], "datetime": [pd.Timestamp("2024-01-09")],
        "variable": ["temp_min_f"], "value": [-6.736], "unit": ["degF"],
        "qa_flag": [pd.NA], "concept": ["climate.temp_min_f"],
    })
    out = schema.validate(df)
    assert out.iloc[0]["value"] == -6.736


def test_validate_rejects_unknown_variable():
    df = pd.DataFrame({
        "source": ["cdss_climate"], "vintage": ["current"], "site_id": ["X"],
        "site_name": ["X"], "datetime": [pd.Timestamp("2024-01-01")],
        "variable": ["not_a_variable"], "value": [1.0], "unit": ["in"],
        "qa_flag": [pd.NA], "concept": [pd.NA],
    })
    with pytest.raises(Exception):
        schema.validate(df)
