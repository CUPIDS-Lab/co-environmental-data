"""Audit — the snowpack-specific math: HUC→basin mapping, basin % of normal,
the co-location crosswalk, and cross-source reconciliation, all on constructed
fixtures (no network, no dependence on the live record).
"""
import pandas as pd

from snowpack import audit, stations


# ── HUC → basin crosswalk ─────────────────────────────────────────────────────
def test_huc_to_basin():
    assert stations.huc_to_basin("140200010101") == "Gunnison"
    assert stations.huc_to_basin("14050005...") == "White"        # White–Yampa split
    assert stations.huc_to_basin("140500010203") == "Yampa-Green"
    assert stations.huc_to_basin("101900020304") == "South Platte"
    assert stations.huc_to_basin("130100010101") == "Rio Grande"
    assert stations.huc_to_basin("99999999") == "Other"


def _sites(tmp_path):
    p = tmp_path / "sites.csv"
    pd.DataFrame([
        {"source": "nrcs_snotel", "site_id": "680:CO:SNTL", "station_id": "680",
         "site_name": "Park Cone", "basin": "Gunnison", "network": "SNTL",
         "latitude": 38.823, "longitude": -106.588},
        {"source": "nrcs_snowcourse", "site_id": "06L02:CO:SNOW", "station_id": "06L02",
         "site_name": "Park Cone", "basin": "Gunnison", "network": "SNOW",
         "latitude": 38.824, "longitude": -106.589},
    ]).to_csv(p, index=False)
    return p


def test_basin_percent_normal(tmp_path):
    sites = _sites(tmp_path)
    rows = []
    for yr, swe in [(2015, 10), (2016, 12), (2017, 8), (2018, 14), (2019, 11)]:
        rows.append(dict(source="nrcs_snotel", vintage="current", site_id="680:CO:SNTL",
                         site_name="Park Cone", datetime=f"{yr}-03-01", variable="swe_in",
                         value=swe, unit="in", qa_flag="V", concept="snowpack.swe_in"))
    rows.append(dict(source="nrcs_snotel", vintage="current", site_id="680:CO:SNTL",
                     site_name="Park Cone", datetime="2020-03-01", variable="swe_in",
                     value=16.5, unit="in", qa_flag="P", concept="snowpack.swe_in"))
    csv = tmp_path / "snowpack.csv"
    pd.DataFrame(rows).to_csv(csv, index=False)

    out = audit.basin_percent_normal(csv=csv, sites_csv=sites, baseline=(2015, 2019))
    gunnison = out[out["basin"] == "Gunnison"].iloc[0]
    # current 16.5 / median([10,12,8,14,11]=11) = 150%
    assert gunnison["pct_of_normal"] == 150
    assert "STATEWIDE" in set(out["basin"])


def test_colocated_pairs(tmp_path):
    pairs = audit.colocated_pairs(sites_csv=_sites(tmp_path))
    assert len(pairs) == 1
    row = pairs.iloc[0]
    assert row["same_name"] and row["snotel_site_id"] == "680:CO:SNTL"
    assert row["distance_km"] < 1.0  # ~co-located


def test_reconcile_cross_source(tmp_path):
    sites = _sites(tmp_path)
    rows = []
    for d, sntl, snow in [("2020-02-01", 6.7, 6.5), ("2020-02-02", 6.8, 7.0),
                          ("2020-02-03", 6.9, 7.2)]:
        rows.append(dict(source="nrcs_snotel", vintage="current", site_id="680:CO:SNTL",
                         site_name="Park Cone", datetime=d, variable="swe_in", value=sntl,
                         unit="in", qa_flag="V", concept="snowpack.swe_in"))
        rows.append(dict(source="nrcs_snowcourse", vintage="current", site_id="06L02:CO:SNOW",
                         site_name="Park Cone", datetime=d, variable="swe_in", value=snow,
                         unit="in", qa_flag="P", concept="snowpack.swe_in"))
    csv = tmp_path / "snowpack.csv"
    pd.DataFrame(rows).to_csv(csv, index=False)

    res = audit.reconcile_cross_source(csv=csv, sites_csv=sites, min_overlap=2)
    assert len(res) == 1
    assert res.iloc[0]["shared_dates"] == 3
    assert res.iloc[0]["agree_rate"] == 1.0   # all within the 2-inch floor tolerance
