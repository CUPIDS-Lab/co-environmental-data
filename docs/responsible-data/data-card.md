# Data Card — Colorado Environmental Data Hub

A people-centered transparency summary of this project's datasets, in the spirit of the [Data Cards Playbook](https://sites.research.google/datacardsplaybook/). It documents the facts a reader needs to decide whether and how to (re)use the data. This complements — it does not replace — the field-level schema in `DATA-DICTIONARY.md` (catalog) and each pipeline's `docs/data-dictionary.md` (liberated datasets).

## Overview

- **Datasets:** (1) **Colorado Environmental Data Source Catalog** — the shipped catalog, v1 · last updated 2026-06-23; (2) **Reservoir Storage**, (3) **Stream/River Flow**, (4) **Snowpack (SWE)**, (5) **Daily Climate Stations** — liberated, day-resolution, tidy-long datasets in `pipelines/`; (6) **Journalist→Citation Corpus** — *planned*, specified in `context/architecture.md`.
- **Summary:** a curated, independently verifiable catalog of ~56 authoritative Colorado environmental data sources, plus tidy liberated datasets built from it — the foundation for measuring how Colorado environmental journalism depends on public data.
- **Sensitivity:** public today (open government/agency metadata); conditionally sensitive-human once the corpus ingests article text + journalist records. **Openness:** open. **License:** MIT.
- **Maintainer:** Brian Keegan · accounts@brianckeegan.com · CUPIDS Lab.
- **Authorship:** created and owned by CUPIDS Lab (University of Colorado Public Interest Data Science Lab) with Center for Environmental Journalism collaborators; funding via CU (no external grant recorded).

## Motivation & intended use

The catalog exists because Colorado's environmental data is fragmented across dozens of federal/state/local systems and is actively eroding and enclosing; the project documents and liberates it while it is still reachable, and uses it as the backbone for a journalist→data-citation corpus. It is for environmental journalists, researchers of data-driven reporting, and the Colorado public. **What it can plausibly support:** description and comparison — which sources exist, their provenance and risk flags, and (via the corpus) which are cited, by whom, how often, over time. **What it cannot:** prediction or causal claims about data use, or judgments of a reporter's quality.

## Provenance & collection

The catalog was hand-compiled from authoritative federal, state, and local sources and audited in `context/source-inventory.md`; each entry records its provenance tier and a `verification_status`. Liberated datasets come from public agency APIs (reservoir storage from CO DWR/CDSS + USBR Reclamation RISE), reachable and re-released so the pipeline regenerates them. The future corpus draws on open-web retrieval (Media Cloud, GDELT, sitemaps, Wayback) and CU Libraries' licensed databases by manual export only. Detailed field provenance lives in the dictionaries.

## Composition

The catalog: ~56 sources across **six themes** (water, fire, wind, minerals, pollution, land use) and **three provenance tiers** (federal, state, local/regional), each flagged for `enclosure` and `erosion` risk — grain is one row per source. The reservoir dataset: one observation per site per day, 118 major reservoirs + 20 RISE sites, with full per-site history, per-extract provenance (`run_id`), and a concept catalog of caveats. The **streamflow**, **snowpack**, and **climate-station** datasets share the same tidy-long grain — one observation per `(source, site, day, variable)`, with per-extract provenance and per-concept caveats (66 gage-series; 199 snow stations; a 40-station climate cross-section). See the respective dictionaries for the field-level schema rather than duplicating it here.

## Recommended & out-of-scope uses

**Recommended:** discovering and citing Colorado environmental data sources; reproducible analysis of reservoir storage; methods research on data journalism. **Out of scope:** treating the catalog as exhaustive (it is curated, not complete); relying on a `needs_followup` source without confirming it; using citation counts as a quality ranking of journalists; redistributing any licensed-database content; republishing full article text from the future corpus.

## Sensitive attributes & fairness

The catalog and liberated datasets contain **no personal data**. The **future corpus** introduces journalist records (public, professional) and article text (in-copyright). Sensitive considerations there: avoid mislabeling an occasional contributor as an "environmental journalist" (mitigated by `coverage_tier`); protect any vulnerable *source quoted within* an archived article; represent reporters by the fact of citation only, never a quality judgment. Pair every identifier/retention affordance with the access tiers and remedy process in `GOVERNANCE.md`, and complete the `responsible-data-checklist.md` before ingesting or sharing corpus data — affordances without duties are theater.

## Known limitations & caveats

The catalog is curated, not exhaustive, and is a point-in-time snapshot of a moving target (sources erode). Specific issues, mirrored in `DATA-DICTIONARY.md` and `data-quality-checklist.md`: the spurious "NREL → `nlr.gov`" claim is quarantined (`nrel.gov` is canonical); some sources remain `needs_followup`; reservoir data carries vertical-datum and capacity-baseline caveats and real historical gaps; library-database records will arrive with hyperlinks stripped (`links_unavailable=true`); syndicated stories must be deduped before counting.

## Maintenance & governance

Maintained by CUPIDS Lab (Brian Keegan); liberated datasets refresh **monthly** via CI (draft-only Dataverse deposit, human-published). Report a problem — including a journalist correction/right-to-respond request — via accounts@brianckeegan.com (`GOVERNANCE.md` §Remedy). Access conditions, the retention schedule, the disposal plan, and what survives the pilot are in `GOVERNANCE.md` and `CHARTER.md`; decisions are logged in `decision-log.md`.

## Citation

Brian Keegan et al., *Colorado Environmental Data Hub*, CUPIDS Lab, 2026.
