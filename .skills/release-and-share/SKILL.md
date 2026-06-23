---
name: release-and-share
description: >-
  Read before packaging, publishing, or sharing any output from the Colorado Environmental Data Hub. Covers
  exporting processed data in open, version-stamped formats with a defined export, applying the access tier from
  GOVERNANCE.md, routing anything touching sensitive traces through the escalation rules, and completing the
  bulletproofing and data-quality checks first. Trigger on "publish," "release," "share data," "export,"
  "Dataverse," "deposit," or "send this out."
---

# Release and share

Package and publish outputs so others can find, trust, and reuse them — and so nothing sensitive or unverified leaves by accident. Get the checks done before anything goes out the door.

Verify before you publish. Complete the `data-bulletproofing-checklist.md` so the numbers reconcile against the source's own totals and surprising results have been double-checked, and run the `data-quality-checklist.md` where the data warrants it. The reservoir pipeline's reconciliation spot-check against each agency's current-storage page is exactly this discipline; shipping unverified figures is how a project loses its credibility in one release.

Package in open, version-stamped formats with a defined export. Release processed outputs in plain-text, version-controllable formats (CSV/Parquet, Markdown, text-based pipeline definitions), stamp each release with a version and date, and provide a defined, scriptable export rather than a hand-assembled snapshot. The shared artifact is the **re-runnable pipeline**, not a one-off cleaned file: anything a hosted tool (Datasette, R2, Quarto) produces must be exportable, and no vendor-locked artifact should be a required dependency. Ship the relevant `DATA-DICTIONARY.md` (and the Data Card) alongside the data so a reader can interpret it.

Apply the access tier and respect the escalation rules. Before publishing, apply the access tier from `GOVERNANCE.md` — the catalog and liberated datasets are **public**; licensed-database content and raw article HTML are **restricted** and never redistributed — and confirm the openness and license you are releasing under (open; MIT).

Deposit for a citable archive. To make a liberated dataset findable and citable, deposit its processed data, code, and documentation to **Harvard Dataverse** for a DOI — each pipeline ships its own kit (e.g. `pipelines/reservoir-storage/dataverse/DEPOSIT.md`), wired into the monthly CI refresh as **draft-only**. Try a `DRY_RUN=1` deposit against `demo.dataverse.org` first; CI never mints a DOI unattended — a deposit stops at a reviewable draft and only publishes on **explicit human confirmation**, after the bulletproofing checks pass, because a DOI is permanent. Recurring refreshes target the existing dataset as a **new version** (one DOI), not a new DOI.

This project will handle **conditionally sensitive-human** data once the corpus ingests article text + journalist records. Nothing touching sensitive traces is published on your own authority: route it through the access tiers and the remedy/escalation rules in `GOVERNANCE.md` first, keep to metadata + excerpts + archived links (never republished full text), desensitize before anything leaves the controlled tier, and complete the `responsible-data-checklist.md`. Releasing an affordance without its governance is exactly the theater this project refuses to ship.
