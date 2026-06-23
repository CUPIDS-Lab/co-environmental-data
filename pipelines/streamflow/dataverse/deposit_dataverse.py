#!/usr/bin/env python3
"""Deposit Colorado Stream/River Flow to a Dataverse repository using pyDataverse.

Creates a DRAFT dataset from dataset.json, uploads processed data / code /
documentation tagged by category, then OFFERS to publish (mint the DOI) behind an
explicit confirmation. Mirrors deposit-dataverse.sh but uses the official GDCC
client and validates the metadata before the network call.

    pip install pyDataverse
    DATAVERSE_API_TOKEN=xxxx python deposit_dataverse.py            # draft + upload, then prompt to publish
    DATAVERSE_API_TOKEN=xxxx python deposit_dataverse.py --publish  # pre-confirm publish
    python deposit_dataverse.py --no-publish                        # draft + upload only
    DRY_RUN=1 python deposit_dataverse.py                           # validate manifest + print actions, no network
    RESTRICT_DATA=1 ...                                             # upload data/ files as restricted

Test against https://demo.dataverse.org first. Publishing mints a DOI and is permanent.

This kit was generated from the CUPIDS Lab data-project skill (references/
dataverse-deposit.md). It lives in <pipeline>/dataverse/, so the project root —
where data/processed, src/, and the docs live — is this script's parent's parent.
"""
import json
import os
import sys
from pathlib import Path

BASE_URL = os.environ.get("DATAVERSE_URL", "https://dataverse.harvard.edu")
COLLECTION = os.environ.get("DATAVERSE_COLLECTION", "cupids-lab")  # ⚠️ confirm the real alias
TOKEN = os.environ.get("DATAVERSE_API_TOKEN", "")
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
RESTRICT_DATA = os.environ.get("RESTRICT_DATA", "0") == "1"

publish = "ask"
for arg in sys.argv[1:]:
    if arg == "--publish":
        publish = "yes"
    elif arg == "--no-publish":
        publish = "no"
    else:
        sys.exit("unknown argument: " + arg)

here = Path(__file__).resolve().parent          # <pipeline>/dataverse/
root = here.parent                              # <pipeline>/  (data/processed, src/, docs/)
manifest = here / "dataset.json"
sync = here / ".dataverse-deposit.json"
if not manifest.exists():
    sys.exit("missing dataset.json next to this script")
manifest_str = manifest.read_text(encoding="utf-8")


def validate_manifest(text: str) -> None:
    """Parse the citation manifest and confirm the Native-API-required fields are
    present, so a broken manifest fails fast (CI runs this every refresh)."""
    doc = json.loads(text)  # raises on invalid JSON
    fields = {f["typeName"]: f for f in
              doc["datasetVersion"]["metadataBlocks"]["citation"]["fields"]}
    required = ["title", "author", "datasetContact", "dsDescription", "subject"]
    missing = [r for r in required if r not in fields or not fields[r].get("value")]
    if missing:
        raise ValueError("dataset.json missing required citation field(s): " + ", ".join(missing))


validate_manifest(manifest_str)  # always — cheap, catches a broken manifest before any network call

if not DRY_RUN and not TOKEN:
    sys.exit("Set DATAVERSE_API_TOKEN (account menu -> API Token on %s)." % BASE_URL)

# What to deposit: (directory, category, directoryLabel, restrict)
DATA_DIRS = [
    (root / "data" / "processed", "Data", "data/processed", RESTRICT_DATA),
    (root / "src", "Code", "code", False),
    (root / "notebooks", "Code", "code", False),
    (root / "docs", "Documentation", "documentation", False),
    (root / "data" / "lookups", "Documentation", "data/lookups", False),
]
DOC_FILES = ["README.md", "AGENTS.md"]

print("Target: %s  collection: %s" % (BASE_URL, COLLECTION))

# Lazily import so DRY_RUN works without pyDataverse installed.
if not DRY_RUN:
    try:
        from pyDataverse.api import NativeApi
        from pyDataverse.models import Dataset, Datafile
    except ImportError:
        sys.exit("pyDataverse not installed. `pip install pyDataverse`, or use deposit-dataverse.sh (curl).")


def skip(path: Path) -> bool:
    """Don't deposit build/cache junk into an archival dataset."""
    parts = set(path.parts)
    return (path.name == ".gitkeep" or path.name.startswith(".")
            or path.suffix in {".pyc", ".pyo"}
            or "__pycache__" in parts or ".ipynb_checkpoints" in parts)


def upload_file(api, pid, path: Path, category, label, restrict):
    print("  + [%s] %s" % (category, path.name))
    if DRY_RUN:
        return
    df = Datafile()
    df.set({
        "pid": pid,
        "filename": str(path),
        "description": category + " file",
        "categories": [category],
        "directoryLabel": label,
        "restrict": restrict,
    })
    api.upload_datafile(pid, str(path), df.json())


def main():
    if DRY_RUN:
        print("DRY-RUN: manifest valid; POST %s/api/dataverses/%s/datasets (from dataset.json)"
              % (BASE_URL, COLLECTION))
        pid = "doi:10.5072/FK2/DRYRUN"
        api = None
    else:
        api = NativeApi(BASE_URL, TOKEN)
        ds = Dataset()
        try:
            ds.from_json(manifest_str)
            if not ds.validate_json():
                print("WARNING: dataset.json failed pyDataverse validation; check required citation fields.")
            metadata = ds.json()
        except Exception as exc:  # fall back to posting the manifest verbatim
            print("note: using dataset.json verbatim (%s)" % exc)
            metadata = manifest_str
        resp = api.create_dataset(COLLECTION, metadata)
        data = resp.json()
        if data.get("status") != "OK":
            sys.exit("create failed: " + json.dumps(data))
        pid = data["data"]["persistentId"]
    print("Draft dataset: %s" % pid)

    print("Uploading files...")
    for d, category, label, restrict in DATA_DIRS:
        if d.is_dir():
            for path in sorted(d.rglob("*")):
                if path.is_file() and not skip(path):
                    upload_file(api, pid, path, category, label, restrict)
    for doc in DOC_FILES:
        p = root / doc
        if p.is_file():
            upload_file(api, pid, p, "Documentation", "documentation", False)

    if not DRY_RUN:
        sync.write_text(json.dumps({
            "persistentId": pid,
            "url": "%s/dataset.xhtml?persistentId=%s" % (BASE_URL, pid),
        }, indent=2), encoding="utf-8")

    do_publish = publish
    if do_publish == "ask":
        if DRY_RUN:
            print("DRY-RUN: would offer to publish %s" % pid)
            do_publish = "no"
        elif sys.stdin.isatty():
            ans = input("Review the draft, then publish now and mint the DOI? [y/N] ")
            do_publish = "yes" if ans.strip().lower().startswith("y") else "no"
        else:
            print("Non-interactive: left as DRAFT. Review, then re-run with --publish.")
            do_publish = "no"
    if do_publish == "yes":
        print("Publishing %s (major, mints the DOI)..." % pid)
        if not DRY_RUN:
            api.publish_dataset(pid, release_type="major")
        print("Published: %s/dataset.xhtml?persistentId=%s" % (BASE_URL, pid))
    else:
        print("Left as DRAFT. Publish later: python %s --publish" % Path(__file__).name)


if __name__ == "__main__":
    main()
