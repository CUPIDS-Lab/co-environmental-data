"""Canonical tidy-long schema for Colorado daily climate-station observations.

One row per observation: ``(source, site_id, datetime, variable)`` is the
composite key. Wide views (a station × date matrix, or a station-day with all
variables side by side) are recovered with the recipes in
``docs/filter-pivot-recipes.md`` — long is the *storage* shape, wide is the
*analysis* shape.

``LONG_COLUMNS`` + ``CanonicalLong`` together are the **contract** the processed
CSV obeys; ``docs/data-dictionary.md`` is the human-readable side of the same
contract. A parser that emits something the schema rejects is a *contract
violation* (fix the parser); changing ``LONG_COLUMNS`` is a *contract change* (a
migration — record it in the changelog).

Mirrors the sibling ``streamflow`` schema (#10). The domain changes:

- ``site_id`` is the CDSS ``stationNum`` (a stable integer id), not a gage abbrev.
  A station's **network** (``dataSource``: NOAA / CoCoRaHS / NRCS / CoAgMet /
  NCWCD) and its network-native id (GHCN ``siteId``) are *station* attributes —
  they live in the ``data/lookups/stations.csv`` dimension table, joined on
  ``site_id``, not repeated on every observation row (proper tidy normalization).
- the controlled ``variable`` vocabulary is **twelve** climate measures, each with
  its own unit, rather than a single ``discharge_cfs``. Because units differ by
  measure, harmonization is **per concept**, not one global unit. ``MEAS_MAP`` is
  the authoritative CDSS ``measType`` → ``(variable, concept, unit)`` table; all
  units were confirmed against the live API (see ``docs/survey-notes.md``).
"""
from __future__ import annotations

import pandas as pd

from co_pipeline_core import schema as _coreschema

try:  # pandera is an install-time dep; keep import survivable for `py_compile`
    import pandera.pandas as pa
    from pandera.typing.pandas import Series
    _HAVE_PANDERA = True
except Exception:  # pragma: no cover - exercised only without the extra installed
    _HAVE_PANDERA = False


# The canonical column list. The parser returns exactly these columns.
LONG_COLUMNS = [
    "source",          # registry slug: cdss_climate
    "vintage",         # extract identifier (retrieval snapshot, e.g. "current")
    "site_id",         # CDSS stationNum (stable integer id, as string)
    "site_name",       # human-readable station name
    "datetime",        # observation date (UTC, day-resolution)
    "variable",        # one of VARIABLES (12 climate measures)
    "value",           # the measurement
    "unit",            # per-variable unit (degF | in | mJ/m^2 | kPa | KM), nullable
    "qa_flag",         # CDSS quality flags flagA..flagD, space-joined; nullable
    "concept",         # cross-source concept key (see data/lookups/concepts.yaml)
]

# Authoritative CDSS ``measType`` → (canonical variable, concept, unit).
# Units ✅ confirmed live 2026-06-22 (docs/survey-notes.md). FrostDate is a rare
# measure whose daily-series unit was not observed in the sampled stations; it is
# carried defensively with a null canonical unit (the parser still passes its value
# and flags through). Temperatures are degF and **may be negative** — only the
# non-negative-domain measures get sentinel/negative cleaning (see NON_NEGATIVE_VARS).
MEAS_MAP: dict[str, tuple[str, str, str | None]] = {
    "MaxTemp":   ("temp_max_f",          "climate.temp_max_f",          "degF"),
    "MeanTemp":  ("temp_mean_f",         "climate.temp_mean_f",         "degF"),
    "MinTemp":   ("temp_min_f",          "climate.temp_min_f",          "degF"),
    "Precip":    ("precip_in",           "climate.precip_in",           "in"),
    "Snow":      ("snowfall_in",         "climate.snowfall_in",         "in"),
    "SnowDepth": ("snow_depth_in",       "climate.snow_depth_in",       "in"),
    "SnowSWE":   ("swe_in",              "climate.swe_in",              "in"),
    "Evap":      ("evap_in",             "climate.evap_in",             "in"),
    "Solar":     ("solar_rad_mj_m2",     "climate.solar_rad_mj_m2",     "mJ/m^2"),
    "VP":        ("vapor_pressure_kpa",  "climate.vapor_pressure_kpa",  "kPa"),
    "Wind":      ("wind_run_km",         "climate.wind_run_km",         "KM"),
    "FrostDate": ("frost_date",          "climate.frost_date",          None),
}

# Controlled vocabulary for `variable` → its canonical unit (None = source-reported).
VARIABLES: dict[str, str | None] = {var: unit for var, _concept, unit in MEAS_MAP.values()}
CONCEPTS: dict[str, str] = {var: concept for var, concept, _unit in MEAS_MAP.values()}
# Allowed non-null units (the isin set; None/NA is also permitted for frost_date).
UNITS = sorted({u for u in VARIABLES.values() if u})

# Measures whose physical domain excludes negatives — an impossible negative is a
# missing/sentinel value to clean to NA. Temperatures are EXCLUDED (sub-zero degF is
# real); frost_date is excluded (semantics unconfirmed — don't second-guess it).
NON_NEGATIVE_VARS = {
    "precip_in", "snowfall_in", "snow_depth_in", "swe_in", "evap_in",
    "solar_rad_mj_m2", "vapor_pressure_kpa", "wind_run_km",
}

SOURCE_SLUGS = ("cdss_climate",)


if _HAVE_PANDERA:

    class CanonicalLong(pa.DataFrameModel):
        """Pandera contract validated at the boundary of the parser."""

        source: Series[str] = pa.Field(isin=list(SOURCE_SLUGS))
        vintage: Series[str]
        site_id: Series[str]
        site_name: Series[str] = pa.Field(nullable=True)
        datetime: Series[pd.Timestamp] = pa.Field()
        variable: Series[str] = pa.Field(isin=list(VARIABLES))
        value: Series[float] = pa.Field(nullable=True)
        unit: Series[str] = pa.Field(isin=UNITS, nullable=True)  # None for frost_date
        qa_flag: Series[str] = pa.Field(nullable=True)
        concept: Series[str] = pa.Field(nullable=True)

        class Config:
            strict = True
            coerce = True
            # Composite uniqueness — one value per station/date/variable/source.
            unique = ["source", "site_id", "datetime", "variable"]

    def validate(df: pd.DataFrame) -> pd.DataFrame:
        return CanonicalLong.validate(df)

else:  # pragma: no cover

    def validate(df: pd.DataFrame) -> pd.DataFrame:
        raise RuntimeError("pandera not installed; run `uv sync` (or `pip install -e .`)")


def normalize_long(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a parser's output to the canonical schema, then validate (shared
    machinery in ``co_pipeline_core.schema``)."""
    return _coreschema.normalize_long(
        df, long_columns=LONG_COLUMNS, variables=VARIABLES, validate=validate,
        id_col="site_id", name_col="site_name", datetime_mode="local_date")
