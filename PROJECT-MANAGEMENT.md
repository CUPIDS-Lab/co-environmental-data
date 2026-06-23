# Project management — how we track work on Colorado Environmental Data Hub

This document explains how Colorado Environmental Data Hub tracks its work so that anyone joining can see what is planned, what is in flight, and who owns it. The short answer that always holds: we keep the assignable checklist in `ROADMAP.md` and the human handoff memo in `NEXT-STEPS.md`, and those two files are enough to run the project on their own. Everything below describes the GitHub layer that mirrors them for the team.

## The flow: issue → milestone → board

Each task is one GitHub Issue, because an issue is the smallest unit a person can be assigned and held accountable for, and a single task per issue keeps that accountability legible. Issues for a given work batch are grouped under a **milestone** — there are now **four**: **L1-L2: catalog hardening & pipeline** (#2–#5, #7), **Water data liberation** (#9–#11), **Climate data liberation** (#44, complete), and **L3-L4: collaboration & responsible-data** (#31–#36), grown as the project climbed and added pipelines — so "what does this batch still owe" is one click away and closing the milestone marks it done. Issues then surface on the **Colorado Environmental Data Hub** Project board, which is where the team plans and tracks across views — board, table, and roadmap — rather than reading raw issue lists.

The tracked batches are the *actionable-now* slices of the roadmap: (1) harden the source catalog (verify the `needs_followup` sources, quarantine the spurious NREL `nlr.gov` claim, add the `match_hosts`/`match_keywords` citation-match fields) and stand up the L2 reproducible pipeline; and (2) operationalize the L3/L4 scaffolds — onboard the team, name the CEJ contact, secure a fair-use/ToS review, fill the codebook + calibration, validate the LLM detector, and run the QA gates before the first Dataverse publish. The deferred L5 concerns (OKF bundle, Datasette + Quarto site, agent-discovery) stay as roadmap text until the project climbs to them.

## Label taxonomy

Labels are kept deliberately few so an issue's chips read at a glance. **Planning metadata the board sorts by — priority, size, and level — lives in Project _fields_, not labels** (see "The board" below); labels carry only *what kind of work* it is plus a couple of at-a-glance flags. A label nobody trusts is worse than no label, so apply these consistently and resist re-adding planning dimensions as labels.

- `type:*` (`type:data`, `type:docs`, `type:pipeline`, `type:governance`, `type:infra`) — the kind of work, so a specialist can find the issues that need their skills.
- `blocking` — this task gates a real action (ingesting article text, publishing, or climbing a level); a `blocking` issue must be closed, or its risk explicitly accepted, before the project does the thing it guards, and before climbing.
- `good-first-issue` — well-scoped and approachable; the unassigned data-quality tasks are flagged this way for incoming undergraduate contributors.
- `help-wanted` — maintainers are actively seeking help on this.

> **Priority, Size, and Level are Project fields, not labels** (retired as labels on 2026-06-23 to cut per-issue chip clutter — an issue went from ~5 chips to ~2). The board sorts and groups by them; `seed-github.sh` sets them per issue from the `ROADMAP.md` Priority/Size/Level columns. GitHub's unused default labels (`bug`, `enhancement`, `question`, `duplicate`, …) were removed at the same time in favor of this taxonomy. The full label set is now just the eight above (`type:*` ×5 + `blocking` + `good-first-issue` + `help-wanted`).

## Source of truth and idempotent sync

The `ROADMAP.md` checklist is the source of truth, and GitHub is a projection of it, so that the project's plan survives even when the board does not and never lives in only one place. Edit the checklist first, then re-run `data-project track` (or `.github/seed-github.sh`) to create-or-update the labels, milestone, issues, and Project items from it. The sync is **idempotent** — it matches existing issues by the hidden `<!-- data-project:task=… -->` marker (and `.github/engagement-sync.json`) and updates them rather than filing duplicates — so it is safe to run again after every roadmap edit; let Projects auto-sync assignees, labels, and milestones rather than maintaining the same value in two places.

## The board (standardized setup)

The `Colorado Environmental Data Hub` Project configures these custom fields, because tracking each value in exactly one place — and not duplicating it as a label — is what stops metadata drift and keeps the issue list legible:

- **Status** (Todo / In progress / Done) — the source of the board columns. The sync sets it to Todo on a *newly created* issue only, so re-syncs never reset a card you've moved.
- **Priority** (High / Medium / Low) — set per issue by `seed-github.sh` from the ROADMAP Priority column.
- **Size** (S / M / L) — set per issue by the sync from the ROADMAP Size column.
- **Level** (L0–L5) — set per issue by the sync; lets the board group by escalation rung (the milestone gives the coarser L1-L2 / L3-L4 batches).
- **Iteration** — week-by-week cadence for planning, once the team works in iterations.

Setting a single-select field needs the Project/field/option GraphQL node ids (the `gh project item-edit --field NAME --value VAL` shorthand silently no-ops), so the sync resolves them once and edits each item by id; see `project_set_select` in `seed-github.sh`.

Three saved views cover the common reads: **Board by Status** (day-to-day flow), **Table by Level** (planning a level's scope, bulk edits), and **Roadmap** (timeline over target dates). Enable the built-in workflows — auto-add matching repo issues, set Status→Done when an issue closes, and auto-archive — so the board maintains itself. Assignees, labels, milestone, and linked PRs are **not** duplicated as custom fields; Projects syncs those from the issue automatically. Once the layout is right, save it as an **org template** ("Make template" → "Use this template") so the next CUPIDS engagement starts standardized.

## Power-user tips

Drive the board from the terminal with the `gh project` CLI (list, item-add, item-edit) to script repetitive changes. On the **table view**, set one cell and copy/paste it across a selection to bulk-edit a field — for example, set `Priority` or `Iteration` for a whole batch in one motion. Add issues from any repository by pasting their links or searching with `#` in the board, so cross-team dependencies live on one board.

## Access and scopes

Automating any of the above needs the right token scopes, and the most common failure is that Projects v2 lives at org/user scope, not repo scope — so a token that can file issues still cannot touch the board. See `.github/ACCESS.md` for the exact scopes each path needs (`gh` refresh, classic PAT, fine-grained PAT, or GitHub App) and the preflight that downgrades gracefully rather than failing when a scope is missing. When a CI workflow needs to reach a Project or the wiki, supply a PAT or App token as a repository secret and reference it by its secrets name (for example secrets.PROJECTS_TOKEN); the default Actions token cannot modify org Projects or push the wiki.

## Long-form docs live in the wiki

Narrative and how-to documentation that outgrows the README lives in this repository's wiki, a separate git repo with its own `Home` and `_Sidebar`, so the front-door docs stay short while deeper material has room. By default only repository collaborators can edit the wiki, which is why it stays opt-in; the seed pages live in `.github/wiki-seeds/` and are pushed to `<repo>.wiki.git` once the wiki's first page exists. Point readers there for context, and keep the plan itself in `ROADMAP.md`.

We track work in `ROADMAP.md` and `NEXT-STEPS.md`. Those two files are always present and always current, and they are sufficient on their own; the GitHub layer above is a convenience for shared, assignable tracking, not a replacement for the Markdown record.
