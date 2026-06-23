# Project management — how we track work on Colorado Environmental Data Hub

This document explains how Colorado Environmental Data Hub tracks its work so that anyone joining can see what is planned, what is in flight, and who owns it. The short answer that always holds: we keep the assignable checklist in `ROADMAP.md` and the human handoff memo in `NEXT-STEPS.md`, and those two files are enough to run the project on their own. Everything below describes the GitHub layer that mirrors them for the team.

## The flow: issue → milestone → board

Each task is one GitHub Issue, because an issue is the smallest unit a person can be assigned and held accountable for, and a single task per issue keeps that accountability legible. Issues for a given work batch are grouped under a **milestone** — there are now two: **L1-L2: catalog hardening & pipeline** (#2–#5, #7) and **L3-L4: collaboration & responsible-data** (#31–#36), added when the project climbed to L4 — so "what does this batch still owe" is one click away and closing the milestone marks it done. Issues then surface on the **Colorado Environmental Data Hub** Project board, which is where the team plans and tracks across views — board, table, and roadmap — rather than reading raw issue lists.

The tracked batches are the *actionable-now* slices of the roadmap: (1) harden the source catalog (verify the `needs_followup` sources, quarantine the spurious NREL `nlr.gov` claim, add the `match_hosts`/`match_keywords` citation-match fields) and stand up the L2 reproducible pipeline; and (2) operationalize the L3/L4 scaffolds — onboard the team, name the CEJ contact, secure a fair-use/ToS review, fill the codebook + calibration, validate the LLM detector, and run the QA gates before the first Dataverse publish. The deferred L5 concerns (OKF bundle, Datasette + Quarto site, agent-discovery) stay as roadmap text until the project climbs to them.

## Label taxonomy

Labels exist so you can slice the work the way a question demands — by level, by urgency, by effort, by kind, or by what is stuck — without reading every issue. Apply them consistently; a label nobody trusts is worse than no label, because it invites filtering on stale data.

- `level:*` (`level:L0` … `level:L5`) — which maturity rung the task belongs to, mirroring the level milestone so you can filter the ladder.
- `priority:*` (`priority:high`, `priority:med`, `priority:low`) — how soon it matters, so the team pulls the right work next rather than the most recently filed.
- `size:*` (`size:s`, `size:m`, `size:l`) — rough effort, so a week can be planned against real capacity instead of issue count.
- `type:*` (`type:data`, `type:docs`, `type:pipeline`, `type:governance`, `type:infra`) — the kind of work, so a specialist can find the issues that need their skills.
- `blocking` — this task gates a real action (ingesting article text, publishing, or climbing a level); a `blocking` issue must be closed, or its risk explicitly accepted, before the project does the thing it guards, and before climbing.
- `good-first-issue` — well-scoped and approachable; the two unassigned data-quality tasks are flagged this way for incoming undergraduate contributors.

## Source of truth and idempotent sync

The `ROADMAP.md` checklist is the source of truth, and GitHub is a projection of it, so that the project's plan survives even when the board does not and never lives in only one place. Edit the checklist first, then re-run `data-project track` (or `.github/seed-github.sh`) to create-or-update the labels, milestone, issues, and Project items from it. The sync is **idempotent** — it matches existing issues by the hidden `<!-- data-project:task=… -->` marker (and `.github/engagement-sync.json`) and updates them rather than filing duplicates — so it is safe to run again after every roadmap edit; let Projects auto-sync assignees, labels, and milestones rather than maintaining the same value in two places.

## The board (standardized setup)

The `Colorado Environmental Data Hub` Project configures these custom fields, because tracking each value in exactly one place — and letting the Project sync the rest from the issues — is what stops metadata drift:

- **Status** (Todo / In progress / Done) — the source of the board columns.
- **Priority** (High / Medium / Low) — set from each issue's `priority:*` label.
- **Size** (S / M / L) — set from the `size:*` label.
- **Level** (L0–L5) — set from the `level:*` label; lets the board group by escalation level.
- **Iteration** — week-by-week cadence for planning, once the team works in iterations.

Three saved views cover the common reads: **Board by Status** (day-to-day flow), **Table by Level** (planning a level's scope, bulk edits), and **Roadmap** (timeline over target dates). Enable the built-in workflows — auto-add matching repo issues, set Status→Done when an issue closes, and auto-archive — so the board maintains itself. Assignees, labels, milestone, and linked PRs are **not** duplicated as custom fields; Projects syncs those from the issue automatically. Once the layout is right, save it as an **org template** ("Make template" → "Use this template") so the next CUPIDS engagement starts standardized.

## Power-user tips

Drive the board from the terminal with the `gh project` CLI (list, item-add, item-edit) to script repetitive changes. On the **table view**, set one cell and copy/paste it across a selection to bulk-edit a field — for example, set `Priority` or `Iteration` for a whole batch in one motion. Add issues from any repository by pasting their links or searching with `#` in the board, so cross-team dependencies live on one board.

## Access and scopes

Automating any of the above needs the right token scopes, and the most common failure is that Projects v2 lives at org/user scope, not repo scope — so a token that can file issues still cannot touch the board. See `.github/ACCESS.md` for the exact scopes each path needs (`gh` refresh, classic PAT, fine-grained PAT, or GitHub App) and the preflight that downgrades gracefully rather than failing when a scope is missing. When a CI workflow needs to reach a Project or the wiki, supply a PAT or App token as a repository secret and reference it by its secrets name (for example secrets.PROJECTS_TOKEN); the default Actions token cannot modify org Projects or push the wiki.

## Long-form docs live in the wiki

Narrative and how-to documentation that outgrows the README lives in this repository's wiki, a separate git repo with its own `Home` and `_Sidebar`, so the front-door docs stay short while deeper material has room. By default only repository collaborators can edit the wiki, which is why it stays opt-in; the seed pages live in `.github/wiki-seeds/` and are pushed to `<repo>.wiki.git` once the wiki's first page exists. Point readers there for context, and keep the plan itself in `ROADMAP.md`.

We track work in `ROADMAP.md` and `NEXT-STEPS.md`. Those two files are always present and always current, and they are sufficient on their own; the GitHub layer above is a convenience for shared, assignable tracking, not a replacement for the Markdown record.
