"""Discover builds correct, parameterized URLs and honors the sites/meas_types filters.

Offline (no network): discover() only reads the seed and builds URLs. They pin the
request contract the live probes confirmed (climatestationtsday; measType per
request; min-measDate/max-measDate date keys; a station identifier is required).
"""
import pandas as pd

from climate_stations import config, schema


def _first_seed_site() -> str:
    return str(pd.read_csv(config.STATIONS_CSV, dtype=str)["site_id"].iloc[0])


def test_discover_builds_climatestationtsday_url():
    site = _first_seed_site()
    src = config.get_sources()["cdss_climate"]
    arts = list(src.discover(sites={site}, meas_types={"Precip"}))
    assert len(arts) == 1                                   # one station × one measType
    url = arts[0].url
    assert "climatedata/climatestationtsday/" in url
    assert f"stationNum={site}" in url
    assert "measType=Precip" in url
    assert "min-measDate=" in url and "max-measDate=" in url  # NOT startDate
    assert arts[0].metadata["variable"] == "precip_in"
    assert arts[0].local_path.name == f"{site}_Precip.json"


def test_no_meastype_filter_yields_all_twelve():
    site = _first_seed_site()
    src = config.get_sources()["cdss_climate"]
    arts = list(src.discover(sites={site}))
    assert len(arts) == len(schema.MEAS_MAP) == 12          # one artifact per measType


def test_sites_filter_restricts_to_subset():
    site = _first_seed_site()
    src = config.get_sources()["cdss_climate"]
    all_arts = list(src.discover())
    one = list(src.discover(sites={site}))
    assert len(all_arts) > len(one) == 12                   # seed has many stations
