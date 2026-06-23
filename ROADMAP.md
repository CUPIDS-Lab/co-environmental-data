# ROADMAP — this level's work and what's deferred

This project was scaffolded at level **L1** and **climbed to L4** (collaboration + responsible-data & accessibility) on **2026-06-22**, deliberately right-sized. It records both the work being tracked now (assignable, below) and the concerns deferred to future levels, so nothing important is lost and the next maintainer — or agent — knows what to do now and what to add later. The full methodology and technical design for most items already exist in `context/` — `methodology.md` (research design), `architecture.md` (the pipeline), and `source-inventory.md` (the discovery audit).

**What the L3/L4 climb added:** the collaboration scaffolds (`CONTRIBUTING`, `CODE_OF_CONDUCT`, `ROLES`+`.github/CODEOWNERS`, `GOVERNANCE`, `CHARTER`, `collaboration-protocol`, `contributed-data-intake`, nested `.skills/`) and the responsible-data & accessibility layer (`INSTALLED-BASE`, `data-management-plan`, `responsible-data-checklist`, `data-bulletproofing-checklist`, `data-quality-checklist`, `accessibility-checklist`, `data-card`). These **encode duties before the affordances they guard** — the news corpus's copyright/fair-use and journalist-privacy obligations are now first-class checklists, not buried roadmap prose. The remaining work below is to **operationalize** them (name the partners, fill the codebook, satisfy the gates) and then publish (L5).

## This level's work (assignable)

The actionable-now slice of the roadmap. Each row is a checkbox you can assign and track; check it when its definition-of-done is met. The full definition-of-done lives in the linked issue.

