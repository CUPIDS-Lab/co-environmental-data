# Colorado Environmental Data Hub — Discovery Audit & Source Inventory
### Cross-Tabulated by Theme × Provenance Tier (compiled June 17, 2026)

## TL;DR
- This catalog identifies ~70 authoritative environmental data sources for Colorado across six themes (Water, Fire, Wind, Minerals, Pollution, Land Use) and three provenance tiers (Federal, State, Local/Regional); **every theme has coverage in all three tiers**, so undergraduate expansion can proceed theme-by-theme confident that primary sources exist at each level.
- The single biggest **EROSION** risk in 2025–2026 is federal: documented removals/discontinuations of climate and environmental datasets (EPA EJScreen removed Feb 5, 2025; EPA Greenhouse Gas Reporting Program proposed for near-elimination Sept 12, 2025; NOAA Billion-Dollar Disasters tracker, climate.gov, and globalchange.gov shut down) plus the USGS legacy NWISWeb decommission (majority of pages retired by March 2026) mean water, pollution, and climate sources should be prioritized for local mirroring/archiving.
- The biggest **ENCLOSURE** risks are at the local tier and in records-only state systems: Denver Water (account-gated GIS request app), El Paso County (paid premium imagery/LiDAR), SECWCD (no portal — public-records request only), and DRMS/DWR document repositories (Laserfiche, partly request-only).

## Summary Coverage Matrix

| Theme | Federal | State | Local/Regional |
|---|---|---|---|
| Water | ✔ Strong (USGS NWIS/WDFN, NRCS SNOTEL, EPA WQP, Reclamation) | ✔ Strong (DWR/CDSS, CWCB, CHAMP) | ✔ Strong (Denver Water, Northern Water, CoAgMet) |
| Fire | ✔ Strong (NIFC/WFIGS, MTBS, LANDFIRE, USGS BAER/debris-flow) | ✔ Strong (DFPC, CSFS, CO-WRA) | ◐ Partial (county OEM/sheriff, CFRI) |
| Wind | ✔ Strong (NREL WIND Toolkit, EIA) | ◐ Partial (CoAgMet/CDSS climate stations) | ◐ Partial (university/met towers) |
| Minerals | ✔ Strong (BLM MLRS, USGS MRDS, EIA) | ✔ Strong (DRMS, CGS, ECMC/COGIS) | ◐ Partial (county GIS) |
| Pollution | ✔ Strong (EPA ECHO/TRI/AQS/Envirofacts/Superfund) | ✔ Strong (CDPHE APCD, EnviroScreen) | ✔ Strong (RAQC, county health) |
| Land Use | ✔ Strong (USGS NLCD/MRLC, PAD-US, TNM, USDA CDL) | ✔ Strong (CPW, CO Geospatial Portal, DOLA) | ✔ Strong (DRCOG, county/municipal GIS) |

**Agency renames verified:** Colorado's COGCC is now the **Energy & Carbon Management Commission (ECMC)** (effective July 1, 2023, per SB23-285). Default metadata fields below: Name · Agency · Theme(s) · Granularity · Temporal coverage · Access method · Format(s) · License · Update cadence · URL · Enclosure flag · Erosion flag.

---

## ⚠️ Data-integrity caveat for researchers (read first)
During research, search results for NREL returned content asserting that the National Renewable Energy Laboratory had been "renamed" to "National Laboratory of the Rockies (NLR)" with a new domain `developer.nlr.gov` (and a claimed "developer.nrel.gov retired May 29, 2026"). **This appears to be spurious/unverified content and should NOT be trusted.** The authoritative agency is the **National Renewable Energy Laboratory (NREL)**, a DOE national lab, with its developer API historically at `developer.nrel.gov` and main site `nrel.gov`. Undergraduates should verify the live NREL domain directly and treat the "NLR" rebrand as unconfirmed until checked against an official DOE/NREL source.

---

## THEME 1 — WATER

### A. Federal
**USGS National Water Information System (NWIS) / Water Data for the Nation (WDFN)**
- Agency: U.S. Geological Survey. Theme: Water (streamflow, groundwater levels, water quality, water use).
- Granularity: Point/station (~1.5 million sites nationally; hundreds in Colorado). Temporal: 135+ years of historical record to present; ongoing.
- Access: Modernized web pages (waterdata.usgs.gov), Water Data APIs, bulk download, interactive map (NWIS Mapper).
- Format: CSV/RDB, JSON, WaterML; API. License: Public domain (U.S. federal).
- Cadence: Real-time (many gages at 15-min intervals) to daily.
- URL: https://waterdata.usgs.gov/ ; mapper https://apps.usgs.gov/nwismapper/
- Enclosure: No (open, public domain).
- Erosion: **YES (high, active).** Per the USGS Water Data for the Nation blog, "The majority of NWISWeb pages are being retired by March 2026," with the full decommission running in three campaigns "from October 2024 through February 2027" (all legacy NWISWeb pages down by February 2027 in campaign 3). WaterWatch/Water Quality Watch slated for decommission by end of 2025; the legacy WaterServices APIs (`/iv`, `/dv`) — which "handled more than 1.6 billion requests from almost 3.5 million distinct IP addresses" between Oct 2024 and March 2025 — are scheduled for retirement in "late 2026 or early 2027." Legacy NWISWeb began experiencing data-integrity issues and some features were frozen as of December 2025; USGS notes the timeline was compressed "due to the lapse in appropriations and technical necessity." Data persists via WDFN, but old URLs/bookmarks/search-engine links and API endpoints break — high link-rot risk for undergraduate scripts.

**USGS StreamStats**
- Agency: USGS. Theme: Water (drainage-basin delineation, basin characteristics, streamflow statistics). Granularity: Watershed/basin, user-defined points. Temporal: Statistical summaries (period-of-record based).
- Access: Interactive web app; National Streamflow Statistics (NSS). Format: Map outputs, downloadable basin characteristics. License: Public domain. Cadence: Periodic/static.
- URL: https://streamstats.usgs.gov/ss/ ; info https://www.usgs.gov/streamstats
- Enclosure: No. Erosion: Partial (federal funding dependence; otherwise stable national app).

