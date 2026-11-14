"""Presentation-only scene objects with explicit geometry units.

Coordinate contract:
- q/r are integer map-cell coordinates (axial for the current hex placement schema).
- offset_x/offset_y are world-pixel offsets from the cell centre.
- anchor values are normalized sprite coordinates in [0, 1].
- collision boxes are local world-pixel AABBs relative to the placement ground anchor.
- footprint values are positive map-cell dimensions, never pixel dimensions.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType


SCENE_LAYERS = ("underlay", "ground", "canopy", "overlay")
SCENE_LAYER_ORDER = MappingProxyType({
    "underlay": 0,
    "ground": 1,
    "canopy": 2,
    "overlay": 3,
})


def _finite_number(value):
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _collision_box(value, label):
    if value is None:
        return None
    if len(value) != 4 or any(not _finite_number(item) for item in value):
        raise ValueError(f"{label} must contain finite local-pixel x/y/width/height values.")
    x, y, width, height = (float(item) for item in value)
    if width <= 0 or height <= 0:
        raise ValueError(f"{label} width and height must be positive.")
    return x, y, width, height


@dataclass(frozen=True, slots=True)
class SceneObjectPlacement:
    """One map-authored instance; offsets and collision geometry use world pixels."""

    object_id: str
    asset_id: str
    map_id: str
    q: int
    r: int
    offset_x: float = 0.0
    offset_y: float = 0.0
    footprint: tuple[int, int] = (1, 1)
    collision_box: tuple[float, float, float, float] | None = None
    depth_offset: float = 0.0
    layer: str = "ground"
    kind: str = "prop"

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.object_id, self.asset_id, self.map_id, self.kind)
        ):
            raise ValueError("Placement IDs and kind must be non-empty strings.")
        if any(type(value) is not int for value in (self.q, self.r)):
            raise TypeError("Placement cell coordinates must be integers.")
        if any(
            not _finite_number(value)
            for value in (self.offset_x, self.offset_y, self.depth_offset)
        ):
            raise TypeError("Placement offsets and depth_offset must be finite numbers.")
        footprint = tuple(self.footprint)
        if len(footprint) != 2 or any(type(value) is not int or value <= 0 for value in footprint):
            raise ValueError("Placement footprint must contain positive map-cell dimensions.")
        if self.layer not in SCENE_LAYER_ORDER:
            raise ValueError(f"Unsupported placement layer: {self.layer!r}.")
        object.__setattr__(self, "footprint", footprint)
        object.__setattr__(
            self, "collision_box",
            _collision_box(self.collision_box, "Placement collision_box"),
        )
        object.__setattr__(self, "offset_x", float(self.offset_x))
        object.__setattr__(self, "offset_y", float(self.offset_y))
        object.__setattr__(self, "depth_offset", float(self.depth_offset))


@dataclass(frozen=True, slots=True)
class SceneObject:
    """Resolved render object; visual dimensions are scaled display pixels."""

    object_id: str
    asset_id: str
    world_x: float
    world_y: float
    visual_width: float
    visual_height: float
    anchor_x: float = 0.5
    anchor_y: float = 1.0
    footprint: tuple[int, int] = (1, 1)
    collision_box: tuple[float, float, float, float] | None = None
    depth_offset: float = 0.0
    layer: str = "ground"
    stable_order: int = 0

    def __post_init__(self):
        if any(not isinstance(value, str) or not value.strip() for value in (self.object_id, self.asset_id)):
            raise ValueError("Scene object IDs must be non-empty.")
        values = (
            self.world_x, self.world_y, self.visual_width, self.visual_height,
            self.anchor_x, self.anchor_y, self.depth_offset,
        )
        if any(not _finite_number(value) for value in values):
            raise TypeError("Scene object geometry must be finite and numeric.")
        if self.visual_width <= 0 or self.visual_height <= 0:
            raise ValueError("Visual dimensions must be positive display-pixel values.")
        if not 0 <= self.anchor_x <= 1 or not 0 <= self.anchor_y <= 1:
            raise ValueError("Anchors must be normalized coordinates from 0 to 1.")
        footprint = tuple(self.footprint)
        if len(footprint) != 2 or any(type(value) is not int or value <= 0 for value in footprint):
            raise ValueError("Footprint must contain positive map-cell dimensions.")
        if self.layer not in SCENE_LAYER_ORDER:
            raise ValueError(f"Unsupported scene object layer: {self.layer!r}.")
        object.__setattr__(self, "footprint", footprint)
        object.__setattr__(
            self, "collision_box",
            _collision_box(self.collision_box, "Scene object collision_box"),
        )
        object.__setattr__(self, "depth_offset", float(self.depth_offset))

    @property
    def depth(self):
        """Depth line in world pixels, plus a world-pixel fine adjustment."""
        return self.world_y + self.depth_offset

    @property
    def visual_bounds(self):
        left = self.world_x - self.visual_width * self.anchor_x
        top = self.world_y - self.visual_height * self.anchor_y
        return left, top, left + self.visual_width, top + self.visual_height


class SceneObjectRenderer:
    """Draw cached sprites and cull against complete visual bounds."""

    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        self._scaled_images = {}

    @staticmethod
    def is_visible(obj, camera_rect, zoom=1.0):
        visual_width = obj.visual_width * zoom
        visual_height = obj.visual_height * zoom
        left = obj.world_x - visual_width * obj.anchor_x
        top = obj.world_y - visual_height * obj.anchor_y
        right, bottom = left + visual_width, top + visual_height
        x, y, width, height = camera_rect
        return not (right < x or bottom < y or left > x + width or top > y + height)

    def draw(self, renderer, obj, screen_anchor, zoom=1.0):
        image = self.asset_manager.get_image(obj.asset_id)
        if image is None:
            return False
        width = max(1, round(obj.visual_width * zoom))
        height = max(1, round(obj.visual_height * zoom))
        key = (obj.asset_id, width, height)
        if key not in self._scaled_images:
            self._scaled_images[key] = (
                image if image.get_size() == (width, height)
                else renderer.pg.transform.smoothscale(image, (width, height))
            )
        image = self._scaled_images[key]
        renderer.surface.blit(
            image,
            (
                round(screen_anchor[0] - width * obj.anchor_x),
                round(screen_anchor[1] - height * obj.anchor_y),
            ),
        )
        return True
