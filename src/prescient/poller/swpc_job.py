"""SWPC polling job: periodically ingest solar regions and events."""

from __future__ import annotations

import asyncio

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from prescient.db import session_scope
from prescient.sources.swpc.client import SwpcClient
from prescient.sources.swpc.repository import SwpcRepository

log = structlog.get_logger(__name__)


async def run_swpc_poller(
    factory: async_sessionmaker[AsyncSession],
    *,
    interval_seconds: float,
    base_url: str,
) -> None:
    """Poll SWPC feeds forever. Errors are logged and retried next tick."""
    log.info("swpc_poller_starting", interval=interval_seconds)
    async with SwpcClient(base_url) as client:
        while True:
            try:
                await _tick(client, factory)
            except Exception:
                log.exception("swpc_poll_failed")
            await asyncio.sleep(interval_seconds)


async def _tick(client: SwpcClient, factory: async_sessionmaker[AsyncSession]) -> None:
    regions = await client.get_solar_regions()
    events = await client.get_solar_events()
    async with session_scope(factory) as session:
        repo = SwpcRepository(session)
        n_regions = await repo.upsert_regions(regions)
        n_events = await repo.upsert_events(events)
    log.info("swpc_ingested", regions=n_regions, events=n_events)
