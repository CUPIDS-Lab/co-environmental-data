# Summary

Describe what this PR changes and, more importantly, *why* — the diff already shows what changed, so use this space for the reasoning and any tradeoff you accepted. Keep the change focused on one concern so a reviewer can reason about it.

Closes #

## PR checklist

Before requesting review, confirm:

- [ ] Branched from `main`; the PR describes the change and *why* it was made.
- [ ] Nothing under `data/raw/` was edited in place; any derived data is regenerable from raw.
- [ ] No secrets or sensitive data in the diff (code, config, or notebook outputs).
- [ ] Docs updated (`README.md`, `DATA-DICTIONARY.md`, `decision-log.md`, `CHANGELOG.md`) for any user-visible or non-obvious change.
- [ ] Linked the issue this closes, and checked its definition-of-done.

<!-- Forward-looking (L2+): reusable logic in src/, notebooks in exploratory/ with outputs cleared, env/lockfile updated, results reproduce clean. -->
