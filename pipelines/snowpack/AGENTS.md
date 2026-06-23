# AGENTS.md — snowpack pipeline

The architecture brief. A returning maintainer or AI agent should be able to read this and add a source without re-reading every Python file.

## What this project is

A data-liberation pipeline that pulls **Colorado snowpack** — snow water equivalent (SWE, in), snow depth (in), and water-year precipitation accumulation (in) — from the **NRCS AWDB REST API** across two networks (**SNOTEL**, automated daily; **snow courses**, manual semimonthly) into one tidy long-format CSV. It implements issue [#11](https://github.com/CUPIDS-Lab/co-environmental-data/issues/11) of the Colorado Environmental Data Hub and is **stamped out from the sibling `streamflow` pipeline** (#10): same convention (immutable originals, per-source parsers, a harmonized canonical schema, reconciliation against truth), with the domain swapped (`swe_in`/`snow_depth_in`/`precip_accum_in` not `discharge_cfs`).

## Quickstart

```bash
uv sync
uv run pytest                 # 28 tests, offline
# then run notebooks/snowpack-pipeline.ipynb top to bottom, OR the headless twin:
uv run python -m snowpack.pipeline --mode demo --fresh                  # offline smoke test
uv run python -m snowpack.pipeline --mode live --fresh \
    --sites 680:CO:SNTL,06L02:CO:SNOW                                   # live sample
```

**Notebooks are committed output-free** via the repo-root `nbstripout` filter (`uv run nbstripout --install` once per clone; clones without it just skip it).

## Layout

| Path | Responsibility |
|---|---|
| `notebooks/snowpack-pipeline.ipynb` | Thin orchestration — all four stages (retrieve/audit/cleanup/publish) in one notebook. |
| `src/snowpack/schema.py` | `LONG_COLUMNS`, pandera `CanonicalLong`, `normalize_long` (day-floor + dedupe). |
| `src/snowpack/sources.py` | `Source` ABC + `Artifact` + the 2 AWDB source clients (one request per station, all elements). |
| `src/snowpack/config.py` | Paths, HTTP defaults, `get_sources()`, reads `lookups/sources.yaml`; env-tunable rate/retries. **No API key** (AWDB is open). |
| `src/snowpack/fetch.py` | Idempotent downloader (requests-cache + tenacity); writes `data/original/`. |
| `src/snowpack/parsers/` | `_awdb.py` shared parser + thin `nrcs_snotel` / `nrcs_snowcourse` adapters. |
| `src/snowpack/clean.py` | Orchestrator: ingest all → concat → validate → write CSV + provenance. |
| `src/snowpack/audit.py` | `profile_raw`, `audit_processed`, `coverage_report`, `variables_report`, **`basin_percent_normal`**, `reconcile_basin_pct_normal`, `colocated_pairs`, `reconcile_cross_source`. |
| `src/snowpack/stations.py` | Station enumeration: AWDB catalog URL + `huc_to_basin` + the seed builder helpers. |
| `src/snowpack/provenance.py` | Per-extract `provenance.csv` writer + sha256. |
| `scripts/build_sites_seed.py` | Regenerate `data/lookups/sites.csv` live (stdlib-only; `--all` for discontinued stations). |
| `data/{original,processed,audit,lookups}/` | Immutable raw · deliverable CSV · reports · crosswalks/config. |
| `docs/` | Survey notes, data dictionary, filter-pivot recipes (incl. a basin %-of-normal recipe). |

## Design decisions

- **Two networks that COMPLEMENT, not overlap (the central fact).** Unlike streamflow's USGS↔DWR re-serve (same gage, identical values), a SNOTEL and a same-named snow course are **nearby but distinct sites**, sampled differently (continuous pillow vs periodic manual transect). They are kept distinct (`source` in the key) and are *complementary*: the snow course extends the SWE record decades before SNOTEL (live Gunnison sample reaches **1936**). `audit.reconcile_cross_source` uses the **co-location** (same name or <2 km via `colocated_pairs`) as a **looser** sanity check — a pair tracks within a few inches, not byte-identically. **Never treat a co-located pair as two independent reads of one point.**
- **One AWDB API, two sources.** Both clients hit the same `data` endpoint; they differ only in `network` (SNTL/SNOW), `duration` (DAILY/SEMIMONTHLY), and the per-value date field (`date` vs `collectionDate`). The real parsing is in `parsers/_awdb.py`; the two modules are thin adapters. Adding SNOLITE (`SNTLT`) or SCAN is a `sources.yaml` block + a one-line source subclass.
- **One request per station, all elements.** AWDB serves multiple elements and a station's **full POR in one response** (not paginated) — so `discover()` yields one Artifact per station requesting `WTEQ,SNWD,PREC` at once. Raw file: `data/original/<source>/current/<triplet>.json` (colons → underscores in the filename).
- **The signature product is basin % of normal.** `audit.basin_percent_normal` = `100 × Σ current SWE / Σ day-of-year-median SWE` (NRCS 1991–2020 baseline), per basin — the headline Colorado snow number. `reconcile_basin_pct_normal` checks it against the NRCS basin report. It is the snowpack analog of streamflow's free cross-source check; meaningful in-season only.
- **HUC → basin.** `stations.huc_to_basin` derives each station's major river basin from its HUC (HUC4 + a White/Yampa split on HUC8). A documented approximation; NRCS basin definitions are the authority.
- **Day resolution is the grain.** `normalize_long` floors timestamps to the date and keeps the latest reading per `(source, site, day, variable)`.
- **Tidy long, not wide.** One row per `(source, site_id, datetime, variable)`. Wide/seasonal/%-of-normal views are recipes (`docs/filter-pivot-recipes.md`).
- **Missing/impossible harmonized to NA.** SWE/depth/precip are non-negative; AWDB missing sentinels (e.g. `-99.9`) and any negative map to NA (never zero-filled). The qcFlag/qaFlag are preserved (space-joined) in `qa_flag`.
- **`vintage = "current"`** for these live pulls; the snapshot time is in `provenance.csv:retrieved_at`. Composite key enforced unique in pandera.
- **`src/snowpack/` not `scripts/`.** Deliberate deviation from the data-liberation template's `scripts/` convention, for consistency with the parent repo's `src/<pkg>/` + thin-notebooks architecture.
- **No network on import.** Only `fetch.py` (and the seed builder) touch the network, and only when called.
- **Errors durable, not fatal.** A failed fetch → `data/audit/fetch_errors.json`; a failed parse → `data/audit/extraction_errors.json`; the run continues. `clean.run(fail_on_empty=True)` turns a zero-row result into a hard error.

## Test coverage

Both parsers are fixture-tested against **real** (trimmed) AWDB responses (`tests/test_nrcs_{snotel,snowcourse}.py`), including the SNOTEL multi-element split, the negative-sentinel→NA regression, the unknown-element skip, and the snow-course `collectionDate` gotcha; a **multi-source integration test** asserts the combined frame satisfies the schema + composite-key uniqueness and that snow courses extend history before SNOTEL; `test_sources.py` pins the AWDB URL contract (elements/duration/returnFlags, no key) + the sites filter; `test_audit.py` checks `huc_to_basin`, `basin_percent_normal`, `colocated_pairs`, and `reconcile_cross_source` on constructed data; `test_schema.py` guards the contract; `test_fetch.py` covers progress rendering + the no-data path. **28 tests; the suite runs offline with no network.**

## Known limitations

- **No API key needed, no throttle observed** — simpler than the CDSS pipelines. Politeness rate-limit (`SNOWPACK_RATE_LIMIT`, default 0.3 s) + exponential back-off on transient 5xx/429 are kept as insurance for the full 199-station pull.
- **Active-station seed.** `data/lookups/sites.csv` is **all 199 active CO SNOTEL + snow courses** (full-state coverage, not a sample). Discontinued stations (even deeper history) are one flag away: `scripts/build_sites_seed.py --all`.
- **SNOTEL snow depth starts ~2003** (sensor added after the pillow); early absence is "sensor not installed," not "no snow."
- **`precip_accum_in` is water-year cumulative** (resets Oct 1) — difference it for daily/monthly precip; never sum it.
- **Temperature & snow density declared, not pulled.** `air_temp_obs_f` carries the documented SNOTEL **extended-range temperature-sensor bias** (issue #11) — read the caveat in `concepts.yaml` before populating it.
- **Single response shape per source** (no vintage bands yet); add `parsers/<source>_<vintage>.py` if AWDB's response shape changes.

## How to add a new source / vintage

1. Add a `Source` subclass in `src/snowpack/sources.py` and register it in `SOURCES` (e.g. `SNTLT` SNOLITE, `SCAN`).
2. Add its config block to `data/lookups/sources.yaml` (network, duration, date_field, elements).
3. If the response shape differs, add a parser `src/snowpack/parsers/<source>.py`; otherwise reuse `_awdb.parse_awdb`.
4. Add a fixture in `tests/fixtures/` + a `tests/test_<source>.py` with a known-value assertion.
5. Add the source's element codes to `data/lookups/concepts.yaml` with caveats.
6. Run `audit.audit_processed()`, `audit.basin_percent_normal()`, `audit.reconcile_cross_source()`; investigate any anomaly.

## Relationship to #44 (CO DWR/CDSS climate stations)

Issue #11 lists "CO DWR/CDSS climate stations" as a snowpack source; **#44 owns that domain** (it serves `SnowSWE`/`SnowDepth` across 12k+ CDSS climate stations) and asks #11 to focus on **NRCS SNOTEL** with a SNOTEL↔CDSS crosswalk. This pipeline does exactly that. When both are used together, build the explicit site crosswalk (by name/proximity, as `colocated_pairs` does) and do **not** treat CDSS `SnowSWE` and NRCS `WTEQ` for the same physical site as independent — same discipline as the streamflow USGS↔DWR overlap. See `concepts.yaml:crosswalks`.

## Out-of-scope uses

This dataset exists for public-interest water reporting and research — runoff and drought outlooks, water-supply forecasting, Colorado River context. Repackaging it to enrich water-rights speculation, or to obscure rather than inform public drought response, is out of scope; the maintainers ask downstream users to honor that. SWE at a point is **not** the basin's water supply — aggregate honestly (see the % -of-normal caveats), and remember missing ≠ zero. (Open data ≠ information justice.)

## References

- `context/source-inventory.md` (Hub) — Theme 1 Water source catalogue (NRCS SNOTEL).
- NRCS AWDB REST API (Swagger): https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html
- NRCS National Water and Climate Center: https://www.nrcs.usda.gov/wps/portal/wcc/home/
- Sibling pipeline (shared architecture): `../streamflow/AGENTS.md`
