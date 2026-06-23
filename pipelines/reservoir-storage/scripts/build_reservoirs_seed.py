#!/usr/bin/env python3
"""Enrich the curated reservoir seed `data/lookups/reservoirs.csv` with station
metadata (reproducible, in place — preserves the existing curated row set).

Adds latitude / longitude / elevation_ft / county / start_date / end_date:
  • dwr_cdss rows — joined by `abbrev` to the CDSS telemetrystation (STORAGE)
    catalog (coordinates, county, station period of record). The telemetrystation
    record has no elevation, so `elevation_ft` stays blank for CDSS rows — a
    reservoir's pool elevation is a measured variable (the ELEV series), not fixed
    station metadata.
  • reclamation_rise rows — resolved by name to a RISE `location`, whose
    `locationCoordinates` (a GeoJSON point) and `elevation` are fixed site metadata
    (county / POR are not exposed on the RISE location, so they stay blank).

This does NOT re-enumerate (so the curated 138-reservoir set is untouched); it only
fills the metadata columns. Idempotent — re-running rewrites the same columns.
Stdlib-only. Run: CDSS_API_KEY=… python scripts/build_reservoirs_seed.py
"""
import csv, json, os, time, urllib.parse, urllib.request
from pathlib import Path

UA = "co-environmental-data/reservoir (CUPIDS Lab; accounts@brianckeegan.com)"
ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "lookups" / "reservoirs.csv"
CDSS = "https://dwr.state.co.us/Rest/GET/api/v2"
RISE = "https://data.usbr.gov/rise/api"
NEW_COLS = ["latitude", "longitude", "elevation_ft", "county", "start_date", "end_date"]

def _cdss_key():
    if os.environ.get("CDSS_API_KEY"):
        return os.environ["CDSS_API_KEY"]
    p = ROOT / "dwr_api.json"
    try:
        if p.exists():
            d = json.loads(p.read_text())
            return d.get("CDSS_API_KEY") or d.get("api_key") or d.get("apiKey") or ""
    except Exception:
        pass
    return ""

CDSS_KEY = _cdss_key()


def get(url, jsonapi=False):
    headers = {"User-Agent": UA}
    if jsonapi:
        headers["Accept"] = "application/vnd.api+json"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def cdss_storage_meta():
    """abbrev -> {latitude, longitude, county, start_date, end_date} for STORAGE
    telemetry stations. The API's `parameter` filter is unreliable — filter here."""
    url = f"{CDSS}/telemetrystations/telemetrystation/?format=json&parameter=STORAGE&pageSize=50000"
    if CDSS_KEY:
        url += "&apiKey=" + urllib.parse.quote(CDSS_KEY, safe="")
    out = {}
    for r in get(url).get("ResultList", []) or []:
        if (r.get("parameter") or "") != "STORAGE":
            continue
        ab = r.get("abbrev")
        if not ab:
            continue
        out[ab] = {
            "latitude": r.get("latitude") or "",
            "longitude": r.get("longitude") or "",
            "county": (r.get("county") or "").strip().title(),
            "start_date": (r.get("stationPorStart") or "")[:10],
            "end_date": (r.get("stationPorEnd") or "")[:10],
        }
    return out


def _fmt_elev(v):
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else f"{f:.1f}"
    except (TypeError, ValueError):
        return ""


def _rise_id(ref):
    """Trailing numeric id from a JSON:API ref (``/rise/api/location/1533`` → ``1533``)."""
    return str(ref).rstrip("/").split("/")[-1]


def rise_meta(rise_item_ids):
    """Resolve a reservoir's fixed RISE location metadata via its stored item ids.

    RISE's `?search=` text filter is unreliable (returns an unfiltered list), so we
    use the EXACT relationship chain from the seed's confirmed item id:
    catalog-item → catalogRecord → location → locationCoordinates/elevation.
    """
    try:
        ids = json.loads(rise_item_ids) if rise_item_ids else {}
    except (TypeError, ValueError):
        ids = {}
    item = ids.get("storage_af") or ids.get("elevation_ft") or ids.get("release_cfs")
    if not item:
        return {}
    try:
        it = get(f"{RISE}/catalog-item/{_rise_id(item)}", jsonapi=True)
        rec = (it.get("data", {}).get("relationships", {}).get("catalogRecord", {}) or {}).get("data")
        if not rec:
            return {}
        cr = get(f"{RISE}/catalog-record/{_rise_id(rec['id'])}", jsonapi=True)
        loc = (cr.get("data", {}).get("relationships", {}).get("location", {}) or {}).get("data")
        if not loc:
            return {}
        attrs = get(f"{RISE}/location/{_rise_id(loc['id'])}", jsonapi=True).get("data", {}).get("attributes", {})
    except Exception as e:
        print("  RISE err", item, e)
        return {}
    coords = (attrs.get("locationCoordinates") or {}).get("coordinates") or []
    if len(coords) != 2:
        return {}
    return {"latitude": coords[1], "longitude": coords[0],
            "elevation_ft": _fmt_elev(attrs.get("elevation"))}


def main():
    rows = list(csv.DictReader(SEED.open()))
    src_cols = list(rows[0].keys()) if rows else []
    base = [c for c in src_cols if c not in NEW_COLS and c != "notes"]
    out_cols = base + NEW_COLS + (["notes"] if "notes" in src_cols else [])

    print("CDSS key:", bool(CDSS_KEY), "— fetching STORAGE telemetrystation catalog…")
    cdss = cdss_storage_meta()
    print(f"  {len(cdss)} STORAGE stations in catalog")

    n_dwr = n_rise = 0
    for row in rows:
        for c in NEW_COLS:
            row.setdefault(c, "")
        if row["source"] == "dwr_cdss":
            m = cdss.get(row["reservoir_id"])
            if m:
                row.update(m)
                n_dwr += 1
        elif row["source"] == "reclamation_rise":
            m = rise_meta(row.get("rise_item_ids"))
            if m:
                row.update(m)
                n_rise += 1
            time.sleep(0.2)

    with SEED.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=out_cols, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    n_dwr_total = sum(r["source"] == "dwr_cdss" for r in rows)
    n_rise_total = sum(r["source"] == "reclamation_rise" for r in rows)
    print(f"wrote {SEED.name}: {len(rows)} rows; "
          f"coordinates for {n_dwr}/{n_dwr_total} dwr_cdss + {n_rise}/{n_rise_total} rise")


if __name__ == "__main__":
    main()
