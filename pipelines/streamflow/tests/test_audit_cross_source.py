"""The cross-source reconciliation this pipeline gets for free.

USGS and DWR re-serve many of the same gages; their series should agree on shared
dates. ``reconcile_cross_source`` joins them via ``usgs_site_no`` and reports the
agreement rate. A divergence flags an id-mapping/unit error (or a provisional vs
approved revision lag). This builds a tiny known frame and checks the math.
"""
import pandas as pd

from streamflow import audit, config


def _write_inputs(tmp_path):
    csv = tmp_path / "streamflow.csv"
    sites = tmp_path / "sites.csv"
    # Same gage via two sources: USGS site 09095500, DWR abbrev COLCAMCO.
    # Day 3 diverges by 10% (> 5% tol) → should count as a disagreement.
    rows = []
    for d, u, w in [("2024-06-01", 100.0, 100.0),
                    ("2024-06-02", 200.0, 200.0),
                    ("2024-06-03", 300.0, 330.0)]:
        rows.append(["usgs_nwis", "current", "09095500", "Cameo", d,
                     "discharge_cfs", u, "cfs", "A", "streamflow.discharge_cfs"])
        rows.append(["dwr_cdss", "current", "COLCAMCO", "Cameo", d,
                     "discharge_cfs", w, "cfs", "A", "streamflow.discharge_cfs"])
    pd.DataFrame(rows, columns=[
        "source", "vintage", "site_id", "site_name", "datetime",
        "variable", "value", "unit", "qa_flag", "concept"]).to_csv(csv, index=False)
    pd.DataFrame([
        ["usgs_nwis", "09095500", "Cameo", "Colorado", "09095500", ""],
        ["dwr_cdss", "COLCAMCO", "Cameo", "Colorado", "09095500", ""],
    ], columns=["source", "site_id", "site_name", "basin", "usgs_site_no", "notes"]
    ).to_csv(sites, index=False)
    return csv, sites


def test_cross_source_pairs_and_scores(tmp_path, monkeypatch):
    # Keep the test hermetic: reconcile_cross_source writes its report to config.AUDIT,
    # so redirect that to tmp_path rather than clobbering the project's real audit dir.
    monkeypatch.setattr(config, "AUDIT", tmp_path)
    csv, sites = _write_inputs(tmp_path)
    res = audit.reconcile_cross_source(csv=csv, sites_csv=sites, rel_tol=0.05, min_overlap=2)
    assert len(res) == 1                                    # one paired gage
    row = res.iloc[0]
    assert row["usgs_site_no"] == "09095500"
    assert row["shared_days"] == 3
    assert row["agree_within_tol"] == 2                     # days 1–2 agree, day 3 diverges 10%
    assert row["max_abs_diff_cfs"] == 30.0
