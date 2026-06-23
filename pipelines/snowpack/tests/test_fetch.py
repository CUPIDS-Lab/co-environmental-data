"""Fetch — progress rendering (pure) + the AWDB no-data path (404 → None) and the
empty-but-200 save path, exercised with a fake session (no network).
"""
from snowpack import fetch
from snowpack.sources import Artifact


def test_progress_messages():
    assert "fetching" in fetch._progress_message(
        {"phase": "start", "total": 5, "sources": ["nrcs_snotel", "nrcs_snowcourse"]})
    assert "nrcs_snotel" in fetch._progress_message(
        {"phase": "source", "source": "nrcs_snotel", "count": 3})
    tick = fetch._progress_message(
        {"phase": "tick", "done": 2, "total": 4, "fetched": 1, "no_data": 1,
         "errors": 0, "site": "Park Cone"})
    assert "2/4" in tick and "50%" in tick and "Park Cone" in tick
    assert "✓" in fetch._progress_message(
        {"phase": "done", "fetched": 4, "no_data": 1, "errors": 0})


class _Resp:
    def __init__(self, status, content=b"[]"):
        self.status_code = status
        self.content = content
        self.from_cache = True

    def raise_for_status(self):
        if self.status_code >= 400 and self.status_code != 404:
            raise RuntimeError(f"HTTP {self.status_code}")


class _Sess:
    def __init__(self, status):
        self._status = status

    def get(self, url, timeout=None):
        return _Resp(self._status)


def _art(tmp_path):
    return Artifact("nrcs_snotel", "current", "http://x",
                    tmp_path / "680_CO_SNTL.json", {"site_id": "680:CO:SNTL"})


def test_404_is_no_data(tmp_path):
    art = _art(tmp_path)
    assert fetch.fetch_artifact(_Sess(404), art) is None
    assert not art.local_path.exists()


def test_200_saves_even_when_empty(tmp_path):
    art = _art(tmp_path)
    path = fetch.fetch_artifact(_Sess(200), art)
    assert path == art.local_path and art.local_path.read_text() == "[]"
