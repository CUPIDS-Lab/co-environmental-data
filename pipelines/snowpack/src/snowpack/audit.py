"""Audit: profile the retrieval, profile the processed data, reconcile vs. truth.

Three layers (Ehrlinger & Wöß): **profile** (describe what's there), **measure**
(metrics against the schema/dimensions), **monitor** (diff the reports over time).

- ``profile_raw``      — did the fetch return data? counts/shapes per source,
  straight off ``data/original/``. Catches an empty/failed retrieval *before*
  cleaning.
- ``audit_processed``  — full profile of the tidy CSV: rows per source, null
  rates, distinct stations, date coverage, per-variable value ranges → Markdown.
- ``coverage_report``  — per-station period of record (SNOTEL ~1980+; snow courses
  back to the 1930s–40s), the "full history per site" check.
- ``variables_report`` — the mechanical column profile (``docs/variables.csv``).
- ``basin_percent_normal`` — THE signature snowpack product (issue #11): basin SWE
  as a percent of the day-of-year normal, the number every CO runoff/drought story
  leads with. Computed from the liberated record itself.
- ``reconcile_basin_pct_normal`` — accuracy gate: our basin % of normal vs. the
  NRCS basin report's published figure.
- ``reconcile_cross_source`` — SNOTEL↔snow-course **co-location** agreement. Unlike
  streamflow's USGS↔DWR re-serve (identical values), these are NEARBY-not-identical
  sites, so the check is looser by design (a correlation sanity check, not identity).
"""
from __future__ import annotations

import datetime as _dt
import json
import math
from pathlib import Path

import pandas as pd

from snowpack import config

from co_pipeline_core import audit as _coreaudit

# NRCS normals baseline (the current official period). The median for a station's
# day-of-year is computed over these years where available; documented in concepts.
NORMAL_BASELINE = (1991, 2020)


def _ts() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def profile_raw(original_dir: Path | None = None) -> str:
    """Summarize what's on disk in ``data/original/`` -> Markdown (shared)."""
    return _coreaudit.profile_raw(original_dir or config.ORIGINAL, config.AUDIT)


def audit_processed(csv: Path | None = None) -> str:
    """Profile the tidy CSV -> ``data/audit/summary-<ts>.md`` (shared)."""
    return _coreaudit.audit_processed(csv or config.CANONICAL_CSV, config.AUDIT, id_col="site_id", entity="stations")


def coverage_report(csv: Path | None = None) -> pd.DataFrame:
    """Per-station period of record — SNOTEL ~1980+, snow courses to the 1930s–40s.
    Each station is pulled for its *full* history (auto-clamped to its own record).
    Writes ``data/audit/coverage-<ts>.md``."""
    csv = csv or config.CANONICAL_CSV
    df = pd.read_csv(csv)
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    g = (df.groupby(["source", "site_id", "site_name"], dropna=False)
           .agg(first=("datetime", "min"), last=("datetime", "max"),
                rows=("value", "size")).reset_index())
    g["years"] = ((g["last"] - g["first"]).dt.days / 365.25).round(1)
    g = g.sort_values("first").reset_index(drop=True)

    def _d(x):  # NaT-safe date format
        return f"{x:%Y-%m-%d}" if pd.notna(x) else "—"

    span_lo, span_hi = g["first"].min(), g["last"].max()
    med = g["years"].median()
    L = [f"# Coverage per station — {_ts()}", "",
         f"{len(g)} station-series · spanning {_d(span_lo)} → {_d(span_hi)} · "
         f"median record {med:.0f} yr" if pd.notna(med) else f"{len(g)} station-series", "",
         "| source | station | first | last | years | rows |", "|---|---|---|---|--:|--:|"]
    for _, r in g.iterrows():
        L.append(f"| {r['source']} | {r['site_name'] or r['site_id']} | "
                 f"{_d(r['first'])} | {_d(r['last'])} | {r['years']} | {int(r['rows'])} |")
    out = config.AUDIT / f"coverage-{_ts()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n")
    return g


