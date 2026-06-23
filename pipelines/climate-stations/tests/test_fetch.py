"""Fetch progress rendering — pure functions, no network, no side effects."""
from climate_stations import fetch


def test_progress_messages_render():
    assert "fetching" in fetch._progress_message(
        {"phase": "start", "total": 10, "sources": ["cdss_climate"]})
    assert "cdss_climate" in fetch._progress_message(
        {"phase": "source", "source": "cdss_climate", "count": 5})
    tick = fetch._progress_message(
        {"phase": "tick", "done": 5, "total": 10, "fetched": 4,
         "no_data": 1, "errors": 0, "site": "Buckhorn"})
    assert "5/10" in tick and "50%" in tick and "Buckhorn" in tick
    assert "fetched" in fetch._progress_message(
        {"phase": "done", "fetched": 8, "no_data": 2, "errors": 0})


def test_callable_emitter_receives_raw_events():
    seen = []
    emit = fetch._make_emitter(seen.append)
    emit({"phase": "start", "total": 1, "sources": ["cdss_climate"]})
    assert seen and seen[0]["phase"] == "start"


def test_falsy_progress_is_silent():
    emit = fetch._make_emitter(False)
    assert emit({"phase": "start", "total": 1, "sources": []}) is None
