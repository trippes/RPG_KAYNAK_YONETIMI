"""Conservative AABB broadphase candidate gathering."""

from dataclasses import dataclass
import math
from typing import Iterable, Protocol

from .obstacle import ObstacleDefinition
from .shapes import CircleShape, ConvexPolygonShape


@dataclass(frozen=True, slots=True)
class AABB:
    """Axis-aligned bounds in world coordinates."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        values = (self.min_x, self.min_y, self.max_x, self.max_y)
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
            raise TypeError("AABB coordinates must be real numbers")
        if any(not math.isfinite(value) for value in values):
            raise ValueError("AABB coordinates must be finite")
        if self.min_x > self.max_x or self.min_y > self.max_y:
            raise ValueError("AABB minimums must not exceed maximums")

    @classmethod
    def from_shape(cls, shape: CircleShape | ConvexPolygonShape) -> "AABB":
        if isinstance(shape, CircleShape):
            return cls(
                shape.center.x - shape.radius, shape.center.y - shape.radius,
                shape.center.x + shape.radius, shape.center.y + shape.radius,
            )
        if isinstance(shape, ConvexPolygonShape):
            xs = tuple(point.x for point in shape.vertices)
            ys = tuple(point.y for point in shape.vertices)
            return cls(min(xs), min(ys), max(xs), max(ys))
        raise TypeError("shape must be a supported collider shape")

    def expanded(self, amount: float) -> "AABB":
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise TypeError("amount must be a real number")
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("amount must be finite and non-negative")
        return AABB(
            self.min_x - amount, self.min_y - amount,
            self.max_x + amount, self.max_y + amount,
        )

    def intersects(self, other: "AABB") -> bool:
        if not isinstance(other, AABB):
            raise TypeError("other must be an AABB")
        # Inclusive comparisons deliberately retain edge-touching candidates.
        return not (
            self.max_x < other.min_x or other.max_x < self.min_x
            or self.max_y < other.min_y or other.max_y < self.min_y
        )


def gather_candidates(
    query_bounds: AABB,
    obstacles: Iterable[ObstacleDefinition],
) -> tuple[ObstacleDefinition, ...]:
    """Return every AABB-overlapping obstacle in deterministic ID order.

    This is a conservative filter only. Its results must be passed to narrowphase;
    AABB overlap is never itself treated as a collision.
    """
    if not isinstance(query_bounds, AABB):
        raise TypeError("query_bounds must be an AABB")
    values = tuple(obstacles)
    if any(not isinstance(item, ObstacleDefinition) for item in values):
        raise TypeError("obstacles must contain ObstacleDefinition values")
    ids = [item.obstacle_id for item in values]
    if len(ids) != len(set(ids)):
        raise ValueError("obstacle IDs must be unique")
    matches = [
        item for item in values
        if query_bounds.intersects(AABB.from_shape(item.world_shape()))
    ]
    return tuple(sorted(matches, key=lambda item: item.obstacle_id))


class ObstacleCandidateProvider(Protocol):
    """Map-scoped source of conservative obstacle candidates."""
    def query(self, query_bounds: AABB) -> tuple[ObstacleDefinition, ...]: ...
