# AGENTS.md — streamflow pipeline

The architecture brief. A returning maintainer or AI agent should be able to read this and add a source without re-reading every Python file.

## What this project is

A data-liberation pipeline that pulls **Colorado stream/river flow** (daily mean discharge, cfs) from two public APIs — **USGS NWIS** (federal; the national record) and **CO DWR/CDSS surface water** (state) — into one tidy long-format CSV. It implements issue [#10](https://github.com/CUPIDS-Lab/co-environmental-data/issues/10) of the Colorado Environmental Data Hub and is **stamped out from the sibling `reservoir-storage` pipeline** (#9): same PUDL/BoulderPublicData convention (immutable originals, per-source parsers, a harmonized canonical schema, reconciliation against truth), with the domain swapped (`site_*` not `reservoir_*`; `discharge_cfs` not `storage_af`).

## Quickstart

```bash
uv sync
uv run pytest                 # 25 tests, offline
# then run notebooks/streamflow-pipeline.ipynb top to bottom, OR the headless twin:
uv run python -m streamflow.pipeline --mode demo --fresh    # offline smoke test
uv run python -m streamflow.pipeline --mode live --fresh \
    --sites 09095500,08220000,06714000                      # live sample
```

**Notebooks are committed output-free** via the repo-root `nbstripout` filter (`uv run nbstripout --install` once per clone; clones without it just skip it).

## Layout

| Path | Responsibility |
|---|---|
| `notebooks/streamflow-pipeline.ipynb` | Thin orchestration — all four stages (retrieve/audit/cleanup/publish) in one notebook. |
| `src/streamflow/schema.py` | `LONG_COLUMNS`, pandera `CanonicalLong`, `normalize_long` (day-floor + dedupe). |
| `src/streamflow/sources.py` | `Source` ABC + `Artifact` + the 2 source clients (discover/ingest). |
| `src/streamflow/config.py` | Paths, HTTP defaults, `get_sources()`, reads `lookups/sources.yaml`; env-tunable rate/retries. |
| `src/streamflow/fetch.py` | Idempotent downloader (requests-cache + tenacity); throttle-retry; writes `data/original/`. |
| `src/streamflow/parsers/*.py` | Per-source response → tidy long (`usgs_nwis`, `dwr_cdss`). |
| `src/streamflow/clean.py` | Orchestrator: ingest all → concat → validate → write CSV + provenance. |
| `src/streamflow/audit.py` | `profile_raw`, `audit_processed`, `coverage_report`, `variables_report`, `reconcile`, **`reconcile_cross_source`**. |
| `src/streamflow/stations.py` | Gage enumeration: build each source's catalog URL + the USGS↔DWR cross-link resolver. |
| `src/streamflow/provenance.py` | Per-extract `provenance.csv` writer + sha256. |
| `data/{original,processed,audit,lookups}/` | Immutable raw · deliverable CSV · reports · crosswalks/config. |
| `docs/` | Survey notes, data dictionary, filter-pivot recipes. |

## Design decisions

- **Two sources that OVERLAP (the central fact).** Unlike reservoir's disjoint DWR/RISE, DWR surface water **re-serves** many USGS gages (`dataSource=USGS`). The same gage appears under both slugs, joined by `usgs_site_no` in `sites.csv`. `source` is in the composite key so they coexist as distinct rows; **never treat them as independent** — de-dup to one source for analysis (USGS = system of record; DWR often *extends* it past USGS discontinuation). The overlap doubles as a free accuracy check: `audit.reconcile_cross_source` (33 pairs, 97.6–100 %, median 100 %).
- **`--sites` matches `site_id` OR `usgs_site_no`.** Because the two sources use different id namespaces (USGS number vs DWR abbrev), the sampling key is the USGS number — passing `--sites 09095500` selects both that USGS gage and its DWR mirror.
- **Full history per gage, different coverage per gage.** Each gage is pulled for its entire record (USGS clamps to POR; CDSS clamps to its station POR). Retrieval gotchas: **USGS** dv is one (large) response, not paginated; **DWR** needs `min-measDate`/`max-measDate` (not `startDate`), `measType=Streamflow` (not `DISCHRG`), and the value field is `value` (not `measValue`). See `coverage_report`.
- **Day resolution is the grain.** `normalize_long` floors timestamps to the date and keeps the latest reading per `(source, site, day, variable)` before validating.
- **Tidy long, not wide.** One row per `(source, site_id, datetime, variable)`. Wide views are recipes (`docs/filter-pivot-recipes.md`).
- **Ice/missing harmonized to NA.** CDSS encodes ice-affected days as the impossible discharge `-999` (`U`/`Ice` flag); the DWR parser maps negative discharge → NA, matching USGS's NA. The flag is preserved so the *reason* stays in `qa_flag`.
- **`vintage = "current"`** for these live pulls; the snapshot time is in `provenance.csv:retrieved_at`. Composite key enforced unique in pandera.
- **`src/streamflow/` not `scripts/`.** Deliberate deviation from the data-liberation template's `scripts/` convention, for consistency with the parent repo's `src/<pkg>/` + thin-notebooks architecture (`context/architecture.md`).
- **No network on import.** Only `fetch.py` touches the network, and only when a notebook/CLI calls it.
- **Errors durable, not fatal.** A failed fetch → `data/audit/fetch_errors.json`; a failed parse → `data/audit/extraction_errors.json`; the run continues. `clean.run(fail_on_empty=True)` turns a zero-row result into a hard error.

## Test coverage

Both parsers are fixture-tested against **real** (trimmed) API responses (`tests/test_{usgs_nwis,dwr_cdss}.py`), including the ice-sentinel→NA regression and the DWR `value`-not-`measValue` guard; a **multi-source integration test** asserts the combined frame satisfies the schema + composite-key uniqueness and that the overlap values agree; `test_sources.py` pins the URL contract + sites filter; `test_audit_cross_source.py` checks the cross-source reconciliation math; `test_schema.py` guards the contract; `test_fetch.py` covers progress rendering; `test_stations.py` asserts the committed seed carries station coordinates (lat/long within Colorado) and that the enumeration helpers parse coordinates/county/POR. 25 tests; the suite runs offline with no network.

## Known limitations

- **⚠️ CDSS throttle (HTTP 403) on keyless pulls.** A burst of large full-history DWR requests *without* an API key trips a persistent IP-level 403 throttle. The fix — and what this pipeline uses — is a **CDSS API key** in the git-ignored `dwr_api.json` (or `$CDSS_API_KEY`), read by `config._load_cdss_api_key`; with it the full 33-DWR pull completes with **zero errors**. Keyless, raise `STREAMFLOW_RATE_LIMIT` and lean on the retry/back-off for transient throttles. USGS has no such limit.
- **Curated seed, not exhaustive.** `data/lookups/sites.csv` is a curated **33 major-river gages** (all 8 basins) + their **33 DWR mirrors** (66 rows) — a dated snapshot regenerable via `scripts/build_sites_seed.py` (USGS site service + CDSS `usgsSiteId` cross-link, using the key). Scale to "all active CO discharge gages" via `streamflow.stations`; a station-filter change, not a refactor.
- **Discharge only.** `gage_height_ft` is declared in the schema but not pulled; add a parameter to `sources.yaml` + map the code in the parsers (no contract change).
- **Single response shape per source** (no vintage bands yet); add `parsers/<source>_<vintage>.py` if a source's API response shape changes.
- **Legacy USGS NWIS migration.** `waterservices.usgs.gov/nwis/dv` is confirmed live but USGS is migrating to `api.waterdata.usgs.gov`; if it sunsets, add a new parser/vintage against the OGC API.

## How to add a new source / vintage

1. Add a `Source` subclass in `src/streamflow/sources.py` and register it in `SOURCES`.
2. Add its config block to `data/lookups/sources.yaml`.
3. Add a parser `src/streamflow/parsers/<source>.py` exposing `parse(path, artifact) -> DataFrame`.
4. Add a fixture in `tests/fixtures/` + a `tests/test_<source>.py` with a known-value assertion.
5. Add the source's variable codes to `data/lookups/concepts.yaml` with caveats.
6. Run `audit.audit_processed()`, `audit.reconcile_cross_source()`; investigate any mismatch.

## Out-of-scope uses

This dataset exists for public-interest water reporting and research. Repackaging it to enrich water-rights speculation, or to obscure rather than inform public drought and flood response, is out of scope; the maintainers ask downstream users to honor that. Gaged discharge is **regulated, not naturalized** flow — do not present it as undepleted hydrology. (Open data ≠ information justice.)

## References

- `context/source-inventory.md` (Hub) — Theme 1 Water source catalogue.
- USGS NWIS daily values: https://waterservices.usgs.gov/docs/dv-service/
- USGS Water Data APIs (successor): https://api.waterdata.usgs.gov
- CO DWR/CDSS REST API: https://dwr.state.co.us/rest/get/help
- Sibling pipeline (shared architecture): `../reservoir-storage/AGENTS.md`
