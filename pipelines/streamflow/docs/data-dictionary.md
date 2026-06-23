# Data dictionary — `streamflow.csv`

Hand-maintained, one entry per column. The machine-enforced side of this contract is the pandera `CanonicalLong` model in `src/streamflow/schema.py`; the mechanical sanity check is the auto-generated `docs/variables.csv` (from `audit.variables_report`). If the dictionary and `variables.csv` disagree, the parser is usually wrong.

**Grain:** one row per `(source, site_id, datetime, variable)` (tidy long). **Provenance:** join `(source, vintage)` → `data/processed/provenance.csv`.

## `source`
- **Type:** `string`
- **Description:** Which API the observation came from.
- **Vocabulary:** `usgs_nwis` · `dwr_cdss`.
- **Crosswalk:** joins to `provenance.csv` and to `data/lookups/sites.csv`.

## `vintage`
- **Type:** `string`
- **Description:** Extract identifier. `"current"` for these live pulls; the actual retrieval timestamp is in `provenance.csv:retrieved_at`.

## `site_id`
- **Type:** `string`
- **Description:** Source-native gage identifier — the **USGS site number** (e.g. `09095500`) for `usgs_nwis`, the **CDSS abbrev** (e.g. `COLCAMCO`) for `dwr_cdss`.
- **⚠️ Known caveat (read this):** the two sources use **different id namespaces** for the **same physical gage**. DWR re-serves many USGS gages; to join them, use `usgs_site_no` in `data/lookups/sites.csv` (USGS `site_id` == its `usgs_site_no`; the DWR row carries the same `usgs_site_no` as a cross-link). Do **not** treat the USGS row and its DWR mirror as two independent observations.

## `site_name`
- **Type:** `string` (nullable)
- **Description:** Human-readable gage name as reported by the source (e.g. "COLORADO RIVER NEAR CAMEO, CO.").

## `datetime`
- **Type:** `datetime` (UTC, day-resolution)
- **Description:** Observation **date** (daily mean). Floored to midnight so the two sources' timestamps align on the date.
- **Known caveat:** absence of a date means **the gage was not operating / not reporting** that day (or ice/no-record) — it is **not** zero flow. Periods of record differ per gage (see `data/audit/coverage-*.md`).

## `variable`
- **Type:** `string`
- **Description:** What is measured.
- **Vocabulary / units:** `discharge_cfs` (cfs) — the only variable populated in this build. `gage_height_ft` (ft) is declared in the schema for extensibility (adding it is a parser change, not a contract change) but is not yet pulled.

## `value`
- **Type:** `Float64` (nullable)
- **Description:** The measurement (daily mean discharge), in the unit given by `unit`. **NA is preserved** for missing/suppressed/ice-affected days — never silently zero-filled. CDSS's impossible `-999` ice sentinel is mapped to NA.

## `unit`
- **Type:** `string`
- **Description:** Unit of `value`. Derived from `variable`; `cfs` (or `ft` for the declared-but-unpopulated `gage_height_ft`).

## `qa_flag`
- **Type:** `string` (nullable)
- **Description:** Source quality/approval code, preserved not dropped.
  - **USGS:** WaterML qualifiers — `A` approved, `P` provisional, `e` estimated (space-joined, e.g. `A e`).
  - **DWR:** `flagA`..`flagD` space-joined (e.g. `U Ice` for ice-affected).
- **Why it matters:** recent values are provisional and may be revised; a USGS↔DWR disagreement on recent dates is usually a provisional/approved lag.

## `concept`
- **Type:** `string` (nullable)
- **Description:** Cross-source concept key (`streamflow.discharge_cfs`) from `data/lookups/concepts.yaml`. **Concepts carry caveats** — the overlap (DWR re-serves USGS), regulated-not-naturalized flow, and provisional-vs-approved. Read the catalog before comparing or combining series across sources.
