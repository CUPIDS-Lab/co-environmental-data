"""Shared core for the Colorado Environmental Data Hub liberation pipelines.

Domain-agnostic plumbing factored out of the per-pipeline packages
(`reservoir`, `streamflow`, `snowpack`, `climate_stations`) so it lives once
instead of being copy-stamped four times (AAR §4.1). Each pipeline depends on this
package via a uv path dependency (`[tool.uv.sources]`) and re-exports / subclasses
the shared modules, keeping only its domain logic (sources, parsers, stations,
schema vocabulary, audit extensions).

Modules are extracted incrementally; `provenance` is the first (issue #54).
"""
