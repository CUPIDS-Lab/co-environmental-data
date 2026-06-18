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
uv run pytest                # verify the scaffold (schema + parser fixture)
uv run jupyter lab           # then run notebooks nb-01 → nb-04 in order
```

The four notebooks map to the four stages:

1. `nb-01-retrieve` — fetch raw responses → immutable `data/original/` + manifest.
2. `nb-02-audit` — profile the retrieval (did we get data? shapes? counts?).
3. `nb-03-cleanup` — parse → tidy long → validate → `data/processed/*.csv`.
4. `nb-04-publish-csv` — finalize the CSV deliverable + audit summary + reconcile.

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
immutable (sha256 manifest).

## License

- **Code:** MIT.
- **Data:** the upstream sources are public domain (USGS/Reclamation) or public
  "as-is" (Colorado DWR) / public-verify (Northern Water); the harmonized dataset
  is released CC-BY-4.0. Per-source license is recorded in `provenance.csv`.

## Citation

> Keegan, B. et al. *Colorado Reservoir Storage* (Colorado Environmental Data Hub),
> CUPIDS Lab, 2026. https://github.com/CUPIDS-Lab/co-environmental-data
