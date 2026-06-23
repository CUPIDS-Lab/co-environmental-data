# Depositing Colorado Stream/River Flow to Dataverse

This dataset can be archived in a [Dataverse](https://dataverse.org) repository (default: `https://dataverse.harvard.edu`) to get a **citable DOI** and make its data, code, and documentation findable and reusable (the *Findable* + *Accessible* in FAIR). This guide and the two scripts beside it (`deposit-dataverse.sh`, `deposit_dataverse.py`) deposit from `dataset.json` — the citation-metadata manifest for this pipeline. The kit was generated from the CUPIDS Lab `data-project` skill (Harvard Dataverse deposit, L5) and mirrors the sibling `reservoir-storage` kit.

## What gets deposited

| From the pipeline | Uploaded as category | Folder in the dataset |
| --- | --- | --- |
| `data/processed/` (`streamflow.csv`, `provenance.csv`) | **Data** | `data/processed` |
| `src/streamflow/` · `notebooks/` (the re-runnable pipeline) | **Code** | `code` |
| `README.md`, `AGENTS.md`, `docs/` (data dictionary, recipes, survey notes) | **Documentation** | `documentation` |
| `data/lookups/` (`sites.csv` station metadata — name, lat/long, elevation, county, period of record; plus `sources.yaml`, `concepts.yaml`) | **Documentation** | `data/lookups` |
| title · author · contact · description · subject · keywords | citation metadata | — |

`data/original/` (the immutable raw cache) is **not** uploaded — the deliverable is the regenerable `data/processed` output plus the pipeline. The dataset's subject is **Earth and Environmental Sciences**; the data license is **CC BY 4.0** (code is MIT). Edit `dataset.json` to add authors, keywords, related publications, or a different subject (from Dataverse's controlled list).

> **Note the source overlap in the dataset description.** Because DWR re-serves many USGS gages, downstream users must de-duplicate to one series per gage (USGS = system of record). This is stated in `dataset.json`'s description and documented fully in `data/lookups/concepts.yaml` and the data dictionary — keep that caveat in the deposited metadata.

## Configure the target

1. **Get an API token.** Log in to `https://dataverse.harvard.edu` → account menu → **API Token** → Create. Treat it like a password; pass it via the environment (`DATAVERSE_API_TOKEN`), never commit it.
2. **Set the collection.** `DATAVERSE_COLLECTION` must be an existing, **published** collection alias your account can create datasets in. The scripts default to `cupids-lab` as a **placeholder** — confirm the real alias and set `DATAVERSE_COLLECTION` (or a repo Actions variable) accordingly.
3. **Test on the demo server first** (free, throwaway DOIs):

   ```bash
   DATAVERSE_URL=https://demo.dataverse.org DATAVERSE_API_TOKEN=xxxx ./deposit-dataverse.sh
   ```

> Run the pipeline first so `data/processed/*.csv` exists. For a clean **full** DWR pull, set `CDSS_API_KEY` (avoids the CDSS 403 throttle — see `AGENTS.md`): `CDSS_API_KEY=xxxx uv run python -m streamflow.pipeline --mode live --fresh`.

## Deposit it

Either client works — they do the same three Native-API calls (create draft → upload files → publish):

```bash
# curl, zero dependencies:
DATAVERSE_API_TOKEN=xxxx ./deposit-dataverse.sh

# or the official Python client (richer validation):
uv pip install pyDataverse            # or: pip install pyDataverse
DATAVERSE_API_TOKEN=xxxx python deposit_dataverse.py
```

Each creates a **draft**, uploads the files above, writes `.dataverse-deposit.json` (the record used to avoid duplicate deposits on re-runs), then **asks before publishing**. Add `DRY_RUN=1` to validate the manifest and preview the actions without writing anything (this is what CI runs every refresh).

## Draft → review → publish

A deposit run stops at a **draft** and offers to publish. **Review the draft in the web UI first** — publishing mints the DOI and is effectively permanent. Publish when ready by answering the prompt, or later with `./deposit-dataverse.sh --publish` (`--no-publish` to never publish). Before publishing, confirm the license (CC BY 4.0) and that the audit + **cross-source reconciliation** checks passed (`data/audit/reconcile-cross-source.json` — agreement should be ~100 % on shared gages).

After publishing, record the DOI in the pipeline `README.md` and the repo `CHANGELOG.md`, and verify the record — e.g. `curl "https://dataverse.harvard.edu/api/datasets/:persistentId?persistentId=<doi>"`.

## Monthly refresh & versioning

The monthly CI (`.github/workflows/monthly-data-refresh.yml`) **validates this kit on every run** (`DRY_RUN=1`) and, when the `DATAVERSE_*` secrets are configured, uploads the freshly rebuilt `data/processed` to a **draft** — it never publishes a DOI unattended. Recurring deposits should update the **existing** dataset (a new version) rather than mint a new DOI each month: the first deposit creates the dataset (a human reviews and publishes v1.0), and subsequent updates target that dataset's persistent id (recorded in `.dataverse-deposit.json` / set as `DATAVERSE_DATASET_DOI`), replacing the data files and publishing a minor version on review.
