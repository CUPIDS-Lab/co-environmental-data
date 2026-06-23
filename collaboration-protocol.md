# Collaboration protocol — Colorado Environmental Data Hub

This file describes how the Colorado Environmental Data Hub coordinates its partner organizations — primarily the **Center for Environmental Journalism (CEJ)** and **CU Libraries** — without the coordination becoming heavier than the work. It is the operational complement to `CHARTER.md` (what we agreed) and `GOVERNANCE.md` (who may touch what): the charter sets the terms, this protocol runs the partnership day to day. Keep the formality minimal and proportionate — this is a within-CU research collaboration, not a multi-agency data-sharing treaty.

## Partnership lifecycle

Treat each partner relationship as having a lifecycle so that joining, contributing, and leaving are all deliberate rather than accidental.

- **Recruit** — identify partners whose data or context the project needs and confirm the value is mutual. *CEJ* brings the journalism judgment (citation definitions, the sampling frame of Colorado environmental reporters via Ted Scripps Fellows and Water Desk contributors) and gains an evidence base about data-driven reporting. *CU Libraries* brings licensed-database access (Nexis Uni, NewsBank, ProQuest, Factiva) and the entitlement to use it.
- **Onboard** — agree the terms (below), grant the appropriate access tier from `GOVERNANCE.md`, walk the partner through the shared definitions and the codebook, and name their point of contact. For the **undergraduate research team**, onboarding additionally means clearing the codebook calibration (every coder codes a training set, then a calibration set, and must clear the α threshold before coding live data — `context/methodology.md` §6.3).
- **Maintain** — keep the agreed cadence, share back results and credit, and surface problems early through the remedy pathway in `GOVERNANCE.md` rather than letting them fester.
- **Wind down** — when a partner leaves or the project ends, settle data retention and deletion (licensed exports are deleted when the entitlement ends), honor any attribution still owed, and record what survives in `CHARTER.md`.

## MOU essentials

A memorandum of understanding here should be short and readable, capturing the few things that prevent disputes. Keep the terms symmetric. At minimum, agree:

- **Embargo** — findings about a partner's domain are not published before joint interpretation (below); CEJ may review corpus findings about Colorado reporting before release.
- **Attribution** — CEJ and CU Libraries are credited in outputs as collaborators; the citation in `README.md` names CUPIDS Lab; agreed before publication, not after.
- **Information-sharing** — the catalog and liberated datasets are public; **licensed-database content stays restricted** and is never redistributed (a hard term from CU Libraries' licenses); article full text stays in the controlled tier per the fair-use posture.
- **Data governance** — which access tier applies to shared data, retention and deletion terms, and licensing, all cross-referenced to `GOVERNANCE.md`. The governing licenses for library exports are the databases' own terms of service.

## Communication cadence

Agree a regular rhythm of contact so coordination does not depend on crises. Standing cadence: a **per-semester planning check-in** (scope for the term, which students take which tasks) plus **ad-hoc adjudication sessions** when the codebook needs a ruling. Between-meeting questions and decisions run through GitHub issues (the source of truth) and the project manager. Decisions affecting a partner are surfaced to that partner's named contact before they land. A predictable cadence keeps smaller voices — a single student coder, a part-time CEJ contact — informed without having to chase.

## Coordinator

One named person — the **coordinator / project manager** from `ROLES.md` — owns the partnership relationships, runs the cadence, and is the point of contact when something needs deciding across partners.

- **Coordinator:** Brian Keegan, PI (@brianckeegan, accounts@brianckeegan.com).
- **CEJ contact:** *to be named before citation coding begins* — see the blocking GAP-CHECK in `ROLES.md`.
- **CU Libraries contact:** *to be named before any licensed-database export is ingested.*

## Reporting recipe and caveats

When partners publish or report from shared data, agree a common **reporting recipe** so the same figure is not described three incompatible ways. The recipe: report citation counts with their `coverage_tier` and `citation_type` breakdown, the time window, the outlets in scope, and the catalog version, and always pair a number with its caveats. The limitations that must travel with any public use: the data **describes and compares, it does not predict or establish causation**; `coverage_tier` boundaries are judgment calls; library-database records carry `links_unavailable=true` (hyperlinks are stripped on export), so their citation detection is weaker; LLM-assigned labels are only authoritative above the validated precision threshold. Collaborative interpretation with CEJ precedes publication so the journalism context corrects misreadings before they reach an audience (`CHARTER.md`, "Collaborative interpretation").
