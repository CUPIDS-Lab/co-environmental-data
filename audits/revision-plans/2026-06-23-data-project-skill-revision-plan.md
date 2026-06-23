---
# Versioning
version: "2.0"
status: draft
created: 2026-06-23
updated: 2026-06-23
supersedes: audits/revision-plans/2026-06-18-data-project-skill-revision-plan.md  # v1.0 (2026-06-19), substantially implemented
# Provenance
title: "Revision plan v2 — data-project skill (post multi-pipeline phase)"
doc_type: revision-plan
subject_skill: data-project
repository: "CUPIDS-Lab/co-environmental-data"
skill_path: "~/.claude/skills/data-project/"
author: "Claude (Opus 4.8 · claude-opus-4-8)"
generated_by: "Claude Code session"
basis: "Status-check of v1 phases A–I against the shipped skill + new frictions from the 4-pipeline, multi-agent phase (PRs #37/#45/#46/#47/#48)."
related:
  - audits/revision-plans/2026-06-18-data-project-skill-revision-plan.md
  - audits/after-action/2026-06-23-pipeline-deployments-aar.md
  - audits/qa/2026-06-23-project-audit.md
tags: [plan, revision, data-project, skill, multi-pipeline, cupids]
---

# Plan v2 — revise the `data-project` skill

**Audience:** a Claude Code session opened in `~/.claude/skills/data-project/`.
**Why v2:** the v1 plan (2026-06-19) was written after a build that stopped at **one** pipeline and is now **substantially implemented** (7 of 9 phases DONE). The repo then grew to **four** pipelines through a multi-agent phase the v1 plan never saw. That phase exposed a new cluster of frictions — all in the `pipelines/<name>/` **monorepo seam** that v1 Phase D *introduced at the directory-convention level but never made operational** (CI, landing, shared code, registration, issue closure).

**Center of gravity:** make the monorepo seam work. Do **not** add new top-level modes; extend the existing ones (scaffold/track/deposit) and references.

## Preserve (do not regress)

The v1-era strengths held up across four pipelines and must survive this revision: **lean-by-default + now/later/`ROADMAP.md` deferral**; the **L0–L5 ladder + Infer→State→Execute→Offer**; **"GitHub is an idempotent projection of `ROADMAP.md`"** (marker + `engagement-sync.json`); the **sensitivity affordance↔duty coupling** incl. the conditional "becomes-sensitive-when-X" disposition; **templates emit real content, not stubs**; the **`decision-log.md`** discipline. The repo's reservoir publish-gating (honest blocking issues) is the model the skill already enables — keep it.

## Part 1 — Status of v1 phases A–I (verified in the shipped skill)

| Phase | Topic | Status | Note |
|---|---|---|---|
| **A** | Formalize Track mode | **DONE (re-architected)** | Shipped as a `SKILL.md` mode + Step 6.5 + `agents/data-project-tracker.md` + `references/github-project-management.md`. **But not in the files v1 named:** no `references/track-mode.md`; `engagement-sync.json` is tracker-generated, not a `.tmpl`; issue forms shipped as `task`/`data-issue` (not `bug`/`data-task`/`good-first-issue`). |
| **B** | External-prereq preflight | **DONE** | `github-project-management.md` preflight (`gh auth` scopes, Projects-v2 org gotcha, wiki first-page, graceful downgrade). |
| **C** | Curated vs bulk raw | **DONE** | `gitignore.tmpl` carve-out idiom + `context.md` + `AGENTS.md.tmpl`. |
| **D** | Multi-pipeline monorepo + src/scripts | **DONE (directory-level only)** | `context.md`/`directory-tree.md` specify `pipelines/<name>/` + 1:1 issue mapping and resolve src↔scripts. **This is the seam Part 2 must operationalize.** |
| **E** | Deferred/conditional sensitivity | **DONE** | escalation-levels + installed-base + interviewer + `ROADMAP.md.tmpl`. |
| **F** | Context-rich fast path | **DONE** | `SKILL.md` Step 2 + interviewer "fast path." |
| **G** | Notebook hygiene / nbstripout | **DONE** | `NOTEBOOKS` flag + `gitattributes.tmpl` + pre-commit + `environment.yml` + AGENTS note. |
| **H** | Novice-legibility pass | **PARTIAL** | The authoring guardrail shipped (`SKILL.md`); the **line-level rewrite of the named checklists' instructions was not done** — carry forward (Phase 7). |
| **I** | Minor notes | **DONE** | CI-first-at-L2 note; branch→PR→merge guardrail. |

**Reconcile-before-extend:** before adding anything, align the v1 plan's file names with what actually shipped (Phase A) so `INDEX.md` and cross-references are accurate.

## Part 2 — New phases (the monorepo seam)

Ranked by leverage. Each is opt-in by level/flag; lean-by-default still governs.

### Phase 1 — Template the **multi-pipeline CI** (auto-discovered matrix) *(highest leverage, cheapest)*
**Problem:** the skill's CI template (`templates/ci/github-actions-ci.yml.tmpl`) is **single-job, single-project** — no matrix, no `pipelines/<name>` awareness. The repo hand-wrote a static matrix, **duplicated across two workflows**, and a row landed before its dir → `main` CI red for 4m24s (PR #47).
**Changes:** add a **monorepo CI template** that derives the matrix by globbing `pipelines/*/pyproject.toml` (covers test + scheduled-refresh workflows from one source); document the ordering rule (**CI row and pipeline land in the same PR**) for the static fallback. Gate behind a `PIPELINES` (multi-pipeline) flag.
**Acceptance:** scaffolding a multi-pipeline repo emits a CI that tests every `pipelines/*` automatically; adding a pipeline needs no workflow edit; a dry-run shows all current pipelines discovered.

