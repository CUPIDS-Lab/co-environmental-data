"""Per-source parsers: saved API response → canonical tidy-long frame.

One module per source slug (``usgs_nwis``, ``dwr_cdss``). Each exposes
``parse(path, artifact) -> DataFrame`` returning exactly ``schema.LONG_COLUMNS``,
already passed through ``schema.normalize_long`` (day-floored, deduped, validated).
"""
