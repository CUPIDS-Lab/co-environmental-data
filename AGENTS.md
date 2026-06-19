# AGENTS.md — guidance for agents and humans working in this repo

Read this first. It states the non-negotiables and points you at the right place for each task. This repo was scaffolded with the CUPIDS Lab `data-project` skill at level **L1**.

## Non-negotiables

- **Raw data is immutable.** Never edit anything under `data/raw/` in place — including `colorado_environmental_data_sources.json`. Read it, write derived data to `data/interim/` or `data/processed/`. A new catalog vintage is a new file, not an in-place edit. Anything derived must be reproducible from raw.
- **Open, version-controllable formats.** Prefer plain text, CSV/Parquet, JSON, Markdown, and text-based pipeline definitions. Do not introduce a vendor-locked artifact as a required dependency; anything a hosted tool produces (Datasette, R2, Quarto) must be exportable.
- **Provenance lives with the data.** Record where data came from, its license, and any transformations in `DATA-DICTIONARY.md` and `decision-log.md`. Every source in the catalog carries `verification_status`; do not silently rely on a `needs_followup` source.
- **Secrets and sensitive data never land in the repo.** Keep credentials out of code and notebooks (`.env` is git-ignored). The planned news corpus introduces copyright (fair-use: metadata + excerpts + archived links, **never** republished full text) and journalist-privacy duties — see the **blocking** items in `ROADMAP.md` before ingesting article text or journalist records.

## Where things are

- Source data and derived outputs: `data/`. Schema: `DATA-DICTIONARY.md`.
- Project design memos (methodology, technical architecture, source-inventory audit, grant proposals): `context/`. Read these before extending the project — the corpus pipeline is already specified there.
- **Data-liberation pipelines:** `pipelines/<name>/` — one self-contained pipeline per liberated dataset, each with its own `AGENTS.md`. The first, `pipelines/reservoir-storage/` ([#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9)), is built; **read its `AGENTS.md` before touching it.**
- What's planned but not built yet: `ROADMAP.md`.

## How we work

The repository is a **documented catalog** plus a growing set of **data-liberation pipelines** under `pipelines/<name>/` (the first — reservoir-storage, #9 — is built and live against the DWR/CDSS and Reclamation RISE APIs). Each pipeline is thin notebooks over a tested `src/<pkg>/` package: explore, then package reusable code at the exploration boundary. The journalist→citation **corpus** pipeline (`context/architecture.md`) is still to be built (the `cejcorpus` package, notebooks `nb-00…09`). Pipelines are code (re-runnable), not cleaned snapshots. Pin environments so others — and other agents — can reproduce results. Stamp every row a stage writes with a `run_id`, and archive every cited URL at coding time.

## A data-integrity note (read before touching the catalog)

Compilation surfaced spurious search content claiming NREL was renamed "National Laboratory of the Rockies" with a `nlr.gov` domain. **This is unverified and almost certainly false.** Keep `nrel.gov` canonical and do not seed any dictionary or catalog field with `nlr.gov` without confirmation against an official DOE/NREL source. See `context/source-inventory.md` for the full caveat.
