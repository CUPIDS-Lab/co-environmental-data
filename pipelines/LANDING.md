# Landing a pipeline

The ordered, **one-PR** procedure for taking a built data-liberation pipeline from a
working directory to a registered, tested, tracked dataset on `main`. It exists
because the first four pipelines landed four different ways — one was bundled
invisibly into a governance PR (#37), one swept another agent's untracked files
(#45→#46), one registered its CI row before its code and reded `main` (#47→#48). See
`retro/2026-06-23-pipeline-deployments-aar.md` §4.4–4.5.

Follow this and a pipeline lands as a single, reviewable, correctly-ordered,
issue-closing PR.

## 0. Before you start

- There is a tracking issue for the pipeline (a sub-issue of the water/climate epic
  #7). If not, open one first.
- Work in an **isolated worktree off freshly-fetched `origin/main`** and stage
  **explicit paths** — never `git add -A` (see the repo `AGENTS.md` → *Working in a
  shared tree with other agents*):
  ```bash
  git fetch && git worktree add -b data/<name>-pipeline /tmp/<name> origin/main
  ```

## 1. Build the pipeline (its own directory)

Stamp from the closest sibling under `pipelines/<name>/`:
`src/<module>/` (schema · config · sources · fetch · clean · audit · stations ·
provenance · parsers/ · pipeline CLI) · `tests/` (offline, fixtures from trimmed
real responses) · `data/lookups/` (the committed seed) · `docs/` · `pyproject.toml`
· `README.md` · `AGENTS.md` · `notebooks/` · a `.gitignore` covering
`*.requests-cache.sqlite*`, `dwr_api.json`, `*.api.json`, `.venv/`, `data/{original,processed,audit}/*`.

Verify offline before going further:
```bash
cd pipelines/<name> && uv sync && uv run pytest -q
uv run python -m <module>.pipeline --mode demo --fresh
```

## 2. CI — nothing to edit

The CI matrix is **auto-discovered** from `pipelines/*/pyproject.toml`
(`.github/scripts/discover-pipelines.sh`); a new `pipelines/<name>/` with a
`pyproject.toml` and a `src/<module>/` is tested + monthly-refreshed automatically.
Do **not** hand-edit a matrix row (that ordering hazard is gone). CI also gates the
README test count — keep `N tests` in the README accurate (or omit the number).

## 3. Dataverse kit

Add `pipelines/<name>/dataverse/` (stamp a sibling): `dataset.json` (domain title /
description / keywords), `DEPOSIT.md`, `deposit-dataverse.sh`, `deposit_dataverse.py`.
Validate: `DRY_RUN=1 uv run python dataverse/deposit_dataverse.py --no-publish`.

## 4. Register the pipeline across the repo docs

Registration is a **projection** — the repo's prose must agree with the built state.
Update each of these (grep the count phrases afterward to confirm none are stale):

- [ ] `README.md` — add the `## Pipelines` bullet; bump the pipeline count.
- [ ] `AGENTS.md` — add to the "N are built" list (Where things are + How we work).
- [ ] `ROADMAP.md` — the epic tracking-table row + the epic blockquote sub-issue clause.
- [ ] `CHANGELOG.md` — a `### Added` entry.
- [ ] `data-management-plan.md` — the "(N present)" liberated-datasets bullet.
- [ ] `data-card.md` — add it to the Datasets list + Composition.
- [ ] `.github/wiki-seeds/Home.md` — the built-pipelines sentence.

(Acceptance for the whole set: `grep -rIn "N are built\|N present"` shows the new
count everywhere, and the new pipeline is named in each file.)

## 5. One PR → CI green → merge → verify

```bash
git add pipelines/<name> README.md AGENTS.md ROADMAP.md CHANGELOG.md \
        data-management-plan.md data-card.md .github/wiki-seeds/Home.md
git commit -m "Add <name> pipeline (#NN)"   # body ends with: Closes #NN
git push -u origin data/<name>-pipeline
gh pr create --base main --title "Add <name> pipeline (#NN)" --body "...Closes #NN"
```

- One concern per PR — the pipeline + its registration only. Never bundle into a
  docs/governance PR.
- Wait for **all** CI jobs green; then **`git fetch` and verify `origin/main`**
  (the ground moves) and squash-merge.
- `Closes #NN` closes the tracking issue on merge (issue rule: *closed when built +
  registered*; the first Dataverse publish is tracked separately by #36).
- Clean up: delete the remote branch and `git worktree remove`.

## 6. After merge

- Confirm `origin/main` shows the pipeline tracked, in CI (the `discover` job lists
  it), and registered (the doc counts match).
- If anything in steps 3–4 was deferred, the tracking issue stays open with the
  residue named — never a silent gap.
