# Data dictionary — Colorado Environmental Data Hub

Documentation is half the work: a dataset without this file is a private spreadsheet. Keep this current and co-located with the data. One entry per dataset/table below; one variable per row within each table.

---

## Dataset: `colorado_environmental_data_sources` (the source catalog)

- **File:** `data/raw/colorado_environmental_data_sources.json` (immutable source-of-record; a copy also lives in `context/` as part of the design bundle).
- **Grain (unit of observation):** one record per **data source** (an authoritative system/portal that publishes Colorado environmental data). `source_count = 56`.
- **Source / provenance:** hand-compiled discovery audit by the CUPIDS Lab / CEJ team, **compiled 2026-06-17**. Each source was located and characterized from agency websites; the narrative behind it (with citations and risk analysis) is in `context/source-inventory.md`. `schema_version = 1.0`.
- **Input license:** the catalog itself is released under this repo's MIT License / open data. Each *source's* own license is recorded per-record in the `license` field (several are "verify" — unstated upstream).
- **Sensitivity:** Public — open government/agency metadata. No personal or restricted data.
- **Update cadence:** static snapshot; re-released as a new dated vintage when sources are re-verified or added. Treat the June 2026 `enclosure`/`erosion` flags as **point-in-time** assessments.

### Container fields (top-level object)

| Variable | Type | Description |
| --- | --- | --- |
| `title` | string | Human title of the catalog. |
| `description` | string | One-line description of the catalog's purpose. |
| `compiled_date` | date (`YYYY-MM-DD`) | When this vintage was compiled (`2026-06-17`). |
| `project` | string | Owning project: "CU Environmental Data Hub (CUPIDS / CEJ)". |
| `schema_version` | string | Catalog schema version (`1.0`). Bump on any breaking field change. |
| `source_count` | int | Number of records in `sources` (56). Must equal `len(sources)`. |
| `themes` | array | Controlled vocabulary of the 6 themes (see below). |
| `tiers` | array | Controlled vocabulary of the 3 provenance tiers (see below). |
| `metadata_fields` | array[string] | The 16 field names every source record carries (self-documenting). |
| `flag_legend` | object | Definitions of `enclosure_flag`, `erosion_flag`, `verification_status`. |
| `data_integrity_caveat` | string | Warning about the spurious NREL "nlr.gov" rebrand — do not trust. |
| `sources` | array[object] | The 56 source records; schema below. |

### Variables (one `sources[]` record — the analytic grain)

| Variable | Type | Units / vocab | Allowed values / range | Description | Missingness |
| --- | --- | --- | --- | --- | --- |
| `id` | string (slug) | — | unique kebab slug, e.g. `water-fed-usgs-nwis` | Stable primary key. Convention: `<theme>-<tier>-<agency/system>`. | never null; unique |
| `name` | string | — | free text | Official source/system name. | never null |
| `agency` | string | — | free text | Owning agency/organization. | never null |
| `tier` | string (enum) | provenance | `federal` · `state` · `local_regional` | Government level that publishes the data. | never null |
| `themes` | array[string] (enum) | theme | subset of the 6 themes | Environmental theme(s) the source covers; ≥1. | never empty |
| `granularity` | string | — | free text | Spatial/observational grain (e.g. "Point/station", "Census block group"). | rarely empty |
| `temporal_coverage` | string | — | free text | Period of record (e.g. "1984–present; annual"). | rarely empty |
| `access_method` | array[string] | — | free text | How to get the data (API, bulk download, web map, records request…). | ≥1 typical |
| `formats` | array[string] | — | free text | Distribution formats (CSV, JSON, GeoTIFF, shapefile, PDF…). | ≥1 typical |
| `license` | string | — | free text incl. `"verify"`/"unstated" | Source's own use license. **Treat unstated/"verify" as restricted until confirmed.** | "verify" where unknown |
| `update_cadence` | string | — | free text | Refresh frequency (real-time, daily, annual, static…). | rarely empty |
| `links` | object | URLs | see sub-fields | Canonical URLs for the source (see "Nested: `links`"). | object always present; sub-fields optional |
| `enclosure_flag` | object | — | `{status, note}` | Is the data privatized/paywalled/login-gated/vendor-mediated? | always present |
| `erosion_flag` | object | — | `{status, note}` | Is the data at risk of removal/decommission/degradation? | always present |
| `verification_status` | string (enum) | — | `verified` · `needs_followup` | Whether the record's URLs/access were confirmed during compilation. | never null |
| `verification_note` | string | — | free text | What still needs checking (for `needs_followup`); may be empty when `verified`. | empty when verified |

