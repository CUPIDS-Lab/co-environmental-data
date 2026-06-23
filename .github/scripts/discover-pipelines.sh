#!/usr/bin/env bash
# Discover the data-liberation pipelines for the CI matrix.
#
# Emits one matrix row per directory under pipelines/ that (a) has a pyproject.toml
# and (b) is NOT the shared `_core` library. `module` is the importable package
# name (the single dir under src/). Output is a `matrix=<json>` line suitable for
# appending to $GITHUB_OUTPUT, consumed downstream via fromJson().
#
# This replaces the hand-maintained matrix.include in both workflows: a new pipeline
# is covered automatically (no workflow edit), and a matrix row can never reference a
# directory that doesn't exist on main (the PR #47 ordering hazard). See AAR §4.3.
set -euo pipefail

rows=()
for d in pipelines/*/; do
  name="$(basename "$d")"
  [ "$name" = "_core" ] && continue              # shared library — its own job, not a pipeline
  [ -f "${d}pyproject.toml" ] || continue
  pkg="$(basename "$(ls -d "${d}"src/*/ 2>/dev/null | head -1)")"
  [ -n "$pkg" ] || continue
  rows+=("{\"pipeline\":\"$name\",\"module\":\"$pkg\"}")
done

IFS=,
echo "matrix={\"include\":[${rows[*]}]}"
