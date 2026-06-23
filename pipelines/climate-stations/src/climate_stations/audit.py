"""Audit: profile the retrieval, profile the processed data, reconcile vs. truth.

Three layers (Ehrlinger & Wöß): **profile** (describe what's there), **measure**
(metrics against the schema/dimensions), **monitor** (diff the reports over time).

- ``profile_raw``       — did the fetch return data? counts/shapes per source,
  straight off ``data/original/``. Catches an empty/failed retrieval *before*
  cleaning.
- ``audit_processed``   — full profile of the tidy CSV: rows per variable, null
  rates, distinct stations, date coverage, per-variable value ranges → Markdown.
- ``coverage_report``   — per-station period of record (different stations,
  different spans), the "full history per station" check.
- ``variables_report``  — the mechanical column profile (``docs/variables.csv``),
  the data dictionary's sanity check.
- ``network_summary``   — rows/stations per observing network (NOAA / CoCoRaHS /
  NRCS / CoAgMet / NCWCD), by joining ``stations.csv``. The climate analogue of the
  streamflow cross-source check: it surfaces the multi-network composition (and the
  NRCS/SNOTEL rows that overlap snowpack issue #11).
- ``reconcile``         — accuracy vs. a published figure (optional, non-blocking).
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd

from climate_stations import config

from co_pipeline_core import audit as _coreaudit


def _ts() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def profile_raw(original_dir: Path | None = None) -> str:
    """Summarize what's on disk in ``data/original/`` -> Markdown (shared)."""
    return _coreaudit.profile_raw(original_dir or config.ORIGINAL, config.AUDIT)


def audit_processed(csv: Path | None = None) -> str:
    """Profile the tidy CSV → ``data/audit/summary-<ts>.md`` (returns the text)."""
    csv = csv or config.CANONICAL_CSV
    df = pd.read_csv(csv, parse_dates=["datetime"])
    L = [f"# Processed audit — {_ts()}", "", f"Rows: **{len(df):,}**", ""]

    L += ["## Rows per variable", "",
          "| variable | unit | rows | stations | null values |", "|---|---|--:|--:|--:|"]
    for var, sub in df.groupby("variable"):
        unit = sub["unit"].dropna().iloc[0] if sub["unit"].notna().any() else "—"
        L.append(f"| {var} | {unit} | {len(sub):,} | {sub['site_id'].nunique()} "
                 f"| {sub['value'].isna().sum()} |")

    L += ["", "## Date coverage", "", "| earliest | latest |", "|---|---|"]
    L.append(f"| {df['datetime'].min():%Y-%m-%d} | {df['datetime'].max():%Y-%m-%d} |")

    L += ["", "## Value ranges per variable (sanity / outliers)", "",
          "| variable | unit | min | median | max |", "|---|---|--:|--:|--:|"]
    for var, sub in df.groupby("variable"):
        v = sub["value"].dropna()
        unit = sub["unit"].dropna().iloc[0] if sub["unit"].notna().any() else "—"
        if len(v):
            L.append(f"| {var} | {unit} | {v.min():,.2f} | {v.median():,.2f} | {v.max():,.2f} |")

    report = "\n".join(L) + "\n"
    out = config.AUDIT / f"summary-{_ts()}.md"
    out.write_text(report)
    return report


