"""Per-source parsers: saved AWDB response → canonical tidy-long frame.

One module per source slug (``nrcs_snotel``, ``nrcs_snowcourse``). Each exposes
``parse(path, artifact) -> DataFrame`` returning exactly ``schema.LONG_COLUMNS``,
already passed through ``schema.normalize_long`` (day-floored, deduped, validated).

Both sources are the SAME AWDB response shape, differing only in the per-value
date field (SNOTEL ``date`` vs snow-course ``collectionDate``) and duration — so
the real work lives in the shared :mod:`snowpack.parsers._awdb` helper and the two
modules are thin adapters that pin the source slug + date field.
"""
