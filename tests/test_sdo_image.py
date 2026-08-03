"""Tests for SDO/HMI image processing."""

from __future__ import annotations

import cv2
import numpy as np

from prescient.sources.sdo.image import (
    Contour,
    Coordinate,
    ImageScale,
    _find_contours,
    extract_contours,
)


def test_coordinate_serializes_as_pair() -> None:
    c = Coordinate(x=1.5, y=2.5)
    assert c.model_dump() == [1.5, 2.5]
    assert Coordinate.model_validate([1.5, 2.5]) == c


def test_area_of_unit_square() -> None:
    square = Contour(
        coordinates=[
            Coordinate(x=0, y=0),
            Coordinate(x=1, y=0),
            Coordinate(x=1, y=1),
            Coordinate(x=0, y=1),
        ]
    )
    assert abs(square.area() - 1.0) < 1e-9


def test_remap_and_valid() -> None:
    c = Contour(coordinates=[Coordinate(x=5, y=5), Coordinate(x=6, y=7)])
    remapped = c.remap(0.0, 10.0)
    assert remapped.coordinates[0] == Coordinate(x=0.5, y=0.5)
    assert remapped.valid()  # all < 1

    out_of_range = Contour(coordinates=[Coordinate(x=11, y=5)]).remap(0.0, 10.0)
    assert not out_of_range.valid()  # x -> 1.1


def test_find_contours_detects_square() -> None:
    image = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(image, (50, 50), (90, 90), color=255, thickness=-1)  # 40x40 filled
    contours = _find_contours(image, level=0.5)
    assert len(contours) == 1
    # Shoelace area of the ~40x40 square (contour traces the inner edge).
    assert 1400 <= contours[0].area() <= 1700


def test_extract_contours_end_to_end() -> None:
    image = np.zeros((300, 300), dtype=np.uint8)
    cv2.rectangle(image, (100, 100), (140, 140), color=255, thickness=-1)
    ok, jpeg = cv2.imencode(".jpg", image)
    assert ok
    result = extract_contours(jpeg.tobytes(), ImageScale.BIG)
    # The square passes the area band at both thresholds.
    assert len(result.umbra) >= 1
    assert len(result.penumbra) >= 1
