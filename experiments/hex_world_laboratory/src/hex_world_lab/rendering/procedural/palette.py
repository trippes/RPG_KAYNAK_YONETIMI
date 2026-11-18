"""Immutable RGB values and deterministic color ramps."""
from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

RGB = tuple[int, int, int]


def validate_rgb(color: RGB, name: str = "color") -> RGB:
    """Validate and return an immutable 8-bit RGB triple."""
    if not isinstance(color, tuple) or len(color) != 3:
        raise TypeError(f"{name} must be an RGB tuple")
    if any(isinstance(channel, bool) or not isinstance(channel, int) for channel in color):
        raise TypeError(f"{name} channels must be integers")
    if any(not 0 <= channel <= 255 for channel in color):
        raise ValueError(f"{name} channels must be between 0 and 255")
    return color


def interpolate_rgb(start: RGB, end: RGB, amount: float) -> RGB:
    """Linearly interpolate two RGB colors; amount must be in [0, 1]."""
    validate_rgb(start, "start")
    validate_rgb(end, "end")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise TypeError("amount must be a real number")
    amount = float(amount)
    if not math.isfinite(amount) or not 0.0 <= amount <= 1.0:
        raise ValueError("amount must be finite and between 0 and 1")
    return tuple(
        round(left + (right - left) * amount)
        for left, right in zip(start, end, strict=True)
    )


@dataclass(frozen=True, slots=True)
class ColorRamp:
    """An immutable ramp sampled evenly between at least two RGB stops."""

    stops: tuple[RGB, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.stops, tuple):
            raise TypeError("stops must be a tuple")
        if len(self.stops) < 2:
            raise ValueError("a color ramp requires at least two stops")
        for index, color in enumerate(self.stops):
            validate_rgb(color, f"stops[{index}]")

    def sample(self, amount: float) -> RGB:
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise TypeError("amount must be a real number")
        amount = float(amount)
        if not math.isfinite(amount) or not 0.0 <= amount <= 1.0:
            raise ValueError("amount must be finite and between 0 and 1")
        scaled = amount * (len(self.stops) - 1)
        segment = min(int(scaled), len(self.stops) - 2)
        local_amount = scaled - segment
        return interpolate_rgb(self.stops[segment], self.stops[segment + 1], local_amount)

    @classmethod
    def from_colors(cls, colors: Iterable[RGB]) -> ColorRamp:
        return cls(tuple(colors))
