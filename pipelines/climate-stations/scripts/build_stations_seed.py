#!/usr/bin/env python3
"""Regenerate the curated climate-station seed `data/lookups/stations.csv`.

Pulls the CDSS climate-station catalog (~12,700 CO stations), keeps the ACTIVE
subset (period of record extends to/after --since), and down-selects a deterministic
cross-section: up to --per-network stations from each observing network (NOAA,
CoCoRaHS, NRCS, CoAgMet, NCWCD), spread across water divisions, so the committed seed
exercises every network and unit without pulling all 12,700. Full history is still
retrieved per retained station at pipeline time. Stdlib-only so it runs without the
package env.

  python scripts/build_stations_seed.py [--per-network 8] [--since 2024-01-01] [--all]

--all writes EVERY active station (the expandable "all stations" seed) instead of the
curated cross-section.
"""
import argparse
import csv
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

UA = "co-environmental-data/climate-stations (CUPIDS Lab; accounts@brianckeegan.com)"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "lookups" / "stations.csv"
BASE = "https://dwr.state.co.us/Rest/GET/api/v2/climatedata/climatestations"
COLUMNS = ["source", "site_id", "site_name", "network", "site_id_network",
           "division", "water_district", "county", "latitude", "longitude",
           "start_date", "end_date", "notes"]


def _cdss_key():
    p = ROOT / "dwr_api.json"
    try:
        if p.exists():
            d = json.loads(p.read_text())
            return d.get("CDSS_API_KEY") or d.get("api_key") or d.get("apiKey") or ""
    except Exception:
        pass
    return ""


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


# Normalize the network label: CDSS carries both "CoAgMet" and "COAGMET" for the
# agricultural mesonet — fold to one so it isn't double-counted.
NETWORK_FOLD = {"COAGMET": "CoAgMet"}


def _clean(s):
    """Unescape HTML entities (&NBSP;, &amp;), drop control bytes, collapse whitespace."""
    s = html.unescape(s or "").replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return "" if s in (";", "&", "-") else s


def to_row(r):
    net = (r.get("dataSource") or "").strip()
    return {
        "source": "cdss_climate",
        "site_id": str(r.get("stationNum")),
        "site_name": _clean(r.get("stationName")),
        "network": NETWORK_FOLD.get(net.upper(), net),
        "site_id_network": (r.get("siteId") or "").strip(),
        "division": r.get("division"),
        "water_district": r.get("waterDistrict"),
        "county": _clean(r.get("county")),
        "latitude": r.get("latitude"),
        "longitude": r.get("longitude"),
        "start_date": (r.get("startDate") or "")[:10],
        "end_date": (r.get("endDate") or "")[:10],
        "notes": "",
    }


def dedupe(rows):
    """Collapse multiple catalog records for one stationNum (POR segments / network
    casing) to a single row: widest period of record, a non-empty cleaned name."""
    by_id = {}
    for r in rows:
        cur = by_id.get(r["site_id"])
        if cur is None:
            by_id[r["site_id"]] = dict(r)
            continue
        cur["start_date"] = min(x for x in (cur["start_date"], r["start_date"]) if x) or ""
        cur["end_date"] = max(cur["end_date"], r["end_date"])
        if not cur["site_name"] and r["site_name"]:
            cur["site_name"] = r["site_name"]
        if not cur["site_id_network"] and r["site_id_network"]:
            cur["site_id_network"] = r["site_id_network"]
    return list(by_id.values())


def curate(rows, per_network, since):
    active = [r for r in rows if (r["end_date"] or "") >= since]
    by_net = {}
    for r in active:
        by_net.setdefault(r["network"], []).append(r)
    picks = []
    for net, grp in by_net.items():
        # spread across divisions: round-robin one station per division up to the cap
        by_div = {}
        for r in sorted(grp, key=lambda x: str(x["site_id"])):
            by_div.setdefault(r["division"], []).append(r)
        divs = sorted(by_div, key=lambda d: str(d))
        taken, i = [], 0
        while len(taken) < min(per_network, len(grp)) and any(by_div.values()):
            d = divs[i % len(divs)]
            if by_div[d]:
                taken.append(by_div[d].pop(0))
            i += 1
            if i > 10000:
                break
        picks.extend(taken)
    return picks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-network", type=int, default=8)
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--all", action="store_true", help="write every active station")
    args = ap.parse_args()

    key = _cdss_key()
    q = {"format": "json", "pageSize": 20000}
    if key:
        q["apiKey"] = key
    payload = get(f"{BASE}/?{urllib.parse.urlencode(q)}")
    rows = dedupe([to_row(r) for r in payload.get("ResultList", [])
                   if r.get("stationNum") is not None])
    print(f"catalog: {len(rows)} CO climate stations (deduped on stationNum)")

    if args.all:
        out = [r for r in rows if (r["end_date"] or "") >= args.since]
        print(f"--all: {len(out)} active stations (end >= {args.since})")
    else:
        out = curate(rows, args.per_network, args.since)
        nets = {}
        for r in out:
            nets[r["network"]] = nets.get(r["network"], 0) + 1
        print(f"curated cross-section: {len(out)} stations by network {nets}")

    out.sort(key=lambda r: (r["network"], str(r["division"]), str(r["site_id"])))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out)} rows")


if __name__ == "__main__":
    main()
