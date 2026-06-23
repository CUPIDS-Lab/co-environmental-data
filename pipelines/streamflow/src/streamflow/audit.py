"""Audit: profile the retrieval, profile the processed data, reconcile vs. truth.

Three layers (Ehrlinger & Wöß): **profile** (describe what's there), **measure**
(metrics against the schema/dimensions), **monitor** (diff the reports over time).

- ``profile_raw``      — did the fetch return data? counts/shapes per source,
  straight off ``data/original/``. Catches an empty/failed retrieval *before*
  cleaning.
- ``audit_processed``  — full profile of the tidy CSV: rows per source, null
  rates, distinct gages, date coverage, per-variable value ranges → Markdown.
- ``coverage_report``  — per-gage period of record (different gages, different
  spans), the "full history per site" check.
- ``variables_report`` — the mechanical column profile (``docs/variables.csv``),
  the data dictionary's sanity check.
- ``reconcile``        — accuracy vs. each agency's own published current flow.
- ``reconcile_cross_source`` — the check this pipeline gets *for free* that the
  reservoir pipeline couldn't: USGS and DWR re-serve many of the SAME gages, so
  the two independent series should agree on shared dates. A large divergence
  flags an id-mapping or unit error. (See ``docs/survey-notes.md``.)
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd

from streamflow import config


def _ts() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def profile_raw(original_dir: Path | None = None) -> str:
    """Summarize what's on disk in ``data/original/`` → Markdown (also written)."""
    original_dir = original_dir or config.ORIGINAL
    lines = [f"# Raw retrieval profile — {_ts()}", ""]
    files = sorted(p for p in original_dir.rglob("*.json") if p.name != "manifest.json")
    by_source: dict[str, list[Path]] = {}
    for f in files:
        by_source.setdefault(f.relative_to(original_dir).parts[0], []).append(f)
    lines.append(f"- Sources with data: **{len(by_source)}** · files: **{len(files)}**\n")
    lines.append("| Source | Files | Total bytes | Sample top-level keys |")
    lines.append("|---|--:|--:|---|")
    for source, fs in sorted(by_source.items()):
        nbytes = sum(p.stat().st_size for p in fs)
        try:
            sample = json.loads(fs[0].read_text())
            keys = ", ".join(list(sample)[:5]) if isinstance(sample, dict) else type(sample).__name__
        except Exception as e:  # noqa: BLE001
            keys = f"(unreadable: {e})"
        lines.append(f"| `{source}` | {len(fs)} | {nbytes:,} | {keys} |")
    if not by_source:
        lines.append("\n> ⚠️ No raw files found — run the retrieve step first, or the fetch failed.")
    report = "\n".join(lines) + "\n"
    out = config.AUDIT / f"raw-profile-{_ts()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    return report


def audit_processed(csv: Path | None = None) -> str:
    """Profile the tidy CSV → ``data/audit/summary-<ts>.md`` (returns the text)."""
    csv = csv or config.CANONICAL_CSV
    df = pd.read_csv(csv, parse_dates=["datetime"])
    L = [f"# Processed audit — {_ts()}", "", f"Rows: **{len(df):,}**", ""]

    L += ["## Rows per source × variable", "",
          "| source | variable | rows | gages | null values |", "|---|---|--:|--:|--:|"]
    for (src, var), sub in df.groupby(["source", "variable"]):
        L.append(f"| {src} | {var} | {len(sub):,} | {sub['site_id'].nunique()} | {sub['value'].isna().sum()} |")

    L += ["", "## Date coverage per source", "", "| source | earliest | latest |", "|---|---|---|"]
    for src, sub in df.groupby("source"):
        L.append(f"| {src} | {sub['datetime'].min():%Y-%m-%d} | {sub['datetime'].max():%Y-%m-%d} |")

    L += ["", "## Value ranges per variable (sanity / outliers)", "",
          "| variable | unit | min | median | max |", "|---|---|--:|--:|--:|"]
    for var, sub in df.groupby("variable"):
        v = sub["value"].dropna()
        if len(v):
            L.append(f"| {var} | {sub['unit'].iloc[0]} | {v.min():,.1f} | {v.median():,.1f} | {v.max():,.1f} |")

    report = "\n".join(L) + "\n"
    out = config.AUDIT / f"summary-{_ts()}.md"
    out.write_text(report)
    return report


def coverage_report(csv: Path | None = None) -> pd.DataFrame:
    """Per-gage period of record — makes 'different gages, different coverage'
    explicit. Each gage is pulled for its *full* history (auto-clamped to its own
    record), so spans vary widely. Writes ``data/audit/coverage-<ts>.md``."""
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
    L = [f"# Coverage per gage — {_ts()}", "",
         f"{len(g)} gage-series · spanning {_d(span_lo)} → {_d(span_hi)} · "
         f"median record {med:.0f} yr" if pd.notna(med) else f"{len(g)} gage-series", "",
         "| source | gage | first | last | years | rows |", "|---|---|---|---|--:|--:|"]
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


