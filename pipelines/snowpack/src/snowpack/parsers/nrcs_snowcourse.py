"""Parser for NRCS snow course (network ``SNOW``) AWDB ``data`` responses.

Snow courses are manual surveys: SEMIMONTHLY values, each carrying
``{month, monthPart, year, collectionDate, value, ...}`` — the actual measurement
date is ``collectionDate`` (not ``date``). All the work is in the shared
:func:`snowpack.parsers._awdb.parse_awdb`; this module pins the source slug and the
``collectionDate`` value field.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from snowpack.parsers._awdb import parse_awdb
from snowpack.sources import Artifact


def parse(path: Path, artifact: Artifact) -> pd.DataFrame:
    return parse_awdb(path, artifact, source="nrcs_snowcourse", date_field="collectionDate")
