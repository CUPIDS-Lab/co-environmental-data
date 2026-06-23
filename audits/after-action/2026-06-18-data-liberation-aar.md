---
# Versioning
version: "1.0"
status: final
created: 2026-06-19
updated: 2026-06-19
# Provenance
title: "After-Action Report — first implementation of the data-liberation skill"
doc_type: after-action-report
subject_skill: data-liberation
project: "Colorado Environmental Data Hub -> pipelines/reservoir-storage"
repository: "CUPIDS-Lab/co-environmental-data"
author: "Claude (Opus 4.8 · claude-opus-4-8)"
generated_by: "Claude Code session"
basis: "First real-world build of the skill — ~14 PRs scaffolding and hardening the reservoir-storage pipeline (3 live API sources, full-history retrieval, dedup, publish-to-CSV)."
related:
  - audits/after-action/2026-06-18-data-project-aar.md
tags: [retrospective, aar, data-liberation, cupids]
---

# After-Action Report — first implementation of the `data-liberation` skill

**Project:** Colorado Environmental Data Hub → `pipelines/reservoir-storage/`
**Skill under review:** `data-liberation` (downstream sibling of `data-project`)
**Window:** scaffold a notebook pipeline for issue #9 → full live multi-source dataset
**Date:** 2026-06-19
**Author:** Claude (Opus 4.8), Claude Code session

---

## 1. What we set out to do

Use `/data-liberation` to scaffold a **retrieve → audit → cleanup → publish-to-CSV**
pipeline, as **Jupyter notebooks with strong documentation**, for issue #9 (Colorado
reservoir storage from three sources: CO DWR/CDSS, USBR Reclamation RISE, Northern
Water). Then make it produce a real, full-historical, multi-source dataset.

## 2. What got built

A self-contained pipeline under `pipelines/reservoir-storage/`:

- **Notebook driver** (`reservoir-pipeline.ipynb`) — four stages in one notebook, thin
  orchestration over a tested package.
- **`src/reservoir/`** package — `schema` (tidy-long pandera contract), `config`,
  `sources` (3 API clients), `fetch` (idempotent + paginating + progress), `clean`
  (orchestrator + reject port), `audit` (profile / coverage / reconcile), `provenance`,
  `stations` (entity enumeration), `parsers/`.
- **`data/{original,processed,audit,lookups}/`**, `docs/{survey-notes, data-dictionary,
  filter-pivot-recipes}`, tests, `pyproject.toml`, `README`, `AGENTS.md`.
- **3 live sources** wired (DWR/CDSS confirmed; RISE 17/20 reservoirs; Northern
  resolved as *not a storage source*), full-history retrieval, day-grain dedup, a
  concept catalog with datum/capacity caveats, and a reconciliation spot-check.

Net: ~14 merged PRs after the initial scaffold, mostly **live-API debugging**.

## 3. What worked well

- **Immutable originals + per-extract provenance** — exactly right. Raw API responses
  saved once; a `(source, vintage)` provenance sidecar; the CSV reconstructs from raw.
- **Tidy long as the storage shape** — `(source, reservoir_id, datetime, variable)`
  absorbed three very different sources cleanly; cross-source work is a `groupby`.
- **"Concepts carry caveats"** earned its keep. The **vertical-datum** caveat on
  elevation and the **capacity-baseline** caveat on storage are exactly the traps that
  produce cross-source misinformation; the skill's insistence on documenting them
  prevented a real error.
- **pandera schema as a boundary contract** caught the duplicate-key problem (even if it
  then over-dropped — see §4).
- **"Errors durable, not fatal"** kept a 280-series fetch alive through per-station
  404s and parse failures.
- **AGENTS.md-before-code** and the **six-phase framing** (Survey → Scaffold → Extract →
  Tidy → Audit → Publish) structured a long, messy effort.
- **Reconciliation against the source's own published total** was the right verification
  idea, and the **bulletproofing "probe the source, don't assume"** discipline is what
  ultimately cracked every API quirk.

## 4. Friction and gaps (with root causes)

1. **The template is a script-CLI; the ask was notebooks.** The skill's scaffold is
   `scripts/*.py` + a `pipeline.py` argparse CLI. The request — *"notebooks with good
   documentation"* — has no first-class variant, so the scaffold was **hand-written** as
   thin notebooks over a package. *Root cause:* notebook-first pipelines (common in data
   journalism and teaching) aren't a supported deliverable shape.

