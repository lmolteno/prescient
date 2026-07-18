"""SWPC solar-region models and parsing.

Mirrors the NOAA ``solar_regions.json`` feed. The raw feed is permissive
(many nullable fields); :func:`to_observation` applies the same "drop the row
if a required field is missing" rules the original Kotlin service used.
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class SolarRegionRaw(BaseModel):
    """A raw row from ``solar_regions.json`` (extra keys ignored)."""

    model_config = ConfigDict(extra="ignore")

    region: int
    latitude: int | None = None
    longitude: int | None = None
    location: str | None = None
    observed_date: dt.date
    carrington_longitude: int | None = None
    area: int | None = None
    spot_class: str | None = None
    extent: int | None = None
    number_spots: int | None = None
    mag_class: str | None = None
    mag_string: str | None = None
    status: str | None = None
    c_xray_events: int = 0
    m_xray_events: int = 0
    x_xray_events: int = 0
    proton_events: int | None = None
    c_flare_probability: int = 0
    m_flare_probability: int = 0
    x_flare_probability: int = 0
    proton_probability: int | None = None
    first_date: dt.datetime  # naive-UTC in the feed


class SolarRegionMetadata(BaseModel):
    """Type-specific detail stored in the ``metadata`` JSONB column."""

    location: str
    carrington_longitude: int | None
    area: int
    spot_class: str | None
    extent: int
    number_spots: int
    mag_class: str | None
    mag_string: str | None
    status: str | None
    c_xray_events: int
    m_xray_events: int
    x_xray_events: int
    proton_events: int | None
    c_flare_probability: int
    m_flare_probability: int
    x_flare_probability: int
    proton_probability: int | None


class SolarRegionObservation(BaseModel):
    """A validated, storable solar-region observation."""

    region: int
    observed_date: dt.date
    latitude: int
    longitude: int
    first_date: dt.datetime
    metadata: SolarRegionMetadata


def to_observation(raw: SolarRegionRaw) -> SolarRegionObservation | None:
    """Convert a raw feed row to an observation, or ``None`` if incomplete.

    Required fields (dropped if missing): latitude, longitude, location, area,
    extent, number_spots. Matches the original service's validation.
    """
    if raw.latitude is None or raw.longitude is None or raw.location is None:
        return None
    if raw.area is None or raw.extent is None or raw.number_spots is None:
        return None

    first_date = raw.first_date
    if first_date.tzinfo is None:
        first_date = first_date.replace(tzinfo=dt.UTC)

    return SolarRegionObservation(
        region=raw.region,
        observed_date=raw.observed_date,
        latitude=raw.latitude,
        longitude=raw.longitude,
        first_date=first_date,
        metadata=SolarRegionMetadata(
            location=raw.location,
            carrington_longitude=raw.carrington_longitude,
            area=raw.area,
            spot_class=raw.spot_class,
            extent=raw.extent,
            number_spots=raw.number_spots,
            mag_class=raw.mag_class,
            mag_string=raw.mag_string,
            status=raw.status,
            c_xray_events=raw.c_xray_events,
            m_xray_events=raw.m_xray_events,
            x_xray_events=raw.x_xray_events,
            proton_events=raw.proton_events,
            c_flare_probability=raw.c_flare_probability,
            m_flare_probability=raw.m_flare_probability,
            x_flare_probability=raw.x_flare_probability,
            proton_probability=raw.proton_probability,
        ),
    )
