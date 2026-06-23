#!/usr/bin/env python3
"""Regenerate the curated gage seed `data/lookups/sites.csv` (reproducible).

Curated major-river USGS gages across all 8 Colorado basins; official names come
from the USGS site service; each gage's DWR mirror (abbrev) is resolved live via
the CDSS `usgsSiteId` cross-link. Stdlib-only so it runs without the package env.
Run: python scripts/build_sites_seed.py
"""
import csv, json, time, urllib.parse, urllib.request
from pathlib import Path

UA = "co-environmental-data/streamflow (CUPIDS Lab; accounts@brianckeegan.com)"
OUT = Path(__file__).resolve().parent.parent / "data" / "lookups" / "sites.csv"

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

import re
sites = ",".join(s for s, _ in CURATED)
_, rdb = get("https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=" + sites +
             "&siteOutput=expanded&siteStatus=all")
names = {}
lines = [ln for ln in rdb.splitlines() if ln and not ln.startswith("#")]
ix = {c: i for i, c in enumerate(lines[0].split("\t"))}
for ln in lines[2:]:
    f = ln.split("\t")
    names[f[ix["site_no"]]] = re.sub(r"\s+", " ", f[ix["station_nm"]]).strip()

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
                dwr[no] = (rl[0].get("abbrev"),
                           re.sub(r"\s+", " ", (rl[0].get("stationName") or "")).strip())
    except Exception as e:
        print("  DWR err", no, e)
    time.sleep(0.3)

rows = [["usgs_nwis", no, names[no], basin, no, "USGS stream gage"]
        for no, basin in CURATED if no in names]
rows += [["dwr_cdss", dwr[no][0], dwr[no][1] or names.get(no, ""), basin, no,
          f"DWR surface-water station; re-serves USGS {no}"]
         for no, basin in CURATED if no in dwr and dwr[no][0]]

with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["source", "site_id", "site_name", "basin", "usgs_site_no", "notes"])
    w.writerows(rows)
n_u = sum(r[0] == "usgs_nwis" for r in rows); n_d = sum(r[0] == "dwr_cdss" for r in rows)
print(f"wrote {OUT.name}: {len(rows)} rows ({n_u} usgs + {n_d} dwr)")
