# Governance — Colorado Environmental Data Hub

This file says who may touch what, how long we keep things, how decisions get made, and how a documented problem becomes a correction. It exists because public-interest data infrastructure sits under chronic pressure to be enclosed, exempted from scrutiny, and quietly eroded; the answers below are how the Colorado Environmental Data Hub resists each. Read it with `ROLES.md` (who holds these responsibilities) and `CHARTER.md` (what survives the pilot). This project's sensitivity is **public today (open government/agency metadata), conditionally sensitive-human once the news corpus ingests article text + journalist records**, and its openness posture is **open (MIT-licensed; open data)**.

## Access tiers

Access is documented and tiered so that visibility is legitimate rather than ambient — what is open is deliberately open, and what is restricted is reachable only by accountable people. Least privilege is the default.

| Tier | What it covers | Who may access | How access is granted |
| --- | --- | --- | --- |
| **Public** | The curated source catalog (`data/raw/colorado_environmental_data_sources.json`); processed liberated datasets (e.g. the reservoir-storage CSV); all documentation; the planned Datasette + Quarto site, which shows **metadata + short excerpts + archived links only** — never republished article text. | Anyone. | No request needed; this is the default and the point. |
| **Restricted** | Interim/un-reconciled pipeline outputs; **licensed-database manual exports** (Nexis Uni, NewsBank, ProQuest, Factiva) whose terms forbid redistribution; raw article HTML and Wayback snapshots cached in Cloudflare R2. | Named project members and approved collaborators with a CU library entitlement where the license requires it. | Request to the project manager (`ROLES.md`); logged; license terms travel with the data. |
| **Sensitive** *(future — gated, empty today)* | Full article text linked to journalist identity; any journalist record beyond a public professional byline. **Not present in the repo today**; this tier is provisioned now so the duty exists before the affordance. | A named, minimal set of accountable intermediaries only. | Documented approval; access logged and time-bound; gated by the **blocking** responsible-data items in `ROADMAP.md`. |

## Retention schedule

Data held without a reason becomes a liability rather than an asset, so each class has a stated life and a custodian (named in `ROLES.md` / `CHARTER.md`).

- **Source catalog (raw):** kept permanently, versioned in git. Immutable — a new vintage is a new file, never an in-place edit (see `decision-log.md`, 2026-06-17).
- **Raw article HTML + archived snapshots (R2):** retained immutably for the life of the corpus so any label can be reconstructed (per `context/methodology.md` §4.6). Restricted tier.
- **Licensed-database exports:** retained only as long as the license permits and only in the restricted tier; deleted when the entitlement ends. Never redistributed.
- **Interim / processed data:** regenerable from raw; not retained as a source of truth — rebuilt by the monthly CI refresh.
- **Sensitive journalist records (future):** minimal, time-bound retention in the sensitive tier; disposal procedure defined before any such record is ingested.

Review this schedule at each level climb and at the start of each semester so it does not drift into indefinite retention by default. The project manager is responsible for carrying out disposal.

## Decision-making

Routine decisions are made by the role that owns the affected path in `.github/CODEOWNERS` (e.g. the data engineer decides a pipeline's grain; the subject-matter expert decides a coding definition). Larger decisions — scope, a new data source, a definition that changes the dataset's meaning, a level climb, anything touching the future corpus's copyright/privacy posture — are made by **consensus among the core roles, with the project manager breaking ties**. Record every non-obvious decision as a dated entry in `decision-log.md` so the reasoning is reviewable by people who join later. Codebook and coding-rule changes additionally follow the adjudication process in `context/methodology.md` §4.2 (third-coder or consensus meeting; log the resolution).

## Contestable oversight

Oversight here is testable, not nominal. What is logged and reviewable:

- **Provenance and change history** — every pipeline run stamps a `run_id`, tool versions, source method, and timestamps on each row it writes (`context/methodology.md` §4.6); `decision-log.md` and `CHANGELOG.md` carry the human-legible history; git carries the rest.
- **Access to the restricted/sensitive tiers** — recorded by the project manager when granted.
- **Releases** — each Dataverse deposit is human-reviewed (draft-only in CI); the published version + UNF is recorded.

The **project manager** holds audit rights and reviews access and release logs at each level climb; the **subject-matter expert** is authorized to interpret and contest coding/labeling evidence rather than merely receive it. The point is that no powerful actor — including an upstream data provider that decommissions a dataset — can quietly carve out an exemption from scrutiny: the catalog's `enclosure`/`erosion` flags and the archived snapshots make erosion itself visible and reviewable.

## Remedy and escalation

A documented problem must have a path to becoming a correction, or oversight is theater. Anyone — a contributor, a journalist whose work appears in the corpus, a collaborating organization, or a member of the public — can raise a concern by contacting **accounts@brianckeegan.com**. A raised concern is acknowledged within a stated timeframe (target: five business days), reviewed by the project manager with the relevant subject-matter expert, escalated to CU Libraries / University Counsel if it concerns licensing or privacy, and its outcome communicated back to the person who raised it and recorded in `decision-log.md`. For the future corpus specifically, a journalist may request **correction or right-to-respond** about how their work is represented; that pathway is part of the responsible-data posture, not a favor (`context/methodology.md` §6.2). The pathway is accessible, protects the person raising the concern, and is consequential.

## Transparency vs. privacy

This project publishes in the public interest and protects the people in its data at the same time, and those goals pull against each other. Standing posture: **default to openness** for the catalog, the liberated environmental datasets, and non-sensitive aggregate findings; **default to protection** for anything that links article text to journalist identity. Resolve specific tradeoffs deliberately, recording the reasoning in `decision-log.md`. When the two genuinely conflict, the duty to the people in the data takes precedence over the convenience of disclosure — concretely, the public site ships metadata + excerpts + archived links, never republished full article text, even though full text would be more convenient.

## Sensitive data — affordances ship with duties

This project will handle **conditionally sensitive-human** data once the news corpus ingests article text + journalist records, where the coupling above is load-bearing and not optional. The data today is public agency metadata, so the sensitive tier is empty — but it is provisioned now, deliberately, so the duty exists *before* the affordance. Every linkability and retention affordance the corpus will introduce — a journalist identifier, an article-to-source crosswalk, a preserved HTML snapshot, an access log — must ship together with the access tier that limits who can reach it and the remedy pathway that lets its use be contested. Do not add a journalist-identifier scheme, a retention extension, or new logging without simultaneously updating the access tiers and escalation process here, and do not ingest article text or journalist records until the **blocking** responsible-data items in `ROADMAP.md` are satisfied. Affordances without duties are surveillance dressed as service. (No Indigenous data is implicated today; if any source in scope changes that, apply the CARE Principles alongside these tiers.)
