# METHODOLOGY MEMO: Building a Research Database of Colorado Environmental Journalists and Their Data-Citing Reporting (2014–Present)

**To:** CU Environmental Data Hub / CUPIDS Clinic undergraduate research team; Center for Environmental Journalism collaborators
**Re:** Retrieval and verification methodology for a journalist → article → data-source-citation corpus
**Date:** June 17, 2026

## TL;DR
- Build the corpus in three relational layers (journalists → articles → data-source citations) using a hybrid pipeline: enumerate a sampling frame of ~30–40 Colorado outlets and named journalists; retrieve bylined 2014–present articles via Media Cloud (free, academic) + GDELT DOC API (free) + outlet sitemaps/RSS + CU Libraries' licensed databases (Nexis Uni, NewsBank Access World News, ProQuest, Factiva) for paywalled/legacy content; then detect data-source citations with a two-stage detector (deterministic URL/domain matching against a dictionary seeded from the 56-source catalog, then LLM-assisted prose classification).
- Treat citation detection as a measured information-extraction task: every automated label must be validated against a hand-coded gold standard with reported precision/recall, double-coding with Krippendorff's α ≥ 0.80, and archiving of every cited URL at coding time via the Wayback Machine CDX/save APIs to combat link rot.
- Do NOT attempt to scale first. Run a bounded pilot (Colorado Sun water coverage, 2014–present) end-to-end to validate retrieval recall and citation-detection precision before expanding to all outlets and all six themes. The project's existing Datasette + Cloudflare R2 + Quarto + Prefect stack and CU Research Computing (Alpine) open-weight LLM inference are sufficient; no paid tools are strictly required.

## Key Findings (Design Decisions)
1. **Coverage requires triangulation, not one source.** No single retrieval method covers 2014–present Colorado environmental reporting. Open web crawlers (Media Cloud, GDELT) miss paywalled and defunct content; library databases (NewsBank, ProQuest, Nexis Uni) cover legacy dailies but strip hyperlinks—the very signal needed for citation detection. The Wayback Machine recovers dead links and preserves original HTML. Use all four classes.
2. **Citation detection is hardest where it matters most.** Hyperlinks to known data portals are the highest-precision signal and should anchor the detector. Prose mentions ("according to USGS streamgage data") require LLM-assisted extraction, which has high recall but unreliable precision and a documented tendency to hallucinate citations—mandating gold-standard validation.
3. **Undergraduates can execute this, but only with a codebook, double-coding, and a phased pilot.** The labor-intensive risk points are coder drift, false positives from boilerplate/footer links, and journalist name disambiguation.
4. **Fair use supports the research corpus, but storage choices matter.** Text-and-data-mining of in-copyright news for non-consumptive research is well-supported by case law; store metadata + short excerpts + archived links rather than republishing full text.

## DETAILS

---

### SECTION 1 — ENTITY DEFINITION AND INCLUSION CRITERIA

**1.1 Defining "Colorado environmental journalist" (the population).**
Operationalize inclusion as a scored rule, not a binary judgment, so undergraduate coders apply it consistently. A byline enters the journalist table if it meets **both** a *place* test and a *beat* test within the 2014–present window:

- **Place test (any one):** (a) employed/contracted by a Colorado-based outlet (HQ in CO); OR (b) produced ≥1 qualifying article whose primary subject is a Colorado environmental topic/geography; OR (c) is a CEJ Ted Scripps Fellow or Water Desk contributor reporting on Colorado/Western water.
- **Beat test (any one):** ≥3 qualifying environmental articles in any rolling 24-month period (the "regular" tier), OR ≥1 qualifying article (the "occasional" tier, flagged separately so analysts can filter).

Record a `coverage_tier` field (dedicated-beat / occasional / one-off) and an `affiliation_type` field (staff / freelancer / student / newsletter-Substack / fellow). This preserves the broad scope while letting downstream analysis subset to dedicated reporters.

