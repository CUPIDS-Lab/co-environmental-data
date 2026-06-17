# Technical Architecture — Colorado Environmental Journalism Corpus Pipeline

**Project:** CU Environmental Data Hub / CUPIDS Clinic × Center for Environmental Journalism
**Artifact:** Notebook-based pipeline implementing the journalist → article → data-source-citation research design (2014–present)
**Status:** Architecture proposal. Notebooks and package modules are scaffolded as **stubs**; sections requiring manual configuration, retrieval, or analysis are marked and registered in §13.
**Date:** June 17, 2026

---

## 1. Purpose and scope

This document specifies a reproducible pipeline of Jupyter notebooks that implements the methodology memo's three-layer corpus. The pipeline has four named stages — **retrieval, cleanup, alignment, analysis** — bracketed by setup, verification, and publishing. It produces a SQLite database (served via Datasette) backed by immutable raw HTML in Cloudflare R2, with every data-source citation independently re-verifiable via archived links.

The architecture deliberately separates **what is automated** (retrieval, extraction, URL-matching, archiving, metrics) from **what requires a human** (credentials, the sampling frame, library-database exports, LLM-prompt tuning, hand-coding the gold standard, and the analytic questions). The latter are left as explicit stubs so an undergraduate team can see exactly where judgment enters and the architecture cannot proceed on autopilot.

This is infrastructural, not bespoke: the directory layout is multi-source and multi-vintage from day one, so adding an outlet is a registry entry plus a parser, not a refactor.

## 2. Design principles

1. **Notebooks are thin orchestration; logic lives in an importable package.** Each notebook imports `cejcorpus`, calls a few functions, inspects results, and writes to the database. Reusable logic (clients, extractors, the detector, metrics) sits in `src/cejcorpus/` so it is testable with `pytest` and reusable across notebooks. Notebooks are the *driver and lab notebook*; the package is the *machinery*.
2. **Immutable originals + per-extract provenance.** Raw HTML is written once to R2 and never edited; all cleaning produces new records. Provenance (source method, tool version, fetch timestamp, run_id, content hash) is a sidecar keyed on `(article_id, retrieval_run)`, not carried on every analytic row.
3. **Idempotent and resumable.** Every stage is safe to re-run: fetches are cached and hash-checked, writes are upserts keyed on stable IDs, and each notebook records which records it has already processed so a crash mid-batch loses nothing.
4. **Provenance-stamped and versioned.** Every row a notebook creates or edits carries a `run_id`. Code, codebook, dictionary, and prompts are in Git; database releases are tagged (`v0.1-pilot`, …).
5. **Automated/manual separation is explicit.** A single stub convention (§13) marks every human touchpoint. Package functions that need a credential or a decision `raise NotImplementedError` with a pointer to the register rather than silently doing the wrong thing.
6. **Highest-precision signal is the backbone.** Deterministic URL matching against the 56-source dictionary is the system of record for citations; the LLM extends recall into prose and is treated as *candidate* output until validated.
7. **Defensible by construction.** Every cited URL is archived at coding time; every automated label is measured against a hand-coded gold standard before it is trusted.

## 3. Repository layout

