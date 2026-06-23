"""Re-export the shared provenance module (lives in ``co_pipeline_core``).

Kept as a thin module so existing imports (``from snowpack import provenance``)
keep working unchanged; the implementation is shared across all pipelines.
"""
from co_pipeline_core.provenance import (  # noqa: F401  (intentional re-export)
    PROVENANCE_COLUMNS,
    ProvenanceRecord,
    sha256_file,
    write,
)
