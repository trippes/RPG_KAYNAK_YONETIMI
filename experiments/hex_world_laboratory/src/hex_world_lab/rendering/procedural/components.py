"""Small reusable drawing primitives built on the procedural canvas."""
from __future__ import annotations

import math
from collections.abc import Sequence

import pygame

from .canvas import ProceduralCanvas
from .geometry import Point2D


Color = tuple[int, int, int] | tuple[int, int, int, int]


def _validate_color(color: Color) -> None:
    if not isinstance(color, tuple) or len(color) not in (3, 4):
        raise TypeError("color must be an RGB or RGBA tuple")
    if any(isinstance(channel, bool) or not isinstance(channel, int) for channel in color):
        raise TypeError("color channels must be integers")
    if any(not 0 <= channel <= 255 for channel in color):
        raise ValueError("color channels must be between 0 and 255")


def _validate_width(width: int) -> None:
    if isinstance(width, bool) or not isinstance(width, int):
        raise TypeError("width must be an integer")
    if width < 0:
        raise ValueError("width must not be negative")


def draw_ellipse(
    canvas: ProceduralCanvas,
    color: Color,
    rect: tuple[float, float, float, float],
    width: int = 0,
) -> pygame.Rect:
    """Draw a logical-coordinate ellipse; width zero fills the shape."""
    _validate_canvas_color(canvas, color)
    _validate_width(width)
    return pygame.draw.ellipse(
        canvas.surface, color, canvas.rect(rect), width * canvas.supersampling
    )


def draw_polygon(
    canvas: ProceduralCanvas,
    color: Color,
    points: Sequence[Point2D],
    width: int = 0,
) -> pygame.Rect:
    """Draw a polygon from at least three logical-coordinate points."""
    _validate_canvas_color(canvas, color)
    _validate_width(width)
    if len(points) < 3:
        raise ValueError("a polygon requires at least three points")
    mapped = [canvas.point(point) for point in points]
    return pygame.draw.polygon(
        canvas.surface, color, mapped, width * canvas.supersampling
    )


def draw_polyline(
    canvas: ProceduralCanvas,
    color: Color,
    points: Sequence[Point2D],
    width: int = 1,
    closed: bool = False,
) -> pygame.Rect:
    """Draw connected logical-coordinate points without filling the shape."""
    _validate_canvas_color(canvas, color)
    if isinstance(width, bool) or not isinstance(width, int):
        raise TypeError("width must be an integer")
    if width <= 0:
        raise ValueError("polyline width must be positive")
    if len(points) < 2:
        raise ValueError("a polyline requires at least two points")
    mapped = [canvas.point(point) for point in points]
    return pygame.draw.lines(
        canvas.surface, color, bool(closed), mapped, width * canvas.supersampling
    )


def draw_circle(
    canvas: ProceduralCanvas,
    color: Color,
    center: Point2D,
    radius: float,
    width: int = 0,
) -> pygame.Rect:
    """Draw a logical-coordinate circle."""
    _validate_canvas_color(canvas, color)
    _validate_width(width)
    if isinstance(radius, bool) or not isinstance(radius, (int, float)):
        raise TypeError("radius must be a real number")
    if not math.isfinite(radius) or radius < 0:
        raise ValueError("radius must be finite and non-negative")
    return pygame.draw.circle(
        canvas.surface,
        color,
        canvas.point(center),
        round(radius * canvas.supersampling),
        width * canvas.supersampling,
    )


def _validate_canvas_color(canvas: ProceduralCanvas, color: Color) -> None:
    if not isinstance(canvas, ProceduralCanvas):
        raise TypeError("canvas must be a ProceduralCanvas")
    _validate_color(color)
