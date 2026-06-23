"""Snow-course parser — the two gotchas vs SNOTEL: the date lives in
``collectionDate`` (not ``date``), and the cadence is semimonthly. Asserted against
a trimmed real AWDB response (Park Cone snow course, 06L02:CO:SNOW).
"""
import pandas as pd

from snowpack.parsers import nrcs_snowcourse
from snowpack.schema import LONG_COLUMNS
from snowpack.sources import Artifact


def _art(path):
    return Artifact("nrcs_snowcourse", "current", "u", path,
                    {"site_id": "06L02:CO:SNOW", "site_name": "Park Cone",
                     "date_field": "collectionDate"})


def test_uses_collection_date(fixtures_dir):
    fx = fixtures_dir / "nrcs_snowcourse_sample.json"
    df = nrcs_snowcourse.parse(fx, _art(fx))
    assert list(df.columns) == LONG_COLUMNS
    assert set(df["variable"]) == {"swe_in", "snow_depth_in"}  # snow courses: SWE + depth, no PREC
    # the real measurement date comes from collectionDate (floored to the day)
    dates = set(df["datetime"])
    assert pd.Timestamp("2019-01-29") in dates
    assert pd.Timestamp("2020-02-27") in dates


def test_known_swe_value(fixtures_dir):
    fx = fixtures_dir / "nrcs_snowcourse_sample.json"
    df = nrcs_snowcourse.parse(fx, _art(fx))
    swe = df[df["variable"] == "swe_in"].set_index("datetime")["value"]
    assert swe[pd.Timestamp("2019-03-28")] == 14.7
    assert swe[pd.Timestamp("2020-01-28")] == 5.6


def test_qa_flag_from_qaflag(fixtures_dir):
    fx = fixtures_dir / "nrcs_snowcourse_sample.json"
    df = nrcs_snowcourse.parse(fx, _art(fx))
    # snow-course values carry qaFlag 'P' (qcFlag is null) → qa_flag == 'P'
    assert (df["qa_flag"] == "P").all()
