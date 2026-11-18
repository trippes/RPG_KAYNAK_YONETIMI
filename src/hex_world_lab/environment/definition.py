"""Immutable, image-independent definitions for static environmental objects."""
from __future__ import annotations

from dataclasses import dataclass
import math

from hex_world_lab.physics.shapes import CircleShape, ConvexPolygonShape, ColliderShape


def _normalized_pair(value: tuple[float, float], field: str) -> tuple[float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise TypeError(f"{field} must contain exactly two normalized numbers")
    result = tuple(value)
    for item in result:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise TypeError(f"{field} values must be real numbers")
        if not math.isfinite(item) or not 0.0 <= item <= 1.0:
            raise ValueError(f"{field} values must be finite and between 0 and 1")
    return result


def _normalized_rect(value: tuple[float, float, float, float] | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    if not isinstance(value, (tuple, list)) or len(value) != 4:
        raise TypeError("canopy_bounds must contain x, y, width and height")
    x, y, width, height = value
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise TypeError("canopy_bounds values must be real numbers")
        if not math.isfinite(item):
            raise ValueError("canopy_bounds values must be finite")
    if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > 1 or y + height > 1:
        raise ValueError("canopy_bounds must be a positive rectangle inside the normalized image")
    return (x, y, width, height)


@dataclass(frozen=True, slots=True)
class EnvironmentalObjectDefinition:
    """Reusable object type; visual metadata never defines its collider."""

    definition_id: str
    asset_key: str
    ground_anchor: tuple[float, float]
    depth_anchor: tuple[float, float]
    canopy_bounds: tuple[float, float, float, float] | None = None
    collider: ColliderShape | None = None

    def __post_init__(self) -> None:
        for name, value in (("definition_id", self.definition_id), ("asset_key", self.asset_key)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        object.__setattr__(self, "ground_anchor", _normalized_pair(self.ground_anchor, "ground_anchor"))
        object.__setattr__(self, "depth_anchor", _normalized_pair(self.depth_anchor, "depth_anchor"))
        object.__setattr__(self, "canopy_bounds", _normalized_rect(self.canopy_bounds))
        if self.collider is not None and not isinstance(self.collider, (CircleShape, ConvexPolygonShape)):
            raise TypeError("collider must be CircleShape, ConvexPolygonShape or None")
