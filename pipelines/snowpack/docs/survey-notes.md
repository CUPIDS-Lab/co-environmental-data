# Survey notes — Colorado snowpack (SWE)

The Survey phase output (data-liberation phase 1): understand the source before touching code. Seeds the README and `AGENTS.md`. Tracks issue [#11](https://github.com/CUPIDS-Lab/co-environmental-data/issues/11). Stamped out from the sibling `streamflow` pipeline (#10).

## What this data is

Snow water equivalent (SWE), snow depth, and water-year precipitation accumulation at Colorado snow-monitoring sites, current and historical, pulled from the **NRCS AWDB REST API** across two networks:

| Source | What | Access | License | Erosion/enclosure |
|---|---|---|---|---|
| **NRCS SNOTEL** (`SNTL`) ✅ | Automated snow-pillow telemetry — DAILY SWE, snow depth, water-year precip; the modern backbone (record since ~1980) | AWDB REST API (JSON), `wcc.sc.egov.usda.gov/awdbRestApi` | Public domain (U.S. federal) | Federal funding dependence; legacy SOAP web service being retired in favor of this REST API |
| **NRCS Snow Course** (`SNOW`) ✅ | Manual snow surveys — SEMIMONTHLY SWE + depth; the deep history (many CO courses back to the 1930s–40s) | Same AWDB REST API, network `SNOW`, duration `SEMIMONTHLY` | Public domain (U.S. federal) | Same |

> **Scope boundary with #44.** Issue #11 also lists "CO DWR/CDSS climate stations" as a snowpack source; issue #44 carves the **CDSS climate-station** domain into its own pipeline and asks #11 to focus on **NRCS SNOTEL** with a SNOTEL↔CDSS crosswalk. This pipeline does exactly that: NRCS SNOTEL + snow courses, with the crosswalk discipline documented in `concepts.yaml` (and `audit.colocated_pairs` as the matching mechanism). CoAgMet (ET/precip) is out of scope.

## Unit of observation (the consequential choice)

**One row per `(source, site_id, datetime, variable)`** — tidy long. SWE, depth, and precip are *variables* (long), not columns (wide). Wide views come from `filter-pivot-recipes.md`. A new station or a new variable (e.g. snow density) is *more rows*, not a schema change; basin aggregation is a `groupby`.

- **`site_id`** is the AWDB **station triplet** (`<id>:CO:<network>`, e.g. `680:CO:SNTL`, `06L02:CO:SNOW`) — the natural, unambiguous AWDB key. `--sites` also accepts the bare id (`680`).
- **Vintage convention:** `vintage = "current"` (continuously-updated live pulls); the snapshot date is in `provenance.csv:retrieved_at`.
- **Composite key:** `(source, site_id, datetime, variable)`, enforced unique in the pandera schema.

## ⚠️ The headline harmonization note: the two networks are NEARBY, not identical

Unlike streamflow's USGS↔DWR (the *same* gage re-served, byte-identical), a SNOTEL and a same-named snow course (e.g. Park Cone) are **distinct sites at roughly the same place** — different aspect/elevation/exposure, and a continuous pillow vs a periodic manual transect. They are **complementary** (the snow course *extends the record decades before SNOTEL*), **not duplicate**.

- Keep both (`source` is in the key); for a single SWE series per place, prefer SNOTEL in the satellite era and the snow course before it.
- `audit.reconcile_cross_source` uses the **co-location** (same name or <2 km, via `audit.colocated_pairs`) as a *looser* accuracy check — a co-located pair should track to within a few inches, not be identical. In the live Gunnison sample the two paired courses agreed 86–100 % within tolerance.

Full caveats in `data/lookups/concepts.yaml`.

## Structural quirks (confirmed against the live API, 2026-06-22)

- **AWDB `data` shape:** a JSON **list** of `{stationTriplet, data:[{stationElement:{elementCode, storedUnitCode, beginDate, endDate}, values:[…]}]}`. One response carries a station's **full period of record** across **all requested elements** (not paginated) — so one request per station covers WTEQ+SNWD+PREC.
- **SNOTEL value shape:** `{date, value, qcFlag, qaFlag}` (with `returnFlags=true`). Units inches.
- **⚠️ Snow-course gotchas:** (1) duration is **`SEMIMONTHLY`** — `DAILY`/`MONTHLY` return zero blocks for a course; (2) each value is `{month, monthPart, year, collectionDate, value}` — the measurement date is **`collectionDate`**, not `date`. The parser selects the field via `date_field`.
- **Elements:** `WTEQ` (SWE), `SNWD` (snow depth), `PREC` (precipitation accumulation, water-year cumulative) — all inches. Snow depth (SNOTEL) starts ~2003 (sensor added later than the pillow). `PREC` is SNOTEL-only.
- **No-data convention:** a station/element with no data returns HTTP 200 with an empty `values` list (or empty `data`) — handled as no-data, not an error. **No API key required** (contrast the CDSS pipelines).

## Public-interest stake

SWE is the backbone of Colorado water supply: April-1 SWE and **basin percent of normal** drive runoff forecasts, reservoir operations, drought declarations, and Colorado River Compact context. The long snow-course records (to the 1930s) are irreplaceable; the legacy NRCS SOAP service is being retired, so immutable originals + a tidy, documented, citable CSV are the insurance.

## Prior work / corroboration

- The Hub's own `context/source-inventory.md` (Theme 1 — Water) catalogs NRCS SNOTEL as an authoritative Colorado water source.
- The sibling `streamflow` (#10) / `reservoir-storage` (#9) pipelines established the architecture reused here.
- NRCS itself publishes basin **percent of normal** reports — the independent truth that `audit.reconcile_basin_pct_normal` checks our computed figure against.

## ⚠️ Verify-against-live-API checklist (first real run)

- [x] **SNOTEL (SNTL):** ✅ confirmed live (2026-06). `data` endpoint, `WTEQ,SNWD,PREC`, DAILY, `returnFlags=true`; full POR in one response; 118 active CO stations enumerated.
- [x] **Snow course (SNOW):** ✅ confirmed live. `SEMIMONTHLY`, `collectionDate` value field; 81 active CO stations; deep history (live Gunnison sample reached **1936**).
- [x] **Basin % of normal:** ✅ live Gunnison sample (11 SNOTEL) computed **106 % of the 1991–2020 normal as of 2024-04-01** — sensible and reconcilable.
- [x] **Cross-source co-location:** ✅ same-name/proximity pairs detected (16 statewide); Gunnison sample reconciled 2 pairs at 86–100 %.
- [x] **No-data / negatives:** ✅ empty `values` handled as no-data; negative SWE/depth/precip sentinels → NA.
- [x] **No API key:** ✅ all requests succeeded keyless; no throttle observed.

## Reconciliation — confirming our numbers

Two layers, both optional and non-blocking:

1. **Basin % of normal vs. NRCS (the signature check):** `audit.reconcile_basin_pct_normal(expected_pct)` compares our computed basin percent of normal to the figure published in the NRCS Colorado Snow Survey / NWCC basin report for the same date. Tolerance ±10 points (methodology and the exact normals baseline differ).
2. **Cross-source co-location (automatic):** `audit.reconcile_cross_source()` joins co-located SNOTEL↔snow-course pairs on shared dates and reports agreement within 25 % / 2 in. A *looser* check by design (nearby-not-identical sites).

```python
expected = {   # NRCS basin % of normal, read off the basin report for the run date
    "Gunnison": 106,
    "Colorado": 110,
}
```

## Enumeration (how the seed scales)

`snowpack.stations` + `scripts/build_sites_seed.py` build the AWDB station-catalog query (`stations?stationTriplets=*:CO:SNTL&activeOnly=true`, and `…:SNOW`) and derive each station's major river basin from its HUC (`huc_to_basin`). The shipped `sites.csv` is **all 199 active CO SNOTEL + snow courses** — full-state coverage, not a sample (SNOTEL/snow courses are a small, enumerable universe, unlike #44's 12k CDSS climate stations). Scale to discontinued stations (deeper history) with `build_sites_seed.py --all`.
