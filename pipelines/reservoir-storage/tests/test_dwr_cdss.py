"""Parser test for CO DWR/CDSS — known-fixture-in, expected-frame-out.

The second assertion is a small-scale reconciliation (the work `reconcile.py`
does at full scale), run against a fixture so it's fast in CI.
"""
from pathlib import Path

from reservoir.parsers import dwr_cdss
from reservoir.sources import Artifact


def _artifact(path: Path) -> Artifact:
    return Artifact(
        source="dwr_cdss", vintage="current", url="https://example/test",
        local_path=path,
        metadata={"reservoir_id": "GRERESCO",
                  "reservoir_name": "Green Mountain Reservoir", "param": "STORAGE"},
    )


def test_parses_canonical_schema(fixtures_dir):
    fx = fixtures_dir / "dwr_cdss_storage_sample.json"
    df = dwr_cdss.parse(fx, _artifact(fx))
    assert len(df) == 3
    assert df["source"].unique().tolist() == ["dwr_cdss"]
    assert set(df["variable"]) == {"storage_af"}
    assert df["unit"].unique().tolist() == ["acre-ft"]


def test_known_value(fixtures_dir):
    fx = fixtures_dir / "dwr_cdss_storage_sample.json"
    df = dwr_cdss.parse(fx, _artifact(fx))
    latest = df.sort_values("datetime").iloc[-1]
    assert latest["value"] == 138214.0          # measValue from the fixture
    assert latest["reservoir_id"] == "GRERESCO"  # parser reads abbrev from the response
    assert str(latest["datetime"].date()) == "2025-06-18"