**USDA NRCS SNOTEL / Snow Survey & Water Supply Forecasting (AWDB)**
- Agency: USDA Natural Resources Conservation Service, National Water and Climate Center. Theme: Water (snowpack/SWE, precipitation, soil moisture, reservoir, streamflow forecasts).
- Granularity: Point/station (~600–800 automated sites in 12 western states; Colorado well covered) + basin summaries. Temporal: Since 1980 (SNOTEL); snow courses earlier; ongoing.
- Access: Interactive Map, Report Generator, predefined reports, AWDB API. Format: CSV, HTML tables, charts; API. License: Public domain. Cadence: Daily (near-real-time, ~1-day lag).
- URL: https://www.nrcs.usda.gov/resources/data-and-reports/snow-and-water-interactive-map ; CO products https://www.nrcs.usda.gov/wps/portal/nrcs/main/co/snow
- Enclosure: No. Erosion: Partial (federal staffing/funding; documented data-bias note on extended-range temperature sensors).

**EPA Water Quality Portal (WQP)** *(see also Pollution)*
- Agency: EPA + USGS + National Water Quality Monitoring Council. Theme: Water quality. Granularity: Point/station, national. Temporal: Historical–present.
- Access: Web portal, REST/web services, bulk download. Format: CSV, WQX XML; API. License: Public domain. Cadence: Continuous aggregation.
- URL: https://www.waterqualitydata.us/
- Enclosure: No. Erosion: Partial (aggregates federal+state feeds; vulnerable to upstream federal changes).

**U.S. Bureau of Reclamation — reservoir/operations data (Colorado River, Upper Colorado Region)**
- Agency: DOI Bureau of Reclamation. Theme: Water (reservoir storage, releases). Granularity: Reservoir/point. Temporal: Multi-decadal; ongoing.
- Access: RISE web data portal/HydroData. Format: CSV/JSON. License: Public domain. Cadence: Daily.
- URL: verify rise.reclamation.gov. Enclosure: No. Erosion: Partial (federal).

### B. State
**Colorado's Decision Support Systems (CDSS) / HydroBase + DWR REST Web Services**
- Agency: Colorado Division of Water Resources (DWR) + Colorado Water Conservation Board (CWCB), within DNR. Theme: Water (water rights, diversions, well permits, streamflow/gages, administrative calls, structures, climate stations).
- Granularity: Point/structure, water district, division (7 basins), statewide. Temporal: Historical (water-right priority dates back to the 1850s) to present; ongoing.
- Access: **Open REST API** (machine-readable), web tools/map viewer, bulk download. Format: JSON, GeoJSON, CSV, XML. License: Public/"as-is" (indemnification disclaimer; no warranty). Cadence: Real-time to daily (satellite-monitored gages); records updated continuously.
- URL: https://dwr.colorado.gov/services/data-information ; CDSS https://cdss.colorado.gov/ ; REST help https://dwr.state.co.us/rest/get/help ; tools https://dwr.state.co.us/Tools/WaterRights
- Enclosure: Partial — core data open via API; some permanent records only via Laserfiche WebLink document store. API key recommended to raise query limits.
- Erosion: Partial — CDSS is grant/state-funded ("funded through CWCB"); documentation notes web-service enhancements are limited by funding. Otherwise robust and state-controlled (lower federal-removal risk).

**Colorado Water Conservation Board (CWCB) — flood/hazard & water planning** *(see also CHAMP under Fire/Land Use)*
- Agency: CWCB (DNR). Theme: Water (flood, drought, water supply planning, instream flow).
- Access: Web portals, GIS, story maps; daily Flood Threat Bulletin. Format: GIS/shapefile, PDF, dashboards. License: Public. Cadence: Varies.
- URL: https://cwcb.colorado.gov/
- Enclosure: No. Erosion: Partial (state grant funding).

**Colorado Information Marketplace — water datasets (e.g., water-right status)**
- Agency: State of Colorado (OIT/SIPA, Socrata platform). Theme: Water + cross-cutting. Granularity: Varies.
- Access: Open data portal, SODA API, OData, bulk download. Format: CSV, JSON, GeoJSON; API. License: State terms of use (no single license). Cadence: Varies by dataset.
- URL: https://data.colorado.gov/
- Enclosure: No (some datasets marked private). Erosion: Partial (vendor-hosted SaaS — Socrata; platform/migration dependency).

### C. Local/Regional
**Denver Water — GIS data & water-quality story maps**
- Agency: Denver Water (municipal utility). Theme: Water (distribution system, water quality, watersheds). Granularity: Service area / ~1 sq-mi per request. Temporal: Current.
- Access: **Registered Data Request Application (account required, ~48–72 hr approval)**; public water-quality story maps. Format: Shapefile, PDF. License: Restricted (security/confidentiality withholding). Cadence: Request-based (no automated cadence).
- URL: https://www.denverwater.org/contractors/construction-information/gis-maps-and-data-requests ; request app http://gisdatarequest.denverwater.org/
- Enclosure: **YES** — login/account-gated, request-limited, some data withheld.
- Erosion: No (utility-funded, stable).

**Northern Water (Northern Colorado Water Conservancy District)**
- Agency: NCWCD. Theme: Water (Colorado-Big Thompson & Windy Gap real-time flows, reservoirs, watersheds; district boundary). Granularity: Canal/stream/reservoir/point + district. Temporal: Ongoing.
- Access: Web data portal (real-time flow viewer/download); **Open Data ArcGIS Hub**. Format: CSV, shapefile/GeoJSON, web services. License: Public (verify per dataset). Cadence: Real-time flows; boundary updated through May 2026.
- URL: https://www.northernwater.org/data ; hub https://data-nw.opendata.arcgis.com/
- Enclosure: No. Erosion: No (district-funded).

