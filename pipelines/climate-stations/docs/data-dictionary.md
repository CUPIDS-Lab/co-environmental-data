# Data dictionary — Colorado climate stations (daily)

Two tables: the **observations** deliverable (`data/processed/climate-stations.csv`, tidy long) and the **stations** dimension (`data/lookups/stations.csv`). Join on `site_id`.

## `climate-stations.csv` — observations (grain: one row per `source` × `site_id` × `datetime` × `variable`)

| column | type | description |
|---|---|---|
| `source` | str | Registry slug — always `cdss_climate`. |
| `vintage` | str | Extract snapshot id (`current`); join key to `provenance.csv`. |
| `site_id` | str | CDSS `stationNum` (stable integer id, as string). Join key to `stations.csv`. |
| `site_name` | str | Human-readable station name. |
| `datetime` | date | Observation date (local calendar date; day grain). |
| `variable` | str | One of the 12 measures below. |
| `value` | float | The measurement (nullable; sentinels/impossible negatives → NA). |
| `unit` | str | Per-variable unit (`degF` / `in` / `mJ/m^2` / `kPa` / `KM`); null for `frost_date`. |
| `qa_flag` | str | CDSS `flagA..flagD`, space-joined (nullable). Raw, not decoded. |
| `concept` | str | Cross-source concept key (see `data/lookups/concepts.yaml`). |

### Controlled vocabulary for `variable`

| variable | unit | measType | notes |
|---|---|---|---|
| `temp_max_f` | degF | MaxTemp | **negatives valid** (not nulled) |
| `temp_mean_f` | degF | MeanTemp | definition varies by network ((max+min)/2 vs integrated) |
| `temp_min_f` | degF | MinTemp | **negatives valid** |
| `precip_in` | in | Precip | 0.0 is a real dry day (not missing); trace often coded |
| `snowfall_in` | in | Snow | new snow over the obs-day |
| `snow_depth_in` | in | SnowDepth | depth on ground (≠ SWE) |
| `swe_in` | in | SnowSWE | ⚠️ overlaps SNOTEL / issue #11 |
| `evap_in` | in | Evap | **pan** evaporation (apply pan coefficient) |
| `solar_rad_mj_m2` | mJ/m^2 | Solar | daily **total** (not a flux) |
| `vapor_pressure_kpa` | kPa | VP | actual VP (not VPD) |
| `wind_run_km` | KM | Wind | wind **run** km/day (not speed) |
| `frost_date` | — | FrostDate | ⚠️ semantics unconfirmed; passed through raw |

## `stations.csv` — station dimension (grain: one row per `site_id`)

| column | type | description |
|---|---|---|
| `source` | str | `cdss_climate`. |
| `site_id` | str | CDSS `stationNum`. |
| `site_name` | str | Station name (HTML-cleaned). |
| `network` | str | Observing network / `dataSource`: NOAA · CoCoRaHS · NRCS · CoAgMet · NCWCD. |
| `site_id_network` | str | Network-native id (GHCN `siteId`) — the **#11 SNOTEL/GHCN crosswalk key**. |
| `division` | int | CO water division (1–7). |
| `water_district` | int | CO water district. |
| `county` | str | County. |
| `latitude`,`longitude` | float | Decimal degrees (WGS84). |
| `start_date`,`end_date` | date | Period of record (widest across catalog segments). |
| `notes` | str | Free text. |

## Provenance, license, missingness

- **Provenance:** `data/processed/provenance.csv`, one row per `(source, vintage)` — `source_url`, `retrieved_at`, `sha256` of the immutable original in `data/original/`, parser module, extraction quality.
- **License:** CDSS **"as-is"** (Colorado DWR; no warranty/indemnification). An API key is required in practice (anonymous limits since 2025-12-10).
- **Missing vs zero:** `value` NA = missing/sentinel (`<= -999`) or an impossible negative for a non-negative measure. A genuine `0.0` (dry day, no snow) is preserved. Absence of a date for a station = not operating / not reporting (not zero).
- **Not homogenized:** raw values carry time-of-observation and sensor-change biases and are **not network-equivalent**. See `data/lookups/concepts.yaml` for the per-measure caveats.
