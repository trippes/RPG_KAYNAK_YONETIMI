"""Shared procedural graphics primitives."""

from .canvas import ProceduralCanvas
from .geometry import Bounds2D, Point2D, Transform2D
from .palette import ColorRamp, interpolate_rgb, validate_rgb

__all__ = [
    "Bounds2D",
    "ColorRamp",
    "Point2D",
    "ProceduralCanvas",
    "Transform2D",
    "interpolate_rgb",
    "validate_rgb",
]
