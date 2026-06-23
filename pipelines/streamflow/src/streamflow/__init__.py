"""Colorado stream/river flow liberation pipeline.

Liberates daily mean streamflow (discharge, cfs) for Colorado's major rivers from
two public sources — **USGS NWIS** (federal; the national gold standard) and
**CO DWR/CDSS surface water** (state) — into one tidy long-format CSV. Implements
issue #10 of the Colorado Environmental Data Hub. Stamped out from the sibling
``reservoir-storage`` pipeline (#9); same architecture, different domain.
"""
__version__ = "0.1.0"
