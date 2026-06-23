# Data management plan — Colorado Environmental Data Hub

How this project handles its data across its life: what we hold, where it lives, how it is documented and shared, who can reach it, how long we keep it, and the rules we are bound by. Maintained by Brian Keegan (accounts@brianckeegan.com, CUPIDS Lab). The hard gates are privacy law and the CARE Principles; everything else is advisory. Keep this consistent with `GOVERNANCE.md`, `DATA-DICTIONARY.md`, and `decision-log.md`.

## Data types & sources

The Hub holds three kinds of data, at different stages of maturity:

- **The source catalog** (present): one curated JSON file, `docs/planning/colorado_environmental_data_sources.json` — ~56 authoritative Colorado environmental data sources across six themes and three provenance tiers, hand-compiled, with `enclosure`/`erosion`/`verification_status` flags. Small, version-controlled, immutable. License: the catalog itself is MIT/open; it *describes* third-party sources, each with its own terms.
- **Liberated datasets** (four present): tidy CSVs produced by `pipelines/<name>/` from public agency APIs — reservoir storage (CO DWR/CDSS + USBR Reclamation RISE), stream/river flow (USGS NWIS + CO DWR/CDSS), snowpack/SWE (NRCS SNOTEL + snow courses via AWDB), and daily climate stations (CO DWR/CDSS, twelve measTypes across five networks) are all built (day-resolution, per-site, full history). Unit of observation: one observation per site per day. Sources are reachable and re-releasable, so the pipeline regenerates results rather than depending on a frozen snapshot.
- **The news corpus** (future, specified in `context/architecture.md`): article metadata, short excerpts, and archived links for Colorado environmental reporting 2014–present, plus a journalist → article → data-source citation graph. Text-and-tabular. This is the stage that introduces copyright and journalist-privacy duties.

Detailed per-field provenance lives in the relevant `DATA-DICTIONARY.md`, not here.

## Storage & backup

- **Catalog + code + docs:** committed to git (`CUPIDS-Lab/co-environmental-data`); GitHub is the source of record, with every contributor's clone a redundant copy.
- **Liberated datasets:** regenerable from the source APIs by the **monthly CI refresh** (a full rebuild that self-heals upstream revisions); the canonical archived copy is the **Harvard Dataverse** deposit (citable DOI).
- **Raw article HTML + Wayback snapshots (future):** Cloudflare R2, retained immutably so any label can be reconstructed; restricted tier.
- **Backup cadence & responsibility:** git history + the monthly Dataverse draft are the backup; the project manager is responsible. Each pipeline's derived data (its own `data/processed/`) is treated as regenerable output, never a source of truth.

## Metadata & documentation standards

Documentation is half the work, so it is part of the plan, not an afterthought. Keep each `DATA-DICTIONARY.md` current and co-located with the data — grain, fields, units, allowed values, missingness, derived-variable formulas, and known issues — and record non-obvious choices in `decision-log.md`. The project practices recognized standards informally: provenance records resemble W3C PROV (per-row `run_id`, source method, timestamps), dataset metadata mirrors DCAT, and openness aims at FAIR. The `data-card.md` is the people-facing transparency summary; keep it consistent with the dictionary.

## Sharing conditions

What is shared, with whom, in what form, and under what license (MIT; open): the catalog and the liberated datasets are released publicly in open, version-stamped formats through a defined export, and the **re-runnable pipeline** is shared rather than only a cleaned snapshot. For long-term findability, each liberated dataset is deposited to **Harvard Dataverse** to mint a citable DOI (the *Findable* and *Accessible* in FAIR); each `pipelines/<name>/dataverse/` kit archives that pipeline's `data/processed`, code, and documentation, and the deposit is **draft-only in CI and published only on explicit human review** (a DOI is permanent). Record each resulting DOI in the pipeline's README and the Hub `README.md`. Recurring monthly refreshes target the existing dataset as a **new version** (one DOI), not a new DOI. Name foreseeable misuses up front (below and in `data-card.md`), and run the `data-bulletproofing-checklist.md` before anything is published. **Licensed-database content is never shared or redistributed** — it stays in the restricted tier per its license.

## Access controls

Who can reach which data follows the tiers in `GOVERNANCE.md` — public catalog/datasets, restricted licensed content + raw HTML, and the provisioned-but-empty sensitive tier for future journalist records. Apply least privilege: people get the narrowest access their role needs, credentials (`CDSS_API_KEY`, `DATAVERSE_API_TOKEN`) are read from the environment or repository secrets rather than committed, and changes to data are tracked and replayable through git + per-row `run_id`. Access to restricted/sensitive tiers is requested from the project manager, logged, and revoked when a role or entitlement ends.

## Retention & secure disposal

Retention is set per data class in `GOVERNANCE.md`: the catalog is kept permanently (versioned); archived HTML/snapshots are kept for the life of the corpus; licensed exports are kept only as long as the entitlement permits and then deleted; interim/processed data is regenerable and not retained as a source of truth. Sensitive journalist records (future) get minimal, time-bound retention with a disposal procedure defined before any are ingested. The project manager is the named custodian responsible for disposal; recording the disposal plan is part of what makes retention legitimate rather than open-ended accumulation.

## Compliance

The legal and ethical regimes that bind this project:

- **Human subjects / IRB:** not engaged — the project analyzes *published* journalism, not primary data collected from human subjects. Revisit if scope ever shifts to interviewing journalists.
- **Copyright / fair use:** the load-bearing regime for the corpus. Text-and-data-mining of in-copyright news for **non-consumptive research** is the basis; it holds only while the public site shows **metadata + short excerpts + archived links, never republished full article text**. Respect `robots.txt` and outlet ToS.
- **Licensed-database terms:** Nexis Uni, NewsBank, ProQuest, Factiva forbid bulk/automated download — manual export within license terms only; no redistribution.
- **Privacy:** journalists are public figures acting professionally; record professional information only, offer a correction/right-to-respond pathway, and use `coverage_tier` to avoid mislabeling.

These are hard gates, not advisory preferences — they can constrain or redirect what may be collected, linked, retained, or published, and they take precedence over convenience.

This project will handle **conditionally sensitive-human** data once the corpus ingests article text + journalist records, so the gates above become load-bearing at that point. Every identifier and retention affordance must ship with the matching access tiers and contestable governance in `GOVERNANCE.md` — affordances without duties are theater. Complete the `responsible-data-checklist.md` before ingesting or sharing corpus data, and keep to metadata + excerpts + archived links before anything leaves the controlled tier. (No Indigenous data is implicated today; CARE applies if that ever changes.)
