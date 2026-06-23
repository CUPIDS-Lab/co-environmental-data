"""Parser test for USGS NWIS — known-fixture-in, expected-frame-out.

The fixture is a real (trimmed) dv response for Colorado River near Cameo
(09095500). The known-value assertion is a small-scale reconciliation (what
``reconcile`` does at full scale), run against a fixture so it's fast in CI.
"""
from pathlib import Path

from streamflow.parsers import usgs_nwis
from streamflow.sources import Artifact


def _artifact(path: Path) -> Artifact:
    return Artifact(
        source="usgs_nwis", vintage="current", url="https://example/test",
        local_path=path,
        metadata={"site_id": "09095500", "site_name": "COLORADO RIVER NEAR CAMEO, CO.",
                  "variable": "discharge_cfs", "param_cd": "00060"},
    )


def test_parses_canonical_schema(fixtures_dir):
    fx = fixtures_dir / "usgs_nwis_sample.json"
    df = usgs_nwis.parse(fx, _artifact(fx))
    assert len(df) == 3
    assert df["source"].unique().tolist() == ["usgs_nwis"]
    assert set(df["variable"]) == {"discharge_cfs"}
    assert df["unit"].unique().tolist() == ["cfs"]
    assert df["concept"].unique().tolist() == ["streamflow.discharge_cfs"]


def test_known_value(fixtures_dir):
    fx = fixtures_dir / "usgs_nwis_sample.json"
    df = usgs_nwis.parse(fx, _artifact(fx))
    latest = df.sort_values("datetime").iloc[-1]
    assert latest["value"] == 12400.0                 # 2024-06-03 daily mean, cfs
    assert latest["site_id"] == "09095500"            # parser reads siteCode from the response
    assert str(latest["datetime"].date()) == "2024-06-03"
    assert latest["qa_flag"] == "A"                   # approved


def test_no_data_site_is_empty_not_error(fixtures_dir, tmp_path):
    """A site with no data returns an empty timeSeries (HTTP 200) → empty frame."""
    empty = tmp_path / "empty.json"
    empty.write_text('{"value": {"timeSeries": []}}')
    df = usgs_nwis.parse(empty, _artifact(empty))
    assert df.empty
