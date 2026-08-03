"""End-to-end tests: repository writes → API reads (real Postgres)."""

from __future__ import annotations

import datetime as dt

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from prescient.sources.sdo.image import Contour, Coordinate, SunHmiImage
from prescient.sources.sdo.repository import SdoRepository
from prescient.sources.swpc.events import SolarEventRaw, to_event
from prescient.sources.swpc.regions import SolarRegionRaw, to_observation
from prescient.sources.swpc.repository import SwpcRepository
from tests.test_swpc_events import BASE as EVENT_BASE
from tests.test_swpc_regions import SAMPLE as REGION_SAMPLE


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_region_roundtrip(session: AsyncSession, client: AsyncClient) -> None:
    obs = to_observation(SolarRegionRaw.model_validate(REGION_SAMPLE))
    assert obs is not None
    await SwpcRepository(session).upsert_regions([obs])
    await session.commit()

    resp = await client.get("/swpc/region", params={"start": "2024-05-01", "end": "2024-05-31"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["region"] == 3664
    assert body[0]["metadata"]["area"] == 1170

    resp = await client.get("/swpc/region/3664")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_region_upsert_is_idempotent(session: AsyncSession) -> None:
    obs = to_observation(SolarRegionRaw.model_validate(REGION_SAMPLE))
    assert obs is not None
    repo = SwpcRepository(session)
    await repo.upsert_regions([obs])
    await repo.upsert_regions([obs])  # same natural key
    await session.commit()
    rows = await repo.read_region(3664)
    assert len(rows) == 1


async def test_event_roundtrip(session: AsyncSession, client: AsyncClient) -> None:
    event = to_event(
        SolarEventRaw.model_validate({**EVENT_BASE, "particulars1": "C4.1"})
    )
    assert event is not None
    await SwpcRepository(session).upsert_events([event])
    await session.commit()

    resp = await client.get(
        "/swpc/event",
        params={"start": "2024-05-28T00:00:00Z", "end": "2024-05-29T00:00:00Z"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["type"] == "XRA"
    assert body[0]["details"]["x_ray_class"] == "C4.1"

    resp = await client.get("/swpc/region/3697/event")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_event_batch_with_duplicate_key(session: AsyncSession) -> None:
    # Two rows collapsing to the same natural key in one batch must not raise
    # (regression: ON CONFLICT cannot touch a row twice).
    raw = {**EVENT_BASE, "type": "RSP", "frequency": "025-180", "observatory": "PAL"}
    e1 = to_event(SolarEventRaw.model_validate({**raw, "particulars1": "CTM/2"}))
    e2 = to_event(SolarEventRaw.model_validate({**raw, "particulars1": "VI/2"}))
    assert e1 is not None and e2 is not None
    repo = SwpcRepository(session)
    await repo.upsert_events([e1, e2])
    await session.commit()
    rows = await repo.read_region_events(3697)
    assert len(rows) == 1  # deduped, last wins


async def test_hmi_roundtrip(session: AsyncSession, client: AsyncClient) -> None:
    image = SunHmiImage(
        umbra=[Contour(coordinates=[Coordinate(x=0.1, y=0.2), Coordinate(x=0.3, y=0.4)])],
        penumbra=[],
    )
    t = dt.datetime(2024, 5, 28, 6, 30, tzinfo=dt.UTC)
    await SdoRepository(session).create(t, dt.datetime.now(dt.UTC), image)
    await session.commit()

    resp = await client.get("/sdo/hmi/latest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["umbra_contours"] == [[[0.1, 0.2], [0.3, 0.4]]]

    resp = await client.get(
        "/sdo/hmi",
        params={"start": "2024-05-28T00:00:00Z", "end": "2024-05-29T00:00:00Z"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_hmi_latest_empty_returns_204(client: AsyncClient) -> None:
    resp = await client.get("/sdo/hmi/latest")
    assert resp.status_code == 204
