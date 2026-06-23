# AGENTS.md — climate-stations pipeline

The architecture brief. A returning maintainer or AI agent should be able to read this and add a measure (or scale the station seed) without re-reading every Python file.

## What this project is

A data-liberation pipeline that pulls **Colorado daily climate-station observations** — temperature (max/mean/min), precipitation, snowfall / snow depth / snow water equivalent, pan evaporation, solar radiation, vapor pressure, and wind run — from the **CO DWR / CDSS** Climate Station Time Series (day) API into one tidy long-format CSV. It implements issue [#44](https://github.com/CUPIDS-Lab/co-environmental-data/issues/44) of the Colorado Environmental Data Hub and is **stamped out from the sibling `streamflow` pipeline** (#10): same PUDL/BoulderPublicData convention (immutable originals, a per-source parser, a harmonized canonical schema, reconciliation against truth), with the domain swapped.

**The two structural differences from `streamflow`:**
1. **One API, many networks.** A single source (`cdss_climate`) federates five observing networks behind one schema — NOAA COOP/GHCN, CoCoRaHS, NRCS/SNOTEL, CoAgMet, NCWCD. The network is a *station* attribute (`stations.csv:network` / the row's `dataSource`), not a separate source slug.
2. **Twelve measures, five units.** `MEAS_MAP` maps each CDSS measType to `(variable, concept, unit)`. Units differ (degF / in / mJ/m^2 / kPa / KM), so harmonization is **per concept**, and the daily endpoint takes **one measType per request** (a station costs up to 12 requests).

## Quickstart

```bash
uv sync
uv run pytest                 # 23 tests, offline
# then run notebooks/climate-stations-pipeline.ipynb top to bottom, OR the headless twin:
uv run python -m climate_stations.pipeline --mode demo --fresh    # offline smoke test
uv run python -m climate_stations.pipeline --mode live --fresh \
    --sites 1886,10417 --meas-types Precip,SnowSWE,MaxTemp        # live sample
```

A **CDSS API key is required in practice** (anonymous limits since 2025-12-10): put `{"CDSS_API_KEY": "..."}` in a git-ignored `dwr_api.json` at the pipeline root, or set `$CDSS_API_KEY`. **Notebooks are committed output-free** via the repo-root `nbstripout` filter.

## Layout

| Path | Responsibility |
|---|---|
| `notebooks/climate-stations-pipeline.ipynb` | Thin orchestration — all four stages (retrieve/audit/cleanup/publish) in one notebook. |
| `src/climate_stations/schema.py` | `LONG_COLUMNS`, `MEAS_MAP` (12 measTypes → variable/concept/unit), pandera `CanonicalLong`, `normalize_long` (local-date floor + dedupe). |
| `src/climate_stations/sources.py` | `Source` ABC + `Artifact` + the `CdssClimate` client (discover/ingest; station × measType fan-out). |
| `src/climate_stations/config.py` | Paths, HTTP defaults, `get_sources()`, reads `lookups/sources.yaml`; env-tunable rate/retries; CDSS key loader. |
| `src/climate_stations/fetch.py` | Idempotent downloader (requests-cache + tenacity); throttle-retry; 404 = no-data; writes `data/original/`. |
| `src/climate_stations/parsers/cdss_climate.py` | Response → tidy long; per-variable sentinel cleaning (preserves sub-zero temps). |
| `src/climate_stations/clean.py` | Orchestrator: ingest all → concat → validate → write CSV + provenance. |
| `src/climate_stations/audit.py` | `profile_raw`, `audit_processed`, `coverage_report`, `variables_report`, **`network_summary`**, `reconcile`. |
| `src/climate_stations/stations.py` | Station enumeration: catalog URL + parser; `select_active` / `curate_seed`. |
| `src/climate_stations/provenance.py` | Per-extract `provenance.csv` writer + sha256. |
| `scripts/build_stations_seed.py` | Regenerate `stations.csv` (stdlib-only; `--all` for every active station). |
| `data/{original,processed,audit,lookups}/` | Immutable raw · deliverable CSV · reports · seed/config. |
| `docs/` | Survey notes (the confirmed contract), data dictionary, filter-pivot recipes. |

## Design decisions

- **`site_id` = CDSS `stationNum`**, a stable integer id. The network-native id (GHCN `siteId`) is `stations.csv:site_id_network` — the join key for the SNOTEL/GHCN crosswalk to snowpack #11. The catalog returns **12,704 records → 4,962 distinct stations** (multiple POR segments per station); `build_stations_seed.py` **dedupes on `stationNum`** (widest POR).
- **Station identifier is REQUIRED.** The daily endpoint rejects a measType-only query (`Error: (stationNum or siteId) required`), so enumeration is inherently per-station. One measType per request; full POR fits one page.
- **Per-variable sentinel cleaning (the central correctness rule).** A value `<= -999` is the missing sentinel → NA for any measure. For non-negative-domain measures (precip, snow, SWE, depth, evap, solar, wind, VP) any negative → NA. **Temperatures are exempt** — sub-zero degF is real (the live sample carries a `-39.98°F` daily max). See `schema.NON_NEGATIVE_VARS`.
- **Local-date day grain.** CDSS `measDate` is midnight LOCAL with a tz offset (-06:00/-07:00); `normalize_long` floors to the **local** calendar date (converting to UTC first would roll an evening reading to the next day) and keeps the latest reading per `(source, site_id, day, variable)`. (A deliberate refinement over streamflow's UTC floor.)
- **Tidy long, not wide.** One row per `(source, site_id, datetime, variable)`. Wide views are recipes (`docs/filter-pivot-recipes.md`). The station dimension (network, lat/lon, POR) is `stations.csv`, joined on `site_id`.
- **`vintage = "current"`** for these live pulls; the snapshot time is in `provenance.csv:retrieved_at`.
- **No network on import.** Only `fetch.py` touches the network, and only when a notebook/CLI calls it.
- **Errors durable, not fatal.** A failed fetch → `data/audit/fetch_errors.json`; a 404 (a station that doesn't report a measure) → silent no-data; a failed parse → `data/audit/extraction_errors.json`. `clean.run(fail_on_empty=True)` turns a zero-row result into a hard error.

## Test coverage

The parser is fixture-tested against **real** (trimmed) API responses (`tests/test_cdss_climate.py`): a Precip series (zero-preservation), a Solar series (the non-degF `mJ/m^2` unit + a known value), and inline guards for the sub-zero-temp-preserved / `-999`-sentinel→NA / impossible-negative→NA / flag-join behaviors. `test_pipeline_integration.py` asserts heterogeneous-unit measures coexist under the schema + composite-key uniqueness; `test_sources.py` pins the URL contract + sites/meas_types filters; `test_schema.py` guards the contract (12 measTypes, confirmed units, temps exempt from cleaning); `test_stations.py` covers catalog parsing + the active filter; `test_fetch.py` covers progress rendering. **23 tests; the suite runs offline with no network.**

## Known limitations

- **⚠️ CDSS anonymous limits (since 2025-12-10).** A keyless pull returns `"Error: Exceeded Daily Data Limit"`. Use a CDSS API key (`dwr_api.json` / `$CDSS_API_KEY`), read by `config._load_cdss_api_key`. A burst of large full-history requests can still trip a transient 403 — the tenacity back-off + `CLIMATE_RATE_LIMIT` handle it.
- **Curated seed, not exhaustive.** `data/lookups/stations.csv` is a **40-station** active cross-section (8 per network) — a dated snapshot regenerable via `scripts/build_stations_seed.py`. Scale to "all active CO climate stations" with `--all` (≈ thousands; a station-filter change, not a refactor).
- **`FrostDate` unconfirmed.** A valid measType but returned no rows in the sampled stations; its unit/semantics are not verified. The parser passes it through with NO sentinel cleaning; `concept` caveats flag it. Verify before use.
- **Raw flags, not decoded.** `flagA..flagD` are preserved verbatim; a per-network approved/estimated/filled decoder is future work.
- **Datasette / Dataverse publication** is roadmap (declared in `pyproject.toml [publish]`), not yet wired.

## How to add a measure / scale the seed

1. The 12 measTypes are already mapped in `schema.MEAS_MAP` and listed in `sources.yaml:meas_types`. To add a *new* CDSS measType: add a `MEAS_MAP` row (variable, concept, unit), list it in `sources.yaml`, add a `concepts.yaml` entry with caveats, and a fixture + assertion in `tests/test_cdss_climate.py`.
2. To scale the station seed: `python scripts/build_stations_seed.py --all` (every active station) or raise `--per-network`.
3. Run `audit.audit_processed()`, `audit.network_summary()`; investigate any out-of-range value or `(unknown)` network.

## Out-of-scope uses

This dataset exists for public-interest climate and water reporting and research. Repackaging it to enrich speculation, or to obscure rather than inform public drought/heat/flood response, is out of scope; the maintainers ask downstream users to honor that. Raw station values are **not homogenized** (no time-of-observation or sensor-change adjustment) and **not network-equivalent** — do not present them as a clean climate-trend series without the caveats in `concepts.yaml`. (Open data ≠ information justice.)

## References

- `context/source-inventory.md` (Hub) — Theme 1 Water / climate source catalogue.
- CDSS climate daily API: https://dwr.state.co.us/Rest/GET/Help/Api/GET-api-v2-climatedata-climatestationtsday
- CO DWR/CDSS REST API: https://dwr.state.co.us/rest/get/help
- Sibling pipeline (shared architecture): `../streamflow/AGENTS.md`
- Snowpack pipeline (SWE overlap): issue #11.
