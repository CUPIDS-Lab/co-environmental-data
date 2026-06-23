---
name: documentation
description: >-
  Read before writing or updating documentation in the Colorado Environmental Data Hub. Covers keeping the data
  dictionary, schema, and derived-variable definitions current and co-located with the data, writing for a reader
  who has none of the project's context, and updating docs in the same change as the data or code they describe.
  Trigger on "document," "data dictionary," "schema," "codebook," "what does this field mean," or "update the docs."
---

# Documentation

Documentation is half the work: a dataset without it is a private spreadsheet. Write it for reuse, keep it next to what it describes, and never let it drift behind the data. The standard this project holds itself to: **documentation is only done when a novice can act on it** — a future maintainer who was not here for the build.

Keep the schema and definitions current and co-located. The root `DATA-DICTIONARY.md` documents the source catalog; each pipeline keeps its own `docs/data-dictionary.md` (and `variables.csv`) for its tidy output — grain, fields, types, units, allowed values, missingness, derived-variable formulas, and known issues. Keep these living next to the data rather than in a separate, forgotten place. Publish derived/computed variables centrally with their definitions so analysts reuse one agreed definition instead of each re-deriving their own and quietly disagreeing. For the future corpus, the **codebook** (`context/methodology.md` §4.2) is this same discipline applied to human coding: written definitions for every `citation_type` and `coverage_tier`, with inclusion/exclusion criteria and ≥2 worked examples each — a living document, versioned in the repo.

Write for someone with none of the project's context. Explain not just what each field is but why it exists and how it should and should not be used, and record the data problems you found and how you handled them — missing versus zero, suspicious sentinels, inconsistent encodings, totals that do not reconcile, the vertical-datum and capacity caveats the reservoir pipeline carries — so the next reader is not surprised by them. The same standard applies to operator instructions: a stub like "fill `expected` with current storage off each agency's page" is not done until it says *what to do, where, how, and what success versus failure looks like* (a lesson from the project's own retro).

Update docs in the same change as the data or code. Documentation that has fallen behind the code is a bug, not a chore for later. When a field, a transformation, or a definition changes, change the relevant `DATA-DICTIONARY.md` in the same commit, add a dated entry to `decision-log.md` for any non-obvious choice, and note user-visible changes in `CHANGELOG.md`. Coupling the doc edit to the code edit is the only reliable way to keep them honest.