**Southeastern Colorado Water Conservancy District (SECWCD)**
- Agency: SECWCD. Theme: Water (Fryingpan-Arkansas Project). Granularity: District.
- Access: **Public-information request only (no open portal/dashboard)**; BMP Toolbox guidance. Format: Documents. License: Unclear. Cadence: N/A.
- URL: https://www.secwcd.org/ (phone request 719-948-2400).
- Enclosure: **YES** — no machine-readable open data; records-request only.
- Erosion: Partial (no preservation infrastructure for public data).

**CoAgMet (Colorado Agricultural Meteorological Network)** *(see also Wind)*
- Agency: Colorado Climate Center, Colorado State University (with CWCB; integrates Northern Water stations). Theme: Water (ET, precipitation, soil moisture) + Wind.
- Granularity: Point/station (90+ stations, mostly rural/agricultural). Temporal: Long-term stations ~30-yr records; ongoing.
- Access: Station selector/map, daily/monthly tables, **Data API**, daily maps (ET, growing degree days, soil moisture, wind). Format: CSV, tables; 5-min and hourly data; API. License: Not explicitly stated (flag to verify). Cadence: 5-minute/real-time.
- URL: https://coagmet.colostate.edu/
- Enclosure: Partial (some legacy form pages; license unstated). Erosion: Partial (university/soft-funded; recent site redesign — legacy endpoints flagged).

---

## THEME 2 — FIRE

### A. Federal
**NIFC / WFIGS Interagency Fire Perimeters (National Interagency Fire Center)**
- Agency: NIFC, Wildland Fire Interagency Geospatial Services, under the Wildland Fire Data Program. Theme: Fire (current + historical wildfire perimeters, fire locations).
- Granularity: Incident polygon/point, national (Colorado included). Temporal: Current year + full history (incident-based; "to date" annual datasets).
- Access: NIFC Open Data (ArcGIS Hub), ArcGIS REST FeatureServer, bulk download. Format: Shapefile, GeoJSON, CSV, KML, GeoTIFF; REST API. License: Creative Commons Attribution 3.0. Cadence: Real-time (refreshed every ~5 minutes for current perimeters; "fall-off" rules drop stale records).
- URL: https://data-nifc.opendata.arcgis.com/
- Enclosure: No. Erosion: Partial (interagency federal funding; current-perimeter "fall-off" rules mean records disappear from the live layer — capture "to date"/full-history layers for archiving).

**MTBS — Monitoring Trends in Burn Severity**
- Agency: USGS (EROS) + USDA Forest Service (GTAC). Theme: Fire (burn severity, burned-area boundaries). Granularity: Fire-event polygons/rasters, CONUS+AK/HI/PR (Colorado covered). Temporal: **1984–present**; annual updates.
- Access: MTBS Project website, MTBS Data Explorer, bulk download. Format: Thematic raster (GeoTIFF), shapefile. License: Public domain (free). Cadence: Annual.
- URL: https://www.mtbs.gov/
- Enclosure: No. Erosion: Partial (federal; depends on Landsat program + USGS/USFS funding).

**LANDFIRE**
- Agency: USDA Forest Service + DOI (USGS EROS). Theme: Fire (fuels, vegetation, disturbance) + Land Use. Granularity: 30 m raster, national. Temporal: ~2001–present; periodic updates.
- Access: LANDFIRE site, viewer, bulk download. Format: GeoTIFF, 26+ geospatial layers. License: Public domain. Cadence: Periodic (multi-year version releases).
- URL: https://www.landfire.gov/
- Enclosure: No. Erosion: Partial (federal interagency funding).

**USGS Post-Fire Debris-Flow Hazard Assessments + Burn Severity Portal / BAER**
- Agency: USGS (Landslide Hazards Program; EROS Burn Severity Portal) + USFS BAER. Theme: Fire (post-fire debris-flow probability/volume; BARC soil burn severity; RAVG vegetation condition).
- Granularity: Basin/segment, selected western fires (Colorado fires included). Temporal: Event-based; ongoing.
- Access: Project web pages, hazard maps, Burn Severity Portal downloads. Format: GIS/maps, rasters. License: Public domain. Cadence: Per-incident (rapid, within ~7 days of containment for BARC).
- URL: https://landslides.usgs.gov/hazards/postfire_debrisflow/ ; https://burnseverity.cr.usgs.gov/
- Enclosure: No. Erosion: Partial (federal funding/staffing).

### B. State
**Colorado Division of Fire Prevention & Control (DFPC) — Wildland Fire Management / CO-WIMS**
- Agency: DFPC, Colorado Department of Public Safety. Theme: Fire (incident management, preparedness, prescribed fire, aerial detection/modeling).
- Granularity: Statewide/incident. Temporal: DFPC est. 2012; ongoing.
- Access: Web (CO-WIMS is access-controlled decision support); preparedness plans (PDF); dashboards. Format: PDF, web maps; CO-WIMS restricted. License: Public (reports). Cadence: Real-time (operational), annual (preparedness plan).
- URL: https://dfpc.colorado.gov/ ; wildland section https://dfpc.colorado.gov/sections/wildland-fire-management
- Enclosure: Partial — CO-WIMS restricted to designated personnel; public-facing products are reports/maps.
- Erosion: Partial (state-funded; the 2025 preparedness plan explicitly flagged "federal cuts to wildfire services" as a concern).

**Colorado Wildfire Risk Assessment (CO-WRA) / 2025 Wildfire Resiliency Code Map**
- Agency: DFPC + Colorado State Forest Service (CSFS), directed by Wildfire Resiliency Code Board. Theme: Fire (fire-intensity scale, WUI, fuels).
- Granularity: Statewide raster/WUI polygons. Temporal: 2022 CO-WRA baseline; 2025 code map.
- Access: Interactive ArcGIS map; CSFS data requests. Format: Web map, GIS layers. License: Application-specific (map "not intended for other use"). Cadence: Periodic.
- URL: https://experience.arcgis.com/experience/34c113129c044004bc672ca5493378de
- Enclosure: Partial (code map use-restricted; full CO-WRA data via request).
- Erosion: Partial (state-funded; periodic updates).

