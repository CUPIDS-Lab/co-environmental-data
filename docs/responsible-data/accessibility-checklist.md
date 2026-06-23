# Accessibility checklist — Colorado Environmental Data Hub

> **Applied per dataset in the dated QA audits** in [`audits/`](../../audits/): [reservoir (2026-06-22)](../../audits/2026-06-22-qa-audit.md) and [streamflow / snowpack / climate-stations (2026-06-23)](../../audits/2026-06-23-pipelines-qa.md). This file is the standing checklist; each audit is its application to specific data.

Make this project usable by the widest possible range of people — including those using screen readers, those who cannot perceive color differences, and those who are not specialists in the subject. Accessibility is part of being legible to someone with none of the project's context, not a final polish, so apply these as you write and build rather than at the end. The guidance follows the Turing Way's communication recommendations.

**Where this bites.** The Hub's public deliverable today is text (the catalog, the docs, the notebooks), so the document-structure and notebook checks apply **now**. The figure/color/table checks become load-bearing when the planned **Datasette + Quarto public site** and any charts are built — treat this list as the acceptance criteria for that site, tracked in `ROADMAP.md`.

## Language & summary

- [ ] A plain-language summary explains what the project is, who it serves, and what it found, without jargon or unexplained acronyms (the `README.md` "What & why" is this; keep it jargon-light as the corpus lands).
- [ ] Specialist terms — "vertical datum," "coverage_tier," "citation_type," "enclosure/erosion" — are defined on first use, and sentences are kept short enough to follow.

## Figures & color

- [ ] Every figure, chart, and image (in notebooks, the site, and reports) has alternative text describing what it shows and the point it makes.
- [ ] Charts use a colorblind-safe palette and do not rely on color alone — pair it with labels, patterns, or shape (relevant for any reservoir-storage or citation time-series viz).
- [ ] Text and graphical elements meet sufficient contrast against their background.

## Document structure

- [ ] Headings are properly nested (one level at a time) so the document has a navigable outline.
- [ ] Lists use real list markup rather than manual bullets or numbers.
- [ ] Links use meaningful text that says where they go, not "click here" or a bare URL.

## Tables

- [ ] Tables have real header rows (and row headers where needed) so assistive technology can read them — applies to the catalog rendered on the site and to `DATA-DICTIONARY.md`.
- [ ] Data is presented as actual text tables, never as an image of a table.

## Documents & notebooks

- [ ] Any PDF deliverable is tagged and readable by assistive technology (or an accessible HTML/Markdown version is offered instead).
- [ ] Notebooks (`pipelines/<name>/notebooks/`) include narrative text, alt text on plotted figures, and a logical reading order rather than code cells alone.

## Meetings & communication

- [ ] Team and partner meetings (the per-semester check-ins, codebook adjudication sessions) are run inclusively — captions or notes provided, materials shared in advance, and multiple ways to contribute offered.
- [ ] Communication channels and documents are available in formats people can actually access, and you invite people — students, CEJ collaborators, the public — to tell you what they need.