**1.2 Edge cases — explicit coding rules.**
| Edge case | Rule |
|---|---|
| National reporter covering CO (e.g., NYT story on Colorado River) | Include the *article* if it passes the place+beat test; tag journalist `affiliation_type=national`, `co_resident=false`. |
| CO reporter covering national/global topics | Include journalist; include only articles with a Colorado nexus (geography, data, or named CO entity). Tag non-CO articles `co_nexus=false` and exclude from primary corpus. |
| Moved in/out of state | Keep one journalist record with an `affiliation_history` sub-table (outlet, start/end dates); attribute each article to the outlet/affiliation active at publication. |
| Occasional vs. regular | Captured by `coverage_tier` (see 1.1). |
| Wire/syndicated (AP, etc.) | Tag `byline_type=wire`; exclude from journalist-level analysis but retain at article level with `is_syndicated=true`. Deduplicate syndicated reprints by headline+date+first-200-chars hash. |
| Opinion vs. news | Code `genre` (news / investigation / column-opinion / explainer / newsletter / multimedia / data-viz). Keep opinion in corpus but filterable. |
| Data journalists vs. traditional | Not an inclusion criterion; captured by `genre=data-viz` and by citation density. |

**1.3 Defining the unit "article."**
An article is a single published, individually-addressable work (unique canonical URL or unique database record). Count as articles: news stories, investigations, explainers, opinion/columns, newsletter issues (each issue = one unit), multimedia/audio segments with a text landing page, and standalone data visualizations. Exclude: photo galleries with no reporting text, event listings, and aggregation/"morning roundup" link dumps (tag `is_roundup=true` if ambiguous). For series, code each installment separately but link via a `series_id`. For audio/podcast (e.g., KUNC, Aspen Public Radio), the unit is the episode/segment landing page; code the show-notes/transcript text for data citations.

**1.4 Defining "cites a data source" — a typology.**
This is the project's core measurement. Code a `citation_type` enum per (article × data_source) pair, ordered from strongest to weakest evidence:

1. **`direct_link_data`** — hyperlink resolves to a known data-source domain/portal (e.g., `waterdata.usgs.gov`, `echo.epa.gov`). Highest confidence.
2. **`embedded_viz`** — an embedded chart/map whose underlying data is attributed to a catalog source (iframe, datawrapper, Flourish, ArcGIS embed citing the source).
3. **`named_attribution`** — prose attributes data to the agency/dataset by name without a link ("EPA's Toxics Release Inventory shows…").
4. **`agency_mention_ambiguous`** — agency named but unclear whether *data* (vs. a spokesperson quote, a regulatory action) is the referent. Flag for human review; do not count as a data citation without adjudication.
5. **`foia_records`** — reporter cites their own records/FOIA request or a dataset they obtained, not a published portal. Tag `data_origin=primary_records`.
6. **`secondary_citation`** — article cites *another outlet* that cited the data ("as the Colorado Sun reported, state figures show…"). Tag `is_secondary=true`; do not credit the original data source unless independently present.

Record `data_origin` (published_portal / primary_records / unclear) and `attribution_strength` (1–6 above) so analysts can apply strict or loose definitions.

---

### SECTION 2 — SOURCE IDENTIFICATION / SAMPLING FRAME

**2.1 Outlet enumeration.** Build an `outlets` table seeded from the list below, then expand via SEJ/SPJ membership and Corey Hutchins' "Inside the News in Colorado" newsletter (an authoritative running census of the Colorado media ecosystem). Tier outlets so the pilot can start narrow.

| Tier | Outlets (non-exhaustive seed) |
|---|---|
| Legacy dailies | The Denver Post, The Gazette (Colorado Springs), Daily Camera (Boulder), Longmont Times-Call, Loveland Reporter-Herald, The Pueblo Chieftain, Grand Junction Daily Sentinel, Durango Herald, Steamboat Pilot |
| Nonprofit/digital | The Colorado Sun, Colorado Newsline, Boulder Reporting Lab, Aspen Journalism, Fresh Water News (Water Education Colorado), The Water Desk (CEJ), KUNC, Colorado Public Radio (CPR), Rocky Mountain PBS, The Lever |
| Regional/mountain | Aspen Times, Aspen Daily News, Vail Daily, Summit Daily, Sky-Hi News, Steamboat Pilot & Today, Montrose Daily Press, Sopris Sun, Cortez Journal |
| National w/ CO base | High Country News (Paonia), Inside Climate News (founder ties) |
| Student | CU Independent (CU Boulder), Rocky Mountain Collegian (CSU), other campus papers |
| Newsletters/Substack | Big Pivots (Allen Best, energy/climate), Coyote Gulch (water), Land Desk (Jonathan Thompson), individual reporter Substacks |
| Alt-weekly | Westword |

For each outlet store: `outlet_id`, name, HQ city, ownership, type, founding/closure dates, CMS platform if known, sitemap URL, RSS URL, author-archive URL pattern, paywall status, and a `defunct` flag with last-publication date.