def variables_report(csv: Path | None = None) -> pd.DataFrame:
    """Auto-generated per-column profile → ``docs/variables.csv`` (dict sanity check)."""
    csv = csv or config.CANONICAL_CSV
    df = pd.read_csv(csv)
    rows = []
    for col in df.columns:
        s = df[col]
        rows.append({"column": col, "dtype": str(s.dtype), "distinct": s.nunique(dropna=True),
                     "null_rate": round(s.isna().mean(), 4),
                     "sample": "; ".join(map(str, s.dropna().unique()[:5]))})
    out = pd.DataFrame(rows)
    (config.PROJECT_DIR / "docs").mkdir(exist_ok=True)
    out.to_csv(config.PROJECT_DIR / "docs" / "variables.csv", index=False)
    return out


# ── the signature snowpack product ────────────────────────────────────────────
def basin_percent_normal(csv: Path | None = None, sites_csv: Path | None = None,
                         target_date: str | None = None, window_days: int = 7,
                         baseline: tuple[int, int] = NORMAL_BASELINE) -> pd.DataFrame:
    """Basin SWE as a percent of the day-of-year normal — the headline snowpack metric.

    For each **SNOTEL** station (the daily automated network), takes the SWE on
    ``target_date`` (default: the latest date in the data) — or the most recent value
    within ``window_days`` before it — and divides by that station's **median SWE for
    the same month-day** over the ``baseline`` years (NRCS's 1991–2020 normals period,
    falling back to the full record if a station lacks that window). The basin figure
    is ``100 × Σ current / Σ normal`` over stations reporting both — the same
    sum-of-stations construction NRCS uses. Writes ``data/audit/basin-percent-normal-
    <ts>.md`` + ``.json``. Returns the per-basin frame.
    """
    csv = csv or config.CANONICAL_CSV
    sites_csv = sites_csv or config.SITES_CSV
    df = pd.read_csv(csv, parse_dates=["datetime"])
    df = df[(df["variable"] == "swe_in") & (df["source"] == "nrcs_snotel")].copy()
    seed = pd.read_csv(sites_csv, dtype=str)[["site_id", "basin"]]

    res_cols = ["basin", "stations", "current_swe_in", "normal_swe_in", "pct_of_normal"]
    if df.empty:
        empty = pd.DataFrame(columns=res_cols)
        (config.AUDIT / "basin-percent-normal.json").write_text(empty.to_json(orient="records", indent=2))
        return empty

    target = pd.to_datetime(target_date) if target_date else df["datetime"].max()
    lo, hi = baseline
    df["md"] = df["datetime"].dt.strftime("%m-%d")
    df["yr"] = df["datetime"].dt.year

    # per-station current value: latest non-null SWE in (target - window, target]
    win = df[(df["datetime"] <= target)
             & (df["datetime"] > target - pd.Timedelta(days=window_days))
             & df["value"].notna()]
    current = (win.sort_values("datetime").groupby("site_id").tail(1)
               [["site_id", "value"]].rename(columns={"value": "current_swe_in"}))

    # per-station normal: median SWE for the target month-day over the baseline years
    md = target.strftime("%m-%d")
    base = df[(df["md"] == md) & (df["yr"].between(lo, hi)) & df["value"].notna()]
    if base.empty:  # baseline window not covered — fall back to full record for that day
        base = df[(df["md"] == md) & df["value"].notna()]
    normal = (base.groupby("site_id")["value"].median()
              .reset_index().rename(columns={"value": "normal_swe_in"}))

    j = (current.merge(normal, on="site_id", how="inner")
         .merge(seed, on="site_id", how="left"))
    j = j[j["normal_swe_in"] > 0]  # can't take % of a zero/absent normal
    out = (j.groupby("basin")
           .agg(stations=("site_id", "nunique"),
                current_swe_in=("current_swe_in", "sum"),
                normal_swe_in=("normal_swe_in", "sum")).reset_index())
    out["pct_of_normal"] = (100 * out["current_swe_in"] / out["normal_swe_in"]).round(0)
    out = out.sort_values("basin").reset_index(drop=True)[res_cols]

    statewide = {
        "basin": "STATEWIDE", "stations": int(out["stations"].sum()),
        "current_swe_in": float(out["current_swe_in"].sum()),
        "normal_swe_in": float(out["normal_swe_in"].sum()),
        "pct_of_normal": round(100 * out["current_swe_in"].sum() / out["normal_swe_in"].sum(), 0)
        if out["normal_swe_in"].sum() else None,
    }
    out_full = pd.concat([out, pd.DataFrame([statewide])], ignore_index=True)

    L = [f"# Basin SWE — percent of {lo}–{hi} normal — {_ts()}", "",
         f"As of **{target:%Y-%m-%d}** · {statewide['stations']} SNOTEL stations reporting · "
         f"day-of-year median normal.", "",
         "| basin | stations | current SWE (in) | normal SWE (in) | % of normal |",
         "|---|--:|--:|--:|--:|"]
    for _, r in out_full.iterrows():
        bold = "**" if r["basin"] == "STATEWIDE" else ""
        pct = f"{r['pct_of_normal']:.0f}%" if pd.notna(r["pct_of_normal"]) else "—"
        L.append(f"| {bold}{r['basin']}{bold} | {int(r['stations'])} | {r['current_swe_in']:,.1f} | "
                 f"{r['normal_swe_in']:,.1f} | {bold}{pct}{bold} |")
    L += ["", "> Computed from the liberated SNOTEL record, not the official NRCS basin "
          "report — see `reconcile_basin_pct_normal` for the accuracy check and "
          "`concepts.yaml` for the methodology caveat (sum-of-stations; missing ≠ zero)."]
    (config.AUDIT / f"basin-percent-normal-{_ts()}.md").write_text("\n".join(L) + "\n")
    (config.AUDIT / "basin-percent-normal.json").write_text(out_full.to_json(orient="records", indent=2))
    return out_full


