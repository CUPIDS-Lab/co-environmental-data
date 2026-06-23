# Glossary

Plain-language definitions of the acronyms and specialist terms used across this project's docs, so a reader with none of the project's context can follow them. Linked from `README.md` and `AGENTS.md`; the accessibility checklist asks that terms also be expanded on first use in each doc.

## Agencies & data sources

- **DWR** — Colorado **Division of Water Resources** (the state water agency).
- **CDSS** — **Colorado's Decision Support Systems**, the DWR data platform whose API serves reservoir storage, surface-water, and station data (`dwr.colorado.gov`).
- **RISE** — the U.S. Bureau of Reclamation's **Reclamation Information Sharing Environment** (`data.usbr.gov/rise`), the source for Reclamation-owned reservoirs.
- **USBR / Reclamation** — the U.S. **Bureau of Reclamation**.
- **NWIS** — the USGS **National Water Information System** (`waterservices.usgs.gov`), the source for streamflow gages.
- **USGS** — U.S. **Geological Survey**.
- **C-BT** — the **Colorado–Big Thompson** project, the trans-basin water system whose reservoirs (Carter, Horsetooth, Granby, …) are Reclamation-owned and sourced from RISE.
- **NREL** — the National Renewable Energy Laboratory. (Note: a spurious claim that NREL was renamed "National Laboratory of the Rockies / `nlr.gov`" is **false**; `nrel.gov` is canonical — see `AGENTS.md`.)
- **ECMC / COGCC** — Colorado's **Energy & Carbon Management Commission**, formerly the Colorado Oil & Gas Conservation Commission (renamed; both names appear in source history).
- **CEJ** — the **Center for Environmental Journalism** at CU Boulder, the project's journalism subject-matter partner.
- **CUPIDS Lab** — the **C**U **P**ublic **I**nterest **D**ata **S**cience Lab, the project's home.

## Measures & data terms

- **SWE** — **snow water equivalent**, the depth of water held in the snowpack (the snowpack pipeline's measure, #11).
- **acre-foot (AF)** — the volume of water covering one acre to a depth of one foot (~325,851 gallons); the unit for reservoir storage.
- **cfs** — **cubic feet per second**, the unit for streamflow discharge and reservoir release.
- **vertical datum** — the reference surface elevations are measured from; it differs across agencies, so elevations are not directly comparable without accounting for it.
- **tidy-long** — a data shape with one observation per row (here: one site × date × variable), the canonical schema for the liberated datasets.
- **provenance / `run_id`** — the record of where each row came from and which pipeline run produced it.

## Research & methodology

- **TDM** — **text and data mining**: the non-consumptive analysis of in-copyright text (here, news articles) that underpins the project's fair-use posture.
- **coverage_tier** — a journalist's level of environmental reporting (dedicated beat / frequent / occasional), used to avoid mislabeling a one-off contributor as an "environmental journalist."
- **citation_type** — the six-way classification of how a news article references a public dataset (defined in the forthcoming codebook).
- **Krippendorff's α (alpha)** — a chance-corrected measure of inter-coder agreement; the project targets α ≥ 0.80 before scaling human coding.

## Publishing & standards

- **FAIR** — **F**indable, **A**ccessible, **I**nteroperable, **R**eusable; the open-data principles the project aims at.
- **CARE** — **C**ollective benefit, **A**uthority to control, **R**esponsibility, **E**thics; the principles for Indigenous data governance (a hard gate where Indigenous data is implicated).
- **DOI** — **Digital Object Identifier**, the permanent citable identifier minted when a dataset is deposited to Dataverse.
- **Dataverse** — the open-source research-data repository (here, Harvard Dataverse) used to archive liberated datasets for a citable DOI.
- **UNF** — **Universal Numeric Fingerprint**, Dataverse's content hash that lets a specific dataset version be cited and verified.
- **OKF** — **Open Knowledge Format**, the concept-catalog bundle planned for L5 publication.
- **Datasette / Quarto** — the tools planned for the L5 public site (a queryable data catalog and a documentation site).
- **R2** — **Cloudflare R2**, the object storage for bulk artifacts (raw HTML, archived snapshots).
