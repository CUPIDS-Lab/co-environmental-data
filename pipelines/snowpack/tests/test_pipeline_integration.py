"""Multi-source integration: the two parsers' outputs are mutually compatible.

Parses one fixture per source (Park Cone SNOTEL + Park Cone snow course — a
co-located pair), concatenates, and asserts the combined frame satisfies the
canonical contract (schema, composite-key uniqueness, vocabulary) and that both
sources coexist as distinct rows.

Unlike streamflow's USGS↔DWR test (same gage, identical values), SNOTEL and snow
course are NEARBY-not-identical sites, so we assert coexistence — NOT value
equality.
"""
import pandas as pd

from snowpack import schema
from snowpack.parsers import nrcs_snotel, nrcs_snowcourse
from snowpack.sources import Artifact


def _build(fixtures_dir):
    a_sntl = Artifact("nrcs_snotel", "current", "u", fixtures_dir / "nrcs_snotel_sample.json",
                      {"site_id": "680:CO:SNTL", "site_name": "Park Cone", "date_field": "date"})
    a_snow = Artifact("nrcs_snowcourse", "current", "u",
                      fixtures_dir / "nrcs_snowcourse_sample.json",
                      {"site_id": "06L02:CO:SNOW", "site_name": "Park Cone",
                       "date_field": "collectionDate"})
    return pd.concat([nrcs_snotel.parse(a_sntl.local_path, a_sntl),
                      nrcs_snowcourse.parse(a_snow.local_path, a_snow)], ignore_index=True)


def test_combined_frame_validates(fixtures_dir):
    combined = _build(fixtures_dir)
    validated = schema.validate(combined)
    assert set(validated["source"]) == {"nrcs_snotel", "nrcs_snowcourse"}


def test_composite_key_unique(fixtures_dir):
    combined = _build(fixtures_dir)
    key = ["source", "site_id", "datetime", "variable"]
    assert not combined.duplicated(key).any()


def test_vocabulary(fixtures_dir):
    combined = _build(fixtures_dir)
    assert set(combined["variable"]) <= set(schema.VARIABLES)
    assert set(combined["unit"]) <= set(schema.VARIABLES.values())


def test_snowcourse_extends_history_before_snotel(fixtures_dir):
    """The deep-history rationale: the snow course carries 2019 readings; the SNOTEL
    fixture is 2020 — together they span more than either alone."""
    combined = _build(fixtures_dir)
    snow = combined[combined["source"] == "nrcs_snowcourse"]
    assert snow["datetime"].min() == pd.Timestamp("2019-01-29")
