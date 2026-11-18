"""Adapters from environment domain data to existing physics and render DTOs."""
from __future__ import annotations

from collections.abc import Mapping

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.physics import ObstacleDefinition
from hex_world_lab.rendering.snapshot import EnvironmentDebugVisual, SpriteVisual
from .scene import EnvironmentalObjectScene


def _definitions(scene: EnvironmentalObjectScene):
    return {item.definition_id: item for item in scene.definitions}


def environment_obstacles(scene: EnvironmentalObjectScene) -> tuple[ObstacleDefinition, ...]:
    """Adapt only explicit colliders; visual bounds never become obstacles."""
    definitions = _definitions(scene)
    result = []
    for placement in scene.placements:
        definition = definitions[placement.definition_id]
        if definition.collider is None:
            continue
        result.append(ObstacleDefinition(
            obstacle_id=f"object:{placement.instance_id}",
            map_id=placement.map_id,
            shape=definition.collider,
            position=placement.ground_position,
        ))
    return tuple(result)


def environment_sprite_visuals(
    scene: EnvironmentalObjectScene,
    asset_sizes: Mapping[str, tuple[int, int]],
) -> tuple[SpriteVisual, ...]:
    """Build sprite DTOs with depth Y derived from normalized metadata and asset size."""
    definitions = _definitions(scene)
    result = []
    for placement in scene.placements:
        definition = definitions[placement.definition_id]
        if definition.asset_key not in asset_sizes:
            raise KeyError(f"missing dimensions for environment asset: {definition.asset_key}")
        width, height = asset_sizes[definition.asset_key]
        if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in (width, height)):
            raise ValueError("environment asset dimensions must be positive integers")
        gx, gy = definition.ground_anchor
        dx, dy = definition.depth_anchor
        depth_y = placement.ground_position.y + (gy - dy) * height
        result.append(SpriteVisual(
            visual_id=placement.instance_id,
            asset_key=definition.asset_key,
            ground_anchor=placement.ground_position,
            depth_anchor_y=depth_y,
            layer_priority=5,
            normalized_anchor=definition.ground_anchor,
        ))
    return tuple(result)


def environment_debug_visuals(
    scene: EnvironmentalObjectScene,
    asset_sizes: Mapping[str, tuple[int, int]],
) -> tuple[EnvironmentDebugVisual, ...]:
    """Expose full sprite and canopy bounds in world coordinates for F4."""
    definitions = _definitions(scene)
    result = []
    for placement in scene.placements:
        definition = definitions[placement.definition_id]
        width, height = asset_sizes[definition.asset_key]
        gx, gy = definition.ground_anchor
        left = placement.ground_position.x - gx * width
        right = left + width
        bottom = placement.ground_position.y - (1.0 - gy) * height
        top = bottom + height
        canopy = None
        if definition.canopy_bounds is not None:
            x, y, w, h = definition.canopy_bounds
            canopy_left = left + x * width
            canopy_right = left + (x + w) * width
            canopy_top = placement.ground_position.y + (gy - y) * height
            canopy_bottom = placement.ground_position.y + (gy - (y + h)) * height
            canopy = (WorldPoint(canopy_left, canopy_bottom), WorldPoint(canopy_right, canopy_top))
        result.append(EnvironmentDebugVisual(
            instance_id=placement.instance_id,
            ground_anchor=placement.ground_position,
            depth_anchor=WorldPoint(
                placement.ground_position.x,
                placement.ground_position.y + (gy - definition.depth_anchor[1]) * height,
            ),
            visual_bounds=(WorldPoint(left, bottom), WorldPoint(right, top)),
            canopy_bounds=canopy,
        ))
    return tuple(result)
