# co-pipeline-core

Shared, domain-agnostic core for the Colorado Environmental Data Hub liberation
pipelines. The per-pipeline packages (`reservoir`, `streamflow`, `snowpack`,
`climate_stations`) were stamped from each other and had ~49% copy-paste
duplication (see `retro/2026-06-23-pipeline-deployments-aar.md` §4.1); this package
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

Extracted incrementally (issue #54), one module per PR, proving each on one
pipeline before rolling to the rest:

- [x] `provenance` — per-extract sidecar dataclass + `sha256_file` + `write` (config-free)
- [ ] `config`, `schema`, `fetch`, `clean`, `pipeline`, `audit` (base + per-pipeline hooks)

It is **not** in the pipeline CI matrix (it is a library, excluded by
`.github/scripts/discover-pipelines.sh`); it has its own test job.

```bash
cd pipelines/_core && uv sync --extra dev && uv run pytest
```