```
cej-corpus/
├── notebooks/                      <- thin orchestration + lab notebook (run in order)
│   ├── nb-00-config-and-setup.ipynb
│   ├── nb-01-build-frame.ipynb         RETRIEVAL  (frame; partly manual)
│   ├── nb-02-retrieve-articles.ipynb   RETRIEVAL
│   ├── nb-03-extract-and-clean.ipynb   CLEANUP
│   ├── nb-04-build-source-dictionary.ipynb  ALIGNMENT
│   ├── nb-05-detect-citations.ipynb    ALIGNMENT  (Stage A auto / Stage B LLM)
│   ├── nb-06-archive-cited-links.ipynb ALIGNMENT
│   ├── nb-07-verify-and-reliability.ipynb  VERIFY  (manual coding + alpha)
│   ├── nb-08-analyze.ipynb             ANALYSIS   (manual RQs)
│   └── nb-09-publish.ipynb             PUBLISH
├── src/cejcorpus/                  <- importable package (the machinery)
│   ├── __init__.py
│   ├── config.py        <- load config.yaml + .env; paths; new_run_id()
│   ├── schema.py        <- canonical table/column defs + pandera schemas
│   ├── storage.py       <- SQLite (sqlite-utils) + R2 (boto3 S3) + provenance
│   ├── frame.py         <- Outlet/Journalist registry (Source-ABC analog)
│   ├── retrieve.py      <- Media Cloud, GDELT, sitemap, Wayback CDX clients
│   ├── extract.py       <- trafilatura text+links+metadata; dedupe; fallback chain
│   ├── dictionary.py    <- build URL/keyword dictionary from the 56-source catalog
│   ├── detect.py        <- Stage A URL match + Stage B LLM (Ollama/Alpine) classifier
│   ├── archive.py       <- Wayback Save-Page-Now + CDX lookup
│   ├── reliability.py   <- Krippendorff alpha; precision/recall/F1 vs gold standard
│   └── provenance.py    <- run manifest + per-extract provenance writer
├── data/
│   ├── original/        <- pointers/manifests; raw HTML bodies live in R2
│   │   └── manifest.json
│   ├── processed/       <- corpus.db (SQLite) built by the pipeline
│   ├── audit/           <- reliability + reconciliation reports (auto-generated)
│   └── lookups/         <- source_dictionary.json, codebook.md, frame seeds
│       ├── colorado_environmental_data_sources.json   <- the 56-source catalog (input)
│       ├── source_dictionary.json                      <- generated by nb-04
│       ├── outlets_seed.csv          <- MANUAL: curated outlet frame
│       └── journalists_seed.csv      <- MANUAL: curated journalist seeds
├── docs/                           <- Quarto site source
│   ├── _quarto.yml
│   ├── index.qmd
│   ├── data-dictionary.md
│   ├── codebook.md
│   └── methodology.qmd
├── tests/                          <- pytest (schema contracts, parser fixtures, dict matching)
├── config.example.yaml             <- copy to config.yaml and edit (non-secret config)
├── .env.example                    <- copy to .env and edit (secrets)
├── pyproject.toml                  <- uv-managed environment
├── AGENTS.md                       <- architecture brief + how-to-add-a-source + gotchas
├── README.md
├── ARCHITECTURE.md                 <- this document
└── .gitignore
```

## 4. Data flow and storage model

```
 ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌─────────────┐
 │ nb-01 FRAME│──>│nb-02 RETRV │──>│nb-03 CLEAN │──>│nb-05 DETECT│──>│nb-08 ANALYZE│
 │ outlets +  │   │ Media Cloud│   │ trafilatura│   │ A: URL match│  │ freq, RQs,  │
 │ journalists│   │ GDELT,     │   │ text+links │   │ B: LLM prose│  │ precision/  │
 │ (MANUAL)   │   │ sitemaps,  │   │ dedupe     │   │ +nb-06 arch.│  │ recall      │
 └─────┬──────┘   │ Wayback,   │   └─────┬──────┘   └─────┬──────┘   └─────┬───────┘
       │          │ library DB │         │                │                │
       │          │ (MANUAL)   │         │     ┌──────────▼─────────┐      │
       │          └─────┬──────┘         │     │ nb-04 DICTIONARY   │      │
       │                │                │     │ from 56-source cat │      │
       ▼                ▼                ▼     └────────────────────┘      ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │  SQLite  data/processed/corpus.db   (relational tables; served by Datasette)  │
 │  outlets · journalists · affiliations · articles · article_authors ·          │
 │  data_sources · citations · coding (gold standard + double-coding)            │
 └─────────────────────────────────────────────────────────────────────────────┘
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │  Cloudflare R2 (S3-compatible)   raw HTML bodies · archived snapshots ·       │
 │  large blobs. Referenced from SQLite by object key; never inlined in the DB.  │
 └─────────────────────────────────────────────────────────────────────────────┘
        ▲                                   ▲
   nb-07 VERIFY (Krippendorff alpha,    nb-09 PUBLISH (build SQLite indexes +
   gold standard, adjudication)         metadata.yaml → Datasette; render Quarto)
```

