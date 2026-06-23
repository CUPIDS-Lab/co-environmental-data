"""Station enumeration: catalog response → stations.csv shape, active filter."""
from climate_stations import stations


SAMPLE = {"ResultList": [
    {"stationNum": 18, "siteId": "USC00051342", "stationName": "CARIBOU RANCH",
     "dataSource": "NOAA", "division": 1, "waterDistrict": 6, "county": "BOULDER ",
     "latitude": 40.0, "longitude": -105.5,
     "startDate": "1964-01-01T00:00:00", "endDate": "1968-12-31T00:00:00"},
    {"stationNum": 1886, "siteId": "CTR01", "stationName": "CENTER CSU",
     "dataSource": "CoAgMet", "division": 3, "waterDistrict": 20, "county": "RIO GRANDE",
     "latitude": 37.7, "longitude": -106.1,
     "startDate": "1993-10-08T00:00:00", "endDate": "2026-02-14T00:00:00"},
]}


def test_parse_maps_canonical_columns():
    df = stations.parse_climate_stations(SAMPLE)
    assert list(df.columns) == stations.STATION_COLUMNS
    assert len(df) == 2
    r = df[df["site_id"] == "18"].iloc[0]
    assert r["network"] == "NOAA"
    assert r["site_id_network"] == "USC00051342"            # GHCN id — the #11 crosswalk key
    assert r["start_date"] == "1964-01-01" and r["end_date"] == "1968-12-31"
    assert r["source"] == "cdss_climate"


def test_select_active_filters_by_end_date():
    df = stations.parse_climate_stations(SAMPLE)
    active = stations.select_active(df, since="2024-01-01")
    assert active["site_id"].tolist() == ["1886"]           # Caribou ended 1968, dropped
