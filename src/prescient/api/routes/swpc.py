"""SWPC region and event endpoints."""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from prescient.api.deps import SessionDep
from prescient.sources.swpc.regions import SolarRegionMetadata
from prescient.sources.swpc.repository import SwpcRepository

router = APIRouter(prefix="/swpc", tags=["swpc"])


class RegionResponse(BaseModel):
    id: int
    region: int
    observed_date: dt.date
    first_date: dt.datetime
    latitude: int
    longitude: int
    metadata: SolarRegionMetadata


class EventResponse(BaseModel):
    id: int
    event_id: int
    type: str
    observatory: str
    region: int | None
    begin_datetime: dt.datetime
    max_datetime: dt.datetime | None
    end_datetime: dt.datetime | None
    details: dict


@router.get("/region", response_model=list[RegionResponse])
async def get_regions(
    session: SessionDep,
    start: Annotated[dt.date, Query(description="Inclusive start date (UTC).")],
    end: Annotated[dt.date, Query(description="Inclusive end date (UTC).")],
) -> list[RegionResponse]:
    rows = await SwpcRepository(session).read_regions(start, end)
    return [
        RegionResponse(
            id=r.id,
            region=r.region,
            observed_date=r.observed_date,
            first_date=r.first_date,
            latitude=r.latitude,
            longitude=r.longitude,
            metadata=SolarRegionMetadata.model_validate(r.region_metadata),
        )
        for r in rows
    ]


@router.get("/region/{region_id}", response_model=list[RegionResponse])
async def get_region(session: SessionDep, region_id: int) -> list[RegionResponse]:
    rows = await SwpcRepository(session).read_region(region_id)
    return [
        RegionResponse(
            id=r.id,
            region=r.region,
            observed_date=r.observed_date,
            first_date=r.first_date,
            latitude=r.latitude,
            longitude=r.longitude,
            metadata=SolarRegionMetadata.model_validate(r.region_metadata),
        )
        for r in rows
    ]


@router.get("/event", response_model=list[EventResponse])
async def get_events(
    session: SessionDep,
    start: Annotated[dt.datetime, Query(description="Inclusive start datetime (UTC).")],
    end: Annotated[dt.datetime, Query(description="Inclusive end datetime (UTC).")],
) -> list[EventResponse]:
    rows = await SwpcRepository(session).read_events(start, end)
    return [EventResponse.model_validate(r, from_attributes=True) for r in rows]


@router.get("/region/{region_id}/event", response_model=list[EventResponse])
async def get_region_events(session: SessionDep, region_id: int) -> list[EventResponse]:
    rows = await SwpcRepository(session).read_region_events(region_id)
    return [EventResponse.model_validate(r, from_attributes=True) for r in rows]
