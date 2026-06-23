"""Cleanup orchestrator (thin wrapper over co_pipeline_core.clean).

The shared ingest → concat → validate → write logic lives in the core; this passes
the per-pipeline registry, discover signature, composite-key id column, and config
paths + schema.
"""
from __future__ import annotations

import pandas as pd

from co_pipeline_core import clean as _coreclean

from snowpack import config, schema


def run(*, sources: list[str] | None = None, sites: set[str] | None = None, fail_on_empty: bool = False,
        write: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ingest → concat → validate → write. Returns ``(data, provenance)`` frames."""
    return _coreclean.run(
        config.get_sources(),
        discover=lambda src: src.discover(sites=sites),
        sources=sources, fail_on_empty=fail_on_empty, write=write,
        audit_dir=config.AUDIT, processed_dir=config.PROCESSED,
        canonical_csv=config.CANONICAL_CSV, provenance_csv=config.PROVENANCE_CSV,
        long_columns=schema.LONG_COLUMNS, validate=schema.validate,
        key_id_col="site_id", parser_module_prefix="snowpack",
    )