### Nested objects

**`links`** — `landing_page` (string URL), `documentation` (string URL), `api` (string URL), `notes_url` (string URL). All optional; absent keys mean "no such URL recorded" (not "no such resource exists"). Canonicalize before matching (strip scheme/`www`, lowercase host).

**`enclosure_flag` / `erosion_flag`** — each is `{ "status": <value>, "note": <string> }`.

### Controlled vocabularies

- **`themes`** (6): `water`, `fire`, `wind`, `minerals`, `pollution`, `land_use`.
- **`tiers`** (3): `federal`, `state`, `local_regional`.
- **`enclosure_flag.status`** (3): `no`, `partial`, `yes`.
- **`erosion_flag.status`** (3): `no`, `partial`, `yes`.
- **`verification_status`** (2): `verified`, `needs_followup`.

### Distribution (this vintage, 2026-06-17)

- **By tier:** federal 25 · state 15 · local_regional 16.
- **By theme** (sources may carry >1 theme): land_use 22 · water 16 · pollution 13 · minerals 9 · fire 8 · wind 5.
- **Verification:** verified 47 · needs_followup 9.

### Derived variables

None published centrally yet. When the L2 pipeline builds the citation dictionary, it will derive `match_hosts` (canonical hostnames exploded from `links.*`) and `match_keywords` (agency/dataset aliases) per source — these do **not** yet exist in the catalog and are required by the Stage-A URL matcher (`context/architecture.md` §6, nb-04). Tracked as a **blocking** item in `ROADMAP.md`.

### Known issues & caveats

- **NREL "nlr.gov" is spurious.** Search content during compilation claimed NREL was renamed "National Laboratory of the Rockies" with domain `nlr.gov`. This is unverified and almost certainly false. Keep `nrel.gov` canonical; do not add `nlr.gov` anywhere without official confirmation (`data_integrity_caveat` field; `context/source-inventory.md`).
- **9 of 56 sources are `needs_followup`** — URLs/licenses/hubs not yet confirmed (e.g. Reclamation RISE URL, Larimer County download hub, CoAgMet license). Filter on `verification_status == "verified"` for anything load-bearing; resolving these is a **blocking** roadmap item before relying on them.
- **Unstated licenses.** Several sources have `license` = "verify"/unstated. Treat any source without a named open license as "restricted — verify" until confirmed.
- **Flags are point-in-time.** `enclosure_flag` and `erosion_flag` reflect the federal/state data landscape as of **June 2026** (active 2025–2026 removals: EPA EJScreen removed Feb 2025; GHGRP proposed for near-elimination; USGS NWISWeb decommission by 2026–2027). Re-assess on each vintage; snapshot at-risk sources to the Wayback / End-of-Term archive when a removal banner or 404 appears.
- **56 structured vs. ~70 discussed.** `context/source-inventory.md` discusses ~70 sources in prose; only 56 are structured in this JSON. The remainder (watershed coalitions, additional county portals, tribal data) are expansion candidates, not omissions of fact. Note EnviroScreen explicitly excludes tribal-jurisdiction areas.
- **What this data supports.** The catalog supports *description and comparison* (coverage by theme/tier, enclosure/erosion risk) well; it is a curated discovery inventory, **not** an exhaustive census and not a basis for prediction.
