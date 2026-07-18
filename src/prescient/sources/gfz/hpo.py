"""GFZ Hpo-index (Hp30/ap30) models and parsing.

Parses the GFZ Potsdam ``Hp30_ap30_nowcast.txt`` feed. The file has 30 header
lines (each starting with ``#``) followed by fixed-width, blank-separated data
lines with the columns::

    YYYY MM DD hh.h hh._m days days_m Hp30 ap30 D

where ``hh.h`` is the interval start time in hours UT. Missing data is flagged
with ``-1.000`` for Hp30 and ``-1`` for ap30; both become ``None`` here.

Both indices are unitless (Yamazaki et al. 2024, GFZ Data Services,
https://doi.org/10.5880/Hpo.0003).
"""

from __future__ import annotations

import datetime as dt

import structlog
from pydantic import BaseModel

log = structlog.get_logger(__name__)

_MISSING = -1.0


class HpoObservation(BaseModel):
    """A single 30-minute Hp30/ap30 observation."""

    time: dt.datetime  # start of the interval (UTC)
    hp30: float | None
    ap30: int | None


def parse_hpo(text: str) -> list[HpoObservation]:
    """Parse the Hp30/ap30 nowcast text into observations, skipping headers."""
    observations: list[HpoObservation] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) < 9:
            log.debug("hpo_short_line", line=line)
            continue
        try:
            year, month, day = int(fields[0]), int(fields[1]), int(fields[2])
            start_hours = float(fields[3])
            hp30 = float(fields[7])
            ap30 = int(fields[8])
        except ValueError:
            log.debug("hpo_unparseable_line", line=line)
            continue

        time = dt.datetime(year, month, day, tzinfo=dt.UTC) + dt.timedelta(
            hours=start_hours
        )
        observations.append(
            HpoObservation(
                time=time,
                hp30=None if hp30 <= _MISSING else hp30,
                ap30=None if ap30 < 0 else ap30,
            )
        )
    return observations
