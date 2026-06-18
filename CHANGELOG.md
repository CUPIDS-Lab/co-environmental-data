# Changelog

All notable changes to Colorado Environmental Data Hub are recorded here. Format follows [Keep a Changelog](https://keepachangelog.com/); this project aims to use semantic versioning for data and code releases.

## [Unreleased]

### Added
- Initial project scaffold (level L1) via the CUPIDS Lab `data-project` skill.
- `DATA-DICTIONARY.md` documenting the 56-source Colorado environmental data catalog (schema v1.0, compiled 2026-06-17).
- Immutable copy of `colorado_environmental_data_sources.json` under `data/raw/` (tracked).
- `ROADMAP.md` recording the deferred L2–L5 program (pipeline, collaboration, responsible-data, open-knowledge publication).
- `AGENTS.md`, `decision-log.md`, data-aware `.gitignore`, and `.gitattributes`.
- GitHub project-management layer (Track mode): 4 tracked issues ([#2–#5](https://github.com/CUPIDS-Lab/co-environmental-data/issues)), the `L1-L2: catalog hardening & pipeline` milestone, the full `priority/size/level/type/blocking` label taxonomy, issue forms + PR template under `.github/`, `PROJECT-MANAGEMENT.md`, `NEXT-STEPS.md`, `.github/ACCESS.md`, an idempotent `.github/seed-github.sh` + `engagement-sync.json`, and wiki seeds under `.github/wiki-seeds/`.
- Epic issue [#7](https://github.com/CUPIDS-Lab/co-environmental-data/issues/7) under a new **Water data liberation** milestone: retrieve / clean / document / republish Colorado reservoir storage, stream/river flow, and snowpack (SWE) — current and historical — added to the Project board and the `ROADMAP.md` tracking table.
- Per-domain sub-issues under #7, linked as native GitHub sub-issues and added to the board: [#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9) reservoir storage, [#10](https://github.com/CUPIDS-Lab/co-environmental-data/issues/10) stream/river flow, [#11](https://github.com/CUPIDS-Lab/co-environmental-data/issues/11) snowpack (SWE).
- Scaffolded the **reservoir-storage** data-liberation pipeline (`pipelines/reservoir-storage/`) for [#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9): notebook-driven (retrieve → audit → cleanup → publish-CSV) over a tested `reservoir` package, with three source clients (DWR/CDSS, Reclamation RISE, Northern Water), a tidy-long pandera schema, per-extract provenance, a concept catalog with caveats, and an offline-runnable demo (6 tests passing).
- Hardened the reservoir-storage pipeline ([#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9)): fixtures + parser tests for all three sources, a multi-source integration test, an automated reservoir-enumeration capability (`reservoir.stations`), and an expanded ~37-reservoir curated seed — 17 tests passing offline.

### Changed
- Expanded the stub `README.md` into an L1 front door.
- `fetch.fetch_all` now reports **throttled progress** (current source/reservoir, `done/total`, ok/no-data/error counts) so long full-history pulls show liveness; `progress=False` silences it, or pass a callable to drive a custom sink (tqdm/structlog).
- Added an **`nbstripout` git filter** (repo-root `.gitattributes`) so Jupyter notebooks commit output-free automatically. Run `nbstripout --install` once per clone to activate (dev dependency); the filter is non-required, so clones without it simply skip stripping.
- Restructured `ROADMAP.md` with an assignable "this level's work" tracking table linked to issues #2–#5; moved the catalog-hardening + pipeline items out of the deferred list into tracked work.
- Full DWR enumeration ([#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9)): `pipelines/reservoir-storage/data/lookups/reservoirs.csv` now holds all **140 live CDSS STORAGE telemetry stations** (pulled via `reservoir.stations`), replacing the 7-reservoir curated seed (the 7 majors keep their curated names).
- RISE + Northern enumeration ([#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9)): resolved RISE catalog **item ids for 17/20 reservoirs** via the confirmed `location → catalogRecords → catalogItems` traversal (implemented + tested in `reservoir.stations`). **Finding: Northern Water's ArcGIS hub has no reservoir-storage series** (4 boundary datasets only) — its C-BT reservoirs (Carter, Horsetooth, Granby, Shadow Mountain, Willow Creek, Lake Estes, Marys Lake, Pinewood) are Reclamation-owned and were **moved to RISE**. `reservoirs.csv` = 140 DWR + 20 RISE; `northern_water` is reclassified as a non-storage (boundaries-only) source.

### Deprecated

### Removed
- Merged the four reservoir notebooks (`nb-01`…`nb-04`) into one `pipelines/reservoir-storage/notebooks/reservoir-pipeline.ipynb`.

### Fixed
- Reservoir-storage live retrieval ([#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9)): CDSS returns **HTTP 404 for zero-record queries**, which was crashing `fetch.fetch_all()`. `fetch` now treats 404 as no-data (durable, not fatal, per-artifact error log); also corrected the parser field (`measValue` not `value`), the real station abbrevs (`GRERESCO`, …), and dropped the too-early default `startDate`. A live DWR pull now returns ~4,374 rows across 6 reservoirs.
- **Full historical scope** ([#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9)): the pipeline was returning only the past ~year per site. Two root causes fixed: **DWR** needs *both* `startDate`+`endDate` (no dates → last 365 days; startDate alone → 404) — now sends an early start + `endDate=today` so CDSS auto-clamps to each site's period of record; **RISE** silently capped series at 10,000 rows (used the wrong page param `page[size]`, no pagination) — now uses `itemsPerPage` and the fetcher follows `links.next`. Verified: Green Mountain 14,187 rows back to 1986, Blue Mesa 22,053 back to 1966. `normalize_long` floors to day-resolution for uniform serialization; new `audit.coverage_report` documents each site's span (different sites, different coverage).

### Security
