---
# Versioning
version: "1.0"
status: final
created: 2026-06-23
updated: 2026-06-23
# Provenance
title: "Project audit — accuracy & utilization after the multi-pipeline phase"
doc_type: audit
project: "Colorado Environmental Data Hub"
repository: "CUPIDS-Lab/co-environmental-data"
audited_ref: "origin/main @ fffd55e (re-verified with git fetch; NOT the local checkout)"
author: "Claude (Opus 4.8 · claude-opus-4-8)"
generated_by: "Claude Code session (3 read-only audit agents, reconciled against origin/main)"
basis: "Successor to audits/qa/2026-06-22-qa-audit.md, run after streamflow/snowpack/climate-stations landed."
related:
  - audits/qa/2026-06-22-qa-audit.md
  - audits/after-action/2026-06-23-pipeline-deployments-aar.md
  - audits/revision-plans/2026-06-23-project-revision-plan.md
tags: [audit, accuracy, utilization, project-management, cupids]
---

# Project audit — accuracy & utilization (2026-06-23)

**Scope:** the *project* layer (docs, templates, utilization, issues/PM), not pipeline internals.
**Audited against:** `origin/main @ fffd55e` — **re-verified with `git fetch`**, because the local working tree was 6 commits stale and produced false findings (see AAR §4.7). Every filesystem claim below was confirmed with `git show origin/main:<file>`.

## Executive summary

| Area | Verdict | Headline |
|---|---|---|
| **Repo self-description** | 🟡 **Undercounts itself** | 4 pipelines exist; README/AGENTS/data-management-plan still say "three built", ROADMAP says snowpack "remains", the Data Card lists only reservoir. |
| **climate-stations landing** | 🟡 **Code-only landing** | #48 shipped clean code + 1 CI row, but **no Dataverse kit, not in the monthly refresh, and zero repo-doc registration**. Issue #44 is closed. |
| **L4 checklists & audits** | 🟡 **Templates, never run** | All four checklists are empty `[ ]`; only reservoir was ever audited; streamflow/snowpack/climate-stations have no QA record despite shipping reconciliation. |
| **Issue / milestone state** | 🟡 **Drifted** | #9/#10 open but built; #11/#44 closed — 3 states for 4 pipelines. "Climate data liberation" milestone done but open. PROJECT-MANAGEMENT says "two milestones"; there are four. |
| **Reservoir publish gating** | 🟢 **Honest** | #36 correctly blocked on #38–#40; reservoir correctly "not publish-ready." Preserve this as the model. |
| **Catalog accuracy** | 🟢 **Accurate** | 56 sources verified; tier/theme/verification splits match `DATA-DICTIONARY.md` exactly. |

Severity legend: **HIGH** (misleads a reader or risks data/credential loss) · **MED** · **LOW**.

## A. Inaccuracies / staleness (verified on origin/main)

- **A1 [HIGH] The repo undercounts its own pipelines.** Four pipelines are on `main`, but: `AGENTS.md` says "**Three are built**"; `data-management-plan.md` says "**(three present)**"; `README.md` "## Pipelines" and `.github/wiki-seeds/Home.md` list only reservoir/streamflow/snowpack (**0 mentions of climate-stations**, incl. CHANGELOG). `ROADMAP.md` tracking-table row #7 still reads "**snowpack #11 remains**, ◐". *(climate-stations #48 registered no docs; snowpack #45 missed the ROADMAP table row.)*
- **A2 [HIGH] The Data Card omits 2–3 shipped datasets.** `data-card.md` lists only the catalog + **Reservoir Storage** + the planned corpus; streamflow, snowpack, and climate-stations are absent from the public-facing transparency summary (0 mentions).
- **A3 [MED] README still describes the pre-pipeline state.** `README.md`: "The current deliverable is a documented dataset, **not yet a runnable pipeline**," and "Getting started" never shows how to run a built pipeline — though 3–4 runnable, tested, CI-wired pipelines exist.
- **A4 [MED] streamflow doc numbers are wrong.** `pipelines/streamflow/README.md` says "**19 tests**" (actual **21**; its own AGENTS.md says 21) and "**all eight**" basins while listing/holding **nine**.
- **A5 [MED] The 2026-06-22 audit's central streamflow finding is now stale.** It records the streamflow engine as "**untracked in git**"; it is now fully tracked. The audit is point-in-time (expected), but it is still the *only* audit and is cited as current in `README.md`/`decision-log.md`.
- **A6 [LOW] No Dataverse deposit has ever occurred.** Only `<doi>` placeholders; no `.dataverse-deposit.json`. Expected (publish is blocked), but the deposit kits are unexercised end-to-end.
- **Verified accurate (no action):** catalog `source_count = 56`; tier (25/15/16), theme, and verification (47/9) splits match `DATA-DICTIONARY.md`. No broken internal links found.

