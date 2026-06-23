"""Audit: profile the retrieval, profile the processed data, reconcile vs. truth.

Three layers (Ehrlinger & Wöß): **profile** (describe what's there), **measure**
(metrics against the schema/dimensions), **monitor** (diff the reports over time).

- ``profile_raw``      — for nb-02: did the fetch return data? counts/shapes per
  source, straight off ``data/original/``. Catches an empty/failed retrieval
  *before* cleaning.
- ``audit_processed``  — full profile of the tidy CSV: rows per source, null
  rates, distinct values, date coverage, per-variable value ranges → Markdown.
- ``variables_report`` — the mechanical column profile (``docs/variables.csv``),
  the data dictionary's sanity check.
- ``reconcile``        — accuracy check against each source's own published
  top-line (e.g. current reservoir storage shown on the agency page). Scaffolded;
  fill the expected totals as they are confirmed (see ``docs/survey-notes.md``).
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd

from reservoir import config

from co_pipeline_core import audit as _coreaudit


def _ts() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def profile_raw(original_dir: Path | None = None) -> str:
    """Summarize what's on disk in ``data/original/`` -> Markdown (shared)."""
    return _coreaudit.profile_raw(original_dir or config.ORIGINAL, config.AUDIT)


def audit_processed(csv: Path | None = None) -> str:
    """Profile the tidy CSV -> ``data/audit/summary-<ts>.md`` (shared)."""
    return _coreaudit.audit_processed(csv or config.CANONICAL_CSV, config.AUDIT, id_col="reservoir_id", entity="reservoirs")


def coverage_report(csv: Path | None = None) -> pd.DataFrame:
    """Per-reservoir period of record — makes 'different sites, different coverage'
    explicit. Each site is pulled for its *full* history (auto-clamped to its own
    record), so spans vary widely. Writes ``data/audit/coverage-<ts>.md``."""
    csv = csv or config.CANONICAL_CSV
    df = pd.read_csv(csv)
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    g = (df.groupby(["source", "reservoir_id", "reservoir_name"], dropna=False)
           .agg(first=("datetime", "min"), last=("datetime", "max"),
                rows=("value", "size")).reset_index())
    g["years"] = ((g["last"] - g["first"]).dt.days / 365.25).round(1)
    g = g.sort_values("first").reset_index(drop=True)

    def _d(x):  # NaT-safe date format
        return f"{x:%Y-%m-%d}" if pd.notna(x) else "—"

    span_lo, span_hi = g["first"].min(), g["last"].max()
    med = g["years"].median()
    L = [f"# Coverage per reservoir — {_ts()}", "",
         f"{len(g)} reservoirs · spanning {_d(span_lo)} → {_d(span_hi)} · "
         f"median record {med:.0f} yr" if pd.notna(med) else f"{len(g)} reservoirs", "",
         "| source | reservoir | first | last | years | rows |", "|---|---|---|---|--:|--:|"]
    for _, r in g.iterrows():
        L.append(f"| {r['source']} | {r['reservoir_name'] or r['reservoir_id']} | "
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


def reconcile(expected_totals: dict | None = None, csv: Path | None = None) -> pd.DataFrame:
    """Spot-check our latest storage value against the agency's own published figure.

    ``expected_totals`` maps ``(source, reservoir_id) -> storage_af``, where the value
    is the current storage (acre-feet) read off the agency's current-conditions page
    (DWR: dwr.colorado.gov station search; RISE: data.usbr.gov/rise). Returns a frame
    with ``expected_af`` (yours), ``got_af`` (our latest ``storage_af`` for that
    reservoir, or null if absent), and ``match`` — True when ``|got - expected|`` is
    within ``max(1, 0.01 * expected)`` (1%, or 1 AF for tiny reservoirs). A False is a
    discrepancy to investigate before publishing (units / wrong id / stale / not
    fetched). Optional and non-blocking; see ``docs/survey-notes.md`` (Reconciliation).
    """
    expected_totals = expected_totals or {}
    csv = csv or config.CANONICAL_CSV
    df = pd.read_csv(csv, parse_dates=["datetime"])
    out = []
    latest = (df[df["variable"] == "storage_af"]
              .sort_values("datetime").groupby(["source", "reservoir_id"]).tail(1))
    for (src, rid), exp in expected_totals.items():
        got = latest[(latest["source"] == src) & (latest["reservoir_id"] == rid)]["value"]
        got_v = float(got.iloc[0]) if len(got) else None
        out.append({"source": src, "reservoir_id": rid, "expected_af": exp,
                    "got_af": got_v,
                    "match": got_v is not None and abs(got_v - exp) <= max(1.0, 0.01 * exp)})
    res = pd.DataFrame(out, columns=["source", "reservoir_id", "expected_af", "got_af", "match"])
    (config.AUDIT / "reconcile.json").write_text(res.to_json(orient="records", indent=2))
    return res