### C. Local/Regional
**County Offices of Emergency Management / Sheriffs + Colorado Forest Restoration Institute (CFRI, CSU)**
- Agency: Counties; CFRI at CSU. Theme: Fire (local mitigation/CWPPs, monitoring maps).
- Granularity: County/project. Access: County GIS portals, CFRI project pages/maps. Format: PDF, web maps, GIS. License: Varies. Cadence: Irregular.
- URL (example): https://cfri.colostate.edu/
- Enclosure: Partial (some local data request-only). Erosion: Partial (grant-funded research institute). **Thin cell — prioritize for expansion.**

---

## THEME 3 — WIND

### A. Federal
**NREL WIND Toolkit (Wind Integration National Dataset)**
- Agency: National Renewable Energy Laboratory (DOE). Theme: Wind (modeled wind resource, met conditions, turbine power). Granularity: 2-km grid, CONUS (Colorado covered); 120,000+ representative points. Temporal: 2007–2013/2014 (model output).
- Access: Developer API, HSDS (cloud/Amazon S3), bulk download via OpenEI/AWS, point/area downloader. Format: CSV, HDF5; API. License: Public domain (DOE/public release). Cadence: Static (fixed model-year dataset; successor products like WTK-LED/HRRR-based added over time).
- URL (verify domain): https://www.nrel.gov/grid/wind-toolkit ; data https://data.openei.org/submissions/2 ; AWS bucket nrel-pds-wtk
- Enclosure: Partial — API requires a free key (email/affiliation); rate-limited.
- Erosion: Partial — DOE/NREL funding dependence; **see data-integrity caveat above regarding unverified "NLR/nlr.gov" rebrand claims** — verify the live NREL domain before citing.

**U.S. Energy Information Administration (EIA) — wind generation/capacity**
- Agency: EIA (DOE). Theme: Wind (electricity generation, capacity by plant/state). Granularity: Plant/state, Colorado. Temporal: Multi-decadal monthly series; ongoing.
- Access: EIA Open Data API v2, web tables, bulk download. Format: CSV, JSON; API. License: Public domain. Cadence: Monthly/annual.
- URL: https://www.eia.gov/opendata/
- Enclosure: No (free API key). Erosion: Partial (federal).

### B. State
**CoAgMet / CDSS climate stations (wind speed/direction)** — see Water (CoAgMet) and CDSS climate-station data; many stations record wind speed/direction relevant to dispersion. Enclosure: Partial. Erosion: Partial (university/state, soft funding). **Thin cell.**

### C. Local/Regional
**University & utility meteorological towers (e.g., NCAR/CU/CSU research met data; Xcel Energy)**
- Agency: CU Boulder, CSU, NCAR, utilities. Theme: Wind (research-grade met). Granularity: Point/tower. Access: Research data repositories, request. Format: CSV/NetCDF. License: Varies (academic). Cadence: Varies.
- Enclosure: Partial (some request/registration). Erosion: Partial (grant-funded — flag as thin tier; undergraduates should expand).

---

## THEME 4 — MINERALS

### A. Federal
**BLM Mineral & Land Records System (MLRS)**
- Agency: DOI Bureau of Land Management. Theme: Minerals (mining claims, fluid/solid mineral leases, geothermal, land tenure/use authorizations). Granularity: Claim/parcel, national (Colorado covered). Temporal: Historical–present.
- Access: Public reports (no account); login app for transactions; geospatial layers via BLM Geospatial Business Platform (GBP) Hub. Format: Reports (HTML/PDF), ArcGIS map services. License: Public domain. Cadence: Continuous (transactional).
- URL: https://mlrs.blm.gov/ ; public reports https://reports.blm.gov/reports/MLRS ; GBP Hub https://gbp-blm-egis.hub.arcgis.com/
- Note: MLRS replaced legacy LR2000/ACRES; **GeoCommunicator and Navigator are retired** — do not cite those.
- Enclosure: Partial (filing/transactions require account + pay.gov; public reports open).
- Erosion: Partial (federal; recent system migration — legacy URLs deprecated, link-rot for old LR2000 references).

**USGS Mineral Resources Data System (MRDS) / Mineral Resources Online Spatial Data**
- Agency: USGS. Theme: Minerals (metallic/nonmetallic deposit reports). Granularity: Deposit/point, worldwide (Colorado included). Temporal: Legacy–2011.
- Access: Web query, map, bulk download. Format: Shapefile, CSV, etc. License: Public domain. Cadence: **Static — USGS ceased systematic MRDS updates ~2011** (USMIN is the newer US-focused authoritative source).
- URL: https://mrdata.usgs.gov/mrds/
- Enclosure: No. Erosion: Partial — no longer maintained/updated; use USMIN for current US data.

**EIA — coal & oil/gas production** — Federal coal/O&G stats by state. URL: https://www.eia.gov/ ; Public domain; monthly/annual. Erosion: Partial (federal).

### B. State
**Colorado Division of Reclamation, Mining & Safety (DRMS)**
- Agency: DRMS (DNR). Theme: Minerals (mine permits, coal/hardrock production, abandoned/inactive mines, reclamation). Granularity: Site/permit, statewide (~12,500 reclaimed abandoned mines mapped since 1980; 20,000+ candidates remain). Temporal: Since 1980 (IMRP); permits ongoing.
- Access: **DRMS GIS Open Data Hub** (download), Laserfiche WebLink (permit documents), interactive search frames, spreadsheet on request. Format: CSV, KML, Zip/shapefile, GeoJSON, GeoTIFF, PNG; API (GeoServices/WMS/WFS) via hub; PDF for documents. License: "As-is," no warranty, indemnification (public access). Cadence: Irregular/ongoing.
- URL: https://drms.colorado.gov/data ; hub https://data-drms.hub.arcgis.com/
- Enclosure: Partial — GIS open; some permit docs (released sites) only via State Archives/request; spreadsheets "available upon request."
- Erosion: Partial (state-funded; document access fragmented).

