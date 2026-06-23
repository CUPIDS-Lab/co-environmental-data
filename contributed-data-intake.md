# Contributed / external data intake — Colorado Environmental Data Hub

**Applicability:** the Hub does not take crowdsourced submissions from the public, so the classic "a stranger uploads PII about themselves" intake does not apply. What *does* apply — and what the `ROADMAP.md` flags as a **blocking** L3 concern — is **data acquired from outside the team under binding constraints**: news article corpora pulled from the open web and, critically, from **CU Libraries' licensed databases** (Nexis Uni, NewsBank Access World News, ProQuest, Factiva). Those licenses forbid bulk/automated download and the records carry copyright; that is the intake this protocol governs. None of it is in the repo today — this is the contract for when the corpus build begins.

## Intake methods

Keep the set of channels deliberately small, because every channel is a surface you must secure, deduplicate, and document. The two channels:

- **Open-web retrieval (automated, allowed):** Media Cloud API, GDELT DOC API, outlet sitemaps, and the Wayback CDX API. Automated retrieval here **respects `robots.txt` and each outlet's terms of service**; it captures metadata + short excerpts + archived links, not republished full text.
- **Licensed-database export (manual only, never automated):** an operator with a CU entitlement searches Nexis Uni / NewsBank / ProQuest / Factiva **within license terms**, exports results by hand, and drops the files into a **quarantine directory** (`data/original/library/` in the corpus pipeline, per `context/architecture.md` nb-02) — *not* directly into any tracked `data/raw/`. Automated scraping of these databases is prohibited by their ToS and must never be added to the pipeline.

Nothing is treated as source data until it has cleared dedup and verification below.

## Deduplication

News data arrives repetitive: the same wire/AP story runs in a dozen outlets, syndication republishes verbatim, and library exports overlap the open-web pull. Decide up front what counts as a duplicate — here, near-identical body text or a shared canonical URL across outlets — and **dedupe before coding**, so one syndicated story is not counted as N independent citations. Do it as a documented, re-runnable pipeline step (a composite key + similarity threshold), not a manual cleanup, so the rule is legible and the same input always produces the same result. Library-database records that arrive with hyperlinks stripped (flagged `links_unavailable=true`) need URL-independent dedup keys.

## Role-based access

Licensed-database exports and raw article HTML sit in the **restricted** tier from `GOVERNANCE.md` — the license forbids redistribution, so only project members with the appropriate CU entitlement may handle the raw exports. The **derived** outputs that leave that tier are citation *records* (which source was cited, by whom, when) plus short excerpts and archived links — never the republished article text. State which role reviews incoming exports (the data engineer), who may see raw full text (the minimal set in the restricted tier), and the point at which the redacted/derived data moves to public. Least privilege is the default: most of the team works with the citation records, not the raw articles.

## Handling at import (the redaction analogue)

These records are about **journalists acting professionally**, not private individuals, so this is not classic PII redaction — but the coupling is the same: an affordance (storing article text + bylines) ships with a duty. At import: store **metadata + short excerpts + archived links, never republished full article text** (the fair-use/TDM posture, `context/methodology.md` §6.1); keep any full text in the restricted tier for non-consumptive analysis only; and stamp each journalist with a `coverage_tier` (dedicated / frequent / occasional) so a one-off environmental story never mislabels someone as an "environmental journalist." Make these steps part of the intake pipeline so they happen automatically and consistently.

## Verify before you cite

A retrieved article — and especially an automated label on it — is a claim, not a fact. Two hard rules:

- **Archive every cited URL at coding time:** submit it to the Wayback Machine "Save Page Now," record the nearest CDX snapshot, and store `archive_url` + `archive_timestamp`, so every citation is independently re-verifiable even after link rot (`context/methodology.md` §4.4).
- **Validate every automated label:** require a verbatim quote span for every LLM-asserted citation and programmatically reject any quote not found in the source text; only promote LLM labels unreviewed above the pre-registered precision threshold (≥ 0.90); hold human double-coding to Krippendorff's α ≥ 0.80. Never publish a single uncorroborated automated label.

## Minimal form design

Not applicable in the public-submission sense — there is **no public contribution form**, by design. The "form" analogue is the licensed-database export query and the open-web crawl scope: capture only the fields the research questions need (byline, outlet, date, URL, the cited source, the citation type), prefer the fixed `citation_type` / `coverage_tier` enums over free text, and document the query/scope so the sample is reproducible. If a public-facing submission path is ever added (e.g. journalists flagging their own data citations), return to this section and design it minimally with an up-front plain-language privacy notice.

## Protecting the people in the data

Journalists are exposed by being measured, and protecting them is a duty of the project, not a favor. Concretely: record professional information only (bylines, outlets, the public fact of a citation), never characterizations of a reporter's quality; offer a **correction / right-to-respond** pathway (a contact email and a documented process, `GOVERNANCE.md`); and where a record could expose a vulnerable source *cited within* an article (not the journalist), weigh that risk before publication and resolve it in favor of the person at risk. The affordance to measure is coupled to the duty to represent fairly and to be correctable.
