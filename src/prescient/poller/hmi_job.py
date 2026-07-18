"""HMI polling job: walk forward through available images, extracting contours.

On a cold start it backfills from ``backfill_days`` ago, then tracks the live
feed. Each 15-minute slot is fetched at most once (deduped against the DB).
"""

from __future__ import annotations

import asyncio
import datetime as dt

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from prescient.db import session_scope
from prescient.sources.sdo.client import HmiClient, previous_quarter_hour
from prescient.sources.sdo.image import ImageScale
from prescient.sources.sdo.repository import SdoRepository

log = structlog.get_logger(__name__)

_QUARTER = dt.timedelta(minutes=15)


async def run_hmi_poller(
    factory: async_sessionmaker[AsyncSession],
    *,
    times_url: str,
    image_base_url: str,
    idle_interval_seconds: float,
    backfill_days: int,
    now: dt.datetime | None = None,
) -> None:
    """Poll HMI images forever, backfilling then tracking the live feed."""
    start_now = now or dt.datetime.now(dt.UTC)

    async with session_scope(factory) as session:
        latest_stored = await SdoRepository(session).latest_time()

    observation_time = latest_stored or (
        previous_quarter_hour(start_now)
        - dt.timedelta(days=backfill_days)
        - _QUARTER
    )
    log.info("hmi_poller_starting", resume_from=observation_time.isoformat())

    cached_latest: dt.datetime | None = None
    async with HmiClient(times_url, image_base_url) as client:
        while True:
            if cached_latest is None or observation_time >= cached_latest:
                latest = await client.get_latest_time()
                if latest is None:
                    await asyncio.sleep(idle_interval_seconds)
                    continue
                cached_latest = latest

            # Invariant after the guard above: cached_latest is set.
            assert cached_latest is not None
            if observation_time + _QUARTER < cached_latest:
                observation_time += _QUARTER
            else:
                observation_time = cached_latest

            try:
                caught_up = await _process_slot(
                    client, factory, observation_time, cached_latest
                )
            except Exception:
                log.exception("hmi_poll_failed", observation_time=observation_time.isoformat())
                await asyncio.sleep(idle_interval_seconds)
                continue

            if caught_up:
                await asyncio.sleep(idle_interval_seconds)


async def _process_slot(
    client: HmiClient,
    factory: async_sessionmaker[AsyncSession],
    observation_time: dt.datetime,
    latest: dt.datetime,
) -> bool:
    """Fetch/store one slot. Returns True if we've caught up to the live feed."""
    async with session_scope(factory) as session:
        repo = SdoRepository(session)
        if await repo.exists(observation_time):
            return observation_time >= latest

    image = await client.get_image(observation_time, ImageScale.BIG)
    if image is None:
        log.debug("hmi_no_observation", observation_time=observation_time.isoformat())
        return observation_time >= latest

    async with session_scope(factory) as session:
        await SdoRepository(session).create(
            observation_time, dt.datetime.now(dt.UTC), image
        )
    log.info(
        "hmi_stored",
        observation_time=observation_time.isoformat(),
        umbra=len(image.umbra),
        penumbra=len(image.penumbra),
    )
    return observation_time >= latest
