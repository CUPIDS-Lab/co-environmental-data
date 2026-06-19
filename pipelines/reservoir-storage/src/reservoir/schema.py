"""Canonical tidy-long schema for Colorado reservoir storage.

One row per observation: ``(source, reservoir_id, datetime, variable)`` is the
composite key. Wide views (a reservoir × date matrix) are recovered with the
recipes in ``docs/filter-pivot-recipes.md`` — long is the *storage* shape, wide
is the *analysis* shape.

``LONG_COLUMNS`` + ``CanonicalLong`` together are the **contract** the processed
CSV obeys; ``docs/data-dictionary.md`` is the human-readable side of the same
contract. A parser that emits something the schema rejects is a *contract
violation* (fix the parser); changing ``LONG_COLUMNS`` is a *contract change*
(a migration — record it in the changelog).
"""
from __future__ import annotations

import pandas as pd

try:  # pandera is an install-time dep; keep import survivable for `py_compile`
    import pandera.pandas as pa
    from pandera.typing.pandas import Series
    _HAVE_PANDERA = True
except Exception:  # pragma: no cover - exercised only without the extra installed
    _HAVE_PANDERA = False


# The canonical column list. Every parser returns exactly these columns.
LONG_COLUMNS = [
    "source",          # registry slug: dwr_cdss | reclamation_rise | northern_water
    "vintage",         # extract identifier (retrieval snapshot, e.g. "2026-06-18")
    "reservoir_id",    # source-native station/site id
    "reservoir_name",  # human-readable reservoir name
    "datetime",        # observation timestamp (UTC, day-resolution)
    "variable",        # storage_af | pct_capacity | elevation_ft | release_cfs | inflow_cfs
    "value",           # the measurement
    "unit",            # acre-ft | percent | ft | cfs
    "qa_flag",         # source quality/approval code (provisional/approved/estimated/…)
    "concept",         # cross-source concept key (see data/lookups/concepts.yaml), nullable
]

# Controlled vocabulary for `variable`.
VARIABLES = {
    "storage_af": "acre-ft",
    "pct_capacity": "percent",
    "elevation_ft": "ft",
    "release_cfs": "cfs",
    "inflow_cfs": "cfs",
}

SOURCE_SLUGS = ("dwr_cdss", "reclamation_rise", "northern_water")


if _HAVE_PANDERA:

    class CanonicalLong(pa.DataFrameModel):
        """Pandera contract validated at the boundary of every parser."""

        source: Series[str] = pa.Field(isin=list(SOURCE_SLUGS))
        vintage: Series[str]
        reservoir_id: Series[str]
        reservoir_name: Series[str] = pa.Field(nullable=True)
        datetime: Series[pd.Timestamp] = pa.Field()
        variable: Series[str] = pa.Field(isin=list(VARIABLES))
        value: Series[float] = pa.Field(nullable=True)
        unit: Series[str] = pa.Field(isin=sorted(set(VARIABLES.values())))
        qa_flag: Series[str] = pa.Field(nullable=True)
        concept: Series[str] = pa.Field(nullable=True)

        class Config:
            strict = True
            coerce = True
            # Composite uniqueness — one value per reservoir/date/variable/source.
            unique = ["source", "reservoir_id", "datetime", "variable"]

    def validate(df: pd.DataFrame) -> pd.DataFrame:
        return CanonicalLong.validate(df)

else:  # pragma: no cover

    def validate(df: pd.DataFrame) -> pd.DataFrame:
        raise RuntimeError("pandera not installed; run `uv sync` (or `pip install -e .`)")


def normalize_long(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a parser's output to the canonical schema, then validate.

    Parsers may carry intermediate columns; this drops them, reorders to
    ``LONG_COLUMNS``, fills the unit from the variable when absent, and validates.
    """
    missing = [c for c in LONG_COLUMNS if c not in df.columns and c not in ("unit", "concept", "qa_flag", "reservoir_name")]
    if missing:
        raise ValueError(f"normalize_long: missing required columns: {missing}")
    out = df.copy()
    if "unit" not in out.columns:
        out["unit"] = out["variable"].map(VARIABLES)
    for optional in ("reservoir_name", "qa_flag", "concept"):
        if optional not in out.columns:
            out[optional] = pd.NA
    out = out[LONG_COLUMNS].copy()
    # Day resolution is the grain. Floor to midnight so heterogeneous source
    # timestamps (DWR midnight vs RISE 07:00Z) serialize uniformly; the UTC date is
    # preserved (e.g. 1966-01-31T07:00Z -> 1966-01-31). Some days carry MULTIPLE
    # readings — sub-daily timestamps or a later same-day revision (e.g. RISE ruedi
    # 2026-03-06 at 06:00Z and 07:00Z; DWR same-day AF/ACFT revisions). Collapse
    # those to the latest reading per (reservoir, day, variable) so the day key is
    # unique; otherwise a few dupe dates would fail validation and drop the whole
    # reservoir.
    _ts = pd.to_datetime(out["datetime"], utc=True).dt.tz_localize(None)
    out["datetime"] = _ts.dt.normalize()
    out = (out.assign(_ts=_ts)
              .sort_values("_ts")
              .drop_duplicates(["source", "reservoir_id", "datetime", "variable"], keep="last")
              .drop(columns="_ts")
              .reset_index(drop=True))
    return validate(out)
