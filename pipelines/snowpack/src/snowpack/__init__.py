"""Colorado snowpack (SWE) data-liberation pipeline.

Liberates Colorado snow water equivalent, snow depth, and water-year precipitation
accumulation from the NRCS AWDB REST API (SNOTEL + snow courses) into one tidy
long-format CSV. Issue #11 of the Colorado Environmental Data Hub; stamped out from
the sibling ``streamflow`` pipeline (#10). See ``AGENTS.md``.
"""
