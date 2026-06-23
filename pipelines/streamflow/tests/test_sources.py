"""Discover builds correct, parameterized URLs and honors the sites filter.

These are offline (no network): discover() only reads the seed and builds URLs.
They pin the source-specific request contract that the live probes confirmed
(USGS parameterCd/statCd; DWR measType=Streamflow + min-measDate keys).
"""
from streamflow import config


def test_usgs_discover_builds_dv_url():
    src = config.get_sources()["usgs_nwis"]
    arts = list(src.discover(sites={"09095500"}))
    assert len(arts) == 1                                   # one site × one variable
    url = arts[0].url
    assert "/dv/?" in url
    assert "sites=09095500" in url
    assert "parameterCd=00060" in url                       # discharge
    assert "statCd=00003" in url                            # daily mean
    assert arts[0].metadata["variable"] == "discharge_cfs"
    assert arts[0].local_path.name == "09095500_00060.json"


def test_dwr_discover_builds_surfacewater_url():
    src = config.get_sources()["dwr_cdss"]
    arts = list(src.discover(sites={"COLCAMCO"}))
    assert len(arts) == 1
    url = arts[0].url
    assert "surfacewater/surfacewatertsday/" in url
    assert "measType=Streamflow" in url                     # NOT DISCHRG
    assert "min-measDate=" in url and "max-measDate=" in url  # NOT startDate
    assert arts[0].metadata["site_id"] == "COLCAMCO"


def test_sites_filter_restricts_to_subset():
    src = config.get_sources()["usgs_nwis"]
    all_arts = list(src.discover())
    one = list(src.discover(sites={"09095500"}))
    assert len(all_arts) > len(one) == 1                    # seed has many gages
