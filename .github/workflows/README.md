# CI/CD for `pipelines/`

Two workflows keep every dataset under [`pipelines/`](../../pipelines) healthy and
fresh. They share one contract so adding a pipeline is a one-line matrix edit.

| Workflow | Trigger | What it does |
|---|---|---|
| [`pipelines-ci.yml`](pipelines-ci.yml) | PRs / pushes touching `pipelines/**` | `uv sync --extra dev` → `uv run pytest` → an **offline demo** of the full retrieve→publish flow. The fast guardrail; no network, no secrets. |
| [`monthly-data-refresh.yml`](monthly-data-refresh.yml) | `cron: 0 9 1 * *` (1st of each month, 09:00 UTC) + manual dispatch | Gate on tests, then a **live full rebuild** per pipeline, surface the audit summary in the run, archive outputs, and (seam) publish to Dataverse. |

## The pipeline contract

Every pipeline directory exposes the same seams, so the workflows stay generic:

- a `pyproject.toml` so `uv sync --extra dev` and `uv run pytest` work;
- a headless entrypoint **`python -m <module>.pipeline`** that runs
  retrieve → audit → clean → audit/reconcile → publish and exits non-zero on a
  regression (see [`reservoir/pipeline.py`](../../pipelines/reservoir-storage/src/reservoir/pipeline.py));
- `data/processed/*.csv` as the deliverable and `data/audit/summary-latest.md`
  as the stable-named run summary.

## Adding a pipeline (e.g. streamflow #10, snowpack #11)

Add one row to the `matrix.include` in **both** workflows:

```yaml
include:
  - pipeline: reservoir-storage
    module: reservoir
  - pipeline: streamflow          # ← new
    module: streamflow
```

`fail-fast: false` isolates a failing pipeline from the rest. (A later
enhancement can auto-discover the matrix from `pipelines/*/pyproject.toml` so even
this edit goes away.)

## Why a full rebuild, not a windowed append

`clean.run()` de-dupes on the composite key `(source, reservoir_id, datetime,
variable)` keeping the last value — so re-pulling full history each month yields a
**superset** of last month plus the new rows (the append you want) and additionally
**self-heals** upstream QA revisions and backfills that a pure windowed append
would silently miss. Monthly cadence makes the cost acceptable. A windowed
incremental mode (fetch only `--start-date`'s window, merge into the prior CSV) is
a future optimization with a periodic full-rebuild safety net.

## Review & persistence (interim) and the Dataverse seam

The canonical home for each refreshed dataset is a **Dataverse** dataset. Until
that integration is wired (it depends on conventions coming from the
`data-project-skill` — dataset DOI, file layout, replace-vs-add version
semantics), the monthly run:

1. writes the audit summary to the **Job Summary** so a human can scan
   row counts / coverage / reconcile at a glance, and
2. uploads `data/processed/*.csv` + `data/audit/*` as a **workflow artifact**
   (90-day retention) — the recoverable interim deliverable.

The **Publish to Dataverse** step is scaffolded and **safely no-ops** until these
repository secrets are set, at which point its TODO body is replaced with the
upload call:

| Secret | Purpose |
|---|---|
| `DATAVERSE_BASE_URL` | Dataverse installation, e.g. `https://dataverse.harvard.edu` |
| `DATAVERSE_TOKEN` | API token for the publishing account |
| `DATAVERSE_DATASET_DOI` | Target dataset DOI, e.g. `doi:10.7910/DVN/XXXXXX` |
| `CDSS_API_KEY` | *(optional)* raises CO DWR/CDSS rate limits; the run works without it |

## Notes

- Cron is **UTC**. GitHub disables scheduled workflows after ~60 days of repo
  inactivity — fine while the project is active, worth knowing during quiet spells.
- `monthly-data-refresh.yml` requests only `contents: read` because outputs go to
  artifacts / Dataverse, not git. If you later choose to commit deliverables or
  open a data-review PR, bump it to `contents: write` (+ `pull-requests: write`).