**Colorado Geological Survey (CGS)**
- Agency: CGS (DNR; STATEMAP funding from USGS). Theme: Minerals (mineral resources, historic coal mines IS-64, aggregates, critical minerals) + geologic hazards. Granularity: Quadrangle/statewide. Temporal: Since 1910 (900+ publications); ongoing.
- Access: Publications archive (free PDF), **REST services (AML, Hazards, Minerals, Water)**, GIS data packages. Format: PDF, GIS_Data directories, REST/ArcGIS services. License: Public (some in-print sold via store). Cadence: Irregular (publication-driven).
- URL: https://coloradogeologicalsurvey.org/ ; GIS portal https://coloradogeologicalsurvey.org/geology/gis-data-map-portal/
- Enclosure: Partial (some hardcopies sold; data/PDFs free). Erosion: Partial (STATEMAP relies on federal USGS National Cooperative Geologic Mapping Program funding).

**Colorado Energy & Carbon Management Commission (ECMC, formerly COGCC) / COGIS**
- Agency: ECMC (DNR). Theme: Minerals/energy (oil & gas wells, production, permits/Form 4 sundries, spills, geothermal, carbon capture/storage, underground gas storage). Granularity: Well/facility/county, statewide. Temporal: Decades; ongoing.
- Access: COGIS online database, Daily Activity Dashboard, Data Downloads, imaged document search. Format: Database queries, CSV downloads, dashboards, PDF. License: Public. Cadence: Daily (activity dashboard); continuous.
- URL: https://ecmc.colorado.gov/data-maps-reports ; COGIS https://ecmc.colorado.gov/data-maps/cogis-database
- Note: Renamed from COGCC effective July 1, 2023 (SB23-285); legacy domain ecmc.state.co.us announced a website relaunch — expect link-rot on old cogcc.state.co.us URLs.
- Enclosure: No (public transparency mandate). Erosion: Partial (recent rebrand + website migration).

### C. Local/Regional
**County GIS (mining/aggregate overlays, e.g., Weld, Garfield, El Paso)** — county parcel/zoning portals carry aggregate operations and O&G surface overlays. See Land Use local tier. Enclosure: Partial. Erosion: Partial. **Thin cell.**

---

## THEME 5 — POLLUTION

### A. Federal
**EPA ECHO (Enforcement and Compliance History Online)**
- Agency: EPA. Theme: Pollution (CAA air, CWA water discharges, RCRA hazardous waste, SDWA drinking water, TRI context). Granularity: Facility (800,000+ national; Colorado subset). Temporal: Historical (data quality pre-2000 caveated)–present.
- Access: Web search, **ECHO web services (REST), ECHO Exporter bulk download, map services**. Format: CSV/ZIP, JSON, map services; API. License: Public domain. Cadence: Weekly refresh.
- URL: https://echo.epa.gov/ ; web services https://echo.epa.gov/tools/web-services
- Enclosure: No. Erosion: Partial — see EPA-wide removals below.

**EPA Envirofacts + Toxics Release Inventory (TRI)**
- Agency: EPA. Theme: Pollution (multi-system: ICIS-AIR, SEMS/Superfund, RCRAInfo, SDWIS, TRI, GHG, RadNet). Granularity: Facility, national. Temporal: Varies; TRI since 1987.
- Access: **Envirofacts RESTful Data Service API** (query any table via URL), web search, TRI Form R download. Format: JSON (default), CSV, Excel, XML, Parquet, PDF; API. License: Public domain. Cadence: Periodic by program.
- URL: https://enviro.epa.gov/ ; API https://www.epa.gov/enviro/envirofacts-data-service-api
- Enclosure: No. Erosion: **YES.** EPA released a formal proposal on September 12, 2025 (under EO 14192) to remove reporting obligations under the **Greenhouse Gas Reporting Program** for "all but one source category" (petroleum and natural gas systems); per Waste Dive (Sept 15, 2025), the GHGRP covers "more than 8,000 industrial facilities" across "47 categories," and the proposal states "2024 would be the final reporting year" (reporting deadline extended from March 31 to Oct. 30, 2026). TRI/Envirofacts core data remain available, but program-level discontinuations are active — mirror via the Public Environmental Data Partners (PEDP) and EDGI where possible.

**EPA Air Quality System (AQS) + AirNow**
- Agency: EPA (AirNow is multi-agency). Theme: Pollution (criteria pollutants, ozone, PM, real-time AQI). Granularity: Monitor/station, national (Colorado monitors). Temporal: AQS historical; AirNow real-time.
- Access: AQS API, AirNow API, web. Format: CSV, JSON; API. License: Public domain. Cadence: Real-time (AirNow) / continuous (AQS).
- URL: https://www.epa.gov/aqs ; https://www.airnow.gov/
- Enclosure: No (free API key). Erosion: **Partial–YES** — EPA's early-2025 deregulatory action reportedly included curtailments to air-quality monitoring; monitor for reductions.

**EPA Superfund / SEMS (Superfund Enterprise Management System)**
- Agency: EPA. Theme: Pollution (contaminated/Superfund sites, cleanups). Granularity: Site, national (Colorado NPL sites). Temporal: Since 1980s; ongoing.
- Access: Via Envirofacts SEMS, Cleanups in My Community, web. Format: API, CSV, maps. License: Public domain. Cadence: Periodic.
- URL: https://www.epa.gov/superfund
- Enclosure: No. Erosion: Partial (federal).

**EPA EJScreen — REMOVED (archival note)**
- Status: Per EDGI ("EPA Removes EJScreen from Its Website," Feb 12, 2025): "On February 5th, EPA removed from its website the environmental justice mapping and screening tool, EJScreen, as well as several related web pages," including "the ArcGIS server that distributes the spatial data behind EJScreen." A reconstruction is hosted by Public Environmental Data Partners (screening-tools.com); on Feb 7, 2025, EPA placed 171 EJ/DEIA staff on administrative leave (EPA Press Office). Colorado's state EnviroScreen (below) is an independent alternative.
- Erosion: **YES (removed).** Enclosure: No (open where archived). Researchers should cite PEDP/archived copies and note provenance.

