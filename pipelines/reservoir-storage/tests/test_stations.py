"""Tests for reservoir enumeration (station-list URLs + DWR station parsing)."""
from reservoir import stations


def test_station_list_urls_build():
    for slug in ("dwr_cdss", "reclamation_rise", "northern_water"):
        url = stations.station_list_url(slug)
        assert url.startswith("http")
    assert "telemetrystation" in stations.station_list_url("dwr_cdss")
    assert "catalog-item" in stations.station_list_url("reclamation_rise")
    assert "/query" in stations.station_list_url("northern_water")


def test_parse_dwr_stations(fixtures_dir):
    df = stations.parse_dwr_stations(fixtures_dir / "dwr_cdss_stations_sample.json")
    assert len(df) == 2
    assert list(df.columns) == stations.SEED_COLUMNS
    assert set(df["reservoir_id"]) == {"GREEN MOUNTAIN", "DILLON"}
    assert df["source"].unique().tolist() == ["dwr_cdss"]


def test_merge_into_seed_dedupes(fixtures_dir, tmp_path):
    seed = tmp_path / "reservoirs.csv"
    first = stations.parse_dwr_stations(fixtures_dir / "dwr_cdss_stations_sample.json")
    stations.merge_into_seed(first, seed_path=seed)
    # merging the same rows again must not duplicate
    merged = stations.merge_into_seed(first, seed_path=seed)
    assert len(merged) == 2
