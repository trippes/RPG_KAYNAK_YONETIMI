"""Translate presentation scene collider metadata into native static obstacles."""
from __future__ import annotations

from pathlib import Path

from application.content_loader import load_content_package
from core.domain.physics import ConvexPolygonShape, StaticObstacle
from core.domain.spatial import HexCoord, WorldPoint, axial_to_world_point


def build_scene_object_obstacles(
    package_path: str | Path | None,
    map_definition,
    hex_size: float = 32.0,
) -> tuple[StaticObstacle, ...]:
    """Build map-scoped static colliders without coupling physics to Pygame.

    Collision boxes are local world-pixel AABBs attached to the placement's
    ground anchor. Visual sprite bounds never generate collision geometry.
    """
    if package_path is None:
        return ()
    if isinstance(hex_size, bool) or not isinstance(hex_size, (int, float)) or hex_size <= 0:
        raise ValueError("hex_size must be a positive number.")
    map_id = getattr(map_definition, "map_id", None)
    if not isinstance(map_id, str) or not map_id:
        raise TypeError("map_definition must expose a non-empty map_id.")

    package = load_content_package(package_path)
    catalog = package.presentation_catalog
    placements = package.scene_placements
    if catalog is None or placements is None:
        return ()

    obstacles = []
    for placement in placements.objects_for_map(map_id):
        asset = catalog.require(placement.asset_id)
        box = placement.collision_box if placement.collision_box is not None else asset.collision
        if box is None:
            continue
        x, y, width, height = box
        center = axial_to_world_point(
            HexCoord(placement.q, placement.r), float(hex_size),
        )
        center = WorldPoint(
            center.x + placement.offset_x,
            center.y + placement.offset_y,
        )
        vertices = (
            WorldPoint(x, y),
            WorldPoint(x + width, y),
            WorldPoint(x + width, y + height),
            WorldPoint(x, y + height),
        )
        obstacles.append(StaticObstacle(
            f"scene:{placement.object_id}",
            map_id,
            ConvexPolygonShape(vertices),
            center,
        ))
    return tuple(obstacles)