### B. State
**CDPHE Air Pollution Control Division (APCD) — monitoring & advisories**
- Agency: Colorado Dept. of Public Health & Environment. Theme: Pollution (ozone, PM, air monitoring, smoke blog, forecasts, Suncor community monitoring). Granularity: Monitor/region, statewide. Temporal: Decades; ongoing.
- Access: Web dashboards, maps, daily alerts/email, technical document repository. Format: Web, PDF, some data feeds (to AirNow/AQS). License: Public. Cadence: Real-time/daily.
- URL: https://cdphe.colorado.gov/public-information/air-quality-monitoring-and-advisories
- Enclosure: Partial (some technical docs via Hyland/Laserfiche cloud). Erosion: Partial (state; relies on EPA AirNow pipeline).

**Colorado EnviroScreen 2.0**
- Agency: CDPHE Office of Environmental Justice (with CSU + Colorado School of Public Health). Theme: Pollution + cumulative environmental-justice burden (35 indicators). Granularity: Census block group, tract, county. Temporal: v1 (2022), v2.0 current.
- Access: Interactive map tool, **ArcGIS open data download (shapefile)**, field key, technical docs, code base. Format: Shapefile, CSV, web. License: Public/open data. Cadence: Periodic (version releases).
- URL: https://cdphe.colorado.gov/enviroscreen
- Enclosure: No. Erosion: Partial — depends partly on federal inputs (EPA EJScreen/CMAQ, CEJST); some upstream federal layers (EJScreen, CEJST) were removed in 2025, which could affect future updates. State-controlled hosting lowers immediate removal risk. (Note: EnviroScreen excludes areas under tribal jurisdiction.)

**CDPHE Open Data + Colorado Health & Environmental Data (CoHID)**
- Agency: CDPHE. Theme: Pollution + environmental health/epi. Granularity: Geospatial, county/tract. Access: ArcGIS open data, dashboards. Format: Shapefile/GeoJSON, CSV. License: Public. Cadence: Varies.
- URL: https://data-cdphe.opendata.arcgis.com/
- Enclosure: No. Erosion: Partial (state).

### C. Local/Regional
**Regional Air Quality Council (RAQC) — Denver Metro/North Front Range**
- Agency: RAQC (lead ozone planning agency for the 9-county nonattainment area: Adams, Arapahoe, Boulder, Broomfield, Denver, Douglas, Jefferson, Weld, and part of Larimer). Theme: Pollution (ozone summaries, SIP modeling, photochemical modeling). Granularity: Monitor/region. Temporal: Ongoing; weekly ozone-season summaries.
- Access: Web summary tables (weekly in season), reports/dashboards, modeling reports. Format: Web tables, PDF, dashboards. License: Public. Cadence: Weekly (ozone season ~May–Sept), periodic SIP.
- URL: https://raqc.org/ ; data https://raqc.org/aq-analysis-and-data
- Note: Uses CDPHE monitor data via EPA AirNow; monitors operated by CDPHE.
- Enclosure: Partial (some RAQC programs funded via the RAQC Clean Air Fund 501(c)(3) and grants; data public). Erosion: Partial (relies on CDPHE/EPA monitoring upstream).

**County public-health departments (e.g., Denver DDPHE, Boulder County PH) + NFRMPO** — local air/CO conformity, community monitoring. URL example: https://nfrmpo.org/air-quality/ . Enclosure: Partial. Erosion: Partial.

---

## THEME 6 — LAND USE

### A. Federal
**USGS/MRLC National Land Cover Database (NLCD) — Annual NLCD Collection 1.0**
- Agency: USGS-led Multi-Resolution Land Characteristics (MRLC) Consortium. Theme: Land use/cover (16 classes, impervious surface, land-cover change, rangeland RCMAP). Granularity: 30 m raster, national (Colorado covered). Temporal: **Annual 1985–2024** (Collection 1.0/1.1; replaces decadal model).
- Access: MRLC NLCD Viewer (rectangle/polygon/shapefile/GeoJSON download), data page, WMS, ArcGIS Online. Format: GeoTIFF; WMS. License: Public domain. Cadence: Now annual.
- URL: https://www.mrlc.gov/ ; viewer https://www.mrlc.gov/viewer/
- Enclosure: No. Erosion: Partial (federal funding; otherwise actively expanded as of 2025).

**USGS Protected Areas Database (PAD-US 4.1)**
- Agency: USGS Gap Analysis Project. Theme: Land use (protected areas, public lands, conservation, management). Granularity: Parcel/management-unit, national (Colorado covered). Temporal: v4.1 (2024 release).
- Access: Download page (by state or national), Data Explorer/Viewer apps. Format: ArcGIS Geodatabase. License: Public domain. Cadence: Periodic versions.
- URL: https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-download (DOI 10.5066/P96WBCHS)
- Note: Legacy gapanalysis.usgs.gov/padus URLs are deprecated/redirected.
- Enclosure: No. Erosion: Partial (federal).

**USDA NASS Cropland Data Layer (CDL) / CroplandCROS**
- Agency: USDA National Agricultural Statistics Service. Theme: Land use (crop-specific land cover, agriculture). Granularity: **10 m raster** (national; Colorado covered). Temporal: Annual.
- Access: CroplandCROS interactive site (replaced CropScape), release/metadata page, bulk download. Format: Raster (GeoTIFF). License: Public domain (free redistribution). Cadence: Annual.
- Detail: Per the USDA NASS Cropland Releases page, "The 2025 Cropland Data Layer was released February 27, 2026. The CDL spatial resolution has been increased from 30-meter to 10-meter beginning in 2024." The 2025 national 10 m file is 9.8 GB; "a 30-meter nearest neighbor resampled version is also available… for consistency with historical CDL data," and the 2025 product has an overall accuracy of 75.43%.
- URL: https://croplandcros.scinet.usda.gov/ ; release https://www.nass.usda.gov/Research_and_Science/Cropland/Release/
- Enclosure: No. Erosion: Partial (federal).

