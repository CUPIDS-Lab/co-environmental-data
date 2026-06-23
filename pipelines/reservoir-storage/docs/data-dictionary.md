# Data dictionary — `reservoir-storage.csv`

Hand-maintained, one entry per column. The machine-enforced side of this
contract is the pandera `CanonicalLong` model in `src/reservoir/schema.py`; the
mechanical sanity check is the auto-generated `docs/variables.csv` (from
`audit.variables_report`). If the dictionary and `variables.csv` disagree, the
parser is usually wrong.

**Grain:** one row per `(source, reservoir_id, datetime, variable)` (tidy long).
**Provenance:** join `(source, vintage)` → `data/processed/provenance.csv`.

## `source`
- **Type:** `string`
- **Description:** Which API the observation came from.
- **Vocabulary:** `dwr_cdss` · `reclamation_rise` · `northern_water`.
- **Crosswalk:** joins to `provenance.csv` and to `data/lookups/reservoirs.csv`.

## `vintage`
- **Type:** `string`
- **Description:** Extract identifier. `"current"` for these live pulls; the
  actual retrieval timestamp is in `provenance.csv:retrieved_at`.

## `reservoir_id`
- **Type:** `string`
- **Description:** Source-native station/site identifier (CDSS `abbrev`, RISE
  reservoir slug, ArcGIS `STATION_ID`).
- **Known caveats:** Not harmonized across sources — the same physical reservoir
  may carry different ids per source. A cross-source id crosswalk is future work
  (`reservoirs.csv` is the seed).

## `reservoir_name`
- **Type:** `string` (nullable)
- **Description:** Human-readable reservoir name as reported by the source.

## `datetime`
- **Type:** `datetime` (UTC, day-resolution)
- **Description:** Observation date. Sources report at different sub-daily times;
  align on the **date**, not the timestamp.
- **Known caveat:** Some days carry **multiple readings** in the source — a sub-daily
  timestamp or a later same-day revision (e.g. RISE ruedi 2026-03-06 at 06:00Z and
  07:00Z; DWR same-day `AF`/`ACFT` revisions). The pipeline floors to the date and
  keeps the **latest reading** per `(reservoir, date, variable)`, so there is exactly
  one row per day. Revised/superseded same-day values are dropped (the differences are
  typically negligible).

## `variable`
- **Type:** `string`
- **Description:** What is measured.
- **Vocabulary / units:** `storage_af` (acre-ft) · `pct_capacity` (percent) ·
  `elevation_ft` (ft) · `release_cfs` (cfs) · `inflow_cfs` (cfs).

## `value`
- **Type:** `Float64` (nullable)
- **Description:** The measurement, in the unit given by `unit`. NA preserved
  (suppressed/absent readings) — never silently zero-filled.

## `unit`
- **Type:** `string`
- **Description:** Unit of `value`. Derived from `variable`; one of
  `acre-ft` · `percent` · `ft` · `cfs`.

## `qa_flag`
- **Type:** `string` (nullable)
- **Description:** Source quality/approval code (CDSS `flagA`/`flagB`, RISE flag).
  Provisional vs. approved is preserved, not dropped.

## `concept`
- **Type:** `string` (nullable)
- **Description:** Cross-source concept key (`reservoir.storage_af`, …) from
  `data/lookups/concepts.yaml`. **Concepts carry caveats** — especially the
  vertical-datum caveat on elevation; read the catalog before comparing across
  sources.

## Known issues (2026-06-22 QA audit)

Defects found auditing the built CSV against `data-bulletproofing-checklist.md` and `data-quality-checklist.md`. Documented here so downstream users are not surprised; tracked in the repo `ROADMAP.md`. **Do not treat the current `data/processed` output as publication-ready until the blocking items clear.**

- **Reconciliation not run (blocking — [#38](https://github.com/CUPIDS-Lab/co-environmental-data/issues/38)).** No passing reconciliation exists; `data/audit/reconcile.json` holds placeholder values. The values have not been independently confirmed against the agencies' current-storage pages.
- **Impossible values present (blocking — [#40](https://github.com/CUPIDS-Lab/co-environmental-data/issues/40)).** The output contains an elevation of ~70,235 ft (Dillon, 1 row), ~2,903 negative elevations, and ~134 negative `release_cfs`. No range gate screens these yet.
- **RISE zeros read as missing (blocking — [#39](https://github.com/CUPIDS-Lab/co-environmental-data/issues/39)).** The RISE parser coerces a real `0.0` storage (dead pool) to NA, corrupting the boundary between ~5,217 storage zeros and ~7,451 NAs.
- **`qa_flag` corruption ([#41](https://github.com/CUPIDS-Lab/co-environmental-data/issues/41)).** The DWR flag join emits the literal string `"None None"` in ~268k rows (`"O None"` in ~134k) instead of empty/NA.
- **Record-count shortfall ([#41](https://github.com/CUPIDS-Lab/co-environmental-data/issues/41)).** The CSV covers ~53 reservoirs vs. the 138 enumerated (the rest returned 404/no-data); the shortfall is not yet documented, so a silent drop is indistinguishable from real no-data.
- **Cross-source name casing ([#41](https://github.com/CUPIDS-Lab/co-environmental-data/issues/41)).** The same reservoir appears as `Blue Mesa Reservoir` (RISE) and `BLUE MESA RESERVOIR` (DWR); no crosswalk yet.
- **Documented & accepted (not defects):** real historical gaps per site; multi-reading-per-day flooring (tested); vertical-datum and capacity-baseline caveats (`concepts.yaml`).
