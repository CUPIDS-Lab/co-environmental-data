# Roles — Colorado Environmental Data Hub

This file names who does what on the Colorado Environmental Data Hub so that responsibility is legible and nothing important is owned by nobody. A data collaboration runs on five core roles embedded in a wider community and supported by auxiliary specialists; a small project may have one person wearing several hats, which is fine as long as the hats are named. Keep this current as people join and leave, and read it alongside `.github/CODEOWNERS`, which maps these roles to the repository paths they review.

> **Reality today (2026):** the Hub is effectively a single-maintainer project — **Brian Keegan (@brianckeegan)** holds most core roles — about to onboard a **CUPIDS Lab undergraduate research team** and formalize the **Center for Environmental Journalism (CEJ)** subject-matter partnership. That transition is *why* the project climbed to L3; the GAP-CHECK at the bottom names the hats that are doubled-up until the team lands.

## The five core roles

The core roles are **data engineer, software developer, subject-matter expert, mediator, and project manager**. Each is a responsibility, not necessarily a separate person — but each must be claimed by someone for the work to hold together.

## The thinker/doer split

These teams are small, interdisciplinary, and low-turnover, and the work divides into framing and building. Subject-matter experts are the **thinkers**: they frame the questions, define the terms, and interpret the results, because they hold the context that prevents misreadings. On this project that context is twofold — **environmental-journalism** judgment (what counts as a citation, who counts as an environmental journalist) lives with CEJ, and **data-science methodology** (sampling, reliability, detector validation) lives with the PI. The data engineer and software developer are the **doers**: they build the liberation pipelines and the corpus tooling. Design for tight, high-bandwidth, often synchronous feedback between the two rather than for crowd scale — the value comes from the loop being short, not from the team being large.

## The mediator function

Someone has to translate between the technical view and the subject-matter view, and that person is the **mediator**. This is where collaborations succeed or stall: an unmediated team produces technically correct work that answers the wrong question, or domain-correct intentions that never become working code. On the Hub the mediator sits between the CEJ journalists who define the research questions and the data team that builds the pipelines; the PI currently holds this hat. Name the mediator explicitly below even when it is a hat someone else also wears, because a function nobody owns is a function that quietly fails.

## Roles table

| Role | Who | Responsibilities |
| --- | --- | --- |
| Data engineer | Brian Keegan (@brianckeegan); **undergraduate team on onboarding** | Acquires and models data; owns the `pipelines/<name>/` liberation pipelines, schema, identifiers, and quality checks; keeps derived data reproducible from raw (the immutable source catalog). |
| Software developer | Brian Keegan (@brianckeegan); **undergraduate team on onboarding** | Builds and maintains the tested `src/<pkg>/` packages (`reservoir`, future `cejcorpus`), the notebooks-over-package pattern, CI, and the Dataverse deposit tooling. |
| Subject-matter expert | **Center for Environmental Journalism** collaborators (journalism domain); Brian Keegan (data-science methodology) | Frame the questions; define "environmental journalist," `coverage_tier`, and the six `citation_type` values; own the codebook and `DATA-DICTIONARY.md` meaning; interpret findings. |
| Mediator | Brian Keegan (@brianckeegan) | Translates between CEJ's journalism judgment and the data team's implementation; keeps the feedback loop tight; surfaces mismatches (e.g. a coding rule that the pipeline cannot operationalize) early. |
| Project manager | Brian Keegan (@brianckeegan), PI | Coordinates the work and cadence; owns `CHARTER.md` and `GOVERNANCE.md`; runs the `ROADMAP.md` ↔ GitHub sync; tracks decisions and what survives the pilot. |
| Community — publishers | CUPIDS Lab · CEJ | Release and steward the catalog, the liberated datasets, and (later) the corpus for the beneficiaries. |
| Community — consumers | Environmental journalists; researchers studying data-driven reporting; the Colorado public | Use the data and outputs; their needs shape scope (the catalog exists to be cited; the corpus exists to be queried). |
| Community — connectors | CEJ (Ted Scripps Fellows, Water Desk); CU Libraries | Link the project to journalists, outlets, and the licensed news databases. |
| Community — communicators | CUPIDS Lab · CEJ | Make the project and its findings findable and understandable (README, wiki, planned Datasette/Quarto site). |
| Auxiliary — infrastructure | CU Research Computing (Alpine); Cloudflare R2; GitHub Actions | Hosting, compute, object storage for raw HTML + archived snapshots, backups, and access controls. |
| Auxiliary — statistics | Brian Keegan (methodology owner) | Sampling frame, inter-coder reliability (Krippendorff's α), detector precision/recall, guards against overfitting. |
| Auxiliary — legal | CU Libraries; CU Office of University Counsel (to be consulted) | Licensed-database terms of service, copyright/fair-use (TDM) posture, journalist-privacy review before corpus ingest. |

## GAP-CHECK — unfilled roles

If any core role above is unfilled, name it here rather than papering over it with an empty cell, and make filling it the first priority before the project takes on work that role guards. An unowned core role — especially the mediator — is the most likely point of failure, so treat closing these gaps as blocking, not aspirational.

- **Data engineer / software developer — doubled up on the PI.** Open because the undergraduate research team is not yet onboarded; interim coverage is Brian Keegan. Plan: distribute the `pipelines/<name>/` build and catalog-hardening work (the two `good-first-issue` tasks) to students as they clear onboarding. **This is the gap L3 was scaffolded to close.**
- **Subject-matter expert (journalism) — partner-side, not yet formalized.** Open because the CEJ partnership is collaborative but has no named, committed point of contact for codebook adjudication. Interim coverage: Brian Keegan applies the methodology's documented rules. Plan: name a CEJ contact in `collaboration-protocol.md` before any citation coding begins. **Blocking before coding starts.**
- **Mediator — held by the project manager.** Open because the same person frames data-science decisions and brokers the CEJ relationship, so a mismatch the PI doesn't personally see has no second catcher. Interim coverage: Brian Keegan. Plan: revisit once the team has ≥2 people who can hold the domain↔technical translation.
- **Legal — advisory, not yet engaged.** Open because no counsel has reviewed the fair-use/TDM posture or the licensed-database ToS. Interim coverage: the documented posture in `context/methodology.md` §6 and `data-management-plan.md`. Plan: secure a CU Libraries / University Counsel review. **Blocking before ingesting article text or library-database exports.**
