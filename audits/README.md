# audits/

Point-in-time, dated project records — what was checked or decided at a given moment, kept as a durable trail. Organized **by document type**:

| Subdirectory | `doc_type` | What it holds |
| --- | --- | --- |
| [`qa/`](qa/) | `audit` | QA audits of the data and repo against the L4 checklists (bulletproofing · data-quality · accessibility). |
| [`after-action/`](after-action/) | `after-action-report` | After-action reviews (AARs) of a build phase — what happened, what to harden. |
| [`revision-plans/`](revision-plans/) | `revision-plan` | Forward-looking plans derived from an audit/AAR (for the repo or a skill). |

## Conventions

- **Filename:** `YYYY-MM-DD-<kebab-slug>.md` — the date the record was produced.
- **Front-matter:** every file opens with the YAML block below; `doc_type` must match its subdirectory, and `related:` paths are repo-root-relative.

```yaml
---
# Versioning
version: "1.0"
status: final            # final | draft
created: YYYY-MM-DD
updated: YYYY-MM-DD
supersedes: <path>       # optional
# Provenance
title: "..."
doc_type: audit | after-action-report | revision-plan
project: "Colorado Environmental Data Hub"   # and/or subject_skill: <skill> for skill-focused docs
repository: "CUPIDS-Lab/co-environmental-data"
audited_ref: "..."       # audits: the ref/state audited (optional)
author: "..."
generated_by: "..."
basis: "..."
related:
  - <path>
---
```

> History: `audits/` and a separate top-level `retro/` were merged here on 2026-06-23, and the front-matter convention was applied to every file (the 2026-06-22 audit had none). See `docs/reference/decision-log.md`.
