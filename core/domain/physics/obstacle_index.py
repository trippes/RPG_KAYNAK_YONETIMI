"""Map-scoped broadphase index for native static collision obstacles."""
from __future__ import annotations

from core.domain.spatial import AABB, UniformGridIndex, WorldPoint
from .obstacle import StaticObstacle
from .shapes import CircleShape, ConvexPolygonShape


def obstacle_bounds(obstacle: StaticObstacle) -> AABB:
    if not isinstance(obstacle, StaticObstacle):
        raise TypeError("obstacle must be a StaticObstacle.")
    shape = obstacle.world_shape()
    if isinstance(shape, CircleShape):
        center = shape.center
        radius = shape.radius
        return AABB(center.x - radius, center.y - radius, center.x + radius, center.y + radius)
    xs = tuple(point.x for point in shape.vertices)
    ys = tuple(point.y for point in shape.vertices)
    return AABB(min(xs), min(ys), max(xs), max(ys))


class StaticObstacleIndex:
    """Derived broadphase index; obstacle definitions remain snapshot-owned."""
    def __init__(self, obstacles: tuple[StaticObstacle, ...], cell_size: float = 128.0):
        values = tuple(obstacles)
        if any(not isinstance(item, StaticObstacle) for item in values):
            raise TypeError("obstacles must contain StaticObstacle values.")
        ids = [item.obstacle_id for item in values]
        if len(ids) != len(set(ids)):
            raise ValueError("obstacle IDs must be unique.")
        self._obstacles = {item.obstacle_id: item for item in values}
        self._index = UniformGridIndex(cell_size)
        for item in values:
            self._index.insert(item.obstacle_id, item.map_id, obstacle_bounds(item))

    def query(self, map_id: str, bounds: AABB) -> tuple[StaticObstacle, ...]:
        return tuple(self._obstacles[item_id] for item_id in self._index.query(map_id, bounds))

    def query_circle(self, map_id: str, center: WorldPoint, radius: float) -> tuple[StaticObstacle, ...]:
        if not isinstance(center, WorldPoint):
            raise TypeError("center must be a WorldPoint.")
        return self.query(map_id, AABB.around_point(center, radius))
