# AGENTS.md — guidance for agents and humans working in this repo

Read this first. It states the non-negotiables and points you at the right place for each task. This repo was scaffolded with the CUPIDS Lab `data-project` skill at level **L1**.

## Non-negotiables

- **Raw data is immutable.** Never edit anything under `data/raw/` in place — including `colorado_environmental_data_sources.json`. Read it, write derived data to `data/interim/` or `data/processed/`. A new catalog vintage is a new file, not an in-place edit. Anything derived must be reproducible from raw.
- **Open, version-controllable formats.** Prefer plain text, CSV/Parquet, JSON, Markdown, and text-based pipeline definitions. Do not introduce a vendor-locked artifact as a required dependency; anything a hosted tool produces (Datasette, R2, Quarto) must be exportable.
- **Provenance lives with the data.** Record where data came from, its license, and any transformations in `DATA-DICTIONARY.md` and `decision-log.md`. Every source in the catalog carries `verification_status`; do not silently rely on a `needs_followup` source.
- **Secrets and sensitive data never land in the repo.** Keep credentials out of code and notebooks (`.env` is git-ignored). The planned news corpus introduces copyright (fair-use: metadata + excerpts + archived links, **never** republished full text) and journalist-privacy duties — see the **blocking** items in `ROADMAP.md` before ingesting article text or journalist records.

## Where things are

- Source data and derived outputs: `data/`. Schema: `DATA-DICTIONARY.md`.
- Project design memos (methodology, technical architecture, source-inventory audit, grant proposals): `context/`. Read these before extending the project — the pipeline is already specified there.
- What's planned but not built yet: `ROADMAP.md`.

## How we work

The repository is currently a **documented catalog**, not yet a running pipeline. When you build the L2 pipeline, explore in `exploratory/`, then package reusable code into `src/cejcorpus/` at the exploration boundary (per `context/architecture.md`). Pipelines are code (re-runnable), not cleaned snapshots. Pin environments so others — and other agents — can reproduce results. Stamp every row a stage writes with a `run_id`, and archive every cited URL at coding time.

## A data-integrity note (read before touching the catalog)

Compilation surfaced spurious search content claiming NREL was renamed "National Laboratory of the Rockies" with a `nlr.gov` domain. **This is unverified and almost certainly false.** Keep `nrel.gov` canonical and do not seed any dictionary or catalog field with `nlr.gov` without confirmation against an official DOE/NREL source. See `context/source-inventory.md` for the full caveat.