## B. Under-utilized / at-risk artifacts

- **B1 [HIGH] All four L4 checklists are empty templates.** `data-bulletproofing-checklist.md`, `data-quality-checklist.md`, `responsible-data-checklist.md`, `accessibility-checklist.md` contain **zero `[x]`**. The only executed QA is `audits/qa/2026-06-22-qa-audit.md` (reservoir only). streamflow & snowpack ship an *automatic cross-source reconciliation* — their strongest QA artifact — that no audit or checklist records.
- **B2 [HIGH] climate-stations landed code without its registration tail.** On `origin/main`: **no `pipelines/climate-stations/dataverse/` kit** (the only pipeline missing one), **absent from `monthly-data-refresh.yml`** (still 3 rows → no scheduled refresh), and **unregistered in every repo doc**. Issue #44 is closed, so this remaining work is invisible.
- **B3 [MED] Only one audit for four pipelines.** snowpack and climate-stations have never been audited; the audit doc's own instruction ("re-run and date a new file after material data changes") has three unmet triggers.
- **B4 [MED] Local working-tree hygiene risk.** The local checkout still holds pre-#48 climate-stations WIP plus a **~290 MB `.requests-cache.sqlite`** and a **`dwr_api.json` credential** as untracked files. `#48` correctly excluded them, but in a shared tree a broad `git add` could still sweep the key/cache (the §4.2 failure mode). *(Repo on `origin/main` is clean; this is a checkout-hygiene item.)*
- **B5 [MED] `context/` carries design clutter & a stale "stubs" framing.** Tracked `context/` holds `cej-corpus-scaffold.zip`, two `.docx` proposals, and a **duplicate** of the catalog JSON; `context/architecture.md` still says modules are "scaffolded as stubs" (true only for the unbuilt corpus) yet is cited repo-wide as "the pipeline."
- **Working as designed (no action):** `.skills/{data-intake,documentation,release-and-share}` are real, referenced content; `retro/` AARs are substantive; `ROLES.md` GAP-CHECK is honestly filled.

## C. Issue / project-management drift (live `gh` data)

- **C1 [HIGH] Sub-issue states are inconsistent:** #11, #44 **closed**; #9, #10 **open** — all four built. Pick one rule (e.g. *closed when built; publish tracked by #36*) and apply to all four.
- **C2 [MED] Milestones not maintained:** "**Climate data liberation**" (0 open / 1 closed) should be **closed**; "Water data liberation" can't close while #9/#10 are erroneously open. `PROJECT-MANAGEMENT.md` says "there are now **two** milestones" — there are **four**.
- **C3 [MED] Untracked remaining work:** no issue tracks (a) finishing climate-stations registration (B2), (b) the shared-library refactor (AAR §4.1), (c) the CI-matrix auto-discovery / completeness (AAR §4.3), or (d) per-pipeline audits / filling the L4 checklists (B1/B3).
- **C4 [OK] Reservoir publish gating is honest:** #38/#39/#40 and #36 are open and labeled `blocking`; docs consistently say reservoir is not publish-ready. #41/#42/#43 consistent. **Preserve this as the model for the other pipelines.**

## Top findings → revision plan (HIGH → LOW)

1. **[HIGH]** Finish climate-stations registration *or* reopen #44 (Dataverse kit + monthly-refresh row + repo docs). — B2, C3
2. **[HIGH]** Fix the "three/snowpack-remains" undercount across README/AGENTS/ROADMAP/DMP/data-card/wiki. — A1, A2
3. **[HIGH]** Reconcile #9/#10/#11/#44 to one issue-state rule; close the Climate milestone. — C1, C2
4. **[HIGH]** Fill the L4 checklists / extend the audit to every pipeline. — B1, B3
5. **[MED]** File the shared-library refactor + CI-matrix-completeness issues. — C3
6. **[MED]** Refresh README "Getting started"/L2 framing; mark the 2026-06-22 audit superseded. — A3, A5
7. **[MED]** Resolve local checkout hygiene (protect the key/cache; sync to origin/main). — B4
8. **[LOW]** Fix streamflow 19↔21 tests and "eight/nine" basins; declutter `context/`. — A4, B5

The phased plan, with file-level edits and acceptance criteria, is in `audits/revision-plans/2026-06-23-project-revision-plan.md`.
