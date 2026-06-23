"""Schema contract — the pandera model is the machine-enforced data dictionary."""
import pandas as pd
import pytest

from snowpack import schema


def _row(**kw):
    base = dict(source="nrcs_snotel", vintage="current", site_id="680:CO:SNTL",
                site_name="Park Cone", datetime="2020-02-01", variable="swe_in",
                value=6.7, unit="in", qa_flag="V", concept="snowpack.swe_in")
    base.update(kw)
    return base


def test_valid_frame_validates():
    df = pd.DataFrame([_row(), _row(variable="snow_depth_in", value=28.0,
                                    concept="snowpack.snow_depth_in")])
    out = schema.normalize_long(df)
    assert len(out) == 2
    assert list(out.columns) == schema.LONG_COLUMNS


def test_bad_variable_rejected():
    df = pd.DataFrame([_row(variable="not_a_variable")])
    with pytest.raises(Exception):
        schema.normalize_long(df)


def test_bad_unit_rejected():
    df = pd.DataFrame([_row(unit="furlongs")])
    with pytest.raises(Exception):
        schema.validate(df)


def test_composite_key_unique_enforced():
    # same (source, site_id, datetime, variable) twice with different values —
    # normalize_long keeps the latest; validate must then see a unique key.
    df = pd.DataFrame([_row(value=6.7), _row(value=6.9)])
    out = schema.normalize_long(df)
    assert len(out) == 1
    assert out.iloc[0]["value"] == 6.9  # keep="last"


def test_negative_allowed_only_after_parser_maps_it():
    # the schema itself does not forbid negatives (the parser maps them to NA);
    # a NA value is valid.
    df = pd.DataFrame([_row(value=None)])
    out = schema.normalize_long(df)
    assert pd.isna(out.iloc[0]["value"])
