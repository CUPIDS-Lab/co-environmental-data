"""Fetch progress rendering — pure functions, no network, no side effects."""
from streamflow import fetch


def test_progress_messages_render():
    assert "fetching" in fetch._progress_message(
        {"phase": "start", "total": 10, "sources": ["usgs_nwis", "dwr_cdss"]})
    assert "usgs_nwis" in fetch._progress_message(
        {"phase": "source", "source": "usgs_nwis", "count": 5})
    tick = fetch._progress_message(
        {"phase": "tick", "done": 5, "total": 10, "fetched": 4,
         "no_data": 1, "errors": 0, "site": "Cameo"})
    assert "5/10" in tick and "50%" in tick and "Cameo" in tick
    assert "fetched" in fetch._progress_message(
        {"phase": "done", "fetched": 8, "no_data": 2, "errors": 0})


def test_callable_emitter_receives_raw_events():
    seen = []
    emit = fetch._make_emitter(seen.append)
    emit({"phase": "start", "total": 1, "sources": ["usgs_nwis"]})
    assert seen and seen[0]["phase"] == "start"


def test_falsy_progress_is_silent():
    emit = fetch._make_emitter(False)
    assert emit({"phase": "start", "total": 1, "sources": []}) is None
