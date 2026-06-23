"""Tests for the shared fetch plumbing."""
from co_pipeline_core import fetch as core


class _Resp:
    def __init__(self, status):
        self.status_code = status


class _Sess:
    def __init__(self, status):
        self._status = status
        self.calls = 0

    def get(self, url, timeout=None):
        self.calls += 1
        return _Resp(self._status)


def test_get_with_retry_passes_through_non_retry_status():
    s = _Sess(404)
    r = core.get_with_retry(s, "http://x", max_retries=3, timeout=5, retry_codes=(429, 503))
    assert r.status_code == 404 and s.calls == 1   # 404 not in retry_codes → no retry


def test_get_with_retry_retries_then_reraises_on_retry_code():
    s = _Sess(503)
    try:
        core.get_with_retry(s, "http://x", max_retries=3, timeout=5, retry_codes=(429, 503))
        assert False, "expected RateLimited"
    except core.RateLimited:
        assert s.calls == 3   # retried up to max_retries


def test_make_emitter_silent_and_callable():
    assert core.make_emitter(False, lambda ev: "x")({"phase": "start"}) is None
    seen = []
    emit = core.make_emitter(lambda ev: seen.append(ev), lambda ev: "x")
    emit({"phase": "tick"})
    assert seen == [{"phase": "tick"}]


def test_make_emitter_throttled_uses_render(capsys):
    emit = core.make_emitter(True, lambda ev: f"RENDERED {ev['phase']}")
    emit({"phase": "start"})
    out = capsys.readouterr().out
    assert "RENDERED start" in out
