"""Reusable technical skeletons for sprite-backed trees.

The skeleton owns geometry (ground/depth anchors and trunk collision), while
PNG artwork remains a replaceable visual layer. All normalized coordinates
are relative to the source sprite rectangle.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


def _point(value, name):
    if len(value) != 2:
        raise ValueError(f"{name} must contain two normalized coordinates.")
    if any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(item)
        or not 0.0 <= item <= 1.0
        for item in value
    ):
        raise ValueError(f"{name} coordinates must be finite values from 0 to 1.")
    return tuple(float(item) for item in value)


def _rect(value, name):
    if len(value) != 4:
        raise ValueError(f"{name} must contain normalized x, y, width and height.")
    if any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(item)
        for item in value
    ):
        raise ValueError(f"{name} values must be finite numbers.")
    x, y, width, height = (float(item) for item in value)
    if x < 0 or y < 0 or width < 0 or height < 0 or x + width > 1 or y + height > 1:
        raise ValueError(f"{name} must fit inside the normalized sprite rectangle.")
    return x, y, width, height


@dataclass(frozen=True, slots=True)
class TreeSkeleton:
    """Geometry contract shared by every tree PNG variant.

    ground_anchor places the sprite in the world.
    depth_anchor selects the point used for front/behind ordering.
    trunk_collision is independent of the full visual canopy.
    canopy_bounds describes foliage for future editor/debug tools.
    """

    ground_anchor: tuple[float, float] = (0.5, 0.985)
    depth_anchor: tuple[float, float] = (0.5, 0.955)
    trunk_collision: tuple[float, float, float, float] = (0.39, 0.82, 0.22, 0.16)
    canopy_bounds: tuple[float, float, float, float] = (0.03, 0.02, 0.94, 0.76)

    def __post_init__(self):
        object.__setattr__(self, "ground_anchor", _point(self.ground_anchor, "ground_anchor"))
        object.__setattr__(self, "depth_anchor", _point(self.depth_anchor, "depth_anchor"))
        object.__setattr__(self, "trunk_collision", _rect(self.trunk_collision, "trunk_collision"))
        object.__setattr__(self, "canopy_bounds", _rect(self.canopy_bounds, "canopy_bounds"))

    def sprite_top_left(self, world_anchor, sprite_size, scale=1.0):
        """Return the sprite's top-left world point for its ground anchor."""
        width, height = self._scaled_size(sprite_size, scale)
        return (
            float(world_anchor[0]) - width * self.ground_anchor[0],
            float(world_anchor[1]) - height * self.ground_anchor[1],
        )

    def depth_y(self, world_anchor, sprite_size, scale=1.0):
        """Return the world-space depth line, independent of the canopy height."""
        _, height = self._scaled_size(sprite_size, scale)
        return float(world_anchor[1]) + height * (
            self.depth_anchor[1] - self.ground_anchor[1]
        )

    def trunk_collision_bounds(self, world_anchor, sprite_size, scale=1.0):
        """Return an x/y/width/height trunk rectangle in world coordinates."""
        width, height = self._scaled_size(sprite_size, scale)
        left, top = self.sprite_top_left(world_anchor, sprite_size, scale)
        x, y, collision_width, collision_height = self.trunk_collision
        return (
            left + x * width,
            top + y * height,
            collision_width * width,
            collision_height * height,
        )

    @staticmethod
    def _scaled_size(sprite_size, scale):
        if len(sprite_size) != 2:
            raise ValueError("sprite_size must contain width and height.")
        width, height = sprite_size
        if (
            isinstance(width, bool) or isinstance(height, bool)
            or not isinstance(width, (int, float))
            or not isinstance(height, (int, float))
            or width <= 0 or height <= 0
            or not math.isfinite(width) or not math.isfinite(height)
        ):
            raise ValueError("sprite dimensions must be finite positive numbers.")
        if (
            isinstance(scale, bool) or not isinstance(scale, (int, float))
            or not math.isfinite(scale) or scale <= 0
        ):
            raise ValueError("scale must be a finite positive number.")
        return float(width) * float(scale), float(height) * float(scale)


DEFAULT_TREE_SKELETON = TreeSkeleton()
