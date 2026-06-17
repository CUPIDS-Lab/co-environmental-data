# Decision log — Colorado Environmental Data Hub

A running, dated record of design and data decisions and *why* they were made — the provenance of the project's choices, legible to people who join later. Add an entry whenever you make a non-obvious choice (a filtering rule, a definition, a tool, a tradeoff). Newest first.

## 2026-06-17 — Treat the source catalog as immutable raw, tracked in `data/raw/`

- **Context:** the curated catalog (`colorado_environmental_data_sources.json`) is small (~64 KB) and hand-compiled — more a curated source-of-record than a re-downloadable bulk file.
- **Decision:** place it in `data/raw/` and add a `.gitignore` carve-out so this one file is version-controlled, while the rest of `data/raw/*` stays ignored. New catalog vintages are new files, never in-place edits.
- **Why:** it is the project's actual tracked asset; versioning it gives a defensible history. The blanket "raw is git-ignored" convention assumes large/external inputs, which this is not.
- **Consequences:** the `context/` copy is retained as part of the design bundle; `data/raw/` is the canonical copy the data dictionary documents.

## 2026-06-17 — Frame the repo as the "Colorado Environmental Data Hub" (catalog now; corpus later)

- **Context:** the `context/` memos describe two layers — a source-inventory **catalog** (real data, present) and a journalist→article→citation **corpus** (specified as stubs in `architecture.md`).
- **Decision:** name the project the **Colorado Environmental Data Hub** (umbrella, matching the repo and the catalog JSON); document the catalog at L1 and record the corpus pipeline as the flagship L2+ roadmap initiative.
- **Why:** L1 documents what exists. The corpus is a future build; framing the Hub as the umbrella lets the catalog stand on its own while keeping the corpus discoverable in `ROADMAP.md`.
- **Consequences:** README/AGENTS center the catalog; the full pipeline lives in `ROADMAP.md` pointing at `context/architecture.md`.

## 2026-06-17 — Do not fire the full sensitive-data governance coupling at L1

- **Context:** the data present today is public agency metadata. The *planned* corpus will involve news article text (copyright) and journalist records (public figures acting professionally — low-risk per `context/methodology.md` §6.2), but neither is in the repo yet.
- **Decision:** keep L1 lean — no GOVERNANCE/responsible-data files now — but record the copyright/fair-use posture (metadata + excerpts + archived links, never republished full text) and the journalist correction/right-to-respond mechanism as **blocking** rows in `ROADMAP.md`.
- **Why:** generating governance scaffolds now would create dangling references and over-engineer a public catalog; dropping the duties silently would be worse. A named, blocking roadmap entry keeps the coupling honest without bloat. This is not a regulated/CARE/Indigenous-data case (which would force the coupling regardless of level).
- **Consequences:** before the corpus ingests article text or journalist PII, the project must climb to L3/L4 and satisfy those blocking items first.

## 2026-06-17 — Project scaffolded

- **Context:** project started with the CUPIDS Lab `data-project` skill at level L1.
- **Decision:** adopt the standard layout, immutable-raw-data convention, and the deferred-work roadmap; scaffold in place into the existing repo (replacing the stub README and `.gitignore`, keeping the MIT `LICENSE`).
- **Why:** right-sized, reproducible, and legible by default.
- **Consequences:** see `ROADMAP.md` for deferred concerns (the L2 pipeline, L3 collaboration, L4 responsible-data/QA, L5 open-knowledge publication).
