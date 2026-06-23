# Colorado snowpack (SWE)

A tidy, documented, reproducible dataset of **Colorado snowpack** — snow water
equivalent (SWE), snow depth, and water-year precipitation accumulation at NRCS
**SNOTEL** and **snow-course** sites — liberated from the **NRCS AWDB REST API**
into a single long-format CSV. Part of the [Colorado Environmental Data Hub](../../README.md);
implements issue [#11](https://github.com/CUPIDS-Lab/co-environmental-data/issues/11).
Stamped out from the sibling [`streamflow`](../streamflow/) pipeline (#10): same
architecture, different domain.

| source | site_id | site_name | datetime | variable | value | unit | qa_flag |
|---|---|---|---|---|---|---|---|
| nrcs_snotel | 680:CO:SNTL | Park Cone | 2020-02-03 | swe_in | 6.9 | in | V |
| nrcs_snotel | 680:CO:SNTL | Park Cone | 2020-02-03 | snow_depth_in | 30 | in | V |
| nrcs_snotel | 680:CO:SNTL | Park Cone | 2020-02-03 | precip_accum_in | 6.7 | in | E |
| nrcs_snowcourse | 06L02:CO:SNOW | Park Cone | 2020-02-27 | swe_in | 7.4 | in | P |

*(illustrative rows; run the pipeline for live values. Note the last two: the
**same place**, Park Cone, measured two ways — an automated SNOTEL sensor and a
manual snow course nearby. See the co-location caveat below.)*

## What's in it

Daily **SWE / snow depth / water-year precipitation accumulation** for **all
active Colorado SNOTEL stations** (automated telemetry, record since ~1980), plus
semimonthly **SWE / snow depth** for **all active Colorado snow courses** (manual
surveys, many back to the 1930s–40s), each pulled for its **full period of
record**. The committed seed (`data/lookups/sites.csv`) is **199 stations** (118
SNOTEL + 81 snow courses) across every Colorado river basin — full-state coverage,
not a sample. Regenerate or expand it (to discontinued stations, for even deeper
history) with [`scripts/build_sites_seed.py`](scripts/build_sites_seed.py).

The headline product is **basin SWE as a percent of normal** — the number every
Colorado runoff and drought story leads with — computed from the liberated record
in [`audit.basin_percent_normal`](src/snowpack/audit.py).

### ⚠️ The caveats to read first

- **Two networks, NEARBY not identical.** A SNOTEL and a snow course with the same
  name (e.g. Park Cone) sit at roughly the same place but are **distinct sites**
  (different aspect/elevation/exposure) measured on different cadences. They are
  **complementary** — snow courses extend the record decades before SNOTEL — **not
  duplicate**. `audit.reconcile_cross_source` treats their agreement as a *looser*
  sanity check, never an identity (contrast streamflow's USGS↔DWR re-serve).
- **Missing ≠ zero.** Absence of a value means the site wasn't reporting, not "no
  snow." Off-season SWE is a real 0; a gap is NA. Impossible negatives (AWDB
  missing sentinels) are mapped to NA, never zero-filled.
- **`precip_accum_in` is water-year cumulative** (resets to 0 each Oct 1) — it is a
  running total, not a daily increment.
- **Temperature is out of scope here** and SNOTEL has a *documented extended-range
  temperature-sensor bias*; if you add the declared `air_temp_obs_f`, read the
  caveat in `data/lookups/concepts.yaml` first.

Full caveats in [`data/lookups/concepts.yaml`](data/lookups/concepts.yaml).

## Movement context

This follows the civic data-liberation tradition (Sunlight → PDF Liberation →
PUDL → BoulderPublicData): immutable originals, per-source parsers, a harmonized
canonical schema with documented caveats, and reconciliation against independent
truth. Open data ≠ information justice — see the *out-of-scope uses* note in
[`AGENTS.md`](AGENTS.md).

## How to run

```bash
cd pipelines/snowpack
uv sync                      # create the pinned environment
uv run pytest                # verify the scaffold (offline)
uv run jupyter lab           # then run notebooks/snowpack-pipeline.ipynb top to bottom
```

The pipeline runs four stages (retrieve → audit → cleanup → publish). The headless
twin:

```bash
# Sample: a handful of stations, both networks, full history each (fast)
uv run python -m snowpack.pipeline --mode live --fresh \
    --sites 680:CO:SNTL,06L02:CO:SNOW,713:CO:SNTL

# Full dataset: all 199 stations × full POR (larger/slower)
uv run python -m snowpack.pipeline --mode live --fresh

# Offline smoke test (no network; seeds one SNOTEL station from a fixture)
uv run python -m snowpack.pipeline --mode demo --fresh
```

`--sites` is the sampling hook (comma-separated station triplets **or** bare ids);
`--sources` restricts to `nrcs_snotel` or `nrcs_snowcourse`. The CLI exits
non-zero on a regression (zero rows / empty retrieval / reconcile mismatch), which
is what the scheduled monthly refresh keys off — see [`.github/workflows`](../../.github/workflows/README.md).

## How to load (consumers)

```python
import pandas as pd
df = pd.read_csv("data/processed/snowpack.csv", parse_dates=["datetime"])
# SNOTEL SWE only (the daily automated series):
swe = df[(df.source == "nrcs_snotel") & (df.variable == "swe_in")]
```
```r
df <- readr::read_csv("data/processed/snowpack.csv")
```
Wide views & a basin-% -of-normal recipe: `docs/filter-pivot-recipes.md`. Full
schema: `docs/data-dictionary.md`.

## Schema overview

Tidy long, one row per `(source, site_id, datetime, variable)`. Columns:
`source, vintage, site_id, site_name, datetime, variable, value, unit, qa_flag,
concept`. Populated `variable`s: `swe_in`, `snow_depth_in`, `precip_accum_in` (all
inches). `snow_density_pct` and `air_temp_obs_f` are declared for extensibility.
See `docs/data-dictionary.md`.

## Provenance & refresh

Per-extract sidecar at `data/processed/provenance.csv` (`source_url`,
`retrieved_at`, `sha256`, license, parser). Recent SNOTEL values are provisional
(`qaFlag=P`) and may be revised; the pipeline is re-runnable and idempotent.
Originals in `data/original/` are immutable (sha256 manifest). The dataset is
**rebuilt and re-audited monthly** by [`.github/workflows/monthly-data-refresh.yml`](../../.github/workflows/README.md).

## Archive & DOI (Dataverse)

The processed dataset, the pipeline code, and the docs can be deposited to
**Harvard Dataverse** for a citable DOI. The deposit kit is in [`dataverse/`](dataverse/DEPOSIT.md)
(`dataset.json` + `deposit-dataverse.sh` / `deposit_dataverse.py`); it creates a
**draft** and only publishes on explicit confirmation. Validate it offline with
`DRY_RUN=1 python dataverse/deposit_dataverse.py --no-publish`.

## License

- **Code:** MIT.
- **Data:** NRCS AWDB (SNOTEL + snow courses) is public domain (U.S. federal); the
  harmonized dataset is released CC-BY-4.0. Per-source license is recorded in
  `provenance.csv`.

## Citation

> Keegan, B. et al. *Colorado Snowpack (SWE)* (Colorado Environmental Data Hub),
> CUPIDS Lab, 2026. https://github.com/CUPIDS-Lab/co-environmental-data
