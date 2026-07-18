"""Tests for SWPC solar-region parsing."""

from __future__ import annotations

import datetime as dt

from prescient.sources.swpc.regions import SolarRegionRaw, to_observation

# A real row from solar_regions.json.
SAMPLE = {
    "observed_date": "2024-05-13",
    "region": 3664,
    "latitude": -19,
    "longitude": -87,
    "location": "S19W87",
    "carrington_longitude": 348,
    "old_carrington_longitude": 349,
    "area": 1170,
    "spot_class": "Fkc",
    "extent": 24,
    "number_spots": 15,
    "mag_class": "BGD",
    "mag_string": None,
    "status": "f",
    "c_xray_events": 0,
    "m_xray_events": 5,
    "x_xray_events": 0,
    "proton_events": None,
    "c_flare_probability": 99,
    "m_flare_probability": 75,
    "x_flare_probability": 40,
    "proton_probability": 99,
    "first_date": "2024-05-01T16:42:56",
}


def test_parses_full_row() -> None:
    obs = to_observation(SolarRegionRaw.model_validate(SAMPLE))
    assert obs is not None
    assert obs.region == 3664
    assert obs.observed_date == dt.date(2024, 5, 13)
    assert obs.latitude == -19
    # naive feed timestamp is coerced to UTC
    assert obs.first_date == dt.datetime(2024, 5, 1, 16, 42, 56, tzinfo=dt.UTC)
    assert obs.metadata.area == 1170
    assert obs.metadata.mag_string is None


def test_drops_row_missing_coordinates() -> None:
    row = {**SAMPLE, "latitude": None}
    assert to_observation(SolarRegionRaw.model_validate(row)) is None


def test_drops_row_missing_required_metadata() -> None:
    row = {**SAMPLE, "area": None}
    assert to_observation(SolarRegionRaw.model_validate(row)) is None


def test_ignores_unknown_keys() -> None:
    row = {**SAMPLE, "some_new_field": "whatever"}
    assert to_observation(SolarRegionRaw.model_validate(row)) is not None
