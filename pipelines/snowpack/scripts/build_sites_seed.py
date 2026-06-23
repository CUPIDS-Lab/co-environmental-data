#!/usr/bin/env python3
"""Regenerate the station seed `data/lookups/sites.csv` (reproducible).

Enumerates EVERY active Colorado SNOTEL (network SNTL) and snow-course (network
SNOW) station from the NRCS AWDB REST API, derives each station's major river
basin from its HUC, and writes the seed. SNOTEL + snow courses are a small,
enumerable universe (~200 stations), so the committed seed is full-state coverage,
not a sample. Stdlib-only (no API key needed) so it runs without the package env.

Run: python scripts/build_sites_seed.py            # active stations (default)
     python scripts/build_sites_seed.py --all      # include discontinued (deep history)
"""
import argparse
import csv
import json
import urllib.request
from pathlib import Path

UA = "co-environmental-data/snowpack (CUPIDS Lab; accounts@brianckeegan.com)"
BASE = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"
OUT = Path(__file__).resolve().parent.parent / "data" / "lookups" / "sites.csv"
NETWORK_TO_SOURCE = {"SNTL": "nrcs_snotel", "SNOW": "nrcs_snowcourse"}
COLUMNS = ["source", "site_id", "station_id", "site_name", "basin", "network",
           "huc", "elevation_ft", "latitude", "longitude", "county", "begin_date",
           "end_date", "notes"]


def huc_to_basin(huc):
    """Map a HUC to a Colorado major river basin (documented approximation; see
    snowpack.stations.huc_to_basin / concepts.yaml)."""
    h = str(huc or "")
    h4, h8 = h[:4], h[:8]
    if h4 == "1405":
        return "White" if h8 in {"14050005", "14050006", "14050007"} else "Yampa-Green"
    if h4 in ("1406", "1407"):
        return "Yampa-Green"
    return {
        "1401": "Colorado", "1402": "Gunnison", "1403": "Dolores-San Miguel",
        "1408": "San Juan", "1301": "Rio Grande", "1302": "Rio Grande",
        "1019": "South Platte", "1018": "North Platte",
        "1102": "Arkansas", "1103": "Arkansas",
    }.get(h4, "Other")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def fetch_network(network, active_only):
    url = (f"{BASE}/stations?stationTriplets=*:CO:{network}"
           f"&activeOnly={'true' if active_only else 'false'}")
    rows = []
    for s in get_json(url):
        net = s.get("networkCode")
        triplet = s.get("stationTriplet")
        if not triplet or net not in NETWORK_TO_SOURCE:
            continue
        rows.append({
            "source": NETWORK_TO_SOURCE[net],
            "site_id": triplet,
            "station_id": s.get("stationId"),
            "site_name": s.get("name"),
            "basin": huc_to_basin(s.get("huc")),
            "network": net,
            "huc": s.get("huc"),
            "elevation_ft": s.get("elevation"),
            "latitude": s.get("latitude"),
            "longitude": s.get("longitude"),
            "county": s.get("countyName"),
            "begin_date": (s.get("beginDate") or "")[:10] or None,
            "end_date": (s.get("endDate") or "")[:10] or None,
            "notes": f"{net} station",
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="include discontinued stations (deeper history)")
    args = ap.parse_args()
    active_only = not args.all

    rows = fetch_network("SNTL", active_only) + fetch_network("SNOW", active_only)
    # de-dup on (source, site_id); sort by source, basin, name
    seen, deduped = set(), []
    for r in rows:
        k = (r["source"], r["site_id"])
        if k not in seen:
            seen.add(k)
            deduped.append(r)
    deduped.sort(key=lambda r: (r["source"], r["basin"] or "zzz", r["site_name"] or ""))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(deduped)
    n_sntl = sum(r["source"] == "nrcs_snotel" for r in deduped)
    n_snow = sum(r["source"] == "nrcs_snowcourse" for r in deduped)
    print(f"wrote {OUT.name}: {len(deduped)} stations ({n_sntl} SNOTEL + {n_snow} snow course)")


if __name__ == "__main__":
    main()
