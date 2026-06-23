# Colorado Environmental Data Hub

A documented, reproducible catalog of Colorado environmental data sources — and the foundation for a research corpus linking Colorado environmental journalists to the public data they cite.

A CUPIDS Lab data project. Maturity level: **L4** (collaborative, responsible & accessible). Toolchain: **Python (Datasette · Cloudflare R2 · Quarto · Prefect)**. Sensitivity: **Public today (open government/agency metadata); conditionally sensitive-human once the news corpus ingests article text + journalist records**. Openness: **Open (MIT-licensed; open data)**.

## What & why

Colorado's environmental data lives in dozens of federal, state, and local systems — and in 2025–2026 a meaningful slice of it is **eroding** (datasets removed or decommissioned) or **enclosing** (paywalled, login-gated, vendor-mediated). This project does two things:

1. **Now (this repo):** maintains a curated **catalog of ~56 authoritative Colorado environmental data sources** across six themes (water, fire, wind, minerals, pollution, land use) and three provenance tiers (federal, state, local/regional), each flagged for *enclosure* and *erosion* risk. The catalog is the real, documented dataset this repository ships today.
2. **Next (see [`ROADMAP.md`](docs/planning/ROADMAP.md)):** uses that catalog as the backbone of a **journalist → article → data-citation corpus** — measuring which Colorado environmental journalists cite which public datasets, 2014–present. The full methodology and technical architecture for that build are in `context/`.

- **Design partners (who builds it):** the CUPIDS Lab undergraduate research team and Center for Environmental Journalism (CEJ) collaborators.
- **Beneficiaries (who it serves):** environmental journalists, researchers studying data-driven reporting, and the Colorado public — plus future maintainers who can re-verify every source.
- **Success looks like:** a catalog whose every source is independently verifiable, and a corpus whose every citation is archived and defensible.

## Repository layout

