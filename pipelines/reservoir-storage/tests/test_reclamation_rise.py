"""Parser test for USBR Reclamation RISE (JSON:API)."""
from pathlib import Path

from reservoir.parsers import reclamation_rise
from reservoir.sources import Artifact


def _artifact(path: Path) -> Artifact:
    return Artifact(
        source="reclamation_rise", vintage="current", url="https://example/rise",
        local_path=path,
        metadata={"reservoir_id": "blue-mesa", "reservoir_name": "Blue Mesa Reservoir",
                  "variable": "storage_af"},
    )


def test_parses_canonical_schema(fixtures_dir):
    fx = fixtures_dir / "reclamation_rise_storage_sample.json"
    df = reclamation_rise.parse(fx, _artifact(fx))
    assert len(df) == 3
    assert df["source"].unique().tolist() == ["reclamation_rise"]
    assert set(df["variable"]) == {"storage_af"}
    assert df["concept"].unique().tolist() == ["reservoir.storage_af"]


def test_known_value(fixtures_dir):
    fx = fixtures_dir / "reclamation_rise_storage_sample.json"
    df = reclamation_rise.parse(fx, _artifact(fx))
    latest = df.sort_values("datetime").iloc[-1]
    assert latest["value"] == 561800.0
    assert latest["unit"] == "acre-ft"
