# Data dictionary — `snowpack.csv`

Hand-maintained, one entry per column. The machine-enforced side of this contract is the pandera `CanonicalLong` model in `src/snowpack/schema.py`; the mechanical sanity check is the auto-generated `docs/variables.csv` (from `audit.variables_report`). If the dictionary and `variables.csv` disagree, the parser is usually wrong.

**Grain:** one row per `(source, site_id, datetime, variable)` (tidy long). **Provenance:** join `(source, vintage)` → `data/processed/provenance.csv`.

## `source`
- **Type:** `string`
- **Description:** Which NRCS network the observation came from.
- **Vocabulary:** `nrcs_snotel` (automated SNOTEL, network `SNTL`) · `nrcs_snowcourse` (manual snow course, network `SNOW`).
- **Crosswalk:** joins to `provenance.csv` and to `data/lookups/sites.csv`.

## `vintage`
- **Type:** `string`
- **Description:** Extract identifier. `"current"` for these live pulls; the actual retrieval timestamp is in `provenance.csv:retrieved_at`.

## `site_id`
- **Type:** `string`
- **Description:** Source-native station identifier — the **AWDB station triplet** `<id>:CO:<network>` (e.g. `680:CO:SNTL`, `06L02:CO:SNOW`). This is the key the AWDB `data` endpoint takes.
- **⚠️ Known caveat:** a SNOTEL and a same-named snow course are **nearby but distinct sites**, not one site in two namespaces. Use `audit.colocated_pairs` (same name or <2 km) to pair them; do **not** treat the pair as two independent reads of one point. `station_id` (the bare id) and lat/lon/basin live in `data/lookups/sites.csv`.

## `site_name`
- **Type:** `string` (nullable)
- **Description:** Human-readable station name as reported by AWDB (e.g. "Park Cone").

## `datetime`
- **Type:** `datetime` (UTC, day-resolution)
- **Description:** Observation **date**. For SNOTEL this is the daily `date`; for snow courses it is the manual-survey `collectionDate`, floored to the day.
- **Known caveat:** absence of a date means **the site was not reporting** that day (or the sensor/course predates/postdates the gap) — it is **not** zero snow. Periods of record differ per station (SNOTEL ~1980+, snow courses to the 1930s–40s; SNOTEL snow-depth ~2003+). See `data/audit/coverage-*.md`.

## `variable`
- **Type:** `string`
- **Description:** What is measured.
- **Vocabulary / units:**
  - `swe_in` (in) — snow water equivalent (WTEQ). The primary variable.
  - `snow_depth_in` (in) — snow depth (SNWD).
  - `precip_accum_in` (in) — **water-year-cumulative** precipitation accumulation (PREC); SNOTEL only. A running total that resets each Oct 1 — *difference* it for daily/monthly precip; never sum it.
  - `snow_density_pct` (pct) and `air_temp_obs_f` (degF) are **declared for extensibility** (adding them is a parser change, not a contract change) but **not populated** in this build. `air_temp_obs_f` carries the documented SNOTEL extended-range temperature-sensor bias — see `concepts.yaml`.

## `value`
- **Type:** `Float64` (nullable)
- **Description:** The measurement, in the unit given by `unit`. **NA is preserved** for missing/not-reporting days — never silently zero-filled. Impossible negatives (AWDB missing sentinels, e.g. `-99.9`) are mapped to NA.

## `unit`
- **Type:** `string`
- **Description:** Unit of `value`. Derived from `variable`; `in` for SWE/depth/precip (`pct`/`degF` reserved for the declared-but-unpopulated variables).

## `qa_flag`
- **Type:** `string` (nullable)
- **Description:** AWDB quality flags, preserved not dropped — `qcFlag` then `qaFlag`, space-joined.
  - **qcFlag** (quality control): e.g. `V` valid, `E` edited/estimated, `S` suspect.
  - **qaFlag** (quality assurance): e.g. `P` provisional.
- **Why it matters:** recent SNOTEL values are provisional and may be revised; a SNOTEL↔snow-course disagreement on recent dates is usually a provisional/revision lag. Full definitions: NRCS NWCC documentation.

## `concept`
- **Type:** `string` (nullable)
- **Description:** Cross-source concept key (`snowpack.swe_in`, `snowpack.snow_depth_in`, `snowpack.precip_accum_in`) from `data/lookups/concepts.yaml`. **Concepts carry caveats** — the nearby-not-identical co-location, missing ≠ zero, water-year-cumulative precip, % -of-normal methodology, and the temperature-sensor bias. Read the catalog before comparing or combining series.

---

## Derived products (not columns)

- **Basin percent of normal** — `audit.basin_percent_normal` writes `data/audit/basin-percent-normal-*.md` + `.json`: per-basin `100 × Σ current SWE / Σ day-of-year-median SWE` (NRCS 1991–2020 baseline), the headline snowpack metric. Reconciled against the NRCS basin report by `audit.reconcile_basin_pct_normal`.
- **Co-location crosswalk** — `audit.colocated_pairs` writes the SNOTEL↔snow-course pairing (which historical snow course a SNOTEL continues), the basis for the cross-source check.

## Known issues / limitations

- **SNOTEL snow depth starts ~2003**, decades after the same station's SWE/precip — the depth sensor was added later. Early absence is "sensor not installed."
- **`precip_accum_in` is cumulative**, not incremental (see above).
- **Temperature & snow density not pulled** (declared only).
- **Seed is active stations**; discontinued stations (even deeper history) are one flag away (`build_sites_seed.py --all`).
- **% of normal is in-season only** (Nov–Jun); off-season it is a degenerate 0/0.
