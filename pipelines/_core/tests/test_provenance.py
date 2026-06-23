"""Tests for the shared provenance module."""
import pandas as pd

from co_pipeline_core import provenance
from co_pipeline_core.provenance import PROVENANCE_COLUMNS, ProvenanceRecord


def _rec(**kw):
    base = dict(source="src", vintage="current", source_url="http://x", retrieved_at="2026-01-01T00:00:00Z",
                sha256="abc", extraction_quality="clean", extraction_notes="", parser_module="m",
                source_license="public domain")
    base.update(kw)
    return ProvenanceRecord(**base)


def test_columns_match_dataclass_fields():
    # the CSV column order must match the dataclass fields (clean.py relies on this)
    assert PROVENANCE_COLUMNS == list(_rec().__dict__.keys())


def test_sha256_file(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"hello world")
    # sha256 of "hello world"
    assert provenance.sha256_file(f) == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_write_requires_explicit_path_and_round_trips(tmp_path):
    out = tmp_path / "sub" / "provenance.csv"
    returned = provenance.write([_rec(source="a"), _rec(source="b")], out)
    assert returned == out and out.exists()
    df = pd.read_csv(out)
    assert list(df.columns) == PROVENANCE_COLUMNS
    assert list(df["source"]) == ["a", "b"]
