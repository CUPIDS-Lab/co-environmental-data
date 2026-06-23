"""Tests for the shared config helpers."""
import json

from co_pipeline_core import config as core


def test_user_agent():
    ua = core.user_agent("snowpack")
    assert ua.startswith("co-environmental-data/snowpack ")
    assert "CUPIDS Lab" in ua and "accounts@brianckeegan.com" in ua


def test_read_sources_yaml(tmp_path):
    y = tmp_path / "sources.yaml"
    y.write_text("a:\n  base_url: http://x\n")
    assert core.read_sources_yaml(y) == {"a": {"base_url": "http://x"}}


def test_load_cdss_api_key_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CDSS_API_KEY", "from-env")
    assert core.load_cdss_api_key(tmp_path) == "from-env"


def test_load_cdss_api_key_from_file(monkeypatch, tmp_path):
    monkeypatch.delenv("CDSS_API_KEY", raising=False)
    (tmp_path / "dwr_api.json").write_text(json.dumps({"CDSS_API_KEY": "from-file"}))
    assert core.load_cdss_api_key(tmp_path) == "from-file"


def test_load_cdss_api_key_absent(monkeypatch, tmp_path):
    monkeypatch.delenv("CDSS_API_KEY", raising=False)
    assert core.load_cdss_api_key(tmp_path) == ""
