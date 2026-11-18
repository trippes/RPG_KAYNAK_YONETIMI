"""Explicit collider definitions; visual geometry never creates collision."""

from dataclasses import dataclass
from .values import finite_number


@dataclass(frozen=True, slots=True)
class CircleCollider:
    center_x: float
    center_y: float
    radius: float

    def __post_init__(self):
        for name in ("center_x", "center_y", "radius"):
            value = finite_number(getattr(self, name), name)
            if name == "radius" and value <= 0:
                raise ValueError("radius must be positive")
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class ConvexPolygonCollider:
    vertices: tuple[tuple[float, float], ...]

    def __post_init__(self):
        vertices = tuple(
            (finite_number(x, "vertex.x"), finite_number(y, "vertex.y")) for x, y in self.vertices
        )
        if len(vertices) < 3 or len(set(vertices)) != len(vertices):
            raise ValueError("convex polygon requires at least three unique vertices")
        crosses = []
        for index, point in enumerate(vertices):
            following = vertices[(index + 1) % len(vertices)]
            after = vertices[(index + 2) % len(vertices)]
            ab_x, ab_y = following[0] - point[0], following[1] - point[1]
            bc_x, bc_y = after[0] - following[0], after[1] - following[1]
            cross = ab_x * bc_y - ab_y * bc_x
            if abs(cross) <= 1e-12:
                raise ValueError("convex polygon must not contain collinear consecutive edges")
            crosses.append(cross)
        if not (all(value > 0 for value in crosses) or all(value < 0 for value in crosses)):
            raise ValueError("vertices must describe a strictly convex ordered polygon")
        object.__setattr__(self, "vertices", vertices)


ColliderDefinition = CircleCollider | ConvexPolygonCollider
