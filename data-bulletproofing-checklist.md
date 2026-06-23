# Data bulletproofing checklist — Colorado Environmental Data Hub

> **Applied per dataset in the dated QA audits** in [`audits/`](audits/): [reservoir (2026-06-22)](audits/2026-06-22-qa-audit.md) and [streamflow / snowpack / climate-stations (2026-06-23)](audits/2026-06-23-pipelines-qa.md). This file is the standing checklist; each audit is its application to specific data.

Run this before any number leaves the building. Bulletproofing is the pre-publication QA that makes a dataset defensible: you reconcile the data against the source's own published totals, recompute the key figures a second way, and have someone else replicate the result. Surprising findings get double-checked *before* they get shipped, not after a correction. Keep a data notebook recording every procedure you run here (this complements `decision-log.md` and the pipeline).

**On this project** the canonical example is the reservoir pipeline's **reconciliation spot-check** against each agency's current-storage page — that *is* this checklist applied. Use it as the model for every liberated dataset and for any corpus finding.

## Integrity

- [ ] Verified record counts against expected totals (e.g. the 118 major reservoirs + 20 RISE sites; the ~56 catalog sources), and watched for silent software row limits that drop data without warning.
- [ ] Ran `GROUP BY` on key fields to catch inconsistent spelling, stray whitespace, and duplicate records hiding behind near-identical values — for the corpus, this is the **syndication/wire-story dedupe** (one AP story in twelve outlets is not twelve citations).
- [ ] Validated that numeric ranges and dates are plausible — storage volumes within capacity, dates within the period the data should cover, no impossible values.
- [ ] Distinguished genuinely missing values from zeros and from sentinel codes so "no data" is never silently averaged in as a number (a real risk in long reservoir histories with gaps).

## Recomputation

- [ ] Recomputed each key figure with an alternate query or method and confirmed the two agree.
- [ ] Pulled a random sample of records and checked each one against the raw source by hand (against the agency page for water data; against the archived article for a citation).
- [ ] Gut-checked surprising or convenient results — a number that is exactly what you hoped for gets more scrutiny, not less — and traced any anomaly back to its cause before reporting it.

## Independent review

- [ ] Had a colleague independently replicate the key results from the raw data, without copying your queries (for corpus findings, this pairs with the double-coding / Krippendorff's α ≥ 0.80 reliability check).
- [ ] Kept a data notebook documenting every procedure — sources, transformations, queries, and decisions — so the work can be reproduced and defended.

This project will handle **conditionally sensitive-human** data once the corpus is built: do the verification inside the controlled tier, share only desensitized samples (citation records, not full text) for review, and confirm the release respects the access tiers and escalation rules in `GOVERNANCE.md` before anything is published. Complete the `responsible-data-checklist.md` as well.
