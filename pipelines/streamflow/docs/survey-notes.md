# Survey notes — Colorado stream/river flow

The Survey phase output (data-liberation phase 1): understand the source before touching code. Seeds the README and `AGENTS.md`. Tracks issue [#10](https://github.com/CUPIDS-Lab/co-environmental-data/issues/10). Stamped out from the sibling `reservoir-storage` pipeline (#9).

## What this data is

Daily **mean discharge** (streamflow, cubic feet per second) at Colorado stream gages, current and historical, pulled from two public APIs:

| Source | What | Access | License | Erosion/enclosure |
|---|---|---|---|---|
| **USGS NWIS** ✅ | The national streamflow record — daily mean discharge, deepest history (many CO gages to the early 1900s) | Daily-values REST service (WaterML-JSON), `waterservices.usgs.gov/nwis/dv` | Public domain (U.S. federal) | Federal funding dependence; legacy NWIS services being migrated to `api.waterdata.usgs.gov` |
| **CO DWR / CDSS** ✅ | State surface-water daily series; **continues** many USGS gages past their federal discontinuation | REST API v2 (JSON), `dwr.state.co.us/Rest` | Public / "as-is" | State-controlled (lower erosion risk) |

## Unit of observation (the consequential choice)

**One row per `(source, site_id, datetime, variable)`** — tidy long. Discharge is a *variable* (long), not a column (wide). Wide views come from `filter-pivot-recipes.md`. A new gage or a new variable (e.g. gage height) is *more rows*, not a schema change; cross-source comparison is a `groupby`.

- **Vintage convention:** `vintage = "current"` (continuously-updated live pulls); the snapshot date is in `provenance.csv:retrieved_at`.
- **Composite key:** `(source, site_id, datetime, variable)`, enforced unique in the pandera schema. `site_id` is the USGS site number for `usgs_nwis` and the CDSS `abbrev` for `dwr_cdss`.

## ⚠️ The headline harmonization trap: the two sources OVERLAP

Unlike the reservoir pipeline's disjoint DWR/RISE sources, here the two sources **substantially overlap**: DWR surface-water daily frequently **re-serves the USGS gage** — its row-level `dataSource` is literally `USGS`. The same physical gage appears once under `usgs_nwis` (keyed by site number) and once under `dwr_cdss` (keyed by abbrev), joined by `usgs_site_no` in `sites.csv`.

- They are **not independent measurements** — do not average/sum the two as if they were. For single-series analysis, de-duplicate to one source per gage (USGS is the system of record; DWR is the convenient state mirror that often *extends* it past USGS discontinuation — e.g. South Platte at Denver: USGS ends 2007-09-29, DWR carries it to the present).
- It is also a **gift**: the overlap is a built-in accuracy check. Across the 33 paired gages the two agreed on 97.6–100 % of shared days (median 100 %; often byte-identical, since DWR literally re-serves USGS). `audit.reconcile_cross_source` quantifies it; a divergence flags an id-mapping/unit error or a provisional-vs-approved lag.

Full caveats in `data/lookups/concepts.yaml`.

## Structural quirks (confirmed against the live APIs, 2026-06-22)

- **USGS dv (WaterML-JSON):** `value.timeSeries[].values[0].value[] = {value, qualifiers, dateTime}`; discharge is parameter `00060`, daily mean is statistic `00003`; unit `ft3/s` = cfs. Missing data is the per-series `noDataValue` sentinel (e.g. -999999) and ice/no-record days come back absent → preserved as NA. **Not paginated** — full POR arrives in one (multi-MB) JSON.
- **DWR surfacewatertsday — three gotchas vs the reservoir telemetry endpoint:** (1) the value field is **`value`**, not `measValue`; (2) the date keys are **`min-measDate` / `max-measDate`** (MM/DD/YYYY) — `startDate` returns *"not a valid URL query key"*; (3) `measType` is the spelled-out **`Streamflow`** — `DISCHRG` returns zero records. Row flags are `flagA`..`flagD`.
- **CDSS ice sentinel:** ice-affected/missing days are encoded as the *impossible* discharge **`-999`** with a `U`/`Ice` flag. The parser maps any negative discharge → NA (preserving the flag), harmonizing with USGS's NA.
- **No-data conventions:** USGS returns HTTP 200 with an empty `timeSeries` list; CDSS returns **HTTP 404** ("zero records"). Both are handled as no-data, not errors.

## Public-interest stake

Streamflow is the backbone series of Colorado water reporting — runoff forecasts, drought, Colorado River Compact accounting, in-stream flow rights, flood response. Long gage records are irreplaceable; the legacy USGS NWIS web services are being migrated, so immutable originals + archived endpoints are the insurance, and a tidy, documented CSV is what a newsroom or researcher can actually cite.

## Prior work / corroboration

- The Hub's own `context/source-inventory.md` (Theme 1 — Water) catalogs USGS and CDSS as authoritative Colorado water sources.
- The sibling `reservoir-storage` pipeline (#9) already uses CDSS — its retrieval/parsing patterns are reused here for a different CDSS endpoint.
- USGS and DWR re-serving the same gages is itself the corroboration: the cross-source reconciliation is an independent-of-us accuracy check.

## ⚠️ Verify-against-live-API checklist (first real run)

- [x] **USGS NWIS:** ✅ confirmed live (2026-06). dv service, `00060`/`00003`; full POR in one response; live sample pulled 33 gages (1.14M rows, to 1900).
- [x] **DWR/CDSS surface water:** ✅ confirmed live (2026-06). `surfacewatertsday`, `measType=Streamflow`, `min-measDate`/`max-measDate`, value field `value`; full pull retrieved 33 gages (1.16M rows) with the API key.
- [x] **Cross-source overlap:** ✅ confirmed — DWR `dataSource=USGS` on shared gages; 33 paired gages agreed 97.6–100 % on shared days (median 100 %).
- [x] **Ice/missing sentinel:** ✅ `-999` + `U/Ice` → NA (27 rows in the sample); no impossible negatives remain.
- [x] **⚠️ CDSS throttle (resolved):** a *keyless* burst of large full-history DWR requests trips a **persistent HTTP 403** IP throttle. Resolved by the **`CDSS_API_KEY`** in the git-ignored `dwr_api.json` (raises the limit) — the full 33-DWR pull then completes with **zero errors**; keyless, raise `STREAMFLOW_RATE_LIMIT` and lean on the retry/back-off. USGS has no such limit.

## Reconciliation — confirming our numbers

Two layers, both optional and non-blocking:

1. **Cross-source (automatic, this pipeline's signature check):** `audit.reconcile_cross_source()` joins `usgs_nwis` ↔ `dwr_cdss` on `(usgs_site_no, date)` for shared gages and reports the share agreeing within 5 %. ~100 % is expected (DWR re-serves USGS); a low rate flags an id/unit error. Writes `data/audit/reconcile-cross-source.json`.
2. **Against the agency page (manual spot-check):** `audit.reconcile(expected_now)` compares our latest `discharge_cfs` to the current daily mean read off [waterdata.usgs.gov](https://waterdata.usgs.gov) (USGS) or [dwr.colorado.gov](https://dwr.colorado.gov) (DWR). Tolerance is the looser of 5 % or 1 cfs (daily-mean vs the page's possibly-instantaneous reading).

```python
expected = {   # current daily-mean discharge, cfs — refresh before running
    ("usgs_nwis", "09095500"): 12400.0,   # Colorado R near Cameo
    ("usgs_nwis", "08220000"):  1840.0,   # Rio Grande near Del Norte
}
```

## Enumeration (how the curated seed scales to "all")

`streamflow.stations` builds each source's catalog query:
- **USGS:** `usgs_site_list_url(state="CO", param_cd="00060")` → NWIS site service RDB → `parse_usgs_sites` (all CO stream gages with daily discharge).
- **DWR:** `dwr_stations_url(...)` → `surfacewaterstations` → `parse_dwr_stations`; `resolve_dwr_abbrev_url(usgs_site_no)` is the cross-link used to seed both sources from one curated USGS list (how the shipped `sites.csv` was built). The shipped seed is a curated **33 major-river gages** (all 8 basins), each with its DWR mirror — a dated snapshot; re-run the enumeration to scale or refresh.
