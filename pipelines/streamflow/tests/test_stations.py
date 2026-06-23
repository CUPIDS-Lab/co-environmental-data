"""Station-metadata: the committed seed carries coordinates, and the enumeration
helpers stay on the same schema (offline; reads the committed seed + parses
in-memory responses)."""
import pandas as pd

from streamflow import config, stations

META_COLS = ["latitude", "longitude", "elevation_ft", "county", "start_date", "end_date"]


def test_committed_seed_has_station_metadata():
    seed = pd.read_csv(config.SITES_CSV, dtype=str)
    # every station-metadata column is present (data dictionary contract)
    for c in stations.SEED_COLUMNS:
        assert c in seed.columns, f"seed missing column {c}"
    # coordinates are populated for every curated gage (both sources)
    for c in ("latitude", "longitude"):
        assert seed[c].notna().all() and (seed[c].str.strip() != "").all()
    # coordinates fall inside Colorado's bounding box
    lat, lon = seed["latitude"].astype(float), seed["longitude"].astype(float)
    assert lat.between(36.0, 41.5).all()
    assert lon.between(-109.5, -101.5).all()


def test_parse_usgs_sites_captures_coords_from_expanded_rdb():
    rdb = (
        "agency_cd\tsite_no\tstation_nm\tdec_lat_va\tdec_long_va\talt_va\n"
        "5s\t15s\t50s\t16s\t16s\t8s\n"
        "USGS\t09095500\tCOLORADO RIVER NEAR CAMEO\t39.2391\t-108.2662\t4799\n"
    )
    df = stations.parse_usgs_sites(rdb)
    row = df.iloc[0]
    assert row["site_id"] == "09095500"
    assert row["latitude"] == "39.2391" and row["longitude"] == "-108.2662"
    assert row["elevation_ft"] == "4799"


def test_parse_dwr_stations_captures_coords_county_por():
    payload = {"ResultList": [{
        "abbrev": "COLCAMCO", "stationName": "COLORADO RIVER NEAR CAMEO, CO.",
        "usgsSiteId": "09095500", "latitude": 39.239151, "longitude": -108.266208,
        "county": "MESA", "startDate": "1933-10-01T00:00:00", "endDate": "2026-06-22T00:00:00",
    }]}
    df = stations.parse_dwr_stations(payload)
    row = df.iloc[0]
    assert row["site_id"] == "COLCAMCO"
    assert row["latitude"] == 39.239151 and row["longitude"] == -108.266208
    assert row["county"] == "Mesa"               # title-cased
    assert row["start_date"] == "1933-10-01" and row["end_date"] == "2026-06-22"


def test_merge_into_seed_fills_missing_columns():
    usgs = stations.parse_usgs_sites(
        "agency_cd\tsite_no\tstation_nm\n5s\t15s\t50s\nUSGS\t09095500\tCAMEO\n")
    merged = stations.merge_into_seed([usgs])
    assert list(merged.columns) == stations.SEED_COLUMNS   # county/POR present though blank