**2.2 Identifying individual journalists.** Layered approach, cheapest first:
- **Outlet author-archive pages** (e.g., `coloradosun.com/author/<name>/`) — the primary, free byline census per outlet.
- **Mastheads/staff pages** (current and via Wayback snapshots for historical rosters).
- **Muck Rack** — strong dynamic journalist directory with coverage history, continuously editor-curated; **paid/closed, enterprise-tier pricing**. TrustRadius lists Muck Rack as starting at $5,000 per year, Prowly estimates "an average of about $15,000 annually," and SpendHound's de-identified data from 160 customers reports "average SMB pricing for Muck Rack is $12874 per year, while average enterprise pricing for Muck Rack is $78996 per year." Journalists get free profiles, but the searchable database is a PR-sales product. Use as a cross-check only if the project already has institutional access; do not budget the project around it.
- **CEJ Scripps Fellow rosters** (5/year, on colorado.edu/cej) and **Water Desk** contributor pages — directly name fellows and water reporters.
- **Professional bodies:** Society of Environmental Journalists (SEJ) member directory; SPJ Colorado Pro chapter.
- **LinkedIn** — last resort for affiliation history/disambiguation; never scrape at scale (ToS), use manual lookups for ambiguous cases only.

**2.3 Defunct outlets, paywalls, link rot.** For shut-down outlets (e.g., Rocky Mountain News ceased 2009, predates window but illustrative; more recent closures appear in Hutchins' newsletter), reconstruct bylines and articles from (a) CU Libraries' NewsBank Access World News and ProQuest, which carry archived full text of CO papers including the Denver Post (1986–present) and Daily Camera (1996–present); and (b) the Wayback Machine CDX API to enumerate captured article URLs. For paywalled current content, prefer library-licensed full text; where a link is dead, resolve it through the Wayback Machine.

---

### SECTION 3 — RETRIEVAL STRATEGIES (CORE TECHNICAL SECTION)

**3.1 Retrieval methods and tradeoffs.**

| Method | Access model | Strengths | Limitations |
|---|---|---|---|
| **Media Cloud** (search.mediacloud.org; Python API client) | Free, open-source, academic; free API key | "A searchable index of the over 60,000 news media sources in our database, the largest open-source repository of digital news worldwide," with an underlying DB holding "over 1.7 billion stories belonging to 1.1 million distinct media sources" (Roberts et al., AAAI ICWSM 2021); built for academic content analysis; gives URL, title, date, domain; spiders hyperlinks | Story metadata only (often no full text for paywalled); coverage of small CO outlets uneven; per-query result caps |
| **GDELT DOC 2.0 API** | Free | Global, near-real-time; domain & theme filters; Python clients (gdeltdoc) | Per the DOC 2.0 docs, the API returns up to 75 results by default and can be raised "up to 250 results" via MAXRECORDS; the API "officially only supports the most recent 3 months of articles" (gdeltdoc client docs), while the form-based query tools reach back "as far as January 2017 for all news and June 2009 for TV news" (Ken Blake, drkblake.com); metadata not full text; explicitly not licensed content |
| **Outlet sitemaps + RSS archives** | Free | Authoritative per-outlet URL lists; `trafilatura.sitemaps.sitemap_search()` enumerates all article URLs; best recall for a single outlet | RSS often only recent items; sitemap structures vary; some outlets block crawlers |
| **CU Libraries licensed DBs** — Nexis Uni, NewsBank Access World News, ProQuest, Factiva | Free to CU via IdentiKey | Deep full-text incl. paywalled/legacy CO dailies; clean text; legal access | Strips hyperlinks (kills URL-based citation detection); ToS forbids bulk/automated download — manual/export-limited; no embedded viz |
| **Wayback Machine CDX API** (`web.archive.org/cdx/search/cdx`) | Free | Enumerate every captured URL for a domain; recover dead links; retrieve original HTML (`…id_/` raw URLs) preserving hyperlinks | Coverage gaps for small/new sites; redirects; rate limits (be polite, ~throttle) |
| **Google Programmable Search / `site:` queries** | Free tier limited; paid above | Quick targeted discovery (`site:coloradosun.com "SNOTEL"`) | Not exhaustive; ranking bias; quota limits; ToS limits automation |
| **NewsAPI** | Paid (enterprise ~$449/mo) | Simple REST | Short historical window on cheap tiers; not worth it given free options |

**Recommended retrieval stack:** Media Cloud (broad discovery) + outlet sitemaps via trafilatura (per-outlet completeness) + Wayback CDX (defunct/paywalled/dead-link recovery) as the open-web spine; CU Libraries databases as the supplement for full text of legacy dailies. Reconcile/deduplicate across sources on canonical URL and a normalized (headline + date + author + text-hash) key.

**3.2 Article extraction.** Use **trafilatura** (Python; open-source) as the primary extractor for main text + metadata (author, date, title, tags) AND, critically, to extract hyperlinks from article HTML. Trafilatura scored F1 0.945 (precision 0.925, recall 0.966) — the top general-purpose open-source extractor — in the scrapinghub/article-extraction-benchmark results table. Fallback chain for hard pages: trafilatura → readability-lxml → newspaper3k/4k → Playwright headless browser for JS-rendered pages. Always retain the raw HTML (in R2) so hyperlink/citation extraction can be re-run as the detector improves.

**3.3 Detecting data-source citations — two-stage detector.**

**Stage A — Deterministic URL/domain matching (high precision).** Build a domain dictionary seeded from the 56-source catalog (each source's landing-page + documentation URLs). Extract every outbound `<a href>` from article HTML, canonicalize (strip scheme/www, lowercase host), and match host (and where needed, subpath) against the dictionary. The verified canonical hostnames to seed the dictionary:

| Source | Canonical host(s) to match |
|---|---|
| USGS NWIS / Water Data | `waterdata.usgs.gov`, `nwis.waterdata.usgs.gov`, `api.waterdata.usgs.gov` |
| USGS/EPA Water Quality Portal | `waterqualitydata.us` |
| NRCS SNOTEL | `wcc.nrcs.usda.gov`, `nwcc-apps.sc.egov.usda.gov`, `nrcs.usda.gov` |
| EPA ECHO | `echo.epa.gov` |
| EPA TRI | `enviro.epa.gov` (TRI Explorer/Envirofacts); `epa.gov/toxics-release-inventory-tri-program` |
| EPA AQS / AirData / AirNow | `aqs.epa.gov`, `epa.gov/outdoor-air-quality-data`, `airnow.gov`, `files.airnowtech.org` |
| NIFC fire | `data-nifc.opendata.arcgis.com`, `nifc.gov`, `ftp.wildfire.gov` |
| MTBS | `mtbs.gov`, `burnseverity.cr.usgs.gov` |
| NREL WIND Toolkit | `nrel.gov`, `developer.nrel.gov`, `data.openei.org` |
| BLM MLRS / geospatial | `mlrs.blm.gov`, `reports.blm.gov`, `blm.gov`, `gbp-blm-egis.hub.arcgis.com` |
| CO DWR / CDSS | `cdss.colorado.gov`, `dwr.colorado.gov`, `dwr.state.co.us`, `data.colorado.gov` |
| CO ECMC / COGCC (COGIS) | `ecmc.state.co.us`, `ecmc.colorado.gov` (and legacy `cogcc.state.co.us`) |
| CO DRMS mining | `drms.colorado.gov`, `data-drms.hub.arcgis.com`, `dnr.colorado.gov` |
| Colorado Parks & Wildlife | `cpw.state.co.us`, `geodata-cpw.hub.arcgis.com`, `geodata.colorado.gov` |
| Colorado EnviroScreen | `cdphe.colorado.gov/enviroscreen`, `teeo-cdphe.shinyapps.io`, `cohealthmaps.dphe.state.co.us` |
| DRCOG | `drcog.org`, `data.drcog.org` |
| RAQC | `raqc.org` |
| USGS EarthExplorer / National Map | `earthexplorer.usgs.gov`, `apps.nationalmap.gov`, `cr.usgs.gov` |

Design notes for the dictionary: (i) Many EPA tools share `www.epa.gov` and differ only by subpath, so match host **plus** subpath for epa.gov, usgs.gov, and county portals; distinct subdomains (`echo.`, `enviro.`, `aqs.`) can match at host level. (ii) Colorado agencies are split across `colorado.gov` subdomains AND legacy `state.co.us` subdomains—include both. (iii) Several agencies' actual data downloads live on third-party `*.hub.arcgis.com` / `*.opendata.arcgis.com` and `shinyapps.io` hosts—include these explicitly. (iv) Account for agency renames (COGCC→ECMC; GeoMAC→NIFC Open Data). Note: a subagent search surfaced anomalous references to an "nlr.gov" rebrand of NREL; this is unverified and should be treated with caution—keep `nrel.gov` as canonical and verify before adding any alternate.

**Stage B — Prose/named-entity detection (high recall).** For articles with no matching link, run (1) a keyword/alias dictionary (agency names, dataset names, and aliases: "SNOTEL," "streamgage," "ECHO database," "Toxics Release Inventory," "EnviroScreen," "COGIS") for candidate generation, then (2) **LLM-assisted extraction/classification** to decide whether each candidate is a genuine *data* citation and to assign `citation_type`/`attribution_strength`. Run the LLM with the article text + the candidate source list and require it to return a verbatim supporting quote span for each claimed citation (quotes that don't appear in the text are auto-rejected as hallucinations).

**3.4 Metadata capture.** For every article record, capture and store: `author(s)`, `outlet`, `publication_date`, `headline`, `canonical_url`, `section/beat`, `topic_tags`, `genre`, retrieval `source_method`, `retrieved_at`, `raw_html_pointer` (R2 key), and `archive_url`+`archive_timestamp`. Prefer structured metadata from the page's JSON-LD/`<meta>` tags (trafilatura extracts these) over inference.

**3.5 Tooling for undergraduates.**
- **Language/libraries:** Python with `requests`/`httpx`, `trafilatura` (extraction + sitemaps + link extraction), `beautifulsoup4` (targeted HTML parsing), the Wayback CDX endpoint (simple GET + JSON), `gdeltdoc` and the Media Cloud Python client.
- **Orchestration:** **Prefect** (open-source, Apache-2.0, pure-Python decorators—turn each retrieval/extraction step into a `@task`/`@flow` with automatic retries, caching, and observability; ideal for resumable scrape jobs students can monitor in a UI).
- **LLM inference:** **CU Research Computing (Alpine)** open-weight models via the cluster's shared LLM space and Ollama module (NVIDIA A100/L40 partitions; `atesting_a100` for quick tests). This keeps article text on-premises (privacy, cost control) and avoids per-token API fees. Reserve commercial APIs only for spot-checking.
- **Storage:** Use the project's existing **Datasette + Cloudflare R2 + Quarto** stack. Author the relational tables as SQLite for Datasette (excellent for exploring/publishing the journalist→article→citation graph; built for exactly this data-journalism use case); store raw HTML and archived snapshots as objects in R2; publish documentation and the public-facing site via Quarto. A spreadsheet is acceptable ONLY for the human-coding worksheet during the pilot; migrate to SQLite immediately after. Reference manager (Zotero) is optional for the methodological literature, not for the corpus itself.

---

### SECTION 4 — VERIFICATION STRATEGIES (CORE SECTION)

**4.1 Distinguishing true citations from false positives.** The dominant false-positive sources are boilerplate footer/nav links, ad/related-article modules, and social-share widgets. Mitigations: (a) extract links only from the article-body DOM node that trafilatura identifies as main content, discarding header/footer/aside; (b) maintain a *stoplist* of site-chrome domains and of an outlet's own boilerplate links; (c) require that a Stage-A link match be located within the article body, and flag links appearing identically across many articles from the same outlet (boilerplate signature) for exclusion; (d) for `agency_mention_ambiguous`, never auto-count—route to human adjudication.

**4.2 Inter-coder reliability and codebook.**
- **Codebook:** Written definitions for every field/enum (esp. the six `citation_type` values), with inclusion/exclusion criteria, ≥2 worked examples each, and explicit edge-case rules. Treat it as a living document; version it in the repo.
- **Pilot reliability check before scaling** (do not skip): two coders independently code an overlapping subsample; compute chance-corrected agreement.
- **Metric:** Report **Krippendorff's α** (handles >2 coders, missing data, nominal categories; Hayes–Krippendorff macro or Python `krippendorff`). Target **α ≥ 0.80**; 0.667–0.80 tolerable only for exploratory fields with documented justification. Communication-research convention is to double-code ~10% of the full dataset for the reliability subsample.
- **Adjudication:** Disagreements resolved in a third-coder or consensus meeting; log the resolution and update the codebook. Hold periodic calibration sessions to counter coder drift.

**4.3 Journalist identity / disambiguation.** Assign each person a stable internal `journalist_id`. Disambiguate common names using (outlet + beat + active dates + co-bylines) as a composite key; never merge on name alone. "Staff" and wire bylines get synthetic IDs flagged `is_org_byline=true` and are excluded from person-level analysis. For genuinely ambiguous cases, verify against the outlet author page and (manually) LinkedIn/Muck Rack. Record `disambiguation_status` (confirmed / probable / unresolved).

**4.4 Link verification and archiving (link-rot defense).** At coding time, for **every** cited URL: (1) submit it to the Wayback Machine "Save Page Now" to force a fresh capture; (2) query the CDX API to record the nearest existing snapshot timestamp; (3) store the resulting `archive_url` + `archive_timestamp` in the citations table. For already-dead links, use the CDX API to find what the URL pointed to at/near the article's publication date (using `from`/`to` date filters) and use the `…id_/` raw memento to confirm the target was a data portal. This makes every citation independently re-verifiable—core to defensibility.

**4.5 Validating LLM-assisted extraction.** This is mandatory, not optional, because LLMs hallucinate citations. Procedure:
- **Gold standard:** Humans hand-code a stratified random sample (across outlets, themes, years) as ground truth for presence/absence and type of each data-source citation.
- **Metrics:** Report **precision, recall, and F1** of the LLM detector against the gold standard, per `citation_type` and overall. The literature is explicit that LLM extractors often show high recall but poor precision and will "default to generating plausible values rather than acknowledging absence"—so precision is the metric to watch.
- **Hallucination control:** Require a verbatim quote span for every LLM-asserted citation and programmatically reject any quote not found in the source text; constrain the model to choose only from the provided 56-source list (closed-set classification) rather than free-generating source names; log model name/version and prompt in every run.
- **Decision rule:** Only promote LLM labels to the database unreviewed if precision ≥ a pre-registered threshold (recommend ≥0.90 for `direct`/`named`); below that, LLM output is treated as *candidate* requiring human confirmation.
- **Prompt design:** few-shot with the codebook definitions; chain-of-thought improves recall in extraction tasks but can slightly reduce precision—measure both.

**4.6 Versioning, audit trails, reproducibility.** Everything in Git (code, codebook, dictionary, prompts). Each pipeline run writes provenance: tool versions, source method, timestamps, model version, and a run ID stamped on every row it creates/edits. Keep raw HTML + archived snapshots immutably in R2 so any label can be reconstructed. Use Prefect's run history as the execution audit log. Tag database releases (v0.1 pilot, etc.) and publish a changelog.

---

### SECTION 5 — DATA SCHEMA AND DOCUMENTATION

**5.1 Recommended relational schema (SQLite for Datasette).**

**`journalists`** — `journalist_id` (PK), `full_name`, `name_variants`, `affiliation_type` (staff/freelance/student/newsletter/fellow/national/wire), `coverage_tier`, `co_resident` (bool), `is_org_byline` (bool), `muckrack_url`, `notes`, `disambiguation_status`, `created_by`, `run_id`.

**`affiliations`** (history) — `affiliation_id` (PK), `journalist_id` (FK), `outlet_id` (FK), `start_date`, `end_date`, `role`.

**`outlets`** — `outlet_id` (PK), `name`, `type`, `hq_city`, `ownership`, `founded`, `defunct` (bool), `last_pub_date`, `sitemap_url`, `rss_url`, `author_archive_pattern`, `paywall_status`.

**`articles`** — `article_id` (PK), `outlet_id` (FK), `headline`, `canonical_url`, `publication_date`, `section_beat`, `genre`, `topic_tags`, `is_syndicated`, `is_roundup`, `co_nexus` (bool), `series_id`, `source_method`, `retrieved_at`, `raw_html_key` (R2), `archive_url`, `archive_timestamp`, `dedupe_hash`, `run_id`.

**`article_authors`** (junction, many-to-many) — `article_id` (FK), `journalist_id` (FK), `byline_order`.

**`data_sources`** (the 56-source catalog) — `source_id` (PK), `name`, `theme` (water/fire/wind/minerals/pollution/land_use), `provenance_tier` (federal-CO/state/local-regional), `agency`, `landing_url`, `doc_url`, `match_hosts` (array of canonical hostnames), `match_keywords` (aliases for prose detection).

**`citations`** (junction — the heart of the DB) — `citation_id` (PK), `article_id` (FK), `source_id` (FK), `citation_type` (enum 1–6 from §1.4), `attribution_strength` (1–6), `data_origin` (portal/primary_records/unclear), `is_secondary` (bool), `evidence_quote` (verbatim span or matched URL), `detection_method` (url_match/llm/human), `confidence` (0–1), `verification_status` (auto/human_confirmed/adjudicated), `coder_id`, `cited_url`, `cited_url_archive`, `cited_url_archive_ts`, `run_id`.

**5.2 Documentation standards.** Ship with: a **data dictionary** (every table/field/enum, types, allowed values); the **codebook** (coding rules + examples + edge cases, version-stamped); a **README** (project scope, pipeline diagram, how to reproduce, refresh cadence, known limitations); a **sources catalog doc** (provenance of the 56 sources). Follow reproducible/public-interest-data norms: include `license`, `source`, and methodology in the Datasette `metadata.json` so provenance shows on the published site; release derived data (not republished full article text) consistent with fair-use TDM practice.

---

### SECTION 6 — ETHICAL, LEGAL, AND PRACTICAL CONSIDERATIONS

**6.1 Copyright / ToS / scraping.** Reproducing in-copyright news text to build and mine a research corpus is well-supported as fair use: U.S. courts (Authors Guild v. HathiTrust, 2d Cir. 2014; Authors Guild v. Google, 2d Cir. 2015) held that creating searchable, non-consumptive research databases of in-copyright works is transformative fair use, and that releasing derived data/metadata/analysis is also fair use so long as it does not re-express the originals to the public as a market substitute. Practical guardrails: (a) store **metadata + short excerpts + archived links**, not republished full articles, on the public site; full text/HTML kept privately in R2 for analysis only; (b) **respect robots.txt** and outlet ToS; (c) **rate-limit** politely (the Wayback CDX guidance and general etiquette suggest throttling, e.g., a delay between requests) and identify the crawler with a descriptive User-Agent and contact; (d) honor that CU's **licensed databases (Nexis Uni, ProQuest, NewsBank) prohibit bulk/automated downloading**—use them via manual search/export within license terms, not the scraper.

**6.2 Privacy of journalists.** Journalists are public figures acting professionally, so documenting bylined public work is low-risk; nonetheless: collect only professional information (no personal addresses/phones beyond public press contacts); prioritize **accuracy** and offer a **correction/right-to-respond** mechanism (a contact email and documented correction process); avoid characterizations beyond what the data supports (the DB records *whether* a source was cited, not quality judgments about the reporter). Note the asymmetry: the "occasional"/one-off tier could mislabel someone as an "environmental journalist" on the basis of a single story—hence the explicit `coverage_tier` flag.

**6.3 Practical workflow for an undergraduate team.**
- **Task division:** split by *function* (frame-builders, retrieval engineers, coders, QA/adjudicators) rather than by outlet, so expertise concentrates; rotate coders across outlets to reduce systematic bias.
- **Training:** every coder codes the same training set, then a calibration set, before touching live data; must clear the α threshold on a calibration batch to be cleared for solo coding.
- **Phased pilot** (see §7).
- **Effort estimate (planning figures, to be re-calibrated after pilot):** budget on the order of a few minutes per article for human coding/QA of an automatically pre-labeled article, materially more for articles requiring full manual citation review—measure the true rate during the pilot and use it to size the full build.
- **Common failure modes to watch:** coder drift (recalibrate); JS-rendered pages defeating extraction (Playwright fallback); paywalls (route to library DBs); link rot (archive at coding time); LLM hallucinated citations (quote-span verification); duplicate syndicated content (dedupe hash); name collisions (composite-key disambiguation); over-counting boilerplate links (body-only extraction + stoplist).

---

### SECTION 7 — PHASED IMPLEMENTATION PLAN

**Phase 0 — Setup (weeks 1–2).** Stand up the repo, SQLite schema, Datasette/R2/Quarto, Prefect, and Alpine LLM access. Load the 56-source catalog into `data_sources` and build the domain/keyword dictionary. Draft the codebook v0.1. *Milestone:* a coder can open Datasette and see empty, documented tables; dictionary unit-tested against a handful of known data-portal URLs.

**Phase 1 — Pilot: Colorado Sun, water theme, 2014–present (weeks 3–8).** Chosen because the Sun is digital-native (clean HTML, no hard paywall, rich hyperlinks), water has the densest catalog coverage (USGS NWIS, SNOTEL, DWR/CDSS, Water Quality Portal), and the Sun republishes Aspen Journalism water work (tests syndication handling). Execute the full pipeline end-to-end on this slice: retrieve (sitemaps + Media Cloud), extract (trafilatura), detect (Stage A + B), hand-code a gold standard, archive links.
- **Decision thresholds to exit Phase 1:**
  - Retrieval **recall ≥ 0.90** against a hand-built list of known Sun water articles (else add retrieval sources/fix sitemap parsing).
  - Stage-A URL-match **precision ≥ 0.95** (else refine dictionary/body-extraction/stoplist).
  - Stage-B LLM **precision ≥ 0.90** and **recall ≥ 0.80** vs. gold standard (else revise prompts, tighten closed-set, or downgrade LLM output to candidate-only).
  - Inter-coder **Krippendorff's α ≥ 0.80** on the citation-type field.
  - If thresholds are unmet, iterate on the pilot—do **not** scale.

**Phase 2 — Theme/outlet expansion (weeks 9–18).** Add the remaining five themes and the nonprofit/digital tier (Newsline, Boulder Reporting Lab, Aspen Journalism, KUNC, CPR, Fresh Water News, High Country News). Introduce Wayback CDX recovery for dead links. Re-measure precision/recall on each new outlet's first batch (extraction quality varies by CMS). *Milestone:* ≥10 outlets, all six themes, with per-outlet QA passing thresholds.

**Phase 3 — Legacy/paywalled + long tail (weeks 19–28).** Integrate CU Libraries databases for the Denver Post, Gazette, Daily Camera and other legacy/defunct dailies (manual export workflow, link-detection limited—flag these records `links_unavailable=true` and rely on prose detection). Add regional/mountain papers, student outlets, and newsletters/Substacks. *Milestone:* sampling frame substantially covered; coverage gaps documented.

**Phase 4 — Publication & maintenance (ongoing).** Publish the Datasette instance + Quarto site with full documentation; tag a versioned release; define a refresh cadence (e.g., quarterly re-crawl of active outlets) and a correction process. Re-run reliability checks each semester as new coders join.

## Recommendations (staged, with thresholds)
1. **Start now on Phase 0–1 only.** Prove the pipeline on Colorado Sun water coverage before any expansion. The single most important early metric is **Stage-B LLM precision**; if it cannot clear ~0.90 with quote-span verification and closed-set constraint, keep LLM output as human-review *candidates* rather than authoritative labels.
2. **Anchor on the highest-precision signal.** Make Stage-A URL/domain matching (with body-only extraction + boilerplate stoplist) the backbone; use the LLM to extend recall into prose, not to be the system of record.
3. **Archive every cited URL at coding time.** This is cheap insurance that makes the whole database defensible against link rot.
4. **Use free/owned infrastructure.** Media Cloud + GDELT + sitemaps + Wayback + CU Libraries + Alpine LLMs + the existing Datasette/R2/Quarto/Prefect stack cover the entire workload. Avoid Muck Rack/NewsAPI unless already licensed.
5. **Re-calibrate effort after the pilot.** Replace the planning-level per-article estimates with measured pilot rates before committing to the full outlet list, and let those numbers drive scope (which outlets/themes are feasible).
6. **Benchmarks that change the plan:** recall <0.90 → add retrieval sources; Stage-A precision <0.95 → dictionary/extraction fixes; α <0.80 → codebook revision + recalibration; LLM precision <0.90 → human-in-the-loop required.

## Caveats
- **GDELT/Media Cloud historical depth** is uneven for small Colorado outlets, and GDELT's DOC API officially supports only the most recent 3 months (its query tools reach back to January 2017 for all news); expect to lean on sitemaps + Wayback + library DBs for full 2014 coverage.
- **Library databases strip hyperlinks**, so citation detection for legacy/paywalled dailies will rely disproportionately on prose (Stage B), with lower precision—flag those records explicitly.
- **LLM extraction will hallucinate citations** if not constrained; the precision/recall validation and quote-span rejection are load-bearing, not optional.
- **Muck Rack pricing is non-public and enterprise-tier** (publicly cited figures range from ~$5,000/yr entry to a ~$79k/yr enterprise average); do not assume access.
- The **"nlr.gov" NREL rebrand** surfaced in one search trace is unverified and possibly spurious; verify before adding to the dictionary—keep `nrel.gov` canonical.
- **Fair-use protection is for non-consumptive research**; the moment the public site reproduces full article text as a substitute for the originals, that protection weakens—stick to metadata + excerpts + archived links.
- Effort estimates here are **planning figures**, not measured; the pilot exists precisely to replace them with real rates.