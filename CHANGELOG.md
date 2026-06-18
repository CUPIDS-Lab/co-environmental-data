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
- Restructured `ROADMAP.md` with an assignable "this level's work" tracking table linked to issues #2–#5; moved the catalog-hardening + pipeline items out of the deferred list into tracked work.

### Deprecated

### Removed

### Fixed

### Security
