"""Shared config helpers.

The per-pipeline ``config.py`` keeps its own path constants and ``get_sources()``
registry (those are the genuinely per-pipeline parts), but the duplicated *logic* —
the User-Agent string, the ``sources.yaml`` reader, and the CDSS API-key loader —
lives here so it is written once instead of copy-stamped four times.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def user_agent(pipeline: str) -> str:
    """The polite, descriptive User-Agent every pipeline sends."""
    return (f"co-environmental-data/{pipeline} (CUPIDS Lab; "
            "https://github.com/CUPIDS-Lab/co-environmental-data; accounts@brianckeegan.com)")


def read_sources_yaml(path: Path) -> dict:
    """Read a pipeline's ``data/lookups/sources.yaml`` (endpoints + per-source params)."""
    import yaml  # local import so byte-compilation works without the dep

    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_cdss_api_key(project_dir: Path) -> str:
    """Resolve the optional CDSS API key.

    Order: ``$CDSS_API_KEY``, else a git-ignored ``dwr_api.json`` (the pipeline root,
    then the repo root) holding ``{"CDSS_API_KEY": "..."}``. A malformed key file is
    non-fatal — fall through to keyless. Returns ``""`` when no key is found.
    """
    env = os.environ.get("CDSS_API_KEY", "")
    if env:
        return env
    project_dir = Path(project_dir)
    for candidate in (project_dir / "dwr_api.json", project_dir.parent.parent / "dwr_api.json"):
        try:
            if candidate.exists():
                data = json.loads(candidate.read_text())
                key = (data.get("CDSS_API_KEY") or data.get("api_key")
                       or data.get("apiKey") or data.get("key") or "")
                if key:
                    return key
        except Exception:
            pass  # malformed key file is non-fatal — fall through to keyless
    return ""