**What lives where.** Relational facts — every table in the schema — live in `corpus.db` (small, queryable, the citable deliverable). Bulky/immutable artifacts — raw article HTML, Wayback snapshots, model run logs — live in R2 and are referenced from SQLite by object key (`raw_html_key`, `archive_url`). This keeps the database light enough to ship to Datasette while preserving the originals needed to re-run extraction and re-verify citations. SQLite is the system of record for *labels*; R2 is the system of record for *evidence*.

## 5. The notebook pipeline at a glance

| Notebook | Stage | Reads | Writes | Manual stub(s) |
|---|---|---|---|---|
| `nb-00-config-and-setup` | setup | `config.yaml`, `.env` | connections, empty schema, `run_id` | **CONFIG**: secrets, endpoints |
| `nb-01-build-frame` | retrieval | `outlets_seed.csv`, author-archive pages | `outlets`, `journalists`, `affiliations` | **RETRIEVAL**: curate frame; fellow rosters |
| `nb-02-retrieve-articles` | retrieval | frame, Media Cloud, GDELT, sitemaps, Wayback | `articles` (metadata), raw HTML→R2 | **RETRIEVAL**: Media Cloud query; library-DB export ingest |
| `nb-03-extract-and-clean` | cleanup | raw HTML (R2) | cleaned `articles` (text ptr, links, dedupe) | — (auto; fallback chain) |
| `nb-04-build-source-dictionary` | alignment | 56-source catalog JSON | `source_dictionary.json`, `data_sources` | **CONFIG**: alias/keyword curation |
| `nb-05-detect-citations` | alignment | articles, dictionary, LLM endpoint | `citations` (candidate) | **CONFIG**: LLM endpoint + prompt template |
| `nb-06-archive-cited-links` | alignment | `citations` | `archive_url`/`ts` on citations; snapshots→R2 | — (auto; rate-limited) |
| `nb-07-verify-and-reliability` | verify | citations sample | `coding` table, alpha report, adjudications | **ANALYSIS/CODING**: human double-coding; gold standard |
| `nb-08-analyze` | analysis | full DB | figures, tables, precision/recall | **ANALYSIS**: research questions |
| `nb-09-publish` | publish | `corpus.db`, docs | Datasette metadata, Quarto site | **CONFIG**: deploy target/creds |

## 6. Per-notebook specifications

Each notebook opens with a markdown cell stating purpose, inputs, outputs, and preconditions; ends with a validation cell (pandera schema check + row-count assertion); and stamps every write with `run_id`.

### nb-00 · Config and setup
**Purpose.** Load configuration, establish connections, create the schema if absent, mint a `run_id`.
**Cells.** (1) import `cejcorpus`; (2) `cfg = config.load()` — reads `config.yaml` + `.env`; (3) `db = storage.connect_sqlite(cfg)`, `r2 = storage.connect_r2(cfg)`; (4) `storage.ensure_schema(db)` applies `schema.py`; (5) `run_id = config.new_run_id()`; (6) connectivity smoke tests (R2 head-bucket, optional LLM ping).
**Outputs.** Open connections; empty, documented tables; `run_id`.
**Stub.** `# === STUB:MANUAL-CONFIG ===` — all credentials and endpoints (R2 keys, Media Cloud API key, LLM base URL, optional library-DB notes) are supplied by the operator in `.env`/`config.yaml`; `config.load()` raises if required keys are missing.

