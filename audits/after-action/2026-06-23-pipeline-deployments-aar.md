---
# Versioning
version: "1.0"
status: final
created: 2026-06-23
updated: 2026-06-23
# Provenance
title: "After-Action Report — deploying streamflow, snowpack & climate-stations (the multi-pipeline phase)"
doc_type: after-action-report
subject_skill: [data-liberation, data-project]
project: "Colorado Environmental Data Hub -> pipelines/{streamflow,snowpack,climate-stations}"
repository: "CUPIDS-Lab/co-environmental-data"
author: "Claude (Opus 4.8 · claude-opus-4-8)"
generated_by: "Claude Code session"
basis: "Forensic review of PRs #37/#45/#46/#47/#48/#49 and the four pipeline trees on origin/main (fffd55e), 2026-06-23. Extends the 2026-06-19 reservoir-storage AARs."
related:
  - audits/after-action/2026-06-18-data-liberation-aar.md
  - audits/after-action/2026-06-18-data-project-aar.md
  - audits/revision-plans/2026-06-18-data-project-skill-revision-plan.md
  - audits/qa/2026-06-23-project-audit.md
  - audits/revision-plans/2026-06-23-project-revision-plan.md
  - audits/revision-plans/2026-06-23-data-project-skill-revision-plan.md
tags: [retrospective, aar, data-liberation, data-project, multi-pipeline, cupids]
---

# After-Action Report — the multi-pipeline phase (streamflow, snowpack, climate-stations)

**Project:** Colorado Environmental Data Hub (`CUPIDS-Lab/co-environmental-data`)
**Window:** 2026-06-23 — three liberation pipelines landed on `main` in one day (≈01:17–12:04 UTC), through four *different* deployment paths, partly by concurrent agents sharing one working tree.
**Predecessors:** the 2026-06-19 reservoir-storage AARs (`audits/after-action/2026-06-18-data-liberation-aar.md`, `audits/after-action/2026-06-18-data-project-aar.md`). This report covers what happened *after* the first pipeline — the move from one pipeline to four.

---

## 1. What we set out to do

