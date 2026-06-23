# Colorado climate stations (daily)

A tidy, documented, reproducible dataset of **Colorado daily climate-station observations** — temperature (max / mean / min), precipitation, snowfall / snow depth / snow water equivalent, pan evaporation, solar radiation, vapor pressure, and wind run — liberated from the **CO DWR / CDSS** Climate Station Time Series (day) API into a single long-format CSV. Part of the [Colorado Environmental Data Hub](../../README.md); implements issue [#44](https://github.com/CUPIDS-Lab/co-environmental-data/issues/44). Stamped out from the sibling [`streamflow`](../streamflow/) pipeline (#10): same architecture, different domain — one API serving many networks and **twelve** measures rather than two sources and one variable.

| source | site_id | site_name | datetime | variable | value | unit | qa_flag |
|---|---|---|---|---|---|---|---|
| cdss_climate | 3 | BUCKHORN MTN 1 E | 2024-06-01 | precip_in | 0.00 | in | 0 1700 |
| cdss_climate | 1886 | CENTER, CSU SLV EXPT STA | 2024-06-01 | solar_rad_mj_m2 | 27.45 | mJ/m^2 | |
| cdss_climate | 1886 | CENTER, CSU SLV EXPT STA | 2024-01-09 | temp_min_f | -6.74 | degF | |

*(illustrative rows; run the pipeline for live values. Note the three different units — harmonization is **per concept**, not global.)*

## What's in it

Daily observations across **twelve measurement types** for a curated, **active** cross-section of Colorado climate stations — eight from each of the five observing networks the CDSS climate API federates (**NOAA** COOP/GHCN, **CoCoRaHS** citizen observers, **NRCS**/SNOTEL, **CoAgMet** agricultural mesonet, **NCWCD** Northern Water) — each pulled for its **full period of record**.

| measType | variable | unit |
|---|---|---|
| MaxTemp / MeanTemp / MinTemp | `temp_max_f` / `temp_mean_f` / `temp_min_f` | degF |
| Precip | `precip_in` | in |
| Snow / SnowDepth / SnowSWE | `snowfall_in` / `snow_depth_in` / `swe_in` | in |
| Evap | `evap_in` | in |
| Solar | `solar_rad_mj_m2` | mJ/m^2 |
| VP | `vapor_pressure_kpa` | kPa |
| Wind | `wind_run_km` | KM (wind run/day) |
| FrostDate | `frost_date` | *(unconfirmed — see caveats)* |

The committed seed (`data/lookups/stations.csv`) is a **40-station** cross-section (`build_stations_seed.py`). It is **expandable to "all active CO climate stations"** — `python scripts/build_stations_seed.py --all` — a station-filter change, not a refactor. The CDSS catalog holds **12,704 records → 4,962 distinct stations** (multiple period-of-record segments per `stationNum`).

### ⚠️ The caveats to read first

- **Many networks, one schema.** The same measType from NOAA COOP, CoCoRaHS, CoAgMet, and SNOTEL is **not** instrument-, siting-, or QA-equivalent. Each station's `network` is in `stations.csv`; stratify by it before comparing. Manual COOP/CoCoRaHS days are observer-clock days (not midnight-aligned); temps carry time-of-observation bias; precip gauges undercatch snow.
- **`SnowSWE` overlaps snowpack issue [#11](https://github.com/CUPIDS-Lab/co-environmental-data/issues/11).** SWE here is chiefly NRCS/**SNOTEL** — the same physical sites #11 pulls from the NRCS AWDB API. Crosswalk on `site_id_network` and de-duplicate; do not treat the two as independent. (The climate analogue of DWR re-serving USGS in the streamflow pipeline.)
- **Units differ by measure** (degF / in / mJ/m^2 / kPa / KM) — harmonize per concept. `wind_run_km` is **wind run** (km/day), not speed; `solar_rad_mj_m2` is a **daily total** (MJ/m²/day), not a flux; `evap_in` is **pan** evaporation (apply a pan coefficient for open water).

Full caveats per measure: [`data/lookups/concepts.yaml`](data/lookups/concepts.yaml).

## Movement context

This follows the civic data-liberation tradition (Sunlight → PDF Liberation → PUDL → BoulderPublicData): immutable originals, a per-source parser, a harmonized canonical schema with documented caveats, and reconciliation against truth. Open data ≠ information justice — see the *out-of-scope uses* note in `AGENTS.md`.

## How to run

```bash
cd pipelines/climate-stations
uv sync                      # create the pinned environment
uv run pytest                # verify the scaffold (offline, no network)
uv run jupyter lab           # then run notebooks/climate-stations-pipeline.ipynb top to bottom
```

The pipeline runs four stages (retrieve → audit → cleanup → publish). The headless twin:

```bash
# Sample: a few stations, water-relevant measures, full history each (fast)
uv run python -m climate_stations.pipeline --mode live --fresh \
    --sites 3,1886,10419 --meas-types Precip,SnowSWE,MaxTemp

# Full curated seed: all 40 stations × all 12 measTypes, full POR (larger/slower)
uv run python -m climate_stations.pipeline --mode live --fresh

# Offline smoke test (no network; seeds one station from a fixture)
uv run python -m climate_stations.pipeline --mode demo --fresh
```

`--sites` is the sampling hook (comma-separated `site_id` = CDSS `stationNum`); `--meas-types` restricts the measTypes pulled. A **CDSS API key is required in practice** — anonymous daily/row limits took effect 2025-12-10 (a keyless pull returns `"Error: Exceeded Daily Data Limit"`). Put `{"CDSS_API_KEY": "..."}` in a git-ignored `dwr_api.json` at the pipeline root, or set `$CDSS_API_KEY`. The CLI exits non-zero on a regression (zero rows / empty retrieval / reconcile mismatch).

## How to load (consumers)

```python
import pandas as pd
df = pd.read_csv("data/processed/climate-stations.csv", parse_dates=["datetime"],
                 dtype={"site_id": str})
# one measure, wide over stations:
swe = df[df.variable == "swe_in"].pivot_table(index="datetime", columns="site_id", values="value")
# join the station dimension (network, lat/lon, POR):
stations = pd.read_csv("data/lookups/stations.csv", dtype={"site_id": str})
df = df.merge(stations[["site_id", "network", "latitude", "longitude"]], on="site_id", how="left")
```

## Roadmap (not in this build)

- **Datasette + Dataverse publication** — declared in `pyproject.toml [publish]`, wired by the sibling pipelines' workflow pattern; not yet wired here.
- **Provisional QA decoding** — `flagA..flagD` are preserved verbatim; a per-network flag dictionary (approved/estimated/filled) is future work.
- **SNOTEL crosswalk table** — `audit.network_summary` flags the NRCS overlap with #11; an explicit site crosswalk is future work.