### nb-01 · Build the sampling frame *(retrieval; partly manual)*
**Purpose.** Populate `outlets`, `journalists`, `affiliations` — the population boundary from methodology §1–2.
**Cells.** (1) load `outlets_seed.csv` (hand-curated); (2) `frame.register_outlets(db, seed)`; (3) for each outlet, `frame.discover_author_pages(outlet)` to enumerate bylines from author-archive pages; (4) merge `journalists_seed.csv` (fellows, freelancers, Substackers that lack archive pages); (5) assign stable `journalist_id`, set `affiliation_type`, `coverage_tier` placeholders; (6) validate.
**Outputs.** Frame tables seeded.
**Stubs.** `# === STUB:MANUAL-RETRIEVAL ===` — the outlet list and the journalist seeds are curated by hand (Corey Hutchins' newsletter, SEJ/SPJ rosters, CEJ Scripps Fellow lists); author-archive URL *patterns* per outlet are entered manually because every CMS differs. `coverage_tier` is finalized only after nb-02 counts qualifying articles.

### nb-02 · Retrieve articles *(retrieval)*
**Purpose.** Build `articles` (metadata) for 2014–present and write raw HTML to R2.
**Cells.** (1) for each outlet, run the configured retrieval methods via `retrieve.*`: `media_cloud_search()`, `gdelt_search()`, `sitemap_urls()` (trafilatura), `wayback_cdx()` for defunct/dead URLs; (2) union + dedupe candidate URLs on canonical URL; (3) fetch with polite rate-limiting and `requests-cache`; (4) `storage.put_raw_html(r2, url, html)` → returns `raw_html_key`; (5) upsert `articles` rows with provenance; (6) ingest any library-database exports (manual) via `retrieve.ingest_library_export(path)`.
**Outputs.** `articles` metadata; raw HTML in R2; provenance rows.
**Stubs.** `# === STUB:MANUAL-RETRIEVAL ===` — (a) Media Cloud query parameters (collection IDs, date windows, keywords) are set per run; (b) **CU Libraries databases (Nexis Uni, NewsBank, ProQuest, Factiva) forbid automated download** — an operator exports results manually within license terms and drops files in `data/original/library/` for ingestion. `ingest_library_export()` flags these rows `links_unavailable=true`.

### nb-03 · Extract and clean *(cleanup)*
**Purpose.** Turn raw HTML into clean text, extracted hyperlinks, and normalized metadata; deduplicate.
**Cells.** (1) for each un-extracted article, `extract.article(html)` via trafilatura (fallback chain: trafilatura → readability-lxml → newspaper → Playwright flag for JS pages); (2) `extract.body_links(html)` — links from the main-content node only, discarding header/footer/aside; (3) normalize author/date/section from JSON-LD/meta; (4) `extract.dedupe_hash()` on (headline+date+author+first-200-chars) and resolve syndicated reprints; (5) write cleaned fields + `links_json` pointer; (6) pandera-validate.
**Outputs.** Cleaned `articles`; extracted body links staged for detection.
**Stub.** None required (fully automated). Playwright-needed pages are *flagged* `needs_render=true` for an operator to batch — a soft touchpoint, not a hard stub.

### nb-04 · Build the source dictionary *(alignment)*
**Purpose.** Compile the URL/domain + keyword dictionary that the detector matches against, from the existing 56-source catalog.
**Cells.** (1) load `colorado_environmental_data_sources.json`; (2) `dictionary.from_catalog(catalog)` — explode each source's `match_hosts` and `links.*` into canonical hostnames and host+subpath rules, and `match_keywords` into agency/dataset aliases; (3) write `source_dictionary.json`; (4) load the catalog into the `data_sources` table; (5) unit-test the matcher against known-good and known-bad URLs.
**Outputs.** `source_dictionary.json`; `data_sources` table.
**Stub.** `# === STUB:MANUAL-CONFIG ===` — keyword aliases and host+subpath disambiguation (shared `www.epa.gov`/`usgs.gov` subpaths; legacy `state.co.us` vs `colorado.gov`; `*.hub.arcgis.com` download hosts; COGCC→ECMC rename) need human curation. Do **not** add the unverified NREL "nlr.gov" host without confirmation; `nrel.gov` stays canonical.

### nb-05 · Detect citations *(alignment)*
**Purpose.** Produce candidate (article × data_source) citations via the two-stage detector.
**Cells.** (1) **Stage A** — `detect.url_match(article_links, dictionary)` → high-precision `direct_link_data` citations with the matched URL as evidence; (2) generate prose candidates with the keyword dictionary; (3) **Stage B** — `detect.llm_classify(article_text, candidate_sources, endpoint)` (Ollama on CU Research Computing / Alpine), closed-set over the 56 sources, requiring a verbatim quote span per asserted citation; (4) programmatically reject any quote not found in the text (hallucination guard); (5) write `citations` with `detection_method`, `citation_type`, `attribution_strength`, `confidence`, `verification_status='auto'`.
**Outputs.** Candidate `citations`.
**Stubs.** `# === STUB:MANUAL-CONFIG ===` — the LLM base URL/model name and the prompt template (few-shot examples drawn from the codebook) are operator-set and tuned during the pilot. LLM output stays `verification_status='auto'` (candidate) until nb-07 measures precision and clears a threshold.

### nb-06 · Archive cited links *(alignment)*
**Purpose.** Make every citation re-verifiable against link rot.
**Cells.** (1) for each citation with a `cited_url`, `archive.save_page_now(url)` to force a fresh capture; (2) `archive.cdx_nearest(url, article_date)` to record the snapshot closest to publication; (3) write `archive_url` + `archive_timestamp`; (4) store snapshot copies in R2; (5) for already-dead links, confirm the original target via the `…id_/` raw memento.
**Outputs.** Archived URLs/timestamps on `citations`; snapshots in R2.
**Stub.** None (automated; politely rate-limited).

### nb-07 · Verify and reliability *(verify; manual coding)*
**Purpose.** Hand-build the gold standard, double-code a sample, compute agreement, adjudicate, and validate the LLM detector.
**Cells.** (1) draw a stratified sample (outlet × theme × year); (2) export a coding worksheet; (3) **MANUAL: coders independently code** presence/type per the codebook; (4) ingest coding into the `coding` table; (5) `reliability.krippendorff_alpha(coding)` on `citation_type` (target ≥ 0.80); (6) `reliability.precision_recall(auto=citations, gold=coding)` per `citation_type` and overall; (7) record adjudications; promote confirmed labels to `verification_status='human_confirmed'`.
**Outputs.** `coding` table; `data/audit/reliability.md`; promotion of validated labels.
**Stub.** `# === STUB:MANUAL-ANALYSIS/CODING ===` — human double-coding and gold-standard construction are irreducibly manual; this notebook orchestrates and measures but does not produce the codes.

### nb-08 · Analyze *(analysis)*
**Purpose.** Answer the research questions over the verified corpus.
**Cells.** (1) load joined views (citations × articles × journalists × data_sources); (2) descriptive cuts — citation frequency by source, theme, provenance tier, outlet, journalist, and year; coverage of the 56 sources; data-citing vs non-data-citing reporting over time; (3) detector performance summary (precision/recall by type); (4) figures (matplotlib) and exportable tables.
**Outputs.** Figures/tables under `data/audit/` or `docs/`.
**Stub.** `# === STUB:MANUAL-ANALYSIS ===` — the specific research questions, breakdowns, and interpretation are the analyst's; only scaffolding queries are provided.

### nb-09 · Publish *(publish)*
**Purpose.** Ship the queryable Datasette interface and the Quarto documentation site.
**Cells.** (1) build SQLite indexes + FTS on narrative columns via sqlite-utils; (2) generate `metadata.yaml` from `docs/data-dictionary.md`; (3) `datasette publish …` (target from config); (4) render Quarto site; (5) tag a release.
**Outputs.** Public Datasette instance; documentation site; tagged release.
**Stub.** `# === STUB:MANUAL-CONFIG ===` — deploy target and credentials (Vercel/Cloud Run/Fly, or self-hosted) are operator-set.

## 7. Supporting package (`src/cejcorpus/`)

| Module | Responsibility | Key callables (stubbed) |
|---|---|---|
| `config.py` | Load `config.yaml` + `.env`; resolve paths; mint run IDs | `load()`, `new_run_id()`, `require(keys)` |
| `schema.py` | Canonical table/column defs; pandera schemas | `TABLES`, `Articles`, `Citations`, `ensure(db)` |
| `storage.py` | SQLite (sqlite-utils) + R2 (boto3 S3) + provenance writes | `connect_sqlite()`, `connect_r2()`, `put_raw_html()`, `get_raw_html()`, `upsert()` |
| `frame.py` | Outlet/journalist registry; author-page discovery | `register_outlets()`, `discover_author_pages()`, `assign_journalist_id()` |
| `retrieve.py` | Retrieval clients + library-export ingest | `media_cloud_search()`, `gdelt_search()`, `sitemap_urls()`, `wayback_cdx()`, `ingest_library_export()` |
| `extract.py` | Text/link/metadata extraction; dedupe; fallback chain | `article()`, `body_links()`, `dedupe_hash()` |
| `dictionary.py` | Build matcher from the 56-source catalog | `from_catalog()`, `canonicalize_host()`, `match()` |
| `detect.py` | Stage A URL match + Stage B LLM classify | `url_match()`, `llm_classify()`, `reject_hallucinations()` |
| `archive.py` | Wayback Save-Page-Now + CDX | `save_page_now()`, `cdx_nearest()` |
| `reliability.py` | Agreement + detector metrics | `krippendorff_alpha()`, `precision_recall()` |
| `provenance.py` | Run manifest + per-extract provenance | `record()`, `manifest()` |

Stub functions carry full type signatures and docstrings; those needing a credential or a human decision `raise NotImplementedError("STUB — see ARCHITECTURE.md §13 register row …")`.

## 8. Canonical schema

Tables follow the methodology memo §5: `outlets`, `journalists`, `affiliations`, `articles`, `article_authors`, `data_sources`, `citations`, plus a `coding` table (gold standard + double-coding: `coding_id`, `article_id`, `source_id`, `coder_id`, `citation_type`, `round`, `is_gold`). Defined canonically in `schema.py` (with pandera contracts) and mirrored in `schema.sql` for direct SQLite/Datasette use. Keys: stable surrogate IDs everywhere; `citations` is the junction carrying `citation_type`, `attribution_strength`, `data_origin`, `detection_method`, `confidence`, `verification_status`, `cited_url`, `cited_url_archive`, `run_id`.

## 9. Configuration and secrets

Two files, both git-ignored, both with committed `.example` templates:
- **`config.yaml`** (non-secret): outlet collection IDs, date window (`2014-01-01`→present), retrieval method toggles, LLM model name, rate limits, Datasette deploy target, paths.
- **`.env`** (secret): `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `MEDIACLOUD_API_KEY`, `LLM_BASE_URL`, `LLM_API_KEY` (if any). `config.require()` fails fast with a clear message naming any missing key.

## 10. Provenance, validation, reproducibility

**Provenance.** `provenance.record()` writes one row per extract: `(article_id, retrieval_run, source_method, tool, tool_version, fetched_at, content_sha256, run_id)`. `data/original/manifest.json` hashes raw HTML so re-runs detect drift. **Validation.** pandera schemas guard the boundary of every notebook; `pytest` covers schema contracts, the dictionary matcher (known-good/known-bad URLs), and extraction fixtures. **Reproducibility.** `uv` lockfile pins dependencies; code/codebook/dictionary/prompts in Git; tagged DB releases; raw HTML + snapshots immutable in R2 so any label reconstructs. A clone runs `uv sync` then executes notebooks `nb-00`→`nb-09` (or the papermill driver in §11).

## 11. Orchestration

Three execution modes, same package:
1. **Interactive** (default for the team) — run notebooks in order in JupyterLab; the lab-notebook cells make state visible.
2. **Headless replay** — `papermill` executes each notebook with parameters for CI smoke tests and full re-runs (`papermill nb-02-retrieve-articles.ipynb out.ipynb -p outlet_id …`).
3. **Scheduled refresh** — **Prefect** flows wrap the package functions (not the notebooks) for the quarterly re-crawl of active outlets, with retries, caching, and a run UI. The notebooks remain the canonical human-facing pipeline; Prefect is the unattended path.

## 12. Publishing

Per the data-liberation publishing convention: **Datasette** serves `corpus.db` (faceting, SQL, JSON API, per-column docs from `metadata.yaml`); **Quarto on GitHub Pages** serves the methodology, codebook, and data dictionary; **R2 / Releases** distribute bulk artifacts. The public site shows metadata + short excerpts + archived links — never republished full article text — consistent with the fair-use posture in the methodology memo §6.

## 13. Stub convention and manual-touchpoints register

**Convention.** Every human touchpoint is marked in code with one of three banners, and package functions that cannot proceed without it raise `NotImplementedError` pointing here:

```python
# === STUB:MANUAL-CONFIG ===      operator must supply credentials / endpoints / parameters
# === STUB:MANUAL-RETRIEVAL ===   operator must curate a list or perform a manual/licensed export
# === STUB:MANUAL-ANALYSIS ===    human judgment: coding, gold standard, or research questions
```

**Register.**

| ID | Notebook | Type | What the human must do | Why it can't be automated |
|---|---|---|---|---|
| M1 | nb-00 | CONFIG | Fill `.env`/`config.yaml` (R2, Media Cloud, LLM endpoint, deploy target) | Secrets; environment-specific |
| M2 | nb-01 | RETRIEVAL | Curate `outlets_seed.csv` + author-archive URL patterns | No canonical machine list; per-CMS patterns |
| M3 | nb-01 | RETRIEVAL | Curate `journalists_seed.csv` (fellows, freelancers, Substackers) | Sources are rosters/newsletters, not APIs |
| M4 | nb-02 | RETRIEVAL | Set Media Cloud query parameters per run | Editorial scoping decision |
| M5 | nb-02 | RETRIEVAL | Export library-DB results manually, drop in `data/original/library/` | License forbids automated download |
| M6 | nb-04 | CONFIG | Curate keyword aliases + host/subpath disambiguation | Linguistic/structural judgment; renames |
| M7 | nb-05 | CONFIG | Set LLM model + tune prompt template | Prompt engineering; pilot-tuned |
| M8 | nb-07 | ANALYSIS | Hand-code gold standard + double-code sample | Ground truth is human-defined |
| M9 | nb-07 | ANALYSIS | Adjudicate disagreements; update codebook | Requires deliberation |
| M10 | nb-08 | ANALYSIS | Define research questions and interpret | The scholarship itself |
| M11 | nb-09 | CONFIG | Choose deploy target + credentials | Deployment decision |

## 14. How to run / bootstrap

```bash
uv sync                                  # create the pinned environment
cp config.example.yaml config.yaml       # M1: edit non-secret config
cp .env.example .env                      # M1: add secrets
uv run pytest                             # verify the scaffold
# then, in JupyterLab, run notebooks in order:
#   nb-00 -> nb-01 (M2,M3) -> nb-02 (M4,M5) -> nb-03 -> nb-04 (M6)
#   -> nb-05 (M7) -> nb-06 -> nb-07 (M8,M9) -> nb-08 (M10) -> nb-09 (M11)
```

Pilot first (methodology §7): run the full chain on **Colorado Sun water coverage** and clear the exit thresholds (retrieval recall ≥ 0.90; Stage-A precision ≥ 0.95; Stage-B precision ≥ 0.90 / recall ≥ 0.80; alpha ≥ 0.80) before scaling to all outlets and themes.

## 15. Open decisions and caveats

- **Notebooks vs. CLI.** The data-liberation skill's reference template is a `scripts/` CLI (`pipeline.py discover|fetch|clean|…`). This design keeps that package discipline but exposes the pipeline as notebooks per the request; the package is identical machinery, so a CLI wrapper can be added later with no rework.
- **LLM precision is load-bearing.** If Stage-B precision can't clear ~0.90 with quote-span verification + closed-set constraint, the architecture keeps LLM labels as human-review candidates rather than authoritative — nb-07 enforces this gate.
- **Library-DB records are link-poor.** Articles ingested from Nexis Uni/ProQuest/NewsBank lack hyperlinks, so they rely on Stage-B prose detection and are flagged `links_unavailable=true`; expect lower precision there.
- **NREL host caveat.** Do not seed the dictionary with the unverified `nlr.gov` rebrand; confirm against an official source first.
- **Effort figures are estimates.** Per-article coding rates are unknown until the pilot; nb-07 measures them and they should drive final scope.
