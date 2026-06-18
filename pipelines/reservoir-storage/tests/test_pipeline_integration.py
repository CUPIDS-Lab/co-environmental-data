"""Multi-source integration: all three parsers' outputs are mutually compatible.

Parses one fixture per source, concatenates, and asserts the combined frame
satisfies the canonical contract (schema, composite-key uniqueness, vocab). This
is the cross-source check that single-parser tests can't give — it catches a
parser that validates alone but collides with another on the shared schema.
"""
from pathlib import Path

import pandas as pd

from reservoir import schema
from reservoir.parsers import dwr_cdss, northern_water, reclamation_rise
from reservoir.sources import Artifact


def _build(fixtures_dir: Path) -> pd.DataFrame:
    a_dwr = Artifact("dwr_cdss", "current", "u", fixtures_dir / "dwr_cdss_storage_sample.json",
                     {"reservoir_id": "GRERESCO", "reservoir_name": "Green Mountain Reservoir",
                      "param": "STORAGE"})
    a_rise = Artifact("reclamation_rise", "current", "u",
                      fixtures_dir / "reclamation_rise_storage_sample.json",
                      {"reservoir_id": "blue-mesa", "reservoir_name": "Blue Mesa Reservoir",
                       "variable": "storage_af"})
    a_nw = Artifact("northern_water", "current", "u", fixtures_dir / "northern_water_sample.json", {})
    frames = [
        dwr_cdss.parse(a_dwr.local_path, a_dwr),
        reclamation_rise.parse(a_rise.local_path, a_rise),
        northern_water.parse(a_nw.local_path, a_nw),
    ]
    return pd.concat(frames, ignore_index=True)


def test_combined_frame_validates(fixtures_dir):
    combined = _build(fixtures_dir)
    validated = schema.validate(combined)               # raises on any contract violation
    assert len(validated) == 3 + 3 + 4                  # dwr + rise + northern
    assert set(validated["source"]) == {"dwr_cdss", "reclamation_rise", "northern_water"}


def test_composite_key_unique(fixtures_dir):
    combined = _build(fixtures_dir)
    key = ["source", "reservoir_id", "datetime", "variable"]
    assert not combined.duplicated(key).any()


def test_units_and_variables_in_vocabulary(fixtures_dir):
    combined = _build(fixtures_dir)
    assert set(combined["variable"]) <= set(schema.VARIABLES)
    assert set(combined["unit"]) <= set(schema.VARIABLES.values())
