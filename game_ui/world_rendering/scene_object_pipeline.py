"""Validated bridge from content-authored scene placements to Pygame sprites."""
from __future__ import annotations

from pathlib import Path

from application.content_loader import load_content_package
from core.domain.spatial import HexCoord, axial_to_world_point
from game_ui.assets.asset_manager import AssetManager
from game_ui.world_rendering.scene_object import SceneObject, SceneObjectRenderer


class SceneObjectPipeline:
    """Resolve immutable content placements once and draw cached scene sprites."""

    def __init__(self, package_path: str | Path, pygame_module, hex_size: float = 32.0):
        if isinstance(hex_size, bool) or not isinstance(hex_size, (int, float)) or hex_size <= 0:
            raise ValueError("hex_size must be a positive number.")
        self.package = load_content_package(package_path)
        self.catalog = self.package.presentation_catalog
        self.placements = self.package.scene_placements
        self.asset_manager = AssetManager(pygame_module)
        self.renderer = SceneObjectRenderer(self.asset_manager)
        self._objects_by_map = {}
        if self.catalog is None or self.placements is None:
            return

        used_asset_ids = {
            placement.asset_id for placement in self.placements.placements
        }
        for asset_id in sorted(used_asset_ids):
            source = self.catalog.resolve_path(asset_id)
            if source is not None and source.is_file():
                try:
                    self.asset_manager.load_image(asset_id, source)
                except (OSError, getattr(pygame_module, "error", OSError)):
                    # A missing or unreadable visual is non-fatal; the view draws
                    # a deterministic placeholder while content validation logs it.
                    continue

        objects_by_map = {}
        for stable_order, placement in enumerate(self.placements.placements):
            asset = self.catalog.require(placement.asset_id)
            source_size = self.catalog.source_size(placement.asset_id)
            if source_size is None:
                source_size = (
                    asset.width if asset.width > 0 else 64,
                    asset.height if asset.height > 0 else 64,
                )
            center = axial_to_world_point(
                HexCoord(placement.q, placement.r), float(hex_size),
            )
            obj = SceneObject(
                object_id=placement.object_id,
                asset_id=placement.asset_id,
                world_x=center.x + placement.offset_x,
                world_y=center.y + placement.offset_y,
                visual_width=max(1.0, source_size[0] * asset.scale),
                visual_height=max(1.0, source_size[1] * asset.scale),
                anchor_x=asset.anchor[0],
                anchor_y=asset.anchor[1],
                footprint=placement.footprint,
                collision_box=(
                    placement.collision_box
                    if placement.collision_box is not None
                    else asset.collision
                ),
                depth_offset=placement.depth_offset + asset.depth_offset,
                layer=placement.layer,
                stable_order=stable_order,
            )
            objects_by_map.setdefault(placement.map_id, []).append(obj)
        self._objects_by_map = {
            map_id: tuple(items) for map_id, items in objects_by_map.items()
        }

    def objects_for_map(self, map_id: str) -> tuple[SceneObject, ...]:
        return self._objects_by_map.get(map_id, ())

    @staticmethod
    def is_visible(obj: SceneObject, screen_anchor, viewport, zoom: float = 1.0) -> bool:
        width = obj.visual_width * zoom
        height = obj.visual_height * zoom
        left = screen_anchor[0] - width * obj.anchor_x
        top = screen_anchor[1] - height * obj.anchor_y
        right, bottom = left + width, top + height
        return not (
            right < viewport.left or bottom < viewport.top
            or left > viewport.right or top > viewport.bottom
        )

    def draw(self, renderer, obj: SceneObject, screen_anchor, zoom: float = 1.0) -> bool:
        return self.renderer.draw(renderer, obj, screen_anchor, zoom)

    @property
    def loaded_asset_count(self) -> int:
        return self.asset_manager.image_count
