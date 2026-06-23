# Colorado Environmental Data Hub

Colorado Environmental Data Hub is a documented, reproducible catalog of Colorado environmental data sources — and the foundation for a research corpus linking Colorado environmental journalists to the public data they cite. This page is the front door to the project's wiki, written so that someone with none of the project's context can understand what it is and where to go next; read this paragraph first, then follow the links below to whatever you need. The project is at maturity level **L4** (collaborative, responsible & accessible): a curated 56-source catalog with a full data dictionary, the built **reservoir-storage**, **streamflow**, **snowpack**, and **climate-stations** data-liberation pipelines (issues #9–#11, #44), the full **collaboration layer** (CONTRIBUTING, ROLES + CODEOWNERS, GOVERNANCE, CHARTER), and the **responsible-data & accessibility** checklists. A 2026-06-22 QA audit (`audits/2026-06-22-qa-audit.md`) tracks the remaining work to publish; the L5 open-knowledge layer (Datasette + Quarto site, OKF bundle) is still to come.

## How we track work

We keep the project's plan in two always-current files in the repository rather than only in a tracker, so the plan is portable and survives any one tool. The `ROADMAP.md` checklist is the assignable, source-of-truth list of what this level still owes and who owns it, and `NEXT-STEPS.md` is the short narrative handoff memo for a reader who will not open a board. For shared, assignable tracking, those same tasks are mirrored as GitHub Issues (#2–#43, across the `L1-L2` and `L3-L4` milestones) and onto the **Colorado Environmental Data Hub** Project board, where the team plans across board, table, and roadmap views.

## Key documents

These links point to the documents most people need; start with the one that matches your question, and treat `README.md` as the canonical front door for the repository itself.

- [README](https://github.com/CUPIDS-Lab/co-environmental-data) — what the project is, how to get started, and how it is laid out.
- [Roadmap](https://github.com/CUPIDS-Lab/co-environmental-data/blob/main/ROADMAP.md) — the assignable checklist of this level's work and what is deferred.
- [Next steps](https://github.com/CUPIDS-Lab/co-environmental-data/blob/main/NEXT-STEPS.md) — the plain-language handoff memo.
- [Project management](https://github.com/CUPIDS-Lab/co-environmental-data/blob/main/PROJECT-MANAGEMENT.md) — how we track work, the label taxonomy, and how to keep the board in sync.
- [Data dictionary](https://github.com/CUPIDS-Lab/co-environmental-data/blob/main/DATA-DICTIONARY.md) — the catalog schema: fields, controlled vocabularies, and known issues.
- [Working norms (AGENTS.md)](https://github.com/CUPIDS-Lab/co-environmental-data/blob/main/AGENTS.md) — the non-negotiables (immutable raw data, open formats, the NREL data-integrity note).
- [Contributing](https://github.com/CUPIDS-Lab/co-environmental-data/blob/main/CONTRIBUTING.md) · [Governance](https://github.com/CUPIDS-Lab/co-environmental-data/blob/main/GOVERNANCE.md) · [Roles](https://github.com/CUPIDS-Lab/co-environmental-data/blob/main/ROLES.md) — how to work here, who may touch what, and who reviews which paths.
- [QA audit (2026-06-22)](https://github.com/CUPIDS-Lab/co-environmental-data/blob/main/audits/2026-06-22-qa-audit.md) — the current bulletproofing/quality/accessibility assessment and what blocks publication.

> Governance now exists: **access tiers, retention, oversight, and the correction process** are in [`GOVERNANCE.md`](https://github.com/CUPIDS-Lab/co-environmental-data/blob/main/GOVERNANCE.md) (arrived with the L3/L4 climb). The future news corpus's copyright and journalist-privacy duties are the **blocking** items in `ROADMAP.md` — satisfy them before ingesting article text.
