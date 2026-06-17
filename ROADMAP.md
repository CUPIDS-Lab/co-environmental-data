# ROADMAP — what's deferred and how to add it

This project was scaffolded at level **L1**, deliberately right-sized. This file records concerns that are real but not built yet, so nothing important is lost and the next maintainer (or agent) knows exactly what to add and when. Building less now and documenting the rest here is the intended workflow, not a shortcut.

The full methodology and technical design for most of the items below already exist in `context/` — `methodology.md` (research design), `architecture.md` (the pipeline), and `source-inventory.md` (the discovery audit). This roadmap points at them.

## How to climb a level

Re-run the `data-project` skill in this directory and ask to climb to the next level (e.g. "take this to L2"). The skill will add only the new level's artifacts and update this roadmap. Items marked **blocking** below should be resolved before the project does the thing they guard (e.g. before ingesting article text, onboarding the team, or publishing).

## Deferred items

| Concern | Why deferred | Adds it (template / level) | Blocking? |
| --- | --- | --- | --- |
| **Reproducible pipeline** — pinned env, the `cejcorpus` package, notebooks `nb-00`…`nb-09`, `config.yaml`, `tests/`, CI dry-run | Today's asset is a static catalog; the journalist→article→citation pipeline (fully specified in `context/architecture.md`) is the next build | L2 (`python/` env + `Snakefile`/notebooks, `src/cejcorpus/`, `tests/`, `ci/`) | No |
| **Add `match_hosts` / `match_keywords` to the catalog** | Required by the Stage-A URL matcher and the keyword detector; not present in the JSON yet | L2 (dictionary stage, `context/architecture.md` §6 nb-04) | **Blocking** before Stage-A citation detection |
| **Verify the 9 `needs_followup` sources + quarantine the NREL "nlr.gov" claim** | 9 of 56 sources unconfirmed; the spurious NREL rebrand must never enter the dictionary | L1/L2 data-quality follow-up (`context/source-inventory.md` caveats) | **Blocking** before relying on those sources |
| **Codebook + inter-coder reliability protocol** (Krippendorff α ≥ 0.80; double-code ~10%) | Needed before any human coding of citations; corpus not yet ingested | L2/L3 (lives with pipeline + collaboration docs; `context/methodology.md` §4.2) | **Blocking** before coding begins |
| **Collaboration scaffolds** — `CONTRIBUTING`, `CODE_OF_CONDUCT`, `ROLES`+`CODEOWNERS`, `GOVERNANCE`, `CHARTER`, `collaboration-protocol` | Single-maintainer today; the undergraduate research team is not yet onboarded | L3 | **Blocking** before onboarding the student team |
| **Contributed / licensed-data intake** — CU Libraries (Nexis Uni, NewsBank, ProQuest, Factiva) manual-export workflow | No article ingest yet; these databases forbid automated download (ToS) and strip hyperlinks | L3 (`contributed-data-intake`) | **Blocking** before library-DB ingest |
| **Responsible-data + copyright/fair-use posture** — store metadata + excerpts + archived links (never full text); journalist correction / right-to-respond mechanism | Current catalog is public agency metadata; these duties attach when article text + journalist records are ingested | L4 (`responsible-data-checklist`, `data-management-plan`, `INSTALLED-BASE`) | **Blocking** before ingesting article text or journalist records |
| **Data-quality + bulletproofing checklists** — boilerplate/footer false positives, syndication dedupe, link-rot archiving at coding time, reconcile against source totals | QA matters at analysis/publication; pre-pilot today | L4 (`data-bulletproofing-checklist`, `data-quality-checklist`) | **Blocking** before publishing findings |
| **LLM-detector validation** — precision/recall vs. gold standard, quote-span hallucination guard, closed-set constraint | No detector running yet; load-bearing for defensibility (`context/methodology.md` §4.5) | L4 (QA) | **Blocking** before promoting LLM labels as authoritative |
| **Accessibility** — alt text, plain-language summaries, colorblind-safe viz for the public site | No public site yet | L4 (`accessibility-checklist`) | No |
| **Open-knowledge publication** — OKF `knowledge/` bundle, Datasette catalog + Quarto site, `LICENSE-NOTE`, `data-collaborative-canvas` | Publish after the pilot clears its exit thresholds (`context/methodology.md` §7) | L5 (`knowledge/` OKF, `LICENSE-NOTE`, canvases) | No |

## Note on future-sensitive work (do not skip)

The data in this repo today is public, so the full sensitive-data governance coupling was intentionally **not** generated at L1. But the planned news corpus introduces two duties that must travel with the affordances they guard: **copyright/fair-use** (the public site shows metadata + excerpts + archived links, never republished article text) and **journalist privacy** (professional information only; a documented correction / right-to-respond process). The rows above marked *blocking before ingesting article text or journalist records* encode this — resolve them (climb to L3/L4) before building the corpus, not after. Affordances without duties are theater.
