"""Tests for reservoir enumeration (station-list URLs + DWR station parsing)."""
from reservoir import stations


def test_station_list_urls_build():
    # DWR + RISE are the enumerable storage sources
    assert stations.station_list_url("dwr_cdss").startswith("http")
    assert "telemetrystation" in stations.station_list_url("dwr_cdss")
    assert stations.station_list_url("reclamation_rise").startswith("http")
    assert "/location?search=" in stations.station_list_url("reclamation_rise")
    # Northern has no storage service -> empty enumeration URL (boundaries-only hub)
    assert stations.station_list_url("northern_water") == ""


def test_parse_dwr_stations(fixtures_dir):
    df = stations.parse_dwr_stations(fixtures_dir / "dwr_cdss_stations_sample.json")
    # 3 stations in the fixture, but the DISCHRG one is filtered out (STORAGE only)
    assert len(df) == 2
    assert list(df.columns) == stations.SEED_COLUMNS
    assert set(df["reservoir_id"]) == {"GRERESCO", "DILRESCO"}
    assert df["source"].unique().tolist() == ["dwr_cdss"]


def test_parse_rise_location_items(fixtures_dir):
    import json
    payload = json.loads((fixtures_dir / "rise_location_items_sample.json").read_text())
    ids = stations.parse_rise_location_items(payload)
    # Precipitation + catalog-record ignored; storage/elevation/release mapped
    assert ids == {"storage_af": 76, "elevation_ft": 78, "release_cfs": 4310}


def test_rise_enumeration_urls_build():
    assert "/location?search=" in stations.rise_location_search_url("Blue Mesa")
    assert stations.rise_location_items_url(1533).endswith(
        "/location/1533?include=catalogRecords.catalogItems")


def test_merge_into_seed_dedupes(fixtures_dir, tmp_path):
    seed = tmp_path / "reservoirs.csv"
    first = stations.parse_dwr_stations(fixtures_dir / "dwr_cdss_stations_sample.json")
    stations.merge_into_seed(first, seed_path=seed)
    # merging the same rows again must not duplicate
    merged = stations.merge_into_seed(first, seed_path=seed)
    assert len(merged) == 2
