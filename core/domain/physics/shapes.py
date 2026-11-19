"""Immutable collider geometry in local or world coordinates."""
from __future__ import annotations

from dataclasses import dataclass
import math

from core.domain.spatial import WorldPoint


@dataclass(frozen=True, slots=True)
class CircleShape:
    radius: float
    center: WorldPoint = WorldPoint(0.0, 0.0)

    def __post_init__(self) -> None:
        if not isinstance(self.center, WorldPoint):
            raise TypeError("center must be a WorldPoint.")
        if isinstance(self.radius, bool) or not isinstance(self.radius, (int, float)):
            raise TypeError("radius must be a real number.")
        if not math.isfinite(self.radius) or self.radius <= 0:
            raise ValueError("radius must be finite and greater than zero.")
        object.__setattr__(self, "radius", float(self.radius))


@dataclass(frozen=True, slots=True)
class ConvexPolygonShape:
    vertices: tuple[WorldPoint, ...]

    def __post_init__(self) -> None:
        vertices = tuple(self.vertices)
        if len(vertices) < 3:
            raise ValueError("a polygon requires at least three vertices.")
        if any(not isinstance(point, WorldPoint) for point in vertices):
            raise TypeError("all vertices must be WorldPoint values.")
        if len(set(vertices)) != len(vertices):
            raise ValueError("polygon vertices must be unique.")

        crosses = []
        for index, point in enumerate(vertices):
            following = vertices[(index + 1) % len(vertices)]
            after = vertices[(index + 2) % len(vertices)]
            ab_x, ab_y = following.x - point.x, following.y - point.y
            bc_x, bc_y = after.x - following.x, after.y - following.y
            cross = ab_x * bc_y - ab_y * bc_x
            if abs(cross) <= 1e-12:
                raise ValueError("polygon must not contain collinear consecutive edges.")
            crosses.append(cross)

        if not (all(value > 0 for value in crosses) or all(value < 0 for value in crosses)):
            raise ValueError("vertices must describe a strictly convex ordered polygon.")

        twice_area = sum(
            vertices[i].x * vertices[(i + 1) % len(vertices)].y
            - vertices[(i + 1) % len(vertices)].x * vertices[i].y
            for i in range(len(vertices))
        )
        if abs(twice_area) <= 1e-12:
            raise ValueError("polygon area must be non-zero.")
        object.__setattr__(self, "vertices", vertices)


ColliderShape = CircleShape | ConvexPolygonShape