| ✓ | Task | Owner | Priority | Size | Definition of done | Blocking? | Level | Links |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ☐ | Verify the 9 `needs_followup` sources | _unassigned_ · good-first-issue | High | M | 9 sources confirmed live and flipped to `verified` | **Yes** | L1 | [#2](https://github.com/CUPIDS-Lab/co-environmental-data/issues/2) |
| ☐ | Quarantine the spurious NREL `nlr.gov` claim | _unassigned_ · good-first-issue | High | S | `nrel.gov` confirmed canonical; `nlr.gov` absent everywhere | **Yes** | L1 | [#3](https://github.com/CUPIDS-Lab/co-environmental-data/issues/3) |
| ☐ | Add `match_hosts` / `match_keywords` to the catalog | @brianckeegan | High | M | both fields on every source; matcher unit-tested | **Yes** | L2 | [#4](https://github.com/CUPIDS-Lab/co-environmental-data/issues/4) |
| ☐ | Build the L2 reproducible pipeline (cejcorpus stubs) | @brianckeegan | Med | L | env + package + `nb-00…09` stubs + tests + CI dry-run | No | L2 | [#5](https://github.com/CUPIDS-Lab/co-environmental-data/issues/5) |
| ◐ | Liberate CO water data — reservoir, streamflow, snowpack (reservoir #9 **built**) | _unassigned_ · help-wanted | High | L | series retrieved, tidied, documented, reconciled vs. source, republished | No | L2 | [#7](https://github.com/CUPIDS-Lab/co-environmental-data/issues/7) |
| ☐ | **Onboard the undergraduate team** — fill `ROLES.md` gaps; replace `@brianckeegan` placeholders in `.github/CODEOWNERS` with team handles | @brianckeegan | High | M | each core role owned or its gap named; CODEOWNERS routes to real reviewers | No | L3 | [#31](https://github.com/CUPIDS-Lab/co-environmental-data/issues/31) |
| ☐ | **Name the CEJ subject-matter contact** in `collaboration-protocol.md` | @brianckeegan | High | S | a committed CEJ contact named for codebook adjudication | **Yes** | L3 | [#32](https://github.com/CUPIDS-Lab/co-environmental-data/issues/32) |
| ☐ | **Secure a fair-use / licensed-DB ToS review** (CU Libraries / University Counsel) | @brianckeegan | High | M | the `data-management-plan.md` §Compliance posture reviewed and signed off | **Yes** | L3 | [#33](https://github.com/CUPIDS-Lab/co-environmental-data/issues/33) |
| ☐ | **Fill the codebook + run inter-coder calibration** (Krippendorff α ≥ 0.80; double-code ~10%) | @brianckeegan | High | L | codebook with ≥2 examples per `citation_type`; calibration clears α threshold | **Yes** | L4 | [#34](https://github.com/CUPIDS-Lab/co-environmental-data/issues/34) |
| ☐ | **Validate the LLM citation detector** (precision/recall vs. gold standard; quote-span guard; closed-set) | @brianckeegan | Med | M | precision ≥ 0.90 with quote-span verification before any label is promoted | **Yes** | L4 | [#35](https://github.com/CUPIDS-Lab/co-environmental-data/issues/35) |
| ☐ | **Run the QA gates before the first Dataverse publish** of reservoir storage (`data-bulletproofing-checklist` + `responsible-data-checklist`) | @brianckeegan | High | S | both checklists complete; human-reviewed v1.0 published; DOI recorded | **Yes** | L4 | [#36](https://github.com/CUPIDS-Lab/co-environmental-data/issues/36) |

**Tracking:** this checklist is the source of truth for the current work. It is mirrored as GitHub Issues on the **Colorado Environmental Data Hub** [Project board](https://github.com/orgs/CUPIDS-Lab/projects/1) — see `PROJECT-MANAGEMENT.md`. Edit this checklist and re-run `.github/seed-github.sh` (or `data-project track`) to create-or-update the issues idempotently; the checklist stays canonical. The two `good-first-issue` rows are left unassigned for incoming undergraduate contributors.

> **Epic #7 breaks into per-domain sub-issues:** [#9](https://github.com/CUPIDS-Lab/co-environmental-data/issues/9) reservoir storage — **built** in [`pipelines/reservoir-storage/`](pipelines/reservoir-storage/) (CO DWR/CDSS + USBR Reclamation RISE live; full per-site history; tidy day-resolution CSV; provenance + concept caveats; Northern Water resolved as boundaries-only, its C-BT reservoirs sourced from RISE; monthly CI refresh + Dataverse deposit kit). *Remaining:* publishing only — the first **human-reviewed** Dataverse deposit, now gated behind the L4 QA checklist (#36). · [#10](https://github.com/CUPIDS-Lab/co-environmental-data/issues/10) stream/river flow and [#11](https://github.com/CUPIDS-Lab/co-environmental-data/issues/11) snowpack (SWE) — **not started**. Each is a retrieve → tidy → document → audit → publish slice, linked as native GitHub sub-issues of #7.

## Deferred items

Concerns that are real but above the current tracked work — added when you climb to **L5 (publish as open knowledge)**. The design for most already exists in `context/`.

| Concern | Why deferred | Adds it (template / level) | Blocking? |
| --- | --- | --- | --- |
| **Open-knowledge publication** — OKF `knowledge/` bundle (concept catalog from the data dictionary), the **Datasette catalog + Quarto site**, `LICENSE-NOTE`, `data-collaborative-canvas` | Publish after the pilot clears its exit thresholds (`context/methodology.md` §7); the public site is where the accessibility checklist's figure/color/table checks become load-bearing | L5 | No |
| **Extend the Dataverse deposit to the sibling pipelines** — streamflow (#10), snowpack (#11) inherit the reservoir pipeline's `dataverse/` kit | Those pipelines are not built yet | L5 / ongoing | No |
| **Agent-discovery layer** — `ai-catalog.json` (ARD) + `DISCOVERY.md` so agents can find the catalog, datasets, and `.skills/`; host `.well-known/` + registry deployment | Discoverability matters once there is a stable published surface | L5 | No |
| **Zero-copy sharing** — OpenSharing share kit for partners who need working access without a copy (gated by `GOVERNANCE.md` tiers) | No external partner needs in-place access yet | L5 (optional) | No |

## How to climb a level

Re-run the `data-project` skill in this directory and ask to climb to the next level (e.g. "take this to L5"). The skill adds only the new level's artifacts, refreshes this roadmap, and files the new level's tasks as issues. Items marked **blocking** must be resolved — or explicitly acknowledged — before the project does the thing they guard (e.g. before coding citations, ingesting article text, promoting LLM labels, or publishing), and before climbing.

## Note on future-sensitive work (do not skip)

The data in this repo today is public, so the sensitive tier in `GOVERNANCE.md` is provisioned but **empty**. The L3/L4 climb made the planned news corpus's two duties first-class so they travel with the affordances they guard: **copyright/fair-use** (the public site shows metadata + excerpts + archived links, never republished article text; licensed-DB content is manual-export-only and never redistributed) and **journalist privacy** (professional information only; a documented correction / right-to-respond process; the `coverage_tier` guard). These now live in `GOVERNANCE.md`, `responsible-data-checklist.md`, `contributed-data-intake.md`, and `INSTALLED-BASE.md`, and the **blocking** rows above (#32–#36) gate the corpus build on them. Resolve those before building the corpus, not after. Affordances without duties are theater.
