"""Cached Pygame sprite renderer for the parametric humanoid body mesh."""

from __future__ import annotations

import math
from collections import OrderedDict
from functools import lru_cache
from collections.abc import Mapping

import pygame

from game_ui.world_rendering.humanoid_body_3d import HumanoidBodyModel
from game_ui.world_rendering.humanoid_rig_3d import HumanoidRig


class HumanoidBodyRenderer3D:
    """Bake each unique rig pose to a sprite and reuse it across matching actors."""

    DEFAULT_PALETTE = {
        "skin": (194, 145, 105),
        "tunic": (68, 112, 79),
        "trousers": (62, 66, 79),
        "boots": (85, 57, 39),
    }
    CACHE_MAX_ENTRIES = 1024
    CACHE_MAX_BYTES = 32 * 1024 * 1024
    POSE_CACHE_QUANTIZATION = 1.0 / 128.0
    TRANSLATION_CACHE_QUANTIZATION = 1.0 / 128.0
    LOW_DETAIL_POSE_CACHE_QUANTIZATION = 1.0 / 64.0
    LOW_DETAIL_TRANSLATION_CACHE_QUANTIZATION = 1.0 / 64.0

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
        local_translations: Mapping[str, tuple[float, float, float]] | None = None,
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

        pose_quantization = (
            self.LOW_DETAIL_POSE_CACHE_QUANTIZATION
            if detail_level == "low" else self.POSE_CACHE_QUANTIZATION
        )
        translation_quantization = (
            self.LOW_DETAIL_TRANSLATION_CACHE_QUANTIZATION
            if detail_level == "low" else self.TRANSLATION_CACHE_QUANTIZATION
        )
        render_rotations = self._quantize_map(
            local_rotations, pose_quantization,
        )
        render_translations = self._quantize_map(
            local_translations, translation_quantization,
        )
        pose_key = tuple(
            sorted(
                (name, tuple(rotation))
                for name, rotation in (render_rotations or {}).items()
            )
        )
        translation_key = tuple(
            sorted(
                (name, tuple(translation))
                for name, translation in (render_translations or {}).items()
            )
        )
        target_format = None
        if isinstance(surface, pygame.Surface):
            target_format = (surface.get_bitsize(), surface.get_masks())
        palette_key = tuple(sorted(colors.items()))
        cache_key = (
            id(body),
            id(rig),
            round(float(yaw) % math.tau, 6),
            round(float(world_scale), 4),
            detail_level,
            pose_key,
            translation_key,
            palette_key,
            target_format,
        )
        cached = self._sprite_cache.get(cache_key)
        if cached is None:
            self._cache_misses += 1
            cached = self._build_sprite(
                body, rig, float(world_scale), float(yaw), render_rotations,
                render_translations, colors, detail_level,
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
        local_translations: Mapping[str, tuple[float, float, float]] | None,
        colors: Mapping[str, tuple[int, int, int]],
        detail_level: str,
    ) -> tuple[pygame.Surface, tuple[int, int], int]:
        anchor = rig.ground_anchor
        triangles = []
        (
            cosine_yaw, sine_yaw, cosine_pitch, sine_pitch,
            inverse_cosine_pitch, inverse_sqrt_two,
        ) = self._projection_basis(yaw)
        for triangle in body.build_mesh(
            rig, local_rotations, local_translations=local_translations,
            detail_level=detail_level,
        ):
            vertices = tuple(
                (
                    point[0] - anchor[0],
                    point[1] - anchor[1],
                    point[2] - anchor[2],
                )
                for point in triangle.vertices
            )
            projected = []
            depths = []
            for x, y, z in vertices:
                world_x = x * cosine_yaw + y * sine_yaw
                world_y = -x * sine_yaw + y * cosine_yaw
                ground_depth = (world_x + world_y) * inverse_sqrt_two
                vertical = z * cosine_pitch - ground_depth * sine_pitch
                projected.append((
                    (world_x - world_y) * world_scale,
                    -(vertical * inverse_cosine_pitch) * world_scale,
                ))
                depths.append(
                    ground_depth * cosine_pitch + z * sine_pitch
                )
            depth = sum(depths) / 3.0
            shade = self._shade(triangle.normal, colors[triangle.material])
            triangles.append((depth, tuple(projected), shade))

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
        display_surface = (
            pygame.display.get_surface() if pygame.display.get_init() else None
        )
        if display_surface is not None:
            sprite = sprite.convert_alpha(display_surface)
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
    def _quantize_map(values, step):
        if not values:
            return None
        return {
            name: tuple(round(float(value) / step) * step for value in vector)
            for name, vector in values.items()
        }

    @staticmethod
    @lru_cache(maxsize=64)
    def _projection_basis(yaw):
        """Precompute the isometric camera matrix once per actor heading."""
        pitch = math.atan(1.0 / math.sqrt(2.0))
        cosine_pitch, sine_pitch = math.cos(pitch), math.sin(pitch)
        return (
            math.cos(yaw),
            math.sin(yaw),
            cosine_pitch,
            sine_pitch,
            1.0 / cosine_pitch,
            1.0 / math.sqrt(2.0),
        )

    @classmethod
    def _camera_depth(cls, point, yaw):
        """Return view-space depth in the canonical isometric camera basis."""
        x, y, z = point
        cosine_yaw, sine_yaw, cosine_pitch, sine_pitch, _, inverse_sqrt_two = (
            cls._projection_basis(yaw)
        )
        world_x = x * cosine_yaw + y * sine_yaw
        world_y = -x * sine_yaw + y * cosine_yaw
        return (
            (world_x + world_y) * inverse_sqrt_two * cosine_pitch
            + z * sine_pitch
        )

    @staticmethod
    def _shade(normal, base_color):
        light = (-0.35, -0.45, 0.82)
        illumination = sum(normal[index] * light[index] for index in range(3))
        brightness = max(0.62, min(1.12, 0.82 + max(0.0, illumination) * 0.30))
        return tuple(
            max(0, min(255, round(channel * brightness)))
            for channel in base_color
        )