def coverage_report(csv: Path | None = None) -> pd.DataFrame:
    """Per-station period of record — makes 'different stations, different coverage'
    explicit. Each station is pulled for its *full* history (auto-clamped to its own
    record), so spans vary widely. Writes ``data/audit/coverage-<ts>.md``."""
    csv = csv or config.CANONICAL_CSV
    df = pd.read_csv(csv)
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    g = (df.groupby(["site_id", "site_name"], dropna=False)
           .agg(first=("datetime", "min"), last=("datetime", "max"),
                rows=("value", "size"), variables=("variable", "nunique")).reset_index())
    g["years"] = ((g["last"] - g["first"]).dt.days / 365.25).round(1)
    g = g.sort_values("first").reset_index(drop=True)

    def _d(x):  # NaT-safe date format
        return f"{x:%Y-%m-%d}" if pd.notna(x) else "—"

    span_lo, span_hi = g["first"].min(), g["last"].max()
    med = g["years"].median()
    L = [f"# Coverage per station — {_ts()}", "",
         f"{len(g)} stations · spanning {_d(span_lo)} → {_d(span_hi)} · "
         f"median record {med:.0f} yr" if pd.notna(med) else f"{len(g)} stations", "",
         "| station | first | last | years | vars | rows |", "|---|---|---|--:|--:|--:|"]
    for _, r in g.iterrows():
        L.append(f"| {r['site_name'] or r['site_id']} | {_d(r['first'])} | {_d(r['last'])} "
                 f"| {r['years']} | {int(r['variables'])} | {int(r['rows'])} |")
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


def network_summary(csv: Path | None = None, stations_csv: Path | None = None) -> pd.DataFrame:
    """Rows/stations per observing network — the multi-network composition of the
    dataset. Joins the processed CSV to ``stations.csv`` on ``site_id`` to recover
    each station's ``network`` (``dataSource``). Flags the NRCS/SNOTEL stations whose
    ``swe_in`` overlaps snowpack issue #11. Writes ``data/audit/network-summary.json``."""
    csv = csv or config.CANONICAL_CSV
    stations_csv = stations_csv or config.STATIONS_CSV
    df = pd.read_csv(csv, dtype={"site_id": str})
    seed = pd.read_csv(stations_csv, dtype={"site_id": str})[["site_id", "network"]]
    merged = df.merge(seed, on="site_id", how="left")
    merged["network"] = merged["network"].fillna("(unknown)")
    out = []
    for net, sub in merged.groupby("network"):
        out.append({
            "network": net,
            "stations": int(sub["site_id"].nunique()),
            "rows": int(len(sub)),
            "variables": int(sub["variable"].nunique()),
            "has_swe": bool((sub["variable"] == "swe_in").any()),
        })
    res = pd.DataFrame(out, columns=["network", "stations", "rows", "variables", "has_swe"])
    res = res.sort_values("rows", ascending=False).reset_index(drop=True)
    (config.AUDIT / "network-summary.json").write_text(res.to_json(orient="records", indent=2))
    return res


def reconcile(expected_now: dict | None = None, csv: Path | None = None) -> pd.DataFrame:
    """Spot-check our latest value against a published figure (optional, non-blocking).

    ``expected_now`` maps ``(variable, site_id) -> value``, the most-recent daily
    value read off the agency's station page (CDSS / NOAA). Returns a frame with
    ``expected`` (yours), ``got`` (our latest value for that station+variable, or
    null if absent), and ``match`` — True when ``|got - expected|`` is within
    ``max(0.1, 0.05 * |expected|)``. A False is a discrepancy to investigate before
    publishing."""
    expected_now = expected_now or {}
    csv = csv or config.CANONICAL_CSV
    df = pd.read_csv(csv, parse_dates=["datetime"], dtype={"site_id": str})
    out = []
    latest = df.sort_values("datetime").groupby(["variable", "site_id"]).tail(1)
    for (variable, sid), exp in expected_now.items():
        got = latest[(latest["variable"] == variable) & (latest["site_id"] == str(sid))]["value"]
        got_v = float(got.iloc[0]) if len(got) and pd.notna(got.iloc[0]) else None
        out.append({"variable": variable, "site_id": str(sid), "expected": exp, "got": got_v,
                    "match": got_v is not None and abs(got_v - exp) <= max(0.1, 0.05 * abs(exp))})
    res = pd.DataFrame(out, columns=["variable", "site_id", "expected", "got", "match"])
    (config.AUDIT / "reconcile.json").write_text(res.to_json(orient="records", indent=2))
    return res
