# AGENTS.md — guidance for agents and humans working in this repo

Read this first. It states the non-negotiables and points you at the right place for each task. This repo was scaffolded with the CUPIDS Lab `data-project` skill at level **L1** and **climbed to L4** (collaboration + responsible-data & accessibility) on 2026-06-22. For task-specific guidance, the nested `.skills/` (`data-intake`, `documentation`, `release-and-share`) tell you the rules before you ingest, document, or publish.

## Non-negotiables

- **Raw data is immutable.** Never edit anything under `data/raw/` in place — including `colorado_environmental_data_sources.json`. Read it, write derived data to `data/interim/` or `data/processed/`. A new catalog vintage is a new file, not an in-place edit. Anything derived must be reproducible from raw.
- **Open, version-controllable formats.** Prefer plain text, CSV/Parquet, JSON, Markdown, and text-based pipeline definitions. Do not introduce a vendor-locked artifact as a required dependency; anything a hosted tool produces (Datasette, R2, Quarto) must be exportable.
- **Provenance lives with the data.** Record where data came from, its license, and any transformations in `DATA-DICTIONARY.md` and `decision-log.md`. Every source in the catalog carries `verification_status`; do not silently rely on a `needs_followup` source.
- **Secrets and sensitive data never land in the repo.** Keep credentials out of code and notebooks (`.env` is git-ignored). The planned news corpus introduces copyright (fair-use: metadata + excerpts + archived links, **never** republished full text) and journalist-privacy duties — these are now encoded as access tiers in `GOVERNANCE.md` and a `responsible-data-checklist.md`; satisfy the **blocking** items in `ROADMAP.md` (#32–#36) before ingesting article text or journalist records. Licensed-database content (Nexis Uni, ProQuest, NewsBank, Factiva) is manual-export-only and **restricted** — never committed or redistributed (`contributed-data-intake.md`).

## Where things are

- Source data and derived outputs: `data/`. Schema: `DATA-DICTIONARY.md`.
- Project design memos (methodology, technical architecture, source-inventory audit, grant proposals): `context/`. Read these before extending the project — the corpus pipeline is already specified there.
- **Data-liberation pipelines:** `pipelines/<name>/` — one self-contained pipeline per liberated dataset, each with its own `AGENTS.md`, a Dataverse deposit kit (`dataverse/`), and a slot in the monthly CI refresh (`.github/workflows/`). Four are built: `pipelines/reservoir-storage/` ([#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9)), `pipelines/streamflow/` ([#10](https://github.com/CUPIDS-Lab/co-environmental-data/issues/10), USGS NWIS + DWR/CDSS surface water; note the DWR/USGS source overlap and CDSS 403 throttle documented in its AGENTS.md), `pipelines/snowpack/` ([#11](https://github.com/CUPIDS-Lab/co-environmental-data/issues/11), NRCS SNOTEL + snow courses via the AWDB API — no key; note the two networks are nearby-not-identical, complementary not duplicate), and `pipelines/climate-stations/` ([#44](https://github.com/CUPIDS-Lab/co-environmental-data/issues/44), CO DWR/CDSS daily climate — twelve measTypes across five networks; apiKey effectively required). **Read a pipeline's own `AGENTS.md` before touching it.** New pipelines stamp out from these.
- **How we work together:** `CONTRIBUTING.md` (branch/PR/review, env setup), `ROLES.md` + `.github/CODEOWNERS` (who reviews what), `GOVERNANCE.md` (access tiers, retention, remedy), `CHARTER.md`, `CODE_OF_CONDUCT.md`.
- **The data's duties:** before ingesting, publishing, or sharing, read the matching nested skill in `.skills/` and the relevant L4 checklist — `responsible-data-checklist.md`, `data-bulletproofing-checklist.md`, `data-quality-checklist.md`, `accessibility-checklist.md`; `INSTALLED-BASE.md` and `data-management-plan.md` set the standing requirements.
- **Glossary & QA audits:** `GLOSSARY.md` defines the acronyms (CDSS, RISE, DWR, SWE, TDM, …); `audits/` holds point-in-time QA audits of the data — the [2026-06-22 audit](audits/2026-06-22-qa-audit.md) records what blocks publication (notably the reservoir reconciliation is stubbed — #38 — so do **not** treat `pipelines/reservoir-storage/data/processed` as publish-ready yet).
- What's planned but not built yet: `ROADMAP.md`.

## How we work

The repository is a **documented catalog** plus a growing set of **data-liberation pipelines** under `pipelines/<name>/` (four are built — reservoir-storage #9, streamflow #10, snowpack #11, climate-stations #44 — live against public agency APIs, with a monthly CI refresh and Dataverse deposit kits). Each pipeline is thin notebooks over a tested `src/<pkg>/` package: explore, then package reusable code at the exploration boundary. The journalist→citation **corpus** pipeline (`context/architecture.md`) is still to be built (the `cejcorpus` package, notebooks `nb-00…09`). Pipelines are code (re-runnable), not cleaned snapshots. Pin environments so others — and other agents — can reproduce results. Stamp every row a stage writes with a `run_id`, and archive every cited URL at coding time.

## Working in a shared tree with other agents

Multiple agents and sessions operate on this repo's **single working tree concurrently**. Untracked work-in-progress is vulnerable to another agent's broad `git add`, rebase, or branch switch — on 2026-06-23 a snowpack PR swept another agent's untracked `pipelines/climate-stations/` files into its commit (PR #45, repaired by #46, re-landed correctly via #48). To stay isolated:

- **Build each commit/PR in its own git worktree off freshly-fetched `origin/main`:** `git fetch && git worktree add -b <branch> /tmp/<dir> origin/main`. A branch switch by another agent then can't disturb your work.
- **Stage explicit paths** (`git add pipelines/<name> path/to/file`) — **never `git add -A` / `git add .`** while the tree is dirty.
- **`git fetch` and re-verify `origin/main` immediately before merging** — the ground moves; check recent PRs and `git ls-tree origin/main -- <path>`. An audit or a merge run against a stale local checkout will mislead you.
- **One concern per PR.** Don't bundle a pipeline into a docs/governance PR (the streamflow ↔ #37 lesson).

## A data-integrity note (read before touching the catalog)

Compilation surfaced spurious search content claiming NREL was renamed "National Laboratory of the Rockies" with a `nlr.gov` domain. **This is unverified and almost certainly false.** Keep `nrel.gov` canonical and do not seed any dictionary or catalog field with `nlr.gov` without confirmation against an official DOE/NREL source. See `context/source-inventory.md` for the full caveat.
