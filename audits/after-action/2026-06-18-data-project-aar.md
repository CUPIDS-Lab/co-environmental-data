---
# Versioning
version: "1.0"
status: final
created: 2026-06-19
updated: 2026-06-19
# Provenance
title: "After-Action Report — first implementation of the data-project skill"
doc_type: after-action-report
subject_skill: data-project
project: "Colorado Environmental Data Hub"
repository: "CUPIDS-Lab/co-environmental-data"
author: "Claude (Opus 4.8 · claude-opus-4-8)"
generated_by: "Claude Code session"
basis: "First real-world build of the skill — ~24 merged PRs: L1 scaffold -> GitHub Track mode -> handoff to data-liberation for the reservoir-storage pipeline."
related:
  - audits/after-action/2026-06-18-data-liberation-aar.md
  - audits/revision-plans/2026-06-18-data-project-skill-revision-plan.md
tags: [retrospective, aar, data-project, cupids]
---

# After-Action Report — first implementation of the `data-project` skill

**Project:** Colorado Environmental Data Hub (`CUPIDS-Lab/co-environmental-data`)
**Skill under review:** `data-project` (with `data-liberation` as the downstream sibling)
**Window:** initial scaffold → L1 documented repo → GitHub tracking → one liberated pipeline
**Date:** 2026-06-19
**Author:** Claude (Opus 4.8), Claude Code session

---

## 1. What we set out to do

Use `/data-project` to stand up a public-interest data repository from a rich
`/context/` dump (a methodology memo, a technical architecture, a ~70-source
discovery audit, and a 56-source catalog JSON), then grow it incrementally as the
user directed. The skill's remit — *structure, document, govern, track, and compose
with `data-liberation`* — was the spine of the whole session.

## 2. What actually got built

| Layer | Output |
|---|---|
| **L1 scaffold** (data-project) | `README`, `AGENTS.md`, `ROADMAP.md`, `DATA-DICTIONARY.md`, `decision-log.md`, `CHANGELOG.md`, `data/{raw,interim,processed,external}`, data-aware `.gitignore`/`.gitattributes`; catalog JSON tracked as immutable source-of-record via a carve-out. |
| **GitHub "Track mode"** | 6 issues under 2 milestones, full label taxonomy, an org Project board with custom fields (Status/Priority/Size/Level), a wiki, and `.github/` machinery (`seed-github.sh`, `engagement-sync.json`, issue forms, PR template, `ACCESS.md`, wiki seeds). |
| **Epic decomposition** | Issue #7 (water-data liberation) → native sub-issues #9/#10/#11 (reservoir / streamflow / snowpack). |
| **Composition w/ data-liberation** | `pipelines/reservoir-storage/` — a full notebook-driven pipeline for #9 (3 sources, tidy schema, ~14 follow-on PRs of live-API debugging). |

Net: ~24 merged PRs. The data-project skill delivered the repo + docs + governance
posture + tracking; data-liberation built one limb on top of it.

## 3. What worked well

- **Lean-by-default was correct.** L1 was the right entry; the skill resisted
  pipeline/governance/OKF bloat. The **now / later / `ROADMAP.md`** mechanism cleanly
  parked the entire L2–L5 program (the architecture's whole pipeline, collaboration,
  responsible-data, and publication layers) as named, deferred, sometimes-*blocking*
  work — nothing was lost, nothing was over-built.
- **The level ladder + entry protocol** (Infer → State → Execute → Offer) matched the
  user's actual cadence — they climbed one rung at a time ("merge", "add an issue",
  "harden #9", "take it live") and the skill's framing fit each step.
- **Templates produced real content, not stubs.** `DATA-DICTIONARY.md` documented the
  actual 56-source catalog (grain, vocabularies, the NREL `nlr.gov` data-integrity
  caveat); `ROADMAP.md` captured the architecture's full design as deferred rows.
- **Sensitivity reasoning was sound.** The skill (and operator) correctly did **not**
  fire the heavy sensitive-data coupling for public agency metadata, while capturing
  the *future* copyright/fair-use and journalist-privacy duties as **blocking**
  ROADMAP items — affordance↔duty kept honest without governance theater at L1.
- **`decision-log.md` discipline** captured the non-obvious calls (naming, raw-as-tracked,
  the sensitivity stance) where they'd be found later.
- **Composability with `data-liberation`** was smooth at the conceptual level — a
  roadmap issue became a sub-pipeline.

## 4. Friction and gaps (with root causes)

