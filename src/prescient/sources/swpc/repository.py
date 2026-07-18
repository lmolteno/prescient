"""Persistence for SWPC regions and events."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from prescient.models import SolarEvent as SolarEventRow
from prescient.models import SolarRegion as SolarRegionRow
from prescient.sources.swpc.events import SolarEvent
from prescient.sources.swpc.regions import SolarRegionObservation


class SwpcRepository:
    """Reads and writes SWPC data through an :class:`AsyncSession`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- regions ---

    async def upsert_regions(self, observations: Sequence[SolarRegionObservation]) -> int:
        if not observations:
            return 0
        # Dedupe on the (observed_date, region) key, last wins, so one batch
        # never touches a conflicting row twice.
        deduped: dict[tuple[object, int], dict] = {}
        for o in observations:
            deduped[(o.observed_date, o.region)] = {
                "region": o.region,
                "observed_date": o.observed_date,
                "latitude": o.latitude,
                "longitude": o.longitude,
                "first_date": o.first_date,
                "region_metadata": o.metadata.model_dump(mode="json"),
            }
        rows = list(deduped.values())
        stmt = insert(SolarRegionRow).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_solar_region_date_region",
            set_={
                "latitude": stmt.excluded.latitude,
                "longitude": stmt.excluded.longitude,
                "first_date": stmt.excluded.first_date,
                "region_metadata": stmt.excluded.region_metadata,
            },
        )
        await self._session.execute(stmt)
        return len(rows)

    async def read_regions(
        self, start: dt.date, end: dt.date
    ) -> Sequence[SolarRegionRow]:
        stmt = (
            select(SolarRegionRow)
            .where(SolarRegionRow.observed_date.between(start, end))
            .order_by(SolarRegionRow.observed_date)
        )
        return (await self._session.scalars(stmt)).all()

    async def read_region(self, region_id: int) -> Sequence[SolarRegionRow]:
        stmt = (
            select(SolarRegionRow)
            .where(SolarRegionRow.region == region_id)
            .order_by(SolarRegionRow.observed_date)
        )
        return (await self._session.scalars(stmt)).all()

    # --- events ---

    async def upsert_events(self, events: Sequence[SolarEvent]) -> int:
        if not events:
            return 0
        # The feed can carry several rows that collapse to the same natural key
        # within one fetch (e.g. simultaneous multi-type sweep bursts). Postgres
        # rejects an ON CONFLICT batch that touches a row twice, so dedupe here,
        # keeping the last occurrence.
        deduped: dict[tuple[int, str, str, object], dict] = {}
        for e in events:
            key = (e.event_id, e.type.value, e.observatory.value, e.begin_datetime)
            deduped[key] = {
                "event_id": e.event_id,
                "type": e.type.value,
                "observatory": e.observatory.value,
                "region": e.region,
                "begin_datetime": e.begin_datetime,
                "max_datetime": e.max_datetime,
                "end_datetime": e.end_datetime,
                "details": e.model_dump(mode="json"),
            }
        rows = list(deduped.values())
        stmt = insert(SolarEventRow).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_solar_event_natural_key",
            set_={
                "region": stmt.excluded.region,
                "max_datetime": stmt.excluded.max_datetime,
                "end_datetime": stmt.excluded.end_datetime,
                "details": stmt.excluded.details,
            },
        )
        await self._session.execute(stmt)
        return len(rows)

    async def read_events(
        self, start: dt.datetime, end: dt.datetime
    ) -> Sequence[SolarEventRow]:
        stmt = (
            select(SolarEventRow)
            .where(SolarEventRow.begin_datetime.between(start, end))
            .order_by(SolarEventRow.begin_datetime)
        )
        return (await self._session.scalars(stmt)).all()

    async def read_region_events(self, region_id: int) -> Sequence[SolarEventRow]:
        stmt = (
            select(SolarEventRow)
            .where(SolarEventRow.region == region_id)
            .order_by(SolarEventRow.begin_datetime)
        )
        return (await self._session.scalars(stmt)).all()
