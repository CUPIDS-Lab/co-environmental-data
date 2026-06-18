"""Per-source parsers. Each exposes ``parse(path, artifact) -> pd.DataFrame``
returning a frame that validates against ``reservoir.schema.CanonicalLong``.

One module per source (and per vintage band, if a source's response shape ever
changes mid-period). Resist a single universal parser — diagnosis-by-stage is
what the per-source split buys you.
"""
