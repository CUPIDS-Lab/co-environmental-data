"""Shared audit profiling — the two functions every pipeline runs identically:

- ``profile_raw``    — describe what the fetch left in ``data/original/`` (did it
  return data?), straight off disk.
- ``audit_processed`` — profile the tidy CSV: rows per source × variable, distinct
  entities, date coverage, per-variable value ranges → Markdown.

Per-pipeline ``audit.py`` keeps its domain reports (coverage, reconciliation,
basin %-of-normal, …) and delegates these two here. ``audit_processed`` is
parameterized by the composite-key id column and the entity noun (stations / gages
/ reservoirs); a pipeline whose layout genuinely differs (climate-stations groups
by variable + unit) keeps its own.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd


def _ts() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def profile_raw(original_dir: Path, audit_dir: Path) -> str:
    """Summarize what's on disk in ``data/original/`` → Markdown (also written)."""
    original_dir, audit_dir = Path(original_dir), Path(audit_dir)
    lines = [f"# Raw retrieval profile — {_ts()}", ""]
    files = sorted(p for p in original_dir.rglob("*.json") if p.name != "manifest.json")
    by_source: dict[str, list[Path]] = {}
    for f in files:
        by_source.setdefault(f.relative_to(original_dir).parts[0], []).append(f)
    lines.append(f"- Sources with data: **{len(by_source)}** · files: **{len(files)}**\n")
    lines.append("| Source | Files | Total bytes | Sample top-level shape |")
    lines.append("|---|--:|--:|---|")
    for source, fs in sorted(by_source.items()):
        nbytes = sum(p.stat().st_size for p in fs)
        try:
            sample = json.loads(fs[0].read_text())
            if isinstance(sample, list):
                shape = f"list[{len(sample)}]"
            elif isinstance(sample, dict):
                shape = ", ".join(list(sample)[:5])
            else:
                shape = type(sample).__name__
        except Exception as e:  # noqa: BLE001
            shape = f"(unreadable: {e})"
        lines.append(f"| `{source}` | {len(fs)} | {nbytes:,} | {shape} |")
    if not by_source:
        lines.append("\n> ⚠️ No raw files found — run the retrieve step first, or the fetch failed.")
    report = "\n".join(lines) + "\n"
    out = audit_dir / f"raw-profile-{_ts()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    return report


def audit_processed(csv: Path, audit_dir: Path, *, id_col: str = "site_id",
                    entity: str = "stations") -> str:
    """Profile the tidy CSV → ``data/audit/summary-<ts>.md`` (returns the text)."""
    csv, audit_dir = Path(csv), Path(audit_dir)
    df = pd.read_csv(csv, parse_dates=["datetime"])
    L = [f"# Processed audit — {_ts()}", "", f"Rows: **{len(df):,}**", ""]

    L += ["## Rows per source × variable", "",
          f"| source | variable | rows | {entity} | null values |", "|---|---|--:|--:|--:|"]
    for (src, var), sub in df.groupby(["source", "variable"]):
        L.append(f"| {src} | {var} | {len(sub):,} | {sub[id_col].nunique()} | "
                 f"{sub['value'].isna().sum()} |")

    L += ["", "## Date coverage per source", "", "| source | earliest | latest |", "|---|---|---|"]
    for src, sub in df.groupby("source"):
        L.append(f"| {src} | {sub['datetime'].min():%Y-%m-%d} | {sub['datetime'].max():%Y-%m-%d} |")

    L += ["", "## Value ranges per variable (sanity / outliers)", "",
          "| variable | unit | min | median | max |", "|---|---|--:|--:|--:|"]
    for var, sub in df.groupby("variable"):
        v = sub["value"].dropna()
        if len(v):
            L.append(f"| {var} | {sub['unit'].iloc[0]} | {v.min():,.1f} | "
                     f"{v.median():,.1f} | {v.max():,.1f} |")

    report = "\n".join(L) + "\n"
    out = audit_dir / f"summary-{_ts()}.md"
    out.write_text(report)
    return report
