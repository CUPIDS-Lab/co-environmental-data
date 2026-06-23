# Survey notes — CO DWR/CDSS climate daily

What was confirmed against the **live** API on **2026-06-22** (the evidence behind the `✅ CONFIRMED` markers in `data/lookups/sources.yaml`). Re-confirm on any contract change.

## Endpoint & request contract

- **Data:** `GET https://dwr.state.co.us/Rest/GET/api/v2/climatedata/climatestationtsday/`
- **Catalog:** `GET …/climatedata/climatestations/`
- **MeasType reference:** `…/referencetables/climatestationmeastype/` → 12 values.

Request params (daily): `format=json`, **`stationNum=<int>`** *or* `siteId=<id>` (**required** — a measType-only query returns `Error: (stationNum or siteId) required for this search`), `measType=<one>`, **`min-measDate`/`max-measDate`** in `MM/DD/YYYY` (NOT `startDate`), `pageSize=<n>`, `apiKey=<key>`. One measType per request; the full period of record for a (station, measType) fits one page.

Row fields: `{stationNum, siteId, measType, measDate (ISO + tz offset), value, flagA, flagB, flagC, flagD, dataSource, modified, measUnit}`.

## The 12 measTypes and their units (confirmed)

| measType | canonical variable | unit | confirmed via |
|---|---|---|---|
| MaxTemp | `temp_max_f` | `degF` | NOAA st#3 |
| MeanTemp | `temp_mean_f` | `degF` | CoAgMet st#1886 |
| MinTemp | `temp_min_f` | `degF` | NOAA st#3 (sub-zero seen at st#1886) |
| Precip | `precip_in` | `in` | NOAA st#3 |
| Snow | `snowfall_in` | `in` | NOAA st#3 |
| SnowDepth | `snow_depth_in` | `in` | NRCS st#10419 |
| SnowSWE | `swe_in` | `in` | NRCS st#10419 (APISHAPA) |
| Evap | `evap_in` | `in` | NOAA st#30 (CLIMAX) |
| Solar | `solar_rad_mj_m2` | `mJ/m^2` | CoAgMet st#1886 |
| VP | `vapor_pressure_kpa` | `kPa` | CoAgMet st#1886 |
| Wind | `wind_run_km` | `KM` (run/day) | CoAgMet st#1886 |
| FrostDate | `frost_date` | **unconfirmed** | no rows in sampled stations |

Units **differ by measure** → harmonize per concept (`schema.MEAS_MAP`), not globally. The parser carries the source-reported `measUnit` (identical to canonical for every sampled measType).

## Station universe

- Catalog returns **12,704 records → 4,962 distinct `stationNum`** (= distinct `siteId`); the surplus is multiple period-of-record segments per station. `build_stations_seed.py` dedupes on `stationNum` (widest POR).
- `dataSource` (network) composition of the catalog records: **NOAA 5,196 · CoCoRaHS 5,411 · NRCS 954 · CoAgMet 916 (+ "COAGMET" 59 casing variant, folded) · NCWCD 168**. CoCoRaHS (citizen observers) and NOAA COOP dominate by count; CoAgMet/NRCS/NCWCD are automated.
- The `dataSource` query param on the catalog endpoint is **ignored** server-side — bucket by network client-side.

## Behaviors that shaped the code

- **Anonymous limit (since 2025-12-10):** a keyless request returns the string body `"Error: Exceeded Daily Data Limit"`. A CDSS API key is required in practice. (Confirmed by hitting the limit keyless, then succeeding with the key.)
- **Zero records:** a (station, measType) with no data returns HTTP 404 (or a string sentinel) — handled as *no-data*, not an error. Stations do not report every measure (a CoCoRaHS site is precip-only; a SNOTEL site has no pan Evap).
- **Throttle:** a burst of large full-history requests can return HTTP 403 transiently — retried with exponential back-off.
- **Live sample (5 stations, 5 measTypes):** 134,494 rows, coverage 1906→2026, 0 errors, 13/25 (station, measType) combinations were no-data. Value ranges sane: `temp_max_f` −39.98…111 °F (sub-zero preserved), `precip_in` 0…15.46 in, `solar_rad_mj_m2` 0.39…32.97, `wind_run_km` 0.32…463, `swe_in` 0…2.60.
