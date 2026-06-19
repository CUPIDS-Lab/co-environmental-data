"""The headless entrypoint (`python -m reservoir.pipeline`), offline demo path.

Exercises retrieve(demo) → audit → clean → publish end to end with the config
paths redirected to a tmp dir, so it runs with no network and leaves no
artifacts behind. Mirrors how test_fetch.py monkeypatches config paths."""
import reservoir.config as config
from reservoir import pipeline


def _redirect(monkeypatch, tmp_path):
    """Point every output path at a throwaway dir so the run is hermetic."""
    orig, proc, aud = tmp_path / "original", tmp_path / "processed", tmp_path / "audit"
    for name, val in {
        "ORIGINAL": orig, "PROCESSED": proc, "AUDIT": aud,
        "CANONICAL_CSV": proc / "reservoir-storage.csv",
        "PROVENANCE_CSV": proc / "provenance.csv",
        "MANIFEST": orig / "manifest.json",
    }.items():
        monkeypatch.setattr(config, name, val)


def test_demo_run_produces_csv_and_summary(monkeypatch, tmp_path):
    _redirect(monkeypatch, tmp_path)
    rc = pipeline.run(mode="demo", fresh=True, log=lambda *a, **k: None)
    assert rc == pipeline.EX_OK
    csv = config.CANONICAL_CSV
    assert csv.exists() and csv.read_text().count("\n") > 1          # header + ≥1 row
    assert (config.AUDIT / "summary-latest.md").exists()             # publish ran


def test_no_raw_files_aborts_before_clean(monkeypatch, tmp_path):
    _redirect(monkeypatch, tmp_path)
    # disable demo seeding → retrieve yields nothing → abort before clean, no CSV
    monkeypatch.setattr(pipeline, "_seed_demo", lambda: None)
    rc = pipeline.run(mode="demo", fresh=True, log=lambda *a, **k: None)
    assert rc == pipeline.EX_NO_RAW
    assert not config.CANONICAL_CSV.exists()


def test_main_parses_args(monkeypatch):
    captured = {}
    monkeypatch.setattr(pipeline, "run", lambda **kw: captured.update(kw) or 0)
    assert pipeline.main(["--mode", "demo", "--no-fresh",
                          "--sources", "dwr_cdss,reclamation_rise", "--no-publish"]) == 0
    assert captured["mode"] == "demo" and captured["fresh"] is False
    assert captured["sources"] == ["dwr_cdss", "reclamation_rise"]
    assert captured["do_publish"] is False