2. **`scripts/` vs `src/` rigidity.** The skill mandates `scripts/` ("not `src/` or
   `pipeline/`"); the build used `src/reservoir/` for testability, importability, and
   parent-repo consistency, and had to **document the deviation**. *Root cause:* the
   convention is rigid and conflicts with both notebooks+package and `data-project`'s
   `src/`.

3. **API sources are badly under-served — the single biggest gap.** The toolchain
   decision trees are **PDF / document / scrape-centric**. But the work that consumed
   the session was **quirky REST/JSON:API/ArcGIS endpoints**:
   - CDSS: `404 = zero records` (not an error); *both* `startDate`+`endDate` required for
     full history (neither alone works); the value field is `measValue`, not `value`.
   - RISE: `locationId[]` and `search` filters silently return an unrelated default page;
     the only reliable discovery is relationship traversal
     (`location → catalogRecords → catalogItems`); results paginate via `links.next`
     with a **10k-row cap**; the cached session returns empty bodies for big pages.
   - ArcGIS FeatureServer (Northern) — a dead end (boundaries only).

   There is a `toolchain-scraping.md` but **no `toolchain-apis.md`** for REST / JSON:API
   / GraphQL / ArcGIS / pagination / "probe-then-extract." *Root cause:* the skill grew
   from PDF liberation; civic data has moved behind quirky APIs the skill doesn't model.

4. **Immutable-originals has no cache-invalidation story.** `fetch_all` skips files that
   already exist; when the *extraction contract* changed (the full-history fix), cached
   files went stale and **never refreshed**, so the CSV was silently partial. The
   "`data/original` is a rebuildable cache, not an archive" framing had to be
   **discovered**. *Root cause:* the convention covers immutability but not "refetch when
   the contract changes" (a `--force` / clear-on-change story).

5. **The reject port silently dropped whole entities.** A handful of duplicate-date rows
   failed the parser-level **frame uniqueness** check → `clean.run` logged a SchemaError
   and dropped the **entire reservoir** (ruedi, turquoise, twin-lakes…). Durable-errors
   is right, but **validation at the wrong granularity** plus **no dedup-before-validate
   guidance** turned a few bad rows into missing sources, visible only by reading a JSON
   file. *Root cause:* the skill doesn't warn that whole-frame validation inside a parser
   can drop a source, nor guide deduplication of real-world multi-observation data.

6. **The error log accumulated stale failures.** `extraction_errors.json` was
   append-only, so JSONDecodeErrors from an earlier interrupted run mixed with current
   SchemaErrors and **misled debugging**. *Root cause:* the error-log pattern isn't
   run-scoped (reset per run) and isn't surfaced loudly (a quiet JSON file vs. the
   audit's "Empty sources" flag).

7. **Time-series / multiple-readings-per-period grain isn't modeled.** The skill's
   worked examples (votes, enrollment) are one value per entity-period. Daily reservoir
   data with **sub-daily readings + same-day revisions**, collapsed by day-flooring,
   broke the uniqueness assumption. *Root cause:* `data-modeling.md` covers tidy-long but
   not the temporal subtleties — which reading wins, flooring, revisions.

8. **Entity-universe enumeration isn't modeled.** Substantial effort went into "what
   stations/reservoirs exist behind this API" (the CDSS station list; the RISE catalog
   traversal), captured in a hand-built `stations.py`. The skill's `discover.py` is about
   *new files/vintages upstream*, not *enumerating the entity universe behind an API*.
   *Root cause:* discovery is file/vintage-oriented, not entity-oriented.

9. **No progress/liveness for large fetches.** A full historical pull fans out to
   hundreds of paginated requests and **sat silent**; progress reporting had to be
   added. *Root cause:* the fetch pattern (idempotent + cached) omits progress, though
   `structlog` is already a dependency.

10. **Scaffolded operator instructions assume expertise.** The `reconcile()` stub shipped
    with *"fill `expected` with current storage off each agency's page; any mismatch
    beyond tolerance is a regression"* — unactionable for a novice until expanded to
    what/where/how/success-vs-failure. *Root cause:* the *why* is well-documented
    (`discovery-and-audit.md`) but the scaffolded artifact's *operator copy* isn't
    novice-legible.

11. **Notebook output hygiene** — notebooks were committed with executed outputs until an
    `nbstripout` filter was added (shared with the `data-project` finding).

## 5. Lessons

- The skill's **documentation + provenance + tidy-long + caveats** spine is excellent and
  held up under a long, adversarial real-world build.
- Its **toolchain center of gravity (PDF/documents/scraping) lags where civic data has
  moved.** Quirky REST/JSON:API/ArcGIS endpoints dominated, and the skill lacked both an
  **API toolchain** and an explicit **"decode-the-API-by-probing-before-extracting"**
  discipline (the thing that actually worked every time).
- **Immutable originals need a cache-invalidation rule** for when the extraction contract
  changes — otherwise stale partial data leaks into the deliverable.
- **Durable-errors is right but needs granularity guidance**: dedup before validate;
  don't let a few rows drop a whole entity; reset + surface the error log loudly.
- **Temporal grain is a first-class modeling case** (multiple observations per period,
  revisions, flooring) — not an afterthought to tidy-long.
- **Notebook-first pipelines are a legitimate variant** the skill should support
  natively, and `scripts/`↔`src/` should be reconciled with `data-project`.
- **Operator-facing copy in scaffolded artifacts must be novice-legible** — the same bar
  the skill sets for data dictionaries.

## 6. Recommendations (highest impact first)

- **Add `references/toolchain-apis.md`** (REST / JSON:API / GraphQL / ArcGIS;
  pagination; rate limits; the "probe a few records, decode the contract, *then* write
  the parser" loop; empty-vs-404 conventions) and an **entity-enumeration** pattern
  alongside `discover.py`.
- **Add a notebook-driven pipeline variant** (thin notebooks + tested package) and
  reconcile `scripts/`↔`src/` with `data-project`.
- **Give immutable-originals a cache-invalidation rule** (`--force` / clear-on-contract-
  change) and a `FRESH` run option in the driver.
- **Strengthen the cleaning pipeline**: dedup-before-validate guidance, validation
  granularity (don't drop a whole source over a few rows), and a **run-scoped, loud**
  error report.
- **Add a temporal-grain section to `data-modeling.md`** (one row per period; which
  observation wins; revisions; flooring).
- **Scaffold `nbstripout`** for notebook pipelines; **novice-legibility pass** on
  scaffolded operator instructions (reconcile, bulletproofing checklist).

A companion **Claude Code revision plan** (parallel to
`audits/revision-plans/2026-06-18-data-project-skill-revision-plan.md`) can turn these into phased, file-level
edits with acceptance criteria — say the word and I'll write it.
