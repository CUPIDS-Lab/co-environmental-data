"""Shared tidy-long normalization.

The per-pipeline ``schema.py`` keeps its own ``LONG_COLUMNS`` / ``VARIABLES`` /
``SOURCE_SLUGS`` and its pandera contract (the vocabulary and, for climate, the
per-measure units, are genuinely per-pipeline). The duplicated *machinery* —
coercing a parser's frame to the canonical columns, filling the unit from the
variable, day-flooring timestamps, and collapsing duplicate keys to the latest
reading before validation — lives here.

Two day-flooring modes (the only real divergence):

- ``utc_floor`` — convert to UTC, drop tz, floor to midnight. Used where source
  timestamps are UTC-ish (reservoir, streamflow, snowpack).
- ``local_date`` — keep the reported LOCAL calendar date (the first 10 chars),
  ordering by the full UTC timestamp so a same-day revision still wins. Used by
  climate-stations (CDSS ``measDate`` is local-midnight with a tz offset; UTC
  conversion would roll an evening reading into the next day).
"""
from __future__ import annotations

from typing import Callable

import pandas as pd


def normalize_long(df: pd.DataFrame, *, long_columns: list[str], variables: dict,
                   validate: Callable[[pd.DataFrame], pd.DataFrame],
                   id_col: str = "site_id", name_col: str = "site_name",
                   datetime_mode: str = "utc_floor") -> pd.DataFrame:
    """Coerce ``df`` to the canonical schema, dedupe to day-grain, then ``validate``.

    Parsers may carry intermediate columns; this drops them, reorders to
    ``long_columns``, fills the unit from ``variables`` when absent, and collapses
    any duplicate ``(source, <id_col>, datetime, variable)`` to the latest reading.
    """
    optional = (name_col, "qa_flag", "concept")
    missing = [c for c in long_columns if c not in df.columns and c not in ("unit", *optional)]
    if missing:
        raise ValueError(f"normalize_long: missing required columns: {missing}")
    out = df.copy()
    if "unit" not in out.columns:
        out["unit"] = out["variable"].map(variables)
    for col in optional:
        if col not in out.columns:
            out[col] = pd.NA
    out = out[long_columns].copy()

    if datetime_mode == "local_date":
        _ord = pd.to_datetime(out["datetime"], utc=True)                      # ordering key
        out["datetime"] = pd.to_datetime(out["datetime"].astype(str).str[:10], errors="coerce")
    elif datetime_mode == "utc_floor":
        _ord = pd.to_datetime(out["datetime"], utc=True).dt.tz_localize(None)
        out["datetime"] = _ord.dt.normalize()
    else:  # pragma: no cover
        raise ValueError(f"unknown datetime_mode: {datetime_mode!r}")

    key = ["source", id_col, "datetime", "variable"]
    out = (out.assign(_ord=_ord)
              .sort_values("_ord")
              .drop_duplicates(key, keep="last")
              .drop(columns="_ord")
              .reset_index(drop=True))
    return validate(out)
