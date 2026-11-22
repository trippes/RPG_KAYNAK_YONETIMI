"""Cached Pygame sprite renderer for the parametric humanoid body mesh."""

from __future__ import annotations

import math
from collections import OrderedDict
from collections.abc import Mapping

import pygame

from game_ui.world_rendering.humanoid_body_3d import HumanoidBodyModel
from game_ui.world_rendering.humanoid_rig_3d import HumanoidRig, project_point_orthographic


class HumanoidBodyRenderer3D:
    """Bake each unique rig pose to a sprite and reuse it across matching actors."""

    DEFAULT_PALETTE = {
        "skin": (194, 145, 105),
        "tunic": (68, 112, 79),
        "trousers": (62, 66, 79),
        "boots": (85, 57, 39),
    }
    CACHE_MAX_ENTRIES = 96
    CACHE_MAX_BYTES = 32 * 1024 * 1024

    def __init__(self) -> None:
        self._sprite_cache: OrderedDict[tuple, tuple[pygame.Surface, tuple[int, int], int]] = (
            OrderedDict()
        )
        self._cache_bytes = 0
        self._cache_hits = 0
        self._cache_misses = 0

    def clear_cache(self) -> None:
        """Release cached pose sprites and reset diagnostic counters."""
        self._sprite_cache.clear()
        self._cache_bytes = 0
        self._cache_hits = 0
        self._cache_misses = 0

    def cache_info(self) -> dict[str, int]:
        """Return bounded sprite-cache usage and hit/miss counters."""
        return {
            "entries": len(self._sprite_cache),
            "bytes": self._cache_bytes,
            "hits": self._cache_hits,
            "misses": self._cache_misses,
        }

    def draw(
        self,
        surface,
        body: HumanoidBodyModel,
        rig: HumanoidRig,
        foot_position: tuple[float, float],
        world_scale: float,
        *,
        yaw: float = 0.0,
        local_rotations: Mapping[str, tuple[float, float, float]] | None = None,
        palette: Mapping[str, tuple[int, int, int]] | None = None,
        detail_level: str = "high",
    ) -> int:
        """Blit a cached pose sprite and return its source triangle count."""
        if (
            isinstance(world_scale, bool)
            or not isinstance(world_scale, (int, float))
            or not math.isfinite(world_scale)
            or world_scale <= 0
        ):
            raise ValueError("world_scale must be a finite positive number.")
        if (
            not isinstance(foot_position, (tuple, list))
            or len(foot_position) != 2
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in foot_position
            )
        ):
            raise ValueError("foot_position must contain two finite coordinates.")
        if not isinstance(yaw, (int, float)) or isinstance(yaw, bool) or not math.isfinite(yaw):
            raise ValueError("yaw must be a finite number.")

        colors = dict(self.DEFAULT_PALETTE)
        if palette is not None:
            if not isinstance(palette, Mapping):
                raise ValueError("palette must be a material-to-RGB mapping.")
            unknown = set(palette) - set(colors)
            if unknown:
                raise ValueError(f"Unknown body materials: {', '.join(sorted(unknown))}.")
            colors.update(palette)

        pose_key = tuple(
            sorted(
                (name, tuple(round(float(value), 6) for value in rotation))
                for name, rotation in (local_rotations or {}).items()
            )
        )
        palette_key = tuple(sorted(colors.items()))
        cache_key = (
            id(body),
            id(rig),
            round(float(yaw) % math.tau, 6),
            round(float(world_scale), 4),
            detail_level,
            pose_key,
            palette_key,
        )
        cached = self._sprite_cache.get(cache_key)
        if cached is None:
            self._cache_misses += 1
            cached = self._build_sprite(
                body, rig, float(world_scale), float(yaw), local_rotations,
                colors, detail_level,
            )
            self._store_sprite(cache_key, cached)
        else:
            self._cache_hits += 1
            self._sprite_cache.move_to_end(cache_key)

        sprite, offset, triangle_count = cached
        destination = (
            round(float(foot_position[0]) + offset[0]),
            round(float(foot_position[1]) + offset[1]),
        )
        surface.blit(sprite, destination)
        return triangle_count

    def _build_sprite(
        self,
        body: HumanoidBodyModel,
        rig: HumanoidRig,
        world_scale: float,
        yaw: float,
        local_rotations: Mapping[str, tuple[float, float, float]] | None,
        colors: Mapping[str, tuple[int, int, int]],
        detail_level: str,
    ) -> tuple[pygame.Surface, tuple[int, int], int]:
        anchor = rig.ground_anchor
        triangles = []
        for triangle in body.build_mesh(rig, local_rotations, detail_level=detail_level):
            vertices = tuple(
                (
                    point[0] - anchor[0],
                    point[1] - anchor[1],
                    point[2] - anchor[2],
                )
                for point in triangle.vertices
            )
            depth = sum(
                point[0] * math.sin(yaw) + point[1] * math.cos(yaw)
                for point in vertices
            ) / 3.0
            projected = tuple(
                project_point_orthographic(
                    point, yaw=yaw, scale=world_scale, origin=(0.0, 0.0)
                )
                for point in vertices
            )
            shade = self._shade(triangle.normal, colors[triangle.material])
            triangles.append((depth, projected, shade))

        triangles.sort(key=lambda item: item[0])
        all_points = [point for _, points, _ in triangles for point in points]
        left = math.floor(min(point[0] for point in all_points))
        top = math.floor(min(point[1] for point in all_points))
        right = math.ceil(max(point[0] for point in all_points))
        bottom = math.ceil(max(point[1] for point in all_points))
        sprite = pygame.Surface(
            (max(1, right - left + 1), max(1, bottom - top + 1)),
            pygame.SRCALPHA,
            32,
        )
        draw = pygame.draw
        for _, points, color in triangles:
            draw.polygon(
                sprite,
                color,
                [
                    (round(point[0] - left), round(point[1] - top))
                    for point in points
                ],
            )
        return sprite, (left, top), len(triangles)

    def _store_sprite(
        self,
        key: tuple,
        value: tuple[pygame.Surface, tuple[int, int], int],
    ) -> None:
        sprite = value[0]
        size_bytes = sprite.get_width() * sprite.get_height() * 4
        if size_bytes > self.CACHE_MAX_BYTES:
            return
        self._sprite_cache[key] = value
        self._cache_bytes += size_bytes
        while (
            len(self._sprite_cache) > self.CACHE_MAX_ENTRIES
            or self._cache_bytes > self.CACHE_MAX_BYTES
        ):
            _, (old_sprite, _, _) = self._sprite_cache.popitem(last=False)
            self._cache_bytes -= old_sprite.get_width() * old_sprite.get_height() * 4

    @staticmethod
    def _shade(normal, base_color):
        light = (-0.35, -0.45, 0.82)
        illumination = sum(normal[index] * light[index] for index in range(3))
        brightness = max(0.62, min(1.12, 0.82 + max(0.0, illumination) * 0.30))
        return tuple(
            max(0, min(255, round(channel * brightness)))
            for channel in base_color
        )
