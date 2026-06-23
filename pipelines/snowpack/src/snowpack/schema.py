"""Canonical tidy-long schema for Colorado snowpack (SWE).

One row per observation: ``(source, site_id, datetime, variable)`` is the
composite key. Wide views (a site × date matrix) are recovered with the recipes
in ``docs/filter-pivot-recipes.md`` — long is the *storage* shape, wide is the
*analysis* shape.

``LONG_COLUMNS`` + ``CanonicalLong`` together are the **contract** the processed
CSV obeys; ``docs/data-dictionary.md`` is the human-readable side of the same
contract. A parser that emits something the schema rejects is a *contract
violation* (fix the parser); changing ``LONG_COLUMNS`` is a *contract change*
(a migration — record it in the changelog).

Stamped out from the sibling ``streamflow`` schema (#10): the only domain changes
are ``site_*`` keeping its name (still a point station) and the controlled
``variable`` vocabulary (``swe_in`` / ``snow_depth_in`` / ``precip_accum_in``
here vs ``discharge_cfs`` there).
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
    "source",          # registry slug: nrcs_snotel | nrcs_snowcourse
    "vintage",         # extract identifier (retrieval snapshot, e.g. "current")
    "site_id",         # source-native station id — the AWDB station triplet (e.g. 713:CO:SNTL)
    "site_name",       # human-readable station name
    "datetime",        # observation date (UTC, day-resolution)
    "variable",        # swe_in | snow_depth_in | precip_accum_in
    "value",           # the measurement
    "unit",            # in | pct | degF
    "qa_flag",         # source quality/approval code (qcFlag+qaFlag, space-joined)
    "concept",         # cross-source concept key (see data/lookups/concepts.yaml), nullable
]

# Controlled vocabulary for `variable`. The three water-relevant concepts named in
# issue #11 are populated; snow_density_pct (snow courses) and air_temp_obs_f are
# declared so adding them later is a parser change, not a *contract* change (cf.
# streamflow's unused gage_height_ft).
VARIABLES = {
    "swe_in": "in",             # WTEQ — snow water equivalent
    "snow_depth_in": "in",      # SNWD — snow depth
    "precip_accum_in": "in",    # PREC — precipitation accumulation (water-year cumulative)
    "snow_density_pct": "pct",  # SNDN — snow density (declared; snow courses serve it)
    "air_temp_obs_f": "degF",   # TOBS — observed air temp (declared; see temp-sensor-bias caveat)
}

SOURCE_SLUGS = ("nrcs_snotel", "nrcs_snowcourse")


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
    # timestamps (SNOTEL daily `date`, snow-course `collectionDate`) serialize
    # uniformly; the UTC date is preserved. A station can carry more than one
    # reading for a day (a same-day revision, or — across sources — a SNOTEL and a
    # co-located snow course on the same measurement date). Collapse to the latest
    # reading per (source, site, day, variable) so the day key is unique within a
    # source; cross-source rows stay distinct (source is in the key).
    _ts = pd.to_datetime(out["datetime"], utc=True).dt.tz_localize(None)
    out["datetime"] = _ts.dt.normalize()
    out = (out.assign(_ts=_ts)
              .sort_values("_ts")
              .drop_duplicates(["source", "site_id", "datetime", "variable"], keep="last")
              .drop(columns="_ts")
              .reset_index(drop=True))
    return validate(out)
