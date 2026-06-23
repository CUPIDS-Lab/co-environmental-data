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
      resolved — **all 20/20** (crystal, taylor-park, and powell added 2026-06; powell's
      storage lives under "Lake Powell Glen Canyon Dam and Powerplant", loc 393, not the
      "Lake Powell At …" sub-gauges). Blue Mesa storage verified = 317,822 acre-ft.
- [x] **Northern Water:** ❌ **resolved — not a storage source.** The ArcGIS hub
      (`data-nw.opendata.arcgis.com`) has only 4 boundary datasets; no storage
      FeatureServer exists. The C-BT reservoirs it operates are Reclamation-owned and
      moved to RISE (Carter, Horsetooth, Granby, Shadow Mountain, Willow Creek, Lake
      Estes, Marys Lake, Pinewood). Grand Lake (natural) + Boulder (municipal) have
      no open storage series.
- [x] Enumerate the **full** Colorado reservoir list per source. **DWR + RISE done**;
      Northern is not a storage source (above). `reservoirs.csv` = 140 DWR + 20 RISE.
- [x] Resolve the 3 remaining RISE reservoirs — **done; RISE is 20/20** (crystal→item 274, powell→509, taylor-park→793).
- [ ] Fill `reconcile()` expected totals **and run a passing reconciliation** — **NOT done** (corrected 2026-06-22). Reference anchors are recorded in **Reconciliation** below, but the notebook `expected` block is commented out and the persisted `data/audit/reconcile.json` still holds placeholder values (a literal `NOTREAL`, `expected=1.0`, a failing `blue-mesa`). Tracked as [#38](https://github.com/CUPIDS-Lab/co-environmental-data/issues/38); **must pass before the first Dataverse publish.**

## Reconciliation — confirming our numbers against the agencies

> ⚠️ **Status (2026-06-22 QA audit): NOT yet run to passing.** The anchors below are recorded, but no passing reconciliation exists on disk — `data/audit/reconcile.json` holds placeholders. This is the canonical pre-publication gate (per `data-bulletproofing-checklist.md`); resolve [#38](https://github.com/CUPIDS-Lab/co-environmental-data/issues/38) before publishing #36.

Reconciliation is the cheap insurance that the pipeline didn't quietly corrupt the
*values* — wrong units, a parsing slip, the wrong station, stale data. It compares a few
storage numbers you read off the agencies' own websites against the **latest** storage
value in `data/processed/reservoir-storage.csv`. It's a **spot-check** (2–3 reservoirs per
source is plenty), and it's **optional** — it never blocks a run. It lives in nb-04's
reconcile cell and calls `audit.reconcile(expected)`.

**Where to read the ground-truth number** (current storage, in **acre-feet**):

| Source | Where | How |
|---|---|---|
| `dwr_cdss` | [dwr.colorado.gov](https://dwr.colorado.gov) — *Surface Water Conditions* map / station search | Find the reservoir by name or `abbrev` (e.g. `GRERESCO`); read the latest **Storage (AF)**. |
| `reclamation_rise` | [data.usbr.gov/rise](https://data.usbr.gov/rise) | Search the reservoir; open its **Lake/Reservoir Storage** series; the most recent point is current storage. (Reclamation's UC Region *current reservoir status* tables are an alternative.) |

**How to enter it.** Each entry is `(source, reservoir_id): storage_af`:
- `source` — the slug, `"dwr_cdss"` or `"reclamation_rise"`.
- `reservoir_id` — the id **exactly as in `data/lookups/reservoirs.csv`** (CDSS `abbrev` like
  `DILRESCO`, or RISE slug like `blue-mesa`).
- the value — current storage in acre-feet, e.g. `138214.0`.

```python
expected = {   # real values as of 2026-06-21 — refresh before running
    ("dwr_cdss", "GRERESCO"):           55480.0,   # Green Mountain
    ("reclamation_rise", "blue-mesa"):  309743.0,  # Blue Mesa
}
```

**Reading the result** — `audit.reconcile` returns a table of `expected_af` (yours) vs
`got_af` (ours) with a boolean `match`, and writes `data/audit/reconcile.json`:
- **`match = True`** — within **1 %** (or 1 acre-foot, whichever is larger; tolerance is
  `max(1, 0.01·expected)`) → faithful extraction; trust that series.
- **`match = False`** — investigate **before publishing**:
  - `got_af` blank → reservoir not in the CSV (not fetched / rows dropped) → check Retrieve.
  - off by a round factor (×1000, ×43 560) → a **units** bug.
  - off by a bit but >1 % → wrong `reservoir_id`, *or* the CSV's latest **daily** value is
    several days stale vs. the live page (check our latest `datetime`).

The tolerance is slack on purpose: the agency page is "now," ours is the latest daily value,
so they differ slightly but should agree to within a percent.

**Confirmed reference values** — current storage per the pipeline, spot-checked against each
reservoir's known capacity (all plausible), **as of 2026-06-21**. Use as reconcile anchors;
refresh against the live agency page before re-running, since storage changes daily.

| source | reservoir | storage (acre-ft) |
|---|---|--:|
| reclamation_rise | Lake Powell (powell) | 5,674,710 |
| reclamation_rise | Blue Mesa (blue-mesa) | 309,743 |
| reclamation_rise | Taylor Park (taylor-park) | 67,584 |
| reclamation_rise | Crystal (crystal) | 17,005 |
| dwr_cdss | Dillon (DILRESCO) | 204,746 |
| dwr_cdss | Cheesman (CHERESCO) | 66,315 |
| dwr_cdss | Green Mountain (GRERESCO) | 55,480 |

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
