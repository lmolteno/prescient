"""HTTP client for the NOAA SWPC JSON feeds."""

from __future__ import annotations

import httpx
import structlog

from prescient.sources.retry import network_retry
from prescient.sources.swpc.events import SolarEvent, SolarEventRaw, to_event
from prescient.sources.swpc.regions import (
    SolarRegionObservation,
    SolarRegionRaw,
    to_observation,
)

log = structlog.get_logger(__name__)


class SwpcClient:
    """Fetches and parses NOAA SWPC feeds. Owns a reusable HTTP client."""

    def __init__(self, base_url: str, *, client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> SwpcClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    @network_retry(include_status_errors=True)
    async def _get_json(self, path: str) -> list[dict]:
        resp = await self._client.get(f"{self._base_url}{path}")
        resp.raise_for_status()
        return resp.json()

    async def get_solar_regions(self) -> list[SolarRegionObservation]:
        """Fetch and parse ``/json/solar_regions.json``."""
        rows = await self._get_json("/json/solar_regions.json")
        observations = [
            obs
            for raw in (SolarRegionRaw.model_validate(row) for row in rows)
            if (obs := to_observation(raw)) is not None
        ]
        log.info("fetched_solar_regions", raw=len(rows), parsed=len(observations))
        return observations

    async def get_solar_events(self) -> list[SolarEvent]:
        """Fetch and parse ``/json/edited_events.json``."""
        rows = await self._get_json("/json/edited_events.json")
        events = [
            event
            for raw in (SolarEventRaw.model_validate(row) for row in rows)
            if (event := to_event(raw)) is not None
        ]
        log.info("fetched_solar_events", raw=len(rows), parsed=len(events))
        return events
