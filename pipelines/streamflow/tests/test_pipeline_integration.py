"""Multi-source integration: both parsers' outputs are mutually compatible.

Parses one fixture per source, concatenates, and asserts the combined frame
satisfies the canonical contract (schema, composite-key uniqueness, vocab). Both
fixtures are the SAME physical gage (Colorado R near Cameo) seen through each
source — so this also exercises the headline property: the two co-exist as
distinct rows (``source`` is in the key) with identical values.
"""
from pathlib import Path

import pandas as pd

from streamflow import schema
from streamflow.parsers import dwr_cdss, usgs_nwis
from streamflow.sources import Artifact


def _build(fixtures_dir: Path) -> pd.DataFrame:
    a_usgs = Artifact("usgs_nwis", "current", "u", fixtures_dir / "usgs_nwis_sample.json",
                      {"site_id": "09095500", "site_name": "COLORADO RIVER NEAR CAMEO, CO.",
                       "variable": "discharge_cfs", "param_cd": "00060"})
    a_dwr = Artifact("dwr_cdss", "current", "u", fixtures_dir / "dwr_cdss_sample.json",
                     {"site_id": "COLCAMCO", "site_name": "COLORADO RIVER NEAR CAMEO, CO.",
                      "variable": "discharge_cfs", "meas_type": "Streamflow"})
    frames = [usgs_nwis.parse(a_usgs.local_path, a_usgs),
              dwr_cdss.parse(a_dwr.local_path, a_dwr)]
    return pd.concat(frames, ignore_index=True)


def test_combined_frame_validates(fixtures_dir):
    combined = _build(fixtures_dir)
    validated = schema.validate(combined)               # raises on any contract violation
    assert len(validated) == 3 + 3                       # usgs + dwr
    assert set(validated["source"]) == {"usgs_nwis", "dwr_cdss"}


def test_composite_key_unique(fixtures_dir):
    combined = _build(fixtures_dir)
    key = ["source", "site_id", "datetime", "variable"]
    assert not combined.duplicated(key).any()


def test_units_and_variables_in_vocabulary(fixtures_dir):
    combined = _build(fixtures_dir)
    assert set(combined["variable"]) <= set(schema.VARIABLES)
    assert set(combined["unit"]) <= set(schema.VARIABLES.values())


def test_overlap_values_agree(fixtures_dir):
    """DWR re-serves USGS: the same gage/date should carry the same value across
    sources. This is the per-row form of audit.reconcile_cross_source."""
    combined = _build(fixtures_dir)
    by_date = combined.pivot_table(index="datetime", columns="source", values="value")
    assert (by_date["usgs_nwis"] == by_date["dwr_cdss"]).all()
