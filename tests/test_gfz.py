"""Tests for the GFZ Hp30/ap30 source."""

from __future__ import annotations

import datetime as dt

import httpx
import respx
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from prescient.sources.gfz.client import GfzClient
from prescient.sources.gfz.hpo import parse_hpo
from prescient.sources.gfz.repository import GfzRepository

SAMPLE = """\
# PURPOSE: This file distributes the Hp30 index and ap30 index
# 30 header lines, all starting with #
#YYY MM DD hh.h hh._m        days      days_m   Hp30 ap30 D
2026 06 19 00.0 00.25 34503.00000 34503.01042  3.000   15 0
2026 06 19 00.5 00.75 34503.02083 34503.03125  3.333   18 0
2026 06 19 01.0 01.25 34503.04167 34503.05208 -1.000   -1 0
"""


def test_parses_intervals_and_missing_data() -> None:
    obs = parse_hpo(SAMPLE)
    assert len(obs) == 3
    assert obs[0].time == dt.datetime(2026, 6, 19, 0, 0, tzinfo=dt.UTC)
    assert obs[0].hp30 == 3.0
    assert obs[0].ap30 == 15
    # second interval starts at 00:30
    assert obs[1].time == dt.datetime(2026, 6, 19, 0, 30, tzinfo=dt.UTC)
    # missing data -> None
    assert obs[2].hp30 is None
    assert obs[2].ap30 is None


def test_ignores_headers_and_blank_lines() -> None:
    assert parse_hpo("# just a header\n\n   \n") == []


@respx.mock
async def test_client_fetches_and_parses() -> None:
    respx.get("https://gfz.test/hp30.txt").mock(
        return_value=httpx.Response(200, text=SAMPLE)
    )
    async with GfzClient("https://gfz.test/hp30.txt") as client:
        obs = await client.get_hp30()
    assert len(obs) == 3


async def test_roundtrip(session: AsyncSession, client: AsyncClient) -> None:
    obs = parse_hpo(SAMPLE)
    n = await GfzRepository(session).upsert_hp30(obs)
    await session.commit()
    assert n == 3

    resp = await client.get(
        "/geomag/hp30",
        params={"start": "2026-06-19T00:00:00Z", "end": "2026-06-19T02:00:00Z"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3
    assert body[0]["hp30"] == 3.0
    assert body[2]["hp30"] is None

    resp = await client.get("/geomag/hp30/latest")
    assert resp.status_code == 200
    assert resp.json()["time"] == "2026-06-19T01:00:00Z"


async def test_upsert_idempotent(session: AsyncSession) -> None:
    obs = parse_hpo(SAMPLE)
    repo = GfzRepository(session)
    await repo.upsert_hp30(obs)
    await repo.upsert_hp30(obs)
    await session.commit()
    rows = await repo.read_hp30(
        dt.datetime(2026, 6, 19, tzinfo=dt.UTC),
        dt.datetime(2026, 6, 20, tzinfo=dt.UTC),
    )
    assert len(rows) == 3


async def test_hp30_latest_empty_returns_204(client: AsyncClient) -> None:
    resp = await client.get("/geomag/hp30/latest")
    assert resp.status_code == 204
