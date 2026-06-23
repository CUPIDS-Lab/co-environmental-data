"""Source URL contract + the sampling filter — pins the AWDB request shape so a
silent endpoint/param drift fails a test, not a live refresh.
"""
from urllib.parse import parse_qs, urlparse

from snowpack import config


def _q(url):
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


def test_snotel_discover_url_contract():
    src = config.get_sources()["nrcs_snotel"]
    arts = list(src.discover(sites={"680:CO:SNTL"}))
    assert len(arts) == 1
    q = _q(arts[0].url)
    assert q["stationTriplets"] == "680:CO:SNTL"
    assert q["elements"] == "WTEQ,SNWD,PREC"
    assert q["duration"] == "DAILY"
    assert q["returnFlags"] == "true"
    assert arts[0].local_path.name == "680_CO_SNTL.json"   # colons sanitized for the filename


def test_snowcourse_discover_url_contract():
    src = config.get_sources()["nrcs_snowcourse"]
    arts = list(src.discover(sites={"06L02:CO:SNOW"}))
    assert len(arts) == 1
    q = _q(arts[0].url)
    assert q["duration"] == "SEMIMONTHLY"            # the snow-course gotcha
    assert q["elements"] == "WTEQ,SNWD"              # no PREC at snow courses


def test_sites_filter_matches_triplet_or_bare_id():
    src = config.get_sources()["nrcs_snotel"]
    by_triplet = list(src.discover(sites={"680:CO:SNTL"}))
    by_bare = list(src.discover(sites={"680"}))      # bare station_id is a convenient key
    assert len(by_triplet) == len(by_bare) == 1
    assert by_triplet[0].metadata["site_id"] == by_bare[0].metadata["site_id"] == "680:CO:SNTL"


def test_no_key_required():
    """AWDB is open — neither source URL carries an apiKey/token param."""
    for slug in ("nrcs_snotel", "nrcs_snowcourse"):
        art = next(config.get_sources()[slug].discover(sites={"680", "06L02"}), None)
        if art:
            q = _q(art.url)
            assert "apiKey" not in q and "token" not in q