### Phase 2 — A first-class **"land a pipeline" sub-flow**
**Problem:** four pipelines landed four ways (reservoir ~15 PRs; streamflow bundled invisibly into governance PR #37; snowpack 1 + contaminated; climate-stations 2 in the wrong order). The skill models *build* and *track* but not *land*.
**Changes:** add a documented, ordered procedure (a `references/landing-a-pipeline.md` + a `SKILL.md` pointer): isolated worktree → scaffold `pipelines/<name>/` → CI row (same PR) → **repo-doc registration** (Phase 3) → Dataverse kit → one PR `Add <name> pipeline (#NN)` with `Closes #NN` → CI green → merge → verify `origin/main`. One concern per PR; never bundle a pipeline into a docs/governance PR.
**Acceptance:** the skill can walk a built pipeline to a single, correctly-ordered, issue-closing PR.

### Phase 3 — Model **repo-doc registration as a projection**
**Problem:** registering a "complete" pipeline means hand-editing ~9 repo docs + a Dataverse kit + two CI workflows. It was done **inconsistently** (climate-stations #48 registered *zero* docs; snowpack #45 missed the ROADMAP table row; streamflow got light registration). `engagement-sync.json` was never updated for #44. Result: the repo undercounts itself ("three built").
**Changes:** extend the "projection" model beyond GitHub issues to the **prose docs**. Ship a **registration checklist** (the exact file set: README/ROADMAP/CHANGELOG/AGENTS/decision-log/data-management-plan/data-card/wiki + both CI workflows + `engagement-sync.json`) and, where feasible, a generator/`<!-- data-project:pipeline=<name> -->` marker block the tracker can reconcile. Tie it into Phase 2's landing flow.
**Acceptance:** landing a pipeline updates (or verifiably lists) every registration surface; a reconcile step flags a repo whose doc pipeline-count disagrees with `pipelines/*`.

### Phase 4 — Decide & document the **shared-code stance for stamped siblings**
**Problem:** the skill says "shared code belongs in `src/<pkg>/`" (`context.md`) but offers **no mechanism**; reality went 100% copy-paste (≈49% duplication; `provenance.py` AST-identical ×4). "Stamp a sibling" is the de-facto process with no guidance on *what* to share vs copy.
**Changes:** add a short **`references/stamping-and-shared-core.md`**: when a repo crosses ~3 pipelines, factor domain-agnostic plumbing (provenance, fetch engine, clean orchestration, CLI skeleton, `normalize_long`) into a shared package (`pipelines/_core/` or root `src/<pkg>/`), keep domain logic (sources/parsers/stations/schema-vocab/audit-extensions) per pipeline; ship a "stamp a sibling" procedure (what to copy, what to rename, the contract each pipeline must expose). State the trade-off (coupling vs maintenance) and the threshold.
**Acceptance:** a user adding a 4th pipeline is pointed at a shared-core refactor with a concrete what-to-share list, not left to copy-paste.

### Phase 5 — **Multi-agent / shared-working-tree isolation** guidance
**Problem:** a grep of the entire skill for worktree / `git add -A` / concurrent-agent returns **nothing**. Concurrent agents on one checkout caused PR #45 to swallow 37 untracked files from another agent (3-PR repair). The lesson currently lives only in user memory.
**Changes:** add to `SKILL.md` guardrails (and/or a `references/git-github-collaboration.md`): prefer a **git worktree per agent**; **stage explicit paths, never `git add -A`/`.`** in a dirty tree; **`git fetch` + verify `origin/main` before merge** (and before auditing — a stale checkout produces false findings).
**Acceptance:** the skill's collaboration guidance names worktree isolation and explicit staging as defaults on shared repos.

### Phase 6 — **Close issues on landing** in Track mode
**Problem:** the tracker closes an issue when its TODO leaves `ROADMAP.md`, decoupled from PR merges — so #11/#44 closed but #9/#10 stayed open though built (3 states / 4 pipelines).
**Changes:** in `agents/data-project-tracker.md` + `github-project-management.md`: enforce `Closes #N` on the landing PR and reconcile issue state against **merged work**, not only `ROADMAP.md` diffs; on a track run, flag built-but-open (and closed-but-unbuilt) pipeline issues.
**Acceptance:** a tracked pipeline issue is closed by its landing PR; a reconcile run reports any built/open mismatch.

### Phase 7 — Finish the v1 **novice-legibility** pass (carry-over)
**Problem:** v1 Phase H shipped the *principle* but not the *line-level rewrite* of the QA / responsible-data / data-dictionary checklist instructions; the repo's four L4 checklists are still terse, empty templates that no pipeline filled.
**Changes:** rewrite each templated checklist instruction to be self-contained (what / where / how / success-vs-failure), and add a per-pipeline "fill this for each dataset" prompt so the checklists get *executed*, not just shipped.
**Acceptance:** a newcomer can action each checklist item without outside context, and the scaffold nudges filling one per pipeline.

---

## Suggested order & sizing

1. **Reconcile Phase A's file names** with the shipped skill (housekeeping; prevents compounding drift).
2. **Phases 1 + 2 + 3** (CI matrix, landing flow, registration projection) — the load-bearing monorepo-seam gap; do together.
3. **Phases 5 + 6** (isolation, issue-closure) — small, high-value process fixes.
4. **Phase 4** (shared-core stance) — documentation now; it guides the project's own Phase 4 refactor.
5. **Phase 7** (legibility carry-over).

Per change: scaffold into a temp dir / dry-run, grep for unfilled `{{` tokens, confirm links resolve, and keep `INDEX.md` build-status honest. Keep the diff small and the defaults lean — the goal is to make the skill anticipate what the **second through fourth** pipelines had to improvise, not to make it heavier.
