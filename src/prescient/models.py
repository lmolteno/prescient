"""SQLAlchemy ORM models.

JSON payloads (region metadata, HMI contours, event details) are stored in
JSONB columns. The Python-side shapes are the Pydantic models in the source
packages; these ORM rows hold their serialized (``mode="json"``) form.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import (
    Date,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from prescient.db import Base


class SolarRegion(Base):
    """A daily observation of a solar (sunspot) region from NOAA SWPC."""

    __tablename__ = "solar_region"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observed_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    region: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[int] = mapped_column(Integer, nullable=False)
    longitude: Mapped[int] = mapped_column(Integer, nullable=False)
    first_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # Attribute/column both named region_metadata: ``metadata`` is reserved on
    # the declarative Base.
    region_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint("observed_date", "region", name="uq_solar_region_date_region"),
    )


class HmiObservation(Base):
    """Sunspot umbra/penumbra contours extracted from an SDO/HMI image."""

    __tablename__ = "hmi_observation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation_time: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, unique=True, index=True
    )
    processed_time: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    umbra_contours: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    penumbra_contours: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)


class SolarEvent(Base):
    """A solar event (flare, X-ray, radio burst, …) from NOAA SWPC edited events."""

    __tablename__ = "solar_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(8), nullable=False)
    observatory: Mapped[str] = mapped_column(String(8), nullable=False)
    region: Mapped[int | None] = mapped_column(Integer, nullable=True)

    begin_datetime: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    max_datetime: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_datetime: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Common fields + type-specific payload (discriminated by ``type``).
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "type",
            "observatory",
            "begin_datetime",
            name="uq_solar_event_natural_key",
        ),
    )
