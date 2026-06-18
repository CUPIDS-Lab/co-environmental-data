# Survey notes — Colorado reservoir storage

The Survey phase output (data-liberation phase 1): understand the source before
touching code. Seeds the README and `AGENTS.md`. Tracks issue
[#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9).

## What this data is

Current and historical **reservoir storage** (and pool elevation, releases where
available) for Colorado reservoirs, pulled from three public APIs:

| Source | What | Access | License | Erosion/enclosure |
|---|---|---|---|---|
| **CO DWR / CDSS** | Statewide telemetry: storage, elevation | REST API v2 (JSON/CSV), `dwr.state.co.us/Rest` | Public / "as-is" | State-controlled (lower erosion risk); some records only via Laserfiche |
| **USBR Reclamation RISE** | Colorado River reservoirs (Blue Mesa, Navajo, Powell…): storage, elevation, release | JSON:API, `data.usbr.gov/rise/api` | Public domain | Federal funding dependence |
| **Northern Water** | C‑BT system (Carter, Horsetooth, Granby): storage, elevation | ArcGIS Hub FeatureServer, `data-nw.opendata.arcgis.com` | Public (verify) | District-funded (stable) |

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

- [ ] **DWR/CDSS:** confirm the telemetry timeseries endpoint + parameter codes
      (`STORAGE`, `ELEV`) and the real station `abbrev`s for the seed reservoirs.
- [ ] **RISE:** discover the real catalog **item ids** per reservoir × variable
      (via `/catalog-item` or the RISE catalog UI); fill `reservoirs.csv:rise_item_ids`.
- [ ] **Northern Water:** confirm the FeatureServer **service URL** and the ArcGIS
      **field names** (`field_map` in `sources.yaml`).
- [ ] Enumerate the **full** Colorado reservoir list per source. The seed in
      `reservoirs.csv` is a curated ~37-reservoir starter; `reservoir.stations`
      automates the full pull — call `stations.station_list_url(slug)`, fetch it,
      then `stations.parse_dwr_stations(...)` → `stations.merge_into_seed(...)`.
      DWR station parsing is implemented + tested; add the RISE/Northern station
      parsers here once their catalog/FeatureServer responses are confirmed.
- [ ] Fill `reconcile()` expected totals from each agency's current-conditions page.

## Enumeration (how the seed gets to "full")

`reservoir.stations` builds each source's catalog/station-list query:
- **DWR/CDSS:** `telemetrystations/telemetrystation/?parameter=STORAGE` → reservoirs
  reporting storage; parsed by `parse_dwr_stations` (✅ implemented + tested).
- **RISE:** `/catalog-item?...` filtered to the reservoir-storage parameter (CO);
  parse the returned catalog items into `rise_item_ids` per reservoir × variable.
- **Northern Water:** the FeatureServer `/query` returns all reservoirs in one call;
  parse `features[].attributes` into rows (the same `field_map` the parser uses).
