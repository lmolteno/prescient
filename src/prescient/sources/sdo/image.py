"""SDO/HMI image processing: threshold a continuum image and extract sunspot
umbra/penumbra contours, normalized to the solar disk.

Ports the original Kotlin/OpenCV pipeline to ``cv2`` + ``numpy``.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

import cv2
import numpy as np
from pydantic import BaseModel, model_serializer, model_validator

# Threshold levels (fraction of full 8-bit brightness).
PENUMBRA_LEVEL = 0.65
UMBRA_LEVEL = 0.25

# Pixel bounds of the solar disk in the full-resolution (4k) image; used to
# normalize contour coordinates into a 0..1 disk frame.
SUN_MAX = 3931.0
SUN_MIN = 162.0

# Contours outside this pixel-area band are noise / the whole disk.
MIN_AREA = 10.0
MAX_AREA = 100_000.0


class ImageScale(Enum):
    """HMI image size variants. ``denominator`` scales the pixel disk bounds."""

    BIG = ("4k", 1)
    MEDIUM = ("1k", 4)
    SMALL = ("512", 8)
    EXTRA_SMALL = ("256", 16)

    def __init__(self, repr_: str, denominator: int) -> None:
        self.repr = repr_
        self.denominator = denominator


class Coordinate(BaseModel):
    """A 2D point. Serializes as ``[x, y]`` to match the original wire format."""

    x: float
    y: float

    @model_validator(mode="before")
    @classmethod
    def _from_pair(cls, value: Any) -> Any:
        if isinstance(value, (list, tuple)):
            return {"x": value[0], "y": value[1]}
        return value

    @model_serializer
    def _to_pair(self) -> list[float]:
        return [self.x, self.y]


class Contour(BaseModel):
    """A closed contour as a list of coordinates."""

    coordinates: list[Coordinate]

    def area(self) -> float:
        """Shoelace polygon area in the coordinates' current units."""
        if len(self.coordinates) < 3:
            return 0.0
        xs = np.array([c.x for c in self.coordinates], dtype=np.float64)
        ys = np.array([c.y for c in self.coordinates], dtype=np.float64)
        return float(0.5 * abs(np.dot(xs, np.roll(ys, -1)) - np.dot(ys, np.roll(xs, -1))))

    def remap(self, min_: float, max_: float) -> Contour:
        span = max_ - min_
        return Contour(
            coordinates=[
                Coordinate(x=(c.x - min_) / span, y=(c.y - min_) / span)
                for c in self.coordinates
            ]
        )

    def valid(self) -> bool:
        return all(c.x < 1.0 and c.y < 1.0 for c in self.coordinates)


class SunHmiImage(BaseModel):
    """Extracted umbra and penumbra contours for one HMI observation."""

    umbra: list[Contour]
    penumbra: list[Contour]


def _find_contours(image: np.ndarray, level: float) -> list[Contour]:
    """Threshold at ``level`` and return contours with at least 3 points."""
    _, thresh = cv2.threshold(image, level * 255, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    result: list[Contour] = []
    for c in contours:
        pts = c.reshape(-1, 2)
        if len(pts) < 3:
            continue
        result.append(
            Contour(coordinates=[Coordinate(x=float(p[0]), y=float(p[1])) for p in pts])
        )
    return result


def _process(contours: list[Contour], scale: ImageScale) -> list[Contour]:
    min_ = SUN_MIN / scale.denominator
    max_ = SUN_MAX / scale.denominator
    out: list[Contour] = []
    for c in contours:
        if not (MIN_AREA <= c.area() <= MAX_AREA):
            continue
        remapped = c.remap(min_, max_)
        if remapped.valid():
            out.append(remapped)
    return out


def extract_contours(jpeg: bytes, scale: ImageScale) -> SunHmiImage:
    """Decode a grayscale JPEG and extract umbra/penumbra sunspot contours."""
    buffer = np.frombuffer(jpeg, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("could not decode HMI image")

    penumbra = _process(_find_contours(image, PENUMBRA_LEVEL), scale)
    umbra = _process(_find_contours(image, UMBRA_LEVEL), scale)
    return SunHmiImage(umbra=umbra, penumbra=penumbra)
