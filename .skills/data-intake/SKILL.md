---
name: data-intake
description: >-
  Read before acquiring, assessing, or first understanding any dataset in the Colorado Environmental Data Hub.
  Covers recording provenance and license on ingestion, verifying that the source is reachable and that you have
  the authority to use it, never editing raw data in place, and securing the subject-matter knowledge needed to
  read the data correctly. Trigger on "ingest," "import data," "new source," "where did this come from," "liberate,"
  or "can we use this."
---

# Data intake

Acquire, assess, and understand a dataset before it becomes a dependency. The work here is what makes everything downstream trustworthy, so do not rush it to get to analysis. On this project, an intake usually means either adding a source to the catalog or standing up a new `pipelines/<name>/` liberation.

Record provenance and license at the moment of ingestion, not later from memory. For every source, capture where it came from, how and when you obtained it, the chain of custody, and the license or terms that govern its reuse, and write those into the relevant `DATA-DICTIONARY.md` (per-field provenance) and `decision-log.md` (why this source). Every catalog source also carries a `verification_status`; do not silently rely on a `needs_followup` source. A dataset whose origin you cannot reconstruct is a liability, not an asset.

Verify availability and authority before you build on the data. Confirm the source is reachable and re-releasable so the pipeline can regenerate results later (the monthly CI refresh depends on this), and confirm you actually have the right to use, transform, and share it. This is where this project's hardest constraint lives: **CU Libraries' licensed databases (Nexis Uni, NewsBank, ProQuest, Factiva) forbid bulk/automated download** — use them by manual search/export within license terms only, never the scraper, and keep their content in the restricted tier (`GOVERNANCE.md`, `contributed-data-intake.md`). For open-web sources, respect `robots.txt` and outlet terms of service. If the right to use is unclear, resolve it before ingesting.

Never edit raw data in place. Treat everything under `data/raw/` as immutable — including the curated source catalog `colorado_environmental_data_sources.json`. Read it, write derived data to `data/interim/` or `data/processed/` (or the pipeline's own outputs), and make sure any derived output can be regenerated from the original. A new catalog vintage is a **new file**, not an in-place edit. Editing the source destroys your ability to audit against it and to reproduce your own work.

Learn or recruit the knowledge needed to interpret the data. Numbers without context get misread, so identify the subject-matter expertise a dataset requires and either learn it or bring in the person who holds it before drawing conclusions — for environmental-reporting judgment that is the CEJ subject-matter expert (`ROLES.md`); for a water dataset's quirks (vertical datum, capacity baseline) it is the agency documentation the pipeline's concept catalog records. Stay in contact with the data owners, and record what you learn so the next reader does not have to rediscover it.

This project will handle **conditionally sensitive-human** data once the corpus ingests article text + journalist records. Before ingesting anything that touches people, confirm the legal basis (fair-use/TDM for non-consumptive research) covers this use, take only what the stated purpose needs (metadata + excerpts + archived links, never republished full text), route the data into the controlled tier defined in `GOVERNANCE.md`, and complete the `responsible-data-checklist.md`. Keep credentials and raw sensitive data out of the repository entirely.
