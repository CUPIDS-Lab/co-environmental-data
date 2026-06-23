# Colorado stream/river flow

A tidy, documented, reproducible dataset of **Colorado streamflow** — daily mean discharge (cubic feet per second) at major-river gages — liberated from two public sources (**USGS NWIS** and **CO DWR/CDSS surface water**) into a single long-format CSV. Part of the [Colorado Environmental Data Hub](../../README.md); implements issue [#10](https://github.com/CUPIDS-Lab/co-environmental-data/issues/10). Stamped out from the sibling [`reservoir-storage`](../reservoir-storage/) pipeline (#9): same architecture, different domain.

| source | site_id | site_name | datetime | variable | value | unit | qa_flag |
|---|---|---|---|---|---|---|---|
| usgs_nwis | 09095500 | COLORADO RIVER NEAR CAMEO, CO. | 2024-06-03 | discharge_cfs | 12400 | cfs | A |
| usgs_nwis | 09152500 | GUNNISON RIVER NEAR GRAND JUNCTION | 2024-06-03 | discharge_cfs | 6230 | cfs | A |
| dwr_cdss | COLCAMCO | COLORADO RIVER NEAR CAMEO, CO. | 2024-06-03 | discharge_cfs | 12400 | cfs | A |
| usgs_nwis | 08220000 | RIO GRANDE NEAR DEL NORTE, CO | 2024-06-03 | discharge_cfs | 1840 | cfs | A |

*(illustrative rows; run the pipeline for live values. Note rows 1 and 3: the **same gage**, same value, two sources — DWR re-serves USGS. See the overlap caveat below.)*

## What's in it

Daily **mean** discharge for **33 curated major-river gages** across all eight of Colorado's major basins (Colorado, Gunnison, Dolores/San Miguel, San Juan, White, Yampa/Green, Rio Grande, South Platte, Arkansas), each pulled for its **full period of record** (some back to 1900; some discontinued mid-century).

The committed seed (`data/lookups/sites.csv`) is the full **33 USGS gages + their 33 DWR mirrors** (66 rows), resolved via the CDSS `usgsSiteId` cross-link using the configured API key (`dwr_api.json`; a *keyless* full pull trips the CDSS throttle noted below). Regenerate or refresh it with [`scripts/build_sites_seed.py`](scripts/build_sites_seed.py). The seed is also **expandable** to "all active CO discharge gages" — a station-filter change, not a refactor (see `streamflow.stations`).

### ⚠️ The one caveat to read first: the two sources overlap

Unlike the reservoir pipeline's disjoint sources, **DWR surface water frequently re-serves the USGS gage** — its `dataSource` is literally `USGS`. The same physical gage therefore appears once under `usgs_nwis` (keyed by site number) and once under `dwr_cdss` (keyed by abbrev), joined by `usgs_site_no` in `sites.csv`. They are **not independent measurements** — do not average or sum them; de-duplicate to one series per gage for analysis. This is also a feature: `audit.reconcile_cross_source` uses the overlap as an automatic accuracy check (the two should agree on shared dates). Full caveats in `data/lookups/concepts.yaml`.

## Movement context

This follows the civic data-liberation tradition (Sunlight → PDF Liberation → PUDL → BoulderPublicData): immutable originals, per-source parsers, a harmonized canonical schema with documented caveats, and reconciliation against independent truth. Open data ≠ information justice — see the *out-of-scope uses* note in `AGENTS.md`.

## How to run

```bash
cd pipelines/streamflow
uv sync                      # create the pinned environment
uv run pytest                # verify the scaffold (19 tests, offline)
uv run jupyter lab           # then run notebooks/streamflow-pipeline.ipynb top to bottom
```

The pipeline runs four stages (retrieve → audit → cleanup → publish). The headless twin:

```bash
# Sample: a handful of gages, both sources, full history each (fast)
uv run python -m streamflow.pipeline --mode live --fresh \
    --sites 09095500,09152500,08220000,06714000,07091200

# Full dataset: all 33 curated gages × both sources, full POR (larger/slower)
uv run python -m streamflow.pipeline --mode live --fresh

# Offline smoke test (no network; seeds one gage from a fixture)
uv run python -m streamflow.pipeline --mode demo --fresh
```

`--sites` is the sampling hook (comma-separated `site_id`s); `--sources` restricts to `usgs_nwis` or `dwr_cdss`. The CLI exits non-zero on a regression (zero rows / empty retrieval / reconcile mismatch), which is what the scheduled monthly refresh keys off — see [`.github/workflows`](../../.github/workflows/README.md).

## How to load (consumers)

```python
import pandas as pd
df = pd.read_csv("data/processed/streamflow.csv", parse_dates=["datetime"])
# one series per gage (drop the DWR re-serve of USGS):
usgs = df[df.source == "usgs_nwis"]
```
```r
df <- readr::read_csv("data/processed/streamflow.csv")
```
Wide views: `docs/filter-pivot-recipes.md`. Full schema: `docs/data-dictionary.md`.

## Schema overview

Tidy long, one row per `(source, site_id, datetime, variable)`. Columns: `source, vintage, site_id, site_name, datetime, variable, value, unit, qa_flag, concept`. The only `variable` populated in this build is `discharge_cfs` (cfs); `gage_height_ft` is declared for extensibility. See `docs/data-dictionary.md`.

## Provenance & refresh

Per-extract sidecar at `data/processed/provenance.csv` (`source_url`, `retrieved_at`, `sha256`, license, parser). USGS approves values on a lag (recent data is provisional); the pipeline is re-runnable and idempotent. Originals in `data/original/` are immutable (sha256 manifest). The dataset is **rebuilt and re-audited monthly** by [`.github/workflows/monthly-data-refresh.yml`](../../.github/workflows/README.md).

## Archive & DOI (Dataverse)

The processed dataset, the pipeline code, and the docs can be deposited to **Harvard Dataverse** for a citable DOI. The deposit kit is in [`dataverse/`](dataverse/DEPOSIT.md) (`dataset.json` + `deposit-dataverse.sh` / `deposit_dataverse.py`); it creates a **draft** and only publishes on explicit confirmation. Validate it offline with `DRY_RUN=1 python dataverse/deposit_dataverse.py --no-publish`.

## License

- **Code:** MIT.
- **Data:** USGS NWIS is public domain (U.S. federal); Colorado DWR is public "as-is"; the harmonized dataset is released CC-BY-4.0. Per-source license is recorded in `provenance.csv`.

## Citation

> Keegan, B. et al. *Colorado Stream/River Flow* (Colorado Environmental Data Hub), CUPIDS Lab, 2026. https://github.com/CUPIDS-Lab/co-environmental-data