1. **Track mode is under-formalized.** The GitHub-projection layer — issues + board +
   wiki as an *idempotent projection of `ROADMAP.md`*, the `engagement-sync.json`
   manifest, the marker-matched seed script, sub-issue decomposition — was the single
   largest chunk of work and was largely **hand-built**, not driven by documented
   skill templates. *Root cause:* the skill stops at the repo boundary; "project
   management as a projection of the roadmap" isn't a first-class, templated mode.

2. **External-prerequisite stalls.** The Project board needed a `project` OAuth scope
   grant; the wiki needed a manually-created first page. Both **stalled mid-flow**
   until the user acted. *Root cause:* no preflight for the tracker's external
   dependencies, and no documented graceful-degradation path.

3. **`data/raw` immutability guidance is too blunt.** "Raw is immutable and
   git-ignored" assumes large/external/re-downloadable inputs. The hand-curated
   catalog JSON is a small *source-of-record* that **should** be version-controlled —
   handled by improvising a `.gitignore` carve-out + a decision-log entry. *Root
   cause:* the skill doesn't distinguish *curated source-of-record* from *bulk
   external raw*.

4. **`src/` vs `scripts/` convention divergence.** `data-project`'s tree uses
   `src/<pkg>/`; `data-liberation`'s template uses `scripts/`. The nested pipeline had
   to pick one and **document the deviation**. *Root cause:* the sibling skills aren't
   aligned on package location.

5. **Notebook hygiene isn't scaffolded.** Notebooks were repeatedly committed *with
   executed outputs* (cleaned by hand twice) until an `nbstripout` git filter was
   added. *Root cause:* the skill doesn't set up output-stripping when notebooks are
   part of the project.

6. **Deferred/conditional sensitivity isn't a first-class disposition.** "Public now,
   sensitive once the corpus ingests article text + journalist PII" had to be
   **hand-encoded** as blocking ROADMAP rows. *Root cause:* the sensitivity coupling is
   modeled as binary/now, not "becomes-sensitive-when-X".

7. **No context-rich fast path.** With a substantial `/context/` dump, the skill's
   3-agent cold-start interview (interviewer → indexer → synthesizer) was overkill; the
   profile was **inferred from the docs and confirmed** instead. It worked, but is
   undocumented. *Root cause:* the workflow assumes a cold start.

8. **Multi-pipeline monorepo pattern is undocumented.** A `data-project` repo hosting
   *N* `data-liberation` pipelines under `pipelines/<name>/`, each mapped to an
   issue/sub-issue and tracked by the umbrella board, is the **real working shape** —
   but only described in prose, not as a directory/issue convention. *Root cause:* the
   data-project↔data-liberation handoff is narrated, not specified.

9. **Template instructions assume an expert runner.** The reconciliation step shipped
   as *"fill `expected` with current storage off each agency's page; any mismatch
   beyond tolerance is a regression"* — unactionable for a novice until expanded to
   what/where/how/success-failure. Other QA/responsible-data checklists likely share
   the terseness. *Root cause:* templates optimize for the author, not the newcomer who
   executes them.

## 5. Lessons

- The skill's value **peaked at structure + documentation + right-sized deferral**.
  Its biggest gaps were everything **after the repo**: project-management projection,
  external prerequisites, and multi-pipeline composition.
- **"Projection" is the right mental model** and should be made explicit: `ROADMAP.md`
  is the source of truth; GitHub (issues/board/wiki) is an idempotent projection.
- **Right-sizing held up** under a long, escalating session — the ladder didn't force
  premature heavy artifacts.
- **Real-world data breaks blunt conventions.** Curated-vs-bulk raw, conditional
  sensitivity, and notebook hygiene are common enough to be anticipated by the scaffold.
- **Documentation is only done when a novice can act on it** — the same standard the
  skill applies to data dictionaries should apply to its own template instructions.

## 6. Recommendations (→ see the companion revision plan)

Highest impact first: **(A)** formalize Track mode + **(B)** add an external-prereq
preflight; then **(C)** refine the raw-data convention, **(D)** specify the
multi-pipeline/data-liberation handoff and align `src/`↔`scripts/`; then the
refinements — **(E)** deferred-sensitivity disposition, **(F)** context-rich fast path,
**(G)** notebook hygiene in the scaffold, **(H)** a novice-legibility pass on template
instructions. Details, files, and acceptance criteria in
`audits/revision-plans/2026-06-18-data-project-skill-revision-plan.md`.
