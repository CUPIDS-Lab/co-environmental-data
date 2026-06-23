# Responsible data checklist — Colorado Environmental Data Hub

Work through the rights and risks of the people this data is about, at each stage of its life rather than once at the start. The checklist is organized by lifecycle stage — design, getting, understanding, sharing, closure — because a harm introduced at intake is cheapest to prevent there and most expensive to undo at release. Two things are **hard gates** that cannot be waived: **privacy and data-protection law** and the **CARE Principles for Indigenous Data Governance**. Everything else is advisory.

**Where this bites.** The data the repo ships *today* — the source catalog and the liberated water datasets — is public agency metadata, so most boxes below are trivially satisfied or N/A. This checklist becomes **load-bearing** at the **news-corpus** build, when article text + journalist records enter; the corpus is gated on the **blocking** items in `ROADMAP.md`, and this is the checklist those items point to. Center the people whose data this is — the journalists being measured — not an abstract public, and record whose risks are being carried.

## Design

- [ ] Stated the project's purpose and the specific questions narrowly enough to test collection against them (`CHARTER.md`; `context/methodology.md` §1).
- [ ] Named design partners (CUPIDS team + CEJ) separately from beneficiaries (journalists, researchers, the public), and recorded whose risks are centered — the journalists being measured (`CHARTER.md`).
- [ ] Identified the applicable regimes up front — **copyright/fair-use (TDM)**, licensed-database ToS, journalist privacy; IRB **not** engaged (published journalism, not human-subjects collection); CARE N/A today — and confirmed the project can satisfy them (`data-management-plan.md` §Compliance).
- [ ] Made the transparency-versus-privacy tradeoff legible rather than leaving it to defaults (`GOVERNANCE.md` §Transparency vs. privacy).

## Getting

- [ ] **Consent / legal basis:** for published journalism the basis is fair-use/non-consumptive research, **not** individual consent; confirmed that basis holds and that it breaks if the public site republishes full text. (Catalog/water data: public open data, no consent issue.)
- [ ] **Data minimization & purpose limitation:** collect and keep only what the questions need — **metadata + short excerpts + archived links, never republished full article text**; professional journalist information only; nothing gathered "just in case."
- [ ] Confirmed the authority and license to use, transform, and share each source before ingesting — including the **licensed-database manual-export-only** constraint (no automated download; no redistribution).
- [ ] Recorded provenance and chain of custody on ingestion (per-row `run_id`; archived `archive_url`/`archive_timestamp` for every cited URL), and kept raw sensitive data and credentials out of the repository.

## Understanding

- [ ] **Harms assessment by stage:** enumerated foreseeable harms — mislabeling someone as an "environmental journalist" on one story, re-identifying a vulnerable *source quoted within* an article, misreading a citation pattern as a quality judgment — rated likelihood/severity, and recorded mitigations (`coverage_tier`; professional-info-only; collaborative interpretation with CEJ).
- [ ] Checked re-identification risk specifically: the journalists are public, but assessed whether any *source* named inside an archived article could be singled out or endangered by aggregation.
- [ ] Brought in the subject-matter knowledge (CEJ) needed to interpret coding categories so patterns are not misread in ways that harm the people behind them.
- [ ] Documented known limitations and biases (`DATA-DICTIONARY.md`, `data-quality-checklist.md`): library records with `links_unavailable=true`, syndication double-counting, LLM-label precision floor.

## Sharing

- [ ] **Security & least-privilege access:** licensed content + raw HTML encrypted/restricted in R2, access scoped to the narrowest role, access and changes audited (`GOVERNANCE.md`), and a breach-response path defined.
- [ ] Applied the access tier from `GOVERNANCE.md` — public (catalog, datasets, metadata+excerpts+links), restricted (licensed content, full text), sensitive (future journalist records).
- [ ] Desensitized/aggregated before release, and named the out-of-scope uses and foreseeable misuses explicitly (`data-card.md`).
- [ ] Routed anything touching the restricted/sensitive tiers through the escalation rules in `GOVERNANCE.md` before publishing; confirmed automated labels clear the validated precision floor before being promoted as authoritative.

## Closure

- [ ] **Retention & disposal:** retention schedule set per data class and tied to purpose; licensed exports deleted when the entitlement ends; sensitive records securely disposed of by the named custodian (`GOVERNANCE.md`, `data-management-plan.md`).
- [ ] Communicated wind-down to partners (CEJ, CU Libraries) as the relationship requires; honored the journalist correction/right-to-respond pathway throughout, not only at closure.
- [ ] Stated what survives the pilot — CUPIDS Lab as custodian, the Dataverse deposits and git history as the portable core — so the project ends deliberately rather than eroding (`CHARTER.md`).
