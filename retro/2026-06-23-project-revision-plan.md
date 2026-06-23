---
# Versioning
version: "1.0"
status: draft
created: 2026-06-23
updated: 2026-06-23
# Provenance
title: "Revision plan — Colorado Environmental Data Hub (post multi-pipeline phase)"
doc_type: revision-plan
project: "Colorado Environmental Data Hub"
repository: "CUPIDS-Lab/co-environmental-data"
author: "Claude (Opus 4.8 · claude-opus-4-8)"
generated_by: "Claude Code session"
basis: "Derived from audits/2026-06-23-project-audit.md and retro/2026-06-23-pipeline-deployments-aar.md."
related:
  - audits/2026-06-23-project-audit.md
  - retro/2026-06-23-pipeline-deployments-aar.md
  - retro/2026-06-23-data-project-skill-revision-plan.md
tags: [plan, revision, project, refactor, ci, cupids]
---

# Plan — revise the Colorado Environmental Data Hub

**Goal:** make the repo's *self-description, structure, CI, and tracking* match the four-pipeline reality, and pay down the duplication/process debt the multi-pipeline phase exposed — **without** touching the (honest) reservoir publish-gating, which is the model to copy.

**Sequencing principle:** cheap-accuracy-and-hygiene first (restores trust in the repo as documentation), then the structural refactor, then process. Each phase is independently shippable as its own PR (one concern per PR — the lesson of streamflow's bundled #37).

---

## Phase 0 — Hygiene & isolation *(do first; ~30 min)*

**Problem:** the local checkout is 6 commits stale and holds a ~290 MB cache + a `dwr_api.json` credential as untracked files in a tree shared by concurrent agents (audit B4; AAR §4.2, §4.7).

- Sync the local checkout to `origin/main`; preserve/relocate the untracked climate-stations WIP cache & key **out** of the worktree (or confirm `.gitignore` covers `*.requests-cache.sqlite*` and `dwr_api.json` in `pipelines/climate-stations/`).
- Add a one-paragraph **"working in this repo with other agents"** note to `AGENTS.md`: prefer `git worktree add`, stage explicit paths (never `git add -A`), `git fetch` + verify `origin/main` before any merge. (Mirrors the user's `git-worktree-isolation` memory.)

**Acceptance:** `git status` is clean on a synced `main`; no credential/cache is stageable by accident; `AGENTS.md` documents the isolation rule.

## Phase 1 — Reconcile the repo's self-description *(highest trust-per-effort)*

**Problem:** the repo undercounts itself — "three built", "snowpack remains", Data Card lists one dataset (audit A1, A2, A3, A4, A5).

- `AGENTS.md`: "Three are built" → **four**; add the `pipelines/climate-stations/` entry.
- `ROADMAP.md`: fix tracking-table row #7 ("snowpack #11 remains, ◐" → snowpack **built**; add climate-stations #44 **built**); update the epic blockquote + deferred table.
- `README.md`: add the climate-stations bullet to "## Pipelines"; rewrite the stale "not yet a runnable pipeline" / "Getting started" framing to show how to **run a built pipeline** (`cd pipelines/<name> && uv sync && uv run python -m <module>.pipeline --mode demo`).
- `data-management-plan.md`: "(three present)" → **four**, add climate-stations.
- `data-card.md`: add **streamflow, snowpack, climate-stations** as datasets (grain, sources, counts); stamp a real `updated:` date.
- `.github/wiki-seeds/Home.md`: list all four.
- `CHANGELOG.md`: add the missing **climate-stations** entry.
- streamflow `README.md`: **"19 tests" → 21**; reconcile "eight"/"nine" basins (the list and `sites.csv` have nine — fix the prose to "nine").

**Acceptance:** `grep -ri "three are built\|snowpack #11 remains\|three present"` returns nothing; every repo-level doc that enumerates pipelines lists four; the Data Card names all shipped datasets; streamflow numbers are self-consistent. (Phase 6 adds a CI check so this can't rot again.)

## Phase 2 — Finish (or formally defer) climate-stations *(HIGH)*

**Problem:** #48 was a code-only landing — no Dataverse kit, not in the monthly refresh, unregistered (audit B2). Issue #44 is closed, so the gap is invisible.

- Add `pipelines/climate-stations/dataverse/` (stamp from a sibling kit; domain-specific `dataset.json` + `DEPOSIT.md`).
- Add the `climate-stations` row to **`monthly-data-refresh.yml`** (it's already in `pipelines-ci.yml`).
- Registration is folded into Phase 1's doc edits.
- If any of this is intentionally deferred, **reopen #44** (or file a follow-up) so the remaining work is tracked, not lost.

**Acceptance:** climate-stations has a Dataverse kit, appears in **both** CI workflows, is registered in all repo docs, and either its issue is reopened for the residue or there is no residue.

## Phase 3 — Issue & milestone reconciliation *(HIGH; mostly `gh`)*

**Problem:** 4 pipelines in 3 issue states; stale milestones; PM doc wrong (audit C1, C2, C3).

- Adopt one rule — recommend: **a pipeline issue closes when its pipeline is built + registered; the first-publish obligation lives on #36** — and apply it to #9, #10, #11, #44 (close #9/#10 with a "built; publish tracked by #36" comment, or reopen #11/#44; be consistent).
- Close the **"Climate data liberation"** milestone; reconcile **"Water data liberation."**
- Fix `PROJECT-MANAGEMENT.md` "two milestones" → **four**.
- File the missing issues: **shared-library refactor** (Phase 4), **CI-matrix auto-discovery** (Phase 5), **per-pipeline audits / fill L4 checklists** (Phase 6), and **climate-stations residue** if any (Phase 2).

**Acceptance:** all four pipeline issues follow one rule; the Climate milestone is closed; `PROJECT-MANAGEMENT.md` is accurate; the four new work items are tracked issues.

## Phase 4 — Extract a shared pipeline core *(highest structural impact; its own multi-PR effort)*

**Problem:** ≈49% of pipeline source is copy-stamped; `provenance.py` is AST-identical ×4; no shared library (AAR §4.1).

- Create a shared package — **`pipelines/_core/` (`co_pipeline_core`)** or a root `src/` package — holding the domain-agnostic plumbing: `provenance` (verbatim), the `fetch` engine (session + retry/backoff + progress + manifest), `clean` orchestration, the `pipeline` CLI skeleton, and the `schema.normalize_long` machinery. Keep **per-pipeline**: `sources`, `parsers/`, `stations`, the `schema` column vocab, and `audit` domain extensions.
- Migrate **one** pipeline first (snowpack — it already has the `_awdb.py` DRY instinct), prove tests still pass, then migrate the others one PR each.
- Add a `pipelines/_core/` test suite; each pipeline depends on it via its `pyproject.toml`.

**Acceptance:** `provenance.py`/`fetch` engine/`clean`/CLI exist once; per-pipeline `src/` shrinks to domain logic; all four test suites pass against the shared core; total src LOC drops materially (target: remove the ~1,380 redundant lines).

> **Tension to weigh:** a shared core couples the pipelines (a change can break all four) and adds an intra-repo dependency. Mitigate with the `_core` test suite + the CI matrix (Phase 5) running every pipeline on every `_core` change. The maintenance win (one provenance, one fetch engine) outweighs the coupling at four+ pipelines; below ~3 pipelines copy-paste was defensible.

## Phase 5 — CI matrix: auto-discover + order-safe *(MED)*

**Problem:** static, duplicated, order-sensitive matrix; #47 reded `main` for 4m24s; climate-stations missing from the refresh (AAR §4.3).

- Replace the hardcoded `matrix.include` in **both** `pipelines-ci.yml` and `monthly-data-refresh.yml` with a discovery step that globs `pipelines/*/pyproject.toml` and emits the matrix (so a new pipeline dir is covered automatically and the two workflows can't diverge).
- Until/unless auto-discovery lands, add the rule (in the workflows' README and Phase 7 runbook): **the CI matrix row and the pipeline dir land in the same PR** — never a row before the dir on `main`.

**Acceptance:** adding a `pipelines/<name>/` with a `pyproject.toml` is automatically tested by both workflows with no workflow edit; a dry-run confirms all four current pipelines are discovered.

## Phase 6 — QA parity across pipelines *(MED)*

**Problem:** L4 checklists are empty; only reservoir was audited; doc numbers rot silently (audit B1, B3; AAR §4.8).

- Run the bulletproofing + data-quality + accessibility checklists for **streamflow, snowpack, climate-stations** (or extend the `audits/` prose pattern per pipeline), recording each one's reconciliation result.
- Add a tiny **CI doc-accuracy check** per pipeline: assert the README's stated test count equals `pytest --collect-only -q | wc -l` (and, where cheap, station/seed counts). This converts §4.8/A4 from recurring manual bugs into a gate.
- Decide snowpack's deliverable shape: commit the full product or document that the committed CSV is a sample and the full pull is CI/Dataverse-only.

**Acceptance:** each built pipeline has a dated QA record; CI fails if a README test count drifts from reality.

## Phase 7 — Adopt a "land a pipeline" runbook *(process; cheap, prevents recurrence)*

**Problem:** four pipelines, four landing processes; bundling (#37), sweeps (#45), ordering breaks (#47) (AAR §4.4, §4.5).

- Add `pipelines/LANDING.md` (or a section in the repo `AGENTS.md`): the ordered, one-PR procedure — *isolated worktree → build `pipelines/<name>/` → add CI rows (both workflows, same PR) → register in the ~9 repo docs + Dataverse kit → open one PR titled `Add <name> pipeline (#NN)` with `Closes #NN` → CI green → squash-merge → verify `origin/main`.* Include a copy-paste **registration checklist** (the exact file list).
- One concern per PR; never bundle a pipeline into a docs/governance PR.

**Acceptance:** the next pipeline (or a retro dry-run against snowpack) follows the runbook in a single, reviewable, correctly-ordered PR that closes its issue.

---

## Suggested order & sizing

1. **Phase 0 + 1 + 3** (hygiene, accuracy, issue reconciliation) — a day; restores the repo's truthfulness and is mostly edits + `gh`.
2. **Phase 2 + 5 + 7** (finish climate-stations, fix CI, runbook) — small, high-leverage infra/process.
3. **Phase 4** (shared core) — the large structural payoff; one pipeline at a time, gated by Phase 5's matrix.
4. **Phase 6** (QA parity) — ongoing; do streamflow/snowpack first since their reconciliations already pass.

After each phase: open a single-concern PR, let CI go green, **`git fetch` and verify `origin/main`** before merge (the ground moves). Keep the reservoir publish-gating untouched — it is the standard the rest should rise to.
