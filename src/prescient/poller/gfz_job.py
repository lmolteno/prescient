"""GFZ polling job: periodically ingest the Hp30/ap30 geomagnetic indices."""

from __future__ import annotations

import asyncio

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from prescient.db import session_scope
from prescient.sources.gfz.client import GfzClient
from prescient.sources.gfz.repository import GfzRepository

log = structlog.get_logger(__name__)


async def run_gfz_poller(
    factory: async_sessionmaker[AsyncSession],
    *,
    interval_seconds: float,
    hp30_url: str,
) -> None:
    """Poll the GFZ Hp30/ap30 feed forever. Errors are logged and retried."""
    log.info("gfz_poller_starting", interval=interval_seconds)
    async with GfzClient(hp30_url) as client:
        while True:
            try:
                observations = await client.get_hp30()
                async with session_scope(factory) as session:
                    n = await GfzRepository(session).upsert_hp30(observations)
                log.info("gfz_ingested", hp30=n)
            except Exception:
                log.exception("gfz_poll_failed")
            await asyncio.sleep(interval_seconds)
