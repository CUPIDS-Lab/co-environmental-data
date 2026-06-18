# AGENTS.md — reservoir-storage pipeline

The architecture brief. A returning maintainer or AI agent should be able to read
this and add a source without re-reading every Python file.

## What this project is

A data-liberation pipeline that pulls **Colorado reservoir storage** (volume,
elevation, release) from three public APIs — CO DWR/CDSS, USBR Reclamation RISE,
Northern Water — into one tidy long-format CSV. It implements issue
[#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9) of the Colorado
Environmental Data Hub. Follows the PUDL/BoulderPublicData convention: immutable
originals, per-source parsers, a harmonized canonical schema, reconciliation
against published totals.

## Quickstart

```bash
uv sync
uv run pytest
# then run notebooks/reservoir-pipeline.ipynb top to bottom
```

## Layout

| Path | Responsibility |
|---|---|
| `notebooks/reservoir-pipeline.ipynb` | Thin orchestration — all four stages (retrieve/audit/cleanup/publish) in one notebook. |
| `src/reservoir/schema.py` | `LONG_COLUMNS`, pandera `CanonicalLong`, `normalize_long`. |
| `src/reservoir/sources.py` | `Source` ABC + `Artifact` + the 3 source clients (discover/ingest). |
| `src/reservoir/config.py` | Paths, HTTP defaults, `get_sources()`, reads `lookups/sources.yaml`. |
| `src/reservoir/fetch.py` | Idempotent downloader (requests-cache + tenacity); writes `data/original/`. |
| `src/reservoir/parsers/*.py` | Per-source response → tidy long (`dwr_cdss`, `reclamation_rise`, `northern_water`). |
| `src/reservoir/clean.py` | Orchestrator: ingest all → concat → validate → write CSV + provenance. |
| `src/reservoir/audit.py` | `profile_raw`, `audit_processed`, `variables_report`, `reconcile`. |
| `src/reservoir/stations.py` | Reservoir enumeration: build each source's catalog/station-list URL + parse it into the seed (`merge_into_seed`). |
| `src/reservoir/provenance.py` | Per-extract `provenance.csv` writer + sha256. |
| `data/{original,processed,audit,lookups}/` | Immutable raw · deliverable CSV · reports · crosswalks/config. |
| `docs/` | Survey notes, data dictionary, filter-pivot recipes. |

## Design decisions

- **Tidy long, not wide.** One row per `(source, reservoir_id, datetime, variable)`.
  A new reservoir/variable is more rows, not a schema change; cross-source compare
  is a `groupby`. Wide views are recipes (`docs/filter-pivot-recipes.md`).
- **Unit of observation** chosen over the alternative (one row per reservoir×date
  with storage/elev/release as columns) so adding `pct_capacity`/`inflow` later
  doesn't migrate the schema.
- **`vintage = "current"`** for these live API pulls; the real snapshot time lives
  in `provenance.csv:retrieved_at`. Composite key is enforced unique in pandera.
- **`src/reservoir/` not `scripts/`.** Deliberate deviation from the data-liberation
  template's `scripts/` convention, for consistency with the parent repo's
  `src/<pkg>/` + thin-notebooks architecture (`context/architecture.md`).
- **No network on import.** Only `fetch.py` touches the network, and only when a
  notebook calls it — a live pull is always a deliberate, visible step.
- **Concepts carry caveats.** `data/lookups/concepts.yaml` — especially the
  **vertical-datum** caveat on elevation and the **capacity-baseline** caveat on
  storage. Comparing across sources without them produces misinformation.
- **Errors durable, not fatal.** A failed parse appends to
  `data/audit/extraction_errors.json`; the run continues. `clean.run(fail_on_empty=True)`
  turns a zero-row result (silent regression) into a hard error.

## Test coverage

All three parsers are fixture-tested (`tests/test_{dwr_cdss,reclamation_rise,northern_water}.py`),
plus a **multi-source integration test** (`test_pipeline_integration.py`) that
concatenates one fixture per source and asserts the combined frame satisfies the
schema + composite-key uniqueness, and the enumeration helpers
(`test_stations.py`). 17 tests; the suite runs offline with no network.

## Known limitations

- **DWR/CDSS is confirmed live** (endpoint, params, abbrevs, `measValue`, the
  404=zero-records convention) and returns data. The remaining `⚠️ VERIFY` points
  are **RISE** catalog **item ids** and **Northern Water** FeatureServer **service
  URL** + field names — both skip safely until filled. See `docs/survey-notes.md`.
- `data/lookups/reservoirs.csv` now holds the **full live DWR enumeration — all
  140 CDSS STORAGE telemetry stations** (pulled via `reservoir.stations` from the
  telemetrystation endpoint; the 7 majors keep curated names, the rest carry CDSS
  names), plus 12 RISE + 10 Northern rows. It is a dated **snapshot**; refresh it
  by re-running `stations.parse_dwr_stations(...) → stations.merge_into_seed(...)`.
  The 140 STORAGE stations include small ponds/tanks as well as major reservoirs —
  subset by name if you want only the majors. RISE/Northern enumeration URLs build;
  their station parsers land once those VERIFY endpoints are confirmed.
- A full live run now fans out to **280 DWR requests** (140 reservoirs × STORAGE+ELEV);
  the resilient `fetch` handles the per-station 404s (no-data) without crashing.
- RISE `discover()` skips reservoirs whose `rise_item_ids` are still null
  placeholders, so a live run is safe before every id is filled.
- `reconcile()` has no expected totals filled yet.
- Single response shape per source assumed (no vintage bands yet); add
  `parsers/<source>_<vintage>.py` if a source's API response shape changes.

## How to add a new source / vintage

1. Add a `Source` subclass in `src/reservoir/sources.py` and register it in `SOURCES`.
2. Add its config block to `data/lookups/sources.yaml`.
3. Add a parser `src/reservoir/parsers/<source>.py` exposing `parse(path, artifact) -> DataFrame`.
4. Add a fixture in `tests/fixtures/` + a `tests/test_<source>.py` with a known-total assertion.
5. Add the source's variable codes to `data/lookups/concepts.yaml` with caveats.
6. Run `audit.audit_processed()` and `audit.reconcile()`; investigate any mismatch.

## Out-of-scope uses

This dataset exists for public-interest water reporting and research. Repackaging
it to enrich water-rights speculation or to obscure rather than inform public
drought response is out of scope; the maintainers ask downstream users to honor
that. (Open data ≠ information justice.)

## References

- `context/source-inventory.md` (Hub) — Theme 1 Water source catalogue.
- CO DWR/CDSS REST API: https://dwr.state.co.us/rest/get/help
- USBR RISE API: https://data.usbr.gov/rise/api
- Northern Water open data: https://data-nw.opendata.arcgis.com
