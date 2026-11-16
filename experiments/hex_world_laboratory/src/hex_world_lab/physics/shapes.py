"""Immutable local-space collider shapes for the physics core."""

from dataclasses import dataclass
import math

from hex_world_lab.movement.vector import Vector2


@dataclass(frozen=True, slots=True)
class CircleShape:
    """A circle centered at the local origin."""

    radius: float

    def __post_init__(self) -> None:
        if isinstance(self.radius, bool) or not isinstance(self.radius, (int, float)):
            raise TypeError("radius must be a real number")
        if not math.isfinite(self.radius) or self.radius <= 0:
            raise ValueError("radius must be finite and greater than zero")


@dataclass(frozen=True, slots=True)
class ConvexPolygonShape:
    """A strictly convex polygon in local space, with ordered vertices."""

    vertices: tuple[Vector2, ...]

    def __post_init__(self) -> None:
        vertices = tuple(self.vertices)
        if len(vertices) < 3:
            raise ValueError("a polygon requires at least three vertices")
        if any(not isinstance(point, Vector2) for point in vertices):
            raise TypeError("all polygon vertices must be Vector2 instances")
        if len(set(vertices)) != len(vertices):
            raise ValueError("polygon vertices must be unique")

        crosses: list[float] = []
        count = len(vertices)
        for index in range(count):
            a = vertices[index]
            b = vertices[(index + 1) % count]
            c = vertices[(index + 2) % count]
            ab_x, ab_y = b.x - a.x, b.y - a.y
            bc_x, bc_y = c.x - b.x, c.y - b.y
            cross = ab_x * bc_y - ab_y * bc_x
            if abs(cross) <= 1e-12:
                raise ValueError("polygon must not contain collinear consecutive edges")
            crosses.append(cross)

        if not (all(value > 0 for value in crosses) or all(value < 0 for value in crosses)):
            raise ValueError("polygon vertices must describe a strictly convex ordered polygon")

        twice_area = sum(
            vertices[index].x * vertices[(index + 1) % count].y
            - vertices[(index + 1) % count].x * vertices[index].y
            for index in range(count)
        )
        if abs(twice_area) <= 1e-12:
            raise ValueError("polygon area must be non-zero")

        object.__setattr__(self, "vertices", vertices)


ColliderShape = CircleShape | ConvexPolygonShape
