# ROADMAP — this level's work and what's deferred

This project was scaffolded at level **L1**, deliberately right-sized. It records both the work being tracked now (assignable, below) and the concerns deferred to future levels, so nothing important is lost and the next maintainer — or agent — knows what to do now and what to add later. The full methodology and technical design for most deferred items already exist in `context/` — `methodology.md` (research design), `architecture.md` (the pipeline), and `source-inventory.md` (the discovery audit).

## This level's work (assignable)

The actionable-now slice of the roadmap: harden the catalog, then stand up the pipeline. Each row is a checkbox you can assign and track; check it when its definition-of-done is met. The full definition-of-done lives in the linked issue.

| ✓ | Task | Owner | Priority | Size | Definition of done | Blocking? | Level | Links |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ☐ | Verify the 9 `needs_followup` sources | _unassigned_ | High | M | 9 sources confirmed live and flipped to `verified` | **Yes** | L1 | [#2](https://github.com/CUPIDS-Lab/co-environmental-data/issues/2) |
| ☐ | Quarantine the spurious NREL `nlr.gov` claim | _unassigned_ | High | S | `nrel.gov` confirmed canonical; `nlr.gov` absent everywhere | **Yes** | L1 | [#3](https://github.com/CUPIDS-Lab/co-environmental-data/issues/3) |
| ☐ | Add `match_hosts` / `match_keywords` to the catalog | @brianckeegan | High | M | both fields on every source; matcher unit-tested | **Yes** | L2 | [#4](https://github.com/CUPIDS-Lab/co-environmental-data/issues/4) |
| ☐ | Build the L2 reproducible pipeline (cejcorpus stubs) | @brianckeegan | Med | L | env + package + `nb-00…09` stubs + tests + CI dry-run | No | L2 | [#5](https://github.com/CUPIDS-Lab/co-environmental-data/issues/5) |
| ☐ | Liberate CO water data — reservoir, streamflow, snowpack (*Water data liberation* milestone) | _unassigned_ · help-wanted | High | L | series retrieved, tidied, documented, reconciled vs. source, republished to Datasette | No | L2 | [#7](https://github.com/CUPIDS-Lab/co-environmental-data/issues/7) |

**Tracking:** this checklist is the source of truth for the current work. It is mirrored as GitHub Issues #2–#5 and #7 on the **Colorado Environmental Data Hub** [Project board](https://github.com/orgs/CUPIDS-Lab/projects/1) — see `PROJECT-MANAGEMENT.md`. Edit this checklist and re-run `.github/seed-github.sh` (or `data-project track`) to create-or-update the issues idempotently; the checklist stays canonical. The two `good-first-issue` rows are left unassigned for incoming undergraduate contributors.

> **Epic #7 breaks into per-domain sub-issues:** [#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9) reservoir storage · [#10](https://github.com/CUPIDS-Lab/co-environmental-data/issues/10) stream/river flow · [#11](https://github.com/CUPIDS-Lab/co-environmental-data/issues/11) snowpack (SWE) — each a retrieve → tidy → document → audit → publish slice, linked as native GitHub sub-issues of #7.

## Deferred items

Concerns that are real but above the current tracked work — added when you climb. The design for most already exists in `context/`.

| Concern | Why deferred | Adds it (template / level) | Blocking? |
| --- | --- | --- | --- |
| **Codebook + inter-coder reliability** (Krippendorff α ≥ 0.80; double-code ~10%) | No human coding of citations yet | L2/L3 (`context/methodology.md` §4.2) | **Blocking** before coding begins |
| **Collaboration scaffolds** — `CONTRIBUTING`, `CODE_OF_CONDUCT`, `ROLES`+`CODEOWNERS`, `GOVERNANCE`, `CHARTER`, `collaboration-protocol` | Single-maintainer today; the undergraduate team is not yet onboarded | L3 | **Blocking** before onboarding the student team |
| **Contributed / licensed-data intake** — CU Libraries (Nexis Uni, NewsBank, ProQuest, Factiva) manual-export workflow | No article ingest yet; these DBs forbid automated download (ToS) and strip hyperlinks | L3 (`contributed-data-intake`) | **Blocking** before library-DB ingest |
| **Responsible-data + copyright/fair-use posture** — metadata + excerpts + archived links (never full text); journalist correction / right-to-respond | Current catalog is public agency metadata; duties attach when article text + journalist records are ingested | L4 (`responsible-data-checklist`, `data-management-plan`, `INSTALLED-BASE`) | **Blocking** before ingesting article text or journalist records |
| **Data-quality + bulletproofing checklists** — boilerplate false positives, syndication dedupe, link-rot archiving, reconcile against source totals | QA matters at analysis/publication; pre-pilot today | L4 (`data-bulletproofing-checklist`, `data-quality-checklist`) | **Blocking** before publishing findings |
| **LLM-detector validation** — precision/recall vs. gold standard, quote-span hallucination guard, closed-set constraint | No detector running yet; load-bearing for defensibility (`context/methodology.md` §4.5) | L4 (QA) | **Blocking** before promoting LLM labels as authoritative |
| **Accessibility** — alt text, plain-language summaries, colorblind-safe viz for the public site | No public site yet | L4 (`accessibility-checklist`) | No |
| **Open-knowledge publication** — OKF `knowledge/` bundle, Datasette catalog + Quarto site, `LICENSE-NOTE`, `data-collaborative-canvas` | Publish after the pilot clears its exit thresholds (`context/methodology.md` §7) | L5 | No |

## How to climb a level

Re-run the `data-project` skill in this directory and ask to climb to the next level (e.g. "take this to L2"). The skill adds only the new level's artifacts, refreshes this roadmap, and files the new level's tasks as issues. Items marked **blocking** must be resolved — or explicitly acknowledged — before the project does the thing they guard (e.g. before relying on unverified sources, running citation detection, or publishing), and before climbing.

## Note on future-sensitive work (do not skip)

The data in this repo today is public, so the full sensitive-data governance coupling was intentionally **not** generated at L1. But the planned news corpus introduces two duties that must travel with the affordances they guard: **copyright/fair-use** (the public site shows metadata + excerpts + archived links, never republished article text) and **journalist privacy** (professional information only; a documented correction / right-to-respond process). The deferred rows marked *blocking before ingesting article text or journalist records* encode this — resolve them (climb to L3/L4) before building the corpus, not after. Affordances without duties are theater.