def reconcile_basin_pct_normal(expected_pct: dict | None = None, csv: Path | None = None,
                               tol_points: float = 10.0) -> pd.DataFrame:
    """Accuracy gate: our basin % of normal vs. the NRCS basin report's figure.

    ``expected_pct`` maps ``basin -> published % of normal`` read off the NRCS
    Colorado Snow Survey / NWCC basin report for the same date. ``match`` is True when
    ``|ours - published| <= tol_points`` (default 10 pts — methodology and the exact
    normals baseline differ between us and NRCS, so a looser band than streamflow's
    discharge gate). A False is worth investigating before publishing. Non-blocking."""
    expected_pct = expected_pct or {}
    ours = basin_percent_normal(csv=csv).set_index("basin")["pct_of_normal"].to_dict()
    out = []
    for basin, exp in expected_pct.items():
        got = ours.get(basin)
        out.append({"basin": basin, "expected_pct": exp, "got_pct": got,
                    "match": got is not None and abs(got - exp) <= tol_points})
    res = pd.DataFrame(out, columns=["basin", "expected_pct", "got_pct", "match"])
    (config.AUDIT / "reconcile-basin.json").write_text(res.to_json(orient="records", indent=2))
    return res


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def colocated_pairs(sites_csv: Path | None = None, max_km: float = 2.0) -> pd.DataFrame:
    """Crosswalk SNOTEL ↔ snow-course stations that are co-located (same name OR
    within ``max_km``). The basis for the cross-source check and a deliverable in its
    own right (which historical snow course a SNOTEL continues). Writes
    ``data/lookups/`` is NOT touched — this is computed on demand."""
    sites_csv = sites_csv or config.SITES_CSV
    seed = pd.read_csv(sites_csv)
    for c in ("latitude", "longitude"):
        seed[c] = pd.to_numeric(seed[c], errors="coerce")
    sntl = seed[seed["source"] == "nrcs_snotel"]
    snow = seed[seed["source"] == "nrcs_snowcourse"]
    rows = []
    for _, a in sntl.iterrows():
        for _, b in snow.iterrows():
            same_name = (str(a["site_name"]).strip().lower()
                         == str(b["site_name"]).strip().lower())
            dist = None
            if pd.notna(a["latitude"]) and pd.notna(b["latitude"]):
                dist = _haversine_km(a["latitude"], a["longitude"], b["latitude"], b["longitude"])
            if same_name or (dist is not None and dist <= max_km):
                rows.append({"snotel_site_id": a["site_id"], "snotel_name": a["site_name"],
                             "snowcourse_site_id": b["site_id"], "snowcourse_name": b["site_name"],
                             "same_name": same_name,
                             "distance_km": round(dist, 2) if dist is not None else None})
    return pd.DataFrame(rows, columns=["snotel_site_id", "snotel_name", "snowcourse_site_id",
                                       "snowcourse_name", "same_name", "distance_km"])


