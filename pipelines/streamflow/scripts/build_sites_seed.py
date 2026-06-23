#!/usr/bin/env python3
"""Regenerate the curated gage seed `data/lookups/sites.csv` (reproducible).

Curated major-river USGS gages across all 8 Colorado basins; official names,
coordinates, elevation, county and period of record come from the USGS site
service; each gage's DWR mirror (abbrev) — plus the DWR record's own coordinates,
county and POR — is resolved live via the CDSS `usgsSiteId` cross-link. Stdlib-only
so it runs without the package env. Run: python scripts/build_sites_seed.py

Station-metadata columns (lat/long/elevation_ft/county/start_date/end_date) are
sidecar metadata about each gage; the processed output joins back to this seed by
(source, site_id). DWR's surfacewaterstations record carries no elevation, so each
DWR mirror borrows `elevation_ft` from the USGS gage it re-serves (same physical
gage). See docs/data-dictionary.md ("Station metadata").
"""
import csv, json, re, time, urllib.parse, urllib.request
from pathlib import Path

UA = "co-environmental-data/streamflow (CUPIDS Lab; accounts@brianckeegan.com)"
OUT = Path(__file__).resolve().parent.parent / "data" / "lookups" / "sites.csv"
COLUMNS = ["source", "site_id", "site_name", "basin", "usgs_site_no",
           "latitude", "longitude", "elevation_ft", "county", "start_date",
           "end_date", "notes"]

# Colorado county FIPS (3-digit, state 08) -> name, for the USGS `county_cd`.
# DWR's surfacewaterstations record reports the county name directly; USGS reports
# only the numeric code, so this static map keeps the USGS rows self-contained.
CO_COUNTY_FIPS = {
    "001": "Adams", "003": "Alamosa", "005": "Arapahoe", "007": "Archuleta",
    "009": "Baca", "011": "Bent", "013": "Boulder", "014": "Broomfield",
    "015": "Chaffee", "017": "Cheyenne", "019": "Clear Creek", "021": "Conejos",
    "023": "Costilla", "025": "Crowley", "027": "Custer", "029": "Delta",
    "031": "Denver", "033": "Dolores", "035": "Douglas", "037": "Eagle",
    "039": "Elbert", "041": "El Paso", "043": "Fremont", "045": "Garfield",
    "047": "Gilpin", "049": "Grand", "051": "Gunnison", "053": "Hinsdale",
    "055": "Huerfano", "057": "Jackson", "059": "Jefferson", "061": "Kiowa",
    "063": "Kit Carson", "065": "Lake", "067": "La Plata", "069": "Larimer",
    "071": "Las Animas", "073": "Lincoln", "075": "Logan", "077": "Mesa",
    "079": "Mineral", "081": "Moffat", "083": "Montezuma", "085": "Montrose",
    "087": "Morgan", "089": "Otero", "091": "Ouray", "093": "Park",
    "095": "Phillips", "097": "Pitkin", "099": "Prowers", "101": "Pueblo",
    "103": "Rio Blanco", "105": "Rio Grande", "107": "Routt", "109": "Saguache",
    "111": "San Juan", "113": "San Miguel", "115": "Sedgwick", "117": "Summit",
    "119": "Teller", "121": "Washington", "123": "Weld", "125": "Yuma",
}


# Optional CDSS API key (raises rate limits / avoids the 403 throttle) from the
# git-ignored dwr_api.json at the pipeline root. Keyless still works but throttles.
def _cdss_key():
    p = Path(__file__).resolve().parent.parent / "dwr_api.json"
    try:
        if p.exists():
            d = json.loads(p.read_text())
            return d.get("CDSS_API_KEY") or d.get("api_key") or d.get("apiKey") or ""
    except Exception:
        pass
    return ""

CDSS_KEY = _cdss_key()

# (usgs_site_no, basin) — curated mainstem gages, all 8 Colorado basins.
CURATED = [
    ("09058000","Colorado"),("09070500","Colorado"),("09095500","Colorado"),
    ("09163500","Colorado"),("09057500","Colorado"),("09070000","Colorado"),
    ("09085000","Colorado"),
    ("09114500","Gunnison"),("09128000","Gunnison"),("09152500","Gunnison"),
    ("09147500","Gunnison"),
    ("09165000","Dolores-San Miguel"),("09169500","Dolores-San Miguel"),
    ("09172500","Dolores-San Miguel"),
    ("09342500","San Juan"),("09361500","San Juan"),
    ("09304500","White"),
    ("09239500","Yampa-Green"),("09251000","Yampa-Green"),("09260000","Yampa-Green"),
    ("08220000","Rio Grande"),("08251500","Rio Grande"),("08246500","Rio Grande"),
    ("06714000","South Platte"),("06754000","South Platte"),("06764000","South Platte"),
    ("06752000","South Platte"),("06738000","South Platte"),
    ("07091200","Arkansas"),("07094500","Arkansas"),("07099970","Arkansas"),
    ("07124000","Arkansas"),("07106500","Arkansas"),
]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.status, r.read().decode("utf-8", "replace")


