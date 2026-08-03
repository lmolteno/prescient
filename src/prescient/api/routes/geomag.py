"""Geomagnetic index (GFZ Hp30/ap30) endpoints."""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel

from prescient.api.deps import SessionDep
from prescient.sources.gfz.repository import GfzRepository

router = APIRouter(prefix="/geomag", tags=["geomag"])


class Hp30Response(BaseModel):
    time: dt.datetime
    hp30: float | None
    ap30: int | None


@router.get("/hp30", response_model=list[Hp30Response])
async def get_hp30(
    session: SessionDep,
    start: Annotated[dt.datetime, Query(description="Inclusive start datetime (UTC).")],
    end: Annotated[dt.datetime, Query(description="Inclusive end datetime (UTC).")],
) -> list[Hp30Response]:
    rows = await GfzRepository(session).read_hp30(start, end)
    return [Hp30Response.model_validate(r, from_attributes=True) for r in rows]


@router.get(
    "/hp30/latest",
    response_model=Hp30Response,
    responses={status.HTTP_204_NO_CONTENT: {"description": "No observations yet."}},
)
async def get_hp30_latest(session: SessionDep) -> Hp30Response | Response:
    row = await GfzRepository(session).read_latest_hp30()
    if row is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return Hp30Response.model_validate(row, from_attributes=True)
