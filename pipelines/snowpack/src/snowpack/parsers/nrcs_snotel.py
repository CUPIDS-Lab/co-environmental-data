"""Parser for NRCS SNOTEL (network ``SNTL``) AWDB ``data`` responses.

SNOTEL is automated telemetry: DAILY values, each ``{date, value, qcFlag, qaFlag}``.
All the work is in the shared :func:`snowpack.parsers._awdb.parse_awdb`; this module
just pins the source slug and the ``date`` value field.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from snowpack.parsers._awdb import parse_awdb
from snowpack.sources import Artifact


def parse(path: Path, artifact: Artifact) -> pd.DataFrame:
    return parse_awdb(path, artifact, source="nrcs_snotel", date_field="date")
