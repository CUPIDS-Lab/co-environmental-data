# Depositing Colorado Daily Climate Stations to Dataverse

This dataset can be archived in a [Dataverse](https://dataverse.org) repository (default: `https://dataverse.harvard.edu`) for a **citable DOI**. This guide and the two scripts beside it (`deposit-dataverse.sh`, `deposit_dataverse.py`) deposit from `dataset.json`. The kit was generated from the CUPIDS Lab `data-project` skill (Harvard Dataverse deposit, L5) and mirrors the sibling `snowpack`/`streamflow` kits.

## What gets deposited

| From the pipeline | Uploaded as category | Folder in the dataset |
| --- | --- | --- |
| `data/processed/` (`climate-stations.csv`, `provenance.csv`) | **Data** | `data/processed` |
| `src/climate_stations/` · `notebooks/` (the re-runnable pipeline) | **Code** | `code` |
| `README.md`, `AGENTS.md`, `docs/` (data dictionary, recipes, survey notes) | **Documentation** | `documentation` |
| `data/lookups/` (`stations.csv` station metadata — name, lat/long, elevation, county, period of record; plus `sources.yaml`, `concepts.yaml`) | **Documentation** | `data/lookups` |
| title · author · contact · description · subject · keywords | citation metadata | — |

`data/original/` (the immutable raw cache) is **not** uploaded — the deliverable is the regenerable `data/processed` output plus the pipeline. Subject: **Earth and Environmental Sciences**; data license **CC BY 4.0** (code is MIT).

> **Keep the per-measType + overlap caveats in the deposited metadata.** Units are harmonized **per measurement type** (degF / in / mJ/m² / kPa / km), not globally; and `SnowSWE`/`SnowDepth` overlap NRCS SNOTEL (build the site crosswalk before treating them as independent). This is stated in `dataset.json` and documented fully in `data/lookups/concepts.yaml` and the data dictionary.

## Configure the target

1. **Get an API token** on `https://dataverse.harvard.edu` (account menu → API Token); pass it via `DATAVERSE_API_TOKEN`, never commit it.
2. **Set the collection.** `DATAVERSE_COLLECTION` must be an existing, published collection alias your account can create datasets in (the scripts default to `cupids-lab` as a placeholder — confirm the real alias).
3. **Test on the demo server first:** `DATAVERSE_URL=https://demo.dataverse.org DATAVERSE_API_TOKEN=xxxx ./deposit-dataverse.sh`.

> Run the pipeline first so `data/processed/*.csv` exists. The CDSS API needs a key (`CDSS_API_KEY` or the git-ignored `dwr_api.json`): `CDSS_API_KEY=xxxx uv run python -m climate_stations.pipeline --mode live --fresh`.

## Deposit it

```bash
# curl, zero dependencies:
DATAVERSE_API_TOKEN=xxxx ./deposit-dataverse.sh
# or the official Python client:
uv pip install pyDataverse && DATAVERSE_API_TOKEN=xxxx python deposit_dataverse.py
```

Each creates a **draft**, uploads the files above, writes `.dataverse-deposit.json`, then **asks before publishing**. Add `DRY_RUN=1` to validate the manifest and preview actions without writing anything (this is what CI runs every refresh).

## Draft → review → publish

A run stops at a **draft** and offers to publish — **review it in the web UI first**; publishing mints the DOI and is effectively permanent. Publish via the prompt or later with `./deposit-dataverse.sh --publish`. Before publishing, confirm the audit checks passed and the per-measType units/overlap caveats are present. After publishing, record the DOI in the pipeline `README.md` and the repo `CHANGELOG.md`.

## Monthly refresh & versioning

The monthly CI (`.github/workflows/monthly-data-refresh.yml`) **validates this kit every run** (`DRY_RUN=1`) and, when the `DATAVERSE_*` secrets are configured, uploads the freshly rebuilt `data/processed` to a **draft** — it never publishes a DOI unattended. Recurring deposits update the **existing** dataset (a new version), not a new DOI.