Stamp out the remaining water-data pipelines from the proven reservoir-storage template: **streamflow** (#10, USGS NWIS + CO DWR/CDSS), **snowpack** (#11, NRCS AWDB SNOTEL + snow courses), and **climate-stations** (#44, CO DWR/CDSS daily climate). Each is a `retrieve → tidy → document → audit → publish` slice under `pipelines/<name>/`, CI-gated and Dataverse-ready.

## 2. What actually got deployed

| Pipeline | Issue | Landed via | Process shape | Outcome |
|---|---|---|---|---|
| **streamflow** | #10 | **PR #37** (commit `0ffb069`) | **Bundled** into the "Elevate Hub to L4" PR alongside governance + a QA audit — *3 unrelated concerns in one merge* | Built (42 files, 21 tests); never reviewable in isolation |
| **snowpack** | #11 | **PR #45** + cleanup **PR #46** | One commit that **swept in 37 untracked climate-stations files**; #46 untracked them | Built (43 files, 28 tests); main briefly carried foreign files |
| **climate-stations** | #44 | **PR #47** (CI row) → **PR #48** (code) | Two PRs **in the wrong order**: the CI matrix row merged ~4.5 min before the directory existed | Built (37 files, 23 tests); **main CI red for 4m24s**; registration left incomplete |
| *(labels)* | — | **PR #49** | The label-declutter commit I had rebased out of #45 landed on its own | Confirms the rebase decision was correct |

Net for the day: three pipelines on `main`, four distinct (and partly broken) paths to get there. Reservoir-storage, for contrast, had landed earlier via ~15 small incremental PRs.

## 3. What worked well

- **The 2026-06-19 recommendations were adopted and paid off.** The reservoir AAR's biggest asks now ship in every pipeline: a **`--fresh`/cache-invalidation** flag, **throttled progress reporting** in `fetch_all`, a **run-scoped error log**, the **`src/<pkg>/` + thin-notebook** layout, **`nbstripout`**, **novice-legible reconcile** copy, **entity enumeration** (`build_*_seed.py`), and **temporal-grain handling** (`normalize_long` day-floor + keep-latest). The skill learned from the first build.
- **The API-probing discipline worked on a brand-new API.** Snowpack's AWDB contract was decoded live before any parser was written — including the host gotcha (`wcc.sc.egov.usda.gov`, not `wcc.nrcs.usda.gov`) and the snow-course `SEMIMONTHLY`/`collectionDate` quirk. "Probe, then extract" is now reliable.
- **The canonical spine held across four very different domains.** Tidy-long `(source, site_id, datetime, variable)`, the pandera boundary contract, per-extract provenance, and "concepts carry caveats" absorbed reservoirs, gages, SNOTEL/snow-courses, and climate stations without contortion.
- **One genuinely good abstraction emerged:** snowpack's `parsers/_awdb.py` shared parser with thin `nrcs_snotel`/`nrcs_snowcourse` adapters (18–20 lines each). This is the DRY pattern the *repo* should generalize (see §4.1).
- **CI caught the ordering bug loudly.** `fail-fast: false` meant the #47 break showed exactly one red leg (`climate-stations`) while the others stayed green — the failure was legible and self-limiting.
- **The cleanup was honest and reversible.** When #45 swept in foreign files, #46 untracked them with `git rm --cached` (preserving them on disk) and they later landed correctly via #48 — no work lost.

## 4. Friction and gaps (with root causes)

### 4.1 ~49% of pipeline source is copy-stamped duplication — and there is no shared library *(highest impact)*
The four pipelines were "stamped out" from each other (reservoir → streamflow → {snowpack, climate-stations}). The result: **`provenance.py` is AST-identical across all four** (the only real difference is the import line); `clean.py` is near-identical (streamflow ≡ snowpack); `fetch.py`, `schema.py`, `pipeline.py`, and `config.py` share 67–86% of their code. There is **no `pipelines/common/`, no root package, and zero cross-pipeline imports** — every pipeline re-implements the plumbing. Estimated **~1,380 redundant lines out of ~2,845 src LOC (≈49%)**. *Root cause:* "stamp a sibling" is the documented process (`AGENTS.md`: "New pipelines stamp out from these") but copy-paste is the only mechanism offered; the genuinely-shared plumbing (provenance, the fetch engine, clean orchestration, the CLI skeleton) was never factored out. The drift is already visible — the provenance docstring diverged between siblings despite identical code.

### 4.2 Concurrent agents share one working tree → untracked WIP gets swept *(highest impact)*
Snowpack PR #45 (`d0c7f68`) included **37 untracked `pipelines/climate-stations/` files** that a *different* agent had left in the shared working tree; the branch was also switched out from under the session mid-task. It took a three-PR repair (#46 remove → #47 re-register CI → #48 re-land) to sort out. *Root cause:* multiple agents/sessions operate on a single checkout, and any broad `git add` / rebase / `checkout` sweeps another agent's untracked work-in-progress. (Captured in user memory as `git-worktree-isolation-multiagent`; this report is the corroborating post-mortem.)

### 4.3 The CI matrix is static, duplicated, and order-sensitive
`pipelines-ci.yml` and `monthly-data-refresh.yml` each hardcode one `{pipeline, module}` row per pipeline — **two files to edit per pipeline**, by hand. PR #47 added the climate-stations row **before** PR #48 added the directory, so `origin/main` had a matrix row pointing at a `working-directory` that didn't exist; the very first step (`uv sync`) failed and **`main` CI was red for 4m24s** (run `30951e5`, 12:00:09 → fixed by #48 at 12:04:30). The inverse hazard also bit: climate-stations is in `pipelines-ci.yml` but **was never added to `monthly-data-refresh.yml`** (still 3 rows), so it gets no scheduled refresh. *Root cause:* a hand-maintained matrix with no auto-discovery and no rule binding "add the row" to "the dir exists on main."

### 4.4 There is no standard "land a pipeline" process — four pipelines, four ways
Reservoir = ~15 incremental PRs; streamflow = **0 dedicated PRs** (bundled invisibly into governance PR #37, whose body even claims streamflow was "left out" while the next commit adds all 44 files); snowpack = 1 PR + a cleanup; climate-stations = 2 PRs in the wrong order. *Root cause:* "build a pipeline" is well-modeled, but "take a built pipeline from branch → CI row → docs → PR → merge → close issue" is not a documented, ordered procedure, so each landing improvised.

### 4.5 Registration-as-projection is manual and gets forgotten — so the repo undercounts itself
Adding a "complete" pipeline requires hand-editing **~9 repo-level docs** (README, ROADMAP, CHANGELOG, AGENTS, decision-log, data-management-plan, data-card, wiki Home) **+ a Dataverse kit + two CI matrices**. **No pipeline did this completely:**
- **climate-stations (#48)** shipped *code only* — **no Dataverse kit, not in the monthly-refresh matrix, and zero repo-doc updates** (0 mentions in README/CHANGELOG/data-card).
- **snowpack (#45)** registered itself in most docs but **missed the ROADMAP tracking-table row** (which still reads "snowpack #11 remains, ◐").
- **streamflow (#37)**, bundled, got only light registration.

The visible result on `origin/main` today: README/AGENTS/data-management-plan still say **"three are built"**, ROADMAP still says **snowpack "remains,"** and the Data Card lists **only the reservoir dataset** — while four pipelines exist. *Root cause:* the repo's prose self-description is a *projection* of the built state, but (unlike the GitHub-issue projection) nothing templates or checklists it, so it silently rots.

### 4.6 Issue lifecycle drifted — four pipelines, three states
`#11` and `#44` are **closed**; `#9` and `#10` are **open** — though all four are built. *Root cause:* Track mode closes an issue when its TODO leaves `ROADMAP.md`, not when its pipeline PR merges; nothing enforces `Closes #N` on the landing PR.

### 4.7 An audit run against a stale local checkout produced false findings *(new, meta)*
While preparing this report, read-only audit agents ran against a working tree **6 commits behind `origin/main`** and concluded climate-stations was "untracked, not in CI, in limbo" — all **false** on `origin/main` (it had landed via #48). The findings had to be re-verified with `git fetch` + `git show origin/main:…` before use. *Root cause:* the same multi-agent drift (§4.2) means the local tree is not a reliable picture of `main`; **audits must re-verify against `origin/main`, not the local checkout.**

### 4.8 Per-pipeline doc inaccuracies
- streamflow `README.md` says **"19 tests"** (actual **21**; its own AGENTS.md says 21) and **"all eight" basins** while listing/holding **nine**.
- snowpack committed only a **12-row sample** `snowpack.csv` (vs ~1–2.3 M rows for the others) — the deliverable shape is a sample, not the full product. *Root cause:* doc numbers are hand-maintained and not asserted by a test/CI check (the same class of bug the 2026-06-22 audit fixed for reservoir, recurring).

## 5. Lessons

- **Stamping does not scale without a shared core.** Four near-identical copies are cheaper to *write* and far more expensive to *maintain* than one shared `co_pipeline_core` + four thin domain packages. The one-API/two-network `_awdb.py` pattern shows the team already knows how to factor; it just wasn't done across pipelines.
- **A shared working tree is the wrong substrate for concurrent agents.** Isolation (a worktree per agent), explicit path-scoped staging, and a pre-merge `git fetch`/verify are not optional once more than one agent touches the repo.
- **"Done" is a projection, not an event.** A pipeline is not landed when its code merges; it is landed when its **code + CI (both workflows) + Dataverse kit + ~9 repo docs + its tracking issue** all agree. Today none of those projections is enforced, so the repo's self-image is stale.
- **CI ordering is a correctness property.** Register-the-row and add-the-dir must be atomic (one PR) or auto-discovered; splitting them across PRs will red `main` every time.
- **Audits must target `origin/main`.** In a multi-agent repo the local checkout lies; verification has to fetch.

## 6. Recommendations (→ see the two companion plans)

1. **Extract a shared `co_pipeline_core`** (provenance, the fetch engine, clean orchestration, schema/CLI skeleton); leave only domain logic (`sources`, `parsers`, `stations`, `audit` extensions, `schema` columns) per pipeline. *(project plan, Phase 1)*
2. **Auto-discover the CI matrix** from `pipelines/*/pyproject.toml` across *both* workflows; bless "CI row and code in the same PR." *(project plan, Phase 3)*
3. **Adopt a one-PR "land a pipeline" runbook** (branch → code → CI row → repo-doc registration → Dataverse kit → PR with `Closes #N` → merge), and an **isolated-worktree** default for agents. *(both plans)*
4. **Make repo-doc registration a checklist/generator** (a "registering a pipeline touches these N files" projection), and **reconcile the repo's "three/four" undercount now**. *(project plan, Phases 2 & 4)*
5. **Tie issue closure to landing**; reconcile #9/#10/#11/#44 to one rule. *(project plan, Phase 5)*

File-level edits, acceptance criteria, and sequencing are in `audits/revision-plans/2026-06-23-project-revision-plan.md` (the repo) and `audits/revision-plans/2026-06-23-data-project-skill-revision-plan.md` (the skill). The point-in-time evidence is in `audits/qa/2026-06-23-project-audit.md`.