def _rdb_rows(text):
    """Parse an NWIS RDB body into dicts (skip `#` comments + the type-def row)."""
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    if len(lines) < 3:
        return []
    hdr = lines[0].split("\t")
    return [dict(zip(hdr, ln.split("\t"))) for ln in lines[2:]]


sites = ",".join(s for s, _ in CURATED)

# 1) Expanded site service: name, coordinates, elevation, county.
_, rdb = get("https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=" + sites +
             "&siteOutput=expanded&siteStatus=all")
usgs = {}
for rec in _rdb_rows(rdb):
    no = rec.get("site_no")
    if not no:
        continue
    usgs[no] = {
        "name": re.sub(r"\s+", " ", rec.get("station_nm", "")).strip(),
        "lat": rec.get("dec_lat_va") or "",
        "lon": rec.get("dec_long_va") or "",
        "alt": rec.get("alt_va") or "",
        "county": CO_COUNTY_FIPS.get((rec.get("county_cd") or "").strip(), ""),
    }

# 2) Series-catalog: daily-discharge period of record (begin_date / end_date).
_, scat = get("https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=" + sites +
              "&seriesCatalogOutput=true&outputDataTypeCd=dv&parameterCd=00060")
for rec in _rdb_rows(scat):
    if rec.get("parm_cd") != "00060":
        continue
    no = rec.get("site_no")
    b, e = rec.get("begin_date") or "", rec.get("end_date") or ""
    if no in usgs:
        cur = usgs[no]
        cur["start"] = min(x for x in [cur.get("start"), b] if x) if (cur.get("start") or b) else ""
        cur["end"] = max(x for x in [cur.get("end"), e] if x) if (cur.get("end") or e) else ""

# 3) DWR mirror per gage (abbrev + the DWR record's own coordinates/county/POR).
dwr = {}
for no, _ in CURATED:
    try:
        u = ("https://dwr.state.co.us/Rest/GET/api/v2/surfacewater/"
             "surfacewaterstations/?format=json&usgsSiteId=" + no)
        if CDSS_KEY:
            u += "&apiKey=" + urllib.parse.quote(CDSS_KEY, safe="")
        st, body = get(u)
        if st == 200:
            rl = json.loads(body).get("ResultList", []) or []
            if rl:
                r = rl[0]
                dwr[no] = {
                    "abbrev": r.get("abbrev"),
                    "name": re.sub(r"\s+", " ", (r.get("stationName") or "")).strip(),
                    "lat": r.get("latitude") or "",
                    "lon": r.get("longitude") or "",
                    "county": (r.get("county") or "").strip().title(),
                    "start": (r.get("startDate") or "")[:10],
                    "end": (r.get("endDate") or "")[:10],
                }
    except Exception as e:
        print("  DWR err", no, e)
    time.sleep(0.3)

rows = []
for no, basin in CURATED:
    u = usgs.get(no)
    if not u:
        continue
    rows.append(["usgs_nwis", no, u["name"], basin, no, u["lat"], u["lon"],
                 u["alt"], u["county"], u.get("start", ""), u.get("end", ""),
                 "USGS stream gage"])
for no, basin in CURATED:
    d = dwr.get(no)
    if not d or not d.get("abbrev"):
        continue
    # DWR's surfacewaterstations has no elevation -> borrow the USGS gage's alt_va
    # (the DWR row re-serves the same physical gage).
    elev = usgs.get(no, {}).get("alt", "")
    rows.append(["dwr_cdss", d["abbrev"], d["name"] or usgs.get(no, {}).get("name", ""),
                 basin, no, d["lat"], d["lon"], elev, d["county"], d["start"],
                 d["end"], f"DWR surface-water station; re-serves USGS {no}"])

with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(COLUMNS)
    w.writerows(rows)
n_u = sum(r[0] == "usgs_nwis" for r in rows); n_d = sum(r[0] == "dwr_cdss" for r in rows)
n_geo = sum(1 for r in rows if r[5] and r[6])
print(f"wrote {OUT.name}: {len(rows)} rows ({n_u} usgs + {n_d} dwr); {n_geo} with coordinates")
