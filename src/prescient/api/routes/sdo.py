"""SDO/HMI observation endpoints."""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel

from prescient.api.deps import SessionDep
from prescient.models import HmiObservation
from prescient.sources.sdo.repository import SdoRepository

router = APIRouter(prefix="/sdo", tags=["sdo"])


class HmiObservationResponse(BaseModel):
    id: int
    observed: dt.datetime
    processed: dt.datetime
    umbra_contours: list[list[list[float]]]
    penumbra_contours: list[list[list[float]]]

    @classmethod
    def from_row(cls, row: HmiObservation) -> HmiObservationResponse:
        return cls(
            id=row.id,
            observed=row.observation_time,
            processed=row.processed_time,
            umbra_contours=[c["coordinates"] for c in row.umbra_contours],
            penumbra_contours=[c["coordinates"] for c in row.penumbra_contours],
        )


@router.get("/hmi", response_model=list[HmiObservationResponse])
async def get_hmi(
    session: SessionDep,
    start: Annotated[dt.datetime, Query(description="Inclusive start datetime (UTC).")],
    end: Annotated[dt.datetime, Query(description="Inclusive end datetime (UTC).")],
) -> list[HmiObservationResponse]:
    rows = await SdoRepository(session).read_range(start, end)
    return [HmiObservationResponse.from_row(r) for r in rows]


@router.get(
    "/hmi/latest",
    response_model=HmiObservationResponse,
    responses={status.HTTP_204_NO_CONTENT: {"description": "No observations yet."}},
)
async def get_hmi_latest(session: SessionDep) -> HmiObservationResponse | Response:
    row = await SdoRepository(session).read_latest()
    if row is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return HmiObservationResponse.from_row(row)
