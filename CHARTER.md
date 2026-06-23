# Charter — Colorado Environmental Data Hub

This charter settles the questions a collaboration must agree on before the work hardens around unstated assumptions. Different institutions define the same things differently and bring incompatible expectations; writing the agreement down up front is cheaper than discovering the disagreement halfway through. Keep it short and revisit it when the collaboration changes. It pairs with `GOVERNANCE.md` (access, retention, remedy) and `ROLES.md` (who does the work).

## Purpose

Colorado's environmental data lives in dozens of federal, state, and local systems, and in 2025–2026 a meaningful slice of it is **eroding** (datasets removed or decommissioned) or **enclosing** (paywalled, login-gated, vendor-mediated). The Colorado Environmental Data Hub maintains a curated, independently verifiable **catalog of ~56 authoritative Colorado environmental data sources** and liberates priority datasets (reservoir storage first) into tidy, documented, citable form — and on that backbone builds a **journalist → article → data-citation corpus** measuring which Colorado environmental journalists cite which public datasets, 2014–present. It is worth doing now because the erosion is happening now, and because no one is systematically measuring how environmental reporting depends on public data while that data is under pressure. Success looks like a catalog whose every source is independently verifiable and a corpus whose every citation is archived and defensible.

## Design partners vs. beneficiaries

- **Design partners (who builds it):** the **CUPIDS Lab** undergraduate research team (CU Boulder — data engineering, software, pipelines) and **Center for Environmental Journalism (CEJ)** collaborators (the journalism subject-matter judgment — what counts as a citation, who counts as an environmental journalist). Brian Keegan (PI) holds the data-science methodology and brokers the two.
- **Beneficiaries (who it's for):** environmental journalists (who gain an evidence base about data-driven reporting and a defense against link rot), researchers studying data journalism, the Colorado public, and future maintainers who can re-verify every source.
- **Standpoint:** when "make the finding public" and "protect the person in the data" pull apart, the project centers **the journalist whose work is being measured** — professional information only, a correction/right-to-respond pathway, and the `coverage_tier` flag so a single environmental story never mislabels someone as an "environmental journalist." The catalog's categories also distribute attention: flagging a source for `erosion`/`enclosure` is itself a normative act that directs scrutiny toward data under threat.

## Shared definitions and joint indicators

Agree on the terms and the measures before collecting or joining data, because the same word registers as incompatible data when each partner uses its own institutional logic. The definitions this collaboration commits to (full rules live in the codebook, `context/methodology.md` §4.2):

- **Environmental journalist** — a person bylined on environmental coverage in a Colorado outlet, classified by `coverage_tier` (**dedicated** beat / **frequent** / **occasional** one-off). The boundary is contested: CEJ's working sense of "environmental journalist" is narrower (a beat) than the data-driven net (anyone bylined once); the `coverage_tier` flag makes the gap explicit rather than absorbing it silently.
- **Data citation** — a journalistic reference to a public dataset, classified into the six `citation_type` values (defined in the codebook with ≥2 worked examples each).
- **Data source** — an entry in the 56-source catalog: an authoritative Colorado environmental dataset with provenance tier (federal/state/local), theme, and `enclosure`/`erosion` flags.
- **Joint indicators** everyone reports against: citation counts by source, by outlet, by `coverage_tier`, and by year; catalog coverage and verification status; per-dataset link-rot / archival rate.

## What the data can plausibly support

Set expectations deliberately, because expectations of data are usually high while data quality is usually low. This data supports **description and comparison far more readily than prediction**: it can show *which* sources are cited, by *whom*, *how often*, and *how that changes over time*, and can compare outlets, themes, and provenance tiers. It cannot forecast which datasets will be cited next, cannot establish that a citation caused an outcome, and cannot, from citation counts alone, judge the quality of a reporter's work. Effort and rate estimates in the methodology are planning figures, not measurements — the pilot exists to replace them with real ones.

## Collaborative interpretation

Joint, contextualized interpretation is a standing practice, not a courtesy: CEJ holds the journalism context that prevents the data team from misreading a pattern (e.g. a drop in citations that reflects a newsroom layoff, not a change in data use). Findings are reviewed with a CEJ subject-matter expert **before** they are published or acted on; a result produced without that expert in the room is provisional. Cadence and the named CEJ contact are set in `collaboration-protocol.md`.

## What survives the pilot

The default trajectory of these projects is quiet erosion when the grant, semester, or pilot ends, so the maintenance commitment is explicit:

- **Custodians after the pilot:** **CUPIDS Lab** (Brian Keegan, PI) is the standing custodian; the catalog and pipelines are designed to be re-runnable by a future maintainer who was not here for the build.
- **Where it lives / migration plan:** source of record is the GitHub repo (`CUPIDS-Lab/co-environmental-data`); liberated datasets are archived to **Harvard Dataverse** for citable DOIs; bulk artifacts (raw HTML, snapshots) live in **Cloudflare R2**. If the host changes, the git history + the Dataverse deposits are the portable core; everything else regenerates from them.
- **Maintenance commitment:** liberation pipelines run on a **monthly CI refresh** (full rebuild, self-healing); the corpus (when built) re-crawls active outlets on a quarterly cadence; **inter-coder reliability checks re-run each semester** as new student coders join (`context/methodology.md` §7, Phase 4). Retention duties are cross-referenced to `GOVERNANCE.md`.