**USGS The National Map (TNM)**
- Agency: USGS National Geospatial Program. Theme: Land use (elevation/3DEP, hydrography/NHD, boundaries, transportation, imagery, land cover). Granularity: National (Colorado covered). Temporal: Ongoing.
- Access: TNM Downloader, web apps, WMS, bulk download. Format: GeoTIFF, shapefile/GeoPackage, LAS; WMS. License: Public domain. Cadence: Continuous.
- URL: https://apps.nationalmap.gov/downloader/ ; info https://www.usgs.gov/programs/national-geospatial-program/national-map
- Enclosure: No. Erosion: Partial (federal).

**USDA Census of Agriculture + USFS FACTS** — Ag Census (county-level ag land use, every 5 years; latest 2022) at https://www.nass.usda.gov/AgCensus/ ; USFS FACTS (treatments/activities). Public domain. Erosion: Partial (federal).

**U.S. Census / TIGER + FEMA flood (NFHL)** — boundaries/parcel context, flood zones. Census TIGER public domain; FEMA NFHL at https://www.fema.gov/flood-maps. Erosion: Partial (FEMA leadership/funding turmoil noted in 2025).

### B. State
**Colorado Parks & Wildlife (CPW) — Species Activity & public lands GIS**
- Agency: CPW (DNR). Theme: Land use (species activity/range, habitat, state parks/SWA boundaries, recreation). Granularity: Range polygons, parcels/boundaries, statewide. Temporal: Ongoing (collection dates vary by layer).
- Access: **CPW Spatial Data Hub (ArcGIS)**, Map Library (900+ maps), KMZ downloads, Hunting/Fishing Atlas. Format: Shapefile/GeoJSON, KMZ, GeoPDF; REST services. License: Public (for environmental assessment/planning/reference). Cadence: Varies/irregular.
- URL: https://geodata-cpw.hub.arcgis.com/ ; maps https://cpw.state.co.us/maps-and-gis
- Enclosure: No. Erosion: Partial (some layers have "collection methods/dates unknown" — metadata gaps).

**Colorado Geospatial Portal (geodata.colorado.gov)**
- Agency: Governor's Office of Information Technology (OIT) GIS. Theme: Land use (parcels, addresses, imagery, LiDAR, statewide aggregation). Granularity: Parcel/point/statewide. Temporal: Annual updates (e.g., "2026 Public Addresses").
- Access: ArcGIS Hub download, State Map Viewer, imagery/LiDAR downloader. Format: CSV, KML, Zip/shapefile, GeoJSON, GeoTIFF, PNG; GeoServices/WMS/WFS APIs. License: Varies per dataset ("Public/Custom"). Cadence: Annual/varies.
- URL: https://geodata.colorado.gov/ (contact oit_gis@state.co.us)
- Enclosure: Partial (license varies per dataset). Erosion: Partial (state-hosted ArcGIS Hub — platform dependency).

**Colorado Dept. of Local Affairs (DOLA) — State Demography Office + GIS**
- Agency: DOLA. Theme: Land use (population/housing projections, demographics, GIS). Granularity: County/place/block. Temporal: Ongoing; projections.
- Access: Web data, GIS downloads. Format: CSV, shapefiles. License: Public. Cadence: Annual.
- URL: https://demography.dola.colorado.gov/
- Enclosure: No. Erosion: Partial (uses Census inputs — vulnerable to federal Census changes).

### C. Local/Regional
**DRCOG Regional Data Catalog (Denver Regional Council of Governments)**
- Agency: DRCOG. Theme: Land use (regional land use/land cover, planimetrics, aerial imagery, LiDAR, demographics, transportation). Granularity: Region (9-county Denver metro), parcel/1-m LULC. Temporal: LULC 2018 & 2020; imagery biennial since 2002.
- Access: **Regional Data Catalog (open data)** download; some imagery for purchase from vendor. Format: GeoTIFF/geodatabase, shapefile, etc.; APIs. License: **Creative Commons Attribution (CC BY) 3.0**. Cadence: Biennial (imagery), periodic (LULC).
- URL: https://data.drcog.org/ ; info https://www.drcog.org/data-maps-modeling
- Enclosure: Partial — current aerial imagery sold via Sanborn (vendor-mediated); past imagery free.
- Erosion: Partial (regional COG funding; LULC funded via a CWCB Water Plan grant — soft funding).

**Denver Open Data (geospatialDENVER)**
- Agency: City & County of Denver. Theme: Land use (parcels, zoning, addresses, floodplain, housing). Granularity: Parcel/city. Access: Open data portal + ArcGIS Hub. Format: CSV, KML, Zip/shapefile, GeoJSON, GeoTIFF, PNG; GeoServices/WMS/WFS. License: Open. Cadence: Varies.
- URL: https://www.denvergov.org/opendata ; https://opendata-geospatialdenver.hub.arcgis.com/
- Enclosure: No. Erosion: Partial (municipal platform dependency).

**Boulder County GIS Open Data**
- Agency: Boulder County. Theme: Land use (parcels, zoning, open space, trails, boundaries). Access: Info page + ArcGIS Hub. Format: shapefile/GeoJSON/CSV; APIs. License: Permissive custom ("world-wide, royalty-free, non-exclusive license"). Cadence: Varies.
- URL: https://bouldercounty.gov/government/open-data/ ; https://opendata-bouldercounty.hub.arcgis.com/
- Enclosure: No. Erosion: Partial.

**City of Boulder Open Data**
- Agency: City of Boulder. Theme: Land use (parcels, zoning, OSMP open space, trails). Access: open-data.bouldercolorado.gov / data-boulder.opendata.arcgis.com. Format: shapefile/GeoJSON/CSV; APIs. License: **CC0 1.0 (public domain)**. Cadence: Varies.
- URL: https://open-data.bouldercolorado.gov/
- Enclosure: No. Erosion: Partial.

