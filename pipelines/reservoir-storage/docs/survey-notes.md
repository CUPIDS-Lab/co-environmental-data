# Survey notes — Colorado reservoir storage

The Survey phase output (data-liberation phase 1): understand the source before
touching code. Seeds the README and `AGENTS.md`. Tracks issue
[#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9).

## What this data is

Current and historical **reservoir storage** (and pool elevation, releases where
available) for Colorado reservoirs, pulled from three public APIs:

| Source | What | Access | License | Erosion/enclosure |
|---|---|---|---|---|
| **CO DWR / CDSS** ✅ | Statewide telemetry: storage, elevation (140 stations) | REST API v2 (JSON/CSV), `dwr.state.co.us/Rest` | Public / "as-is" | State-controlled (lower erosion risk) |
| **USBR Reclamation RISE** ✅ | Federal **and C-BT** reservoirs (Blue Mesa, Navajo, Granby, Carter, Horsetooth…): storage, elevation, release | JSON:API, `data.usbr.gov/rise/api` | Public domain | Federal funding dependence |
| ~~**Northern Water**~~ ❌ | **No storage series.** The ArcGIS hub publishes only 4 spatial-boundary datasets. The C-BT reservoirs it operates are Reclamation-owned → sourced from **RISE**. Grand Lake (natural) + Boulder (municipal) have no open series. | `data-nw.opendata.arcgis.com` (boundaries) | — | — |

## Unit of observation (the consequential choice)

**One row per `(source, reservoir_id, datetime, variable)`** — tidy long. Storage,
elevation, and release are *variables* (long), not columns (wide). Wide views come
from `filter-pivot-recipes.md`. This makes a new reservoir or a new variable *more
rows*, not a schema change, and makes cross-source comparison a `groupby`.

- **Vintage convention:** `vintage = "current"` (these are continuously-updated
  live pulls); the snapshot date is recorded in `provenance.csv:retrieved_at`.
- **Composite key:** `(source, reservoir_id, datetime, variable)`, enforced unique
  in the pandera schema.

## Structural quirks

- **Three different response shapes:** CDSS `ResultList` (paged), RISE JSON:API
  (`data[].attributes`), ArcGIS `features[].attributes` (epoch‑millis dates).
- **Unit harmonization:** acre-feet (storage), feet (elevation), cfs (release).
- **Vertical datum** differs across sources for elevation — *do not* compare
  elevations across sources without confirming/converting datums (see
  `concepts.yaml` caveats). This is the highest-risk harmonization trap.
- **Capacity baselines differ** → compute `pct_capacity` per source.

## Public-interest stake

Reservoir storage is the headline number for Colorado water reporting (drought,
Colorado River shortage, runoff). Federal access tools are eroding (see
`context/source-inventory.md`); immutable originals + archived endpoints are the
insurance, and a tidy, documented CSV is what a newsroom can actually cite.

## Prior work / corroboration

- The Hub's own `context/source-inventory.md` (Theme 1 — Water) catalogued these
  sources and their access methods.
- USGS NWIS (the streamflow sibling, #10) corroborates some reservoir gauges.
- The Bureau of Reclamation's UC Region "current status" pages give an independent
  top-line for reconciliation.

## ⚠️ Verify-against-live-API checklist (first real run)

The request machinery is correct; these specifics are the first-run confirmation
(all marked `VERIFY` in `data/lookups/sources.yaml` and `sources.py`):

- [x] **DWR/CDSS:** ✅ **confirmed live (2026-06).** Endpoint
      `telemetrystations/telemetrytimeseriesday`; params `STORAGE`/`ELEV`; the value
      is `measValue` (not `value`); abbrevs are codes (Green Mountain → `GRERESCO`,
      Dillon → `DILRESCO`, Chatfield → `CHARESCO`, Cheesman → `CHERESCO`, Spinney →
      `SPIRESCO`, Rifle Gap → `RIFRESCO`). **CDSS returns HTTP 404 for any zero-record
      query** — handled as no-data. Omit `startDate` for full history (a too-early
      startDate triggers the 404). A live pull returned ~4,374 rows across 6 reservoirs.
- [x] **RISE:** ✅ **confirmed live (2026-06).** `/result?itemId=<id>` →
      `data[].attributes.{dateTime, result}`. Item ids resolved via the relationship
      traversal `location?search=<name>` → Lake/Reservoir match →
      `location/<id>?include=catalogRecords.catalogItems` → `parameterName`→item id
      (catalog-item `search`/`locationId[]` filters are broken). 17/20 reservoirs
      resolved (crystal/powell/taylor-park need search-term tuning). Blue Mesa storage
      verified = 317,822 acre-ft.
- [x] **Northern Water:** ❌ **resolved — not a storage source.** The ArcGIS hub
      (`data-nw.opendata.arcgis.com`) has only 4 boundary datasets; no storage
      FeatureServer exists. The C-BT reservoirs it operates are Reclamation-owned and
      moved to RISE (Carter, Horsetooth, Granby, Shadow Mountain, Willow Creek, Lake
      Estes, Marys Lake, Pinewood). Grand Lake (natural) + Boulder (municipal) have
      no open storage series.
- [x] Enumerate the **full** Colorado reservoir list per source. **DWR + RISE done**;
      Northern is not a storage source (above). `reservoirs.csv` = 140 DWR + 20 RISE.
- [ ] Resolve the 3 remaining RISE reservoirs (crystal/powell/taylor-park).
- [ ] Fill `reconcile()` expected totals from each agency's current-conditions page.

## Enumeration (how the seed gets to "full")

`reservoir.stations` builds each source's enumeration query:
- **DWR/CDSS:** `telemetrystations/telemetrystation/` → client-side STORAGE filter →
  reservoir stations; parsed by `parse_dwr_stations` (✅ implemented + tested). 140 stations.
- **RISE:** `rise_location_search_url(name)` → pick the Lake/Reservoir result →
  `rise_location_items_url(id)` (`?include=catalogRecords.catalogItems`) →
  `parse_rise_location_items` maps `parameterName`→item id (✅ implemented + tested).
  17/20 reservoirs resolved.
- **Northern Water:** ❌ no storage service exists (hub = boundaries only); nothing to
  enumerate. C-BT reservoirs are enumerated under RISE instead.
