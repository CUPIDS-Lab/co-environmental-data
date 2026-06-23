"""Canonical tidy-long schema for Colorado stream/river flow.

One row per observation: ``(source, site_id, datetime, variable)`` is the
composite key. Wide views (a site × date matrix) are recovered with the recipes
in ``docs/filter-pivot-recipes.md`` — long is the *storage* shape, wide is the
*analysis* shape.

``LONG_COLUMNS`` + ``CanonicalLong`` together are the **contract** the processed
CSV obeys; ``docs/data-dictionary.md`` is the human-readable side of the same
contract. A parser that emits something the schema rejects is a *contract
violation* (fix the parser); changing ``LONG_COLUMNS`` is a *contract change*
(a migration — record it in the changelog).

Mirrors the sibling ``reservoir-storage`` schema (#9): the only domain changes
are ``reservoir_*`` → ``site_*`` and the controlled ``variable`` vocabulary
(``discharge_cfs`` here vs ``storage_af`` there).
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
    "source",          # registry slug: usgs_nwis | dwr_cdss
    "vintage",         # extract identifier (retrieval snapshot, e.g. "current")
    "site_id",         # source-native gage/station id (USGS site no. | DWR abbrev)
    "site_name",       # human-readable gage/station name
    "datetime",        # observation date (UTC, day-resolution)
    "variable",        # discharge_cfs | gage_height_ft
    "value",           # the measurement
    "unit",            # cfs | ft
    "qa_flag",         # source quality/approval code (approved/provisional/estimated/…)
    "concept",         # cross-source concept key (see data/lookups/concepts.yaml), nullable
]

# Controlled vocabulary for `variable`. discharge_cfs is the primary (and, in this
# build, only populated) variable; gage_height_ft is declared so adding it later is
# a parser change, not a *contract* change (cf. reservoir's unused pct_capacity).
VARIABLES = {
    "discharge_cfs": "cfs",
    "gage_height_ft": "ft",
}

SOURCE_SLUGS = ("usgs_nwis", "dwr_cdss")


if _HAVE_PANDERA:

    class CanonicalLong(pa.DataFrameModel):
        """Pandera contract validated at the boundary of every parser."""

        source: Series[str] = pa.Field(isin=list(SOURCE_SLUGS))
        vintage: Series[str]
        site_id: Series[str]
        site_name: Series[str] = pa.Field(nullable=True)
        datetime: Series[pd.Timestamp] = pa.Field()
        variable: Series[str] = pa.Field(isin=list(VARIABLES))
        value: Series[float] = pa.Field(nullable=True)
        unit: Series[str] = pa.Field(isin=sorted(set(VARIABLES.values())))
        qa_flag: Series[str] = pa.Field(nullable=True)
        concept: Series[str] = pa.Field(nullable=True)

        class Config:
            strict = True
            coerce = True
            # Composite uniqueness — one value per site/date/variable/source.
            unique = ["source", "site_id", "datetime", "variable"]

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
    missing = [c for c in LONG_COLUMNS
               if c not in df.columns and c not in ("unit", "concept", "qa_flag", "site_name")]
    if missing:
        raise ValueError(f"normalize_long: missing required columns: {missing}")
    out = df.copy()
    if "unit" not in out.columns:
        out["unit"] = out["variable"].map(VARIABLES)
    for optional in ("site_name", "qa_flag", "concept"):
        if optional not in out.columns:
            out[optional] = pd.NA
    out = out[LONG_COLUMNS].copy()
    # Day resolution is the grain. Floor to midnight so heterogeneous source
    # timestamps serialize uniformly; the UTC date is preserved. A gage can carry
    # MORE THAN ONE reading for a day — most importantly when the SAME physical gage
    # is pulled from both sources (DWR re-serves USGS), or on a same-day revision.
    # Collapse to the latest reading per (source, site, day, variable) so the day key
    # is unique within a source; cross-source rows stay distinct (source is in the key).
    _ts = pd.to_datetime(out["datetime"], utc=True).dt.tz_localize(None)
    out["datetime"] = _ts.dt.normalize()
    out = (out.assign(_ts=_ts)
              .sort_values("_ts")
              .drop_duplicates(["source", "site_id", "datetime", "variable"], keep="last")
              .drop(columns="_ts")
              .reset_index(drop=True))
    return validate(out)
