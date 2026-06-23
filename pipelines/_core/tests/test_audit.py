"""Tests for the shared audit profiling."""
import pandas as pd

from co_pipeline_core import audit as core


def test_profile_raw(tmp_path):
    orig = tmp_path / "original" / "src_a"
    orig.mkdir(parents=True)
    (orig / "x.json").write_text('{"a": 1, "b": 2}')
    audit = tmp_path / "audit"
    report = core.profile_raw(tmp_path / "original", audit)
    assert "Raw retrieval profile" in report and "`src_a`" in report
    assert list(audit.glob("raw-profile-*.md"))            # written


def test_profile_raw_empty(tmp_path):
    report = core.profile_raw(tmp_path / "original", tmp_path / "audit")
    assert "No raw files found" in report


def test_audit_processed_uses_entity_and_id_col(tmp_path):
    csv = tmp_path / "data.csv"
    pd.DataFrame([
        {"source": "s", "variable": "v", "site_id": "A", "datetime": "2024-01-01", "value": 1.0, "unit": "u"},
        {"source": "s", "variable": "v", "site_id": "B", "datetime": "2024-01-02", "value": 3.0, "unit": "u"},
    ]).to_csv(csv, index=False)
    audit = tmp_path / "audit"; audit.mkdir()
    report = core.audit_processed(csv, audit, id_col="site_id", entity="gages")
    assert "| source | variable | rows | gages | null values |" in report
    assert "Rows: **2**" in report
    assert list(audit.glob("summary-*.md"))