This repo follows the CUPIDS Lab data-project conventions. **Code & data:** `data/raw` holds original, **immutable** source data (never edited in place) — currently the curated source catalog; `data/interim` and `data/processed` hold derived data that can always be regenerated from raw; **`pipelines/<name>/`** holds self-contained data-liberation pipelines (one per liberated dataset), and **`pipelines/_core/`** is the shared [`co_pipeline_core`](pipelines/_core/README.md) library they all build on (provenance · fetch · clean · schema · audit, extracted in #54); `context/` holds the project's design memos (methodology, architecture, source-inventory audit, proposals). **Documentation & governance:** the catalog schema is [`docs/reference/DATA-DICTIONARY.md`](docs/reference/DATA-DICTIONARY.md), and the planning, reference, governance, and responsible-data docs are organized under **[`docs/`](docs/)** — indexed in [Documentation](#documentation) below; the nested `.skills/` give downstream agents task-specific guidance (data intake, documentation, release). See [`docs/planning/ROADMAP.md`](docs/planning/ROADMAP.md) for what is planned but not yet built (the corpus pipeline and the L5 open-knowledge publication layer).

## Pipelines

The Hub hosts self-contained **data-liberation pipelines** under `pipelines/<name>/` — each liberates one dataset into a tidy, documented CSV, ships a Harvard **Dataverse deposit kit** (`dataverse/`), and is wired into the repo's **monthly CI refresh** (`.github/workflows/`). Each is tracked by a roadmap issue. All four are thin domain packages over the shared [`co_pipeline_core`](pipelines/_core/README.md) library (`pipelines/_core/`): provenance, the fetch engine, clean orchestration, schema normalization, and audit profiling live there once (#54), so a fix lands for every pipeline at once.

- **`pipelines/reservoir-storage/`** ([#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9)) — **built.** Liberates Colorado **reservoir storage** (volume, elevation, release) from **CO DWR/CDSS** and **USBR Reclamation RISE** into a tidy, day-resolution CSV with full per-site history (118 major reservoirs + 20 RISE), per-extract provenance, a concept catalog (vertical-datum / capacity caveats), and a reconciliation spot-check. Notebook-driven (`reservoir-pipeline.ipynb`) over a tested `reservoir` package. *Northern Water's hub publishes only boundaries, so its C-BT reservoirs are sourced from RISE.* See its [README](pipelines/reservoir-storage/README.md) and [AGENTS.md](pipelines/reservoir-storage/AGENTS.md).
- **`pipelines/streamflow/`** ([#10](https://github.com/CUPIDS-Lab/co-environmental-data/issues/10)) — **built.** Liberates Colorado **stream/river flow** (daily mean discharge, cfs) from **USGS NWIS** and **CO DWR/CDSS surface water** into a tidy, day-resolution CSV with full per-gage history (33 curated major-river gages across all 8 basins, each with its DWR mirror), per-extract provenance, a concept catalog, and an automatic **cross-source reconciliation**. Notebook-driven (`streamflow-pipeline.ipynb`) over a tested `streamflow` package. *DWR re-serves many USGS gages (joined via `usgs_site_no`) and often extends them past USGS discontinuation — de-duplicate to one series per gage; the overlap doubles as a built-in accuracy check.* See its [README](pipelines/streamflow/README.md) and [AGENTS.md](pipelines/streamflow/AGENTS.md).
- **`pipelines/snowpack/`** ([#11](https://github.com/CUPIDS-Lab/co-environmental-data/issues/11)) — **built.** Liberates Colorado **snowpack** (snow water equivalent, snow depth, water-year precip accumulation — inches) from the **NRCS AWDB REST API** across two networks — **SNOTEL** (automated daily, record since ~1980) and **snow courses** (manual semimonthly, many back to the 1930s–40s) — into a tidy, day-resolution CSV with full per-station history (199 stations across every CO basin), per-extract provenance, a concept catalog, the headline **basin percent-of-normal** product, and a SNOTEL↔snow-course **co-location reconciliation**. Notebook-driven (`snowpack-pipeline.ipynb`) over a tested `snowpack` package. *SNOTEL and snow courses are nearby-not-identical sites — complementary (snow courses extend the record before SNOTEL), not duplicate; AWDB needs no API key.* See its [README](pipelines/snowpack/README.md) and [AGENTS.md](pipelines/snowpack/AGENTS.md).
- **`pipelines/climate-stations/`** ([#44](https://github.com/CUPIDS-Lab/co-environmental-data/issues/44)) — **built.** Liberates Colorado **daily climate-station** observations — temperature (max/mean/min), precipitation, snowfall / snow depth / SWE, pan evaporation, solar radiation, vapor pressure, wind run (**twelve** measurement types) — from the **CO DWR/CDSS** Climate Station Time Series API into a tidy, day-resolution CSV with full per-station history, per-extract provenance, and a concept catalog (units harmonized **per measType**). Notebook-driven (`climate-stations-pipeline.ipynb`) over a tested `climate_stations` package. *One API federates five networks (NOAA COOP/GHCN, CoCoRaHS, NRCS/SNOTEL, CoAgMet, NCWCD); the committed 40-station seed is expandable to the full ~4,962-station catalog; an apiKey is effectively required (anonymous pulls hit a daily-data limit).* See its [README](pipelines/climate-stations/README.md) and [AGENTS.md](pipelines/climate-stations/AGENTS.md).

> **Publication is gated by QA.** Before any pipeline's data is deposited, its output must clear the bulletproofing + responsible-data checklists. The 2026-06-22 audit ([`audits/2026-06-22-qa-audit.md`](audits/2026-06-22-qa-audit.md)) found the reservoir output **not yet publish-ready** — the reconciliation is stubbed and the output carries impossible values — so the first Dataverse deposit (#36) is **blocked** on #38–#40.

## Getting started

```bash
git clone https://github.com/CUPIDS-Lab/co-environmental-data.git
cd co-environmental-data
```

Two kinds of deliverable ship today: the **source catalog** and four **liberated datasets** (the pipelines above). To explore the catalog:

```bash
# 56 sources, 6 themes, 3 provenance tiers — see DATA-DICTIONARY.md for the schema
python3 -m json.tool data/raw/colorado_environmental_data_sources.json | less
```

To run a built pipeline (each is self-contained under `pipelines/<name>/`):

```bash
cd pipelines/snowpack          # or reservoir-storage | streamflow | climate-stations
uv sync && uv run pytest       # pinned env + offline tests
uv run python -m snowpack.pipeline --mode demo --fresh   # offline end-to-end; --mode live for the real pull
```

The journalist→citation **corpus** pipeline (the `cejcorpus` package, notebooks `nb-00`…`nb-09`) is a separate, **not-yet-built** L2 effort — specified in `context/architecture.md` and tracked in [`ROADMAP.md`](docs/planning/ROADMAP.md).

## Data access

Processed, non-sensitive data is shared in open formats under the access tiers in [`GOVERNANCE.md`](docs/governance/GOVERNANCE.md). See [`DATA-DICTIONARY.md`](docs/reference/DATA-DICTIONARY.md) for the schema; a published open-knowledge catalog (Datasette + Quarto site, OKF bundle) is planned — see [`ROADMAP.md`](docs/planning/ROADMAP.md). Note: the planned news corpus will introduce copyright (fair-use TDM) and journalist-privacy considerations; those duties are now encoded in [`GOVERNANCE.md`](docs/governance/GOVERNANCE.md), [`responsible-data-checklist.md`](docs/responsible-data/responsible-data-checklist.md), and [`contributed-data-intake.md`](docs/governance/contributed-data-intake.md), and the **blocking** items in [`ROADMAP.md`](docs/planning/ROADMAP.md) (#32–#36) must be satisfied before any article text or journalist records are ingested.

## Documentation

Repository documentation lives in a **[`docs/`](docs/) tree** — the root keeps only `README`, `AGENTS`, `CHANGELOG`, `CONTRIBUTING`, and `CODE_OF_CONDUCT`:

| Folder | What's inside |
| --- | --- |
| **[`docs/planning/`](docs/planning/)** | [ROADMAP](docs/planning/ROADMAP.md) — assignable work + what's deferred · [NEXT-STEPS](docs/planning/NEXT-STEPS.md) — plain-language handoff memo · [PROJECT-MANAGEMENT](docs/planning/PROJECT-MANAGEMENT.md) — how we track work |
| **[`docs/reference/`](docs/reference/)** | [DATA-DICTIONARY](docs/reference/DATA-DICTIONARY.md) — catalog schema, grain, provenance, known issues · [GLOSSARY](docs/reference/GLOSSARY.md) — acronyms & terms · [decision-log](docs/reference/decision-log.md) — why key choices were made |
| **[`docs/governance/`](docs/governance/)** — L3 | [GOVERNANCE](docs/governance/GOVERNANCE.md) — access tiers, retention, remedy · [CHARTER](docs/governance/CHARTER.md) — partners, shared definitions, what survives the pilot · [ROLES](docs/governance/ROLES.md) + [`.github/CODEOWNERS`](.github/CODEOWNERS) — who owns what · [collaboration-protocol](docs/governance/collaboration-protocol.md) · [contributed-data-intake](docs/governance/contributed-data-intake.md) — licensed-database manual-export workflow |
| **[`docs/responsible-data/`](docs/responsible-data/)** — L4 | [INSTALLED-BASE](docs/responsible-data/INSTALLED-BASE.md) — values spine as repo requirements · [data-management-plan](docs/responsible-data/data-management-plan.md) · [data-card](docs/responsible-data/data-card.md) — dataset transparency summary · checklists: [responsible-data](docs/responsible-data/responsible-data-checklist.md) · [data-bulletproofing](docs/responsible-data/data-bulletproofing-checklist.md) · [data-quality](docs/responsible-data/data-quality-checklist.md) · [accessibility](docs/responsible-data/accessibility-checklist.md) |

Also: `CONTRIBUTING.md` (how to work here) · `CODE_OF_CONDUCT.md` · `CHANGELOG.md` (what changed and when) · [`context/`](context/) (methodology memo, technical architecture, source-inventory audit) · `.skills/` (nested agent guidance) · [`audits/`](audits/) — point-in-time QA audits; see [`audits/2026-06-22-qa-audit.md`](audits/2026-06-22-qa-audit.md) (reservoir — what blocks the first publish) and [`audits/2026-06-23-pipelines-qa.md`](audits/2026-06-23-pipelines-qa.md) (streamflow / snowpack / climate-stations on the shared core).

## Citation

If you use this project, please cite it. Brian Keegan et al., *Colorado Environmental Data Hub*, CUPIDS Lab, 2026.

## License

Released under the MIT License. See `LICENSE`.

## Contact

Brian Keegan · accounts@brianckeegan.com · CUPIDS Lab.
