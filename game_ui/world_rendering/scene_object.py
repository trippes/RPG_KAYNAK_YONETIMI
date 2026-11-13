"""Presentation-only scene objects with independent visual and collision bounds."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class SceneObjectPlacement:
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
        if any(not isinstance(value, str) or not value.strip() for value in
               (self.object_id, self.asset_id, self.map_id, self.kind)):
            raise ValueError("Placement IDs and kind must be non-empty strings.")
        if any(type(value) is not int for value in (self.q, self.r)):
            raise TypeError("Placement cell coordinates must be integers.")
        if any(isinstance(value, bool) or not isinstance(value, (int, float))
               for value in (self.offset_x, self.offset_y, self.depth_offset)):
            raise TypeError("Placement offsets must be numeric.")
        if len(self.footprint) != 2 or any(type(value) is not int or value <= 0 for value in self.footprint):
            raise ValueError("Placement footprint must contain positive integers.")
        if self.layer not in {"underlay", "ground", "canopy", "overlay"}:
            raise ValueError("Unsupported placement layer.")
        if self.collision_box is not None and (
            len(self.collision_box) != 4
            or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in self.collision_box)
            or self.collision_box[2] < 0 or self.collision_box[3] < 0
        ):
            raise ValueError("Collision box must be x/y/width/height.")

@dataclass(frozen=True, slots=True)
class SceneObject:
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
        if not self.object_id or not self.asset_id:
            raise ValueError("Scene object IDs must be non-empty.")
        values = (self.world_x, self.world_y, self.visual_width, self.visual_height, self.anchor_x, self.anchor_y, self.depth_offset)
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in values):
            raise TypeError("Scene object geometry must be numeric.")
        if self.visual_width <= 0 or self.visual_height <= 0:
            raise ValueError("Visual dimensions must be positive.")
        if not 0 <= self.anchor_x <= 1 or not 0 <= self.anchor_y <= 1:
            raise ValueError("Anchors must be normalized.")
        if len(self.footprint) != 2 or any(type(v) is not int or v <= 0 for v in self.footprint):
            raise ValueError("Footprint must contain positive integers.")
        if self.layer not in {"underlay", "ground", "canopy", "overlay"}:
            raise ValueError("Unsupported scene object layer.")
        if self.collision_box is not None and (len(self.collision_box) != 4 or self.collision_box[2] < 0 or self.collision_box[3] < 0):
            raise ValueError("Collision box must be x/y/width/height.")
    @property
    def depth(self):
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
        width, height = max(1, round(obj.visual_width * zoom)), max(1, round(obj.visual_height * zoom))
        key = (obj.asset_id, width, height)
        if key not in self._scaled_images:
            self._scaled_images[key] = (
                image if image.get_size() == (width, height)
                else renderer.pg.transform.smoothscale(image, (width, height))
            )
        image = self._scaled_images[key]
        renderer.surface.blit(image, (round(screen_anchor[0] - width * obj.anchor_x), round(screen_anchor[1] - height * obj.anchor_y)))
        return True
