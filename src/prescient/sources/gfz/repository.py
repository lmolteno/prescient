"""Persistence for GFZ Hpo-index observations."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from prescient.models import HpoIndex as HpoIndexRow
from prescient.sources.gfz.hpo import HpoObservation


class GfzRepository:
    """Reads and writes Hpo-index data through an :class:`AsyncSession`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_hp30(self, observations: Sequence[HpoObservation]) -> int:
        if not observations:
            return 0
        # Dedupe on the interval start time (last wins) so one batch never
        # touches a conflicting row twice.
        deduped: dict[dt.datetime, dict] = {
            o.time: {"time": o.time, "hp30": o.hp30, "ap30": o.ap30}
            for o in observations
        }
        rows = list(deduped.values())
        stmt = insert(HpoIndexRow).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["time"],
            set_={"hp30": stmt.excluded.hp30, "ap30": stmt.excluded.ap30},
        )
        await self._session.execute(stmt)
        return len(rows)

    async def read_hp30(
        self, start: dt.datetime, end: dt.datetime
    ) -> Sequence[HpoIndexRow]:
        stmt = (
            select(HpoIndexRow)
            .where(HpoIndexRow.time.between(start, end))
            .order_by(HpoIndexRow.time)
        )
        return (await self._session.scalars(stmt)).all()

    async def read_latest_hp30(self) -> HpoIndexRow | None:
        stmt = select(HpoIndexRow).order_by(HpoIndexRow.time.desc())
        return await self._session.scalar(stmt)
