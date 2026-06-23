# Colorado Environmental Data Hub

A documented, reproducible catalog of Colorado environmental data sources — and the foundation for a research corpus linking Colorado environmental journalists to the public data they cite.

A CUPIDS Lab data project. Maturity level: **L4** (collaborative, responsible & accessible). Toolchain: **Python (Datasette · Cloudflare R2 · Quarto · Prefect)**. Sensitivity: **Public today (open government/agency metadata); conditionally sensitive-human once the news corpus ingests article text + journalist records**. Openness: **Open (MIT-licensed; open data)**.

## What & why

Colorado's environmental data lives in dozens of federal, state, and local systems — and in 2025–2026 a meaningful slice of it is **eroding** (datasets removed or decommissioned) or **enclosing** (paywalled, login-gated, vendor-mediated). This project does two things:

1. **Now (this repo):** maintains a curated **catalog of ~56 authoritative Colorado environmental data sources** across six themes (water, fire, wind, minerals, pollution, land use) and three provenance tiers (federal, state, local/regional), each flagged for *enclosure* and *erosion* risk. The catalog is the real, documented dataset this repository ships today.
2. **Next (see `ROADMAP.md`):** uses that catalog as the backbone of a **journalist → article → data-citation corpus** — measuring which Colorado environmental journalists cite which public datasets, 2014–present. The full methodology and technical architecture for that build are in `context/`.

- **Design partners (who builds it):** the CUPIDS Lab undergraduate research team and Center for Environmental Journalism (CEJ) collaborators.
- **Beneficiaries (who it serves):** environmental journalists, researchers studying data-driven reporting, and the Colorado public — plus future maintainers who can re-verify every source.
- **Success looks like:** a catalog whose every source is independently verifiable, and a corpus whose every citation is archived and defensible.

## Repository layout

This repo follows the CUPIDS Lab data-project conventions. Key locations: `data/raw` holds original, **immutable** source data (never edited in place) — currently the curated source catalog; `data/interim` and `data/processed` hold derived data that can always be regenerated from raw; `DATA-DICTIONARY.md` documents the schema; `context/` holds the project's design memos (methodology, architecture, source-inventory audit, proposals); **`pipelines/<name>/`** holds self-contained data-liberation pipelines, one per liberated dataset; the collaboration and responsible-data layer (`CONTRIBUTING`, `GOVERNANCE`, `ROLES`, `responsible-data-checklist`, and the rest below) governs how people work here and how the data's duties are met; the nested `.skills/` give downstream agents task-specific guidance (data intake, documentation, release). See `ROADMAP.md` for what is planned but not yet built (the corpus pipeline and the L5 open-knowledge publication layer).

## Pipelines

The Hub hosts self-contained **data-liberation pipelines** under `pipelines/<name>/` — each liberates one dataset into a tidy, documented CSV, ships a Harvard **Dataverse deposit kit** (`dataverse/`), and is wired into the repo's **monthly CI refresh** (`.github/workflows/`). Each is tracked by a roadmap issue.

