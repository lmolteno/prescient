"""Persistence for SDO/HMI observations."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from prescient.models import HmiObservation as HmiObservationRow
from prescient.sources.sdo.image import SunHmiImage


class SdoRepository:
    """Reads and writes HMI observations through an :class:`AsyncSession`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, observation_time: dt.datetime, processed_time: dt.datetime, image: SunHmiImage
    ) -> None:
        stmt = (
            insert(HmiObservationRow)
            .values(
                observation_time=observation_time,
                processed_time=processed_time,
                umbra_contours=[c.model_dump(mode="json") for c in image.umbra],
                penumbra_contours=[c.model_dump(mode="json") for c in image.penumbra],
            )
            .on_conflict_do_nothing(index_elements=["observation_time"])
        )
        await self._session.execute(stmt)

    async def exists(self, observation_time: dt.datetime) -> bool:
        stmt = select(HmiObservationRow.id).where(
            HmiObservationRow.observation_time == observation_time
        )
        return (await self._session.scalar(stmt)) is not None

    async def read_range(
        self, start: dt.datetime, end: dt.datetime
    ) -> Sequence[HmiObservationRow]:
        stmt = (
            select(HmiObservationRow)
            .where(HmiObservationRow.observation_time.between(start, end))
            .order_by(HmiObservationRow.observation_time)
        )
        return (await self._session.scalars(stmt)).all()

    async def latest_time(self) -> dt.datetime | None:
        stmt = select(HmiObservationRow.observation_time).order_by(
            HmiObservationRow.observation_time.desc()
        )
        return await self._session.scalar(stmt)

    async def read_latest(self) -> HmiObservationRow | None:
        stmt = (
            select(HmiObservationRow)
            .order_by(HmiObservationRow.observation_time.desc())
        )
        return await self._session.scalar(stmt)
