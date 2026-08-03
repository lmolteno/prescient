"""Poller entrypoint: ``python -m prescient.poller`` / ``prescient-poller``.

Runs the SWPC and HMI ingest jobs concurrently in a single process, separate
from the web API so the API can scale without duplicating ingestion.
"""

from __future__ import annotations

import asyncio

import structlog

from prescient.config import get_settings
from prescient.db import create_engine, create_session_factory
from prescient.logging import configure_logging
from prescient.poller.gfz_job import run_gfz_poller
from prescient.poller.hmi_job import run_hmi_poller
from prescient.poller.swpc_job import run_swpc_poller

log = structlog.get_logger(__name__)


async def run() -> None:
    settings = get_settings()
    configure_logging(level=settings.log_level, json=settings.log_json)
    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)

    log.info("poller_starting")
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(
                run_swpc_poller(
                    factory,
                    interval_seconds=settings.swpc_poll_interval_seconds,
                    base_url=settings.swpc_base_url,
                )
            )
            tg.create_task(
                run_hmi_poller(
                    factory,
                    times_url=settings.hmi_times_url,
                    image_base_url=settings.hmi_image_base_url,
                    idle_interval_seconds=settings.hmi_poll_interval_seconds,
                    backfill_days=settings.hmi_backfill_days,
                )
            )
            tg.create_task(
                run_gfz_poller(
                    factory,
                    interval_seconds=settings.gfz_poll_interval_seconds,
                    hp30_url=settings.gfz_hp30_url,
                )
            )
    finally:
        await engine.dispose()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log.info("poller_stopped")


if __name__ == "__main__":
    main()