- **`pipelines/reservoir-storage/`** ([#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9)) — **built.** Liberates Colorado **reservoir storage** (volume, elevation, release) from **CO DWR/CDSS** and **USBR Reclamation RISE** into a tidy, day-resolution CSV with full per-site history (118 major reservoirs + 20 RISE), per-extract provenance, a concept catalog (vertical-datum / capacity caveats), and a reconciliation spot-check. Notebook-driven (`reservoir-pipeline.ipynb`) over a tested `reservoir` package. *Northern Water's hub publishes only boundaries, so its C-BT reservoirs are sourced from RISE.* See its [README](pipelines/reservoir-storage/README.md) and [AGENTS.md](pipelines/reservoir-storage/AGENTS.md).
- **`pipelines/streamflow/`** ([#10](https://github.com/CUPIDS-Lab/co-environmental-data/issues/10)) — **built.** Liberates Colorado **stream/river flow** (daily mean discharge, cfs) from **USGS NWIS** and **CO DWR/CDSS surface water** into a tidy, day-resolution CSV with full per-gage history (33 curated major-river gages across all 8 basins, each with its DWR mirror), per-extract provenance, a concept catalog, and an automatic **cross-source reconciliation**. Notebook-driven (`streamflow-pipeline.ipynb`) over a tested `streamflow` package. *DWR re-serves many USGS gages (joined via `usgs_site_no`) and often extends them past USGS discontinuation — de-duplicate to one series per gage; the overlap doubles as a built-in accuracy check.* See its [README](pipelines/streamflow/README.md) and [AGENTS.md](pipelines/streamflow/AGENTS.md).
- **`pipelines/snowpack/`** ([#11](https://github.com/CUPIDS-Lab/co-environmental-data/issues/11)) — **built.** Liberates Colorado **snowpack** (snow water equivalent, snow depth, water-year precip accumulation — inches) from the **NRCS AWDB REST API** across two networks — **SNOTEL** (automated daily, record since ~1980) and **snow courses** (manual semimonthly, many back to the 1930s–40s) — into a tidy, day-resolution CSV with full per-station history (199 stations across every CO basin), per-extract provenance, a concept catalog, the headline **basin percent-of-normal** product, and a SNOTEL↔snow-course **co-location reconciliation**. Notebook-driven (`snowpack-pipeline.ipynb`) over a tested `snowpack` package. *SNOTEL and snow courses are nearby-not-identical sites — complementary (snow courses extend the record before SNOTEL), not duplicate; AWDB needs no API key.* See its [README](pipelines/snowpack/README.md) and [AGENTS.md](pipelines/snowpack/AGENTS.md).

> **Publication is gated by QA.** Before any pipeline's data is deposited, its output must clear the bulletproofing + responsible-data checklists. The 2026-06-22 audit ([`audits/2026-06-22-qa-audit.md`](audits/2026-06-22-qa-audit.md)) found the reservoir output **not yet publish-ready** — the reconciliation is stubbed and the output carries impossible values — so the first Dataverse deposit (#36) is **blocked** on #38–#40.

## Getting started

```bash
git clone https://github.com/CUPIDS-Lab/co-environmental-data.git
cd co-environmental-data
```

The current deliverable is a documented dataset, not yet a runnable pipeline. To explore the catalog:

```bash
# 56 sources, 6 themes, 3 provenance tiers — see DATA-DICTIONARY.md for the schema
python3 -m json.tool data/raw/colorado_environmental_data_sources.json | less
```

The reproducible pipeline (pinned environment, the `cejcorpus` package, notebooks `nb-00`…`nb-09`) is the L2 build — specified in `context/architecture.md` and tracked in `ROADMAP.md`.

## Data access

Processed, non-sensitive data is shared in open formats under the access tiers in `GOVERNANCE.md`. See `DATA-DICTIONARY.md` for the schema; a published open-knowledge catalog (Datasette + Quarto site, OKF bundle) is planned — see `ROADMAP.md`. Note: the planned news corpus will introduce copyright (fair-use TDM) and journalist-privacy considerations; those duties are now encoded in `GOVERNANCE.md`, `responsible-data-checklist.md`, and `contributed-data-intake.md`, and the **blocking** items in `ROADMAP.md` (#32–#36) must be satisfied before any article text or journalist records are ingested.

## Documentation

- `DATA-DICTIONARY.md` — variables, grain, provenance, units, missingness, known issues.
- `decision-log.md` — why key choices were made.
- `CHANGELOG.md` — what changed and when.
- `context/` — methodology memo, technical architecture, and the source-inventory discovery audit behind the catalog.

**Collaboration & governance (L3):** `CONTRIBUTING.md` (how to work here) · `CODE_OF_CONDUCT.md` · `ROLES.md` + `.github/CODEOWNERS` (who owns what) · `GOVERNANCE.md` (access tiers, retention, remedy) · `CHARTER.md` (partners, shared definitions, what survives the pilot) · `collaboration-protocol.md` · `contributed-data-intake.md` (the licensed-database manual-export workflow) · `.skills/` (nested agent guidance).

**Responsible data & accessibility (L4):** `INSTALLED-BASE.md` (the values spine as repo requirements) · `data-management-plan.md` · `responsible-data-checklist.md` · `data-bulletproofing-checklist.md` · `data-quality-checklist.md` · `accessibility-checklist.md` · `data-card.md` (dataset transparency summary).

**Quality & onboarding:** `GLOSSARY.md` (acronyms & terms) · `audits/` — point-in-time QA audits of the data deliverables; see [`audits/2026-06-22-qa-audit.md`](audits/2026-06-22-qa-audit.md), which records what currently blocks the first publish.

## Citation

If you use this project, please cite it. Brian Keegan et al., *Colorado Environmental Data Hub*, CUPIDS Lab, 2026.

## License

Released under the MIT License. See `LICENSE`.

## Contact

Brian Keegan · accounts@brianckeegan.com · CUPIDS Lab.
