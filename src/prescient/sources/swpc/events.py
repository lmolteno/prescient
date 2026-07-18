"""SWPC solar-event models and parsing.

Mirrors the NOAA ``edited_events.json`` feed. A single raw row maps to one of
several event kinds depending on its ``type`` code; type-specific fields come
out of the positional ``particulars1..10`` columns.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum
from typing import Annotated, Literal

import structlog
from pydantic import BaseModel, ConfigDict, Field

log = structlog.get_logger(__name__)


class SolarEventType(StrEnum):
    BRIGHT_SURGE = "BSL"
    FILAMENT_DISAPPEARANCE = "DSF"
    ERUPTIVE_PROMINENCE = "EPL"
    FILAMENT = "FIL"
    OPTICAL_FLARE = "FLA"
    FORBUSH_DECREASE = "FOR"
    GROUND_LEVEL_EVENT = "GLE"
    LOOP_PROMINENCE_SYSTEM = "LPS"
    POLAR_CAP_ABSORPTION = "PCA"
    FIXED_FREQUENCY_RADIO_BURST = "RBR"
    RADIO_NOISE_STORM = "RNS"
    SWEEP_FREQUENCY_RADIO_BURST = "RSP"
    SPRAY = "SPY"
    XRAY_FLARE = "XFL"
    XRAY_EVENT = "XRA"


class SolarObservatory(StrEnum):
    CULGOORA = "CUL"
    HOLLOMAN = "HOL"
    PALAHUA = "PAL"
    LEARMONTH = "LEA"
    RAMEY = "RAM"
    SAGAMORE_HILL = "SAG"
    SAN_VITO = "SVI"
    GOES_13 = "G13"
    GOES_14 = "G14"
    GOES_15 = "G15"
    GOES_16 = "G16"
    GOES_17 = "G17"
    GOES_18 = "G18"
    GOES_19 = "G19"


class FlareBrightness(StrEnum):
    F = "F"  # faint
    N = "N"  # normal
    B = "B"  # brilliant


class FlareCharacteristic(StrEnum):
    VWL = "VWL"  # visible in white light
    UMB = "UMB"  # greater than or equal to 20% umbral coverage
    PRB = "PRB"  # parallel ribbon
    LPS = "LPS"  # associated loop prominence (LPS)
    YSR = "YSR"  # Y-shaped ribbon
    ERU = "ERU"  # several eruptive centers
    BPT = "BPT"  # one or more brilliant points
    HSS = "HSS"  # associated high speed dark or bright surge
    DSD = "DSD"  # dark surge on the disk
    DSF = "DSF"  # flare followed the disappearance of a solar filament in the same region
    BLU = "BLU"  # H-alpha emission greater in the blue wing than in the red wing


class RadioBurstType(StrEnum):
    II = "II"  # slow drift burst
    III = "III"  # fast drift burst
    IV = "IV"  # broadband smooth continuum burst
    V = "V"  # brief continuum burst, generally associated with Type III bursts
    # Series of Type III bursts over a period of 10 minutes or more, with no
    # period longer than 30 minutes without activity.
    VI = "VI"
    # Series of Type III and Type V bursts over a period of 10 minutes or more,
    # with no period longer than 30 minutes without activity.
    VII = "VII"
    CTM = "CTM"  # broadband, long-lived, dekametric continuum


class SolarEventRaw(BaseModel):
    """A raw row from ``edited_events.json`` (extra keys ignored)."""

    model_config = ConfigDict(extra="ignore")

    begin_datetime: dt.datetime | None = None
    begin_quality: str | None = None
    max_datetime: dt.datetime | None = None
    max_quality: str | None = None
    end_datetime: dt.datetime | None = None
    end_quality: str | None = None
    observatory: str
    quality: str | None = None
    type: str
    coded_type: int
    obsid: int | None = None
    location: str | None = None
    frequency: str = ""
    particulars1: str | None = None
    particulars2: str | None = None
    particulars3: str | None = None
    particulars4: str | None = None
    particulars5: str | None = None
    particulars6: str | None = None
    particulars7: str | None = None
    particulars8: str | None = None
    particulars9: str | None = None
    particulars10: str | None = None
    region: int | None = None
    bin: int
    age: str | None = None
    status_code: int
    status_text: str = ""
    change_flag: int

    def particulars(self) -> list[str | None]:
        return [
            self.particulars1,
            self.particulars2,
            self.particulars3,
            self.particulars4,
            self.particulars5,
            self.particulars6,
            self.particulars7,
            self.particulars8,
            self.particulars9,
            self.particulars10,
        ]


# Shared explanation of the event's begin/max/end timing, applied to
# begin_datetime below (and surfaced in the API schema).
_TIMING_DESCRIPTION = (
    "The begin time of an x-ray event is defined as the first minute, in a "
    "sequence of 4 minutes, of steep monotonic increase in 0.1-0.8 nm flux. "
    "The x-ray event maximum is taken as the minute of the peak x-ray flux. "
    "The end time is the time when the flux level decays to a point halfway "
    "between the maximum flux and the pre-flare background level.\n\n"
    "The begin time of an SXI flare (XFL) is minutes following the associated "
    "x-ray event. The maximum time is the most intense period in the brightest "
    "region of the SXI image. The end time is the last SXI image before the "
    "x-ray event end time."
)


class _EventBase(BaseModel):
    region: int | None
    event_id: int
    begin_datetime: dt.datetime = Field(description=_TIMING_DESCRIPTION)
    begin_quality: str | None
    max_datetime: dt.datetime | None
    max_quality: str | None
    end_datetime: dt.datetime | None
    end_quality: str | None
    type: SolarEventType
    observatory: SolarObservatory
    quality: str | None
    status_code: int
    status_text: str
    change_flag: int


class XrayEvent(_EventBase):
    kind: Literal["xray"] = "xray"
    frequency: str = Field(description="MHz")
    x_ray_class: str


class FlareEvent(_EventBase):
    kind: Literal["flare"] = "flare"
    location: str
    importance: str = Field(
        description=(
            "Corrected area of the flare in heliospheric square degrees at "
            "maximum brightness, observed in the H-alpha line (656.3 nm):\n"
            "  S - Subflare (area <= 2.0 square degrees)\n"
            "  1 - Importance 1 ( 2.1 <= area <=  5.1 square degrees)\n"
            "  2 - Importance 2 ( 5.2 <= area <= 12.4 square degrees)\n"
            "  3 - Importance 3 (12.5 <= area <= 24.7 square degrees)\n"
            "  4 - Importance 4 (area >= 24.8 square degrees)"
        )
    )
    brightness: FlareBrightness = Field(
        description=(
            "Relative maximum brightness of the flare in H-alpha: "
            "F - faint, N - normal, B - brilliant."
        )
    )
    characteristics: list[FlareCharacteristic]


class FixedRadioBurstEvent(_EventBase):
    kind: Literal["fixed_radio_burst"] = "fixed_radio_burst"
    frequency: int
    max_brightness: int = Field(
        description=(
            "The peak value above pre-burst background of associated radio "
            "bursts at frequencies 245, 410, 610, 1415, 2695, 4995, 8800 and "
            "15400 MHz: 1 flux unit = 10^-22 W m^-2 Hz^-1."
        )
    )


class SweptRadioBurstEvent(_EventBase):
    kind: Literal["swept_radio_burst"] = "swept_radio_burst"
    frequency_min: int
    frequency_max: int
    radio_burst_type: RadioBurstType
    intensity: int = Field(
        description="Relative scale: 1 = Minor, 2 = Significant, 3 = Major."
    )


class GenericSolarEvent(_EventBase):
    kind: Literal["generic"] = "generic"


SolarEvent = Annotated[
    XrayEvent
    | FlareEvent
    | FixedRadioBurstEvent
    | SweptRadioBurstEvent
    | GenericSolarEvent,
    Field(discriminator="kind"),
]


def _utc(value: dt.datetime | None) -> dt.datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=dt.UTC) if value.tzinfo is None else value


def to_event(raw: SolarEventRaw) -> SolarEvent | None:
    """Convert a raw feed row into a typed event, or ``None`` if unparseable."""
    try:
        event_type = SolarEventType(raw.type)
    except ValueError:
        log.debug("unknown_event_type", type=raw.type)
        return None

    try:
        observatory = SolarObservatory(raw.observatory)
    except ValueError:
        log.debug("unknown_observatory", observatory=raw.observatory)
        return None

    begin = _utc(raw.begin_datetime)
    if begin is None:
        return None

    common = {
        "region": raw.region,
        "event_id": raw.bin,
        "begin_datetime": begin,
        "begin_quality": raw.begin_quality,
        "max_datetime": _utc(raw.max_datetime),
        "max_quality": raw.max_quality,
        "end_datetime": _utc(raw.end_datetime),
        "end_quality": raw.end_quality,
        "type": event_type,
        "observatory": observatory,
        "quality": raw.quality,
        "status_code": raw.status_code,
        "status_text": raw.status_text,
        "change_flag": raw.change_flag,
    }

    p1 = raw.particulars1

    if event_type is SolarEventType.XRAY_EVENT:
        if p1 is None:
            return None
        return XrayEvent(**common, frequency=raw.frequency, x_ray_class=p1)

    if event_type is SolarEventType.OPTICAL_FLARE:
        if p1 is None or len(p1) < 2:
            return None
        characteristics = [
            FlareCharacteristic(p)
            for p in raw.particulars()
            if p is not None and p in FlareCharacteristic.__members__
        ]
        try:
            brightness = FlareBrightness(p1[1:])
        except ValueError:
            return None
        return FlareEvent(
            **common,
            location=raw.location or "",
            importance=p1[0],
            brightness=brightness,
            characteristics=characteristics,
        )

    if event_type is SolarEventType.FIXED_FREQUENCY_RADIO_BURST:
        if p1 is None:
            return None
        frequency = _int_or_none(raw.frequency)
        max_brightness = _int_or_none(p1)
        if frequency is None or max_brightness is None:
            return None
        return FixedRadioBurstEvent(
            **common, frequency=frequency, max_brightness=max_brightness
        )

    if event_type is SolarEventType.SWEEP_FREQUENCY_RADIO_BURST:
        bounds = [_int_or_none(x) for x in raw.frequency.split("-")]
        if len(bounds) != 2 or bounds[0] is None or bounds[1] is None:
            return None
        if p1 is None or "/" not in p1:
            return None
        burst_str, _, intensity_str = p1.partition("/")
        intensity = _int_or_none(intensity_str)
        if intensity is None or burst_str not in RadioBurstType.__members__:
            return None
        return SweptRadioBurstEvent(
            **common,
            frequency_min=bounds[0],
            frequency_max=bounds[1],
            radio_burst_type=RadioBurstType(burst_str),
            intensity=intensity,
        )

    return GenericSolarEvent(**common)


def _int_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None