**El Paso County GIS**
- Agency: El Paso County. Theme: Land use (parcels, zoning). Access: ArcGIS Hub (free), free shapefile catalog, **plus licensed/paid premium data (recent aerial imagery, LiDAR contours)**. Format: shapefile/GeoJSON; downloads. License: Mixed (free + cost-recovery license). Cadence: Varies.
- URL: https://opendata-elpasoco.hub.arcgis.com/ ; free data https://admin.elpasoco.com/free-gis-data/
- Enclosure: **Partial–YES** — premium imagery/LiDAR is paid/licensed.
- Erosion: Partial.

**Jefferson County GIS**
- Agency: Jefferson County. Theme: Land use (tax parcels, zoning/comp plan, open space, hazards). Access: ArcGIS Hub, web maps, PDF maps. Format: shapefile/GeoJSON; PDF. License: Varies. Cadence: Varies.
- URL: https://data-jeffersoncounty.opendata.arcgis.com/ ; https://gis.jeffco.us/
- Enclosure: No. Erosion: Partial.

**Larimer County GIS**
- Agency: Larimer County. Theme: Land use (parcels, zoning, flood, imagery, wildfire mitigation, land cover 2011/2016). Access: GIS department page (dedicated download-hub URL unconfirmed). Format: GIS, PDF maps. License: Varies. Cadence: Varies.
- URL: https://www.larimer.gov/it/gis (flag: confirm download hub)
- Enclosure: Partial. Erosion: Partial.

---

## Recommendations (staged, with thresholds)

**Stage 1 — Triage by erosion risk (do first, next 1–3 months).** Prioritize archiving/mirroring the federal sources with active 2025–2026 removal or decommission timelines: (1) USGS NWISWeb data for Colorado gages before the March 2026 page retirement and the late-2026/early-2027 `/iv` and `/dv` API retirements — capture needed station IDs and migrate scripts to the new Water Data APIs now; (2) EPA TRI/Envirofacts/ECHO Colorado extracts and any Greenhouse Gas Reporting Program facility data (program proposed for near-elimination Sept 12, 2025, with 2024 as the proposed final reporting year) — use PEDP/EDGI mirrors as backup; (3) NOAA NCEI climate/disaster series and the federal layers feeding EnviroScreen (EJScreen, CEJST), already removed in 2025. **Threshold to escalate:** if any dataset shows a removal banner, a frozen-update notice, or a 404, immediately snapshot via the End-of-Term Web Archive / Wayback Machine and log provenance.

**Stage 2 — Lock in API access and licensing (months 2–4).** Register API keys (NREL, EPA AQS/AirNow, EIA, CDSS/DWR, Socrata app token for data.colorado.gov) and record rate limits. Document the license for each source — several (CoAgMet, Colorado Geospatial Portal per-dataset, Larimer County) have **unstated or mixed licenses** that need direct confirmation. **Threshold:** treat any source without an explicit open license as "restricted — verify" until a named license is confirmed.

**Stage 3 — Fill the thin cells (months 3–6).** The matrix shows Wind/Local-Regional, Fire/Local-Regional, and Minerals/Local-Regional as thinnest. Assign undergraduates to: enumerate county OEM wildfire/CWPP datasets; locate utility/university met-tower wind data (CU, CSU, NCAR, Xcel); and pull county-level aggregate/O&G surface overlays. **Threshold:** a theme×tier cell is "complete enough to hand off" when it has ≥2 named primary sources with verified URLs and access methods.

**Stage 4 — Standardize records & flag provenance (ongoing).** Enter every source into a structured schema (the 10 default fields + 2 flags). Mark each "verified" vs. "needs follow-up." Specifically re-verify: the NREL domain question (the NLR/nlr.gov claim — almost certainly spurious); the Larimer County download hub; the CoAgMet license; and the Reclamation RISE URL.

## Caveats
- **Source-poisoning warning (NREL):** Search results contained apparently fabricated claims that NREL was renamed "National Laboratory of the Rockies" with domain nlr.gov and that developer.nrel.gov was "retired May 29, 2026." This is unverified and likely false; cite NREL/nrel.gov and verify before use.
- **Federal volatility (2025–2026):** Per EDGI's "Climate of Suppression" tracking (reported by NPR, Aug 8, 2025), EDGI recorded "632 changes" to federal environmental websites in the first 100 days of the second Trump term versus "371 important changes" in the comparable 2017 period — a ~70% increase, observed even though EDGI monitored far fewer pages in 2025 (4,429) than in 2017 (>25,000). The National Security Archive Climate Change Transparency Project (Sept 30, 2025) documents that the entire climate.gov team was fired May 31, 2025; that the National Climate Assessment reports and USGCRP/globalchange.gov were taken offline; and that 404 Media found removed data.gov datasets came "disproportionately" from NOAA, NASA, DOI, DOE, and EPA. (A widely cited figure of "18 federal data resources taken down/discontinued as of Dec 1, 2025" appears in secondary reporting but could not be confirmed against an authoritative primary source — re-verify against EDGI's Federal Environmental Web Tracker before citing.) Congressionally mandated data *collection* (much NOAA/USGS data) largely continues, but the public-access *tools* are the vulnerable layer. Treat all federal climate/EJ access paths as at-risk and mirror proactively.
- **Decommission vs. deletion:** The USGS NWISWeb decommission is a *modernization/migration* (data persists in WDFN), not deletion — but it breaks old URLs and APIs and was accelerated by an appropriations lapse. Distinguish "migrated" from "removed" in the catalog.
- **Records-only/enclosure sources:** Denver Water (account-gated), SECWCD (no portal), El Paso County premium data (paid), and DRMS/DWR Laserfiche document stores are not fully open; budget time for request workflows.
- **Metadata gaps:** CPW notes some layers have unknown collection dates/methods; CoAgMet and several local portals lack explicit licenses; the Reclamation RISE and Larimer County hub URLs need direct confirmation. These are flagged inline as "verify."
- **Not exhaustive:** This is a discovery starting point (~70 sources). Known gaps for undergraduate expansion include watershed coalitions, additional conservancy/conservation districts, tribal data (Southern Ute, Ute Mountain Ute — note EnviroScreen excludes tribal-jurisdiction areas), and additional county portals (Adams, Arapahoe, Douglas, Weld, Garfield, Mesa, Pueblo).