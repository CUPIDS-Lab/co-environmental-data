"""Tests for the shared cleanup orchestrator."""
import pandas as pd

from co_pipeline_core import clean as core

LONG = ["source", "vintage", "site_id", "datetime", "variable", "value", "unit", "qa_flag", "concept"]


class _Art:
    def __init__(self, path):
        self.local_path = path
        self.vintage = "current"
        self.url = "http://x"


class _Src:
    name = "s"
    license = "public domain"

    def __init__(self, arts, fail=False):
        self._arts = arts
        self._fail = fail

    def discover(self):
        return self._arts

    def ingest(self, art):
        if self._fail:
            raise ValueError("boom")
        return pd.DataFrame([{"source": "s", "vintage": "current", "site_id": "A",
                              "datetime": "2024-01-01", "variable": "v", "value": 1.0,
                              "unit": "u", "qa_flag": "", "concept": "c"}])


def _kw(tmp_path):
    return dict(discover=lambda s: s.discover(), audit_dir=tmp_path / "audit",
                processed_dir=tmp_path / "proc", canonical_csv=tmp_path / "proc" / "out.csv",
                provenance_csv=tmp_path / "proc" / "prov.csv", long_columns=LONG,
                validate=lambda df: df, key_id_col="site_id", parser_module_prefix="pkg")


def test_writes_data_and_provenance(tmp_path):
    f = tmp_path / "a.json"; f.write_text("{}")
    data, prov = core.run({"s": _Src([_Art(f)])}, **_kw(tmp_path))
    assert len(data) == 1 and len(prov) == 1
    assert prov.iloc[0]["extraction_quality"] == "clean"
    assert prov.iloc[0]["parser_module"] == "pkg.parsers.s"
    assert (tmp_path / "proc" / "out.csv").exists()


def test_parse_failure_is_durable(tmp_path):
    f = tmp_path / "a.json"; f.write_text("{}")
    data, prov = core.run({"s": _Src([_Art(f)], fail=True)}, **_kw(tmp_path))
    assert prov.iloc[0]["extraction_quality"] == "degraded"
    assert (tmp_path / "audit" / "extraction_errors.json").exists()


def test_fail_on_empty_raises(tmp_path):
    try:
        core.run({"s": _Src([])}, fail_on_empty=True, **_kw(tmp_path))
        assert False, "expected RuntimeError"
    except RuntimeError as e:
        assert "zero rows" in str(e)