def reconcile_cross_source(csv: Path | None = None, sites_csv: Path | None = None,
                           rel_tol: float = 0.25, abs_floor_in: float = 2.0,
                           min_overlap: int = 5) -> pd.DataFrame:
    """Cross-source check: a SNOTEL and its co-located snow course should track on
    shared measurement dates. Joins co-located pairs (``colocated_pairs``) on
    ``date`` for ``swe_in`` and reports, per pair, the count of shared
    (snow-course-measurement) dates and the share agreeing within ``rel_tol`` (25 %)
    or ``abs_floor_in`` (2 in) — whichever is larger.

    ⚠️ Looser than streamflow's USGS↔DWR re-serve: these are NEARBY, not identical,
    sites (different aspect/elevation/exposure), and a semimonthly point sample vs a
    daily sensor — so agreement is a *sanity correlation*, not an identity. A very low
    rate flags a bad pairing; near-zero overlap is expected for pairs whose records
    don't temporally overlap. Writes ``data/audit/reconcile-cross-source.json``."""
    csv = csv or config.CANONICAL_CSV
    pairs = colocated_pairs(sites_csv)
    df = pd.read_csv(csv, parse_dates=["datetime"])
    df = df[df["variable"] == "swe_in"]
    sntl = df[df["source"] == "nrcs_snotel"][["site_id", "datetime", "value"]]
    snow = df[df["source"] == "nrcs_snowcourse"][["site_id", "datetime", "value"]]

    out = []
    for _, p in pairs.iterrows():
        a = sntl[sntl["site_id"] == p["snotel_site_id"]].rename(columns={"value": "snotel_in"})
        b = snow[snow["site_id"] == p["snowcourse_site_id"]].rename(columns={"value": "snow_in"})
        m = a.merge(b, on="datetime", how="inner").dropna(subset=["snotel_in", "snow_in"])
        if len(m) < min_overlap:
            continue
        tol = (rel_tol * m["snotel_in"].abs()).clip(lower=abs_floor_in)
        within = (m["snotel_in"] - m["snow_in"]).abs() <= tol
        out.append({
            "snotel_site_id": p["snotel_site_id"],
            "snowcourse_site_id": p["snowcourse_site_id"],
            "name": p["snotel_name"],
            "distance_km": p["distance_km"],
            "shared_dates": int(len(m)),
            "agree_within_tol": int(within.sum()),
            "agree_rate": round(float(within.mean()), 4),
            "median_abs_diff_in": round(float((m["snotel_in"] - m["snow_in"]).abs().median()), 2),
        })
    res = pd.DataFrame(out, columns=["snotel_site_id", "snowcourse_site_id", "name",
                                     "distance_km", "shared_dates", "agree_within_tol",
                                     "agree_rate", "median_abs_diff_in"])
    (config.AUDIT / "reconcile-cross-source.json").write_text(res.to_json(orient="records", indent=2))
    return res
