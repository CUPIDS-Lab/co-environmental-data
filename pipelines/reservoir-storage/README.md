# Colorado reservoir storage

A tidy, documented, reproducible dataset of **Colorado reservoir storage** —
volume, pool elevation, and releases — liberated from three public APIs
(CO DWR/CDSS, USBR Reclamation RISE, Northern Water) into a single long-format
CSV. Part of the [Colorado Environmental Data Hub](../../README.md); implements
issue [#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9).

| source | reservoir_name | datetime | variable | value | unit | qa_flag |
|---|---|---|---|---|---|---|
| dwr_cdss | Green Mountain Reservoir | 2026-06-17 | storage_af | 138214 | acre-ft | Approved |
| dwr_cdss | Green Mountain Reservoir | 2026-06-17 | elevation_ft | 7942.1 | ft | Approved |
| reclamation_rise | Blue Mesa Reservoir | 2026-06-17 | storage_af | 561800 | acre-ft | |
| reclamation_rise | Blue Mesa Reservoir | 2026-06-17 | release_cfs | 1050 | cfs | |
| northern_water | Carter Lake | 2026-06-17 | storage_af | 108900 | acre-ft | |

*(illustrative rows; run the pipeline for live values.)*

## Movement context

This follows the civic data-liberation tradition (Sunlight → PDF Liberation →
PUDL → BoulderPublicData): immutable originals, per-vintage parsers, a harmonized
canonical schema with documented caveats, and reconciliation against the source's
own published totals. Open data ≠ information justice — see the *out-of-scope
uses* note in `AGENTS.md`.

## How to run

```bash
cd pipelines/reservoir-storage
uv sync                      # create the pinned environment
uv run pytest                # verify the scaffold (30 tests, offline)
uv run jupyter lab           # then run notebooks/reservoir-pipeline.ipynb top to bottom
```

`notebooks/reservoir-pipeline.ipynb` runs the four stages in one notebook:

1. **Retrieve** — fetch raw responses → immutable `data/original/` + manifest.
2. **Audit** — profile the retrieval (did we get data? shapes? counts?).
3. **Cleanup** — parse → tidy long → validate → `data/processed/*.csv`.
4. **Publish** — finalize the CSV deliverable + audit summary + reconcile.

The retrieve cell has a small config block: **`MODE`** (`"live"` = fetch from the
APIs / `"demo"` = offline 1-reservoir sample), **`FRESH`** (`True` clears the
`data/original/` cache first so the CSV reflects exactly that run), and **`SOURCES`**
(split the fast DWR pull from the large RISE one). For the **full dataset**, run with
`MODE="live"`, `FRESH=True` — it pulls full history for all 118 DWR + RISE reservoirs
(large/slow; progress streams). DWR/CDSS and RISE return data; Northern Water is
boundaries-only (its C-BT reservoirs come from RISE).

### Headless / CI

The notebook's automatable twin runs the same four stages without Jupyter:

```bash
uv run python -m reservoir.pipeline --mode live --fresh   # full rebuild
uv run python -m reservoir.pipeline --mode demo --fresh   # offline smoke test
```

It exits non-zero on a regression (zero rows / empty retrieval / reconcile
mismatch), which is what the scheduled monthly refresh keys off — see
[`.github/workflows`](../../.github/workflows/README.md).

## How to load (consumers)

```python
import pandas as pd
df = pd.read_csv("data/processed/reservoir-storage.csv", parse_dates=["datetime"])
```
```r
df <- readr::read_csv("data/processed/reservoir-storage.csv")
```
Wide views: `docs/filter-pivot-recipes.md`. Full schema: `docs/data-dictionary.md`.

## Schema overview

Tidy long, one row per `(source, reservoir_id, datetime, variable)`. Columns:
`source, vintage, reservoir_id, reservoir_name, datetime, variable, value, unit,
qa_flag, concept`. See `docs/data-dictionary.md`.

## Provenance & refresh

Per-extract sidecar at `data/processed/provenance.csv` (`source_url`,
`retrieved_at`, `sha256`, license, parser). Sources update daily (telemetry); the
pipeline is re-runnable and idempotent. Originals in `data/original/` are
immutable (sha256 manifest). The dataset is **rebuilt and re-audited monthly** by
[`.github/workflows/monthly-data-refresh.yml`](../../.github/workflows/README.md).

## Archive & DOI (Dataverse)

The processed dataset, the pipeline code, and the docs can be deposited to
**Harvard Dataverse** for a citable DOI. The deposit kit is in
[`dataverse/`](dataverse/DEPOSIT.md) (`dataset.json` + `deposit-dataverse.sh` /
`deposit_dataverse.py`); it creates a **draft** and only publishes on explicit
confirmation. Validate it offline with
`DRY_RUN=1 python dataverse/deposit_dataverse.py --no-publish`. The monthly
workflow validates the kit every run and can deposit a draft when opted in — see
`dataverse/DEPOSIT.md`.

## License

- **Code:** MIT.
- **Data:** the upstream sources are public domain (USGS/Reclamation) or public
  "as-is" (Colorado DWR) / public-verify (Northern Water); the harmonized dataset
  is released CC-BY-4.0. Per-source license is recorded in `provenance.csv`.

## Citation

> Keegan, B. et al. *Colorado Reservoir Storage* (Colorado Environmental Data Hub),
> CUPIDS Lab, 2026. https://github.com/CUPIDS-Lab/co-environmental-data
