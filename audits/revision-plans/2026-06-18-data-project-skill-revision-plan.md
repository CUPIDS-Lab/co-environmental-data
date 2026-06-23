---
# Versioning
version: "1.0"
status: draft
created: 2026-06-19
updated: 2026-06-19
# Provenance
title: "Revision plan — data-project skill (post-implementation)"
doc_type: revision-plan
subject_skill: data-project
repository: "CUPIDS-Lab/co-environmental-data"
author: "Claude (Opus 4.8 · claude-opus-4-8)"
generated_by: "Claude Code session"
basis: "Derived from audits/after-action/2026-06-18-data-project-aar.md — phased, file-level edits for a Claude Code session opened in the skill directory."
related:
  - audits/after-action/2026-06-18-data-project-aar.md
tags: [plan, revision, data-project, cupids]
---

# Plan — revise the `data-project` skill in light of the first implementation

**Audience:** a Claude Code session opened in the skill directory
(`~/.claude/skills/data-project/`). **Source of lessons:**
`audits/after-action/2026-06-18-data-project-aar.md` (Colorado Environmental Data Hub build, 2026-06).

## Objective

Close the gaps the first real build exposed — chiefly the **un-formalized GitHub
"Track mode"**, the lack of an **external-prerequisite preflight**, and a handful of
convention/legibility refinements — **without** breaking the skill's lean-by-default
stance. Every addition must be opt-in by level/mode and default to a `ROADMAP.md`
entry when unsure.

## Orient first (don't skip)

Read, in order: `SKILL.md`, `references/escalation-levels.md`,
`references/installed-base.md`, `references/collaboration-architecture.md`,
`references/context.md`, `references/INDEX.md`, and `templates/directory-tree.md`.
Confirm the current modes (scaffold via interviewer→indexer→synthesizer; audit) and
the `{{TOKEN}}` / `<!-- IF:FLAG -->` template conventions. Keep the build-status
discipline in `INDEX.md` (⭐ built / ○ roadmap) accurate for anything you add.

## Global guardrails for this revision

- **Lean-by-default is non-negotiable.** New capability is opt-in (a mode or a level),
  never auto-emitted. Prefer documenting a pattern over generating files.
- **Match existing form:** same token/conditional conventions; new references mirror the
  digest style; new templates carry `{{TOKENS}}` and `IF:FLAG` blocks.
- **Validation per change:** scaffold into a temp dir (`--dry-run` or a throwaway path),
  confirm no unfilled `{{` tokens, confirm links resolve to generated files (or to
  `ROADMAP.md`), and re-read `INDEX.md` for build-status truth.

---

## Phase A — Formalize **Track mode** (GitHub projection) [highest impact]

**Problem:** the issues/board/wiki projection of `ROADMAP.md` was hand-built.

**Changes**
- `SKILL.md`: add a **Track mode** section beside scaffold + audit. Define it: *project
  the actionable-now slice of `ROADMAP.md` onto GitHub Issues + a Project board + the
  wiki, idempotently, as a projection — `ROADMAP.md` stays the source of truth, GitHub
  is regenerable.* State explicitly that **Track mode ≠ an L3 climb** (no governance
  docs are implied).
