"""Per-extract provenance sidecar (``data/processed/provenance.csv``).

Provenance is per-*extract* (one row per ``(source, vintage)`` query), not
per-row — carrying the source URL on every observation is wasteful. The processed
CSV joins to this sidecar on ``(source, vintage)``. This is what makes the dataset
defensible: anomaly → ``(source, vintage)`` → provenance row → ``source_url`` +
``sha256`` → the immutable original in ``data/original/``.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from climate_stations import config

PROVENANCE_COLUMNS = [
    "source", "vintage", "source_url", "retrieved_at", "sha256",
    "extraction_quality", "extraction_notes", "parser_module", "source_license",
]


@dataclass
class ProvenanceRecord:
    source: str
    vintage: str
    source_url: str
    retrieved_at: str          # ISO-8601 UTC
    sha256: str
    extraction_quality: str    # clean | caveats | degraded
    extraction_notes: str
    parser_module: str
    source_license: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def write(records: list[ProvenanceRecord], path: Path | None = None) -> Path:
    path = path or config.PROVENANCE_CSV
    df = pd.DataFrame([asdict(r) for r in records], columns=PROVENANCE_COLUMNS)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
