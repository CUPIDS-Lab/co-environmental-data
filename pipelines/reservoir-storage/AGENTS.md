# AGENTS.md — reservoir-storage pipeline

The architecture brief. A returning maintainer or AI agent should be able to read
this and add a source without re-reading every Python file.

## What this project is

A data-liberation pipeline that pulls **Colorado reservoir storage** (volume,
elevation, release) from public APIs — **CO DWR/CDSS** (state telemetry) and
**USBR Reclamation RISE** (federal + the C-BT reservoirs) — into one tidy
long-format CSV. (Northern Water, the third source originally scoped, turned out
to publish only spatial boundaries via its ArcGIS hub — no storage time series —
so its C-BT reservoirs are sourced from RISE instead; see *Known limitations*.)
It implements issue
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

**Notebooks are committed output-free.** A repo-root `.gitattributes` runs the
`nbstripout` git filter on `*.ipynb`, so cell outputs/exec-counts are stripped on
`git add`. Activate it once per clone (it's a dev dependency):

```bash
uv run nbstripout --install        # or: pip install nbstripout && nbstripout --install
```

Clones without it just skip stripping (the filter is non-required — no errors).

## Layout

| Path | Responsibility |
|---|---|
| `notebooks/reservoir-pipeline.ipynb` | Thin orchestration — all four stages (retrieve/audit/cleanup/publish) in one notebook. |
| `src/reservoir/schema.py` | `LONG_COLUMNS`, pandera `CanonicalLong`, `normalize_long`. |
| `src/reservoir/sources.py` | `Source` ABC + `Artifact` + the 3 source clients (discover/ingest). |
| `src/reservoir/config.py` | Paths, HTTP defaults, `get_sources()`, reads `lookups/sources.yaml`. |
| `src/reservoir/fetch.py` | Idempotent downloader (requests-cache + tenacity); RISE pagination; throttled progress reporting; writes `data/original/`. |
| `src/reservoir/parsers/*.py` | Per-source response → tidy long (`dwr_cdss`, `reclamation_rise`, `northern_water`). |
| `src/reservoir/clean.py` | Orchestrator: ingest all → concat → validate → write CSV + provenance. |
| `src/reservoir/audit.py` | `profile_raw`, `audit_processed`, `coverage_report` (per-site period of record), `variables_report`, `reconcile`. |
| `src/reservoir/stations.py` | Reservoir enumeration: build each source's catalog/station-list URL + parse it into the seed (`merge_into_seed`). |
| `src/reservoir/provenance.py` | Per-extract `provenance.csv` writer + sha256. |
| `data/{original,processed,audit,lookups}/` | Immutable raw · deliverable CSV · reports · crosswalks/config. |
| `docs/` | Survey notes, data dictionary, filter-pivot recipes. |

## Design decisions

- **Full history per site, different coverage per site.** Each site is pulled for
  its entire record, auto-clamped to that site's coverage (Green Mountain → 1986,
  the Walker pond → 2022; Blue Mesa → 1966). The retrieval gotchas this required:
  **DWR needs BOTH `startDate`+`endDate`** (no dates → last ~365 days only;
  startDate alone → 404), and **RISE must paginate** (`links.next`; its page cap is
  10k rows, well under a full series). `audit.coverage_report` documents each site's
  span. **RISE full-history pulls are large/slow** — window via `start_date` to speed up.
- **`data/original/` is a rebuildable cache, not an archive.** `fetch_all` skips
  files that already exist (idempotent re-runs), so when the *retrieval contract*
  changes (the full-history / pagination fixes), already-cached files go stale and a
  normal re-run won't refresh them. The notebook's retrieve cell defaults to
  **`FRESH=True`** (clears `data/original/` first) so the CSV always reflects exactly
  that run; `MODE` (live/demo) and `SOURCES` (split the big RISE pull) round out the
  config. `clean.run` faithfully turns whatever is on disk into the CSV — so a
  partial/stale cache yields a partial/stale CSV. Rebuild from clean on any contract change.
- **Day resolution is the grain.** `normalize_long` floors timestamps to the date
  (DWR reports midnight, RISE 07:00Z) so the CSV serializes uniformly and re-parses
  cleanly; the UTC date is preserved. Sources carry **multiple readings on some days**
  (sub-daily times / same-day revisions); `normalize_long` keeps the latest reading
  per `(reservoir, day, variable)` *before* validating, so a few dupe dates don't fail
  the uniqueness check and drop the whole reservoir. `clean.run` also resets
  `data/audit/extraction_errors.json` per run (it's append-only) so it reflects only
  the current run.
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

- **DWR/CDSS and RISE are both confirmed live** and return data; the pipeline's two
  storage sources are now DWR (state) + RISE (federal + C-BT). **Northern Water is
  NOT a storage source** — its ArcGIS hub publishes only 4 spatial-boundary datasets,
  so its discover() yields nothing and its C-BT reservoirs were moved to RISE.
- `data/lookups/reservoirs.csv` holds **118 DWR** reservoirs + **20 RISE**, **17 with
  confirmed item ids** (the 3 TODO — crystal/powell/taylor-park — need search-term
  tuning; their rows carry null `rise_item_ids` and are skipped). It was enumerated
  from CDSS (`reservoir.stations`) then **filtered to major reservoirs** — recharge/ag
  ponds (`POND|RECHARGE|ARF`, ~22 stations) were dropped as noise for a *reservoir
  storage* dataset; re-add them by re-running the full enumeration if needed. It is a
  dated **snapshot**; refresh DWR via `stations.parse_dwr_stations → merge_into_seed`,
  RISE via `stations.{rise_location_search_url, rise_location_items_url, parse_rise_location_items}`.
- A full live run fans out to **~280 DWR + ~51 RISE requests**; the resilient `fetch`
  handles per-station 404s (no-data) without crashing. **RISE full-history pulls are
  large** (records back to the 1930s–50s) — window with `start_date` for speed.
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
