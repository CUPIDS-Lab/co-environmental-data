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

## Review, persistence, and the Dataverse deposit

The canonical home for each refreshed dataset is a **Harvard Dataverse** dataset
(a citable DOI). Each pipeline carries a deposit kit at `pipelines/<pipeline>/dataverse/`
(`dataset.json`, `deposit-dataverse.sh`, `deposit_dataverse.py`, `DEPOSIT.md`),
generated from the `data-project-skill` (PR #7). Every monthly run:

1. writes the audit summary to the **Job Summary** so a human can scan
   row counts / coverage / reconcile at a glance,
2. uploads `data/processed/*.csv` + `data/audit/*` as a **workflow artifact**
   (90-day retention) — the recoverable deliverable, and
3. **validates the deposit kit** (`DRY_RUN=1`) so a broken citation manifest fails
   the run.

The actual deposit is **opt-in and draft-only** — it never mints/publishes a DOI
unattended (the skill's hard rule: a deposit stops at a draft for human review).
Set the repo variable `DATAVERSE_DEPOSIT=true` to have the monthly run upload the
fresh `data/processed` to a **draft** dataset; a maintainer reviews and publishes.

| Setting | Kind | Purpose |
|---|---|---|
| `DATAVERSE_DEPOSIT` | variable | `true` enables the draft-deposit step (default off → validate only) |
| `DATAVERSE_URL` | variable | installation, e.g. `https://dataverse.harvard.edu` (script default) |
| `DATAVERSE_COLLECTION` | variable | target collection alias — **must exist and be published** |
| `DATAVERSE_API_TOKEN` | secret | API token for the depositing account (treat like a password) |
| `CDSS_API_KEY` | secret | *(optional)* raises CO DWR/CDSS rate limits; the run works without it |

**First deposit vs. monthly versioning.** The kit's scripts *create* a draft dataset;
the first deposit mints v1.0 after a human publishes. Recurring monthly updates should
target that **existing** dataset (a new version, not a new DOI) — record its persistent
id and drive the idempotent update via the `data-project-depositor` agent. Until that is
configured, keep `DATAVERSE_DEPOSIT` off so the monthly job validates the kit without
creating draft clutter. See `pipelines/<pipeline>/dataverse/DEPOSIT.md`.

## Notes

- Cron is **UTC**. GitHub disables scheduled workflows after ~60 days of repo
  inactivity — fine while the project is active, worth knowing during quiet spells.
- `monthly-data-refresh.yml` requests only `contents: read` because outputs go to
  artifacts / Dataverse, not git. If you later choose to commit deliverables or
  open a data-review PR, bump it to `contents: write` (+ `pull-requests: write`).
