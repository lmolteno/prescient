"""Tests for the SWPC and HMI HTTP clients (network mocked with respx)."""

from __future__ import annotations

import datetime as dt

import httpx
import respx

from prescient.sources.sdo.client import HmiClient, previous_quarter_hour
from prescient.sources.swpc.client import SwpcClient
from tests.test_swpc_events import BASE as EVENT_BASE
from tests.test_swpc_regions import SAMPLE as REGION_SAMPLE


@respx.mock
async def test_swpc_client_parses_feeds() -> None:
    respx.get("https://swpc.test/json/solar_regions.json").mock(
        return_value=httpx.Response(200, json=[REGION_SAMPLE])
    )
    respx.get("https://swpc.test/json/edited_events.json").mock(
        return_value=httpx.Response(200, json=[{**EVENT_BASE, "particulars1": "C4.1"}])
    )
    async with SwpcClient("https://swpc.test") as client:
        regions = await client.get_solar_regions()
        events = await client.get_solar_events()
    assert len(regions) == 1
    assert regions[0].region == 3664
    assert len(events) == 1
    assert events[0].type.value == "XRA"


@respx.mock
async def test_hmi_client_latest_time() -> None:
    respx.get("https://jsoc.test/times.json").mock(
        return_value=httpx.Response(
            200, json={"first": "20240501_000000", "last": "20240528_063000"}
        )
    )
    async with HmiClient("https://jsoc.test/times.json", "https://jsoc.test/img") as c:
        latest = await c.get_latest_time()
    assert latest == dt.datetime(2024, 5, 28, 6, 30, tzinfo=dt.UTC)


@respx.mock
async def test_hmi_client_missing_time_returns_none() -> None:
    respx.get("https://jsoc.test/times.json").mock(return_value=httpx.Response(404))
    async with HmiClient("https://jsoc.test/times.json", "https://jsoc.test/img") as c:
        assert await c.get_latest_time() is None


@respx.mock
async def test_hmi_client_missing_image_returns_none() -> None:
    from prescient.sources.sdo.image import ImageScale

    route = respx.get(url__startswith="https://jsoc.test/img/").mock(
        return_value=httpx.Response(404)
    )
    async with HmiClient("https://jsoc.test/times.json", "https://jsoc.test/img") as c:
        result = await c.get_image(
            dt.datetime(2024, 5, 28, 6, 30, tzinfo=dt.UTC), ImageScale.BIG
        )
    assert result is None
    assert route.called
    # URL is built with the yyyy/MM/dd/yyyyMMdd_HHmmss stamp.
    assert "2024/05/28/20240528_063000_Ic_flat_4k.jpg" in str(route.calls[0].request.url)


def test_previous_quarter_hour() -> None:
    t = dt.datetime(2024, 5, 28, 6, 37, 42, tzinfo=dt.UTC)
    assert previous_quarter_hour(t) == dt.datetime(2024, 5, 28, 6, 30, tzinfo=dt.UTC)
    on_boundary = dt.datetime(2024, 5, 28, 6, 45, 0, tzinfo=dt.UTC)
    assert previous_quarter_hour(on_boundary) == on_boundary