- New `references/track-mode.md` documenting:
  - The **`engagement-sync.json`** manifest: `task-id → {issue, hash, parent?}`; content
    hash for change detection; never stores values GitHub already syncs.
  - The **idempotent seed** pattern: match existing issues by a hidden marker
    (`<!-- data-project:task=<id> -->`), create-or-update, never duplicate.
  - **Epic decomposition** to native sub-issues (REST `…/sub_issues`), milestones, the
    label taxonomy, and the board's custom fields (Status/Priority/Size/Level).
  - The "tracking status in level-climb offers" rule (e.g. "L3 scaffolded; its 6 tasks
    are issues, 2 blocking still open").
- New `templates/.github/`: `seed-github.sh.tmpl`, `engagement-sync.json.tmpl`, issue
  forms (`bug`, `data-task`, `good-first-issue`), `pull_request_template.md.tmpl`,
  `ACCESS.md.tmpl`, and `wiki-seeds/{Home,_Sidebar}.md.tmpl`.
- `references/INDEX.md`: add a Track-mode row block (artifact → template → status).

**Acceptance:** invoking Track mode on a repo with a `ROADMAP.md` produces issues +
board + wiki from the roadmap, idempotently (a second run reconciles, creates nothing
duplicate), with `engagement-sync.json` as the manifest.

## Phase B — External-prerequisite **preflight** for Track mode [highest impact]

**Problem:** the `project` OAuth scope and the wiki's first page stalled the flow.

**Changes**
- In `references/track-mode.md` (and a one-line pointer in `SKILL.md`): a **preflight**
  the skill runs *before* projecting — check `gh auth status` scopes (`repo`; `project`
  for boards; `read:org`), wiki initialization (first page exists), and the git remote.
- Provide **exact remediation** strings and **graceful degradation**: do everything that
  doesn't need the missing capability (Markdown + issues), then clearly defer the board
  / wiki with a single quoted instruction (grant scope; create the wiki home page) —
  never silently stall.

**Acceptance:** with a missing `project` scope, the skill files issues, states the
exact scope-grant command, defers the board, and continues — no silent hang.

## Phase C — Refine the **raw-data** convention (curated vs bulk)

**Problem:** "raw is immutable + git-ignored" wrongly excludes small curated catalogs.

**Changes**
- `references/context.md` (Design principles) + `templates/AGENTS.md.tmpl` +
  `templates/gitignore.tmpl`: distinguish **(a) curated source-of-record** (small,
  hand-made, the project's actual asset) → **tracked** via a `.gitignore` carve-out and
  documented as immutable, vs **(b) bulk/external/re-downloadable raw** → git-ignored.
  Ship the carve-out idiom in `gitignore.tmpl` as a commented example.

**Acceptance:** scaffolding a project whose input is a small curated file tracks it (or
asks), instead of git-ignoring the project's only data.

## Phase D — Specify the **multi-pipeline monorepo** + `data-liberation` handoff

**Problem:** the real shape (N liberation pipelines under one data-project repo) is
narrated, not specified; `src/` vs `scripts/` diverges.

**Changes**
- `references/context.md` ("relationship to data-liberation") + a short section in
  `templates/directory-tree.md`: a data-project repo hosts pipelines under
  **`pipelines/<name>/`**, each mapped to a Track-mode issue/sub-issue and tracked by
  the umbrella `ROADMAP.md`/board. Show the issue→pipeline mapping.
- **Resolve `src/`↔`scripts/`:** pick one convention repo-wide (recommend `src/<pkg>/`
  for testability/imports) and state it in both skills, *or* explicitly bless
  `data-liberation`'s `scripts/` when nested and document why. Don't leave it implicit.

**Acceptance:** a user climbing from data-project into building pipelines has a
documented directory + issue convention and no `src/`/`scripts/` ambiguity.

## Phase E — Add **deferred/conditional sensitivity** as a disposition

**Problem:** "public now, sensitive when X is built" was hand-encoded.

**Changes**
- `references/installed-base.md` (the affordance↔duty coupling) +
  `references/escalation-levels.md` (now/later/skip) + the interviewer agent +
  `templates/ROADMAP.md.tmpl`: add a **"becomes-sensitive-when-`<event>`"** disposition
  that emits **blocking** ROADMAP rows gating the sensitive build (coupling deferred but
  enforced), rather than firing heavy governance now.

**Acceptance:** the interview can mark "sensitive once the corpus ingests PII/copyright"
and the scaffold records it as blocking roadmap items — a first-class outcome.

## Phase F — Document the **context-rich fast path**

**Problem:** a full cold-start interview is overkill when design docs are supplied.

**Changes**
- `SKILL.md` (workflow) + `agents/data-project-interviewer.md`: when the user supplies
  substantial design docs (a `/context/` dump), **infer the Project Context Profile from
  them and present it for confirmation/correction**, instead of interrogating. Keep the
  single human approval gate intact.

**Acceptance:** a rich-context invocation skips the questionnaire and lands on a
confirmable, inferred profile.

## Phase G — Scaffold **notebook hygiene** when notebooks are present

**Problem:** notebooks kept getting committed with outputs.

**Changes**
- `templates/` + `SKILL.md`: when the project uses notebooks (L2 `exploratory/`, or a
  notebook-driven pipeline), scaffold the **`nbstripout`** git filter — a
  `*.ipynb filter=nbstripout diff=ipynb` rule in `.gitattributes`, **non-required**
  config, the dev-dependency, and a one-time `nbstripout --install` note in `AGENTS.md`.

**Acceptance:** a notebook project commits output-free by default; clones without the
filter degrade gracefully (no errors).

## Phase H — **Novice-legibility pass** on template instructions

**Problem:** template instructions assume an expert runner (e.g. the reconcile step).

**Changes**
- Audit `templates/*.md.tmpl` (priority: `data-quality-checklist`,
  `responsible-data-checklist`, `data-bulletproofing-checklist`, `data-card`,
  `data-dictionary`): every instruction a runner must act on should answer **what /
  where / how / what success vs failure looks like**, self-contained.
- Add a one-line **template-authoring guardrail** to `SKILL.md`: instructions are
  written for the newcomer who executes them, not the author.

**Acceptance:** a novice can action each checklist item without outside context.

## Phase I — Minor notes

- `references/escalation-levels.md`: note that CI/checks first appear at **L2+**, so
  "watch/verify after merge" has nothing to report at L0/L1.
- `SKILL.md` guardrails: recommend **branch → PR → merge** for scaffolds on a shared
  repo (avoid committing scaffolds straight to the default branch).

---

## Suggested order & sizing

1. **A + B** (Track mode + preflight) — the load-bearing gap; do together.
2. **C, D** (raw convention, monorepo/handoff) — small but high-leverage.
3. **E, F, G, H** (dispositions, fast path, notebooks, legibility) — refinements.
4. **I** — trivial.

After each phase: dry-run scaffold (and, for A/B, a Track-mode dry-run against a scratch
repo), grep for unfilled `{{`, and update `INDEX.md` build-status. Keep the diff small
and the defaults lean — the goal is to make the skill anticipate what this build had to
improvise, not to make it heavier.
