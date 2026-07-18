"""HTTP client for Stanford JSOC HMI continuum images."""

from __future__ import annotations

import datetime as dt

import httpx
import structlog
from pydantic import BaseModel

from prescient.sources.retry import network_retry
from prescient.sources.sdo.image import ImageScale, SunHmiImage, extract_contours

log = structlog.get_logger(__name__)

# e.g. 2024/05/28/20240528_063800
_IMAGE_TIME_FMT = "%Y/%m/%d/%Y%m%d_%H%M%S"
# e.g. 20240528_063800
_LATEST_TIME_FMT = "%Y%m%d_%H%M%S"


class _TimesResponse(BaseModel):
    first: str
    last: str


class HmiClient:
    """Fetches HMI image-time metadata and continuum images."""

    def __init__(
        self,
        times_url: str,
        image_base_url: str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._times_url = times_url
        self._image_base_url = image_base_url.rstrip("/")
        # jsoc.stanford.edu 302-redirects images to jsoc1.stanford.edu (https).
        self._client = client or httpx.AsyncClient(timeout=300.0, follow_redirects=True)
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> HmiClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    @network_retry()
    async def get_latest_time(self) -> dt.datetime | None:
        """Return the timestamp of the most recent available image, or ``None``."""
        resp = await self._client.get(self._times_url)
        if resp.status_code == httpx.codes.NOT_FOUND:
            return None
        resp.raise_for_status()
        last = _TimesResponse.model_validate(resp.json()).last
        return dt.datetime.strptime(last, _LATEST_TIME_FMT).replace(tzinfo=dt.UTC)

    @network_retry()
    async def get_image(self, time: dt.datetime, scale: ImageScale) -> SunHmiImage | None:
        """Fetch and process the image at ``time``, or ``None`` if not published."""
        stamp = time.astimezone(dt.UTC).strftime(_IMAGE_TIME_FMT)
        url = f"{self._image_base_url}/{stamp}_Ic_flat_{scale.repr}.jpg"
        resp = await self._client.get(url)
        if resp.status_code == httpx.codes.NOT_FOUND:
            return None
        resp.raise_for_status()
        return extract_contours(resp.content, scale)


def previous_quarter_hour(instant: dt.datetime) -> dt.datetime:
    """Round ``instant`` down to the previous :00/:15/:30/:45 (UTC)."""
    instant = instant.astimezone(dt.UTC)
    return instant.replace(
        minute=instant.minute - (instant.minute % 15), second=0, microsecond=0
    )
