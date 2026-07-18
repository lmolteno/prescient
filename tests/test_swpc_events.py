"""Tests for SWPC solar-event parsing (the newly-wired feature)."""

from __future__ import annotations

from prescient.sources.swpc.events import (
    FixedRadioBurstEvent,
    FlareEvent,
    GenericSolarEvent,
    RadioBurstType,
    SolarEventRaw,
    SweptRadioBurstEvent,
    XrayEvent,
    to_event,
)

BASE = {
    "begin_datetime": "2024-05-28T06:38:00",
    "begin_quality": "",
    "max_datetime": "2024-05-28T06:43:00",
    "max_quality": "",
    "end_datetime": "2024-05-28T06:48:00",
    "end_quality": "",
    "observatory": "G16",
    "quality": "5",
    "type": "XRA",
    "coded_type": 1,
    "obsid": 0,
    "location": "",
    "frequency": "1-8A",
    "region": 3697,
    "bin": 7000,
    "age": None,
    "status_code": 5,
    "status_text": "",
    "change_flag": 0,
}


def _raw(**overrides) -> SolarEventRaw:
    return SolarEventRaw.model_validate({**BASE, "particulars1": None, **overrides})


def test_xray_event() -> None:
    event = to_event(_raw(type="XRA", frequency="1-8A", particulars1="C4.1"))
    assert isinstance(event, XrayEvent)
    assert event.x_ray_class == "C4.1"
    assert event.event_id == 7000
    assert event.begin_datetime.tzinfo is not None


def test_optical_flare() -> None:
    event = to_event(
        _raw(type="FLA", location="N05W10", particulars1="1N", particulars2="VWL")
    )
    assert isinstance(event, FlareEvent)
    assert event.importance == "1"
    assert event.brightness.value == "N"
    assert event.characteristics[0].value == "VWL"


def test_optical_flare_rejects_short_particular() -> None:
    assert to_event(_raw(type="FLA", particulars1="1")) is None


def test_fixed_radio_burst() -> None:
    event = to_event(_raw(type="RBR", frequency="245", particulars1="120"))
    assert isinstance(event, FixedRadioBurstEvent)
    assert event.frequency == 245
    assert event.max_brightness == 120


def test_swept_radio_burst() -> None:
    event = to_event(_raw(type="RSP", frequency="25-180", particulars1="III/2"))
    assert isinstance(event, SweptRadioBurstEvent)
    assert event.frequency_min == 25
    assert event.frequency_max == 180
    assert event.radio_burst_type is RadioBurstType.III
    assert event.intensity == 2


def test_generic_event() -> None:
    event = to_event(_raw(type="FIL"))
    assert isinstance(event, GenericSolarEvent)


def test_unknown_type_dropped() -> None:
    assert to_event(_raw(type="ZZZ")) is None


def test_unknown_observatory_dropped() -> None:
    assert to_event(_raw(observatory="XYZ", particulars1="C4.1")) is None


def test_missing_begin_dropped() -> None:
    assert to_event(_raw(begin_datetime=None, particulars1="C4.1")) is None


def test_nullable_obsid_and_location() -> None:
    # The real feed sends null obsid/location on some rows (regression).
    event = to_event(_raw(type="XRA", obsid=None, location=None, particulars1="C4.1"))
    assert isinstance(event, XrayEvent)
    flare = to_event(_raw(type="FLA", obsid=None, location=None, particulars1="1N"))
    assert isinstance(flare, FlareEvent)
    assert flare.location == ""