def reconcile(expected_now: dict | None = None, csv: Path | None = None) -> pd.DataFrame:
    """Spot-check our latest discharge value against the agency's published figure.

    ``expected_now`` maps ``(source, site_id) -> discharge_cfs``, where the value is
    the most-recent daily mean flow read off the agency's current-conditions page
    (USGS: waterdata.usgs.gov; DWR: dwr.colorado.gov station page). Returns a frame
    with ``expected_cfs`` (yours), ``got_cfs`` (our latest ``discharge_cfs`` for that
    gage, or null if absent), and ``match`` — True when ``|got - expected|`` is within
    ``max(1, 0.05 * expected)`` (5%, or 1 cfs for tiny flows; daily-mean vs the page's
    possibly-instantaneous reading warrants a looser band than reservoir storage). A
    False is a discrepancy to investigate before publishing. Optional, non-blocking."""
    expected_now = expected_now or {}
    csv = csv or config.CANONICAL_CSV
    df = pd.read_csv(csv, parse_dates=["datetime"])
    out = []
    latest = (df[df["variable"] == "discharge_cfs"]
              .sort_values("datetime").groupby(["source", "site_id"]).tail(1))
    for (src, sid), exp in expected_now.items():
        got = latest[(latest["source"] == src) & (latest["site_id"] == sid)]["value"]
        got_v = float(got.iloc[0]) if len(got) else None
        out.append({"source": src, "site_id": sid, "expected_cfs": exp, "got_cfs": got_v,
                    "match": got_v is not None and abs(got_v - exp) <= max(1.0, 0.05 * exp)})
    res = pd.DataFrame(out, columns=["source", "site_id", "expected_cfs", "got_cfs", "match"])
    (config.AUDIT / "reconcile.json").write_text(res.to_json(orient="records", indent=2))
    return res


def reconcile_cross_source(csv: Path | None = None, sites_csv: Path | None = None,
                           rel_tol: float = 0.05, min_overlap: int = 30) -> pd.DataFrame:
    """Independent accuracy check unique to this pipeline: USGS and DWR re-serve
    many of the SAME physical gages, so the two series should agree on shared dates.

    Joins ``usgs_nwis`` (keyed by USGS site number) to ``dwr_cdss`` (keyed by abbrev,
    cross-linked via ``usgs_site_no`` in ``sites.csv``) on ``(usgs_site_no, date)`` for
    ``discharge_cfs``. For each paired gage with at least ``min_overlap`` shared days,
    reports the count of shared days and the share agreeing within ``rel_tol`` (5%, or
    0.5 cfs floor). A low agreement rate flags an id-mapping or unit error — or a
    genuine provisional-vs-approved revision lag worth a caveat. Writes
    ``data/audit/reconcile-cross-source.json``. Returns the per-gage frame (empty if
    no gage is present in both sources)."""
    csv = csv or config.CANONICAL_CSV
    sites_csv = sites_csv or config.SITES_CSV
    df = pd.read_csv(csv, parse_dates=["datetime"])
    df = df[df["variable"] == "discharge_cfs"].copy()

    seed = pd.read_csv(sites_csv, dtype=str)
    dwr_link = (seed[(seed["source"] == "dwr_cdss") & seed["usgs_site_no"].notna()]
                [["site_id", "usgs_site_no"]]
                .rename(columns={"site_id": "dwr_site_id"}))

    usgs = df[df["source"] == "usgs_nwis"][["site_id", "datetime", "value"]].rename(
        columns={"site_id": "usgs_site_no", "value": "usgs_cfs"})
    dwr = df[df["source"] == "dwr_cdss"][["site_id", "datetime", "value"]].rename(
        columns={"site_id": "dwr_site_id", "value": "dwr_cfs"})
    dwr = dwr.merge(dwr_link, on="dwr_site_id", how="inner")

    paired = usgs.merge(dwr, on=["usgs_site_no", "datetime"], how="inner")
    out = []
    if not paired.empty:
        paired = paired.dropna(subset=["usgs_cfs", "dwr_cfs"])
        denom = paired["usgs_cfs"].abs().clip(lower=0.5)
        paired["within"] = (paired["usgs_cfs"] - paired["dwr_cfs"]).abs() <= (
            rel_tol * denom).clip(lower=0.5)
        for site, sub in paired.groupby("usgs_site_no"):
            if len(sub) < min_overlap:
                continue
            out.append({
                "usgs_site_no": site,
                "shared_days": int(len(sub)),
                "agree_within_tol": int(sub["within"].sum()),
                "agree_rate": round(float(sub["within"].mean()), 4),
                "median_abs_diff_cfs": round(float((sub["usgs_cfs"] - sub["dwr_cfs"]).abs().median()), 3),
                "max_abs_diff_cfs": round(float((sub["usgs_cfs"] - sub["dwr_cfs"]).abs().max()), 3),
            })
    res = pd.DataFrame(out, columns=["usgs_site_no", "shared_days", "agree_within_tol",
                                     "agree_rate", "median_abs_diff_cfs", "max_abs_diff_cfs"])
    (config.AUDIT / "reconcile-cross-source.json").write_text(res.to_json(orient="records", indent=2))
    return res
