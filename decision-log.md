# Decision log — Colorado Environmental Data Hub

A running, dated record of design and data decisions and *why* they were made — the provenance of the project's choices, legible to people who join later. Add an entry whenever you make a non-obvious choice (a filtering rule, a definition, a tool, a tradeoff). Newest first.

## 2026-06-19 — Monthly CI/CD refresh + Harvard Dataverse as the dataset's home of record

- **Context:** the reservoir-storage pipeline produces a tidy CSV that needs re-deriving as upstream telemetry updates, a durable home between (ephemeral) runs, and a citable archive. Asked to automate a monthly refresh and to integrate the Dataverse deposit that landed in `data-project-skill` [PR #7](https://github.com/CUPIDS-Lab/data-project-skill/pull/7).
- **Decision:** schedule the refresh with **GitHub Actions** (monthly cron, matrix-per-pipeline) running a **full rebuild** — the composite-key de-dup in `clean.run` makes a rebuild a superset-append that also self-heals upstream revisions. Adopt **Harvard Dataverse** as the canonical home (citable DOI) via the skill's deposit kit, rendered into `pipelines/reservoir-storage/dataverse/`. CI **validates** the kit every run and deposits only a **draft** (opt-in `DATAVERSE_DEPOSIT`), **never** minting/publishing a DOI unattended.
- **Why:** a monthly batch doesn't justify a long-running Prefect agent; Actions is native, free, and secret-aware. Full rebuild is the simplest correct thing (and needs no restored prior CSV). Dataverse gives FAIR, citable archiving; the skill's hard rule — a deposit stops at a draft, publish only on explicit confirmation, since a DOI is permanent — is preserved by keeping CI draft-only and human-gated.
- **Consequences:** the first deposit creates the dataset (human reviews + publishes v1.0); recurring monthly updates should target that existing dataset (a new version, not a new DOI) via the `data-project-depositor` idempotent workflow — until configured, `DATAVERSE_DEPOSIT` stays off so the job validates without draft clutter. Needs repo config: `DATAVERSE_COLLECTION` (real alias), `DATAVERSE_API_TOKEN` (secret), optional `CDSS_API_KEY`. Streamflow (#10) / snowpack (#11) inherit the pattern with a one-line matrix add + their own `dataverse/` kit.

## 2026-06-19 — First data-liberation pipeline (reservoir storage) under `pipelines/`

- **Context:** issue #9 (reservoir storage) was the first slice of the water-liberation epic (#7) to be built, using the `data-liberation` skill.
- **Decision:** scaffold it as a **self-contained pipeline under `pipelines/reservoir-storage/`** — thin notebooks over a tested `src/reservoir/` package — establishing the **`pipelines/<name>/` convention** for liberated datasets. Sources: CO DWR/CDSS + USBR Reclamation RISE (Northern Water resolved as **boundaries-only**; its C-BT reservoirs are sourced from RISE). Scope filtered to **118 major reservoirs** (recharge/ag ponds dropped). `data/original/` is treated as a **rebuildable cache**, not an archive. (The monthly CI refresh + Harvard Dataverse deposit added on top are recorded in the entry above.)
- **Why:** the Hub will host several liberated datasets (streamflow, snowpack, …); one pipeline per directory keeps them independent and individually testable. `src/<pkg>/` (over the data-liberation template's `scripts/`) matches the repo's package convention and keeps notebooks thin and testable.
- **Consequences:** `pipelines/<name>/` is the home for future datasets (#10/#11 stamp out from it, inheriting the CI + Dataverse pattern). The Hub stays **L1**; pipelines are data-liberation sub-projects, not Hub level-climbs. Full per-extract provenance, day-resolution grain, and concept caveats (vertical-datum / capacity) are the pipeline's documented contracts. See `pipelines/reservoir-storage/AGENTS.md`.

## 2026-06-18 — Project-manage the roadmap on GitHub (Track mode)

- **Context:** with the L1 scaffold merged, the next need was a shared, assignable work record so the undergraduate team can pick up tasks. Asked to add issues, a Project board, and a wiki.
- **Decision:** ran the `data-project` tracker in **Track mode** — projected the *actionable-now* slice of the roadmap (catalog hardening + L2 pipeline) onto GitHub as 4 issues (#2–#5) under one milestone, with the full label taxonomy; seeded the wiki; and prepared the Project board (pending a one-time `project` scope grant). Kept the `ROADMAP.md` checklist as the source of truth and GitHub as an idempotent projection (`.github/seed-github.sh` + `engagement-sync.json`).
- **Why:** the team needs assignable, trackable work, but the repo is still L1 — so this is Track mode, *not* an L3 climb. The real collaboration docs (`CONTRIBUTING`, `GOVERNANCE`, `ROLES`) remain deferred in the roadmap. Tracking only the actionable slice (not all 11 deferred items) keeps the board honest about what can be worked now. The two data-quality good-first-issues are left unassigned for incoming students.
- **Consequences:** editing the roadmap and re-running the seed script reconciles issues without duplicating. The Project board and the wiki push each need one human action (grant `project` scope; create the wiki's first page). Adding the PM layer does not by itself raise the maturity level.

## 2026-06-17 — Treat the source catalog as immutable raw, tracked in `data/raw/`

- **Context:** the curated catalog (`colorado_environmental_data_sources.json`) is small (~64 KB) and hand-compiled — more a curated source-of-record than a re-downloadable bulk file.
- **Decision:** place it in `data/raw/` and add a `.gitignore` carve-out so this one file is version-controlled, while the rest of `data/raw/*` stays ignored. New catalog vintages are new files, never in-place edits.
- **Why:** it is the project's actual tracked asset; versioning it gives a defensible history. The blanket "raw is git-ignored" convention assumes large/external inputs, which this is not.
- **Consequences:** the `context/` copy is retained as part of the design bundle; `data/raw/` is the canonical copy the data dictionary documents.

## 2026-06-17 — Frame the repo as the "Colorado Environmental Data Hub" (catalog now; corpus later)

- **Context:** the `context/` memos describe two layers — a source-inventory **catalog** (real data, present) and a journalist→article→citation **corpus** (specified as stubs in `architecture.md`).
- **Decision:** name the project the **Colorado Environmental Data Hub** (umbrella, matching the repo and the catalog JSON); document the catalog at L1 and record the corpus pipeline as the flagship L2+ roadmap initiative.
- **Why:** L1 documents what exists. The corpus is a future build; framing the Hub as the umbrella lets the catalog stand on its own while keeping the corpus discoverable in `ROADMAP.md`.
- **Consequences:** README/AGENTS center the catalog; the full pipeline lives in `ROADMAP.md` pointing at `context/architecture.md`.

## 2026-06-17 — Do not fire the full sensitive-data governance coupling at L1

- **Context:** the data present today is public agency metadata. The *planned* corpus will involve news article text (copyright) and journalist records (public figures acting professionally — low-risk per `context/methodology.md` §6.2), but neither is in the repo yet.
- **Decision:** keep L1 lean — no GOVERNANCE/responsible-data files now — but record the copyright/fair-use posture (metadata + excerpts + archived links, never republished full text) and the journalist correction/right-to-respond mechanism as **blocking** rows in `ROADMAP.md`.
- **Why:** generating governance scaffolds now would create dangling references and over-engineer a public catalog; dropping the duties silently would be worse. A named, blocking roadmap entry keeps the coupling honest without bloat. This is not a regulated/CARE/Indigenous-data case (which would force the coupling regardless of level).
- **Consequences:** before the corpus ingests article text or journalist PII, the project must climb to L3/L4 and satisfy those blocking items first.

## 2026-06-17 — Project scaffolded

- **Context:** project started with the CUPIDS Lab `data-project` skill at level L1.
- **Decision:** adopt the standard layout, immutable-raw-data convention, and the deferred-work roadmap; scaffold in place into the existing repo (replacing the stub README and `.gitignore`, keeping the MIT `LICENSE`).
- **Why:** right-sized, reproducible, and legible by default.
- **Consequences:** see `ROADMAP.md` for deferred concerns (the L2 pipeline, L3 collaboration, L4 responsible-data/QA, L5 open-knowledge publication).
