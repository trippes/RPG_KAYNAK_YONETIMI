"""Pygame canvas adapter for procedural Surface generation."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import pygame

from .geometry import Point2D


def _positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _size(value: tuple[int, int], name: str) -> tuple[int, int]:
    if not isinstance(value, tuple) or len(value) != 2:
        raise TypeError(f"{name} must be a (width, height) tuple")
    return (
        _positive_int(value[0], f"{name}.width"),
        _positive_int(value[1], f"{name}.height"),
    )


@dataclass(slots=True)
class ProceduralCanvas:
    """Logical-coordinate drawing surface with configurable supersampling."""

    logical_size: tuple[int, int]
    supersampling: int = 3
    surface: pygame.Surface = field(init=False)

    def __post_init__(self) -> None:
        self.logical_size = _size(self.logical_size, "logical_size")
        self.supersampling = _positive_int(self.supersampling, "supersampling")
        self.surface = pygame.Surface(
            (
                self.logical_size[0] * self.supersampling,
                self.logical_size[1] * self.supersampling,
            ),
            flags=pygame.SRCALPHA,
            depth=32,
        )

    @property
    def pixel_size(self) -> tuple[int, int]:
        return self.surface.get_size()

    def point(self, point: Point2D) -> tuple[int, int]:
        if not isinstance(point, Point2D):
            raise TypeError("point must be a Point2D")
        return (
            round(point.x * self.supersampling),
            round(point.y * self.supersampling),
        )

    def rect(self, rect: tuple[float, float, float, float]) -> pygame.Rect:
        if not isinstance(rect, tuple) or len(rect) != 4:
            raise TypeError("rect must be an (x, y, width, height) tuple")
        x, y, width, height = rect
        values = (x, y, width, height)
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
            raise TypeError("rectangle values must be numbers")
        if any(not math.isfinite(value) for value in values):
            raise ValueError("rectangle values must be finite")
        if width < 0 or height < 0:
            raise ValueError("rectangle dimensions must not be negative")
        scale = self.supersampling
        return pygame.Rect(
            round(x * scale),
            round(y * scale),
            round(width * scale),
            round(height * scale),
        )

    def finish(self, output_size: tuple[int, int] | None = None) -> pygame.Surface:
        """Return a final-size SRCALPHA surface without requiring a display."""
        target_size = self.logical_size if output_size is None else _size(output_size, "output_size")
        if target_size == self.pixel_size:
            return self.surface.copy()
        return pygame.transform.smoothscale(self.surface, target_size)
