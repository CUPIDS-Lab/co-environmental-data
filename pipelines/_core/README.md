# co-pipeline-core

Shared, domain-agnostic core for the Colorado Environmental Data Hub liberation
pipelines. The per-pipeline packages (`reservoir`, `streamflow`, `snowpack`,
`climate_stations`) were stamped from each other and had ~49% copy-paste
duplication (see `audits/after-action/2026-06-23-pipeline-deployments-aar.md` §4.1); this package
holds the plumbing once.

Each pipeline depends on it via a uv path dependency:

```toml
[project]
dependencies = ["co-pipeline-core", ...]

[tool.uv.sources]
co-pipeline-core = { path = "../_core", editable = true }
```

and re-exports / subclasses the shared modules, keeping only its domain logic
(`sources`, `parsers/`, `stations`, the `schema` vocabulary, `audit` extensions).

## Status

Extracted incrementally (issue [#54](https://github.com/CUPIDS-Lab/co-environmental-data/issues/54), **landed**), one
module per PR, proving each on one pipeline before rolling it to the rest:

- [x] `provenance` — per-extract sidecar dataclass + `sha256_file` + `write` (config-free)
- [x] `config` — shared config helpers (paths, run settings)
- [x] `schema` — `normalize_long` (day-floor timestamps, collapse duplicate keys to latest, long-form contract)
- [x] `fetch` — session + retry/backoff + throttled progress + per-artifact manifest
- [x] `clean` — cleanup orchestration
- [x] `audit` — shared profiling (base + per-pipeline hooks)
- [ ] `pipeline` CLI skeleton — **intentionally kept per-pipeline** (retrieve→publish orchestration is domain-specific)

All four pipelines (`reservoir`, `streamflow`, `snowpack`, `climate_stations`) now
depend on it via the uv path dependency above and run green against it; a change here
is exercised against every pipeline by the CI matrix.

It is **not** in the pipeline CI matrix (it is a library, excluded by
`.github/scripts/discover-pipelines.sh`); it has its own test job.

```bash
cd pipelines/_core && uv sync --extra dev && uv run pytest
```
