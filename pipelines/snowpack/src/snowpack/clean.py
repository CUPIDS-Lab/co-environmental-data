"""Cleanup orchestrator: ingest every fetched artifact → tidy long → CSV.

Routes each source's saved responses through its parser, concatenates the
canonical frames, validates against the pandera schema, writes the deliverable
``data/processed/snowpack.csv`` plus the ``provenance.csv`` sidecar.

Errors are **durable, not fatal**: a parser that raises on one artifact appends
to ``data/audit/extraction_errors.json`` and the run continues, so one bad station
never empties the whole dataset. The notebook/CLI can pass ``fail_on_empty=True``
to turn a zero-row result (a silent layout regression) into a hard error.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd

from snowpack import config, provenance, schema


def _record_error(source: str, artifact_path: Path, err: Exception) -> None:
    errs_path = config.AUDIT / "extraction_errors.json"
    errs = json.loads(errs_path.read_text()) if errs_path.exists() else []
    errs.append({"source": source, "artifact": str(artifact_path),
                 "error": f"{type(err).__name__}: {err}",
                 "at": _dt.datetime.utcnow().isoformat() + "Z"})
    errs_path.parent.mkdir(parents=True, exist_ok=True)
    errs_path.write_text(json.dumps(errs, indent=2))


def run(*, sources: list[str] | None = None, sites: set[str] | None = None,
        fail_on_empty: bool = False, write: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ingest → concat → validate → write. Returns ``(data, provenance)`` frames."""
    # Fresh error log per run: _record_error appends, so reset here so the file
    # reflects only this run rather than accumulating stale failures across runs.
    errs_path = config.AUDIT / "extraction_errors.json"
    if errs_path.exists():
        errs_path.unlink()

    registry = config.get_sources()
    frames: list[pd.DataFrame] = []
    prov: list[provenance.ProvenanceRecord] = []
    now = _dt.datetime.utcnow().isoformat() + "Z"

    for slug, src in registry.items():
        if sources and slug not in sources:
            continue
        for art in src.discover(sites=sites):
            if not art.local_path.exists():
                continue  # not fetched yet — retrieve first
            try:
                frames.append(src.ingest(art))
                quality = "clean"
                notes = ""
            except Exception as err:  # durable, not fatal
                _record_error(slug, art.local_path, err)
                quality, notes = "degraded", f"parse failed: {type(err).__name__}"
            prov.append(provenance.ProvenanceRecord(
                source=slug, vintage=art.vintage, source_url=art.url,
                retrieved_at=now, sha256=provenance.sha256_file(art.local_path)
                if art.local_path.exists() else "",
                extraction_quality=quality, extraction_notes=notes,
                parser_module=f"snowpack.parsers.{slug}", source_license=src.license))

    data = (pd.concat(frames, ignore_index=True) if frames
            else pd.DataFrame(columns=schema.LONG_COLUMNS))
    if not data.empty:
        # de-duplicate on the composite key (idempotent re-pulls), keep last.
        data = (data.sort_values("datetime")
                .drop_duplicates(["source", "site_id", "datetime", "variable"], keep="last")
                .reset_index(drop=True))
        data = schema.validate(data)
    if fail_on_empty and data.empty:
        raise RuntimeError("clean.run produced zero rows — likely a layout/endpoint regression.")

    prov_df = pd.DataFrame([p.__dict__ for p in prov], columns=provenance.PROVENANCE_COLUMNS)
    if write:
        config.PROCESSED.mkdir(parents=True, exist_ok=True)
        data.to_csv(config.CANONICAL_CSV, index=False)
        prov_df.to_csv(config.PROVENANCE_CSV, index=False)
    return data, prov_df
