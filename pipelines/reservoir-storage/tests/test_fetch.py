"""Progress-reporting tests for fetch_all (the network parts aren't unit-tested,
but the message rendering + throttle/dispatch logic are pure and are)."""
from reservoir import fetch


def test_progress_messages_render():
    start = fetch._progress_message(
        {"phase": "start", "total": 331, "sources": ["dwr_cdss", "reclamation_rise"]})
    assert "331" in start and "dwr_cdss" in start and "reclamation_rise" in start

    assert "reclamation_rise" in fetch._progress_message(
        {"phase": "source", "source": "reclamation_rise", "count": 51})

    tick = fetch._progress_message(
        {"phase": "tick", "done": 33, "total": 330, "fetched": 30,
         "no_data": 2, "errors": 1, "reservoir": "Blue Mesa Reservoir"})
    assert "33/330" in tick and "10%" in tick and "Blue Mesa Reservoir" in tick

    done = fetch._progress_message(
        {"phase": "done", "fetched": 300, "no_data": 28, "errors": 3})
    assert done.startswith("✓") and "300" in done


def test_emitter_silent_and_callable():
    assert fetch._make_emitter(False)({"phase": "tick"}) is None     # silenced
    assert fetch._make_emitter(None)({"phase": "tick"}) is None
    events = []
    emit = fetch._make_emitter(events.append)                        # custom sink
    emit({"phase": "start", "total": 1, "sources": ["x"]})
    emit({"phase": "tick", "done": 1, "total": 1})
    assert [e["phase"] for e in events] == ["start", "tick"]


def test_fetch_all_reports_progress(monkeypatch, tmp_path):
    # exercise the real fetch_all control flow with the network stubbed out
    monkeypatch.setattr(fetch, "_session", lambda: None)
    monkeypatch.setattr(fetch, "fetch_artifact", lambda sess, art, force=False: None)
    monkeypatch.setattr(fetch.config, "MANIFEST", tmp_path / "manifest.json")
    monkeypatch.setattr(fetch.config, "AUDIT", tmp_path / "audit")

    events = []
    fetched = fetch.fetch_all(sources=["reclamation_rise"], progress=events.append)

    phases = [e["phase"] for e in events]
    assert phases[0] == "start" and phases[-1] == "done"
    assert "source" in phases and "tick" in phases
    assert fetched == [] and events[-1]["no_data"] >= 1   # every artifact returned no data
    assert events[0]["total"] == sum(1 for e in events if e["phase"] == "tick")


def test_emitter_throttles_ticks(monkeypatch):
    lines = []
    monkeypatch.setattr("builtins.print", lambda *a, **k: lines.append(" ".join(map(str, a))))
    clock = {"t": 1000.0}
    monkeypatch.setattr(fetch.time, "monotonic", lambda: clock["t"])
    emit = fetch._make_emitter(True)
    emit({"phase": "start", "total": 2, "sources": ["x"]})           # always prints
    emit({"phase": "tick", "done": 0, "total": 2, "fetched": 0, "no_data": 0, "errors": 0})  # throttled out
    clock["t"] += 5                                                  # past the interval
    emit({"phase": "tick", "done": 1, "total": 2, "fetched": 1, "no_data": 0, "errors": 0})  # prints
    assert sum("1/2" in ln for ln in lines) == 1
    assert any("fetching ~2" in ln for ln in lines)
