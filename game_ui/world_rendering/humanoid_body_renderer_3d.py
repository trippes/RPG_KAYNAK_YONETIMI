"""Pygame triangle renderer for the parametric humanoid body mesh."""

from __future__ import annotations

import math
from collections.abc import Mapping

import pygame

from game_ui.world_rendering.humanoid_body_3d import HumanoidBodyModel
from game_ui.world_rendering.humanoid_rig_3d import HumanoidRig, project_point_orthographic


class HumanoidBodyRenderer3D:
    """Project and depth-sort low-poly body triangles without owning game position."""

    DEFAULT_PALETTE = {
        "skin": (194, 145, 105),
        "tunic": (68, 112, 79),
        "trousers": (62, 66, 79),
        "boots": (85, 57, 39),
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
        """Draw the posed body and return the number of rasterized triangles."""
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

        colors = dict(self.DEFAULT_PALETTE)
        if palette is not None:
            if not isinstance(palette, Mapping):
                raise ValueError("palette must be a material-to-RGB mapping.")
            unknown = set(palette) - set(colors)
            if unknown:
                raise ValueError(f"Unknown body materials: {', '.join(sorted(unknown))}.")
            colors.update(palette)

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
                    point,
                    yaw=yaw,
                    scale=float(world_scale),
                    origin=(float(foot_position[0]), float(foot_position[1])),
                )
                for point in vertices
            )
            color = colors[triangle.material]
            shade = self._shade(triangle.normal, color)
            triangles.append((depth, projected, shade))

        # Camera looks toward the origin from the positive depth side.
        triangles.sort(key=lambda item: item[0])
        draw = pygame.draw
        for _, points, color in triangles:
            draw.polygon(
                surface,
                color,
                [(round(point[0]), round(point[1])) for point in points],
            )
        return len(triangles)

    @staticmethod
    def _shade(normal, base_color):
        light = (-0.35, -0.45, 0.82)
        illumination = sum(normal[index] * light[index] for index in range(3))
        brightness = max(0.62, min(1.12, 0.82 + max(0.0, illumination) * 0.30))
        return tuple(
            max(0, min(255, round(channel * brightness)))
            for channel in base_color
        )
