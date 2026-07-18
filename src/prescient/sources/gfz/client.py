"""HTTP client for the GFZ Potsdam Hpo-index feeds."""

from __future__ import annotations

import httpx
import structlog

from prescient.sources.gfz.hpo import HpoObservation, parse_hpo
from prescient.sources.retry import network_retry

log = structlog.get_logger(__name__)


class GfzClient:
    """Fetches and parses GFZ Hpo-index text feeds."""

    def __init__(self, hp30_url: str, *, client: httpx.AsyncClient | None = None) -> None:
        self._hp30_url = hp30_url
        self._client = client or httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> GfzClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    @network_retry(include_status_errors=True)
    async def _get_text(self, url: str) -> str:
        resp = await self._client.get(url)
        resp.raise_for_status()
        return resp.text

    async def get_hp30(self) -> list[HpoObservation]:
        """Fetch and parse the Hp30/ap30 nowcast feed."""
        observations = parse_hpo(await self._get_text(self._hp30_url))
        log.info("fetched_hp30", parsed=len(observations))
        return observations
