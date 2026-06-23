"""Shared cleanup orchestrator: ingest fetched artifacts → tidy long → CSV.

Routes each source's saved responses through its parser, concatenates the
canonical frames, validates against the pipeline's schema, and writes the
deliverable CSV plus the ``provenance.csv`` sidecar. Errors are **durable, not
fatal**: a parser that raises on one artifact appends to
``data/audit/extraction_errors.json`` and the run continues, so one bad entity
never empties the whole dataset.

The per-pipeline ``clean.py`` is a thin wrapper that passes its registry, the
``discover`` call (whose signature differs — ``sites`` / ``meas_types`` / none),
the composite-key id column, the parser-module prefix, and its config paths +
schema. The orchestration logic lives here, written once.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Callable

import pandas as pd

from co_pipeline_core import provenance


def _record_error(audit_dir: Path, source: str, artifact_path: Path, err: Exception) -> None:
    errs_path = Path(audit_dir) / "extraction_errors.json"
    errs = json.loads(errs_path.read_text()) if errs_path.exists() else []
    errs.append({"source": source, "artifact": str(artifact_path),
                 "error": f"{type(err).__name__}: {err}",
                 "at": _dt.datetime.utcnow().isoformat() + "Z"})
    errs_path.parent.mkdir(parents=True, exist_ok=True)
    errs_path.write_text(json.dumps(errs, indent=2))


def run(registry: dict, *, discover: Callable, audit_dir: Path, processed_dir: Path,
        canonical_csv: Path, provenance_csv: Path, long_columns: list[str],
        validate: Callable[[pd.DataFrame], pd.DataFrame], key_id_col: str,
        parser_module_prefix: str, sources: list[str] | None = None,
        fail_on_empty: bool = False, write: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ingest → concat → validate → write. Returns ``(data, provenance)`` frames.

    ``discover(src)`` yields a source's artifacts (the pipeline supplies it so the
    differing ``discover()`` signatures stay per-pipeline).
    """
    audit_dir = Path(audit_dir)
    # Fresh error log per run: _record_error appends, so reset here.
    errs_path = audit_dir / "extraction_errors.json"
    if errs_path.exists():
        errs_path.unlink()

    frames: list[pd.DataFrame] = []
    prov: list[provenance.ProvenanceRecord] = []
    now = _dt.datetime.utcnow().isoformat() + "Z"

    for slug, src in registry.items():
        if sources and slug not in sources:
            continue
        for art in discover(src):
            if not art.local_path.exists():
                continue  # not fetched yet — retrieve first
            try:
                frames.append(src.ingest(art))
                quality = "clean"
                notes = ""
            except Exception as err:  # durable, not fatal
                _record_error(audit_dir, slug, art.local_path, err)
                quality, notes = "degraded", f"parse failed: {type(err).__name__}"
            prov.append(provenance.ProvenanceRecord(
                source=slug, vintage=art.vintage, source_url=art.url,
                retrieved_at=now, sha256=provenance.sha256_file(art.local_path)
                if art.local_path.exists() else "",
                extraction_quality=quality, extraction_notes=notes,
                parser_module=f"{parser_module_prefix}.parsers.{slug}", source_license=src.license))

    data = (pd.concat(frames, ignore_index=True) if frames
            else pd.DataFrame(columns=long_columns))
    if not data.empty:
        # de-duplicate on the composite key (idempotent re-pulls), keep last.
        data = (data.sort_values("datetime")
                .drop_duplicates(["source", key_id_col, "datetime", "variable"], keep="last")
                .reset_index(drop=True))
        data = validate(data)
    if fail_on_empty and data.empty:
        raise RuntimeError("clean.run produced zero rows — likely a layout/endpoint regression.")

    prov_df = pd.DataFrame([p.__dict__ for p in prov], columns=provenance.PROVENANCE_COLUMNS)
    if write:
        Path(processed_dir).mkdir(parents=True, exist_ok=True)
        data.to_csv(canonical_csv, index=False)
        prov_df.to_csv(provenance_csv, index=False)
    return data, prov_df
