# Data quality checklist — Colorado Environmental Data Hub

Scan a new or updated dataset for the common "bad data" problems before you build on it, using this adaptation of the Quartz bad-data taxonomy. The checks are grouped by who is best placed to fix each problem — your source, you, a subject-matter expert, or a programmer — because knowing whose problem it is determines what to do next. Record what you find and how you handled it in the relevant `DATA-DICTIONARY.md` known-issues section so downstream users are not surprised. This is about whether the data can be trusted at all; `data-bulletproofing-checklist.md` is the pre-publication reconciliation that follows.

## Issues your SOURCE should fix

- [ ] Values are missing where you expected data, and the gaps are unexplained (long reservoir histories have real gaps — distinguish them from errors).
- [ ] Zeros are standing in for missing values (or vice versa), so absence is silently counted as a real measurement.
- [ ] Suspicious sentinel values appear (e.g. `65535`, `-1`, `9999`, `1900-01-01`) that actually mean "unknown."
- [ ] Spelling or capitalization is inconsistent across records, fragmenting what should be one category (reservoir/site names across DWR vs. RISE; outlet names across sources).
- [ ] Date and number formats are inconsistent across rows.
- [ ] Units or essential metadata are missing — note the reservoir pipeline's documented **vertical-datum** and **capacity-baseline** caveats, where a column of numbers means different things across agencies.
- [ ] The data looks truncated — cut off at exactly a tool's export limit.

## Issues YOU should fix

- [ ] Text is garbled by an encoding or line-ending mismatch (mojibake, stray characters, broken rows).
- [ ] The data only exists inside PDFs or scanned images and has to be extracted before use.
- [ ] The data is at the wrong aggregation level for the question — too coarse, or aggregated when you need the daily per-site units.
- [ ] Human data entry is inconsistent (free-text where codes were expected).
- [ ] Figures are not adjusted for confounders, or a seasonal series (snowpack, reservoir storage) is compared without accounting for seasonality.
- [ ] **Hyperlinks stripped on export:** library-database records arrive without URLs, breaking URL-based citation detection — flag them `links_unavailable=true` rather than dropping them.
- [ ] The sample is non-random or otherwise biased in a way that does not support the claim (the journalist sampling frame is hand-curated — state its coverage limits).

## Issues an EXPERT should weigh in on

- [ ] The author or collecting body is of uncertain trustworthiness or has an interest in the result.
- [ ] The collection methodology is opaque, so you cannot tell what the numbers actually measure.
- [ ] **Unverified provenance claims:** treat anything a search surfaced as unconfirmed until checked against an official source — e.g. the spurious "NREL renamed to National Laboratory of the Rockies / `nlr.gov`" claim the compilation surfaced is **almost certainly false**; keep `nrel.gov` canonical (see `AGENTS.md`, `context/source-inventory.md`).
- [ ] Figures show false precision — more decimal places than the method could support.
- [ ] There are inexplicable outliers that no one can account for.
- [ ] An index or composite masks the underlying variation that matters for interpretation.
- [ ] **`verification_status` not cleared:** a catalog source still flagged `needs_followup` has not been confirmed live — do not silently rely on it.

## Issues a PROGRAMMER should help with

- [ ] The data needs to be re-aggregated or reshaped programmatically (rolled up from records, pivoted, or floored to a temporal grain — multiple observations per period and upstream revisions are a first-class modeling case here).
- [ ] OCR or text/API extraction needs tuning to recover the data reliably (quirky REST/JSON:API/ArcGIS endpoints dominate Colorado civic data — probe the API before extracting).

This project will handle **conditionally sensitive-human** data once the corpus is built: run these checks inside the controlled tier and treat any field that could re-identify a source quoted within an article as a quality *and* a privacy concern — pair it with the access tiers in `GOVERNANCE.md` and the `responsible-data-checklist.md`.
