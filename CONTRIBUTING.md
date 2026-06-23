# Contributing to Colorado Environmental Data Hub

Thanks for working on the Colorado Environmental Data Hub. This guide explains how to make changes here in a way that keeps the project reproducible, legible, and safe for the data it holds. Read `AGENTS.md` for the non-negotiables and `CODE_OF_CONDUCT.md` for community norms before you start. New contributors: the two `good-first-issue` catalog-hardening tasks ([#2](https://github.com/CUPIDS-Lab/co-environmental-data/issues/2), [#3](https://github.com/CUPIDS-Lab/co-environmental-data/issues/3)) are a good first landing.

## Environment setup

Reproducibility starts with a pinned environment so that another person — or another agent — gets the same results from the same inputs. The Hub uses **`uv`**, and each liberation pipeline under `pipelines/<name>/` is **self-contained** with its own pinned lockfile. Set up the pipeline you're working on, not the whole repo:

```bash
git clone https://github.com/CUPIDS-Lab/co-environmental-data.git
cd co-environmental-data/pipelines/reservoir-storage

uv sync                 # creates .venv from uv.lock — exact pinned versions
uv run pytest           # confirm the package + tests pass in the clean env
```

`uv sync` is the reproducibility contract: it installs the exact versions in `uv.lock`. If you add or upgrade a dependency, run `uv add <pkg>` (or edit `pyproject.toml`) **and commit the updated `uv.lock` in the same change**, so the lock and the code never drift apart. Do not rely on packages that only exist on your machine. The catalog itself needs no environment — it's a JSON file you can read directly.

## Branch, PR, and review workflow

Work on a branch named for the change, following the repo's convention of a kind prefix: `data/<slug>` for dataset work, `docs/<slug>` for documentation, `scaffold/<slug>` for structure, `fix/<slug>` for corrections (e.g. `data/2026-q3-reservoir-refresh`). Never commit directly to `main`. Open a pull request early, even as a draft, so others can see where the work is going before it hardens. Every PR needs a review from someone other than the author; `.github/CODEOWNERS` routes each path to the role responsible for it, so request the owner of the files you touched. Use `.github/PULL_REQUEST_TEMPLATE.md`. Keep PRs small and focused on one concern — a reviewer can reason about a tight change but not a sprawling one.

## Commit messages explain WHY

Write commit messages that explain the reasoning behind a change, not just the mechanics of it — the diff already shows *what* changed, so the message should capture *why* it changed and what tradeoff was accepted. A future maintainer reading `git log` should understand a filtering rule or a definition choice without having to reconstruct it. For non-obvious design or data decisions, also add a dated entry to `decision-log.md`; the commit explains the change, the decision log explains the project's choices over time.

## The pipeline is the shared artifact

The thing this project shares is the **re-runnable, text-based pipeline**, not a cleaned snapshot of the data. When an upstream source re-releases, sharing only the cleaned output guarantees redoing the work every vintage; sharing the pipeline means the next person regenerates the result — which is exactly how the **monthly CI refresh** works (a full rebuild that self-heals upstream revisions). Keep pipeline definitions legible to the subject-matter experts who need to read them, not only to developers, and treat each pipeline's derived data (its own `data/processed/`) as reproducible output rather than a source of truth.

## Notebooks are thin; logic lives in the package

Notebooks are playgrounds, not products. Each pipeline is **thin notebooks over a tested `src/<pkg>/` package** (`pipelines/reservoir-storage/` is the reference shape): explore in the notebook, then package the reusable parts into the `src/` module at the exploration boundary, so the project's logic lives in code that can be tested and re-run. Notebook outputs are stripped automatically by the repo's `.gitattributes` `nbstripout` filter — run `nbstripout --install` once per clone to activate it (clones without it simply skip stripping, no error), and check that no outputs snuck into the diff before you push.

## Keep secrets and sensitive data out of the repo

Credentials, tokens, and raw sensitive data never belong in version control, including inside notebook cells and their outputs. Read configuration and secrets from the environment or a git-ignored `.env`, and keep `.env.example` free of real values (API keys like `CDSS_API_KEY` or `DATAVERSE_API_TOKEN` are referenced by name, never inlined). This project will handle **conditionally sensitive-human** data once the news corpus ingests article text + journalist records: desensitize before anything leaves the controlled tier, follow the access tiers in `GOVERNANCE.md`, and complete the `responsible-data-checklist.md` before ingesting or sharing that data. Licensed-database exports (Nexis Uni, ProQuest, NewsBank, Factiva) are **restricted** and never committed — see `contributed-data-intake.md`.

## Discoverability is a feature

A data portal is poor at connecting people, so the burden of making this project and its contributors findable falls on its documentation. When you add a capability, update `README.md`, the relevant role in `ROLES.md`, and the schema in `DATA-DICTIONARY.md` (and the pipeline's own `docs/data-dictionary.md`) so the next person can find and reuse what you built. Treat documentation that has fallen behind the code as a bug.

## PR checklist

Before requesting review, confirm:

- [ ] Branched from `main` with a kind-prefixed name; the PR describes the change and *why* it was made.
- [ ] Derived data is regenerable from the pipeline's source APIs; nothing under a pipeline's `data/original/` (raw cache) or `data/lookups/` (committed seed) was edited in place.
- [ ] Reusable logic lives in `src/<pkg>/`; notebooks stay thin with outputs stripped.
- [ ] No secrets or sensitive data in the diff (code, config, or notebook outputs); no licensed-database content committed.
- [ ] `uv.lock` updated if dependencies changed; `uv run pytest` passes in a clean `uv sync` environment.
- [ ] Docs updated (`README.md`, the relevant `DATA-DICTIONARY.md`, `decision-log.md`, `CHANGELOG.md`) for any user-visible or non-obvious change.
- [ ] The right `.github/CODEOWNERS` reviewer is requested.
