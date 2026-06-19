"""Headless pipeline entrypoint — ``python -m reservoir.pipeline``.

Runs the four stages the notebook orchestrates (retrieve → audit → cleanup →
publish) without Jupyter, so CI can refresh the dataset on a schedule. This is a
thin CLI over ``fetch`` / ``audit`` / ``clean`` — **no new data logic**; the
notebook stays the human-facing narrative, this is its automatable twin.

Stages
------
1. retrieve   ``fetch.fetch_all`` (live) | offline 1-reservoir demo seed (``--mode demo``)
2. audit-raw  ``audit.profile_raw``     — did the fetch return data? (catches an
              empty/failed pull *before* it pollutes the deliverable)
3. clean      ``clean.run(fail_on_empty=…)`` → tidy CSV + provenance. The
              composite-key de-dup inside ``clean.run`` *is* the append: a full
              rebuild yields a superset of last month plus the new rows, and
              self-heals upstream revisions/backfills a pure append would miss.
4. audit      ``audit.audit_processed`` + ``coverage_report`` + ``variables_report``;
              ``reconcile`` is the optional accuracy gate (drift vs. the agency's
              own published totals).
5. publish    finalize the local deliverable + a stable-named ``summary-latest.md``
              the CI surfaces in the run. External publication (Dataverse) is a
              documented seam wired in the workflow — see ``.github/workflows``.

Exit codes
----------
0 ok · 1 clean produced zero rows (layout/endpoint regression) · 2 reconcile
mismatch · 3 retrieval produced no raw files (empty/failed live pull).
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from reservoir import audit, clean, config, fetch

# Exit codes (documented above; the workflow keys its failure handling off these).
EX_OK, EX_EMPTY, EX_RECONCILE, EX_NO_RAW = 0, 1, 2, 3


def _seed_demo() -> None:
    """Offline smoke path: seed one DWR fixture so ``clean`` has something to do
    (mirrors the notebook's demo cell). No network — lets CI exercise the whole
    retrieve→publish flow on every PR without hitting the live APIs."""
    registry = config.get_sources()
    fx = config.PROJECT_DIR / "tests" / "fixtures" / "dwr_cdss_storage_sample.json"
    art = next(a for a in registry["dwr_cdss"].discover()
               if a.metadata.get("reservoir_id") == "GRERESCO"
               and a.local_path.name.endswith("STORAGE.json"))
    art.local_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(fx, art.local_path)


def _raw_files() -> list[Path]:
    if not config.ORIGINAL.exists():
        return []
    return [p for p in config.ORIGINAL.rglob("*.json") if p.name != "manifest.json"]


def retrieve(*, mode: str, fresh: bool, sources: list[str] | None) -> int:
    """Stage 1. ``fresh`` clears ``data/original/`` first (full rebuild) so the
    CSV reflects exactly this run. Returns the raw-file count afterwards."""
    if fresh and config.ORIGINAL.exists():
        shutil.rmtree(config.ORIGINAL)
    config.ORIGINAL.mkdir(parents=True, exist_ok=True)
    if mode == "live":
        fetch.fetch_all(sources=sources)
    else:
        _seed_demo()
    return len(_raw_files())


def publish(summary: str) -> Path:
    """Stage 5 (local). Finalize a stable-named summary the CI surfaces in the
    run and uploads as an artifact. External publication to **Dataverse** is the
    canonical home but is intentionally wired in the workflow, not here, until
    the data-project-skill conventions land (see ``.github/workflows`` and the
    Dataverse seam there). Returns the summary path."""
    out = config.AUDIT / "summary-latest.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(summary)
    return out


def run(*, mode: str = "live", fresh: bool = True, sources: list[str] | None = None,
        fail_on_empty: bool = True, reconcile_expected: dict | None = None,
        do_publish: bool = True, log=print) -> int:
    """Run all stages. Returns a process exit code (see module docstring)."""
    log(f"[1/5] retrieve · mode={mode} fresh={fresh} sources={sources or 'all'}")
    n_raw = retrieve(mode=mode, fresh=fresh, sources=sources)
    log(f"      {n_raw} raw file(s) under {config.ORIGINAL}")
    if n_raw == 0:
        log("✗ retrieval produced no raw files — empty/failed pull; aborting before clean.")
        return EX_NO_RAW

    log("[2/5] audit-raw · profile_raw")
    audit.profile_raw()

    log(f"[3/5] clean · fail_on_empty={fail_on_empty}")
    try:
        data, _prov = clean.run(sources=sources, fail_on_empty=fail_on_empty)
    except RuntimeError as err:  # zero rows with fail_on_empty=True → loud failure
        log(f"✗ {err}")
        return EX_EMPTY
    log(f"      rows={len(data):,} reservoirs={data['reservoir_id'].nunique()} "
        f"→ {config.CANONICAL_CSV}")

    log("[4/5] audit · processed + coverage + variables"
        + (" + reconcile" if reconcile_expected else ""))
    summary = audit.audit_processed()
    audit.coverage_report()
    audit.variables_report()
    rc = EX_OK
    if reconcile_expected:
        res = audit.reconcile(reconcile_expected)
        bad = res[~res["match"]]
        if len(bad):
            log(f"✗ reconcile: {len(bad)} mismatch(es) — investigate before publishing.")
            rc = EX_RECONCILE
        else:
            log(f"      reconcile: all {len(res)} within tolerance ✓")

    if do_publish:
        log("[5/5] publish · finalize deliverable + summary-latest.md")
        publish(summary)
    else:
        log("[5/5] publish · skipped (--no-publish)")
    return rc


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m reservoir.pipeline",
        description="Headless reservoir-storage refresh (retrieve → audit → clean → publish).")
    p.add_argument("--mode", choices=["live", "demo"], default="live",
                   help="live = fetch the APIs (default); demo = offline 1-reservoir sample")
    fresh = p.add_mutually_exclusive_group()
    fresh.add_argument("--fresh", dest="fresh", action="store_true",
                       help="clear data/original first — full rebuild (default)")
    fresh.add_argument("--no-fresh", dest="fresh", action="store_false",
                       help="reuse the data/original cache (idempotent re-run)")
    p.add_argument("--sources", default=None,
                   help="comma-separated source slugs (e.g. dwr_cdss,reclamation_rise); default all")
    p.add_argument("--no-fail-on-empty", dest="fail_on_empty", action="store_false",
                   help="do not treat a zero-row result as a hard failure (default: fail)")
    p.add_argument("--no-publish", dest="do_publish", action="store_false",
                   help="run audit/clean but skip the publish finalize step")
    p.set_defaults(fresh=True, fail_on_empty=True, do_publish=True)
    args = p.parse_args(argv)
    sources = [s.strip() for s in args.sources.split(",")] if args.sources else None
    return run(mode=args.mode, fresh=args.fresh, sources=sources,
               fail_on_empty=args.fail_on_empty, do_publish=args.do_publish)


if __name__ == "__main__":
    raise SystemExit(main())
