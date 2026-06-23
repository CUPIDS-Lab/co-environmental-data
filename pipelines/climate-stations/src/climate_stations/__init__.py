"""Colorado climate-station daily liberation pipeline.

Liberates daily climate-station observations — temperature (max/mean/min),
precipitation, snowfall / snow depth / snow water equivalent, pan evaporation,
solar radiation, vapor pressure, and wind run — for Colorado's ~12,700 climate
stations from the **CO DWR / CDSS** Climate Station Time Series (day) API into one
tidy long-format CSV. Implements issue #44 of the Colorado Environmental Data Hub.
Stamped out from the sibling ``streamflow`` pipeline (#10); same architecture
(immutable originals, per-source parser, a harmonized canonical schema with
documented caveats, reconciliation against truth) — different domain: one API,
many networks (NOAA COOP, CoCoRaHS, NRCS/SNOTEL, CoAgMet, NCWCD) and 12 daily
measurement types rather than two sources and a single variable.
"""
__version__ = "0.1.0"
